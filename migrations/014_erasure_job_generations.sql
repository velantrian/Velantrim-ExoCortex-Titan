-- migrations/014_erasure_job_generations.sql
-- P0-B post-merge hotfix: generation-aware erasure sagas
-- ==================================================================
-- Four findings from post-merge review, all rooted in the same class of
-- bug — trusting a cached/legacy signal about a fact_id's erasure state
-- without re-verifying it against what is CURRENTLY true:
--
-- P1-A (legacy tombstone): erase_fact_durable() treated ANY row in
-- erasure_log as proof of a durable COMPLETE, with no requirement that a
-- corresponding erasure_jobs row exists, or that it itself reached
-- COMPLETE. A tombstone written by the pre-coordinator
-- core.erasure.erase_fact() shim (which never touched embeddings/ngram)
-- made erase_fact_durable() report a false COMPLETE while residual
-- embeddings/ngram entries were never cleaned up.
--
-- P1-B (fact_id reuse): migration 013's UNIQUE(fact_id) index on
-- erasure_jobs allowed exactly ONE erasure job to ever exist for a given
-- fact_id. If that fact_id was later recreated (re-ingested under the
-- same ID) and given new embeddings/ngram entries, erase_fact_durable()
-- found the OLD COMPLETE job and short-circuited, reporting a false
-- COMPLETE without erasing the NEW data — a genuine data-retention
-- violation under GDPR Art. 17.
--
-- This migration fixes both by making erasure_jobs generation-aware:
--
--   generation column: each fact_id can accumulate multiple erasure_jobs
--   rows over time — one per "erase, recreate, erase again" cycle. Prior
--   generations are immutable history, never rewritten.
--
--   idx_erasure_jobs_fact_active: a PARTIAL unique index on fact_id,
--   scoped to non-terminal statuses only (status NOT IN ('COMPLETE',
--   'RESIDUAL_IMMUTABLE_DATA')) — enforces "at most one ACTIVE saga per
--   fact_id at a time" (the same concurrency guarantee migration 013's
--   unconditional index provided), while allowing multiple TERMINAL rows
--   — one per generation — to coexist.
--
--   idx_erasure_jobs_fact_generation: UNIQUE(fact_id, generation) — a
--   data-integrity backstop against two rows ever claiming the same
--   generation number for the same fact_id.
--
-- core.erasure_coordinator.ErasureCoordinator now verifies, before
-- trusting any cached terminal job or tombstone, that the fact row and
-- embeddings/ngram entries have not reappeared since that generation
-- completed (_residual_data_present()); if they have, a NEW generation's
-- job is created and run instead of returning a stale cached report.
--
-- erasure_log also gains a nullable job_id column: write_tombstone()'s
-- idempotency check is now scoped to a specific job_id/generation rather
-- than "any tombstone ever recorded for this fact_id" — a fact_id that is
-- durably re-erased under a NEW generation gets its OWN new tombstone row
-- (its own content_hash/erased_at), instead of being silently skipped
-- because an EARLIER generation's tombstone already exists. Legacy rows
-- (written before this column existed, or by core.forgetting's batch path,
-- or by the pre-coordinator core.erasure.erase_fact() shim) keep
-- job_id = NULL and are never touched or overwritten — erasure_log is
-- still append-only (migration 012's triggers are unaffected) and the
-- full historical audit trail is preserved, exactly as Art. 30 requires.

ALTER TABLE erasure_jobs ADD COLUMN generation INTEGER NOT NULL DEFAULT 1;

DROP INDEX IF EXISTS idx_erasure_jobs_fact;

CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_jobs_fact_active
    ON erasure_jobs(fact_id)
    WHERE status NOT IN ('COMPLETE', 'RESIDUAL_IMMUTABLE_DATA');

CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_jobs_fact_generation
    ON erasure_jobs(fact_id, generation);

ALTER TABLE erasure_log ADD COLUMN job_id TEXT DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_erasure_job ON erasure_log(job_id);

-- ── Проверка после применения ─────────────────────────────────────────────────
-- PRAGMA table_info(erasure_jobs);  -- ожидать колонку generation
-- PRAGMA table_info(erasure_log);   -- ожидать колонку job_id
-- SELECT sql FROM sqlite_master WHERE name IN
--   ('idx_erasure_jobs_fact_active', 'idx_erasure_jobs_fact_generation');
-- Ожидаемые объекты: обе строки присутствуют, idx_erasure_jobs_fact отсутствует.
