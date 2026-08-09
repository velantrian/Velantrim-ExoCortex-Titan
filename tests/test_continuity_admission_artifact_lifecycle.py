"""Adversarial tests for the internal Continuity admission-artifact lifecycle."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

import pytest

import core.continuity as continuity_package
from core.continuity.admission_artifact_lifecycle import (
    ARTIFACT_SCHEMA_VERSION,
    ContinuityAdmissionArtifact,
    ContinuityArtifactExpiredError,
    ContinuityArtifactLifecycleError,
    ContinuityArtifactNeutralizedError,
    ContinuityArtifactScope,
    ContinuityArtifactStore,
    ContinuityErasureDecision,
    ContinuityErasureStatus,
    ContinuityNeutralizationKind,
    ContinuityRetentionPolicy,
)
from core.continuity.admission_evaluator import (
    ContinuityAdmissionEvaluatorDefinition,
    ContinuityAdmissionRegistry,
    ContinuityAdmissionRuleDefinition,
    ContinuityCurrentDecisionEvidence,
    ContinuityCurrentDecisionStatus,
)
from core.continuity.admission_facade import (
    ContinuityAdmissionFacadePolicy,
    evaluate_continuity_admission_facade,
)
from core.continuity.contracts import SubjectKind, SubjectRef
from core.continuity.current_decision_resolver import (
    ContinuityCurrentDecisionOwnerDomain,
    ContinuityCurrentDecisionOwnerSnapshot,
)
from core.continuity.observations import ContinuitySignalType
from core.continuity.source_admission import (
    ContinuityAuthorizationContext,
    ContinuityPrincipalContext,
    ContinuitySourceBindingReceipt,
)
from core.continuity.source_admission_payloads import (
    ContinuityObservationDraft,
    ContinuitySourceEnvelope,
)

_NOW = datetime(2026, 8, 9, 20, 0, tzinfo=UTC)
_SUBJECT = SubjectRef(subject_id="subject:alice", kind=SubjectKind.PERSON)
_OTHER_SUBJECT = SubjectRef(subject_id="subject:bob", kind=SubjectKind.PERSON)


@dataclass(frozen=True, slots=True)
class _Scenario:
    principal: ContinuityPrincipalContext
    authorization: ContinuityAuthorizationContext
    binding: ContinuitySourceBindingReceipt
    envelope: ContinuitySourceEnvelope
    drafts: tuple[ContinuityObservationDraft, ...]
    snapshots: tuple[ContinuityCurrentDecisionOwnerSnapshot, ...]
    current_evidence: ContinuityCurrentDecisionEvidence
    registry: ContinuityAdmissionRegistry
    facade_policy: ContinuityAdmissionFacadePolicy
    facade_result: object
    retention_policy: ContinuityRetentionPolicy
    artifact: ContinuityAdmissionArtifact
    scope: ContinuityArtifactScope


@dataclass(slots=True)
class _StaticResolver:
    evidence: ContinuityCurrentDecisionEvidence
    resolver_id: str = "continuity.test_current_decision_resolver"
    resolver_version: str = "1"
    calls: int = 0

    def resolve_current_decision(
        self,
        *,
        principal_context: ContinuityPrincipalContext,
        authorization_context: ContinuityAuthorizationContext,
        source_envelope: ContinuitySourceEnvelope,
        binding_receipt: ContinuitySourceBindingReceipt,
        evaluated_at: datetime,
    ) -> ContinuityCurrentDecisionEvidence:
        del (
            principal_context,
            authorization_context,
            source_envelope,
            binding_receipt,
            evaluated_at,
        )
        self.calls += 1
        return self.evidence


@dataclass(slots=True)
class _ErasureOwner:
    status: ContinuityErasureStatus = ContinuityErasureStatus.ALLOW
    decision_artifact: ContinuityAdmissionArtifact | None = None
    fail: bool = False
    mutate_identity: bool = False
    observed_at: datetime = _NOW - timedelta(minutes=1)
    valid_until: datetime = _NOW + timedelta(minutes=30)
    owner_id: str = "erasure.owner.test"
    owner_version: str = "1"
    calls: int = 0

    def resolve_erasure(
        self,
        *,
        artifact: ContinuityAdmissionArtifact,
        requested_at: datetime,
    ) -> ContinuityErasureDecision:
        del requested_at
        self.calls += 1
        if self.fail:
            raise RuntimeError("owner unavailable")
        owner_id = self.owner_id
        if self.mutate_identity:
            self.owner_id = "erasure.owner.changed"
        return ContinuityErasureDecision.create(
            owner_id=owner_id,
            owner_version=self.owner_version,
            status=self.status,
            artifact=self.decision_artifact or artifact,
            observed_at=self.observed_at,
            valid_until=self.valid_until,
            evidence_refs=("erasure:evidence",),
        )


class _AppendFaultStore(ContinuityArtifactStore):
    def _after_append_insert(
        self,
        connection: sqlite3.Connection,
        artifact: ContinuityAdmissionArtifact,
    ) -> None:
        del connection, artifact
        raise RuntimeError("simulated append interruption")


class _NeutralizationFaultStore(ContinuityArtifactStore):
    def _after_neutralization(self, connection, receipt) -> None:  # type: ignore[no-untyped-def]
        del connection, receipt
        raise RuntimeError("simulated neutralization interruption")


def _principal(*, suffix: str = "alice") -> ContinuityPrincipalContext:
    return ContinuityPrincipalContext.create(
        principal_ref=f"principal:{suffix}",
        principal_kind="human",
        authentication_method="oidc",
        authentication_strength="mfa",
        authenticated_at=_NOW - timedelta(minutes=30),
        issuer_ref="issuer:test",
        authentication_receipt_ref=f"authentication:{suffix}",
    )


def _authorization(
    principal: ContinuityPrincipalContext,
    *,
    subjects: tuple[SubjectRef, ...] = (_SUBJECT,),
    tenant_ref: str = "tenant:one",
    policy_snapshot_id: str = "policy:current",
) -> ContinuityAuthorizationContext:
    return ContinuityAuthorizationContext.create(
        tenant_ref=tenant_ref,
        subject_refs=subjects,
        principal_context=principal,
        purpose_code="continuity_analysis",
        lawful_basis_or_consent_ref="consent:active",
        authorization_receipt_ref="authorization:active",
        policy_snapshot_id=policy_snapshot_id,
        retention_class="ephemeral",
        erasure_domain_refs=tuple(
            f"erasure:{subject.subject_id}" for subject in subjects
        ),
        valid_from=_NOW - timedelta(hours=1),
        valid_until=_NOW + timedelta(hours=2),
        data_handling_mode="local_only",
    )


def _binding(
    *,
    tag: str,
    subjects: tuple[SubjectRef, ...] = (_SUBJECT,),
    tenant_ref: str = "tenant:one",
) -> ContinuitySourceBindingReceipt:
    return ContinuitySourceBindingReceipt.create(
        source_type="state_reconciliation_result",
        source_result_id=f"state-result:{tag}",
        source_digest=sha256(f"state-result:{tag}".encode()).hexdigest(),
        source_owner="continuity.state_reconciler",
        tenant_ref=tenant_ref,
        subject_refs=subjects,
        source_component_version="1",
        source_policy_version="1",
        source_as_of=_NOW - timedelta(minutes=5),
        evidence_refs=(f"event:{tag}",),
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


def _draft(envelope: ContinuitySourceEnvelope, *, tag: str) -> ContinuityObservationDraft:
    return ContinuityObservationDraft.create(
        source_envelope=envelope,
        signal_type=ContinuitySignalType.CONTEXT_DEGRADED,
        value=True,
        proposed_confidence=1.0,
        evidence_refs=envelope.evidence_refs,
        reason_codes=(f"reason:{tag}",),
        derivation_rule_id="state.context_degraded.v1",
        created_at=_NOW - timedelta(minutes=2),
        scope=f"scope:{tag}",
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
    if domain is ContinuityCurrentDecisionOwnerDomain.ERASURE:
        return authorization.erasure_domain_refs
    return (authorization.policy_snapshot_id,)


def _snapshots(
    *,
    principal: ContinuityPrincipalContext,
    authorization: ContinuityAuthorizationContext,
    envelope: ContinuitySourceEnvelope,
    binding: ContinuitySourceBindingReceipt,
) -> tuple[ContinuityCurrentDecisionOwnerSnapshot, ...]:
    statuses = {
        ContinuityCurrentDecisionOwnerDomain.PRINCIPAL: (
            ContinuityCurrentDecisionStatus.ACTIVE
        ),
        ContinuityCurrentDecisionOwnerDomain.AUTHORIZATION: (
            ContinuityCurrentDecisionStatus.ACTIVE
        ),
        ContinuityCurrentDecisionOwnerDomain.LAWFUL_BASIS: (
            ContinuityCurrentDecisionStatus.ACTIVE
        ),
        ContinuityCurrentDecisionOwnerDomain.RESTRICTION: (
            ContinuityCurrentDecisionStatus.CLEAR
        ),
        ContinuityCurrentDecisionOwnerDomain.ERASURE: (
            ContinuityCurrentDecisionStatus.CLEAR
        ),
        ContinuityCurrentDecisionOwnerDomain.POLICY_SNAPSHOT: (
            ContinuityCurrentDecisionStatus.ACTIVE
        ),
    }
    return tuple(
        ContinuityCurrentDecisionOwnerSnapshot.create(
            domain=domain,
            owner_id=f"owner:{domain.value}",
            owner_version="1",
            principal_context=principal,
            authorization_context=authorization,
            source_envelope=envelope,
            binding_receipt=binding,
            scope_refs=_scope_refs(domain, principal, authorization),
            status=statuses[domain],
            observed_at=_NOW - timedelta(minutes=1),
            valid_until=_NOW + timedelta(minutes=30),
            evidence_refs=(f"owner:evidence:{domain.value}",),
        )
        for domain in ContinuityCurrentDecisionOwnerDomain
    )


def _registry() -> ContinuityAdmissionRegistry:
    rule = ContinuityAdmissionRuleDefinition.create(
        rule_id="continuity.admission.default",
        rule_version="1",
        allowed_source_types=("state_reconciliation_result",),
        allowed_adapter_ids=("continuity.state_reconciliation_to_drafts",),
        allowed_derivation_rule_ids=("state.context_degraded.v1",),
        allowed_signal_types=(ContinuitySignalType.CONTEXT_DEGRADED,),
        minimum_confidence=0.8,
        maximum_draft_age_seconds=600,
        required_purpose_code="continuity_analysis",
        required_data_handling_mode="local_only",
        allowed_retention_classes=("ephemeral",),
    )
    evaluator = ContinuityAdmissionEvaluatorDefinition.create(
        evaluator_id="continuity.admission_evaluator",
        evaluator_version="1",
        allowed_rules=(rule,),
    )
    return ContinuityAdmissionRegistry.create(
        evaluator_definitions=(evaluator,),
        rule_definitions=(rule,),
    )


def _scenario(
    *,
    tag: str = "a",
    recorded_at: datetime = _NOW,
    subjects: tuple[SubjectRef, ...] = (_SUBJECT,),
) -> _Scenario:
    principal = _principal()
    authorization = _authorization(principal, subjects=subjects)
    binding = _binding(tag=tag, subjects=subjects)
    envelope = _envelope(authorization, binding)
    drafts = (_draft(envelope, tag=tag),)
    snapshots = _snapshots(
        principal=principal,
        authorization=authorization,
        envelope=envelope,
        binding=binding,
    )
    current_evidence = ContinuityCurrentDecisionEvidence.create(
        principal_context=principal,
        authorization_context=authorization,
        authorization_status=ContinuityCurrentDecisionStatus.ACTIVE,
        lawful_basis_status=ContinuityCurrentDecisionStatus.ACTIVE,
        restriction_status=ContinuityCurrentDecisionStatus.CLEAR,
        erasure_status=ContinuityCurrentDecisionStatus.CLEAR,
        observed_at=_NOW - timedelta(minutes=1),
        valid_until=_NOW + timedelta(minutes=30),
        evidence_refs=tuple(snapshot.owner_snapshot_id for snapshot in snapshots),
    )
    registry = _registry()
    facade_policy = ContinuityAdmissionFacadePolicy.create(
        expected_registry=registry,
        evaluator_id="continuity.admission_evaluator",
        evaluator_version="1",
        rule_id="continuity.admission.default",
        rule_version="1",
        resolver_id="continuity.test_current_decision_resolver",
        resolver_version="1",
    )
    resolver = _StaticResolver(current_evidence)
    facade_result = evaluate_continuity_admission_facade(
        policy=facade_policy,
        registry=registry,
        resolver=resolver,
        principal_context=principal,
        authorization_context=authorization,
        source_envelope=envelope,
        binding_receipt=binding,
        drafts=drafts,
        evaluated_at=_NOW,
    )
    retention_policy = ContinuityRetentionPolicy.create(
        retention_class="ephemeral",
        retention_seconds=60,
        max_cleanup_batch=10,
    )
    artifact = ContinuityAdmissionArtifact.create(
        principal_context=principal,
        authorization_context=authorization,
        source_envelope=envelope,
        binding_receipt=binding,
        drafts=drafts,
        owner_snapshots=snapshots,
        current_decision_evidence=current_evidence,
        registry=registry,
        facade_policy=facade_policy,
        facade_result=facade_result,
        retention_policy=retention_policy,
        recorded_at=recorded_at,
    )
    scope = ContinuityArtifactScope(
        tenant_ref=authorization.tenant_ref,
        principal_context_id=principal.principal_context_id,
        authorization_context_id=authorization.authorization_context_id,
        subject_refs=authorization.subject_refs,
        policy_snapshot_id=authorization.policy_snapshot_id,
    )
    return _Scenario(
        principal=principal,
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        drafts=drafts,
        snapshots=snapshots,
        current_evidence=current_evidence,
        registry=registry,
        facade_policy=facade_policy,
        facade_result=facade_result,
        retention_policy=retention_policy,
        artifact=artifact,
        scope=scope,
    )


def _db(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def test_artifact_identity_append_and_replay_are_deterministic(tmp_path: Path) -> None:
    first = _scenario()
    second = _scenario()
    store = ContinuityArtifactStore(tmp_path / "artifacts.sqlite")

    first_receipt = store.append(first.artifact, appended_at=_NOW)
    duplicate_receipt = store.append(second.artifact, appended_at=_NOW + timedelta(seconds=1))
    replayed = store.replay(
        first.artifact.artifact_id,
        scope=first.scope,
        replayed_at=_NOW + timedelta(seconds=30),
    )

    assert first.artifact == second.artifact
    assert first_receipt == duplicate_receipt
    assert replayed == first.artifact
    assert replayed.no_runtime_authority is True


def test_concurrent_duplicate_append_is_idempotent(tmp_path: Path) -> None:
    scenario = _scenario()
    store = ContinuityArtifactStore(tmp_path / "artifacts.sqlite")

    with ThreadPoolExecutor(max_workers=8) as pool:
        receipts = tuple(
            pool.map(
                lambda _: store.append(scenario.artifact, appended_at=_NOW),
                range(16),
            )
        )

    assert len(set(receipts)) == 1
    assert store.replay(
        scenario.artifact.artifact_id,
        scope=scenario.scope,
        replayed_at=_NOW + timedelta(seconds=1),
    ) == scenario.artifact


@pytest.mark.parametrize(
    "scope",
    [
        lambda scenario: replace(scenario.scope, tenant_ref="tenant:other"),
        lambda scenario: replace(
            scenario.scope,
            principal_context_id="0" * 64,
        ),
        lambda scenario: replace(
            scenario.scope,
            authorization_context_id="1" * 64,
        ),
        lambda scenario: replace(scenario.scope, subject_refs=(_OTHER_SUBJECT,)),
        lambda scenario: replace(
            scenario.scope,
            policy_snapshot_id="policy:stale",
        ),
    ],
)
def test_replay_rejects_scope_substitution(tmp_path: Path, scope) -> None:  # type: ignore[no-untyped-def]
    scenario = _scenario()
    store = ContinuityArtifactStore(tmp_path / "artifacts.sqlite")
    store.append(scenario.artifact, appended_at=_NOW)

    with pytest.raises(ContinuityArtifactLifecycleError, match="substitution"):
        store.replay(
            scenario.artifact.artifact_id,
            scope=scope(scenario),
            replayed_at=_NOW + timedelta(seconds=1),
        )


def test_retention_boundary_is_fail_closed(tmp_path: Path) -> None:
    scenario = _scenario()
    store = ContinuityArtifactStore(tmp_path / "artifacts.sqlite")
    store.append(scenario.artifact, appended_at=_NOW)

    assert store.replay(
        scenario.artifact.artifact_id,
        scope=scenario.scope,
        replayed_at=scenario.artifact.retained_until - timedelta(microseconds=1),
    ) == scenario.artifact
    with pytest.raises(ContinuityArtifactExpiredError):
        store.replay(
            scenario.artifact.artifact_id,
            scope=scenario.scope,
            replayed_at=scenario.artifact.retained_until,
        )
    with pytest.raises(ContinuityArtifactExpiredError):
        store.replay(
            scenario.artifact.artifact_id,
            scope=scenario.scope,
            replayed_at=scenario.artifact.retained_until + timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("integrity_digest", "0" * 64, "integrity_digest"),
        ("payload_json", "{", "canonical JSON"),
        ("schema_version", "continuity.admission_artifact.v999", "unknown"),
        ("subject_refs_json", "[]", "subject_refs"),
    ],
)
def test_corrupt_or_malformed_storage_fails_closed(
    tmp_path: Path,
    column: str,
    value: str,
    message: str,
) -> None:
    scenario = _scenario()
    path = tmp_path / "artifacts.sqlite"
    store = ContinuityArtifactStore(path)
    store.append(scenario.artifact, appended_at=_NOW)
    with _db(path) as connection:
        connection.execute(
            f"UPDATE continuity_admission_artifacts SET {column}=? WHERE artifact_id=?",
            (value, scenario.artifact.artifact_id),
        )

    with pytest.raises(ContinuityArtifactLifecycleError, match=message):
        store.replay(
            scenario.artifact.artifact_id,
            scope=scenario.scope,
            replayed_at=_NOW + timedelta(seconds=1),
        )


def test_coherently_rehashed_unknown_manifest_still_fails() -> None:
    scenario = _scenario()
    payload = json.loads(scenario.artifact.payload_json)
    payload["schema_manifest"]["admission_facade"] = "unknown.v999"
    payload_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    digest = sha256(payload_json.encode()).hexdigest()
    identity = scenario.artifact.identity_payload()
    identity["integrity_digest"] = digest
    identity["payload_json"] = payload_json

    with pytest.raises(ContinuityArtifactLifecycleError, match="metadata"):
        ContinuityAdmissionArtifact(
            artifact_id=sha256(
                json.dumps(
                    identity,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            ).hexdigest(),
            integrity_digest=digest,
            tenant_ref=scenario.artifact.tenant_ref,
            principal_context_id=scenario.artifact.principal_context_id,
            authorization_context_id=scenario.artifact.authorization_context_id,
            subject_refs=scenario.artifact.subject_refs,
            policy_snapshot_id=scenario.artifact.policy_snapshot_id,
            retention_policy_id=scenario.artifact.retention_policy_id,
            erasure_domain_refs=scenario.artifact.erasure_domain_refs,
            recorded_at=scenario.artifact.recorded_at,
            retained_until=scenario.artifact.retained_until,
            payload_json=payload_json,
        )


def test_conflicting_stored_identity_is_not_overwritten(tmp_path: Path) -> None:
    scenario = _scenario()
    other = _scenario(tag="other")
    path = tmp_path / "artifacts.sqlite"
    store = ContinuityArtifactStore(path)
    store.append(scenario.artifact, appended_at=_NOW)
    with _db(path) as connection:
        connection.execute(
            "UPDATE continuity_admission_artifacts SET payload_json=? WHERE artifact_id=?",
            (other.artifact.payload_json, scenario.artifact.artifact_id),
        )

    with pytest.raises(ContinuityArtifactLifecycleError):
        store.append(scenario.artifact, appended_at=_NOW + timedelta(seconds=1))
    with _db(path) as connection:
        row = connection.execute(
            "SELECT payload_json FROM continuity_admission_artifacts WHERE artifact_id=?",
            (scenario.artifact.artifact_id,),
        ).fetchone()
    assert row["payload_json"] == other.artifact.payload_json


def test_partial_append_rolls_back_atomically(tmp_path: Path) -> None:
    scenario = _scenario()
    path = tmp_path / "artifacts.sqlite"

    with pytest.raises(RuntimeError, match="append interruption"):
        _AppendFaultStore(path).append(scenario.artifact, appended_at=_NOW)

    with pytest.raises(ContinuityArtifactLifecycleError, match="not found"):
        ContinuityArtifactStore(path).replay(
            scenario.artifact.artifact_id,
            scope=scenario.scope,
            replayed_at=_NOW + timedelta(seconds=1),
        )


def test_cleanup_is_bounded_ordered_and_idempotent(tmp_path: Path) -> None:
    first = _scenario(tag="a")
    second = _scenario(tag="b")
    path = tmp_path / "artifacts.sqlite"
    store = ContinuityArtifactStore(path)
    store.append(first.artifact, appended_at=_NOW)
    store.append(second.artifact, appended_at=_NOW)
    effective = first.artifact.retained_until

    receipts = store.cleanup(
        tenant_ref="tenant:one",
        retention_policy=first.retention_policy,
        effective_at=effective,
        limit=10,
    )
    retry = store.cleanup(
        tenant_ref="tenant:one",
        retention_policy=first.retention_policy,
        effective_at=effective,
        limit=10,
    )

    assert tuple(receipt.artifact_id for receipt in receipts) == tuple(
        sorted((first.artifact.artifact_id, second.artifact.artifact_id))
    )
    assert retry == receipts
    assert all(
        receipt.kind is ContinuityNeutralizationKind.RETENTION
        and receipt.owner_id is None
        and first.retention_policy.policy_id in receipt.evidence_refs
        for receipt in receipts
    )


def test_cleanup_limit_and_empty_retry_are_stable(tmp_path: Path) -> None:
    first = _scenario(tag="a")
    second = _scenario(tag="b")
    path = tmp_path / "artifacts.sqlite"
    store = ContinuityArtifactStore(path)
    store.append(first.artifact, appended_at=_NOW)
    store.append(second.artifact, appended_at=_NOW)

    one = store.cleanup(
        tenant_ref="tenant:one",
        retention_policy=first.retention_policy,
        effective_at=first.artifact.retained_until,
        limit=1,
    )
    assert len(one) == 1

    empty_time = _NOW - timedelta(seconds=1)
    empty = store.cleanup(
        tenant_ref="tenant:one",
        retention_policy=first.retention_policy,
        effective_at=empty_time,
        limit=10,
    )
    retry = store.cleanup(
        tenant_ref="tenant:one",
        retention_policy=first.retention_policy,
        effective_at=empty_time,
        limit=10,
    )
    assert empty == retry == ()


def test_interrupted_cleanup_rolls_back_and_retry_succeeds(tmp_path: Path) -> None:
    scenario = _scenario()
    path = tmp_path / "artifacts.sqlite"
    normal = ContinuityArtifactStore(path)
    normal.append(scenario.artifact, appended_at=_NOW)

    with pytest.raises(RuntimeError, match="neutralization interruption"):
        _NeutralizationFaultStore(path).cleanup(
            tenant_ref="tenant:one",
            retention_policy=scenario.retention_policy,
            effective_at=scenario.artifact.retained_until,
            limit=10,
        )

    assert normal.replay(
        scenario.artifact.artifact_id,
        scope=scenario.scope,
        replayed_at=_NOW + timedelta(seconds=1),
    ) == scenario.artifact
    receipts = normal.cleanup(
        tenant_ref="tenant:one",
        retention_policy=scenario.retention_policy,
        effective_at=scenario.artifact.retained_until,
        limit=10,
    )
    assert len(receipts) == 1


def test_erasure_neutralizes_payload_and_preserves_addressability(tmp_path: Path) -> None:
    scenario = _scenario()
    path = tmp_path / "artifacts.sqlite"
    store = ContinuityArtifactStore(path)
    store.append(scenario.artifact, appended_at=_NOW)

    receipt = store.erase(
        scenario.artifact,
        scope=scenario.scope,
        owner=_ErasureOwner(),
        requested_at=_NOW + timedelta(seconds=1),
    )

    assert receipt.kind is ContinuityNeutralizationKind.ERASURE
    assert receipt.tenant_ref == scenario.artifact.tenant_ref
    assert receipt.subject_refs == scenario.artifact.subject_refs
    assert receipt.erasure_domain_refs == scenario.artifact.erasure_domain_refs
    with pytest.raises(ContinuityArtifactNeutralizedError):
        store.replay(
            scenario.artifact.artifact_id,
            scope=scenario.scope,
            replayed_at=_NOW + timedelta(seconds=2),
        )
    with pytest.raises(ContinuityArtifactNeutralizedError):
        store.append(scenario.artifact, appended_at=_NOW + timedelta(seconds=2))
    with _db(path) as connection:
        assert connection.execute(
            "SELECT 1 FROM continuity_admission_artifacts WHERE artifact_id=?",
            (scenario.artifact.artifact_id,),
        ).fetchone() is None
        tombstone = connection.execute(
            "SELECT * FROM continuity_admission_artifact_tombstones WHERE artifact_id=?",
            (scenario.artifact.artifact_id,),
        ).fetchone()
    assert tombstone["tenant_ref"] == scenario.artifact.tenant_ref
    assert tombstone["principal_context_id"] == scenario.artifact.principal_context_id
    assert "payload_json" not in tombstone.keys()


@pytest.mark.parametrize(
    "status",
    [ContinuityErasureStatus.BLOCK, ContinuityErasureStatus.UNKNOWN],
)
def test_erasure_requires_explicit_allow(
    tmp_path: Path,
    status: ContinuityErasureStatus,
) -> None:
    scenario = _scenario()
    store = ContinuityArtifactStore(tmp_path / "artifacts.sqlite")
    store.append(scenario.artifact, appended_at=_NOW)

    with pytest.raises(ContinuityArtifactLifecycleError, match="explicitly allow"):
        store.erase(
            scenario.artifact,
            scope=scenario.scope,
            owner=_ErasureOwner(status=status),
            requested_at=_NOW + timedelta(seconds=1),
        )
    assert store.replay(
        scenario.artifact.artifact_id,
        scope=scenario.scope,
        replayed_at=_NOW + timedelta(seconds=2),
    ) == scenario.artifact


@pytest.mark.parametrize(
    "owner",
    [
        _ErasureOwner(fail=True),
        _ErasureOwner(mutate_identity=True),
        _ErasureOwner(
            observed_at=_NOW - timedelta(hours=2),
            valid_until=_NOW - timedelta(hours=1),
        ),
    ],
)
def test_erasure_owner_failure_or_staleness_fails_closed(
    tmp_path: Path,
    owner: _ErasureOwner,
) -> None:
    scenario = _scenario()
    store = ContinuityArtifactStore(tmp_path / "artifacts.sqlite")
    store.append(scenario.artifact, appended_at=_NOW)

    with pytest.raises(ContinuityArtifactLifecycleError):
        store.erase(
            scenario.artifact,
            scope=scenario.scope,
            owner=owner,
            requested_at=_NOW + timedelta(seconds=1),
        )


def test_erasure_rejects_cross_artifact_decision(tmp_path: Path) -> None:
    scenario = _scenario(tag="a")
    other = _scenario(tag="b")
    store = ContinuityArtifactStore(tmp_path / "artifacts.sqlite")
    store.append(scenario.artifact, appended_at=_NOW)

    with pytest.raises(ContinuityArtifactLifecycleError, match="substituted"):
        store.erase(
            scenario.artifact,
            scope=scenario.scope,
            owner=_ErasureOwner(decision_artifact=other.artifact),
            requested_at=_NOW + timedelta(seconds=1),
        )


def test_interrupted_erasure_rolls_back(tmp_path: Path) -> None:
    scenario = _scenario()
    path = tmp_path / "artifacts.sqlite"
    normal = ContinuityArtifactStore(path)
    normal.append(scenario.artifact, appended_at=_NOW)

    with pytest.raises(RuntimeError, match="neutralization interruption"):
        _NeutralizationFaultStore(path).erase(
            scenario.artifact,
            scope=scenario.scope,
            owner=_ErasureOwner(),
            requested_at=_NOW + timedelta(seconds=1),
        )
    assert normal.replay(
        scenario.artifact.artifact_id,
        scope=scenario.scope,
        replayed_at=_NOW + timedelta(seconds=2),
    ) == scenario.artifact


def test_artifact_creation_rejects_principal_and_subject_substitution() -> None:
    scenario = _scenario()
    other_principal = _principal(suffix="mallory")

    with pytest.raises(ContinuityArtifactLifecycleError, match="exactly bound"):
        ContinuityAdmissionArtifact.create(
            principal_context=other_principal,
            authorization_context=scenario.authorization,
            source_envelope=scenario.envelope,
            binding_receipt=scenario.binding,
            drafts=scenario.drafts,
            owner_snapshots=scenario.snapshots,
            current_decision_evidence=scenario.current_evidence,
            registry=scenario.registry,
            facade_policy=scenario.facade_policy,
            facade_result=scenario.facade_result,  # type: ignore[arg-type]
            retention_policy=scenario.retention_policy,
            recorded_at=_NOW,
        )

    substituted_binding = _binding(tag="substitute", subjects=(_OTHER_SUBJECT,))
    with pytest.raises(ContinuityArtifactLifecycleError, match="exactly bound"):
        ContinuityAdmissionArtifact.create(
            principal_context=scenario.principal,
            authorization_context=scenario.authorization,
            source_envelope=scenario.envelope,
            binding_receipt=substituted_binding,
            drafts=scenario.drafts,
            owner_snapshots=scenario.snapshots,
            current_decision_evidence=scenario.current_evidence,
            registry=scenario.registry,
            facade_policy=scenario.facade_policy,
            facade_result=scenario.facade_result,  # type: ignore[arg-type]
            retention_policy=scenario.retention_policy,
            recorded_at=_NOW,
        )


def test_duplicate_or_missing_owner_snapshot_fails_closed() -> None:
    scenario = _scenario()
    snapshots = scenario.snapshots[:-1] + (scenario.snapshots[0],)

    with pytest.raises(ContinuityArtifactLifecycleError, match="six exact"):
        ContinuityAdmissionArtifact.create(
            principal_context=scenario.principal,
            authorization_context=scenario.authorization,
            source_envelope=scenario.envelope,
            binding_receipt=scenario.binding,
            drafts=scenario.drafts,
            owner_snapshots=snapshots,
            current_decision_evidence=scenario.current_evidence,
            registry=scenario.registry,
            facade_policy=scenario.facade_policy,
            facade_result=scenario.facade_result,  # type: ignore[arg-type]
            retention_policy=scenario.retention_policy,
            recorded_at=_NOW,
        )


def test_storage_exception_is_wrapped_fail_closed(tmp_path: Path) -> None:
    scenario = _scenario()
    missing_parent = tmp_path / "missing" / "artifacts.sqlite"

    with pytest.raises(ContinuityArtifactLifecycleError, match="storage schema"):
        ContinuityArtifactStore(missing_parent).append(
            scenario.artifact,
            appended_at=_NOW,
        )


def test_no_producer_runtime_or_public_package_side_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario = _scenario()

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        raise AssertionError("producer/runtime side effect")

    import core.continuity.signal_producer as signal_producer

    monkeypatch.setattr(
        signal_producer,
        "produce_continuity_compute_signals",
        _forbidden,
    )
    store = ContinuityArtifactStore(tmp_path / "artifacts.sqlite")
    store.append(scenario.artifact, appended_at=_NOW)
    store.replay(
        scenario.artifact.artifact_id,
        scope=scenario.scope,
        replayed_at=_NOW + timedelta(seconds=1),
    )

    assert not hasattr(continuity_package, "ContinuityArtifactStore")
    assert not hasattr(continuity_package, "ContinuityAdmissionArtifact")
    with _db(tmp_path / "artifacts.sqlite") as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert tables == {
        "continuity_admission_artifacts",
        "continuity_admission_artifact_tombstones",
        "continuity_admission_artifact_cleanup_requests",
    }
    assert scenario.artifact.schema_version == ARTIFACT_SCHEMA_VERSION
