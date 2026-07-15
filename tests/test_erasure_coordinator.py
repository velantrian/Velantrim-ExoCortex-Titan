"""P0-B: core.erasure_coordinator — durable, resumable GDPR Art. 17 saga.

Every test constructs a real, temp-file-backed SQLiteGraphStore +
EmbeddingStore + NGramIndex and wires them into an isolated
ErasureCoordinator — no fakes/stubs/mocks anywhere in this file. Each
storage backend is a real SQLite file; deletion is proven by directly
querying that file afterwards, not by trusting the coordinator's own report.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import threading
import time

import numpy as np
import pytest

from core import memory
from core.embedding_store import EmbeddingStore
from core.erasure_coordinator import (
    COMPLETE,
    FAILED,
    NOT_FOUND,
    PARTIAL,
    PENDING,
    RESIDUAL_IMMUTABLE_DATA,
    SUPERSEDED,
    ErasureCoordinator,
)
from core.memory import make_store
from core.ngram_index import NGramIndex


def _fact(fid, claim="user contact is a@b.com", **extra):
    return {"fact_id": fid, "claim": claim, "source": "test", "confidence": 0.9, **extra}


@pytest.fixture
def rig(tmp_path):
    """A fully isolated erasure rig: real facts DB + real embeddings DB +
    real ngram DB, none of them touching the process defaults."""
    store = make_store(str(tmp_path / "facts.db"))
    embeddings = EmbeddingStore(str(tmp_path / "embeddings.db"))
    embeddings.ensure_table()
    ngram = NGramIndex(str(tmp_path / "ngram.db"))
    coordinator = ErasureCoordinator(
        store=store, embedding_store=embeddings, ngram_index=ngram
    )
    return coordinator, store, embeddings, ngram


@pytest.fixture
def migrated_rig(tmp_path):
    """Same as `rig`, but the facts DB has gone through the REAL migration
    chain (008-014), so same-DB dependent tables (relations, fact_mentions,
    l0_fact_provenance, ...) genuinely exist — `rig`'s bare make_store()
    DB only has the runtime-bootstrapped tables (facts, l0_raw_memory,
    l0_fact_provenance, erasure_log), not the migration-only ones."""
    import subprocess
    import sys as _sys

    db_path = str(tmp_path / "facts.db")
    subprocess.run(
        [_sys.executable, os.path.join(os.path.dirname(__file__), "..", "scripts", "apply_migrations.py"),
         "--db", db_path],
        check=True, capture_output=True,
    )
    store = make_store(db_path)
    embeddings = EmbeddingStore(str(tmp_path / "embeddings.db"))
    embeddings.ensure_table()
    ngram = NGramIndex(str(tmp_path / "ngram.db"))
    coordinator = ErasureCoordinator(
        store=store, embedding_store=embeddings, ngram_index=ngram
    )
    return coordinator, store, embeddings, ngram


def _orphan_fact_with_dependent(store, fact_id, insert_dependent):
    """Simulate a legacy/out-of-band deletion: store a fact, let
    `insert_dependent(conn, fact_id)` create a same-DB dependent row for
    it, then remove ONLY the `facts` row directly (bypassing
    erase_fact_dependents_atomic(), which would have cleaned the
    dependent too) — mirroring the exact P1-A "legacy tombstone" shape,
    but for a same-DB dependent table instead of embeddings/ngram."""
    store.store_fact(_fact(fact_id, claim="will be legacy-erased"))
    with store._db() as conn:
        insert_dependent(conn, fact_id)
        conn.execute("DROP TRIGGER IF EXISTS prevent_fact_delete")
        conn.execute("DELETE FROM facts WHERE fact_id = ?", (fact_id,))
        conn.execute(store._PREVENT_FACT_DELETE_TRIGGER_SQL)
        conn.commit()


def _seed_all_layers(store, embeddings, ngram, fact_id, claim):
    store.store_fact(_fact(fact_id, claim=claim))
    embeddings.store(fact_id, np.array([0.1, 0.2, 0.3], dtype=np.float32), model_name="test-model")
    ngram.index(fact_id, claim)


# ── Happy path: COMPLETE across all three storage backends ──────────────────

def test_complete_erasure_purges_facts_embeddings_and_ngram(rig):
    coordinator, store, embeddings, ngram = rig
    _seed_all_layers(store, embeddings, ngram, "f1", "quantum entanglement links particles")

    assert store.get_fact("f1") is not None
    assert embeddings.has_any("f1") is True
    assert ngram.contains("f1") is True

    report = coordinator.erase_fact_durable("f1", reason="dsr", actor="tester")

    assert report["outcome"] == COMPLETE
    assert report["erased_now"] is True
    assert report["residual"] == "none"
    assert report["content_hash"].startswith("sha256:")
    for step in ("determine_raw", "l1_same_db", "embeddings", "ngram"):
        assert report["steps"][step]["status"] == COMPLETE

    # Proven by direct inspection of each real store, not just the report.
    assert store.get_fact("f1") is None
    assert embeddings.has_any("f1") is False
    assert ngram.contains("f1") is False
    assert coordinator.is_erased("f1") is True


def test_complete_report_lists_every_dependent_table(rig):
    coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f2"))
    store._release_stray_locks()
    with store._db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS relations (relation_id TEXT PRIMARY KEY, "
            "from_fact_id TEXT NOT NULL, to_fact_id TEXT NOT NULL, relation_type TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO relations VALUES ('r1', 'f2', 'other', 'causes')"
        )

    report = coordinator.erase_fact_durable("f2")
    tables = report["steps"]["l1_same_db"]["detail"]["tables"]

    assert tables["relations"] == {"applicable": True, "deleted": 1}
    assert tables["facts"] == {"applicable": True, "deleted": 1}
    # fact_versions is created eagerly by SQLiteGraphStore's VersionStore
    # warmup, so it IS applicable here (just empty — f2 was never updated).
    assert tables["fact_versions"] == {"applicable": True, "deleted": 0}
    # fact_mentions (migration 012) was never applied to this bare test
    # store — honestly reported as not_applicable, never silently skipped.
    assert tables["fact_mentions"]["applicable"] is False


# ── Idempotency ───────────────────────────────────────────────────────────

def test_erasure_is_idempotent(rig):
    coordinator, store, _, _ = rig
    store.store_fact(_fact("f3"))

    first = coordinator.erase_fact_durable("f3")
    second = coordinator.erase_fact_durable("f3")

    assert first["outcome"] == COMPLETE and first["erased_now"] is True
    assert second["outcome"] == COMPLETE and second["erased_now"] is False
    assert first["job_id"] == second["job_id"]
    assert len(coordinator.erasure_log()) == 1


# ── NOT_FOUND ────────────────────────────────────────────────────────────

def test_unknown_fact_reports_not_found_without_writing_anything(rig):
    coordinator, store, _, _ = rig

    report = coordinator.erase_fact_durable("does-not-exist")

    assert report["outcome"] == NOT_FOUND
    assert report["erased_now"] is False
    assert coordinator.get_job_report("does-not-exist") is None
    assert coordinator.is_erased("does-not-exist") is False


# ── Ring Zero ────────────────────────────────────────────────────────────

def test_ring_zero_refused_no_job_no_tombstone(rig):
    coordinator, store, _, _ = rig

    with pytest.raises(memory.ImmutableStateError):
        coordinator.erase_fact_durable("RING_ZERO")

    assert coordinator.is_erased("RING_ZERO") is False
    assert coordinator.get_job_report("RING_ZERO") is None


# ── Residual: raw original tri-state ────────────────────────────────────────

def test_residual_none_when_fact_has_no_raw_origin(rig):
    coordinator, store, _, _ = rig
    store.store_fact(_fact("f4"))

    report = coordinator.erase_fact_durable("f4")
    assert report["residual"] == "none"
    assert report["outcome"] == COMPLETE


def test_residual_raw_original_present_yields_residual_immutable_data_not_complete(rig):
    """Review finding: a raw L0 origin means personal data is known to
    still exist (l0_raw_memory is immutable, never deleted) — reporting
    COMPLETE here would claim "provably, completely erased" while that
    isn't true. The derived layer IS fully erased, but the outcome must be
    the distinct terminal state RESIDUAL_IMMUTABLE_DATA: no completion
    tombstone, is_erased() stays False.
    """
    coordinator, store, _, _ = rig
    raw_id = store.store_raw_text("the original raw text", source_type="user_input")
    store.store_fact(_fact("f5"))
    store.link_raw_to_fact(raw_id, "f5")

    report = coordinator.erase_fact_durable("f5")

    assert report["outcome"] == RESIDUAL_IMMUTABLE_DATA
    assert report["residual"] == "raw_original_present"
    assert report["erased_now"] is False
    assert report["content_hash"] is None
    assert report["erased_at"] is None
    # Derived layer IS erased — only the immutable raw origin remains.
    assert store.get_fact("f5") is None
    # No completion tombstone: this must never look "completely erased".
    assert coordinator.is_erased("f5") is False
    assert len(coordinator.erasure_log()) == 0
    # l0_raw_memory itself is untouched (append-only by design).
    with store._db() as conn:
        assert conn.execute(
            "SELECT 1 FROM l0_raw_memory WHERE raw_id = ?", (raw_id,)
        ).fetchone() is not None

    # Idempotent: re-calling doesn't re-run steps or flip the outcome.
    again = coordinator.erase_fact_durable("f5")
    assert again["outcome"] == RESIDUAL_IMMUTABLE_DATA
    assert again["job_id"] == report["job_id"]

    # resume_incomplete_jobs() must not treat this as something to retry
    # forever — it's a terminal, permanent fact about this record.
    assert not any(r["fact_id"] == "f5" for r in coordinator.resume_incomplete_jobs())


def test_undetermined_residual_can_never_reach_complete(rig, monkeypatch):
    coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f6"))

    def _broken_get_fact_durable(fact_id):
        raise __import__("sqlite3").OperationalError("database is locked")

    monkeypatch.setattr(store, "get_fact_durable", _broken_get_fact_durable)

    report = coordinator.erase_fact_durable("f6")

    assert report["residual"] == "undetermined"
    assert report["outcome"] != COMPLETE
    assert report["outcome"] == PARTIAL  # l1_same_db/embeddings/ngram still ran fine
    assert coordinator.is_erased("f6") is False
    assert len(coordinator.erasure_log()) == 0


# ── Honest failure + resumability ───────────────────────────────────────────

def test_embeddings_failure_yields_partial_and_resume_reaches_complete(rig, monkeypatch):
    coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f7"))
    embeddings.store("f7", np.array([1.0, 2.0], dtype=np.float32))

    real_purge = embeddings.purge_node
    calls = {"n": 0}

    def _flaky_purge_node(node_id):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated disk error")
        return real_purge(node_id)

    monkeypatch.setattr(embeddings, "purge_node", _flaky_purge_node)

    first = coordinator.erase_fact_durable("f7")
    assert first["outcome"] == PARTIAL
    assert first["steps"]["embeddings"]["status"] == FAILED
    assert first["steps"]["l1_same_db"]["status"] == COMPLETE
    assert coordinator.is_erased("f7") is False
    # Facts row is really gone already, even though the job isn't COMPLETE.
    assert store.get_fact("f7") is None

    monkeypatch.setattr(embeddings, "purge_node", real_purge)
    second = coordinator.erase_fact_durable("f7")

    assert second["outcome"] == COMPLETE
    assert second["job_id"] == first["job_id"]  # resumed, not duplicated
    assert embeddings.has_any("f7") is False
    assert coordinator.is_erased("f7") is True


def test_l1_failure_does_not_block_other_backends_and_resumes(rig, monkeypatch):
    coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f8"))
    embeddings.store("f8", np.array([1.0], dtype=np.float32))
    ngram.index("f8", "some claim text")

    real_atomic = store.erase_fact_dependents_atomic
    calls = {"n": 0}

    def _flaky_atomic(fact_id):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated same-db failure")
        return real_atomic(fact_id)

    monkeypatch.setattr(store, "erase_fact_dependents_atomic", _flaky_atomic)

    first = coordinator.erase_fact_durable("f8")
    assert first["outcome"] == PARTIAL
    assert first["steps"]["l1_same_db"]["status"] == FAILED
    assert first["steps"]["embeddings"]["status"] == COMPLETE
    assert first["steps"]["ngram"]["status"] == COMPLETE
    assert embeddings.has_any("f8") is False
    assert ngram.contains("f8") is False
    assert store.get_fact("f8") is not None  # not deleted yet — honest PARTIAL

    monkeypatch.setattr(store, "erase_fact_dependents_atomic", real_atomic)
    second = coordinator.erase_fact_durable("f8")

    assert second["outcome"] == COMPLETE
    assert store.get_fact("f8") is None


def test_resume_incomplete_jobs_sweeps_partial_jobs_to_complete(rig, monkeypatch):
    coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f9"))

    real_atomic = store.erase_fact_dependents_atomic
    monkeypatch.setattr(
        store, "erase_fact_dependents_atomic",
        lambda fact_id: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    partial = coordinator.erase_fact_durable("f9")
    assert partial["outcome"] == PARTIAL

    monkeypatch.setattr(store, "erase_fact_dependents_atomic", real_atomic)
    results = coordinator.resume_incomplete_jobs()

    assert any(r["fact_id"] == "f9" and r["outcome"] == COMPLETE for r in results)
    assert coordinator.is_erased("f9") is True


# ── prevent_fact_delete trigger (migration 009) is lifted-then-restored ─────

def test_prevent_fact_delete_trigger_is_restored_after_erasure(rig):
    coordinator, store, _, _ = rig
    store.store_fact(_fact("guarded", epistemic_state="Observed"))
    # A fact stuck in Observed (never Collapsed/Deprecated) — a raw DELETE
    # would be rejected by the real production guard once installed.
    with store._db() as conn:
        conn.execute(memory.SQLiteGraphStore._PREVENT_FACT_DELETE_TRIGGER_SQL)

    report = coordinator.erase_fact_durable("guarded")
    assert report["outcome"] == COMPLETE
    assert store.get_fact("guarded") is None

    # The guard must still be armed afterwards — prove it by trying (and
    # failing) to raw-DELETE a second Observed fact directly.
    store.store_fact(_fact("still_guarded", epistemic_state="Observed"))
    store._release_stray_locks()
    with pytest.raises(Exception):  # sqlite3.IntegrityError from RAISE(ABORT, ...)
        with store._db() as conn:
            conn.execute("DELETE FROM facts WHERE fact_id = 'still_guarded'")
    assert store.get_fact("still_guarded") is not None


def _install_real_failure_trigger(store, *, table: str, fact_id: str) -> None:
    """Install a REAL SQLite trigger that raises on DELETE from `table` for
    `fact_id` — a genuine DB-level failure (RAISE(ABORT, ...)), not a mock,
    exercising the exact code path erase_fact_dependents_atomic()'s
    docstring describes: "a present table whose DELETE raises aborts the
    whole transaction"."""
    trigger_name = f"simulate_{table}_delete_failure"
    with store._db() as conn:
        conn.execute(f"""
            CREATE TRIGGER IF NOT EXISTS {trigger_name}
            BEFORE DELETE ON {table}
            WHEN OLD.fact_id = '{fact_id}'
            BEGIN
                SELECT RAISE(ABORT, 'SIMULATED: real DB failure mid-transaction');
            END;
        """)


def test_prevent_fact_delete_trigger_restored_after_real_delete_failure(rig):
    """Security fix: erase_fact_dependents_atomic() opens an explicit
    BEGIN IMMEDIATE before DROP TRIGGER, so a real failure partway through
    the dependent-table deletes rolls back BOTH the data changes AND the
    DROP TRIGGER — not just the data. Before this fix, DROP TRIGGER
    auto-committed standalone (Python sqlite3 does not implicitly open a
    transaction before DDL), so conn.rollback() could not undo it, leaving
    the whole facts table without its anti-accidental-deletion guard after
    any transient delete failure."""
    coordinator, store, _, _ = rig
    store.store_fact(_fact("trig_fail", epistemic_state="Observed"))
    with store._db() as conn:
        conn.execute(
            "INSERT INTO fact_versions (fact_id, version_num, claim, recorded_at) "
            "VALUES (?, ?, ?, ?)",
            ("trig_fail", 1, "user contact is a@b.com", "2026-01-01T00:00:00Z"),
        )
    _install_real_failure_trigger(store, table="fact_versions", fact_id="trig_fail")

    with pytest.raises(Exception):  # sqlite3.IntegrityError from our RAISE(ABORT, ...)
        store.erase_fact_dependents_atomic("trig_fail")

    # Rollback must have restored BOTH the data ...
    assert store.get_fact("trig_fail") is not None
    with store._db() as conn:
        fv_count = conn.execute(
            "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?", ("trig_fail",)
        ).fetchone()[0]
    assert fv_count == 1

    # ... AND the prevent_fact_delete guard, verified via sqlite_master (not
    # merely assumed), and proven enforcing against a DIFFERENT fact.
    with store._db() as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' "
            "AND name='prevent_fact_delete'"
        ).fetchone()
    assert row is not None, "prevent_fact_delete missing after a failed erasure transaction"

    store.store_fact(_fact("still_guarded_after_failure", epistemic_state="Observed"))
    store._release_stray_locks()
    with pytest.raises(Exception):
        with store._db() as conn:
            conn.execute("DELETE FROM facts WHERE fact_id = 'still_guarded_after_failure'")
    assert store.get_fact("still_guarded_after_failure") is not None

    # Retry after the failed attempt must still work cleanly.
    with store._db() as conn:
        conn.execute("DROP TRIGGER IF EXISTS simulate_fact_versions_delete_failure")
    result = store.erase_fact_dependents_atomic("trig_fail")
    assert result["tables"]["facts"]["deleted"] == 1
    assert result["tables"]["fact_versions"]["deleted"] == 1
    assert store.get_fact("trig_fail") is None
    with store._db() as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' "
            "AND name='prevent_fact_delete'"
        ).fetchone()
    assert row is not None


def test_prevent_fact_delete_trigger_restored_after_failure_in_other_dependent_table(rig):
    """The fix must not be special-cased to fact_versions — any dependent
    table's failure must leave the trigger correctly restored."""
    coordinator, store, _, _ = rig
    store.store_fact(_fact("trig_fail_prov", epistemic_state="Observed"))
    raw_id = store.store_raw_text("some raw text", source_type="user_input")
    with store._db() as conn:
        conn.execute(
            "INSERT INTO l0_fact_provenance (id, raw_id, fact_id) VALUES (?, ?, ?)",
            ("prov1", raw_id, "trig_fail_prov"),
        )
    _install_real_failure_trigger(store, table="l0_fact_provenance", fact_id="trig_fail_prov")

    with pytest.raises(Exception):
        store.erase_fact_dependents_atomic("trig_fail_prov")

    assert store.get_fact("trig_fail_prov") is not None
    with store._db() as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' "
            "AND name='prevent_fact_delete'"
        ).fetchone()
    assert row is not None


def test_prevent_fact_delete_trigger_sql_matches_canonical_guard_after_failure(rig):
    """Not just present — the restored trigger's SQL must match migration
    009's canonical guard exactly, not an approximation."""
    coordinator, store, _, _ = rig
    store.store_fact(_fact("trig_fail_sql", epistemic_state="Observed"))
    with store._db() as conn:
        conn.execute(
            "INSERT INTO fact_versions (fact_id, version_num, claim, recorded_at) "
            "VALUES (?, ?, ?, ?)",
            ("trig_fail_sql", 1, "user contact is a@b.com", "2026-01-01T00:00:00Z"),
        )
    _install_real_failure_trigger(store, table="fact_versions", fact_id="trig_fail_sql")

    with pytest.raises(Exception):
        store.erase_fact_dependents_atomic("trig_fail_sql")

    with store._db() as conn:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='trigger' "
            "AND name='prevent_fact_delete'"
        ).fetchone()
    assert row is not None
    # sqlite_master.sql echoes back the statement without "IF NOT EXISTS"
    # and without a trailing semicolon — normalize both sides the same way
    # before comparing so this only fails on a REAL guard-body mismatch.
    def _normalize(sql: str) -> str:
        return " ".join(sql.replace("IF NOT EXISTS", "").split()).rstrip(";").strip()

    canonical = _normalize(memory.SQLiteGraphStore._PREVENT_FACT_DELETE_TRIGGER_SQL)
    actual = _normalize(row["sql"])
    assert actual == canonical


def test_ring_zero_protection_not_weakened_by_trigger_fix(rig):
    """The explicit-transaction trigger fix must not touch Ring Zero (I6)
    protection — still refused before any transaction is even opened."""
    coordinator, store, _, _ = rig
    with pytest.raises(memory.ImmutableStateError):
        store.erase_fact_dependents_atomic("RING_ZERO")
    with pytest.raises(memory.ImmutableStateError):
        coordinator.erase_fact_durable("RING_ZERO")


# ── concurrency: one durable saga per fact_id, even under a real race ──────

def _seed_one(store, embeddings, ngram, fact_id):
    _seed_all_layers(store, embeddings, ngram, fact_id, "a fact erased under a concurrent race")


def test_concurrent_erase_fact_durable_calls_converge_on_one_job(rig):
    """Security fix: erasure_jobs.fact_id has a UNIQUE index, and
    _get_or_create_job() recovers from a lost create-race by adopting the
    winner's job_id — so two callers racing for the SAME fact_id end up
    with exactly one job row, one job_id, and (thanks to the RUNNING claim
    in _run_job()) the SAME final, consistent outcome."""
    coordinator, store, embeddings, ngram = rig
    _seed_one(store, embeddings, ngram, "race1")

    # Widen the race window deterministically: force both callers to
    # observe "no existing job" before either one proceeds to create it.
    orig_peek = coordinator._peek_job_row

    def slow_peek(fact_id):
        result = orig_peek(fact_id)
        if result is None:
            time.sleep(0.15)
        return result

    coordinator._peek_job_row = slow_peek

    results: dict[str, dict] = {}

    def call(name):
        results[name] = coordinator.erase_fact_durable("race1", reason="test", actor=name)

    t1 = threading.Thread(target=call, args=("A",))
    t2 = threading.Thread(target=call, args=("B",))
    t1.start()
    time.sleep(0.02)
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    assert "A" in results and "B" in results
    assert results["A"]["job_id"] == results["B"]["job_id"]
    assert results["A"]["outcome"] == results["B"]["outcome"] == COMPLETE

    with coordinator._jobs_db() as conn:
        job_rows = conn.execute(
            "SELECT job_id FROM erasure_jobs WHERE fact_id = ?", ("race1",)
        ).fetchall()
        step_rows = conn.execute(
            "SELECT step_name FROM erasure_job_steps WHERE job_id = ?",
            (results["A"]["job_id"],),
        ).fetchall()
    assert len(job_rows) == 1, f"expected exactly 1 job row, got {len(job_rows)}"
    step_names = {r["step_name"] for r in step_rows}
    assert len(step_rows) == 4
    assert len(step_names) == 4

    # No zombie PARTIAL/FAILED job left over after a successful concurrent
    # COMPLETE — the resume sweep must find nothing left to do.
    assert coordinator.resume_incomplete_jobs() == []
    assert coordinator.is_erased("race1") is True


def test_concurrent_erase_fact_durable_across_two_coordinator_instances(rig):
    """Repeat the race with two SEPARATE ErasureCoordinator instances
    sharing one jobs DB file — simulating two processes, not just two
    threads of one coordinator object — to prove the protection is a real
    SQLite constraint/transaction, not an in-process object lock."""
    coordinator, store, embeddings, ngram = rig
    _seed_one(store, embeddings, ngram, "race2")

    coordinator2 = ErasureCoordinator(
        store=make_store(store.db_path),
        embedding_store=EmbeddingStore(embeddings._db_path),
        ngram_index=NGramIndex(ngram.db_path),
        jobs_db_path=coordinator.jobs_db_path,
    )

    for c in (coordinator, coordinator2):
        orig_peek = c._peek_job_row

        def make_slow(orig):
            def slow_peek(fact_id):
                result = orig(fact_id)
                if result is None:
                    time.sleep(0.15)
                return result
            return slow_peek

        c._peek_job_row = make_slow(orig_peek)

    results: dict[str, dict] = {}

    def call(c, name):
        results[name] = c.erase_fact_durable("race2", reason="test", actor=name)

    t1 = threading.Thread(target=call, args=(coordinator, "coord1"))
    t2 = threading.Thread(target=call, args=(coordinator2, "coord2"))
    t1.start()
    time.sleep(0.02)
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    assert results["coord1"]["job_id"] == results["coord2"]["job_id"]
    assert results["coord1"]["outcome"] == results["coord2"]["outcome"] == COMPLETE

    with coordinator._jobs_db() as conn:
        job_rows = conn.execute(
            "SELECT job_id FROM erasure_jobs WHERE fact_id = ?", ("race2",)
        ).fetchall()
    assert len(job_rows) == 1

    assert coordinator.resume_incomplete_jobs() == []
    assert coordinator2.resume_incomplete_jobs() == []
    assert coordinator.is_erased("race2") is True


def test_public_retry_after_complete_returns_cached_job_without_new_generation(rig):
    """The PUBLIC entrypoint, erase_fact_durable(), must adopt the cached
    COMPLETE report and never open a new generation when nothing has
    changed (no residual data reappeared) — this is the idempotency
    contract callers actually rely on."""
    coordinator, store, embeddings, ngram = rig
    _seed_one(store, embeddings, ngram, "retry_complete")

    first = coordinator.erase_fact_durable("retry_complete", reason="test", actor="A")
    assert first["outcome"] == COMPLETE

    again = coordinator.erase_fact_durable("retry_complete", reason="test", actor="B")
    assert again["job_id"] == first["job_id"]
    assert again["outcome"] == COMPLETE
    with coordinator._jobs_db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM erasure_jobs WHERE fact_id = ?", ("retry_complete",)
        ).fetchone()[0]
    assert count == 1


def test_public_retry_after_residual_immutable_data_returns_cached_job(rig):
    """Same guarantee for the RESIDUAL_IMMUTABLE_DATA terminal outcome."""
    coordinator, store, embeddings, ngram = rig
    raw_id = store.store_raw_text("the original raw text", source_type="user_input")
    store.store_fact(_fact("retry_residual"))
    store.link_raw_to_fact(raw_id, "retry_residual")

    first = coordinator.erase_fact_durable("retry_residual", reason="test", actor="A")
    assert first["outcome"] == RESIDUAL_IMMUTABLE_DATA

    again = coordinator.erase_fact_durable("retry_residual", reason="test", actor="B")
    assert again["job_id"] == first["job_id"]
    assert again["outcome"] == RESIDUAL_IMMUTABLE_DATA
    with coordinator._jobs_db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM erasure_jobs WHERE fact_id = ?", ("retry_residual",)
        ).fetchone()[0]
    assert count == 1


def test_internal_get_or_create_job_opens_new_generation_after_terminal(rig):
    """Post-review hotfix: _get_or_create_job() is an internal primitive
    that always opens the NEXT generation when the latest one is terminal
    — it is erase_fact_durable() (the public entrypoint), not this method,
    that decides whether a new generation is actually warranted (via
    _residual_data_present()). Calling it directly after a COMPLETE job
    must NOT return the same job_id — that was the exact P1-B bug
    (fact_id reuse permanently blocked by the old unconditional
    UNIQUE(fact_id) index)."""
    coordinator, store, embeddings, ngram = rig
    _seed_one(store, embeddings, ngram, "direct_call_new_gen")

    first = coordinator.erase_fact_durable("direct_call_new_gen", reason="test", actor="A")
    assert first["outcome"] == COMPLETE

    second_job_id = coordinator._get_or_create_job("direct_call_new_gen", "test", "B")
    assert second_job_id != first["job_id"]
    with coordinator._jobs_db() as conn:
        rows = conn.execute(
            "SELECT job_id, generation, status FROM erasure_jobs "
            "WHERE fact_id = ? ORDER BY generation",
            ("direct_call_new_gen",),
        ).fetchall()
    assert len(rows) == 2
    assert rows[0]["generation"] == 1
    assert rows[0]["job_id"] == first["job_id"]
    assert rows[1]["generation"] == 2
    assert rows[1]["job_id"] == second_job_id


# ── P0-B post-merge hotfix: mandatory regression tests (Section 6) ──────────
#
# P1-A / P1-B / P1-C / P2 were all found in production review after PR #24
# merged. Each test below reproduces the exact failure shape via the public
# API (or, where the bug is about process wiring / import-time behavior,
# via a real subprocess) and asserts the fixed, honest behavior.

def test_legacy_tombstone_with_residual_data_is_not_trusted_as_complete(rig):
    """P1-A regression: a bare `erasure_log` tombstone with NO corresponding
    durable `erasure_jobs` row (written by a pre-coordinator path, e.g. the
    deprecated core.erasure.erase_fact() shim) must never be trusted as
    proof of a durable COMPLETE. erase_fact_durable() must re-verify and
    re-clean any residual embeddings/ngram data instead of returning a false
    early COMPLETE, and must never overwrite the original legacy tombstone."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "legacy_tombstone_fact"

    # Legacy tombstone: job_id=None, no erasure_jobs row exists at all.
    store.write_tombstone(
        fact_id, reason="legacy_shim", actor="legacy", content_hash="deadbeef",
    )
    legacy_tombstone = store.get_tombstone(fact_id)
    assert legacy_tombstone is not None
    with coordinator._jobs_db() as conn:
        job_count = conn.execute(
            "SELECT COUNT(*) FROM erasure_jobs WHERE fact_id = ?", (fact_id,)
        ).fetchone()[0]
    assert job_count == 0

    # The legacy shim never touched embeddings/ngram — residual entries
    # remain, with no `facts` row (exactly the P1-A repro shape).
    embeddings.store(fact_id, np.array([0.1, 0.2, 0.3], dtype=np.float32), model_name="test-model")
    ngram.index(fact_id, "residual claim text")
    assert embeddings.has_any(fact_id) is True
    assert ngram.contains(fact_id) is True

    report = coordinator.erase_fact_durable(fact_id)

    # The bug was returning COMPLETE immediately with residuals untouched.
    # The fix must actually clean the residuals before this call returns.
    assert embeddings.has_any(fact_id) is False
    assert ngram.contains(fact_id) is False
    assert report["outcome"] in (COMPLETE, PARTIAL, FAILED, RESIDUAL_IMMUTABLE_DATA)

    # A NEW durable job now exists for this fact_id, distinct from the
    # legacy tombstone's (nonexistent) job_id.
    with coordinator._jobs_db() as conn:
        job_count = conn.execute(
            "SELECT COUNT(*) FROM erasure_jobs WHERE fact_id = ?", (fact_id,)
        ).fetchone()[0]
    assert job_count == 1

    # The original legacy tombstone row is preserved untouched — append-only
    # Art. 30 audit trail, never overwritten.
    with coordinator._jobs_db() as conn:
        legacy_rows = conn.execute(
            "SELECT erasure_id FROM erasure_log WHERE fact_id = ? AND job_id IS NULL",
            (fact_id,),
        ).fetchall()
    assert len(legacy_rows) == 1
    assert legacy_rows[0]["erasure_id"] == legacy_tombstone["erasure_id"]


def test_fact_recreated_under_same_fact_id_gets_new_generation_via_public_api(rig):
    """P1-B regression, exercised end-to-end through the PUBLIC API (not the
    internal _get_or_create_job() primitive): once a fact_id is durably
    erased, recreated with new data, and durably re-erased, the SECOND call
    must open and complete a NEW generation — deleting the new fact row and
    new embeddings/ngram entries — while the FIRST generation's job row and
    tombstone remain untouched as immutable history."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "reused_fact_public_api"

    _seed_all_layers(store, embeddings, ngram, fact_id, "user phone is 555-1234")
    first = coordinator.erase_fact_durable(fact_id, reason="test", actor="A")
    assert first["outcome"] == COMPLETE
    first_tombstone = store.get_tombstone(fact_id)
    assert first_tombstone is not None

    # Fact re-created under the SAME fact_id, with fresh embeddings/ngram.
    _seed_all_layers(store, embeddings, ngram, fact_id, "user phone is 555-9999 (new)")
    assert store.get_fact(fact_id) is not None
    assert embeddings.has_any(fact_id) is True
    assert ngram.contains(fact_id) is True

    second = coordinator.erase_fact_durable(fact_id, reason="test", actor="B")

    assert second["outcome"] == COMPLETE
    assert second["job_id"] != first["job_id"]
    assert store.get_fact(fact_id) is None
    assert embeddings.has_any(fact_id) is False
    assert ngram.contains(fact_id) is False

    with coordinator._jobs_db() as conn:
        rows = conn.execute(
            "SELECT job_id, generation, status FROM erasure_jobs "
            "WHERE fact_id = ? ORDER BY generation", (fact_id,),
        ).fetchall()
    assert len(rows) == 2
    assert rows[0]["job_id"] == first["job_id"] and rows[0]["status"] == COMPLETE
    assert rows[1]["job_id"] == second["job_id"] and rows[1]["status"] == COMPLETE

    # Both generations get their OWN tombstone row — the first is preserved,
    # not overwritten by the second.
    with coordinator._jobs_db() as conn:
        tombstone_job_ids = {
            r["job_id"] for r in conn.execute(
                "SELECT job_id FROM erasure_log WHERE fact_id = ?", (fact_id,)
            ).fetchall()
        }
    assert tombstone_job_ids == {first["job_id"], second["job_id"]}


def test_concurrent_erase_calls_on_recreated_fact_id_converge_on_one_new_generation(rig):
    """Combine the P1-B fix with the existing concurrency guarantee: two
    threads racing erase_fact_durable() on a fact_id whose PRIOR generation
    is already COMPLETE, but whose data was just recreated, must converge on
    exactly ONE new generation's job_id — not two, and not the stale first
    generation's."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "reused_fact_race"

    _seed_all_layers(store, embeddings, ngram, fact_id, "first generation data")
    first = coordinator.erase_fact_durable(fact_id, reason="test", actor="setup")
    assert first["outcome"] == COMPLETE

    _seed_all_layers(store, embeddings, ngram, fact_id, "second generation data")

    orig_peek = coordinator._peek_job_row

    def slow_peek(fid):
        result = orig_peek(fid)
        if result is not None and result["job_id"] == first["job_id"]:
            time.sleep(0.15)
        return result

    coordinator._peek_job_row = slow_peek

    results: dict[str, dict] = {}

    def call(name):
        results[name] = coordinator.erase_fact_durable(fact_id, reason="test", actor=name)

    t1 = threading.Thread(target=call, args=("A",))
    t2 = threading.Thread(target=call, args=("B",))
    t1.start()
    time.sleep(0.02)
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    assert "A" in results and "B" in results
    assert results["A"]["job_id"] == results["B"]["job_id"]
    assert results["A"]["job_id"] != first["job_id"]
    assert results["A"]["outcome"] == results["B"]["outcome"] == COMPLETE

    with coordinator._jobs_db() as conn:
        rows = conn.execute(
            "SELECT job_id, generation FROM erasure_jobs WHERE fact_id = ? ORDER BY generation",
            (fact_id,),
        ).fetchall()
    assert len(rows) == 2, f"expected exactly 2 generations, got {len(rows)}"
    assert rows[1]["generation"] == 2
    assert rows[1]["job_id"] == results["A"]["job_id"]
    assert store.get_fact(fact_id) is None
    assert embeddings.has_any(fact_id) is False
    assert ngram.contains(fact_id) is False


def test_production_wiring_cleans_the_server_registered_ngram_instance(tmp_path, monkeypatch):
    """P1-C regression: ErasureCoordinator(), constructed the PRODUCTION way
    (no explicit ngram_index=), must clean the SAME NGramIndex instance the
    running server registered via set_global_ngram() — not a second,
    independently-defaulted instance pointing at a different SQLite file.

    core.ngram_index and core.erasure_coordinator are resolved dynamically
    via importlib here, rather than via this file's top-level imports:
    other test modules in this suite (e.g. test_server_integration.py)
    delete and re-import `core.*` modules mid-session to get a clean
    server startup, which would otherwise leave this test comparing a
    stale generation's ErasureCoordinator class against the current
    generation's global ngram instance — a test-isolation hazard, not a
    product bug, but one this test must not be sensitive to.
    """
    import importlib

    ngram_mod = importlib.import_module("core.ngram_index")
    ec_mod = importlib.import_module("core.erasure_coordinator")

    server_ngram = ngram_mod.NGramIndex(str(tmp_path / "server_ngram.db"))
    ngram_mod.set_global_ngram(server_ngram)
    try:
        assert ngram_mod.get_global_ngram() is server_ngram

        store = make_store(str(tmp_path / "facts.db"))
        fact_id = "prod_wiring_fact"
        store.store_fact(_fact(fact_id, claim="the quick brown fox"))
        server_ngram.index(fact_id, "the quick brown fox")
        assert server_ngram.contains(fact_id) is True

        # Production construction: no explicit ngram_index kwarg.
        coordinator = ec_mod.ErasureCoordinator(store=store)
        assert coordinator._ngram is server_ngram
        assert coordinator._ngram.db_path == server_ngram.db_path

        report = coordinator.erase_fact_durable(fact_id)
        assert report["outcome"] == ec_mod.COMPLETE
        assert server_ngram.contains(fact_id) is False
    finally:
        # Restore the module's own default global instance so this test
        # cannot leak state into any test that runs after it.
        ngram_mod.set_global_ngram(ngram_mod.NGramIndex())


def test_embeddings_backend_unavailable_does_not_claim_false_complete(rig, monkeypatch):
    """P2 corollary: if the optional embeddings backend cannot be reached at
    all (e.g. numpy/embedding_store unavailable in a base/server install),
    that must surface as an honest PARTIAL/FAILED outcome for the
    `embeddings` step — never as `applicable=false` silently folded into a
    false COMPLETE. fact_id genuinely HAS an embeddings row here (state B
    — see Codex review fix 5): mere table existence is not the signal,
    a row for THIS fact_id is."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "embeddings_unavailable_fact"
    store.store_fact(_fact(fact_id))
    embeddings.store(fact_id, np.array([0.1, 0.2, 0.3], dtype=np.float32), model_name="test-model")

    def _broken_get_embeddings():
        raise ImportError("embeddings backend unavailable (numpy not installed)")

    monkeypatch.setattr(coordinator, "_get_embeddings", _broken_get_embeddings)

    report = coordinator.erase_fact_durable(fact_id)

    assert report["outcome"] != COMPLETE
    assert report["outcome"] == PARTIAL
    assert report["steps"]["embeddings"]["status"] == FAILED
    assert coordinator.is_erased(fact_id) is False


# ── Security review round 2: job-scoped tombstone corroboration ────────────

def test_stale_generation_tombstone_does_not_corroborate_newer_generation(rig):
    """A generation's COMPLETE outcome must only be corroborated by ITS OWN
    tombstone — never an earlier generation's tombstone for the same
    fact_id. Simulates generation 2's own tombstone write being lost (e.g.
    a crash between write_tombstone() and the job-status COMPLETE update)
    while generation 1's real tombstone still exists: get_job_report() and
    is_erased() must not silently borrow generation 1's tombstone and
    report generation 2 as corroborated when it isn't."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "stale_tombstone_fact"

    _seed_all_layers(store, embeddings, ngram, fact_id, "gen1 data")
    gen1 = coordinator.erase_fact_durable(fact_id, reason="test", actor="A")
    assert gen1["outcome"] == COMPLETE

    _seed_all_layers(store, embeddings, ngram, fact_id, "gen2 data")
    gen2 = coordinator.erase_fact_durable(fact_id, reason="test", actor="B")
    assert gen2["outcome"] == COMPLETE
    assert gen2["job_id"] != gen1["job_id"]

    # Simulate generation 2's own tombstone having been lost/corrupted —
    # generation 1's tombstone is untouched.
    with coordinator._jobs_db() as conn:
        deleted = conn.execute(
            "DELETE FROM erasure_log WHERE fact_id = ? AND job_id = ?",
            (fact_id, gen2["job_id"]),
        ).rowcount
    assert deleted == 1
    assert store.get_tombstone(fact_id) is not None  # gen1's tombstone remains

    report = coordinator.get_job_report(fact_id)
    assert report["job_id"] == gen2["job_id"]
    assert report["content_hash"] is None
    assert report["erased_at"] is None

    assert coordinator.is_erased(fact_id) is False


def test_pre_014_generation_1_tombstone_with_null_job_id_still_honored(rig):
    """Compatibility: a durable job that reached COMPLETE before migration
    014 introduced job-scoped tombstones recorded its own completion
    tombstone with job_id=NULL. Since migration 014 backfills generation=1
    for every pre-existing job, a job_id=NULL tombstone is a valid
    corroboration for generation 1 specifically — this must keep working,
    it is not the same as the P1-A bug (an arbitrary legacy tombstone with
    NO corroborating durable job at all)."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "pre014_compat_fact"

    _seed_all_layers(store, embeddings, ngram, fact_id, "pre014 data")
    gen1 = coordinator.erase_fact_durable(fact_id, reason="test", actor="A")
    assert gen1["outcome"] == COMPLETE

    with coordinator._jobs_db() as conn:
        conn.execute(
            "UPDATE erasure_log SET job_id = NULL WHERE fact_id = ? AND job_id = ?",
            (fact_id, gen1["job_id"]),
        )
        conn.commit()

    assert coordinator.is_erased(fact_id) is True
    report = coordinator.get_job_report(fact_id)
    assert report["outcome"] == COMPLETE
    assert report["content_hash"] is not None

    again = coordinator.erase_fact_durable(fact_id, reason="test", actor="B")
    assert again["outcome"] == COMPLETE
    assert again["erased_now"] is False
    assert again["job_id"] == gen1["job_id"]


def test_concurrent_write_tombstone_for_same_job_id_leaves_exactly_one_row():
    """Security review round 2, risk 2: write_tombstone()'s SELECT-then-
    INSERT idempotency check is not atomic across connections — two
    concurrent callers finalizing the SAME job_id (e.g. a live
    erase_fact_durable() racing resume_incomplete_jobs()'s crash-recovery
    sweep) could both pass the existence check before either commits. A
    real DB-level constraint (idx_erasure_job_unique, a partial UNIQUE
    index on erasure_log(job_id) WHERE job_id IS NOT NULL) is the actual
    source of truth, and write_tombstone() must swallow the resulting
    IntegrityError as "someone else already wrote it" rather than let it
    surface — exactly one row must exist afterward, from either caller's
    perspective, and neither call may raise."""
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "facts.db")

    store_a = make_store(db_path)
    store_b = make_store(db_path)
    # Pre-warm both connections so each instance's own DDL bootstrap runs
    # BEFORE the race below — otherwise an unrelated bootstrap-DDL race
    # (two instances initializing the same fresh file for the first time)
    # could mask the actual thing under test.
    store_a.get_fact("__warm__")
    store_b.get_fact("__warm__")

    fact_id = "race_tombstone_fact"
    job_id = "erj_shared_race_job"

    barrier = threading.Barrier(2)

    def synced_release(orig):
        def _inner():
            orig()
            barrier.wait(timeout=5)
        return _inner

    store_a._release_stray_locks = synced_release(store_a._release_stray_locks)
    store_b._release_stray_locks = synced_release(store_b._release_stray_locks)

    errors: dict[str, Exception] = {}

    def call(store, name):
        try:
            store.write_tombstone(
                fact_id, reason="test", actor=name, content_hash="deadbeef", job_id=job_id
            )
        except Exception as e:  # noqa: BLE001
            errors[name] = e

    t1 = threading.Thread(target=call, args=(store_a, "A"))
    t2 = threading.Thread(target=call, args=(store_b, "B"))
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    assert errors == {}, f"write_tombstone() must never raise on a lost race: {errors}"

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT erasure_id FROM erasure_log WHERE job_id = ?", (job_id,)
        ).fetchall()
    assert len(rows) == 1, f"expected exactly 1 tombstone row for job_id, got {len(rows)}"

    # Both stores must read back the SAME proven receipt.
    receipt_a = store_a.get_tombstone_for_job(fact_id, job_id)
    receipt_b = store_b.get_tombstone_for_job(fact_id, job_id)
    assert receipt_a is not None and receipt_b is not None
    assert receipt_a["erasure_id"] == receipt_b["erasure_id"] == rows[0][0]


# ── Security review round 2: embeddings tri-state honesty (risk 3) ─────────

def test_embeddings_store_genuinely_absent_reaches_honest_complete(rig, monkeypatch):
    """State A: the embeddings feature has never been used in this
    deployment (no DB file at all — provable via stdlib sqlite3, no numpy
    needed). Even if the real backend can't be constructed (numpy
    unavailable), there is nothing for this step to possibly need to clean
    up, so an honest COMPLETE with a PROVEN applicable=False is correct —
    not a silent guess, and not a false PARTIAL/FAILED either."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "state_a_fact"
    store.store_fact(_fact(fact_id))

    # Simulate "no embedding_store was ever injected and numpy is missing":
    # force _get_embeddings() to fail, and point the existence check at a
    # path that genuinely has no file.
    missing_path = os.path.join(tempfile.mkdtemp(), "never_used_embeddings.db")
    monkeypatch.setattr(coordinator, "_resolve_embeddings_db_path", lambda: missing_path)
    monkeypatch.setattr(
        coordinator, "_get_embeddings",
        lambda: (_ for _ in ()).throw(ModuleNotFoundError("No module named 'numpy'")),
    )

    assert not os.path.exists(missing_path)

    report = coordinator.erase_fact_durable(fact_id)

    assert report["outcome"] == COMPLETE
    assert report["steps"]["embeddings"]["status"] == COMPLETE
    assert report["steps"]["embeddings"]["detail"]["applicable"] is False
    assert coordinator.is_erased(fact_id) is True


def _make_gs_vectors_db(path, rows=()):
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE gs_vectors (
            node_id TEXT NOT NULL, model_name TEXT NOT NULL,
            embedding_blob BLOB NOT NULL, dims INTEGER NOT NULL,
            computed_at REAL NOT NULL, content_hash TEXT,
            PRIMARY KEY (node_id, model_name)
        )
    """)
    for node_id in rows:
        conn.execute(
            "INSERT INTO gs_vectors (node_id, model_name, embedding_blob, dims, computed_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (node_id, "default", b"\x00\x00\x80?", 1, 0.0),
        )
    conn.commit()
    conn.close()


def _break_embeddings(coordinator, monkeypatch, db_path, exc_message="No module named 'numpy'"):
    monkeypatch.setattr(coordinator, "_resolve_embeddings_db_path", lambda: db_path)
    monkeypatch.setattr(
        coordinator, "_get_embeddings",
        lambda: (_ for _ in ()).throw(ModuleNotFoundError(exc_message)),
    )


def test_embeddings_gs_vectors_table_empty_is_honest_complete(rig, monkeypatch):
    """Codex review fix 5, state: gs_vectors table exists but has NO rows
    at all — an empty table is not proof of use for ANY fact_id, must
    reach a proven COMPLETE/applicable=false."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "empty_gs_vectors_fact"
    store.store_fact(_fact(fact_id))

    db_path = os.path.join(tempfile.mkdtemp(), "empty.db")
    _make_gs_vectors_db(db_path, rows=())
    _break_embeddings(coordinator, monkeypatch, db_path)

    report = coordinator.erase_fact_durable(fact_id)
    assert report["outcome"] == COMPLETE
    assert report["steps"]["embeddings"]["detail"]["applicable"] is False


def test_embeddings_gs_vectors_only_has_other_fact_id_is_honest_complete(rig, monkeypatch):
    """Codex review fix 5, state: gs_vectors table exists with rows, but
    NONE for this fact_id — mere table existence must never be treated as
    proof of use for a DIFFERENT fact_id; must still reach a proven
    COMPLETE/applicable=false for this one."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "state_b_fact"
    store.store_fact(_fact(fact_id))

    db_path = os.path.join(tempfile.mkdtemp(), "used_embeddings.db")
    _make_gs_vectors_db(db_path, rows=("some_other_fact",))
    _break_embeddings(coordinator, monkeypatch, db_path)

    report = coordinator.erase_fact_durable(fact_id)
    assert report["outcome"] == COMPLETE
    assert report["steps"]["embeddings"]["detail"]["applicable"] is False


def test_embeddings_target_fact_id_row_present_without_numpy_is_not_complete(rig, monkeypatch):
    """Codex review fix 5, state: a row for THIS fact_id exists, but the
    real backend can't be reached (numpy unavailable) — must surface as
    an honest FAILED/PARTIAL, never a false COMPLETE."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "target_row_present_fact"
    store.store_fact(_fact(fact_id))

    db_path = os.path.join(tempfile.mkdtemp(), "used_embeddings.db")
    _make_gs_vectors_db(db_path, rows=(fact_id, "some_other_fact"))
    _break_embeddings(coordinator, monkeypatch, db_path)

    report = coordinator.erase_fact_durable(fact_id)
    assert report["outcome"] != COMPLETE
    assert report["outcome"] == PARTIAL
    assert report["steps"]["embeddings"]["status"] == FAILED
    assert coordinator.is_erased(fact_id) is False


def test_embeddings_target_present_with_backend_available_purges_normally(rig):
    """Codex review fix 5, state: backend available — the normal
    purge_node() + has_any() path runs unchanged."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "target_present_backend_ok_fact"
    store.store_fact(_fact(fact_id))
    embeddings.store(fact_id, np.array([0.1, 0.2, 0.3], dtype=np.float32), model_name="test-model")

    report = coordinator.erase_fact_durable(fact_id)
    assert report["outcome"] == COMPLETE
    assert report["steps"]["embeddings"]["status"] == COMPLETE
    assert embeddings.has_any(fact_id) is False


def test_embeddings_corrupted_db_fails_closed_not_complete(rig, monkeypatch):
    """Codex review fix 5, state: the embeddings DB file exists but is not
    a readable SQLite database (corrupted) — the existence/row check must
    fail CLOSED (residual might be present), never toward a false
    COMPLETE."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "corrupted_db_fact"
    store.store_fact(_fact(fact_id))

    db_path = os.path.join(tempfile.mkdtemp(), "corrupted.db")
    with open(db_path, "wb") as f:
        f.write(b"this is not a valid sqlite file, just garbage bytes")
    _break_embeddings(coordinator, monkeypatch, db_path)

    report = coordinator.erase_fact_durable(fact_id)
    assert report["outcome"] != COMPLETE
    assert coordinator.is_erased(fact_id) is False


# ── Security review round 2: post-winner recreation race (risk 4) ──────────

def test_get_or_create_job_reopens_generation_when_winner_is_stale(rig):
    """A loser's IntegrityError recovery (_get_or_create_job()) may find a
    winner row that has ALREADY reached a terminal outcome — by the time
    the loser rolls back its own failed INSERT and runs its recovery
    SELECT, a fast saga on a small DB can easily have finished end-to-end.
    If fact_id was recreated AGAIN in that same window (a third actor
    re-ingesting under the same ID before the loser's recovery runs),
    blindly adopting the winner's stale-COMPLETE job_id would let
    _run_job()/_finalize() short-circuit through already-COMPLETE steps
    and return a COMPLETE report while the newly-recreated data sits
    completely unerased. The recovery path must re-check residual data and
    open the NEXT generation instead.

    Deterministic reproduction (no thread timing): capture a stale
    pre-race snapshot, directly insert an ALREADY-COMPLETE "winner" row at
    the generation the stale snapshot would compute next, recreate data
    under fact_id, then force _get_or_create_job() to compute its
    candidate generation from the stale snapshot — this reliably drives it
    into the exact IntegrityError-recovery-finds-a-terminal-winner branch
    under test, without depending on real wall-clock races."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "risk4_fact"

    _seed_all_layers(store, embeddings, ngram, fact_id, "gen1 data")
    gen1 = coordinator.erase_fact_durable(fact_id, reason="test", actor="setup")
    assert gen1["outcome"] == COMPLETE

    stale_existing = coordinator._peek_job_row(fact_id)
    assert stale_existing["job_id"] == gen1["job_id"]

    # Directly insert an ALREADY-COMPLETE "winner" gen2 row + steps,
    # bypassing the normal saga machinery — simulates a concurrent winner
    # that already finished this generation by the time our loser's
    # recovery SELECT runs.
    winner_job_id = "erj_winner_gen2_test"
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with coordinator._jobs_db() as conn:
        conn.execute(
            "INSERT INTO erasure_jobs (job_id, fact_id, generation, reason, actor, status, "
            "residual, content_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (winner_job_id, fact_id, 2, "test", "winner", COMPLETE, "none", "somehash", now, now),
        )
        for step_name in ("determine_raw", "l1_same_db", "embeddings", "ngram"):
            conn.execute(
                "INSERT INTO erasure_job_steps (step_id, job_id, step_name, status) "
                "VALUES (?, ?, ?, ?)",
                (f"{winner_job_id}_{step_name}", winner_job_id, step_name, COMPLETE),
            )
    store.write_tombstone(
        fact_id, reason="test", actor="winner", content_hash="somehash", job_id=winner_job_id
    )

    # Recreate data under fact_id — the event that must NOT be left
    # unerased.
    _seed_all_layers(store, embeddings, ngram, fact_id, "gen3 data (recreated after winner)")
    assert coordinator._residual_data_present(fact_id) is True

    # Force the candidate-generation computation to use the STALE
    # pre-winner snapshot exactly once (as a real concurrent loser would
    # have read it before the winner's gen2 committed), then fall back to
    # the real implementation for any further (recursive) calls.
    orig_peek = coordinator._peek_job_row
    call_count = {"n": 0}

    def lie_once(fid):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return dict(stale_existing)
        return orig_peek(fid)

    coordinator._peek_job_row = lie_once
    try:
        result_job_id = coordinator._get_or_create_job(fact_id, "test", "loser")
    finally:
        coordinator._peek_job_row = orig_peek

    assert result_job_id != winner_job_id, (
        "must not blindly adopt a stale-COMPLETE winner when data reappeared"
    )

    with coordinator._jobs_db() as conn:
        rows = conn.execute(
            "SELECT job_id, generation, status FROM erasure_jobs WHERE fact_id = ? "
            "ORDER BY generation",
            (fact_id,),
        ).fetchall()
    assert [r["generation"] for r in rows] == [1, 2, 3]
    assert rows[2]["job_id"] == result_job_id
    assert rows[2]["status"] == PENDING

    # Running the newly-opened generation must actually clean the
    # recreated data.
    final = coordinator._run_job(result_job_id)
    assert final["outcome"] == COMPLETE
    assert store.get_fact(fact_id) is None
    assert embeddings.has_any(fact_id) is False
    assert ngram.contains(fact_id) is False


# ── Security review round 2: full checklist — misc coverage ────────────────

def test_concurrent_resume_and_live_erase_converge_safely(rig, monkeypatch):
    """resume_incomplete_jobs() (wait_if_running=False — its whole premise
    is crash recovery when no other live caller is processing the job) is
    documented as not intended to run concurrently with live traffic on
    the SAME job. Verify that if it happens anyway (a startup sweep
    overlapping a live erase_fact_durable() call for the same fact_id),
    the two converge safely: every underlying operation (delete, tombstone
    write) is idempotent, so no exception, no data corruption, no
    duplicate tombstone, and the final state is genuinely COMPLETE."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "resume_vs_live_fact"
    _seed_all_layers(store, embeddings, ngram, fact_id, "resume vs live data")

    real_purge = embeddings.purge_node
    calls = {"n": 0}

    def flaky_purge(node_id):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated failure — leaves job PARTIAL")
        return real_purge(node_id)

    monkeypatch.setattr(embeddings, "purge_node", flaky_purge)
    partial = coordinator.erase_fact_durable(fact_id)
    assert partial["outcome"] == PARTIAL
    monkeypatch.setattr(embeddings, "purge_node", real_purge)

    errors: dict[str, Exception] = {}
    results: dict[str, object] = {}

    def run_live():
        try:
            results["live"] = coordinator.erase_fact_durable(fact_id)
        except Exception as e:  # noqa: BLE001
            errors["live"] = e

    def run_resume():
        try:
            results["resume"] = coordinator.resume_incomplete_jobs()
        except Exception as e:  # noqa: BLE001
            errors["resume"] = e

    t1 = threading.Thread(target=run_live)
    t2 = threading.Thread(target=run_resume)
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    assert errors == {}, f"unexpected exceptions: {errors}"
    assert coordinator.is_erased(fact_id) is True
    assert store.get_fact(fact_id) is None
    assert embeddings.has_any(fact_id) is False
    assert ngram.contains(fact_id) is False

    with coordinator._jobs_db() as conn:
        tombstone_count = conn.execute(
            "SELECT COUNT(*) FROM erasure_log WHERE fact_id = ?", (fact_id,)
        ).fetchone()[0]
    assert tombstone_count == 1


# ── Codex review fix 1: same-DB dependents checked before NOT_FOUND ─────────

def test_orphaned_relation_triggers_saga_and_is_cleaned(migrated_rig):
    coordinator, store, embeddings, ngram = migrated_rig
    fact_id = "orphan_relation_fact"
    other_fact_id = "orphan_relation_other_fact"
    store.store_fact(_fact(other_fact_id, claim="other fact"))

    def insert_relation(conn, fid):
        conn.execute(
            "INSERT INTO relations (from_fact_id, to_fact_id, relation_type) VALUES (?, ?, ?)",
            (fid, other_fact_id, "supports"),
        )

    _orphan_fact_with_dependent(store, fact_id, insert_relation)

    assert coordinator._residual_data_present(fact_id) is True
    report = coordinator.erase_fact_durable(fact_id)
    assert report["outcome"] != NOT_FOUND

    with store._db() as conn:
        remaining = conn.execute(
            "SELECT COUNT(*) FROM relations WHERE from_fact_id = ? OR to_fact_id = ?",
            (fact_id, fact_id),
        ).fetchone()[0]
    assert remaining == 0


def test_orphaned_fact_mentions_triggers_saga_and_is_cleaned(migrated_rig):
    coordinator, store, embeddings, ngram = migrated_rig
    fact_id = "orphan_mentions_fact"

    def insert_mention(conn, fid):
        conn.execute(
            "INSERT INTO entities (entity_id, canonical_name, first_seen, last_seen) "
            "VALUES (?, ?, ?, ?)",
            ("ent_1", "Test Entity", "t0", "t0"),
        )
        conn.execute(
            "INSERT INTO fact_mentions (mention_id, fact_id, entity_id, extracted_at) "
            "VALUES (?, ?, ?, ?)",
            ("mention_1", fid, "ent_1", "t0"),
        )

    _orphan_fact_with_dependent(store, fact_id, insert_mention)

    assert coordinator._residual_data_present(fact_id) is True
    report = coordinator.erase_fact_durable(fact_id)
    assert report["outcome"] != NOT_FOUND

    with store._db() as conn:
        remaining = conn.execute(
            "SELECT COUNT(*) FROM fact_mentions WHERE fact_id = ?", (fact_id,)
        ).fetchone()[0]
    assert remaining == 0


def test_orphaned_provenance_triggers_saga_and_is_cleaned(migrated_rig):
    coordinator, store, embeddings, ngram = migrated_rig
    fact_id = "orphan_provenance_fact"

    def insert_provenance(conn, fid):
        conn.execute(
            "INSERT INTO l0_raw_memory (raw_id, original_text, content_hash, source_type) "
            "VALUES (?, ?, ?, ?)",
            ("raw_1", "original raw text", "hash_raw_1", "user_input"),
        )
        conn.execute(
            "INSERT INTO l0_fact_provenance (id, raw_id, fact_id, linked_at) "
            "VALUES (?, ?, ?, ?)",
            ("prov_1", "raw_1", fid, "t0"),
        )

    _orphan_fact_with_dependent(store, fact_id, insert_provenance)

    assert coordinator._residual_data_present(fact_id) is True
    report = coordinator.erase_fact_durable(fact_id)
    assert report["outcome"] != NOT_FOUND

    with store._db() as conn:
        remaining = conn.execute(
            "SELECT COUNT(*) FROM l0_fact_provenance WHERE fact_id = ?", (fact_id,)
        ).fetchone()[0]
    assert remaining == 0


def test_dependent_check_error_fails_closed_not_not_found(rig, monkeypatch):
    """If checking same-DB dependents itself raises, _residual_data_present()
    must fail CLOSED (residual might be present) — never silently proceed
    to NOT_FOUND."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "dependent_check_error_fact"

    def broken_check(fid):
        raise sqlite3.OperationalError("simulated disk error checking dependents")

    monkeypatch.setattr(store, "same_db_dependents_present", broken_check)

    assert coordinator._residual_data_present(fact_id) is True
    report = coordinator.erase_fact_durable(fact_id)
    assert report["outcome"] != NOT_FOUND


# ── Codex review fix 2: SUPERSEDED terminal status for stale active jobs ────

def test_legacy_partial_job_superseded_when_data_recreated(rig):
    """A P1-A legacy-tombstone job (no facts row, residual embeddings/ngram
    only) always lands PARTIAL with residual='undetermined' — all four
    steps COMPLETE, but the overall job non-terminal. If fact_id is then
    recreated, erase_fact_durable() must supersede the old job (not
    silently reuse it) and open a new generation that actually cleans the
    new data."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "legacy_partial_recreate_fact"

    embeddings.store(fact_id, np.array([0.1, 0.2, 0.3], dtype=np.float32), model_name="test-model")
    ngram.index(fact_id, "legacy residual claim")

    first = coordinator.erase_fact_durable(fact_id, reason="test", actor="A")
    assert first["outcome"] == PARTIAL
    with coordinator._jobs_db() as conn:
        first_steps = {
            r["step_name"]: r["status"] for r in conn.execute(
                "SELECT step_name, status FROM erasure_job_steps WHERE job_id = ?",
                (first["job_id"],),
            ).fetchall()
        }
    assert all(s == COMPLETE for s in first_steps.values())

    _seed_all_layers(store, embeddings, ngram, fact_id, "recreated after PARTIAL job")

    second = coordinator.erase_fact_durable(fact_id, reason="test", actor="B")

    assert second["job_id"] != first["job_id"]
    assert second["outcome"] == COMPLETE
    assert store.get_fact(fact_id) is None
    assert embeddings.has_any(fact_id) is False
    assert ngram.contains(fact_id) is False


def test_superseded_job_preserves_original_step_receipts(rig):
    """The old job's step receipts must never be rewritten when it is
    superseded — only its own status/error change. This is the historical
    audit trail; resetting steps back to PENDING would destroy it."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "superseded_preserves_receipts_fact"

    embeddings.store(fact_id, np.array([0.1, 0.2, 0.3], dtype=np.float32), model_name="test-model")
    ngram.index(fact_id, "legacy residual claim")
    first = coordinator.erase_fact_durable(fact_id, reason="test", actor="A")
    assert first["outcome"] == PARTIAL

    with coordinator._jobs_db() as conn:
        before = {
            r["step_name"]: (r["status"], r["detail"]) for r in conn.execute(
                "SELECT step_name, status, detail FROM erasure_job_steps WHERE job_id = ?",
                (first["job_id"],),
            ).fetchall()
        }

    _seed_all_layers(store, embeddings, ngram, fact_id, "recreated data")
    coordinator.erase_fact_durable(fact_id, reason="test", actor="B")

    with coordinator._jobs_db() as conn:
        after = {
            r["step_name"]: (r["status"], r["detail"]) for r in conn.execute(
                "SELECT step_name, status, detail FROM erasure_job_steps WHERE job_id = ?",
                (first["job_id"],),
            ).fetchall()
        }
        job_row = conn.execute(
            "SELECT status FROM erasure_jobs WHERE job_id = ?", (first["job_id"],)
        ).fetchone()

    assert before == after, "step receipts must be byte-for-byte unchanged after superseding"
    assert job_row["status"] == SUPERSEDED


def test_concurrent_erase_calls_on_superseded_candidate_converge_on_one_generation(rig):
    """Two threads racing erase_fact_durable() on a fact_id whose latest
    generation is a stale PARTIAL/all-steps-COMPLETE job with reappeared
    data must converge on exactly ONE new generation — never two, and
    never silently adopting the stale job."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "superseded_race_fact"

    embeddings.store(fact_id, np.array([0.1, 0.2, 0.3], dtype=np.float32), model_name="test-model")
    ngram.index(fact_id, "legacy residual claim")
    first = coordinator.erase_fact_durable(fact_id, reason="test", actor="setup")
    assert first["outcome"] == PARTIAL

    _seed_all_layers(store, embeddings, ngram, fact_id, "recreated for race")

    orig_peek = coordinator._peek_job_row

    def slow_peek(fid):
        result = orig_peek(fid)
        if result is not None and result["job_id"] == first["job_id"]:
            time.sleep(0.15)
        return result

    coordinator._peek_job_row = slow_peek

    results: dict[str, dict] = {}

    def call(name):
        results[name] = coordinator.erase_fact_durable(fact_id, reason="test", actor=name)

    t1 = threading.Thread(target=call, args=("A",))
    t2 = threading.Thread(target=call, args=("B",))
    t1.start()
    time.sleep(0.02)
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    coordinator._peek_job_row = orig_peek

    assert "A" in results and "B" in results
    assert results["A"]["job_id"] == results["B"]["job_id"]
    assert results["A"]["job_id"] != first["job_id"]
    assert results["A"]["outcome"] == results["B"]["outcome"] == COMPLETE

    with coordinator._jobs_db() as conn:
        rows = conn.execute(
            "SELECT job_id, generation, status FROM erasure_jobs WHERE fact_id = ? ORDER BY generation",
            (fact_id,),
        ).fetchall()
    assert len(rows) == 2, f"expected exactly 2 generations, got {len(rows)}"
    assert rows[0]["status"] == SUPERSEDED
    assert rows[1]["status"] == COMPLETE
    assert rows[1]["job_id"] == results["A"]["job_id"]
    assert store.get_fact(fact_id) is None
    assert embeddings.has_any(fact_id) is False
    assert ngram.contains(fact_id) is False


def test_resume_incomplete_jobs_does_not_repick_superseded_job(rig):
    """resume_incomplete_jobs() must never re-pick a SUPERSEDED job — its
    generation has already been replaced, re-running it would just
    recompute the identical stale outcome forever."""
    coordinator, store, embeddings, ngram = rig
    fact_id = "resume_skips_superseded_fact"

    embeddings.store(fact_id, np.array([0.1, 0.2, 0.3], dtype=np.float32), model_name="test-model")
    ngram.index(fact_id, "legacy residual claim")
    first = coordinator.erase_fact_durable(fact_id, reason="test", actor="A")
    assert first["outcome"] == PARTIAL

    _seed_all_layers(store, embeddings, ngram, fact_id, "recreated data")
    second = coordinator.erase_fact_durable(fact_id, reason="test", actor="B")
    assert second["outcome"] == COMPLETE

    with coordinator._jobs_db() as conn:
        status = conn.execute(
            "SELECT status FROM erasure_jobs WHERE job_id = ?", (first["job_id"],)
        ).fetchone()["status"]
    assert status == SUPERSEDED

    resumed = coordinator.resume_incomplete_jobs()
    assert first["job_id"] not in [r["job_id"] for r in resumed]


# ── Codex review fix 4: atomic runtime index swap in _ensure_schema() ───────

def test_ensure_schema_rolls_back_fully_on_index_creation_failure(tmp_path, monkeypatch):
    """A legacy (pre-014) DB has erasure_jobs with the OLD, unconditional
    idx_erasure_jobs_fact index and no `generation` column.
    ErasureCoordinator._ensure_schema() upgrades it in place (add column,
    drop the old index, create the new generation-aware ones) inside one
    explicit transaction. If index creation fails partway through, the
    WHOLE upgrade must roll back — the DB must be left exactly as it was
    (old index intact, no generation column, no new indexes), never in an
    intermediate state with neither uniqueness constraint."""
    import core.erasure_coordinator as ec_mod

    db_path = str(tmp_path / "legacy.db")
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE erasure_jobs (
            job_id TEXT PRIMARY KEY, fact_id TEXT NOT NULL,
            reason TEXT NOT NULL, actor TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            residual TEXT, content_hash TEXT, error TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE UNIQUE INDEX idx_erasure_jobs_fact ON erasure_jobs(fact_id);
        CREATE INDEX idx_erasure_jobs_status ON erasure_jobs(status);
        CREATE TABLE erasure_job_steps (
            step_id TEXT PRIMARY KEY, job_id TEXT NOT NULL,
            step_name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING',
            detail TEXT, started_at TEXT, finished_at TEXT,
            UNIQUE(job_id, step_name)
        );
    """)
    conn.commit()
    conn.close()

    broken_index_sql = ec_mod._INDEX_SQL.replace(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_jobs_fact_generation",
        "INSERT INTO this_table_does_not_exist VALUES (1);\n"
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_jobs_fact_generation",
    )
    monkeypatch.setattr(ec_mod, "_INDEX_SQL", broken_index_sql)

    store = make_store(str(tmp_path / "facts.db"))
    with pytest.raises(Exception):  # noqa: B017 — sqlite3.OperationalError, deliberately broad
        ec_mod.ErasureCoordinator(store=store, jobs_db_path=db_path)

    conn = sqlite3.connect(db_path)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(erasure_jobs)").fetchall()}
        indexes = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'erasure_jobs'"
            ).fetchall()
        }
    finally:
        conn.close()

    assert "generation" not in cols, "ALTER TABLE must have been rolled back too"
    assert "idx_erasure_jobs_fact" in indexes, "old index must survive a failed upgrade"
    assert "idx_erasure_jobs_fact_active" not in indexes
    assert "idx_erasure_jobs_fact_generation" not in indexes
