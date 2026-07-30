"""Increment 2 routing contract tests (PR #91).

Proves BudgetPlanner now *executes* an adaptive retrieval route instead of
only scaling k, and that adaptivity never buys a shortcut around the
canonical query path:

    Query -> [NGram] -> Retrieve(lexical|hybrid) -> FactsPack -> TRACE
           -> Guardian -> TruthGate -> Answer

Covers (see PR description "Обязательные тесты"):
  1. lexical never calls DenseRetriever.retrieve
  2. lexical never calls reciprocal_rank_fusion
  3. hybrid calls DenseRetriever.retrieve when Dense is available
  4. ENABLE_BUDGET_PLANNER off -> behavior unchanged (always "hybrid")
  5. every successful route still crosses Guardian and TruthGate
  6. Hypothesized/policy-ineligible facts get no fast-path bypass
  7. empty query triggers no NGram/BM25/Dense call at all
  8. query path performs no writes to Canon/ESM/relations
  9. the executed retrieval_mode is observable on the result
"""
from __future__ import annotations

import sys
import types

import pytest

import core.hybrid_retriever as hr
import core.memory as mem
import core.pipeline as pipeline
from core.memory import (
    SQLiteGraphStore,
    get_fact_ids,
    promote_to_validated,
    store_fact,
    transition_esm,
)

_COMPLEX_QUERY = (
    "почему использование закалённого металла снижает энергозатраты "
    "при сравнении с бетоном и какие риски пожара возникают"
)


class _StubNGram:
    """Deterministic FTS5 stand-in: always returns a fixed candidate id list,
    so tests don't depend on real trigram matching or a shared index file."""

    available = True

    def __init__(self, ids):
        self._ids = list(ids)

    def query(self, _text, limit=50):
        return list(self._ids)


def _stub_ngram(monkeypatch, ids):
    monkeypatch.setattr(pipeline, "_NGRAM_INDEX", _StubNGram(ids))


class _FakeSentenceTransformer:
    """Dependency-free stand-in for sentence_transformers.SentenceTransformer
    (the real package is an optional extra, not installed in this env)."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def encode(self, texts, normalize_embeddings: bool = True):
        return [[((hash((t, i)) % 997) / 997.0) for i in range(6)] for t in texts]


def _enable_fake_dense(monkeypatch):
    """Make DenseRetriever genuinely `.available` via a fake sentence_transformers,
    and reset its process-persistent caches so tests don't see each other's state."""
    fake_module = types.ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = _FakeSentenceTransformer  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)
    monkeypatch.setattr(hr.DenseRetriever, "_AVAILABLE", None, raising=False)
    monkeypatch.setattr(hr.DenseRetriever, "_MODEL_CACHE", {}, raising=False)
    monkeypatch.setattr(hr.DenseRetriever, "_VECTOR_CACHE", {}, raising=False)


@pytest.fixture(autouse=True)
def reset_hybrid_singleton(monkeypatch):
    """Isolate pipeline's module-level HybridRetriever singleton per test."""
    monkeypatch.setattr(pipeline, "_HYBRID_RETRIEVER", None)
    monkeypatch.setattr(pipeline, "_HYBRID_DIRTY", True)
    monkeypatch.setattr(pipeline, "_HYBRID_FACTS_COUNT", 0)
    monkeypatch.setattr(pipeline, "_HYBRID_FACT_IDS", frozenset())


@pytest.fixture
def store(tmp_path, monkeypatch):
    s = SQLiteGraphStore(str(tmp_path / "t.db"))
    monkeypatch.setattr(mem, "_GLOBAL_STORE", s)
    yield s
    s.close()


@pytest.fixture
def seeded_store(store):
    facts = [
        {"fact_id": "f1", "claim": "вода кипит при ста градусах цельсия",
         "source": "physics", "confidence": 0.95},
        {"fact_id": "f2", "claim": "квантовая запутанность связывает частицы",
         "source": "physics", "confidence": 0.9},
        {"fact_id": "f3", "claim": "земля вращается вокруг солнца",
         "source": "astronomy", "confidence": 0.95},
    ]
    for f in facts:
        store_fact(f)
        promote_to_validated(str(f["fact_id"]))
    return store


# ─── 1 & 2: lexical never touches Dense / RRF ─────────────────────────────

def test_lexical_never_calls_dense_retrieve(seeded_store, monkeypatch):
    _stub_ngram(monkeypatch, ["f1", "f2", "f3"])

    def _boom(*_a, **_kw):
        raise AssertionError("lexical route must never call DenseRetriever.retrieve")

    monkeypatch.setattr(hr.DenseRetriever, "retrieve", _boom)

    results = pipeline._retrieve_from_store("вода кипит", k=3, retrieval_mode="lexical")
    assert results
    assert all(r["origin"] == "bm25_lexical" for r in results)


def test_lexical_never_calls_rrf(seeded_store, monkeypatch):
    _stub_ngram(monkeypatch, ["f1", "f2", "f3"])

    def _boom(*_a, **_kw):
        raise AssertionError("lexical route must never call reciprocal_rank_fusion")

    monkeypatch.setattr(hr, "reciprocal_rank_fusion", _boom)

    results = pipeline._retrieve_from_store("вода кипит", k=3, retrieval_mode="lexical")
    assert results


def test_lexical_never_builds_hybrid_singleton_or_reranker(seeded_store, monkeypatch):
    """Belt-and-braces: lexical must not even reach _get_hybrid_retriever
    (so CrossEncoderReranker/graph expansion inside HybridRetriever can't fire either)."""
    _stub_ngram(monkeypatch, ["f1", "f2", "f3"])

    def _boom(*_a, **_kw):
        raise AssertionError("lexical route must not build the HybridRetriever singleton")

    monkeypatch.setattr(pipeline, "_get_hybrid_retriever", _boom)

    results = pipeline._retrieve_from_store("вода кипит", k=3, retrieval_mode="lexical")
    assert results


# ─── 3: hybrid calls Dense when available ─────────────────────────────────

def test_hybrid_calls_dense_when_available(seeded_store, monkeypatch):
    _stub_ngram(monkeypatch, ["f1", "f2", "f3"])
    _enable_fake_dense(monkeypatch)

    calls = {"n": 0}
    original_retrieve = hr.DenseRetriever.retrieve

    def _spy(self, *a, **kw):
        calls["n"] += 1
        return original_retrieve(self, *a, **kw)

    monkeypatch.setattr(hr.DenseRetriever, "retrieve", _spy)

    results = pipeline._retrieve_from_store("вода кипит", k=3, retrieval_mode="hybrid")
    assert results
    assert calls["n"] >= 1, "hybrid route must call DenseRetriever.retrieve when Dense is available"
    assert all(r.get("retrieval_mode") == "hybrid" for r in results)


# ─── 4: BudgetPlanner flag off -> unchanged ("hybrid") behavior ───────────

def test_flag_off_always_routes_hybrid_regardless_of_query(monkeypatch):
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: False)
    captured = {}

    def _spy(query, k=3, domain=None, retrieval_mode="hybrid", max_hops=1):
        captured["retrieval_mode"] = retrieval_mode
        captured["k"] = k
        return []

    monkeypatch.setattr(pipeline, "_retrieve_from_store", _spy)

    pipeline.retrieve("вода", k=3)               # trivial query
    assert captured["retrieval_mode"] == "hybrid"
    assert captured["k"] == 3

    pipeline.retrieve(_COMPLEX_QUERY, k=3)        # complex query
    assert captured["retrieval_mode"] == "hybrid"
    assert captured["k"] == 3                     # k also unchanged when flag is off


def test_flag_on_routes_lexical_for_trivial_query(monkeypatch):
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: True)
    captured = {}

    def _spy(query, k=3, domain=None, retrieval_mode="hybrid", max_hops=1):
        captured["retrieval_mode"] = retrieval_mode
        return []

    monkeypatch.setattr(pipeline, "_retrieve_from_store", _spy)
    pipeline.retrieve("вода", k=3)
    assert captured["retrieval_mode"] == "lexical"


def test_flag_on_routes_hybrid_for_complex_query(monkeypatch):
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: True)
    captured = {}

    def _spy(query, k=3, domain=None, retrieval_mode="hybrid", max_hops=1):
        captured["retrieval_mode"] = retrieval_mode
        return []

    monkeypatch.setattr(pipeline, "_retrieve_from_store", _spy)
    pipeline.retrieve(_COMPLEX_QUERY, k=3)
    assert captured["retrieval_mode"] == "hybrid"


# ─── 5: every successful route still crosses Guardian + TruthGate ─────────

def _spy_on(monkeypatch, obj, name, counter, key):
    original = getattr(obj, name)

    def _wrapped(*a, **kw):
        counter[key] += 1
        return original(*a, **kw)

    monkeypatch.setattr(obj, name, _wrapped)


def test_lexical_route_still_crosses_guardian_and_truth_gate(seeded_store, monkeypatch):
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: True)
    _stub_ngram(monkeypatch, ["f1", "f2", "f3"])

    calls = {"guardian": 0, "truth_gate": 0}
    _spy_on(monkeypatch, pipeline, "guardian", calls, "guardian")
    _spy_on(monkeypatch, pipeline, "truth_gate", calls, "truth_gate")

    result = pipeline.run("вода")  # trivial -> lexical, per BudgetPlanner
    assert result.get("error") is None
    assert calls["guardian"] == 1
    assert calls["truth_gate"] == 1


def test_hybrid_route_still_crosses_guardian_and_truth_gate(seeded_store, monkeypatch):
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: True)
    _stub_ngram(monkeypatch, ["f1", "f2", "f3"])

    calls = {"guardian": 0, "truth_gate": 0}
    _spy_on(monkeypatch, pipeline, "guardian", calls, "guardian")
    _spy_on(monkeypatch, pipeline, "truth_gate", calls, "truth_gate")

    result = pipeline.run(_COMPLEX_QUERY)  # complex -> hybrid, per BudgetPlanner
    assert result.get("error") is None
    assert calls["guardian"] == 1
    assert calls["truth_gate"] == 1


# ─── 6: Hypothesized / policy-ineligible facts get no fast-path bypass ────

def test_lexical_fast_path_does_not_surface_hypothesized_facts(store, monkeypatch):
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: True)
    store_fact({"fact_id": "hyp1", "claim": "вода превращается в лёд мгновенно",
                "source": "physics", "confidence": 0.9})
    transition_esm("hyp1", "Hypothesized")
    _stub_ngram(monkeypatch, ["hyp1"])

    result = pipeline.run("вода")  # trivial -> lexical
    assert result.get("insufficient_evidence") is True
    assert result.get("facts") == []
    assert "hyp1" not in {f.get("fact_id") for f in result.get("facts", [])}


def test_hybrid_fast_path_does_not_surface_hypothesized_facts(store, monkeypatch):
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: True)
    store_fact({"fact_id": "hyp2", "claim": "закалённый металл никогда не плавится",
                "source": "physics", "confidence": 0.9})
    transition_esm("hyp2", "Hypothesized")
    _stub_ngram(monkeypatch, ["hyp2"])

    result = pipeline.run(_COMPLEX_QUERY)  # complex -> hybrid
    assert result.get("insufficient_evidence") is True
    assert result.get("facts") == []


# ─── 7: empty query -> no expensive retrieval at all ──────────────────────

def test_empty_query_skips_ngram_bm25_and_dense_entirely(seeded_store, monkeypatch):
    def _boom(*_a, **_kw):
        raise AssertionError("empty query must not reach NGram narrowing")

    monkeypatch.setattr(pipeline, "_narrow_candidates", _boom)
    monkeypatch.setattr(hr.DenseRetriever, "retrieve", _boom)
    monkeypatch.setattr(hr, "reciprocal_rank_fusion", _boom)

    assert pipeline._retrieve_from_store("", k=3, retrieval_mode="hybrid") == []
    assert pipeline._retrieve_from_store("   ", k=3, retrieval_mode="lexical") == []
    assert pipeline._retrieve_from_store("вода", k=3, retrieval_mode="none") == []


def test_budget_planner_plan_for_empty_query_is_none_mode():
    from core.budget_planner import plan

    assert plan("").mode == "none"
    assert plan("   ").mode == "none"


# ─── 8: query path performs no writes to Canon/ESM/relations ─────────────

def test_lexical_route_run_performs_no_canon_writes(seeded_store, monkeypatch):
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: True)
    _stub_ngram(monkeypatch, ["f1", "f2", "f3"])

    before = sorted(get_fact_ids(limit=1000))
    pipeline.run("вода")
    after = sorted(get_fact_ids(limit=1000))
    assert after == before, "lexical route must not create/mutate any canonical fact"


def test_hybrid_route_run_performs_no_canon_writes(seeded_store, monkeypatch):
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: True)
    _stub_ngram(monkeypatch, ["f1", "f2", "f3"])

    before = sorted(get_fact_ids(limit=1000))
    pipeline.run(_COMPLEX_QUERY)
    after = sorted(get_fact_ids(limit=1000))
    assert after == before, "hybrid route must not create/mutate any canonical fact"


def test_query_path_creates_no_relations_table_rows(seeded_store, monkeypatch):
    """CausalGraph is read-only from the query path (_extract_causal_hints only
    ever proposes; QueryPipeline never calls graph.add_relation())."""
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: True)
    _stub_ngram(monkeypatch, ["f1", "f2", "f3"])

    pipeline.run("вода")
    pipeline.run(_COMPLEX_QUERY)

    cg = pipeline._get_causal_graph()
    if cg is not None:
        row = cg._conn.execute("SELECT COUNT(*) FROM relations").fetchone()
        assert row[0] == 0


# ─── 9: executed retrieval_mode is observable on the result ──────────────

def test_result_carries_observed_retrieval_mode_lexical(seeded_store, monkeypatch):
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: True)
    _stub_ngram(monkeypatch, ["f1", "f2", "f3"])

    result = pipeline.run("вода")
    assert result.get("retrieval_mode") == "lexical"


def test_result_carries_observed_retrieval_mode_hybrid(seeded_store, monkeypatch):
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: True)
    _stub_ngram(monkeypatch, ["f1", "f2", "f3"])

    result = pipeline.run(_COMPLEX_QUERY)
    assert result.get("retrieval_mode") == "hybrid"


def test_result_reports_hybrid_when_flag_off(seeded_store, monkeypatch):
    """Flag off -> the executed route is genuinely still "hybrid" (the
    prior, only) behavior — the new key is purely additive observability,
    never a behavior change."""
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: False)
    _stub_ngram(monkeypatch, ["f1", "f2", "f3"])

    result = pipeline.run("вода")
    assert result.get("retrieval_mode") == "hybrid"
