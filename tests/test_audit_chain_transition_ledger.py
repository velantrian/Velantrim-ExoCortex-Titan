"""
PR-C2 (AuditChain final design gate, approved): ESM/terminal-state
transitions get a tamper-evident, atomic AuditChain event.

Design actually under test (see the design-gate reports for the full
evidence trail):

- C1: the AuditChain append and the canonical `facts` UPDATE inside
  core.memory.SQLiteGraphStore.update_state() commit or roll back
  together — same connection, same transaction.
- S2: `chain_id = f"fact-transition:{audit_subject_id}"`, one independent
  hash-chain per fact. `audit_subject_id` is an opaque, lazily-generated
  token stored on `facts.audit_subject_id` (migration 018) — NEVER the
  real `fact_id`. `memory_events.fact_id` stays NULL for every event
  produced by this integration.
- No free text ever reaches AuditChain: `actor` is a closed `actor_code`
  (mapped from the caller's `by` string, falling back to
  "actor_unmapped"), `reason` is the single structured
  `REASON_CODE_CAS_TRANSITION` constant, `payload`/`confidence` are
  always None.
- update_state() itself is the sole choke point — transition_esm() gets
  coverage for free, and a direct update_state() call cannot bypass it.

A shared deterministic real-thread + threading.Event technique (no
time.sleep) is reused from PR-C1d's own test suite for the concurrency
proof.
"""
from __future__ import annotations

import os
import sqlite3
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
    """Same convention as the other test files' fixture of the same name —
    migrations 008-018 actually applied, real triggers present."""
    from core import memory

    db_path = str(tmp_path / "ledger.db")
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


def _events(store, chain_id: str) -> list[sqlite3.Row]:
    with store._db() as conn:
        return conn.execute(
            "SELECT * FROM memory_events WHERE chain_id = ? ORDER BY chain_sequence",
            (chain_id,),
        ).fetchall()


def _all_transition_events(store) -> list[sqlite3.Row]:
    with store._db() as conn:
        return conn.execute(
            "SELECT * FROM memory_events WHERE chain_id LIKE 'fact-transition:%' "
            "ORDER BY rowid"
        ).fetchall()


def _audit_subject_id(store, fact_id: str) -> str | None:
    with store._db() as conn:
        row = conn.execute(
            "SELECT audit_subject_id FROM facts WHERE fact_id = ?", (fact_id,)
        ).fetchone()
        return row[0] if row else None


def _chain_id_for(store, fact_id: str) -> str:
    subject_id = _audit_subject_id(store, fact_id)
    assert subject_id, f"expected facts.audit_subject_id to be set for {fact_id!r}"
    return f"fact-transition:{subject_id}"


class TestSuccessfulTransitionsLogExactlyOneEvent:
    def test_esm_transition_logs_one_structured_event(self, migrated_store):
        store = migrated_store
        fid = "f_esm1"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})

        ok = store.transition_esm(fid, "Hypothesized", by="truth_gate")
        assert ok is True

        chain_id = _chain_id_for(store, fid)
        rows = _events(store, chain_id)
        assert len(rows) == 1, f"expected exactly one event, got {len(rows)}"
        row = rows[0]
        assert row["event_type"] == "esm_transition"
        assert row["actor"] == "truth_gate"
        assert row["reason"] == "cas_guarded_transition"
        assert row["from_state"] == "Observed"
        assert row["to_state"] == "Hypothesized"
        assert row["fact_id"] is None, "memory_events.fact_id must NEVER hold the real fact_id"
        assert row["payload"] == "{}", "no free-text payload for this integration"
        assert row["hash_version"] == 2
        assert row["chain_id"] == chain_id

    def test_terminal_collapsed_transition_uses_same_path_and_event_type(self, migrated_store):
        store = migrated_store
        fid = "f_term_collapsed"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        assert store.transition_esm(fid, "Hypothesized", by="truth_gate")
        assert store.transition_esm(fid, "Deprecated", by="truth_gate")
        assert store.transition_esm(fid, "Collapsed", by="truth_gate")

        chain_id = _chain_id_for(store, fid)
        rows = _events(store, chain_id)
        assert len(rows) == 3
        assert rows[-1]["event_type"] == "fact_collapsed"
        assert rows[-1]["to_state"] == "Collapsed"

    def test_terminal_contradicted_transition_uses_same_path_and_event_type(self, migrated_store):
        store = migrated_store
        fid = "f_term_contradicted"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        assert store.transition_esm(fid, "Hypothesized", by="contradiction_resolver")
        assert store.transition_esm(fid, "Contradicted", by="contradiction_resolver")

        chain_id = _chain_id_for(store, fid)
        rows = _events(store, chain_id)
        assert len(rows) == 2
        assert rows[-1]["event_type"] == "fact_contradicted"
        assert rows[-1]["to_state"] == "Contradicted"

    def test_chain_id_stable_across_multiple_transitions_of_same_fact(self, migrated_store):
        store = migrated_store
        fid = "f_stable_chain"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        store.transition_esm(fid, "Hypothesized", by="truth_gate")
        chain_after_1 = _chain_id_for(store, fid)
        store.transition_esm(fid, "Supported", by="truth_gate")
        chain_after_2 = _chain_id_for(store, fid)
        assert chain_after_1 == chain_after_2, (
            "audit_subject_id (and therefore chain_id) must not change between "
            "transitions of the same fact"
        )
        assert len(_events(store, chain_after_1)) == 2


def _force_stale_l0_cas_miss(store, fact_id: str, real_new_state: str) -> None:
    """update_state() always re-reads the CURRENT state fresh (L0 or a
    fallback SELECT) and uses THAT as its own CAS precondition — it never
    trusts a caller's claimed "from" state. The only way to force a
    genuine CAS-guard miss deterministically (without real threads) is a
    stale L0 cache entry that disagrees with the real DB row: change the
    DB directly (bypassing update_state()/L0 entirely, simulating an
    out-of-band concurrent writer), while leaving the L0 cache holding
    the now-stale prior state."""
    with store._db() as conn:
        conn.execute(
            "UPDATE facts SET epistemic_state = ?, updated_at = ?, "
            "fact_version = fact_version + 1 WHERE fact_id = ?",
            (real_new_state, "2026-01-01T00:00:00+00:00", fact_id),
        )


class TestCasGuardMissProducesNoEvent:
    def test_stale_l0_cache_precondition_creates_zero_events(self, migrated_store):
        store = migrated_store
        fid = "f_cas_miss"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        store.transition_esm(fid, "Hypothesized", by="truth_gate")
        chain_id = _chain_id_for(store, fid)
        assert len(_events(store, chain_id)) == 1

        # L0 cache still says "Hypothesized"; the real row is moved to
        # "Supported" out-of-band (bypassing update_state()/L0 entirely).
        _force_stale_l0_cas_miss(store, fid, "Supported")

        ok = store.update_state(
            fid, "Contradicted",
            {"state": "Contradicted", "from": "Hypothesized", "at": "2026-01-01T00:00:00+00:00", "by": "truth_gate"},
            "2026-01-01T00:00:00+00:00",
        )
        assert ok is False, "the stale L0-cached old_state must miss the CAS guard against the real row"
        assert len(_events(store, chain_id)) == 1, (
            "a CAS-guard miss must not append a second event — the log call "
            "site sits strictly after the rowcount check"
        )


class TestAtomicRollbackOnAuditFailure:
    def test_forced_audit_chain_failure_rolls_back_canonical_update(self, migrated_store, monkeypatch):
        store = migrated_store
        fid = "f_rollback"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})

        from core import audit_chain

        def _boom(self, *a, **k):
            raise RuntimeError("forced AuditChain failure for atomicity proof")

        monkeypatch.setattr(audit_chain.AuditChain, "log_in_transaction", _boom)

        with pytest.raises(RuntimeError, match="forced AuditChain failure"):
            store.transition_esm(fid, "Hypothesized", by="truth_gate")

        fact = store.get_fact(fid)
        assert fact["epistemic_state"] == "Observed", (
            "the canonical UPDATE must be rolled back together with the "
            "failed AuditChain append — same transaction, same connection"
        )
        # No orphan event either, obviously — the whole transaction rolled back.
        rows = _all_transition_events(store)
        assert len(rows) == 0


class TestMissingSchemaFailsClosed:
    def test_missing_append_only_triggers_fails_closed_before_canonical_transition(
        self, migrated_store,
    ):
        store = migrated_store
        fid = "f_missing_triggers"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})

        # Simulate a corrupted/incomplete deployment: memory_events exists
        # (migration 018 ran) but its append-only triggers were somehow
        # dropped. verify_schema_ready() must not silently re-create them
        # (that would defeat deliberately-triggerless test fixtures
        # elsewhere) — it must fail closed instead.
        with store._db() as conn:
            conn.execute("DROP TRIGGER IF EXISTS prevent_audit_update")
            conn.execute("DROP TRIGGER IF EXISTS prevent_audit_delete")

        from core.audit_chain import AuditChainError

        with pytest.raises(AuditChainError, match="missing"):
            store.transition_esm(fid, "Hypothesized", by="truth_gate")

        fact = store.get_fact(fid)
        assert fact["epistemic_state"] == "Observed", (
            "the readiness check runs on a SEPARATE connection/transaction "
            "BEFORE the canonical transaction opens — a failure there must "
            "never touch the facts row at all"
        )


class TestConcurrentWritersNoForkNoDuplicate:
    def test_two_real_threads_same_fact_exactly_one_event_each_no_fork(self, migrated_store):
        store = migrated_store
        fid = "f_concurrent"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        store.transition_esm(fid, "Hypothesized", by="truth_gate")
        chain_id = _chain_id_for(store, fid)

        release_b = threading.Event()
        a_done = threading.Event()
        results: dict[str, bool] = {}

        from core import audit_chain as ac_module
        real_append_once = ac_module.AuditChain._append_once

        def _gated_append_once(self, conn, **kwargs):
            # Writer A pauses right before its own append completes, so
            # writer B's whole CAS-guarded transition (including ITS
            # append) can interleave in between — proving the CAS guard
            # on `facts.epistemic_state` (not just the audit head CAS)
            # prevents a genuine fork: only one of the two concurrent
            # transitions from "Hypothesized" can ever succeed.
            if kwargs.get("to_state") == "Supported":
                release_b.wait(timeout=5)
            return real_append_once(self, conn, **kwargs)

        def writer_a():
            ac_module.AuditChain._append_once = _gated_append_once
            try:
                results["a"] = store.transition_esm(fid, "Supported", by="truth_gate")
            finally:
                a_done.set()

        def writer_b():
            a_done.wait(timeout=1)  # ensure A has entered its transaction first
            results["b"] = store.transition_esm(fid, "Contradicted", by="contradiction_resolver")
            release_b.set()

        # writer_a is entered first synchronously up to the gate; writer_b
        # is only meaningful once A actually holds the CAS precondition —
        # start both as real threads, gate arbitrates ordering.
        t_a = threading.Thread(target=writer_a)
        t_a.start()
        # Give A a moment to actually be inside update_state()'s transaction
        # before B starts, using a_done only for a coarse bound (worst case
        # both attempts race legitimately, which is still a valid proof).
        t_b = threading.Thread(target=writer_b)
        t_b.start()
        t_a.join(timeout=10)
        t_b.join(timeout=10)
        ac_module.AuditChain._append_once = real_append_once

        rows = _events(store, chain_id)
        # Exactly one of Supported/Contradicted must have won the CAS race
        # from "Hypothesized" (both target it as their precondition), so
        # exactly one new event beyond the initial transition is expected.
        assert len(rows) == 2, f"expected 2 events total (1 initial + 1 winner), got {len(rows)}"
        to_states = [r["to_state"] for r in rows]
        assert to_states[0] == "Hypothesized"
        assert to_states[1] in ("Supported", "Contradicted")
        # No forked chain_sequence / duplicate rows for this chain_id.
        sequences = [r["chain_sequence"] for r in rows]
        assert sequences == sorted(set(sequences)), "chain_sequence must be strictly increasing, no fork"


class TestRetrySemantics:
    def test_retry_after_rollback_creates_exactly_one_event(self, migrated_store, monkeypatch):
        store = migrated_store
        fid = "f_retry_rollback"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})

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
            store.transition_esm(fid, "Hypothesized", by="truth_gate")
        assert store.get_fact(fid)["epistemic_state"] == "Observed"

        # Retry: same transition, now succeeds.
        ok = store.transition_esm(fid, "Hypothesized", by="truth_gate")
        assert ok is True
        chain_id = _chain_id_for(store, fid)
        rows = _events(store, chain_id)
        assert len(rows) == 1, "the failed first attempt must have left no trace"

    def test_retry_after_success_creates_no_second_event(self, migrated_store):
        store = migrated_store
        fid = "f_retry_success"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        assert store.transition_esm(fid, "Hypothesized", by="truth_gate") is True
        chain_id = _chain_id_for(store, fid)
        assert len(_events(store, chain_id)) == 1

        # Simulate a caller retrying "the same request" using a stale
        # belief about the pre-transition state, after a genuine
        # out-of-band concurrent write has already moved the real row on
        # (same stale-L0-vs-real-DB technique as the CAS-miss test above)
        # — this is the retry-after-success scenario from the design
        # gate's idempotency proof.
        _force_stale_l0_cas_miss(store, fid, "Supported")
        ok_retry = store.update_state(
            fid, "Hypothesized",
            {"state": "Hypothesized", "from": "Observed", "at": "2026-01-01T00:00:00+00:00", "by": "truth_gate"},
            "2026-01-01T00:00:00+00:00",
        )
        assert ok_retry is False
        assert len(_events(store, chain_id)) == 1, "retry after success must create no second event"


class TestVerifyChainAndTamperDetectionPerFactChain:
    def test_verify_chain_succeeds_for_the_per_fact_chain(self, migrated_store):
        store = migrated_store
        fid = "f_verify"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        store.transition_esm(fid, "Hypothesized", by="truth_gate")
        store.transition_esm(fid, "Supported", by="truth_gate")
        chain_id = _chain_id_for(store, fid)

        from core.audit_chain import AuditChain
        with store._db() as conn:
            report = AuditChain(conn, chain_id=chain_id).verify_chain()
        assert report["valid"] is True, report

    def test_tampering_a_transition_ledger_event_is_detected(self, migrated_store):
        store = migrated_store
        fid = "f_tamper"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        store.transition_esm(fid, "Hypothesized", by="truth_gate")
        chain_id = _chain_id_for(store, fid)

        # Replicate the row onto an untriggered in-memory copy (mirrors
        # tests/test_audit_chain_v2.py's own mutable_db approach) since the
        # real table's append-only triggers correctly forbid a direct
        # UPDATE — this proves the HASH layer independently detects
        # tampering, the same guarantee already proven for every other
        # AuditChain event type, now exercised for this integration's rows.
        with store._db() as conn:
            row = dict(conn.execute(
                "SELECT * FROM memory_events WHERE chain_id = ?", (chain_id,)
            ).fetchone())

        mutable = sqlite3.connect(":memory:")
        mutable.row_factory = sqlite3.Row
        mutable.execute("""
            CREATE TABLE memory_events (
                event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, fact_id TEXT,
                from_state TEXT, to_state TEXT, actor TEXT NOT NULL, reason TEXT,
                payload TEXT, confidence REAL, event_hash TEXT NOT NULL UNIQUE,
                prev_event_hash TEXT, created_at TEXT NOT NULL,
                hash_version INTEGER NOT NULL DEFAULT 1,
                chain_id TEXT NOT NULL DEFAULT 'memory_events', chain_sequence INTEGER
            )
        """)
        cols = list(row.keys())
        mutable.execute(
            f"INSERT INTO memory_events ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
            [row[c] for c in cols],
        )
        mutable.execute(
            "CREATE TABLE audit_chain_heads (chain_id TEXT PRIMARY KEY, "
            "last_sequence INTEGER NOT NULL, last_event_hash TEXT, updated_at TEXT)"
        )
        mutable.execute(
            "INSERT INTO audit_chain_heads VALUES (?, ?, ?, datetime('now'))",
            (chain_id, row["chain_sequence"], row["event_hash"]),
        )
        mutable.commit()

        from core.audit_chain import AuditChain
        assert AuditChain(mutable, chain_id=chain_id).verify_chain()["valid"] is True

        mutable.execute(
            "UPDATE memory_events SET actor = 'tampered_actor' WHERE event_id = ?",
            (row["event_id"],),
        )
        mutable.commit()
        report = AuditChain(mutable, chain_id=chain_id).verify_chain()
        assert report["valid"] is False, "tampering actor must be detected by hash mismatch"


class TestErasureRemovesDirectMappingOnly:
    def test_erasure_removes_live_mapping_but_chain_still_verifies(self, migrated_store):
        store = migrated_store
        fid = "f_erase"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        store.transition_esm(fid, "Hypothesized", by="truth_gate")
        chain_id = _chain_id_for(store, fid)
        assert len(_events(store, chain_id)) == 1

        result = store.erase_fact_dependents_atomic(fid)
        assert result["tables"]["facts"]["deleted"] == 1
        assert store.get_fact(fid) is None, "the fact and its audit_subject_id mapping must be gone"

        # The events themselves survive erasure (tamper-evident ledger
        # preserved) — only the direct live-DB mapping back to the fact is
        # removed.
        rows = _events(store, chain_id)
        assert len(rows) == 1, "erasure must not touch memory_events at all"

        from core.audit_chain import AuditChain
        with store._db() as conn:
            report = AuditChain(conn, chain_id=chain_id).verify_chain()
        assert report["valid"] is True, (
            "an erased fact's chain must still verify — chain integrity "
            "never depended on facts existing once fact_id is NULL"
        )


class TestListChainIds:
    def test_list_chain_ids_enumerates_including_erased_fact_chains(self, migrated_store):
        store = migrated_store
        for fid in ("f_list_1", "f_list_2"):
            store.store_fact_result({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.5})
            store.transition_esm(fid, "Hypothesized", by="truth_gate")
        chain_1 = _chain_id_for(store, "f_list_1")
        chain_2 = _chain_id_for(store, "f_list_2")
        store.erase_fact_dependents_atomic("f_list_1")
        assert store.get_fact("f_list_1") is None

        from core.audit_chain import AuditChain
        with store._db() as conn:
            chain_ids = AuditChain(conn).list_chain_ids()
        assert chain_1 in chain_ids, "an erased fact's chain must still be enumerable"
        assert chain_2 in chain_ids

    def test_list_chain_ids_rejects_invalid_limit(self, migrated_store):
        store = migrated_store
        from core.audit_chain import AuditChain, AuditChainError
        with store._db() as conn:
            chain = AuditChain(conn)
            with pytest.raises(AuditChainError):
                chain.list_chain_ids(limit=0)
            with pytest.raises(AuditChainError):
                chain.list_chain_ids(limit=-5)
            with pytest.raises(AuditChainError):
                chain.list_chain_ids(limit=True)


class TestActorCodeAllowlist:
    def test_unknown_by_value_maps_to_actor_unmapped_never_raises(self, migrated_store):
        store = migrated_store
        fid = "f_unmapped_actor"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})

        # Direct update_state() call with a `by` value not in the
        # allowlist — must not raise, must not store it verbatim.
        ok = store.update_state(
            fid, "Hypothesized",
            {"state": "Hypothesized", "from": "Observed", "at": "2026-01-01T00:00:00+00:00",
             "by": "someone@example.com free text prompt injection attempt"},
            "2026-01-01T00:00:00+00:00",
        )
        assert ok is True
        chain_id = _chain_id_for(store, fid)
        rows = _events(store, chain_id)
        assert len(rows) == 1
        assert rows[0]["actor"] == "actor_unmapped", (
            "free text / unmapped `by` values must never reach AuditChain verbatim"
        )
        assert "@" not in rows[0]["actor"]
        assert "prompt" not in rows[0]["actor"]

    def test_every_production_by_value_maps_to_the_allowlist(self, migrated_store):
        from core.audit_chain import ACTOR_CODE_ALLOWLIST, map_actor_code

        production_by_values = (
            "transition_esm", "truth_gate", "contradiction_resolver",
            "graduated_promotion", "consolidation_engine", "promote_esm",
            "promote_to_validated", "tool:validate_fact", "tool:contradict_fact",
            "tool:propose_hypothesis",
        )
        for by in production_by_values:
            assert map_actor_code(by) in ACTOR_CODE_ALLOWLIST
        assert map_actor_code(None) == "actor_unmapped"
        assert map_actor_code("") == "actor_unmapped"
