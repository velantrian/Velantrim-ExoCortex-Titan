"""Follow-up to the DenseRetriever lifecycle fix (PR #91/#95).

`DenseRetriever._VECTOR_CACHE` used to key solely on `fact_id`. That let an
edited fact (same fact_id, changed claim) or a runtime embedding-model swap
silently reuse a stale — or wrong-model — embedding: a correctness bug, not
just a missed-cache-hit performance one.

The cache key is now `(model_name, fact_id, sha256(claim))`, so either axis
changing invalidates the old entry automatically, while an unchanged fact
still gets its cache hit. The cache is also now bounded with LRU eviction so
an ever-growing set of distinct claims can't grow it without limit.

Uses a dependency-free fake `sentence_transformers` module (the real package
is an optional extra, not installed here), same technique as
tests/test_hybrid_retriever_lifecycle.py and tests/test_retrieval_routing.py.
"""
from __future__ import annotations

import sys
import types

import pytest

import core.hybrid_retriever as hr


class _FakeSentenceTransformer:
    """Stand-in for sentence_transformers.SentenceTransformer."""

    encode_calls = 0
    encoded_texts: list[str] = []

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def encode(self, texts, normalize_embeddings: bool = True):
        type(self).encode_calls += 1
        type(self).encoded_texts.extend(texts)
        return [
            [((hash((self.model_name, t, i)) % 997) / 997.0) for i in range(6)]
            for t in texts
        ]


@pytest.fixture
def fake_dense(monkeypatch):
    """Install the fake backend and reset DenseRetriever's process-persistent
    caches (plain dicts, matching production — no OrderedDict required)."""
    _FakeSentenceTransformer.encode_calls = 0
    _FakeSentenceTransformer.encoded_texts = []
    fake_module = types.ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = _FakeSentenceTransformer  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)
    monkeypatch.setattr(hr.DenseRetriever, "_AVAILABLE", None, raising=False)
    monkeypatch.setattr(hr.DenseRetriever, "_MODEL_CACHE", {}, raising=False)
    monkeypatch.setattr(hr.DenseRetriever, "_VECTOR_CACHE", {}, raising=False)
    yield _FakeSentenceTransformer


# ─── 1. claim changed under the same fact_id -> re-encoded ────────────────

def test_claim_change_under_same_fact_id_invalidates_cached_embedding(fake_dense):
    v1 = [{"fact_id": "f1", "claim": "вода кипит при 100 градусах"}]
    hr.DenseRetriever(v1, model_name="model-a")
    assert fake_dense.encode_calls == 1
    assert len(hr.DenseRetriever._VECTOR_CACHE) == 1

    v2 = [{"fact_id": "f1", "claim": "вода кипит при 90 градусах"}]  # edited claim, same id
    hr.DenseRetriever(v2, model_name="model-a")
    assert fake_dense.encode_calls == 2, (
        "an edited claim under the same fact_id must be re-encoded, not "
        "silently served the old claim's stale embedding"
    )
    assert len(hr.DenseRetriever._VECTOR_CACHE) == 2, (
        "old and new claim embeddings must coexist under distinct keys"
    )


# ─── 2. model_name changed -> new embedding used ──────────────────────────

def test_model_name_change_does_not_reuse_other_models_embedding(fake_dense):
    fact = [{"fact_id": "f1", "claim": "вода кипит при 100 градусах"}]
    hr.DenseRetriever(fact, model_name="model-a")
    assert fake_dense.encode_calls == 1

    hr.DenseRetriever(fact, model_name="model-b")  # same fact_id + claim, different model
    assert fake_dense.encode_calls == 2, (
        "switching the embedding model must not reuse a vector computed by "
        "a different model"
    )
    assert len(hr.DenseRetriever._VECTOR_CACHE) == 2, (
        "both models' embeddings for this fact must be cached independently"
    )


# ─── 3. same claim + model_name -> embedding reused ───────────────────────

def test_unchanged_claim_and_model_reuses_cached_embedding(fake_dense):
    fact = [{"fact_id": "f1", "claim": "вода кипит при 100 градусах"}]
    hr.DenseRetriever(fact, model_name="model-a")
    assert fake_dense.encode_calls == 1

    # Fresh dict/list instances, identical content -> must still hit cache.
    same_fact_again = [{"fact_id": "f1", "claim": "вода кипит при 100 градусах"}]
    hr.DenseRetriever(same_fact_again, model_name="model-a")
    assert fake_dense.encode_calls == 1, (
        "identical fact_id + claim + model_name must reuse the cached embedding"
    )
    assert len(hr.DenseRetriever._VECTOR_CACHE) == 1


# ─── bonus: cache key is genuinely a function of all three axes ───────────

def test_cache_key_changes_with_each_axis_independently():
    base = hr.DenseRetriever._cache_key("model-a", "f1", "claim text")
    diff_model = hr.DenseRetriever._cache_key("model-b", "f1", "claim text")
    diff_fact = hr.DenseRetriever._cache_key("model-a", "f2", "claim text")
    diff_claim = hr.DenseRetriever._cache_key("model-a", "f1", "different claim")

    assert len({base, diff_model, diff_fact, diff_claim}) == 4
    # Same inputs -> same key (deterministic), so a genuine cache hit is possible.
    assert hr.DenseRetriever._cache_key("model-a", "f1", "claim text") == base


# ─── bounded growth: cache doesn't grow without limit ─────────────────────

def test_vector_cache_is_bounded_and_evicts_least_recently_used(fake_dense, monkeypatch):
    monkeypatch.setattr(hr.DenseRetriever, "_VECTOR_CACHE_MAX_ENTRIES", 3, raising=False)

    for i in range(5):
        hr.DenseRetriever([{"fact_id": f"f{i}", "claim": f"claim number {i}"}],
                          model_name="model-a")

    cache = hr.DenseRetriever._VECTOR_CACHE
    assert len(cache) <= 3, "cache must never exceed its configured bound"

    remaining_fact_ids = {key.split("\0")[1] for key in cache}
    assert remaining_fact_ids == {"f2", "f3", "f4"}, (
        "eviction must drop the least-recently-used entries (f0, f1), "
        "keeping the most recently built ones"
    )


def test_revisiting_an_entry_protects_it_from_eviction(fake_dense, monkeypatch):
    monkeypatch.setattr(hr.DenseRetriever, "_VECTOR_CACHE_MAX_ENTRIES", 2, raising=False)

    hr.DenseRetriever([{"fact_id": "f0", "claim": "claim 0"}], model_name="model-a")
    hr.DenseRetriever([{"fact_id": "f1", "claim": "claim 1"}], model_name="model-a")
    # Touch f0 again (cache hit) -> it becomes the most-recently-used entry.
    hr.DenseRetriever([{"fact_id": "f0", "claim": "claim 0"}], model_name="model-a")
    assert fake_dense.encode_calls == 2, "revisiting f0 must be a cache hit, not a re-encode"

    # f1 is now the least-recently-used; adding f2 must evict f1, not f0.
    hr.DenseRetriever([{"fact_id": "f2", "claim": "claim 2"}], model_name="model-a")

    remaining_fact_ids = {key.split("\0")[1] for key in hr.DenseRetriever._VECTOR_CACHE}
    assert remaining_fact_ids == {"f0", "f2"}
