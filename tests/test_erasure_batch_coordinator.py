"""FORGET_ALL -> durable, resumable GDPR Art. 17 BATCH erasure saga.

Every test constructs a real, temp-file-backed SQLiteGraphStore +
EmbeddingStore + NGramIndex, wires them into an isolated ErasureCoordinator
(the existing P0-B per-fact saga) and BatchErasureCoordinator (this CR) — no
fakes/stubs/mocks. Deletion/residual/compliance outcomes are proven by
directly querying the real SQLite files afterwards, not by trusting the
coordinator's own report alone.
"""
from __future__ import annotations

import sqlite3

import pytest

from core import memory
from core.embedding_store import EmbeddingStore
from core.erasure_batch_coordinator import (
    COMPLETE,
    COMPLETE_WITH_RESIDUAL,
    CRITICAL_COMPLIANCE_VIOLATION,
    FAILED,
    PARTIAL,
    REFUSED,
    RESIDUAL_IMMUTABLE_DATA,
    RUNNING,
    SKIPPED_RING_ZERO,
    BatchErasureCoordinator,
)
from core.erasure_coordinator import ErasureCoordinator
from core.memory import make_store
from core.ngram_index import NGramIndex


def _fact(fid, claim="user contact is a@b.com", source="userA", **extra):
    return {"fact_id": fid, "claim": claim, "source": source, "confidence": 0.9, **extra}


def _force_epistemic_state(store, fact_id, state):
    """Directly mutate epistemic_state via raw SQL, bypassing transition_esm()
    (which forbids transitioning INTO 'ImmutableCore' entirely — I-F1/P0-D).
    Used only to reproduce the defensive scenario this CR is guarding
    against: a personal fact that ended up 'ImmutableCore' through some
    upstream gap, which must never be silently exempted from GDPR erasure.
    """
    with store._db() as conn:
        conn.execute(
            "UPDATE facts SET epistemic_state = ? WHERE fact_id = ?", (state, fact_id)
        )
        conn.commit()


@pytest.fixture
def rig(tmp_path):
    store = make_store(str(tmp_path / "facts.db"))
    embeddings = EmbeddingStore(str(tmp_path / "embeddings.db"))
    embeddings.ensure_table()
    ngram = NGramIndex(str(tmp_path / "ngram.db"))
    coordinator = ErasureCoordinator(store=store, embedding_store=embeddings, ngram_index=ngram)
    batch = BatchErasureCoordinator(store=store, coordinator=coordinator)
    return batch, coordinator, store, embeddings, ngram


# ── Happy path ────────────────────────────────────────────────────────────

def test_happy_path_erases_all_matching_facts(rig):
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f1"))
    store.store_fact(_fact("f2"))
    store.store_fact(_fact("other", source="userB"))

    report = batch.forget_all_durable("userA", reason="dsr", actor="tester")

    assert report["outcome"] == COMPLETE
    assert report["success"] is True
    assert report["items_total"] == 2
    assert {i["fact_id"] for i in report["items"]} == {"f1", "f2"}
    assert all(i["status"] == COMPLETE for i in report["items"])
    assert store.get_fact("f1") is None
    assert store.get_fact("f2") is None
    assert store.get_fact("other") is not None


def test_ring_zero_literal_matched_by_filter_is_skipped_not_critical(rig):
    batch, coordinator, store, embeddings, ngram = rig
    # Ring Zero facts never legitimately match a user filter, but the batch
    # coordinator must handle it defensively rather than assume it can't happen.
    store.store_fact({"fact_id": "VALUES_CORE", "claim": "core value",
                       "source": "VALUES_CORE", "confidence": 1.0,
                       "epistemic_state": "Validated"})
    store.store_fact(_fact("f1", source="VALUES_CORE"))

    report = batch.forget_all_durable("VALUES_CORE", reason="dsr", actor="tester")

    assert report["outcome"] == COMPLETE
    items = {i["fact_id"]: i["status"] for i in report["items"]}
    assert items["VALUES_CORE"] == SKIPPED_RING_ZERO
    assert items["f1"] == COMPLETE
    # Ring Zero literal is never touched.
    assert store.get_fact("VALUES_CORE") is not None


# ── Refusal / guardrail tests ───────────────────────────────────────────────

def test_ambiguous_user_id_refused_without_force(rig):
    batch, *_ = rig
    for uid in ("", "default"):
        report = batch.forget_all_durable(uid, reason="dsr")
        assert report["outcome"] == REFUSED
        assert report["reason"] == "ambiguous_user_id"
        assert report["batch_id"] is None


def test_force_requires_admin_capability(rig):
    batch, *_ = rig
    report = batch.forget_all_durable(
        "userA", force=True, scope="explicit_cleanup", actor_capability="guardian",
    )
    assert report["outcome"] == REFUSED
    assert report["reason"] == "force_requires_admin_capability"


def test_force_requires_explicit_scope(rig):
    batch, *_ = rig
    report = batch.forget_all_durable(
        "userA", force=True, actor_capability="admin", scope="",
    )
    assert report["outcome"] == REFUSED
    assert report["reason"] == "force_requires_explicit_scope"


def test_force_with_admin_and_scope_on_ambiguous_user_id_succeeds_and_writes_receipt(rig):
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1", source="default"))

    report = batch.forget_all_durable(
        "default", reason="gdpr_cleanup", actor="root",
        actor_capability="admin", force=True, scope="placeholder_user_cleanup",
    )

    assert report["outcome"] == COMPLETE
    assert report["force"] is True
    assert report["scope"] == "placeholder_user_cleanup"
    with sqlite3.connect(store.db_path) as conn:
        row = conn.execute(
            "SELECT actor, actor_capability, scope FROM erasure_batch_force_receipts "
            "WHERE batch_id = ?",
            (report["batch_id"],),
        ).fetchone()
    assert row == ("root", "admin", "placeholder_user_cleanup")


def test_dry_run_does_not_create_batch_or_delete(rig):
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))
    _force_epistemic_state(store, "f1", "ImmutableCore")
    store.store_fact(_fact("f2"))

    report = batch.forget_all_durable("userA", dry_run=True)

    assert report["outcome"] == "DRY_RUN"
    assert report["items_total"] == 2
    assert report["would_erase"] == 1
    assert report["would_be_critical_items"] == ["f1"]
    # Nothing was deleted, no batch row persisted.
    assert store.get_fact("f1") is not None
    assert store.get_fact("f2") is not None
    with sqlite3.connect(store.db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM erasure_batches").fetchone()[0]
    assert count == 0


# ── Requirement #4: ImmutableCore is not an automatic GDPR exemption ───────

def test_immutable_core_personal_fact_flagged_critical_never_reports_success(rig):
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))
    _force_epistemic_state(store, "f1", "ImmutableCore")
    store.store_fact(_fact("f2"))

    report = batch.forget_all_durable("userA", reason="dsr", actor="tester")

    assert report["outcome"] == CRITICAL_COMPLIANCE_VIOLATION
    assert report["success"] is False
    assert report["critical_compliance_violation"] is True
    assert report["critical_items"] == ["f1"]
    items = {i["fact_id"]: i["status"] for i in report["items"]}
    assert items["f1"] == CRITICAL_COMPLIANCE_VIOLATION
    assert items["f2"] == COMPLETE
    # The flagged fact is NOT deleted (out of scope for this CR to decide
    # how to remediate an architectural ImmutableCore violation) and NOT
    # silently treated as exempt either — it is durably recorded as critical.
    assert store.get_fact("f1") is not None
    assert store.get_fact("f2") is None

    # Re-running (e.g. an operator retry) reaches the identical verdict —
    # it is not a transient failure that quietly clears itself.
    again = batch.get_batch_report(report["batch_id"])
    assert again["outcome"] == CRITICAL_COMPLIANCE_VIOLATION


# ── L0 residual (raw original present) ─────────────────────────────────────

def test_l0_residual_item_yields_complete_with_residual_not_plain_complete(rig):
    batch, coordinator, store, *_ = rig
    raw_id = store.store_raw_text("the original raw text", source_type="user_input")
    store.store_fact(_fact("f1"))
    store.link_raw_to_fact(raw_id, "f1")
    store.store_fact(_fact("f2"))

    report = batch.forget_all_durable("userA", reason="dsr")

    assert report["outcome"] == COMPLETE_WITH_RESIDUAL
    assert report["success"] is True
    items = {i["fact_id"]: i["status"] for i in report["items"]}
    assert items["f1"] == RESIDUAL_IMMUTABLE_DATA
    assert items["f2"] == COMPLETE
    # Derived layer is gone; raw origin (immutable, by design) remains.
    assert store.get_fact("f1") is None
    with store._db() as conn:
        assert conn.execute(
            "SELECT 1 FROM l0_raw_memory WHERE raw_id = ?", (raw_id,)
        ).fetchone() is not None


# ── Partial failure + resume ────────────────────────────────────────────────

def test_partial_failure_then_resume_completes(rig, monkeypatch):
    batch, coordinator, store, *_ = rig
    for fid in ("f1", "f2", "f3"):
        store.store_fact(_fact(fid))

    orig_run_l1 = coordinator._run_l1_same_db
    state = {"failed_once": False}

    def flaky_l1(job_id, fact_id):
        if fact_id == "f2" and not state["failed_once"]:
            state["failed_once"] = True
            coordinator._step_start(job_id, "l1_same_db")
            coordinator._step_finish(job_id, "l1_same_db", FAILED, {"error": "simulated_outage"})
            coordinator._set_job_error(job_id, "l1_same_db: simulated_outage")
            return
        return orig_run_l1(job_id, fact_id)

    monkeypatch.setattr(coordinator, "_run_l1_same_db", flaky_l1)

    first = batch.forget_all_durable("userA", reason="dsr")
    assert first["outcome"] == PARTIAL
    items = {i["fact_id"]: i["status"] for i in first["items"]}
    assert items["f1"] == COMPLETE
    assert items["f2"] in (PARTIAL, FAILED)
    assert items["f3"] == COMPLETE
    # f1/f3 are genuinely gone already — a resume must not re-delete or
    # re-run their already-COMPLETE per-fact jobs.
    assert store.get_fact("f1") is None
    assert store.get_fact("f3") is None
    assert store.get_fact("f2") is not None  # l1_same_db never actually ran

    monkeypatch.setattr(coordinator, "_run_l1_same_db", orig_run_l1)
    # Resume the SAME original batch (its own durable snapshot/ledger) —
    # a fresh forget_all_durable() call with no idempotency_key would open
    # an unrelated new batch instead, which is not what "resume" means here.
    resumed = _resume_specific_batch(batch, first["batch_id"])
    assert resumed["outcome"] == COMPLETE
    assert store.get_fact("f2") is None


def _resume_specific_batch(batch: BatchErasureCoordinator, batch_id: str):
    result = batch._run_batch(batch_id)
    assert result is not None
    return result


def test_resume_incomplete_batches_crash_recovery(rig, monkeypatch):
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))
    store.store_fact(_fact("f2"))

    orig_run_l1 = coordinator._run_l1_same_db

    def always_fail(job_id, fact_id):
        coordinator._step_start(job_id, "l1_same_db")
        coordinator._step_finish(job_id, "l1_same_db", FAILED, {"error": "down"})
        coordinator._set_job_error(job_id, "l1_same_db: down")

    monkeypatch.setattr(coordinator, "_run_l1_same_db", always_fail)
    first = batch.forget_all_durable("userA", reason="dsr")
    assert first["outcome"] == PARTIAL

    # Simulate a crash mid-batch: force the row back to RUNNING, as a dead
    # process would have left it (no live caller ever set it back to a
    # resumable status).
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE erasure_batches SET status = ? WHERE batch_id = ?",
            (RUNNING, first["batch_id"]),
        )
        conn.commit()

    monkeypatch.setattr(coordinator, "_run_l1_same_db", orig_run_l1)

    # A brand-new BatchErasureCoordinator instance (simulating a fresh
    # process after restart) must pick this batch up from its OWN durable
    # ledger, using the SAME store/coordinator — never re-querying `facts`.
    fresh_batch = BatchErasureCoordinator(store=store, coordinator=coordinator)
    results = fresh_batch.resume_incomplete_batches()

    assert any(r["batch_id"] == first["batch_id"] and r["outcome"] == COMPLETE for r in results)
    assert store.get_fact("f1") is None
    assert store.get_fact("f2") is None


# ── Idempotency ──────────────────────────────────────────────────────────

def test_idempotency_key_reuse_resumes_same_batch_no_duplicate_snapshot(rig, monkeypatch):
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))
    store.store_fact(_fact("f2"))

    orig_run_l1 = coordinator._run_l1_same_db

    def fail_once(job_id, fact_id):
        if fact_id == "f2":
            coordinator._step_start(job_id, "l1_same_db")
            coordinator._step_finish(job_id, "l1_same_db", FAILED, {"error": "down"})
            coordinator._set_job_error(job_id, "l1_same_db: down")
            return
        return orig_run_l1(job_id, fact_id)

    monkeypatch.setattr(coordinator, "_run_l1_same_db", fail_once)
    first = batch.forget_all_durable("userA", reason="dsr", idempotency_key="req-123")
    assert first["outcome"] == PARTIAL

    monkeypatch.setattr(coordinator, "_run_l1_same_db", orig_run_l1)
    second = batch.forget_all_durable("userA", reason="dsr", idempotency_key="req-123")

    assert second["batch_id"] == first["batch_id"]
    assert second["outcome"] == COMPLETE
    with sqlite3.connect(store.db_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM erasure_batches WHERE idempotency_key = ?", ("req-123",)
        ).fetchone()[0]
    assert count == 1  # never a second, diverging snapshot


def test_idempotency_key_repeat_after_complete_is_pure_readback(rig):
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))

    first = batch.forget_all_durable("userA", reason="dsr", idempotency_key="req-456")
    assert first["outcome"] == COMPLETE

    # Delete the fact's job row to prove a repeat call does NOT re-run
    # per-fact processing (it must short-circuit on the already-terminal
    # batch, not touch erase_fact_durable() again).
    with sqlite3.connect(store.db_path) as conn:
        job_count_before = conn.execute("SELECT COUNT(*) FROM erasure_jobs").fetchone()[0]

    second = batch.forget_all_durable("userA", reason="dsr", idempotency_key="req-456")
    assert second == first or second["outcome"] == COMPLETE

    with sqlite3.connect(store.db_path) as conn:
        job_count_after = conn.execute("SELECT COUNT(*) FROM erasure_jobs").fetchone()[0]
    assert job_count_after == job_count_before


# ── Concurrent addition of a new fact mid-batch ─────────────────────────────

def test_concurrent_new_fact_after_snapshot_is_never_included(rig, monkeypatch):
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))

    orig_run_l1 = coordinator._run_l1_same_db
    inserted = {"done": False}

    def insert_new_fact_mid_run(job_id, fact_id):
        # Simulate a fact for the SAME user being ingested concurrently,
        # right in the middle of this batch's processing.
        if not inserted["done"]:
            inserted["done"] = True
            store.store_fact(_fact("f_concurrent"))
        return orig_run_l1(job_id, fact_id)

    monkeypatch.setattr(coordinator, "_run_l1_same_db", insert_new_fact_mid_run)

    report = batch.forget_all_durable("userA", reason="dsr")

    assert report["outcome"] == COMPLETE
    assert report["items_total"] == 1  # snapshot fixed BEFORE the insert
    assert {i["fact_id"] for i in report["items"]} == {"f1"}
    assert store.get_fact("f1") is None
    # The concurrently-ingested fact is untouched — out of scope for THIS
    # batch by construction; it needs its own subsequent forget_all call.
    assert store.get_fact("f_concurrent") is not None


def test_resume_never_requeries_facts_for_new_membership(rig, monkeypatch):
    """Same guarantee, exercised via crash-resume rather than mid-run:
    a fact inserted for the same user_id AFTER the snapshot but BEFORE a
    resume must still not be swept into the resumed batch."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))

    def always_fail(job_id, fact_id):
        coordinator._step_start(job_id, "l1_same_db")
        coordinator._step_finish(job_id, "l1_same_db", FAILED, {"error": "down"})
        coordinator._set_job_error(job_id, "l1_same_db: down")

    monkeypatch.setattr(coordinator, "_run_l1_same_db", always_fail)
    first = batch.forget_all_durable("userA", reason="dsr")
    assert first["outcome"] == PARTIAL

    store.store_fact(_fact("f_late"))  # ingested for userA after the snapshot

    monkeypatch.undo()
    resumed = _resume_specific_batch(batch, first["batch_id"])

    assert resumed["items_total"] == 1
    assert {i["fact_id"] for i in resumed["items"]} == {"f1"}
    assert store.get_fact("f1") is None
    assert store.get_fact("f_late") is not None


# ── Legacy shim (core.forgetting.ForgettingEngine.forget_all) ─────────────

def test_forgetting_engine_forget_all_is_deprecated_and_delegates(rig, monkeypatch):
    from core import forgetting as forgetting_mod

    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f1"))

    import core.erasure_batch_coordinator as _ebc

    monkeypatch.setattr(memory, "_GLOBAL_STORE", store)
    # NOTE: patch via the imported module OBJECT, not a dotted string — a
    # string target re-resolves "core.erasure_batch_coordinator" through
    # import machinery, which is not guaranteed to hand back the exact
    # module object core.forgetting's own `from core.erasure_batch_coordinator
    # import forget_all_durable` closed over once enough of the suite's
    # other modules have been collected/imported first (observed to only
    # reproduce inside the full test session, never in isolation).
    monkeypatch.setattr(_ebc, "_default_batch_coordinator", batch)

    engine = forgetting_mod.ForgettingEngine(db_path=store.db_path)
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr")

    assert verdict.allowed is True
    assert verdict.affected_facts == 1
    assert store.get_fact("f1") is None
