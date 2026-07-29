"""tests/test_truth_maintenance_contradict.py

M8 (Claude audit 2026-07-28): core.truth_maintenance.contradict() has zero
production callers and, until this fix, zero test coverage — its two
secondary writes (the CONTRADICTS causal-graph edge, the
contradiction_registry entry) were both wrapped in a bare
`except Exception: pass`, so a real failure in either left no trace
anywhere, not even a debug log, while contradict() still reported
changed=True from the ESM transition alone.
"""
from __future__ import annotations

import logging

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    """contradict() (a module-level function) always operates through
    core.memory's module-level get_fact/transition_esm, which read the
    global store — redirect it rather than constructing a disconnected
    instance. tests/conftest.py's autouse fixture restores the original
    _GLOBAL_STORE after every test regardless."""
    import core.memory as memory_mod

    s = memory_mod.SQLiteGraphStore(str(tmp_path / "contradict.db"))
    monkeypatch.setattr(memory_mod, "_GLOBAL_STORE", s)
    return s


def _hypothesized_fact(store, fact_id: str, claim: str) -> None:
    """Store a fact and advance it to Hypothesized — Observed cannot
    transition directly to Contradicted (core.memory.ESM_TRANSITIONS)."""
    from core.memory import transition_esm

    store.store_fact({
        "fact_id": fact_id, "claim": claim, "source": "test", "confidence": 0.7,
    })
    transition_esm(fact_id, "Hypothesized")


class _BrokenCausalGraph:
    def add_relation(self, **kwargs):
        raise RuntimeError("simulated causal_graph failure")


class _BrokenContradictionRegistry:
    def record(self, *args, **kwargs):
        raise RuntimeError("simulated contradiction_registry failure")


def test_contradict_transitions_both_facts(store):
    from core.truth_maintenance import contradict

    _hypothesized_fact(store, "fa", "claim a")
    _hypothesized_fact(store, "fb", "claim b")

    changed = contradict("fa", "fb", reason="test")

    assert changed is True
    assert store.get_fact("fa")["epistemic_state"] == "Contradicted"
    assert store.get_fact("fb")["epistemic_state"] == "Contradicted"


def test_contradict_causal_graph_failure_is_logged_not_silent(store, monkeypatch, caplog):
    import core.causal_graph as causal_graph_mod

    monkeypatch.setattr(causal_graph_mod, "get_causal_graph", lambda: _BrokenCausalGraph())

    _hypothesized_fact(store, "fa", "claim a")
    _hypothesized_fact(store, "fb", "claim b")

    with caplog.at_level(logging.WARNING, logger="velantrim.truth_maintenance"):
        from core.truth_maintenance import contradict

        changed = contradict("fa", "fb", reason="test")

    # The ESM transition (the operation's primary effect) still succeeds —
    # the secondary edge write failing must not roll that back or hide it.
    assert changed is True
    assert store.get_fact("fa")["epistemic_state"] == "Contradicted"
    assert any(
        "CONTRADICTS" in r.message and "fa" in r.message and r.levelno == logging.WARNING
        for r in caplog.records
    ), f"no WARNING logged for the causal_graph failure: {[r.message for r in caplog.records]}"


def test_contradict_registry_failure_is_logged_not_silent(store, monkeypatch, caplog):
    import core.contradiction_registry as registry_mod

    monkeypatch.setattr(
        registry_mod, "get_contradiction_registry", lambda: _BrokenContradictionRegistry()
    )

    _hypothesized_fact(store, "fa", "claim a")
    _hypothesized_fact(store, "fb", "claim b")

    with caplog.at_level(logging.WARNING, logger="velantrim.truth_maintenance"):
        from core.truth_maintenance import contradict

        changed = contradict("fa", "fb", reason="test")

    assert changed is True
    assert store.get_fact("fa")["epistemic_state"] == "Contradicted"
    assert any(
        "contradiction-registry" in r.message and r.levelno == logging.WARNING
        for r in caplog.records
    ), f"no WARNING logged for the registry failure: {[r.message for r in caplog.records]}"
