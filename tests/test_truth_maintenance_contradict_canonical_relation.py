"""Issue #501: real ESM, canonical causal edge and contradiction registry agree.

Unlike mock-based truth-maintenance tests, these checks exercise the actual
CausalGraph/WriteGate/audit path against the same isolated SQLite database.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def canonical_runtime(tmp_path, monkeypatch):
    from core import contradiction_registry, memory, pipeline
    from core.causal_graph import get_causal_graph

    store = memory.SQLiteGraphStore(str(tmp_path / "issue501.db"))
    store.ensure_schema()
    monkeypatch.setattr(memory, "_GLOBAL_STORE", store)
    # Isolate the pipeline singleton without replacing its canonical writer.
    monkeypatch.setattr(pipeline, "_CAUSAL_GRAPH", None)
    monkeypatch.setattr(pipeline, "_CAUSAL_GRAPH_DB_PATH", "")
    monkeypatch.setattr(contradiction_registry, "_registry", None)
    graph = get_causal_graph()
    try:
        yield store, graph, contradiction_registry
    finally:
        graph._conn.close()
        store.close()


def _seed_supported(store, fact_id: str, claim: str) -> None:
    assert store.store_fact({
        "fact_id": fact_id,
        "claim": claim,
        "source": "issue501-test",
        "confidence": 0.8,
        "metadata": {"evidence_refs": ["ref-a", "ref-b"]},
    }) is True
    assert store.transition_esm(fact_id, "Hypothesized") is True
    assert store.transition_esm(fact_id, "Supported") is True
    assert store.get_fact_durable(fact_id)["epistemic_state"] == "Supported"


def test_canonical_graph_rejects_legacy_uppercase_relation(canonical_runtime):
    """The old caller value must not be silently accepted by a new writer."""
    store, graph, registry_mod = canonical_runtime
    _seed_supported(store, "alpha", "Claim A")
    _seed_supported(store, "beta", "Claim B")

    with pytest.raises(ValueError, match="relation_type"):
        graph.add_relation("alpha", "beta", "CONTRADICTS", confidence=0.95)
    assert graph.get_relations_from("alpha") == []
    assert graph.get_relations_from("beta") == []
    assert registry_mod.get_contradiction_registry().spacer_count() == 0
    assert store.get_fact_durable("alpha")["epistemic_state"] == "Supported"
    assert store.get_fact_durable("beta")["epistemic_state"] == "Supported"


def test_contradict_supported_pair_writes_canonical_edge_and_registry(canonical_runtime):
    """Both durable transitions, canonical bidirectional edge and registry exist."""
    from core.truth_maintenance import contradict

    store, graph, registry_mod = canonical_runtime
    _seed_supported(store, "alpha", "Claim A")
    _seed_supported(store, "beta", "Claim B")
    assert graph.get_relations_from("alpha") == []

    assert contradict("alpha", "beta") is True
    registry = registry_mod.get_contradiction_registry()
    for fact_id in ("alpha", "beta"):
        fact = store.get_fact_durable(fact_id)
        assert fact["epistemic_state"] == "Contradicted"
        assert fact["history"][-1]["by"] == "truth_maintenance.contradict"

    forward = graph.get_relations_from("alpha", relation_type="contradicts")
    inverse = graph.get_relations_from("beta", relation_type="contradicts")
    assert len(forward) == len(inverse) == 1
    assert forward[0].to_fact_id == "beta"
    assert inverse[0].to_fact_id == "alpha"
    assert forward[0].confidence == pytest.approx(0.95)
    assert inverse[0].confidence == pytest.approx(0.95)
    assert any(rel.to_fact_id == "beta" for rel in graph.find_contradictions("alpha"))

    rows = graph._conn.execute(
        "SELECT from_fact_id, to_fact_id, relation_type FROM relations "
        "WHERE relation_type = 'contradicts'"
    ).fetchall()
    assert {tuple(row) for row in rows} == {
        ("alpha", "beta", "contradicts"),
        ("beta", "alpha", "contradicts"),
    }
    audit_count = graph._conn.execute(
        "SELECT COUNT(*) FROM memory_events WHERE event_type = 'relation_created'"
    ).fetchone()[0]
    assert audit_count == 2

    assert registry.spacer_count() == 1
    assert set(registry.known_contradictions("alpha")) == {"beta"}
    assert set(registry.known_contradictions("beta")) == {"alpha"}


def test_contradict_partial_esm_keeps_canonical_pair_artifacts(canonical_runtime):
    """One legal ESM commit still records the pair through canonical owners."""
    from core.truth_maintenance import contradict

    store, graph, registry_mod = canonical_runtime
    _seed_supported(store, "supported", "Claim A")
    assert store.store_fact({
        "fact_id": "observed",
        "claim": "Claim B",
        "source": "issue501-test",
        "confidence": 0.5,
        "metadata": {},
    }) is True
    assert store.get_fact_durable("observed")["epistemic_state"] == "Observed"

    assert contradict("supported", "observed") is True
    registry = registry_mod.get_contradiction_registry()
    assert store.get_fact_durable("supported")["epistemic_state"] == "Contradicted"
    assert store.get_fact_durable("observed")["epistemic_state"] == "Observed"

    forward = graph.get_relations_from("supported", relation_type="contradicts")
    inverse = graph.get_relations_from("observed", relation_type="contradicts")
    assert len(forward) == len(inverse) == 1
    assert forward[0].to_fact_id == "observed"
    assert inverse[0].to_fact_id == "supported"

    assert registry.spacer_count() == 1
    assert set(registry.known_contradictions("supported")) == {"observed"}
    assert set(registry.known_contradictions("observed")) == {"supported"}
