-- migrations/019_suggested_edges.sql
-- EdgeSuggester HITL (Crystal RFC0063 I64): предлагает рёбра, не пишет в relations сам.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS suggested_edges (
    suggestion_id     TEXT PRIMARY KEY,
    from_fact_id      TEXT NOT NULL,
    to_fact_id        TEXT NOT NULL,
    relation_type     TEXT NOT NULL DEFAULT 'analogous_to',
    score             REAL NOT NULL DEFAULT 0.0,
    reason            TEXT NOT NULL DEFAULT '',
    evidence_json     TEXT NOT NULL DEFAULT '{}',
    status            TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at       TEXT,
    resolved_by       TEXT,
    relation_id       TEXT,
    CHECK (from_fact_id != to_fact_id)
);

CREATE INDEX IF NOT EXISTS idx_suggested_edges_status
    ON suggested_edges(status, created_at);
CREATE INDEX IF NOT EXISTS idx_suggested_edges_pair
    ON suggested_edges(from_fact_id, to_fact_id, relation_type);
