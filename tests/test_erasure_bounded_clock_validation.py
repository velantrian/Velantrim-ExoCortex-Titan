from __future__ import annotations

import pytest

import core.erasure_bounded_recovery as bounded


class _NoExecutionCoordinator:
    def _reconcile_completed_job_from_tombstone(self, job_id: str):
        raise AssertionError("invalid clock must fail before reconciliation")

    def _run_job(self, job_id: str, *, wait_if_running: bool):
        raise AssertionError("invalid clock must fail before recovery execution")


def test_non_finite_clock_result_fails_before_job_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    coordinator = _NoExecutionCoordinator()
    monkeypatch.setattr(
        bounded,
        "_select_resumable_job_ids",
        lambda active, limit: ["candidate-1"],
    )

    with pytest.raises(ValueError, match="monotonic clock result"):
        bounded.resume_single_fact_jobs_bounded(
            max_jobs=1,
            deadline_monotonic=1.0,
            monotonic=lambda: float("nan"),
            coordinator=coordinator,  # type: ignore[arg-type]
        )
