"""Build conservative, source-grounded, public SYNTHETIC research examples.

No LLM, no tenant data, no claims that obligations apply. This output is a
screening worksheet. It links only already curated official references and
requires human checking of the current legal text and provision.
"""
from __future__ import annotations
import re
from knowledge_index import KnowledgeValidationError, official_url

SCHEMA = "lexsignal-example-research-v1"
_ID = re.compile(r"^[a-z][a-z0-9-]{1,70}$")


def _required_text(row, key, min_len=1):
    value = row.get(key)
    if not isinstance(value, str) or len(value.strip()) < min_len:
        raise KnowledgeValidationError(f"Invalid example research field: {key}")
    return value.strip()


def build_example_research(library, lenses, index):
    if library.get("schema") != "lexsignal-regulatory-library-v1":
        raise KnowledgeValidationError("Unknown curated law library")
    if lenses.get("schema") != "lexsignal-example-profile-lenses-v1":
        raise KnowledgeValidationError("Unknown synthetic profile schema")
    if index.get("schema") != "lexsignal-knowledge-v1":
        raise KnowledgeValidationError("Unknown canonical knowledge schema")
    acts = {a["id"]: a for a in library["acts"]}
    if len(acts) != len(library["acts"]):
        raise KnowledgeValidationError("Duplicate curated act")
    canonical = {e["id"][4:]: e for e in index["entities"]
                 if e.get("type") == "legal_instrument" and e.get("id", "").startswith("act:")}
    if len(canonical) != len(acts):
        raise KnowledgeValidationError("Canonical/curated law counts disagree")
    results = []
    seen_profiles = set()
    profiles = lenses.get("profiles")
    if not isinstance(profiles, list) or not 1 <= len(profiles) <= 10:
        raise KnowledgeValidationError("Unexpected synthetic profiles")
    for profile in profiles:
        if not isinstance(profile, dict):
            raise KnowledgeValidationError("Invalid synthetic profile")
        pid = _required_text(profile, "id")
        if not _ID.fullmatch(pid) or pid in seen_profiles:
            raise KnowledgeValidationError("Invalid or duplicate synthetic profile ID")
        seen_profiles.add(pid)
        title = _required_text(profile, "name")
        note = _required_text(profile, "note", 25)
        jurisdiction = _required_text(profile, "jurisdiction")
        activities = profile.get("assumedActivities")
        if not isinstance(activities, list) or not activities or not all(isinstance(s, str) and s.strip() for s in activities):
            raise KnowledgeValidationError("Invalid assumed activities")
        candidate_rows = profile.get("candidates")
        if not isinstance(candidate_rows, list) or not 1 <= len(candidate_rows) <= 20:
            raise KnowledgeValidationError("Unexpected candidate count")
        seen_acts = set()
        evidence = []
        for candidate in candidate_rows:
            if not isinstance(candidate, dict):
                raise KnowledgeValidationError("Invalid candidate")
            act_id = _required_text(candidate, "actId")
            if act_id in seen_acts or act_id not in acts or act_id not in canonical:
                raise KnowledgeValidationError("Duplicate/unknown candidate legal source")
            seen_acts.add(act_id)
            law, record = acts[act_id], canonical[act_id]
            url = _required_text(law, "source")
            if not official_url(url) or record.get("officialSourceUrl") != url:
                raise KnowledgeValidationError("Source URL not canonical or not official")
            if record.get("reviewStatus") != "curated_reference_metadata":
                raise KnowledgeValidationError("Research source requires explicit curation")
            eli = record.get("legalIdentifiers", {}).get("eli")
            if eli is not None and eli != url:
                raise KnowledgeValidationError("Inconsistent original ELI identifier")
            milestones = []
            for m in library["milestones"]:
                if m.get("act") == act_id:
                    if not official_url(m.get("url")):
                        raise KnowledgeValidationError("Invalid milestone source")
                    milestones.append({
                        "id": m["id"], "date": m["date"], "name": m["title"],
                        "type": m["kind"], "sourceUrl": m["url"],
                        "scopeNote": m["scope"],
                    })
            evidence.append({
                "actId": act_id,
                "name": _required_text(law, "title"),
                "shortName": _required_text(law, "short"),
                "citation": _required_text(law, "citation"),
                "sourceUrl": url,
                "sourceClass": "original_official_journal" if eli == url else "official_guidance_or_initiative",
                "provenanceStatus": "curated_reference_metadata",
                "screeningRationale": _required_text(candidate, "why", 20),
                "verificationQuestion": _required_text(candidate, "verify", 20),
                "evidenceStatus": "reference_only_provision_not_verified",
                "applicabilityStatus": "not_assessed",
                "humanReviewRequired": True,
                "milestones": sorted(milestones, key=lambda m: (m["date"], m["id"])),
            })
        results.append({
            "id": pid, "name": title, "jurisdiction": jurisdiction,
            "assumptions": activities, "limitations": note,
            "items": evidence,
        })
    return {
        "schema": SCHEMA, "sourceCuratedAt": _required_text(library, "curatedAt"),
        "status": "synthetic_research_draft_not_an_applicability_assessment",
        "warning": "Public illustrative examples only. Source links identify curated references, not verified provisions or the current consolidated text. No law is asserted to apply. Human source and scope review required.",
        "profiles": results,
    }
