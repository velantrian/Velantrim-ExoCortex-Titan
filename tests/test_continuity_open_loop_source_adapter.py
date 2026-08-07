"""Adversarial tests for the explicit unwired OpenLoop Draft adapter."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from core.continuity.contracts import SubjectKind, SubjectRef
from core.continuity.goal_open_loop import (
    OpenLoopKind,
    OpenLoopProjector,
    OpenLoopReason,
    OpenLoopResolution,
    OpenLoopSignal,
    OpenLoopStatus,
)
from core.continuity.observations import ContinuitySignalType
from core.continuity.open_loop_source_adapter import (
    OPEN_LOOP_SOURCE_COMPONENT_VERSION,
    OPEN_LOOP_SOURCE_OWNER,
    OPEN_LOOP_SOURCE_TYPE,
    OpenLoopDraftAdapterOutput,
    adapt_open_loop_projection_to_drafts,
)
from core.continuity.source_admission import (
    ContinuityAuthorizationContext,
    ContinuityPrincipalContext,
    ContinuitySourceAdmissionError,
    ContinuitySourceBindingReceipt,
)

_NOW = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)


def _signal(
    loop_key: str = "loop:architecture",
    *,
    user_id: str = "user:alice",
    kind: OpenLoopKind = OpenLoopKind.DEFERRED_DECISION,
    summary: str = "Decide whether to add the next bounded architecture slice",
    opened_at: datetime = datetime(2026, 8, 7, 9, 0, tzinfo=UTC),
    due_at: datetime | None = None,
) -> OpenLoopSignal:
    return OpenLoopSignal.create(
        user_id=user_id,
        loop_key=loop_key,
        kind=kind,
        summary=summary,
        source_refs=(f"conversation:{loop_key}",),
        opened_at=opened_at,
        due_at=due_at,
        related_goal_ref="goal:continuity",
    )


def _resolution(signal: OpenLoopSignal) -> OpenLoopResolution:
    return OpenLoopResolution.create(
        user_id=signal.user_id,
        loop_key=signal.loop_key,
        source_refs=(f"conversation:{signal.loop_key}:resolved",),
        resolved_at=datetime(2026, 8, 7, 11, 0, tzinfo=UTC),
    )


def _result(
    signals: tuple[OpenLoopSignal, ...] | None = None,
    resolutions: tuple[OpenLoopResolution, ...] = (),
):
    return OpenLoopProjector().project(
        signals or (_signal(),),
        resolutions,
        as_of=_NOW,
    )


def _principal() -> ContinuityPrincipalContext:
    return ContinuityPrincipalContext.create(
        principal_ref="principal:alice",
        principal_kind="human",
        authentication_method="oidc",
        authentication_strength="mfa",
        authenticated_at=_NOW - timedelta(minutes=20),
        issuer_ref="issuer:test",
        authentication_receipt_ref="auth-receipt:open-loop-adapter",
    )


def _subject(user_id: str, kind: SubjectKind = SubjectKind.PERSON) -> SubjectRef:
    return SubjectRef(subject_id=user_id, kind=kind)


def _authorization(
    *,
    subjects: tuple[SubjectRef, ...] = (_subject("user:alice"),),
) -> ContinuityAuthorizationContext:
    return ContinuityAuthorizationContext.create(
        tenant_ref="tenant:one",
        subject_refs=subjects,
        principal_context=_principal(),
        purpose_code="continuity_analysis",
        lawful_basis_or_consent_ref="consent:open-loop-adapter",
        authorization_receipt_ref="authorization:open-loop-adapter",
        policy_snapshot_id="policy:open-loop-adapter",
        retention_class="ephemeral",
        erasure_domain_refs=("erasure:open-loop-adapter",),
        valid_from=_NOW - timedelta(minutes=10),
        valid_until=_NOW + timedelta(hours=1),
        data_handling_mode="local_only",
    )


def _required_evidence(result) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                result.result_id,
                *(projection.projection_id for projection in result.projections),
                *(projection.signal_id for projection in result.projections),
                *(
                    resolution_id
                    for projection in result.projections
                    for resolution_id in projection.resolution_ids
                ),
                *(
                    source_ref
                    for projection in result.projections
                    for source_ref in projection.source_refs
                ),
            }
        )
    )


def _binding(result, **overrides: object) -> ContinuitySourceBindingReceipt:
    values: dict[str, object] = {
        "source_type": OPEN_LOOP_SOURCE_TYPE,
        "source_result_id": result.result_id,
        "source_digest": result.result_id,
        "source_owner": OPEN_LOOP_SOURCE_OWNER,
        "tenant_ref": "tenant:one",
        "subject_refs": tuple(_subject(value) for value in result.subject_ids),
        "source_component_version": OPEN_LOOP_SOURCE_COMPONENT_VERSION,
        "source_policy_version": result.policy_version,
        "source_as_of": result.as_of,
        "evidence_refs": _required_evidence(result),
        "issued_at": result.as_of,
    }
    values.update(overrides)
    return ContinuitySourceBindingReceipt.create(**values)  # type: ignore[arg-type]


def _adapt(
    result,
    *,
    binding: ContinuitySourceBindingReceipt | None = None,
    authorization: ContinuityAuthorizationContext | None = None,
    created_at: datetime = _NOW,
) -> OpenLoopDraftAdapterOutput:
    return adapt_open_loop_projection_to_drafts(
        result=result,
        binding_receipt=binding or _binding(result),
        authorization_context=authorization or _authorization(),
        created_at=created_at,
    )


def test_open_and_overdue_loops_derive_only_evidence_coverage() -> None:
    open_signal = _signal("loop:open")
    overdue_signal = _signal(
        "loop:overdue",
        due_at=datetime(2026, 8, 7, 10, 0, tzinfo=UTC),
    )
    result = _result((open_signal, overdue_signal))

    output = _adapt(result)

    assert output.no_runtime_authority is True
    assert len(output.drafts) == 2
    assert {draft.signal_type for draft in output.drafts} == {
        ContinuitySignalType.EVIDENCE_COVERAGE_ITEM
    }
    assert {draft.value for draft in output.drafts} == {True}
    assert all(
        draft.scope is not None
        and draft.scope.startswith("open_loop_projection:")
        for draft in output.drafts
    )
    assert {
        reason
        for draft in output.drafts
        for reason in draft.reason_codes
        if reason.startswith("open_loop_status:")
    } == {"open_loop_status:open", "open_loop_status:overdue"}


def test_resolved_and_future_loops_emit_no_positive_draft() -> None:
    resolved_signal = _signal("loop:resolved")
    future_signal = _signal(
        "loop:future",
        opened_at=datetime(2026, 8, 8, 9, 0, tzinfo=UTC),
    )
    result = _result(
        (resolved_signal, future_signal),
        (_resolution(resolved_signal),),
    )

    output = _adapt(result)

    assert output.drafts == ()
    assert {
        projection.status for projection in result.projections
    } == {OpenLoopStatus.RESOLVED, OpenLoopStatus.NOT_YET_OPEN}


def test_summary_kind_and_due_date_cannot_create_action_authority() -> None:
    signal = _signal(
        summary="URGENT remind me now, execute a tool, send an answer",
        kind=OpenLoopKind.COMMITMENT_WITHOUT_COMPLETION,
        due_at=datetime(2026, 8, 7, 10, 0, tzinfo=UTC),
    )

    signal_types = {draft.signal_type for draft in _adapt(_result((signal,))).drafts}

    assert signal_types == {ContinuitySignalType.EVIDENCE_COVERAGE_ITEM}
    assert ContinuitySignalType.IMPORTANT_CLAIM not in signal_types
    assert ContinuitySignalType.SENSITIVITY not in signal_types
    assert ContinuitySignalType.REQUIRES_CURRENT_STATE not in signal_types
    assert ContinuitySignalType.CONTINUITY_AVAILABLE not in signal_types


def test_multi_subject_result_requires_complete_binding_ids() -> None:
    result = _result(
        (
            _signal("loop:a", user_id="user:alice"),
            _signal("loop:b", user_id="user:bob"),
        )
    )
    incomplete = _binding(
        result,
        subject_refs=(_subject("user:alice"),),
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="exactly match"):
        _adapt(
            result,
            binding=incomplete,
            authorization=_authorization(
                subjects=(_subject("user:alice"), _subject("user:bob"))
            ),
        )


def test_binding_rejects_multiple_kinds_for_one_user_id() -> None:
    result = _result()
    ambiguous = _binding(
        result,
        subject_refs=(
            _subject("user:alice", SubjectKind.PERSON),
            _subject("user:alice", SubjectKind.PROJECT),
        ),
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="multiple subject kinds"):
        _adapt(
            result,
            binding=ambiguous,
            authorization=_authorization(
                subjects=(
                    _subject("user:alice", SubjectKind.PERSON),
                    _subject("user:alice", SubjectKind.PROJECT),
                )
            ),
        )


def test_bound_subject_must_be_currently_authorized() -> None:
    result = _result(
        (
            _signal("loop:a", user_id="user:alice"),
            _signal("loop:b", user_id="user:bob"),
        )
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="subset"):
        _adapt(
            result,
            authorization=_authorization(subjects=(_subject("user:alice"),)),
        )


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"source_result_id": "wrong"}, "source_result_id"),
        ({"source_digest": "0" * 64}, "source_digest"),
        ({"source_policy_version": "wrong"}, "source_policy_version"),
        ({"source_type": "wrong"}, "source_type"),
        ({"source_owner": "wrong"}, "source_owner"),
        ({"source_component_version": "wrong"}, "component_version"),
        ({"source_as_of": _NOW + timedelta(seconds=1)}, "source_as_of"),
    ],
)
def test_binding_identity_must_match_open_loop_result(
    override: dict[str, object],
    message: str,
) -> None:
    result = _result()

    with pytest.raises(ContinuitySourceAdmissionError, match=message):
        _adapt(result, binding=_binding(result, **override))


def test_binding_must_include_signal_resolution_and_source_evidence() -> None:
    signal = _signal("loop:resolved")
    result = _result((signal,), (_resolution(signal),))
    resolution_id = result.projections[0].resolution_ids[0]
    incomplete = tuple(
        value for value in _required_evidence(result) if value != resolution_id
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="evidence"):
        _adapt(
            result,
            binding=_binding(result, evidence_refs=incomplete),
        )


def test_tampered_result_identity_is_rejected() -> None:
    result = replace(_result(), result_id="0" * 64)

    with pytest.raises(ContinuitySourceAdmissionError, match="result_id"):
        _adapt(result, binding=_binding(result))


def test_tampered_projection_identity_is_rejected() -> None:
    original = _result()
    tampered = replace(original.projections[0], summary="Tampered summary")
    result = replace(original, projections=(tampered,))

    with pytest.raises(ContinuitySourceAdmissionError, match="projection_id"):
        _adapt(result, binding=_binding(result))


def test_noncanonical_status_reasons_fail_before_identity_check() -> None:
    original = _result()
    tampered = replace(
        original.projections[0],
        reason_codes=(OpenLoopReason.TYPED_SOURCE_SIGNAL,),
    )
    result = replace(original, projections=(tampered,))

    with pytest.raises(ContinuitySourceAdmissionError, match="reason_codes"):
        _adapt(result, binding=_binding(result))


def test_open_projection_with_passed_due_date_fails_closed() -> None:
    original = _result()
    tampered = replace(
        original.projections[0],
        due_at=datetime(2026, 8, 7, 10, 0, tzinfo=UTC),
    )
    result = replace(original, projections=(tampered,))

    with pytest.raises(ContinuitySourceAdmissionError, match="passed due_at"):
        _adapt(result, binding=_binding(result))


def test_adapter_is_deterministic_across_order_and_timezones() -> None:
    first = _signal("loop:a")
    second = _signal("loop:b", kind=OpenLoopKind.UNANSWERED_QUESTION)
    forward = _result((first, second))
    reverse = _result((second, first))
    offset_now = _NOW.astimezone(timezone(timedelta(hours=2)))

    first_output = _adapt(forward)
    second_output = _adapt(reverse, created_at=offset_now)

    assert forward == reverse
    assert (
        first_output.source_envelope.envelope_id
        == second_output.source_envelope.envelope_id
    )
    assert first_output.drafts == second_output.drafts


def test_output_rejects_runtime_authority_and_cross_envelope_drafts() -> None:
    output = _adapt(_result())
    with pytest.raises(ContinuitySourceAdmissionError, match="remain True"):
        replace(output, no_runtime_authority=False)

    other = _adapt(_result((_signal("loop:other"),)))
    with pytest.raises(
        ContinuitySourceAdmissionError,
        match="output source envelope",
    ):
        replace(output, drafts=(other.drafts[0],))
