from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256

import pytest

from core.continuity.contracts import (
    ActorKind,
    ActorRef,
    AssertionRecord,
    AssertionRelationType,
    InteractionEventType,
    OriginType,
    SubjectKind,
    SubjectRef,
)
from core.continuity.state_reconciler import (
    ProjectionStatus,
    StateReason,
    StateReconciler,
)
from core.continuity.ticc import (
    ConversationSourceTurn,
    TICCConfig,
    TICCDisposition,
    TICCSemanticAnnotation,
    TICCSemanticModality,
    TICCSourceSpan,
    capture_turn,
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


def _assertion(
    value: str,
    *,
    hour: int,
    source: str,
    actor: ActorRef = USER,
    origin: OriginType = OriginType.USER_STATED,
) -> AssertionRecord:
    point = datetime(2026, 8, 27, hour, 0, tzinfo=UTC)
    return AssertionRecord.create(
        subject_ref=PROJECT,
        predicate="memory_policy",
        value=value,
        origin_type=origin,
        source_refs=(source,),
        asserted_by=actor,
        valid_from=point,
        recorded_at=point,
    )


def _candidate(modality: TICCSemanticModality, text: str):
    turn = ConversationSourceTurn(
        turn_ref=f"turn:{modality.value}",
        session_ref="session:relations",
        sequence=1,
        event_type=InteractionEventType.MESSAGE,
        actor_ref=USER,
        subject_refs=(PROJECT,),
        raw_text=text,
        occurred_at=AS_OF,
        recorded_at=AS_OF,
        raw_text_sha256=sha256(text.encode("utf-8")).hexdigest(),
    )
    span = TICCSourceSpan(
        source_turn_ref=turn.turn_ref,
        start_offset=0,
        end_offset=len(text),
        slice_sha256=sha256(text.encode("utf-8")).hexdigest(),
    )
    result = capture_turn(
        turn=turn,
        annotation=TICCSemanticAnnotation(
            modality=modality,
            source_span=span,
            origin_type=OriginType.USER_STATED,
        ),
        config=TICCConfig(enabled=True, scenario_id="ticc-relations-v0"),
        created_at=AS_OF,
    )
    candidate = result.candidates[0]
    assert candidate.disposition is TICCDisposition.DEFERRED
    return candidate


def _request(
    relation_type: AssertionRelationType,
    source_candidate,
    source: AssertionRecord,
    target: AssertionRecord,
    *,
    evidence_refs: tuple[str, ...] | None = None,
) -> TICCRelationRequest:
    return TICCRelationRequest(
        relation_type=relation_type,
        source_candidate=source_candidate,
        source_assertion=source,
        target_assertion=target,
        evidence_refs=evidence_refs or (source_candidate.source_ref,),
        actor_ref=OPERATOR,
        created_at=AS_OF,
    )


def test_exact_correction_composes_with_existing_state_reconciler() -> None:
    candidate = _candidate(
        TICCSemanticModality.CORRECTION,
        "Replace the earlier rule with original records only.",
    )
    old = _assertion("store_summaries", hour=8, source="source:old")
    corrected = _assertion(
        "keep_original_records", hour=9, source=candidate.source_ref
    )

    relation_result = materialize_exact_relation(
        _request(AssertionRelationType.CORRECTS, candidate, corrected, old)
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
    candidate = _candidate(
        TICCSemanticModality.RETRACTION,
        "I retract the earlier storage rule.",
    )
    old = _assertion("store_summaries", hour=8, source="source:old")
    retractor = _assertion(
        "retract_previous_policy", hour=9, source=candidate.source_ref
    )

    relation_result = materialize_exact_relation(
        _request(AssertionRelationType.RETRACTS, candidate, retractor, old)
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
    candidate = _candidate(TICCSemanticModality.CORRECTION, "Correct the earlier rule.")
    first = _assertion("a", hour=8, source="source:a")
    second = _assertion("b", hour=9, source=candidate.source_ref)

    with pytest.raises(TICCRelationError, match="only CORRECTS/RETRACTS"):
        _request(AssertionRelationType.SUPPORTS, candidate, second, first)


def test_relation_adapter_rejects_self_target() -> None:
    candidate = _candidate(TICCSemanticModality.CORRECTION, "Correct the earlier rule.")
    assertion = _assertion("a", hour=8, source=candidate.source_ref)

    with pytest.raises(TICCRelationError, match="endpoints must be distinct"):
        _request(
            AssertionRelationType.CORRECTS,
            candidate,
            assertion,
            assertion,
        )


def test_relation_adapter_rejects_modality_relation_mismatch() -> None:
    candidate = _candidate(TICCSemanticModality.RETRACTION, "Retract the earlier rule.")
    old = _assertion("a", hour=8, source="source:a")
    source = _assertion("b", hour=9, source=candidate.source_ref)

    with pytest.raises(TICCRelationError, match="modality does not match"):
        _request(AssertionRelationType.CORRECTS, candidate, source, old)


def test_relation_adapter_rejects_unbound_evidence_reference() -> None:
    candidate = _candidate(TICCSemanticModality.CORRECTION, "Correct the earlier rule.")
    old = _assertion("a", hour=8, source="source:a")
    source = _assertion("b", hour=9, source=candidate.source_ref)

    with pytest.raises(TICCRelationError, match="must include source candidate"):
        _request(
            AssertionRelationType.CORRECTS,
            candidate,
            source,
            old,
            evidence_refs=("source:unrelated",),
        )


def test_relation_adapter_rejects_actor_origin_mismatch() -> None:
    candidate = _candidate(TICCSemanticModality.CORRECTION, "Correct the earlier rule.")
    old = _assertion("a", hour=8, source="source:a")
    source = _assertion(
        "b",
        hour=9,
        source=candidate.source_ref,
        actor=OPERATOR,
    )

    with pytest.raises(TICCRelationError, match="actor does not match"):
        _request(AssertionRelationType.CORRECTS, candidate, source, old)


def test_relation_adapter_rejects_unrelated_source_assertion() -> None:
    candidate = _candidate(TICCSemanticModality.CORRECTION, "Correct the earlier rule.")
    old = _assertion("a", hour=8, source="source:a")
    source = _assertion("b", hour=9, source="source:not-the-candidate")

    with pytest.raises(TICCRelationError, match="not bound to source candidate"):
        _request(AssertionRelationType.CORRECTS, candidate, source, old)


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
