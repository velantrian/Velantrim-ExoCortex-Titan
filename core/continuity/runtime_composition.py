"""Bounded internal runtime composition for Continuity artifact persistence.

The owner in this module selects one exact SQLite lifecycle implementation from
immutable deployment configuration and exposes only explicit persistence and replay of
an already-completed, facade-bound accepted admission graph. It does not activate a
producer, change public API behavior, authorize use of stored evidence, or grant runtime
authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
from threading import RLock

from .admission_artifact_lifecycle import (
    ContinuityAdmissionArtifact,
    ContinuityArtifactLifecycleError,
    ContinuityArtifactScope,
    ContinuityArtifactStore,
    ContinuityRetentionPolicy,
)
from .admission_evaluator import (
    ContinuityAdmissionRegistry,
    ContinuityCurrentDecisionEvidence,
)
from .admission_facade import (
    ContinuityAdmissionFacadePolicy,
    ContinuityAdmissionFacadeResult,
)
from .current_decision_resolver import ContinuityCurrentDecisionOwnerSnapshot
from .source_admission import (
    ContinuityAuthorizationContext,
    ContinuityPrincipalContext,
    ContinuitySourceBindingReceipt,
)
from .source_admission_payloads import (
    ContinuityObservationDraft,
    ContinuitySourceEnvelope,
)

RUNTIME_COMPOSITION_SCHEMA_VERSION = "continuity.runtime_composition.v1"
SUPPORTED_LIFECYCLE_OWNER_ID = "continuity.admission_artifact.sqlite"
SUPPORTED_LIFECYCLE_OWNER_VERSION = "1"

ENV_RUNTIME_OWNER_ID = "VELANTRIM_CONTINUITY_RUNTIME_OWNER_ID"
ENV_RUNTIME_OWNER_VERSION = "VELANTRIM_CONTINUITY_RUNTIME_OWNER_VERSION"
ENV_RUNTIME_STORAGE_ROOT = "VELANTRIM_CONTINUITY_RUNTIME_STORAGE_ROOT"
ENV_RUNTIME_TENANT_REF = "VELANTRIM_CONTINUITY_RUNTIME_TENANT_REF"
_RUNTIME_ENV_FIELDS = (
    ENV_RUNTIME_OWNER_ID,
    ENV_RUNTIME_OWNER_VERSION,
    ENV_RUNTIME_STORAGE_ROOT,
    ENV_RUNTIME_TENANT_REF,
)

_EXPECTED_SCHEMA_COLUMNS: dict[str, tuple[str, ...]] = {
    "continuity_admission_artifacts": (
        "artifact_id",
        "integrity_digest",
        "tenant_ref",
        "principal_context_id",
        "authorization_context_id",
        "subject_refs_json",
        "policy_snapshot_id",
        "retention_policy_id",
        "erasure_domain_refs_json",
        "recorded_at",
        "retained_until",
        "payload_json",
        "append_receipt_id",
        "appended_at",
        "schema_version",
    ),
    "continuity_admission_artifact_tombstones": (
        "artifact_id",
        "receipt_id",
        "kind",
        "request_id",
        "tenant_ref",
        "principal_context_id",
        "authorization_context_id",
        "subject_refs_json",
        "erasure_domain_refs_json",
        "policy_snapshot_id",
        "neutralized_at",
        "evidence_refs_json",
        "owner_id",
        "owner_version",
        "schema_version",
    ),
    "continuity_admission_artifact_cleanup_requests": (
        "request_id",
        "tenant_ref",
        "retention_policy_id",
        "effective_at",
        "cleanup_limit",
        "completed_at",
    ),
}


class ContinuityRuntimeCompositionError(ContinuityArtifactLifecycleError):
    """Base failure for the bounded runtime-composition boundary."""


class ContinuityRuntimeConfigurationError(ContinuityRuntimeCompositionError):
    """Raised when deployment configuration is absent in part or cannot be trusted."""


class ContinuityRuntimeStateError(ContinuityRuntimeCompositionError):
    """Raised when an operation violates the owner lifecycle state machine."""


class ContinuityRuntimeState(str, Enum):
    NEW = "new"
    STARTED = "started"
    STOPPED = "stopped"


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContinuityRuntimeConfigurationError(f"{name} must be a non-empty string")
    return value.strip()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: object) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _safe_storage_root(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)):
        raise ContinuityRuntimeConfigurationError(
            "storage_root must be an absolute deployment-owned directory"
        )
    path = Path(value)
    if not path.is_absolute():
        raise ContinuityRuntimeConfigurationError(
            "storage_root must be an absolute deployment-owned directory"
        )
    if path.is_symlink():
        raise ContinuityRuntimeConfigurationError("storage_root cannot be a symlink")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ContinuityRuntimeConfigurationError(
            "storage_root must already exist"
        ) from exc
    if resolved != path or not resolved.is_dir():
        raise ContinuityRuntimeConfigurationError(
            "storage_root must be a canonical existing directory"
        )
    return resolved


def _verify_selected_schema(database_path: Path) -> None:
    try:
        with sqlite3.connect(database_path) as connection:
            for table, expected in _EXPECTED_SCHEMA_COLUMNS.items():
                rows = connection.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()
                actual = tuple(str(row[1]) for row in rows)
                if actual != expected:
                    raise ContinuityRuntimeCompositionError(
                        "selected lifecycle storage schema is incompatible"
                    )
    except ContinuityRuntimeCompositionError:
        raise
    except sqlite3.Error as exc:
        raise ContinuityRuntimeCompositionError(
            "selected lifecycle storage schema validation failed"
        ) from exc


@dataclass(frozen=True, slots=True)
class ContinuityRuntimeConfiguration:
    """Immutable deployment selection for one exact lifecycle owner and tenant."""

    configuration_id: str
    lifecycle_owner_id: str
    lifecycle_owner_version: str
    storage_root: Path
    tenant_ref: str
    schema_version: str = RUNTIME_COMPOSITION_SCHEMA_VERSION
    no_runtime_authority: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != RUNTIME_COMPOSITION_SCHEMA_VERSION:
            raise ContinuityRuntimeConfigurationError(
                "runtime configuration schema version is unsupported"
            )
        if self.no_runtime_authority is not True:
            raise ContinuityRuntimeConfigurationError(
                "runtime configuration cannot grant runtime authority"
            )
        owner_id = _text(self.lifecycle_owner_id, "lifecycle_owner_id")
        owner_version = _text(
            self.lifecycle_owner_version,
            "lifecycle_owner_version",
        )
        if owner_id != SUPPORTED_LIFECYCLE_OWNER_ID:
            raise ContinuityRuntimeConfigurationError(
                "lifecycle owner ID is unsupported"
            )
        if owner_version != SUPPORTED_LIFECYCLE_OWNER_VERSION:
            raise ContinuityRuntimeConfigurationError(
                "lifecycle owner version is unsupported"
            )
        storage_root = _safe_storage_root(self.storage_root)
        tenant_ref = _text(self.tenant_ref, "tenant_ref")
        object.__setattr__(self, "lifecycle_owner_id", owner_id)
        object.__setattr__(self, "lifecycle_owner_version", owner_version)
        object.__setattr__(self, "storage_root", storage_root)
        object.__setattr__(self, "tenant_ref", tenant_ref)
        expected = _digest(self.identity_payload())
        if self.configuration_id != expected:
            raise ContinuityRuntimeConfigurationError(
                "runtime configuration identity mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        lifecycle_owner_id: str,
        lifecycle_owner_version: str,
        storage_root: str | Path,
        tenant_ref: str,
    ) -> "ContinuityRuntimeConfiguration":
        owner_id = _text(lifecycle_owner_id, "lifecycle_owner_id")
        owner_version = _text(
            lifecycle_owner_version,
            "lifecycle_owner_version",
        )
        root = _safe_storage_root(storage_root)
        tenant = _text(tenant_ref, "tenant_ref")
        payload = {
            "schema_version": RUNTIME_COMPOSITION_SCHEMA_VERSION,
            "lifecycle_owner_id": owner_id,
            "lifecycle_owner_version": owner_version,
            "storage_root": str(root),
            "tenant_ref": tenant,
            "no_runtime_authority": True,
        }
        return cls(
            configuration_id=_digest(payload),
            lifecycle_owner_id=owner_id,
            lifecycle_owner_version=owner_version,
            storage_root=root,
            tenant_ref=tenant,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "lifecycle_owner_id": self.lifecycle_owner_id,
            "lifecycle_owner_version": self.lifecycle_owner_version,
            "storage_root": str(self.storage_root),
            "tenant_ref": self.tenant_ref,
            "no_runtime_authority": self.no_runtime_authority,
        }

    def database_path(self) -> Path:
        """Derive the internal SQLite location; callers never supply a DB path."""

        return self.storage_root / (
            f"continuity-admission-{self.configuration_id[:24]}.sqlite3"
        )


def load_continuity_runtime_configuration(
    environ: Mapping[str, str] | None = None,
) -> ContinuityRuntimeConfiguration | None:
    """Load one all-or-nothing deployment selection; no fields means no owner."""

    source = os.environ if environ is None else environ
    values = {field: source.get(field, "").strip() for field in _RUNTIME_ENV_FIELDS}
    present = {field for field, value in values.items() if value}
    if not present:
        return None
    if present != set(_RUNTIME_ENV_FIELDS):
        missing = sorted(set(_RUNTIME_ENV_FIELDS) - present)
        raise ContinuityRuntimeConfigurationError(
            "partial Continuity runtime configuration; missing: "
            + ", ".join(missing)
        )
    return ContinuityRuntimeConfiguration.create(
        lifecycle_owner_id=values[ENV_RUNTIME_OWNER_ID],
        lifecycle_owner_version=values[ENV_RUNTIME_OWNER_VERSION],
        storage_root=values[ENV_RUNTIME_STORAGE_ROOT],
        tenant_ref=values[ENV_RUNTIME_TENANT_REF],
    )


@dataclass(frozen=True, slots=True)
class ContinuityAcceptedAdmissionGraph:
    """Complete facade-bound accepted graph.

    Raw evaluator results and caller-built artifacts are intentionally excluded.
    """

    principal_context: ContinuityPrincipalContext
    authorization_context: ContinuityAuthorizationContext
    source_envelope: ContinuitySourceEnvelope
    binding_receipt: ContinuitySourceBindingReceipt
    drafts: tuple[ContinuityObservationDraft, ...]
    owner_snapshots: tuple[ContinuityCurrentDecisionOwnerSnapshot, ...]
    current_decision_evidence: ContinuityCurrentDecisionEvidence
    registry: ContinuityAdmissionRegistry
    facade_policy: ContinuityAdmissionFacadePolicy
    facade_result: ContinuityAdmissionFacadeResult
    retention_policy: ContinuityRetentionPolicy
    recorded_at: datetime
    no_runtime_authority: bool = True

    def __post_init__(self) -> None:
        exact_types = (
            (self.principal_context, ContinuityPrincipalContext, "principal_context"),
            (
                self.authorization_context,
                ContinuityAuthorizationContext,
                "authorization_context",
            ),
            (self.source_envelope, ContinuitySourceEnvelope, "source_envelope"),
            (
                self.binding_receipt,
                ContinuitySourceBindingReceipt,
                "binding_receipt",
            ),
            (
                self.current_decision_evidence,
                ContinuityCurrentDecisionEvidence,
                "current_decision_evidence",
            ),
            (self.registry, ContinuityAdmissionRegistry, "registry"),
            (
                self.facade_policy,
                ContinuityAdmissionFacadePolicy,
                "facade_policy",
            ),
            (
                self.facade_result,
                ContinuityAdmissionFacadeResult,
                "facade_result",
            ),
            (
                self.retention_policy,
                ContinuityRetentionPolicy,
                "retention_policy",
            ),
        )
        for value, expected, name in exact_types:
            if not isinstance(value, expected):
                raise ContinuityRuntimeCompositionError(f"{name} is malformed")
        drafts = tuple(self.drafts)
        snapshots = tuple(self.owner_snapshots)
        if not drafts or any(
            not isinstance(value, ContinuityObservationDraft) for value in drafts
        ):
            raise ContinuityRuntimeCompositionError(
                "completed accepted graph requires typed Draft evidence"
            )
        if any(
            not isinstance(value, ContinuityCurrentDecisionOwnerSnapshot)
            for value in snapshots
        ):
            raise ContinuityRuntimeCompositionError(
                "completed accepted graph requires typed owner snapshots"
            )
        object.__setattr__(self, "drafts", drafts)
        object.__setattr__(self, "owner_snapshots", snapshots)
        if (
            not isinstance(self.recorded_at, datetime)
            or self.recorded_at.tzinfo is None
        ):
            raise ContinuityRuntimeCompositionError(
                "recorded_at must be timezone-aware"
            )
        if self.no_runtime_authority is not True:
            raise ContinuityRuntimeCompositionError(
                "accepted graph cannot grant runtime authority"
            )
        if self.facade_result.no_runtime_authority is not True:
            raise ContinuityRuntimeCompositionError(
                "facade result cannot grant runtime authority"
            )
        if not self.facade_result.evaluation.admitted_draft_ids:
            raise ContinuityRuntimeCompositionError(
                "facade result must contain accepted Draft evidence"
            )


@dataclass(frozen=True, slots=True)
class ContinuityRuntimeAppendEvidence:
    configuration_id: str
    lifecycle_owner_id: str
    lifecycle_owner_version: str
    artifact_id: str
    append_receipt_id: str
    no_runtime_authority: bool = True


@dataclass(frozen=True, slots=True)
class ContinuityRuntimeDiagnosticEvidence:
    configuration_id: str
    lifecycle_owner_id: str
    lifecycle_owner_version: str
    state: ContinuityRuntimeState
    storage_location_id: str
    no_runtime_authority: bool = True


class ContinuityRuntimeCompositionOwner:
    """Single bounded owner for internal startup, append and exact-scope replay."""

    def __init__(self, configuration: ContinuityRuntimeConfiguration) -> None:
        if not isinstance(configuration, ContinuityRuntimeConfiguration):
            raise ContinuityRuntimeConfigurationError(
                "configuration must be ContinuityRuntimeConfiguration"
            )
        self._configuration = configuration
        self._pinned_configuration_id = configuration.configuration_id
        self._state = ContinuityRuntimeState.NEW
        self._store: ContinuityArtifactStore | None = None
        self._lock = RLock()

    @property
    def state(self) -> ContinuityRuntimeState:
        with self._lock:
            return self._state

    @property
    def configuration_id(self) -> str:
        return self._pinned_configuration_id

    def startup(self) -> ContinuityRuntimeDiagnosticEvidence:
        """Initialize exactly one logical SQLite lifecycle instance."""

        with self._lock:
            self._assert_configuration()
            if self._state is ContinuityRuntimeState.STARTED:
                return self._diagnostic()
            previous_state = self._state
            candidate = ContinuityArtifactStore(self._configuration.database_path())
            try:
                candidate.ensure_schema()
                _verify_selected_schema(self._configuration.database_path())
            except Exception:
                self._store = None
                self._state = previous_state
                raise
            self._store = candidate
            self._state = ContinuityRuntimeState.STARTED
            return self._diagnostic()

    def shutdown(self) -> ContinuityRuntimeDiagnosticEvidence:
        """Release the logical owner.

        The selected lifecycle store holds no persistent connection between calls.
        """

        with self._lock:
            self._assert_configuration()
            self._store = None
            self._state = ContinuityRuntimeState.STOPPED
            return self._diagnostic()

    def persist_accepted_admission(
        self,
        graph: ContinuityAcceptedAdmissionGraph,
        *,
        appended_at: datetime,
    ) -> ContinuityRuntimeAppendEvidence:
        """Persist one complete accepted graph through the selected lifecycle only."""

        if not isinstance(graph, ContinuityAcceptedAdmissionGraph):
            raise ContinuityRuntimeCompositionError(
                "runtime persistence requires a complete facade-bound accepted graph"
            )
        with self._lock:
            store = self._started_store()
            if graph.authorization_context.tenant_ref != self._configuration.tenant_ref:
                raise ContinuityRuntimeCompositionError(
                    "accepted graph tenant does not match deployment configuration"
                )
            artifact = ContinuityAdmissionArtifact.create(
                principal_context=graph.principal_context,
                authorization_context=graph.authorization_context,
                source_envelope=graph.source_envelope,
                binding_receipt=graph.binding_receipt,
                drafts=graph.drafts,
                owner_snapshots=graph.owner_snapshots,
                current_decision_evidence=graph.current_decision_evidence,
                registry=graph.registry,
                facade_policy=graph.facade_policy,
                facade_result=graph.facade_result,
                retention_policy=graph.retention_policy,
                recorded_at=graph.recorded_at,
            )
            append_receipt_id = store.append(artifact, appended_at=appended_at)
            return ContinuityRuntimeAppendEvidence(
                configuration_id=self._pinned_configuration_id,
                lifecycle_owner_id=self._configuration.lifecycle_owner_id,
                lifecycle_owner_version=(
                    self._configuration.lifecycle_owner_version
                ),
                artifact_id=artifact.artifact_id,
                append_receipt_id=append_receipt_id,
            )

    def replay(
        self,
        artifact_id: str,
        *,
        scope: ContinuityArtifactScope,
        replayed_at: datetime,
    ) -> ContinuityAdmissionArtifact:
        """Perform explicit deterministic replay; replay is evidence, not permission."""

        if not isinstance(scope, ContinuityArtifactScope):
            raise ContinuityRuntimeCompositionError(
                "replay requires an exact ContinuityArtifactScope"
            )
        with self._lock:
            store = self._started_store()
            if scope.tenant_ref != self._configuration.tenant_ref:
                raise ContinuityRuntimeCompositionError(
                    "replay tenant does not match deployment configuration"
                )
            artifact = store.replay(
                artifact_id,
                scope=scope,
                replayed_at=replayed_at,
            )
            if artifact.tenant_ref != self._configuration.tenant_ref:
                raise ContinuityRuntimeCompositionError(
                    "replayed artifact escaped deployment tenant binding"
                )
            return artifact

    def _started_store(self) -> ContinuityArtifactStore:
        self._assert_configuration()
        if self._state is not ContinuityRuntimeState.STARTED or self._store is None:
            raise ContinuityRuntimeStateError(
                "Continuity runtime composition owner is not started"
            )
        return self._store

    def _assert_configuration(self) -> None:
        current = _digest(self._configuration.identity_payload())
        if (
            self._configuration.configuration_id
            != self._pinned_configuration_id
            or current != self._pinned_configuration_id
        ):
            raise ContinuityRuntimeConfigurationError(
                "runtime configuration was substituted after composition"
            )
        if self._configuration.lifecycle_owner_id != SUPPORTED_LIFECYCLE_OWNER_ID:
            raise ContinuityRuntimeConfigurationError(
                "lifecycle owner identity was substituted"
            )
        if (
            self._configuration.lifecycle_owner_version
            != SUPPORTED_LIFECYCLE_OWNER_VERSION
        ):
            raise ContinuityRuntimeConfigurationError(
                "lifecycle owner version was substituted"
            )

    def _diagnostic(self) -> ContinuityRuntimeDiagnosticEvidence:
        location_id = sha256(
            str(self._configuration.database_path()).encode("utf-8")
        ).hexdigest()
        return ContinuityRuntimeDiagnosticEvidence(
            configuration_id=self._pinned_configuration_id,
            lifecycle_owner_id=self._configuration.lifecycle_owner_id,
            lifecycle_owner_version=self._configuration.lifecycle_owner_version,
            state=self._state,
            storage_location_id=location_id,
        )


def compose_continuity_runtime_from_environment(
    environ: Mapping[str, str] | None = None,
) -> ContinuityRuntimeCompositionOwner | None:
    """Create the selected owner only when complete deployment config exists."""

    configuration = load_continuity_runtime_configuration(environ)
    if configuration is None:
        return None
    return ContinuityRuntimeCompositionOwner(configuration)


__all__ = [
    "ContinuityAcceptedAdmissionGraph",
    "ContinuityRuntimeAppendEvidence",
    "ContinuityRuntimeCompositionError",
    "ContinuityRuntimeCompositionOwner",
    "ContinuityRuntimeConfiguration",
    "ContinuityRuntimeConfigurationError",
    "ContinuityRuntimeDiagnosticEvidence",
    "ContinuityRuntimeState",
    "ContinuityRuntimeStateError",
    "compose_continuity_runtime_from_environment",
    "load_continuity_runtime_configuration",
]
