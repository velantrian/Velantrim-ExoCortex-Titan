"""Focused regression tests for the T1 answer-context relevance boundary."""
from __future__ import annotations

from core.facts_pack import FactsPackBuilder


def _candidate(*, claim: str, score: float, canonical_record: bool = False) -> dict:
    return {
        "fact_id": "t1_candidate",
        "claim": claim,
        "source": "t1",
        "confidence": 0.95,
        "epistemic_state": "Validated",
        "retrieval_score": score,
        "origin": "hybrid_retriever",
        "canonical_record": canonical_record,
    }


def test_rounded_single_rank_hybrid_without_anchor_is_excluded() -> None:
    pack = (
        FactsPackBuilder("BALANCED")
        .add_facts([
            _candidate(
                claim="The active project codename is T1_COBALT_ORCHARD_7F31.",
                score=0.0164,
            )
        ])
        .build("Tell me the capital of an imaginary planet called Nereid-9.")
    )

    assert pack.facts == []
    assert len(pack.excluded_facts) == 1
    assert "lexical relevance anchor" in pack.excluded_facts[0].reason


def test_rounded_two_list_rank_with_only_stopword_overlap_is_excluded() -> None:
    pack = (
        FactsPackBuilder("BALANCED")
        .add_facts([
            _candidate(
                claim="The active project codename is T1_COBALT_ORCHARD_7F31.",
                score=0.0328,
            )
        ])
        .build("Tell me the capital of an imaginary planet called Nereid-9.")
    )

    assert pack.facts == []
    assert len(pack.excluded_facts) == 1
    assert "lexical relevance anchor" in pack.excluded_facts[0].reason


def test_same_weak_hybrid_with_lexical_anchor_remains_usable() -> None:
    pack = (
        FactsPackBuilder("BALANCED")
        .add_facts([
            _candidate(
                claim="The active project codename is T1_COBALT_ORCHARD_7F31.",
                score=0.0164,
            )
        ])
        .build("What is the active project codename?")
    )

    assert [fact.fact_id for fact in pack.facts] == ["t1_candidate"]
    assert pack.excluded_facts == []


def test_two_list_rank_with_meaningful_lexical_anchor_remains_usable() -> None:
    pack = (
        FactsPackBuilder("BALANCED")
        .add_facts([
            _candidate(
                claim="The active project codename is T1_COBALT_ORCHARD_7F31.",
                score=0.0328,
            )
        ])
        .build("What is the active project codename?")
    )

    assert [fact.fact_id for fact in pack.facts] == ["t1_candidate"]
    assert pack.excluded_facts == []


def test_noncanonical_zero_score_candidate_keeps_legacy_behavior() -> None:
    pack = (
        FactsPackBuilder("BALANCED")
        .add_facts([
            _candidate(
                claim="A candidate outside the T1 weakest-RRF shape.",
                score=0.0,
            )
        ])
        .build("A query with deliberately unrelated vocabulary")
    )

    assert [fact.fact_id for fact in pack.facts] == ["t1_candidate"]
    assert pack.excluded_facts == []


def test_canonical_zero_score_without_anchor_is_excluded() -> None:
    pack = (
        FactsPackBuilder("BALANCED")
        .add_facts([
            _candidate(
                claim="The active project codename is T1_COBALT_ORCHARD_7F31.",
                score=0.0,
                canonical_record=True,
            )
        ])
        .build("Tell me the capital of an imaginary planet called Nereid-9.")
    )

    assert pack.facts == []
    assert len(pack.excluded_facts) == 1
    assert "lexical relevance anchor" in pack.excluded_facts[0].reason


def test_canonical_zero_score_with_anchor_remains_usable() -> None:
    pack = (
        FactsPackBuilder("BALANCED")
        .add_facts([
            _candidate(
                claim="The active project codename is T1_COBALT_ORCHARD_7F31.",
                score=0.0,
                canonical_record=True,
            )
        ])
        .build("What is the active project codename?")
    )

    assert [fact.fact_id for fact in pack.facts] == ["t1_candidate"]
    assert pack.excluded_facts == []


def test_guard_does_not_reject_stronger_semantic_candidate_only_for_lack_of_anchor() -> None:
    pack = (
        FactsPackBuilder("BALANCED")
        .add_facts([
            _candidate(
                claim="A semantically related statement expressed with different vocabulary.",
                score=0.02,
            )
        ])
        .build("A conceptually matching query with no shared content terms")
    )

    assert [fact.fact_id for fact in pack.facts] == ["t1_candidate"]