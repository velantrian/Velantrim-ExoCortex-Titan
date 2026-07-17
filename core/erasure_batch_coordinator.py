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
#     any deletion is attempted.
#   - erasure_batch_items is the durable SNAPSHOT — one row per fact_id
#     selected by the batch's filter, captured atomically WITH the batch
#     row. This is the one and only membership list this batch will ever
#     process: a resume (crash recovery, or a repeat call with the same
#     idempotency_key) replays exactly these rows and NEVER re-queries
#     `facts` by user_id again. A fact ingested for the same user_id AFTER
#     the snapshot was taken is out of scope for THIS batch by
#     construction — it needs its own subsequent forget_all_durable() call.
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
#     data forever with no alarm. This coordinator flags it
#     CRITICAL_COMPLIANCE_VIOLATION instead of deleting OR silently
#     skipping it, and the batch can never report success while such an
#     item is outstanding.
#
# See migrations/015_erasure_batches.sql for the schema and rationale, and
# the "Batch state machine" section below for the full status model.
#
# ── Batch state machine ──────────────────────────────────────────────────
#
#   PENDING --(claim)--> RUNNING --(finalize)--> one of:
#       COMPLETE                    every item COMPLETE / NOT_FOUND /
#                                   SKIPPED_RING_ZERO — nothing outstanding.
#       COMPLETE_WITH_RESIDUAL      every item terminal, no compliance
#                                   violation, but >=1 item is
#                                   RESIDUAL_IMMUTABLE_DATA (L0 raw text —
#                                   the SAME accepted, tracked limitation
#                                   erase_fact_durable() itself reports).
#       PARTIAL                     >=1 item still PENDING/PARTIAL/FAILED —
#                                   resumable; a later run_batch()/resume
#                                   call retries ONLY those items.
#       CRITICAL_COMPLIANCE_VIOLATION
#                                   >=1 item is a personal fact found inside
#                                   ImmutableCore. Takes precedence over
#                                   PARTIAL: even if other items are still
#                                   retryable, the batch must never be
#                                   silently reported as "just still
#                                   running" while a compliance violation
#                                   sits unresolved. Retryable items are
#                                   still retried on the next run/resume;
#                                   this status does not auto-clear —
#                                   resolving it is a manual/administrative
#                                   act (out of scope for this CR).
#
#   PARTIAL/FAILED/PENDING/RUNNING(crash) are all resumable — see
#   resume_incomplete_batches(). COMPLETE / COMPLETE_WITH_RESIDUAL /
#   CRITICAL_COMPLIANCE_VIOLATION are terminal: a repeat call (via
#   idempotency_key) returns the cached report without reprocessing.

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
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

# ─── batch-level statuses ────────────────────────────────────────────────────
PENDING = "PENDING"
RUNNING = "RUNNING"
COMPLETE_WITH_RESIDUAL = "COMPLETE_WITH_RESIDUAL"
CRITICAL_COMPLIANCE_VIOLATION = "CRITICAL_COMPLIANCE_VIOLATION"
REFUSED = "REFUSED"
DRY_RUN = "DRY_RUN"

# ─── item-level statuses (own to this module; per-fact outcomes from
# erase_fact_durable() — COMPLETE/PARTIAL/FAILED/NOT_FOUND/
# RESIDUAL_IMMUTABLE_DATA — pass through unchanged as item status) ──────────
SKIPPED_RING_ZERO = "SKIPPED_RING_ZERO"

_TERMINAL_BATCH_STATUSES = (COMPLETE, COMPLETE_WITH_RESIDUAL, CRITICAL_COMPLIANCE_VIOLATION)
_RUNNABLE_BATCH_STATUSES = (PENDING, PARTIAL, FAILED)
_RESUMABLE_BATCH_STATUSES = (PENDING, RUNNING, PARTIAL, FAILED)
_ITEM_RETRYABLE_STATUSES = (PENDING, PARTIAL, FAILED)
_ITEM_TERMINAL_NON_CRITICAL = (COMPLETE, NOT_FOUND, SKIPPED_RING_ZERO)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS erasure_batches (
    batch_id          TEXT PRIMARY KEY,
    user_id           TEXT NOT NULL,
    reason            TEXT NOT NULL,
    actor             TEXT NOT NULL,
    force             INTEGER NOT NULL DEFAULT 0,
    scope             TEXT,
    idempotency_key   TEXT,
    status            TEXT NOT NULL DEFAULT 'PENDING',
    items_total       INTEGER NOT NULL DEFAULT 0,
    error             TEXT,
    snapshot_at       TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
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
        self._ensure_schema()

    # ── schema ────────────────────────────────────────────────────────────

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

    def _set_batch_status(self, batch_id: str, status: str, *, error: str | None = None) -> None:
        with self._jobs_db() as conn:
            conn.execute(
                "UPDATE erasure_batches SET status = ?, error = COALESCE(?, error), "
                "updated_at = ? WHERE batch_id = ?",
                (status, error, _now(), batch_id),
            )

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
    ) -> str:
        """Select candidate facts and durably persist the batch + its full
        item snapshot in ONE atomic transaction. This SELECT is the only
        time `facts` is ever queried by user_id for this batch — every
        subsequent run/resume operates purely on the persisted
        erasure_batch_items rows created here.
        """
        candidates = self._store.list_fact_ids_by_user_durable(user_id)
        batch_id = f"eb_{uuid.uuid4().hex[:16]}"
        now = _now()
        try:
            with self._jobs_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    conn.execute(
                        "INSERT INTO erasure_batches "
                        "(batch_id, user_id, reason, actor, force, scope, idempotency_key, "
                        "status, items_total, snapshot_at, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            batch_id, user_id, reason, actor, int(force), scope or None,
                            idempotency_key, PENDING, len(candidates), now, now, now,
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
            # Adopt the winner's batch_id rather than diverge into a second
            # snapshot for one idempotency_key.
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

    # ── orchestration ─────────────────────────────────────────────────────

    def _claim_batch_for_running(
        self, batch_id: str, *, from_statuses: tuple[str, ...]
    ) -> bool:
        with self._jobs_db() as conn:
            placeholders = ", ".join("?" for _ in from_statuses)
            cur = conn.execute(
                f"UPDATE erasure_batches SET status = ?, updated_at = ? "  # noqa: S608
                f"WHERE batch_id = ? AND status IN ({placeholders})",
                (RUNNING, _now(), batch_id, *from_statuses),
            )
        return cur.rowcount > 0

    def _wait_for_batch_completion(self, batch_id: str, timeout_s: float = 30.0) -> dict[str, Any]:
        """Another live caller already holds the RUNNING claim (e.g. a
        concurrent forget_all_durable() call for the same idempotency_key)
        — poll for it to reach a terminal status rather than redundantly
        reprocessing the same snapshot."""
        deadline = time.monotonic() + timeout_s
        batch = self._load_batch(batch_id)
        while batch["status"] in (PENDING, RUNNING) and time.monotonic() < deadline:
            time.sleep(0.05)
            batch = self._load_batch(batch_id)
        return self._report(batch, self._load_items(batch_id))

    def _run_batch(self, batch_id: str, *, wait_if_running: bool = True) -> dict[str, Any] | None:
        """Process every not-yet-terminal item in `batch_id`'s ORIGINAL
        snapshot and finalize. Never re-queries `facts` by user_id.

        `wait_if_running=True` (live caller path) claims FROM
        `_RUNNABLE_BATCH_STATUSES`; if the batch is already terminal, its
        cached report is returned immediately (idempotent repeat call —
        no reprocessing). If another live caller holds the RUNNING claim,
        this waits for it instead of racing it.

        `wait_if_running=False` is used only by resume_incomplete_batches()
        (crash-recovery sweep): it claims from the broader
        `_RESUMABLE_BATCH_STATUSES` (includes RUNNING — a batch left
        RUNNING by a dead process) and returns None if the claim is lost
        to a concurrent transition, rather than proceeding.
        """
        from_statuses = _RUNNABLE_BATCH_STATUSES if wait_if_running else _RESUMABLE_BATCH_STATUSES
        if not self._claim_batch_for_running(batch_id, from_statuses=from_statuses):
            current = self._load_batch(batch_id)
            if current["status"] in _TERMINAL_BATCH_STATUSES:
                return self._report(current, self._load_items(batch_id))
            if wait_if_running:
                return self._wait_for_batch_completion(batch_id)
            return None

        batch = self._load_batch(batch_id)
        items = self._load_items(batch_id)
        for item in items:
            if item["status"] in _ITEM_RETRYABLE_STATUSES:
                self._process_item(batch, item)

        return self._finalize_batch(batch_id)

    def _finalize_batch(self, batch_id: str) -> dict[str, Any]:
        items = self._load_items(batch_id)
        statuses = [i["status"] for i in items]

        retryable = [s for s in statuses if s in _ITEM_RETRYABLE_STATUSES]
        critical = [s for s in statuses if s == CRITICAL_COMPLIANCE_VIOLATION]
        residual = [s for s in statuses if s == RESIDUAL_IMMUTABLE_DATA]

        if critical:
            # Highest precedence: a compliance violation must never be
            # hidden behind an otherwise-in-progress PARTIAL status —
            # retryable items are still retried on the next run, but the
            # batch's headline outcome always surfaces the violation.
            outcome = CRITICAL_COMPLIANCE_VIOLATION
        elif retryable:
            outcome = PARTIAL
        elif residual:
            outcome = COMPLETE_WITH_RESIDUAL
        else:
            outcome = COMPLETE

        self._set_batch_status(batch_id, outcome)
        return self._report(self._load_batch(batch_id), items)

    # ── reporting ─────────────────────────────────────────────────────────

    def _report(self, batch: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
        critical_items = [i["fact_id"] for i in items if i["status"] == CRITICAL_COMPLIANCE_VIOLATION]
        return {
            "batch_id": batch["batch_id"],
            "user_id": batch["user_id"],
            "reason": batch["reason"],
            "actor": batch["actor"],
            "force": bool(batch["force"]),
            "scope": batch["scope"],
            "idempotency_key": batch["idempotency_key"],
            "outcome": batch["status"],
            "success": batch["status"] in (COMPLETE, COMPLETE_WITH_RESIDUAL),
            "critical_compliance_violation": batch["status"] == CRITICAL_COMPLIANCE_VIOLATION,
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
            "success": False,
            "critical_compliance_violation": False,
            "critical_items": [],
            "force": force,
            "scope": scope,
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
            "success": None,
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
          - idempotency_key: a repeat call with the SAME key resumes (or
            returns the cached terminal report of) the SAME batch —
            never re-snapshots or double-processes.
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

        if idempotency_key:
            existing = self._find_batch_by_idempotency_key(idempotency_key)
            if existing is not None:
                result = self._run_batch(existing["batch_id"])
                assert result is not None
                return result

        batch_id = self._create_batch_snapshot(
            user_id=user_id, reason=reason, actor=actor, force=force,
            scope=scope, idempotency_key=idempotency_key,
            actor_capability=actor_capability,
        )
        result = self._run_batch(batch_id)
        assert result is not None
        return result

    def resume_incomplete_batches(self) -> list[dict[str, Any]]:
        """Crash recovery sweep: re-run every batch not in a terminal
        state, against its ORIGINAL durable snapshot only."""
        with self._jobs_db() as conn:
            placeholders = ", ".join("?" for _ in _RESUMABLE_BATCH_STATUSES)
            rows = conn.execute(
                f"SELECT batch_id FROM erasure_batches WHERE status IN ({placeholders}) "  # noqa: S608
                "ORDER BY created_at",
                _RESUMABLE_BATCH_STATUSES,
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
]
