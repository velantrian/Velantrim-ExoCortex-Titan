"""Adversarial tests for the internal Continuity current-decision composition."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest

import core.continuity as continuity_package
from core.continuity.admission_evaluator import ContinuityCurrentDecisionStatus
from core.continuity.admission_facade import ContinuityCurrentDecisionResolver
from core.continuity.contracts import SubjectKind, SubjectRef
from core.continuity.current_decision_resolver import (
    ContinuityCurrentDecisionOwnerDomain,
    ContinuityCurrentDecisionOwnerSnapshot,
    ContinuityCurrentDecisionResolverComposition,
)
from core.continuity.source_admission import (
    ContinuityAuthorizationContext,
    ContinuityPrincipalContext,
    ContinuitySourceAdmissionError,
    ContinuitySourceBindingReceipt,
    _digest,
)
from core.continuity.source_admission_payloads import ContinuitySourceEnvelope

_NOW = datetime(2026, 8, 9, 18, 0, tzinfo=UTC)
_SUBJECT = SubjectRef(subject_id="subject:alice", kind=SubjectKind.PERSON)
_OTHER_SUBJECT = SubjectRef(subject_id="subject:bob", kind=SubjectKind.PERSON)


def _principal() -> ContinuityPrincipalContext:
    return ContinuityPrincipalContext.create(
        principal_ref="principal:alice",
        principal_kind="human",
        authentication_method="oidc",
        authentication_strength="mfa",
        authenticated_at=_NOW - timedelta(minutes=30),
        issuer_ref="issuer:test",
        authentication_receipt_ref="authentication:alice",
    )


def _authorization(
    principal: ContinuityPrincipalContext,
    *,
    subjects: tuple[SubjectRef, ...] = (_SUBJECT,),
) -> ContinuityAuthorizationContext:
    return ContinuityAuthorizationContext.create(
        tenant_ref="tenant:one",
        subject_refs=subjects,
        principal_context=principal,
        purpose_code="continuity_analysis",
        lawful_basis_or_consent_ref="consent:active",
        authorization_receipt_ref="authorization:active",
        policy_snapshot_id="policy:current",
        retention_class="ephemeral",
        erasure_domain_refs=tuple(
            f"erasure:{subject.subject_id}" for subject in subjects
        ),
        valid_from=_NOW - timedelta(hours=1),
        valid_until=_NOW + timedelta(hours=1),
        data_handling_mode="local_only",
    )


def _binding(
    *,
    subjects: tuple[SubjectRef, ...] = (_SUBJECT,),
) -> ContinuitySourceBindingReceipt:
    return ContinuitySourceBindingReceipt.create(
        source_type="state_reconciliation_result",
        source_result_id="state-result:a",
        source_digest=sha256(b"state-result:a").hexdigest(),
        source_owner="continuity.state_reconciler",
        tenant_ref="tenant:one",
        subject_refs=subjects,
        source_component_version="1",
        source_policy_version="1",
        source_as_of=_NOW - timedelta(minutes=5),
        evidence_refs=("event:a",),
        issued_at=_NOW - timedelta(minutes=4),
    )


def _envelope(
    authorization: ContinuityAuthorizationContext,
    binding: ContinuitySourceBindingReceipt,
) -> ContinuitySourceEnvelope:
    return ContinuitySourceEnvelope.create(
        binding_receipt=binding,
        authorization_context=authorization,
        source_schema_version="continuity.state_projection.v1",
        producer_adapter_id="continuity.state_reconciliation_to_drafts",
        producer_adapter_version="1",
        created_at=_NOW - timedelta(minutes=3),
    )


def _scope_refs(
    domain: ContinuityCurrentDecisionOwnerDomain,
    principal: ContinuityPrincipalContext,
    authorization: ContinuityAuthorizationContext,
) -> tuple[str, ...]:
    if domain is ContinuityCurrentDecisionOwnerDomain.PRINCIPAL:
        return (
            principal.principal_context_id,
            principal.principal_ref,
            principal.authentication_receipt_ref,
        )
    if domain is ContinuityCurrentDecisionOwnerDomain.AUTHORIZATION:
        return (
            authorization.authorization_context_id,
            authorization.authorization_receipt_ref,
        )
    if domain is ContinuityCurrentDecisionOwnerDomain.LAWFUL_BASIS:
        return (authorization.lawful_basis_or_consent_ref,)
    if domain is ContinuityCurrentDecisionOwnerDomain.RESTRICTION:
        return (authorization.policy_snapshot_id,)
    if domain is ContinuityCurrentDecisionOwnerDomain.ERASURE:
        return authorization.erasure_domain_refs
    return (authorization.policy_snapshot_id,)


_DEFAULT_STATUS = {
    ContinuityCurrentDecisionOwnerDomain.PRINCIPAL: ContinuityCurrentDecisionStatus.ACTIVE,
    ContinuityCurrentDecisionOwnerDomain.AUTHORIZATION: ContinuityCurrentDecisionStatus.ACTIVE,
    ContinuityCurrentDecisionOwnerDomain.LAWFUL_BASIS: ContinuityCurrentDecisionStatus.ACTIVE,
    ContinuityCurrentDecisionOwnerDomain.RESTRICTION: ContinuityCurrentDecisionStatus.CLEAR,
    ContinuityCurrentDecisionOwnerDomain.ERASURE: ContinuityCurrentDecisionStatus.CLEAR,
    ContinuityCurrentDecisionOwnerDomain.POLICY_SNAPSHOT: ContinuityCurrentDecisionStatus.ACTIVE,
}


@dataclass(slots=True)
class _Owner:
    domain: ContinuityCurrentDecisionOwnerDomain
    status: ContinuityCurrentDecisionStatus | None = None
    count: int = 1
    observed_at: datetime = _NOW - timedelta(minutes=1)
    valid_until: datetime = _NOW + timedelta(minutes=10)
    evidence_refs: tuple[str, ...] = ("owner:evidence:z", "owner:evidence:a")
    returned_domain: ContinuityCurrentDecisionOwnerDomain | None = None
    substitute_subjects: tuple[SubjectRef, ...] | None = None
    corrupt_digest: bool = False
    fail: bool = False
    mutate_identity: bool = False
    identity_suffix: str = "stable"
    calls: int = 0

    @property
    def owner_id(self) -> str:
        return f"owner:{self.domain.value}:{self.identity_suffix}"

    @property
    def owner_version(self) -> str:
        return "1"

    def resolve_current_decision_snapshots(
        self,
        *,
        principal_context: ContinuityPrincipalContext,
        authorization_context: ContinuityAuthorizationContext,
        source_envelope: ContinuitySourceEnvelope,
        binding_receipt: ContinuitySourceBindingReceipt,
        evaluated_at: datetime,
    ) -> tuple[ContinuityCurrentDecisionOwnerSnapshot, ...]:
        del evaluated_at
        self.calls += 1
        if self.fail:
            raise RuntimeError("owner unavailable")
        if self.count == 0:
            return ()
        if self.mutate_identity:
            self.identity_suffix = "changed"
        snapshot = ContinuityCurrentDecisionOwnerSnapshot.create(
            domain=self.returned_domain or self.domain,
            owner_id=self.owner_id,
            owner_version=self.owner_version,
            principal_context=principal_context,
            authorization_context=authorization_context,
            source_envelope=source_envelope,
            binding_receipt=binding_receipt,
            scope_refs=_scope_refs(
                self.domain,
                principal_context,
                authorization_context,
            ),
            status=self.status or _DEFAULT_STATUS[self.domain],
            observed_at=self.observed_at,
            valid_until=self.valid_until,
            evidence_refs=self.evidence_refs,
        )
        if self.substitute_subjects is not None:
            object.__setattr__(snapshot, "subject_refs", self.substitute_subjects)
            object.__setattr__(
                snapshot,
                "owner_snapshot_id",
                _digest(snapshot.identity_payload()),
            )
        if self.corrupt_digest:
            object.__setattr__(snapshot, "owner_snapshot_id", "0" * 64)
        return tuple(snapshot for _ in range(self.count))


def _resolver(
    *,
    overrides: dict[ContinuityCurrentDecisionOwnerDomain, _Owner] | None = None,
) -> ContinuityCurrentDecisionResolverComposition:
    owners = {
        domain: _Owner(domain=domain)
        for domain in ContinuityCurrentDecisionOwnerDomain
    }
    owners.update(overrides or {})
    return ContinuityCurrentDecisionResolverComposition(
        principal_owner=owners[ContinuityCurrentDecisionOwnerDomain.PRINCIPAL],
        authorization_owner=owners[
            ContinuityCurrentDecisionOwnerDomain.AUTHORIZATION
        ],
        lawful_basis_owner=owners[
            ContinuityCurrentDecisionOwnerDomain.LAWFUL_BASIS
        ],
        restriction_owner=owners[
            ContinuityCurrentDecisionOwnerDomain.RESTRICTION
        ],
        erasure_owner=owners[ContinuityCurrentDecisionOwnerDomain.ERASURE],
        policy_snapshot_owner=owners[
            ContinuityCurrentDecisionOwnerDomain.POLICY_SNAPSHOT
        ],
    )


def _scenario(
    *,
    subjects: tuple[SubjectRef, ...] = (_SUBJECT,),
) -> tuple[
    ContinuityPrincipalContext,
    ContinuityAuthorizationContext,
    ContinuitySourceBindingReceipt,
    ContinuitySourceEnvelope,
]:
    principal = _principal()
    authorization = _authorization(principal, subjects=subjects)
    binding = _binding(subjects=subjects)
    return principal, authorization, binding, _envelope(authorization, binding)


def _resolve(
    resolver: ContinuityCurrentDecisionResolverComposition,
    *,
    subjects: tuple[SubjectRef, ...] = (_SUBJECT,),
):
    principal, authorization, binding, envelope = _scenario(subjects=subjects)
    evidence = resolver.resolve_current_decision(
        principal_context=principal,
        authorization_context=authorization,
        source_envelope=envelope,
        binding_receipt=binding,
        evaluated_at=_NOW,
    )
    return evidence, principal, authorization, binding, envelope


def test_composition_is_deterministic_and_matches_facade_protocol() -> None:
    first_resolver = _resolver()
    second_resolver = _resolver(
        overrides={
            domain: _Owner(
                domain=domain,
                evidence_refs=("owner:evidence:a", "owner:evidence:z"),
            )
            for domain in ContinuityCurrentDecisionOwnerDomain
        }
    )

    first, *_ = _resolve(first_resolver, subjects=(_SUBJECT, _OTHER_SUBJECT))
    second, *_ = _resolve(second_resolver, subjects=(_SUBJECT, _OTHER_SUBJECT))

    assert isinstance(first_resolver, ContinuityCurrentDecisionResolver)
    assert first_resolver.resolver_id == second_resolver.resolver_id
    assert first == second
    assert first.authority == "current_decision_evidence_only"


def test_composition_binds_exact_context_source_and_subject_scope() -> None:
    evidence, principal, authorization, binding, envelope = _resolve(_resolver())

    assert evidence.principal_context_id == principal.principal_context_id
    assert evidence.authorization_context_id == authorization.authorization_context_id
    assert evidence.subject_refs == authorization.subject_refs
    assert principal.principal_context_id in evidence.evidence_refs
    assert authorization.authorization_context_id in evidence.evidence_refs
    assert binding.binding_receipt_id in evidence.evidence_refs
    assert envelope.envelope_id in evidence.evidence_refs


@pytest.mark.parametrize("count", [0, 2])
def test_missing_or_duplicate_owner_snapshot_fails_closed(count: int) -> None:
    domain = ContinuityCurrentDecisionOwnerDomain.AUTHORIZATION
    resolver = _resolver(overrides={domain: _Owner(domain=domain, count=count)})

    with pytest.raises(ContinuitySourceAdmissionError, match="exactly one snapshot"):
        _resolve(resolver)


def test_extra_domain_snapshot_fails_closed() -> None:
    domain = ContinuityCurrentDecisionOwnerDomain.PRINCIPAL
    resolver = _resolver(
        overrides={
            domain: _Owner(
                domain=domain,
                returned_domain=ContinuityCurrentDecisionOwnerDomain.POLICY_SNAPSHOT,
            )
        }
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="extra domain"):
        _resolve(resolver)


def test_subject_substitution_fails_closed() -> None:
    domain = ContinuityCurrentDecisionOwnerDomain.ERASURE
    resolver = _resolver(
        overrides={
            domain: _Owner(domain=domain, substitute_subjects=(_OTHER_SUBJECT,))
        }
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="subject substitution"):
        _resolve(resolver)


@pytest.mark.parametrize(
    ("owner", "message"),
    [
        (
            _Owner(
                domain=ContinuityCurrentDecisionOwnerDomain.AUTHORIZATION,
                observed_at=_NOW - timedelta(minutes=10),
                valid_until=_NOW,
            ),
            "not current",
        ),
        (
            _Owner(
                domain=ContinuityCurrentDecisionOwnerDomain.AUTHORIZATION,
                observed_at=_NOW + timedelta(minutes=1),
                valid_until=_NOW + timedelta(minutes=10),
            ),
            "not current",
        ),
    ],
)
def test_stale_or_future_effective_snapshot_fails_closed(
    owner: _Owner,
    message: str,
) -> None:
    resolver = _resolver(overrides={owner.domain: owner})

    with pytest.raises(ContinuitySourceAdmissionError, match=message):
        _resolve(resolver)


def test_tampered_snapshot_digest_fails_closed() -> None:
    domain = ContinuityCurrentDecisionOwnerDomain.LAWFUL_BASIS
    resolver = _resolver(
        overrides={domain: _Owner(domain=domain, corrupt_digest=True)}
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        _resolve(resolver)


@pytest.mark.parametrize(
    ("domain", "status", "field_name"),
    [
        (
            ContinuityCurrentDecisionOwnerDomain.AUTHORIZATION,
            ContinuityCurrentDecisionStatus.WITHDRAWN,
            "authorization_status",
        ),
        (
            ContinuityCurrentDecisionOwnerDomain.LAWFUL_BASIS,
            ContinuityCurrentDecisionStatus.UNKNOWN,
            "lawful_basis_status",
        ),
        (
            ContinuityCurrentDecisionOwnerDomain.RESTRICTION,
            ContinuityCurrentDecisionStatus.BLOCKED,
            "restriction_status",
        ),
        (
            ContinuityCurrentDecisionOwnerDomain.ERASURE,
            ContinuityCurrentDecisionStatus.UNKNOWN,
            "erasure_status",
        ),
    ],
)
def test_represented_blocking_and_unknown_states_are_not_softened(
    domain: ContinuityCurrentDecisionOwnerDomain,
    status: ContinuityCurrentDecisionStatus,
    field_name: str,
) -> None:
    resolver = _resolver(overrides={domain: _Owner(domain=domain, status=status)})

    evidence, *_ = _resolve(resolver)

    assert getattr(evidence, field_name) is status


@pytest.mark.parametrize(
    "domain",
    [
        ContinuityCurrentDecisionOwnerDomain.PRINCIPAL,
        ContinuityCurrentDecisionOwnerDomain.POLICY_SNAPSHOT,
    ],
)
def test_non_active_principal_or_policy_snapshot_fails_closed(
    domain: ContinuityCurrentDecisionOwnerDomain,
) -> None:
    resolver = _resolver(
        overrides={
            domain: _Owner(
                domain=domain,
                status=ContinuityCurrentDecisionStatus.UNKNOWN,
            )
        }
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="must be ACTIVE"):
        _resolve(resolver)


def test_owner_identity_mutation_during_resolution_fails_closed() -> None:
    domain = ContinuityCurrentDecisionOwnerDomain.AUTHORIZATION
    resolver = _resolver(
        overrides={domain: _Owner(domain=domain, mutate_identity=True)}
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="identity changed"):
        _resolve(resolver)


def test_owner_exception_fails_closed() -> None:
    domain = ContinuityCurrentDecisionOwnerDomain.RESTRICTION
    resolver = _resolver(overrides={domain: _Owner(domain=domain, fail=True)})

    with pytest.raises(ContinuitySourceAdmissionError, match="failed closed"):
        _resolve(resolver)


def test_resolver_remains_internal_and_unexported() -> None:
    assert not hasattr(
        continuity_package,
        "ContinuityCurrentDecisionResolverComposition",
    )
    assert not hasattr(
        continuity_package,
        "ContinuityCurrentDecisionOwnerSnapshot",
    )
