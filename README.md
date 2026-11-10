# LexSignal — EU Regulatory Intelligence (prototype)

Public research-preview demonstration of a source-linked EU regulatory monitoring dashboard. Includes a browser-based briefing generator and an RSS collection pipeline.

- Product homepage: [LexSignal](https://lexsignal-eu.github.io/lexsignal/)
- Research workspace: [Open workspace](https://lexsignal-eu.github.io/lexsignal/workspace.html)
- Landing page: [Project overview](https://lexsignal-eu.github.io/lexsignal/landing.html)
- Sources: ESMA, EDPB, European Commission and Central Bank of Ireland (official RSS endpoints).
- Automated snapshot: `data/regulatory_snapshot.json` when feed collection succeeds.
- Review: RSS entries are **unreviewed** until manually validated and are excluded from generated client briefs by default.
- Storage: watchlists, manual review status and private notes are stored in your local browser, not shared across users.
- Status: no LLM-generated legal conclusions, authentication, subscription billing or production compliance assurance.

## Deployment
1. Settings → Pages → Build and deployment → Source → **GitHub Actions**.
2. Actions → **Refresh and publish LexSignal** → **Run workflow**.
3. Check action logs and open the Pages URL when it reports success.

Scheduled updates run at approximately 07:17 UTC on weekdays. GitHub may delay scheduled jobs; data availability depends on source feeds. This prototype requires editorial review before any commercial delivery.

## Signal triage (v0.3)
RSS items are automatically labelled high, monitor or background, and an indicative event type is assigned from headline patterns. The Priority signals view shows high-priority matches by default; All updates shows every collected record. These classifications are **unverified**. Client briefs omit unreviewed RSS items and background news.

## Approved visual identity
The official website icon is the **original shaded blue sphere with curved signal bands** chosen during design review. The original raster design was cropped and resized without regenerating or redrawing it. It is distributed as `brand/lexsignal-sphere-approved.webp` and used as the website mark and favicon. Superseded flat golden-ratio vector artwork has been removed from the current source tree.


## Human + Agent interface (v0.4)
The public website includes stable read-only JSON exports suitable for server-side consumers and AI agents:
- `/api/v1/updates.json`: full source-linked auto-collected RSS feed, all records unreviewed.
- `/api/v1/signals.json`: heuristic high-tier items; *not editorial approval*.
- `/api/v1/status.json`: latest snapshot timestamp, source collection status.
- `/api/v1/feed.jsonld`: Schema.org DataFeed JSON-LD.
- `/api/v1/openapi.json`: static OpenAPI 3.1.2 description.
- `/llms.txt` and `/agent-access.html`: human and machine guidance.

These files are generated as part of each GitHub Pages publication by `build_agent_feed.py` from the existing RSS snapshot. No dynamic query API, MCP server, API key, analytics-based SLA or automated verification is claimed. See `docs/AGENT_ACCESS.md`. The approved spherical brand logo is unchanged.

## RSS resilience and provenance
The collector keeps up to 250 previously seen publications for 150 days after publication, including when a source temporarily fails. Every entry reports collectionState (observed/cached), firstSeenAt and lastObservedAt. A cached entry is not proof that its source still lists it. Agent status exports expose per-source cache counts and fetch failures. If all four sources fail, the previous snapshot is left unchanged, including its timestamp; no empty success is manufactured. Such snapshots still require checking against the official source before citation.

## Research workbench update (v0.5)

The dashboard's primary purpose is now to support the cycle **source → assess → reviewer decision → owner/action → briefing**.

- Separate source publication dates from later implementation milestones in the selected research records.
- Add a directly sourced ESMA case for the T+1 conversion and 7 December 2026 preparation requirements, plus an EMIR 3 PTRR final report **awaiting Commission endorsement**.
- Open source-specific ESMA and Irish DPC publications instead of generic news indices for two curated examples.
- Let reviewers override automated screening for a checked RSS publication. The exclusion safeguard for unreviewed RSS is unchanged, and user exclusion always overrides inclusion.
- Track assessment status, responsible person, next step and internal due date in local browser storage; include these in CSV and draft briefing exports.
- Add a documented customer-facing example to the overview.

**Limits:** Review decisions, notes and action assignments are browser-local, not shared across devices or accounts. A manual review flag only records the user's action; it does not certify the legal correctness of the classification. Sourcing remains selective. Outreach is paused while the product is being strengthened.


## Product experience v0.6
The root page is now a human-first product overview, and the prior application moved to workspace.html. A new documents.html Document Lab processes TXT, MD, CSV, JSON, saved EML and HTML in-browser (2 MB limit); users can explicitly save short, unreviewed sourced records to the workspace. Uploaded file contents are not transmitted or stored by LexSignal. Live Gmail/Outlook connections, shared accounts, PDF/DOCX parsing and payments are not yet deployed. A separate secure backend and provider configuration are required. See docs/PRODUCT_INFRASTRUCTURE.md. The approved sphere mark is unchanged.


## Global Signals — interactive map (v0.7)

`/global-signals.html` displays eight source-backed historical AI policy milestones with hover previews, event photos and credits, date/type/search filters, pan and zoom. It uses the public-domain Natural Earth 1:110m land basemap bundled in `geo/ne_110m_land.geojson`. `data/global_signals.json` contains the curated event locations and primary source links, accessible to people and agents. A separate "Latest regulator updates" layer groups the existing read-only RSS feed at publisher office locations; it **does not geolocate the legal impact or assert the physical place of publication**. No paid map API, server credentials or map tile requests. Later work can integrate editor-approved geocoding for individual events.


## Regulatory Library & Calendar (v0.8)

`/regulatory-library.html` contains a small curated, primary-source-linked catalogue of 10 EU legal frameworks/initiatives and 17 significant application, transposition and transition milestones from `data/regulatory_library.json`. Content was researched against the European Commission, ESMA, EUR-Lex and the Central Bank of Ireland on 9 November 2026. The collection is selected, not exhaustive; a date is not automatically an obligation for a specific client. Distinctions include NIS2 national transposition (dated Irish Commission status), 2026 Digital Omnibus amendments to the AI Act, 2026/2027 Cyber Resilience Act phases and T+1 2026 operational vs 2027 transition dates.

Use industry and text filters, bookmark laws locally, show past/upcoming milestones, and download an .ics calendar of the **visible upcoming** milestones. The page also shows six current unreviewed regulatory RSS headlines from the existing `api/v1/updates.json` when available. No login, calendar account permissions or outbound email are required; watchlists use browser-local storage and .ics is explicitly downloaded by the user. Review official source dates before acting.


## P0 canonical knowledge index (first architecture tranche)

The independent module `knowledge_index.py` validates and combines `data/source_registry.json`, `data/regulatory_library.json` and the existing official RSS snapshot. `build_knowledge_index.py` generates a static `/api/v1/knowledge.json` feed with typed authority, legal-instrument, milestone and publication records, explicit grounded relationships, stable metadata fingerprints and timestamp/review provenance. There is no provision-level legal-text parsing yet and no AI-inferred linking.

Run: `python build_knowledge_index.py --out /tmp/knowledge.json`. Optionally compare two generated files with `--previous old.json --changes-out changes.json`; the resulting events describe **metadata differences only**, not real legal amendments or repeal. Python tests validate source domain allowlists, identity uniqueness, valid calendar dates, entity relations and source flags. See `docs/adr/001-knowledge-index.md` and `docs/ENGINEERING_PLAN.md` for the next system stages.


## Source collection transparency (M1 release increment)

The Regulatory Library now reads the existing generated `/api/v1/knowledge.json` index to display per-authority collection success/failure, observed vs cached publication counts and the published UTC snapshot timestamp, with a warning when that snapshot is older than 48 hours. Failures leave an explicit unavailable status; the page does not silently claim that a stale or failed feed is up to date. Records remain unreviewed unless explicitly curated and human checked. The generated source index is publicly inspectable, but it is not a legal-text version or proof of a regulatory obligation.

For the ten-step engineering and commercial release plan, dependencies and acceptance gates, see [docs/RELEASE_MILESTONES.md](docs/RELEASE_MILESTONES.md). M1–M10 are newly defined release milestones mapped to the existing P0–P3 engineering programme. A milestone is not complete until its acceptance criteria have been tested; a merged PR alone does not imply a customer-ready product.


## Legal source traceability (M2 UI increment)

The Regulatory Library now joins cards to the canonical `act:...` records from the knowledge index and surfaces their curated reference status and exact ELI original Official Journal URL when matched. An initiative such as T+1 is shown as guidance-only. If the independently pending source-identifier work in draft PR #22 is merged, any mechanically derived CELEX candidate will be explicitly labelled unverified. No consolidated law, provision citations, legal-text versions or amendment detection are claimed.


## Release artifact verification (M3 first increment)

`python build_site.py --out /tmp/lexsignal-preview --revision YOUR_COMMIT_SHA` builds the public site and generated API data with an integrity manifest at `/api/v1/build-manifest.json`. Pull requests run the same builder and upload an isolated, downloadable preview artifact; Pages publication requires Python and Node tests plus the offline link, schema and provenance checks. The preview is **not a hosted staging environment**. Remote browser acceptance, alerts and rollback rehearsal remain pending. See `docs/RELEASE_OPERATIONS.md`.


## M4 tenant security foundation (no login deployment)

A standalone backend authorization contract checks database membership for every organizational action, enforces reader/analyst/admin policy and tenant-scoped queries, and rejects context forgery. Draft SQLite/D1 schema has tenant membership foreign keys for reviewers, document uploaders and mail connector owners. These are **offline tests and source files only**: the public website has no accounts, private API or customer storage. See `docs/TENANT_SECURITY.md`.


## M5 illustrative organization lens

The Regulatory Library now offers **synthetic** example profiles, initially an Irish payment institution and an EU AI-enabled SaaS provider. Selecting a profile narrows the curated legal catalogue and attaches research rationales and unanswered verification questions to the displayed acts. Data are static, published in `data/example_profile_lenses.json`; no user or client profile data are collected and no legal applicability is asserted. Real tenant-scoped personalized watchlists require M4 authentication and storage.

## Source-linked example research worksheet (M6/M7 initial increment)

`/research-brief.html` is a public, no-login research demonstration using the existing **synthetic** organization profiles. Its example JSON is compiled at build time by `research_demo.py`, which requires matching canonical sources and preserves unverified applicability. The user may inspect official citations and open questions, manually select records after checking sources, then download a markdown **research worksheet**. No client data are submitted or stored, and no AI legal conclusions or automatically verified obligations are generated. This is not the finished AI research engine or an authenticated customer workflow; see `docs/RELEASE_MILESTONES.md`.

## M8 future document backend (not deployed)

`backend/document_extract.py` contains a bounded in-memory DOCX-only text extraction library with paragraph evidence ordinals, ZIP/macro/entity safety checks and SHA-256 digest for future authenticated services. No server upload endpoint, private data storage, PDF parsing or Gmail/Microsoft OAuth is deployed. See `docs/DOCUMENT_PIPELINE.md`.

## Pilot acceptance and future billing gates (M9/M10)

`docs/PILOT_ACCEPTANCE.md` defines a consent-based 3–5-user synthetic pilot protocol and acceptance criteria, **not actual pilot results**. `backend/payment_webhook.py` verifies Stripe-style raw-body signatures and records test event IDs idempotently in SQLite, but explicitly refuses live-mode events. There is no merchant account, publicly deployed endpoint, checkout, subscription or customer charge. See `docs/BILLING_REVIEW.md`.
