#!/usr/bin/env python3
"""Build LexSignal's public, read-only machine-readable endpoints.

All source events are automatic RSS extracts and UNREVIEWED.
The generated files are static snapshots, not a query API or legal advice.
"""
import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

BASE = "https://lexsignal-eu.github.io/lexsignal/"
ALLOWED_AUTHORITIES = {
    "ESMA", "EDPB", "European Commission", "Central Bank of Ireland"
}
VALID_SECTORS = {"ai", "privacy", "fin"}
VALID_TIERS = {"high", "monitor", "background"}
MAX_ITEMS = 250

def official_url(url):
    try:
        u = urlparse(url)
        host = (u.hostname or "").lower()
        return (u.scheme == "https" and not u.username and not u.password and
                (host == "europa.eu" or host.endswith(".europa.eu") or
                 host == "centralbank.ie" or host.endswith(".centralbank.ie")))
    except (ValueError, TypeError):
        return False

def plain_text(value, size):
    s = re.sub(r"<[^>]*>", " ", str(value or ""))
    return re.sub(r"\s+", " ", s).strip()[:size]

def normalise(record):
    if not isinstance(record, dict):
        return None
    rid = str(record.get("id", ""))
    if not re.fullmatch(r"rss-[0-9a-f]{16}", rid):
        return None
    url = record.get("url", "")
    if not official_url(url):
        return None
    authority = record.get("authority")
    if authority not in ALLOWED_AUTHORITIES:
        return None
    published = record.get("date", "")
    try:
        date.fromisoformat(published)
    except (ValueError, TypeError):
        return None
    title = plain_text(record.get("title"), 200)
    if not title:
        return None
    tier = record.get("signalTier", "monitor")
    if tier not in VALID_TIERS:
        tier = "monitor"
    sectors = record.get("sectors", [])
    if not isinstance(sectors, list):
        sectors = []
    sectors = sorted(set(s for s in sectors if isinstance(s, str) and s in VALID_SECTORS))
    return {
        "id": rid,
        "title": title,
        "publishedOn": published,
        "authority": authority,
        "topic": plain_text(record.get("category"), 75),
        "eventType": plain_text(record.get("eventType") or record.get("kind"), 75),
        "sectors": sectors,
        "signalTier": tier,
        "sourceUrl": url,
        "excerpt": plain_text(record.get("summary"), 230),
        "reviewStatus": "unreviewed",
        "relevanceMethod": "automated_keyword_screening",
        "applicabilityAssessment": "not_performed",
        "collectionState": record.get("collectionState") if record.get("collectionState") in {"observed","cached"} else "unknown",
        "firstSeenAt": record.get("firstSeenAt") if isinstance(record.get("firstSeenAt"),str) else None,
        "lastObservedAt": record.get("lastObservedAt") if isinstance(record.get("lastObservedAt"),str) else None,
    }

def build_documents(snapshot):
    if not isinstance(snapshot, dict) or snapshot.get("schema") != "lexsignal-snapshot-v1":
        raise ValueError("Unknown snapshot schema")
    generated = snapshot.get("generatedAt")
    if not isinstance(generated, str):
        raise ValueError("Missing generatedAt")
    try:
        datetime.fromisoformat(generated.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid generatedAt") from exc
    raw = snapshot.get("records")
    if not isinstance(raw, list) or len(raw) > 500:
        raise ValueError("Invalid record list")
    rec_by_id = {}
    for row in raw:
        item = normalise(row)
        if item:
            rec_by_id[item["id"]] = item
    entries = sorted(rec_by_id.values(),
                     key=lambda x: (x["publishedOn"], x["id"]), reverse=True)[:MAX_ITEMS]
    warning = ("Automatically extracted from official RSS feeds; publication dates and "
               "classifications are not independently verified. Cached entries may "
               "no longer be present in the current feed. Not a complete inventory "
               "or client-specific legal advice.")
    meta = {
        "name": "LexSignal regulatory signal feed",
        "version": "1.0",
        "status": "experimental_static_snapshot",
        "dataStatus": "unreviewed_automated",
        "snapshotGeneratedAt": generated,
        "refreshTarget": "Weekdays around 07:17 UTC; scheduled jobs may be delayed",
        "recordCount": len(entries),
        "cachedRecordCount": sum(x["collectionState"]=="cached" for x in entries),
        "failedSourceCount": sum(s.get("status")=="error" for s in snapshot.get("sources",[])),
        "warning": warning,
        "homepage": BASE,
        "documentation": BASE + "agent-access.html",
        "sourceFeed": BASE + "data/regulatory_snapshot.json",
        "sources": [
            {"authority": str(s.get("authority", ""))[:80],
             "status": str(s.get("status", "unknown"))[:30],
             "matched": s.get("matched") if isinstance(s.get("matched"), int) else None,
             "cachedRecordCount": s.get("cachedRecordCount") if isinstance(s.get("cachedRecordCount"),int) else None,
             "observedRecordCount": s.get("observedRecordCount") if isinstance(s.get("observedRecordCount"),int) else None}
            for s in snapshot.get("sources", []) if isinstance(s, dict)
        ],
    }
    def feed(items, qualifier):
        return {
            "schema": "lexsignal-readonly-feed-v1",
            "filter": qualifier,
            "snapshotGeneratedAt": generated,
            "reviewStatus": "all_items_unreviewed",
            "count": len(items),
            "warning": warning,
            "items": items,
        }
    all_feed = feed(entries, "all")
    signals = feed([x for x in entries if x["signalTier"] == "high"], "automated_high_signal")
    structured = {
        "@context": "https://schema.org",
        "@type": "DataFeed",
        "name": "LexSignal source-linked regulatory updates (unreviewed)",
        "description": warning,
        "url": BASE + "api/v1/updates.json",
        "dateModified": generated,
        "license": BASE + "agent-access.html",
        "dataFeedElement": [{
            "@type": "DataFeedItem",
            "dateCreated": item["publishedOn"],
            "item": {
                "@type": "CreativeWork",
                "name": item["title"],
                "datePublished": item["publishedOn"],
                "url": item["sourceUrl"],
                "description": item["excerpt"],
                "isBasedOn": item["sourceUrl"],
            }
        } for item in entries],
    }
    return {
        "updates.json": all_feed,
        "signals.json": signals,
        "status.json": meta,
        "feed.jsonld": structured,
    }

def openapi_spec():
    paths = {}
    descriptions = {
        "updates.json": "All automatically collected, unreviewed official-source RSS entries.",
        "signals.json": "Only items flagged high by heuristic rules; none has editorial verification.",
        "status.json": "Snapshot timestamp, original feed source status, refresh expectations.",
        "feed.jsonld": "Schema.org DataFeed serialisation of the same unreviewed updates.",
    }
    for filename, summary in descriptions.items():
        paths["/api/v1/" + filename] = {"get": {
            "operationId": "read_" + filename.replace(".", "_"),
            "summary": summary,
            "responses": {"200": {"description": "Read-only static snapshot",
                "content": {( "application/ld+json" if filename.endswith(".jsonld") else "application/json"):
                  {"schema": {"type": "object"}}}}}
        }}
    return {
        "openapi": "3.1.2",
        "info": {"title": "LexSignal Read-only Static Data Feed",
                 "version": "1.0.0",
                 "description": ("Public static JSON exports from an experimental research "
                                 "preview. Not a dynamic/searchable API. All records are "
                                 "unreviewed automated extractions; not legal advice.")},
        "servers": [{"url": BASE.rstrip("/")}],
        "paths": paths,
    }

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
                    + "\n", encoding="utf-8")

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/regulatory_snapshot.json")
    parser.add_argument("--out", default="_site/api/v1")
    args = parser.parse_args(argv)
    snapshot = json.loads(Path(args.input).read_text(encoding="utf-8"))
    documents = build_documents(snapshot)
    output = Path(args.out)
    for name, value in documents.items():
        write_json(output / name, value)
    write_json(output / "openapi.json", openapi_spec())
    print("LexSignal agent feeds:", ", ".join(sorted(documents)), "records:",
          documents["updates.json"]["count"], "signals:", documents["signals.json"]["count"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
