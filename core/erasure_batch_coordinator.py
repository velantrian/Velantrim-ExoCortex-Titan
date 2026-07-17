# core/erasure_batch_coordinator.py
# VELANTRIM Titan — FORGET_ALL durable, resumable GDPR Art. 17 BATCH saga
#
# core.forgetting.ForgettingEngine.forget_all() (the FORGET_ALL MCP tool)
# has always run a single best-effort SQLite transaction: query `facts`
# for a user_id match, delete every matching row in one pass, with no
# durable record of WHICH fact_ids it decided to erase before it started
# deleting. A crash mid-batch loses that decision entirely — a "resumed"
# run would re-query `facts` from scratch, which can legitimately return
# a DIFFERENT set by then (a fact concurrently ingested for the same
# user, a fact whose state changed under the filter) and either silently
# erase the wrong set or claim success over a batch that never finished.
#
# This module is the enforced batch entrypoint, applying the same
# tombstone-vs-attempt-receipt separation P0-B (migrations 013/014,
# core/erasure_coordinator.py) built for single-fact erasure one level up:
#
#   - erasure_batches is the durable BATCH RECEIPT, written once, BEFORE
#     any deletion is attempted, in the SAME transaction, on the SAME
#     connection, as the SELECT that produces its membership list (see
#     _create_batch_snapshot()) — a separate connection for the read
#     would NOT be atomic with the write.
#   - erasure_batch_items is the durable SNAPSHOT — one row per fact_id
#     selected by the batch's filter. This is the one and only
#     membership list this batch will ever process: a resume (crash
#     recovery, or a repeat call with the same idempotency_key) replays
#     exactly these rows and NEVER re-queries `facts` by user_id again. A
#     fact ingested for the same user_id AFTER the snapshot was taken is
#     out of scope for THIS batch by construction. `snapshot_hash` (over
#     the ordered (fact_id, epistemic_state) pairs) is checked before
#     every processing pass — a mismatch (e.g. an out-of-band row
#     inserted/removed directly against erasure_batch_items) fails the
#     batch closed (FAILED) rather than silently processing a tampered
#     membership list.
#   - Each item is erased by handing its fact_id to the existing,
#     unmodified core.erasure_coordinator.erase_fact_durable() — per-fact
#     durability/resumability/residual-detection/idempotency is inherited,
#     never re-implemented.
#   - ImmutableCore is NOT an automatic GDPR exemption: erase_fact_durable()
#     itself only refuses the two true Ring Zero literals
#     (memory.IMMUTABLE_FACT_IDS — VALUES_CORE/RING_ZERO). A fact matched
#     by the user_id filter (i.e. associated with a data subject) whose
#     epistemic_state is 'ImmutableCore' but whose fact_id is NOT one of
#     those literals is either a genuine upstream architectural violation
#     (a P0-D/ESM enforcement gap this CR does not touch) or a residual
#     write from before that enforcement existed. Either way, silently
#     skipping it — the old core.forgetting behavior — could hide personal
#     data forever with no alarm. This coordinator flags it as a
#     COMPLIANCE finding instead of deleting OR silently skipping it.
#
#   - EXECUTION status (`erasure_batches.status`) and COMPLIANCE status
#     (`erasure_batches.compliance_status`) are two INDEPENDENT columns —
#     a compliance violation must never block retryable items from being
#     retried, and a batch with retryable work left must never look
#     "done" just because a violation was already found. See "Batch state
#     machine" below.
#   - idempotency_key is bound to a canonical request fingerprint (over
#     user_id/reason/actor/force/scope). Reusing a key with a DIFFERENT
#     fingerprint returns IDEMPOTENCY_CONFLICT — it never runs, resumes,
#     or reveals the existing batch's contents.
#   - Crash-recovery reclaims a RUNNING batch ONLY via a real lease CAS
#     (`runner_id` + `lease_expires_at`), never a bare RUNNING->RUNNING
#     status write — see _claim_batch_for_running(). A live runner
#     renews its lease after every processed item; losing the lease mid-
#     run stops processing immediately rather than finalizing over
#     another runner's concurrent work.
#
# See migrations/015_erasure_batches.sql for the schema and rationale, and
# the "Batch state machine" section below for the full status model.
#
# ── Batch state machine (EXECUTION status) ───────────────────────────────
#
#   PENDING --(claim)--> RUNNING --(finalize)--> one of:
#       COMPLETE                    every item COMPLETE / NOT_FOUND /
#                                   SKIPPED_RING_ZERO / CRITICAL_COMPLIANCE_
#                                   VIOLATION — nothing RETRYABLE left.
#       COMPLETE_WITH_RESIDUAL      as above, but >=1 item is
#                                   RESIDUAL_IMMUTABLE_DATA (L0 raw text —
#                                   the SAME accepted, tracked limitation
#                                   erase_fact_durable() itself reports).
#       PARTIAL                     >=1 item still PENDING/PARTIAL/FAILED —
#                                   resumable; a later run/resume call
#                                   retries ONLY those items.
#
#   COMPLETE/COMPLETE_WITH_RESIDUAL are the only TERMINAL execution
#   statuses. PARTIAL/FAILED/PENDING/RUNNING(crashed) are all resumable —
#   see resume_incomplete_batches().
#
# ── Compliance status (separate column, independent of the above) ───────
#
#   None -> CRITICAL_COMPLIANCE_VIOLATION: set (and never cleared) the
#   moment ANY item is found to be a personal fact inside ImmutableCore,
#   REGARDLESS of the batch's execution status at that moment. A batch
#   that is simultaneously PARTIAL (other items still retryable) AND
#   CRITICAL_COMPLIANCE_VIOLATION keeps retrying those other items on
#   every resume — the violation is surfaced immediately, not hidden
#   behind "still running", but it also never blocks the rest of the
#   batch from finishing its own, unrelated work.
#
# ── Report fields (see _report()) ────────────────────────────────────────
#
#   operation_finished: bool — True iff the execution status reached a
#       terminal value (COMPLETE or COMPLETE_WITH_RESIDUAL). Says nothing
#       about compliance.
#   erasure_complete / success: bool — True ONLY when operation_finished
#       AND status == COMPLETE (no residual) AND compliance_status is
#       None. COMPLETE_WITH_RESIDUAL is a real, tracked, accepted outcome
#       — but it is NEVER reported as plain "success", since personal data
#       (the L0 raw origin) is known to still exist.

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any

from core import memory
from core.erasure_coordinator import (
    COMPLETE,
    ErasureCoordinator,
    FAILED,
    NOT_FOUND,
    PARTIAL,
    RESIDUAL_IMMUTABLE_DATA,
)

# ─── batch-level EXECUTION statuses ──────────────────────────────────────────
PENDING = "PENDING"
RUNNING = "RUNNING"
COMPLETE_WITH_RESIDUAL = "COMPLETE_WITH_RESIDUAL"

# ─── batch-level COMPLIANCE status (separate column — see module docstring) ──
CRITICAL_COMPLIANCE_VIOLATION = "CRITICAL_COMPLIANCE_VIOLATION"

# ─── pseudo-outcomes returned WITHOUT ever touching the durable ledger ───────
REFUSED = "REFUSED"
DRY_RUN = "DRY_RUN"
IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"

# ─── item-level statuses own to this module; per-fact outcomes from
# erase_fact_durable() — COMPLETE/PARTIAL/FAILED/NOT_FOUND/
# RESIDUAL_IMMUTABLE_DATA — pass through unchanged as item status ────────────
SKIPPED_RING_ZERO = "SKIPPED_RING_ZERO"

_TERMINAL_BATCH_STATUSES = (COMPLETE, COMPLETE_WITH_RESIDUAL)
_RUNNABLE_BATCH_STATUSES = (PENDING, PARTIAL, FAILED)
_ITEM_RETRYABLE_STATUSES = (PENDING, PARTIAL, FAILED)

_LEASE_TTL_SECONDS = 60

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS erasure_batches (
    batch_id            TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    reason              TEXT NOT NULL,
    actor               TEXT NOT NULL,
    force               INTEGER NOT NULL DEFAULT 0,
    scope               TEXT,
    idempotency_key     TEXT,
    request_fingerprint TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'PENDING',
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

CREATE TABLE IF NOT EXISTS erasure_batch_items (
    item_id                       TEXT PRIMARY KEY,
    batch_id                      TEXT NOT NULL REFERENCES erasure_batches(batch_id),
    fact_id                       TEXT NOT NULL,
    epistemic_state_at_snapshot   TEXT NOT NULL,
    status                        TEXT NOT NULL DEFAULT 'PENDING',
    job_id                        TEXT,
    detail                        TEXT,
    created_at                    TEXT NOT NULL,
    updated_at                    TEXT NOT NULL,
    UNIQUE(batch_id, fact_id)
);

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
"""

_INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_batches_idempotency
    ON erasure_batches(idempotency_key)
    WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_erasure_batches_status ON erasure_batches(status);
CREATE INDEX IF NOT EXISTS idx_erasure_batches_user ON erasure_batches(user_id);
CREATE INDEX IF NOT EXISTS idx_erasure_batch_items_batch ON erasure_batch_items(batch_id);
CREATE INDEX IF NOT EXISTS idx_erasure_batch_items_status ON erasure_batch_items(batch_id, status);
CREATE INDEX IF NOT EXISTS idx_erasure_batch_force_receipts_batch
    ON erasure_batch_force_receipts(batch_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _lease_expiry(ttl_seconds: int = _LEASE_TTL_SECONDS) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()


def _request_fingerprint(
    *, user_id: str, reason: str, actor: str, force: bool, scope: str | None,
) -> str:
    """Canonical identity of a logical FORGET_ALL request. Two calls with the
    SAME idempotency_key but a DIFFERENT fingerprint are different requests
    that happen to share a key — resumed as one and the same batch would
    silently let one caller's request (e.g. a different user_id or scope)
    run/resume/reveal another's. See forget_all_durable()."""
    payload = {
        "user_id": user_id, "reason": reason, "actor": actor,
        "force": bool(force), "scope": scope,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


class BatchErasureCoordinator:
    """Durable, resumable GDPR Art. 17 BATCH erasure saga (FORGET_ALL).

    Fully dependency-injectable, mirroring core.erasure_coordinator's own
    design: pass a real, temp-file-backed `store` / `coordinator` in tests
    instead of the process-global singletons.
    """

    def __init__(
        self,
        store: memory.SQLiteGraphStore | None = None,
        coordinator: ErasureCoordinator | None = None,
        jobs_db_path: str | None = None,
    ) -> None:
        self._store = store or memory._GLOBAL_STORE
        self._coordinator = coordinator or ErasureCoordinator(store=self._store)
        self.jobs_db_path = jobs_db_path or self._store.db_path
        if self.jobs_db_path != self._store.db_path:
            # The durable snapshot SELECT and its batch/item INSERTs must run
            # in the SAME transaction on the SAME connection to be atomic
            # (see _create_batch_snapshot()) — a jobs ledger in a different
            # file cannot see the `facts` table it needs to snapshot, and
            # splitting the read and the write across two connections would
            # reopen exactly the non-atomic race this design exists to close.
            raise ValueError(
                "BatchErasureCoordinator requires jobs_db_path == store.db_path"
            )
        self._ensure_schema()

    # ── schema ────────────────────────────────────────────────────────────

    @contextmanager
    def _jobs_db(self):
        conn = sqlite3.connect(self.jobs_db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 30000")
        # Orphan protection: erasure_batch_items/erasure_batch_force_receipts
        # both REFERENCE erasure_batches(batch_id) — without this PRAGMA
        # (OFF by default in stdlib sqlite3), SQLite silently accepts an
        # INSERT for a batch_id that doesn't exist, which would let a bug
        # elsewhere (or direct DB manipulation) create ledger rows this
        # coordinator can never durably account for.
        conn.execute("PRAGMA foreign_keys = ON")
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
            for _stmt in _INDEX_SQL.strip().split(";"):
                _stmt = _stmt.strip()
                if _stmt:
                    conn.execute(_stmt)

    # ── durable ledger helpers ───────────────────────────────────────────

    def _load_batch(self, batch_id: str) -> dict[str, Any]:
        with self._jobs_db() as conn:
            row = conn.execute(
                "SELECT * FROM erasure_batches WHERE batch_id = ?", (batch_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"erasure batch '{batch_id}' not found")
        return dict(row)

    def _load_items(self, batch_id: str) -> list[dict[str, Any]]:
        with self._jobs_db() as conn:
            rows = conn.execute(
                "SELECT * FROM erasure_batch_items WHERE batch_id = ? ORDER BY fact_id",
                (batch_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def _find_batch_by_idempotency_key(self, key: str) -> dict[str, Any] | None:
        with self._jobs_db() as conn:
            row = conn.execute(
                "SELECT * FROM erasure_batches WHERE idempotency_key = ?", (key,)
            ).fetchone()
        return dict(row) if row else None

    def _set_item_status(
        self,
        batch_id: str,
        fact_id: str,
        status: str,
        *,
        job_id: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        with self._jobs_db() as conn:
            conn.execute(
                "UPDATE erasure_batch_items SET status = ?, "
                "job_id = COALESCE(?, job_id), detail = ?, updated_at = ? "
                "WHERE batch_id = ? AND fact_id = ?",
                (
                    status, job_id,
                    json.dumps(detail) if detail is not None else None,
                    _now(), batch_id, fact_id,
                ),
            )

    @staticmethod
    def _compute_snapshot_hash(items: list[dict[str, Any]]) -> str:
        ordered = sorted(items, key=lambda i: i["fact_id"])
        payload = [[i["fact_id"], i["epistemic_state_at_snapshot"]] for i in ordered]
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    def _snapshot_integrity_ok(self, batch: dict[str, Any], items: list[dict[str, Any]]) -> bool:
        if len(items) != batch["items_total"]:
            return False
        return self._compute_snapshot_hash(items) == batch["snapshot_hash"]

    # ── snapshot (durable, taken exactly once per batch) ─────────────────

    def _create_batch_snapshot(
        self,
        *,
        user_id: str,
        reason: str,
        actor: str,
        force: bool,
        scope: str | None,
        idempotency_key: str | None,
        actor_capability: str,
        request_fingerprint: str,
    ) -> str:
        """Select candidate facts and durably persist the batch + its full
        item snapshot in ONE atomic transaction, on ONE connection. The
        SELECT runs directly against `facts` on THIS SAME connection
        (memory.FACTS_BY_USER_FILTER_SQL) — never via a separate connection
        — so it is genuinely part of the same transaction as the INSERTs
        that follow it, not merely "close in time". This is the only time
        `facts` is ever queried by user_id for this batch — every
        subsequent run/resume operates purely on the persisted
        erasure_batch_items rows created here.
        """
        batch_id = f"eb_{uuid.uuid4().hex[:16]}"
        now = _now()
        try:
            with self._jobs_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    rows = conn.execute(
                        memory.FACTS_BY_USER_FILTER_SQL, (user_id, user_id)
                    ).fetchall()
                    candidates = [{"fact_id": r[0], "epistemic_state": r[1]} for r in rows]
                    items_for_hash = [
                        {
                            "fact_id": c["fact_id"],
                            "epistemic_state_at_snapshot": c["epistemic_state"],
                        }
                        for c in candidates
                    ]
                    snapshot_hash = self._compute_snapshot_hash(items_for_hash)

                    conn.execute(
                        "INSERT INTO erasure_batches "
                        "(batch_id, user_id, reason, actor, force, scope, idempotency_key, "
                        "request_fingerprint, status, items_total, snapshot_hash, "
                        "snapshot_at, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            batch_id, user_id, reason, actor, int(force), scope or None,
                            idempotency_key, request_fingerprint, PENDING, len(candidates),
                            snapshot_hash, now, now, now,
                        ),
                    )
                    for c in candidates:
                        conn.execute(
                            "INSERT INTO erasure_batch_items "
                            "(item_id, batch_id, fact_id, epistemic_state_at_snapshot, "
                            "status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (
                                f"{batch_id}_{c['fact_id']}", batch_id, c["fact_id"],
                                c["epistemic_state"], PENDING, now, now,
                            ),
                        )
                    if force:
                        conn.execute(
                            "INSERT INTO erasure_batch_force_receipts "
                            "(receipt_id, batch_id, actor, actor_capability, scope, "
                            "user_id, reason, authorized_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (
                                f"efr_{uuid.uuid4().hex[:16]}", batch_id, actor,
                                actor_capability, scope, user_id, reason, now,
                            ),
                        )
                except sqlite3.IntegrityError:
                    conn.rollback()
                    raise
                else:
                    conn.commit()
        except sqlite3.IntegrityError:
            # Lost a create race on idempotency_key: a concurrent caller
            # using the SAME key already committed its own snapshot first.
            # Adopt the winner's batch_id — forget_all_durable() verifies
            # its request_fingerprint before ever running/revealing it.
            if idempotency_key:
                existing = self._find_batch_by_idempotency_key(idempotency_key)
                if existing is not None:
                    return existing["batch_id"]
            raise
        return batch_id

    # ── per-item processing ───────────────────────────────────────────────

    def _process_item(self, batch: dict[str, Any], item: dict[str, Any]) -> None:
        fact_id = item["fact_id"]
        epistemic_state = item["epistemic_state_at_snapshot"]

        if fact_id in memory.IMMUTABLE_FACT_IDS:
            # True Ring Zero literal (I6) — structurally never personal
            # data, never deletable. The one legitimate "not applicable".
            self._set_item_status(
                batch["batch_id"], fact_id, SKIPPED_RING_ZERO,
                detail={"reason": "ring_zero_literal_never_personal_data"},
            )
            return

        if epistemic_state == "ImmutableCore":
            # Matched the user_id/source filter -> associated with a data
            # subject by definition, yet sitting in ImmutableCore, which is
            # documented (core/forgetting.py I-F1) as reserved for Ring
            # Zero only. ImmutableCore is NOT an automatic GDPR exemption:
            # flag it for mandatory compliance review rather than silently
            # skipping it (the old behavior) or deleting it (a second,
            # independent invariant violation this CR does not attempt to
            # adjudicate — see core/erasure.py, P0-D/ESM are out of scope).
            self._set_item_status(
                batch["batch_id"], fact_id, CRITICAL_COMPLIANCE_VIOLATION,
                detail={
                    "reason": "personal_fact_in_immutable_core",
                    "epistemic_state": epistemic_state,
                },
            )
            return

        report = self._coordinator.erase_fact_durable(
            fact_id, reason=batch["reason"], actor=batch["actor"],
        )
        self._set_item_status(
            batch["batch_id"], fact_id, report["outcome"],
            job_id=report.get("job_id"), detail=report,
        )

    # ── orchestration / lease-based ownership ─────────────────────────────

    def _claim_batch_for_running(
        self, batch_id: str, *, allow_stale_running: bool, runner_id: str,
    ) -> bool:
        """Atomically claim `batch_id` for execution.

        `allow_stale_running=False` (live caller path) claims FROM
        (PENDING, PARTIAL, FAILED) ONLY — a RUNNING batch is currently
        owned by another live runner and is never reclaimed here; the
        caller waits for it instead (_wait_for_batch_completion()).

        `allow_stale_running=True` (crash-recovery path,
        resume_incomplete_batches()) ADDITIONALLY claims FROM RUNNING, but
        ONLY when that row's OWN lease has expired
        (`lease_expires_at < now`) — never a bare "status='RUNNING' ->
        status='RUNNING'" write, which would let two concurrent recovery
        workers (or a recovery worker racing a still-alive live runner)
        both believe they won the claim: SQLite serializes this UPDATE's
        WHERE-clause evaluation against the CURRENT row for each caller in
        turn, so the FIRST winner's write extends lease_expires_at into
        the future, and every LOSING caller's own (already-serialized)
        UPDATE then sees a lease that is no longer stale and matches zero
        rows.
        """
        now = _now()
        lease = _lease_expiry()
        with self._jobs_db() as conn:
            if allow_stale_running:
                cur = conn.execute(
                    "UPDATE erasure_batches SET status = ?, runner_id = ?, "
                    "lease_expires_at = ?, updated_at = ? "
                    "WHERE batch_id = ? AND ("
                    "  status IN (?, ?, ?) "
                    "  OR (status = ? AND lease_expires_at IS NOT NULL AND lease_expires_at < ?)"
                    ")",
                    (
                        RUNNING, runner_id, lease, now, batch_id,
                        PENDING, PARTIAL, FAILED, RUNNING, now,
                    ),
                )
            else:
                cur = conn.execute(
                    "UPDATE erasure_batches SET status = ?, runner_id = ?, "
                    "lease_expires_at = ?, updated_at = ? "
                    "WHERE batch_id = ? AND status IN (?, ?, ?)",
                    (RUNNING, runner_id, lease, now, batch_id, PENDING, PARTIAL, FAILED),
                )
        return cur.rowcount > 0

    def _renew_lease(self, batch_id: str, runner_id: str) -> bool:
        """Heartbeat: called after every processed item so a genuinely-alive
        runner's lease never goes stale mid-run. Returns False if this
        runner no longer owns the row (lost the lease, or someone else
        already reclaimed it) — the caller must stop processing immediately
        rather than risk finalizing over a concurrent owner's writes."""
        with self._jobs_db() as conn:
            cur = conn.execute(
                "UPDATE erasure_batches SET lease_expires_at = ?, updated_at = ? "
                "WHERE batch_id = ? AND runner_id = ? AND status = ?",
                (_lease_expiry(), _now(), batch_id, runner_id, RUNNING),
            )
        return cur.rowcount > 0

    def _cas_batch_status(
        self,
        batch_id: str,
        runner_id: str,
        status: str,
        *,
        compliance_status: str | None = None,
        error: str | None = None,
    ) -> bool:
        """CAS the batch's EXECUTION status (and, if given, sets/keeps the
        separate COMPLIANCE status — COALESCE means a previously-set
        violation is never cleared by a round that found none this time)
        — scoped to `runner_id` still owning the row, so a runner that lost
        its lease mid-processing can never overwrite whatever the new
        owner has since written."""
        with self._jobs_db() as conn:
            cur = conn.execute(
                "UPDATE erasure_batches SET status = ?, "
                "compliance_status = COALESCE(?, compliance_status), "
                "error = COALESCE(?, error), updated_at = ? "
                "WHERE batch_id = ? AND runner_id = ?",
                (status, compliance_status, error, _now(), batch_id, runner_id),
            )
        return cur.rowcount > 0

    def _wait_for_batch_completion(self, batch_id: str, timeout_s: float = 30.0) -> dict[str, Any]:
        """Another live caller already holds the RUNNING claim (e.g. a
        concurrent forget_all_durable() call for the same idempotency_key)
        — poll for it to reach a terminal EXECUTION status rather than
        redundantly reprocessing the same snapshot."""
        deadline = time.monotonic() + timeout_s
        batch = self._load_batch(batch_id)
        while batch["status"] in (PENDING, RUNNING) and time.monotonic() < deadline:
            time.sleep(0.05)
            batch = self._load_batch(batch_id)
        return self._report(batch, self._load_items(batch_id))

    def _run_batch(self, batch_id: str, *, wait_if_running: bool = True) -> dict[str, Any] | None:
        """Process every not-yet-terminal item in `batch_id`'s ORIGINAL
        snapshot and finalize. Never re-queries `facts` by user_id.

        `wait_if_running=True` (live caller path): if the batch is already
        terminal, its cached report is returned immediately (idempotent
        repeat call — no reprocessing). If another live caller holds the
        RUNNING claim, this waits for it instead of racing it.

        `wait_if_running=False` is used only by resume_incomplete_batches()
        (crash-recovery sweep): it may additionally reclaim a RUNNING batch
        whose lease has expired, and returns None if the claim is lost to
        a concurrent transition, rather than proceeding.
        """
        runner_id = f"run_{uuid.uuid4().hex[:12]}"
        claimed = self._claim_batch_for_running(
            batch_id, allow_stale_running=not wait_if_running, runner_id=runner_id,
        )
        if not claimed:
            current = self._load_batch(batch_id)
            if current["status"] in _TERMINAL_BATCH_STATUSES:
                return self._report(current, self._load_items(batch_id))
            if wait_if_running:
                return self._wait_for_batch_completion(batch_id)
            return None

        batch = self._load_batch(batch_id)
        items = self._load_items(batch_id)

        if not self._snapshot_integrity_ok(batch, items):
            # Fail closed: the durable snapshot no longer matches what was
            # hashed at creation time (e.g. an out-of-band row inserted/
            # removed against erasure_batch_items). Refuse to process
            # against a membership list that cannot be proven intact.
            self._cas_batch_status(
                batch_id, runner_id, FAILED, error="snapshot_integrity_check_failed",
            )
            return self._report(self._load_batch(batch_id), self._load_items(batch_id))

        for item in items:
            if item["status"] in _ITEM_RETRYABLE_STATUSES:
                self._process_item(batch, item)
                if not self._renew_lease(batch_id, runner_id):
                    # Lost ownership mid-processing — stop immediately. Do
                    # NOT finalize: the current owner (if any) may be
                    # concurrently writing its own results right now.
                    return self._report(self._load_batch(batch_id), self._load_items(batch_id))

        return self._finalize_batch(batch_id, runner_id)

    def _finalize_batch(self, batch_id: str, runner_id: str) -> dict[str, Any]:
        items = self._load_items(batch_id)
        statuses = [i["status"] for i in items]

        retryable = [s for s in statuses if s in _ITEM_RETRYABLE_STATUSES]
        critical = any(s == CRITICAL_COMPLIANCE_VIOLATION for s in statuses)
        residual = any(s == RESIDUAL_IMMUTABLE_DATA for s in statuses)

        # EXECUTION status is computed purely from retryable/residual items
        # — a CRITICAL_COMPLIANCE_VIOLATION item is terminal-for-itself (it
        # is never re-processed, see _process_item()) and therefore never
        # blocks the batch's execution status from reaching a terminal
        # value, exactly like COMPLETE_WITH_RESIDUAL's `residual`. Whether
        # ANY item is a compliance violation is tracked entirely separately
        # below (compliance_status), so a still-PARTIAL batch (other items
        # genuinely still pending/failed) is not prevented from being
        # resumed just because a violation was also found.
        if retryable:
            outcome = PARTIAL
        elif residual:
            outcome = COMPLETE_WITH_RESIDUAL
        else:
            outcome = COMPLETE

        compliance_status = CRITICAL_COMPLIANCE_VIOLATION if critical else None
        self._cas_batch_status(
            batch_id, runner_id, outcome, compliance_status=compliance_status,
        )
        return self._report(self._load_batch(batch_id), items)

    # ── reporting ─────────────────────────────────────────────────────────

    def _report(self, batch: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
        critical_items = [
            i["fact_id"] for i in items if i["status"] == CRITICAL_COMPLIANCE_VIOLATION
        ]
        compliance_status = batch.get("compliance_status")
        operation_finished = batch["status"] in _TERMINAL_BATCH_STATUSES
        erasure_complete = (
            operation_finished
            and batch["status"] == COMPLETE
            and compliance_status is None
        )
        return {
            "batch_id": batch["batch_id"],
            "user_id": batch["user_id"],
            "reason": batch["reason"],
            "actor": batch["actor"],
            "force": bool(batch["force"]),
            "scope": batch["scope"],
            "idempotency_key": batch["idempotency_key"],
            "outcome": batch["status"],
            # operation_finished: no more retryable items — independent of
            # compliance. erasure_complete/success: the narrower, honest
            # "fully, provably erased, nothing outstanding at all" signal —
            # COMPLETE_WITH_RESIDUAL and any compliance violation are BOTH
            # excluded from this, on purpose (see module docstring).
            "operation_finished": operation_finished,
            "erasure_complete": erasure_complete,
            "success": erasure_complete,
            "compliance_status": compliance_status,
            "critical_compliance_violation": compliance_status == CRITICAL_COMPLIANCE_VIOLATION,
            "critical_items": critical_items,
            "items_total": batch["items_total"],
            "items": [
                {
                    "fact_id": i["fact_id"],
                    "epistemic_state_at_snapshot": i["epistemic_state_at_snapshot"],
                    "status": i["status"],
                    "job_id": i["job_id"],
                }
                for i in items
            ],
            "snapshot_hash": batch["snapshot_hash"],
            "snapshot_integrity_ok": self._snapshot_integrity_ok(batch, items),
            "snapshot_at": batch["snapshot_at"],
            "created_at": batch["created_at"],
            "updated_at": batch["updated_at"],
            "error": batch.get("error"),
        }

    def _refused(
        self, reason: str, *, user_id: str, force: bool, scope: str | None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        return {
            "batch_id": None,
            "user_id": user_id,
            "reason": reason,
            "outcome": REFUSED,
            "operation_finished": False,
            "erasure_complete": False,
            "success": False,
            "compliance_status": None,
            "critical_compliance_violation": False,
            "critical_items": [],
            "force": force,
            "scope": scope,
            "idempotency_key": idempotency_key,
            "items_total": 0,
            "items": [],
        }

    def _idempotency_conflict(self, idempotency_key: str) -> dict[str, Any]:
        """A repeat call reused `idempotency_key` with a DIFFERENT canonical
        request fingerprint (different user_id/reason/actor/force/scope).
        This NEVER runs, resumes, or reveals the existing batch's contents
        — not even its batch_id — since the caller has proven nothing about
        their relationship to whatever request originally claimed this key.
        """
        return {
            "batch_id": None,
            "user_id": None,
            "reason": "idempotency_key_conflict",
            "outcome": IDEMPOTENCY_CONFLICT,
            "operation_finished": False,
            "erasure_complete": False,
            "success": False,
            "compliance_status": None,
            "critical_compliance_violation": False,
            "critical_items": [],
            "idempotency_key": idempotency_key,
            "items_total": 0,
            "items": [],
        }

    def _preview(self, user_id: str) -> dict[str, Any]:
        candidates = self._store.list_fact_ids_by_user_durable(user_id)
        ring_zero_skipped = [
            c["fact_id"] for c in candidates if c["fact_id"] in memory.IMMUTABLE_FACT_IDS
        ]
        would_be_critical = [
            c["fact_id"] for c in candidates
            if c["fact_id"] not in memory.IMMUTABLE_FACT_IDS
            and c["epistemic_state"] == "ImmutableCore"
        ]
        erasable = [
            c["fact_id"] for c in candidates
            if c["fact_id"] not in memory.IMMUTABLE_FACT_IDS
            and c["epistemic_state"] != "ImmutableCore"
        ]
        return {
            "batch_id": None,
            "user_id": user_id,
            "outcome": DRY_RUN,
            "operation_finished": False,
            "erasure_complete": None,
            "success": None,
            "compliance_status": None,
            "critical_compliance_violation": bool(would_be_critical),
            "dry_run": True,
            "items_total": len(candidates),
            "would_erase": len(erasable),
            "would_be_critical_items": would_be_critical,
            "ring_zero_skipped_items": ring_zero_skipped,
        }

    # ── public API ────────────────────────────────────────────────────────

    def forget_all_durable(
        self,
        user_id: str,
        *,
        reason: str = "gdpr_request",
        actor: str = "operator",
        actor_capability: str = "reader",
        force: bool = False,
        scope: str | None = None,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """The one enforced FORGET_ALL entrypoint: durable batch snapshot +
        per-fact erasure via the existing P0-B saga.

        Guardrails (independent of whatever the calling layer — e.g.
        core.tool_registry's capability-gated MCP tool — already
        enforced; this method never trusts an external gate alone):

          - force=True requires actor_capability == "admin" AND a
            non-empty `scope` string describing the intended blast
            radius. Both are recorded in a dedicated, append-only
            erasure_batch_force_receipts row.
          - An empty or 'default' user_id is refused unless force=True
            (and therefore admin + explicit scope) — it is NEVER treated
            as an implicit "erase the whole database" request; the
            underlying selection is always the same structural
            source/metadata.user_id match, never an unscoped sweep.
          - idempotency_key: a repeat call with the SAME key AND the SAME
            canonical request fingerprint (user_id/reason/actor/force/
            scope) resumes (or returns the cached terminal report of) the
            SAME batch. A repeat call with the SAME key but a DIFFERENT
            fingerprint gets IDEMPOTENCY_CONFLICT instead — it never runs
            or reveals the other request's batch.
        """
        scope = (scope or "").strip() or None
        ambiguous_user = not user_id or user_id == "default"

        if force and actor_capability != "admin":
            return self._refused(
                "force_requires_admin_capability", user_id=user_id,
                force=force, scope=scope, idempotency_key=idempotency_key,
            )
        if force and not scope:
            return self._refused(
                "force_requires_explicit_scope", user_id=user_id,
                force=force, scope=scope, idempotency_key=idempotency_key,
            )
        if ambiguous_user and not force:
            return self._refused(
                "ambiguous_user_id", user_id=user_id,
                force=force, scope=scope, idempotency_key=idempotency_key,
            )

        if dry_run:
            return self._preview(user_id)

        fingerprint = _request_fingerprint(
            user_id=user_id, reason=reason, actor=actor, force=force, scope=scope,
        )

        if idempotency_key:
            existing = self._find_batch_by_idempotency_key(idempotency_key)
            if existing is not None:
                if existing["request_fingerprint"] != fingerprint:
                    return self._idempotency_conflict(idempotency_key)
                result = self._run_batch(existing["batch_id"])
                assert result is not None
                return result

        batch_id = self._create_batch_snapshot(
            user_id=user_id, reason=reason, actor=actor, force=force,
            scope=scope, idempotency_key=idempotency_key,
            actor_capability=actor_capability, request_fingerprint=fingerprint,
        )
        if idempotency_key:
            # _create_batch_snapshot() may have lost a create race and
            # adopted a CONCURRENT winner's batch_id — verify it is
            # genuinely OUR request before ever running or revealing it.
            winner = self._load_batch(batch_id)
            if winner["request_fingerprint"] != fingerprint:
                return self._idempotency_conflict(idempotency_key)

        result = self._run_batch(batch_id)
        assert result is not None
        return result

    def resume_incomplete_batches(self) -> list[dict[str, Any]]:
        """Crash recovery sweep: re-run every batch not in a terminal
        EXECUTION state, against its ORIGINAL durable snapshot only.

        A batch left RUNNING is only re-claimed once its lease has expired
        (see _claim_batch_for_running()) — a genuinely still-alive live
        runner is never preempted."""
        now = _now()
        with self._jobs_db() as conn:
            rows = conn.execute(
                "SELECT batch_id FROM erasure_batches WHERE "
                "status IN (?, ?, ?) "
                "OR (status = ? AND lease_expires_at IS NOT NULL AND lease_expires_at < ?) "
                "ORDER BY created_at",
                (PENDING, PARTIAL, FAILED, RUNNING, now),
            ).fetchall()
        results = []
        for row in rows:
            result = self._run_batch(row["batch_id"], wait_if_running=False)
            if result is not None:
                results.append(result)
        return results

    def get_batch_report(self, batch_id: str) -> dict[str, Any] | None:
        try:
            batch = self._load_batch(batch_id)
        except KeyError:
            return None
        return self._report(batch, self._load_items(batch_id))

    def get_batch_report_by_idempotency_key(self, key: str) -> dict[str, Any] | None:
        existing = self._find_batch_by_idempotency_key(key)
        if existing is None:
            return None
        return self._report(existing, self._load_items(existing["batch_id"]))


# ─── module-level convenience (mirrors core.erasure_coordinator) ────────────
_default_batch_coordinator: BatchErasureCoordinator | None = None


def get_batch_coordinator() -> BatchErasureCoordinator:
    if _default_batch_coordinator is not None:
        return _default_batch_coordinator
    return BatchErasureCoordinator()


def forget_all_durable(
    user_id: str,
    *,
    reason: str = "gdpr_request",
    actor: str = "operator",
    actor_capability: str = "reader",
    force: bool = False,
    scope: str | None = None,
    dry_run: bool = False,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    return get_batch_coordinator().forget_all_durable(
        user_id, reason=reason, actor=actor, actor_capability=actor_capability,
        force=force, scope=scope, dry_run=dry_run, idempotency_key=idempotency_key,
    )


def resume_incomplete_batches() -> list[dict[str, Any]]:
    return get_batch_coordinator().resume_incomplete_batches()


def get_batch_report(batch_id: str) -> dict[str, Any] | None:
    return get_batch_coordinator().get_batch_report(batch_id)


def get_batch_report_by_idempotency_key(key: str) -> dict[str, Any] | None:
    return get_batch_coordinator().get_batch_report_by_idempotency_key(key)


__all__ = [
    "BatchErasureCoordinator",
    "get_batch_coordinator",
    "forget_all_durable",
    "resume_incomplete_batches",
    "get_batch_report",
    "get_batch_report_by_idempotency_key",
    "PENDING",
    "RUNNING",
    "COMPLETE",
    "COMPLETE_WITH_RESIDUAL",
    "PARTIAL",
    "FAILED",
    "NOT_FOUND",
    "RESIDUAL_IMMUTABLE_DATA",
    "CRITICAL_COMPLIANCE_VIOLATION",
    "SKIPPED_RING_ZERO",
    "REFUSED",
    "DRY_RUN",
    "IDEMPOTENCY_CONFLICT",
]
