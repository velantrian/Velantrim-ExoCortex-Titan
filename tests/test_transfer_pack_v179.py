import time

import pytest


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = str(tmp_path / "transfer_pack.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", path)
    monkeypatch.setenv("VELANTRIM_VERSION_SNAPSHOTS", "true")
    return path


def test_relation_store_is_additive_first_class_graph(db_path):
    from core.memory import SQLiteGraphStore
    from core.relations import RelationStore

    store = SQLiteGraphStore(db_path)
    store.store_fact({"fact_id": "rain", "claim": "rain wets soil", "source": "test"})
    store.store_fact({"fact_id": "soil", "claim": "wet soil helps plants", "source": "test"})

    rels = RelationStore(db_path)
    rel = rels.add("rain", "soil", "CAUSES", confidence=0.9, source="test")
    assert rel.epistemic_state == "Observed"
    assert rels.transition(rel.relation_id, "Supported", by="test") is True

    outgoing = rels.outgoing("rain")
    assert len(outgoing) == 1
    assert outgoing[0].kind == "CAUSES"
    assert outgoing[0].epistemic_state == "Supported"


def test_causal_retrieval_does_not_treat_analogy_as_cause(db_path):
    from core.causal_retrieval import causal_retrieve
    from core.memory import SQLiteGraphStore
    from core.relations import RelationStore

    store = SQLiteGraphStore(db_path)
    store.store_fact({
        "fact_id": "coffee",
        "claim": "coffee is a stimulating beverage",
        "source": "test",
    })
    store.store_fact({
        "fact_id": "productivity",
        "claim": "productivity is useful output over time",
        "source": "test",
    })

    rels = RelationStore(db_path)
    rels.add("coffee", "productivity", "ANALOGOUS_TO", confidence=0.8, source="test")

    results = causal_retrieve("what causes productivity?", store, rels, top_k=5)
    assert results == []


def test_causal_retrieval_returns_causal_evidence(db_path):
    from core.causal_retrieval import causal_retrieve, explain_causal_decision
    from core.memory import SQLiteGraphStore
    from core.relations import RelationStore

    store = SQLiteGraphStore(db_path)
    store.store_fact({"fact_id": "smoking", "claim": "smoking tobacco", "source": "test"})
    store.store_fact({"fact_id": "cancer", "claim": "lung cancer disease", "source": "test"})

    rels = RelationStore(db_path)
    rels.add("smoking", "cancer", "CAUSES", confidence=0.9, source="medical")

    results = causal_retrieve("what causes lung cancer?", store, rels, top_k=5)
    assert results
    assert results[0]["fact_id"] == "cancer"
    assert results[0]["evidence_kind"] == "causal"

    explanation = explain_causal_decision("what causes lung cancer?", results)
    assert explanation["is_causal"] is True
    assert "CAUSES" in explanation["allowed_edges"]


def test_version_store_snapshots_v86_fact_updates(db_path):
    from core.memory import SQLiteGraphStore
    from core.version_store import VersionStore

    store = SQLiteGraphStore(db_path)
    store.store_fact({"fact_id": "policy", "claim": "version one", "source": "test"})

    time.sleep(0.01)
    store.store_fact({"fact_id": "policy", "claim": "version two", "source": "test"})

    vs = VersionStore(db_path)
    history = vs.get_fact_history("policy")
    assert len(history) == 1
    assert history[0].claim == "version one"
    assert history[0].valid_from is not None
    assert history[0].superseded_at is not None
    assert vs.verify_versions_integrity("policy")["ok"] is True


def test_version_store_snapshots_v86_state_transitions(db_path):
    from core.memory import SQLiteGraphStore
    from core.version_store import VersionStore

    store = SQLiteGraphStore(db_path)
    store.store_fact({"fact_id": "evidence", "claim": "evidence exists", "source": "test"})
    store.transition_esm("evidence", "Supported", by="test")

    history = VersionStore(db_path).get_fact_history("evidence")
    assert len(history) == 1
    assert history[0].epistemic_state == "Observed"
    assert history[0].caused_by.startswith("memory.transition_esm")
