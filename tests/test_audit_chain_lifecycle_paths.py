"""
PR-C3 (approved, same C1+S2 architecture as PR-C2): the remaining
highest-value direct fact-lifecycle mutation paths — store_fact() /
store_fact_result() (core.memory.SQLiteGraphStore._store_fact_outcome()),
store_facts_batch(), invalidate_edge(), and supersede_fact_cas() — get the
identical tamper-evident AuditChain wiring already proven for
update_state()/_promote_to_validated_cas() in PR-C2.

Design reused verbatim, no new architecture:
- C1: the AuditChain append and the canonical `facts` mutation commit or
  roll back together — same connection, same transaction (all four paths
  already do their canonical SQL inside one `with self._db() as conn:`
  block; the audit append is added strictly after the canonical mutation
  is known to have succeeded, inside that same block).
- S2: chain_id = f"fact-transition:{audit_subject_id}" — ONE chain per
  fact, shared across EVERY lifecycle event for that fact regardless of
  which mutation path produced it (creation, ESM transition, terminal
  state, temporal invalidation, supersede). audit_subject_id is reused
  from facts.audit_subject_id (migration 018, already applied on main)
  if already set, else minted lazily — never the real fact_id.
- memory_events.fact_id stays NULL for every event.
- actor/reason are always structured codes, never free text:
  ACTOR_CODE_STORE_FACT / ACTOR_CODE_STORE_FACTS_BATCH /
  ACTOR_CODE_INVALIDATE_EDGE are fixed constants (these call sites accept
  no caller-supplied `by` string at all); supersede_fact_cas's existing
  `by` parameter is mapped through the same closed _ACTOR_CODE_MAP used
  for transition_esm()/update_state(). REASON_CODE_DIRECT_WRITE (plain
  upsert, no CAS precondition) / REASON_CODE_CAS_GUARDED_WRITE
  (invalidate_edge's updated_at CAS) / REASON_CODE_CAS_TRANSITION
  (supersede_fact_cas's genuine CAS-guarded ESM ladder, reused unchanged
  from PR-C2).

A shared deterministic real-thread + threading.Event technique (no
time.sleep) is reused from PR-C1d/PR-C2's own test suites for the
concurrency proof.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
APPLY_MIGRATIONS = os.path.join(SCRIPTS_DIR, "apply_migrations.py")


def _run_apply(db_path: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, APPLY_MIGRATIONS, "--db", db_path, "--no-backup"],
        capture_output=True, text=True,
    )


@pytest.fixture
def migrated_store(tmp_path, monkeypatch):
    """Same convention as tests/test_audit_chain_transition_ledger.py's own
    fixture of the same name — migrations 008-018 actually applied, real
    triggers present, facts.audit_subject_id column present."""
    from core import memory

    db_path = str(tmp_path / "lifecycle.db")
    bootstrap = memory.SQLiteGraphStore(db_path)
    bootstrap.get_fact("__bootstrap__")
    bootstrap.close()
    result = _run_apply(db_path)
    assert result.returncode == 0, (
        f"apply_migrations failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )

    fresh = memory.make_store(db_path)
    monkeypatch.setattr(memory, "_GLOBAL_STORE", fresh)
    monkeypatch.setattr(memory, "_L0", fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH", db_path)
    yield fresh
    fresh.close()


def _events(store, chain_id: str):
    with store._db() as conn:
        return conn.execute(
            "SELECT * FROM memory_events WHERE chain_id = ? ORDER BY chain_sequence",
            (chain_id,),
        ).fetchall()


def _audit_subject_id(store, fact_id: str):
    with store._db() as conn:
        row = conn.execute(
            "SELECT audit_subject_id FROM facts WHERE fact_id = ?", (fact_id,)
        ).fetchone()
        return row[0] if row else None


def _chain_id_for(store, fact_id: str) -> str:
    subject_id = _audit_subject_id(store, fact_id)
    assert subject_id, f"expected facts.audit_subject_id to be set for {fact_id!r}"
    return f"fact-transition:{subject_id}"


def _event_count(store) -> int:
    with store._db() as conn:
        return conn.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0]


class TestStoreFactAuditWiring:
    def test_new_fact_creation_logs_exactly_one_fact_created_event(self, migrated_store):
        store = migrated_store
        fid = "f_create_1"
        ok = store.store_fact({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        assert ok is True

        chain_id = _chain_id_for(store, fid)
        rows = _events(store, chain_id)
        assert len(rows) == 1, f"expected exactly one event, got {len(rows)}"
        row = rows[0]
        assert row["event_type"] == "fact_created"
        assert row["actor"] == "memory_store_fact"
        assert row["reason"] == "direct_write"
        assert row["to_state"] == "Observed"
        assert row["fact_id"] is None, "memory_events.fact_id must NEVER hold the real fact_id"
        assert row["payload"] == "{}"
        assert row["hash_version"] == 2
        assert row["chain_id"] == chain_id

    def test_updating_existing_fact_logs_exactly_one_fact_updated_event(self, migrated_store):
        store = migrated_store
        fid = "f_update_1"
        store.store_fact({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        chain_id = _chain_id_for(store, fid)
        assert len(_events(store, chain_id)) == 1

        ok = store.store_fact({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.9})
        assert ok is False, "an UPDATE of an existing fact must not report a fresh INSERT"

        rows = _events(store, chain_id)
        assert len(rows) == 2
        assert rows[-1]["event_type"] == "fact_updated"
        assert rows[-1]["actor"] == "memory_store_fact"
        assert rows[-1]["reason"] == "direct_write"
        assert rows[-1]["fact_id"] is None

    def test_noop_update_logs_zero_new_events(self, migrated_store):
        store = migrated_store
        fid = "f_noop_1"
        fact = {"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5}
        store.store_fact(fact)
        chain_id = _chain_id_for(store, fid)
        assert len(_events(store, chain_id)) == 1

        ok = store.store_fact(dict(fact))  # byte-identical re-post -> pure no-op, no SQL write
        assert ok is False
        assert len(_events(store, chain_id)) == 1, (
            "a no-op (no durable SQL write at all) must log zero new events"
        )

    def test_write_gate_rejection_logs_zero_events(self, migrated_store, monkeypatch):
        from core import write_gate
        monkeypatch.setattr(write_gate, "is_write_gate_enabled", lambda: True)
        monkeypatch.setattr(write_gate, "admit_fact", lambda **k: (False, "no_evidence"))

        store = migrated_store
        fid = "f_rejected_1"
        result = store.store_fact_result(
            {"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5}
        )
        assert result.status.name == "REJECTED_WRITE_GATE"
        assert store.get_fact(fid) is None
        assert _audit_subject_id(store, fid) is None, "a rejected write must never touch facts at all"
        assert _event_count(store) == 0

    def test_drift_protection_contradiction_logs_fact_contradicted_event(self, migrated_store):
        store = migrated_store
        fid = "f_drift_1"
        store.store_fact({"fact_id": fid, "claim": "original claim", "source": "s", "confidence": 0.9})
        store.transition_esm(fid, "Hypothesized", by="truth_gate")
        store.transition_esm(fid, "Supported", by="truth_gate")
        chain_id = _chain_id_for(store, fid)
        events_before = len(_events(store, chain_id))

        # Re-posting a DIFFERENT claim at a Supported fact triggers TASK-02
        # drift protection: an automatic ESM transition to Contradicted,
        # entirely inside store_fact() — bypassing transition_esm() and
        # update_state() altogether. This is a genuine, pre-existing ESM
        # transition that was never audited before this PR.
        store.store_fact({"fact_id": fid, "claim": "a contradicting claim", "source": "s", "confidence": 0.9})
        assert store.get_fact(fid)["epistemic_state"] == "Contradicted"

        rows = _events(store, chain_id)
        assert len(rows) == events_before + 1
        assert rows[-1]["event_type"] == "fact_contradicted"
        assert rows[-1]["from_state"] == "Supported"
        assert rows[-1]["to_state"] == "Contradicted"
        assert rows[-1]["actor"] == "memory_store_fact"
        assert rows[-1]["reason"] == "direct_write"

    def test_forced_audit_failure_rolls_back_canonical_insert(self, migrated_store, monkeypatch):
        store = migrated_store
        fid = "f_store_rollback"

        from core import audit_chain

        def _boom(self, *a, **k):
            raise RuntimeError("forced AuditChain failure for atomicity proof")

        monkeypatch.setattr(audit_chain.AuditChain, "log_in_transaction", _boom)

        with pytest.raises(RuntimeError, match="forced AuditChain failure"):
            store.store_fact({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.5})

        assert store.get_fact(fid) is None, (
            "the canonical INSERT must be rolled back together with the "
            "failed AuditChain append — same transaction, same connection"
        )
        assert _event_count(store) == 0

    def test_retry_after_rollback_logs_exactly_one_event(self, migrated_store, monkeypatch):
        store = migrated_store
        fid = "f_store_retry"

        from core import audit_chain as ac_module
        real_append_once = ac_module.AuditChain._append_once
        attempts = {"n": 0}

        def _fail_once(self, conn, **kwargs):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise RuntimeError("simulated transient failure on first attempt")
            return real_append_once(self, conn, **kwargs)

        monkeypatch.setattr(ac_module.AuditChain, "_append_once", _fail_once)

        with pytest.raises(RuntimeError, match="simulated transient failure"):
            store.store_fact({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.5})
        assert store.get_fact(fid) is None

        ok = store.store_fact({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.5})
        assert ok is True
        chain_id = _chain_id_for(store, fid)
        assert len(_events(store, chain_id)) == 1, "the failed first attempt must have left no trace"

    def test_chain_id_stable_from_creation_through_later_esm_transition(self, migrated_store):
        store = migrated_store
        fid = "f_store_chain_stable"
        store.store_fact({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.5})
        chain_after_create = _chain_id_for(store, fid)

        store.transition_esm(fid, "Hypothesized", by="truth_gate")
        chain_after_transition = _chain_id_for(store, fid)

        assert chain_after_create == chain_after_transition, (
            "the fact's chain_id must not change between store_fact() and a "
            "later transition_esm() call — one chain, whichever path wrote first"
        )
        rows = _events(store, chain_after_create)
        assert len(rows) == 2
        assert rows[0]["event_type"] == "fact_created"
        assert rows[1]["event_type"] == "esm_transition"


class TestStoreFactsBatchAuditWiring:
    def test_batch_create_logs_one_event_per_new_fact(self, migrated_store):
        store = migrated_store
        facts = [
            {"fact_id": "f_batch_1", "claim": "c1", "source": "s", "confidence": 0.5},
            {"fact_id": "f_batch_2", "claim": "c2", "source": "s", "confidence": 0.5},
        ]
        stats = store.store_facts_batch(facts)
        assert stats["stored"] == 2

        for fid in ("f_batch_1", "f_batch_2"):
            chain_id = _chain_id_for(store, fid)
            rows = _events(store, chain_id)
            assert len(rows) == 1
            assert rows[0]["event_type"] == "fact_created"
            assert rows[0]["actor"] == "memory_store_facts_batch"
            assert rows[0]["reason"] == "direct_write"
            assert rows[0]["fact_id"] is None

    def test_batch_update_logs_fact_updated_events(self, migrated_store):
        store = migrated_store
        store.store_facts_batch([{"fact_id": "f_batch_u", "claim": "c1", "source": "s", "confidence": 0.5}])
        chain_id = _chain_id_for(store, "f_batch_u")
        assert len(_events(store, chain_id)) == 1

        store.store_facts_batch([{"fact_id": "f_batch_u", "claim": "c1", "source": "s", "confidence": 0.9}])
        rows = _events(store, chain_id)
        assert len(rows) == 2
        assert rows[-1]["event_type"] == "fact_updated"
        assert rows[-1]["actor"] == "memory_store_facts_batch"

    def test_batch_partial_validation_failure_only_logs_events_for_valid_facts(self, migrated_store):
        store = migrated_store
        facts = [
            {"fact_id": "f_batch_ok", "claim": "c1", "source": "s", "confidence": 0.5},
            {"fact_id": "", "claim": "no id", "source": "s", "confidence": 0.5},  # invalid: no fact_id
            {"fact_id": "f_batch_bad_state", "claim": "c", "source": "s",
             "confidence": 0.5, "epistemic_state": "Validated"},  # invalid: new fact must be Observed
        ]
        stats = store.store_facts_batch(facts)
        assert stats["stored"] == 1
        assert stats["errors"] == 2

        chain_id = _chain_id_for(store, "f_batch_ok")
        assert len(_events(store, chain_id)) == 1
        assert store.get_fact("f_batch_bad_state") is None
        assert _audit_subject_id(store, "f_batch_bad_state") is None, (
            "a fact that never reached the canonical transaction must never "
            "get an audit_subject_id or any audit event"
        )
        assert _event_count(store) == 1

    def test_empty_batch_logs_nothing(self, migrated_store):
        store = migrated_store
        stats = store.store_facts_batch([])
        assert stats == {"stored": 0, "updated": 0, "drift": 0, "errors": 0}
        assert _event_count(store) == 0

    def test_forced_audit_failure_rolls_back_whole_batch(self, migrated_store, monkeypatch):
        store = migrated_store
        from core import audit_chain

        def _boom(self, *a, **k):
            raise RuntimeError("forced AuditChain failure for atomicity proof")

        monkeypatch.setattr(audit_chain.AuditChain, "log_in_transaction", _boom)

        facts = [
            {"fact_id": "f_batch_roll_1", "claim": "c1", "source": "s", "confidence": 0.5},
            {"fact_id": "f_batch_roll_2", "claim": "c2", "source": "s", "confidence": 0.5},
        ]
        with pytest.raises(RuntimeError, match="forced AuditChain failure"):
            store.store_facts_batch(facts)

        assert store.get_fact("f_batch_roll_1") is None, (
            "the WHOLE batch transaction must roll back, including facts "
            "processed before the one whose audit append failed"
        )
        assert store.get_fact("f_batch_roll_2") is None
        assert _event_count(store) == 0


class TestInvalidateEdgeAuditWiring:
    def test_successful_invalidate_logs_exactly_one_event(self, migrated_store):
        store = migrated_store
        fid = "f_invalidate_1"
        store.store_fact({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.5})
        chain_id = _chain_id_for(store, fid)
        events_before = len(_events(store, chain_id))

        ok = store.invalidate_edge(fid, t_event_valid_end="2026-01-01T00:00:00+00:00")
        assert ok is True

        rows = _events(store, chain_id)
        assert len(rows) == events_before + 1
        row = rows[-1]
        assert row["event_type"] == "fact_invalidated"
        assert row["actor"] == "memory_invalidate_edge"
        assert row["reason"] == "cas_guarded_write"
        assert row["fact_id"] is None
        assert row["payload"] == "{}"

    def test_cas_miss_logs_zero_events(self, migrated_store):
        store = migrated_store
        fid = "f_invalidate_cas_miss"
        store.store_fact({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.5})
        chain_id = _chain_id_for(store, fid)
        events_before = len(_events(store, chain_id))

        # Stale L0 with an updated_at that no longer matches the real row —
        # forces the CAS guard (WHERE fact_id=? AND updated_at=?) to miss.
        cached = dict(store.get_fact(fid))
        cached["updated_at"] = "1999-01-01T00:00:00+00:00"
        store._l0_put(fid, cached)

        ok = store.invalidate_edge(fid)
        assert ok is False
        assert len(_events(store, chain_id)) == events_before

    def test_nonexistent_fact_logs_zero_events(self, migrated_store):
        store = migrated_store
        ok = store.invalidate_edge("f_does_not_exist")
        assert ok is False
        assert _event_count(store) == 0

    def test_forced_audit_failure_rolls_back_invalidate(self, migrated_store, monkeypatch):
        store = migrated_store
        fid = "f_invalidate_rollback"
        store.store_fact({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.5})
        fact_before = store.get_fact(fid)

        from core import audit_chain

        def _boom(self, *a, **k):
            raise RuntimeError("forced AuditChain failure for atomicity proof")

        monkeypatch.setattr(audit_chain.AuditChain, "log_in_transaction", _boom)

        with pytest.raises(RuntimeError, match="forced AuditChain failure"):
            store.invalidate_edge(fid)

        fact_after = store.get_fact(fid)
        assert fact_after["t_event_valid_end"] == fact_before["t_event_valid_end"]
        assert fact_after["updated_at"] == fact_before["updated_at"]


def _make_supersede_ready_old_fact(store, fact_id: str) -> None:
    """supersede_fact_cas()'s guarded old-fact UPDATE goes straight to
    'Deprecated' — the DB-level ESM-transition trigger only allows that
    directly from 'Hypothesized' or 'Validated' (core.memory.
    ESM_TRANSITIONS), matching the real production scenario (replacing an
    established Validated fact), so advance the seed fact there first."""
    store.store_fact({"fact_id": fact_id, "claim": "old claim", "source": "s", "confidence": 0.9})
    assert store.transition_esm(fact_id, "Hypothesized", by="truth_gate")
    assert store.transition_esm(fact_id, "Supported", by="truth_gate")
    assert store.transition_esm(fact_id, "Validated", by="truth_gate")


class TestSupersedeFactCasAuditWiring:
    def test_successful_supersede_logs_new_fact_created_and_old_fact_deprecated(self, migrated_store):
        store = migrated_store
        old_id, new_id = "f_supersede_old_1", "f_supersede_new_1"
        _make_supersede_ready_old_fact(store, old_id)
        old_before = store.get_fact(old_id)
        old_events_before = len(_events(store, _chain_id_for(store, old_id)))

        result = store.supersede_fact_cas(
            old_id=old_id, new_fact_id=new_id,
            new_record_seed={"claim": "new claim", "source": "s", "confidence": 0.9},
            expected_old_state=old_before["epistemic_state"],
            expected_old_updated_at=old_before["updated_at"],
            old_durable_snapshot=old_before,
            by="truth_maintenance.supersede",
        )
        assert result.committed is True

        new_chain_id = _chain_id_for(store, new_id)
        new_rows = _events(store, new_chain_id)
        assert len(new_rows) == 1
        assert new_rows[0]["event_type"] == "fact_created"
        assert new_rows[0]["to_state"] == "Validated"
        assert new_rows[0]["actor"] == "truth_maintenance_supersede"
        assert new_rows[0]["reason"] == "cas_guarded_transition"
        assert new_rows[0]["fact_id"] is None

        old_chain_id = _chain_id_for(store, old_id)
        old_rows = _events(store, old_chain_id)
        assert len(old_rows) == old_events_before + 1
        last_old_row = old_rows[-1]
        assert last_old_row["event_type"] == "fact_deprecated"
        assert last_old_row["from_state"] == old_before["epistemic_state"]
        assert last_old_row["to_state"] == "Deprecated"
        assert last_old_row["actor"] == "truth_maintenance_supersede"
        assert old_chain_id != new_chain_id, "each fact_id keeps its own independent chain"

    def test_cas_miss_on_old_fact_logs_zero_events(self, migrated_store):
        store = migrated_store
        old_id, new_id = "f_supersede_old_miss", "f_supersede_new_miss"
        _make_supersede_ready_old_fact(store, old_id)
        old_snapshot = store.get_fact(old_id)
        events_before = _event_count(store)

        result = store.supersede_fact_cas(
            old_id=old_id, new_fact_id=new_id,
            new_record_seed={"claim": "new claim", "source": "s", "confidence": 0.9},
            expected_old_state=old_snapshot["epistemic_state"],
            expected_old_updated_at="1999-01-01T00:00:00+00:00",  # stale on purpose
            old_durable_snapshot=old_snapshot,
            by="truth_maintenance.supersede",
        )
        assert result.committed is False
        assert store.get_fact(new_id) is None
        assert _event_count(store) == events_before, "a CAS miss must not append any new event"

    def test_new_id_collision_logs_zero_events(self, migrated_store):
        store = migrated_store
        old_id, new_id = "f_supersede_old_coll", "f_supersede_new_coll"
        _make_supersede_ready_old_fact(store, old_id)
        store.store_fact({"fact_id": new_id, "claim": "already exists", "source": "s", "confidence": 0.5})
        old_snapshot = store.get_fact(old_id)
        new_chain = _chain_id_for(store, new_id)
        old_chain = _chain_id_for(store, old_id)
        events_before_new = len(_events(store, new_chain))
        events_before_old = len(_events(store, old_chain))

        result = store.supersede_fact_cas(
            old_id=old_id, new_fact_id=new_id,
            new_record_seed={"claim": "new claim", "source": "s", "confidence": 0.9},
            expected_old_state=old_snapshot["epistemic_state"],
            expected_old_updated_at=old_snapshot["updated_at"],
            old_durable_snapshot=old_snapshot,
            by="truth_maintenance.supersede",
        )
        assert result.committed is False
        assert result.reason == "new_id_collision"
        assert len(_events(store, new_chain)) == events_before_new
        assert len(_events(store, old_chain)) == events_before_old

    def test_forced_audit_failure_rolls_back_both_facts(self, migrated_store, monkeypatch):
        store = migrated_store
        old_id, new_id = "f_supersede_old_rollback", "f_supersede_new_rollback"
        _make_supersede_ready_old_fact(store, old_id)
        old_before = store.get_fact(old_id)

        from core import audit_chain

        def _boom(self, *a, **k):
            raise RuntimeError("forced AuditChain failure for atomicity proof")

        monkeypatch.setattr(audit_chain.AuditChain, "log_in_transaction", _boom)

        with pytest.raises(RuntimeError, match="forced AuditChain failure"):
            store.supersede_fact_cas(
                old_id=old_id, new_fact_id=new_id,
                new_record_seed={"claim": "new claim", "source": "s", "confidence": 0.9},
                expected_old_state=old_before["epistemic_state"],
                expected_old_updated_at=old_before["updated_at"],
                old_durable_snapshot=old_before,
                by="truth_maintenance.supersede",
            )

        assert store.get_fact(new_id) is None, "new fact insert must roll back too"
        fact_after = store.get_fact(old_id)
        assert fact_after["epistemic_state"] == old_before["epistemic_state"], (
            "old fact's Deprecated transition must roll back together with "
            "the failed audit append — same transaction"
        )
        assert fact_after["updated_at"] == old_before["updated_at"]


class TestConcurrencyNoForkAcrossLifecyclePaths:
    def test_concurrent_store_fact_writers_no_fork_no_duplicate_chain_tip(self, migrated_store):
        """Two independent SQLiteGraphStore instances (genuinely separate
        connections/locks, same db file — mirrors PR-C2's own
        TestAuditSubjectIdNeverFragments technique) racing store_fact() on
        the same fact_id. Both writes are unconditional upserts (no CAS
        precondition of their own), so both succeed; the property under
        test is that the audit chain's own head CAS
        (audit_chain_heads.last_sequence) never forks or loses an append
        even when two real threads append to the SAME chain_id."""
        from core.memory import SQLiteGraphStore

        store_a = migrated_store
        fid = "f_concurrent_store"
        store_a.store_fact({"fact_id": fid, "claim": "v0", "source": "s", "confidence": 0.5})
        chain_id = _chain_id_for(store_a, fid)

        store_b = SQLiteGraphStore(store_a.db_path)

        release_b = threading.Event()
        a_entered = threading.Event()
        paused_once = threading.Event()
        results: dict[str, bool] = {}

        from core import audit_chain as ac_module
        real_append_once = ac_module.AuditChain._append_once

        def _gated_append_once(self, conn, **kwargs):
            if kwargs.get("event_type") == "fact_updated" and not paused_once.is_set():
                paused_once.set()
                a_entered.set()
                release_b.wait(timeout=5)
            return real_append_once(self, conn, **kwargs)

        def writer_a():
            results["a"] = store_a.store_fact(
                {"fact_id": fid, "claim": "v1", "source": "s", "confidence": 0.5}
            )

        def writer_b():
            assert a_entered.wait(timeout=5), "writer A never reached its audit append"
            results["b"] = store_b.store_fact(
                {"fact_id": fid, "claim": "v2", "source": "s", "confidence": 0.5}
            )
            release_b.set()

        ac_module.AuditChain._append_once = _gated_append_once
        t_a = threading.Thread(target=writer_a)
        t_a.start()
        t_b = threading.Thread(target=writer_b)
        t_b.start()
        t_a.join(timeout=10)
        t_b.join(timeout=10)
        ac_module.AuditChain._append_once = real_append_once
        store_b.close()

        rows = _events(store_a, chain_id)
        assert len(rows) == 3, f"expected 1 create + 2 updates, got {len(rows)}"
        sequences = [r["chain_sequence"] for r in rows]
        assert sequences == sorted(set(sequences)), "chain_sequence must be strictly increasing, no fork"


class TestErasureRegressionForLifecyclePaths:
    def test_erasure_removes_direct_mapping_for_a_fact_created_via_store_fact(self, migrated_store):
        store = migrated_store
        fid = "f_erase_c3"
        store.store_fact({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.5})
        chain_id = _chain_id_for(store, fid)
        assert len(_events(store, chain_id)) == 1

        result = store.erase_fact_dependents_atomic(fid)
        assert result["tables"]["facts"]["deleted"] == 1
        assert store.get_fact(fid) is None, "the fact and its audit_subject_id mapping must be gone"

        rows = _events(store, chain_id)
        assert len(rows) == 1, "erasure must not touch memory_events at all"

        from core.audit_chain import AuditChain
        with store._db() as conn:
            report = AuditChain(conn, chain_id=chain_id).verify_chain()
        assert report["valid"] is True, (
            "an erased fact's chain must still verify — chain integrity "
            "never depended on the fact row existing"
        )


class TestChainEnumerationNoPhantomChains:
    def test_invalidate_edge_cas_miss_does_not_produce_a_listed_chain(self, migrated_store):
        store = migrated_store
        fid = "f_phantom_invalidate"
        store.store_fact({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.5})

        cached = dict(store.get_fact(fid))
        cached["updated_at"] = "1999-01-01T00:00:00+00:00"
        store._l0_put(fid, cached)

        ok = store.invalidate_edge(fid)
        assert ok is False, "sanity: the CAS guard must actually miss for this test to be meaningful"

        from core.audit_chain import AuditChain
        with store._db() as conn:
            real_chain_ids = {
                r[0] for r in conn.execute("SELECT DISTINCT chain_id FROM memory_events").fetchall()
            }
            listed = AuditChain(conn).list_chain_ids()
        assert set(listed) == real_chain_ids, (
            f"list_chain_ids() must only report chains with real events; "
            f"listed={listed}, real={real_chain_ids}"
        )


class TestChainIdStabilityAcrossMutationFamilies:
    def test_same_fact_shares_one_chain_across_store_fact_transition_esm_and_invalidate_edge(
        self, migrated_store,
    ):
        """The core architectural claim of this PR: every lifecycle event
        for one fact — however it was produced, C2's update_state()/
        _promote_to_validated_cas() or C3's store_fact()/invalidate_edge()/
        supersede_fact_cas() — lands in the SAME per-fact chain."""
        store = migrated_store
        fid = "f_cross_path_chain"
        store.store_fact({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.5})
        chain_id = _chain_id_for(store, fid)

        store.transition_esm(fid, "Hypothesized", by="truth_gate")
        assert _chain_id_for(store, fid) == chain_id

        store.invalidate_edge(fid, t_event_valid_end="2026-01-01T00:00:00+00:00")
        assert _chain_id_for(store, fid) == chain_id

        rows = _events(store, chain_id)
        assert len(rows) == 3
        assert [r["event_type"] for r in rows] == [
            "fact_created", "esm_transition", "fact_invalidated",
        ]

        from core.audit_chain import AuditChain
        with store._db() as conn:
            report = AuditChain(conn, chain_id=chain_id).verify_chain()
        assert report["valid"] is True


class TestActorReasonCodesStructuredOnlyForLifecyclePaths:
    def test_new_actor_and_reason_codes_are_in_the_allowlists(self):
        from core.audit_chain import (
            ACTOR_CODE_ALLOWLIST,
            ACTOR_CODE_INVALIDATE_EDGE,
            ACTOR_CODE_STORE_FACT,
            ACTOR_CODE_STORE_FACTS_BATCH,
            REASON_CODE_ALLOWLIST,
            REASON_CODE_CAS_GUARDED_WRITE,
            REASON_CODE_DIRECT_WRITE,
            map_actor_code,
        )
        assert ACTOR_CODE_STORE_FACT in ACTOR_CODE_ALLOWLIST
        assert ACTOR_CODE_STORE_FACTS_BATCH in ACTOR_CODE_ALLOWLIST
        assert ACTOR_CODE_INVALIDATE_EDGE in ACTOR_CODE_ALLOWLIST
        assert REASON_CODE_DIRECT_WRITE in REASON_CODE_ALLOWLIST
        assert REASON_CODE_CAS_GUARDED_WRITE in REASON_CODE_ALLOWLIST
        assert map_actor_code("truth_maintenance.supersede") in ACTOR_CODE_ALLOWLIST
        assert map_actor_code("truth_maintenance.supersede") != "actor_unmapped"
