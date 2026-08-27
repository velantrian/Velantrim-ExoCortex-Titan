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


NOW = datetime(2026, 8, 27, 16, 0, tzinfo=UTC)
USER = ActorRef("user:test", ActorKind.HUMAN)
MODEL = ActorRef("titan:test-model", ActorKind.TITAN_COMPONENT)
SYSTEM = ActorRef("system:test", ActorKind.SYSTEM)
PROJECT = SubjectRef("project:titan", SubjectKind.PROJECT)


def _turn(
    text: str,
    *,
    actor: ActorRef = USER,
    event_type: InteractionEventType = InteractionEventType.MESSAGE,
) -> ConversationSourceTurn:
    return ConversationSourceTurn(
        turn_ref="turn-1",
        session_ref="session-1",
        sequence=1,
        event_type=event_type,
        actor_ref=actor,
        subject_refs=(PROJECT,),
        raw_text=text,
        occurred_at=NOW,
        recorded_at=NOW,
        raw_text_sha256=sha256(text.encode("utf-8")).hexdigest(),
    )


def _span(turn: ConversationSourceTurn, span_text: str | None = None) -> TICCSourceSpan:
    selected = turn.raw_text if span_text is None else span_text
    start = turn.raw_text.index(selected)
    end = start + len(selected)
    return TICCSourceSpan(
        source_turn_ref=turn.turn_ref,
        start_offset=start,
        end_offset=end,
        slice_sha256=sha256(selected.encode("utf-8")).hexdigest(),
    )


def test_ticc_is_disabled_by_default_and_emits_no_artifacts() -> None:
    turn = _turn("Keep original records.")
    result = capture_turn(
        turn=turn,
        annotation=TICCSemanticAnnotation(
            modality=TICCSemanticModality.DIRECTIVE,
            source_span=_span(turn),
            origin_type=OriginType.USER_STATED,
        ),
        config=TICCConfig(),
        created_at=NOW,
    )

    assert result.interaction_event is None
    assert result.candidates == ()
    assert result.assertions == ()
    assert TICCReasonCode.SHADOW_FEATURE_DISABLED in result.receipt.reason_codes
    assert result.receipt.shadow_only is True
    assert result.receipt.no_runtime_authority is True


def test_exact_source_binding_and_assertion_reuse_existing_contract() -> None:
    turn = _turn("Deployment window is Friday.")
    annotation = TICCSemanticAnnotation(
        modality=TICCSemanticModality.ASSERTION,
        source_span=_span(turn, "Deployment window is Friday"),
        origin_type=OriginType.USER_STATED,
        assertion_spec=TICCAssertionSpec(
            subject_ref=PROJECT,
            predicate="deployment_window",
            value="Friday",
            origin_type=OriginType.USER_STATED,
            valid_from=NOW,
        ),
    )
    result = capture_turn(
        turn=turn,
        annotation=annotation,
        config=TICCConfig(enabled=True),
        created_at=NOW,
    )

    assert result.interaction_event is not None
    assert len(result.candidates) == 1
    assert len(result.assertions) == 1
    candidate = result.candidates[0]
    assertion = result.assertions[0]
    assert candidate.disposition is TICCDisposition.CAPTURED
    assert candidate.semantic_modality is TICCSemanticModality.ASSERTION
    assert candidate.origin_type is OriginType.USER_STATED
    assert candidate.assertion_ref == assertion.assertion_id
    assert assertion.source_refs == (candidate.source_ref,)
    assert "#char=" in candidate.source_ref
    assert "sha256=" in candidate.source_ref


def test_example_simulation_and_pseudocode_do_not_emit_assertions() -> None:
    cases = (
        (USER, OriginType.USER_STATED, TICCSemanticModality.EXAMPLE, "For example, assume latency is 150 ms."),
        (MODEL, OriginType.MODEL_INFERRED, TICCSemanticModality.SIMULATION, "Imagine I researched this for two hours."),
        (MODEL, OriginType.MODEL_INFERRED, TICCSemanticModality.PSEUDOCODE, "Pseudocode: engine.start()."),
    )

    for actor, origin, modality, text in cases:
        turn = _turn(text, actor=actor)
        result = capture_turn(
            turn=turn,
            annotation=TICCSemanticAnnotation(
                modality=modality,
                source_span=_span(turn),
                origin_type=origin,
            ),
            config=TICCConfig(enabled=True),
            created_at=NOW,
        )
        assert result.interaction_event is not None
        assert len(result.candidates) == 1
        assert result.assertions == ()
        assert result.candidates[0].semantic_modality is modality


def test_assertion_is_rejected_for_non_assertive_modality() -> None:
    turn = _turn("For example, latency is 150 ms.")
    annotation = TICCSemanticAnnotation(
        modality=TICCSemanticModality.EXAMPLE,
        source_span=_span(turn),
        origin_type=OriginType.USER_STATED,
        assertion_spec=TICCAssertionSpec(
            subject_ref=PROJECT,
            predicate="latency_ms",
            value=150,
            origin_type=OriginType.USER_STATED,
            valid_from=NOW,
        ),
    )

    with pytest.raises(TICCError, match=TICCReasonCode.ASSERTION_NOT_PERMITTED_FOR_MODALITY.value):
        capture_turn(
            turn=turn,
            annotation=annotation,
            config=TICCConfig(enabled=True),
            created_at=NOW,
        )


def test_actor_origin_mismatch_fails_closed() -> None:
    turn = _turn("I measured latency at 150 ms.", actor=USER)
    annotation = TICCSemanticAnnotation(
        modality=TICCSemanticModality.ASSERTION,
        source_span=_span(turn),
        origin_type=OriginType.SYSTEM_MEASURED,
    )

    with pytest.raises(TICCError, match=TICCReasonCode.ACTOR_ORIGIN_MISMATCH.value):
        capture_turn(
            turn=turn,
            annotation=annotation,
            config=TICCConfig(enabled=True),
            created_at=NOW,
        )


def test_bad_source_span_digest_fails_closed() -> None:
    turn = _turn("Keep original records.")
    bad_span = TICCSourceSpan(
        source_turn_ref=turn.turn_ref,
        start_offset=0,
        end_offset=len(turn.raw_text),
        slice_sha256="0" * 64,
    )
    annotation = TICCSemanticAnnotation(
        modality=TICCSemanticModality.DIRECTIVE,
        source_span=bad_span,
        origin_type=OriginType.USER_STATED,
    )

    with pytest.raises(TICCError, match=TICCReasonCode.SOURCE_SPAN_INVALID.value):
        capture_turn(
            turn=turn,
            annotation=annotation,
            config=TICCConfig(enabled=True),
            created_at=NOW,
        )


def test_declared_loss_is_visible_without_authority_upgrade() -> None:
    turn = _turn("That earlier rule is wrong.")
    result = capture_turn(
        turn=turn,
        annotation=TICCSemanticAnnotation(
            modality=TICCSemanticModality.UNRESOLVED,
            source_span=_span(turn),
            origin_type=OriginType.USER_STATED,
            declared_loss_codes=("correction_target_unresolved",),
        ),
        config=TICCConfig(enabled=True),
        created_at=NOW,
    )

    assert result.assertions == ()
    assert result.candidates[0].disposition is TICCDisposition.CAPTURED_WITH_DECLARED_LOSS
    assert result.candidates[0].declared_loss_codes == ("correction_target_unresolved",)
    assert TICCReasonCode.CAPTURE_LOSS_DECLARED in result.receipt.reason_codes
