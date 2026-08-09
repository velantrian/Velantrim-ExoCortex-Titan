"""Internal composition of authoritative Continuity current-decision snapshots.

The resolver in this module is deterministic and dependency-injected. It does not read
process-global configuration, a database, the network or the clock. It does not invoke a
source producer, persist artifacts, route a request, answer, remind, notify, execute a
tool/action, or mutate Canon/ESM/TruthGate/GoalStack.

Concrete owner adapters remain outside Continuity. This module only verifies one exact,
content-addressed snapshot from each accepted owner domain and composes the existing
``ContinuityCurrentDecisionEvidence`` contract used by the internal admission facade.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol, runtime_checkable

from .admission_evaluator import (
    ContinuityCurrentDecisionEvidence,
    ContinuityCurrentDecisionStatus,
)
from .contracts import SubjectRef
from .source_admission import (
    ContinuityAuthorizationContext,
    ContinuityPrincipalContext,
    ContinuitySourceAdmissionError,
    ContinuitySourceBindingReceipt,
    _aware,
    _canonical_datetime,
    _digest,
    _hash,
    _items,
    _refs,
    _subject_payload,
    _subjects,
    _text,
    _verify_id,
)
from .source_admission_payloads import ContinuitySourceEnvelope

CURRENT_DECISION_RESOLVER_SCHEMA_VERSION = (
    "continuity.current_decision_resolver.composition.v1"
)
CURRENT_DECISION_RESOLVER_VERSION = "1"
_OWNER_SNAPSHOT_AUTHORITY = "current_decision_owner_snapshot_only"


class ContinuityCurrentDecisionOwnerDomain(str, Enum):
    """Accepted owner domains required by the current-decision composition."""

    PRINCIPAL = "principal"
    AUTHORIZATION = "authorization"
    LAWFUL_BASIS = "lawful_basis"
    RESTRICTION = "restriction"
    ERASURE = "erasure"
    POLICY_SNAPSHOT = "policy_snapshot"


_ALLOWED_STATUSES: dict[
    ContinuityCurrentDecisionOwnerDomain,
    frozenset[ContinuityCurrentDecisionStatus],
] = {
    ContinuityCurrentDecisionOwnerDomain.PRINCIPAL: frozenset(
        {
            ContinuityCurrentDecisionStatus.ACTIVE,
            ContinuityCurrentDecisionStatus.INACTIVE,
            ContinuityCurrentDecisionStatus.UNKNOWN,
        }
    ),
    ContinuityCurrentDecisionOwnerDomain.AUTHORIZATION: frozenset(
        {
            ContinuityCurrentDecisionStatus.ACTIVE,
            ContinuityCurrentDecisionStatus.BLOCKED,
            ContinuityCurrentDecisionStatus.INACTIVE,
            ContinuityCurrentDecisionStatus.WITHDRAWN,
            ContinuityCurrentDecisionStatus.UNKNOWN,
        }
    ),
    ContinuityCurrentDecisionOwnerDomain.LAWFUL_BASIS: frozenset(
        {
            ContinuityCurrentDecisionStatus.ACTIVE,
            ContinuityCurrentDecisionStatus.BLOCKED,
            ContinuityCurrentDecisionStatus.INACTIVE,
            ContinuityCurrentDecisionStatus.WITHDRAWN,
            ContinuityCurrentDecisionStatus.UNKNOWN,
        }
    ),
    ContinuityCurrentDecisionOwnerDomain.RESTRICTION: frozenset(
        {
            ContinuityCurrentDecisionStatus.CLEAR,
            ContinuityCurrentDecisionStatus.BLOCKED,
            ContinuityCurrentDecisionStatus.UNKNOWN,
        }
    ),
    ContinuityCurrentDecisionOwnerDomain.ERASURE: frozenset(
        {
            ContinuityCurrentDecisionStatus.CLEAR,
            ContinuityCurrentDecisionStatus.BLOCKED,
            ContinuityCurrentDecisionStatus.UNKNOWN,
        }
    ),
    ContinuityCurrentDecisionOwnerDomain.POLICY_SNAPSHOT: frozenset(
        {
            ContinuityCurrentDecisionStatus.ACTIVE,
            ContinuityCurrentDecisionStatus.INACTIVE,
            ContinuityCurrentDecisionStatus.UNKNOWN,
        }
    ),
}


def _subject_keys(subjects: tuple[SubjectRef, ...]) -> tuple[tuple[str, str], ...]:
    return tuple((value.subject_id, value.kind.value) for value in subjects)


@dataclass(frozen=True, slots=True)
class ContinuityCurrentDecisionOwnerSnapshot:
    """One immutable owner-domain decision bound to an exact admission scope."""

    owner_snapshot_id: str
    schema_version: str
    domain: ContinuityCurrentDecisionOwnerDomain
    owner_id: str
    owner_version: str
    principal_context_id: str
    authorization_context_id: str
    source_envelope_id: str
    source_binding_receipt_id: str
    tenant_ref: str
    subject_refs: tuple[SubjectRef, ...]
    scope_refs: tuple[str, ...]
    status: ContinuityCurrentDecisionStatus
    observed_at: datetime
    valid_until: datetime
    evidence_refs: tuple[str, ...]
    authority: str = _OWNER_SNAPSHOT_AUTHORITY
    no_runtime_authority: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _text(self.schema_version, "schema_version"),
        )
        if not isinstance(self.domain, ContinuityCurrentDecisionOwnerDomain):
            raise ContinuitySourceAdmissionError(
                "domain must be a ContinuityCurrentDecisionOwnerDomain"
            )
        object.__setattr__(self, "owner_id", _text(self.owner_id, "owner_id"))
        object.__setattr__(
            self,
            "owner_version",
            _text(self.owner_version, "owner_version"),
        )
        for field_name in (
            "principal_context_id",
            "authorization_context_id",
            "source_envelope_id",
            "source_binding_receipt_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _hash(getattr(self, field_name), field_name),
            )
        object.__setattr__(self, "tenant_ref", _text(self.tenant_ref, "tenant_ref"))
        object.__setattr__(self, "subject_refs", _subjects(self.subject_refs))
        object.__setattr__(
            self,
            "scope_refs",
            _refs(self.scope_refs, "scope_refs", required=True),
        )
        if not isinstance(self.status, ContinuityCurrentDecisionStatus):
            raise ContinuitySourceAdmissionError(
                "status must be a ContinuityCurrentDecisionStatus"
            )
        if self.status not in _ALLOWED_STATUSES[self.domain]:
            raise ContinuitySourceAdmissionError(
                f"status {self.status.value!r} is not valid for {self.domain.value!r}"
            )
        object.__setattr__(
            self,
            "observed_at",
            _aware(self.observed_at, "observed_at"),
        )
        object.__setattr__(
            self,
            "valid_until",
            _aware(self.valid_until, "valid_until"),
        )
        if self.valid_until <= self.observed_at:
            raise ContinuitySourceAdmissionError(
                "valid_until must be later than observed_at"
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _refs(self.evidence_refs, "evidence_refs", required=True),
        )
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        if self.authority != _OWNER_SNAPSHOT_AUTHORITY:
            raise ContinuitySourceAdmissionError(
                f"authority must be {_OWNER_SNAPSHOT_AUTHORITY!r}"
            )
        if self.no_runtime_authority is not True:
            raise ContinuitySourceAdmissionError(
                "no_runtime_authority must remain True"
            )
        _verify_id(
            self.owner_snapshot_id,
            _digest(self.identity_payload()),
            "owner_snapshot_id",
        )

    @classmethod
    def create(
        cls,
        *,
        domain: ContinuityCurrentDecisionOwnerDomain,
        owner_id: str,
        owner_version: str,
        principal_context: ContinuityPrincipalContext,
        authorization_context: ContinuityAuthorizationContext,
        source_envelope: ContinuitySourceEnvelope,
        binding_receipt: ContinuitySourceBindingReceipt,
        scope_refs: Iterable[str],
        status: ContinuityCurrentDecisionStatus,
        observed_at: datetime,
        valid_until: datetime,
        evidence_refs: Iterable[str],
        schema_version: str = CURRENT_DECISION_RESOLVER_SCHEMA_VERSION,
    ) -> ContinuityCurrentDecisionOwnerSnapshot:
        if not isinstance(principal_context, ContinuityPrincipalContext):
            raise ContinuitySourceAdmissionError(
                "principal_context must be a ContinuityPrincipalContext"
            )
        if not isinstance(authorization_context, ContinuityAuthorizationContext):
            raise ContinuitySourceAdmissionError(
                "authorization_context must be a ContinuityAuthorizationContext"
            )
        if not isinstance(source_envelope, ContinuitySourceEnvelope):
            raise ContinuitySourceAdmissionError(
                "source_envelope must be a ContinuitySourceEnvelope"
            )
        if not isinstance(binding_receipt, ContinuitySourceBindingReceipt):
            raise ContinuitySourceAdmissionError(
                "binding_receipt must be a ContinuitySourceBindingReceipt"
            )
        if not isinstance(domain, ContinuityCurrentDecisionOwnerDomain):
            raise ContinuitySourceAdmissionError(
                "domain must be a ContinuityCurrentDecisionOwnerDomain"
            )
        if not isinstance(status, ContinuityCurrentDecisionStatus):
            raise ContinuitySourceAdmissionError(
                "status must be a ContinuityCurrentDecisionStatus"
            )
        if status not in _ALLOWED_STATUSES[domain]:
            raise ContinuitySourceAdmissionError(
                f"status {status.value!r} is not valid for {domain.value!r}"
            )
        version = _text(schema_version, "schema_version")
        owner_name = _text(owner_id, "owner_id")
        owner_revision = _text(owner_version, "owner_version")
        scopes = _refs(scope_refs, "scope_refs", required=True)
        observed = _aware(observed_at, "observed_at")
        expires = _aware(valid_until, "valid_until")
        refs = _refs(evidence_refs, "evidence_refs", required=True)
        payload: dict[str, object] = {
            "schema_version": version,
            "domain": domain.value,
            "owner_id": owner_name,
            "owner_version": owner_revision,
            "principal_context_id": principal_context.principal_context_id,
            "authorization_context_id": authorization_context.authorization_context_id,
            "source_envelope_id": source_envelope.envelope_id,
            "source_binding_receipt_id": binding_receipt.binding_receipt_id,
            "tenant_ref": authorization_context.tenant_ref,
            "subject_refs": _subject_payload(authorization_context.subject_refs),
            "scope_refs": list(scopes),
            "status": status.value,
            "observed_at": _canonical_datetime(observed),
            "valid_until": _canonical_datetime(expires),
            "evidence_refs": list(refs),
            "authority": _OWNER_SNAPSHOT_AUTHORITY,
            "no_runtime_authority": True,
        }
        return cls(
            owner_snapshot_id=_digest(payload),
            schema_version=version,
            domain=domain,
            owner_id=owner_name,
            owner_version=owner_revision,
            principal_context_id=principal_context.principal_context_id,
            authorization_context_id=authorization_context.authorization_context_id,
            source_envelope_id=source_envelope.envelope_id,
            source_binding_receipt_id=binding_receipt.binding_receipt_id,
            tenant_ref=authorization_context.tenant_ref,
            subject_refs=authorization_context.subject_refs,
            scope_refs=scopes,
            status=status,
            observed_at=observed,
            valid_until=expires,
            evidence_refs=refs,
            authority=_OWNER_SNAPSHOT_AUTHORITY,
            no_runtime_authority=True,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "domain": self.domain.value,
            "owner_id": self.owner_id,
            "owner_version": self.owner_version,
            "principal_context_id": self.principal_context_id,
            "authorization_context_id": self.authorization_context_id,
            "source_envelope_id": self.source_envelope_id,
            "source_binding_receipt_id": self.source_binding_receipt_id,
            "tenant_ref": self.tenant_ref,
            "subject_refs": _subject_payload(self.subject_refs),
            "scope_refs": list(self.scope_refs),
            "status": self.status.value,
            "observed_at": _canonical_datetime(self.observed_at),
            "valid_until": _canonical_datetime(self.valid_until),
            "evidence_refs": list(self.evidence_refs),
            "authority": self.authority,
            "no_runtime_authority": self.no_runtime_authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {"owner_snapshot_id": self.owner_snapshot_id, **self.identity_payload()}


@runtime_checkable
class ContinuityCurrentDecisionOwnerPort(Protocol):
    """Read-only owner port returning snapshots for one exact domain."""

    @property
    def domain(self) -> ContinuityCurrentDecisionOwnerDomain: ...

    @property
    def owner_id(self) -> str: ...

    @property
    def owner_version(self) -> str: ...

    def resolve_current_decision_snapshots(
        self,
        *,
        principal_context: ContinuityPrincipalContext,
        authorization_context: ContinuityAuthorizationContext,
        source_envelope: ContinuitySourceEnvelope,
        binding_receipt: ContinuitySourceBindingReceipt,
        evaluated_at: datetime,
    ) -> Iterable[ContinuityCurrentDecisionOwnerSnapshot]: ...


@dataclass(frozen=True, slots=True)
class ContinuityCurrentDecisionResolverComposition:
    """Strict six-owner composition implementing the facade resolver protocol."""

    principal_owner: ContinuityCurrentDecisionOwnerPort
    authorization_owner: ContinuityCurrentDecisionOwnerPort
    lawful_basis_owner: ContinuityCurrentDecisionOwnerPort
    restriction_owner: ContinuityCurrentDecisionOwnerPort
    erasure_owner: ContinuityCurrentDecisionOwnerPort
    policy_snapshot_owner: ContinuityCurrentDecisionOwnerPort
    _owner_identities: tuple[
        tuple[ContinuityCurrentDecisionOwnerDomain, str, str], ...
    ] = field(init=False, repr=False)
    _resolver_id: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        identities: list[
            tuple[ContinuityCurrentDecisionOwnerDomain, str, str]
        ] = []
        for domain, owner in self._owners():
            owner_id, owner_version = self._read_owner_identity(owner, domain)
            identities.append((domain, owner_id, owner_version))
        object.__setattr__(self, "_owner_identities", tuple(identities))
        object.__setattr__(self, "_resolver_id", _digest(self.identity_payload()))

    @property
    def resolver_id(self) -> str:
        return self._resolver_id

    @property
    def resolver_version(self) -> str:
        return CURRENT_DECISION_RESOLVER_VERSION

    def _owners(
        self,
    ) -> tuple[
        tuple[ContinuityCurrentDecisionOwnerDomain, ContinuityCurrentDecisionOwnerPort],
        ...,
    ]:
        return (
            (ContinuityCurrentDecisionOwnerDomain.PRINCIPAL, self.principal_owner),
            (
                ContinuityCurrentDecisionOwnerDomain.AUTHORIZATION,
                self.authorization_owner,
            ),
            (
                ContinuityCurrentDecisionOwnerDomain.LAWFUL_BASIS,
                self.lawful_basis_owner,
            ),
            (
                ContinuityCurrentDecisionOwnerDomain.RESTRICTION,
                self.restriction_owner,
            ),
            (ContinuityCurrentDecisionOwnerDomain.ERASURE, self.erasure_owner),
            (
                ContinuityCurrentDecisionOwnerDomain.POLICY_SNAPSHOT,
                self.policy_snapshot_owner,
            ),
        )

    @staticmethod
    def _read_owner_identity(
        owner: ContinuityCurrentDecisionOwnerPort,
        expected_domain: ContinuityCurrentDecisionOwnerDomain,
    ) -> tuple[str, str]:
        try:
            domain = owner.domain
            owner_id = _text(owner.owner_id, "owner_id")
            owner_version = _text(owner.owner_version, "owner_version")
            resolver = owner.resolve_current_decision_snapshots
        except (AttributeError, TypeError, ContinuitySourceAdmissionError) as exc:
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} owner port is invalid"
            ) from exc
        if domain is not expected_domain:
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} owner port has the wrong domain"
            )
        if not callable(resolver):
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} owner resolver must be callable"
            )
        return owner_id, owner_version

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": CURRENT_DECISION_RESOLVER_SCHEMA_VERSION,
            "resolver_version": CURRENT_DECISION_RESOLVER_VERSION,
            "owners": [
                {
                    "domain": domain.value,
                    "owner_id": owner_id,
                    "owner_version": owner_version,
                }
                for domain, owner_id, owner_version in self._owner_identities
            ],
            "authority": "current_decision_resolver_composition_only",
            "no_runtime_authority": True,
        }

    def resolve_current_decision(
        self,
        *,
        principal_context: ContinuityPrincipalContext,
        authorization_context: ContinuityAuthorizationContext,
        source_envelope: ContinuitySourceEnvelope,
        binding_receipt: ContinuitySourceBindingReceipt,
        evaluated_at: datetime,
    ) -> ContinuityCurrentDecisionEvidence:
        evaluated = self._validate_input_scope(
            principal_context=principal_context,
            authorization_context=authorization_context,
            source_envelope=source_envelope,
            binding_receipt=binding_receipt,
            evaluated_at=evaluated_at,
        )
        snapshots = {
            domain: self._resolve_one_snapshot(
                owner=owner,
                expected_domain=domain,
                principal_context=principal_context,
                authorization_context=authorization_context,
                source_envelope=source_envelope,
                binding_receipt=binding_receipt,
                evaluated_at=evaluated,
            )
            for domain, owner in self._owners()
        }
        if (
            snapshots[ContinuityCurrentDecisionOwnerDomain.PRINCIPAL].status
            is not ContinuityCurrentDecisionStatus.ACTIVE
        ):
            raise ContinuitySourceAdmissionError(
                "principal owner state must be ACTIVE"
            )
        if (
            snapshots[ContinuityCurrentDecisionOwnerDomain.POLICY_SNAPSHOT].status
            is not ContinuityCurrentDecisionStatus.ACTIVE
        ):
            raise ContinuitySourceAdmissionError(
                "policy snapshot owner state must be ACTIVE"
            )

        observed_at = max(value.observed_at for value in snapshots.values())
        valid_until = min(
            authorization_context.valid_until,
            *(value.valid_until for value in snapshots.values()),
        )
        if not observed_at <= evaluated < valid_until:
            raise ContinuitySourceAdmissionError(
                "composed current-decision evidence is not current at evaluated_at"
            )
        evidence_refs = {
            principal_context.principal_context_id,
            authorization_context.authorization_context_id,
            source_envelope.envelope_id,
            binding_receipt.binding_receipt_id,
        }
        for snapshot in snapshots.values():
            evidence_refs.add(snapshot.owner_snapshot_id)
            evidence_refs.update(snapshot.evidence_refs)

        return ContinuityCurrentDecisionEvidence.create(
            principal_context=principal_context,
            authorization_context=authorization_context,
            authorization_status=snapshots[
                ContinuityCurrentDecisionOwnerDomain.AUTHORIZATION
            ].status,
            lawful_basis_status=snapshots[
                ContinuityCurrentDecisionOwnerDomain.LAWFUL_BASIS
            ].status,
            restriction_status=snapshots[
                ContinuityCurrentDecisionOwnerDomain.RESTRICTION
            ].status,
            erasure_status=snapshots[
                ContinuityCurrentDecisionOwnerDomain.ERASURE
            ].status,
            observed_at=observed_at,
            valid_until=valid_until,
            evidence_refs=evidence_refs,
        )

    @staticmethod
    def _validate_input_scope(
        *,
        principal_context: ContinuityPrincipalContext,
        authorization_context: ContinuityAuthorizationContext,
        source_envelope: ContinuitySourceEnvelope,
        binding_receipt: ContinuitySourceBindingReceipt,
        evaluated_at: datetime,
    ) -> datetime:
        if not isinstance(principal_context, ContinuityPrincipalContext):
            raise ContinuitySourceAdmissionError(
                "principal_context must be a ContinuityPrincipalContext"
            )
        if not isinstance(authorization_context, ContinuityAuthorizationContext):
            raise ContinuitySourceAdmissionError(
                "authorization_context must be a ContinuityAuthorizationContext"
            )
        if not isinstance(source_envelope, ContinuitySourceEnvelope):
            raise ContinuitySourceAdmissionError(
                "source_envelope must be a ContinuitySourceEnvelope"
            )
        if not isinstance(binding_receipt, ContinuitySourceBindingReceipt):
            raise ContinuitySourceAdmissionError(
                "binding_receipt must be a ContinuitySourceBindingReceipt"
            )
        evaluated = _aware(evaluated_at, "evaluated_at")
        if (
            authorization_context.principal_context_id
            != principal_context.principal_context_id
        ):
            raise ContinuitySourceAdmissionError(
                "authorization context must reference the exact principal context"
            )
        if (
            source_envelope.authorization_context_id
            != authorization_context.authorization_context_id
        ):
            raise ContinuitySourceAdmissionError(
                "source envelope must reference the exact authorization context"
            )
        if (
            source_envelope.source_binding_receipt_id
            != binding_receipt.binding_receipt_id
        ):
            raise ContinuitySourceAdmissionError(
                "source envelope must reference the exact binding receipt"
            )
        if not (
            authorization_context.tenant_ref
            == source_envelope.tenant_ref
            == binding_receipt.tenant_ref
        ):
            raise ContinuitySourceAdmissionError(
                "authorization, source envelope and binding tenant must match"
            )
        if _subject_keys(source_envelope.subject_refs) != _subject_keys(
            binding_receipt.subject_refs
        ):
            raise ContinuitySourceAdmissionError(
                "source envelope and binding receipt subjects must match exactly"
            )
        if not set(_subject_keys(binding_receipt.subject_refs)).issubset(
            _subject_keys(authorization_context.subject_refs)
        ):
            raise ContinuitySourceAdmissionError(
                "binding receipt subjects must be authorized"
            )
        if not (
            authorization_context.valid_from
            <= evaluated
            < authorization_context.valid_until
        ):
            raise ContinuitySourceAdmissionError(
                "evaluated_at must fall within the authorization validity interval"
            )
        if (
            evaluated < source_envelope.created_at
            or evaluated < binding_receipt.issued_at
        ):
            raise ContinuitySourceAdmissionError(
                "evaluated_at cannot precede source evidence"
            )
        return evaluated

    @staticmethod
    def _expected_scope_refs(
        domain: ContinuityCurrentDecisionOwnerDomain,
        *,
        principal_context: ContinuityPrincipalContext,
        authorization_context: ContinuityAuthorizationContext,
    ) -> tuple[str, ...]:
        if domain is ContinuityCurrentDecisionOwnerDomain.PRINCIPAL:
            return _refs(
                (
                    principal_context.principal_context_id,
                    principal_context.principal_ref,
                    principal_context.authentication_receipt_ref,
                ),
                "scope_refs",
                required=True,
            )
        if domain is ContinuityCurrentDecisionOwnerDomain.AUTHORIZATION:
            return _refs(
                (
                    authorization_context.authorization_context_id,
                    authorization_context.authorization_receipt_ref,
                ),
                "scope_refs",
                required=True,
            )
        if domain is ContinuityCurrentDecisionOwnerDomain.LAWFUL_BASIS:
            return (authorization_context.lawful_basis_or_consent_ref,)
        if domain is ContinuityCurrentDecisionOwnerDomain.RESTRICTION:
            return (authorization_context.policy_snapshot_id,)
        if domain is ContinuityCurrentDecisionOwnerDomain.ERASURE:
            return authorization_context.erasure_domain_refs
        if domain is ContinuityCurrentDecisionOwnerDomain.POLICY_SNAPSHOT:
            return (authorization_context.policy_snapshot_id,)
        raise ContinuitySourceAdmissionError("unsupported owner domain")  # pragma: no cover

    def _resolve_one_snapshot(
        self,
        *,
        owner: ContinuityCurrentDecisionOwnerPort,
        expected_domain: ContinuityCurrentDecisionOwnerDomain,
        principal_context: ContinuityPrincipalContext,
        authorization_context: ContinuityAuthorizationContext,
        source_envelope: ContinuitySourceEnvelope,
        binding_receipt: ContinuitySourceBindingReceipt,
        evaluated_at: datetime,
    ) -> ContinuityCurrentDecisionOwnerSnapshot:
        owner_id, owner_version = next(
            (
                (value_owner_id, value_owner_version)
                for domain, value_owner_id, value_owner_version in self._owner_identities
                if domain is expected_domain
            ),
            ("", ""),
        )
        if self._read_owner_identity(owner, expected_domain) != (
            owner_id,
            owner_version,
        ):
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} owner identity changed after composition"
            )
        try:
            raw_snapshots = owner.resolve_current_decision_snapshots(
                principal_context=principal_context,
                authorization_context=authorization_context,
                source_envelope=source_envelope,
                binding_receipt=binding_receipt,
                evaluated_at=evaluated_at,
            )
            snapshots = _items(raw_snapshots, f"{expected_domain.value}_snapshots")
        except Exception as exc:
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} owner resolution failed closed"
            ) from exc
        if self._read_owner_identity(owner, expected_domain) != (
            owner_id,
            owner_version,
        ):
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} owner identity changed during resolution"
            )
        if len(snapshots) != 1:
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} owner must return exactly one snapshot"
            )
        snapshot = snapshots[0]
        if not isinstance(snapshot, ContinuityCurrentDecisionOwnerSnapshot):
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} owner returned an invalid snapshot"
            )
        _verify_id(
            snapshot.owner_snapshot_id,
            _digest(snapshot.identity_payload()),
            "owner_snapshot_id",
        )
        if snapshot.domain is not expected_domain:
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} owner returned an extra domain snapshot"
            )
        if (snapshot.owner_id, snapshot.owner_version) != (owner_id, owner_version):
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} snapshot owner identity mismatch"
            )
        if snapshot.principal_context_id != principal_context.principal_context_id:
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} snapshot principal substitution"
            )
        if (
            snapshot.authorization_context_id
            != authorization_context.authorization_context_id
        ):
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} snapshot authorization substitution"
            )
        if snapshot.source_envelope_id != source_envelope.envelope_id:
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} snapshot source-envelope substitution"
            )
        if (
            snapshot.source_binding_receipt_id
            != binding_receipt.binding_receipt_id
        ):
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} snapshot binding-receipt substitution"
            )
        if snapshot.tenant_ref != authorization_context.tenant_ref:
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} snapshot tenant substitution"
            )
        if _subject_keys(snapshot.subject_refs) != _subject_keys(
            authorization_context.subject_refs
        ):
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} snapshot subject substitution"
            )
        expected_scope_refs = self._expected_scope_refs(
            expected_domain,
            principal_context=principal_context,
            authorization_context=authorization_context,
        )
        if snapshot.scope_refs != expected_scope_refs:
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} snapshot scope mismatch"
            )
        if snapshot.status not in _ALLOWED_STATUSES[expected_domain]:
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} snapshot status is invalid"
            )
        if not snapshot.observed_at <= evaluated_at < snapshot.valid_until:
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} snapshot is not current"
            )
        if snapshot.no_runtime_authority is not True:
            raise ContinuitySourceAdmissionError(
                f"{expected_domain.value} snapshot grants runtime authority"
            )
        return snapshot
