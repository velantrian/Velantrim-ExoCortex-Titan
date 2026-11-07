"""Regression: contradict() must not treat transition_esm False as success.

Missing facts return False from transition_esm (no exception). Pre-fix code
still set changed=True and could mint CONTRADICTS edges / registry records.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    import core.memory as memory_mod

    s = memory_mod.SQLiteGraphStore(str(tmp_path / "contradict.db"))
    monkeypatch.setattr(memory_mod, "_GLOBAL_STORE", s)
    return s


class _FakeCausalGraph:
    def __init__(self):
        self.calls: list[dict] = []

    def add_relation(self, from_fact_id, to_fact_id, relation_type,
                      confidence=0.8, **kwargs):
        self.calls.append({
            "from_fact_id": from_fact_id,
            "to_fact_id": to_fact_id,
            "relation_type": relation_type,
            "confidence": confidence,
        })
        return "fake_relation_id"


class _FakeRegistry:
    def __init__(self):
        self.records: list[tuple] = []

    def record(self, *args, **kwargs):
        self.records.append((args, kwargs))


@pytest.fixture
def fake_causal_graph(monkeypatch):
    import core.causal_graph as causal_graph_mod

    fake = _FakeCausalGraph()
    monkeypatch.setattr(causal_graph_mod, "get_causal_graph", lambda: fake)
    return fake


@pytest.fixture
def fake_registry(monkeypatch):
    import core.contradiction_registry as registry_mod

    fake = _FakeRegistry()
    monkeypatch.setattr(registry_mod, "get_contradiction_registry", lambda: fake)
    return fake


def _seed_supported(store, fact_id: str, claim: str) -> None:
    store.store_fact({
        "fact_id": fact_id,
        "claim": claim,
        "source": "integration-test",
        "confidence": 0.8,
        "metadata": {"evidence_refs": ["a", "b"]},
    })
    assert store.transition_esm(fact_id, "Hypothesized")
    assert store.transition_esm(fact_id, "Supported")


def test_contradict_missing_pair_is_false(store, fake_causal_graph, fake_registry):
    from core.truth_maintenance import contradict

    # One durable Supported fact + one missing id: missing returns False,
    # Supported→Contradicted succeeds. Wait — that would still change one.
    # Pure missing/missing is covered by the early both-None return.
    assert contradict("ghost_a", "ghost_b") is False
    assert fake_causal_graph.calls == []
    assert fake_registry.records == []


def test_contradict_missing_partner_of_illegal_state_is_false(
    store, fake_causal_graph, fake_registry,
):
    """Observed cannot go to Contradicted; missing returns False — both fail."""
    from core.truth_maintenance import contradict

    store.store_fact({
        "fact_id": "only_observed",
        "claim": "still observed",
        "source": "integration-test",
        "confidence": 0.5,
        "metadata": {},
    })
    assert store.get_fact("only_observed")["epistemic_state"] == "Observed"

    assert contradict("only_observed", "missing_partner") is False
    assert store.get_fact("only_observed")["epistemic_state"] == "Observed"
    assert fake_causal_graph.calls == []
    assert fake_registry.records == []


def test_contradict_supported_pair_succeeds(
    store, fake_causal_graph, fake_registry,
):
    from core.truth_maintenance import contradict

    _seed_supported(store, "a1", "claim a")
    _seed_supported(store, "b1", "claim b")

    assert contradict("a1", "b1") is True
    assert store.get_fact("a1")["epistemic_state"] == "Contradicted"
    assert store.get_fact("b1")["epistemic_state"] == "Contradicted"
    assert store.get_fact("a1")["history"][-1]["by"] == "truth_maintenance.contradict"
    assert fake_causal_graph.calls == [{
        "from_fact_id": "a1",
        "to_fact_id": "b1",
        "relation_type": "contradicts",
        "confidence": 0.95,
    }]
    assert len(fake_registry.records) == 1
