from dataclasses import replace

import pytest

from core.knowledge_capsule import SourceSpan
from core.reader_core_contracts import RelationKind, stable_reader_core_id
from core.section_relations import (
    ClaimEndpoint,
    CrossSectionRelationCandidate,
    CrossSectionRelationSet,
    SECTION_RELATION_SCHEMA_VERSION,
    SectionRelationError,
    relation_pair_key,
)


def _span(claim_id: str, start: int) -> SourceSpan:
    text = "alpha beta gamma delta"
    return SourceSpan.from_text(
        document_id="doc",
        raw_text=text,
        start_offset=start,
        end_offset=start + 5,
        source_revision="rev",
        span_id=claim_id,
    )


def _endpoint(claim_id: str, start: int, card_id: str) -> ClaimEndpoint:
    return ClaimEndpoint(
        document_id="doc",
        source_revision="rev",
        structure_map_id="map",
        plan_id="plan",
        card_id=card_id,
        section_id=f"section-{card_id}",
        unit_id=f"unit-{card_id}",
        claim_id=claim_id,
        source_spans=(_span(claim_id, start),),
    )


def _relation() -> CrossSectionRelationCandidate:
    return CrossSectionRelationCandidate.create(
        detector_id="fixture",
        detector_version="1",
        kind=RelationKind.SUPPORTS,
        source=_endpoint("claim-a", 0, "card-a"),
        target=_endpoint("claim-b", 6, "card-b"),
        reason_code="explicit_fixture_support",
        evidence_spans=(_span("claim-a", 0), _span("claim-b", 6)),
    )


def test_relation_is_directed_and_self_verifying() -> None:
    relation = _relation()
    assert relation.source.claim_id == "claim-a"
    assert relation.target.claim_id == "claim-b"
    with pytest.raises(SectionRelationError, match="relation_id"):
        replace(relation, reason_code="forged")


def test_relation_pair_direction_changes_key() -> None:
    assert relation_pair_key("a", "b") != relation_pair_key("b", "a")
    with pytest.raises(SectionRelationError, match="self-loops"):
        relation_pair_key("a", "a")


def test_relation_set_uses_explicit_evaluated_pair_denominator() -> None:
    relation = _relation()
    claims = ("claim-a", "claim-b", "claim-c")
    pairs = (relation_pair_key("claim-a", "claim-b"),)
    relation_set_id = stable_reader_core_id(
        "cross-section-relation-set",
        {
            "schema_version": SECTION_RELATION_SCHEMA_VERSION,
            "document_id": "doc",
            "source_revision": "rev",
            "structure_map_id": "map",
            "plan_id": "plan",
            "known_claim_ids": list(claims),
            "evaluated_pair_keys": list(pairs),
            "relation_ids": [relation.relation_id],
        },
    )
    relation_set = CrossSectionRelationSet(
        relation_set_id=relation_set_id,
        schema_version=SECTION_RELATION_SCHEMA_VERSION,
        document_id="doc",
        source_revision="rev",
        structure_map_id="map",
        plan_id="plan",
        known_claim_ids=claims,
        evaluated_pair_keys=pairs,
        candidates=(relation,),
    )
    assert relation_set.relation_denominator == 1
    assert len(relation_set.known_claim_ids) == 3


def test_duplicate_directed_relation_is_rejected() -> None:
    relation = _relation()
    claims = ("claim-a", "claim-b")
    pairs = (relation_pair_key("claim-a", "claim-b"),)
    relation_set_id = stable_reader_core_id(
        "cross-section-relation-set",
        {
            "schema_version": SECTION_RELATION_SCHEMA_VERSION,
            "document_id": "doc",
            "source_revision": "rev",
            "structure_map_id": "map",
            "plan_id": "plan",
            "known_claim_ids": list(claims),
            "evaluated_pair_keys": list(pairs),
            "relation_ids": [relation.relation_id, relation.relation_id],
        },
    )
    with pytest.raises(SectionRelationError, match="relation IDs"):
        CrossSectionRelationSet(
            relation_set_id=relation_set_id,
            schema_version=SECTION_RELATION_SCHEMA_VERSION,
            document_id="doc",
            source_revision="rev",
            structure_map_id="map",
            plan_id="plan",
            known_claim_ids=claims,
            evaluated_pair_keys=pairs,
            candidates=(relation, relation),
        )
