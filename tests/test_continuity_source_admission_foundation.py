"""Adversarial tests for foundational Continuity source-admission contracts."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from hashlib import sha256

import pytest

from core.continuity.contracts import SubjectKind, SubjectRef
from core.continuity.source_admission import (
    SOURCE_ADMISSION_SCHEMA_VERSION,
    ContinuityAuthorizationContext,
    ContinuityPrincipalContext,
    ContinuitySourceAdmissionError,
    ContinuitySourceBindingReceipt,
)

_NOW = datetime(2026, 8, 6, 12, 0, tzinfo=UTC)
_SUBJECT_A = SubjectRef(subject_id="subject-a", kind=SubjectKind.PERSON)
_SUBJECT_B = SubjectRef(subject_id="subject-b", kind=SubjectKind.PROJECT)
_SOURCE_DIGEST = sha256(b"source-result").hexdigest()
_CREDENTIAL_FINGERPRINT = sha256(b"credential").hexdigest()


def _principal(**overrides: object) -> ContinuityPrincipalContext:
    values: dict[str, object] = {
        "principal_ref": "principal:alice",
        "principal_kind": "human",
        "authentication_method": "oidc",
        "authentication_strength": "mfa",
        "authenticated_at": _NOW,
        "issuer_ref": "issuer:test",
        "authentication_receipt_ref": "auth-receipt:1",
        "session_ref": "session:1",
        "credential_fingerprint": _CREDENTIAL_FINGERPRINT,
    }
    values.update(overrides)
    return ContinuityPrincipalContext.create(**values)  # type: ignore[arg-type]


def _authorization(**overrides: object) -> ContinuityAuthorizationContext:
    values: dict[str, object] = {
        "tenant_ref": "tenant:one",
        "subject_refs": (_SUBJECT_B, _SUBJECT_A),
        "principal_context": _principal(),
        "purpose_code": "continuity_analysis",
        "lawful_basis_or_consent_ref": "consent:1",
        "authorization_receipt_ref": "authorization:1",
        "policy_snapshot_id": "policy:1",
        "retention_class": "ephemeral",
        "erasure_domain_refs": ("erasure:b", "erasure:a"),
        "valid_from": _NOW,
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
        "subject_refs": (_SUBJECT_B, _SUBJECT_A),
        "source_component_version": "1",
        "source_policy_version": "1",
        "source_as_of": _NOW,
        "evidence_refs": ("event:b", "event:a"),
        "issued_at": _NOW,
    }
    values.update(overrides)
    return ContinuitySourceBindingReceipt.create(**values)  # type: ignore[arg-type]


def test_contracts_are_deterministic_and_content_addressed() -> None:
    assert _principal() == _principal()
    assert _authorization() == _authorization()
    assert _binding() == _binding()


def test_equivalent_timezone_instants_have_same_principal_identity() -> None:
    utc_value = _principal(authenticated_at=_NOW)
    offset_value = _principal(
        authenticated_at=_NOW.astimezone(timezone(timedelta(hours=2)))
    )
    assert utc_value.principal_context_id == offset_value.principal_context_id


def test_subjects_and_refs_are_sorted_canonically() -> None:
    authorization = _authorization()
    assert authorization.subject_refs == (_SUBJECT_A, _SUBJECT_B)
    assert authorization.erasure_domain_refs == ("erasure:a", "erasure:b")
    binding = _binding()
    assert binding.subject_refs == (_SUBJECT_A, _SUBJECT_B)
    assert binding.evidence_refs == ("event:a", "event:b")


def test_mutable_inputs_do_not_alias_contract_state() -> None:
    subjects = [_SUBJECT_A]
    erasure_refs = ["erasure:a"]
    authorization = _authorization(
        subject_refs=subjects,
        erasure_domain_refs=erasure_refs,
    )
    subjects.append(_SUBJECT_B)
    erasure_refs.append("erasure:b")
    assert authorization.subject_refs == (_SUBJECT_A,)
    assert authorization.erasure_domain_refs == ("erasure:a",)


def test_one_shot_iterables_are_consumed_once_and_normalized() -> None:
    authorization = _authorization(
        subject_refs=(value for value in (_SUBJECT_B, _SUBJECT_A)),
        erasure_domain_refs=(value for value in ("b", "a")),
    )
    assert authorization.subject_refs == (_SUBJECT_A, _SUBJECT_B)
    assert authorization.erasure_domain_refs == ("a", "b")


@pytest.mark.parametrize("bad_value", [datetime(2026, 8, 6), "now", None])
def test_principal_timestamp_must_be_timezone_aware(bad_value: object) -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="timezone-aware"):
        _principal(authenticated_at=bad_value)


@pytest.mark.parametrize("bad_value", [datetime(2026, 8, 6), "now", None])
def test_authorization_timestamps_must_be_timezone_aware(
    bad_value: object,
) -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="timezone-aware"):
        _authorization(valid_from=bad_value)
    with pytest.raises(ContinuitySourceAdmissionError, match="timezone-aware"):
        _authorization(valid_until=bad_value)


@pytest.mark.parametrize("bad_value", [datetime(2026, 8, 6), "now", None])
def test_binding_timestamps_must_be_timezone_aware(bad_value: object) -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="timezone-aware"):
        _binding(source_as_of=bad_value)
    with pytest.raises(ContinuitySourceAdmissionError, match="timezone-aware"):
        _binding(issued_at=bad_value)


@pytest.mark.parametrize("bad_value", ["text", b"bytes", 1, None])
def test_scalar_values_are_not_accepted_as_collections(bad_value: object) -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="iterable"):
        _authorization(subject_refs=bad_value)
    with pytest.raises(ContinuitySourceAdmissionError, match="iterable"):
        _authorization(erasure_domain_refs=bad_value)
    with pytest.raises(ContinuitySourceAdmissionError, match="iterable"):
        _binding(evidence_refs=bad_value)


def test_collection_members_must_have_expected_types() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="SubjectRef"):
        _authorization(subject_refs=("subject-a",))
    with pytest.raises(ContinuitySourceAdmissionError, match="string"):
        _binding(evidence_refs=(1,))


def test_required_collections_cannot_be_empty() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="cannot be empty"):
        _authorization(subject_refs=())
    with pytest.raises(ContinuitySourceAdmissionError, match="cannot be empty"):
        _authorization(erasure_domain_refs=())
    with pytest.raises(ContinuitySourceAdmissionError, match="cannot be empty"):
        _binding(evidence_refs=())


def test_duplicate_collection_members_are_rejected() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="duplicates"):
        _authorization(subject_refs=(_SUBJECT_A, _SUBJECT_A))
    with pytest.raises(ContinuitySourceAdmissionError, match="duplicates"):
        _authorization(erasure_domain_refs=("x", "x"))
    with pytest.raises(ContinuitySourceAdmissionError, match="duplicates"):
        _binding(evidence_refs=("x", "x"))


def test_authorization_interval_must_be_positive() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="later"):
        _authorization(valid_until=_NOW)
    with pytest.raises(ContinuitySourceAdmissionError, match="later"):
        _authorization(valid_until=_NOW - timedelta(seconds=1))


def test_binding_cannot_be_issued_before_source_exists() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="earlier"):
        _binding(issued_at=_NOW - timedelta(microseconds=1))


def test_hash_shaped_fields_reject_non_sha256_values() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="SHA-256"):
        _principal(credential_fingerprint="not-a-hash")
    with pytest.raises(ContinuitySourceAdmissionError, match="SHA-256"):
        _binding(source_digest="not-a-hash")


def test_authorization_requires_a_real_principal_context() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="principal_context"):
        _authorization(principal_context="principal:alice")


def test_strings_are_trimmed_and_unicode_normalized_before_hashing() -> None:
    composed = _principal(principal_ref="  caf\u00e9  ")
    decomposed = _principal(principal_ref="cafe\u0301")
    assert composed.principal_ref == "caf\u00e9"
    assert composed.principal_context_id == decomposed.principal_context_id


def test_contracts_are_frozen() -> None:
    principal = _principal()
    authorization = _authorization()
    binding = _binding()
    with pytest.raises(FrozenInstanceError):
        principal.principal_ref = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        authorization.tenant_ref = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        binding.source_owner = "changed"  # type: ignore[misc]


def test_direct_principal_constructor_rejects_tampered_id() -> None:
    value = _principal()
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        ContinuityPrincipalContext(
            principal_context_id="0" * 64,
            schema_version=value.schema_version,
            principal_ref=value.principal_ref,
            principal_kind=value.principal_kind,
            authentication_method=value.authentication_method,
            authentication_strength=value.authentication_strength,
            authenticated_at=value.authenticated_at,
            issuer_ref=value.issuer_ref,
            authentication_receipt_ref=value.authentication_receipt_ref,
            session_ref=value.session_ref,
            credential_fingerprint=value.credential_fingerprint,
        )


def test_direct_authorization_constructor_rejects_tampered_id() -> None:
    value = _authorization()
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        ContinuityAuthorizationContext(
            authorization_context_id="0" * 64,
            schema_version=value.schema_version,
            tenant_ref=value.tenant_ref,
            subject_refs=value.subject_refs,
            principal_context_id=value.principal_context_id,
            purpose_code=value.purpose_code,
            lawful_basis_or_consent_ref=value.lawful_basis_or_consent_ref,
            authorization_receipt_ref=value.authorization_receipt_ref,
            policy_snapshot_id=value.policy_snapshot_id,
            retention_class=value.retention_class,
            erasure_domain_refs=value.erasure_domain_refs,
            valid_from=value.valid_from,
            valid_until=value.valid_until,
            data_handling_mode=value.data_handling_mode,
            capability_lease_id=value.capability_lease_id,
        )


def test_direct_binding_constructor_rejects_tampered_id() -> None:
    value = _binding()
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        ContinuitySourceBindingReceipt(
            binding_receipt_id="0" * 64,
            schema_version=value.schema_version,
            source_type=value.source_type,
            source_result_id=value.source_result_id,
            source_digest=value.source_digest,
            source_owner=value.source_owner,
            tenant_ref=value.tenant_ref,
            subject_refs=value.subject_refs,
            source_component_version=value.source_component_version,
            source_policy_version=value.source_policy_version,
            source_as_of=value.source_as_of,
            evidence_refs=value.evidence_refs,
            issued_at=value.issued_at,
        )


def test_serialization_exposes_evidence_only_authority_markers() -> None:
    expected = (
        (_principal(), "authentication_evidence_only"),
        (_authorization(), "authorization_evidence_only"),
        (_binding(), "source_ownership_evidence_only"),
    )
    forbidden = {
        "answer",
        "action",
        "tool",
        "execute",
        "canon_write",
        "retrieval_write",
        "runtime_override",
        "final_decision",
    }
    for value, authority in expected:
        payload = value.to_dict()
        assert payload["authority"] == authority
        assert payload["schema_version"] == SOURCE_ADMISSION_SCHEMA_VERSION
        assert forbidden.isdisjoint(payload)


def test_serialization_never_contains_raw_credentials() -> None:
    payload = _principal().to_dict()
    assert "credential" not in payload
    assert "api_key" not in payload
    assert "token" not in payload
    assert payload["credential_fingerprint"] == _CREDENTIAL_FINGERPRINT
