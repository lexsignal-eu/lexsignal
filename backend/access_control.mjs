/**
 * M4: authorization boundary for a future authenticated D1 service.
 * This module DOES NOT authenticate HTTP requests or expose an endpoint.
 * Callers must supply a session verified by a trusted server-side identity
 * provider; never trust client JSON, headers or user-supplied roles.
 */
const PERMISSIONS = Object.freeze({
  'research:read': ['reader', 'analyst', 'admin'],
  'review:write': ['analyst', 'admin'],
  'document:write': ['analyst', 'admin'],
  'organization:manage': ['admin'],
  'connector:manage': ['admin'],
  'billing:manage': ['admin']
});
const TENANT_TABLES = Object.freeze({
  review_decisions: 'research:read',
  stored_documents: 'research:read',
  connector_accounts: 'connector:manage'
});
export class AccessError extends Error {
  constructor(status, code) {
    super(code);
    this.name = 'AccessError';
    this.status = status;
    this.code = code;
  }
}
function safeId(value) {
  return typeof value === 'string' && value.length > 0 && value.length <= 192 &&
    value.trim() === value && /^[a-zA-Z0-9:_-]+$/.test(value);
}
function requireDatabase(db) {
  if (!db || typeof db.prepare !== 'function') {
    throw new Error('Trusted database binding is required');
  }
}
export async function requireOrganizationAccess(db, trustedSession, organizationId, permission) {
  requireDatabase(db);
  if (!trustedSession || trustedSession.verified !== true || !safeId(trustedSession.userId)) {
    throw new AccessError(401, 'authentication_required');
  }
  if (!safeId(organizationId)) {
    throw new AccessError(400, 'invalid_organization_identifier');
  }
  if (!Object.hasOwn(PERMISSIONS, permission)) {
    throw new Error('Unknown server-side permission');
  }
  const row = await db.prepare(
    'SELECT role FROM memberships WHERE organization_id = ?1 AND user_id = ?2'
  ).bind(organizationId, trustedSession.userId).first();
  // Do not disclose to outsiders whether another organization ID exists.
  if (!row || !['reader', 'analyst', 'admin'].includes(row.role)) {
    throw new AccessError(404, 'organization_not_found');
  }
  if (!PERMISSIONS[permission].includes(row.role)) {
    throw new AccessError(403, 'permission_denied');
  }
  return Object.freeze({
    organizationId,
    actorUserId: trustedSession.userId,
    role: row.role,
    permission
  });
}
export async function requireTenantRecord(db, context, table, recordId) {
  requireDatabase(db);
  if (!Object.hasOwn(TENANT_TABLES, table)) {
    throw new Error('Unapproved tenant-scoped resource type');
  }
  if (!context || !safeId(context.organizationId) || !safeId(context.actorUserId) ||
      context.permission !== TENANT_TABLES[table]) {
    throw new AccessError(403, 'missing_authorized_context');
  }
  if (!safeId(recordId)) {
    throw new AccessError(400, 'invalid_record_identifier');
  }
  // The table name comes only from the hardcoded allowlist. Request IDs are
  // always bound as SQL parameters rather than interpolated.
  const record = await db.prepare(
    'SELECT id, organization_id FROM ' + table + ' WHERE id = ?1 AND organization_id = ?2'
  ).bind(recordId, context.organizationId).first();
  if (!record) {
    throw new AccessError(404, 'record_not_found');
  }
  return Object.freeze({ id: record.id, organizationId: context.organizationId });
}
