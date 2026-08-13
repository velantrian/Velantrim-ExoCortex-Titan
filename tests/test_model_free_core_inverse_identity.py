from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from core.model_free_core import (
    L2Evidence,
    L2Relation,
    ModelFreeCore,
    ModelFreeGraphReadError,
)


def _relation(
    relation_id: str,
    from_fact_id: str,
    to_fact_id: str,
    relation_type: str,
    *,
    inverse_of: str | None = None,
    inference_source: str | None = "manual",
) -> L2Relation:
    metadata: dict[str, Any] = {}
    if inverse_of is not None:
        metadata["inverse_of"] = inverse_of
    return L2Relation(
        relation_id=relation_id,
        from_fact_id=from_fact_id,
        to_fact_id=to_fact_id,
        relation_type=relation_type,
        confidence=0.9,
        knowledge_status="known",
        truth_status="validated",
        review_state="approved",
        inference_source=inference_source,
        evidence_ref=None,
        metadata=metadata,
    )


def test_inverse_identity_accepts_one_reciprocal_backlink() -> None:
    forward = _relation("rel-forward", "fact-a", "fact-b", "causes")
    inverse = _relation(
        "rel-inverse",
        "fact-b",
        "fact-a",
        "caused_by",
        inverse_of="rel-forward",
    )

    ModelFreeCore._validate_inverse_identity(
        {forward.relation_id: forward, inverse.relation_id: inverse}
    )


@pytest.mark.parametrize(
    ("relations", "match"),
    [
        (
            [_relation("rel-inverse", "fact-b", "fact-a", "caused_by", inverse_of="missing")],
            "target is missing",
        ),
        (
            [
                _relation("rel-forward", "fact-a", "fact-c", "causes"),
                _relation(
                    "rel-inverse",
                    "fact-b",
                    "fact-a",
                    "caused_by",
                    inverse_of="rel-forward",
                ),
            ],
            "not the reciprocal tuple",
        ),
        (
            [
                _relation("rel-forward", "fact-a", "fact-b", "causes"),
                _relation(
                    "rel-inverse-1",
                    "fact-b",
                    "fact-a",
                    "caused_by",
                    inverse_of="rel-forward",
                ),
                _relation(
                    "rel-inverse-2",
                    "fact-b",
                    "fact-a",
                    "caused_by",
                    inverse_of="rel-forward",
                ),
            ],
            "multiple backlinks",
        ),
    ],
)
def test_inverse_identity_rejects_unsafe_collapse_keys(
    relations: list[L2Relation], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        ModelFreeCore._validate_inverse_identity(
            {relation.relation_id: relation for relation in relations}
        )


@dataclass
class _RawRelation:
    relation_id: str
    from_fact_id: str
    to_fact_id: str
    relation_type: str
    confidence: float = 0.9
    knowledge_status: str = "known"
    truth_status: str = "validated"
    review_state: str = "approved"
    inference_source: str | None = "manual"
    evidence_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class _DanglingGraph:
    def get_relations_from(self, fact_id: str) -> list[_RawRelation]:
        if fact_id != "fact-a":
            return []
        return [
            _RawRelation(
                relation_id="rel-inverse",
                from_fact_id="fact-a",
                to_fact_id="fact-b",
                relation_type="causes",
                metadata={"inverse_of": "missing-forward"},
            )
        ]

    def get_relations_to(self, fact_id: str) -> list[_RawRelation]:
        return []


class _PipelineWithDanglingInverse:
    @staticmethod
    def _peek_causal_graph() -> _DanglingGraph:
        return _DanglingGraph()

    @staticmethod
    def get_facts_by_ids(fact_ids: list[str]) -> list[dict[str, Any]]:
        raise AssertionError("inverse identity validation must run before endpoint admission")


def test_collect_relations_converts_dangling_inverse_to_graph_read_failure() -> None:
    evidence = (
        L2Evidence(
            fact_id="fact-a",
            claim="a",
            source="local",
            epistemic_state="Validated",
            confidence=0.9,
            retrieval_score=1.0,
            claim_type="WORLD_FACT",
            origin_type="INGESTED",
            truth_status="VERIFIED",
        ),
    )

    with pytest.raises(ModelFreeGraphReadError):
        ModelFreeCore._collect_relations(
            _PipelineWithDanglingInverse,
            evidence,
            cognitive_mode="BALANCED",
        )
