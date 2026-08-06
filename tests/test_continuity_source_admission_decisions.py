"""Adversarial tests for admission receipts and authorized batches."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
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
from core.continuity.source_admission_decisions import (
    SOURCE_ADMISSION_DECISION_SCHEMA_VERSION,
    AuthorizedContinuityObservationBatch,
    ContinuityAdmissionDisposition,
    ContinuityDraftObservationLink,
    ContinuityDraftRejection,
    ContinuityObservationAdmissionReceipt,
)
from core.continuity.source_admission_payloads import (
    ContinuityObservationDraft,
    ContinuitySourceEnvelope,
)

_NOW = datetime(2026, 8, 6, 16, 0, tzinfo=UTC)
_SUBJECT_A = SubjectRef(subject_id="subject-a", kind=SubjectKind.PERSON)
_SUBJECT_B = SubjectRef(subject_id="subject-b", kind=SubjectKind.PROJECT)


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


def _authorization(**overrides: object) -> ContinuityAuthorizationContext:
    values: dict[str, object] = {
        "tenant_ref": "tenant:one",
        "subject_refs": (_SUBJECT_A, _SUBJECT_B),
        "principal_context": _principal(),
        "purpose_code": "continuity_analysis",
        "lawful_basis_or_consent_ref": "consent:1",
        "authorization_receipt_ref": "authorization:1",
        "policy_snapshot_id": "policy:1",
        "retention_class": "ephemeral",
        "erasure_domain_refs": ("erasure:a", "erasure:b"),
        "valid_from": _NOW - timedelta(minutes=10),
        "valid_until": _NOW + timedelta(hours=2),
        "data_handling_mode": "local_only",
    }
    values.update(overrides)
    return ContinuityAuthorizationContext.create(**values)  # type: ignore[arg-type]


def _binding(
    *,
    suffix: str = "a",
    subject: SubjectRef = _SUBJECT_A,
    **overrides: object,
) -> ContinuitySourceBindingReceipt:
    values: dict[str, object] = {
        "source_type": "state_reconciliation_result",
        "source_result_id": f"state-result:{suffix}",
        "source_digest": sha256(f"state-result:{suffix}".encode()).hexdigest(),
        "source_owner": "continuity.state_reconciler",
        "tenant_ref": "tenant:one",
        "subject_refs": (subject,),
        "source_component_version": "1",
        "source_policy_version": "1",
        "source_as_of": _NOW - timedelta(minutes=4),
        "evidence_refs": (f"event:{suffix}",),
        "issued_at": _NOW - timedelta(minutes=3),
    }
    values.update(overrides)
    return ContinuitySourceBindingReceipt.create(**values)  # type: ignore[arg-type]


def _envelope(
    *,
    binding: ContinuitySourceBindingReceipt | None = None,
    authorization: ContinuityAuthorizationContext | None = None,
    adapter_id: str = "continuity.state_to_signal_draft",
    **overrides: object,
) -> ContinuitySourceEnvelope:
    binding_value = binding or _binding()
    authorization_value = authorization or _authorization()
    values: dict[str, object] = {
        "binding_receipt": binding_value,
        "authorization_context": authorization_value,
        "source_schema_version": "state-reconciliation.v1",
        "producer_adapter_id": adapter_id,
        "producer_adapter_version": "1",
        "created_at": _NOW - timedelta(minutes=2),
    }
    values.update(overrides)
    return ContinuitySourceEnvelope.create(**values)  # type: ignore[arg-type]


def _draft(
    *,
    envelope: ContinuitySourceEnvelope | None = None,
    signal_type: ContinuitySignalType = ContinuitySignalType.CONTEXT_DEGRADED,
    value: object = True,
    tag: str = "a",
    derivation_rule_id: str | None = None,
    **overrides: object,
) -> ContinuityObservationDraft:
    envelope_value = envelope or _envelope()
    values: dict[str, object] = {
        "source_envelope": envelope_value,
        "signal_type": signal_type,
        "value": value,
        "proposed_confidence": 0.9,
        "evidence_refs": envelope_value.evidence_refs,
        "reason_codes": (f"reason:{tag}",),
        "derivation_rule_id": derivation_rule_id or f"rule:{tag}",
        "created_at": _NOW - timedelta(minutes=1),
        "scope": f"scope:{tag}",
    }
    values.update(overrides)
    return ContinuityObservationDraft.create(**values)  # type: ignore[arg-type]


def _rejection(
    draft: ContinuityObservationDraft,
    **overrides: object,
) -> ContinuityDraftRejection:
    values: dict[str, object] = {
        "draft": draft,
        "reason_code": "authorization_denied",
        "evidence_refs": ("policy:deny",),
    }
    values.update(overrides)
    return ContinuityDraftRejection.create(**values)  # type: ignore[arg-type]


def _receipt(
    *,
    envelope: ContinuitySourceEnvelope | None = None,
    binding: ContinuitySourceBindingReceipt | None = None,
    authorization: ContinuityAuthorizationContext | None = None,
    drafts: tuple[ContinuityObservationDraft, ...] | None = None,
    admitted: tuple[ContinuityObservationDraft, ...] | None = None,
    rejected: tuple[ContinuityDraftRejection, ...] = (),
    **overrides: object,
) -> ContinuityObservationAdmissionReceipt:
    authorization_value = authorization or _authorization()
    binding_value = binding or _binding()
    envelope_value = envelope or _envelope(
        binding=binding_value,
        authorization=authorization_value,
    )
    draft_values = drafts or (_draft(envelope=envelope_value),)
    admitted_values = draft_values if admitted is None else admitted
    values: dict[str, object] = {
        "source_envelope": envelope_value,
        "binding_receipt": binding_value,
        "authorization_context": authorization_value,
        "drafts": draft_values,
        "admitted_drafts": admitted_values,
        "rejected_drafts": rejected,
        "evaluated_at": _NOW,
    }
    values.update(overrides)
    return ContinuityObservationAdmissionReceipt.create(**values)  # type: ignore[arg-type]


def _batch(
    *,
    authorization: ContinuityAuthorizationContext | None = None,
    receipts: tuple[ContinuityObservationAdmissionReceipt, ...] | None = None,
    envelopes: tuple[ContinuitySourceEnvelope, ...] | None = None,
    bindings: tuple[ContinuitySourceBindingReceipt, ...] | None = None,
    admitted_drafts: tuple[ContinuityObservationDraft, ...] | None = None,
    **overrides: object,
) -> AuthorizedContinuityObservationBatch:
    authorization_value = authorization or _authorization()
    binding_value = _binding()
    envelope_value = _envelope(
        binding=binding_value,
        authorization=authorization_value,
    )
    draft_value = _draft(envelope=envelope_value)
    receipt_value = _receipt(
        envelope=envelope_value,
        binding=binding_value,
        authorization=authorization_value,
        drafts=(draft_value,),
        admitted=(draft_value,),
    )
    values: dict[str, object] = {
        "authorization_context": authorization_value,
        "receipts": receipts or (receipt_value,),
        "envelopes": envelopes or (envelope_value,),
        "binding_receipts": bindings or (binding_value,),
        "admitted_drafts": admitted_drafts or (draft_value,),
        "created_at": _NOW + timedelta(minutes=1),
        "valid_until": _NOW + timedelta(hours=1),
    }
    values.update(overrides)
    return AuthorizedContinuityObservationBatch.create(**values)  # type: ignore[arg-type]


def test_rejection_receipt_and_batch_are_deterministic() -> None:
    draft = _draft()
    assert _rejection(draft) == _rejection(draft)
    assert _receipt() == _receipt()
    assert _batch() == _batch()


def test_equivalent_timezone_instants_produce_same_receipt_and_batch_ids() -> None:
    offset_now = _NOW.astimezone(timezone(timedelta(hours=2)))
    assert _receipt(evaluated_at=offset_now).receipt_id == _receipt().receipt_id
    assert _batch(
        created_at=(offset_now + timedelta(minutes=1)),
        valid_until=(offset_now + timedelta(hours=1)),
    ).batch_id == _batch().batch_id


def test_rejection_is_frozen_tamper_evident_and_evidence_only() -> None:
    rejection = _rejection(_draft())
    assert rejection.to_dict()["authority"] == "draft_rejection_evidence_only"
    with pytest.raises(FrozenInstanceError):
        rejection.reason_code = "changed"  # type: ignore[misc]
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(rejection, rejection_id="0" * 64)
    with pytest.raises(ContinuitySourceAdmissionError, match="authority"):
        replace(rejection, authority="admission_authority")


@pytest.mark.parametrize("bad_value", ["policy:deny", b"policy:deny", 1, None])
def test_rejection_evidence_rejects_scalar_values(bad_value: object) -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="iterable"):
        _rejection(_draft(), evidence_refs=bad_value)


def test_rejection_requires_real_draft_and_nonempty_evidence() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="draft"):
        ContinuityDraftRejection.create(
            draft="draft",  # type: ignore[arg-type]
            reason_code="deny",
            evidence_refs=("policy:deny",),
        )
    with pytest.raises(ContinuitySourceAdmissionError, match="cannot be empty"):
        _rejection(_draft(), evidence_refs=())


def test_receipt_derives_all_three_dispositions() -> None:
    envelope = _envelope()
    admitted = _draft(envelope=envelope, tag="admitted")
    rejected_draft = _draft(
        envelope=envelope,
        signal_type=ContinuitySignalType.REQUIRES_CURRENT_STATE,
        tag="rejected",
    )
    rejection = _rejection(rejected_draft)
    assert _receipt(
        envelope=envelope,
        drafts=(admitted,),
        admitted=(admitted,),
    ).disposition is ContinuityAdmissionDisposition.ADMITTED
    assert _receipt(
        envelope=envelope,
        drafts=(rejected_draft,),
        admitted=(),
        rejected=(rejection,),
    ).disposition is ContinuityAdmissionDisposition.REJECTED
    assert _receipt(
        envelope=envelope,
        drafts=(admitted, rejected_draft),
        admitted=(admitted,),
        rejected=(rejection,),
    ).disposition is ContinuityAdmissionDisposition.PARTIAL


def test_receipt_requires_complete_disjoint_partition() -> None:
    envelope = _envelope()
    first = _draft(envelope=envelope, tag="first")
    second = _draft(
        envelope=envelope,
        signal_type=ContinuitySignalType.REQUIRES_CURRENT_STATE,
        tag="second",
    )
    with pytest.raises(ContinuitySourceAdmissionError, match="completely partition"):
        _receipt(
            envelope=envelope,
            drafts=(first, second),
            admitted=(first,),
            rejected=(),
        )
    with pytest.raises(ContinuitySourceAdmissionError, match="disjoint"):
        _receipt(
            envelope=envelope,
            drafts=(first,),
            admitted=(first,),
            rejected=(_rejection(first),),
        )


def test_receipt_rejects_unknown_admitted_or_rejected_drafts() -> None:
    envelope = _envelope()
    known = _draft(envelope=envelope, tag="known")
    unknown = _draft(
        envelope=envelope,
        signal_type=ContinuitySignalType.REQUIRES_CURRENT_STATE,
        tag="unknown",
    )
    with pytest.raises(ContinuitySourceAdmissionError, match="subset"):
        _receipt(
            envelope=envelope,
            drafts=(known,),
            admitted=(unknown,),
        )
    with pytest.raises(ContinuitySourceAdmissionError, match="subset"):
        _receipt(
            envelope=envelope,
            drafts=(known,),
            admitted=(),
            rejected=(_rejection(unknown),),
        )


def test_receipt_rejects_duplicate_draft_ids() -> None:
    envelope = _envelope()
    draft = _draft(envelope=envelope)
    with pytest.raises(ContinuitySourceAdmissionError, match="duplicate"):
        _receipt(
            envelope=envelope,
            drafts=(draft, draft),
            admitted=(draft,),
        )


def test_receipt_requires_matching_envelope_binding_and_authorization() -> None:
    authorization = _authorization()
    binding = _binding()
    envelope = _envelope(binding=binding, authorization=authorization)
    draft = _draft(envelope=envelope)
    with pytest.raises(ContinuitySourceAdmissionError, match="binding"):
        _receipt(
            envelope=envelope,
            binding=_binding(suffix="other"),
            authorization=authorization,
            drafts=(draft,),
            admitted=(draft,),
        )
    with pytest.raises(ContinuitySourceAdmissionError, match="authorization"):
        _receipt(
            envelope=envelope,
            binding=binding,
            authorization=_authorization(purpose_code="other-purpose"),
            drafts=(draft,),
            admitted=(draft,),
        )


def test_receipt_rejects_draft_from_other_envelope() -> None:
    envelope = _envelope()
    other = _envelope(binding=_binding(suffix="other"))
    with pytest.raises(ContinuitySourceAdmissionError, match="source envelope"):
        _receipt(
            envelope=envelope,
            drafts=(_draft(envelope=other),),
            admitted=(),
            rejected=(),
        )


def test_receipt_evaluation_must_follow_drafts_and_be_authorized() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="earlier"):
        _receipt(evaluated_at=_NOW - timedelta(minutes=3))
    with pytest.raises(ContinuitySourceAdmissionError, match="validity"):
        _receipt(evaluated_at=_NOW + timedelta(hours=2))
    with pytest.raises(ContinuitySourceAdmissionError, match="timezone-aware"):
        _receipt(evaluated_at=datetime(2026, 8, 6, 16, 0))


def test_receipt_is_frozen_tamper_evident_and_admission_evidence_only() -> None:
    receipt = _receipt()
    assert receipt.to_dict()["authority"] == "observation_admission_evidence_only"
    with pytest.raises(FrozenInstanceError):
        receipt.adapter_id = "changed"  # type: ignore[misc]
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(receipt, receipt_id="0" * 64)
    with pytest.raises(ContinuitySourceAdmissionError, match="authority"):
        replace(receipt, authority="runtime_authority")


def test_batch_materializes_v1_observation_from_admitted_draft() -> None:
    authorization = _authorization()
    binding = _binding()
    envelope = _envelope(binding=binding, authorization=authorization)
    draft = _draft(envelope=envelope)
    receipt = _receipt(
        envelope=envelope,
        binding=binding,
        authorization=authorization,
        drafts=(draft,),
        admitted=(draft,),
    )
    batch = _batch(
        authorization=authorization,
        receipts=(receipt,),
        envelopes=(envelope,),
        bindings=(binding,),
        admitted_drafts=(draft,),
    )
    observation = batch.observations[0]
    assert observation.signal_type is draft.signal_type
    assert observation.value == draft.value
    assert observation.confidence == draft.proposed_confidence
    assert observation.producer == envelope.producer_adapter_id
    assert observation.source_type == envelope.source_type
    assert observation.source_id == envelope.source_result_id
    assert observation.observed_at == envelope.source_as_of
    assert observation.evidence_refs == draft.evidence_refs
    assert observation.reason_codes == draft.reason_codes
    assert batch.draft_observation_links[0].draft_id == draft.draft_id
    assert batch.draft_observation_links[0].observation_id == observation.observation_id


def test_rejected_draft_never_enters_batch_observations() -> None:
    authorization = _authorization()
    binding = _binding()
    envelope = _envelope(binding=binding, authorization=authorization)
    admitted = _draft(envelope=envelope, tag="admitted")
    rejected = _draft(
        envelope=envelope,
        signal_type=ContinuitySignalType.REQUIRES_CURRENT_STATE,
        tag="rejected",
    )
    receipt = _receipt(
        envelope=envelope,
        binding=binding,
        authorization=authorization,
        drafts=(admitted, rejected),
        admitted=(admitted,),
        rejected=(_rejection(rejected),),
    )
    batch = _batch(
        authorization=authorization,
        receipts=(receipt,),
        envelopes=(envelope,),
        bindings=(binding,),
        admitted_drafts=(admitted,),
    )
    assert {link.draft_id for link in batch.draft_observation_links} == {
        admitted.draft_id
    }


def test_batch_requires_exact_receipt_admitted_draft_set() -> None:
    authorization = _authorization()
    binding = _binding()
    envelope = _envelope(binding=binding, authorization=authorization)
    first = _draft(envelope=envelope, tag="first")
    second = _draft(
        envelope=envelope,
        signal_type=ContinuitySignalType.REQUIRES_CURRENT_STATE,
        tag="second",
    )
    receipt = _receipt(
        envelope=envelope,
        binding=binding,
        authorization=authorization,
        drafts=(first, second),
        admitted=(first, second),
    )
    with pytest.raises(ContinuitySourceAdmissionError, match="exactly match"):
        _batch(
            authorization=authorization,
            receipts=(receipt,),
            envelopes=(envelope,),
            bindings=(binding,),
            admitted_drafts=(first,),
        )


def test_batch_requires_exact_receipt_envelope_and_binding_sets() -> None:
    authorization = _authorization()
    binding = _binding()
    envelope = _envelope(binding=binding, authorization=authorization)
    draft = _draft(envelope=envelope)
    receipt = _receipt(
        envelope=envelope,
        binding=binding,
        authorization=authorization,
        drafts=(draft,),
        admitted=(draft,),
    )
    with pytest.raises(ContinuitySourceAdmissionError, match="envelopes"):
        _batch(
            authorization=authorization,
            receipts=(receipt,),
            envelopes=(),
            bindings=(binding,),
            admitted_drafts=(draft,),
        )
    with pytest.raises(ContinuitySourceAdmissionError, match="binding_receipts"):
        _batch(
            authorization=authorization,
            receipts=(receipt,),
            envelopes=(envelope,),
            bindings=(),
            admitted_drafts=(draft,),
        )


def test_batch_rejects_authorization_mismatch() -> None:
    authorization = _authorization()
    binding = _binding()
    envelope = _envelope(binding=binding, authorization=authorization)
    draft = _draft(envelope=envelope)
    receipt = _receipt(
        envelope=envelope,
        binding=binding,
        authorization=authorization,
        drafts=(draft,),
        admitted=(draft,),
    )
    with pytest.raises(ContinuitySourceAdmissionError, match="authorization"):
        _batch(
            authorization=_authorization(purpose_code="other-purpose"),
            receipts=(receipt,),
            envelopes=(envelope,),
            bindings=(binding,),
            admitted_drafts=(draft,),
        )


def test_batch_unions_subjects_across_receipts() -> None:
    authorization = _authorization()
    binding_a = _binding(suffix="a", subject=_SUBJECT_A)
    binding_b = _binding(suffix="b", subject=_SUBJECT_B)
    envelope_a = _envelope(binding=binding_a, authorization=authorization)
    envelope_b = _envelope(binding=binding_b, authorization=authorization)
    draft_a = _draft(envelope=envelope_a, tag="a")
    draft_b = _draft(
        envelope=envelope_b,
        signal_type=ContinuitySignalType.REQUIRES_CURRENT_STATE,
        tag="b",
    )
    receipt_a = _receipt(
        envelope=envelope_a,
        binding=binding_a,
        authorization=authorization,
        drafts=(draft_a,),
        admitted=(draft_a,),
    )
    receipt_b = _receipt(
        envelope=envelope_b,
        binding=binding_b,
        authorization=authorization,
        drafts=(draft_b,),
        admitted=(draft_b,),
    )
    batch = _batch(
        authorization=authorization,
        receipts=(receipt_a, receipt_b),
        envelopes=(envelope_a, envelope_b),
        bindings=(binding_a, binding_b),
        admitted_drafts=(draft_a, draft_b),
    )
    assert batch.subject_refs == (_SUBJECT_A, _SUBJECT_B)
    assert len(batch.observations) == 2


def test_batch_rejects_two_drafts_that_collapse_to_one_v1_observation() -> None:
    authorization = _authorization()
    binding = _binding()
    envelope = _envelope(binding=binding, authorization=authorization)
    first = _draft(envelope=envelope, derivation_rule_id="rule:first")
    second = _draft(envelope=envelope, derivation_rule_id="rule:second")
    assert first.draft_id != second.draft_id
    receipt = _receipt(
        envelope=envelope,
        binding=binding,
        authorization=authorization,
        drafts=(first, second),
        admitted=(first, second),
    )
    with pytest.raises(ContinuitySourceAdmissionError, match="collapse"):
        _batch(
            authorization=authorization,
            receipts=(receipt,),
            envelopes=(envelope,),
            bindings=(binding,),
            admitted_drafts=(first, second),
        )


def test_batch_validity_must_follow_receipts_and_remain_inside_authorization() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="receipt evaluation"):
        _batch(created_at=_NOW - timedelta(minutes=1))
    with pytest.raises(ContinuitySourceAdmissionError, match="later"):
        _batch(valid_until=_NOW + timedelta(minutes=1))
    with pytest.raises(ContinuitySourceAdmissionError, match="authorization"):
        _batch(valid_until=_NOW + timedelta(hours=3))
    with pytest.raises(ContinuitySourceAdmissionError, match="timezone-aware"):
        _batch(created_at=datetime(2026, 8, 6, 16, 1))


def test_batch_is_frozen_tamper_evident_and_has_no_runtime_authority() -> None:
    batch = _batch()
    assert batch.no_runtime_authority is True
    assert batch.to_dict()["no_runtime_authority"] is True
    with pytest.raises(FrozenInstanceError):
        batch.tenant_ref = "changed"  # type: ignore[misc]
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(batch, batch_id="0" * 64)
    with pytest.raises(ContinuitySourceAdmissionError, match="no_runtime_authority"):
        replace(batch, no_runtime_authority=False)


def test_trace_link_is_frozen_tamper_evident_and_trace_only() -> None:
    link = _batch().draft_observation_links[0]
    assert link.to_dict()["authority"] == "draft_observation_trace_only"
    with pytest.raises(FrozenInstanceError):
        link.draft_id = "changed"  # type: ignore[misc]
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(link, link_id="0" * 64)
    with pytest.raises(ContinuitySourceAdmissionError, match="authority"):
        replace(link, authority="runtime_authority")


def test_batch_direct_constructor_rejects_broken_trace_mapping() -> None:
    batch = _batch()
    link = batch.draft_observation_links[0]
    wrong_link = ContinuityDraftObservationLink(
        link_id=link.link_id,
        schema_version=link.schema_version,
        draft_id=link.draft_id,
        observation_id="0" * 64,
        source_envelope_id=link.source_envelope_id,
        authority=link.authority,
    )
    with pytest.raises(ContinuitySourceAdmissionError):
        replace(batch, draft_observation_links=(wrong_link,))


def test_serialization_contains_no_runtime_or_admission_executor_fields() -> None:
    receipt_payload = _receipt().to_dict()
    batch_payload = _batch().to_dict()
    assert receipt_payload["schema_version"] == SOURCE_ADMISSION_DECISION_SCHEMA_VERSION
    assert batch_payload["schema_version"] == SOURCE_ADMISSION_DECISION_SCHEMA_VERSION
    forbidden = {
        "answer",
        "action",
        "tool",
        "execute",
        "canon_write",
        "retrieval_write",
        "runtime_override",
        "final_decision",
        "persist",
        "enabled",
    }
    assert forbidden.isdisjoint(receipt_payload)
    assert forbidden.isdisjoint(batch_payload)
