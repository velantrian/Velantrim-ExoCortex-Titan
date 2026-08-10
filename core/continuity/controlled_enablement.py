"""Controlled enablement for the bounded internal Continuity runtime.

This module validates one explicit deployment-owned operator decision, binds it to the
already-selected runtime composition, persists deterministic decision evidence in the
same tenant-bound SQLite database, and gates only the existing explicit append/replay
surface. It never invokes a producer, changes public API behavior, or grants runtime
authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
import json
import os
import sqlite3
from threading import RLock
from typing import Any

from .admission_artifact_lifecycle import (
    ContinuityAdmissionArtifact,
    ContinuityArtifactScope,
)
from .runtime_composition import (
    SUPPORTED_LIFECYCLE_OWNER_ID,
    SUPPORTED_LIFECYCLE_OWNER_VERSION,
    ContinuityAcceptedAdmissionGraph,
    ContinuityRuntimeAppendEvidence,
    ContinuityRuntimeCompositionError,
    ContinuityRuntimeCompositionOwner,
    ContinuityRuntimeConfiguration,
    ContinuityRuntimeState,
    load_continuity_runtime_configuration,
)

CONTROLLED_ENABLEMENT_SCHEMA_VERSION = "continuity.controlled_enablement.v1"
CONTROLLED_ENABLEMENT_SCOPE = "continuity.internal.artifact_persistence_replay"

ENV_ACTIVATION_MANIFEST = "VELANTRIM_CONTINUITY_ACTIVATION_MANIFEST"
ENV_ACTIVATION_MANIFEST_SHA256 = "VELANTRIM_CONTINUITY_ACTIVATION_MANIFEST_SHA256"
_ACTIVATION_ENV_FIELDS = (
    ENV_ACTIVATION_MANIFEST,
    ENV_ACTIVATION_MANIFEST_SHA256,
)

_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "action",
        "decision_sequence",
        "operator_ref",
        "configuration_id",
        "lifecycle_owner_id",
        "lifecycle_owner_version",
        "tenant_ref",
        "storage_location_id",
        "scope",
        "issued_at",
        "effective_at",
        "expires_at",
        "no_runtime_authority",
        "no_side_effect_authority",
    }
)

_ACTIVATION_TABLE = "continuity_runtime_activation_decisions"
_EXPECTED_ACTIVATION_COLUMNS = (
    "decision_id",
    "schema_version",
    "decision_sequence",
    "action",
    "operator_ref",
    "configuration_id",
    "lifecycle_owner_id",
    "lifecycle_owner_version",
    "tenant_ref",
    "storage_location_id",
    "scope",
    "issued_at",
    "effective_at",
    "expires_at",
    "manifest_json",
    "manifest_sha256",
    "no_runtime_authority",
    "no_side_effect_authority",
    "applied_at",
)


class ContinuityControlledEnablementError(ContinuityRuntimeCompositionError):
    """Base failure for controlled enablement."""


class ContinuityActivationConfigurationError(ContinuityControlledEnablementError):
    """Raised when the deployment-owned activation contract is malformed."""


class ContinuityActivationStateError(ContinuityControlledEnablementError):
    """Raised when activation is attempted in an invalid lifecycle state."""


class ContinuityActivationConflictError(ContinuityControlledEnablementError):
    """Raised for stale or conflicting monotonic decisions."""


class ContinuityEnablementState(str, Enum):
    NEW = "new"
    DISABLED = "disabled"
    ENABLED = "enabled"
    STOPPED = "stopped"


class ContinuityActivationAction(str, Enum):
    ENABLE = "enable"
    DISABLE = "disable"


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ContinuityActivationConfigurationError(
            "activation manifest must be canonical JSON"
        ) from exc


def _digest_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ContinuityActivationConfigurationError(
            f"{name} must be a non-empty canonical string"
        )
    return value


def _positive_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ContinuityActivationConfigurationError(
            f"{name} must be a positive integer"
        )
    return value


def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ContinuityActivationConfigurationError(
            f"{name} must be a timezone-aware datetime"
        )
    normalized = value.astimezone(UTC)
    if normalized.utcoffset() is None:
        raise ContinuityActivationConfigurationError(
            f"{name} must be a timezone-aware datetime"
        )
    return normalized


def _format_timestamp(value: datetime) -> str:
    return _aware_utc(value, "timestamp").isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: object, name: str) -> datetime:
    text = _text(value, name)
    if not text.endswith("Z"):
        raise ContinuityActivationConfigurationError(
            f"{name} must use canonical UTC Z notation"
        )
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise ContinuityActivationConfigurationError(
            f"{name} must be a valid UTC timestamp"
        ) from exc
    if _format_timestamp(parsed) != text:
        raise ContinuityActivationConfigurationError(
            f"{name} must use canonical UTC timestamp formatting"
        )
    return parsed


def _storage_location_id(configuration: ContinuityRuntimeConfiguration) -> str:
    return _digest_text(str(configuration.database_path()))


@dataclass(frozen=True, slots=True)
class ContinuityActivationDecision:
    """One explicit, bounded operator-controlled activation decision."""

    decision_id: str
    schema_version: str
    action: ContinuityActivationAction
    decision_sequence: int
    operator_ref: str
    configuration_id: str
    lifecycle_owner_id: str
    lifecycle_owner_version: str
    tenant_ref: str
    storage_location_id: str
    scope: str
    issued_at: datetime
    effective_at: datetime
    expires_at: datetime | None
    no_runtime_authority: bool = True
    no_side_effect_authority: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != CONTROLLED_ENABLEMENT_SCHEMA_VERSION:
            raise ContinuityActivationConfigurationError(
                "activation schema version is unsupported"
            )
        if not isinstance(self.action, ContinuityActivationAction):
            raise ContinuityActivationConfigurationError(
                "activation action is unsupported"
            )
        _positive_int(self.decision_sequence, "decision_sequence")
        for value, name in (
            (self.operator_ref, "operator_ref"),
            (self.configuration_id, "configuration_id"),
            (self.lifecycle_owner_id, "lifecycle_owner_id"),
            (self.lifecycle_owner_version, "lifecycle_owner_version"),
            (self.tenant_ref, "tenant_ref"),
            (self.storage_location_id, "storage_location_id"),
            (self.scope, "scope"),
        ):
            _text(value, name)
        if self.scope != CONTROLLED_ENABLEMENT_SCOPE:
            raise ContinuityActivationConfigurationError(
                "activation scope is unsupported"
            )
        if self.lifecycle_owner_id != SUPPORTED_LIFECYCLE_OWNER_ID:
            raise ContinuityActivationConfigurationError(
                "activation lifecycle owner ID is unsupported"
            )
        if self.lifecycle_owner_version != SUPPORTED_LIFECYCLE_OWNER_VERSION:
            raise ContinuityActivationConfigurationError(
                "activation lifecycle owner version is unsupported"
            )
        issued_at = _aware_utc(self.issued_at, "issued_at")
        effective_at = _aware_utc(self.effective_at, "effective_at")
        expires_at = (
            None
            if self.expires_at is None
            else _aware_utc(self.expires_at, "expires_at")
        )
        object.__setattr__(self, "issued_at", issued_at)
        object.__setattr__(self, "effective_at", effective_at)
        object.__setattr__(self, "expires_at", expires_at)
        if effective_at < issued_at:
            raise ContinuityActivationConfigurationError(
                "effective_at cannot precede issued_at"
            )
        if self.action is ContinuityActivationAction.ENABLE:
            if expires_at is None or expires_at <= effective_at:
                raise ContinuityActivationConfigurationError(
                    "enable decision requires a bounded expiry after effective_at"
                )
        elif expires_at is not None:
            raise ContinuityActivationConfigurationError(
                "disable decision must not contain expires_at"
            )
        if self.no_runtime_authority is not True:
            raise ContinuityActivationConfigurationError(
                "activation decision cannot grant runtime authority"
            )
        if self.no_side_effect_authority is not True:
            raise ContinuityActivationConfigurationError(
                "activation decision cannot grant side-effect authority"
            )
        expected = _digest_text(_canonical_json(self.manifest_payload()))
        if self.decision_id != expected:
            raise ContinuityActivationConfigurationError(
                "activation decision digest mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        action: ContinuityActivationAction | str,
        decision_sequence: int,
        operator_ref: str,
        configuration: ContinuityRuntimeConfiguration,
        issued_at: datetime,
        effective_at: datetime,
        expires_at: datetime | None,
    ) -> ContinuityActivationDecision:
        if not isinstance(configuration, ContinuityRuntimeConfiguration):
            raise ContinuityActivationConfigurationError(
                "activation requires ContinuityRuntimeConfiguration"
            )
        try:
            normalized_action = ContinuityActivationAction(action)
        except (TypeError, ValueError) as exc:
            raise ContinuityActivationConfigurationError(
                "activation action is unsupported"
            ) from exc
        payload: dict[str, object] = {
            "schema_version": CONTROLLED_ENABLEMENT_SCHEMA_VERSION,
            "action": normalized_action.value,
            "decision_sequence": decision_sequence,
            "operator_ref": operator_ref,
            "configuration_id": configuration.configuration_id,
            "lifecycle_owner_id": configuration.lifecycle_owner_id,
            "lifecycle_owner_version": configuration.lifecycle_owner_version,
            "tenant_ref": configuration.tenant_ref,
            "storage_location_id": _storage_location_id(configuration),
            "scope": CONTROLLED_ENABLEMENT_SCOPE,
            "issued_at": _format_timestamp(issued_at),
            "effective_at": _format_timestamp(effective_at),
            "expires_at": (
                None if expires_at is None else _format_timestamp(expires_at)
            ),
            "no_runtime_authority": True,
            "no_side_effect_authority": True,
        }
        canonical = _canonical_json(payload)
        return cls.from_manifest(
            canonical,
            _digest_text(canonical),
        )

    @classmethod
    def from_manifest(
        cls,
        manifest_json: str,
        manifest_sha256: str,
    ) -> ContinuityActivationDecision:
        manifest = _text(manifest_json, "activation manifest")
        digest = _text(manifest_sha256, "activation manifest SHA-256")
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ContinuityActivationConfigurationError(
                "activation manifest SHA-256 must be lowercase hexadecimal"
            )
        try:
            value = json.loads(manifest)
        except (TypeError, ValueError) as exc:
            raise ContinuityActivationConfigurationError(
                "activation manifest is malformed JSON"
            ) from exc
        if not isinstance(value, dict):
            raise ContinuityActivationConfigurationError(
                "activation manifest must be a JSON object"
            )
        if set(value) != _MANIFEST_FIELDS:
            unknown = sorted(set(value) - _MANIFEST_FIELDS)
            missing = sorted(_MANIFEST_FIELDS - set(value))
            details: list[str] = []
            if unknown:
                details.append("unknown: " + ", ".join(unknown))
            if missing:
                details.append("missing: " + ", ".join(missing))
            raise ContinuityActivationConfigurationError(
                "activation manifest fields are invalid"
                + (": " + "; ".join(details) if details else "")
            )
        canonical = _canonical_json(value)
        if manifest != canonical:
            raise ContinuityActivationConfigurationError(
                "activation manifest must use exact canonical JSON"
            )
        if _digest_text(canonical) != digest:
            raise ContinuityActivationConfigurationError(
                "activation manifest digest mismatch"
            )
        try:
            action = ContinuityActivationAction(value["action"])
        except (TypeError, ValueError) as exc:
            raise ContinuityActivationConfigurationError(
                "activation action is unsupported"
            ) from exc
        expires_raw = value["expires_at"]
        expires_at = (
            None
            if expires_raw is None
            else _parse_timestamp(expires_raw, "expires_at")
        )
        return cls(
            decision_id=digest,
            schema_version=_text(value["schema_version"], "schema_version"),
            action=action,
            decision_sequence=_positive_int(
                value["decision_sequence"], "decision_sequence"
            ),
            operator_ref=_text(value["operator_ref"], "operator_ref"),
            configuration_id=_text(
                value["configuration_id"], "configuration_id"
            ),
            lifecycle_owner_id=_text(
                value["lifecycle_owner_id"], "lifecycle_owner_id"
            ),
            lifecycle_owner_version=_text(
                value["lifecycle_owner_version"], "lifecycle_owner_version"
            ),
            tenant_ref=_text(value["tenant_ref"], "tenant_ref"),
            storage_location_id=_text(
                value["storage_location_id"], "storage_location_id"
            ),
            scope=_text(value["scope"], "scope"),
            issued_at=_parse_timestamp(value["issued_at"], "issued_at"),
            effective_at=_parse_timestamp(value["effective_at"], "effective_at"),
            expires_at=expires_at,
            no_runtime_authority=value["no_runtime_authority"],
            no_side_effect_authority=value["no_side_effect_authority"],
        )

    def manifest_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "action": self.action.value,
            "decision_sequence": self.decision_sequence,
            "operator_ref": self.operator_ref,
            "configuration_id": self.configuration_id,
            "lifecycle_owner_id": self.lifecycle_owner_id,
            "lifecycle_owner_version": self.lifecycle_owner_version,
            "tenant_ref": self.tenant_ref,
            "storage_location_id": self.storage_location_id,
            "scope": self.scope,
            "issued_at": _format_timestamp(self.issued_at),
            "effective_at": _format_timestamp(self.effective_at),
            "expires_at": (
                None
                if self.expires_at is None
                else _format_timestamp(self.expires_at)
            ),
            "no_runtime_authority": self.no_runtime_authority,
            "no_side_effect_authority": self.no_side_effect_authority,
        }

    def canonical_manifest(self) -> str:
        return _canonical_json(self.manifest_payload())

    def validate_binding(
        self,
        configuration: ContinuityRuntimeConfiguration,
    ) -> None:
        expected = {
            "configuration_id": configuration.configuration_id,
            "lifecycle_owner_id": configuration.lifecycle_owner_id,
            "lifecycle_owner_version": configuration.lifecycle_owner_version,
            "tenant_ref": configuration.tenant_ref,
            "storage_location_id": _storage_location_id(configuration),
        }
        actual = {
            "configuration_id": self.configuration_id,
            "lifecycle_owner_id": self.lifecycle_owner_id,
            "lifecycle_owner_version": self.lifecycle_owner_version,
            "tenant_ref": self.tenant_ref,
            "storage_location_id": self.storage_location_id,
        }
        if actual != expected:
            raise ContinuityActivationConfigurationError(
                "activation decision does not match runtime composition binding"
            )

    def validate_at(self, evaluated_at: datetime) -> None:
        moment = _aware_utc(evaluated_at, "evaluated_at")
        if moment < self.effective_at:
            raise ContinuityActivationConfigurationError(
                "activation decision is not yet effective"
            )
        if (
            self.action is ContinuityActivationAction.ENABLE
            and self.expires_at is not None
            and moment >= self.expires_at
        ):
            raise ContinuityActivationConfigurationError(
                "activation lease is expired"
            )


@dataclass(frozen=True, slots=True)
class ContinuityEnablementDiagnosticEvidence:
    configuration_id: str
    lifecycle_owner_id: str
    lifecycle_owner_version: str
    state: ContinuityEnablementState
    storage_location_id: str
    applied_decision_id: str | None
    applied_decision_sequence: int | None
    operator_enable_decision_present: bool
    enablement_mechanism_implemented: bool = True
    observed: bool = False
    runtime_authority: bool = False
    side_effect_authority: bool = False


class ContinuityControlledEnablementController:
    """Gate the existing internal append/replay owner behind one exact decision."""

    def __init__(
        self,
        *,
        configuration: ContinuityRuntimeConfiguration,
        runtime_owner: ContinuityRuntimeCompositionOwner,
        configured_decision: ContinuityActivationDecision | None = None,
    ) -> None:
        if not isinstance(configuration, ContinuityRuntimeConfiguration):
            raise ContinuityActivationConfigurationError(
                "controller requires ContinuityRuntimeConfiguration"
            )
        if not isinstance(runtime_owner, ContinuityRuntimeCompositionOwner):
            raise ContinuityActivationConfigurationError(
                "controller requires ContinuityRuntimeCompositionOwner"
            )
        if runtime_owner.configuration_id != configuration.configuration_id:
            raise ContinuityActivationConfigurationError(
                "controller runtime owner binding mismatch"
            )
        if configured_decision is not None:
            configured_decision.validate_binding(configuration)
        self._configuration = configuration
        self._runtime_owner = runtime_owner
        self._configured_decision = configured_decision
        self._pinned_configuration_id = configuration.configuration_id
        self._pinned_configured_decision_id = (
            None if configured_decision is None else configured_decision.decision_id
        )
        self._state = ContinuityEnablementState.NEW
        self._applied_decision: ContinuityActivationDecision | None = None
        self._lock = RLock()

    @property
    def state(self) -> ContinuityEnablementState:
        with self._lock:
            return self._state

    @property
    def configuration_id(self) -> str:
        return self._pinned_configuration_id

    def startup(
        self,
        *,
        evaluated_at: datetime,
    ) -> ContinuityEnablementDiagnosticEvidence:
        moment = _aware_utc(evaluated_at, "evaluated_at")
        with self._lock:
            self._assert_configuration()
            if self._state in (
                ContinuityEnablementState.DISABLED,
                ContinuityEnablementState.ENABLED,
            ):
                return self._diagnostic()
            previous_state = self._state
            try:
                self._runtime_owner.startup()
                self._ensure_activation_schema()
                self._read_persisted_decisions()
                self._applied_decision = None
                self._state = ContinuityEnablementState.DISABLED
                if self._configured_decision is not None:
                    self._apply_decision_locked(
                        self._configured_decision,
                        evaluated_at=moment,
                    )
                return self._diagnostic()
            except Exception:
                self._applied_decision = None
                self._state = previous_state
                self._runtime_owner.shutdown()
                raise

    def shutdown(self) -> ContinuityEnablementDiagnosticEvidence:
        with self._lock:
            self._assert_configuration()
            self._applied_decision = None
            self._runtime_owner.shutdown()
            self._state = ContinuityEnablementState.STOPPED
            return self._diagnostic()

    def apply_decision(
        self,
        decision: ContinuityActivationDecision,
        *,
        evaluated_at: datetime,
    ) -> ContinuityEnablementDiagnosticEvidence:
        if not isinstance(decision, ContinuityActivationDecision):
            raise ContinuityActivationConfigurationError(
                "apply_decision requires ContinuityActivationDecision"
            )
        moment = _aware_utc(evaluated_at, "evaluated_at")
        with self._lock:
            if self._state not in (
                ContinuityEnablementState.DISABLED,
                ContinuityEnablementState.ENABLED,
            ) or self._runtime_owner.state is not ContinuityRuntimeState.STARTED:
                raise ContinuityActivationStateError(
                    "controlled enablement requires a started runtime owner"
                )
            self._apply_decision_locked(decision, evaluated_at=moment)
            return self._diagnostic()

    def persist_accepted_admission(
        self,
        graph: ContinuityAcceptedAdmissionGraph,
        *,
        appended_at: datetime,
        evaluated_at: datetime,
    ) -> ContinuityRuntimeAppendEvidence:
        moment = _aware_utc(evaluated_at, "evaluated_at")
        with self._lock:
            self._require_enabled(moment)
            return self._runtime_owner.persist_accepted_admission(
                graph,
                appended_at=appended_at,
            )

    def replay(
        self,
        artifact_id: str,
        *,
        scope: ContinuityArtifactScope,
        replayed_at: datetime,
    ) -> ContinuityAdmissionArtifact:
        moment = _aware_utc(replayed_at, "replayed_at")
        with self._lock:
            self._require_enabled(moment)
            return self._runtime_owner.replay(
                artifact_id,
                scope=scope,
                replayed_at=replayed_at,
            )

    def diagnostic(self) -> ContinuityEnablementDiagnosticEvidence:
        with self._lock:
            return self._diagnostic()

    def lease_valid_at(self, evaluated_at: datetime) -> bool:
        """Read-only check: does the currently applied decision remain valid now?

        This never mutates controller state and never gates access by itself; a
        caller must still go through ``persist_accepted_admission``/``replay``
        for authoritative fail-closed enforcement. It exists only so a
        content-free external observer (see ``bounded_observation.py``) can
        report lease validity without invoking a business operation.
        """

        moment = _aware_utc(evaluated_at, "evaluated_at")
        with self._lock:
            self._assert_configuration()
            if self._applied_decision is None:
                return False
            try:
                self._applied_decision.validate_at(moment)
            except ContinuityActivationConfigurationError:
                return False
            return True

    def _apply_decision_locked(
        self,
        decision: ContinuityActivationDecision,
        *,
        evaluated_at: datetime,
    ) -> None:
        self._assert_configuration()
        decision.validate_binding(self._configuration)
        decision.validate_at(evaluated_at)
        decisions = self._read_persisted_decisions()
        latest = decisions[-1] if decisions else None
        if latest is not None:
            if decision.decision_sequence < latest.decision_sequence:
                raise ContinuityActivationConflictError(
                    "activation decision sequence is stale"
                )
            if decision.decision_sequence == latest.decision_sequence:
                if decision.decision_id != latest.decision_id:
                    raise ContinuityActivationConflictError(
                        "activation decision sequence conflicts with persisted evidence"
                    )
                decision = latest
            else:
                self._insert_decision(decision, applied_at=evaluated_at)
        else:
            self._insert_decision(decision, applied_at=evaluated_at)
        self._applied_decision = decision
        self._state = (
            ContinuityEnablementState.ENABLED
            if decision.action is ContinuityActivationAction.ENABLE
            else ContinuityEnablementState.DISABLED
        )

    def _require_enabled(self, evaluated_at: datetime) -> None:
        if (
            self._state is not ContinuityEnablementState.ENABLED
            or self._runtime_owner.state is not ContinuityRuntimeState.STARTED
            or self._applied_decision is None
        ):
            raise ContinuityActivationStateError(
                "Continuity runtime is not currently enabled"
            )
        try:
            self._applied_decision.validate_at(evaluated_at)
        except ContinuityActivationConfigurationError as exc:
            self._applied_decision = None
            self._state = ContinuityEnablementState.DISABLED
            raise ContinuityActivationStateError(
                "Continuity activation lease is not currently valid"
            ) from exc
        decisions = self._read_persisted_decisions()
        latest = decisions[-1] if decisions else None
        if latest is None or latest.decision_id != self._applied_decision.decision_id:
            self._applied_decision = None
            self._state = ContinuityEnablementState.DISABLED
            raise ContinuityActivationStateError(
                "persisted activation evidence no longer matches enabled state"
            )

    def _assert_configuration(self) -> None:
        if self._configuration.configuration_id != self._pinned_configuration_id:
            raise ContinuityActivationConfigurationError(
                "runtime configuration was substituted after controller composition"
            )
        if self._runtime_owner.configuration_id != self._pinned_configuration_id:
            raise ContinuityActivationConfigurationError(
                "runtime owner was substituted after controller composition"
            )
        current_decision_id = (
            None
            if self._configured_decision is None
            else self._configured_decision.decision_id
        )
        if current_decision_id != self._pinned_configured_decision_id:
            raise ContinuityActivationConfigurationError(
                "configured activation decision was substituted"
            )
        if self._configured_decision is not None:
            expected = _digest_text(self._configured_decision.canonical_manifest())
            if expected != self._configured_decision.decision_id:
                raise ContinuityActivationConfigurationError(
                    "configured activation decision digest changed"
                )
            self._configured_decision.validate_binding(self._configuration)

    def _ensure_activation_schema(self) -> None:
        database_path = self._configuration.database_path()
        try:
            with sqlite3.connect(database_path) as connection:
                connection.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {_ACTIVATION_TABLE}(
                        decision_id TEXT PRIMARY KEY,
                        schema_version TEXT NOT NULL,
                        decision_sequence INTEGER NOT NULL UNIQUE,
                        action TEXT NOT NULL,
                        operator_ref TEXT NOT NULL,
                        configuration_id TEXT NOT NULL,
                        lifecycle_owner_id TEXT NOT NULL,
                        lifecycle_owner_version TEXT NOT NULL,
                        tenant_ref TEXT NOT NULL,
                        storage_location_id TEXT NOT NULL,
                        scope TEXT NOT NULL,
                        issued_at TEXT NOT NULL,
                        effective_at TEXT NOT NULL,
                        expires_at TEXT,
                        manifest_json TEXT NOT NULL,
                        manifest_sha256 TEXT NOT NULL,
                        no_runtime_authority INTEGER NOT NULL,
                        no_side_effect_authority INTEGER NOT NULL,
                        applied_at TEXT NOT NULL
                    )
                    """
                )
                rows = connection.execute(
                    f"PRAGMA table_info({_ACTIVATION_TABLE})"
                ).fetchall()
                actual = tuple(str(row[1]) for row in rows)
                if actual != _EXPECTED_ACTIVATION_COLUMNS:
                    raise ContinuityControlledEnablementError(
                        "controlled-enablement SQLite state is incompatible"
                    )
        except ContinuityControlledEnablementError:
            raise
        except sqlite3.Error as exc:
            raise ContinuityControlledEnablementError(
                "controlled-enablement SQLite initialization failed"
            ) from exc

    def _read_persisted_decisions(self) -> tuple[ContinuityActivationDecision, ...]:
        database_path = self._configuration.database_path()
        try:
            with sqlite3.connect(database_path) as connection:
                rows = connection.execute(
                    f"""
                    SELECT
                        decision_id,
                        schema_version,
                        decision_sequence,
                        action,
                        operator_ref,
                        configuration_id,
                        lifecycle_owner_id,
                        lifecycle_owner_version,
                        tenant_ref,
                        storage_location_id,
                        scope,
                        issued_at,
                        effective_at,
                        expires_at,
                        manifest_json,
                        manifest_sha256,
                        no_runtime_authority,
                        no_side_effect_authority,
                        applied_at
                    FROM {_ACTIVATION_TABLE}
                    ORDER BY decision_sequence, decision_id
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            raise ContinuityControlledEnablementError(
                "controlled-enablement SQLite read failed"
            ) from exc
        decisions: list[ContinuityActivationDecision] = []
        previous_sequence = 0
        for row in rows:
            decision = self._decision_from_row(row)
            if decision.decision_sequence <= previous_sequence:
                raise ContinuityControlledEnablementError(
                    "persisted activation sequence ordering is malformed"
                )
            previous_sequence = decision.decision_sequence
            decisions.append(decision)
        return tuple(decisions)

    def _decision_from_row(
        self,
        row: tuple[Any, ...],
    ) -> ContinuityActivationDecision:
        (
            decision_id,
            schema_version,
            decision_sequence,
            action,
            operator_ref,
            configuration_id,
            lifecycle_owner_id,
            lifecycle_owner_version,
            tenant_ref,
            storage_location_id,
            scope,
            issued_at,
            effective_at,
            expires_at,
            manifest_json,
            manifest_sha256,
            no_runtime_authority,
            no_side_effect_authority,
            applied_at,
        ) = row
        _parse_timestamp(applied_at, "persisted applied_at")
        if no_runtime_authority != 1 or no_side_effect_authority != 1:
            raise ContinuityControlledEnablementError(
                "persisted activation authority flags are malformed"
            )
        decision = ContinuityActivationDecision.from_manifest(
            manifest_json,
            manifest_sha256,
        )
        indexed = (
            decision.decision_id,
            decision.schema_version,
            decision.decision_sequence,
            decision.action.value,
            decision.operator_ref,
            decision.configuration_id,
            decision.lifecycle_owner_id,
            decision.lifecycle_owner_version,
            decision.tenant_ref,
            decision.storage_location_id,
            decision.scope,
            _format_timestamp(decision.issued_at),
            _format_timestamp(decision.effective_at),
            None
            if decision.expires_at is None
            else _format_timestamp(decision.expires_at),
        )
        stored = (
            decision_id,
            schema_version,
            decision_sequence,
            action,
            operator_ref,
            configuration_id,
            lifecycle_owner_id,
            lifecycle_owner_version,
            tenant_ref,
            storage_location_id,
            scope,
            issued_at,
            effective_at,
            expires_at,
        )
        if indexed != stored:
            raise ContinuityControlledEnablementError(
                "persisted activation indexed state is malformed"
            )
        decision.validate_binding(self._configuration)
        return decision

    def _insert_decision(
        self,
        decision: ContinuityActivationDecision,
        *,
        applied_at: datetime,
    ) -> None:
        manifest = decision.canonical_manifest()
        try:
            with sqlite3.connect(self._configuration.database_path()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    f"""
                    INSERT INTO {_ACTIVATION_TABLE}(
                        decision_id,
                        schema_version,
                        decision_sequence,
                        action,
                        operator_ref,
                        configuration_id,
                        lifecycle_owner_id,
                        lifecycle_owner_version,
                        tenant_ref,
                        storage_location_id,
                        scope,
                        issued_at,
                        effective_at,
                        expires_at,
                        manifest_json,
                        manifest_sha256,
                        no_runtime_authority,
                        no_side_effect_authority,
                        applied_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        decision.decision_id,
                        decision.schema_version,
                        decision.decision_sequence,
                        decision.action.value,
                        decision.operator_ref,
                        decision.configuration_id,
                        decision.lifecycle_owner_id,
                        decision.lifecycle_owner_version,
                        decision.tenant_ref,
                        decision.storage_location_id,
                        decision.scope,
                        _format_timestamp(decision.issued_at),
                        _format_timestamp(decision.effective_at),
                        None
                        if decision.expires_at is None
                        else _format_timestamp(decision.expires_at),
                        manifest,
                        decision.decision_id,
                        1,
                        1,
                        _format_timestamp(applied_at),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ContinuityActivationConflictError(
                "activation decision conflicts with persisted evidence"
            ) from exc
        except sqlite3.Error as exc:
            raise ContinuityControlledEnablementError(
                "controlled-enablement SQLite write failed"
            ) from exc

    def _diagnostic(self) -> ContinuityEnablementDiagnosticEvidence:
        decision = self._applied_decision
        return ContinuityEnablementDiagnosticEvidence(
            configuration_id=self._pinned_configuration_id,
            lifecycle_owner_id=self._configuration.lifecycle_owner_id,
            lifecycle_owner_version=self._configuration.lifecycle_owner_version,
            state=self._state,
            storage_location_id=_storage_location_id(self._configuration),
            applied_decision_id=None if decision is None else decision.decision_id,
            applied_decision_sequence=(
                None if decision is None else decision.decision_sequence
            ),
            operator_enable_decision_present=(
                decision is not None
                and decision.action is ContinuityActivationAction.ENABLE
                and self._state is ContinuityEnablementState.ENABLED
            ),
        )


def load_continuity_activation_decision(
    configuration: ContinuityRuntimeConfiguration,
    environ: Mapping[str, str] | None = None,
) -> ContinuityActivationDecision | None:
    """Load a strict all-or-nothing activation manifest from deployment input."""

    if not isinstance(configuration, ContinuityRuntimeConfiguration):
        raise ContinuityActivationConfigurationError(
            "activation loading requires ContinuityRuntimeConfiguration"
        )
    source = os.environ if environ is None else environ
    values = {field: source.get(field, "") for field in _ACTIVATION_ENV_FIELDS}
    present = {field for field, value in values.items() if value}
    if not present:
        return None
    if present != set(_ACTIVATION_ENV_FIELDS):
        missing = sorted(set(_ACTIVATION_ENV_FIELDS) - present)
        raise ContinuityActivationConfigurationError(
            "partial Continuity activation configuration; missing: "
            + ", ".join(missing)
        )
    decision = ContinuityActivationDecision.from_manifest(
        values[ENV_ACTIVATION_MANIFEST],
        values[ENV_ACTIVATION_MANIFEST_SHA256],
    )
    decision.validate_binding(configuration)
    return decision


def compose_controlled_continuity_runtime_from_environment(
    environ: Mapping[str, str] | None = None,
) -> ContinuityControlledEnablementController | None:
    """Compose one disabled-by-default controller around the existing runtime owner."""

    source = os.environ if environ is None else environ
    configuration = load_continuity_runtime_configuration(source)
    activation_present = any(source.get(field, "") for field in _ACTIVATION_ENV_FIELDS)
    if configuration is None:
        if activation_present:
            raise ContinuityActivationConfigurationError(
                "activation configuration requires complete runtime configuration"
            )
        return None
    decision = load_continuity_activation_decision(configuration, source)
    runtime_owner = ContinuityRuntimeCompositionOwner(configuration)
    return ContinuityControlledEnablementController(
        configuration=configuration,
        runtime_owner=runtime_owner,
        configured_decision=decision,
    )
