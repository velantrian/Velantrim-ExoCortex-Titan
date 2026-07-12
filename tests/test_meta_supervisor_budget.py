"""Regression tests for the MetaSupervisor memory-budget channel."""

from __future__ import annotations

import asyncio

from core.memory_budget import BudgetStatus, get_budget_planner
from core.meta_supervisor import MetaSupervisor, SystemMode


def _budget_status(utilization: float) -> BudgetStatus:
    return BudgetStatus(
        fact_count=86,
        limit=100,
        utilization=utilization,
        action="warn",
    )


def test_budget_planner_snapshot_delegates_to_live_evaluation(monkeypatch) -> None:
    monkeypatch.setattr(
        "core.memory_budget.evaluate_budget",
        lambda: _budget_status(0.86),
    )

    planner = get_budget_planner()

    assert planner.fill_ratio == 0.86


def test_meta_supervisor_collects_budget_and_degrades(monkeypatch) -> None:
    # Keep the test focused on the budget channel. With no store, MHI remains
    # healthy; budget pressure alone must still cause HEALTHY -> DEGRADED.
    monkeypatch.setattr("core.memory._GLOBAL_STORE", None)
    monkeypatch.setattr(
        "core.memory_budget.evaluate_budget",
        lambda: _budget_status(0.86),
    )

    supervisor = MetaSupervisor()
    supervisor._collect_mhi()

    assert supervisor.snapshot().budget_pressure == 0.86

    asyncio.run(supervisor._evaluate(elapsed=0.0))

    assert supervisor.mode is SystemMode.DEGRADED
