-- LexSignal D1/SQLite draft — DO NOT treat as a deployed database.
-- Run after tenant-access and authentication are implemented.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS organizations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS memberships (
  organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK(role IN ('reader','analyst','admin')),
  PRIMARY KEY (organization_id,user_id)
);
CREATE TABLE IF NOT EXISTS regulatory_sources (
  id TEXT PRIMARY KEY,
  authority TEXT NOT NULL,
  source_url TEXT NOT NULL,
  title TEXT NOT NULL,
  published_on TEXT,
  retrieved_at TEXT,
  content_hash TEXT,
  review_status TEXT NOT NULL DEFAULT 'unreviewed'
);
CREATE TABLE IF NOT EXISTS review_decisions (
  id TEXT PRIMARY KEY,
  organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  source_id TEXT NOT NULL REFERENCES regulatory_sources(id),
  reviewer_user_id TEXT NOT NULL REFERENCES users(id),
  inclusion_status TEXT NOT NULL CHECK(inclusion_status IN ('include','exclude','undecided')),
  assessment_status TEXT NOT NULL DEFAULT 'not_assessed',
  next_step TEXT,
  owner_user_id TEXT REFERENCES users(id),
  internal_due_date TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(organization_id,source_id)
);
CREATE INDEX IF NOT EXISTS idx_reviews_tenant ON review_decisions(organization_id,updated_at);
CREATE TABLE IF NOT EXISTS connector_accounts (
  id TEXT PRIMARY KEY,
  organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL CHECK(provider IN ('gmail','microsoft_graph')),
  provider_account_id TEXT NOT NULL,
  granted_scopes TEXT NOT NULL,
  encrypted_tokens TEXT NOT NULL, -- application-layer encrypted; never plaintext
  revoked_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id,provider,provider_account_id)
);
CREATE TABLE IF NOT EXISTS stored_documents (
  id TEXT PRIMARY KEY,
  organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  uploaded_by_user_id TEXT NOT NULL REFERENCES users(id),
  private_object_key TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  content_type TEXT NOT NULL,
  byte_length INTEGER NOT NULL CHECK(byte_length >= 0),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deletion_due_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_documents_tenant ON stored_documents(organization_id,created_at);
CREATE TABLE IF NOT EXISTS billing_accounts (
  organization_id TEXT PRIMARY KEY REFERENCES organizations(id) ON DELETE CASCADE,
  stripe_customer_id TEXT UNIQUE,
  subscription_id TEXT UNIQUE,
  payment_status TEXT NOT NULL DEFAULT 'inactive',
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS payment_events (
  provider TEXT NOT NULL,
  event_id TEXT NOT NULL,
  received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  processed_at TEXT,
  PRIMARY KEY(provider,event_id) -- webhook deduplication
);
CREATE TABLE IF NOT EXISTS audit_entries (
  id TEXT PRIMARY KEY,
  organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  actor_user_id TEXT REFERENCES users(id),
  event_type TEXT NOT NULL,
  subject_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_entries(organization_id,recorded_at);
