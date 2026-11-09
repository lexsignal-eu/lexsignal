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
