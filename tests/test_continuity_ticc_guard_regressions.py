from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256

import pytest

from core.continuity.contracts import (
    ActorKind,
    ActorRef,
    InteractionEventType,
    OriginType,
    SubjectKind,
    SubjectRef,
)
from core.continuity.ticc import (
    ConversationSourceTurn,
    TICCAssertionSpec,
    TICCConfig,
    TICCDisposition,
    TICCError,
    TICCReasonCode,
    TICCSemanticAnnotation,
    TICCSemanticModality,
    TICCSourceSpan,
    capture_turn,
)

NOW = datetime(2026, 8, 27, 20, 0, tzinfo=UTC)
USER = ActorRef("user:test", ActorKind.HUMAN)
PROJECT = SubjectRef("project:titan", SubjectKind.PROJECT)


def _turn(text: str) -> ConversationSourceTurn:
    return ConversationSourceTurn(
        turn_ref="turn-guard",
        session_ref="session-guard",
        sequence=1,
        event_type=InteractionEventType.MESSAGE,
        actor_ref=USER,
        subject_refs=(PROJECT,),
        raw_text=text,
        occurred_at=NOW,
        recorded_at=NOW,
        raw_text_sha256=sha256(text.encode("utf-8")).hexdigest(),
    )


def _span(turn: ConversationSourceTurn) -> TICCSourceSpan:
    return TICCSourceSpan(
        source_turn_ref=turn.turn_ref,
        start_offset=0,
        end_offset=len(turn.raw_text),
        slice_sha256=sha256(turn.raw_text.encode("utf-8")).hexdigest(),
    )


def test_correction_without_relation_target_is_deferred_and_never_emits_standalone_assertion() -> None:
    turn = _turn("Replace the earlier rule with original records only.")
    result = capture_turn(
        turn=turn,
        annotation=TICCSemanticAnnotation(
            modality=TICCSemanticModality.CORRECTION,
            source_span=_span(turn),
            origin_type=OriginType.USER_STATED,
            assertion_spec=TICCAssertionSpec(
                subject_ref=PROJECT,
                predicate="storage_policy",
                value="original_records_only",
                origin_type=OriginType.USER_STATED,
                valid_from=NOW,
            ),
        ),
        config=TICCConfig(enabled=True),
        created_at=NOW,
    )

    assert result.assertions == ()
    candidate = result.candidates[0]
    assert candidate.disposition is TICCDisposition.DEFERRED
    assert candidate.assertion_ref is None
    assert TICCReasonCode.RELATION_NOT_IMPLEMENTED in candidate.reason_codes
    assert TICCReasonCode.RELATION_NOT_IMPLEMENTED in result.receipt.reason_codes


def test_retraction_without_relation_target_is_deferred_not_deleted() -> None:
    turn = _turn("I retract the earlier storage rule.")
    result = capture_turn(
        turn=turn,
        annotation=TICCSemanticAnnotation(
            modality=TICCSemanticModality.RETRACTION,
            source_span=_span(turn),
            origin_type=OriginType.USER_STATED,
        ),
        config=TICCConfig(enabled=True),
        created_at=NOW,
    )

    assert result.assertions == ()
    assert result.candidates[0].disposition is TICCDisposition.DEFERRED
    assert TICCReasonCode.RELATION_NOT_IMPLEMENTED in result.candidates[0].reason_codes


def test_conditional_qualifier_must_be_literal_substring_of_exact_source_span() -> None:
    turn = _turn("Do not publish until I explicitly approve it.")
    annotation = TICCSemanticAnnotation(
        modality=TICCSemanticModality.DIRECTIVE,
        source_span=_span(turn),
        origin_type=OriginType.USER_STATED,
        qualifier_text="until legal review completes",
    )

    with pytest.raises(TICCError, match=TICCReasonCode.QUALIFIER_NOT_SOURCE_BOUND.value):
        capture_turn(
            turn=turn,
            annotation=annotation,
            config=TICCConfig(enabled=True),
            created_at=NOW,
        )


def test_source_bound_qualifier_is_preserved_as_candidate_metadata() -> None:
    turn = _turn("Do not publish until I explicitly approve it.")
    qualifier = "until I explicitly approve it"
    result = capture_turn(
        turn=turn,
        annotation=TICCSemanticAnnotation(
            modality=TICCSemanticModality.DIRECTIVE,
            source_span=_span(turn),
            origin_type=OriginType.USER_STATED,
            qualifier_text=qualifier,
        ),
        config=TICCConfig(enabled=True),
        created_at=NOW,
    )

    assert result.candidates[0].qualifier_text == qualifier
    assert qualifier in turn.raw_text
