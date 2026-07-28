"""MetaSupervisor budget pressure: live signal *and* correct transitions.

Two rounds of history:

PR #66 fixed the collector — it had imported a non-existent
`core.memory_budget.get_budget_planner` and swallowed the ImportError, pinning
`_budget_cache` at 0.0 so the `budget_warn` / `budget_block` branches were
unreachable.

Post-merge review then found that making the signal live exposed three further
defects, all fixed here:

  • `_evaluate()`'s DEGRADED branch checked recovery *before* escalation and
    omitted budget from the recovery condition. A store above `budget_block`
    therefore oscillated HEALTHY↔DEGRADED forever and never reached SAFE_MODE.
  • `ENABLE_MEMORY_BUDGET=0` (the default) was ignored, so a feature that
    `check_before_write()` treats as disabled could still drive the system into
    DEGRADED/SAFE_MODE.
  • `evaluate_budget()` logs WARNING/CRITICAL at its thresholds, and the 10s
    heartbeat called it unconditionally — six duplicate high-severity messages a
    minute on a persistently full store.

Transition truth table pinned below:

    HEALTHY  → SAFE_MODE  if mhi < mhi_safe_mode or dlq > dlq_safe_mode
                             or budget > budget_block
    HEALTHY  → DEGRADED   elif mhi < mhi_degraded or dlq > dlq_warn
                             or budget > budget_warn
    DEGRADED → SAFE_MODE  if mhi < mhi_safe_mode or dlq > dlq_safe_mode
                             or budget > budget_block          (checked FIRST)
    DEGRADED → HEALTHY    elif mhi >= mhi_healthy and dlq < dlq_warn
                             and budget <= budget_warn
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


def _cfg() -> SupervisorConfig:
    """Explicit thresholds so tests do not depend on the shipped defaults."""
    return SupervisorConfig(budget_warn=0.85, budget_block=0.90)


@pytest.fixture
def supervisor() -> MetaSupervisor:
    return MetaSupervisor(config=_cfg())


def _collect(sup: MetaSupervisor, monkeypatch: pytest.MonkeyPatch, status: BudgetStatus) -> None:
    """Run one metric-collection pass with a stubbed budget and neutral MHI/DLQ."""
    import core.memory_budget as budget_mod

    # The collector now gates on the feature flag and asks for a quiet read;
    # accept **kwargs so the stub cannot silently diverge from the real call.
    monkeypatch.setattr(budget_mod, "is_memory_budget_enabled", lambda: True)
    monkeypatch.setattr(budget_mod, "evaluate_budget", lambda **kw: status)
    sup._collect_mhi()
    # Neutralise the other two signals so only budget can move the mode.
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


def test_collector_does_not_reference_a_planner_object():
    """The dead `get_budget_planner()` / `.fill_ratio` path must stay gone."""
    import inspect

    import core.meta_supervisor as mod

    source = inspect.getsource(mod)
    assert "get_budget_planner" not in source
    assert "fill_ratio" not in source


def test_supervisor_collection_performs_no_writes(monkeypatch: pytest.MonkeyPatch):
    """MetaSupervisor is read-only; collecting the budget must not write."""
    import core.memory_budget as budget_mod

    executed: list[str] = []

    def fake_count() -> int:
        executed.append("SELECT COUNT(*) FROM facts")
        return 10

    monkeypatch.setattr(budget_mod, "is_memory_budget_enabled", lambda: True)
    monkeypatch.setattr(budget_mod, "count_facts", fake_count)

    MetaSupervisor()._collect_mhi()

    assert executed, "the budget metric should have queried the store"
    forbidden = ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE")
    for statement in executed:
        assert not any(word in statement.upper() for word in forbidden), statement


# ── the feature flag is honoured ────────────────────────────────────────────

def test_disabled_memory_budget_keeps_the_signal_neutral(monkeypatch: pytest.MonkeyPatch):
    """ENABLE_MEMORY_BUDGET=0 must not let budget drive the health signal.

    `check_before_write()` returns without enforcing when the flag is off, so
    feeding the same number into mode transitions would mean a disabled feature
    pushes the system to DEGRADED/SAFE_MODE.
    """
    import core.memory_budget as budget_mod

    called: list[str] = []

    def spy(**kwargs) -> BudgetStatus:
        called.append("evaluated")
        return _budget(0.99)

    monkeypatch.setattr(budget_mod, "is_memory_budget_enabled", lambda: False)
    monkeypatch.setattr(budget_mod, "evaluate_budget", spy)

    sup = MetaSupervisor(config=_cfg())
    sup._collect_mhi()

    assert sup._budget_cache == 0.0
    assert called == [], "a disabled feature should not even be evaluated"


@pytest.mark.asyncio
async def test_disabled_memory_budget_cannot_trigger_degraded(monkeypatch: pytest.MonkeyPatch):
    import core.memory_budget as budget_mod

    monkeypatch.setattr(budget_mod, "is_memory_budget_enabled", lambda: False)
    monkeypatch.setattr(budget_mod, "evaluate_budget", lambda **kw: _budget(0.99))

    sup = MetaSupervisor(config=_cfg())
    sup._collect_mhi()
    sup._mhi_cache = 1.0
    sup._dlq_cache = 0

    await sup._evaluate(elapsed=1.0)

    assert sup.mode is SystemMode.HEALTHY


def test_collection_asks_for_a_quiet_budget_read(monkeypatch: pytest.MonkeyPatch):
    """The 10s heartbeat must not re-emit evaluate_budget's threshold logs.

    evaluate_budget() logs WARNING/CRITICAL at its thresholds — written for the
    write path, once per write. Polled every heartbeat it becomes six duplicate
    high-severity lines a minute, drowning real alerts.
    """
    import core.memory_budget as budget_mod

    seen: list[dict] = []

    def spy(**kwargs) -> BudgetStatus:
        seen.append(kwargs)
        return _budget(0.5)

    monkeypatch.setattr(budget_mod, "is_memory_budget_enabled", lambda: True)
    monkeypatch.setattr(budget_mod, "evaluate_budget", spy)

    MetaSupervisor(config=_cfg())._collect_mhi()

    assert seen == [{"quiet": True}], seen


def test_quiet_evaluate_budget_suppresses_only_logging(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    """quiet=True changes logging, never the returned value."""
    import core.memory_budget as budget_mod

    monkeypatch.setattr(budget_mod, "count_facts", lambda: 10_000_000)

    with caplog.at_level(logging.WARNING, logger="core.memory_budget"):
        quiet = budget_mod.evaluate_budget(quiet=True)
    assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="core.memory_budget"):
        loud = budget_mod.evaluate_budget()
    assert [r for r in caplog.records if r.levelno >= logging.WARNING] != []

    assert quiet.to_dict() == loud.to_dict()


# ── HEALTHY transitions ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_utilization_below_warn_keeps_supervisor_healthy(
    supervisor: MetaSupervisor, monkeypatch: pytest.MonkeyPatch
):
    _collect(supervisor, monkeypatch, _budget(0.50))
    await supervisor._evaluate(elapsed=1.0)
    assert supervisor.mode is SystemMode.HEALTHY


@pytest.mark.asyncio
async def test_exact_threshold_is_not_enough_to_degrade(
    supervisor: MetaSupervisor, monkeypatch: pytest.MonkeyPatch
):
    """The comparison is strictly greater-than; the boundary itself is healthy."""
    _collect(supervisor, monkeypatch, _budget(0.85))
    await supervisor._evaluate(elapsed=1.0)
    assert supervisor.mode is SystemMode.HEALTHY


@pytest.mark.asyncio
async def test_utilization_above_warn_moves_healthy_to_degraded(
    monkeypatch: pytest.MonkeyPatch
):
    fired: list[str] = []
    sup = MetaSupervisor(config=_cfg(), on_degraded=lambda: fired.append("degraded"))
    _collect(sup, monkeypatch, _budget(0.87))

    await sup._evaluate(elapsed=1.0)

    assert sup.mode is SystemMode.DEGRADED
    assert "budget" in sup.snapshot().last_action
    assert fired == ["degraded"]


@pytest.mark.asyncio
async def test_utilization_above_block_moves_healthy_straight_to_safe_mode(
    monkeypatch: pytest.MonkeyPatch
):
    """budget > budget_block escalates directly, even with MHI and DLQ healthy.

    Previously the HEALTHY branch omitted budget from its SAFE_MODE condition, so
    an over-budget store could only reach DEGRADED — and then oscillated back.
    """
    fired: list[str] = []
    sup = MetaSupervisor(config=_cfg(), on_safe_mode=lambda: fired.append("safe_mode"))
    _collect(sup, monkeypatch, _budget(0.95))

    await sup._evaluate(elapsed=1.0)

    assert sup.mode is SystemMode.SAFE_MODE
    assert sup.is_safe_mode is True
    assert fired == ["safe_mode"]
    assert "budget=0.95" in sup.snapshot().last_action


# ── DEGRADED transitions: escalation before recovery ────────────────────────

@pytest.mark.asyncio
async def test_utilization_above_block_moves_degraded_to_safe_mode(
    monkeypatch: pytest.MonkeyPatch
):
    """Escalation is evaluated before recovery, so healthy MHI/DLQ cannot mask it."""
    fired: list[str] = []
    sup = MetaSupervisor(config=_cfg(), on_safe_mode=lambda: fired.append("safe_mode"))
    sup._mode = SystemMode.DEGRADED
    _collect(sup, monkeypatch, _budget(0.95))

    await sup._evaluate(elapsed=1.0)

    assert sup.mode is SystemMode.SAFE_MODE
    assert fired == ["safe_mode"]
    assert "budget=0.95" in sup.snapshot().last_action


@pytest.mark.asyncio
async def test_warned_budget_blocks_recovery_to_healthy(monkeypatch: pytest.MonkeyPatch):
    """Between warn and block: no escalation, but no recovery either.

    This is the case the removed test used to pin the wrong way round — it
    asserted that a store at 95% recovered to HEALTHY. It must now stay DEGRADED.
    """
    fired: list[str] = []
    sup = MetaSupervisor(config=_cfg(), on_recovery=lambda: fired.append("recovery"))
    sup._mode = SystemMode.DEGRADED
    _collect(sup, monkeypatch, _budget(0.88))

    await sup._evaluate(elapsed=1.0)

    assert sup.mode is SystemMode.DEGRADED, "high budget must not satisfy recovery"
    assert fired == []


@pytest.mark.asyncio
async def test_budget_below_warn_allows_recovery(monkeypatch: pytest.MonkeyPatch):
    fired: list[str] = []
    sup = MetaSupervisor(config=_cfg(), on_recovery=lambda: fired.append("recovery"))
    sup._mode = SystemMode.DEGRADED
    _collect(sup, monkeypatch, _budget(0.40))

    await sup._evaluate(elapsed=1.0)

    assert sup.mode is SystemMode.HEALTHY
    assert fired == ["recovery"]
    assert "budget=0.40" in sup.snapshot().last_action


@pytest.mark.asyncio
async def test_exact_warn_threshold_permits_recovery(monkeypatch: pytest.MonkeyPatch):
    """Recovery requires budget <= budget_warn, so the boundary itself recovers."""
    sup = MetaSupervisor(config=_cfg())
    sup._mode = SystemMode.DEGRADED
    _collect(sup, monkeypatch, _budget(0.85))

    await sup._evaluate(elapsed=1.0)

    assert sup.mode is SystemMode.HEALTHY


# ── no oscillation ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_persistent_blocked_budget_reaches_safe_mode_and_stays(
    monkeypatch: pytest.MonkeyPatch
):
    """Repeated heartbeats must converge on SAFE_MODE, not flap.

    The defect: HEALTHY→DEGRADED, then DEGRADED's recovery branch ignored budget
    and returned to HEALTHY before the escalation check ever ran — one flip per
    heartbeat, forever, and SAFE_MODE unreachable for budget pressure alone.
    """
    safe_mode_calls: list[str] = []
    recovery_calls: list[str] = []
    sup = MetaSupervisor(
        config=_cfg(),
        on_safe_mode=lambda: safe_mode_calls.append("safe_mode"),
        on_recovery=lambda: recovery_calls.append("recovery"),
    )
    _collect(sup, monkeypatch, _budget(0.97))

    modes = []
    for _ in range(6):
        await sup._evaluate(elapsed=1.0)
        modes.append(sup.mode)

    assert modes[0] is SystemMode.SAFE_MODE
    assert all(m is SystemMode.SAFE_MODE for m in modes), modes
    assert recovery_calls == [], "must never bounce back to HEALTHY"
    # Callback fires once on entry, not on every heartbeat while already there.
    assert safe_mode_calls == ["safe_mode"]


@pytest.mark.asyncio
async def test_persistent_warned_budget_does_not_flap(monkeypatch: pytest.MonkeyPatch):
    """Between warn and block: settle in DEGRADED and stay there."""
    degraded_calls: list[str] = []
    recovery_calls: list[str] = []
    sup = MetaSupervisor(
        config=_cfg(),
        on_degraded=lambda: degraded_calls.append("degraded"),
        on_recovery=lambda: recovery_calls.append("recovery"),
    )
    _collect(sup, monkeypatch, _budget(0.87))

    modes = []
    for _ in range(6):
        await sup._evaluate(elapsed=1.0)
        modes.append(sup.mode)

    assert all(m is SystemMode.DEGRADED for m in modes), modes
    assert recovery_calls == []
    assert degraded_calls == ["degraded"]
    assert sup.snapshot().transition_count == 1, "no repeated transitions"


@pytest.mark.asyncio
async def test_recovering_budget_transitions_once_each_way(monkeypatch: pytest.MonkeyPatch):
    """A real recovery still works: DEGRADED while high, HEALTHY once relieved."""
    sup = MetaSupervisor(config=_cfg())

    _collect(sup, monkeypatch, _budget(0.87))
    await sup._evaluate(elapsed=1.0)
    assert sup.mode is SystemMode.DEGRADED

    _collect(sup, monkeypatch, _budget(0.10))
    await sup._evaluate(elapsed=1.0)
    assert sup.mode is SystemMode.HEALTHY
    assert sup.snapshot().transition_count == 2


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

    def boom(**kwargs) -> BudgetStatus:
        raise RuntimeError("store unavailable")

    monkeypatch.setattr(budget_mod, "is_memory_budget_enabled", lambda: True)
    monkeypatch.setattr(budget_mod, "evaluate_budget", boom)

    with caplog.at_level(logging.WARNING, logger="velantrim.meta_supervisor"):
        supervisor._collect_mhi()  # must not raise

    assert supervisor._budget_cache == 0.0
    messages = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("budget pressure" in m for m in messages), messages
    assert any("store unavailable" in m for m in messages), messages
