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
                'UNSUPPORTED_SCOPE',
                'UNSUPPORTED_OPERATION',
                'CANON_VERSION_BEHIND_INTENT',
                'INTERNAL_CONTRACT',
                'SQLITE_BUSY',
                'SQLITE_PERMANENT'
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

-- Review finding, PR #197: without an executable invariant, a
-- raw/malformed write (bypassing claim_batch()'s own controlled
-- INSERT ... SELECT ... FROM projection_outbox) could in principle store
-- an aggregate_id inconsistent with the outbox_id it claims to describe,
-- or reference an outbox_id that does not exist at all — either of which
-- would let a dispatch-state row silently drift from the immutable intent
-- it is supposed to track, and could let it survive an erasure keyed on
-- the wrong aggregate_id. claim_batch()'s own INSERT already cannot
-- produce this (it sources aggregate_id from a SELECT of the very row it
-- references), but these triggers make the invariant true by construction
-- for every write path, not just the one this module currently uses.
CREATE TRIGGER IF NOT EXISTS projection_dispatch_state_aggregate_insert_guard
BEFORE INSERT ON projection_dispatch_state
BEGIN
    SELECT RAISE(ABORT, 'projection_dispatch_state.aggregate_id must match an existing projection_outbox row with the same outbox_id')
    WHERE NOT EXISTS (
        SELECT 1 FROM projection_outbox
        WHERE outbox_id = NEW.outbox_id AND aggregate_id = NEW.aggregate_id
    );
END;

CREATE TRIGGER IF NOT EXISTS projection_dispatch_state_aggregate_update_guard
BEFORE UPDATE ON projection_dispatch_state
BEGIN
    SELECT RAISE(ABORT, 'projection_dispatch_state.aggregate_id must match an existing projection_outbox row with the same outbox_id')
    WHERE NOT EXISTS (
        SELECT 1 FROM projection_outbox
        WHERE outbox_id = NEW.outbox_id AND aggregate_id = NEW.aggregate_id
    );
END;
