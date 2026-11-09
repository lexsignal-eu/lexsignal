# LexSignal — EU Regulatory Intelligence (prototype)

Public research-preview demonstration of a source-linked EU regulatory monitoring dashboard. Includes a browser-based briefing generator and an RSS collection pipeline.

- Dashboard: [Open after Pages activation](https://lexsignal-eu.github.io/lexsignal/)
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
