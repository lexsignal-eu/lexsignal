# LexSignal — product infrastructure (design and launch gates)

Status: 9 November 2026. This describes the intended architecture. The public v0.6 app remains on GitHub Pages. Neither live mail OAuth nor real checkout is deployed.

## Product surfaces

- Home: index.html and landing.html (same user-friendly overview).
- Research: workspace.html (official RSS data, evidence, decisions, action register, exports).
- Documents: documents.html (in-memory reading of text-like files, manually saved short entries).
- Agents: agent-access.html plus versioned public JSON data endpoints.

The hosted Pages site is static. Browser-local notes and file-derived research entries are neither synced nor backed up centrally. Uploaded file contents are not transmitted by LexSignal; only short entries deliberately saved by the user persist in localStorage. Unreviewed manual-file entries are excluded from briefs until marked reviewed.

## Proposed next phase: authenticated service

Use a secure API host (for example Cloudflare Workers) with a relational database (D1) and private object storage (R2), or a comparable service stack. Put authentication and organization boundaries in front of every tenant-specific operation. Keep regulator source records shared but user reviews and imported client material tenant-scoped.

A starting SQL model is included in backend/schema.sql. It is a design scaffold, not a deployed database or an authorized data service.

Required deployment tests:
- role-based access for reader, analyst and admin
- organization isolation and checked ownership for every write
- per-user login, session expiry and token revocation
- documented retention, export and deletion
- audit logs and security monitoring
- encryption of connector credentials outside source control
- secrets managed by the platform, never in public HTML or GitHub commits

## Live email connections

### Microsoft 365
Use delegated authorization code flow + PKCE through Microsoft Graph, with a read-only Mail.Read permission if reading is all that is needed. Implement consent, OAuth state/CSRF protection, secure token exchange, refresh/rotation and revoke. Organization-level admin approval might be required.

Reference: https://learn.microsoft.com/graph/auth-v2-user

### Gmail
Use user OAuth with the least-privileged Gmail API scopes. Read-only is a separate scope from sending. Production usage of sensitive or restricted scopes can require Google's app verification and security assessments. Test disconnect and account-level revocation.

Reference: https://developers.google.com/identity/protocols/oauth2/scopes

Start with an explicit folder/search query import. No background mailbox monitoring or automatic sending without a separately approved, well-tested workflow. A pasted or uploaded EML file is not an authorized live mailbox connection.

## Future server file pipeline

- Private, short-lived upload URLs and per-file size caps.
- Virus/MIME checks and safe PDF/DOCX text extraction before optional OCR.
- Explicit processing status and controlled deletion/retention.
- Private originals in R2, derived text with provenance in tenant-scoped storage.
- Avoid sending client documents to third-party AI systems without provider terms and a legal basis for the transfer.
- Treat AI-extracted dates, citations, entities and legal claims as unverified until checked against sources.

## Billing: where EUR 240 would go

EUR 240 was an unapproved pilot price hypothesis. The LexSignal site currently has no active merchant account, checkout, linked payout IBAN, invoice service or paid entitlements. No live pay button should be displayed.

For a first genuine pilot, once the seller's legal identity and business terms are settled:
1. The seller creates/verifies a Stripe account, enters the legal business and a bank account eligible for payouts.
2. The product/service description, duration, refund/cancellation conditions and tax treatment are defined.
3. The seller creates a Stripe-hosted Payment Link or invoice for the agreed pilot.
4. The customer pays on Stripe; the seller sees the payment in Stripe and receives payouts into the connected bank account.
5. Service delivery and any invoice/receipt follow the contract and processor records.

Reference: https://stripe.com/payments/payment-links

Before going live, verify the applicable legal, VAT and invoicing obligations for the actual seller and customers. Do not use the public website to collect card details or hardcode a personal bank account.

For automated subscriptions, use authenticated organization-linked Stripe Checkout, verified webhook signatures and deduplicated processing of subscription, payment success/failure, cancellation and refund events. Never grant account access based on a success-URL redirect. A backend payment handler cannot safely operate as a public GitHub Pages HTML file.

Reference: https://github.com/stripe/ai/blob/main/skills/stripe-best-practices/references/payments.md

## Release sequence

1. v0.6: human-first navigation and local Document Lab. No login required; no billable service.
2. Account, security, tenant storage and documented privacy foundation.
3. A tested single-provider read-only email connector, with consent and disconnect.
4. Secure PDF/DOCX upload/extraction pipeline and evidence/history.
5. Invitation-only pilot with verified seller and hosted payments/invoicing.
6. Organization subscriptions, billing webhook processing and optional agent integrations.

No customer communications or commercial commitments are created by this architecture file.
