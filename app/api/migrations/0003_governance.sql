-- 0003: human governance records (contract C4-local-v1). Rows are written only through
-- role-checked staff routes; nothing is pre-filled.
CREATE TABLE risk_reviews (
    seq              INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_id          TEXT NOT NULL,
    register_version TEXT NOT NULL,
    decision         TEXT NOT NULL CHECK (decision IN ('accept_residual', 'require_mitigation', 'confirm_assessment', 'reopen')),
    rationale        TEXT NOT NULL,
    reviewer         TEXT NOT NULL,
    reviewer_roles   TEXT NOT NULL,
    decided_at       TEXT NOT NULL
);
CREATE INDEX idx_risk_reviews_risk ON risk_reviews(risk_id, seq);

CREATE TABLE release_decisions (
    seq             INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate       TEXT NOT NULL,
    readiness       TEXT NOT NULL,
    snapshot_sha256 TEXT NOT NULL,
    decision        TEXT NOT NULL CHECK (decision IN ('approve', 'reject', 'defer')),
    rationale       TEXT NOT NULL,
    decided_by      TEXT NOT NULL,
    decided_at      TEXT NOT NULL
);
