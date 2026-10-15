-- 0001: anonymous owners, sessions, messages, feedback (contract C2-local-v1 §4).
CREATE TABLE owners (
    id              TEXT PRIMARY KEY,
    credential_hash TEXT NOT NULL UNIQUE,
    created_at      TEXT NOT NULL,
    expires_at      TEXT NOT NULL
);

CREATE TABLE sessions (
    id         TEXT PRIMARY KEY,
    owner_id   TEXT NOT NULL REFERENCES owners(id) ON DELETE CASCADE,
    title      TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX idx_sessions_owner ON sessions(owner_id, updated_at);

CREATE TABLE messages (
    seq                INTEGER PRIMARY KEY AUTOINCREMENT,
    id                 TEXT NOT NULL UNIQUE,
    session_id         TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role               TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    text               TEXT NOT NULL,
    citations_json     TEXT NOT NULL DEFAULT '[]',
    safety_lane        TEXT CHECK (safety_lane IS NULL OR safety_lane IN ('urgent_safety', 'title_ix', 'harassment_hate')),
    response_type      TEXT,
    clarification_json TEXT,
    created_at         TEXT NOT NULL
);
CREATE INDEX idx_messages_session ON messages(session_id, seq);

CREATE TABLE feedback (
    id         TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id TEXT NOT NULL UNIQUE REFERENCES messages(id) ON DELETE CASCADE,
    rating     TEXT NOT NULL CHECK (rating IN ('helpful', 'not_helpful')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
