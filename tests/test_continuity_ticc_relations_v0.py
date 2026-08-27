from __future__ import annotations

from datetime import UTC, datetime

import pytest

from core.continuity.contracts import (
    ActorKind,
    ActorRef,
    AssertionRecord,
    AssertionRelationType,
    OriginType,
    SubjectKind,
    SubjectRef,
)
from core.continuity.state_reconciler import (
    ProjectionStatus,
    StateReason,
    StateReconciler,
)
from core.continuity.ticc_relations import (
    TICCRelationError,
    TICCRelationRequest,
    materialize_exact_relation,
)

USER = ActorRef("actor:user", ActorKind.HUMAN)
OPERATOR = ActorRef("actor:operator", ActorKind.OPERATOR)
PROJECT = SubjectRef("project:titan", SubjectKind.PROJECT)
AS_OF = datetime(2026, 8, 27, 16, 0, tzinfo=UTC)


def _assertion(value: str, *, hour: int, source: str) -> AssertionRecord:
    point = datetime(2026, 8, 27, hour, 0, tzinfo=UTC)
    return AssertionRecord.create(
        subject_ref=PROJECT,
        predicate="memory_policy",
        value=value,
        origin_type=OriginType.USER_STATED,
        source_refs=(source,),
        asserted_by=USER,
        valid_from=point,
        recorded_at=point,
    )


def _request(
    relation_type: AssertionRelationType,
    source: AssertionRecord,
    target: AssertionRecord,
) -> TICCRelationRequest:
    return TICCRelationRequest(
        relation_type=relation_type,
        source_assertion=source,
        target_assertion=target,
        evidence_refs=("source:explicit-relation",),
        actor_ref=OPERATOR,
        created_at=AS_OF,
    )


def test_exact_correction_composes_with_existing_state_reconciler() -> None:
    old = _assertion("store_summaries", hour=8, source="source:old")
    corrected = _assertion("keep_original_records", hour=9, source="source:corrected")

    relation_result = materialize_exact_relation(
        _request(AssertionRelationType.CORRECTS, corrected, old)
    )
    assert relation_result.relation is not None

    result = StateReconciler().reconcile(
        [old, corrected],
        [relation_result.relation],
        as_of=AS_OF,
    )
    projection = result.projections[0]

    assert projection.status is ProjectionStatus.CURRENT
    assert projection.selected_assertion_ref == corrected.assertion_id
    assert projection.superseded_assertion_refs == (old.assertion_id,)
    assert StateReason.EXPLICIT_CORRECTION in projection.reason_codes


def test_exact_retraction_composes_without_inventing_replacement_state() -> None:
    old = _assertion("store_summaries", hour=8, source="source:old")
    retractor = _assertion("retract_previous_policy", hour=9, source="source:retractor")

    relation_result = materialize_exact_relation(
        _request(AssertionRelationType.RETRACTS, retractor, old)
    )
    assert relation_result.relation is not None

    result = StateReconciler().reconcile(
        [old, retractor],
        [relation_result.relation],
        as_of=AS_OF,
    )
    projection = result.projections[0]

    assert old.assertion_id in projection.retracted_assertion_refs
    assert StateReason.EXPLICIT_RETRACTION in projection.reason_codes


def test_relation_adapter_rejects_non_lifecycle_relation_types() -> None:
    first = _assertion("a", hour=8, source="source:a")
    second = _assertion("b", hour=9, source="source:b")

    with pytest.raises(TICCRelationError, match="only CORRECTS/RETRACTS"):
        _request(AssertionRelationType.SUPPORTS, second, first)


def test_relation_adapter_rejects_self_target() -> None:
    assertion = _assertion("a", hour=8, source="source:a")

    with pytest.raises(TICCRelationError, match="endpoints must be distinct"):
        _request(AssertionRelationType.CORRECTS, assertion, assertion)


def test_relation_adapter_has_no_target_discovery_surface() -> None:
    forbidden = (
        "search_target",
        "retrieve_target",
        "semantic_match",
        "llm_classify",
        "infer_relation",
        "write_canon",
        "authorize_action",
    )
    import core.continuity.ticc_relations as module

    for name in forbidden:
        assert not hasattr(module, name)
