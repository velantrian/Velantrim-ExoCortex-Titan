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
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from core import memory
from core.embedding_store import EmbeddingStore
from core.ngram_index import NGramIndex

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

# Terminal job statuses that resume_incomplete_jobs() should never re-pick
# up — COMPLETE because there's nothing left to do, RESIDUAL_IMMUTABLE_DATA
# because the residual is a permanent fact about the record (re-running
# would just recompute the identical outcome forever).
_TERMINAL_STATUSES = (COMPLETE, RESIDUAL_IMMUTABLE_DATA)

_STEP_NAMES = ("determine_raw", "l1_same_db", "embeddings", "ngram")

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS erasure_jobs (
    job_id        TEXT PRIMARY KEY,
    fact_id       TEXT NOT NULL,
    reason        TEXT NOT NULL,
    actor         TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'PENDING',
    residual      TEXT,
    content_hash  TEXT,
    error         TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_erasure_jobs_fact   ON erasure_jobs(fact_id);
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
        self._embeddings = embedding_store or EmbeddingStore()
        self._ngram = ngram_index or NGramIndex()
        self.jobs_db_path = jobs_db_path or self._store.db_path
        self._ensure_schema()

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

    # ── job ledger helpers ───────────────────────────────────────────────

    def _peek_job_row(self, fact_id: str) -> dict[str, Any] | None:
        with self._jobs_db() as conn:
            row = conn.execute(
                "SELECT * FROM erasure_jobs WHERE fact_id = ? "
                "ORDER BY created_at DESC LIMIT 1",
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
        # Re-running an already-COMPLETE job is safe (every step is a no-op
        # replay and _finalize()/write_tombstone() are both idempotent), so
        # any existing job for this fact_id — regardless of status — is
        # resumed rather than duplicated.
        existing = self._peek_job_row(fact_id)
        if existing is not None:
            return existing["job_id"]
        job_id = f"erj_{uuid.uuid4().hex[:16]}"
        now = _now()
        with self._jobs_db() as conn:
            conn.execute(
                "INSERT INTO erasure_jobs "
                "(job_id, fact_id, reason, actor, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (job_id, fact_id, reason, actor, PENDING, now, now),
            )
            for step_name in _STEP_NAMES:
                conn.execute(
                    "INSERT INTO erasure_job_steps (step_id, job_id, step_name, status) "
                    "VALUES (?, ?, ?, ?)",
                    (f"{job_id}_{step_name}", job_id, step_name, PENDING),
                )
        return job_id

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
            deleted = self._embeddings.purge_node(fact_id)
            still_present = self._embeddings.has_any(fact_id)
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

    def _run_job(self, job_id: str) -> dict[str, Any]:
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
            )
            tombstone = self._store.get_tombstone(job["fact_id"])
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

    def erase_fact_durable(
        self,
        fact_id: str,
        *,
        reason: str = "data_subject_request",
        actor: str = "operator",
    ) -> dict[str, Any]:
        """The one enforced GDPR Art. 17 erasure entrypoint.

        Idempotent: a fact already proven COMPLETE, or already resolved to
        RESIDUAL_IMMUTABLE_DATA, returns the cached report without
        re-attempting anything. A PENDING/RUNNING/PARTIAL/FAILED prior job
        for the same fact_id is resumed in place — steps already COMPLETE
        are not re-run, so a crash between storage backends never repeats
        already-proven work (nor claims success it hasn't re-verified).
        """
        if fact_id in memory.IMMUTABLE_FACT_IDS:
            raise memory.ImmutableStateError(
                f"erase_fact_durable: '{fact_id}' is protected by Ring Zero "
                "(I6) and cannot be deleted"
            )

        tombstone = self._store.get_tombstone(fact_id)
        if tombstone is not None:
            job_row = self._peek_job_row(fact_id)
            job = job_row or {
                "fact_id": fact_id, "job_id": None, "reason": tombstone.get("reason"),
                "actor": tombstone.get("actor"), "residual": None,
            }
            report = self._report(job, outcome=COMPLETE, tombstone=tombstone)
            report["erased_now"] = False  # already erased BEFORE this call
            return report

        existing_job = self._peek_job_row(fact_id)
        if existing_job is not None and existing_job["status"] == RESIDUAL_IMMUTABLE_DATA:
            # Terminal and permanent — residual won't change from a re-run,
            # so skip straight to the cached report instead of redoing work.
            steps = self._load_steps(existing_job["job_id"])
            report = self._report(
                existing_job, outcome=RESIDUAL_IMMUTABLE_DATA, tombstone=None, steps=steps
            )
            report["erased_now"] = False
            return report

        if existing_job is None:
            try:
                fact_exists = self._store.get_fact_durable(fact_id) is not None
            except sqlite3.OperationalError:
                # Can't even tell if it exists — do NOT fabricate NOT_FOUND.
                # Fall through to a real job; determine_raw() will hit the
                # same error and honestly record residual="undetermined".
                fact_exists = True
            if not fact_exists:
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
        return [self._run_job(row["job_id"]) for row in rows]

    def get_job_report(self, fact_id: str) -> dict[str, Any] | None:
        """Introspection: the latest job's report for `fact_id`, or None if
        no erasure was ever attempted."""
        job = self._peek_job_row(fact_id)
        if job is None:
            return None
        steps = self._load_steps(job["job_id"])
        tombstone = (
            self._store.get_tombstone(fact_id) if job["status"] == COMPLETE else None
        )
        return self._report(job, outcome=job["status"], tombstone=tombstone, steps=steps)

    def is_erased(self, fact_id: str) -> bool:
        """True only if a COMPLETE erasure tombstone exists — an attempt
        receipt (PENDING/RUNNING/PARTIAL/FAILED) is never enough."""
        return self._store.get_tombstone(fact_id) is not None

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
