"""Proves and guards the confirmed HybridRetriever lifecycle problem (PR #91):

    NGramIndex narrows candidates to a *different* subset of fact_ids on every
    query (limit=50 out of a much larger corpus). `_get_hybrid_retriever()`
    treats "different candidate fact_id set" as "corpus changed" and rebuilds
    the singleton from scratch — reloading the sentence-transformer model and
    re-encoding every candidate's claim, even though the same facts (by
    fact_id) were already embedded on a previous call.

Uses a fake `sentence_transformers` module (the real package is an optional
dependency, not installed here) so the count of model loads / encode() calls
can be asserted without downloading a real model. The fake never touches
numpy: embeddings are plain lists with a `__matmul__` shim, so the test does
not depend on the `embeddings`/`retrieval` extras being installed.
"""
from __future__ import annotations

import sys
import types

import pytest

import core.hybrid_retriever as hr
import core.pipeline as pipeline


def _fake_vector(text: str) -> list[float]:
    """Deterministic, dependency-free stand-in for a sentence embedding."""
    return [((hash((text, i)) % 997) / 997.0) for i in range(6)]


class _FakeArray(list):
    """Just enough of the numpy ndarray surface for DenseRetriever.retrieve()."""

    def __matmul__(self, other: list[float]) -> list[float]:
        return [sum(a * b for a, b in zip(row, other)) for row in self]


class _FakeSentenceTransformer:
    """Stand-in for sentence_transformers.SentenceTransformer.

    Class-level counters so a test can assert how many times the *model* was
    constructed (expensive: real load is ~seconds) and how many claims were
    ever encoded (expensive: one forward pass per text), across many
    DenseRetriever instances.
    """

    instances = 0
    encoded_texts: list[str] = []

    def __init__(self, model_name: str) -> None:
        type(self).instances += 1
        self.model_name = model_name

    def encode(self, texts, normalize_embeddings: bool = True) -> _FakeArray:
        type(self).encoded_texts.extend(texts)
        return _FakeArray(_fake_vector(t) for t in texts)


@pytest.fixture
def fake_sentence_transformers(monkeypatch):
    """Install the fake module and reset its call counters."""
    _FakeSentenceTransformer.instances = 0
    _FakeSentenceTransformer.encoded_texts = []
    fake_module = types.ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = _FakeSentenceTransformer  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)
    # DenseRetriever/_load() caches availability, the loaded model, and every
    # fact's embedding at the CLASS level — intentionally, that persistence is
    # the fix under test. Reset all three per test so tests reusing the same
    # fact_id ranges (f0..f99) don't observe each other's cache warmth.
    monkeypatch.setattr(hr.DenseRetriever, "_AVAILABLE", None, raising=False)
    monkeypatch.setattr(hr.DenseRetriever, "_MODEL_CACHE", {}, raising=False)
    monkeypatch.setattr(hr.DenseRetriever, "_VECTOR_CACHE", {}, raising=False)
    yield _FakeSentenceTransformer


@pytest.fixture(autouse=True)
def reset_hybrid_singleton(monkeypatch):
    """Isolate pipeline's module-level HybridRetriever singleton per test."""
    monkeypatch.setattr(pipeline, "_HYBRID_RETRIEVER", None)
    monkeypatch.setattr(pipeline, "_HYBRID_DIRTY", True)
    monkeypatch.setattr(pipeline, "_HYBRID_FACTS_COUNT", 0)
    monkeypatch.setattr(pipeline, "_HYBRID_FACT_IDS", frozenset())
    yield


def _facts(ids: range) -> list[dict]:
    return [
        {"fact_id": f"f{i}", "claim": f"claim number {i} about topic {i % 7}",
         "source": "s", "confidence": 0.8}
        for i in ids
    ]


class TestNgramChurnRebuildsDenseFromScratch:
    """Reproduces the reported bug directly against DenseRetriever/HybridRetriever
    construction (bypassing NGram/FTS5 itself, which is an implementation detail —
    the defect is in how `_get_hybrid_retriever` reacts to a changed candidate set)."""

    def test_two_disjoint_ngram_candidate_sets_reuse_the_model_and_cached_vectors(
        self, fake_sentence_transformers
    ):
        """Same corpus, two different (same-size) NGram-narrowed candidate sets —
        as happens across two different queries against a large store. The model
        must load once; a fact's claim must be encoded at most once ever.
        """
        batch_a = _facts(range(0, 50))     # candidate set for query A
        batch_b = _facts(range(50, 100))   # disjoint candidate set for query B

        retriever_a = pipeline._get_hybrid_retriever(batch_a)
        retriever_b = pipeline._get_hybrid_retriever(batch_b)

        assert retriever_a is not None and retriever_b is not None
        assert fake_sentence_transformers.instances == 1, (
            "sentence-transformer model reloaded on a mere candidate-set change "
            f"(loaded {fake_sentence_transformers.instances}x) — this is the "
            "reported rebuild-storm: NGram narrows to a different subset on "
            "every query, so a naive rebuild reloads the model every time."
        )
        # Every claim seen so far must have been encoded — but never more than once.
        assert len(fake_sentence_transformers.encoded_texts) == len(
            set(fake_sentence_transformers.encoded_texts)
        ), "a fact's claim was re-encoded even though it was already cached"

    def test_revisiting_a_previously_seen_candidate_set_costs_zero_new_encodes(
        self, fake_sentence_transformers
    ):
        """Query A, then query B (disjoint candidates), then query A again
        (e.g. the user re-asks, or two concurrent queries share topic overlap).
        Revisiting facts already embedded must not re-encode them.
        """
        batch_a = _facts(range(0, 50))
        batch_b = _facts(range(50, 100))

        pipeline._get_hybrid_retriever(batch_a)
        encoded_after_a = len(fake_sentence_transformers.encoded_texts)

        pipeline._get_hybrid_retriever(batch_b)
        encoded_after_b = len(fake_sentence_transformers.encoded_texts)
        assert encoded_after_b == encoded_after_a + 50

        pipeline._get_hybrid_retriever(batch_a)  # revisit — must be free
        encoded_after_a_again = len(fake_sentence_transformers.encoded_texts)
        assert encoded_after_a_again == encoded_after_b, (
            "re-visiting an already-embedded candidate set triggered new "
            "encode() calls — the dense vector cache is not keyed by fact_id"
        )
        assert fake_sentence_transformers.instances == 1

    def test_revisited_candidate_set_yields_byte_identical_results(
        self, fake_sentence_transformers
    ):
        """The lifecycle fix must be a pure caching optimization: retrieving
        the same candidate set again — after an unrelated corpus was cached
        in between — must return exactly the same ranking/scores, not merely
        'doesn't crash'. This is the guard against cross-fact cache
        contamination (e.g. a fact_id collision reusing the wrong vector)."""
        batch_a = _facts(range(0, 10))

        baseline_retriever = pipeline._get_hybrid_retriever(batch_a)
        assert baseline_retriever is not None
        baseline = [
            (r.fact_id, round(r.final_score, 6))
            for r in baseline_retriever.retrieve("claim number 3", top_k=10)
        ]

        pipeline._get_hybrid_retriever(_facts(range(1000, 1050)))  # unrelated warm-up
        revisited_retriever = pipeline._get_hybrid_retriever(batch_a)
        assert revisited_retriever is not None
        revisited = [
            (r.fact_id, round(r.final_score, 6))
            for r in revisited_retriever.retrieve("claim number 3", top_k=10)
        ]

        assert revisited == baseline
