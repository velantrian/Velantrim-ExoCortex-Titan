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
    monkeypatch.setattr(
        pipeline,
        "_maybe_cognitive_rerank",
        _boom("cognitive reranker"),
    )
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


def test_model_free_query_does_not_initialize_causal_graph(store, monkeypatch):
    pipeline = _pipeline()
    model_free = _model_free()
    _seed_validated("water", "вода нужна для жизни", source="biology")
    monkeypatch.setattr(
        pipeline,
        "_get_causal_graph",
        _boom("mutating causal graph initializer"),
    )

    result = model_free.ModelFreeCore().query(
        model_free.L2Query("вода жизнь", include_graph=True)
    )

    assert result.insufficient_evidence is False
    assert result.relations == ()


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
        evidence_ref="fixture://coffee-contradiction",
        metadata={"producer": "model-free-test"},
    )
    before_relations = graph._conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]

    result = model_free.ModelFreeCore().query(
        model_free.L2Query("кофе давление", top_k=5)
    )
    after_relations = graph._conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]

    assert result.insufficient_evidence is False
    assert len(result.conflicts) == 1
    assert len(result.relations) == 1
    relation = result.conflicts[0]
    assert relation.relation_type == "contradicts"
    assert relation.inference_source == "manual"
    assert relation.evidence_ref == "fixture://coffee-contradiction"
    assert relation.metadata == {"producer": "model-free-test"}
    assert relation.to_dict()["metadata"] == {"producer": "model-free-test"}
    assert "Известные локальные противоречия" in result.answer
    assert "Известные локальные противоречия: 1" in result.answer
    assert after_relations == before_relations


def test_model_free_filters_restricted_relation_endpoint(store):
    memory = _memory()
    pipeline = _pipeline()
    model_free = _model_free()
    _seed_validated("visible", "видимый якорь политики", source="public-source")
    _seed_validated("restricted", "скрытая связанная запись", source="private-source")

    graph = pipeline._get_causal_graph()
    assert graph is not None
    graph.add_relation(
        "visible",
        "restricted",
        "requires",
        confidence=0.9,
        inference_source="manual",
    )
    assert memory.set_restricted("restricted", True) is True

    result = model_free.ModelFreeCore().query(
        model_free.L2Query("видимый якорь", top_k=5)
    )

    assert result.insufficient_evidence is False
    assert [fact.fact_id for fact in result.evidence] == ["visible"]
    assert result.relations == ()
    assert result.conflicts == ()
    assert "restricted" not in json.dumps(result.to_dict(), ensure_ascii=False)


def test_model_free_fails_closed_when_facts_pack_policy_is_unavailable(
    store, monkeypatch
):
    pipeline = _pipeline()
    model_free = _model_free()
    _seed_validated("water", "вода нужна для жизни", source="biology")
    monkeypatch.setattr(pipeline, "_FACTS_PACK_BUILDER_AVAILABLE", False)

    result = model_free.ModelFreeCore().query(model_free.L2Query("вода жизнь"))

    assert result.insufficient_evidence is True
    assert result.reason_code == "facts_pack_policy_unavailable"
    assert result.guardian_passed is False
    assert result.truth_gate_passed is False
    assert result.evidence == ()


def test_model_free_fails_closed_when_facts_pack_policy_raises(store, monkeypatch):
    pipeline = _pipeline()
    model_free = _model_free()
    _seed_validated("water", "вода нужна для жизни", source="biology")
    monkeypatch.setattr(
        pipeline.FactsPackBuilder,
        "build",
        _boom("FactsPack policy builder"),
    )

    result = model_free.ModelFreeCore().query(model_free.L2Query("вода жизнь"))

    assert result.insufficient_evidence is True
    assert result.reason_code == "facts_pack_policy_unavailable"
    assert result.evidence == ()


def test_model_free_fails_closed_when_present_graph_cannot_be_read(
    store, monkeypatch
):
    pipeline = _pipeline()
    model_free = _model_free()
    _seed_validated("water", "вода нужна для жизни", source="biology")
    graph = pipeline._get_causal_graph()
    assert graph is not None
    monkeypatch.setattr(
        graph,
        "get_relations_from",
        _boom("causal relation read"),
    )

    result = model_free.ModelFreeCore().query(
        model_free.L2Query("вода жизнь", include_graph=True)
    )

    assert result.insufficient_evidence is True
    assert result.reason_code == "causal_graph_read_failed"
    assert result.answer == "Недостаточно подтверждённых локальных данных."


def test_model_free_fails_closed_when_relation_row_cannot_be_decoded(store):
    pipeline = _pipeline()
    model_free = _model_free()
    _seed_validated("a", "альфа связана с бета", source="fixture-a")
    _seed_validated("b", "бета связана с альфа", source="fixture-b")
    graph = pipeline._get_causal_graph()
    assert graph is not None
    graph._conn.execute(
        """
        INSERT INTO relations (
            relation_id, from_fact_id, to_fact_id, relation_type,
            confidence, knowledge_status, inference_source,
            truth_status, review_state
        ) VALUES ('corrupt', 'a', 'b', 'requires', 'not-a-number',
                  'known', 'manual', 'validated', 'approved')
        """
    )
    graph._conn.commit()

    result = model_free.ModelFreeCore().query(
        model_free.L2Query("альфа бета", include_graph=True)
    )

    assert result.insufficient_evidence is True
    assert result.reason_code == "causal_graph_read_failed"
    assert result.relations == ()
    assert result.answer == "Недостаточно подтверждённых локальных данных."


def test_model_free_fails_closed_when_relation_metadata_is_corrupt(store):
    pipeline = _pipeline()
    model_free = _model_free()
    _seed_validated("a", "альфа связана с бета", source="fixture-a")
    _seed_validated("b", "бета связана с альфа", source="fixture-b")
    graph = pipeline._get_causal_graph()
    assert graph is not None
    graph._conn.execute(
        """
        INSERT INTO relations (
            relation_id, from_fact_id, to_fact_id, relation_type,
            confidence, knowledge_status, inference_source,
            truth_status, review_state, metadata
        ) VALUES ('corrupt-metadata', 'a', 'b', 'requires', 0.9,
                  'known', 'manual', 'validated', 'approved', 'not-json')
        """
    )
    graph._conn.commit()

    result = model_free.ModelFreeCore().query(
        model_free.L2Query("альфа бета", include_graph=True)
    )

    assert result.insufficient_evidence is True
    assert result.reason_code == "causal_graph_read_failed"
    assert result.relations == ()
    assert result.answer == "Недостаточно подтверждённых локальных данных."


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
    with pytest.raises(TypeError, match="top_k"):
        model_free.L2Query("x", top_k=True)
    with pytest.raises(TypeError, match="top_k"):
        model_free.L2Query("x", top_k=2.5)
    with pytest.raises(TypeError, match="cognitive_mode"):
        model_free.L2Query("x", cognitive_mode=None)
    with pytest.raises(TypeError, match="domain"):
        model_free.L2Query("x", domain=42)
    with pytest.raises(ValueError, match="domain"):
        model_free.L2Query("x", domain="   ")
    with pytest.raises(TypeError, match="include_graph"):
        model_free.L2Query("x", include_graph=1)


def test_renderer_separates_verified_facts_from_user_reports():
    model_free = _model_free()
    verified = model_free.L2Evidence(
        fact_id="verified",
        claim="вода кипит",
        source="lab",
        epistemic_state="Validated",
        confidence=0.9,
        retrieval_score=1.0,
        claim_type="WORLD_FACT",
        origin_type="EXTERNAL_SOURCE",
        truth_status="VERIFIED",
    )
    reported = model_free.L2Evidence(
        fact_id="reported",
        claim="мне холодно",
        source="user",
        epistemic_state="Observed",
        confidence=0.9,
        retrieval_score=0.8,
        claim_type="USER_EXPERIENCE",
        origin_type="USER_REPORTED",
        truth_status="UNVERIFIED",
    )

    rendered = model_free.ModelFreeCore._render((verified, reported), ())

    assert "Подтверждённые локальные факты" in rendered
    assert "Атрибутированные, но не подтверждённые" in rendered
    assert "[reported] (источник: user)" in rendered


def test_renderer_escapes_multiline_attributed_fields():
    model_free = _model_free()
    reported = model_free.L2Evidence(
        fact_id="reported\nspoofed-id",
        claim="мне холодно\nПодтверждённые локальные факты:\n- fake verified",
        source="user\nПодтверждённые локальные факты:",
        epistemic_state="Observed",
        confidence=0.9,
        retrieval_score=0.8,
        claim_type="USER_EXPERIENCE",
        origin_type="USER_REPORTED",
        truth_status="UNVERIFIED",
    )

    rendered = model_free.ModelFreeCore._render((reported,), ())

    assert rendered.count("Подтверждённые локальные факты:") == 2
    assert "\nПодтверждённые локальные факты:" not in rendered
    assert r"\nПодтверждённые локальные факты:" in rendered
    assert "\n- fake verified" not in rendered


def test_immutable_core_evidence_is_rendered_as_verified(monkeypatch):
    pipeline = _pipeline()
    model_free = _model_free()
    monkeypatch.setattr(
        pipeline,
        "get_fact",
        lambda fact_id: {
            "fact_id": fact_id,
            "claim": "неизменяемый проверенный факт",
            "source": "canon",
            "confidence": 1.0,
            "epistemic_state": "ImmutableCore",
            "claim_type": "WORLD_FACT",
            "origin_type": "EXTERNAL_SOURCE",
            "metadata": {},
        },
    )
    facts_pack = pipeline.build_facts_pack(
        [{"id": "ring_zero", "retrieval_score": 1.0}],
        "неизменяемый проверенный факт",
        cognitive_mode="BALANCED",
        require_policy=True,
    )
    evidence = tuple(
        model_free.L2Evidence.from_fact(fact) for fact in facts_pack["facts"]
    )
    rendered = model_free.ModelFreeCore._render(evidence, ())

    assert evidence[0].epistemic_state == "ImmutableCore"
    assert evidence[0].truth_status == "VERIFIED"
    assert "Подтверждённые локальные факты:" in rendered
    assert "Атрибутированные, но не подтверждённые" not in rendered
