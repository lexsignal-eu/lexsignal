# LexSignal release operations — M3 first slice

**Status:** public/static prototype operations. Not a production security or availability certification.

## One release builder

The command below builds the same artifact locally, in a pull-request preview and in the GitHub Pages publication job:

    python build_site.py --out /tmp/lexsignal-preview --revision <commit-sha>

The output directory must be empty. The builder only reads the checked-out public repository and makes **no network requests**. It copies the approved pages and assets, generates the read-only agent feeds and knowledge index from the committed snapshot, and checks internal HTML link targets, provenance schemas and record totals.

The generated /api/v1/build-manifest.json contains:
- input code revision supplied to the build;
- source snapshot UTC timestamp and SHA-256 digest;
- each included file's SHA-256 digest (excluding the manifest itself);
- public counts of canonical entities and number of internal links checked.

The manifest is a content-integrity and reproducibility tool, **not** a digital signature, deployment attestation, monitoring SLA or evidence of legal correctness. Build timestamps are intentionally omitted so identical inputs and revision yield identical bytes.

## Change workflow

1. Start a short-lived feature branch; do not develop directly against production.
2. Open a pull request. Run Python and Node test suites plus the exact release builder.
3. Download the isolated GitHub Actions **lexsignal-pr-preview** artifact if manual UI inspection is needed. It is an artifact, not a hosted staging site; no production customer data are involved.
4. Check schema, source and citation labels, mobile/keyboard navigation and empty/error states in an actual browser. Automated offline checks do not prove the remote regulator links are live, nor that a browser journey works.
5. Merge only passing and reviewed PRs. Verify that the Pages job finishes successfully, then test the public URLs and compare /api/v1/build-manifest.json with the expected revision and snapshot.

## Production publishing behavior

- The existing workflow updates official-source RSS snapshots on weekday schedule and on main-branch pushes.
- Feed acquisition failures can be tolerated only when the existing cached snapshot remains available; **stale data remain labelled as stale**.
- Before Pages upload, Python tests, Node tests and the unified artifact builder must complete successfully; malformed knowledge records, broken local HTML references or missing static assets fail the job.
- Publish remains on GitHub Pages; there is no credentialed production backend or private customer storage.
- GitHub Actions currently has a single publishing workflow and group-level concurrency. Repeated snapshot commits from other features should be checked for races; stronger least-privilege permission pinning and deploy provenance remain subsequent M3 tasks.

## Incident / rollback runbook

1. Confirm the failing Pages deployment, source snapshot timestamp, file manifest and whether it is a code, source-data or upstream outage.
2. If the last deployment is faulty, revert the offending merge commit in a **new, reviewed PR** rather than rewriting Git history.
3. Let CI rebuild the candidate against the current cached snapshot; rerun internal-link and JSON checks.
4. After merging the revert, wait for the new Pages job to complete and verify the public pages and manifest. Check source/caching labels before advising any customer.
5. If a feed fails, preserve the last known snapshot and show the error; do not treat vanished RSS entries as repealed laws.
6. Record a short incident report in GitHub issues. Do not restore obsolete or inaccurate regulatory content by bypassing review gates.

## Remaining M3 gates

Actual independent staging URL, Playwright browser smoke on mobile/desktop, official source reachability checks, dependency/action SHA pinning, change/failure alerting, audited rollback rehearsal and client security review are **not implemented** by this slice. They must be completed before a stable, customer-data-bearing commercial release.
