"""Acceptance tests for issue #295 / #53 Phase 1 ModelFreeCore.

The repository contains integration tests that deliberately purge ``core.*`` from
``sys.modules`` and re-import the package.  Therefore these acceptance tests must
resolve reload-sensitive core modules at test-execution time rather than retain stale
module/function objects captured during collection.
"""

from __future__ import annotations

import json
import socket
import sqlite3
import urllib.request

import pytest


def _memory():
    import core.memory as module

    return module


def _pipeline():
    import core.pipeline as module

    return module


def _hybrid():
    import core.hybrid_retriever as module

    return module


def _model_free():
    import core.model_free_core as module

    return module


@pytest.fixture
def store(tmp_path, monkeypatch):
    memory = _memory()
    pipeline = _pipeline()
    db_path = tmp_path / "model_free.db"
    graph_store = memory.SQLiteGraphStore(str(db_path))
    monkeypatch.setattr(memory, "_GLOBAL_STORE", graph_store)
    monkeypatch.setattr(pipeline, "_NGRAM_INDEX", None)
    monkeypatch.setattr(pipeline, "_CAUSAL_GRAPH", None)
    monkeypatch.setattr(pipeline, "_CAUSAL_GRAPH_DB_PATH", "")
    yield graph_store
    if pipeline._CAUSAL_GRAPH is not None:
        try:
            pipeline._CAUSAL_GRAPH._conn.close()
        except Exception:
            pass
    pipeline._CAUSAL_GRAPH = None
    pipeline._CAUSAL_GRAPH_DB_PATH = ""
    graph_store.close()


def _seed_validated(
    fact_id: str,
    claim: str,
    *,
    source: str = "fixture",
    confidence: float = 0.95,
) -> None:
    memory = _memory()
    memory.store_fact(
        {
            "fact_id": fact_id,
            "claim": claim,
            "source": source,
            "confidence": confidence,
        }
    )
    memory.promote_to_validated(fact_id)


def _boom(name: str):
    def fail(*_args, **_kwargs):
        raise AssertionError(f"ModelFreeCore must not invoke {name}")

    return fail


def test_model_free_query_never_invokes_optional_model_or_network_paths(
    store, monkeypatch
):
    pipeline = _pipeline()
    hybrid = _hybrid()
    model_free = _model_free()
    _seed_validated("water", "вода кипит при ста градусах цельсия", source="physics")

    monkeypatch.setattr(pipeline, "_get_hybrid_retriever", _boom("HybridRetriever"))
    monkeypatch.setattr(hybrid.DenseRetriever, "retrieve", _boom("DenseRetriever"))
    monkeypatch.setattr(hybrid, "reciprocal_rank_fusion", _boom("RRF"))
    monkeypatch.setattr(socket, "create_connection", _boom("network"))
    monkeypatch.setattr(urllib.request, "urlopen", _boom("network"))

    result = model_free.ModelFreeCore().query(
        model_free.L2Query("что такое вода", top_k=5)
    )

    assert result.insufficient_evidence is False
    assert result.execution_mode == "model_free"
    assert result.retrieval_mode == "lexical"
    assert result.optional_capabilities_used == ()
    assert [item.fact_id for item in result.evidence] == ["water"]
    assert "вода кипит" in result.answer


def test_model_free_result_is_typed_deterministic_and_json_serializable(store):
    model_free = _model_free()
    _seed_validated("earth", "земля вращается вокруг солнца", source="astronomy")
    core = model_free.ModelFreeCore()
    request = model_free.L2Query("земля солнца", top_k=3, include_graph=False)

    first = core.query(request).to_dict()
    second = core.query(request).to_dict()

    assert first == second
    assert first["query_type"] in {"factual", "unknown"}
    assert first["retrieval_mode"] == "lexical"
    assert first["execution_mode"] == "model_free"
    assert json.loads(json.dumps(first, ensure_ascii=False)) == first


def test_model_free_surfaces_existing_local_contradiction_read_only(store):
    pipeline = _pipeline()
    model_free = _model_free()
    _seed_validated("coffee_a", "кофе повышает давление", source="study-a")
    _seed_validated("coffee_b", "кофе не повышает давление", source="study-b")

    graph = pipeline._get_causal_graph()
    assert graph is not None
    graph.add_relation(
        "coffee_a",
        "coffee_b",
        "contradicts",
        confidence=0.9,
        inference_source="manual",
    )
    before_relations = graph._conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]

    result = model_free.ModelFreeCore().query(
        model_free.L2Query("кофе давление", top_k=5)
    )
    after_relations = graph._conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]

    assert result.insufficient_evidence is False
    assert any(rel.relation_type == "contradicts" for rel in result.conflicts)
    assert "Известные локальные противоречия" in result.answer
    assert after_relations == before_relations


def test_model_free_policy_ineligible_fact_returns_bounded_insufficient_evidence(store):
    memory = _memory()
    model_free = _model_free()
    memory.store_fact(
        {
            "fact_id": "hyp",
            "claim": "вода мгновенно превращается в лёд",
            "source": "unverified",
            "confidence": 0.9,
        }
    )

    result = model_free.ModelFreeCore().query(model_free.L2Query("вода лёд"))

    assert result.insufficient_evidence is True
    assert result.evidence == ()
    assert result.answer == "Недостаточно подтверждённых локальных данных."
    assert result.reason_code == "no_policy_eligible_local_evidence"


def test_model_free_empty_query_is_bounded_and_does_not_retrieve(store, monkeypatch):
    pipeline = _pipeline()
    model_free = _model_free()
    monkeypatch.setattr(
        pipeline,
        "_retrieve_from_store",
        _boom("retrieval for empty query"),
    )

    result = model_free.ModelFreeCore().query(model_free.L2Query("   "))

    assert result.insufficient_evidence is True
    assert result.reason_code == "empty_query"
    assert result.answer == "Недостаточно подтверждённых локальных данных."


def test_model_free_query_does_not_mutate_canon_esm_or_relations(store):
    memory = _memory()
    pipeline = _pipeline()
    model_free = _model_free()
    _seed_validated("f1", "вода нужна для жизни", source="biology")
    _seed_validated("f2", "жизнь зависит от воды", source="biology")

    graph = pipeline._get_causal_graph()
    assert graph is not None
    graph.add_relation(
        "f1",
        "f2",
        "requires",
        confidence=0.8,
        inference_source="manual",
    )

    before_ids = sorted(memory.get_fact_ids(limit=100))
    with sqlite3.connect(store.db_path) as conn:
        before_states = conn.execute(
            "SELECT fact_id, epistemic_state FROM facts ORDER BY fact_id"
        ).fetchall()
        before_relations = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]

    result = model_free.ModelFreeCore().query(
        model_free.L2Query("вода жизнь", top_k=5)
    )
    assert result.insufficient_evidence is False

    after_ids = sorted(memory.get_fact_ids(limit=100))
    with sqlite3.connect(store.db_path) as conn:
        after_states = conn.execute(
            "SELECT fact_id, epistemic_state FROM facts ORDER BY fact_id"
        ).fetchall()
        after_relations = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]

    assert after_ids == before_ids
    assert after_states == before_states
    assert after_relations == before_relations


def test_model_free_contract_has_no_write_or_escalation_api():
    model_free = _model_free()
    core = model_free.ModelFreeCore()

    for forbidden in (
        "store_fact",
        "write",
        "promote",
        "embed",
        "rerank",
        "invoke_llm",
        "remote",
        "enable",
    ):
        assert not hasattr(core, forbidden)


def test_l2_query_bounds_are_fail_closed():
    model_free = _model_free()
    with pytest.raises(ValueError, match="top_k"):
        model_free.L2Query("x", top_k=0)
    with pytest.raises(ValueError, match="cognitive_mode"):
        model_free.L2Query("x", cognitive_mode="AUTO")
