-- migrations/016_erasure_job_subject.sql
-- Round 5 Codex finding (P2): preserve the data-subject user_id in erasure
-- tombstones, separately from the operator/credential fingerprint.
-- ==================================================================
-- PROBLEM: BatchErasureCoordinator._process_item() called
-- core.erasure_coordinator.erase_fact_durable(fact_id, reason=batch["reason"],
-- actor=batch["actor"]) — `batch["actor"]` is the operator/API credential
-- fingerprint that authorized the FORGET_ALL batch, not the person whose
-- data is being erased. ErasureCoordinator._finalize() passed that same
-- `actor` value straight into SQLiteGraphStore.write_tombstone(), which
-- stores it in erasure_log.user_id. An erasure for user_id="userA" run by
-- actor="api:deadbeef" therefore created a tombstone keyed to
-- "api:deadbeef" — ForgettingEngine.get_erasure_log(user_id="userA") (and
-- any other user-scoped GDPR Art. 17/Art. 30 audit query) found no record,
-- even though userA's data really was erased. A real audit-trail defect.
--
-- SOLUTION: erasure_jobs gains a nullable `subject_user_id` column —
-- separate from the existing `actor` column (which keeps recording the
-- operator/credential fingerprint; operator provenance is never lost).
-- core.erasure_coordinator.erase_fact_durable() accepts an explicit
-- `subject_user_id` keyword argument and stores it durably on the job row
-- (survives crashes/retries/resume — a resumed erasure reads the SAME
-- row and therefore produces the SAME subject-scoped tombstone as the
-- original attempt). _finalize() now writes the completion tombstone with
-- `actor=job["subject_user_id"] or job["actor"]` — i.e. erasure_log.user_id
-- is the real data subject when one was provided, falling back to the
-- historical `actor` behavior for every legacy caller that doesn't provide
-- one (core.erasure.erase_fact()'s deprecated shim, the `forget_fact` MCP
-- tool — both remain fully backward-compatible, unchanged output).
-- BatchErasureCoordinator._process_item() is the one caller updated to
-- pass both explicitly: actor=batch["actor"], subject_user_id=batch["user_id"].
--
-- This is a single-fact-job-scoped column (erasure_jobs, migrations
-- 013/014), not a batch-scoped one — migrations/015_erasure_batches.sql
-- (erasure_batches/erasure_batch_items/erasure_batch_force_receipts) is a
-- different table family, extended below only by the read-only backfill
-- join.
--
-- Mirrors migration 014's own pattern: core.erasure_coordinator.
-- ErasureCoordinator._ensure_schema() can self-heal this column onto an
-- existing DB at runtime (same ALTER, guarded the same way) before an
-- operator ever runs this migration script — scripts/apply_migrations.py
-- detects that via column_exists() and skips the (non-idempotent) ALTER
-- in that case, exactly like it already does for erasure_jobs.generation.
-- Skipping that one ALTER statement must never skip the rest of this
-- migration (the backfill/correction phase below) — see the self-heal
-- filtering in scripts/apply_migrations.py.
--
-- ==================================================================
-- Round 5.2 Codex finding (P2): the fix above only prevents the defect
-- going forward. A deployment already running v15 may already hold
-- COMPLETED FORGET_ALL batches whose erasure_log tombstones were written
-- with user_id = operator fingerprint instead of the batch's actual data
-- subject (erasure_batches.user_id) — those historical rows are wrong
-- RIGHT NOW and stay silently undiscoverable via
-- get_erasure_log(user_id=<real subject>) forever unless corrected.
--
-- STRATEGY: erasure_log carries genuine append-only enforcement
-- (migration 012's prevent_erasure_delete/prevent_erasure_update triggers,
-- BEFORE DELETE/UPDATE ... RAISE(ABORT) — inspected before choosing this
-- approach). Rather than UPDATE historical erasure_log rows in place
-- (which would require dropping and re-installing those triggers inside
-- this migration, and would destroy the ORIGINAL recorded evidence), this
-- migration adds a separate, ALSO append-only correction table —
-- erasure_log_subject_corrections — keyed to the specific erasure_log row
-- being corrected. erasure_audit (the view GDPR audit queries actually
-- read — see core/forgetting.py's get_erasure_log()) is redefined to
-- resolve the EFFECTIVE user_id through this correction when one exists,
-- via COALESCE — so get_erasure_log(user_id="userA") now finds these
-- historical batch erasures, while the ORIGINAL erasure_log.user_id value
-- (the operator fingerprint that was actually recorded at the time)
-- remains untouched, immutable history, forever.
--
-- LINKAGE (provable only, never inferred from actor strings): a
-- correction is only ever created for an erasure_log row whose OWN
-- job_id (migration 014) is referenced by an erasure_batch_items row
-- (migration 015), whose batch_id resolves to exactly ONE distinct
-- erasure_batches.user_id. If the SAME job_id is referenced by items
-- from batches for MORE than one distinct user_id (a real ambiguity —
-- e.g. a job adopted across two different-subject batches on a pre-
-- Round-5.2 deployment, before the fencing Round 5.2 itself added), no
-- correction is created for it at all — an ambiguous row is left exactly
-- as originally recorded. A job_id with NO erasure_batch_items reference
-- at all (an ordinary single-fact erasure, core.erasure.erase_fact()'s
-- shim, or the forget_fact MCP tool) is never touched either — this
-- backfill only ever repairs rows with a provable BATCH linkage.
--
-- IDEMPOTENT: the backfill INSERT is guarded by `NOT EXISTS` against
-- erasure_id — re-running this migration (or the equivalent self-heal
-- backfill) a second time inserts zero additional correction rows and
-- changes nothing. Operator/credential provenance (erasure_jobs.actor,
-- erasure_batches.actor) is never modified by this migration — only a
-- NEW, separate, append-only audit correction is added.
--
-- ATOMIC: the whole migration (column add, new table/triggers, backfill,
-- view redefinition) is wrapped in one explicit BEGIN/COMMIT — mirrors
-- migration 014's own documented rationale for why
-- sqlite3.Connection.executescript() alone does not give a multi-
-- statement script real transactional atomicity. A failure at any point
-- rolls back the entire migration, including the column add and the view
-- redefinition — never a partially-applied intermediate state.

BEGIN;

ALTER TABLE erasure_jobs ADD COLUMN subject_user_id TEXT;

-- Separate, append-only audit correction — never mutates erasure_log
-- itself. UNIQUE(erasure_id) backs the idempotency guarantee above (a
-- real DB constraint, not just the NOT EXISTS guard in the INSERT below).
CREATE TABLE IF NOT EXISTS erasure_log_subject_corrections (
    correction_id      TEXT PRIMARY KEY,
    erasure_id         TEXT NOT NULL UNIQUE REFERENCES erasure_log(erasure_id),
    job_id             TEXT,
    batch_id           TEXT NOT NULL REFERENCES erasure_batches(batch_id),
    corrected_user_id  TEXT NOT NULL,
    original_user_id   TEXT NOT NULL,
    created_at         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_erasure_log_subject_corrections_erasure_id
    ON erasure_log_subject_corrections(erasure_id);
CREATE INDEX IF NOT EXISTS idx_erasure_log_subject_corrections_user
    ON erasure_log_subject_corrections(corrected_user_id);

-- Genuinely append-only, enforced by the engine — mirrors migration
-- 012's erasure_log triggers and migration 015's
-- erasure_batch_force_receipts triggers, not just a naming convention.
CREATE TRIGGER IF NOT EXISTS prevent_erasure_log_subject_corrections_delete
BEFORE DELETE ON erasure_log_subject_corrections
BEGIN
    SELECT RAISE(ABORT, 'VELANTRIM: erasure_log_subject_corrections is append-only. Cannot delete audit records.');
END;

CREATE TRIGGER IF NOT EXISTS prevent_erasure_log_subject_corrections_update
BEFORE UPDATE ON erasure_log_subject_corrections
BEGIN
    SELECT RAISE(ABORT, 'VELANTRIM: erasure_log_subject_corrections is append-only. Cannot modify audit records.');
END;

-- Backfill: exactly one correction per erasure_log row that is provably,
-- unambiguously linked to a single batch subject and whose recorded
-- user_id doesn't already match it. See the linkage/idempotency rationale
-- above.
INSERT INTO erasure_log_subject_corrections
    (correction_id, erasure_id, job_id, batch_id, corrected_user_id, original_user_id, created_at)
SELECT
    'elc_' || lower(hex(randomblob(8))),
    el.erasure_id,
    el.job_id,
    linked.batch_id,
    linked.user_id,
    el.user_id,
    datetime('now')
FROM erasure_log el
JOIN (
    SELECT job_id, MIN(user_id) AS user_id, MIN(batch_id) AS batch_id
    FROM (
        SELECT ebi.job_id AS job_id, eb.user_id AS user_id, eb.batch_id AS batch_id
        FROM erasure_batch_items ebi
        JOIN erasure_batches eb ON eb.batch_id = ebi.batch_id
        WHERE ebi.job_id IS NOT NULL
    )
    GROUP BY job_id
    HAVING COUNT(DISTINCT user_id) = 1
) AS linked ON linked.job_id = el.job_id
WHERE el.job_id IS NOT NULL
  AND el.user_id != linked.user_id
  AND NOT EXISTS (
      SELECT 1 FROM erasure_log_subject_corrections c WHERE c.erasure_id = el.erasure_id
  );

-- Also backfill erasure_jobs.subject_user_id itself for the same
-- provably-linked jobs — this is a brand-new column this SAME migration
-- just added (never populated before, no append-only trigger protects
-- erasure_jobs), so populating it for the first time is not "rewriting
-- history" the way mutating erasure_log would be. Idempotent via
-- `WHERE subject_user_id IS NULL` — an already-backfilled (or already
-- explicitly-set, post-Round-5.2) row is never touched again.
WITH job_subjects AS (
    SELECT job_id, MIN(user_id) AS user_id
    FROM (
        SELECT ebi.job_id AS job_id, eb.user_id AS user_id
        FROM erasure_batch_items ebi
        JOIN erasure_batches eb ON eb.batch_id = ebi.batch_id
        WHERE ebi.job_id IS NOT NULL
    )
    GROUP BY job_id
    HAVING COUNT(DISTINCT user_id) = 1
)
UPDATE erasure_jobs
SET subject_user_id = (
    SELECT user_id FROM job_subjects WHERE job_subjects.job_id = erasure_jobs.job_id
),
    updated_at = datetime('now')
WHERE subject_user_id IS NULL
  AND job_id IN (SELECT job_id FROM job_subjects);

-- erasure_audit is the ONLY thing core.forgetting.ForgettingEngine.
-- get_erasure_log() actually queries — redefine it to resolve the
-- EFFECTIVE subject through any correction, via COALESCE. el.user_id
-- (the ORIGINAL recorded value) is completely untouched on disk; this
-- view is the one and only place the correction is applied for readers.
DROP VIEW IF EXISTS erasure_audit;
CREATE VIEW erasure_audit AS
SELECT
    el.erasure_id,
    el.fact_id,
    COALESCE(c.corrected_user_id, el.user_id) AS user_id,
    el.reason,
    el.claim_hash,
    el.erased_at,
    el.request_ref
FROM erasure_log el
LEFT JOIN erasure_log_subject_corrections c ON c.erasure_id = el.erasure_id
ORDER BY el.erased_at DESC;

COMMIT;

-- ── Проверка после применения ─────────────────────────────────────────────────
-- PRAGMA table_info(erasure_jobs);  -- ожидать колонку subject_user_id
-- SELECT COUNT(*) FROM erasure_log_subject_corrections;  -- >=0, idempotent on re-run
-- SELECT sql FROM sqlite_master WHERE name = 'erasure_audit';  -- COALESCE-resolved view
