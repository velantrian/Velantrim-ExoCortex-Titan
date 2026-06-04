"""Tests for core.hybrid_retriever — Velantrim v8.3.1."""

import pytest

from core.hybrid_retriever import (
    BM25Retriever,
    DenseRetriever,
    HybridRetriever,
    RetrievedFact,
    reciprocal_rank_fusion,
)


@pytest.fixture
def sample_facts():
    return [
        {
            "fact_id": "f1",
            "claim": "Квантовая запутанность связывает частицы на расстоянии",
            "source": "physics_textbook",
            "confidence": 0.95,
            "metadata": {},
        },
        {
            "fact_id": "f2",
            "claim": "Эйнштейн назвал это spooky action at a distance",
            "source": "history_of_physics",
            "confidence": 0.90,
            "metadata": {},
        },
        {
            "fact_id": "f3",
            "claim": "Python — это интерпретируемый язык программирования",
            "source": "wikipedia",
            "confidence": 0.85,
            "metadata": {},
        },
        {
            "fact_id": "f4",
            "claim": "Bell experiment подтвердил квантовую нелокальность",
            "source": "nature_paper",
            "confidence": 0.92,
            "metadata": {},
        },
    ]


# ─── BM25 ──────────────────────────────────────────────────────────────────

class TestBM25Retriever:
    def test_creates_index(self, sample_facts):
        bm25 = BM25Retriever(sample_facts)
        assert bm25 is not None

    def test_retrieve_returns_tuples(self, sample_facts):
        bm25 = BM25Retriever(sample_facts)
        results = bm25.retrieve("квантовая", top_k=2)
        assert all(isinstance(r, tuple) for r in results)
        assert all(len(r) == 2 for r in results)

    def test_retrieve_ranks_by_score(self, sample_facts):
        bm25 = BM25Retriever(sample_facts)
        results = bm25.retrieve("квантовая запутанность", top_k=4)
        # Должен вернуть факты с "квантовая" выше python
        if len(results) >= 2:
            assert results[0][1] >= results[1][1]

    def test_empty_query_returns_empty(self, sample_facts):
        bm25 = BM25Retriever(sample_facts)
        results = bm25.retrieve("", top_k=5)
        assert results == []

    def test_no_match_returns_empty(self, sample_facts):
        bm25 = BM25Retriever(sample_facts)
        results = bm25.retrieve("zzzzzzz_nonsense_xyz", top_k=5)
        assert len(results) == 0


# ─── DenseRetriever ────────────────────────────────────────────────────────

class TestDenseRetriever:
    def test_graceful_degradation_without_sentence_transformers(self, sample_facts):
        """Если sentence-transformers не установлен — должно работать без падения."""
        dense = DenseRetriever(sample_facts)
        # Available может быть True (если установлен) или False
        assert isinstance(dense.available, bool)

    def test_retrieve_returns_list(self, sample_facts):
        dense = DenseRetriever(sample_facts)
        results = dense.retrieve("квантовая физика", top_k=3)
        assert isinstance(results, list)

    def test_unavailable_returns_empty(self, sample_facts):
        dense = DenseRetriever(sample_facts)
        if not dense.available:
            assert dense.retrieve("anything", top_k=5) == []


# ─── RRF ───────────────────────────────────────────────────────────────────

class TestRRF:
    def test_rrf_merges_two_lists(self):
        list_a = [(0, 1.0), (1, 0.8), (2, 0.5)]
        list_b = [(2, 0.9), (1, 0.7), (3, 0.4)]
        result = reciprocal_rank_fusion(list_a, list_b)
        assert len(result) == 4  # union: 0, 1, 2, 3

    def test_rrf_index_2_ranked_high(self):
        """idx=2 на 1 месте в list_b и на 3 в list_a — должен быть в топе."""
        list_a = [(0, 1.0), (1, 0.8), (2, 0.5)]
        list_b = [(2, 0.9), (1, 0.7), (3, 0.4)]
        result = reciprocal_rank_fusion(list_a, list_b)
        # idx=2 имеет высокие позиции в обоих → должен быть наверху
        top_idx = result[0][0]
        assert top_idx in (1, 2)  # 1 и 2 оба сильны

    def test_rrf_single_list_preserves_order(self):
        single = [(0, 1.0), (1, 0.5), (2, 0.1)]
        result = reciprocal_rank_fusion(single)
        # Порядок сохраняется
        assert [r[0] for r in result] == [0, 1, 2]

    def test_rrf_k_parameter(self):
        """Меньший k = более резкое затухание ранков."""
        list_a = [(0, 1.0), (1, 0.5)]
        list_b = [(1, 0.9), (2, 0.4)]
        r_small_k = reciprocal_rank_fusion(list_a, list_b, k=5)
        r_large_k = reciprocal_rank_fusion(list_a, list_b, k=100)
        # Разные k → возможно разные score, но факты те же
        assert sorted([r[0] for r in r_small_k]) == sorted([r[0] for r in r_large_k])


# ─── HybridRetriever ───────────────────────────────────────────────────────

class TestHybridRetriever:
    def test_creates_with_facts(self, sample_facts):
        retriever = HybridRetriever(sample_facts)
        assert retriever is not None

    def test_retrieve_returns_retrieved_facts(self, sample_facts):
        retriever = HybridRetriever(sample_facts, use_reranker=False)
        results = retriever.retrieve("квантовая", top_k=2)
        assert all(isinstance(r, RetrievedFact) for r in results)

    def test_retrieve_respects_top_k(self, sample_facts):
        retriever = HybridRetriever(sample_facts, use_reranker=False)
        results = retriever.retrieve("квантовая", top_k=2)
        assert len(results) <= 2

    def test_retrieve_as_dicts(self, sample_facts):
        retriever = HybridRetriever(sample_facts, use_reranker=False)
        results = retriever.retrieve_as_dicts("квантовая", top_k=2)
        for r in results:
            assert "fact_id" in r
            assert "claim" in r
            assert "source" in r
            assert "confidence" in r
            assert "score" in r

    def test_retrieve_quantum_query(self, sample_facts):
        """Запрос про квантовую физику не должен вернуть про Python."""
        retriever = HybridRetriever(sample_facts, use_reranker=False)
        results = retriever.retrieve("квантовая запутанность", top_k=3)
        if results:
            # Топ-1 не должен быть про Python
            assert "Python" not in results[0].claim

    def test_empty_facts_no_crash(self):
        retriever = HybridRetriever([], use_reranker=False)
        results = retriever.retrieve("anything", top_k=5)
        assert results == []

    def test_unknown_query_returns_few_results(self, sample_facts):
        retriever = HybridRetriever(sample_facts, use_reranker=False)
        results = retriever.retrieve("zzzzzz_xyz_nonsense", top_k=5)
        # Может вернуть 0 или несколько (если dense дал что-то)
        assert isinstance(results, list)


# ─── RetrievedFact dataclass ───────────────────────────────────────────────

class TestRetrievedFact:
    def test_creates_with_required_fields(self):
        f = RetrievedFact(
            fact_id="f1", claim="test", source="src", confidence=0.5,
        )
        assert f.fact_id == "f1"
        assert f.bm25_score == 0.0  # default
        assert f.dense_score == 0.0
        assert f.metadata == {}

    def test_to_dict_format(self):
        f = RetrievedFact(
            fact_id="f1", claim="test", source="src", confidence=0.5,
            final_score=0.85,
        )
        d = f.to_dict()
        assert d["fact_id"] == "f1"
        assert d["score"] == 0.85
        assert "metadata" in d
