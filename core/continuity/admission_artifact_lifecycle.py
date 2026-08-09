"""Durable internal lifecycle for accepted Continuity admission artifacts.

This module is evidence-only and explicitly invoked. It performs no producer call,
startup/API/worker wiring, live owner selection, Canon/ESM/TruthGate/GoalStack write,
notification, tool, action, enablement, or runtime-authority grant.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Callable, Protocol, cast

from .admission_evaluator import (
    ADMISSION_EVALUATOR_SCHEMA_VERSION,
    ContinuityAdmissionRegistry,
    ContinuityCurrentDecisionEvidence,
)
from .admission_facade import (
    ADMISSION_FACADE_SCHEMA_VERSION,
    ContinuityAdmissionFacadePolicy,
    ContinuityAdmissionFacadeResult,
)
from .contracts import SubjectKind, SubjectRef
from .current_decision_resolver import (
    CURRENT_DECISION_RESOLVER_SCHEMA_VERSION,
    ContinuityCurrentDecisionOwnerDomain,
    ContinuityCurrentDecisionOwnerSnapshot,
)
from .source_admission import (
    SOURCE_ADMISSION_SCHEMA_VERSION,
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
    _subjects as _normalize_subjects,
    _text,
    _verify_id,
)
from .source_admission_decisions import SOURCE_ADMISSION_DECISION_SCHEMA_VERSION
from .source_admission_payloads import (
    SOURCE_ADMISSION_PAYLOAD_SCHEMA_VERSION,
    ContinuityObservationDraft,
    ContinuitySourceEnvelope,
)

ARTIFACT_SCHEMA_VERSION = "continuity.admission_artifact.v1"
RETENTION_POLICY_SCHEMA_VERSION = "continuity.admission_artifact_retention.v1"
ERASURE_DECISION_SCHEMA_VERSION = "continuity.admission_artifact_erasure.v1"
NEUTRALIZATION_RECEIPT_SCHEMA_VERSION = (
    "continuity.admission_artifact_neutralization.v1"
)
MAX_RETENTION_SECONDS = 31_536_000
MAX_CLEANUP_BATCH = 100
_ACTIVE_TABLE = "continuity_admission_artifacts"
_TOMBSTONE_TABLE = "continuity_admission_artifact_tombstones"
_CLEANUP_REQUEST_TABLE = "continuity_admission_artifact_cleanup_requests"


class ContinuityArtifactLifecycleError(ContinuitySourceAdmissionError):
    """Raised when durable lifecycle evidence cannot be trusted."""


class ContinuityArtifactNeutralizedError(ContinuityArtifactLifecycleError):
    """Raised when replay targets an erased or retention-cleaned artifact."""


class ContinuityArtifactExpiredError(ContinuityArtifactLifecycleError):
    """Raised at or after the explicit retention boundary."""


class ContinuityErasureStatus(str, Enum):
    """External erasure-owner decision for one exact artifact scope."""

    ALLOW = "allow"
    BLOCK = "block"
    UNKNOWN = "unknown"


class ContinuityNeutralizationKind(str, Enum):
    """Why an active payload was atomically neutralized."""

    RETENTION = "retention_cleanup"
    ERASURE = "erasure"


def _bounded_int(value: object, name: str, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ContinuityArtifactLifecycleError(
            f"{name} must be an integer in [1, {maximum}]"
        )
    return value


def _subject_keys(subjects: tuple[SubjectRef, ...]) -> tuple[tuple[str, str], ...]:
    return tuple((subject.subject_id, subject.kind.value) for subject in subjects)


def _canonical_value(value: object) -> object:
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, datetime):
        return _canonical_datetime(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContinuityArtifactLifecycleError(
                    "canonical mapping keys must be strings"
                )
            result[key] = _canonical_value(item)
        return result
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _canonical_value(cast(Callable[[], object], to_dict)())
    raise ContinuityArtifactLifecycleError(
        f"unsupported canonical payload type: {type(value).__name__}"
    )


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            _canonical_value(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ContinuityArtifactLifecycleError(
            "payload cannot be encoded as canonical JSON"
        ) from exc


def _parse_canonical_json(value: object, name: str) -> object:
    if not isinstance(value, str) or not value:
        raise ContinuityArtifactLifecycleError(f"{name} must be canonical JSON")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ContinuityArtifactLifecycleError(
            f"{name} must be canonical JSON"
        ) from exc
    if _canonical_json(parsed) != value:
        raise ContinuityArtifactLifecycleError(
            f"{name} must use canonical JSON encoding"
        )
    return parsed


def _parse_datetime(value: object, name: str) -> datetime:
    if not isinstance(value, str):
        raise ContinuityArtifactLifecycleError(f"{name} must be a canonical datetime")
    try:
        parsed = _aware(datetime.fromisoformat(value.replace("Z", "+00:00")), name)
    except ValueError as exc:
        raise ContinuityArtifactLifecycleError(
            f"{name} must be a canonical datetime"
        ) from exc
    if _canonical_datetime(parsed) != value:
        raise ContinuityArtifactLifecycleError(
            f"{name} must use canonical datetime encoding"
        )
    return parsed


def _stored_subjects(value: object) -> tuple[SubjectRef, ...]:
    parsed = _parse_canonical_json(value, "subject_refs_json")
    if not isinstance(parsed, list):
        raise ContinuityArtifactLifecycleError("stored subject set is malformed")
    subjects: list[SubjectRef] = []
    for item in parsed:
        if not isinstance(item, dict):
            raise ContinuityArtifactLifecycleError("stored subject set is malformed")
        subject_id = item.get("subject_id")
        kind = item.get("kind")
        if not isinstance(subject_id, str) or not isinstance(kind, str):
            raise ContinuityArtifactLifecycleError("stored subject set is malformed")
        try:
            subjects.append(SubjectRef(subject_id=subject_id, kind=SubjectKind(kind)))
        except ValueError as exc:
            raise ContinuityArtifactLifecycleError(
                "stored subject kind is unknown"
            ) from exc
    return _normalize_subjects(subjects)


def _stored_strings(value: object, name: str) -> tuple[str, ...]:
    parsed = _parse_canonical_json(value, name)
    if not isinstance(parsed, list) or any(
        not isinstance(item, str) for item in parsed
    ):
        raise ContinuityArtifactLifecycleError(f"{name} is malformed")
    return _refs(parsed, name)


def _schema_manifest() -> dict[str, str]:
    return {
        "source_admission": SOURCE_ADMISSION_SCHEMA_VERSION,
        "source_payload": SOURCE_ADMISSION_PAYLOAD_SCHEMA_VERSION,
        "source_decision": SOURCE_ADMISSION_DECISION_SCHEMA_VERSION,
        "current_decision_resolver": CURRENT_DECISION_RESOLVER_SCHEMA_VERSION,
        "admission_evaluator": ADMISSION_EVALUATOR_SCHEMA_VERSION,
        "admission_facade": ADMISSION_FACADE_SCHEMA_VERSION,
    }


@dataclass(frozen=True, slots=True)
class ContinuityRetentionPolicy:
    """Explicit bounded retention policy; never selected implicitly."""

    policy_id: str
    retention_class: str
    retention_seconds: int
    max_cleanup_batch: int
    schema_version: str = RETENTION_POLICY_SCHEMA_VERSION
    no_runtime_authority: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != RETENTION_POLICY_SCHEMA_VERSION:
            raise ContinuityArtifactLifecycleError("unknown retention policy version")
        if self.no_runtime_authority is not True:
            raise ContinuityArtifactLifecycleError(
                "retention policy cannot grant runtime authority"
            )
        object.__setattr__(
            self,
            "retention_class",
            _text(self.retention_class, "retention_class"),
        )
        object.__setattr__(
            self,
            "retention_seconds",
            _bounded_int(
                self.retention_seconds,
                "retention_seconds",
                MAX_RETENTION_SECONDS,
            ),
        )
        object.__setattr__(
            self,
            "max_cleanup_batch",
            _bounded_int(
                self.max_cleanup_batch,
                "max_cleanup_batch",
                MAX_CLEANUP_BATCH,
            ),
        )
        _verify_id(self.policy_id, _digest(self.identity_payload()), "policy_id")

    @classmethod
    def create(
        cls,
        *,
        retention_class: str,
        retention_seconds: int,
        max_cleanup_batch: int = MAX_CLEANUP_BATCH,
    ) -> "ContinuityRetentionPolicy":
        payload: dict[str, object] = {
            "schema_version": RETENTION_POLICY_SCHEMA_VERSION,
            "retention_class": _text(retention_class, "retention_class"),
            "retention_seconds": _bounded_int(
                retention_seconds,
                "retention_seconds",
                MAX_RETENTION_SECONDS,
            ),
            "max_cleanup_batch": _bounded_int(
                max_cleanup_batch,
                "max_cleanup_batch",
                MAX_CLEANUP_BATCH,
            ),
            "no_runtime_authority": True,
        }
        return cls(
            policy_id=_digest(payload),
            retention_class=cast(str, payload["retention_class"]),
            retention_seconds=cast(int, payload["retention_seconds"]),
            max_cleanup_batch=cast(int, payload["max_cleanup_batch"]),
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "retention_class": self.retention_class,
            "retention_seconds": self.retention_seconds,
            "max_cleanup_batch": self.max_cleanup_batch,
            "no_runtime_authority": self.no_runtime_authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {"policy_id": self.policy_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class ContinuityArtifactScope:
    """Exact caller scope required for replay and erasure."""

    tenant_ref: str
    principal_context_id: str
    authorization_context_id: str
    subject_refs: tuple[SubjectRef, ...]
    policy_snapshot_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "tenant_ref", _text(self.tenant_ref, "tenant_ref"))
        object.__setattr__(
            self,
            "principal_context_id",
            _hash(self.principal_context_id, "principal_context_id"),
        )
        object.__setattr__(
            self,
            "authorization_context_id",
            _hash(self.authorization_context_id, "authorization_context_id"),
        )
        object.__setattr__(
            self,
            "subject_refs",
            _normalize_subjects(self.subject_refs),
        )
        object.__setattr__(
            self,
            "policy_snapshot_id",
            _text(self.policy_snapshot_id, "policy_snapshot_id"),
        )


@dataclass(frozen=True, slots=True)
class ContinuityAdmissionArtifact:
    """Content-addressed complete admission evidence graph."""

    artifact_id: str
    integrity_digest: str
    tenant_ref: str
    principal_context_id: str
    authorization_context_id: str
    subject_refs: tuple[SubjectRef, ...]
    policy_snapshot_id: str
    retention_policy_id: str
    erasure_domain_refs: tuple[str, ...]
    recorded_at: datetime
    retained_until: datetime
    payload_json: str
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    no_runtime_authority: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != ARTIFACT_SCHEMA_VERSION:
            raise ContinuityArtifactLifecycleError("unknown admission artifact version")
        if self.no_runtime_authority is not True:
            raise ContinuityArtifactLifecycleError(
                "admission artifact cannot grant runtime authority"
            )
        object.__setattr__(
            self,
            "integrity_digest",
            _hash(self.integrity_digest, "integrity_digest"),
        )
        object.__setattr__(self, "tenant_ref", _text(self.tenant_ref, "tenant_ref"))
        object.__setattr__(
            self,
            "principal_context_id",
            _hash(self.principal_context_id, "principal_context_id"),
        )
        object.__setattr__(
            self,
            "authorization_context_id",
            _hash(self.authorization_context_id, "authorization_context_id"),
        )
        object.__setattr__(
            self,
            "subject_refs",
            _normalize_subjects(self.subject_refs),
        )
        object.__setattr__(
            self,
            "policy_snapshot_id",
            _text(self.policy_snapshot_id, "policy_snapshot_id"),
        )
        object.__setattr__(
            self,
            "retention_policy_id",
            _hash(self.retention_policy_id, "retention_policy_id"),
        )
        object.__setattr__(
            self,
            "erasure_domain_refs",
            _refs(
                self.erasure_domain_refs,
                "erasure_domain_refs",
                required=True,
            ),
        )
        object.__setattr__(
            self,
            "recorded_at",
            _aware(self.recorded_at, "recorded_at"),
        )
        object.__setattr__(
            self,
            "retained_until",
            _aware(self.retained_until, "retained_until"),
        )
        if self.retained_until <= self.recorded_at:
            raise ContinuityArtifactLifecycleError("retention interval is empty")
        payload = _parse_canonical_json(self.payload_json, "payload_json")
        if not isinstance(payload, dict):
            raise ContinuityArtifactLifecycleError("artifact payload root is malformed")
        expected_integrity = sha256(self.payload_json.encode("utf-8")).hexdigest()
        _verify_id(self.integrity_digest, expected_integrity, "integrity_digest")
        _verify_id(self.artifact_id, _digest(self.identity_payload()), "artifact_id")
        authorization = payload.get("authorization_context")
        retention = payload.get("retention_policy")
        if not isinstance(authorization, dict) or not isinstance(retention, dict):
            raise ContinuityArtifactLifecycleError(
                "artifact evidence graph is malformed"
            )
        exact_metadata = (
            payload.get("schema_version") == self.schema_version,
            payload.get("schema_manifest") == _schema_manifest(),
            payload.get("recorded_at") == _canonical_datetime(self.recorded_at),
            payload.get("retained_until") == _canonical_datetime(self.retained_until),
            payload.get("no_runtime_authority") is True,
            authorization.get("tenant_ref") == self.tenant_ref,
            authorization.get("principal_context_id") == self.principal_context_id,
            authorization.get("authorization_context_id")
            == self.authorization_context_id,
            authorization.get("subject_refs") == _subject_payload(self.subject_refs),
            authorization.get("policy_snapshot_id") == self.policy_snapshot_id,
            authorization.get("erasure_domain_refs")
            == list(self.erasure_domain_refs),
            retention.get("policy_id") == self.retention_policy_id,
        )
        if not all(exact_metadata):
            raise ContinuityArtifactLifecycleError(
                "artifact payload metadata substitution detected"
            )

    @classmethod
    def create(
        cls,
        *,
        principal_context: ContinuityPrincipalContext,
        authorization_context: ContinuityAuthorizationContext,
        source_envelope: ContinuitySourceEnvelope,
        binding_receipt: ContinuitySourceBindingReceipt,
        drafts: Iterable[ContinuityObservationDraft],
        owner_snapshots: Iterable[ContinuityCurrentDecisionOwnerSnapshot],
        current_decision_evidence: ContinuityCurrentDecisionEvidence,
        registry: ContinuityAdmissionRegistry,
        facade_policy: ContinuityAdmissionFacadePolicy,
        facade_result: ContinuityAdmissionFacadeResult,
        retention_policy: ContinuityRetentionPolicy,
        recorded_at: datetime,
    ) -> "ContinuityAdmissionArtifact":
        if not isinstance(principal_context, ContinuityPrincipalContext):
            raise ContinuityArtifactLifecycleError("principal context is malformed")
        if not isinstance(authorization_context, ContinuityAuthorizationContext):
            raise ContinuityArtifactLifecycleError("authorization context is malformed")
        if not isinstance(source_envelope, ContinuitySourceEnvelope):
            raise ContinuityArtifactLifecycleError("source envelope is malformed")
        if not isinstance(binding_receipt, ContinuitySourceBindingReceipt):
            raise ContinuityArtifactLifecycleError("binding receipt is malformed")
        if not isinstance(current_decision_evidence, ContinuityCurrentDecisionEvidence):
            raise ContinuityArtifactLifecycleError("current decision evidence is malformed")
        if not isinstance(registry, ContinuityAdmissionRegistry):
            raise ContinuityArtifactLifecycleError("admission registry is malformed")
        if not isinstance(facade_policy, ContinuityAdmissionFacadePolicy):
            raise ContinuityArtifactLifecycleError("facade policy is malformed")
        if not isinstance(facade_result, ContinuityAdmissionFacadeResult):
            raise ContinuityArtifactLifecycleError("facade result is malformed")
        if not isinstance(retention_policy, ContinuityRetentionPolicy):
            raise ContinuityArtifactLifecycleError("retention policy is malformed")

        draft_values = _items(drafts, "drafts")
        snapshot_values = _items(owner_snapshots, "owner_snapshots")
        if not draft_values or any(
            not isinstance(value, ContinuityObservationDraft)
            for value in draft_values
        ):
            raise ContinuityArtifactLifecycleError("Draft set is malformed")
        if any(
            not isinstance(value, ContinuityCurrentDecisionOwnerSnapshot)
            for value in snapshot_values
        ):
            raise ContinuityArtifactLifecycleError("owner snapshot set is malformed")
        normalized_drafts = tuple(
            sorted(
                cast(tuple[ContinuityObservationDraft, ...], draft_values),
                key=lambda value: value.draft_id,
            )
        )
        snapshots = tuple(
            sorted(
                cast(
                    tuple[ContinuityCurrentDecisionOwnerSnapshot, ...],
                    snapshot_values,
                ),
                key=lambda value: value.domain.value,
            )
        )
        if len(normalized_drafts) != len(
            {value.draft_id for value in normalized_drafts}
        ):
            raise ContinuityArtifactLifecycleError("duplicate Draft identity")
        if len(snapshots) != 6 or {
            value.domain for value in snapshots
        } != set(ContinuityCurrentDecisionOwnerDomain):
            raise ContinuityArtifactLifecycleError(
                "six exact current-decision owner domains are required"
            )

        evaluation = facade_result.evaluation
        receipt = evaluation.receipt
        graph_checks = (
            authorization_context.principal_context_id
            == principal_context.principal_context_id,
            source_envelope.authorization_context_id
            == authorization_context.authorization_context_id,
            source_envelope.source_binding_receipt_id
            == binding_receipt.binding_receipt_id,
            authorization_context.tenant_ref
            == source_envelope.tenant_ref
            == binding_receipt.tenant_ref,
            _subject_keys(source_envelope.subject_refs)
            == _subject_keys(binding_receipt.subject_refs),
            set(_subject_keys(source_envelope.subject_refs)).issubset(
                set(_subject_keys(authorization_context.subject_refs))
            ),
            all(
                draft.source_envelope_id == source_envelope.envelope_id
                for draft in normalized_drafts
            ),
            receipt.source_envelope_id == source_envelope.envelope_id,
            receipt.source_binding_receipt_id == binding_receipt.binding_receipt_id,
            receipt.authorization_context_id
            == authorization_context.authorization_context_id,
            receipt.policy_snapshot_id == authorization_context.policy_snapshot_id,
            receipt.draft_ids
            == tuple(draft.draft_id for draft in normalized_drafts),
            bool(receipt.admitted_draft_ids),
            current_decision_evidence.principal_context_id
            == principal_context.principal_context_id,
            current_decision_evidence.authorization_context_id
            == authorization_context.authorization_context_id,
            current_decision_evidence.tenant_ref
            == authorization_context.tenant_ref,
            _subject_keys(current_decision_evidence.subject_refs)
            == _subject_keys(authorization_context.subject_refs),
            current_decision_evidence.policy_snapshot_id
            == authorization_context.policy_snapshot_id,
            current_decision_evidence.erasure_domain_refs
            == authorization_context.erasure_domain_refs,
            facade_policy.expected_registry_id == registry.registry_id,
            facade_result.facade_policy_id == facade_policy.facade_policy_id,
            facade_result.registry_id == registry.registry_id,
            facade_result.current_decision_evidence_id
            == current_decision_evidence.current_decision_evidence_id,
            evaluation.current_decision_evidence_id
            == current_decision_evidence.current_decision_evidence_id,
            retention_policy.retention_class
            == authorization_context.retention_class,
        )
        if not all(graph_checks):
            raise ContinuityArtifactLifecycleError(
                "admission evidence graph is not exactly bound"
            )
        for snapshot in snapshots:
            if (
                snapshot.principal_context_id
                != principal_context.principal_context_id
                or snapshot.authorization_context_id
                != authorization_context.authorization_context_id
                or snapshot.source_envelope_id != source_envelope.envelope_id
                or snapshot.source_binding_receipt_id
                != binding_receipt.binding_receipt_id
                or snapshot.tenant_ref != authorization_context.tenant_ref
                or _subject_keys(snapshot.subject_refs)
                != _subject_keys(authorization_context.subject_refs)
                or snapshot.owner_snapshot_id
                not in current_decision_evidence.evidence_refs
            ):
                raise ContinuityArtifactLifecycleError(
                    "current-decision owner snapshot substitution detected"
                )

        recorded = _aware(recorded_at, "recorded_at")
        if recorded < facade_result.evaluated_at:
            raise ContinuityArtifactLifecycleError(
                "artifact recording cannot predate admission evaluation"
            )
        retained_until = recorded + timedelta(
            seconds=retention_policy.retention_seconds
        )
        payload = {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "schema_manifest": _schema_manifest(),
            "principal_context": principal_context.to_dict(),
            "authorization_context": authorization_context.to_dict(),
            "source_binding_receipt": binding_receipt.to_dict(),
            "source_envelope": source_envelope.to_dict(),
            "drafts": [draft.to_dict() for draft in normalized_drafts],
            "owner_snapshots": [snapshot.to_dict() for snapshot in snapshots],
            "current_decision_evidence": current_decision_evidence.to_dict(),
            "registry": registry.to_dict(),
            "facade_policy": facade_policy.to_dict(),
            "facade_result": {
                **facade_result.to_dict(),
                "evaluation": {
                    "receipt": evaluation.receipt.to_dict(),
                    "admitted_draft_ids": list(evaluation.admitted_draft_ids),
                    "rejected_drafts": [
                        rejection.to_dict()
                        for rejection in evaluation.rejected_drafts
                    ],
                    "authority": evaluation.authority,
                    "no_runtime_authority": evaluation.no_runtime_authority,
                },
            },
            "retention_policy": retention_policy.to_dict(),
            "recorded_at": _canonical_datetime(recorded),
            "retained_until": _canonical_datetime(retained_until),
            "no_runtime_authority": True,
        }
        payload_json = _canonical_json(payload)
        integrity_digest = sha256(payload_json.encode("utf-8")).hexdigest()
        identity_payload = {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "integrity_digest": integrity_digest,
            "tenant_ref": authorization_context.tenant_ref,
            "principal_context_id": principal_context.principal_context_id,
            "authorization_context_id": authorization_context.authorization_context_id,
            "subject_refs": _subject_payload(authorization_context.subject_refs),
            "policy_snapshot_id": authorization_context.policy_snapshot_id,
            "retention_policy_id": retention_policy.policy_id,
            "erasure_domain_refs": list(
                authorization_context.erasure_domain_refs
            ),
            "recorded_at": _canonical_datetime(recorded),
            "retained_until": _canonical_datetime(retained_until),
            "payload_json": payload_json,
            "no_runtime_authority": True,
        }
        return cls(
            artifact_id=_digest(identity_payload),
            integrity_digest=integrity_digest,
            tenant_ref=authorization_context.tenant_ref,
            principal_context_id=principal_context.principal_context_id,
            authorization_context_id=authorization_context.authorization_context_id,
            subject_refs=authorization_context.subject_refs,
            policy_snapshot_id=authorization_context.policy_snapshot_id,
            retention_policy_id=retention_policy.policy_id,
            erasure_domain_refs=authorization_context.erasure_domain_refs,
            recorded_at=recorded,
            retained_until=retained_until,
            payload_json=payload_json,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "integrity_digest": self.integrity_digest,
            "tenant_ref": self.tenant_ref,
            "principal_context_id": self.principal_context_id,
            "authorization_context_id": self.authorization_context_id,
            "subject_refs": _subject_payload(self.subject_refs),
            "policy_snapshot_id": self.policy_snapshot_id,
            "retention_policy_id": self.retention_policy_id,
            "erasure_domain_refs": list(self.erasure_domain_refs),
            "recorded_at": _canonical_datetime(self.recorded_at),
            "retained_until": _canonical_datetime(self.retained_until),
            "payload_json": self.payload_json,
            "no_runtime_authority": self.no_runtime_authority,
        }


@dataclass(frozen=True, slots=True)
class ContinuityErasureDecision:
    """Content-addressed decision supplied by an existing erasure owner."""

    decision_id: str
    owner_id: str
    owner_version: str
    status: ContinuityErasureStatus
    artifact_id: str
    tenant_ref: str
    principal_context_id: str
    authorization_context_id: str
    subject_refs: tuple[SubjectRef, ...]
    erasure_domain_refs: tuple[str, ...]
    observed_at: datetime
    valid_until: datetime
    evidence_refs: tuple[str, ...]
    schema_version: str = ERASURE_DECISION_SCHEMA_VERSION
    no_runtime_authority: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != ERASURE_DECISION_SCHEMA_VERSION:
            raise ContinuityArtifactLifecycleError("unknown erasure decision version")
        if self.no_runtime_authority is not True:
            raise ContinuityArtifactLifecycleError(
                "erasure decision cannot grant runtime authority"
            )
        object.__setattr__(self, "owner_id", _text(self.owner_id, "owner_id"))
        object.__setattr__(
            self,
            "owner_version",
            _text(self.owner_version, "owner_version"),
        )
        if not isinstance(self.status, ContinuityErasureStatus):
            raise ContinuityArtifactLifecycleError("erasure status is invalid")
        object.__setattr__(self, "artifact_id", _hash(self.artifact_id, "artifact_id"))
        object.__setattr__(self, "tenant_ref", _text(self.tenant_ref, "tenant_ref"))
        object.__setattr__(
            self,
            "principal_context_id",
            _hash(self.principal_context_id, "principal_context_id"),
        )
        object.__setattr__(
            self,
            "authorization_context_id",
            _hash(self.authorization_context_id, "authorization_context_id"),
        )
        object.__setattr__(
            self,
            "subject_refs",
            _normalize_subjects(self.subject_refs),
        )
        object.__setattr__(
            self,
            "erasure_domain_refs",
            _refs(
                self.erasure_domain_refs,
                "erasure_domain_refs",
                required=True,
            ),
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
        object.__setattr__(
            self,
            "evidence_refs",
            _refs(self.evidence_refs, "evidence_refs", required=True),
        )
        if self.valid_until <= self.observed_at:
            raise ContinuityArtifactLifecycleError(
                "erasure decision validity interval is empty"
            )
        _verify_id(self.decision_id, _digest(self.identity_payload()), "decision_id")

    @classmethod
    def create(
        cls,
        *,
        owner_id: str,
        owner_version: str,
        status: ContinuityErasureStatus,
        artifact: ContinuityAdmissionArtifact,
        observed_at: datetime,
        valid_until: datetime,
        evidence_refs: Iterable[str],
    ) -> "ContinuityErasureDecision":
        if not isinstance(status, ContinuityErasureStatus):
            raise ContinuityArtifactLifecycleError("erasure status is invalid")
        owner_name = _text(owner_id, "owner_id")
        owner_revision = _text(owner_version, "owner_version")
        observed = _aware(observed_at, "observed_at")
        expires = _aware(valid_until, "valid_until")
        refs = _refs(evidence_refs, "evidence_refs", required=True)
        payload = {
            "schema_version": ERASURE_DECISION_SCHEMA_VERSION,
            "owner_id": owner_name,
            "owner_version": owner_revision,
            "status": status.value,
            "artifact_id": artifact.artifact_id,
            "tenant_ref": artifact.tenant_ref,
            "principal_context_id": artifact.principal_context_id,
            "authorization_context_id": artifact.authorization_context_id,
            "subject_refs": _subject_payload(artifact.subject_refs),
            "erasure_domain_refs": list(artifact.erasure_domain_refs),
            "observed_at": _canonical_datetime(observed),
            "valid_until": _canonical_datetime(expires),
            "evidence_refs": list(refs),
            "no_runtime_authority": True,
        }
        return cls(
            decision_id=_digest(payload),
            owner_id=owner_name,
            owner_version=owner_revision,
            status=status,
            artifact_id=artifact.artifact_id,
            tenant_ref=artifact.tenant_ref,
            principal_context_id=artifact.principal_context_id,
            authorization_context_id=artifact.authorization_context_id,
            subject_refs=artifact.subject_refs,
            erasure_domain_refs=artifact.erasure_domain_refs,
            observed_at=observed,
            valid_until=expires,
            evidence_refs=refs,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "owner_id": self.owner_id,
            "owner_version": self.owner_version,
            "status": self.status.value,
            "artifact_id": self.artifact_id,
            "tenant_ref": self.tenant_ref,
            "principal_context_id": self.principal_context_id,
            "authorization_context_id": self.authorization_context_id,
            "subject_refs": _subject_payload(self.subject_refs),
            "erasure_domain_refs": list(self.erasure_domain_refs),
            "observed_at": _canonical_datetime(self.observed_at),
            "valid_until": _canonical_datetime(self.valid_until),
            "evidence_refs": list(self.evidence_refs),
            "no_runtime_authority": self.no_runtime_authority,
        }


class ContinuityErasureOwner(Protocol):
    """Injected existing owner; lifecycle code never selects an implementation."""

    owner_id: str
    owner_version: str

    def resolve_erasure(
        self,
        *,
        artifact: ContinuityAdmissionArtifact,
        requested_at: datetime,
    ) -> ContinuityErasureDecision: ...


@dataclass(frozen=True, slots=True)
class ContinuityNeutralizationReceipt:
    """Addressable evidence left after payload neutralization."""

    receipt_id: str
    artifact_id: str
    kind: ContinuityNeutralizationKind
    request_id: str
    tenant_ref: str
    principal_context_id: str
    authorization_context_id: str
    subject_refs: tuple[SubjectRef, ...]
    erasure_domain_refs: tuple[str, ...]
    policy_snapshot_id: str
    neutralized_at: datetime
    evidence_refs: tuple[str, ...]
    owner_id: str | None
    owner_version: str | None
    schema_version: str = NEUTRALIZATION_RECEIPT_SCHEMA_VERSION
    no_runtime_authority: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != NEUTRALIZATION_RECEIPT_SCHEMA_VERSION:
            raise ContinuityArtifactLifecycleError(
                "unknown neutralization receipt version"
            )
        if self.no_runtime_authority is not True:
            raise ContinuityArtifactLifecycleError(
                "neutralization receipt cannot grant runtime authority"
            )
        object.__setattr__(self, "artifact_id", _hash(self.artifact_id, "artifact_id"))
        object.__setattr__(self, "request_id", _hash(self.request_id, "request_id"))
        if not isinstance(self.kind, ContinuityNeutralizationKind):
            raise ContinuityArtifactLifecycleError("neutralization kind is invalid")
        object.__setattr__(self, "tenant_ref", _text(self.tenant_ref, "tenant_ref"))
        object.__setattr__(
            self,
            "principal_context_id",
            _hash(self.principal_context_id, "principal_context_id"),
        )
        object.__setattr__(
            self,
            "authorization_context_id",
            _hash(self.authorization_context_id, "authorization_context_id"),
        )
        object.__setattr__(
            self,
            "subject_refs",
            _normalize_subjects(self.subject_refs),
        )
        object.__setattr__(
            self,
            "erasure_domain_refs",
            _refs(
                self.erasure_domain_refs,
                "erasure_domain_refs",
                required=True,
            ),
        )
        object.__setattr__(
            self,
            "policy_snapshot_id",
            _text(self.policy_snapshot_id, "policy_snapshot_id"),
        )
        object.__setattr__(
            self,
            "neutralized_at",
            _aware(self.neutralized_at, "neutralized_at"),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _refs(self.evidence_refs, "evidence_refs", required=True),
        )
        if (self.owner_id is None) != (self.owner_version is None):
            raise ContinuityArtifactLifecycleError(
                "neutralization owner identity is incomplete"
            )
        if self.owner_id is not None:
            object.__setattr__(self, "owner_id", _text(self.owner_id, "owner_id"))
            object.__setattr__(
                self,
                "owner_version",
                _text(self.owner_version, "owner_version"),
            )
        if (self.kind is ContinuityNeutralizationKind.ERASURE) != (
            self.owner_id is not None
        ):
            raise ContinuityArtifactLifecycleError(
                "neutralization owner boundary is invalid"
            )
        _verify_id(self.receipt_id, _digest(self.identity_payload()), "receipt_id")

    @classmethod
    def create(
        cls,
        *,
        artifact: ContinuityAdmissionArtifact,
        kind: ContinuityNeutralizationKind,
        request_id: str,
        neutralized_at: datetime,
        evidence_refs: Iterable[str],
        owner_id: str | None = None,
        owner_version: str | None = None,
    ) -> "ContinuityNeutralizationReceipt":
        request = _hash(request_id, "request_id")
        neutralized = _aware(neutralized_at, "neutralized_at")
        refs = _refs(evidence_refs, "evidence_refs", required=True)
        payload = {
            "schema_version": NEUTRALIZATION_RECEIPT_SCHEMA_VERSION,
            "artifact_id": artifact.artifact_id,
            "kind": kind.value,
            "request_id": request,
            "tenant_ref": artifact.tenant_ref,
            "principal_context_id": artifact.principal_context_id,
            "authorization_context_id": artifact.authorization_context_id,
            "subject_refs": _subject_payload(artifact.subject_refs),
            "erasure_domain_refs": list(artifact.erasure_domain_refs),
            "policy_snapshot_id": artifact.policy_snapshot_id,
            "neutralized_at": _canonical_datetime(neutralized),
            "evidence_refs": list(refs),
            "owner_id": owner_id,
            "owner_version": owner_version,
            "no_runtime_authority": True,
        }
        return cls(
            receipt_id=_digest(payload),
            artifact_id=artifact.artifact_id,
            kind=kind,
            request_id=request,
            tenant_ref=artifact.tenant_ref,
            principal_context_id=artifact.principal_context_id,
            authorization_context_id=artifact.authorization_context_id,
            subject_refs=artifact.subject_refs,
            erasure_domain_refs=artifact.erasure_domain_refs,
            policy_snapshot_id=artifact.policy_snapshot_id,
            neutralized_at=neutralized,
            evidence_refs=refs,
            owner_id=owner_id,
            owner_version=owner_version,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "artifact_id": self.artifact_id,
            "kind": self.kind.value,
            "request_id": self.request_id,
            "tenant_ref": self.tenant_ref,
            "principal_context_id": self.principal_context_id,
            "authorization_context_id": self.authorization_context_id,
            "subject_refs": _subject_payload(self.subject_refs),
            "erasure_domain_refs": list(self.erasure_domain_refs),
            "policy_snapshot_id": self.policy_snapshot_id,
            "neutralized_at": _canonical_datetime(self.neutralized_at),
            "evidence_refs": list(self.evidence_refs),
            "owner_id": self.owner_id,
            "owner_version": self.owner_version,
            "no_runtime_authority": self.no_runtime_authority,
        }


class ContinuityArtifactStore:
    """Append-safe SQLite owner for active payloads and addressable tombstones."""

    def __init__(
        self,
        db_path: str | Path,
        *,
        busy_timeout_ms: int = 5_000,
    ) -> None:
        self._db_path = str(Path(db_path))
        self._busy_timeout_ms = _bounded_int(
            busy_timeout_ms,
            "busy_timeout_ms",
            60_000,
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._db_path,
            timeout=self._busy_timeout_ms / 1_000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute(f"PRAGMA busy_timeout={self._busy_timeout_ms}")
        return connection

    def ensure_schema(self) -> None:
        try:
            with self._connect() as connection:
                connection.executescript(
                    f"""
                    CREATE TABLE IF NOT EXISTS {_ACTIVE_TABLE}(
                        artifact_id TEXT PRIMARY KEY,
                        integrity_digest TEXT NOT NULL,
                        tenant_ref TEXT NOT NULL,
                        principal_context_id TEXT NOT NULL,
                        authorization_context_id TEXT NOT NULL,
                        subject_refs_json TEXT NOT NULL,
                        policy_snapshot_id TEXT NOT NULL,
                        retention_policy_id TEXT NOT NULL,
                        erasure_domain_refs_json TEXT NOT NULL,
                        recorded_at TEXT NOT NULL,
                        retained_until TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        append_receipt_id TEXT NOT NULL UNIQUE,
                        appended_at TEXT NOT NULL,
                        schema_version TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_continuity_artifact_retention
                    ON {_ACTIVE_TABLE}(
                        tenant_ref,
                        retention_policy_id,
                        retained_until,
                        artifact_id
                    );
                    CREATE TABLE IF NOT EXISTS {_TOMBSTONE_TABLE}(
                        artifact_id TEXT PRIMARY KEY,
                        receipt_id TEXT NOT NULL UNIQUE,
                        kind TEXT NOT NULL,
                        request_id TEXT NOT NULL,
                        tenant_ref TEXT NOT NULL,
                        principal_context_id TEXT NOT NULL,
                        authorization_context_id TEXT NOT NULL,
                        subject_refs_json TEXT NOT NULL,
                        erasure_domain_refs_json TEXT NOT NULL,
                        policy_snapshot_id TEXT NOT NULL,
                        neutralized_at TEXT NOT NULL,
                        evidence_refs_json TEXT NOT NULL,
                        owner_id TEXT NULL,
                        owner_version TEXT NULL,
                        schema_version TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_continuity_artifact_request
                    ON {_TOMBSTONE_TABLE}(
                        request_id,
                        neutralized_at,
                        artifact_id
                    );
                    CREATE TABLE IF NOT EXISTS {_CLEANUP_REQUEST_TABLE}(
                        request_id TEXT PRIMARY KEY,
                        tenant_ref TEXT NOT NULL,
                        retention_policy_id TEXT NOT NULL,
                        effective_at TEXT NOT NULL,
                        cleanup_limit INTEGER NOT NULL,
                        completed_at TEXT NOT NULL
                    );
                    """
                )
        except sqlite3.Error as exc:
            raise ContinuityArtifactLifecycleError(
                "storage schema failed closed"
            ) from exc

    def append(
        self,
        artifact: ContinuityAdmissionArtifact,
        *,
        appended_at: datetime,
    ) -> str:
        if not isinstance(artifact, ContinuityAdmissionArtifact):
            raise ContinuityArtifactLifecycleError("artifact is malformed")
        appended = _aware(appended_at, "appended_at")
        if appended < artifact.recorded_at:
            raise ContinuityArtifactLifecycleError(
                "append cannot predate artifact recording"
            )
        if appended >= artifact.retained_until:
            raise ContinuityArtifactExpiredError(
                "expired artifact cannot be appended"
            )
        append_receipt_id = _digest(
            {
                "artifact_id": artifact.artifact_id,
                "integrity_digest": artifact.integrity_digest,
                "appended_at": _canonical_datetime(appended),
                "authority": "durable_append_evidence_only",
                "no_runtime_authority": True,
            }
        )
        self.ensure_schema()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute(
                f"SELECT 1 FROM {_TOMBSTONE_TABLE} WHERE artifact_id=?",
                (artifact.artifact_id,),
            ).fetchone():
                raise ContinuityArtifactNeutralizedError(
                    "neutralized artifact cannot be re-appended"
                )
            existing = connection.execute(
                f"SELECT * FROM {_ACTIVE_TABLE} WHERE artifact_id=?",
                (artifact.artifact_id,),
            ).fetchone()
            if existing is not None:
                stored_artifact, stored_receipt_id = self._artifact_from_row(existing)
                if stored_artifact != artifact:
                    raise ContinuityArtifactLifecycleError(
                        "artifact identity conflicts with stored content"
                    )
                connection.execute("COMMIT")
                return stored_receipt_id
            connection.execute(
                f"""
                INSERT INTO {_ACTIVE_TABLE}(
                    artifact_id,
                    integrity_digest,
                    tenant_ref,
                    principal_context_id,
                    authorization_context_id,
                    subject_refs_json,
                    policy_snapshot_id,
                    retention_policy_id,
                    erasure_domain_refs_json,
                    recorded_at,
                    retained_until,
                    payload_json,
                    append_receipt_id,
                    appended_at,
                    schema_version
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    artifact.artifact_id,
                    artifact.integrity_digest,
                    artifact.tenant_ref,
                    artifact.principal_context_id,
                    artifact.authorization_context_id,
                    _canonical_json(_subject_payload(artifact.subject_refs)),
                    artifact.policy_snapshot_id,
                    artifact.retention_policy_id,
                    _canonical_json(list(artifact.erasure_domain_refs)),
                    _canonical_datetime(artifact.recorded_at),
                    _canonical_datetime(artifact.retained_until),
                    artifact.payload_json,
                    append_receipt_id,
                    _canonical_datetime(appended),
                    artifact.schema_version,
                ),
            )
            self._after_append_insert(connection, artifact)
            connection.execute("COMMIT")
            return append_receipt_id
        except ContinuityArtifactLifecycleError:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        except sqlite3.Error as exc:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise ContinuityArtifactLifecycleError(
                "append storage failed closed"
            ) from exc
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def replay(
        self,
        artifact_id: str,
        *,
        scope: ContinuityArtifactScope,
        replayed_at: datetime,
    ) -> ContinuityAdmissionArtifact:
        identifier = _hash(artifact_id, "artifact_id")
        replayed = _aware(replayed_at, "replayed_at")
        self.ensure_schema()
        try:
            with self._connect() as connection:
                if connection.execute(
                    f"SELECT 1 FROM {_TOMBSTONE_TABLE} WHERE artifact_id=?",
                    (identifier,),
                ).fetchone():
                    raise ContinuityArtifactNeutralizedError(
                        "artifact payload was neutralized"
                    )
                row = connection.execute(
                    f"SELECT * FROM {_ACTIVE_TABLE} WHERE artifact_id=?",
                    (identifier,),
                ).fetchone()
                if row is None:
                    raise ContinuityArtifactLifecycleError("artifact was not found")
                artifact, _append_receipt_id = self._artifact_from_row(row)
        except ContinuityArtifactLifecycleError:
            raise
        except sqlite3.Error as exc:
            raise ContinuityArtifactLifecycleError(
                "replay storage failed closed"
            ) from exc
        self._verify_scope(artifact, scope)
        if replayed >= artifact.retained_until:
            raise ContinuityArtifactExpiredError(
                "artifact reached its retention boundary"
            )
        return artifact

    def cleanup(
        self,
        *,
        tenant_ref: str,
        retention_policy: ContinuityRetentionPolicy,
        effective_at: datetime,
        limit: int,
    ) -> tuple[ContinuityNeutralizationReceipt, ...]:
        tenant = _text(tenant_ref, "tenant_ref")
        if not isinstance(retention_policy, ContinuityRetentionPolicy):
            raise ContinuityArtifactLifecycleError("retention policy is malformed")
        effective = _aware(effective_at, "effective_at")
        cleanup_limit = _bounded_int(
            limit,
            "limit",
            retention_policy.max_cleanup_batch,
        )
        request_id = _digest(
            {
                "tenant_ref": tenant,
                "retention_policy_id": retention_policy.policy_id,
                "effective_at": _canonical_datetime(effective),
                "limit": cleanup_limit,
                "authority": "retention_cleanup_request_only",
                "no_runtime_authority": True,
            }
        )
        self.ensure_schema()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            previous = connection.execute(
                f"SELECT * FROM {_CLEANUP_REQUEST_TABLE} WHERE request_id=?",
                (request_id,),
            ).fetchone()
            if previous is not None:
                receipts = self._receipts_for_request(connection, request_id)
                connection.execute("COMMIT")
                return receipts
            rows = connection.execute(
                f"""
                SELECT * FROM {_ACTIVE_TABLE}
                WHERE tenant_ref=?
                  AND retention_policy_id=?
                  AND retained_until<=?
                ORDER BY retained_until, artifact_id
                LIMIT ?
                """,
                (
                    tenant,
                    retention_policy.policy_id,
                    _canonical_datetime(effective),
                    cleanup_limit,
                ),
            ).fetchall()
            receipts: list[ContinuityNeutralizationReceipt] = []
            for row in rows:
                artifact, _append_receipt_id = self._artifact_from_row(row)
                receipt = ContinuityNeutralizationReceipt.create(
                    artifact=artifact,
                    kind=ContinuityNeutralizationKind.RETENTION,
                    request_id=request_id,
                    neutralized_at=effective,
                    evidence_refs=(
                        artifact.integrity_digest,
                        retention_policy.policy_id,
                    ),
                )
                self._neutralize(connection, artifact, receipt)
                receipts.append(receipt)
            connection.execute(
                f"""
                INSERT INTO {_CLEANUP_REQUEST_TABLE}(
                    request_id,
                    tenant_ref,
                    retention_policy_id,
                    effective_at,
                    cleanup_limit,
                    completed_at
                ) VALUES (?,?,?,?,?,?)
                """,
                (
                    request_id,
                    tenant,
                    retention_policy.policy_id,
                    _canonical_datetime(effective),
                    cleanup_limit,
                    _canonical_datetime(effective),
                ),
            )
            connection.execute("COMMIT")
            return tuple(receipts)
        except ContinuityArtifactLifecycleError:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        except sqlite3.Error as exc:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise ContinuityArtifactLifecycleError(
                "cleanup storage failed closed"
            ) from exc
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def erase(
        self,
        artifact: ContinuityAdmissionArtifact,
        *,
        scope: ContinuityArtifactScope,
        owner: ContinuityErasureOwner,
        requested_at: datetime,
    ) -> ContinuityNeutralizationReceipt:
        if not isinstance(artifact, ContinuityAdmissionArtifact):
            raise ContinuityArtifactLifecycleError("artifact is malformed")
        requested = _aware(requested_at, "requested_at")
        self._verify_scope(artifact, scope)
        try:
            owner_identity = (
                _text(owner.owner_id, "owner_id"),
                _text(owner.owner_version, "owner_version"),
            )
            decision = owner.resolve_erasure(
                artifact=artifact,
                requested_at=requested,
            )
        except Exception as exc:
            raise ContinuityArtifactLifecycleError(
                "erasure owner failed closed"
            ) from exc
        if owner_identity != (
            _text(owner.owner_id, "owner_id"),
            _text(owner.owner_version, "owner_version"),
        ):
            raise ContinuityArtifactLifecycleError(
                "erasure owner identity changed during resolution"
            )
        if not isinstance(decision, ContinuityErasureDecision):
            raise ContinuityArtifactLifecycleError("erasure decision is malformed")
        exact_decision = (
            (decision.owner_id, decision.owner_version) == owner_identity,
            decision.artifact_id == artifact.artifact_id,
            decision.tenant_ref == artifact.tenant_ref,
            decision.principal_context_id == artifact.principal_context_id,
            decision.authorization_context_id == artifact.authorization_context_id,
            _subject_keys(decision.subject_refs)
            == _subject_keys(artifact.subject_refs),
            decision.erasure_domain_refs == artifact.erasure_domain_refs,
            decision.observed_at <= requested < decision.valid_until,
        )
        if not all(exact_decision):
            raise ContinuityArtifactLifecycleError(
                "erasure decision is stale or substituted"
            )
        if decision.status is not ContinuityErasureStatus.ALLOW:
            raise ContinuityArtifactLifecycleError(
                "erasure decision did not explicitly allow neutralization"
            )
        receipt = ContinuityNeutralizationReceipt.create(
            artifact=artifact,
            kind=ContinuityNeutralizationKind.ERASURE,
            request_id=decision.decision_id,
            neutralized_at=requested,
            evidence_refs=(
                artifact.integrity_digest,
                decision.decision_id,
                *decision.evidence_refs,
            ),
            owner_id=owner_identity[0],
            owner_version=owner_identity[1],
        )
        self.ensure_schema()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                f"SELECT * FROM {_ACTIVE_TABLE} WHERE artifact_id=?",
                (artifact.artifact_id,),
            ).fetchone()
            if row is None:
                raise ContinuityArtifactLifecycleError(
                    "exact active artifact ownership was lost"
                )
            stored_artifact, _append_receipt_id = self._artifact_from_row(row)
            if stored_artifact != artifact:
                raise ContinuityArtifactLifecycleError(
                    "stored artifact no longer matches erasure target"
                )
            self._neutralize(connection, artifact, receipt)
            connection.execute("COMMIT")
            return receipt
        except ContinuityArtifactLifecycleError:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        except sqlite3.Error as exc:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise ContinuityArtifactLifecycleError(
                "erasure storage failed closed"
            ) from exc
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    @staticmethod
    def _verify_scope(
        artifact: ContinuityAdmissionArtifact,
        scope: ContinuityArtifactScope,
    ) -> None:
        if not isinstance(scope, ContinuityArtifactScope):
            raise ContinuityArtifactLifecycleError("artifact scope is malformed")
        exact_scope = (
            artifact.tenant_ref == scope.tenant_ref,
            artifact.principal_context_id == scope.principal_context_id,
            artifact.authorization_context_id == scope.authorization_context_id,
            _subject_keys(artifact.subject_refs)
            == _subject_keys(scope.subject_refs),
            artifact.policy_snapshot_id == scope.policy_snapshot_id,
        )
        if not all(exact_scope):
            raise ContinuityArtifactLifecycleError(
                "artifact scope substitution detected"
            )

    @staticmethod
    def _artifact_from_row(
        row: sqlite3.Row,
    ) -> tuple[ContinuityAdmissionArtifact, str]:
        artifact = ContinuityAdmissionArtifact(
            artifact_id=row["artifact_id"],
            integrity_digest=row["integrity_digest"],
            tenant_ref=row["tenant_ref"],
            principal_context_id=row["principal_context_id"],
            authorization_context_id=row["authorization_context_id"],
            subject_refs=_stored_subjects(row["subject_refs_json"]),
            policy_snapshot_id=row["policy_snapshot_id"],
            retention_policy_id=row["retention_policy_id"],
            erasure_domain_refs=_stored_strings(
                row["erasure_domain_refs_json"],
                "erasure_domain_refs_json",
            ),
            recorded_at=_parse_datetime(row["recorded_at"], "recorded_at"),
            retained_until=_parse_datetime(
                row["retained_until"],
                "retained_until",
            ),
            payload_json=row["payload_json"],
            schema_version=row["schema_version"],
        )
        append_receipt_id = _hash(
            row["append_receipt_id"],
            "append_receipt_id",
        )
        return artifact, append_receipt_id

    @staticmethod
    def _receipt_from_row(row: sqlite3.Row) -> ContinuityNeutralizationReceipt:
        try:
            kind = ContinuityNeutralizationKind(row["kind"])
        except ValueError as exc:
            raise ContinuityArtifactLifecycleError(
                "stored neutralization kind is unknown"
            ) from exc
        return ContinuityNeutralizationReceipt(
            receipt_id=row["receipt_id"],
            artifact_id=row["artifact_id"],
            kind=kind,
            request_id=row["request_id"],
            tenant_ref=row["tenant_ref"],
            principal_context_id=row["principal_context_id"],
            authorization_context_id=row["authorization_context_id"],
            subject_refs=_stored_subjects(row["subject_refs_json"]),
            erasure_domain_refs=_stored_strings(
                row["erasure_domain_refs_json"],
                "erasure_domain_refs_json",
            ),
            policy_snapshot_id=row["policy_snapshot_id"],
            neutralized_at=_parse_datetime(
                row["neutralized_at"],
                "neutralized_at",
            ),
            evidence_refs=_stored_strings(
                row["evidence_refs_json"],
                "evidence_refs_json",
            ),
            owner_id=row["owner_id"],
            owner_version=row["owner_version"],
            schema_version=row["schema_version"],
        )

    def _receipts_for_request(
        self,
        connection: sqlite3.Connection,
        request_id: str,
    ) -> tuple[ContinuityNeutralizationReceipt, ...]:
        rows = connection.execute(
            f"""
            SELECT * FROM {_TOMBSTONE_TABLE}
            WHERE request_id=?
            ORDER BY neutralized_at, artifact_id
            """,
            (request_id,),
        ).fetchall()
        return tuple(self._receipt_from_row(row) for row in rows)

    def _neutralize(
        self,
        connection: sqlite3.Connection,
        artifact: ContinuityAdmissionArtifact,
        receipt: ContinuityNeutralizationReceipt,
    ) -> None:
        connection.execute(
            f"""
            INSERT INTO {_TOMBSTONE_TABLE}(
                artifact_id,
                receipt_id,
                kind,
                request_id,
                tenant_ref,
                principal_context_id,
                authorization_context_id,
                subject_refs_json,
                erasure_domain_refs_json,
                policy_snapshot_id,
                neutralized_at,
                evidence_refs_json,
                owner_id,
                owner_version,
                schema_version
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                receipt.artifact_id,
                receipt.receipt_id,
                receipt.kind.value,
                receipt.request_id,
                receipt.tenant_ref,
                receipt.principal_context_id,
                receipt.authorization_context_id,
                _canonical_json(_subject_payload(receipt.subject_refs)),
                _canonical_json(list(receipt.erasure_domain_refs)),
                receipt.policy_snapshot_id,
                _canonical_datetime(receipt.neutralized_at),
                _canonical_json(list(receipt.evidence_refs)),
                receipt.owner_id,
                receipt.owner_version,
                receipt.schema_version,
            ),
        )
        deleted = connection.execute(
            f"DELETE FROM {_ACTIVE_TABLE} WHERE artifact_id=?",
            (artifact.artifact_id,),
        ).rowcount
        if deleted != 1:
            raise ContinuityArtifactLifecycleError(
                "neutralization lost exact active artifact ownership"
            )
        self._after_neutralization(connection, receipt)

    def _after_append_insert(
        self,
        connection: sqlite3.Connection,
        artifact: ContinuityAdmissionArtifact,
    ) -> None:
        """Fault-injection seam before append commit; inert in production."""

        del connection, artifact

    def _after_neutralization(
        self,
        connection: sqlite3.Connection,
        receipt: ContinuityNeutralizationReceipt,
    ) -> None:
        """Fault-injection seam before neutralization commit; inert in production."""

        del connection, receipt
