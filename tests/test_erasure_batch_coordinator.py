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
import threading
import time

import pytest

from core import memory
from core.embedding_store import EmbeddingStore
import core.erasure_batch_coordinator as ebc_module
from core.erasure_batch_coordinator import (
    COMPLETE,
    COMPLETE_WITH_RESIDUAL,
    CRITICAL_COMPLIANCE_VIOLATION,
    FAILED,
    IDEMPOTENCY_CONFLICT,
    PARTIAL,
    PENDING,
    REFUSED,
    RESIDUAL_IMMUTABLE_DATA,
    RUNNING,
    SKIPPED_RING_ZERO,
    SUBJECT_CONFLICT,
    BatchErasureCoordinator,
)
from core.erasure_coordinator import ErasureCoordinator, _now
from core.memory import make_store
from core.ngram_index import NGramIndex
from core.tool_registry import PrincipalContext


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
    """Requirement #3/#4: EXECUTION status and COMPLIANCE status are two
    independent fields — a critical item is terminal-for-itself, so the
    batch's execution status still reaches COMPLETE (nothing retryable is
    left), but compliance_status stays CRITICAL_COMPLIANCE_VIOLATION and
    `success`/`erasure_complete` must never be True while it does."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))
    _force_epistemic_state(store, "f1", "ImmutableCore")
    store.store_fact(_fact("f2"))

    report = batch.forget_all_durable("userA", reason="dsr", actor="tester")

    assert report["outcome"] == COMPLETE
    assert report["operation_finished"] is True
    assert report["success"] is False
    assert report["erasure_complete"] is False
    assert report["compliance_status"] == CRITICAL_COMPLIANCE_VIOLATION
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
    assert again["compliance_status"] == CRITICAL_COMPLIANCE_VIOLATION
    assert again["success"] is False


def test_critical_item_alongside_partial_item_stays_resumable_then_stays_flagged(rig, monkeypatch):
    """Requirement #3: a CRITICAL compliance finding must NOT block retryable
    items from being retried — the batch stays PARTIAL (resumable) while f2
    is still failing, even though f1 is already flagged critical. Once f2
    is fixed and resumed, execution reaches COMPLETE, but compliance_status
    stays CRITICAL forever (sticky) — success is never True."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))
    _force_epistemic_state(store, "f1", "ImmutableCore")
    store.store_fact(_fact("f2"))

    orig_run_l1 = coordinator._run_l1_same_db

    def fail_f2(job_id, fact_id):
        if fact_id == "f2":
            coordinator._step_start(job_id, "l1_same_db")
            coordinator._step_finish(job_id, "l1_same_db", FAILED, {"error": "down"})
            coordinator._set_job_error(job_id, "l1_same_db: down")
            return
        return orig_run_l1(job_id, fact_id)

    monkeypatch.setattr(coordinator, "_run_l1_same_db", fail_f2)
    first = batch.forget_all_durable("userA", reason="dsr")

    assert first["outcome"] == PARTIAL  # f2 still retryable
    assert first["compliance_status"] == CRITICAL_COMPLIANCE_VIOLATION  # surfaced immediately
    assert first["success"] is False

    monkeypatch.setattr(coordinator, "_run_l1_same_db", orig_run_l1)
    resumed = _resume_specific_batch(batch, first["batch_id"])

    assert resumed["outcome"] == COMPLETE  # f2 now resolved, nothing retryable
    assert resumed["compliance_status"] == CRITICAL_COMPLIANCE_VIOLATION  # never auto-clears
    assert resumed["success"] is False
    assert store.get_fact("f1") is not None  # critical item still untouched
    assert store.get_fact("f2") is None


# ── L0 residual (raw original present) ─────────────────────────────────────

def test_l0_residual_item_yields_complete_with_residual_not_plain_complete(rig):
    """Requirement #5: COMPLETE_WITH_RESIDUAL is a real, tracked, accepted
    outcome (the derived layer IS fully erased) — but it must never be
    reported as plain success=True, since the L0 raw origin (personal data)
    is known to still exist. operation_finished is True (nothing left to
    retry); success/erasure_complete are False."""
    batch, coordinator, store, *_ = rig
    raw_id = store.store_raw_text("the original raw text", source_type="user_input")
    store.store_fact(_fact("f1"))
    store.link_raw_to_fact(raw_id, "f1")
    store.store_fact(_fact("f2"))

    report = batch.forget_all_durable("userA", reason="dsr")

    assert report["outcome"] == COMPLETE_WITH_RESIDUAL
    assert report["operation_finished"] is True
    assert report["success"] is False
    assert report["erasure_complete"] is False
    assert report["compliance_status"] is None
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

    # Simulate a crash mid-batch: force the row back to RUNNING with an
    # EXPIRED lease, as a dead process would eventually look like (no live
    # caller ever renews the lease past its TTL once the process is gone).
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE erasure_batches SET status = ?, lease_expires_at = ? "
            "WHERE batch_id = ?",
            (RUNNING, "2000-01-01T00:00:00+00:00", first["batch_id"]),
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


# ── Blocker #2: lease-based crash-recovery ownership ────────────────────────

def test_live_running_batch_with_fresh_lease_is_never_reclaimed_by_recovery(rig, monkeypatch):
    """A batch that is genuinely still RUNNING (a live runner holds a
    NOT-yet-expired lease) must be left completely alone by
    resume_incomplete_batches() — reclaiming it would let a crash-recovery
    sweep race a still-alive process's in-flight writes."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))

    def never_finishes(job_id, fact_id):
        raise AssertionError("must not be processed while lease is fresh")

    monkeypatch.setattr(coordinator, "_run_l1_same_db", never_finishes)

    # Claim it live ourselves (simulating a runner mid-flight) — do NOT
    # call forget_all_durable() (it would run to completion synchronously);
    # instead go through the real snapshot + claim primitives directly.
    batch_id = batch._create_batch_snapshot(
        user_id="userA", reason="dsr", actor="tester", force=False, scope=None,
        idempotency_key=None, actor_capability="reader",
        request_fingerprint="fp-live-test",
    )
    claimed = batch._claim_batch_for_running(
        batch_id, allow_stale_running=False, runner_id="live-runner-1",
    )
    assert claimed is True
    before = batch._load_batch(batch_id)
    assert before["status"] == RUNNING

    results = batch.resume_incomplete_batches()

    assert all(r["batch_id"] != batch_id for r in results)
    after = batch._load_batch(batch_id)
    assert after["status"] == RUNNING
    assert after["runner_id"] == "live-runner-1"
    assert store.get_fact("f1") is not None  # never touched


def test_two_recovery_workers_never_both_win_the_same_stale_lease(rig):
    """Two concurrent crash-recovery claims against the SAME stale RUNNING
    batch must not both succeed — the CAS on lease_expires_at means the
    first winner's write extends the lease, so the second (even though it
    observed the same 'stale' snapshot) loses when its own UPDATE actually
    runs against current state."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))

    batch_id = batch._create_batch_snapshot(
        user_id="userA", reason="dsr", actor="tester", force=False, scope=None,
        idempotency_key=None, actor_capability="reader",
        request_fingerprint="fp-two-workers",
    )
    # Force it into a stale-RUNNING state, as a crashed process would leave it.
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE erasure_batches SET status = ?, runner_id = ?, "
            "lease_expires_at = ? WHERE batch_id = ?",
            (RUNNING, "dead-runner", "2000-01-01T00:00:00+00:00", batch_id),
        )
        conn.commit()

    first_claim = batch._claim_batch_for_running(
        batch_id, allow_stale_running=True, runner_id="recovery-worker-A",
    )
    second_claim = batch._claim_batch_for_running(
        batch_id, allow_stale_running=True, runner_id="recovery-worker-B",
    )

    assert first_claim is True
    assert second_claim is False
    final = batch._load_batch(batch_id)
    assert final["runner_id"] == "recovery-worker-A"


def test_item_slower_than_ttl_heartbeat_prevents_reclaim(rig, monkeypatch):
    """Round-2 blocker #1: the lease used to be renewed only AFTER
    _process_item() returned, so a single item slower than
    _LEASE_TTL_SECONDS could let the batch lease go stale mid-item even
    though the runner is genuinely still alive. _BatchLeaseHeartbeat now
    renews continuously in the background for as long as items are being
    processed — a recovery sweep running concurrently, well past the TTL,
    must still find nothing to reclaim."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))

    monkeypatch.setattr(ebc_module, "_LEASE_TTL_SECONDS", 0.3)

    orig_run_l1 = coordinator._run_l1_same_db

    def slow_l1(job_id, fact_id):
        time.sleep(0.8)  # deliberately longer than the lease TTL above
        return orig_run_l1(job_id, fact_id)

    monkeypatch.setattr(coordinator, "_run_l1_same_db", slow_l1)

    result_holder = {}

    def run_live():
        result_holder["report"] = batch.forget_all_durable("userA", reason="dsr")

    t = threading.Thread(target=run_live)
    t.start()
    try:
        time.sleep(0.5)  # well past the 0.3s TTL, while f1 is still mid-sleep

        recovery_worker = BatchErasureCoordinator(store=store, coordinator=coordinator)
        recovered = recovery_worker.resume_incomplete_batches()

        assert recovered == []  # heartbeat kept the lease alive -- nothing stale
    finally:
        t.join(timeout=5.0)

    assert result_holder["report"]["outcome"] == COMPLETE
    assert store.get_fact("f1") is None


def test_heartbeat_lease_lost_stops_pass_before_next_item_even_starts(rig, monkeypatch):
    """Round-4 blocker #2 (from _run_batch's loop): once the heartbeat has
    already flagged lease_lost, the processing loop must not even ATTEMPT
    the next retryable item (no _claim_item()/erase_fact_durable() call at
    all) — checked before the DB round-trip, not only after a claim fails."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))
    store.store_fact(_fact("f2"))

    monkeypatch.setattr(ebc_module, "_LEASE_TTL_SECONDS", 0.2)
    # Simulate the lease being genuinely lost (e.g. reclaimed elsewhere)
    # the very first time the heartbeat tries to renew it.
    monkeypatch.setattr(batch, "_renew_lease", lambda batch_id, runner_id: False)

    orig_run_l1 = coordinator._run_l1_same_db
    processed = []

    def slow_first_item(job_id, fact_id):
        processed.append(fact_id)
        if fact_id == "f1":
            time.sleep(0.5)  # long enough for the heartbeat to fire and fail
        return orig_run_l1(job_id, fact_id)

    monkeypatch.setattr(coordinator, "_run_l1_same_db", slow_first_item)

    report = batch.forget_all_durable("userA", reason="dsr")

    # f1 was already mid-flight when the lease was lost, so it legitimately
    # finishes (its own DB-level ownership CAS is untouched by the mocked
    # _renew_lease) -- but f2 must NEVER have been attempted at all.
    assert "f2" not in processed
    assert report["outcome"] == RUNNING  # never finalized -- lease was lost
    items = {i["fact_id"]: i["status"] for i in report["items"]}
    assert items["f1"] == COMPLETE
    assert items["f2"] == PENDING


def test_renew_lease_raising_operational_error_fails_closed(rig, monkeypatch):
    """Round-4 blocker #2: an exception from the renewal call (e.g. a
    transient sqlite3.OperationalError) must be treated exactly like a
    confirmed lost lease — never silently ignored, never left with
    lease_lost still False. The item loop stops and finalize never runs."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))
    store.store_fact(_fact("f2"))

    monkeypatch.setattr(ebc_module, "_LEASE_TTL_SECONDS", 0.2)

    def raising_renew(batch_id, runner_id):
        raise sqlite3.OperationalError("simulated: database is locked")

    monkeypatch.setattr(batch, "_renew_lease", raising_renew)

    orig_run_l1 = coordinator._run_l1_same_db
    processed = []

    def slow_first_item(job_id, fact_id):
        processed.append(fact_id)
        if fact_id == "f1":
            time.sleep(0.5)
        return orig_run_l1(job_id, fact_id)

    monkeypatch.setattr(coordinator, "_run_l1_same_db", slow_first_item)

    report = batch.forget_all_durable("userA", reason="dsr")

    assert "f2" not in processed
    assert report["outcome"] == RUNNING  # never finalized


def test_heartbeat_stop_treats_still_alive_thread_as_lease_lost():
    """Round-4 blocker #2: if the background renewal thread hasn't
    actually stopped by the join timeout (e.g. wedged inside a slow/hung
    call), stop() can prove neither that the lease is held nor that
    lease_lost would have been set in time -- an alive thread past the
    deadline must be treated as lease lost, not optimistically trusted."""
    release = threading.Event()

    def hung_renew():
        release.wait(5.0)  # blocks well past our tiny join timeout below
        return True

    hb = ebc_module._BatchLeaseHeartbeat(
        hung_renew, interval_seconds=0.05, join_timeout_seconds=0.2,
    )
    hb.start()
    time.sleep(0.15)  # let it enter hung_renew() at least once
    try:
        held = hb.stop()
        assert held is False
        assert hb.lease_lost.is_set() is True
    finally:
        release.set()  # let the background thread finish so it doesn't leak


def test_stale_runner_a_claim_item_rejected_after_runner_b_takes_batch_and_item(rig):
    """Round-3 blocker #1: _claim_item() is itself an ownership CAS on the
    BATCH (runner_id/status/claim_generation), not an unconditional
    overwrite. Runner A claims the batch and an item, then genuinely loses
    the batch to Runner B (a crash-recovery reclaim); Runner B re-claims
    the SAME item. Runner A — still holding its OLD (now-superseded)
    claim_generation — must be REJECTED when it tries to claim ANY item
    again (even one it never touched, f2), and item_runner_id must stay B."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))
    store.store_fact(_fact("f2"))

    batch_id = batch._create_batch_snapshot(
        user_id="userA", reason="dsr", actor="tester", force=False, scope=None,
        idempotency_key=None, actor_capability="reader",
        request_fingerprint="fp-fencing-test",
    )

    claimed_a = batch._claim_batch_for_running(
        batch_id, allow_stale_running=False, runner_id="runner-A",
    )
    assert claimed_a is True
    gen_a = batch._load_batch(batch_id)["claim_generation"]
    assert batch._claim_item(batch_id, "f1", "runner-A", gen_a) is True

    # Runner A "loses" the batch: force the lease stale, then Runner B
    # (crash recovery) reclaims it — a NEW claim_generation.
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE erasure_batches SET lease_expires_at = ? WHERE batch_id = ?",
            ("2000-01-01T00:00:00+00:00", batch_id),
        )
        conn.commit()
    claimed_b = batch._claim_batch_for_running(
        batch_id, allow_stale_running=True, runner_id="runner-B",
    )
    assert claimed_b is True
    gen_b = batch._load_batch(batch_id)["claim_generation"]
    assert gen_b != gen_a
    assert batch._claim_item(batch_id, "f1", "runner-B", gen_b) is True

    # Stale Runner A -- still presenting its OLD generation token -- tries
    # to claim f1 again (already B's) and f2 (never touched by anyone).
    # Both must be rejected: A no longer owns the batch under ANY generation.
    assert batch._claim_item(batch_id, "f1", "runner-A", gen_a) is False
    assert batch._claim_item(batch_id, "f2", "runner-A", gen_a) is False

    items = {i["fact_id"]: i for i in batch._load_items(batch_id)}
    assert items["f1"]["item_runner_id"] == "runner-B"
    assert items["f2"]["item_runner_id"] is None  # never claimed by anyone

    # And a stale _set_item_status() write is rejected the same way, even
    # though item_runner_id superficially still says "runner-B" is not
    # involved here -- it's the BATCH ownership/generation check that
    # fails for A regardless.
    stale_write = batch._set_item_status(
        batch_id, "f1", COMPLETE, runner_id="runner-A", claim_generation=gen_a,
        detail={"stale": True},
    )
    assert stale_write is False
    assert batch._load_items(batch_id)[0]["status"] == PENDING

    # Runner B's own write, using its CURRENT generation, succeeds normally.
    current_write = batch._set_item_status(
        batch_id, "f1", COMPLETE, runner_id="runner-B", claim_generation=gen_b,
        detail={"stale": False},
    )
    assert current_write is True
    assert batch._load_items(batch_id)[0]["status"] == COMPLETE


def test_compliance_flag_visible_immediately_after_critical_item_before_finalize(rig):
    """Round-2 blocker #3: compliance_status must be written atomically
    WITH the critical item's own row, not deferred to _finalize_batch() —
    a crash right after that write (before finalize ever runs) must still
    leave compliance_status durably visible on the batch row, and
    _report() must also derive it directly from item rows as a fail-closed
    backstop."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))
    _force_epistemic_state(store, "f1", "ImmutableCore")

    batch_id = batch._create_batch_snapshot(
        user_id="userA", reason="dsr", actor="tester", force=False, scope=None,
        idempotency_key=None, actor_capability="reader",
        request_fingerprint="fp-crash-before-finalize",
    )
    claimed = batch._claim_batch_for_running(
        batch_id, allow_stale_running=False, runner_id="runner-crash",
    )
    assert claimed is True
    loaded_batch = batch._load_batch(batch_id)
    item = batch._load_items(batch_id)[0]

    # Exactly one item processed, then simulate a crash: _finalize_batch()
    # is never called.
    won = batch._process_item(loaded_batch, item, "runner-crash")
    assert won is True

    raw = batch._load_batch(batch_id)
    assert raw["compliance_status"] == CRITICAL_COMPLIANCE_VIOLATION
    assert raw["status"] == RUNNING  # execution status untouched -- finalize never ran

    report = batch.get_batch_report(batch_id)
    assert report["compliance_status"] == CRITICAL_COMPLIANCE_VIOLATION
    assert report["critical_compliance_violation"] is True

    # Fail-closed backstop: even if the batch column had somehow stayed
    # NULL, _report() independently scans item rows and still reports
    # critical=True.
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE erasure_batches SET compliance_status = NULL WHERE batch_id = ?",
            (batch_id,),
        )
        conn.commit()
    report_after_wipe = batch.get_batch_report(batch_id)
    assert report_after_wipe["compliance_status"] == CRITICAL_COMPLIANCE_VIOLATION
    assert report_after_wipe["critical_compliance_violation"] is True


def test_two_real_recovery_workers_separate_connections_race_exactly_one_winner(rig):
    """Round-2 required test: two GENUINELY concurrent recovery workers,
    each its own BatchErasureCoordinator instance (separate connections),
    synchronized with a barrier so they attempt the claim as close to
    simultaneously as real threads allow. Exactly one must process the
    batch to completion; the other must find nothing to do."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))

    batch_id = batch._create_batch_snapshot(
        user_id="userA", reason="dsr", actor="tester", force=False, scope=None,
        idempotency_key=None, actor_capability="reader",
        request_fingerprint="fp-real-two-workers",
    )
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE erasure_batches SET status = ?, runner_id = ?, "
            "lease_expires_at = ? WHERE batch_id = ?",
            (RUNNING, "dead-runner", "2000-01-01T00:00:00+00:00", batch_id),
        )
        conn.commit()

    worker_a = BatchErasureCoordinator(store=store, coordinator=coordinator)
    worker_b = BatchErasureCoordinator(store=store, coordinator=coordinator)
    barrier = threading.Barrier(2)
    results: dict[str, list] = {}

    def run(name, worker):
        barrier.wait(timeout=5.0)
        results[name] = worker.resume_incomplete_batches()

    t1 = threading.Thread(target=run, args=("A", worker_a))
    t2 = threading.Thread(target=run, args=("B", worker_b))
    t1.start()
    t2.start()
    t1.join(timeout=10.0)
    t2.join(timeout=10.0)

    a_won = any(r["batch_id"] == batch_id for r in results["A"])
    b_won = any(r["batch_id"] == batch_id for r in results["B"])
    assert a_won != b_won  # exactly one of the two processed it

    final = batch._load_batch(batch_id)
    assert final["status"] == COMPLETE
    assert store.get_fact("f1") is None


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


def test_same_idempotency_key_different_request_is_conflict_not_reuse(rig):
    """Blocker #1: reusing an idempotency_key with a DIFFERENT canonical
    request (here: a different user_id) must return IDEMPOTENCY_CONFLICT —
    it must never run, resume, or reveal the first request's batch."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1", source="userA"))
    store.store_fact(_fact("f2", source="userB"))

    first = batch.forget_all_durable("userA", reason="dsr", idempotency_key="shared-key")
    assert first["outcome"] == COMPLETE
    assert store.get_fact("f1") is None

    conflict = batch.forget_all_durable("userB", reason="dsr", idempotency_key="shared-key")

    assert conflict["outcome"] == IDEMPOTENCY_CONFLICT
    assert conflict["batch_id"] is None
    assert conflict["items"] == []
    assert conflict["items_total"] == 0
    # userB's facts were never touched — the conflicting call never ran.
    assert store.get_fact("f2") is not None

    # Also conflicts on a different `reason`/`force`/`scope` for the SAME
    # user_id — fingerprint covers all five fields, not just user_id.
    conflict_reason = batch.forget_all_durable(
        "userA", reason="different_reason", idempotency_key="shared-key",
    )
    assert conflict_reason["outcome"] == IDEMPOTENCY_CONFLICT


def test_idempotency_conflict_report_has_stable_schema_without_disclosure(rig):
    """Round 5.1 fix (Copilot): IDEMPOTENCY_CONFLICT's report dict must
    contain the same structural keys (`force`/`scope`) every other
    forget_all_durable() outcome returns — a caller treating the report
    schema as stable must never hit a KeyError just because this
    particular outcome is IDEMPOTENCY_CONFLICT. The placeholder values
    must still be non-disclosing: never the real force/scope/batch_id/
    user_id/actor belonging to the conflicting EXISTING request."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1", source="userA"))
    store.store_fact(_fact("f2", source="userB"))

    first = batch.forget_all_durable(
        "userA", reason="dsr", actor="original-actor", force=False,
        scope=None, idempotency_key="shared-key-2",
    )
    assert first["outcome"] == COMPLETE

    conflict = batch.forget_all_durable(
        "userB", reason="dsr", actor="conflicting-actor",
        actor_capability="admin", force=True, scope="whole_db_cleanup",
        idempotency_key="shared-key-2",
    )

    assert conflict["outcome"] == IDEMPOTENCY_CONFLICT
    # Schema stability: these keys must exist (no KeyError for a caller
    # that expects every outcome to have them), as plain None placeholders.
    assert conflict["force"] is None
    assert conflict["scope"] is None
    # Non-disclosure: nothing about either the original OR the conflicting
    # request's identity/parameters leaks through.
    assert conflict["batch_id"] is None
    assert conflict["user_id"] is None
    assert "actor" not in conflict


def test_get_batch_report_by_idempotency_key_requires_matching_fingerprint(rig):
    """Additional hardening: the key string ALONE must never be enough to
    read back a batch's contents (user_id, per-item outcomes, compliance
    findings) — the caller must prove it knows the original request by
    supplying the SAME fingerprint compute_request_fingerprint() would
    produce for it. A wrong/missing fingerprint is indistinguishable from
    'not found', so a leaked/guessed key alone discloses nothing."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))

    report = batch.forget_all_durable("userA", reason="dsr", idempotency_key="lookup-key")
    assert report["outcome"] == COMPLETE

    correct_fingerprint = ebc_module.compute_request_fingerprint(
        user_id="userA", reason="dsr", actor="operator", force=False, scope=None,
    )
    found = batch.get_batch_report_by_idempotency_key(
        "lookup-key", request_fingerprint=correct_fingerprint,
    )
    assert found is not None
    assert found["batch_id"] == report["batch_id"]

    wrong_fingerprint = ebc_module.compute_request_fingerprint(
        user_id="someone_else", reason="dsr", actor="operator", force=False, scope=None,
    )
    not_found = batch.get_batch_report_by_idempotency_key(
        "lookup-key", request_fingerprint=wrong_fingerprint,
    )
    assert not_found is None


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


# ── Blocker #7: snapshot_hash fail-closed ───────────────────────────────────

def test_snapshot_hash_mismatch_fails_closed_without_processing(rig):
    """If erasure_batch_items no longer matches what was hashed at snapshot
    time (e.g. an out-of-band row change), the batch must refuse to process
    rather than silently run against a membership list that cannot be
    proven intact."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))
    store.store_fact(_fact("f2"))

    report = batch.forget_all_durable("userA", reason="dsr")
    assert report["outcome"] == COMPLETE
    assert report["snapshot_integrity_ok"] is True

    # Create a SECOND batch and tamper with its item snapshot directly,
    # bypassing the coordinator entirely.
    store.store_fact(_fact("f3"))
    store.store_fact(_fact("f4"))
    batch_id = batch._create_batch_snapshot(
        user_id="userA", reason="dsr", actor="tester", force=False, scope=None,
        idempotency_key=None, actor_capability="reader",
        request_fingerprint="fp-tamper-test",
    )
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE erasure_batch_items SET epistemic_state_at_snapshot = 'TAMPERED' "
            "WHERE batch_id = ? AND fact_id = 'f3'",
            (batch_id,),
        )
        conn.commit()

    tampered_report = _resume_specific_batch(batch, batch_id)

    assert tampered_report["outcome"] == FAILED
    assert tampered_report["error"] == "snapshot_integrity_check_failed"
    assert tampered_report["snapshot_integrity_ok"] is False
    # Fail closed: nothing was erased under the unproven membership list.
    assert store.get_fact("f3") is not None
    assert store.get_fact("f4") is not None


# ── Blocker #8: orphan protection (PRAGMA foreign_keys=ON) ──────────────────

def test_orphan_batch_item_insert_is_rejected(rig):
    batch, coordinator, store, *_ = rig
    with sqlite3.connect(store.db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO erasure_batch_items "
                "(item_id, batch_id, fact_id, epistemic_state_at_snapshot, "
                "status, created_at, updated_at) "
                "VALUES ('orphan_item', 'nonexistent_batch', 'f1', 'Observed', "
                "'PENDING', 'now', 'now')"
            )


def test_orphan_force_receipt_insert_is_rejected(rig):
    batch, coordinator, store, *_ = rig
    with sqlite3.connect(store.db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO erasure_batch_force_receipts "
                "(receipt_id, batch_id, actor, actor_capability, scope, "
                "user_id, reason, authorized_at) "
                "VALUES ('orphan_receipt', 'nonexistent_batch', 'a', 'admin', "
                "'s', 'u', 'r', 'now')"
            )


def test_force_receipts_are_genuinely_append_only(rig):
    """Additional hardening: erasure_batch_force_receipts is enforced
    append-only by real BEFORE DELETE/UPDATE triggers (mirroring
    migration 012's erasure_log triggers) — not just a docstring claim."""
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1", source="default"))

    report = batch.forget_all_durable(
        "default", actor="tester", actor_capability="admin",
        force=True, scope="cleanup",
    )
    assert report["outcome"] == COMPLETE

    with sqlite3.connect(store.db_path) as conn:
        receipt_id = conn.execute(
            "SELECT receipt_id FROM erasure_batch_force_receipts WHERE batch_id = ?",
            (report["batch_id"],),
        ).fetchone()[0]

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "DELETE FROM erasure_batch_force_receipts WHERE receipt_id = ?",
                (receipt_id,),
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "UPDATE erasure_batch_force_receipts SET actor = 'tampered' "
                "WHERE receipt_id = ?",
                (receipt_id,),
            )


# ── Blocker #4: no fake defense-in-depth / real PrincipalContext ──────────

def test_tool_handlers_forget_all_requires_explicit_principal(rig, monkeypatch):
    """core.tool_handlers.forget_all() must NOT hardcode/assume admin
    capability — a direct call with a non-admin PrincipalContext must be
    refused exactly like any other non-admin caller, proving there is no
    hidden 'this handler is always admin' shortcut."""
    from core import tool_handlers

    batch, coordinator, store, *_ = rig
    import core.erasure_batch_coordinator as _ebc
    monkeypatch.setattr(memory, "_GLOBAL_STORE", store)
    monkeypatch.setattr(_ebc, "_default_batch_coordinator", batch)

    store.store_fact(_fact("f1", source="default"))

    non_admin = PrincipalContext(capability="guardian", credential_fingerprint="api:deadbeef")
    result = tool_handlers.forget_all(
        user_id="default", principal=non_admin, force=True, scope="whole_db_cleanup",
    )
    assert result["outcome"] == REFUSED
    assert result["reason"] == "force_requires_admin_capability"
    assert store.get_fact("f1") is not None

    admin = PrincipalContext(capability="admin", credential_fingerprint="api:cafebabe")
    ok = tool_handlers.forget_all(
        user_id="default", principal=admin, force=True, scope="whole_db_cleanup",
    )
    assert ok["outcome"] == COMPLETE
    assert store.get_fact("f1") is None
    # The force receipt records the REAL principal, not a client-suppliable
    # "operator" literal.
    with sqlite3.connect(store.db_path) as conn:
        row = conn.execute(
            "SELECT actor, actor_capability FROM erasure_batch_force_receipts "
            "WHERE batch_id = ?",
            (ok["batch_id"],),
        ).fetchone()
    assert row == ("api:cafebabe", "admin")


# ── Legacy shim (core.forgetting.ForgettingEngine.forget_all) ─────────────

def test_forgetting_engine_forget_all_is_deprecated_and_delegates(rig):
    """Round 5 fix (Codex P2): the shim builds its OWN db_path-bound
    SQLiteGraphStore/BatchErasureCoordinator (see
    test_forgetting.py for the full db_path-isolation regression suite) —
    it no longer delegates to the module-level get_batch_coordinator()
    singleton, so there is nothing left to monkeypatch here. Read the
    result back via a FRESH SQLiteGraphStore against the same file rather
    than the original `store` object: that object's own in-process L0
    read-cache (core.memory.SQLiteGraphStore._l0) has no way to know
    about a DELETE committed through the shim's separate store instance —
    a pre-existing, per-instance-cache characteristic of this codebase,
    not something this fix's db_path-isolation scope touches."""
    from core import forgetting as forgetting_mod

    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f1"))

    engine = forgetting_mod.ForgettingEngine(db_path=store.db_path)
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr")

    assert verdict.allowed is True
    assert verdict.affected_facts == 1
    assert memory.make_store(store.db_path).get_fact("f1") is None


# ── Round 5 fix (Codex P2): batch tombstones keyed to the data subject ──────

def test_batch_tombstones_keyed_to_data_subject_not_operator_actor(rig):
    """A + E: a FORGET_ALL batch run by a different operator than the data
    subject must tombstone under the data subject (batch's user_id), not
    the operator/API credential fingerprint that authorized it — otherwise
    user-scoped GDPR Art. 30 audit queries (erasure_log.user_id) silently
    miss real erasures. coordinator.erasure_log() is the Art. 30 record of
    processing this reads back through (mirrors
    ForgettingEngine.get_erasure_log(), which filters the same column via
    the erasure_audit view — not exercised here since this rig's bare
    make_store() DB doesn't run the full migration chain that view needs)."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f1"))
    store.store_fact(_fact("f2"))

    report = batch.forget_all_durable("userA", reason="dsr", actor="api:deadbeef")
    assert report["outcome"] == COMPLETE

    log = coordinator.erasure_log()
    log_for_user_a = [row for row in log if row["user_id"] == "userA"]
    assert {row["fact_id"] for row in log_for_user_a} == {"f1", "f2"}

    # The operator credential must never itself be discoverable as a data
    # subject in the audit log.
    assert [row for row in log if row["user_id"] == "api:deadbeef"] == []

    # Operator provenance is still available, per-fact, on the durable job.
    for fid in ("f1", "f2"):
        job_report = coordinator.get_job_report(fid)
        assert job_report["actor"] == "api:deadbeef"
        assert job_report["subject_user_id"] == "userA"


def test_batch_force_erasure_receipt_records_operator_tombstone_keeps_subject(rig):
    """B: force=True's append-only receipt records the operator's
    credential fingerprint — the erasure tombstone itself must still be
    associated with the data subject, not that operator fingerprint."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f1", source="userA"))

    report = batch.forget_all_durable(
        "userA", reason="dsr", actor="api:deadbeef",
        actor_capability="admin", force=True, scope="cleanup",
    )
    assert report["outcome"] == COMPLETE

    with sqlite3.connect(store.db_path) as conn:
        receipt_actor = conn.execute(
            "SELECT actor FROM erasure_batch_force_receipts WHERE batch_id = ?",
            (report["batch_id"],),
        ).fetchone()[0]
    assert receipt_actor == "api:deadbeef"

    tombstone = store.get_tombstone("f1")
    assert tombstone["user_id"] == "userA"


# ── Round 5.2 fix (Codex P2): batch adoption binds subject_user_id ─────────

def test_batch_adopts_pending_job_and_binds_subject_before_processing(rig):
    """1: a legacy/crash-left PENDING per-fact job (subject_user_id=NULL,
    actor="legacy-operator") must be bound to the BATCH's data subject
    BEFORE it's resumed/finalized — the same job is adopted (no new
    generation), the tombstone lands under the batch's user_id, and
    operator provenance (actor) on the pre-existing row is preserved."""
    batch, coordinator, store, embeddings, ngram = rig
    fact_id = "f_legacy_pending"
    store.store_fact(_fact(fact_id, source="userA"))

    job_id = "erj_legacy_pending_batch"
    now = _now()
    with coordinator._jobs_db() as conn:
        conn.execute(
            "INSERT INTO erasure_jobs (job_id, fact_id, generation, reason, actor, "
            "subject_user_id, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, fact_id, 1, "legacy", "legacy-operator", None, PENDING, now, now),
        )
        for step_name in ("determine_raw", "l1_same_db", "embeddings", "ngram"):
            conn.execute(
                "INSERT INTO erasure_job_steps (step_id, job_id, step_name, status) "
                "VALUES (?, ?, ?, ?)",
                (f"{job_id}_{step_name}", job_id, step_name, PENDING),
            )

    report = batch.forget_all_durable("userA", reason="dsr", actor="api:deadbeef")
    assert report["outcome"] == COMPLETE

    job_report = coordinator.get_job_report(fact_id)
    assert job_report["job_id"] == job_id  # same job adopted, not a new generation
    assert job_report["subject_user_id"] == "userA"
    assert job_report["actor"] == "legacy-operator"  # operator provenance preserved

    tombstone = store.get_tombstone(fact_id)
    assert tombstone["user_id"] == "userA"


# ── Round 5.3 fix (Codex P1): SUBJECT_CONFLICT must never report success ───

def _insert_conflicting_job(coordinator, *, fact_id, subject_user_id, actor="other-operator"):
    """Pre-create a durable PENDING erasure_jobs row already bound to
    `subject_user_id` — simulates a fact_id whose per-fact job belongs to
    a DIFFERENT data subject than the batch about to process it."""
    job_id = f"erj_conflict_{fact_id}"
    now = _now()
    with coordinator._jobs_db() as conn:
        conn.execute(
            "INSERT INTO erasure_jobs (job_id, fact_id, generation, reason, actor, "
            "subject_user_id, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, fact_id, 1, "legacy", actor, subject_user_id, PENDING, now, now),
        )
        for step_name in ("determine_raw", "l1_same_db", "embeddings", "ngram"):
            conn.execute(
                "INSERT INTO erasure_job_steps (step_id, job_id, step_name, status) "
                "VALUES (?, ?, ?, ?)",
                (f"{job_id}_{step_name}", job_id, step_name, PENDING),
            )
    return job_id


def test_subject_conflict_prevents_batch_complete_success(rig):
    """1: a one-item batch whose only item hits SUBJECT_CONFLICT must
    never be reported as COMPLETE/successful."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_conflict", source="userA"))
    _insert_conflicting_job(coordinator, fact_id="f_conflict", subject_user_id="userB")

    report = batch.forget_all_durable("userA", reason="dsr", actor="api:newoperator")

    assert report["outcome"] == SUBJECT_CONFLICT
    assert report["success"] is False
    assert report["erasure_complete"] is False
    assert report["operation_finished"] is True
    assert report["subject_conflict"] is True
    assert report["conflict_items"] == ["f_conflict"]


def test_mixed_batch_with_subject_conflict_is_not_erasure_complete(rig):
    """2: a mixed batch (one item genuinely erased, one blocked by a
    subject conflict) must still be reported as non-successful overall —
    the genuinely-erased item's own outcome is unaffected."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_ok", source="userA"))
    store.store_fact(_fact("f_conflict", source="userA"))
    _insert_conflicting_job(coordinator, fact_id="f_conflict", subject_user_id="userB")

    report = batch.forget_all_durable("userA", reason="dsr", actor="api:newoperator")

    assert report["outcome"] == SUBJECT_CONFLICT
    assert report["success"] is False
    assert report["erasure_complete"] is False
    items = {i["fact_id"]: i["status"] for i in report["items"]}
    assert items["f_ok"] == COMPLETE
    assert items["f_conflict"] == SUBJECT_CONFLICT
    assert store.get_fact("f_ok") is None
    assert "f_conflict" in report["conflict_items"]


def test_subject_conflict_report_remains_non_successful_on_replay(rig):
    """3: reading the durable report back (get_batch_report) must
    preserve the same non-successful result, not just the live return
    value from the original call."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_conflict", source="userA"))
    _insert_conflicting_job(coordinator, fact_id="f_conflict", subject_user_id="userB")

    first = batch.forget_all_durable("userA", reason="dsr", actor="api:newoperator")
    assert first["outcome"] == SUBJECT_CONFLICT

    reread = batch.get_batch_report(first["batch_id"])
    assert reread["outcome"] == SUBJECT_CONFLICT
    assert reread["success"] is False
    assert reread["erasure_complete"] is False
    assert reread["operation_finished"] is True


def test_subject_conflict_idempotent_replay_stays_non_successful(rig):
    """4: repeating the same idempotent request (same idempotency_key)
    must not convert a subject conflict into a successful outcome —
    resume_incomplete_batches()'s own exclusion of SUBJECT_CONFLICT from
    _RUNNABLE_BATCH_STATUSES means this also proves it never auto-retries
    into a false success."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_conflict", source="userA"))
    _insert_conflicting_job(coordinator, fact_id="f_conflict", subject_user_id="userB")

    first = batch.forget_all_durable(
        "userA", reason="dsr", actor="api:newoperator", idempotency_key="conflict-key",
    )
    assert first["outcome"] == SUBJECT_CONFLICT

    second = batch.forget_all_durable(
        "userA", reason="dsr", actor="api:newoperator", idempotency_key="conflict-key",
    )
    assert second["batch_id"] == first["batch_id"]
    assert second["outcome"] == SUBJECT_CONFLICT
    assert second["success"] is False
    assert second["erasure_complete"] is False

    # A crash-recovery style sweep must also never resurrect this into success.
    resumed = batch.resume_incomplete_batches()
    assert first["batch_id"] not in {r["batch_id"] for r in resumed}


def test_subject_conflict_distinct_from_compliance_and_residual(rig):
    """5: SUBJECT_CONFLICT must not be confused with
    CRITICAL_COMPLIANCE_VIOLATION or RESIDUAL_IMMUTABLE_DATA — both keep
    their own pre-existing, distinct semantics (a batch with only one of
    those still reaches COMPLETE/COMPLETE_WITH_RESIDUAL); only a genuine
    subject conflict blocks batch success."""
    batch, coordinator, store, embeddings, ngram = rig

    store.store_fact(_fact("f_critical"))
    _force_epistemic_state(store, "f_critical", "ImmutableCore")

    critical_report = batch.forget_all_durable("userA", reason="dsr", actor="tester")
    assert critical_report["outcome"] == COMPLETE
    assert critical_report["critical_compliance_violation"] is True
    assert critical_report["subject_conflict"] is False
    assert critical_report["conflict_items"] == []


# ── Round 5.4 Codex finding (P2): fold conflict items into effective ────────
# success reporting. _report() used to derive success/erasure_complete
# purely from the durable batch row's `status` — a restored/hand-repaired/
# pre-Round-5.3 row could have status=COMPLETE while its OWN item rows
# still carried SUBJECT_CONFLICT, and the report would still claim
# success=true/erasure_complete=true. _report() must re-derive the
# effective outcome from conflict_items every time, independent of the
# stored batch status.

def test_report_fails_closed_when_complete_batch_contains_conflict_item(rig):
    """1-3: a batch row hand-restored to status=COMPLETE whose item rows
    still contain SUBJECT_CONFLICT must fail closed when read back — the
    stored status is exposed separately (`stored_status`) but never
    trusted as the effective result."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_conflict", source="userA"))
    _insert_conflicting_job(coordinator, fact_id="f_conflict", subject_user_id="userB")

    first = batch.forget_all_durable("userA", reason="dsr", actor="api:newoperator")
    assert first["outcome"] == SUBJECT_CONFLICT

    # Simulate a restored/stale row: the durable STATUS says COMPLETE, but
    # the item row underneath (never touched) still says SUBJECT_CONFLICT.
    with batch._jobs_db() as conn:
        conn.execute(
            "UPDATE erasure_batches SET status = ? WHERE batch_id = ?",
            (COMPLETE, first["batch_id"]),
        )
        conn.commit()

    reread = batch.get_batch_report(first["batch_id"])
    assert reread["stored_status"] == COMPLETE
    assert reread["outcome"] == SUBJECT_CONFLICT
    assert reread["success"] is False
    assert reread["erasure_complete"] is False
    assert reread["subject_conflict"] is True
    assert reread["conflict_items"] == ["f_conflict"]


def test_restored_complete_batch_with_conflict_is_not_erasure_complete(rig):
    """5: reading a restored/stale report is not just a one-off — repeated
    reads all fail closed, and no execution path (resume) needs to run for
    this to hold."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_ok", source="userA"))
    store.store_fact(_fact("f_conflict", source="userA"))
    _insert_conflicting_job(coordinator, fact_id="f_conflict", subject_user_id="userB")

    first = batch.forget_all_durable("userA", reason="dsr", actor="api:newoperator")
    assert first["outcome"] == SUBJECT_CONFLICT

    with batch._jobs_db() as conn:
        conn.execute(
            "UPDATE erasure_batches SET status = ? WHERE batch_id = ?",
            (COMPLETE, first["batch_id"]),
        )
        conn.commit()

    for _ in range(3):
        reread = batch.get_batch_report(first["batch_id"])
        assert reread["success"] is False
        assert reread["erasure_complete"] is False


def test_critical_and_subject_conflict_batch_remains_non_successful(rig):
    """6: a batch with BOTH a critical-compliance item and a subject
    conflict must preserve critical precedence (compliance_status still
    set) while also never reporting success — the conflict remains
    visible in conflict_items regardless."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_critical"))
    _force_epistemic_state(store, "f_critical", "ImmutableCore")
    store.store_fact(_fact("f_conflict", source="userA"))
    _insert_conflicting_job(coordinator, fact_id="f_conflict", subject_user_id="userB")

    report = batch.forget_all_durable("userA", reason="dsr", actor="tester")

    assert report["critical_compliance_violation"] is True
    assert report["subject_conflict"] is True
    assert "f_conflict" in report["conflict_items"]
    assert report["success"] is False
    assert report["erasure_complete"] is False


def test_conflict_report_replay_cannot_restore_success(rig):
    """7: idempotent replay of a batch whose durable row was tampered with
    to look COMPLETE must remain non-successful — replay must never be a
    way to launder a stale/inconsistent row into a false success."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_conflict", source="userA"))
    _insert_conflicting_job(coordinator, fact_id="f_conflict", subject_user_id="userB")

    first = batch.forget_all_durable(
        "userA", reason="dsr", actor="api:newoperator", idempotency_key="restored-key",
    )
    assert first["outcome"] == SUBJECT_CONFLICT

    with batch._jobs_db() as conn:
        conn.execute(
            "UPDATE erasure_batches SET status = ? WHERE batch_id = ?",
            (COMPLETE, first["batch_id"]),
        )
        conn.commit()

    replay = batch.forget_all_durable(
        "userA", reason="dsr", actor="api:newoperator", idempotency_key="restored-key",
    )
    assert replay["batch_id"] == first["batch_id"]
    assert replay["success"] is False
    assert replay["erasure_complete"] is False


# ── Round 5.4 second-order Codex finding (P2): preserve PARTIAL outcome ─────
# when a subject conflict coexists with a genuinely still-retryable item.
# _report() must never report the terminal SUBJECT_CONFLICT outcome while
# OTHER items remain PENDING/PARTIAL/FAILED — that would look terminal to
# a caller and could stop it from retrying items that are still erasable.

def test_conflict_does_not_override_a_still_retryable_batch(rig):
    """A batch row whose stored status claims a terminal outcome
    (SUBJECT_CONFLICT) while its OWN item rows still contain a retryable
    (PENDING) item alongside the conflicting one must report PARTIAL, not
    SUBJECT_CONFLICT — the conflict is visible via conflict_items/
    subject_conflict, but never promoted to the effective outcome while
    other work remains."""
    batch, coordinator, store, embeddings, ngram = rig
    batch_id = "eb_mixed_conflict_retryable"
    now = _now()
    with batch._jobs_db() as conn:
        conn.execute(
            "INSERT INTO erasure_batches (batch_id, user_id, reason, actor, force, "
            "scope, idempotency_key, request_fingerprint, status, compliance_status, "
            "items_total, snapshot_hash, snapshot_at, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 0, NULL, NULL, ?, ?, NULL, ?, ?, ?, ?, ?)",
            (batch_id, "userA", "dsr", "tester", "fp_mixed", SUBJECT_CONFLICT,
             2, "hash_mixed", now, now, now),
        )
        conn.execute(
            "INSERT INTO erasure_batch_items (item_id, batch_id, fact_id, "
            "epistemic_state_at_snapshot, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"{batch_id}_item1", batch_id, "f_conflict", "Observed", SUBJECT_CONFLICT, now, now),
        )
        conn.execute(
            "INSERT INTO erasure_batch_items (item_id, batch_id, fact_id, "
            "epistemic_state_at_snapshot, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"{batch_id}_item2", batch_id, "f_pending", "Observed", PENDING, now, now),
        )
        conn.commit()

    report = batch.get_batch_report(batch_id)
    assert report["stored_status"] == SUBJECT_CONFLICT
    assert report["outcome"] == PARTIAL
    assert report["operation_finished"] is False
    assert report["success"] is False
    assert report["erasure_complete"] is False
    assert report["subject_conflict"] is True
    assert report["conflict_items"] == ["f_conflict"]


def test_conflict_alone_with_no_retryable_items_still_reports_subject_conflict(rig):
    """The companion case: once the OTHER item genuinely reaches a
    terminal state (no longer retryable), the conflict DOES become the
    effective outcome — the fix narrows to "not while still retryable",
    not "never report SUBJECT_CONFLICT again"."""
    batch, coordinator, store, embeddings, ngram = rig
    batch_id = "eb_conflict_only_terminal"
    now = _now()
    with batch._jobs_db() as conn:
        conn.execute(
            "INSERT INTO erasure_batches (batch_id, user_id, reason, actor, force, "
            "scope, idempotency_key, request_fingerprint, status, compliance_status, "
            "items_total, snapshot_hash, snapshot_at, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 0, NULL, NULL, ?, ?, NULL, ?, ?, ?, ?, ?)",
            (batch_id, "userA", "dsr", "tester", "fp_terminal", SUBJECT_CONFLICT,
             2, "hash_terminal", now, now, now),
        )
        conn.execute(
            "INSERT INTO erasure_batch_items (item_id, batch_id, fact_id, "
            "epistemic_state_at_snapshot, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"{batch_id}_item1", batch_id, "f_conflict", "Observed", SUBJECT_CONFLICT, now, now),
        )
        conn.execute(
            "INSERT INTO erasure_batch_items (item_id, batch_id, fact_id, "
            "epistemic_state_at_snapshot, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"{batch_id}_item2", batch_id, "f_done", "Observed", COMPLETE, now, now),
        )
        conn.commit()

    report = batch.get_batch_report(batch_id)
    assert report["outcome"] == SUBJECT_CONFLICT
    assert report["operation_finished"] is True


# ── Round 5.4 third-order Codex finding (P2): make recomputed PARTIAL ───────
# batches actually runnable again. Reporting outcome=PARTIAL for a stale
# terminal row is not enough — _run_batch()/resume_incomplete_batches()
# both gate on the STORED erasure_batches.status column, so without a
# self-heal write the batch would report PARTIAL forever without ever
# being picked up for reprocessing.

def test_recomputed_partial_batch_self_heals_stored_status(rig):
    """The stored status column itself must be repaired back to PARTIAL
    (best-effort) when _report() discovers a stale terminal claim with
    retryable items underneath — so a later resume actually reprocesses
    them, rather than the batch being stuck reporting PARTIAL forever."""
    batch, coordinator, store, embeddings, ngram = rig
    batch_id = "eb_self_heal_partial"
    now = _now()
    with batch._jobs_db() as conn:
        conn.execute(
            "INSERT INTO erasure_batches (batch_id, user_id, reason, actor, force, "
            "scope, idempotency_key, request_fingerprint, status, compliance_status, "
            "items_total, snapshot_hash, snapshot_at, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 0, NULL, NULL, ?, ?, NULL, ?, ?, ?, ?, ?)",
            (batch_id, "userA", "dsr", "tester", "fp_self_heal", COMPLETE,
             2, "hash_self_heal", now, now, now),
        )
        conn.execute(
            "INSERT INTO erasure_batch_items (item_id, batch_id, fact_id, "
            "epistemic_state_at_snapshot, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"{batch_id}_item1", batch_id, "f_pending", "Observed", PENDING, now, now),
        )
        conn.execute(
            "INSERT INTO erasure_batch_items (item_id, batch_id, fact_id, "
            "epistemic_state_at_snapshot, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"{batch_id}_item2", batch_id, "f_done", "Observed", COMPLETE, now, now),
        )
        conn.commit()

    report = batch.get_batch_report(batch_id)
    assert report["outcome"] == PARTIAL
    assert report["stored_status"] == COMPLETE  # reflects the value AT READ time

    with batch._jobs_db() as conn:
        row = conn.execute(
            "SELECT status FROM erasure_batches WHERE batch_id = ?", (batch_id,),
        ).fetchone()
    assert row["status"] == PARTIAL  # the self-heal actually landed

    # Genuinely runnable now — resume_incomplete_batches() must be able to
    # pick it up, not skip it forever.
    resumed_ids = {r["batch_id"] for r in batch.resume_incomplete_batches()}
    assert batch_id in resumed_ids
    assert report["success"] is False


# ── Round 5.4 fourth-order Codex finding (P2): crash/startup recovery ───────
# must discover a stored-TERMINAL batch whose CURRENT item rows still prove
# retryable work remains, WITHOUT depending on any caller first requesting
# its report (which is the only thing that previously triggered the
# self-heal). resume_incomplete_batches() now selects such batches via a
# targeted EXISTS query and reconciles them itself before claiming.

def _insert_batch_row(
    batch, *, batch_id, user_id, status, items, created_at=None,
):
    """Directly persist a batch + its item rows via raw SQL — mirrors the
    hand-restored/pre-fix state these tests reproduce. `items` is a list of
    (fact_id, epistemic_state, item_status) tuples; snapshot_hash is
    computed for real from (fact_id, epistemic_state) so _run_batch()'s
    snapshot-integrity check passes and items are genuinely processed."""
    now = created_at or _now()
    items_for_hash = [
        {"fact_id": fid, "epistemic_state_at_snapshot": state}
        for fid, state, _status in items
    ]
    snapshot_hash = BatchErasureCoordinator._compute_snapshot_hash(items_for_hash)
    with batch._jobs_db() as conn:
        conn.execute(
            "INSERT INTO erasure_batches (batch_id, user_id, reason, actor, force, "
            "scope, idempotency_key, request_fingerprint, status, compliance_status, "
            "items_total, snapshot_hash, snapshot_at, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 0, NULL, NULL, ?, ?, NULL, ?, ?, ?, ?, ?)",
            (batch_id, user_id, "dsr", "tester", f"fp_{batch_id}", status,
             len(items), snapshot_hash, now, now, now),
        )
        for i, (fid, state, item_status) in enumerate(items):
            conn.execute(
                "INSERT INTO erasure_batch_items (item_id, batch_id, fact_id, "
                "epistemic_state_at_snapshot, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f"{batch_id}_item{i}", batch_id, fid, state, item_status, now, now),
            )
        conn.commit()


def test_recovery_sweep_discovers_complete_batch_with_retryable_item(rig):
    """A batch row hand-restored to status=COMPLETE whose item row is still
    PENDING must be discovered, self-healed, and actually reprocessed by
    resume_incomplete_batches() alone — no report() call precedes it."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_pending", source="userA"))
    _insert_batch_row(
        batch, batch_id="eb_stale_complete_pending", user_id="userA",
        status=COMPLETE, items=[("f_pending", "Observed", PENDING)],
    )

    resumed = {r["batch_id"]: r for r in batch.resume_incomplete_batches()}
    assert "eb_stale_complete_pending" in resumed
    result = resumed["eb_stale_complete_pending"]
    assert result["outcome"] == COMPLETE
    assert result["success"] is True
    assert store.get_fact("f_pending") is None

    with batch._jobs_db() as conn:
        row = conn.execute(
            "SELECT status FROM erasure_batches WHERE batch_id = ?",
            ("eb_stale_complete_pending",),
        ).fetchone()
    assert row["status"] == COMPLETE


def test_recovery_sweep_resumes_retryable_items_beside_subject_conflict(rig):
    """A stored SUBJECT_CONFLICT batch with one FAILED (retryable) item
    beside the conflicting one: recovery must retry the FAILED item, keep
    the conflict item visible, and never falsely report COMPLETE."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_ok", source="userA"))
    _insert_batch_row(
        batch, batch_id="eb_conflict_plus_retryable", user_id="userA",
        status=SUBJECT_CONFLICT,
        items=[
            ("f_conflict", "Observed", SUBJECT_CONFLICT),
            ("f_ok", "Observed", FAILED),
        ],
    )

    resumed = {r["batch_id"]: r for r in batch.resume_incomplete_batches()}
    assert "eb_conflict_plus_retryable" in resumed
    result = resumed["eb_conflict_plus_retryable"]

    assert store.get_fact("f_ok") is None  # the retryable item was reprocessed
    assert result["subject_conflict"] is True
    assert "f_conflict" in result["conflict_items"]
    assert result["outcome"] == SUBJECT_CONFLICT
    assert result["success"] is False


def test_recovery_sweep_does_not_reopen_consistent_terminal_batch(rig):
    """A genuinely consistent COMPLETE batch (no retryable item rows) must
    never be reclaimed/mutated by the recovery sweep."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f1"))
    first = batch.forget_all_durable("userA", reason="dsr", actor="tester")
    assert first["outcome"] == COMPLETE

    with batch._jobs_db() as conn:
        before = conn.execute(
            "SELECT status, updated_at, claim_generation FROM erasure_batches "
            "WHERE batch_id = ?", (first["batch_id"],),
        ).fetchone()

    resumed_ids = {r["batch_id"] for r in batch.resume_incomplete_batches()}
    assert first["batch_id"] not in resumed_ids

    with batch._jobs_db() as conn:
        after = conn.execute(
            "SELECT status, updated_at, claim_generation FROM erasure_batches "
            "WHERE batch_id = ?", (first["batch_id"],),
        ).fetchone()
    assert after["status"] == COMPLETE
    assert after["claim_generation"] == before["claim_generation"]
    assert after["updated_at"] == before["updated_at"]


def test_recovery_sweep_does_not_bypass_critical_compliance_terminal_state(rig):
    """A CRITICAL_COMPLIANCE_VIOLATION item is terminal-for-itself and is
    NOT in _ITEM_RETRYABLE_STATUSES — a batch resolved to COMPLETE with only
    such an item (no other retryable work) must never be reopened by the
    recovery sweep merely because a compliance violation exists."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_critical"))
    _force_epistemic_state(store, "f_critical", "ImmutableCore")

    first = batch.forget_all_durable("userA", reason="dsr", actor="tester")
    assert first["compliance_status"] == CRITICAL_COMPLIANCE_VIOLATION
    assert first["outcome"] == COMPLETE

    with batch._jobs_db() as conn:
        before = conn.execute(
            "SELECT status, claim_generation FROM erasure_batches WHERE batch_id = ?",
            (first["batch_id"],),
        ).fetchone()

    resumed_ids = {r["batch_id"] for r in batch.resume_incomplete_batches()}
    assert first["batch_id"] not in resumed_ids

    with batch._jobs_db() as conn:
        after = conn.execute(
            "SELECT status, claim_generation, compliance_status FROM erasure_batches "
            "WHERE batch_id = ?", (first["batch_id"],),
        ).fetchone()
    assert after["status"] == COMPLETE
    assert after["claim_generation"] == before["claim_generation"]
    assert after["compliance_status"] == CRITICAL_COMPLIANCE_VIOLATION


def test_recovery_terminal_reconciliation_does_not_clobber_concurrent_update(rig):
    """Reproduces the exact race window resume_incomplete_batches()'s
    reconcile step is exposed to: it reads a (stale) terminal batch
    snapshot, then — before its self-heal CAS runs — a concurrent
    transaction writes a genuinely fresher status. The guarded CAS (bound
    to the EXACT stale value read) must miss rather than clobber it."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_pending", source="userA"))
    _insert_batch_row(
        batch, batch_id="eb_cas_race", user_id="userA",
        status=COMPLETE, items=[("f_pending", "Observed", PENDING)],
    )

    # This is exactly what resume_incomplete_batches() does before calling
    # _report() in its reconcile step: read the (about to become stale)
    # batch snapshot first.
    stale_batch = batch._load_batch("eb_cas_race")
    assert stale_batch["status"] == COMPLETE

    # A concurrent transaction — e.g. a live runner independently finalizing
    # this batch for real — writes a fresher status in the gap.
    with batch._jobs_db() as conn:
        conn.execute(
            "UPDATE erasure_batches SET status = ?, updated_at = ? WHERE batch_id = ?",
            (SUBJECT_CONFLICT, _now(), "eb_cas_race"),
        )
        conn.commit()

    batch._report(stale_batch, batch._load_items("eb_cas_race"))

    with batch._jobs_db() as conn:
        row = conn.execute(
            "SELECT status FROM erasure_batches WHERE batch_id = ?",
            ("eb_cas_race",),
        ).fetchone()
    # The self-heal CAS was bound to status='COMPLETE' (the stale read) —
    # it must miss against the now-SUBJECT_CONFLICT row, never clobber it.
    assert row["status"] == SUBJECT_CONFLICT


def test_recovery_of_stale_terminal_batch_does_not_require_report_call(rig, monkeypatch):
    """The SQL EXISTS query alone must discover the candidate. Many
    consistent terminal batches (no retryable items) coexist with one
    genuinely stale candidate — _report() must be invoked only for the
    true candidate, never once per historical terminal batch."""
    batch, coordinator, store, embeddings, ngram = rig

    for n in range(15):
        _insert_batch_row(
            batch, batch_id=f"eb_consistent_{n}", user_id="userA",
            status=COMPLETE, items=[(f"f_done_{n}", "Observed", COMPLETE)],
        )

    store.store_fact(_fact("f_pending", source="userA"))
    _insert_batch_row(
        batch, batch_id="eb_candidate", user_id="userA",
        status=COMPLETE, items=[("f_pending", "Observed", PENDING)],
    )

    call_count = {"n": 0}
    original_report = BatchErasureCoordinator._report

    def counting_report(self, b, items):
        call_count["n"] += 1
        return original_report(self, b, items)

    monkeypatch.setattr(BatchErasureCoordinator, "_report", counting_report)

    resumed_ids = {r["batch_id"] for r in batch.resume_incomplete_batches()}
    assert resumed_ids == {"eb_candidate"}
    # Reconcile (1) + _finalize_batch()'s own report (1) for the ONE true
    # candidate — nowhere near the 15 consistent batches that were never
    # candidates in the first place.
    assert call_count["n"] <= 2


def test_recovery_terminal_candidate_selection_respects_limit(rig, monkeypatch):
    """More stale-terminal candidates than the configured sweep limit: the
    result must be bounded, ordering deterministic (oldest first), and a
    later sweep must recover whatever the first one left behind."""
    batch, coordinator, store, embeddings, ngram = rig
    monkeypatch.setattr(ebc_module, "_RECOVERY_SWEEP_LIMIT", 3)

    batch_ids = []
    for n in range(5):
        store.store_fact(_fact(f"f_{n}", source="userA"))
        bid = f"eb_limit_{n}"
        batch_ids.append(bid)
        created = f"2026-01-01T00:00:0{n}+00:00"
        _insert_batch_row(
            batch, batch_id=bid, user_id="userA", status=COMPLETE,
            items=[(f"f_{n}", "Observed", PENDING)], created_at=created,
        )

    first_sweep_ids = {r["batch_id"] for r in batch.resume_incomplete_batches()}
    assert len(first_sweep_ids) == 3
    assert first_sweep_ids == set(batch_ids[:3])  # oldest 3, deterministic

    second_sweep_ids = {r["batch_id"] for r in batch.resume_incomplete_batches()}
    assert second_sweep_ids == set(batch_ids[3:])


# ── Round 5.4 fifth-order Codex finding (P2): the fourth-order fix combined ─
# the ordinary (PENDING/PARTIAL/FAILED/stale-RUNNING) and the new stale-
# terminal-with-retryable-items branches into ONE query with ONE global
# LIMIT — silently capping the ordinary branch, which was always unbounded
# before, and risking starvation of newer candidates behind a permanently
# stuck old prefix. The two branches are now selected by two separate
# queries and combined/deduplicated in Python.

def test_ordinary_recovery_is_not_capped_by_stale_terminal_limit(rig, monkeypatch):
    """More than _RECOVERY_SWEEP_LIMIT old ORDINARY (FAILED, permanently
    retryable) batches must never exclude a newer ordinary PENDING batch
    from being considered — the ordinary branch is unbounded, exactly as
    before this whole feature existed."""
    batch, coordinator, store, embeddings, ngram = rig
    monkeypatch.setattr(ebc_module, "_RECOVERY_SWEEP_LIMIT", 5)

    old_fact_ids = {f"f_ord_old_{n}" for n in range(8)}  # > limit (5)
    original_erase = coordinator.erase_fact_durable

    def flaky_erase(fact_id, **kwargs):
        if fact_id in old_fact_ids:
            return {"outcome": FAILED, "job_id": None}
        return original_erase(fact_id, **kwargs)

    monkeypatch.setattr(coordinator, "erase_fact_durable", flaky_erase)

    for n, fid in enumerate(sorted(old_fact_ids)):
        _insert_batch_row(
            batch, batch_id=f"eb_ord_old_{n}", user_id="userA", status=FAILED,
            items=[(fid, "Observed", FAILED)],
            created_at=f"2020-01-01T00:00:{n:02d}+00:00",
        )

    store.store_fact(_fact("f_ord_new", source="userA"))
    _insert_batch_row(
        batch, batch_id="eb_ord_new", user_id="userA", status=PENDING,
        items=[("f_ord_new", "Observed", PENDING)],
        created_at="2020-01-02T00:00:00+00:00",
    )

    resumed = {r["batch_id"]: r for r in batch.resume_incomplete_batches()}
    # ALL 8 old ordinary batches AND the newer one are considered in the
    # SAME sweep — the ordinary branch was never limited.
    assert all(f"eb_ord_old_{n}" in resumed for n in range(8))
    assert "eb_ord_new" in resumed
    assert resumed["eb_ord_new"]["outcome"] == COMPLETE
    assert store.get_fact("f_ord_new") is None


def test_stale_terminal_recovery_advances_past_permanent_failing_prefix(rig, monkeypatch):
    """More than _RECOVERY_SWEEP_LIMIT older stale-terminal candidates whose
    items are engineered to keep failing forever must not permanently
    block a newer stale-terminal candidate — it must be reached within a
    bounded number of subsequent sweeps, without the old prefix ever fully
    resolving its underlying items."""
    batch, coordinator, store, embeddings, ngram = rig
    monkeypatch.setattr(ebc_module, "_RECOVERY_SWEEP_LIMIT", 5)

    old_fact_ids = {f"f_stale_old_{n}" for n in range(8)}  # > limit (5)
    original_erase = coordinator.erase_fact_durable

    def flaky_erase(fact_id, **kwargs):
        if fact_id in old_fact_ids:
            return {"outcome": FAILED, "job_id": None}
        return original_erase(fact_id, **kwargs)

    monkeypatch.setattr(coordinator, "erase_fact_durable", flaky_erase)

    for n, fid in enumerate(sorted(old_fact_ids)):
        _insert_batch_row(
            batch, batch_id=f"eb_stale_old_{n}", user_id="userA", status=COMPLETE,
            items=[(fid, "Observed", PENDING)],
            created_at=f"2020-02-01T00:00:{n:02d}+00:00",
        )

    store.store_fact(_fact("f_stale_new", source="userA"))
    _insert_batch_row(
        batch, batch_id="eb_stale_new", user_id="userA", status=COMPLETE,
        items=[("f_stale_new", "Observed", PENDING)],
        created_at="2020-02-02T00:00:00+00:00",
    )

    first_sweep_ids = {r["batch_id"] for r in batch.resume_incomplete_batches()}
    assert len(first_sweep_ids) == 5  # bounded to the limit
    assert "eb_stale_new" not in first_sweep_ids  # not yet reached

    second_sweep = {r["batch_id"]: r for r in batch.resume_incomplete_batches()}
    # The newer candidate is reached WITHOUT the old prefix's items ever
    # actually resolving (they keep returning FAILED forever) — the batches
    # graduated out of the stale-terminal bucket (self-healed to PARTIAL)
    # merely by being reconciled once, vacating the LIMIT window.
    assert "eb_stale_new" in second_sweep
    assert second_sweep["eb_stale_new"]["outcome"] == COMPLETE
    assert store.get_fact("f_stale_new") is None


def test_recovery_limit_applies_only_to_stale_terminal_candidates(rig, monkeypatch):
    """In a single sweep with both classes over-represented: ALL ordinary
    candidates are considered (unbounded), but only _RECOVERY_SWEEP_LIMIT
    stale-terminal candidates are."""
    batch, coordinator, store, embeddings, ngram = rig
    monkeypatch.setattr(ebc_module, "_RECOVERY_SWEEP_LIMIT", 5)

    for n in range(8):
        _insert_batch_row(
            batch, batch_id=f"eb_mix_ord_{n}", user_id="userA", status=FAILED,
            items=[(f"f_mix_ord_{n}", "Observed", FAILED)],
            created_at=f"2020-03-01T00:00:{n:02d}+00:00",
        )
    for n in range(8):
        _insert_batch_row(
            batch, batch_id=f"eb_mix_term_{n}", user_id="userA", status=COMPLETE,
            items=[(f"f_mix_term_{n}", "Observed", PENDING)],
            created_at=f"2020-04-01T00:00:{n:02d}+00:00",
        )

    resumed_ids = {r["batch_id"] for r in batch.resume_incomplete_batches()}
    ordinary_seen = {bid for bid in resumed_ids if bid.startswith("eb_mix_ord_")}
    terminal_seen = {bid for bid in resumed_ids if bid.startswith("eb_mix_term_")}
    assert len(ordinary_seen) == 8
    assert len(terminal_seen) == 5


def test_recovery_candidate_union_deduplicates_batch_ids(rig, monkeypatch):
    """A batch that (due to a race between the two separate selection
    reads) appears in BOTH candidate collections must be processed at most
    once per sweep."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_race", source="userA"))
    _insert_batch_row(
        batch, batch_id="eb_race", user_id="userA", status=PENDING,
        items=[("f_race", "Observed", PENDING)],
    )

    original_select_terminal = batch._select_stale_terminal_recovery_candidates

    def racing_select_terminal():
        # Simulate eb_race ALSO surfacing via the stale-terminal query —
        # e.g. its status flipped and flipped back between the two reads.
        return list(original_select_terminal()) + [{"batch_id": "eb_race"}]

    monkeypatch.setattr(
        batch, "_select_stale_terminal_recovery_candidates", racing_select_terminal,
    )

    run_batch_calls = []
    original_run_batch = batch._run_batch

    def counting_run_batch(batch_id, **kwargs):
        run_batch_calls.append(batch_id)
        return original_run_batch(batch_id, **kwargs)

    monkeypatch.setattr(batch, "_run_batch", counting_run_batch)

    results = batch.resume_incomplete_batches()
    result_ids = [r["batch_id"] for r in results]
    assert result_ids.count("eb_race") == 1
    assert run_batch_calls.count("eb_race") == 1
    assert store.get_fact("f_race") is None


def test_stale_terminal_recovery_cursor_advances_deterministically(rig, monkeypatch):
    """Repeated sweeps advance deterministically through the stale-terminal
    candidate set — every candidate is inspected exactly once, across
    ceil(N / limit) sweeps, never revisited, never skipped."""
    batch, coordinator, store, embeddings, ngram = rig
    monkeypatch.setattr(ebc_module, "_RECOVERY_SWEEP_LIMIT", 5)

    total = 12
    fact_ids = []
    for n in range(total):
        fid = f"f_cursor_{n}"
        fact_ids.append(fid)
        store.store_fact(_fact(fid, source="userA"))
        _insert_batch_row(
            batch, batch_id=f"eb_cursor_{n}", user_id="userA", status=COMPLETE,
            items=[(fid, "Observed", PENDING)],
            created_at=f"2020-05-01T00:00:{n:02d}+00:00",
        )

    seen_order = []
    for _ in range(3):  # ceil(12 / 5) == 3
        sweep_ids = [r["batch_id"] for r in batch.resume_incomplete_batches()]
        seen_order.append(sweep_ids)

    all_seen = [bid for sweep in seen_order for bid in sweep]
    assert sorted(all_seen) == sorted(f"eb_cursor_{n}" for n in range(total))
    assert len(all_seen) == len(set(all_seen))  # never revisited
    assert [len(s) for s in seen_order] == [5, 5, 2]  # deterministic, bounded
    for fid in fact_ids:
        assert store.get_fact(fid) is None


def test_split_recovery_queries_preserve_concurrent_status_updates(rig, monkeypatch):
    """A candidate whose status changes between selection and
    reconciliation (a concurrent transaction finalizing it for real) must
    not be clobbered back to the stale value, and must not be executed
    twice."""
    batch, coordinator, store, embeddings, ngram = rig
    store.store_fact(_fact("f_split_race", source="userA"))
    _insert_batch_row(
        batch, batch_id="eb_split_race", user_id="userA", status=COMPLETE,
        items=[("f_split_race", "Observed", PENDING)],
    )

    original_load_batch = batch._load_batch
    race_done = {"done": False}

    def racing_load_batch(bid):
        result = original_load_batch(bid)
        if bid == "eb_split_race" and not race_done["done"]:
            race_done["done"] = True
            with batch._jobs_db() as conn:
                conn.execute(
                    "UPDATE erasure_batches SET status = ?, updated_at = ? "
                    "WHERE batch_id = ?",
                    (SUBJECT_CONFLICT, _now(), bid),
                )
                conn.commit()
        return result

    monkeypatch.setattr(batch, "_load_batch", racing_load_batch)

    results = batch.resume_incomplete_batches()
    assert [r["batch_id"] for r in results].count("eb_split_race") <= 1

    with batch._jobs_db() as conn:
        final = conn.execute(
            "SELECT status FROM erasure_batches WHERE batch_id = ?",
            ("eb_split_race",),
        ).fetchone()
    # The concurrent write is never clobbered back to the stale COMPLETE
    # this reconciliation started from.
    assert final["status"] != COMPLETE
