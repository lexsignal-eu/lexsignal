# LexSignal: Access for AI Agents and Developers

LexSignal is an experimental regulatory intelligence website, with human-readable pages and public, **read-only static** data exports. These are publication snapshots, not a live query service. Clients perform their own filtering, aggregation, and source verification.

Base URL: https://lexsignal-eu.github.io/lexsignal/

## Endpoints
- [All unreviewed updates](https://lexsignal-eu.github.io/lexsignal/api/v1/updates.json) — compact JSON entries with title, publication date, authority, source URL, sectors, heuristic signal tier and explicit review flags.
- [Automated priority matches](https://lexsignal-eu.github.io/lexsignal/api/v1/signals.json) — subset marked high by keyword rules. *High does not mean verified or legally important.*
- [Feed status](https://lexsignal-eu.github.io/lexsignal/api/v1/status.json) — source availability and timestamp of the snapshot.
- [Schema.org feed](https://lexsignal-eu.github.io/lexsignal/api/v1/feed.jsonld) — JSON-LD representation.
- [OpenAPI specification](https://lexsignal-eu.github.io/lexsignal/api/v1/openapi.json) — machine-readable endpoint description.
- [Original official RSS snapshot](https://lexsignal-eu.github.io/lexsignal/data/regulatory_snapshot.json) — internal RSS-derived data model, less stable than the v1 exports.

## Interpretation of the fields
- `reviewStatus: "unreviewed"`: no editorial check has been made on the item.
- `relevanceMethod: "automated_keyword_screening"`: preliminary classification, not a legal conclusion.
- `applicabilityAssessment: "not_performed"`: no client-specific assessment.
- `snapshotGeneratedAt`: timestamp of the upstream RSS snapshot; not a promise of current-day coverage.
- `sourceUrl`: primary publication link; agents should open it for verification.
- `signalTier`: `high`, `monitor` or `background` according to imperfect heuristic rules.

## Agent usage
1. Fetch `status.json` and inspect the snapshot timestamp.
2. Fetch `updates.json` once and filter locally by `sectors`, `authority`, `signalTier` or `publishedOn`.
3. Select potentially relevant source links; inspect and verify primary publications directly.
4. Explicitly distinguish preliminary publication summaries from enacted law, draft guidance, speeches and enforcement actions.
5. Do not cite LexSignal's auto-triage as a verified compliance finding.

Example with curl and jq (runs on the agent/developer's own machine):

```bash
curl -fsSL https://lexsignal-eu.github.io/lexsignal/api/v1/updates.json |
  jq '.items[] | select(.authority == "ESMA") | {title,publishedOn,sourceUrl,reviewStatus}'
```

## Operational limitations
- Static GitHub Pages; no parameterised server-side filtering, streaming, dedicated backend, API key, SLA, account system, paid subscription or interactive agent tools.
- CORS headers are not managed by this deployment, so browser-based cross-origin `fetch()` clients may need a backend or a different host. Server-to-server HTTP GET is the intended initial access path.
- Not a formally implemented Model Context Protocol (MCP) server.
- `llms.txt` is an emerging site guidance convention, not a guarantee that specific AI crawlers read or obey it.
- Short automated excerpts may be derived from third-party regulator RSS publications; retain the link, attribution and respect each publisher's reuse terms.
- This site is independent of the authorities linked. Their appearance as sources is not an endorsement.
