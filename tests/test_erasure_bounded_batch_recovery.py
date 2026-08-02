"""Bounded batch startup recovery over Titan's durable batch saga."""

from __future__ import annotations

import sqlite3

import pytest

from core.embedding_store import EmbeddingStore
from core.erasure_batch_coordinator import (
    COMPLETE,
    CRITICAL_COMPLIANCE_VIOLATION,
    FAILED,
    PENDING,
    BatchErasureCoordinator,
)
from core.erasure_bounded_batch_recovery import (
    _select_batch_candidates_bounded,
    resume_batch_jobs_bounded,
)
from core.erasure_coordinator import ErasureCoordinator
from core.erasure_startup_recovery import RecoveryDomain
from core.memory import make_store
from core.ngram_index import NGramIndex


@pytest.fixture
def rig(tmp_path):
    store = make_store(str(tmp_path / "facts.db"))
    embeddings = EmbeddingStore(str(tmp_path / "embeddings.db"))
    embeddings.ensure_table()
    ngram = NGramIndex(str(tmp_path / "ngram.db"))
    single = ErasureCoordinator(
        store=store,
        embedding_store=embeddings,
        ngram_index=ngram,
    )
    batch = BatchErasureCoordinator(store=store, coordinator=single)
    return batch, store


def _seed_batch(batch: BatchErasureCoordinator, store, suffix: str) -> str:
    user_id = f"user-{suffix}"
    store.store_fact(
        {
            "fact_id": f"fact-{suffix}",
            "claim": f"claim for {suffix}",
            "source": user_id,
            "confidence": 0.9,
        }
    )
    return batch._create_batch_snapshot(
        user_id=user_id,
        reason="startup_recovery_test",
        actor="test",
        force=False,
        scope=None,
        idempotency_key=None,
        actor_capability="reader",
        request_fingerprint=f"fingerprint-{suffix}",
    )


def test_bounded_batch_recovery_processes_selected_prefix(rig) -> None:
    batch, store = rig
    ids = [_seed_batch(batch, store, suffix) for suffix in ("a", "b", "c")]

    receipt, stopped = resume_batch_jobs_bounded(
        max_batches=2,
        deadline_monotonic=1.0,
        monotonic=lambda: 0.0,
        coordinator=batch,
    )

    assert receipt.domain is RecoveryDomain.BATCH
    assert receipt.selected == 2
    assert receipt.attempted == 2
    assert receipt.completed == 2
    assert receipt.partial == 0
    assert receipt.failed == 0
    assert receipt.skipped == 0
    assert receipt.remaining_backlog == 1
    assert stopped is False

    remaining = batch.resume_incomplete_batches()
    assert len(remaining) == 1
    assert remaining[0]["outcome"] == COMPLETE
    assert {batch.get_batch_report(batch_id)["outcome"] for batch_id in ids} == {
        COMPLETE
    }


def test_expired_deadline_selects_without_attempting(rig) -> None:
    batch, store = rig
    _seed_batch(batch, store, "deadline-a")
    _seed_batch(batch, store, "deadline-b")

    receipt, stopped = resume_batch_jobs_bounded(
        max_batches=2,
        deadline_monotonic=1.0,
        monotonic=lambda: 1.0,
        coordinator=batch,
    )

    assert receipt.selected == 2
    assert receipt.attempted == 0
    assert receipt.remaining_backlog >= 2
    assert stopped is True


def test_deadline_stops_between_batches(rig) -> None:
    batch, store = rig
    _seed_batch(batch, store, "between-a")
    _seed_batch(batch, store, "between-b")
    readings = iter((0.0, 2.0))

    receipt, stopped = resume_batch_jobs_bounded(
        max_batches=2,
        deadline_monotonic=1.0,
        monotonic=lambda: next(readings),
        coordinator=batch,
    )

    assert receipt.selected == 2
    assert receipt.attempted == 1
    assert receipt.completed == 1
    assert receipt.remaining_backlog >= 1
    assert stopped is True


def test_stale_terminal_candidate_gets_fair_first_slot(rig) -> None:
    batch, store = rig
    ordinary_id = _seed_batch(batch, store, "ordinary")
    stale_id = _seed_batch(batch, store, "stale")
    with batch._jobs_db() as conn:
        conn.execute(
            "UPDATE erasure_batches SET status = ? WHERE batch_id = ?",
            (COMPLETE, stale_id),
        )
        conn.execute(
            "UPDATE erasure_batch_items SET status = ? WHERE batch_id = ?",
            (FAILED, stale_id),
        )

    selected = _select_batch_candidates_bounded(batch, 1)

    assert selected == [(stale_id, True)]
    assert ordinary_id != stale_id


def test_lost_batch_claim_is_skipped_and_remains_backlog(
    rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    batch, store = rig
    _seed_batch(batch, store, "lost-claim")
    monkeypatch.setattr(
        batch,
        "_run_batch",
        lambda batch_id, *, wait_if_running=False: None,
    )

    receipt, stopped = resume_batch_jobs_bounded(
        max_batches=1,
        deadline_monotonic=1.0,
        monotonic=lambda: 0.0,
        coordinator=batch,
    )

    assert receipt.attempted == 1
    assert receipt.skipped == 1
    assert receipt.remaining_backlog == 1
    assert stopped is False


def test_critical_compliance_is_failed_not_success(
    rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    batch, store = rig
    _seed_batch(batch, store, "critical")
    monkeypatch.setattr(
        batch,
        "_run_batch",
        lambda batch_id, *, wait_if_running=False: {
            "batch_id": batch_id,
            "outcome": COMPLETE,
            "success": False,
            "compliance_status": CRITICAL_COMPLIANCE_VIOLATION,
            "critical_compliance_violation": True,
        },
    )

    receipt, _ = resume_batch_jobs_bounded(
        max_batches=1,
        deadline_monotonic=1.0,
        monotonic=lambda: 0.0,
        coordinator=batch,
    )

    assert receipt.completed == 0
    assert receipt.failed == 1
    assert receipt.error_codes == ("batch_compliance_violation",)
    assert receipt.remaining_backlog == 0


def test_failed_batch_is_counted_once(rig, monkeypatch: pytest.MonkeyPatch) -> None:
    batch, store = rig
    _seed_batch(batch, store, "failed")
    monkeypatch.setattr(
        batch,
        "_run_batch",
        lambda batch_id, *, wait_if_running=False: {
            "batch_id": batch_id,
            "outcome": FAILED,
            "success": False,
            "compliance_status": None,
            "critical_compliance_violation": False,
        },
    )

    receipt, _ = resume_batch_jobs_bounded(
        max_batches=1,
        deadline_monotonic=1.0,
        monotonic=lambda: 0.0,
        coordinator=batch,
    )

    assert receipt.failed == 1
    assert receipt.error_codes == ("batch_recovery_failed",)
    assert receipt.remaining_backlog == 0


def test_unknown_outcome_propagates_as_contract_failure(
    rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    batch, store = rig
    _seed_batch(batch, store, "unknown")
    monkeypatch.setattr(
        batch,
        "_run_batch",
        lambda batch_id, *, wait_if_running=False: {
            "batch_id": batch_id,
            "outcome": "NEW_UNKNOWN_OUTCOME",
            "success": False,
            "compliance_status": None,
            "critical_compliance_violation": False,
        },
    )

    with pytest.raises(ValueError, match="unsupported batch recovery outcome"):
        resume_batch_jobs_bounded(
            max_batches=1,
            deadline_monotonic=1.0,
            monotonic=lambda: 0.0,
            coordinator=batch,
        )


def test_database_error_propagates_to_aggregate_failure_receipt(
    rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    batch, store = rig
    _seed_batch(batch, store, "db-failure")

    def _raise(batch_id: str, *, wait_if_running: bool = False):
        raise sqlite3.DatabaseError("batch schema unavailable")

    monkeypatch.setattr(batch, "_run_batch", _raise)

    with pytest.raises(sqlite3.DatabaseError, match="schema unavailable"):
        resume_batch_jobs_bounded(
            max_batches=1,
            deadline_monotonic=1.0,
            monotonic=lambda: 0.0,
            coordinator=batch,
        )


def test_bounds_and_clock_validation_are_fail_closed(rig) -> None:
    batch, _ = rig
    with pytest.raises(ValueError, match="non-negative integer"):
        resume_batch_jobs_bounded(
            max_batches=True,
            deadline_monotonic=1.0,
            coordinator=batch,
        )
    with pytest.raises(ValueError, match="finite number"):
        resume_batch_jobs_bounded(
            max_batches=1,
            deadline_monotonic=float("nan"),
            coordinator=batch,
        )
