"""Bounded single-fact startup recovery over the real durable coordinator."""

from __future__ import annotations

import sqlite3

import pytest

from core.embedding_store import EmbeddingStore
from core.erasure_bounded_recovery import resume_single_fact_jobs_bounded
from core.erasure_coordinator import COMPLETE, FAILED, ErasureCoordinator
from core.erasure_startup_recovery import RecoveryDomain
from core.memory import make_store
from core.ngram_index import NGramIndex


@pytest.fixture
def rig(tmp_path):
    store = make_store(str(tmp_path / "facts.db"))
    embeddings = EmbeddingStore(str(tmp_path / "embeddings.db"))
    embeddings.ensure_table()
    ngram = NGramIndex(str(tmp_path / "ngram.db"))
    coordinator = ErasureCoordinator(
        store=store,
        embedding_store=embeddings,
        ngram_index=ngram,
    )
    return coordinator, store


def _seed_pending(coordinator: ErasureCoordinator, store, fact_id: str) -> str:
    store.store_fact(
        {
            "fact_id": fact_id,
            "claim": f"claim for {fact_id}",
            "source": "test",
            "confidence": 0.9,
        }
    )
    return coordinator._get_or_create_job(
        fact_id,
        reason="startup_recovery_test",
        actor="test",
        subject_user_id=None,
    )


def test_bounded_recovery_processes_only_selected_prefix(rig) -> None:
    coordinator, store = rig
    fact_ids = ("bounded-a", "bounded-b", "bounded-c")
    for fact_id in fact_ids:
        _seed_pending(coordinator, store, fact_id)

    receipt, stopped = resume_single_fact_jobs_bounded(
        max_jobs=2,
        deadline_monotonic=1.0,
        monotonic=lambda: 0.0,
        coordinator=coordinator,
    )

    assert receipt.domain is RecoveryDomain.SINGLE_FACT
    assert receipt.selected == 2
    assert receipt.attempted == 2
    assert receipt.completed == 2
    assert receipt.partial == 0
    assert receipt.failed == 0
    assert receipt.skipped == 0
    assert receipt.remaining_backlog == 1
    assert stopped is False
    assert sum(store.get_fact(fid) is None for fid in fact_ids) == 2

    remaining = coordinator.resume_incomplete_jobs()
    assert len(remaining) == 1
    assert remaining[0]["outcome"] == COMPLETE


def test_expired_deadline_selects_but_attempts_nothing(rig) -> None:
    coordinator, store = rig
    _seed_pending(coordinator, store, "deadline-a")
    _seed_pending(coordinator, store, "deadline-b")

    receipt, stopped = resume_single_fact_jobs_bounded(
        max_jobs=2,
        deadline_monotonic=1.0,
        monotonic=lambda: 1.0,
        coordinator=coordinator,
    )

    assert receipt.selected == 2
    assert receipt.attempted == 0
    assert receipt.remaining_backlog >= 2
    assert stopped is True


def test_deadline_stops_between_jobs_and_keeps_unattempted_backlog(rig) -> None:
    coordinator, store = rig
    _seed_pending(coordinator, store, "between-a")
    _seed_pending(coordinator, store, "between-b")
    readings = iter((0.0, 2.0))

    receipt, stopped = resume_single_fact_jobs_bounded(
        max_jobs=2,
        deadline_monotonic=1.0,
        monotonic=lambda: next(readings),
        coordinator=coordinator,
    )

    assert receipt.selected == 2
    assert receipt.attempted == 1
    assert receipt.completed == 1
    assert receipt.remaining_backlog >= 1
    assert stopped is True


def test_failed_report_is_counted_once_not_duplicated_as_backlog(
    rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    coordinator, store = rig
    _seed_pending(coordinator, store, "failed-a")

    monkeypatch.setattr(
        coordinator,
        "_run_job",
        lambda job_id, *, wait_if_running: {
            "job_id": job_id,
            "outcome": FAILED,
        },
    )

    receipt, stopped = resume_single_fact_jobs_bounded(
        max_jobs=1,
        deadline_monotonic=1.0,
        monotonic=lambda: 0.0,
        coordinator=coordinator,
    )

    assert receipt.attempted == 1
    assert receipt.failed == 1
    assert receipt.error_codes == ("single_fact_recovery_failed",)
    assert receipt.remaining_backlog == 0
    assert stopped is False


def test_lost_claim_is_skipped_and_remains_backlog(
    rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    coordinator, store = rig
    _seed_pending(coordinator, store, "skipped-a")
    monkeypatch.setattr(
        coordinator,
        "_run_job",
        lambda job_id, *, wait_if_running: None,
    )

    receipt, stopped = resume_single_fact_jobs_bounded(
        max_jobs=1,
        deadline_monotonic=1.0,
        monotonic=lambda: 0.0,
        coordinator=coordinator,
    )

    assert receipt.attempted == 1
    assert receipt.skipped == 1
    assert receipt.remaining_backlog == 1
    assert stopped is False


def test_unexpected_database_error_propagates_to_future_failure_receipt(
    rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    coordinator, store = rig
    _seed_pending(coordinator, store, "observer-failure")

    def _raise(job_id: str, *, wait_if_running: bool):
        raise sqlite3.DatabaseError("jobs schema unavailable")

    monkeypatch.setattr(coordinator, "_run_job", _raise)

    with pytest.raises(sqlite3.DatabaseError, match="schema unavailable"):
        resume_single_fact_jobs_bounded(
            max_jobs=1,
            deadline_monotonic=1.0,
            monotonic=lambda: 0.0,
            coordinator=coordinator,
        )


def test_unknown_outcome_propagates_as_contract_failure(
    rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    coordinator, store = rig
    _seed_pending(coordinator, store, "unknown-outcome")
    monkeypatch.setattr(
        coordinator,
        "_run_job",
        lambda job_id, *, wait_if_running: {
            "job_id": job_id,
            "outcome": "UNKNOWN_NEW_STATE",
        },
    )

    with pytest.raises(ValueError, match="unsupported single-fact recovery outcome"):
        resume_single_fact_jobs_bounded(
            max_jobs=1,
            deadline_monotonic=1.0,
            monotonic=lambda: 0.0,
            coordinator=coordinator,
        )


def test_bounds_validation_is_fail_closed(rig) -> None:
    coordinator, _ = rig
    with pytest.raises(ValueError, match="non-negative integer"):
        resume_single_fact_jobs_bounded(
            max_jobs=True,
            deadline_monotonic=1.0,
            coordinator=coordinator,
        )
    with pytest.raises(ValueError, match="non-negative integer"):
        resume_single_fact_jobs_bounded(
            max_jobs=-1,
            deadline_monotonic=1.0,
            coordinator=coordinator,
        )
    with pytest.raises(ValueError, match="finite number"):
        resume_single_fact_jobs_bounded(
            max_jobs=1,
            deadline_monotonic=float("nan"),
            coordinator=coordinator,
        )
