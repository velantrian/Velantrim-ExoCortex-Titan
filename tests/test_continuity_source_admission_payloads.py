"""Adversarial tests for source envelopes and observation drafts."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from hashlib import sha256
import math

import pytest

from core.continuity.contracts import SubjectKind, SubjectRef
from core.continuity.observations import ContinuitySignalType
from core.continuity.source_admission import (
    ContinuityAuthorizationContext,
    ContinuityPrincipalContext,
    ContinuitySourceAdmissionError,
    ContinuitySourceBindingReceipt,
)
from core.continuity.source_admission_payloads import (
    SOURCE_ADMISSION_PAYLOAD_SCHEMA_VERSION,
    ContinuityObservationDraft,
    ContinuitySourceEnvelope,
)

_NOW = datetime(2026, 8, 6, 14, 0, tzinfo=UTC)
_SUBJECT_A = SubjectRef(subject_id="subject-a", kind=SubjectKind.PERSON)
_SUBJECT_B = SubjectRef(subject_id="subject-b", kind=SubjectKind.PROJECT)
_SUBJECT_C = SubjectRef(subject_id="subject-c", kind=SubjectKind.PERSON)
_SOURCE_DIGEST = sha256(b"state-result").hexdigest()


def _principal() -> ContinuityPrincipalContext:
    return ContinuityPrincipalContext.create(
        principal_ref="principal:alice",
        principal_kind="human",
        authentication_method="oidc",
        authentication_strength="mfa",
        authenticated_at=_NOW - timedelta(minutes=10),
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
        "valid_from": _NOW - timedelta(minutes=5),
        "valid_until": _NOW + timedelta(hours=1),
        "data_handling_mode": "local_only",
    }
    values.update(overrides)
    return ContinuityAuthorizationContext.create(**values)  # type: ignore[arg-type]


def _binding(**overrides: object) -> ContinuitySourceBindingReceipt:
    values: dict[str, object] = {
        "source_type": "state_reconciliation_result",
        "source_result_id": "state-result:1",
        "source_digest": _SOURCE_DIGEST,
        "source_owner": "continuity.state_reconciler",
        "tenant_ref": "tenant:one",
        "subject_refs": (_SUBJECT_A,),
        "source_component_version": "1",
        "source_policy_version": "1",
        "source_as_of": _NOW - timedelta(minutes=2),
        "evidence_refs": ("event:a", "event:b"),
        "issued_at": _NOW - timedelta(minutes=1),
    }
    values.update(overrides)
    return ContinuitySourceBindingReceipt.create(**values)  # type: ignore[arg-type]


def _envelope(**overrides: object) -> ContinuitySourceEnvelope:
    values: dict[str, object] = {
        "binding_receipt": _binding(),
        "authorization_context": _authorization(),
        "source_schema_version": "state-reconciliation.v1",
        "producer_adapter_id": "continuity.state_to_signal_draft",
        "producer_adapter_version": "1",
        "created_at": _NOW,
    }
    values.update(overrides)
    return ContinuitySourceEnvelope.create(**values)  # type: ignore[arg-type]


def _draft(**overrides: object) -> ContinuityObservationDraft:
    values: dict[str, object] = {
        "source_envelope": _envelope(),
        "signal_type": ContinuitySignalType.CONTEXT_DEGRADED,
        "value": True,
        "proposed_confidence": 0.9,
        "evidence_refs": ("event:a",),
        "reason_codes": ("state_contested",),
        "derivation_rule_id": "state.contested.v1",
        "created_at": _NOW,
    }
    values.update(overrides)
    return ContinuityObservationDraft.create(**values)  # type: ignore[arg-type]


def test_envelope_and_draft_are_deterministic() -> None:
    assert _envelope() == _envelope()
    assert _draft() == _draft()


def test_equivalent_timezone_instants_have_same_identity() -> None:
    offset_now = _NOW.astimezone(timezone(timedelta(hours=2)))
    assert _envelope(created_at=offset_now).envelope_id == _envelope().envelope_id
    assert _draft(created_at=offset_now).draft_id == _draft().draft_id


def test_envelope_copies_complete_binding_scope_and_evidence() -> None:
    binding = _binding(subject_refs=(_SUBJECT_B, _SUBJECT_A))
    envelope = _envelope(binding_receipt=binding)
    assert envelope.subject_refs == (_SUBJECT_A, _SUBJECT_B)
    assert envelope.evidence_refs == ("event:a", "event:b")
    assert envelope.source_binding_receipt_id == binding.binding_receipt_id
    assert envelope.source_digest == binding.source_digest


def test_envelope_rejects_tenant_mismatch() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="tenant"):
        _envelope(binding_receipt=_binding(tenant_ref="tenant:other"))


def test_envelope_rejects_any_unauthorized_source_subject() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="subset"):
        _envelope(binding_receipt=_binding(subject_refs=(_SUBJECT_A, _SUBJECT_C)))


def test_envelope_requires_real_foundational_contracts() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="binding_receipt"):
        _envelope(binding_receipt="binding:1")
    with pytest.raises(ContinuitySourceAdmissionError, match="authorization_context"):
        _envelope(authorization_context="authorization:1")


def test_envelope_created_at_must_be_timezone_aware() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="timezone-aware"):
        _envelope(created_at=datetime(2026, 8, 6, 14, 0))


def test_envelope_cannot_predate_source_or_binding_receipt() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="source_as_of"):
        _envelope(created_at=_NOW - timedelta(minutes=3))
    with pytest.raises(ContinuitySourceAdmissionError, match="issued_at"):
        _envelope(created_at=_NOW - timedelta(minutes=1, seconds=1))


def test_envelope_must_be_created_inside_authorization_window() -> None:
    not_yet_valid = _authorization(
        valid_from=_NOW + timedelta(minutes=1),
        valid_until=_NOW + timedelta(hours=1),
    )
    with pytest.raises(ContinuitySourceAdmissionError, match="validity"):
        _envelope(authorization_context=not_yet_valid, created_at=_NOW)
    with pytest.raises(ContinuitySourceAdmissionError, match="validity"):
        _envelope(created_at=_NOW + timedelta(hours=1))


def test_envelope_is_frozen_and_authority_is_fixed() -> None:
    envelope = _envelope()
    with pytest.raises(FrozenInstanceError):
        envelope.tenant_ref = "tenant:other"  # type: ignore[misc]
    with pytest.raises(ContinuitySourceAdmissionError, match="authority"):
        replace(envelope, authority="runtime_authority")


def test_direct_envelope_constructor_rejects_tampered_id() -> None:
    value = _envelope()
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(value, envelope_id="0" * 64)


@pytest.mark.parametrize(
    ("signal_type", "value"),
    [
        (ContinuitySignalType.CONTEXT_DEGRADED, True),
        (ContinuitySignalType.CONTEXT_DEGRADED, False),
        (ContinuitySignalType.EVIDENCE_COVERAGE_ITEM, True),
        (ContinuitySignalType.CONTINUITY_AVAILABLE, False),
        (ContinuitySignalType.IMPORTANT_CLAIM, True),
        (ContinuitySignalType.REQUIRES_CURRENT_STATE, True),
        (ContinuitySignalType.ACTIVE_CONTRADICTION, True),
        (ContinuitySignalType.CONTEXT_FRESHNESS, "unknown"),
        (ContinuitySignalType.CONTEXT_FRESHNESS, "fresh"),
        (ContinuitySignalType.CONTEXT_FRESHNESS, "stale"),
        (ContinuitySignalType.CONTEXT_FRESHNESS, "critical_stale"),
        (ContinuitySignalType.SENSITIVITY, "low"),
        (ContinuitySignalType.SENSITIVITY, "medium"),
        (ContinuitySignalType.SENSITIVITY, "high"),
        (ContinuitySignalType.SENSITIVITY, "critical"),
    ],
)
def test_draft_accepts_supported_signal_shapes(
    signal_type: ContinuitySignalType,
    value: object,
) -> None:
    assert _draft(signal_type=signal_type, value=value).value == value


@pytest.mark.parametrize("bad_value", [1, 0, "true", None])
def test_boolean_draft_rejects_non_bool_values(bad_value: object) -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="bool"):
        _draft(value=bad_value)


def test_active_contradiction_requires_true() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="value=True"):
        _draft(
            signal_type=ContinuitySignalType.ACTIVE_CONTRADICTION,
            value=False,
        )


@pytest.mark.parametrize("bad_value", ["current", "partial", 1, True])
def test_context_freshness_rejects_unknown_values(bad_value: object) -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="context_freshness"):
        _draft(
            signal_type=ContinuitySignalType.CONTEXT_FRESHNESS,
            value=bad_value,
        )


@pytest.mark.parametrize("bad_value", ["urgent", "none", 1, True])
def test_sensitivity_rejects_unknown_values(bad_value: object) -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="sensitivity"):
        _draft(signal_type=ContinuitySignalType.SENSITIVITY, value=bad_value)


@pytest.mark.parametrize(
    "bad_confidence",
    [True, False, "0.5", -0.1, 1.1, math.nan, math.inf, -math.inf],
)
def test_draft_confidence_is_finite_bool_excluded_and_bounded(
    bad_confidence: object,
) -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="confidence"):
        _draft(proposed_confidence=bad_confidence)


def test_draft_requires_real_envelope_and_signal_enum() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="source_envelope"):
        _draft(source_envelope="envelope:1")
    with pytest.raises(ContinuitySourceAdmissionError, match="signal_type"):
        _draft(signal_type="context_degraded")


@pytest.mark.parametrize("bad_value", ["event:a", b"event:a", 1, None])
def test_draft_collections_reject_scalar_values(bad_value: object) -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="iterable"):
        _draft(evidence_refs=bad_value)
    with pytest.raises(ContinuitySourceAdmissionError, match="iterable"):
        _draft(reason_codes=bad_value)


def test_draft_requires_nonempty_evidence_and_reasons() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="cannot be empty"):
        _draft(evidence_refs=())
    with pytest.raises(ContinuitySourceAdmissionError, match="cannot be empty"):
        _draft(reason_codes=())


def test_draft_rejects_duplicate_evidence_and_reasons() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="duplicates"):
        _draft(evidence_refs=("event:a", "event:a"))
    with pytest.raises(ContinuitySourceAdmissionError, match="duplicates"):
        _draft(reason_codes=("reason", "reason"))


def test_draft_evidence_must_be_subset_of_envelope_evidence() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="subset"):
        _draft(evidence_refs=("event:not-in-envelope",))


def test_draft_collections_are_sorted_and_do_not_alias_mutable_inputs() -> None:
    evidence = ["event:b", "event:a"]
    reasons = ["z", "a"]
    draft = _draft(evidence_refs=evidence, reason_codes=reasons)
    evidence.append("event:c")
    reasons.append("later")
    assert draft.evidence_refs == ("event:a", "event:b")
    assert draft.reason_codes == ("a", "z")


def test_draft_supports_one_shot_iterables() -> None:
    draft = _draft(
        evidence_refs=(value for value in ("event:b", "event:a")),
        reason_codes=(value for value in ("z", "a")),
    )
    assert draft.evidence_refs == ("event:a", "event:b")
    assert draft.reason_codes == ("a", "z")


def test_draft_cannot_predate_envelope() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="envelope"):
        _draft(created_at=_NOW - timedelta(microseconds=1))


def test_draft_created_at_must_be_timezone_aware() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="timezone-aware"):
        _draft(created_at=datetime(2026, 8, 6, 14, 0))


def test_draft_normalizes_unicode_and_optional_scope() -> None:
    composed = _draft(derivation_rule_id="  caf\u00e9  ", scope="  scope:a  ")
    decomposed = _draft(derivation_rule_id="cafe\u0301", scope="scope:a")
    assert composed.derivation_rule_id == "caf\u00e9"
    assert composed.scope == "scope:a"
    assert composed.draft_id == decomposed.draft_id


def test_draft_is_frozen_and_authority_is_fixed() -> None:
    draft = _draft()
    with pytest.raises(FrozenInstanceError):
        draft.value = False  # type: ignore[misc]
    with pytest.raises(ContinuitySourceAdmissionError, match="authority"):
        replace(draft, authority="admitted")


def test_direct_draft_constructor_rejects_tampered_id() -> None:
    value = _draft()
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(value, draft_id="0" * 64)


def test_serialization_is_proposal_only_and_has_no_runtime_fields() -> None:
    envelope_payload = _envelope().to_dict()
    draft_payload = _draft().to_dict()
    assert envelope_payload["schema_version"] == SOURCE_ADMISSION_PAYLOAD_SCHEMA_VERSION
    assert envelope_payload["authority"] == "analysis_proposal_only"
    assert draft_payload["schema_version"] == SOURCE_ADMISSION_PAYLOAD_SCHEMA_VERSION
    assert draft_payload["authority"] == "observation_proposal_only"
    forbidden = {
        "answer",
        "action",
        "tool",
        "execute",
        "canon_write",
        "retrieval_write",
        "runtime_override",
        "final_decision",
        "admitted",
        "approved",
    }
    assert forbidden.isdisjoint(envelope_payload)
    assert forbidden.isdisjoint(draft_payload)


def test_payloads_do_not_embed_raw_source_or_authorization_objects() -> None:
    envelope_payload = _envelope().to_dict()
    draft_payload = _draft().to_dict()
    assert "source_result" not in envelope_payload
    assert "binding_receipt" not in envelope_payload
    assert "authorization_context" not in envelope_payload
    assert "source_envelope" not in draft_payload
