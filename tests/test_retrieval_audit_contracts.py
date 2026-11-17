"""Dense availability/cache concurrency and five-stage score regressions."""
import sys
import threading
import time
import types
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from core import hybrid_retriever as retrieval


def test_failed_dense_instance_cannot_disable_existing_instance(monkeypatch):
    class Model:
        def __init__(self, name):
            if name == "bad":
                raise RuntimeError("model unavailable")
        def encode(self, texts, **kwargs):
            return [[1., 0.] for _ in texts]
    monkeypatch.setitem(sys.modules, "sentence_transformers", types.SimpleNamespace(SentenceTransformer=Model))
    monkeypatch.setattr(retrieval.DenseRetriever, "_MODEL_CACHE", {})
    good = retrieval.DenseRetriever([{"claim": "present"}], model_name="good")
    assert good.available
    failed = retrieval.DenseRetriever([], model_name="bad")
    assert not failed.available
    assert good.available
    assert good.retrieve("present") == [(0, 1.)]


def test_concurrent_initialization_loads_one_model(monkeypatch):
    calls = []
    guard = threading.Lock()
    class Model:
        def __init__(self, name):
            with guard:
                calls.append(name)
            time.sleep(.03)  # deterministic window for competing cache misses
    monkeypatch.setitem(sys.modules, "sentence_transformers", types.SimpleNamespace(SentenceTransformer=Model))
    monkeypatch.setattr(retrieval.DenseRetriever, "_MODEL_CACHE", {})
    with ThreadPoolExecutor(max_workers=4) as pool:
        models = list(pool.map(lambda _: retrieval.DenseRetriever([], model_name="same"), range(4)))
    assert calls == ["same"]
    assert len({id(model._model) for model in models}) == 1


def test_five_stage_scores_and_graph_candidates_share_final_rank(monkeypatch):
    retriever = retrieval.HybridRetriever.__new__(retrieval.HybridRetriever)
    retriever._facts = [{"fact_id": str(i), "claim": f"candidate {i}"} for i in range(3)]
    retriever._bm25 = SimpleNamespace(retrieve=lambda *a, **k: [(0, 2.), (1, 1.)])
    retriever._dense = SimpleNamespace(retrieve=lambda *a, **k: [])
    retriever._reranker = None
    retriever._rrf_k = 60
    monkeypatch.setattr(retriever, "_ego_net_expand", lambda *a, **k: [2])
    plain = retriever.retrieve_5stage("query", top_k=2, use_ego=False)
    assert [r.final_score for r in plain] == [2., 1.]
    assert all(r.final_score == r.rrf_score for r in plain)
    expanded = retriever.retrieve_5stage("query", top_k=2)
    assert [r.fact_id for r in expanded] == ["0", "2"]
    assert all(r.final_score == r.rrf_score > 0 for r in expanded)
    assert all(r.confidence == 0 for r in expanded)


def test_rrf_depends_only_on_rank_not_score_magnitude():
    assert retrieval.reciprocal_rank_fusion([(0, -5.), (1, -10.)], [(1, .9)]) == retrieval.reciprocal_rank_fusion([(0, 1000.), (1, 0.)], [(1, -999.)])


def test_gemini_cache_handles_expire_and_lru_is_bounded(monkeypatch):
    from core import llm_stream
    llm_stream._gemini_explicit_cache.clear()
    now = [0.]
    monkeypatch.setattr(llm_stream.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(llm_stream, "_GEMINI_CACHE_MAX_ENTRIES", 2)
    llm_stream._gemini_cache_store("a", "cached/a")
    llm_stream._gemini_cache_store("b", "cached/b")
    assert llm_stream._gemini_cache_lookup("a") == "cached/a"
    llm_stream._gemini_cache_store("c", "cached/c")
    assert llm_stream._gemini_cache_lookup("b") is None
    assert len(llm_stream._gemini_explicit_cache) == 2
    now[0] = 3600.
    assert llm_stream._gemini_cache_lookup("a") is None
    assert not llm_stream._gemini_explicit_cache


async def test_missing_provider_cache_retries_once_with_complete_system(monkeypatch):
    import copy
    import httpx
    from core import llm_stream
    from core.llm_router import LlmCallConfig
    cfg = LlmCallConfig("gemini", "synthetic-key", model="gemini-2.5-flash")
    system = "complete system " * 2000
    key = llm_stream._gemini_cache_key(cfg, system)
    llm_stream._gemini_cache_store(key, "cached/missing")
    async def ensure(*args):
        return "cached/missing"
    calls = []
    async def post(*args, **kwargs):
        calls.append(copy.deepcopy(kwargs))
        if len(calls) == 1:
            return httpx.Response(404, json={"error": {"status": "NOT_FOUND"}})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "answer"}]}}]})
    monkeypatch.setattr(llm_stream, "_gemini_ensure_explicit_cache", ensure)
    monkeypatch.setattr(llm_stream, "_gemini_post", post)
    text, _ = await llm_stream._gemini_complete_messages(cfg, system, "question", [])
    assert text == "answer" and len(calls) == 2
    assert calls[0]["body"]["cachedContent"] == "cached/missing"
    assert "cachedContent" not in calls[1]["body"]
    assert calls[1]["body"]["systemInstruction"]["parts"][0]["text"] == system
    assert llm_stream._gemini_cache_lookup(key) is None
