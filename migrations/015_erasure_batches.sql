-- migrations/015_erasure_batches.sql
-- FORGET_ALL -> durable, resumable GDPR Art. 17 BATCH erasure saga
-- ==================================================================
-- PROBLEM: core.forgetting.ForgettingEngine.forget_all() (the FORGET_ALL
-- MCP tool) has always been a single, best-effort SQLite transaction: it
-- queries `facts` for a user_id match and deletes every matching row in
-- one pass, with no durable record of WHICH fact_ids it decided to erase
-- before it started deleting. A process crash mid-batch loses that
-- decision entirely — a "resumed" run would just re-query `facts` from
-- scratch, which can legitimately return a DIFFERENT set by then (a
-- concurrently ingested fact for the same user, a fact whose state
-- changed under the filter) and either silently erase the wrong set of
-- facts or claim success over a batch that never actually finished.
--
-- SOLUTION: the same tombstone-vs-attempt-receipt separation P0-B
-- (migrations 013/014, core/erasure_coordinator.py) built for SINGLE-fact
-- erasure, one level up, reusing that same per-fact saga as the unit of
-- work rather than re-implementing deletion:
--
--   erasure_batches is the durable BATCH RECEIPT, written once, BEFORE
--   any deletion is attempted — user_id/reason/actor/force/scope/
--   idempotency_key are fixed at creation and never rewritten.
--
--   erasure_batch_items is the durable SNAPSHOT: one row per fact_id
--   selected by the batch's filter, captured atomically WITH the batch
--   row in the SAME transaction, before any per-fact erasure runs. This
--   is the one and only membership list this batch will ever process —
--   resuming after a crash (or a repeat call with the same
--   idempotency_key) replays exactly these rows and NEVER re-queries
--   `facts` by user_id again. A fact ingested for the same user_id AFTER
--   the snapshot was taken is out of scope for this batch by
--   construction — it needs its own subsequent FORGET_ALL call. This is
--   what makes a batch idempotent and resumable against its ORIGINAL
--   intent, not a moving target.
--
--   erasure_batch_force_receipts is a separate, append-only audit
--   receipt written ONLY when a batch is authorized with force=1 (see
--   core/erasure_batch_coordinator.py's admin-capability + explicit-scope
--   gate) — distinct from the batch row itself so a compliance reviewer
--   can query "every force-authorized batch erasure ever run" without
--   depending on the batch's own, possibly-superseded status.
--
-- idx_erasure_batches_idempotency is a real SQLite UNIQUE constraint
-- (partial, excluding NULL) enforcing "at most one batch per
-- idempotency_key" — the same class of guarantee migrations 013/014 give
-- per-fact_id sagas: a retried call with the same key resumes the
-- existing batch (or returns its already-terminal report) rather than
-- creating a second, diverging snapshot.
--
-- Each erasure_batch_items row is processed by handing its fact_id to
-- core.erasure_coordinator.erase_fact_durable() — the existing,
-- unmodified P0-B saga — so per-fact durability, resumability, residual
-- detection (L0 raw-original) and idempotency are inherited, not
-- re-implemented. The ONE case erase_fact_durable() itself never guards
-- against — a fact whose epistemic_state is 'ImmutableCore' but whose
-- fact_id is NOT a true Ring Zero literal (VALUES_CORE/RING_ZERO) — is
-- never treated as an automatic GDPR exemption here: the batch coordinator
-- flags it CRITICAL_COMPLIANCE_VIOLATION and never lets the batch report
-- success while that item is unresolved. See
-- core/erasure_batch_coordinator.py for the full state machine.

CREATE TABLE IF NOT EXISTS erasure_batches (
    batch_id          TEXT PRIMARY KEY,
    user_id           TEXT NOT NULL,
    reason            TEXT NOT NULL,
    actor             TEXT NOT NULL,
    force             INTEGER NOT NULL DEFAULT 0,
    scope             TEXT,
    idempotency_key   TEXT,
    -- PENDING (snapshot committed, no items processed yet) -> RUNNING ->
    -- COMPLETE | COMPLETE_WITH_RESIDUAL | PARTIAL | FAILED |
    -- CRITICAL_COMPLIANCE_VIOLATION. See
    -- core/erasure_batch_coordinator.py for the full state machine.
    status            TEXT NOT NULL DEFAULT 'PENDING',
    items_total       INTEGER NOT NULL DEFAULT 0,
    error             TEXT,
    snapshot_at       TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
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
