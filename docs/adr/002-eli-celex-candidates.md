# ADR-002 — Source-derived ELI and CELEX candidates (P0 follow-up)

**Status:** Proposed; awaiting PR validation and review.  
**Parent:** #16; engineering programme #14.

## Decision
For existing curated EU legal-instrument records only, parse an explicit EUR-Lex
original-Official-Journal ELI URL of the form
`https://eur-lex.europa.eu/eli/reg|dir/YYYY/NUMBER/oj`.
Validate that instrument type, year and number agree with the editorial citation.
Reject disagreements at build time rather than silently presenting contradictory records.

Emit `legalIdentifiers` on each instrument:
- `eli`: preserved curated original-OJ URL, where available.
- `celexCandidate`: mechanical `3YYYYR####` (regulation) or
  `3YYYYL####` (directive) candidate, zero-padded to four digits.
- `celexVerification`: expressly **not independently resolved** against EUR-Lex.
- `textVersion`: original OJ; not proof of currently consolidated text.
- A clear unavailable/unresolved status for entries that do not link to an OJ ELI.

## Why this is intentionally narrow
An ESMA news page, for example, cannot be mapped to a legal instrument from
keyword similarity. A CELEX candidate is a navigation aid until separately
resolved with an official response and reviewed for the intended provision/version.
No amendment history, repeal status, national transposition or client
applicability is inferred. The RSS source pipeline remains unreviewed.

## Tests and rollout
Offline Python regressions cover direct ELI records, GDPR's leading-zero
CELEX number, NIS2's directive prefix, an ESMA-guidance-only record,
citation/source mismatch, and a generic EUR-Lex page without a resolvable ELI.
Review CI and generated `/api/v1/knowledge.json` before merging.
Do not change payments, accounts, publication frequency or branding.

## Follow-up
Resolve CELEX candidates against official EUR-Lex services, attach verified
provision-level evidence with dates and retrieval metadata, and introduce
immutable version history only after source validation and human review.
