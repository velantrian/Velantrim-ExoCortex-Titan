# core/erasure_coordinator.py
# VELANTRIM Titan — GDPR Art. 17 durable erasure saga (P0-B)
#
# core/erasure.py's original erase_fact() ran one best-effort pass over a
# single SQLite file and unconditionally wrote a tombstone. That cannot be
# provable once a fact's data lives in THREE independent SQLite files
# (the main facts DB, the embeddings DB, the ngram DB) and cannot survive
# a crash mid-erasure. This module is the one enforced entrypoint that
# replaces it:
#
#   - erasure_jobs is the durable ATTEMPT RECEIPT — written before any
#     deletion is attempted, and never conflated with the completion
#     tombstone. A PARTIAL/FAILED job is still an honest, resumable record.
#   - erasure_log (core/memory.py) remains the content-free COMPLETION
#     tombstone — written ONLY when a job's outcome is COMPLETE. is_erased()
#     therefore means "provably, completely erased," not "an attempt was
#     made."
#   - Each storage backend (same-DB dependents, embeddings, ngram) is its
#     own job step with its own PENDING/RUNNING/COMPLETE/FAILED state, so a
#     crash between backends leaves an accurate record of exactly what has
#     and has not been proven deleted — resume_incomplete_jobs() picks up
#     from there without re-attempting already-COMPLETE steps.
#   - A fact whose raw L0 origin cannot be determined (residual =
#     "undetermined" — a real DB error, not "no raw text exists") can NEVER
#     reach outcome COMPLETE. "I don't know" must never be reported as
#     "erased."
#   - A fact whose raw L0 origin is KNOWN to exist (residual =
#     "raw_original_present") also never reaches COMPLETE — it resolves to
#     the distinct terminal outcome RESIDUAL_IMMUTABLE_DATA instead. The
#     derived fact layer is fully, provably erased, but l0_raw_memory still
#     holds the original text by design (see core/erasure.py); no
#     completion tombstone is written and is_erased() stays False, because
#     the record is not "provably, completely erased" while a raw copy is
#     known to remain.
#
# See core/erasure.py for the Ring Zero (I6) invariant and the documented,
# intentional limitation that l0_raw_memory (immutable, append-only) is not
# physically erased by this or any erasure path.

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from core import memory
from core.ngram_index import NGramIndex, get_global_ngram

if TYPE_CHECKING:
    # core.embedding_store depends on numpy — an optional dependency for
    # base/server installs that don't need embeddings. Only imported here
    # for static type-checking (mypy); never evaluated at runtime because
    # `from __future__ import annotations` (above) makes every annotation a
    # string. The real, lazy runtime import lives in
    # ErasureCoordinator._get_embeddings().
    from core.embedding_store import EmbeddingStore

PENDING = "PENDING"
RUNNING = "RUNNING"
COMPLETE = "COMPLETE"
PARTIAL = "PARTIAL"
FAILED = "FAILED"
NOT_FOUND = "NOT_FOUND"
# Every same-DB/embeddings/ngram step succeeded and the derived fact layer
# is provably gone, but the fact had a raw L0 origin (residual =
# "raw_original_present") — l0_raw_memory is immutable by design (see
# core/erasure.py) and is never deleted by any erasure path. This is a
# terminal, non-error outcome, but it is NOT "completely erased": no
# completion tombstone is written and is_erased() stays False, because the
# original text is known to still exist. Review finding: reporting this as
# COMPLETE would let the system claim "provably, completely erased" while
# personal data physically remains.
RESIDUAL_IMMUTABLE_DATA = "RESIDUAL_IMMUTABLE_DATA"
# Codex review finding (P1): a job can finish all four of its steps yet
# still land in a NON-terminal overall status (PARTIAL, when residual=
# "undetermined" because the facts row was already gone when
# determine_raw ran — see _run_determine_raw()). Such a job is "done" in
# the sense that _run_job() has nothing left to execute, but it is NOT
# safe to keep adopting forever: if fact_id is recreated afterward,
# _get_or_create_job()'s old fast path would return this same job_id,
# _run_job() would skip every already-COMPLETE step, and the
# newly-recreated data would never be touched. SUPERSEDED is the terminal
# status such a job is transitioned to once residual data is confirmed to
# have reappeared — its own step receipts are NEVER rewritten (still
# immutable history, exactly like a COMPLETE/RESIDUAL_IMMUTABLE_DATA
# generation), only its own `status`/`error` change, and a NEW generation
# is opened to actually erase the reappeared data. `error` records a
# technical marker only (never PII/claim content) — see _supersede_job().
SUPERSEDED = "SUPERSEDED"

# Terminal job statuses that resume_incomplete_jobs() should never re-pick
# up — COMPLETE because there's nothing left to do, RESIDUAL_IMMUTABLE_DATA
# because the residual is a permanent fact about the record (re-running
# would just recompute the identical outcome forever), SUPERSEDED because
# a NEW generation already exists to handle the reappeared data — see
# above.
_TERMINAL_STATUSES = (COMPLETE, RESIDUAL_IMMUTABLE_DATA, SUPERSEDED)

_STEP_NAMES = ("determine_raw", "l1_same_db", "embeddings", "ngram")

# Mirrors core.embedding_store.EXOCORTEX_DB's env var + default literal —
# duplicated here (rather than imported) specifically so this module never
# has to import core.embedding_store (and therefore numpy) just to resolve
# a path string. Used ONLY as a fallback for the numpy-unavailable case in
# _run_embeddings(), to check via stdlib sqlite3 whether fact_id
# specifically has an embeddings row — see
# _embeddings_row_present_for(). Keep in sync if EXOCORTEX_DB's definition
# ever changes.
_EMBEDDINGS_DB_PATH_ENV = "SQLITE_GRAPH_PATH"
_EMBEDDINGS_DB_PATH_DEFAULT = "./data/exocortex_graph.db"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS erasure_jobs (
    job_id        TEXT PRIMARY KEY,
    fact_id       TEXT NOT NULL,
    generation    INTEGER NOT NULL DEFAULT 1,
    reason        TEXT NOT NULL,
    actor         TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'PENDING',
    residual      TEXT,
    content_hash  TEXT,
    error         TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

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
"""

# Index/constraint DDL is kept separate from _SCHEMA_SQL and applied AFTER
# the generation-column upgrade in _ensure_schema() — idx_erasure_jobs_fact_
# generation references the `generation` column, which a legacy (pre-014)
# DB won't have until the ALTER TABLE right before this runs.
#
# Post-review hotfix (migration 014): a fact_id can be erased, then
# recreated (re-ingested under the same ID) and erased again — this must
# be possible any number of times, with the full history preserved. The
# OLD, unconditional UNIQUE(fact_id) index (migration 013) made that
# impossible: it permitted exactly one erasure_jobs row per fact_id, ever.
#
#   - idx_erasure_jobs_fact_active: a PARTIAL unique index, scoped to
#     non-terminal statuses only, enforces "at most one ACTIVE saga per
#     fact_id at a time" (the same concurrency guarantee migration 013
#     provided) while allowing multiple TERMINAL (COMPLETE /
#     RESIDUAL_IMMUTABLE_DATA / SUPERSEDED) rows — one per generation — to
#     coexist as immutable history.
#   - idx_erasure_jobs_fact_generation: UNIQUE(fact_id, generation) is a
#     data-integrity backstop against two rows ever claiming the same
#     generation number for the same fact_id.
_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_erasure_jobs_status ON erasure_jobs(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_jobs_fact_active
    ON erasure_jobs(fact_id)
    WHERE status NOT IN ('COMPLETE', 'RESIDUAL_IMMUTABLE_DATA', 'SUPERSEDED');
CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_jobs_fact_generation
    ON erasure_jobs(fact_id, generation);
CREATE INDEX IF NOT EXISTS idx_erasure_job_steps_job ON erasure_job_steps(job_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_claim(claim: str) -> str:
    return "sha256:" + hashlib.sha256(claim.encode("utf-8")).hexdigest()


class ErasureCoordinator:
    """Durable, resumable GDPR Art. 17 erasure saga.

    Fully dependency-injectable — pass real, temp-file-backed `store` /
    `embedding_store` / `ngram_index` instances in tests instead of the
    process-global singletons. There is no fake/stub store anywhere in
    this module: every step operates on the real SQLite backend it claims
    to have proven deletion against.
    """

    def __init__(
        self,
        store: memory.SQLiteGraphStore | None = None,
        embedding_store: EmbeddingStore | None = None,
        ngram_index: NGramIndex | None = None,
        jobs_db_path: str | None = None,
    ) -> None:
        self._store = store or memory._GLOBAL_STORE
        # Lazy: core.embedding_store depends on numpy, which is optional for
        # base/server installs — see _get_embeddings(). Explicit injection
        # (tests, or a caller that already has one) is used immediately;
        # otherwise the real EmbeddingStore is constructed on first actual
        # use, not at construction time.
        self._embeddings = embedding_store
        # Use the SAME configured global NGramIndex instance the running
        # server/pipeline already registered via set_global_ngram() — e.g.
        # server.py points VELANTRIM_NGRAM_DB at ./data/ngram_house.db and
        # registers that instance. Constructing a bare NGramIndex() here
        # would silently default to core.ngram_index's OWN module-level
        # default path (./data/velantrim_ngram.db) instead, and "clean up"
        # a completely different, unrelated ngram file — never actually
        # touching what the running server is really using.
        self._ngram = ngram_index or get_global_ngram()
        self.jobs_db_path = jobs_db_path or self._store.db_path
        self._ensure_schema()

    def _get_embeddings(self) -> EmbeddingStore:
        """Construct the embeddings backend on first actual use.

        core.embedding_store imports numpy at module level — an optional
        dependency not every install needs. Deferring the import to here
        (instead of importing EmbeddingStore at the top of this module)
        means `import core.erasure_coordinator` — and therefore
        `core.erasure` and ToolRegistry, which both transitively import
        this module — succeeds even where numpy isn't installed. The cost
        of numpy genuinely being absent is deferred to the one place that
        would need it: if the import fails here, the caller (_run_embeddings)
        catches it like any other step failure. It reports an honest FAILED
        step UNLESS it can also prove, via stdlib sqlite3 alone (see
        _embeddings_row_present_for()), that fact_id specifically has no
        embeddings row — a silent, UNPROVEN "applicable: false" is still
        never acceptable, but a PROVEN one is.
        """
        if self._embeddings is None:
            from core.embedding_store import EmbeddingStore
            self._embeddings = EmbeddingStore()
        return self._embeddings

    def _resolve_embeddings_db_path(self) -> str:
        """Best-effort path to the embeddings DB file, without importing
        core.embedding_store (numpy). Prefers an already-injected store's
        real path; falls back to the same env var + default
        core.embedding_store.EXOCORTEX_DB itself resolves, for the case
        where no store is injected and constructing a real one just failed
        (numpy unavailable)."""
        if self._embeddings is not None:
            return getattr(self._embeddings, "_db_path", _EMBEDDINGS_DB_PATH_DEFAULT)
        return os.getenv(_EMBEDDINGS_DB_PATH_ENV, _EMBEDDINGS_DB_PATH_DEFAULT)

    @staticmethod
    def _embeddings_row_present_for(fact_id: str, db_path: str) -> bool:
        """Stdlib sqlite3 only — no numpy import, and deliberately never
        calls EmbeddingStore.ensure_table() (which would itself CREATE
        gs_vectors as a side effect of merely checking, and does elsewhere
        as a no-op purge_node() side effect — table existence alone is not
        proof this fact_id ever had embeddings; see Codex review finding).

        True only if the embeddings DB file, its gs_vectors table, AND a
        row for THIS SPECIFIC fact_id all exist — meaning there is
        something that could hold residual data for fact_id specifically.
        False is a PROVEN absence in any of these cases: no file, a file
        with no gs_vectors table, or a table with rows for OTHER facts but
        none for this one — there is nothing this step could possibly need
        to clean up for fact_id, regardless of whether numpy/the real
        backend is currently reachable.

        Fails toward "might be present" on any error opening/querying the
        file (e.g. a corrupted/unreadable DB) — the same "can't verify
        absence is not verified absence" principle already applied to
        _residual_data_present() and the raw-origin tri-state.
        """
        if not os.path.exists(db_path):
            return False
        try:
            conn = sqlite3.connect(db_path, timeout=5.0)
            try:
                table_row = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='gs_vectors'"
                ).fetchone()
                if table_row is None:
                    return False
                fact_row = conn.execute(
                    "SELECT 1 FROM gs_vectors WHERE node_id = ? LIMIT 1", (fact_id,)
                ).fetchone()
                return fact_row is not None
            finally:
                conn.close()
        except sqlite3.Error:
            return True

    # ── schema / low-level job ledger (own connection — same DB file as
    #    `facts`, but independent of SQLiteGraphStore's connection cache) ──

    @contextmanager
    def _jobs_db(self):
        conn = sqlite3.connect(self.jobs_db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 30000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._jobs_db() as conn:
            conn.executescript(_SCHEMA_SQL)
            # Codex review finding (P2): the legacy-DB upgrade below (add
            # `generation`, drop the obsolete unconditional unique index,
            # create the new generation-aware ones) must be ONE atomic
            # transaction. sqlite3.Connection.executescript()/individual
            # DDL statements do NOT autocommit-wrap themselves as a unit —
            # confirmed empirically (mirrors the exact hazard already fixed
            # in migrations/014_erasure_job_generations.sql): a failure
            # partway through could otherwise leave the DB with NEITHER the
            # old nor the new uniqueness constraint, letting concurrent
            # erasures create duplicate active sagas until a later
            # successful startup repairs it. An explicit BEGIN IMMEDIATE +
            # COMMIT/ROLLBACK here gives the same real transactional
            # guarantee the migration file already has.
            conn.execute("BEGIN IMMEDIATE")
            try:
                # Upgrade a legacy (pre-014) DB in place: it has
                # erasure_jobs without a `generation` column and the OLD,
                # unconditional UNIQUE(fact_id) index. A fresh DB already
                # has the column from _SCHEMA_SQL above, so the ALTER TABLE
                # below is a no-op (caught as "duplicate column") — this
                # must run in this exact order, since
                # idx_erasure_jobs_fact_generation references the
                # `generation` column.
                try:
                    conn.execute(
                        "ALTER TABLE erasure_jobs ADD COLUMN generation "
                        "INTEGER NOT NULL DEFAULT 1"
                    )
                except sqlite3.OperationalError:
                    pass
                conn.execute("DROP INDEX IF EXISTS idx_erasure_jobs_fact")
                # idx_erasure_jobs_fact_active's WHERE clause changed when
                # SUPERSEDED was added to the terminal-status exclusion
                # list — CREATE ... IF NOT EXISTS is a no-op against a
                # same-named index with a STALE definition, so it must be
                # explicitly dropped first to stay in sync with
                # _INDEX_SQL below (a DB that already ran an earlier
                # version of this method would otherwise keep the old
                # definition forever).
                conn.execute("DROP INDEX IF EXISTS idx_erasure_jobs_fact_active")
                # conn.executescript() implicitly COMMITs any pending
                # transaction before it runs its own statements (a Python
                # sqlite3 module quirk, confirmed empirically) — calling it
                # here would silently commit the ALTER TABLE/DROP INDEX
                # above before this method's own explicit transaction ever
                # reaches its intended COMMIT/ROLLBACK, defeating the whole
                # point of wrapping this sequence atomically. Each
                # statement is executed individually via conn.execute()
                # instead, all within the SAME explicit transaction.
                for _stmt in _INDEX_SQL.strip().split(";"):
                    _stmt = _stmt.strip()
                    if _stmt:
                        conn.execute(_stmt)

                names = {
                    r[0] for r in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'index' "
                        "AND tbl_name = 'erasure_jobs'"
                    ).fetchall()
                }
                if "idx_erasure_jobs_fact" in names:
                    raise RuntimeError(
                        "_ensure_schema: obsolete idx_erasure_jobs_fact "
                        "still present after upgrade — refusing to proceed "
                        "with an unproven schema"
                    )
                for required in (
                    "idx_erasure_jobs_fact_active",
                    "idx_erasure_jobs_fact_generation",
                ):
                    if required not in names:
                        raise RuntimeError(
                            f"_ensure_schema: {required} missing after "
                            "upgrade — refusing to proceed with an "
                            "unproven schema"
                        )
            except Exception:
                conn.rollback()
                raise
            else:
                conn.commit()

    # ── job ledger helpers ───────────────────────────────────────────────

    def _peek_job_row(self, fact_id: str) -> dict[str, Any] | None:
        """The latest-generation erasure_jobs row for `fact_id`, or None if
        no erasure was ever attempted. Ordered by `generation` first (the
        authoritative sequence — see migration 014) with `created_at` only
        as a tie-breaker."""
        with self._jobs_db() as conn:
            row = conn.execute(
                "SELECT * FROM erasure_jobs WHERE fact_id = ? "
                "ORDER BY generation DESC, created_at DESC LIMIT 1",
                (fact_id,),
            ).fetchone()
        return dict(row) if row else None

    def _load_job(self, job_id: str) -> dict[str, Any]:
        with self._jobs_db() as conn:
            row = conn.execute(
                "SELECT * FROM erasure_jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"erasure job '{job_id}' not found")
        return dict(row)

    def _load_steps(self, job_id: str) -> list[dict[str, Any]]:
        with self._jobs_db() as conn:
            rows = conn.execute(
                "SELECT * FROM erasure_job_steps WHERE job_id = ? ORDER BY step_name",
                (job_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def _step_status(self, job_id: str, step_name: str) -> str:
        with self._jobs_db() as conn:
            row = conn.execute(
                "SELECT status FROM erasure_job_steps WHERE job_id = ? AND step_name = ?",
                (job_id, step_name),
            ).fetchone()
        return row["status"] if row else PENDING

    def _get_or_create_job(self, fact_id: str, reason: str, actor: str) -> str:
        """Get the one ACTIVE durable job for `fact_id`, opening a new
        generation if none is active.

        At most one ACTIVE (non-terminal) saga per fact_id may exist at a
        time, enforced by a real SQLite constraint (the partial UNIQUE
        index on erasure_jobs.fact_id, scoped to non-terminal statuses —
        see _SCHEMA_SQL/_INDEX_SQL and migration 014), not merely by this
        method's own check-then-insert ordering. The initial
        `_peek_job_row` check below is only a fast path for the common case
        (no job yet, or an active one already exists and this is a plain
        resume); it does NOT by itself prevent two concurrent callers
        (different threads, or different processes/connections) from both
        observing "no active job" and both proceeding to insert.

        A PRIOR generation that already reached a terminal outcome
        (COMPLETE / RESIDUAL_IMMUTABLE_DATA) is never adopted or reused —
        erase_fact_durable() only calls this once it has already decided a
        NEW generation is actually needed (no active job existed, or the
        latest one is terminal and the underlying data has reappeared).
        That prior row is immutable history and is left untouched; the new
        row gets `generation = prior_generation + 1` (or 1 if none exists).

        The actual concurrency safety comes from wrapping the create in one
        explicit `BEGIN IMMEDIATE` transaction (the job row and all four
        step rows are one atomic unit) and catching the IntegrityError a
        concurrent loser's INSERT raises against the partial UNIQUE index:
        the loser does not error out or invent a second, diverging active
        job for the same fact_id — it looks up and adopts the winner's
        (new-generation) job_id instead, so every concurrent caller ends up
        working the SAME saga.

        Re-running an already-active job is safe (every step is a no-op
        replay and _finalize()/write_tombstone() are both idempotent), so
        an existing ACTIVE job for this fact_id is resumed rather than
        duplicated.

        Codex review finding (P1): an existing NON-terminal job whose steps
        have ALL already finished (PARTIAL with residual="undetermined" —
        see _run_determine_raw()) is a special case: _run_job() has
        nothing left to execute for it, so if fact_id was recreated since,
        blindly resuming it would silently skip re-erasing the new data.
        Before adopting ANY non-terminal job, this checks whether residual
        data has (re)appeared; if it has AND every step already shows
        COMPLETE, the old job is transitioned to the terminal SUPERSEDED
        status (its own step receipts are never rewritten — still
        immutable history) and a NEW generation is opened instead, in the
        SAME atomic transaction as the new generation's INSERT.
        """
        existing = self._peek_job_row(fact_id)
        supersede_job_id = None
        if existing is not None and existing["status"] not in _TERMINAL_STATUSES:
            steps = self._load_steps(existing["job_id"])
            all_steps_done = bool(steps) and all(s["status"] == COMPLETE for s in steps)
            if not (all_steps_done and self._residual_data_present(fact_id)):
                return existing["job_id"]
            supersede_job_id = existing["job_id"]

        next_generation = (existing["generation"] + 1) if existing is not None else 1
        job_id = f"erj_{uuid.uuid4().hex[:16]}"
        now = _now()
        with self._jobs_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                if supersede_job_id is not None:
                    # Preserve the old saga as immutable history: only
                    # status/error change, step receipts are untouched.
                    # error is a technical marker only, never PII/claim
                    # content.
                    conn.execute(
                        "UPDATE erasure_jobs SET status = ?, error = ?, updated_at = ? "
                        "WHERE job_id = ?",
                        (
                            SUPERSEDED,
                            "superseded: residual data reappeared after all steps completed",
                            now,
                            supersede_job_id,
                        ),
                    )
                conn.execute(
                    "INSERT INTO erasure_jobs "
                    "(job_id, fact_id, generation, reason, actor, status, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (job_id, fact_id, next_generation, reason, actor, PENDING, now, now),
                )
                for step_name in _STEP_NAMES:
                    conn.execute(
                        "INSERT INTO erasure_job_steps (step_id, job_id, step_name, status) "
                        "VALUES (?, ?, ?, ?)",
                        (f"{job_id}_{step_name}", job_id, step_name, PENDING),
                    )
            except sqlite3.IntegrityError:
                # Lost the create race: a concurrent caller's INSERT into
                # erasure_jobs committed first. Two distinct unique indexes
                # can be the one that tripped — either is a lost race, never
                # a reason to invent a second job for this fact_id:
                #
                #   idx_erasure_jobs_fact_generation (fact_id, generation):
                #   both callers read the same prior `existing` row and
                #   computed the same candidate generation number. The
                #   winner's row is identified by generation = next_generation
                #   regardless of its CURRENT status — by the time this
                #   loser's rollback + recovery SELECT run, the winner may
                #   already have finished `_run_job()` end-to-end and be
                #   COMPLETE (a fast saga on a small DB easily completes
                #   within the microseconds this loser spends handling its
                #   own failed INSERT + rollback). A recovery query that
                #   filtered out COMPLETE/RESIDUAL_IMMUTABLE_DATA rows here
                #   would find nothing and wrongly re-raise — this was a
                #   genuine, reproducible race exposed by concurrent-erasure
                #   regression tests on a recreated fact_id.
                #
                #   idx_erasure_jobs_fact_active (fact_id, partial on
                #   non-terminal status): the winner used a DIFFERENT
                #   generation number than ours (a staler `existing` read on
                #   our side) but is still non-terminal — matched by the
                #   status filter.
                conn.rollback()
                placeholders = ", ".join("?" for _ in _TERMINAL_STATUSES)
                row = conn.execute(
                    f"SELECT * FROM erasure_jobs WHERE fact_id = ? "  # noqa: S608
                    f"AND (generation = ? OR status NOT IN ({placeholders})) "
                    "ORDER BY generation DESC LIMIT 1",
                    (fact_id, next_generation, *_TERMINAL_STATUSES),
                ).fetchone()
                if row is None:
                    # Not actually a lost create-race (no winner row exists
                    # at the generation we attempted, and no other active
                    # row either) — a genuinely unexpected IntegrityError.
                    # Do not mask it.
                    raise
                winner = dict(row)
            else:
                conn.commit()
                return job_id

        # Reached only via the IntegrityError branch above (a normal
        # winning INSERT already returned). `winner` is the row that
        # blocked our insert.
        if winner["status"] in _TERMINAL_STATUSES and self._residual_data_present(fact_id):
            # Security review round 2, risk 4: the winner's generation
            # already resolved to a terminal outcome, but fact_id was
            # recreated AGAIN after that — possibly before we even got here
            # (this loser lost the create-race, then a THIRD event
            # re-ingested data under the same fact_id before this recovery
            # ran). Blindly adopting the winner's job_id here would let
            # _run_job()/_finalize() short-circuit through already-COMPLETE
            # steps and return a stale COMPLETE report while the
            # newly-recreated data sits unerased — the exact class of bug
            # this hotfix's generation model exists to prevent, one layer
            # removed (inside the race-recovery path itself). Recurse to
            # open the NEXT generation instead of trusting a terminal
            # report that no longer reflects current reality.
            return self._get_or_create_job(fact_id, reason, actor)

        return winner["job_id"]

    def _set_job_status(self, job_id: str, status: str) -> None:
        with self._jobs_db() as conn:
            conn.execute(
                "UPDATE erasure_jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                (status, _now(), job_id),
            )

    def _set_job_error(self, job_id: str, error: str) -> None:
        with self._jobs_db() as conn:
            conn.execute(
                "UPDATE erasure_jobs SET error = ?, updated_at = ? WHERE job_id = ?",
                (error, _now(), job_id),
            )

    def _set_job_residual_and_hash(
        self, job_id: str, residual: str, content_hash: str | None
    ) -> None:
        with self._jobs_db() as conn:
            row = conn.execute(
                "SELECT content_hash FROM erasure_jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            # A resumed job may re-run determine_raw against a facts row that
            # is already gone (this same job deleted it on a prior, crashed
            # attempt) — never let a fresh None clobber an already-captured
            # hash; the first successful capture is the one that matters.
            keep_hash = row["content_hash"] if row and row["content_hash"] else content_hash
            conn.execute(
                "UPDATE erasure_jobs SET residual = ?, content_hash = ?, updated_at = ? "
                "WHERE job_id = ?",
                (residual, keep_hash, _now(), job_id),
            )

    def _step_start(self, job_id: str, step_name: str) -> None:
        with self._jobs_db() as conn:
            conn.execute(
                "UPDATE erasure_job_steps SET status = ?, started_at = ? "
                "WHERE job_id = ? AND step_name = ?",
                (RUNNING, _now(), job_id, step_name),
            )

    def _step_finish(
        self, job_id: str, step_name: str, status: str, detail: dict[str, Any]
    ) -> None:
        with self._jobs_db() as conn:
            conn.execute(
                "UPDATE erasure_job_steps SET status = ?, detail = ?, finished_at = ? "
                "WHERE job_id = ? AND step_name = ?",
                (status, json.dumps(detail), _now(), job_id, step_name),
            )

    # ── step implementations ─────────────────────────────────────────────

    def _run_determine_raw(self, job_id: str, fact_id: str) -> None:
        """Tri-state raw-original check — MUST run before l1_same_db deletes
        the `facts` row, since that row (and its `derived_from` column) is
        the only place this information lives. residual is persisted to the
        job immediately so a resume never needs to re-derive it from a row
        that may no longer exist.
        """
        self._step_start(job_id, "determine_raw")
        try:
            try:
                fact = self._store.get_fact_durable(fact_id)
            except sqlite3.OperationalError:
                # Genuine DB-level inability to check — "I don't know" is
                # NOT the same as "no raw original exists".
                fact = None
                residual = "undetermined"
            else:
                if fact is None:
                    residual = "undetermined"
                else:
                    residual = (
                        "raw_original_present" if fact.get("derived_from") else "none"
                    )
        except Exception as exc:  # noqa: BLE001 — genuine bug, must not be silently "undetermined"
            self._step_finish(job_id, "determine_raw", FAILED, {"error": str(exc)})
            self._set_job_error(job_id, f"determine_raw: {exc}")
            return

        content_hash = (
            _hash_claim(fact["claim"]) if fact and fact.get("claim") else None
        )
        self._set_job_residual_and_hash(job_id, residual, content_hash)
        self._step_finish(job_id, "determine_raw", COMPLETE, {"residual": residual})

    def _run_l1_same_db(self, job_id: str, fact_id: str) -> None:
        """One atomic transaction against the main facts DB — see
        SQLiteGraphStore.erase_fact_dependents_atomic() for the per-table
        proof this step reports verbatim as its `detail`.
        """
        self._step_start(job_id, "l1_same_db")
        try:
            result = self._store.erase_fact_dependents_atomic(fact_id)
        except Exception as exc:  # noqa: BLE001 — must propagate, not be swallowed
            self._step_finish(job_id, "l1_same_db", FAILED, {"error": str(exc)})
            self._set_job_error(job_id, f"l1_same_db: {exc}")
            return
        self._step_finish(job_id, "l1_same_db", COMPLETE, result)

    def _run_embeddings(self, job_id: str, fact_id: str) -> None:
        self._step_start(job_id, "embeddings")
        try:
            embeddings = self._get_embeddings()
        except Exception as exc:  # noqa: BLE001 — the embeddings backend
            # being genuinely unavailable (e.g. numpy not installed).
            # Distinguish two states before giving up:
            #   - fact_id has NO row in gs_vectors — either the embeddings
            #     feature has never been used in this deployment at all
            #     (no DB file / no table), or it has been used for OTHER
            #     facts but never this one. Either way, provable via
            #     stdlib sqlite3 alone (no numpy, no
            #     EmbeddingStore.ensure_table() side effect — mere table
            #     existence is not proof of use for THIS fact_id, since
            #     e.g. a no-op purge_node() elsewhere creates the table as
            #     a side effect even for a fact that never had
            #     embeddings). There is nothing this step could possibly
            #     need to clean up for fact_id, so an honest COMPLETE with
            #     a proven applicable=False is correct here.
            #   - fact_id DOES have a row (this specific fact has/had
            #     embeddings) but the real backend can't be reached right
            #     now — an honest FAILED (-> PARTIAL job), never a silent,
            #     unproven "applicable: false".
            db_path = self._resolve_embeddings_db_path()
            if not self._embeddings_row_present_for(fact_id, db_path):
                self._step_finish(
                    job_id, "embeddings", COMPLETE,
                    {"applicable": False, "reason": "no_embeddings_row_for_fact"},
                )
                return
            self._step_finish(job_id, "embeddings", FAILED, {"error": str(exc)})
            self._set_job_error(job_id, f"embeddings: {exc}")
            return
        try:
            deleted = embeddings.purge_node(fact_id)
            still_present = embeddings.has_any(fact_id)
        except Exception as exc:  # noqa: BLE001
            self._step_finish(job_id, "embeddings", FAILED, {"error": str(exc)})
            self._set_job_error(job_id, f"embeddings: {exc}")
            return
        if still_present:
            self._step_finish(
                job_id, "embeddings", FAILED,
                {"deleted": deleted, "error": "still_present_after_delete"},
            )
            self._set_job_error(job_id, "embeddings: still_present_after_delete")
            return
        self._step_finish(job_id, "embeddings", COMPLETE, {"deleted": deleted})

    def _run_ngram(self, job_id: str, fact_id: str) -> None:
        self._step_start(job_id, "ngram")
        try:
            applicable = self._ngram.purge(fact_id)
            still_present = self._ngram.contains(fact_id)
        except Exception as exc:  # noqa: BLE001
            self._step_finish(job_id, "ngram", FAILED, {"error": str(exc)})
            self._set_job_error(job_id, f"ngram: {exc}")
            return
        if still_present:
            self._step_finish(
                job_id, "ngram", FAILED,
                {"applicable": applicable, "error": "still_present_after_delete"},
            )
            self._set_job_error(job_id, "ngram: still_present_after_delete")
            return
        self._step_finish(job_id, "ngram", COMPLETE, {"applicable": applicable})

    # ── orchestration ─────────────────────────────────────────────────────

    def _claim_job_for_running(self, job_id: str) -> bool:
        """Atomically claim `job_id` for execution.

        A single `UPDATE ... WHERE status NOT IN (...)` is its own implicit
        SQLite transaction (Python's sqlite3 auto-begins before DML) and is
        serialized against every other writer to the same jobs DB file by
        SQLite's own locking — a real cross-process mechanism, not a
        process-local `threading.Lock`. Exactly one concurrent caller's
        UPDATE matches and transitions the row to RUNNING; every other
        caller's UPDATE matches zero rows (rowcount == 0) because the
        winner's write already moved the status out of the claimable set.

        Returns False if another caller already holds the claim (status is
        already RUNNING) or the job already reached a terminal outcome
        (COMPLETE / RESIDUAL_IMMUTABLE_DATA — nothing left to run).
        """
        with self._jobs_db() as conn:
            cur = conn.execute(
                "UPDATE erasure_jobs SET status = ?, updated_at = ? "
                "WHERE job_id = ? AND status NOT IN (?, ?, ?)",
                (RUNNING, _now(), job_id, RUNNING, COMPLETE, RESIDUAL_IMMUTABLE_DATA),
            )
        return cur.rowcount > 0

    def _wait_for_job_completion(
        self, job_id: str, timeout_s: float = 30.0
    ) -> dict[str, Any]:
        """Another live caller already holds the RUNNING claim for `job_id`
        (a concurrent erase_fact_durable() call for the same fact_id) —
        poll for it to reach a terminal status instead of redundantly
        re-running the same steps (which could observe a fact already
        deleted by the other runner and report a false PARTIAL/undetermined
        for a fact that is, in truth, about to be — or already — COMPLETE).

        This is what makes concurrent callers' final reports consistent:
        both end up reading the SAME persisted terminal state rather than
        each computing (and returning) their own, possibly stale, view.
        """
        deadline = time.monotonic() + timeout_s
        job = self._load_job(job_id)
        while job["status"] in (PENDING, RUNNING) and time.monotonic() < deadline:
            time.sleep(0.05)
            job = self._load_job(job_id)
        steps = self._load_steps(job_id)
        tombstone = (
            self._get_tombstone_for(job) if job["status"] == COMPLETE else None
        )
        return self._report(job, outcome=job["status"], tombstone=tombstone, steps=steps)

    def _run_job(self, job_id: str, *, wait_if_running: bool = True) -> dict[str, Any]:
        """Run every not-yet-COMPLETE step for `job_id` and finalize.

        `wait_if_running=True` (the default — used by the live
        `erase_fact_durable()` path) claims the job atomically first; a
        concurrent caller that loses the claim waits for the winner to
        finish instead of racing it. `wait_if_running=False` is used only by
        `resume_incomplete_jobs()`: its whole premise is recovering jobs no
        other live caller is currently processing (e.g. a crash-recovery
        sweep at startup), so it force-claims unconditionally exactly like
        this method always did before — it must never block waiting for a
        runner that no longer exists.
        """
        if wait_if_running:
            if not self._claim_job_for_running(job_id):
                return self._wait_for_job_completion(job_id)
        else:
            self._set_job_status(job_id, RUNNING)

        job = self._load_job(job_id)
        fact_id = job["fact_id"]

        if self._step_status(job_id, "determine_raw") != COMPLETE:
            self._run_determine_raw(job_id, fact_id)
        if self._step_status(job_id, "l1_same_db") != COMPLETE:
            self._run_l1_same_db(job_id, fact_id)
        if self._step_status(job_id, "embeddings") != COMPLETE:
            self._run_embeddings(job_id, fact_id)
        if self._step_status(job_id, "ngram") != COMPLETE:
            self._run_ngram(job_id, fact_id)

        return self._finalize(job_id)

    def _finalize(self, job_id: str) -> dict[str, Any]:
        job = self._load_job(job_id)
        steps = self._load_steps(job_id)
        statuses = {s["step_name"]: s["status"] for s in steps}

        all_complete = all(statuses.get(name) == COMPLETE for name in _STEP_NAMES)
        any_complete = any(statuses.get(name) == COMPLETE for name in _STEP_NAMES)
        residual = job["residual"]

        tombstone = None
        if all_complete and residual == "none":
            outcome = COMPLETE
            # Tombstone is written BEFORE the job row is marked COMPLETE —
            # if the process dies in between, erase_fact_durable()'s
            # tombstone-first check on the next call still reports COMPLETE
            # (write_tombstone() is itself idempotent: first write wins),
            # and a later resume_incomplete_jobs() pass reconciles the job
            # row. The reverse order would let job.status=COMPLETE exist
            # with no tombstone ever written — an unrecoverable false claim
            # of erasure that no resume could detect or repair.
            self._store.write_tombstone(
                job["fact_id"],
                reason=job["reason"],
                actor=job["actor"],
                content_hash=job["content_hash"],
                job_id=job["job_id"],
            )
            tombstone = self._store.get_tombstone_for_job(job["fact_id"], job["job_id"])
        elif all_complete and residual == "raw_original_present":
            # Review finding: the derived layer is provably gone, but
            # l0_raw_memory still holds the original text by design — this
            # must never be reported as COMPLETE, and no completion
            # tombstone is written. is_erased() stays False: the record is
            # not "provably, completely erased" while a raw copy is known
            # to exist. residual == "undetermined" falls through to the
            # PARTIAL branch below — "I don't know" is a transient/resumable
            # state, not this permanent one.
            outcome = RESIDUAL_IMMUTABLE_DATA
        else:
            outcome = PARTIAL if any_complete else FAILED

        self._set_job_status(job_id, outcome)
        job = self._load_job(job_id)

        return self._report(job, outcome=outcome, tombstone=tombstone, steps=steps)

    def _report(
        self,
        job: dict[str, Any],
        *,
        outcome: str,
        tombstone: dict[str, Any] | None,
        steps: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "fact_id": job["fact_id"],
            "job_id": job["job_id"],
            "outcome": outcome,
            "erased_now": outcome == COMPLETE,
            "residual": job.get("residual"),
            "reason": job["reason"],
            "actor": job["actor"],
            "content_hash": (tombstone or {}).get("content_hash"),
            "erased_at": (tombstone or {}).get("erased_at"),
            "steps": {
                s["step_name"]: {
                    "status": s["status"],
                    "detail": json.loads(s["detail"]) if s.get("detail") else None,
                }
                for s in (steps or [])
            },
        }

    # ── public API ────────────────────────────────────────────────────────

    def _residual_data_present(self, fact_id: str) -> bool:
        """True if data this saga is responsible for erasing has (re)appeared
        for `fact_id` — a `facts` row exists again, a same-DB dependent row
        (relations, provenance, fact_mentions, etc. — everything
        l1_same_db/erase_fact_dependents_atomic() purges) still exists, or
        the embeddings/ngram indexes still (or again) hold an entry.

        Used to decide whether a durable job's terminal outcome (COMPLETE /
        RESIDUAL_IMMUTABLE_DATA) can still be trusted as "genuinely,
        currently erased", or whether the underlying data has been
        recreated since (e.g. the fact_id was re-ingested) and a NEW
        generation's saga must run instead of returning a stale cached
        report — post-review hotfix for both the legacy-tombstone
        short-circuit and the fact_id-reuse gap.

        Also gates whether erase_fact_durable() may report NOT_FOUND at
        all (Codex review finding): a legacy/out-of-band deletion that
        removed the `facts` row but left a same-DB dependent row orphaned
        must never be reported NOT_FOUND — that dependent row still needs
        a real saga (l1_same_db) to clean it up.

        If a backend cannot even be checked, this fails toward "residual
        might be present" (never toward silently trusting a stale terminal
        report) — "can't verify absence" is not the same as "verified
        absent", the same principle already applied to the raw-origin
        tri-state (residual="undetermined").
        """
        try:
            if self._store.get_fact_durable(fact_id) is not None:
                return True
        except sqlite3.OperationalError:
            return True
        try:
            if self._store.same_db_dependents_present(fact_id):
                return True
        except sqlite3.Error:
            return True
        try:
            if self._get_embeddings().has_any(fact_id):
                return True
        except Exception:  # noqa: BLE001 — includes the backend being unavailable
            # Same tri-state distinction as _run_embeddings(): a proven
            # absence of a row for fact_id specifically (stdlib sqlite3,
            # no numpy) means there is genuinely nothing there to
            # reappear — returning True unconditionally here would make a
            # base/server install without numpy think residual might be
            # present forever for a fact_id that never had embeddings
            # (even if OTHER facts' embeddings exist), and open a new
            # generation on every repeat call, even though
            # _run_embeddings() would just re-prove the identical
            # applicable=False COMPLETE each time. Only fail toward "might
            # be present" when a row for fact_id itself can't be ruled out.
            if self._embeddings_row_present_for(fact_id, self._resolve_embeddings_db_path()):
                return True
        try:
            if self._ngram.contains(fact_id):
                return True
        except Exception:  # noqa: BLE001
            return True
        return False

    def _get_tombstone_for(self, job: dict[str, Any]) -> dict[str, Any] | None:
        """The tombstone that corroborates THIS SPECIFIC job's COMPLETE
        outcome — never another generation's tombstone for the same
        fact_id. `get_tombstone(fact_id)` (core.memory) returns the LATEST
        tombstone for a fact_id regardless of which job wrote it; with
        generation-aware erasure_jobs (migration 014) a fact_id can have
        several jobs/tombstones over its history, so that is never safe to
        use here — a later generation whose own tombstone write was lost
        (e.g. a crash between write_tombstone() and the job-status COMPLETE
        update) must not silently borrow an EARLIER generation's tombstone
        and be reported as corroborated when it isn't.

        Compatibility: a pre-014 durable job (a real erasure_jobs row that
        reached COMPLETE before job-scoped tombstones existed) recorded its
        own completion tombstone with job_id=NULL — migration 014 backfills
        `generation = 1` for every job that already existed, so generation 1
        is the only generation number a job_id=NULL tombstone can validly
        correspond to. This is deliberately NOT a blanket "any legacy
        tombstone corroborates any job" fallback (that would resurrect the
        exact P1-A bug this hotfix fixed) — it only ever applies to
        generation 1, and only after the caller has already verified a real,
        genuinely-COMPLETE erasure_jobs row exists for this job.
        """
        tombstone = self._store.get_tombstone_for_job(job["fact_id"], job["job_id"])
        if tombstone is not None:
            return tombstone
        if job.get("generation", 1) == 1:
            return self._store.get_tombstone_for_job(job["fact_id"], None)
        return None

    def erase_fact_durable(
        self,
        fact_id: str,
        *,
        reason: str = "data_subject_request",
        actor: str = "operator",
    ) -> dict[str, Any]:
        """The one enforced GDPR Art. 17 erasure entrypoint.

        Idempotent: a fact whose LATEST durable generation already proved
        COMPLETE, or resolved to RESIDUAL_IMMUTABLE_DATA, returns that
        cached report without re-attempting anything — but ONLY once
        _residual_data_present() confirms the underlying data has not
        reappeared since. Two post-review security fixes hinge on this:

          - A bare `erasure_log` tombstone is never, by itself, treated as
            proof of a durable COMPLETE. It must be corroborated by a
            durable erasure_jobs row that itself reached COMPLETE — a
            legacy tombstone (written by the pre-coordinator
            core.erasure.erase_fact() shim, or any other path this
            coordinator didn't run) with no matching durable job is a
            legacy/unverified receipt, not proof. Falling through to a real
            job (re-)cleans any residual embeddings/ngram entries and
            returns an honest, typically non-COMPLETE outcome, WITHOUT
            overwriting the original legacy tombstone (write_tombstone() is
            scoped per job_id — see core.memory.SQLiteGraphStore).
          - A fact_id that was durably erased, then recreated (re-ingested
            under the same ID) and given new embeddings/ngram entries, is
            NOT permanently shielded by its old, terminal generation. A NEW
            generation's job is created and run (see _get_or_create_job()
            and migration 014's generation-aware schema), and the prior
            generation's row is left untouched as immutable history.

        A PENDING/RUNNING/PARTIAL/FAILED active job for the same fact_id is
        resumed in place — steps already COMPLETE are not re-run, so a
        crash between storage backends never repeats already-proven work
        (nor claims success it hasn't re-verified).
        """
        if fact_id in memory.IMMUTABLE_FACT_IDS:
            raise memory.ImmutableStateError(
                f"erase_fact_durable: '{fact_id}' is protected by Ring Zero "
                "(I6) and cannot be deleted"
            )

        latest_job = self._peek_job_row(fact_id)

        if latest_job is not None and latest_job["status"] in _TERMINAL_STATUSES:
            steps = self._load_steps(latest_job["job_id"])
            steps_genuinely_complete = all(s["status"] == COMPLETE for s in steps)
            if steps_genuinely_complete and not self._residual_data_present(fact_id):
                tombstone = (
                    self._get_tombstone_for(latest_job)
                    if latest_job["status"] == COMPLETE else None
                )
                if latest_job["status"] == COMPLETE and tombstone is None:
                    # A job row claims COMPLETE but no tombstone actually
                    # exists — the report must never claim erased_now=False
                    # (already erased) without a real tombstone to point to.
                    # Treat exactly like "residual reappeared": open a new
                    # generation rather than assert an unproven COMPLETE.
                    pass
                else:
                    report = self._report(
                        latest_job, outcome=latest_job["status"],
                        tombstone=tombstone, steps=steps,
                    )
                    report["erased_now"] = False  # already erased BEFORE this call
                    return report
            # Either residual data has reappeared under this fact_id since
            # the last generation's terminal outcome, or that generation's
            # own record doesn't hold up to re-verification — fall through
            # to open/run a new generation below.

        if latest_job is None or latest_job["status"] in _TERMINAL_STATUSES:
            # About to (maybe) open a brand new generation — confirm there
            # is actually something to erase first (a fresh facts row, or
            # residual embeddings/ngram entries with no facts row at all,
            # e.g. the P1-A legacy-tombstone scenario).
            if not self._residual_data_present(fact_id):
                return {
                    "fact_id": fact_id,
                    "job_id": None,
                    "outcome": NOT_FOUND,
                    "erased_now": False,
                    "residual": None,
                    "reason": reason,
                    "actor": actor,
                    "content_hash": None,
                    "erased_at": None,
                    "steps": {},
                }

        job_id = self._get_or_create_job(fact_id, reason, actor)
        return self._run_job(job_id)

    def resume_incomplete_jobs(self) -> list[dict[str, Any]]:
        """Crash recovery sweep: re-run every job not in a terminal state.

        Safe to call repeatedly (e.g. at server startup) — steps already
        COMPLETE are never re-attempted, and a job that resolves to a
        terminal outcome (COMPLETE, or RESIDUAL_IMMUTABLE_DATA — a
        permanent fact about the record, not a transient failure) on this
        pass simply won't be picked up again.
        """
        with self._jobs_db() as conn:
            placeholders = ", ".join("?" for _ in _TERMINAL_STATUSES)
            rows = conn.execute(
                f"SELECT job_id FROM erasure_jobs WHERE status NOT IN ({placeholders}) "  # noqa: S608
                "ORDER BY created_at",
                _TERMINAL_STATUSES,
            ).fetchall()
        return [self._run_job(row["job_id"], wait_if_running=False) for row in rows]

    def get_job_report(self, fact_id: str) -> dict[str, Any] | None:
        """Introspection: the latest job's report for `fact_id`, or None if
        no erasure was ever attempted."""
        job = self._peek_job_row(fact_id)
        if job is None:
            return None
        steps = self._load_steps(job["job_id"])
        tombstone = (
            self._get_tombstone_for(job) if job["status"] == COMPLETE else None
        )
        return self._report(job, outcome=job["status"], tombstone=tombstone, steps=steps)

    def is_erased(self, fact_id: str) -> bool:
        """True only if the LATEST durable generation for `fact_id` reached
        COMPLETE AND that SPECIFIC generation's own tombstone exists (see
        _get_tombstone_for() — never a stale/earlier generation's tombstone)
        AND no residual data has reappeared since. A bare `erasure_log`
        tombstone is never, by itself, sufficient — see erase_fact_durable()'s
        docstring for why: a legacy tombstone with no corroborating durable
        COMPLETE job, or a real-but-stale tombstone left over from an
        earlier generation, must not report True here either."""
        latest_job = self._peek_job_row(fact_id)
        if latest_job is None or latest_job["status"] != COMPLETE:
            return False
        if self._get_tombstone_for(latest_job) is None:
            return False
        return not self._residual_data_present(fact_id)

    def erasure_log(self) -> list[dict[str, Any]]:
        """Art. 30 record of processing — content-free completion
        tombstones only (never attempt receipts)."""
        return self._store.get_tombstones()


# ─── module-level convenience (mirrors core.memory's wrapper functions) ─────
#
# Deliberately NOT cached as a singleton: `ErasureCoordinator()` with no args
# re-reads `memory._GLOBAL_STORE` fresh on every call (exactly like
# core.memory's own `delete_fact_l1()`/`get_fact()` module wrappers), so it
# stays correct under this codebase's test-suite convention of monkeypatching
# `memory._GLOBAL_STORE` per test — a cached instance would freeze onto
# whichever store existed the first time this was ever called. The DDL in
# ErasureCoordinator.__init__ is idempotent (CREATE TABLE IF NOT EXISTS), so
# constructing fresh each call costs a few no-op statements, not a schema
# rebuild. `_default_coordinator`, when set (tests only — see
# tests/conftest.py's leakage guard), overrides this for explicit DI.
_default_coordinator: ErasureCoordinator | None = None


def get_coordinator() -> ErasureCoordinator:
    if _default_coordinator is not None:
        return _default_coordinator
    return ErasureCoordinator()


def erase_fact_durable(
    fact_id: str,
    *,
    reason: str = "data_subject_request",
    actor: str = "operator",
) -> dict[str, Any]:
    return get_coordinator().erase_fact_durable(fact_id, reason=reason, actor=actor)


def resume_incomplete_jobs() -> list[dict[str, Any]]:
    return get_coordinator().resume_incomplete_jobs()


def get_job_report(fact_id: str) -> dict[str, Any] | None:
    return get_coordinator().get_job_report(fact_id)


def is_erased(fact_id: str) -> bool:
    return get_coordinator().is_erased(fact_id)


def erasure_log() -> list[dict[str, Any]]:
    return get_coordinator().erasure_log()


__all__ = [
    "ErasureCoordinator",
    "get_coordinator",
    "erase_fact_durable",
    "resume_incomplete_jobs",
    "get_job_report",
    "is_erased",
    "erasure_log",
    "PENDING",
    "RUNNING",
    "COMPLETE",
    "PARTIAL",
    "FAILED",
    "NOT_FOUND",
    "RESIDUAL_IMMUTABLE_DATA",
]
