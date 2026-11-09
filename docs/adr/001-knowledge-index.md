# ADR-001 — Canonical regulatory knowledge index (P0)

**Status:** Accepted for initial implementation slice (2026-11-09).
**Decision owner:** LexSignal platform programme, issue #14.
**Implementation:** issue #16, branch p0/knowledge-index-contracts.

## Context
LexSignal currently has several source-oriented products (RSS monitoring, curated legal library, regulatory calendar, world map), largely implemented as independent static views. JSON formats differ and a regulatory headline can be confused with an actual change in law. Client data currently lives only in browser storage, and there is no authenticated tenant service.

## Decision
Implement a deterministic, typed knowledge index generated from existing data. It has no model inference and makes no claim of reconstructing current consolidated law.

Entity types:
- authority — registered official RSS publisher, endpoint and jurisdiction.
- legal_instrument — selected editorial reference metadata with official primary source and curation timestamp.
- regulatory_milestone — dated transition/application/transposition point explicitly related to a parent legal instrument.
- source_publication — unreviewed RSS publication with source-collection provenance.

Only explicit relationships are allowed:
- regulatory_milestone to legal_instrument (milestone_of): editorial explicit parent field.
- source_publication to authority (published_by): registered feed publisher.

Do not link RSS publications to legal instruments based on keyword coincidence, and do not infer that any obligation is applicable to a client without verified legal provision evidence.

## Integrity
- Stable entity IDs with authority:, act:, milestone:, publication: prefixes.
- Strict official-source HTTPS host allowlist; reject deceptive hostnames.
- Real ISO dates and timezone-aware snapshot timestamps; dangling links and duplicates fail.
- Unique ID validation and deterministic sorting.
- metadataFingerprint SHA-256 digest of canonical metadata; exclude volatile collection time.
- Explicit provenance and reviewStatus. Editorial law-reference metadata is never a verified legal conclusion; RSS entries stay unreviewed.
- diff_metadata emits added/changed/no-longer-indexed metadata events with legalChangeVerified false; this does not prove a legal amendment or repeal.

Initial deliverable: static api/v1/knowledge.json generated alongside the existing RSS feeds. No dynamic API, tenant storage, legal-advice or complete-coverage claims.

## Next decisions
- Introduce ELI/CELEX and exact provision-level evidence with legal text versioning.
- Persist historical source snapshots, add reviewer decisions and immutable audit trails.
- Separate public sources from private organization data behind real authentication (issue #8).
- Add staging, CI, observable feed-health and rollback (issue #17).

## Boundaries
Website remains on GitHub Pages; no user uploads, OAuth credentials, private customer data or payments are added. Approved shaded sphere branding remains intact.
