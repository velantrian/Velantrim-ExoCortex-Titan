-- migrations/013_erasure_jobs.sql
-- P0-B: Durable erasure saga (GDPR Art. 17, provable + resumable)
-- ==================================================================
-- PROBLEM: a single-transaction erase_fact() cannot honestly prove
-- deletion across three independent SQLite files (main DB, the
-- embeddings DB, the ngram DB) and cannot resume if the process
-- crashes between stores.
--
-- SOLUTION: an `erasure_jobs` row is the durable attempt receipt —
-- written BEFORE any deletion is attempted, one row per erasure
-- request, updated as each step runs. It is NOT the completion
-- tombstone: `erasure_log` (migration-free, see core/memory.py)
-- keeps that role and is only ever written when a job reaches
-- status='COMPLETE'. Conflating the two would let a failed/partial
-- attempt look, from `is_erased()`, like a successful one.
--
-- `erasure_job_steps` records one row per storage backend touched
-- (determine_raw / l1_same_db / embeddings / ngram), each independently
-- PENDING → RUNNING → COMPLETE | FAILED, so a crash between backends
-- leaves an accurate, resumable record of exactly what has and has
-- not been proven deleted.
--
-- SECURITY FIX (post-review): erasure_jobs.fact_id carries a UNIQUE index —
-- there must be exactly one durable erasure saga per fact_id, enforced by
-- a real SQLite constraint (works across processes, not just threads
-- within one), not by application-level check-then-insert timing.
-- core.erasure_coordinator.ErasureCoordinator._get_or_create_job() relies
-- on this: a concurrent caller that loses the create race gets an
-- IntegrityError on its INSERT and adopts the winner's job_id instead of
-- creating a second, diverging job for the same fact.

CREATE TABLE IF NOT EXISTS erasure_jobs (
    job_id        TEXT PRIMARY KEY,
    fact_id       TEXT NOT NULL,
    reason        TEXT NOT NULL,
    actor         TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'PENDING',
    -- residual: 'none' | 'raw_original_present' | 'undetermined' | NULL (not yet checked)
    residual      TEXT,
    content_hash  TEXT,
    error         TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_jobs_fact ON erasure_jobs(fact_id);
CREATE INDEX IF NOT EXISTS idx_erasure_jobs_status ON erasure_jobs(status);

CREATE TABLE IF NOT EXISTS erasure_job_steps (
    step_id       TEXT PRIMARY KEY,
    job_id        TEXT NOT NULL REFERENCES erasure_jobs(job_id),
    step_name     TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'PENDING',
    detail        TEXT,
    started_at    TEXT,
    finished_at   TEXT,
    UNIQUE(job_id, step_name)
);

CREATE INDEX IF NOT EXISTS idx_erasure_job_steps_job ON erasure_job_steps(job_id);

-- ── Проверка после применения ─────────────────────────────────────────────────
-- SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'erasure_job%';
-- Ожидаемые объекты: erasure_jobs, erasure_job_steps
