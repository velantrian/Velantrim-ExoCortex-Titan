"""Adversarial tests for the explicit unwired State Draft adapter."""
from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from hashlib import sha256

import pytest

from core.continuity.contracts import SubjectKind, SubjectRef
from core.continuity.observations import ContinuitySignalType
from core.continuity.source_admission import (
    ContinuityAuthorizationContext,
    ContinuityPrincipalContext,
    ContinuitySourceAdmissionError,
    ContinuitySourceBindingReceipt,
)
from core.continuity.state_reconciler import (
    CurrentStateProjection,
    ProjectionStatus,
    StateReason,
    StateReconciliationResult,
)
from core.continuity.state_source_adapter import (
    STATE_SOURCE_COMPONENT_VERSION,
    STATE_SOURCE_OWNER,
    STATE_SOURCE_TYPE,
    StateDraftAdapterOutput,
    adapt_state_reconciliation_to_drafts,
)

_NOW = datetime(2026, 8, 6, 15, 0, tzinfo=UTC)
_SUBJECT_A = SubjectRef(subject_id="subject-a", kind=SubjectKind.PERSON)
_SUBJECT_B = SubjectRef(subject_id="subject-b", kind=SubjectKind.PROJECT)


def _projection(
    *,
    subject: SubjectRef = _SUBJECT_A,
    predicate: str = "profile.timezone",
    status: ProjectionStatus = ProjectionStatus.CONTESTED,
    selected: str | None = "assertion:a",
    candidates: tuple[str, ...] = ("assertion:a", "assertion:b"),
    contradictions: tuple[str, ...] = ("assertion:b",),
    expired: tuple[str, ...] = (),
    reasons: tuple[StateReason, ...] = (StateReason.ACTIVE_VALUE_CONFLICT,),
    review_required: bool = True,
    as_of: datetime = _NOW - timedelta(minutes=5),
) -> CurrentStateProjection:
    return CurrentStateProjection.create(
        subject_ref=subject,
        predicate=predicate,
        as_of=as_of,
        status=status,
        selected_assertion_ref=selected,
        candidate_assertion_refs=candidates,
        contradiction_assertion_refs=contradictions,
        expired_assertion_refs=expired,
        reason_codes=reasons,
        review_required=review_required,
    )


def _result(
    projections: tuple[CurrentStateProjection, ...] | None = None,
) -> StateReconciliationResult:
    values = projections or (_projection(),)
    assertion_refs = {
        ref
        for projection in values
        for ref in (
            *projection.candidate_assertion_refs,
            *projection.supporting_assertion_refs,
            *projection.contradiction_assertion_refs,
            *projection.superseded_assertion_refs,
            *projection.retracted_assertion_refs,
            *projection.expired_assertion_refs,
            *projection.future_assertion_refs,
        )
    }
    return StateReconciliationResult.create(
        as_of=_NOW - timedelta(minutes=5),
        assertion_refs=assertion_refs,
        relation_refs=("relation:a",),
        projections=values,
    )


def _principal() -> ContinuityPrincipalContext:
    return ContinuityPrincipalContext.create(
        principal_ref="principal:alice",
        principal_kind="human",
        authentication_method="oidc",
        authentication_strength="mfa",
        authenticated_at=_NOW - timedelta(minutes=20),
        issuer_ref="issuer:test",
        authentication_receipt_ref="auth-receipt:1",
    )


def _authorization(
    *,
    subjects: tuple[SubjectRef, ...] = (_SUBJECT_A, _SUBJECT_B),
) -> ContinuityAuthorizationContext:
    return ContinuityAuthorizationContext.create(
        tenant_ref="tenant:one",
        subject_refs=subjects,
        principal_context=_principal(),
        purpose_code="continuity_analysis",
        lawful_basis_or_consent_ref="consent:1",
        authorization_receipt_ref="authorization:1",
        policy_snapshot_id="policy:1",
        retention_class="ephemeral",
        erasure_domain_refs=("erasure:a",),
        valid_from=_NOW - timedelta(minutes=10),
        valid_until=_NOW + timedelta(hours=1),
        data_handling_mode="local_only",
    )


def _required_evidence(result: StateReconciliationResult) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                result.result_id,
                *(value.projection_id for value in result.projections),
                *result.assertion_refs,
                *result.relation_refs,
            }
        )
    )


def _binding(
    result: StateReconciliationResult,
    **overrides: object,
) -> ContinuitySourceBindingReceipt:
    subjects = tuple(
        {projection.subject_ref for projection in result.projections}
    )
    values: dict[str, object] = {
        "source_type": STATE_SOURCE_TYPE,
        "source_result_id": result.result_id,
        "source_digest": sha256(result.canonical_bytes()).hexdigest(),
        "source_owner": STATE_SOURCE_OWNER,
        "tenant_ref": "tenant:one",
        "subject_refs": subjects,
        "source_component_version": STATE_SOURCE_COMPONENT_VERSION,
        "source_policy_version": result.policy_version,
        "source_as_of": result.as_of,
        "evidence_refs": _required_evidence(result),
        "issued_at": _NOW - timedelta(minutes=1),
    }
    values.update(overrides)
    return ContinuitySourceBindingReceipt.create(**values)  # type: ignore[arg-type]


def _adapt(
    result: StateReconciliationResult,
    *,
    binding: ContinuitySourceBindingReceipt | None = None,
    authorization: ContinuityAuthorizationContext | None = None,
    created_at: datetime = _NOW,
) -> StateDraftAdapterOutput:
    return adapt_state_reconciliation_to_drafts(
        result=result,
        binding_receipt=binding or _binding(result),
        authorization_context=authorization or _authorization(),
        created_at=created_at,
    )


def test_contested_projection_derives_only_conservative_drafts() -> None:
    output = _adapt(_result())
    assert output.no_runtime_authority is True
    assert {value.signal_type for value in output.drafts} == {
        ContinuitySignalType.CONTEXT_DEGRADED,
        ContinuitySignalType.ACTIVE_CONTRADICTION,
    }
    assert all(value.value is True for value in output.drafts)
    assert all(value.proposed_confidence == 1.0 for value in output.drafts)
    assert all(
        value.signal_type
        not in {
            ContinuitySignalType.IMPORTANT_CLAIM,
            ContinuitySignalType.REQUIRES_CURRENT_STATE,
            ContinuitySignalType.CONTINUITY_AVAILABLE,
            ContinuitySignalType.SENSITIVITY,
        }
        for value in output.drafts
    )


def test_stale_and_expired_map_to_bounded_freshness_values() -> None:
    stale = _projection(
        predicate="profile.location",
        status=ProjectionStatus.STALE,
        contradictions=(),
        reasons=(),
        review_required=False,
    )
    expired = _projection(
        predicate="profile.employer",
        status=ProjectionStatus.EXPIRED,
        selected=None,
        candidates=("assertion:c",),
        contradictions=(),
        expired=("assertion:c",),
        reasons=(StateReason.ONLY_EXPIRED_ASSERTIONS,),
        review_required=False,
    )
    output = _adapt(_result((stale, expired)))
    freshness = {
        value.scope: value.value
        for value in output.drafts
        if value.signal_type is ContinuitySignalType.CONTEXT_FRESHNESS
    }
    assert freshness == {
        "person:subject-a:profile.employer": "critical_stale",
        "person:subject-a:profile.location": "stale",
    }


def test_current_projection_without_review_or_contradiction_emits_no_draft() -> None:
    current = _projection(
        status=ProjectionStatus.CURRENT,
        candidates=("assertion:a",),
        contradictions=(),
        reasons=(StateReason.ACTIVE_ASSERTION,),
        review_required=False,
    )
    assert _adapt(_result((current,))).drafts == ()


def test_multi_subject_result_requires_complete_exact_binding_scope() -> None:
    projections = (
        _projection(predicate="profile.timezone"),
        _projection(
            subject=_SUBJECT_B,
            predicate="project.status",
            contradictions=(),
            reasons=(),
            review_required=True,
        ),
    )
    result = _result(projections)
    incomplete = _binding(result, subject_refs=(_SUBJECT_A,))
    with pytest.raises(ContinuitySourceAdmissionError, match="exactly match"):
        _adapt(result, binding=incomplete)


def test_result_is_rejected_when_any_bound_subject_is_unauthorized() -> None:
    result = _result(
        (
            _projection(),
            _projection(
                subject=_SUBJECT_B,
                predicate="project.status",
                contradictions=(),
                reasons=(),
                review_required=True,
            ),
        )
    )
    with pytest.raises(ContinuitySourceAdmissionError, match="subset"):
        _adapt(result, authorization=_authorization(subjects=(_SUBJECT_A,)))


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"source_result_id": "wrong"}, "source_result_id"),
        ({"source_digest": "0" * 64}, "source_digest"),
        ({"source_policy_version": "wrong"}, "source_policy_version"),
        ({"source_as_of": _NOW - timedelta(minutes=6)}, "source_as_of"),
        ({"source_type": "wrong"}, "source_type"),
        ({"source_owner": "wrong"}, "source_owner"),
        ({"source_component_version": "wrong"}, "component_version"),
    ],
)
def test_binding_identity_must_match_actual_result(
    override: dict[str, object],
    message: str,
) -> None:
    result = _result()
    with pytest.raises(ContinuitySourceAdmissionError, match=message):
        _adapt(result, binding=_binding(result, **override))


def test_tampered_result_identity_is_rejected_before_receipt_trust() -> None:
    result = replace(_result(), result_id="0" * 64)
    with pytest.raises(ContinuitySourceAdmissionError, match="result_id"):
        _adapt(result, binding=_binding(result))


def test_tampered_projection_identity_is_rejected_before_derivation() -> None:
    projection = replace(_projection(), predicate="tampered.predicate")
    result = _result((projection,))
    with pytest.raises(ContinuitySourceAdmissionError, match="projection_id"):
        _adapt(result, binding=_binding(result))


def test_projection_time_and_assertion_set_must_match_result() -> None:
    wrong_time = _projection(as_of=_NOW - timedelta(minutes=6))
    result = _result((wrong_time,))
    with pytest.raises(ContinuitySourceAdmissionError, match="projection as_of"):
        _adapt(result, binding=_binding(result))

    projection = _projection()
    incomplete = StateReconciliationResult.create(
        as_of=projection.as_of,
        assertion_refs=("assertion:a",),
        relation_refs=("relation:a",),
        projections=(projection,),
    )
    with pytest.raises(ContinuitySourceAdmissionError, match="assertion refs"):
        _adapt(incomplete, binding=_binding(incomplete))


def test_binding_must_include_complete_source_evidence() -> None:
    result = _result()
    evidence = tuple(
        value
        for value in _required_evidence(result)
        if value != result.projections[0].projection_id
    )
    with pytest.raises(ContinuitySourceAdmissionError, match="evidence"):
        _adapt(result, binding=_binding(result, evidence_refs=evidence))


def test_draft_evidence_is_bound_to_envelope_evidence() -> None:
    result = _result()
    output = _adapt(result)
    envelope_refs = set(output.source_envelope.evidence_refs)
    assert output.drafts
    assert all(
        set(value.evidence_refs).issubset(envelope_refs)
        for value in output.drafts
    )


def test_contradiction_scopes_do_not_collapse_distinct_assertions() -> None:
    projection = _projection(
        candidates=("assertion:a", "assertion:b", "assertion:c"),
        contradictions=("assertion:b", "assertion:c"),
    )
    contradictions = [
        value
        for value in _adapt(_result((projection,))).drafts
        if value.signal_type is ContinuitySignalType.ACTIVE_CONTRADICTION
    ]
    assert len(contradictions) == 2
    assert len({value.draft_id for value in contradictions}) == 2
    assert len({value.scope for value in contradictions}) == 2


def test_adapter_is_deterministic_across_input_order_and_timezones() -> None:
    first = _projection(predicate="zeta", contradictions=())
    second = _projection(predicate="alpha", contradictions=())
    result_a = _result((first, second))
    result_b = _result((second, first))
    offset_now = _NOW.astimezone(timezone(timedelta(hours=2)))
    assert result_a == result_b
    assert _adapt(result_a).source_envelope.envelope_id == _adapt(
        result_b,
        created_at=offset_now,
    ).source_envelope.envelope_id
    assert _adapt(result_a).drafts == _adapt(
        result_b,
        created_at=offset_now,
    ).drafts


def test_output_rejects_runtime_authority_and_cross_envelope_drafts() -> None:
    output = _adapt(_result())
    with pytest.raises(ContinuitySourceAdmissionError, match="remain True"):
        replace(output, no_runtime_authority=False)

    other_result = _result((_projection(predicate="profile.location"),))
    other_draft = _adapt(other_result).drafts[0]
    with pytest.raises(
        ContinuitySourceAdmissionError,
        match="output source envelope",
    ):
        replace(output, drafts=(other_draft,))
