# M4 security foundation — tenant authorization contract (NOT deployed)

This is an implementation slice for issue #8. The public LexSignal remains a static GitHub Pages research prototype. No signup, session provider, private API, database instance, document upload service, OAuth connector or billing service has been deployed.

## Authorization boundary

The future server-side service should invoke the functions in backend/access_control.mjs:
- requireOrganizationAccess(database, serverVerifiedSession, organizationId, permission) queries memberships for the current actor and organization on **every request**, enforcing reader/analyst/admin scopes.
- requireTenantRecord(database, context, approvedTable, recordId) checks a record using **both** its identifier and the authorized organization ID.
- Records from another tenant and unknown organizations are indistinguishable to an unauthorised caller (404). Unauthorized roles receive a 403. Missing verified session receives 401.
- Only an internal authenticated service may construct serverVerifiedSession. Do **not** treat its verified flag as authentication if user-controlled data or HTTP headers can set it.
- Authorization context is request-scoped and carries a non-exported module symbol; a caller cannot simply supply a plain object with a fabricated role to a record function.
- Query parameter values are bound in D1-style prepared statements; resource table names come from a fixed internal allowlist, never from request input.

These are library-level controls and tests. They **do not** independently secure any HTTP route, user session, authentication provider, or service deployment.

## SQLite/D1 draft relationships

The draft backend/schema.sql now has compound membership foreign keys for:
- each review decision's reviewer and optional action owner;
- each private document's uploader;
- each connected mail account's actor.

This catches cross-organization assignments independently of route authorization. Foreign keys must be enabled on every database connection. Membership departure requires documented reassignment or deletion of dependent active records. Audit records must retain appropriate historical attribution even after departure, subject to defined retention and GDPR obligations.

## Threat assumptions and missing gates

Required before real customer-data handling:
1. Select and integrate a trusted identity provider; verify signed sessions, expiry, CSRF protections, logout and revocation.
2. Review tenant-scoped list/create/update/delete routes, not only individual read paths. Each operation needs authorization and an organization filter in the same query.
3. Confirm D1 foreign-key and transaction behavior; test migrations on a disposable staging database and plan existing-data migration/recovery.
4. Audit test matrix: horizontal privilege escalation, admin role spoofing, ID enumeration, arbitrary table names, revoked users, cross-tenant file keys, membership removal, concurrent updates and retention/deletion.
5. Enforce secure cookies, anti-CSRF controls, rate limiting, audit logs, incident alerts, encryption at rest/in transit and secret rotation.
6. Verify privacy notices, organizational retention/export/deletion processes and security posture before any real documents or live OAuth tokens enter the service.

All tests in this first slice use **synthetic** users and a disposable in-memory SQLite database or D1-shaped mock. No actual user/customer data, secrets, credentials or paid infrastructure are introduced.

## Release gates

- Python: tests/test_tenant_schema.py verifies composite foreign keys.
- Node: tests/tenant-authorization.test.cjs verifies server-checked roles, forbidden operations, tenant boundaries and context forgery resistance.
- Source changes under backend/** trigger the existing workbench PR checks.
- Production Pages builder uses an explicit static-file allowlist and must not include backend source or schema.
- The merge is a security foundation, not a claim that M4 accounts exist or that the app is ready for customer uploads.
