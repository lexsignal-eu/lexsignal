# LexSignal — M10 Billing Integration Gate (test mode only)

**Status:** FUTURE BACKEND TEST COMPONENT. No Stripe seller account, checkout, subscriptions or endpoint is activated.

Official Stripe implementation guidance: https://docs.stripe.com/events/manage-webhook-endpoints and https://docs.stripe.com/payments/existing-customers

## Implemented in repository

`backend/payment_webhook.py` verifies the raw snapshot event body's `Stripe-Signature` timestamp and v1 HMAC with constant-time comparison, 300-second replay tolerance, strict format checks, and **explicitly rejects any live-mode event**. Test-only verified event IDs can be recorded idempotently using the draft `payment_events` SQLite table. This does **not** map events to customers, grant product access, send receipts or process refunds. There is no HTTP route or secret in source control.

## Hard gates before any actual payment

1. Human owner verifies lawful merchant/seller identity and bank account with Stripe. Never assume public GitHub identity is a merchant of record.
2. Confirm Irish self-employment/tax obligations, consumer/business terms, data protection and the user's social-welfare implications with the appropriate authorities, **before** accepting payments.
3. Select exact pilot scope, cancellation/refund policy, invoicing and payment provider with written approval.
4. Implement a private backend with authenticated organization ownership, Stripe test-mode checkout, securely stored environment secrets, least privilege and a signature-verified, raw-body webhook endpoint.
5. Handle multiple event types and out-of-order/duplicate deliveries; map to organization and confirmed purchase; manage subscription, cancellations, prorations, disputes and refunds. Fulfil only from authoritative verified payment state. A redirect/success page is never entitlement proof.
6. Implement durable processing state beyond basic deduplication, transactional entitlements, recovery, retries, status checks and audit events; run test clock cases and refund/subscription end-to-end scenarios.
7. Prepare incident response, data deletion, monitoring and security review. Test all failure paths with sandbox/test events.
8. Have the owner explicitly approve switching to live API keys and production payment collection.

## Explicit exclusions

No payment account was created or accessed, no email was sent, no charge or money transfer occurred, and no public checkout was added. The example `whsec_` string in tests is a synthetic unit-test secret with no Stripe account association.
