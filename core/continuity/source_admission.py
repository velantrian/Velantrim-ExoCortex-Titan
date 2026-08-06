"""Neutral content-addressed contracts for Continuity source admission.

These contracts carry evidence only. They read no clock, environment, network,
database, or process-global state and grant no Canon, TruthGate, compute-route,
persistence, response, reminder, tool, action, or activation authority.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
import re
import unicodedata

from .contracts import SubjectRef

SOURCE_ADMISSION_SCHEMA_VERSION = "continuity.source_admission.v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ContinuitySourceAdmissionError(ValueError):
    """Raised when a source-admission contract invariant is violated."""


def _text(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise ContinuitySourceAdmissionError(f"{name} must be a non-empty string")
    normalized = unicodedata.normalize("NFC", value).strip()
    if not normalized:
        raise ContinuitySourceAdmissionError(f"{name} must be a non-empty string")
    return normalized


def _optional_text(value: object, name: str) -> str | None:
    return None if value is None else _text(value, name)


def _aware(value: object, name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ContinuitySourceAdmissionError(f"{name} must be timezone-aware")
    return value


def _canonical_datetime(value: datetime) -> str:
    return (
        _aware(value, "datetime")
        .astimezone(UTC)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(payload: object) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _hash(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ContinuitySourceAdmissionError(
            f"{name} must be a lowercase SHA-256 hex digest"
        )
    return value


def _items(values: object, name: str) -> tuple[object, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ContinuitySourceAdmissionError(f"{name} must be an iterable")
    try:
        return tuple(values)
    except TypeError as exc:
        raise ContinuitySourceAdmissionError(f"{name} must be an iterable") from exc


def _refs(
    values: object,
    name: str,
    *,
    required: bool = False,
) -> tuple[str, ...]:
    refs = tuple(_text(value, name) for value in _items(values, name))
    if required and not refs:
        raise ContinuitySourceAdmissionError(f"{name} cannot be empty")
    if len(refs) != len(set(refs)):
        raise ContinuitySourceAdmissionError(f"{name} cannot contain duplicates")
    return tuple(sorted(refs))


def _subjects(values: object) -> tuple[SubjectRef, ...]:
    items = _items(values, "subject_refs")
    if not items:
        raise ContinuitySourceAdmissionError("subject_refs cannot be empty")
    if any(not isinstance(value, SubjectRef) for value in items):
        raise ContinuitySourceAdmissionError(
            "subject_refs must contain SubjectRef values"
        )
    subjects = tuple(value for value in items if isinstance(value, SubjectRef))
    keys = tuple((value.subject_id, value.kind.value) for value in subjects)
    if len(keys) != len(set(keys)):
        raise ContinuitySourceAdmissionError(
            "subject_refs cannot contain duplicates"
        )
    return tuple(
        sorted(subjects, key=lambda value: (value.subject_id, value.kind.value))
    )


def _subject_payload(subjects: tuple[SubjectRef, ...]) -> list[dict[str, str]]:
    return [subject.identity_payload() for subject in subjects]


def _verify_id(actual: object, expected: str, name: str) -> None:
    if actual != expected:
        raise ContinuitySourceAdmissionError(
            f"{name} must match canonical contract content"
        )


@dataclass(frozen=True, slots=True)
class ContinuityPrincipalContext:
    """Authenticated-principal evidence supplied by an external owner."""

    principal_context_id: str
    schema_version: str
    principal_ref: str
    principal_kind: str
    authentication_method: str
    authentication_strength: str
    authenticated_at: datetime
    issuer_ref: str
    authentication_receipt_ref: str
    session_ref: str | None = None
    credential_fingerprint: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        object.__setattr__(
            self, "principal_ref", _text(self.principal_ref, "principal_ref")
        )
        object.__setattr__(
            self, "principal_kind", _text(self.principal_kind, "principal_kind")
        )
        object.__setattr__(
            self,
            "authentication_method",
            _text(self.authentication_method, "authentication_method"),
        )
        object.__setattr__(
            self,
            "authentication_strength",
            _text(self.authentication_strength, "authentication_strength"),
        )
        object.__setattr__(
            self,
            "authenticated_at",
            _aware(self.authenticated_at, "authenticated_at"),
        )
        object.__setattr__(
            self, "issuer_ref", _text(self.issuer_ref, "issuer_ref")
        )
        object.__setattr__(
            self,
            "authentication_receipt_ref",
            _text(
                self.authentication_receipt_ref,
                "authentication_receipt_ref",
            ),
        )
        object.__setattr__(
            self, "session_ref", _optional_text(self.session_ref, "session_ref")
        )
        if self.credential_fingerprint is not None:
            object.__setattr__(
                self,
                "credential_fingerprint",
                _hash(self.credential_fingerprint, "credential_fingerprint"),
            )
        _verify_id(
            self.principal_context_id,
            _digest(self.identity_payload()),
            "principal_context_id",
        )

    @classmethod
    def create(
        cls,
        *,
        principal_ref: str,
        principal_kind: str,
        authentication_method: str,
        authentication_strength: str,
        authenticated_at: datetime,
        issuer_ref: str,
        authentication_receipt_ref: str,
        session_ref: str | None = None,
        credential_fingerprint: str | None = None,
        schema_version: str = SOURCE_ADMISSION_SCHEMA_VERSION,
    ) -> ContinuityPrincipalContext:
        schema = _text(schema_version, "schema_version")
        principal = _text(principal_ref, "principal_ref")
        kind = _text(principal_kind, "principal_kind")
        method = _text(authentication_method, "authentication_method")
        strength = _text(authentication_strength, "authentication_strength")
        authenticated = _aware(authenticated_at, "authenticated_at")
        issuer = _text(issuer_ref, "issuer_ref")
        receipt = _text(
            authentication_receipt_ref,
            "authentication_receipt_ref",
        )
        session = _optional_text(session_ref, "session_ref")
        fingerprint = (
            None
            if credential_fingerprint is None
            else _hash(credential_fingerprint, "credential_fingerprint")
        )
        payload: dict[str, object] = {
            "schema_version": schema,
            "principal_ref": principal,
            "principal_kind": kind,
            "authentication_method": method,
            "authentication_strength": strength,
            "authenticated_at": _canonical_datetime(authenticated),
            "issuer_ref": issuer,
            "authentication_receipt_ref": receipt,
            "session_ref": session,
            "credential_fingerprint": fingerprint,
        }
        return cls(
            principal_context_id=_digest(payload),
            schema_version=schema,
            principal_ref=principal,
            principal_kind=kind,
            authentication_method=method,
            authentication_strength=strength,
            authenticated_at=authenticated,
            issuer_ref=issuer,
            authentication_receipt_ref=receipt,
            session_ref=session,
            credential_fingerprint=fingerprint,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "principal_ref": self.principal_ref,
            "principal_kind": self.principal_kind,
            "authentication_method": self.authentication_method,
            "authentication_strength": self.authentication_strength,
            "authenticated_at": _canonical_datetime(self.authenticated_at),
            "issuer_ref": self.issuer_ref,
            "authentication_receipt_ref": self.authentication_receipt_ref,
            "session_ref": self.session_ref,
            "credential_fingerprint": self.credential_fingerprint,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "principal_context_id": self.principal_context_id,
            **self.identity_payload(),
            "authority": "authentication_evidence_only",
        }


@dataclass(frozen=True, slots=True)
class ContinuityAuthorizationContext:
    """Bounded tenant/subject/purpose authorization evidence."""

    authorization_context_id: str
    schema_version: str
    tenant_ref: str
    subject_refs: tuple[SubjectRef, ...]
    principal_context_id: str
    purpose_code: str
    lawful_basis_or_consent_ref: str
    authorization_receipt_ref: str
    policy_snapshot_id: str
    retention_class: str
    erasure_domain_refs: tuple[str, ...]
    valid_from: datetime
    valid_until: datetime
    data_handling_mode: str
    capability_lease_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        object.__setattr__(
            self, "tenant_ref", _text(self.tenant_ref, "tenant_ref")
        )
        object.__setattr__(self, "subject_refs", _subjects(self.subject_refs))
        object.__setattr__(
            self,
            "principal_context_id",
            _hash(self.principal_context_id, "principal_context_id"),
        )
        for field_name in (
            "purpose_code",
            "lawful_basis_or_consent_ref",
            "authorization_receipt_ref",
            "policy_snapshot_id",
            "retention_class",
            "data_handling_mode",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "erasure_domain_refs",
            _refs(self.erasure_domain_refs, "erasure_domain_refs", required=True),
        )
        object.__setattr__(
            self, "valid_from", _aware(self.valid_from, "valid_from")
        )
        object.__setattr__(
            self, "valid_until", _aware(self.valid_until, "valid_until")
        )
        if self.valid_until <= self.valid_from:
            raise ContinuitySourceAdmissionError(
                "valid_until must be later than valid_from"
            )
        object.__setattr__(
            self,
            "capability_lease_id",
            _optional_text(self.capability_lease_id, "capability_lease_id"),
        )
        _verify_id(
            self.authorization_context_id,
            _digest(self.identity_payload()),
            "authorization_context_id",
        )

    @classmethod
    def create(
        cls,
        *,
        tenant_ref: str,
        subject_refs: Iterable[SubjectRef],
        principal_context: ContinuityPrincipalContext,
        purpose_code: str,
        lawful_basis_or_consent_ref: str,
        authorization_receipt_ref: str,
        policy_snapshot_id: str,
        retention_class: str,
        erasure_domain_refs: Iterable[str],
        valid_from: datetime,
        valid_until: datetime,
        data_handling_mode: str,
        capability_lease_id: str | None = None,
        schema_version: str = SOURCE_ADMISSION_SCHEMA_VERSION,
    ) -> ContinuityAuthorizationContext:
        if not isinstance(principal_context, ContinuityPrincipalContext):
            raise ContinuitySourceAdmissionError(
                "principal_context must be a ContinuityPrincipalContext"
            )
        schema = _text(schema_version, "schema_version")
        tenant = _text(tenant_ref, "tenant_ref")
        subjects = _subjects(subject_refs)
        purpose = _text(purpose_code, "purpose_code")
        basis = _text(
            lawful_basis_or_consent_ref,
            "lawful_basis_or_consent_ref",
        )
        receipt = _text(
            authorization_receipt_ref,
            "authorization_receipt_ref",
        )
        snapshot = _text(policy_snapshot_id, "policy_snapshot_id")
        retention = _text(retention_class, "retention_class")
        erasure_refs = _refs(
            erasure_domain_refs,
            "erasure_domain_refs",
            required=True,
        )
        start = _aware(valid_from, "valid_from")
        end = _aware(valid_until, "valid_until")
        if end <= start:
            raise ContinuitySourceAdmissionError(
                "valid_until must be later than valid_from"
            )
        handling_mode = _text(data_handling_mode, "data_handling_mode")
        lease = _optional_text(capability_lease_id, "capability_lease_id")
        payload: dict[str, object] = {
            "schema_version": schema,
            "tenant_ref": tenant,
            "subject_refs": _subject_payload(subjects),
            "principal_context_id": principal_context.principal_context_id,
            "purpose_code": purpose,
            "lawful_basis_or_consent_ref": basis,
            "authorization_receipt_ref": receipt,
            "policy_snapshot_id": snapshot,
            "retention_class": retention,
            "erasure_domain_refs": list(erasure_refs),
            "valid_from": _canonical_datetime(start),
            "valid_until": _canonical_datetime(end),
            "data_handling_mode": handling_mode,
            "capability_lease_id": lease,
        }
        return cls(
            authorization_context_id=_digest(payload),
            schema_version=schema,
            tenant_ref=tenant,
            subject_refs=subjects,
            principal_context_id=principal_context.principal_context_id,
            purpose_code=purpose,
            lawful_basis_or_consent_ref=basis,
            authorization_receipt_ref=receipt,
            policy_snapshot_id=snapshot,
            retention_class=retention,
            erasure_domain_refs=erasure_refs,
            valid_from=start,
            valid_until=end,
            data_handling_mode=handling_mode,
            capability_lease_id=lease,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "tenant_ref": self.tenant_ref,
            "subject_refs": _subject_payload(self.subject_refs),
            "principal_context_id": self.principal_context_id,
            "purpose_code": self.purpose_code,
            "lawful_basis_or_consent_ref": self.lawful_basis_or_consent_ref,
            "authorization_receipt_ref": self.authorization_receipt_ref,
            "policy_snapshot_id": self.policy_snapshot_id,
            "retention_class": self.retention_class,
            "erasure_domain_refs": list(self.erasure_domain_refs),
            "valid_from": _canonical_datetime(self.valid_from),
            "valid_until": _canonical_datetime(self.valid_until),
            "data_handling_mode": self.data_handling_mode,
            "capability_lease_id": self.capability_lease_id,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "authorization_context_id": self.authorization_context_id,
            **self.identity_payload(),
            "authority": "authorization_evidence_only",
        }


@dataclass(frozen=True, slots=True)
class ContinuitySourceBindingReceipt:
    """Source-owner evidence binding one source result to tenant and subjects."""

    binding_receipt_id: str
    schema_version: str
    source_type: str
    source_result_id: str
    source_digest: str
    source_owner: str
    tenant_ref: str
    subject_refs: tuple[SubjectRef, ...]
    source_component_version: str
    source_policy_version: str
    source_as_of: datetime
    evidence_refs: tuple[str, ...]
    issued_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        for field_name in (
            "source_type",
            "source_result_id",
            "source_owner",
            "tenant_ref",
            "source_component_version",
            "source_policy_version",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self, "source_digest", _hash(self.source_digest, "source_digest")
        )
        object.__setattr__(self, "subject_refs", _subjects(self.subject_refs))
        object.__setattr__(
            self, "source_as_of", _aware(self.source_as_of, "source_as_of")
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _refs(self.evidence_refs, "evidence_refs", required=True),
        )
        object.__setattr__(
            self, "issued_at", _aware(self.issued_at, "issued_at")
        )
        if self.issued_at < self.source_as_of:
            raise ContinuitySourceAdmissionError(
                "issued_at cannot be earlier than source_as_of"
            )
        _verify_id(
            self.binding_receipt_id,
            _digest(self.identity_payload()),
            "binding_receipt_id",
        )

    @classmethod
    def create(
        cls,
        *,
        source_type: str,
        source_result_id: str,
        source_digest: str,
        source_owner: str,
        tenant_ref: str,
        subject_refs: Iterable[SubjectRef],
        source_component_version: str,
        source_policy_version: str,
        source_as_of: datetime,
        evidence_refs: Iterable[str],
        issued_at: datetime,
        schema_version: str = SOURCE_ADMISSION_SCHEMA_VERSION,
    ) -> ContinuitySourceBindingReceipt:
        schema = _text(schema_version, "schema_version")
        source_type_text = _text(source_type, "source_type")
        result_id = _text(source_result_id, "source_result_id")
        digest = _hash(source_digest, "source_digest")
        owner = _text(source_owner, "source_owner")
        tenant = _text(tenant_ref, "tenant_ref")
        subjects = _subjects(subject_refs)
        component_version = _text(
            source_component_version,
            "source_component_version",
        )
        policy_version = _text(
            source_policy_version,
            "source_policy_version",
        )
        as_of = _aware(source_as_of, "source_as_of")
        evidence = _refs(
            evidence_refs,
            "evidence_refs",
            required=True,
        )
        issued = _aware(issued_at, "issued_at")
        if issued < as_of:
            raise ContinuitySourceAdmissionError(
                "issued_at cannot be earlier than source_as_of"
            )
        payload: dict[str, object] = {
            "schema_version": schema,
            "source_type": source_type_text,
            "source_result_id": result_id,
            "source_digest": digest,
            "source_owner": owner,
            "tenant_ref": tenant,
            "subject_refs": _subject_payload(subjects),
            "source_component_version": component_version,
            "source_policy_version": policy_version,
            "source_as_of": _canonical_datetime(as_of),
            "evidence_refs": list(evidence),
            "issued_at": _canonical_datetime(issued),
        }
        return cls(
            binding_receipt_id=_digest(payload),
            schema_version=schema,
            source_type=source_type_text,
            source_result_id=result_id,
            source_digest=digest,
            source_owner=owner,
            tenant_ref=tenant,
            subject_refs=subjects,
            source_component_version=component_version,
            source_policy_version=policy_version,
            source_as_of=as_of,
            evidence_refs=evidence,
            issued_at=issued,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_type": self.source_type,
            "source_result_id": self.source_result_id,
            "source_digest": self.source_digest,
            "source_owner": self.source_owner,
            "tenant_ref": self.tenant_ref,
            "subject_refs": _subject_payload(self.subject_refs),
            "source_component_version": self.source_component_version,
            "source_policy_version": self.source_policy_version,
            "source_as_of": _canonical_datetime(self.source_as_of),
            "evidence_refs": list(self.evidence_refs),
            "issued_at": _canonical_datetime(self.issued_at),
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "binding_receipt_id": self.binding_receipt_id,
            **self.identity_payload(),
            "authority": "source_ownership_evidence_only",
        }
