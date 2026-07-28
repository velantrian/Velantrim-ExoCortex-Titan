"""H1 regression: MetaSupervisor budget-pressure signal must be live.

Before the fix, `_collect_mhi()` imported a non-existent
`core.memory_budget.get_budget_planner`. The ImportError was swallowed, so
`_budget_cache` was pinned at 0.0 forever and the `budget_warn` / `budget_block`
branches in `_evaluate()` were unreachable — of the three immune-system signals
(MHI, DLQ, budget) only two were alive.

These tests pin the repaired behaviour: the ratio is collected from the real
`evaluate_budget()`, it drives both transitions, a collection failure stays
non-fatal but becomes visible, and the value stored in the snapshot is the
utilization ratio rather than the absolute fact count.
"""
from __future__ import annotations

import logging

import pytest

from core.memory_budget import BudgetStatus
from core.meta_supervisor import (
    MetaSupervisor,
    SupervisorConfig,
    SystemMode,
)


def _budget(utilization: float, *, fact_count: int = 0, limit: int = 100_000) -> BudgetStatus:
    """A BudgetStatus whose utilization is deliberately unrelated to fact_count.

    Keeping them independent is what lets the snapshot test below distinguish
    "stored the ratio" from "stored the count".
    """
    return BudgetStatus(
        fact_count=fact_count,
        limit=limit,
        utilization=utilization,
        action="ok",
    )


@pytest.fixture
def supervisor() -> MetaSupervisor:
    # Explicit thresholds so the test does not depend on the shipped defaults.
    return MetaSupervisor(config=SupervisorConfig(budget_warn=0.85, budget_block=0.90))


def _collect(sup: MetaSupervisor, monkeypatch: pytest.MonkeyPatch, status: BudgetStatus) -> None:
    """Run one metric-collection pass with a stubbed budget and neutral MHI/DLQ."""
    import core.memory_budget as budget_mod

    monkeypatch.setattr(budget_mod, "evaluate_budget", lambda: status)
    # Neutralise the other two signals so only budget can move the mode.
    monkeypatch.setattr(sup, "_collect_mhi", sup._collect_mhi)
    sup._collect_mhi()
    sup._mhi_cache = 1.0
    sup._mhi_status_cache = "HEALTHY"
    sup._dlq_cache = 0


# ── the signal is actually collected ────────────────────────────────────────

def test_budget_utilization_is_collected_not_pinned_to_zero(
    supervisor: MetaSupervisor, monkeypatch: pytest.MonkeyPatch
):
    _collect(supervisor, monkeypatch, _budget(0.42))
    assert supervisor._budget_cache == pytest.approx(0.42)


def test_snapshot_stores_the_utilization_ratio_not_the_fact_count(
    supervisor: MetaSupervisor, monkeypatch: pytest.MonkeyPatch
):
    """budget_pressure must be the ratio, not the absolute count."""
    _collect(supervisor, monkeypatch, _budget(0.37, fact_count=37_000, limit=100_000))

    snap = supervisor.snapshot()
    assert snap.budget_pressure == pytest.approx(0.37)
    assert snap.budget_pressure != 37_000
    assert 0.0 <= snap.budget_pressure <= 1.0
    assert snap.to_dict()["budget_pressure"] == pytest.approx(0.37)


# ── the signal drives transitions ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_utilization_below_warn_keeps_supervisor_healthy(
    supervisor: MetaSupervisor, monkeypatch: pytest.MonkeyPatch
):
    _collect(supervisor, monkeypatch, _budget(0.50))
    await supervisor._evaluate(elapsed=1.0)
    assert supervisor.mode is SystemMode.HEALTHY


@pytest.mark.asyncio
async def test_utilization_above_warn_moves_healthy_to_degraded(
    supervisor: MetaSupervisor, monkeypatch: pytest.MonkeyPatch
):
    fired: list[str] = []
    sup = MetaSupervisor(
        config=SupervisorConfig(budget_warn=0.85, budget_block=0.90),
        on_degraded=lambda: fired.append("degraded"),
    )
    _collect(sup, monkeypatch, _budget(0.87))

    await sup._evaluate(elapsed=1.0)

    assert sup.mode is SystemMode.DEGRADED
    assert "budget" in sup.snapshot().last_action
    assert fired == ["degraded"]


@pytest.mark.asyncio
async def test_utilization_above_block_moves_degraded_to_safe_mode(
    monkeypatch: pytest.MonkeyPatch
):
    """budget > budget_block escalates DEGRADED → SAFE_MODE.

    MHI is held inside the degraded band (0.55: below mhi_healthy=0.60, above
    mhi_safe_mode=0.30) so the recovery branch does not pre-empt the escalation
    check — see test_degraded_recovery_currently_ignores_budget_pressure for why
    that ordering matters.
    """
    fired: list[str] = []
    sup = MetaSupervisor(
        config=SupervisorConfig(budget_warn=0.85, budget_block=0.90),
        on_safe_mode=lambda: fired.append("safe_mode"),
    )
    sup._mode = SystemMode.DEGRADED
    _collect(sup, monkeypatch, _budget(0.95))
    sup._mhi_cache = 0.55

    await sup._evaluate(elapsed=1.0)

    assert sup.mode is SystemMode.SAFE_MODE
    assert sup.is_safe_mode is True
    assert fired == ["safe_mode"]
    # The budget term is what carried the transition, so it must be reported.
    assert "budget=0.95" in sup.snapshot().last_action


@pytest.mark.asyncio
async def test_degraded_recovery_currently_ignores_budget_pressure(
    monkeypatch: pytest.MonkeyPatch
):
    """Documents observed behaviour, NOT an endorsement of it.

    `_evaluate()`'s DEGRADED branch recovers on `mhi >= mhi_healthy and
    dlq < dlq_warn` and returns before the escalation check. Budget pressure is
    not a term in that condition, so a store at 95% of its fact budget recovers
    to HEALTHY as long as MHI and DLQ look fine.

    Restoring the budget signal (H1) is what makes this reachable and therefore
    observable at all. Whether recovery *should* consider budget is a transition
    -semantics decision, deliberately left to a separate reviewed change rather
    than altered here. This test exists so the behaviour cannot change silently
    in either direction.
    """
    sup = MetaSupervisor(config=SupervisorConfig(budget_warn=0.85, budget_block=0.90))
    sup._mode = SystemMode.DEGRADED
    _collect(sup, monkeypatch, _budget(0.95))
    sup._mhi_cache = 1.0
    sup._dlq_cache = 0

    await sup._evaluate(elapsed=1.0)

    assert sup.mode is SystemMode.HEALTHY
    # The signal itself is live even though this branch ignores it.
    assert sup.snapshot().budget_pressure == pytest.approx(0.95)


@pytest.mark.asyncio
async def test_exact_threshold_is_not_enough_to_degrade(
    supervisor: MetaSupervisor, monkeypatch: pytest.MonkeyPatch
):
    """The comparison is strictly greater-than; the boundary itself is healthy."""
    _collect(supervisor, monkeypatch, _budget(0.85))
    await supervisor._evaluate(elapsed=1.0)
    assert supervisor.mode is SystemMode.HEALTHY


# ── failure stays non-fatal but observable ──────────────────────────────────

def test_evaluate_budget_failure_is_non_fatal_and_logged_visibly(
    supervisor: MetaSupervisor,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
):
    """A broken budget metric must not kill the heartbeat — but must be visible.

    The original defect was precisely a silent swallow, so DEBUG is not enough:
    at production LOG_LEVEL=INFO the failure has to still appear.
    """
    import core.memory_budget as budget_mod

    def boom() -> BudgetStatus:
        raise RuntimeError("store unavailable")

    monkeypatch.setattr(budget_mod, "evaluate_budget", boom)

    with caplog.at_level(logging.WARNING, logger="velantrim.meta_supervisor"):
        supervisor._collect_mhi()  # must not raise

    assert supervisor._budget_cache == 0.0
    messages = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("budget pressure" in m for m in messages), messages
    assert any("store unavailable" in m for m in messages), messages


def test_collector_does_not_reference_a_planner_object():
    """The dead `get_budget_planner()` / `.fill_ratio` path must stay gone."""
    import inspect

    import core.meta_supervisor as mod

    source = inspect.getsource(mod)
    assert "get_budget_planner" not in source
    assert "fill_ratio" not in source


def test_supervisor_collection_performs_no_writes(monkeypatch: pytest.MonkeyPatch):
    """MetaSupervisor is read-only; collecting the budget must not write.

    evaluate_budget() reaches the store through count_facts(), which is a plain
    SELECT COUNT(*). Assert the collector issues no mutating SQL.
    """
    import core.memory_budget as budget_mod

    executed: list[str] = []

    def fake_count() -> int:
        executed.append("SELECT COUNT(*) FROM facts")
        return 10

    monkeypatch.setattr(budget_mod, "count_facts", fake_count)

    sup = MetaSupervisor()
    sup._collect_mhi()

    assert executed, "the budget metric should have queried the store"
    forbidden = ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE")
    for statement in executed:
        assert not any(word in statement.upper() for word in forbidden), statement
