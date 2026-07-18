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
    BatchErasureCoordinator,
)
from core.erasure_coordinator import ErasureCoordinator
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
