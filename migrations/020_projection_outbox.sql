-- migrations/020_projection_outbox.sql
-- Transactional projection-outbox foundation.
--
-- This table stores only immutable technical routing intent. It deliberately
-- contains no claim, justification, evidence body, model output, retry state,
-- lease, dispatcher acknowledgement or remote transport data.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projection_outbox (
    outbox_id          TEXT PRIMARY KEY,
    aggregate_type     TEXT NOT NULL
        CHECK (aggregate_type = 'fact'),
    aggregate_id       TEXT NOT NULL,
    scope_ref          TEXT NOT NULL,
    projection_kind    TEXT NOT NULL
        CHECK (projection_kind IN ('all', 'fts', 'graph', 'vector')),
    operation          TEXT NOT NULL
        CHECK (operation IN ('refresh', 'remove')),
    canonical_version  INTEGER NOT NULL
        CHECK (canonical_version >= 0),
    policy_version     TEXT NOT NULL,
    created_at         TEXT NOT NULL,
    UNIQUE (
        aggregate_type,
        aggregate_id,
        scope_ref,
        projection_kind,
        operation,
        canonical_version,
        policy_version
    )
);

CREATE INDEX IF NOT EXISTS idx_projection_outbox_created
    ON projection_outbox(created_at, outbox_id);
CREATE INDEX IF NOT EXISTS idx_projection_outbox_aggregate
    ON projection_outbox(aggregate_type, aggregate_id, canonical_version);
