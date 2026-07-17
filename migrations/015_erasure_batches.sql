-- migrations/015_erasure_batches.sql
-- FORGET_ALL -> durable, resumable GDPR Art. 17 BATCH erasure saga
-- ==================================================================
-- PROBLEM: core.forgetting.ForgettingEngine.forget_all() (the FORGET_ALL
-- MCP tool) has always been a single, best-effort SQLite transaction: it
-- queries `facts` for a user_id match and deletes every matching row in
-- one pass, with no durable record of WHICH fact_ids it decided to erase
-- before it started deleting. A process crash mid-batch loses that
-- decision entirely — a "resumed" run would just re-query `facts` from
-- scratch, which can now legitimately return a DIFFERENT set by then (a
-- concurrently ingested fact for the same user, a fact whose state
-- changed under the filter) and either silently erase the wrong set of
-- facts or claim success over a batch that never actually finished.
--
-- SOLUTION: the same tombstone-vs-attempt-receipt separation P0-B
-- (migrations 013/014, core/erasure_coordinator.py) built for SINGLE-fact
-- erasure, one level up, reusing that same per-fact saga as the unit of
-- work rather than re-implementing deletion. See
-- core/erasure_batch_coordinator.py for the full design rationale and
-- state machine — summary of what each column is for below.
--
-- erasure_batches — the durable BATCH RECEIPT, written once, in the SAME
-- transaction as the SELECT that produces its membership (see
-- erasure_batch_items below) and BEFORE any deletion is attempted:
--   - request_fingerprint: canonical hash of (user_id, reason, actor,
--     force, scope) — idx_erasure_batches_idempotency guarantees at most
--     one batch per idempotency_key, but a reused key with a DIFFERENT
--     fingerprint must be refused (IDEMPOTENCY_CONFLICT), never silently
--     resumed/revealed as if it were the same logical request.
--   - status: the EXECUTION status (PENDING/RUNNING/PARTIAL/FAILED/
--     COMPLETE/COMPLETE_WITH_RESIDUAL) — purely "is there more work to
--     do", independent of...
--   - compliance_status: a SEPARATE, sticky flag (NULL or
--     'CRITICAL_COMPLIANCE_VIOLATION') set the moment a personal fact is
--     found inside ImmutableCore. A batch with retryable items left must
--     stay resumable regardless of this flag, and this flag must never
--     silently clear once set — these are two independent concerns, not
--     one overloaded status value.
--   - snapshot_hash: sha256 over the ordered (fact_id, epistemic_state)
--     pairs captured at snapshot time — recomputed and checked against
--     the CURRENT erasure_batch_items rows before every processing pass;
--     a mismatch fails the batch closed (FAILED) rather than silently
--     processing a membership list that may have been tampered with or
--     corrupted out-of-band.
--   - runner_id / lease_expires_at: real lease-based ownership for
--     crash-recovery reclaim. A RUNNING batch is only ever reclaimed by
--     resume_incomplete_batches() once its OWN lease has expired — never
--     via a bare "status='RUNNING' -> status='RUNNING'" write, which
--     would let two concurrent recovery workers (or a recovery worker
--     racing a still-alive live runner) both believe they won the claim.
--     A live runner renews its own lease after every processed item.
--
-- erasure_batch_items — the durable SNAPSHOT: one row per fact_id
-- selected by the batch's filter, captured atomically WITH the batch row
-- (same transaction, same connection — see
-- BatchErasureCoordinator._create_batch_snapshot()). This is the one and
-- only membership list this batch will ever process — resuming after a
-- crash (or a repeat call with the same idempotency_key + fingerprint)
-- replays exactly these rows and NEVER re-queries `facts` by user_id
-- again. A fact ingested for the same user_id AFTER the snapshot was
-- taken is out of scope for this batch by construction.
--
-- erasure_batch_force_receipts — a separate, append-only audit receipt
-- written ONLY when a batch is authorized with force=1 (admin capability
-- + explicit scope, enforced in core/erasure_batch_coordinator.py) —
-- distinct from the batch row itself so a compliance reviewer can query
-- "every force-authorized batch erasure ever run" without depending on
-- the batch's own, possibly-superseded status.
--
-- Both erasure_batch_items and erasure_batch_force_receipts declare a
-- REFERENCES erasure_batches(batch_id) foreign key — enforced only when
-- the connection has run `PRAGMA foreign_keys = ON` (SQLite default is
-- OFF; core.erasure_batch_coordinator's own connections always enable
-- it), which rejects an orphan item/receipt row referencing a
-- nonexistent batch_id outright, rather than silently accepting it.
--
-- Each erasure_batch_items row is processed by handing its fact_id to the
-- existing, unmodified core.erasure_coordinator.erase_fact_durable() — a
-- fact matched by the user filter whose epistemic_state is
-- 'ImmutableCore' (but is NOT a true Ring Zero literal) is never treated
-- as an automatic exemption; it is flagged compliance_status =
-- 'CRITICAL_COMPLIANCE_VIOLATION' instead.

CREATE TABLE IF NOT EXISTS erasure_batches (
    batch_id            TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    reason              TEXT NOT NULL,
    actor               TEXT NOT NULL,
    force               INTEGER NOT NULL DEFAULT 0,
    scope               TEXT,
    idempotency_key     TEXT,
    request_fingerprint TEXT NOT NULL,
    -- status: PENDING (snapshot committed, no items processed yet) ->
    -- RUNNING -> COMPLETE | COMPLETE_WITH_RESIDUAL | PARTIAL | FAILED.
    -- See core/erasure_batch_coordinator.py for the full state machine.
    status              TEXT NOT NULL DEFAULT 'PENDING',
    -- compliance_status: NULL | 'CRITICAL_COMPLIANCE_VIOLATION' — a
    -- SEPARATE, sticky flag, independent of `status` (see rationale above).
    compliance_status   TEXT,
    items_total         INTEGER NOT NULL DEFAULT 0,
    snapshot_hash        TEXT NOT NULL,
    runner_id           TEXT,
    lease_expires_at    TEXT,
    error               TEXT,
    snapshot_at         TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_batches_idempotency
    ON erasure_batches(idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_erasure_batches_status ON erasure_batches(status);
CREATE INDEX IF NOT EXISTS idx_erasure_batches_user ON erasure_batches(user_id);

CREATE TABLE IF NOT EXISTS erasure_batch_items (
    item_id                       TEXT PRIMARY KEY,
    batch_id                      TEXT NOT NULL REFERENCES erasure_batches(batch_id),
    fact_id                       TEXT NOT NULL,
    epistemic_state_at_snapshot   TEXT NOT NULL,
    -- PENDING -> COMPLETE | RESIDUAL_IMMUTABLE_DATA | NOT_FOUND |
    -- CRITICAL_COMPLIANCE_VIOLATION | SKIPPED_RING_ZERO | PARTIAL | FAILED
    status                        TEXT NOT NULL DEFAULT 'PENDING',
    job_id                        TEXT,
    detail                        TEXT,
    created_at                    TEXT NOT NULL,
    updated_at                    TEXT NOT NULL,
    UNIQUE(batch_id, fact_id)
);

CREATE INDEX IF NOT EXISTS idx_erasure_batch_items_batch ON erasure_batch_items(batch_id);
CREATE INDEX IF NOT EXISTS idx_erasure_batch_items_status ON erasure_batch_items(batch_id, status);

CREATE TABLE IF NOT EXISTS erasure_batch_force_receipts (
    receipt_id       TEXT PRIMARY KEY,
    batch_id         TEXT NOT NULL REFERENCES erasure_batches(batch_id),
    actor            TEXT NOT NULL,
    actor_capability TEXT NOT NULL,
    scope            TEXT NOT NULL,
    user_id          TEXT NOT NULL,
    reason           TEXT NOT NULL,
    authorized_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_erasure_batch_force_receipts_batch
    ON erasure_batch_force_receipts(batch_id);

-- ── Проверка после применения ─────────────────────────────────────────────────
-- SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'erasure_batch%';
-- Ожидаемые объекты: erasure_batches, erasure_batch_items, erasure_batch_force_receipts
-- PRAGMA table_info(erasure_batches);  -- ожидать request_fingerprint, compliance_status,
--                                      -- snapshot_hash, runner_id, lease_expires_at
