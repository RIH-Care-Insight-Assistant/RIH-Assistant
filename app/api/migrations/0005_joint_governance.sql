-- 0005: joint governance decisions (L-D13). Decisions are attributed to the staff account id,
-- so a deleted and recreated username never inherits earlier decisions. Rows written before this
-- migration have no account id and therefore never count toward a joint decision.
ALTER TABLE risk_reviews ADD COLUMN reviewer_id TEXT;
ALTER TABLE release_decisions ADD COLUMN decided_by_id TEXT;
ALTER TABLE release_decisions ADD COLUMN reviewer_slot TEXT;
