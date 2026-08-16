"""Issue #191: wire SQLiteGraphStore.validate_and_promote() (via
_promote_to_validated_cas()) as the first Canon caller of the transactional
projection outbox.

Foundation status: no dispatcher exists and no projection is ever applied —
this file proves ONLY that a successful single-fact promotion appends
exactly one projection_outbox intent inside the SAME SQLite transaction as
the Canon CAS UPDATE, VersionStore pre-image, and AuditChain event; that a
real failure anywhere in that transaction rolls back all four together;
that no intent is created on any non-mutating outcome (rejection,
concurrent_modification, already_validated); and that this is gated on
migration 020 activation (PRAGMA user_version), failing closed rather than
silently promoting without a required intent.

Every test constructs a real, temp-file-backed SQLiteGraphStore migrated
through the REAL migration chain (scripts/apply_migrations.py) unless a
test is specifically characterizing pre-migration-020 behavior — no
fakes/stubs/mocks for SQLite itself. Failures are simulated with real
SQLite triggers (BEFORE INSERT ... RAISE(ABORT, ...)), never monkeypatched
exceptions, so rollback is proven at the actual transaction boundary.
"""
from __future__ import annotations

import os
import subprocess
import sys
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from core.memory import ProjectionOutboxActivationError, SQLiteGraphStore, make_store

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_APPLY_MIGRATIONS = os.path.join(_ROOT, "scripts", "apply_migrations.py")

sys.path.insert(0, os.path.join(_ROOT, "scripts"))
from apply_migrations import LATEST_VERSION  # noqa: E402


def _migrate(db_path: Path) -> None:
    subprocess.run(
        [sys.executable, _APPLY_MIGRATIONS, "--db", str(db_path), "--no-backup"],
        check=True, capture_output=True,
    )


def _seed_promotable_fact(
    store: SQLiteGraphStore, fact_id: str, *, weak: bool = False,
) -> None:
    """Store a fact and legally advance it to 'Supported' — the last legal
    predecessor of 'Validated' (ESM_TRANSITIONS). `weak=True` seeds a fact
    TruthGate's BALANCED mode will reject (confidence 0.3, no evidence);
    the default is well-evidenced enough to pass (confidence 0.95, two
    evidence_refs) — mirrors tests/test_sqlite_promotion_cas_contention.py's
    own fixture shape."""
    if weak:
        fact = {
            "fact_id": fact_id,
            "claim": "An under-evidenced claim TruthGate BALANCED must reject",
            "source": "manual",
            "confidence": 0.3,
        }
    else:
        fact = {
            "fact_id": fact_id,
            "claim": "A well-evidenced fact for the first Canon caller increment",
            "source": "manual",
            "confidence": 0.95,
            "metadata": {"evidence_refs": ["source-a", "source-b"]},
        }
    assert store.store_fact(fact) is True
    assert store.promote_esm_to(fact_id, "Supported", by="caller_test_setup") is True


def _outbox_rows(db_path: Path, fact_id: str) -> list[sqlite3.Row]:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM projection_outbox WHERE aggregate_id = ?", (fact_id,),
        ).fetchall()


def _fact_version(db_path: Path, fact_id: str) -> int:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        return int(
            conn.execute(
                "SELECT fact_version FROM facts WHERE fact_id = ?", (fact_id,),
            ).fetchone()[0]
        )


def _fact_versions_count(db_path: Path, fact_id: str) -> int:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        return int(
            conn.execute(
                "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?", (fact_id,),
            ).fetchone()[0]
        )


def _validated_audit_events_count(db_path: Path, fact_id: str) -> int:
    """AuditChain.log_in_transaction() (as called by
    _promote_to_validated_cas()) never passes `fact_id` — events are keyed
    by `chain_id` ('fact-transition:{audit_subject_id}') instead, exactly
    as tests/test_sqlite_promotion_cas_contention.py's own
    _promotion_evidence() helper looks them up."""
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        subject_row = conn.execute(
            "SELECT audit_subject_id FROM facts WHERE fact_id = ?", (fact_id,),
        ).fetchone()
        if subject_row is None or subject_row[0] is None:
            return 0
        chain_id = f"fact-transition:{subject_row[0]}"
        return int(
            conn.execute(
                "SELECT COUNT(*) FROM memory_events "
                "WHERE chain_id = ? AND to_state = 'Validated'", (chain_id,),
            ).fetchone()[0]
        )


def _integrity_ok(db_path: Path) -> bool:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        return conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def _install_insert_failure_trigger(
    store: SQLiteGraphStore, *, table: str, when_sql: str,
) -> None:
    """Real SQLite trigger that raises on INSERT into `table` matching
    `when_sql` — a genuine DB-level failure, never a mocked exception."""
    trigger_name = f"simulate_{table}_insert_failure"
    with store._db() as conn:
        conn.execute(f"""
            CREATE TRIGGER IF NOT EXISTS {trigger_name}
            BEFORE INSERT ON {table}
            WHEN {when_sql}
            BEGIN
                SELECT RAISE(ABORT, 'SIMULATED: real DB failure mid-transaction');
            END;
        """)


# ── A. Successful promotion: Canon + VersionStore + AuditChain + one intent ─

def test_successful_promotion_appends_exactly_one_intent_with_correct_canonical_version(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "success.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_success"
    _seed_promotable_fact(store, fact_id)
    versions_before = _fact_versions_count(db_path, fact_id)
    events_before = _validated_audit_events_count(db_path, fact_id)

    verdict = store.validate_and_promote(fact_id, by="caller_test")

    assert verdict.passed is True
    assert verdict.reason == "passed"
    final = store.get_fact(fact_id)
    assert final is not None and final["epistemic_state"] == "Validated"
    assert _fact_versions_count(db_path, fact_id) == versions_before + 1
    assert _validated_audit_events_count(db_path, fact_id) == events_before + 1

    rows = _outbox_rows(db_path, fact_id)
    assert len(rows) == 1
    row = rows[0]
    assert row["aggregate_type"] == "fact"
    assert row["aggregate_id"] == fact_id
    assert row["scope_ref"] == "local:primary"
    assert row["projection_kind"] == "all"
    assert row["operation"] == "refresh"
    assert row["policy_version"] == "projection-outbox-v1"
    assert row["canonical_version"] == _fact_version(db_path, fact_id)

    assert _integrity_ok(db_path)


# ── B. Real failures roll back Canon + VersionStore + AuditChain + outbox ──

def test_outbox_insert_failure_rolls_back_canon_version_and_audit(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "outbox-failure.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_outbox_fail"
    _seed_promotable_fact(store, fact_id)
    _install_insert_failure_trigger(
        store, table="projection_outbox", when_sql=f"NEW.aggregate_id = '{fact_id}'",
    )
    versions_before = _fact_versions_count(db_path, fact_id)
    events_before = _validated_audit_events_count(db_path, fact_id)

    with pytest.raises(sqlite3.IntegrityError):
        store.validate_and_promote(fact_id, by="caller_test")

    final = store.get_fact(fact_id)
    assert final is not None and final["epistemic_state"] == "Supported"
    assert _fact_versions_count(db_path, fact_id) == versions_before
    assert _validated_audit_events_count(db_path, fact_id) == events_before
    assert _outbox_rows(db_path, fact_id) == []
    assert _integrity_ok(db_path)

    with store._db() as conn:
        conn.execute("DROP TRIGGER simulate_projection_outbox_insert_failure")
    retry = store.validate_and_promote(fact_id, by="caller_retry")
    assert retry.passed is True
    assert len(_outbox_rows(db_path, fact_id)) == 1


def test_version_store_failure_rolls_back_canon_audit_and_prevents_intent(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "versionstore-failure.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_versionstore_fail"
    _seed_promotable_fact(store, fact_id)
    _install_insert_failure_trigger(
        store, table="fact_versions", when_sql=f"NEW.fact_id = '{fact_id}'",
    )
    events_before = _validated_audit_events_count(db_path, fact_id)

    with pytest.raises(sqlite3.IntegrityError):
        store.validate_and_promote(fact_id, by="caller_test")

    final = store.get_fact(fact_id)
    assert final is not None and final["epistemic_state"] == "Supported"
    assert _validated_audit_events_count(db_path, fact_id) == events_before
    assert _outbox_rows(db_path, fact_id) == []
    assert _integrity_ok(db_path)


def test_audit_chain_failure_rolls_back_canon_version_and_prevents_intent(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "auditchain-failure.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_auditchain_fail"
    _seed_promotable_fact(store, fact_id)
    # AuditChain.log_in_transaction() (as called by
    # _promote_to_validated_cas()) never passes fact_id — memory_events
    # rows are keyed by chain_id, not fact_id (see
    # _validated_audit_events_count()'s docstring) — so this test's own
    # fact_id is the only isolated fact in this database, and gating on
    # to_state alone is sufficient and precise here.
    _install_insert_failure_trigger(
        store, table="memory_events", when_sql="NEW.to_state = 'Validated'",
    )
    versions_before = _fact_versions_count(db_path, fact_id)

    with pytest.raises(sqlite3.IntegrityError):
        store.validate_and_promote(fact_id, by="caller_test")

    final = store.get_fact(fact_id)
    assert final is not None and final["epistemic_state"] == "Supported"
    assert _fact_versions_count(db_path, fact_id) == versions_before
    assert _outbox_rows(db_path, fact_id) == []
    assert _integrity_ok(db_path)


# ── C. Non-mutating outcomes never create an intent ─────────────────────────

def test_truth_gate_rejection_creates_no_intent(tmp_path: Path) -> None:
    db_path = tmp_path / "rejection.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_rejected"
    _seed_promotable_fact(store, fact_id, weak=True)

    verdict = store.validate_and_promote(fact_id, by="caller_test")

    assert verdict.passed is False
    final = store.get_fact(fact_id)
    assert final is not None and final["epistemic_state"] == "Supported"
    assert _outbox_rows(db_path, fact_id) == []


def test_already_validated_creates_no_new_version_audit_or_intent(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "already-validated.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_already_validated"
    _seed_promotable_fact(store, fact_id)
    first = store.validate_and_promote(fact_id, by="caller_test")
    assert first.passed is True
    versions_after_first = _fact_versions_count(db_path, fact_id)
    events_after_first = _validated_audit_events_count(db_path, fact_id)
    assert len(_outbox_rows(db_path, fact_id)) == 1

    second = store.validate_and_promote(fact_id, by="caller_retry")

    assert second.passed is True
    assert second.reason == "already_validated"
    assert _fact_versions_count(db_path, fact_id) == versions_after_first
    assert _validated_audit_events_count(db_path, fact_id) == events_after_first
    assert len(_outbox_rows(db_path, fact_id)) == 1, (
        "already_validated must not append a second intent"
    )


# ── D. CAS contention: exactly one winner, exactly one intent ──────────────


@dataclass
class _CasContentionHarness:
    """Stage-aware orchestration for real SQLite CAS contention tests.

    Separates worker/store readiness from synchronized CAS release and records
    per-contender stages so timeout/failure diagnostics can identify which
    workers never reached the pre-CAS gate. This is a diagnostic aid for an
    uncharacterized CAS-contention test failure; it does not prove production
    CAS health by itself.
    """

    contenders: int
    timeout: float = 30.0
    stall_contender: int | None = None
    fail_before_gate: int | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _condition: threading.Condition = field(init=False, repr=False)
    _release_event: threading.Event = field(default_factory=threading.Event, init=False, repr=False)
    _abort_event: threading.Event = field(default_factory=threading.Event, init=False, repr=False)
    _started_at: float = field(default_factory=time.monotonic, init=False, repr=False)
    _stage_by_id: dict[int, str] = field(default_factory=dict, init=False, repr=False)
    _workers_started: int = 0
    _stores_ready: int = 0
    _pre_cas_ready: int = 0
    _cas_returned: int = 0
    _early_failures: dict[int, str] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self._condition = threading.Condition(self._lock)

    def mark_submitted(self, contender_id: int) -> None:
        with self._lock:
            self._stage_by_id[contender_id] = "submitted"

    def mark_worker_started(self, contender_id: int) -> None:
        with self._lock:
            self._stage_by_id[contender_id] = "worker_started"
            self._workers_started += 1

    def mark_store_ready(self, contender_id: int) -> None:
        with self._lock:
            self._stage_by_id[contender_id] = "store_ready"
            self._stores_ready += 1

    def mark_failed_before_gate(self, contender_id: int, reason: str) -> None:
        with self._condition:
            self._stage_by_id[contender_id] = "failed_before_pre_cas_gate"
            self._early_failures[contender_id] = reason
            self._abort_event.set()
            self._condition.notify_all()

    def wait_for_synchronized_cas_release(self, contender_id: int) -> None:
        if self.stall_contender == contender_id:
            with self._lock:
                self._stage_by_id[contender_id] = "pre_cas_gate_stalled"
            deadline = time.monotonic() + self.timeout + 1.0
            while time.monotonic() < deadline:
                if self._abort_event.is_set():
                    raise AssertionError(self.format_timeout())
                time.sleep(0.05)
            return

        with self._lock:
            self._stage_by_id[contender_id] = "pre_cas_gate"
            self._pre_cas_ready += 1
            if self._pre_cas_ready == self.contenders:
                self._release_event.set()
                self._condition.notify_all()

        deadline = time.monotonic() + self.timeout
        with self._condition:
            while self._pre_cas_ready < self.contenders:
                if self._abort_event.is_set() or self._early_failures:
                    message = self._diagnostics_unlocked()
                    raise AssertionError(message)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    message = self._diagnostics_unlocked()
                    raise AssertionError(message)
                self._condition.wait(timeout=min(remaining, 0.25))

        if not self._release_event.wait(timeout=max(0.0, deadline - time.monotonic())):
            raise AssertionError(self.format_timeout())

    def mark_cas_returned(self, contender_id: int) -> None:
        with self._lock:
            self._stage_by_id[contender_id] = "cas_returned"
            self._cas_returned += 1

    def _diagnostics_unlocked(self) -> str:
        missing = [
            contender_id
            for contender_id in range(self.contenders)
            if self._stage_by_id.get(contender_id) not in {
                "pre_cas_gate",
                "cas_returned",
            }
        ]
        stage_lines = [
            f"  contender_{contender_id}: {self._stage_by_id.get(contender_id, 'missing')}"
            for contender_id in range(self.contenders)
        ]
        early = (
            "; ".join(
                f"contender_{cid}: {reason}"
                for cid, reason in sorted(self._early_failures.items())
            )
            or "none"
        )
        elapsed = time.monotonic() - self._started_at
        return (
            "CAS contention harness timed out or aborted before synchronized release\n"
            f"missing contender IDs: {missing}\n"
            f"early failures before pre-CAS gate: {early}\n"
            f"last known stages:\n" + "\n".join(stage_lines) + "\n"
            f"elapsed monotonic seconds: {elapsed:.3f}\n"
            f"workers started: {self._workers_started}/{self.contenders}\n"
            f"stores ready: {self._stores_ready}/{self.contenders}\n"
            f"pre-CAS gate reached: {self._pre_cas_ready}/{self.contenders}\n"
            f"CAS returned: {self._cas_returned}/{self.contenders}"
        )

    def format_timeout(self) -> str:
        with self._lock:
            return self._diagnostics_unlocked()

    def stage_of(self, contender_id: int) -> str:
        with self._lock:
            return self._stage_by_id.get(contender_id, "missing")


def _install_cas_contention_gate(
    store: SQLiteGraphStore,
    harness: _CasContentionHarness,
    contender_id: int,
) -> None:
    original = store._promote_to_validated_cas

    def gated(*args, **kwargs):
        harness.wait_for_synchronized_cas_release(contender_id)
        try:
            return original(*args, **kwargs)
        finally:
            harness.mark_cas_returned(contender_id)

    store._promote_to_validated_cas = gated  # type: ignore[method-assign]


def _run_cas_contention_race(
    db_path: Path,
    *,
    contenders: int,
    timeout: float = 30.0,
    stall_contender: int | None = None,
    fail_before_gate: int | None = None,
) -> list:
    harness = _CasContentionHarness(
        contenders,
        timeout=timeout,
        stall_contender=stall_contender,
        fail_before_gate=fail_before_gate,
    )
    stores = [SQLiteGraphStore(str(db_path)) for _ in range(contenders)]
    # Issue #249 is a CAS-contention test, not a concurrent schema-bootstrap
    # test. Every independent store owns a per-instance lazy DDL guard, so
    # entering validate_and_promote() concurrently on never-opened stores
    # mixes first-use schema churn into the intended CAS race. Initialize
    # each contender sequentially before installing/releasing the CAS gate;
    # the threaded section below then races only the real promotion path.
    for store in stores:
        store.ensure_schema()
    for contender_id, store in enumerate(stores):
        harness.mark_submitted(contender_id)
        _install_cas_contention_gate(store, harness, contender_id)

    def promote(store: SQLiteGraphStore, contender_id: int):
        harness.mark_worker_started(contender_id)
        harness.mark_store_ready(contender_id)
        if harness.fail_before_gate == contender_id:
            harness.mark_failed_before_gate(
                contender_id,
                "injected failure before validate_and_promote / pre-CAS gate",
            )
            raise RuntimeError(
                f"injected pre-CAS failure for contender_{contender_id}"
            )
        try:
            return store.validate_and_promote(
                "f_cas_contention", by=f"contender_{contender_id}"
            )
        except Exception as exc:
            # Preserve stage diagnostics when a worker dies before the gate.
            if harness.stage_of(contender_id) in {
                "submitted",
                "worker_started",
                "store_ready",
            }:
                harness.mark_failed_before_gate(contender_id, f"{type(exc).__name__}: {exc}")
            raise

    try:
        with ThreadPoolExecutor(max_workers=contenders) as executor:
            futures = [
                executor.submit(promote, store, contender_id)
                for contender_id, store in enumerate(stores)
            ]
            verdicts: list = []
            errors: list[BaseException] = []
            for future in futures:
                try:
                    verdicts.append(future.result(timeout=timeout + 5))
                except BaseException as exc:  # noqa: BLE001 — aggregate with diagnostics
                    errors.append(exc)
            if errors:
                details = "; ".join(f"{type(exc).__name__}: {exc}" for exc in errors)
                raise AssertionError(
                    f"{harness.format_timeout()}\nworker exceptions: {details}"
                )
            return verdicts
    finally:
        for store in stores:
            store.close()


@pytest.mark.parametrize("contenders", [2, 10, 25])
def test_cas_contention_yields_exactly_one_winner_and_one_intent(
    tmp_path: Path, contenders: int,
) -> None:
    db_path = tmp_path / f"cas-contention-{contenders}.db"
    _migrate(db_path)
    bootstrap = SQLiteGraphStore(str(db_path))
    fact_id = "f_cas_contention"
    _seed_promotable_fact(bootstrap, fact_id)
    bootstrap.close()

    verdicts = _run_cas_contention_race(db_path, contenders=contenders)

    winners = [v for v in verdicts if v.passed]
    assert len(winners) == 1, [(v.passed, v.reason) for v in verdicts]

    post_race = SQLiteGraphStore(str(db_path))
    try:
        final = post_race.get_fact(fact_id)
        assert final is not None and final["epistemic_state"] == "Validated"
        rows = _outbox_rows(db_path, fact_id)
        assert len(rows) == 1, f"expected exactly one intent, found {len(rows)}"
        assert rows[0]["canonical_version"] == _fact_version(db_path, fact_id)

        retry_verdict = post_race.validate_and_promote(fact_id, by="post_race")
        assert retry_verdict.passed is True
        assert retry_verdict.reason == "already_validated"
        assert len(_outbox_rows(db_path, fact_id)) == 1
    finally:
        post_race.close()
    assert _integrity_ok(db_path)


def test_cas_contention_harness_reports_stalled_contender() -> None:
    harness = _CasContentionHarness(3, timeout=0.5, stall_contender=1)
    errors: list[str] = []

    def worker(contender_id: int) -> None:
        try:
            harness.wait_for_synchronized_cas_release(contender_id)
        except AssertionError as exc:
            errors.append(str(exc))

    threads = [threading.Thread(target=worker, args=(contender_id,)) for contender_id in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=3.0)

    assert errors, "expected at least one bounded harness timeout"
    assert any("contender_1: pre_cas_gate_stalled" in message for message in errors)
    assert any("missing contender IDs: [1]" in message for message in errors)
    assert any("pre-CAS gate reached: 2/3" in message for message in errors)


def test_cas_contention_harness_surfaces_failure_before_pre_cas_gate(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "cas-contention-fail-before-gate.db"
    _migrate(db_path)
    bootstrap = SQLiteGraphStore(str(db_path))
    _seed_promotable_fact(bootstrap, "f_cas_contention")
    bootstrap.close()

    with pytest.raises(AssertionError) as exc_info:
        _run_cas_contention_race(
            db_path,
            contenders=3,
            timeout=2.0,
            fail_before_gate=1,
        )

    message = str(exc_info.value)
    assert "contender_1: failed_before_pre_cas_gate" in message
    assert "early failures before pre-CAS gate: contender_1:" in message
    assert "injected pre-CAS failure" in message
    assert _integrity_ok(db_path)


# ── E. Migration-020 activation gating ──────────────────────────────────────

def test_pre_migration_020_database_promotes_unchanged_without_outbox(
    tmp_path: Path,
) -> None:
    """A bare runtime-bootstrapped store (make_store(), user_version == 0)
    has no projection_outbox at all — promotion must succeed exactly as it
    always has, and must never be described as outbox-backed."""
    db_path = tmp_path / "pre-v20.db"
    store = make_store(str(db_path))
    fact_id = "f_pre_v20"
    with store._db() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
        assert store._table_exists(conn, "projection_outbox") is False
    _seed_promotable_fact(store, fact_id)

    verdict = store.validate_and_promote(fact_id, by="caller_test")

    assert verdict.passed is True
    final = store.get_fact(fact_id)
    assert final is not None and final["epistemic_state"] == "Validated"
    with store._db() as conn:
        assert store._table_exists(conn, "projection_outbox") is False


def test_activated_db_missing_projection_outbox_table_fails_closed(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "v20-missing-outbox.db"
    _migrate(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("DROP TABLE projection_outbox")
        conn.commit()

    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_v20_missing_outbox"
    _seed_promotable_fact(store, fact_id)
    versions_before = _fact_versions_count(db_path, fact_id)
    events_before = _validated_audit_events_count(db_path, fact_id)

    with pytest.raises(ProjectionOutboxActivationError):
        store.validate_and_promote(fact_id, by="caller_test")

    final = store.get_fact(fact_id)
    assert final is not None and final["epistemic_state"] == "Supported", (
        "an activated DB missing projection_outbox must fail closed — "
        "Canon must roll back, not silently promote without the intent"
    )
    assert _fact_versions_count(db_path, fact_id) == versions_before
    assert _validated_audit_events_count(db_path, fact_id) == events_before
    assert _integrity_ok(db_path)


def test_activated_db_with_projection_outbox_as_a_view_fails_closed(
    tmp_path: Path,
) -> None:
    """The general-purpose _table_exists() intentionally treats table/view
    as interchangeable (other callers, e.g. the erasure_audit VIEW, rely on
    exactly that). The promotion activation gate must be stricter: a VIEW
    named projection_outbox would pass a table/view check yet cannot accept
    a plain INSERT (no INSTEAD OF trigger here) — this must be caught by
    the gate itself as a schema inconsistency, not surfaced as a random
    'cannot modify ... because it is a view' error from deep inside the
    outbox append."""
    db_path = tmp_path / "v20-outbox-is-a-view.db"
    _migrate(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("DROP TABLE projection_outbox")
        conn.execute("CREATE VIEW projection_outbox AS SELECT 1 AS outbox_id")
        conn.commit()
        assert conn.execute(
            "SELECT type FROM sqlite_master WHERE name = 'projection_outbox'"
        ).fetchone()[0] == "view"

    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_v20_outbox_is_view"
    _seed_promotable_fact(store, fact_id)
    versions_before = _fact_versions_count(db_path, fact_id)
    events_before = _validated_audit_events_count(db_path, fact_id)

    with pytest.raises(ProjectionOutboxActivationError):
        store.validate_and_promote(fact_id, by="caller_test")

    final = store.get_fact(fact_id)
    assert final is not None and final["epistemic_state"] == "Supported", (
        "a projection_outbox VIEW (not a real table) must fail closed — "
        "Canon must roll back, not attempt an INSERT the object can't accept"
    )
    assert _fact_versions_count(db_path, fact_id) == versions_before
    assert _validated_audit_events_count(db_path, fact_id) == events_before
    assert _integrity_ok(db_path)


def test_activated_db_missing_fact_version_fails_closed(tmp_path: Path) -> None:
    """Simulates migration 009 never having genuinely run (schema
    inconsistency) despite PRAGMA user_version claiming 020: both the
    fact_version column AND its own bump_fact_version trigger are absent,
    matching a real 'the fact_version subsystem is simply not there'
    shape rather than an orphaned-trigger side effect."""
    db_path = tmp_path / "v20-missing-fact-version.db"
    _migrate(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("DROP TRIGGER IF EXISTS bump_fact_version")
        conn.execute("ALTER TABLE facts DROP COLUMN fact_version")
        conn.commit()

    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_v20_missing_fact_version"
    _seed_promotable_fact(store, fact_id)
    events_before = _validated_audit_events_count(db_path, fact_id)

    with pytest.raises(ProjectionOutboxActivationError):
        store.validate_and_promote(fact_id, by="caller_test")

    final = store.get_fact(fact_id)
    assert final is not None and final["epistemic_state"] == "Supported", (
        "an activated DB missing facts.fact_version must fail closed — "
        "Canon must roll back, not silently promote without a durable "
        "canonical_version"
    )
    assert _validated_audit_events_count(db_path, fact_id) == events_before
    assert _outbox_rows(db_path, fact_id) == []
    assert _integrity_ok(db_path)


# ── E2. Characterization: a live store instance across an external
#       migration is NOT a supported lifecycle (pre-existing, not
#       introduced by this issue) ───────────────────────────────────────────

def test_reusing_a_live_store_across_an_external_migration_is_unsupported(
    tmp_path: Path,
) -> None:
    """`SQLiteGraphStore._has_fact_version` is computed once and cached for
    the lifetime of the instance (`_fact_version_bump_sql()`). If a store
    is constructed and used BEFORE `scripts/apply_migrations.py` runs
    against the SAME db_path, and then kept alive and reused AFTER that
    external migration completes, its cached `False` goes stale — but this
    is not merely a projection-outbox gating gap: the very next ESM
    transition through this same instance already fails, because
    migration 009's own `bump_fact_version` trigger (added by the
    migration, unconditionally enforcing `NEW.fact_version >
    OLD.fact_version` on any epistemic_state/claim/confidence change) now
    exists and fires — but this instance's stale cache makes its own
    UPDATE never touch `fact_version` in the first place, so the trigger's
    own WHEN condition raises.

    This confirms the constraint is pre-existing and broader than issue
    #191's own gate: a SQLiteGraphStore instance must be constructed AFTER
    any migration run against its db_path, never kept alive and reused
    across a LIVE migration of the same file — exactly the lifecycle every
    fixture in this repository already follows (migrate, then construct).
    This test pins that CURRENT, correct-per-project-convention failure
    mode (a loud, real `sqlite3.IntegrityError` from the pre-existing
    trigger) rather than silently working around it — see
    ADR-2026-08-04-first-canon-caller-projection-outbox.md."""
    db_path = tmp_path / "live-migration-reuse.db"
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_live_migration_reuse"
    store.store_fact(
        {
            "fact_id": fact_id, "claim": "x", "source": "test", "confidence": 0.9,
        }
    )
    # A real prior ESM transition establishes _has_fact_version's cache
    # (False — no migration has run against this bare-bootstrapped DB yet).
    assert store.promote_esm_to(fact_id, "Hypothesized", by="setup") is True
    assert store._has_fact_version is False

    _migrate(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        # Review finding, PR #195: derive the latest version dynamically
        # (as test_migrations.py already does) — this assertion only
        # needs "the full chain ran", not a specific final version.
        assert conn.execute("PRAGMA user_version").fetchone()[0] == LATEST_VERSION
        assert "fact_version" in {
            r[1] for r in conn.execute("PRAGMA table_info(facts)").fetchall()
        }
    assert store._has_fact_version is False, (
        "the instance's cache does not observe the external migration"
    )

    with pytest.raises(sqlite3.IntegrityError, match="fact_version must increase"):
        store.promote_esm_to(fact_id, "Supported", by="after_migration")

    assert _integrity_ok(db_path)


# ── F. Erasure removes a real promotion-created intent ──────────────────────

def test_erasure_removes_the_intent_a_real_promotion_created(tmp_path: Path) -> None:
    db_path = tmp_path / "erasure-integration.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_erasure_integration"
    _seed_promotable_fact(store, fact_id)
    verdict = store.validate_and_promote(fact_id, by="caller_test")
    assert verdict.passed is True
    assert len(_outbox_rows(db_path, fact_id)) == 1

    result = store.erase_fact_dependents_atomic(fact_id)

    assert result["tables"]["projection_outbox"] == {"applicable": True, "deleted": 1}
    assert _outbox_rows(db_path, fact_id) == []
    assert store.same_db_dependents_present(fact_id) is False
    assert _integrity_ok(db_path)
