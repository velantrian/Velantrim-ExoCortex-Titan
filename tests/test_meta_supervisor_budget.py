"""Regression tests for the MetaSupervisor memory-budget channel."""

from __future__ import annotations

import asyncio
import importlib
from types import SimpleNamespace


def _memory_budget_module():
    """Resolve the live module after any import-isolation tests have run."""

    return importlib.import_module("core.memory_budget")


def _budget_status(utilization: float):
    memory_budget = _memory_budget_module()
    return memory_budget.BudgetStatus(
        fact_count=86,
        limit=100,
        utilization=utilization,
        action="warn",
    )


def test_budget_planner_snapshot_delegates_to_live_evaluation(monkeypatch) -> None:
    memory_budget = _memory_budget_module()
    monkeypatch.setattr(
        memory_budget,
        "evaluate_budget",
        lambda: _budget_status(0.86),
    )

    planner = memory_budget.get_budget_planner()

    assert planner.fill_ratio == 0.86


def test_meta_supervisor_collects_budget_and_degrades(monkeypatch) -> None:
    # Keep the test focused on the budget channel. Resolve all modules at test
    # execution time because the import-isolation suite may replace sys.modules
    # entries before this test is reached in the full run.
    memory = importlib.import_module("core.memory")
    event_bus = importlib.import_module("core.event_bus")
    memory_budget = _memory_budget_module()
    meta_supervisor = importlib.import_module("core.meta_supervisor")

    monkeypatch.setattr(memory, "_GLOBAL_STORE", None)
    monkeypatch.setattr(
        event_bus,
        "get_event_bus",
        lambda: SimpleNamespace(_dlq=[]),
    )
    monkeypatch.setattr(
        memory_budget,
        "evaluate_budget",
        lambda: _budget_status(0.86),
    )

    supervisor = meta_supervisor.MetaSupervisor()
    supervisor._collect_mhi()

    snapshot = supervisor.snapshot()
    assert snapshot.budget_pressure == 0.86
    assert snapshot.dlq_size == 0

    asyncio.run(supervisor._evaluate(elapsed=0.0))

    assert supervisor.mode is meta_supervisor.SystemMode.DEGRADED
