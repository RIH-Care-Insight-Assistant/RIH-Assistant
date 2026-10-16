-- 0004: incident simulation records (Phase 7). Synthetic, created only by an admin-triggered
-- simulation in a non-production environment.
CREATE TABLE incidents (
    id            TEXT PRIMARY KEY,
    scenario      TEXT NOT NULL,
    category      TEXT NOT NULL,
    severity      TEXT NOT NULL,
    started_at    TEXT NOT NULL,
    ended_at      TEXT NOT NULL,
    detected_by   TEXT NOT NULL,
    outcome       TEXT NOT NULL,
    record_json   TEXT NOT NULL,
    created_by    TEXT NOT NULL
);
