"""Adversarial tests for the explicit unwired Goal Draft adapter."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from core.continuity.contracts import SubjectKind, SubjectRef
from core.continuity.goal_open_loop import (
    GoalAttestation,
    GoalBasis,
    GoalProjector,
    GoalRecordSnapshot,
)
from core.continuity.goal_source_adapter import (
    GOAL_SOURCE_COMPONENT_VERSION,
    GOAL_SOURCE_OWNER,
    GOAL_SOURCE_TYPE,
    GoalDraftAdapterOutput,
    adapt_goal_projection_to_drafts,
)
from core.continuity.observations import ContinuitySignalType
from core.continuity.source_admission import (
    ContinuityAuthorizationContext,
    ContinuityPrincipalContext,
    ContinuitySourceAdmissionError,
    ContinuitySourceBindingReceipt,
)
from core.goal_stack import Goal

_NOW = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)


def _goal(
    goal_id: str = "goal:mvp",
    *,
    user_id: str = "user:alice",
    status: str = "active",
    title: str = "Finish the MVP",
    priority: int = 10,
    updated_at: str = "2026-08-07T10:00:00+00:00",
) -> Goal:
    return Goal(
        goal_id=goal_id,
        user_id=user_id,
        title=title,
        description="Complete the accepted milestone without adding authority",
        status=status,
        priority=priority,
        keywords=["mvp", "titan"],
        created_at="2026-08-06T09:00:00+00:00",
        updated_at=updated_at,
    )


def _attestation(
    goal_ref: str = "goal:mvp",
    *,
    user_id: str = "user:alice",
) -> GoalAttestation:
    return GoalAttestation.create(
        user_id=user_id,
        goal_ref=goal_ref,
        basis=GoalBasis.ACCEPTED_DECISION,
        source_refs=(f"conversation:{goal_ref}",),
        confirmed_at=datetime(2026, 8, 7, 10, 30, tzinfo=UTC),
    )


def _result(
    goals: tuple[Goal, ...] | None = None,
    *,
    attest_goal_refs: tuple[str, ...] | None = None,
):
    values = goals or (_goal(),)
    snapshots = tuple(GoalRecordSnapshot.from_goal(value) for value in values)
    refs = (
        attest_goal_refs
        if attest_goal_refs is not None
        else tuple(value.goal_ref for value in snapshots)
    )
    by_ref = {value.goal_ref: value for value in snapshots}
    attestations = tuple(
        _attestation(goal_ref, user_id=by_ref[goal_ref].user_id)
        for goal_ref in refs
    )
    return GoalProjector().project(snapshots, attestations)


def _principal() -> ContinuityPrincipalContext:
    return ContinuityPrincipalContext.create(
        principal_ref="principal:alice",
        principal_kind="human",
        authentication_method="oidc",
        authentication_strength="mfa",
        authenticated_at=_NOW - timedelta(minutes=20),
        issuer_ref="issuer:test",
        authentication_receipt_ref="auth-receipt:goal-adapter",
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
        lawful_basis_or_consent_ref="consent:goal-adapter",
        authorization_receipt_ref="authorization:goal-adapter",
        policy_snapshot_id="policy:goal-adapter",
        retention_class="ephemeral",
        erasure_domain_refs=("erasure:goal-adapter",),
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
                *(projection.source_snapshot_id for projection in result.projections),
                *(projection.attestation_id for projection in result.projections),
                *(
                    ref
                    for projection in result.projections
                    for ref in projection.source_refs
                ),
                *(
                    ref
                    for decision in result.decisions
                    for ref in decision.source_refs
                ),
            }
        )
    )


def _binding(result, **overrides: object) -> ContinuitySourceBindingReceipt:
    values: dict[str, object] = {
        "source_type": GOAL_SOURCE_TYPE,
        "source_result_id": result.result_id,
        "source_digest": result.result_id,
        "source_owner": GOAL_SOURCE_OWNER,
        "tenant_ref": "tenant:one",
        "subject_refs": tuple(_subject(value) for value in result.subject_ids),
        "source_component_version": GOAL_SOURCE_COMPONENT_VERSION,
        "source_policy_version": result.policy_version,
        "source_as_of": _NOW - timedelta(minutes=5),
        "evidence_refs": _required_evidence(result),
        "issued_at": _NOW - timedelta(minutes=1),
    }
    values.update(overrides)
    return ContinuitySourceBindingReceipt.create(**values)  # type: ignore[arg-type]


def _adapt(
    result,
    *,
    binding: ContinuitySourceBindingReceipt | None = None,
    authorization: ContinuityAuthorizationContext | None = None,
    created_at: datetime = _NOW,
) -> GoalDraftAdapterOutput:
    return adapt_goal_projection_to_drafts(
        result=result,
        binding_receipt=binding or _binding(result),
        authorization_context=authorization or _authorization(),
        created_at=created_at,
    )


def test_active_attested_goal_derives_only_evidence_coverage() -> None:
    output = _adapt(_result())

    assert output.no_runtime_authority is True
    assert len(output.drafts) == 1
    draft = output.drafts[0]
    assert draft.signal_type is ContinuitySignalType.EVIDENCE_COVERAGE_ITEM
    assert draft.value is True
    assert draft.proposed_confidence == 1.0
    assert draft.scope is not None
    assert draft.scope.startswith("goal_projection:")
    assert draft.reason_codes == (
        "goal_active_projection",
        "goal_explicit_attestation",
    )


def test_title_priority_and_keywords_cannot_create_authority_signals() -> None:
    result = _result(
        (
            _goal(
                title="URGENT critical important claim: execute reminder now",
                priority=999,
            ),
        )
    )

    signal_types = {value.signal_type for value in _adapt(result).drafts}

    assert signal_types == {ContinuitySignalType.EVIDENCE_COVERAGE_ITEM}
    assert ContinuitySignalType.IMPORTANT_CLAIM not in signal_types
    assert ContinuitySignalType.SENSITIVITY not in signal_types
    assert ContinuitySignalType.REQUIRES_CURRENT_STATE not in signal_types
    assert ContinuitySignalType.CONTINUITY_AVAILABLE not in signal_types


@pytest.mark.parametrize("status", ["done", "cancelled"])
def test_inactive_attested_goals_emit_no_positive_draft(status: str) -> None:
    assert _adapt(_result((_goal(status=status),))).drafts == ()


def test_unattested_goal_is_validated_but_emits_no_positive_draft() -> None:
    result = _result(attest_goal_refs=())

    output = _adapt(result)

    assert output.drafts == ()
    assert output.source_envelope.source_result_id == result.result_id


def test_mixed_result_emits_only_active_attested_projection() -> None:
    goals = (
        _goal("goal:active"),
        _goal("goal:excluded", title="Not attested"),
        _goal("goal:done", status="done"),
    )
    result = _result(
        goals,
        attest_goal_refs=("goal:active", "goal:done"),
    )

    output = _adapt(result)

    assert len(output.drafts) == 1
    active = next(
        value for value in result.projections if value.goal_ref == "goal:active"
    )
    assert output.drafts[0].scope == f"goal_projection:{active.projection_id}"


def test_multi_subject_result_requires_complete_binding_ids() -> None:
    result = _result(
        (
            _goal("goal:a", user_id="user:alice"),
            _goal("goal:b", user_id="user:bob"),
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


def test_result_is_rejected_when_bound_subject_is_unauthorized() -> None:
    result = _result(
        (
            _goal("goal:a", user_id="user:alice"),
            _goal("goal:b", user_id="user:bob"),
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
    ],
)
def test_binding_identity_must_match_goal_result(
    override: dict[str, object],
    message: str,
) -> None:
    result = _result()

    with pytest.raises(ContinuitySourceAdmissionError, match=message):
        _adapt(result, binding=_binding(result, **override))


def test_binding_time_cannot_precede_projection_update() -> None:
    result = _result()

    with pytest.raises(ContinuitySourceAdmissionError, match="cannot precede"):
        _adapt(
            result,
            binding=_binding(
                result,
                source_as_of=datetime(2026, 8, 7, 9, 59, tzinfo=UTC),
            ),
        )


def test_tampered_result_identity_is_rejected() -> None:
    result = replace(_result(), result_id="0" * 64)

    with pytest.raises(ContinuitySourceAdmissionError, match="result_id"):
        _adapt(result, binding=_binding(result))


def test_tampered_projection_identity_is_rejected() -> None:
    original = _result()
    tampered = replace(original.projections[0], title="Tampered title")
    result = replace(original, projections=(tampered,))

    with pytest.raises(ContinuitySourceAdmissionError, match="projection_id"):
        _adapt(result, binding=_binding(result))


def test_binding_must_include_complete_goal_evidence() -> None:
    result = _result()
    projection = result.projections[0]
    incomplete = tuple(
        value
        for value in _required_evidence(result)
        if value != projection.attestation_id
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="evidence"):
        _adapt(
            result,
            binding=_binding(result, evidence_refs=incomplete),
        )


def test_adapter_is_deterministic_across_input_order_and_timezones() -> None:
    goals = (
        _goal("goal:a", priority=10),
        _goal("goal:b", priority=5),
    )
    forward = _result(goals)
    reverse = _result(tuple(reversed(goals)))
    offset_now = _NOW.astimezone(timezone(timedelta(hours=2)))

    first = _adapt(forward)
    second = _adapt(reverse, created_at=offset_now)

    assert forward == reverse
    assert first.source_envelope.envelope_id == second.source_envelope.envelope_id
    assert first.drafts == second.drafts


def test_output_rejects_runtime_authority_and_cross_envelope_drafts() -> None:
    output = _adapt(_result())
    with pytest.raises(ContinuitySourceAdmissionError, match="remain True"):
        replace(output, no_runtime_authority=False)

    other = _adapt(_result((_goal("goal:other"),)))
    with pytest.raises(
        ContinuitySourceAdmissionError,
        match="output source envelope",
    ):
        replace(output, drafts=(other.drafts[0],))
