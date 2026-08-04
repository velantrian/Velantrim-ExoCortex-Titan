-- migrations/022_projection_dispatch_state.sql
-- Bounded local projection dispatcher: mutable dispatch-state sidecar
-- (issue #193, ADR-2026-08-04-bounded-local-projection-dispatcher.md).
--
-- Deliberately separate from the two tables it never rewrites:
-- projection_outbox (migration 020) is immutable intent; projection_checkpoints
-- (migration 021) is a version-monotonic record of what has actually been
-- derived from Canon. This table records ONLY where one outbox intent
-- currently stands in the claim/lease/retry/ack state machine — absence of
-- a row means pending/unclaimed. Content-minimized: no claim, source, Canon
-- payload, evidence, user identity, tenant identity, arbitrary JSON, stack
-- trace, or raw exception text — only a closed allowlisted error code.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projection_dispatch_state (
    outbox_id         TEXT PRIMARY KEY
        REFERENCES projection_outbox(outbox_id),
    aggregate_id      TEXT NOT NULL,
    lifecycle_state   TEXT NOT NULL
        CHECK (lifecycle_state IN ('leased', 'retry', 'acknowledged', 'parked')),
    lease_token       TEXT NULL,
    lease_expires_at  TEXT NULL,
    attempt_count     INTEGER NOT NULL DEFAULT 0
        CHECK (attempt_count >= 0),
    next_attempt_at   TEXT NULL,
    last_error_code   TEXT NULL
        CHECK (
            last_error_code IS NULL
            OR last_error_code IN (
                'FTS_UNAVAILABLE',
                'UNSUPPORTED_POLICY_TARGET',
                'CANON_VERSION_BEHIND_INTENT',
                'INTERNAL_CONTRACT',
                'SQLITE_BUSY',
                'SQLITE_TRANSIENT'
            )
        ),
    updated_at        TEXT NOT NULL,
    acknowledged_at   TEXT NULL,
    CHECK (
        (lifecycle_state = 'leased' AND lease_token IS NOT NULL AND lease_expires_at IS NOT NULL)
        OR (lifecycle_state != 'leased' AND lease_token IS NULL AND lease_expires_at IS NULL)
    ),
    CHECK (
        (lifecycle_state = 'acknowledged' AND acknowledged_at IS NOT NULL)
        OR (lifecycle_state != 'acknowledged' AND acknowledged_at IS NULL)
    ),
    CHECK (
        (lifecycle_state = 'retry' AND next_attempt_at IS NOT NULL)
        OR (lifecycle_state != 'retry' AND next_attempt_at IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_projection_dispatch_state_aggregate
    ON projection_dispatch_state(aggregate_id);
