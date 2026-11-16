"""Lexical matching is independent of Okapi IDF sign and optional dense models."""
import pytest

from core.hybrid_retriever import BM25Retriever


@pytest.mark.parametrize("claims", [["вода кипит"], ["вода кипит", "вода замерзает"]])
def test_frequent_terms_survive_nonpositive_okapi_scores(claims):
    pytest.importorskip("rank_bm25")
    retriever = BM25Retriever([{"claim": c} for c in claims])
    assert {i for i, _ in retriever.retrieve("вода")} == set(range(len(claims)))
    assert retriever.retrieve("квазар") == []


def test_zero_score_nonmatch_cannot_displace_negative_match():
    r = BM25Retriever([{"claim": "вода"}, {"claim": "квазар"}])
    class NegativeScores:
        def get_scores(self, tokens):
            return [-1., 0.]
    r._bm25 = NegativeScores()
    assert r.retrieve("вода", top_k=1) == [(0, -1.)]
