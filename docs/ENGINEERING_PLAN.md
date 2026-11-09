# LexSignal engineering execution programme

Programme: https://github.com/lexsignal-eu/lexsignal/issues/14
Started: 2026-11-09.

The workstreams below are engineering specialties, not hired developers or autonomous agents. GitHub owners remain unassigned until an actual implementer accepts an issue.

| Track | Priority | Issue | Exit criteria |
|---|---|---|---|
| Data engineering | P0 | #15 | Registered official-source adapters, dedup and traceable provenance |
| Regulatory knowledge | P0 | #16 | Canonical entities, explicit relations, deterministic metadata versions |
| Platform / SRE | P0 | #17 | CI, staging, security and rollback |
| Auth / private data | P0 | #8 | Tested organization isolation, role enforcement and audit |
| Company profiles | P1 | #18 | Explainable matching for a named sector and jurisdiction |
| Evidence-grounded AI | P1 | #19 | Source-specific citations, abstention and reviewer approval |
| Unified product UX | P1 | #20 | Consistent navigation and complete research flow |
| Email connectors | P2 | #9 | Consented read-only OAuth with disconnect |
| PDF/DOCX pipeline | P2 | #10 | Tenant-private extraction with evidence pointers |
| Billing | P3 | #11 | Verified seller, commercial terms, hosted payments |

Execution sequence:
1. P0 first vertical slice: typed knowledge index from 10 curated legal references, 17 milestones and the current source snapshot; add registry and CI tests.
2. Better source adapters, exact legal identifiers, evidence history and version comparison.
3. Secure organization tenancy and private data handling before real client uploads.
4. An Irish fintech organization profile with a measurable false-positive rate.
5. Unified interface and real end-to-end research usability sessions.
6. Consent-based connectors and payments only after the necessary security and business gates.

Rules:
- Every change goes through a PR and automated tests.
- Metadata difference is never represented as verified change in law.
- No fictitious buttons, paid subscriptions, client emails or deployed customer storage.
- Preserve the approved blue-sphere logo.
- Creating GitHub issues does not mean a coding team is running in the background.
