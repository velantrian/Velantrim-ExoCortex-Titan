"""P0-B: core.erasure_coordinator — durable, resumable GDPR Art. 17 saga.

Every test constructs a real, temp-file-backed SQLiteGraphStore +
EmbeddingStore + NGramIndex and wires them into an isolated
ErasureCoordinator — no fakes/stubs/mocks anywhere in this file. Each
storage backend is a real SQLite file; deletion is proven by directly
querying that file afterwards, not by trusting the coordinator's own report.
"""
from __future__ import annotations

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
    RESIDUAL_IMMUTABLE_DATA,
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


def test_get_or_create_job_after_complete_returns_existing_job(rig):
    """A retry after COMPLETE must adopt the same job, not create a second
    one — even calling the internal method directly."""
    coordinator, store, embeddings, ngram = rig
    _seed_one(store, embeddings, ngram, "retry_complete")

    first = coordinator.erase_fact_durable("retry_complete", reason="test", actor="A")
    assert first["outcome"] == COMPLETE

    job_id_again = coordinator._get_or_create_job("retry_complete", "test", "B")
    assert job_id_again == first["job_id"]
    with coordinator._jobs_db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM erasure_jobs WHERE fact_id = ?", ("retry_complete",)
        ).fetchone()[0]
    assert count == 1


def test_get_or_create_job_after_residual_immutable_data_returns_existing_job(rig):
    """Same guarantee for the RESIDUAL_IMMUTABLE_DATA terminal outcome."""
    coordinator, store, embeddings, ngram = rig
    raw_id = store.store_raw_text("the original raw text", source_type="user_input")
    store.store_fact(_fact("retry_residual"))
    store.link_raw_to_fact(raw_id, "retry_residual")

    first = coordinator.erase_fact_durable("retry_residual", reason="test", actor="A")
    assert first["outcome"] == RESIDUAL_IMMUTABLE_DATA

    job_id_again = coordinator._get_or_create_job("retry_residual", "test", "B")
    assert job_id_again == first["job_id"]
    with coordinator._jobs_db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM erasure_jobs WHERE fact_id = ?", ("retry_residual",)
        ).fetchone()[0]
    assert count == 1
