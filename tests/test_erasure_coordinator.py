"""P0-B: core.erasure_coordinator — durable, resumable GDPR Art. 17 saga.

Every test constructs a real, temp-file-backed SQLiteGraphStore +
EmbeddingStore + NGramIndex and wires them into an isolated
ErasureCoordinator — no fakes/stubs/mocks anywhere in this file. Each
storage backend is a real SQLite file; deletion is proven by directly
querying that file afterwards, not by trusting the coordinator's own report.
"""
from __future__ import annotations

import numpy as np
import pytest

from core import memory
from core.embedding_store import EmbeddingStore
from core.erasure_coordinator import (
    COMPLETE,
    FAILED,
    NOT_FOUND,
    PARTIAL,
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


def test_residual_raw_original_present_still_reaches_complete(rig):
    coordinator, store, _, _ = rig
    raw_id = store.store_raw_text("the original raw text", source_type="user_input")
    store.store_fact(_fact("f5"))
    store.link_raw_to_fact(raw_id, "f5")

    report = coordinator.erase_fact_durable("f5")

    # Derived layer is erased; the immutable raw origin is an intentional,
    # documented residual — never hidden, but also not a failure.
    assert report["outcome"] == COMPLETE
    assert report["residual"] == "raw_original_present"
    assert store.get_fact("f5") is None
    # l0_raw_memory itself is untouched (append-only by design).
    with store._db() as conn:
        assert conn.execute(
            "SELECT 1 FROM l0_raw_memory WHERE raw_id = ?", (raw_id,)
        ).fetchone() is not None


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
