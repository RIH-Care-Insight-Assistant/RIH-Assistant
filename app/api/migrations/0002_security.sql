-- 0002: staff accounts and sessions, policy decision audit, source reviews,
-- ingestion staging and server-side settings (contract C3-local-v1).
CREATE TABLE users (
    id              TEXT PRIMARY KEY,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    roles           TEXT NOT NULL,
    disabled        INTEGER NOT NULL DEFAULT 0,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until    TEXT,
    created_at      TEXT NOT NULL,
    created_by      TEXT
);

CREATE TABLE staff_sessions (
    id          TEXT PRIMARY KEY,
    token_hash  TEXT NOT NULL UNIQUE,
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL,
    last_seen   TEXT NOT NULL,
    expires_at  TEXT NOT NULL
);
CREATE INDEX idx_staff_sessions_user ON staff_sessions(user_id);

CREATE TABLE audit_events (
    seq            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts             TEXT NOT NULL,
    request_id     TEXT,
    category       TEXT NOT NULL,
    principal_hash TEXT,
    roles          TEXT,
    action         TEXT,
    resource       TEXT,
    via            TEXT,
    allowed        INTEGER,
    rule_id        TEXT,
    policy_version TEXT,
    detail         TEXT
);
CREATE INDEX idx_audit_ts ON audit_events(ts);

CREATE TABLE source_reviews (
    seq            INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id       TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    status         TEXT NOT NULL CHECK (status IN ('approved', 'pending', 'rejected', 'retired')),
    reviewer       TEXT NOT NULL,
    note           TEXT,
    decided_at     TEXT NOT NULL
);
CREATE INDEX idx_source_reviews_chunk ON source_reviews(chunk_id, seq);

CREATE TABLE ingested_sources (
    chunk_id       TEXT PRIMARY KEY,
    url            TEXT NOT NULL,
    title          TEXT NOT NULL,
    category       TEXT NOT NULL,
    text           TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    updated_on     TEXT,
    fetched_at     TEXT NOT NULL,
    fetched_by     TEXT NOT NULL,
    signals        TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE app_settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
