#!/usr/bin/env python3
"""LexSignal P0: deterministic, source-grounded regulatory knowledge index.

Inputs retain their original review classification: curated legal reference metadata
and unreviewed RSS excerpts. This module does not infer legal applicability,
interpret law, track actual legal-text amendments, or assert that RSS disappearance
means repeal. No external dependencies.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from urllib.parse import urlsplit


class KnowledgeValidationError(ValueError):
    """A source fails our public knowledge data contract."""


KNOWN_SCHEMA = "lexsignal-knowledge-v1"
ACT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,70}$")
RSS_ID = re.compile(r"^rss-[0-9a-f]{16}$")


def _required(obj, field, typ=str):
    value = obj.get(field)
    if not isinstance(value, typ) or (typ is str and not value.strip()):
        raise KnowledgeValidationError(f"Missing or invalid {field}")
    return value


def _date(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise KnowledgeValidationError(f"Invalid {label}: expected YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise KnowledgeValidationError(f"Invalid {label}: impossible date") from exc
    return value


def _instant(value, label):
    if not isinstance(value, str):
        raise KnowledgeValidationError(f"Invalid {label}: timestamp is missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise KnowledgeValidationError(f"Invalid {label}: expected ISO 8601") from exc
    if parsed.utcoffset() is None:
        raise KnowledgeValidationError(f"Invalid {label}: timezone missing")
    return value


def official_url(url):
    """Reject deceptive domains, credentials, HTTP and arbitrary third parties."""
    if not isinstance(url, str):
        return False
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        if parts.port not in (None, 443):
            return False
        return (
            parts.scheme == "https" and not parts.username and not parts.password
            and host != "" and
            (host == "europa.eu" or host.endswith(".europa.eu")
             or host == "centralbank.ie" or host.endswith(".centralbank.ie")
             or host == "gov.ie" or host.endswith(".gov.ie")
             or host == "dataprotection.ie" or host.endswith(".dataprotection.ie"))
        )
    except ValueError:
        return False


def _url(obj, key):
    value = _required(obj, key)
    if not official_url(value):
        raise KnowledgeValidationError(f"Non-official or invalid URL in {key}: {value[:120]}")
    return value



def _explicit_eu_legal_identifiers(citation, source_url):
    """Expose only identifiers grounded in a curated EUR-Lex OJ URI.

    A CELEX candidate is derived mechanically from the EU act type/year/number.
    Neither the candidate nor an OJ link proves the latest consolidated text,
    an amendment, or applicability to any organisation.
    """
    source = urlsplit(source_url)
    if source.hostname != "eur-lex.europa.eu":
        return {"legalIdentifiers": {"status": "not_available_from_curated_source"}}
    match = re.fullmatch(r"/eli/(reg|dir)/([0-9]{4})/([0-9]{1,4})/oj/?", source.path)
    if not match or source.query or source.fragment:
        return {"legalIdentifiers": {"status": "unresolved_eurlex_source_uri"}}

    kind, year, number = match.groups()
    cited = re.match(
        r"^(Regulation|Directive)\s+\(EU\)\s+([0-9]{4})/([0-9]{1,4})(?=\b|,)",
        citation,
    )
    kind_label = "Regulation" if kind == "reg" else "Directive"
    if not cited or cited.group(1) != kind_label or cited.group(2) != year or int(cited.group(3)) != int(number):
        raise KnowledgeValidationError(
            "Citation and official EUR-Lex ELI identifier disagree"
        )

    celex_kind = "R" if kind == "reg" else "L"
    return {"legalIdentifiers": {
        "status": "parsed_from_curated_eli_original_journal_uri",
        "eli": source_url,
        "celexCandidate": f"3{year}{celex_kind}{int(number):04d}",
        "celexVerification": "algorithmic_candidate_not_independently_resolved",
        "textVersion": "original_official_journal_not_consolidated_current_text",
    }}


def _fingerprint(payload):
    """Stable 24-char SHA-256 fingerprint of editorial/source content only.

    Collection timestamps are deliberately excluded from fingerprints, because
    a new RSS observation is NOT a new legal rule or even a new source document.
    """
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def _entity(entity_id, kind, content, provenance, **other):
    return {
        "id": entity_id, "type": kind, "metadataFingerprint": _fingerprint(content),
        "provenance": provenance, **content, **other,
    }


def _unique_row_id(name, seen):
    if name in seen:
        raise KnowledgeValidationError(f"Duplicate entity identifier: {name}")
    seen.add(name)


def build_index(library, snapshot, registry):
    if not all(isinstance(x, dict) for x in (library, snapshot, registry)):
        raise KnowledgeValidationError("All inputs must be JSON objects")
    if library.get("schema") != "lexsignal-regulatory-library-v1":
        raise KnowledgeValidationError("Unknown library schema")
    if snapshot.get("schema") != "lexsignal-snapshot-v1":
        raise KnowledgeValidationError("Unknown regulatory snapshot schema")
    if registry.get("schema") != "lexsignal-source-registry-v1":
        raise KnowledgeValidationError("Unknown source registry schema")
    curated_at = _date(_required(library, "curatedAt"), "library curatedAt")
    collected_at = _instant(_required(snapshot, "generatedAt"), "snapshot generatedAt")
    acts, milestones, raw_records = (
        _required(library, "acts", list),
        _required(library, "milestones", list),
        _required(snapshot, "records", list),
    )
    authorities = _required(registry, "authorities", list)
    if not (1 <= len(authorities) <= 100 and 1 <= len(acts) <= 10000
            and len(milestones) <= 20000 and len(raw_records) <= 500):
        raise KnowledgeValidationError("Input exceeds approved entity limits")
    entities, links, seen = [], [], set()
    registry_by_name = {}
    for row in authorities:
        if not isinstance(row, dict):
            raise KnowledgeValidationError("Authority must be an object")
        short_id = _required(row, "id")
        if not ACT_ID.fullmatch(short_id):
            raise KnowledgeValidationError("Bad authority ID")
        name = _required(row, "name")
        if name in registry_by_name:
            raise KnowledgeValidationError("Duplicate authority name")
        registry_by_name[name] = "authority:" + short_id
        _unique_row_id("authority:" + short_id, seen)
        canonical = {
            "name": name,
            "jurisdiction": _required(row, "jurisdiction"),
            "officialWebsite": _url(row, "homepage"),
            "rssEndpoint": _url(row, "rssEndpoint"),
        }
        entities.append(_entity("authority:" + short_id, "authority", canonical,
            "source_registry", reviewStatus="registry_metadata"))

    act_ids = set()
    for row in acts:
        if not isinstance(row, dict):
            raise KnowledgeValidationError("Act must be an object")
        id_part = _required(row, "id")
        if not ACT_ID.fullmatch(id_part):
            raise KnowledgeValidationError("Invalid legal act ID")
        id_ = "act:" + id_part
        _unique_row_id(id_, seen)
        act_ids.add(id_part)
        sectors = _required(row, "sectors", list)
        if not sectors or not all(isinstance(x, str) and x for x in sectors):
            raise KnowledgeValidationError(f"Invalid sectors in {id_}")
        topics = _required(row, "topics", list)
        if not all(isinstance(x, str) and x for x in topics):
            raise KnowledgeValidationError(f"Invalid topics in {id_}")
        citation = _required(row, "citation")
        source_url = _url(row, "source")
        canonical = {
            "name": _required(row, "title"), "shortName": _required(row, "short"),
            "citation": citation, "instrumentType": _required(row, "type"),
            "officialSourceUrl": source_url,
            **_explicit_eu_legal_identifiers(citation, source_url),
            "summary": _required(row, "summary"),
            "assessmentQuestion": _required(row, "check"),
            "sectors": sorted(set(sectors)), "topics": sorted(set(topics)),
            "jurisdiction": "EU",
        }
        entities.append(_entity(id_, "legal_instrument", canonical,
            "editorial_library", reviewStatus="curated_reference_metadata",
            curatedAt=curated_at))

    for row in milestones:
        if not isinstance(row, dict):
            raise KnowledgeValidationError("Milestone must be an object")
        id_part = _required(row, "id")
        if not ACT_ID.fullmatch(id_part):
            raise KnowledgeValidationError("Invalid milestone ID")
        id_ = "milestone:" + id_part
        _unique_row_id(id_, seen)
        act = _required(row, "act")
        if act not in act_ids:
            raise KnowledgeValidationError(f"Unknown linked legal instrument: {act}")
        canonical = {
            "name": _required(row, "title"), "date": _date(_required(row, "date"), "milestone"),
            "milestoneType": _required(row, "kind"), "scopeNote": _required(row, "scope"),
            "officialSourceUrl": _url(row, "url"), "jurisdiction": "EU",
        }
        entities.append(_entity(id_, "regulatory_milestone", canonical,
            "editorial_library", reviewStatus="curated_reference_metadata",
            curatedAt=curated_at))
        links.append({
            "from": id_, "to": "act:" + act, "type": "milestone_of",
            "basis": "explicit_editorial_library_reference",
            "reviewStatus": "curated_reference_metadata",
        })

    for row in raw_records:
        if not isinstance(row, dict):
            raise KnowledgeValidationError("RSS publication must be an object")
        id_part = _required(row, "id")
        if not RSS_ID.fullmatch(id_part):
            raise KnowledgeValidationError("Bad RSS item ID")
        id_ = "publication:" + id_part
        _unique_row_id(id_, seen)
        authority = _required(row, "authority")
        if authority not in registry_by_name:
            raise KnowledgeValidationError(f"Unregistered authority: {authority}")
        canonical = {
            "name": _required(row, "title"),
            "publishedOn": _date(_required(row, "date"), "publication"),
            "authority": authority,
            "officialSourceUrl": _url(row, "url"),
            "excerpt": _required(row, "summary"),
            "sourceKind": "rss",
        }
        state = row.get("collectionState", "unknown")
        if state not in ("observed", "cached", "unknown"):
            raise KnowledgeValidationError(f"Invalid collection state in {id_}")
        provenance = {
            "method": "unreviewed_official_rss_extract",
            "collectionState": state,
            "firstSeenAt": row.get("firstSeenAt"),
            "lastObservedAt": row.get("lastObservedAt"),
        }
        entities.append(_entity(id_, "source_publication", canonical,
            provenance, reviewStatus="unreviewed_automated",
            screeningTier=row.get("signalTier", "unassessed")))
        links.append({
            "from": id_, "to": registry_by_name[authority], "type": "published_by",
            "basis": "declared_official_rss_publisher", "reviewStatus": "unreviewed_automated",
        })

    # Only explicit, grounded relationships are emitted. Do not infer that an RSS
    # headline amends or relates to a specific act from keyword coincidence.
    entities.sort(key=lambda x: x["id"])
    links.sort(key=lambda x: (x["from"], x["to"], x["type"]))
    counters = {
        "authorities": len(authorities), "legalInstruments": len(acts),
        "regulatoryMilestones": len(milestones), "rssPublications": len(raw_records),
        "relationships": len(links),
    }
    source_states = []
    for s in snapshot.get("sources", []):
        if not isinstance(s, dict) or s.get("authority") not in registry_by_name:
            raise KnowledgeValidationError("Invalid/unregistered source status")
        source_states.append({
            "authority": s["authority"],
            "state": s.get("status") if s.get("status") in ("ok", "error") else "unknown",
            "observedRecordCount": int(s.get("observedRecordCount", 0)),
            "cachedRecordCount": int(s.get("cachedRecordCount", 0)),
        })
    return {
        "schema": KNOWN_SCHEMA,
        "indexStatus": "experimental_structured_metadata_not_verified_legal_conclusions",
        "warning": ("Legal references are editorial metadata; RSS publications are unreviewed. "
                    "Metadata fingerprint changes are not proof of a legal amendment. "
                    "No applicability, repeal or effective-law determination has been made."),
        "provenance": {
            "libraryCuratedAt": curated_at,
            "rssSnapshotGeneratedAt": collected_at,
            "sourceStatus": sorted(source_states, key=lambda s: s["authority"]),
        },
        "counts": counters, "entities": entities, "relationships": links,
    }


def diff_metadata(previous, current):
    """Report metadata differences, not actual legal amendments or repeals."""
    if previous.get("schema") != KNOWN_SCHEMA or current.get("schema") != KNOWN_SCHEMA:
        raise KnowledgeValidationError("Unknown knowledge index schema in comparison")
    old = {row["id"]: row for row in previous["entities"]}
    new = {row["id"]: row for row in current["entities"]}
    out = []
    for eid in sorted(set(old) | set(new)):
        a, b = old.get(eid), new.get(eid)
        if a is None:
            kind = "record_added"
        elif b is None:
            kind = "record_no_longer_indexed"
        elif a["metadataFingerprint"] != b["metadataFingerprint"]:
            kind = "metadata_changed"
        else:
            continue
        out.append({
            "entityId": eid, "eventType": kind,
            "oldMetadataFingerprint": a["metadataFingerprint"] if a else None,
            "newMetadataFingerprint": b["metadataFingerprint"] if b else None,
            "legalChangeVerified": False,
        })
    return {"schema": "lexsignal-metadata-diff-v1", "events": out,
            "warning": "Metadata changes do not establish legal amendments or repeal."}
