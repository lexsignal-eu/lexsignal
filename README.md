# LexSignal — EU Regulatory Intelligence (prototype)

Experimental public demonstration of a source-linked EU regulatory monitoring dashboard. Includes a browser-based briefing generator and an RSS collection pipeline.

- Dashboard: [Open after Pages activation](https://yevhennaydenov-lab.github.io/lexsignal/)
- Landing page: [Project overview](https://yevhennaydenov-lab.github.io/lexsignal/landing.html)
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
