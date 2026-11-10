# LexSignal — Ten Release Milestones (M1–M10)

Status: approved engineering execution plan as of 2026-11-10. Source of truth for tasks remains [programme issue #14](https://github.com/lexsignal-eu/lexsignal/issues/14) and its linked implementation issues.

**Naming:** M1–M10 are the current release milestones. They map to existing P0–P3 engineering workstreams, and do not purport to recreate the missing historical P4–P10 chat messages.

## Product release objective

Deliver a secure, evidence-grounded regulatory intelligence application for small legal and compliance teams: official publication → named legal instrument and provision → dated applicability question → human review and task → source-cited export. Every material legal claim must link to the precise source/version, with explicit review and uncertainty status. Customer confidentiality, EU/Irish data protection obligations and business readiness gate commercial release.

| Milestone | Phase / links | Definition of done | Current state |
| --- | --- | --- | --- |
| **M1 — Source integrity and canonical knowledge** | P0 · #15, #16 | Registered official sources; deduplicated typed entries; strict URLs; provenance, timestamps, error and cache status; inspectable user-facing source health; tested static machine feed | **In progress.** First P0 index merged in #21; this PR adds the source transparency panel |
| **M2 — Legal identifiers, versioning and evidence** | P0 · #16 | ELI and CELEX where applicable; law text version history; provision-specific source citations and immutable evidence; amendment vs metadata-diff distinction; test AI Act, MiCA, DORA, NIS2 | **In progress.** Source-linked UI and validated ELI / algorithmic CELEX candidates merged in #22/#24; official identifier resolution, provisions and version history pending |
| **M3 — Release engineering and operational quality** | P0 · #17 | Isolated staging, browser smoke tests, schema/link validation, build artifact provenance, feed-failure alerts, reproducible releases and tested rollback; deploys gated by CI | **In progress.** Candidate PR implements one static build, offline link validation, provenance manifest and downloadable CI preview; browser acceptance, alerts, staging URL and rollback test outstanding |
| **M4 — Accounts, organizations and security** | P0 · #8 | Authenticated organization memberships, role checks, tenant isolation, audited edits, retention/deletion/export, security testing and privacy notices | **In progress.** Tested server-side authorization contract and tenant membership FKs proposed; real authentication, API, audit and private storage pending |
| **M5 — Organization-scoped regulatory watchlists** | P1 · #18 | Explainable sector/jurisdiction/activity profile; relevance questions; test Irish payment institution; reviewer overrides and false-positive measurements | **In progress.** Public synthetic profile lens integrated into Regulatory Library; tenant profiles, relevance evaluation and review history require M4 backend |
| **M6 — Evidence-grounded AI research** | P1 · #19 | Retrieve exact verified provisions and versions; citation checks, abstention, 30+ annotated evaluation cases, prompt-injection tests, human acceptance | **In progress.** Deterministic source-joined research worksheet and 30 mutated fail-closed fixtures; no AI inference, provision text or verified applicability yet |
| **M7 — Unified research workflow and UX** | P1 · #20 | One responsive accessible route: import → validate → instrument → assess → assign → approved cited brief/export; empty/error states and human usability test | **In progress.** Synthetic source-to-reviewed-worksheet route with user-selected export; cross-product import/action continuity and actual usability test pending |
| **M8 — Private documents and consented integrations** | P2 · #9, #10 | Private PDF/DOCX extraction with per-page evidence, malware/size limits, storage policies; permission-scoped read-only Gmail and Microsoft Graph OAuth with revoke/delete | Local text/EML document lab only |
| **M9 — Pilot readiness and external acceptance** | Cross-cutting · #1, #2 | Production-like demo and documented accuracy; 3–5 consented discovery/user tests, issue resolution, customer pilot terms, support process; no unverified legal guarantees | External feedback and acceptance gaps remain |
| **M10 — Commercial release and operations** | P3 · #11 | Verified seller and lawful tax/welfare setup; payment test/refund/webhooks, privacy and terms, security sign-off, support and incident process, monitored stable release | Billing not implemented |

## Execution order and dependencies

1. Complete M1, then M2 and M3 before deploying private organization data.
2. M4 is a hard dependency of M5 shared profiles, M8 private uploads/OAuth and any paid multi-tenant service.
3. M5 and M6 require reviewed primary-source evidence from M2; do not infer obligations from keyword tags.
4. M7 must be tested with actual users before claiming a complete workflow. Accessible source-health UI from M1 is a first increment, not completion of M7.
5. M9 customer validation is allowed as consented discovery/demos; real customer documents and payments require preceding privacy, security and operational gates.
6. M10 only follows verified commercial identity, privacy, security and payment acceptance tests.

## Engineering discipline / release gates

- Modular monolith initially; stable public read-only APIs, no premature microservices or costly hosted infrastructure.
- PRs, branch-based automated Python/Node contract tests and independent browser acceptance before main.
- GitHub Pages currently serves public metadata. No private client data, OAuth tokens or payment credentials in static assets, browser storage or Git history.
- Source metadata changes never equal a verified amendment; RSS disappearance is never repeal. Unreviewed RSS findings cannot silently become legal conclusions.
- Clear status labels: **implemented**, **merged**, **deployed**, **tested externally**, **ready for customer** are separate evidence-backed assertions.
- Maintain the original approved shaded sphere logo and existing functional navigation.
- Post-build verify the public route, API JSON, mobile page, keyboard interactions, source health, failure fallback and citation links.
- Do not claim independently running staff or subagents; GitHub issues assign engineering specialties, not actual people.

## First implementation increment (M1)

The regulatory library reads the already-published `/api/v1/knowledge.json` to display the collector timestamp, curated vs unreviewed record counts, and per-authority collection/cached status. It provides a direct route to inspect the underlying JSON. It labels stale timestamps and network/schema failures rather than presenting an empty or failed feed as current.

This increment exposes existing data; it does not determine legal applicability, offer AI legal advice, prove a new amendment, store private information or create a dynamic API.

## Next implementation PR

M2: validated ELI/CELEX identifiers from exact primary-source documents, provision/evidence records and version provenance. Separate metadata changes from confirmed legal-text amendments, and add offline fixtures before expanding into retrieval and summaries.

## M2 first source-traceability increment

The Regulatory Library cross-references each curated law card with its canonical `act:...` record from the published index, displaying explicit editorial review status and checking that its source URL matches. Where the already curated source is an original EUR-Lex ELI `/oj` link, the user can inspect that exact source. Other initiatives, such as T+1, are described as source-linked guidance rather than a standalone legal instrument. The merged `legalIdentifiers.celexCandidate` metadata from #22 is labelled unverified in the interface.

**Limits:** The UI does not claim a verified current consolidated law, CELEX verification, provision-level content, legal-text version history or amendments. These remain M2 work and independently resolved CELEX identifiers still require verification and review.

## M3 initial release-engineering increment

All static Pages inputs, generated machine feeds, and validated knowledge metadata are assembled by `build_site.py`. PR CI creates a **downloadable preview artifact**, not an independent hosted staging environment. Release files include `/api/v1/build-manifest.json` with source commit, snapshot SHA-256 and file fingerprints. Relative HTML links, exported record totals and known schemas fail the build on inconsistency. The production Pages workflow uses the same builder, with Python and Node checks before upload. See [RELEASE_OPERATIONS.md](RELEASE_OPERATIONS.md) for rollout, verification, rollback procedures and uncompleted gates.

## M4 security foundation (initial increment)

A future server backend now has tested, server-verified-session-dependent authorization helpers, per-request organization membership queries, tenant-scoped record lookups, and compound SQL FKs for reviewer/uploader/connector organization membership. See [TENANT_SECURITY.md](TENANT_SECURITY.md). This code is not deployed as a customer API; no signup, identity provider or private storage yet exists.

## M5 example-profile research lens (initial increment)

The public Regulatory Library offers two **synthetic** illustrative organization profiles and explains why selected curated acts may warrant review. Each profile contains candidate instruments, a research rationale and a verification question linked to the existing source catalogue. These selections are not determinations of applicable law or client obligations; they are not user-supplied organization records, nor saved watchlists. The structured data are published as `data/example_profile_lenses.json`; the view can be disabled without affecting the general catalogue. Real per-organization saved decisions and audited assessments remain blocked on M4.

## M6/M7 source-to-worksheet increment

`research_demo.py` validates the public synthetic organization-lens candidates against canonical curated legal references. It fails closed on missing/duplicate legal acts, mismatched URLs, non-official links, unreviewed records and other malformed input. `build_site.py` emits `data/example_research.json` with explicit **reference-only, provision-unverified, applicability-not-assessed** statuses. Python tests include 30 mutated invalid cases.

The new `research-brief.html` route lets the researcher select a synthetic organization, inspect rationale and unresolved legal questions, follow the exact official source, explicitly mark an item as personally checked, and download a markdown **working worksheet** with citations and review warnings. This is a useful end-to-end demo of discovery → evidence source → question → researcher selection → export.

Remaining: exact provision retrieval and versioned text, verified legal assessment and human approval, tested LLM-assisted drafting/abstention and prompt-injection resilience, authenticated assignments, one-page cross-tool continuity, user usability interviews and browser acceptance. Neither the generator nor the page calls an LLM or claims to issue legal opinions.
