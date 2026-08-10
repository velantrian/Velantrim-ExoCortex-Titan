"""Bounded, content-free observation evidence for controlled Continuity enablement.

This module answers exactly one question: *given the controlled-enablement
boundary that already exists, can a deployment record deterministic evidence
that a bounded activation behaved as declared, without that evidence ever
becoming a permission, an Operator GO, or a runtime-authority grant?*

It wraps :class:`~core.continuity.controlled_enablement.
ContinuityControlledEnablementController` and reads only its public,
content-free diagnostic surface (state, applied-decision identifiers, lease
validity). It never calls ``persist_accepted_admission`` or ``replay``, never
constructs a second runtime owner or database path, and never issues, revokes
or evaluates an activation decision itself — that authority remains exactly
where the controlled-enablement boundary already put it.

Observation evidence records a fixed, structural invariant checklist (see
``_evaluate_invariants``) plus the observed lifecycle state, in one dedicated
append-only table inside the same tenant-bound SQLite database already
selected by runtime composition. Recording an observation has no side effect
on the enablement controller and grants nothing: ``no_new_authority_granted``
and ``evidence_is_not_permission`` are fixed ``True`` markers on every row, not
configurable claims.

Whether any *deployment* has ever actually produced real observation evidence
under a real operator-authorized bounded activation is a fact about that
deployment, not about this module. This module supplies the mechanism; it
does not supply Operator GO, and it does not by itself make ``observed=true``
a project fact.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
import json
import sqlite3
from threading import RLock
from typing import Any

from .controlled_enablement import (
    ContinuityControlledEnablementController,
    ContinuityControlledEnablementError,
    ContinuityEnablementDiagnosticEvidence,
    ContinuityEnablementState,
)
from .runtime_composition import ContinuityRuntimeConfiguration

BOUNDED_OBSERVATION_SCHEMA_VERSION = "continuity.bounded_observation.v1"

_OBSERVATION_TABLE = "continuity_bounded_observation_records"
_EXPECTED_OBSERVATION_COLUMNS = (
    "observation_id",
    "schema_version",
    "observation_sequence",
    "configuration_id",
    "lifecycle_owner_id",
    "lifecycle_owner_version",
    "storage_location_id",
    "observed_state",
    "applied_decision_id",
    "applied_decision_sequence",
    "lease_valid",
    "evidence_json",
    "evidence_sha256",
    "observed_at",
    "no_new_authority_granted",
    "evidence_is_not_permission",
    "recorded_at",
)


class ContinuityBoundedObservationError(ContinuityControlledEnablementError):
    """Base failure for bounded observation."""


class ContinuityObservationConfigurationError(ContinuityBoundedObservationError):
    """Raised when observation composition or evidence input is invalid."""


class ContinuityObservationStateError(ContinuityBoundedObservationError):
    """Raised when observation is attempted outside its own bounded lifecycle."""


class ContinuityObservationConflictError(ContinuityBoundedObservationError):
    """Raised for stale or conflicting monotonic observation sequences."""


class ContinuityObservationLifecycle(str, Enum):
    NEW = "new"
    READY = "ready"
    CLOSED = "closed"


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
        raise ContinuityObservationConfigurationError(
            "observation evidence must be canonical JSON"
        ) from exc


def _digest_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ContinuityObservationConfigurationError(
            f"{name} must be a non-empty canonical string"
        )
    return value


def _optional_text(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _text(value, name)


def _bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ContinuityObservationConfigurationError(f"{name} must be a bool")
    return value


def _positive_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ContinuityObservationConfigurationError(
            f"{name} must be a positive integer"
        )
    return value


def _optional_positive_int(value: object, name: str) -> int | None:
    if value is None:
        return None
    return _positive_int(value, name)


def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ContinuityObservationConfigurationError(
            f"{name} must be a timezone-aware datetime"
        )
    normalized = value.astimezone(UTC)
    if normalized.utcoffset() is None:
        raise ContinuityObservationConfigurationError(
            f"{name} must be a timezone-aware datetime"
        )
    return normalized


def _format_timestamp(value: datetime) -> str:
    return _aware_utc(value, "timestamp").isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: object, name: str) -> datetime:
    text = _text(value, name)
    if not text.endswith("Z"):
        raise ContinuityObservationConfigurationError(
            f"{name} must use canonical UTC Z notation"
        )
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise ContinuityObservationConfigurationError(
            f"{name} must be a valid UTC timestamp"
        ) from exc
    if _format_timestamp(parsed) != text:
        raise ContinuityObservationConfigurationError(
            f"{name} must use canonical UTC timestamp formatting"
        )
    return parsed


def _storage_location_id(configuration: ContinuityRuntimeConfiguration) -> str:
    # Deliberately duplicated from controlled_enablement.py/runtime_composition.py:
    # this module must not depend on their private helpers remaining identical.
    return _digest_text(str(configuration.database_path()))


_INVARIANT_NAMES = frozenset(
    {
        "configuration_binding_stable",
        "storage_location_unchanged",
        "single_lifecycle_owner",
        "decision_binding_consistent",
        "lease_valid_when_enabled",
        "runtime_authority_absent",
        "side_effect_authority_absent",
    }
)


@dataclass(frozen=True, slots=True)
class ContinuityBoundedObservationEvidence:
    """One immutable, content-free record of one bounded observation.

    Carries no admission-graph content, no producer output and no user data —
    only structural identifiers, a fixed invariant checklist, and a lifecycle
    state label. ``no_new_authority_granted`` and ``evidence_is_not_permission``
    are load-bearing fixed markers, not caller-supplied claims: construction
    fails unless both are exactly ``True``.
    """

    observation_id: str
    schema_version: str
    observation_sequence: int
    configuration_id: str
    lifecycle_owner_id: str
    lifecycle_owner_version: str
    storage_location_id: str
    observed_state: str
    applied_decision_id: str | None
    applied_decision_sequence: int | None
    lease_valid: bool
    invariants: tuple[tuple[str, bool], ...]
    observed_at: str
    no_new_authority_granted: bool = True
    evidence_is_not_permission: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        if self.schema_version != BOUNDED_OBSERVATION_SCHEMA_VERSION:
            raise ContinuityObservationConfigurationError(
                "observation schema version is unsupported"
            )
        _positive_int(self.observation_sequence, "observation_sequence")
        for value, name in (
            (self.configuration_id, "configuration_id"),
            (self.lifecycle_owner_id, "lifecycle_owner_id"),
            (self.lifecycle_owner_version, "lifecycle_owner_version"),
            (self.storage_location_id, "storage_location_id"),
        ):
            _text(value, name)
        try:
            observed_state = ContinuityEnablementState(self.observed_state)
        except ValueError as exc:
            raise ContinuityObservationConfigurationError(
                "observed_state is unsupported"
            ) from exc
        object.__setattr__(self, "observed_state", observed_state.value)
        object.__setattr__(
            self,
            "applied_decision_id",
            _optional_text(self.applied_decision_id, "applied_decision_id"),
        )
        object.__setattr__(
            self,
            "applied_decision_sequence",
            _optional_positive_int(
                self.applied_decision_sequence, "applied_decision_sequence"
            ),
        )
        if (self.applied_decision_id is None) != (
            self.applied_decision_sequence is None
        ):
            raise ContinuityObservationConfigurationError(
                "applied decision identifier and sequence must be both present or absent"
            )
        _bool(self.lease_valid, "lease_valid")
        if not isinstance(self.invariants, tuple) or not self.invariants:
            raise ContinuityObservationConfigurationError(
                "invariants must be a non-empty tuple"
            )
        names: set[str] = set()
        for entry in self.invariants:
            if (
                not isinstance(entry, tuple)
                or len(entry) != 2
                or not isinstance(entry[0], str)
                or not isinstance(entry[1], bool)
            ):
                raise ContinuityObservationConfigurationError(
                    "each invariant must be a (name, bool) pair"
                )
            name, _passed = entry
            if name not in _INVARIANT_NAMES:
                raise ContinuityObservationConfigurationError(
                    f"unknown invariant: {name}"
                )
            names.add(name)
        if names != _INVARIANT_NAMES:
            raise ContinuityObservationConfigurationError(
                "invariants must cover exactly the fixed invariant checklist"
            )
        if tuple(sorted(self.invariants)) != self.invariants:
            raise ContinuityObservationConfigurationError(
                "invariants must be stored in canonical sorted order"
            )
        _parse_timestamp(self.observed_at, "observed_at")
        if self.no_new_authority_granted is not True:
            raise ContinuityObservationConfigurationError(
                "observation evidence cannot grant new authority"
            )
        if self.evidence_is_not_permission is not True:
            raise ContinuityObservationConfigurationError(
                "observation evidence cannot become permission"
            )
        expected = _digest_text(_canonical_json(self.identity_payload()))
        if self.observation_id != expected:
            raise ContinuityObservationConfigurationError(
                "observation_id must match canonical observation content"
            )

    @classmethod
    def create(
        cls,
        *,
        observation_sequence: int,
        configuration: ContinuityRuntimeConfiguration,
        diagnostic: ContinuityEnablementDiagnosticEvidence,
        lease_valid: bool,
        invariants: Mapping[str, bool],
        observed_at: datetime,
    ) -> ContinuityBoundedObservationEvidence:
        if not isinstance(configuration, ContinuityRuntimeConfiguration):
            raise ContinuityObservationConfigurationError(
                "observation requires ContinuityRuntimeConfiguration"
            )
        if not isinstance(diagnostic, ContinuityEnablementDiagnosticEvidence):
            raise ContinuityObservationConfigurationError(
                "observation requires ContinuityEnablementDiagnosticEvidence"
            )
        sequence = _positive_int(observation_sequence, "observation_sequence")
        moment = _aware_utc(observed_at, "observed_at")
        sorted_invariants = tuple(sorted(dict(invariants).items()))
        payload = cls._identity_payload(
            schema_version=BOUNDED_OBSERVATION_SCHEMA_VERSION,
            observation_sequence=sequence,
            configuration_id=configuration.configuration_id,
            lifecycle_owner_id=configuration.lifecycle_owner_id,
            lifecycle_owner_version=configuration.lifecycle_owner_version,
            storage_location_id=_storage_location_id(configuration),
            observed_state=diagnostic.state.value,
            applied_decision_id=diagnostic.applied_decision_id,
            applied_decision_sequence=diagnostic.applied_decision_sequence,
            lease_valid=lease_valid,
            invariants=sorted_invariants,
            observed_at=_format_timestamp(moment),
        )
        return cls(
            observation_id=_digest_text(_canonical_json(payload)),
            schema_version=BOUNDED_OBSERVATION_SCHEMA_VERSION,
            observation_sequence=sequence,
            configuration_id=configuration.configuration_id,
            lifecycle_owner_id=configuration.lifecycle_owner_id,
            lifecycle_owner_version=configuration.lifecycle_owner_version,
            storage_location_id=_storage_location_id(configuration),
            observed_state=diagnostic.state.value,
            applied_decision_id=diagnostic.applied_decision_id,
            applied_decision_sequence=diagnostic.applied_decision_sequence,
            lease_valid=lease_valid,
            invariants=sorted_invariants,
            observed_at=_format_timestamp(moment),
        )

    @staticmethod
    def _identity_payload(
        *,
        schema_version: str,
        observation_sequence: int,
        configuration_id: str,
        lifecycle_owner_id: str,
        lifecycle_owner_version: str,
        storage_location_id: str,
        observed_state: str,
        applied_decision_id: str | None,
        applied_decision_sequence: int | None,
        lease_valid: bool,
        invariants: tuple[tuple[str, bool], ...],
        observed_at: str,
    ) -> dict[str, object]:
        return {
            "schema_version": schema_version,
            "observation_sequence": observation_sequence,
            "configuration_id": configuration_id,
            "lifecycle_owner_id": lifecycle_owner_id,
            "lifecycle_owner_version": lifecycle_owner_version,
            "storage_location_id": storage_location_id,
            "observed_state": observed_state,
            "applied_decision_id": applied_decision_id,
            "applied_decision_sequence": applied_decision_sequence,
            "lease_valid": lease_valid,
            "invariants": [list(entry) for entry in invariants],
            "observed_at": observed_at,
            "no_new_authority_granted": True,
            "evidence_is_not_permission": True,
        }

    def identity_payload(self) -> dict[str, object]:
        return self._identity_payload(
            schema_version=self.schema_version,
            observation_sequence=self.observation_sequence,
            configuration_id=self.configuration_id,
            lifecycle_owner_id=self.lifecycle_owner_id,
            lifecycle_owner_version=self.lifecycle_owner_version,
            storage_location_id=self.storage_location_id,
            observed_state=self.observed_state,
            applied_decision_id=self.applied_decision_id,
            applied_decision_sequence=self.applied_decision_sequence,
            lease_valid=self.lease_valid,
            invariants=self.invariants,
            observed_at=self.observed_at,
        )

    def canonical_evidence(self) -> str:
        return _canonical_json(self.identity_payload())

    def all_invariants_passed(self) -> bool:
        return all(passed for _name, passed in self.invariants)

    def to_dict(self) -> dict[str, object]:
        return {"observation_id": self.observation_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class ContinuityObservationSessionSummary:
    """Deterministic, content-free result of one bounded observation session."""

    configuration_id: str
    observation_count: int
    all_invariants_passed: bool
    saw_enabled: bool
    saw_disabled_after_enabled: bool
    no_configuration_drift: bool
    rollback_verified: bool


def summarize_observation_session(
    evidences: Sequence[ContinuityBoundedObservationEvidence],
) -> ContinuityObservationSessionSummary:
    """Reduce an ordered observation session to one deterministic result.

    This is pure and content-free: it only compares already-recorded evidence
    rows. It proves at most that a bounded session transitioned through
    ``ENABLED`` and back to ``DISABLED`` while bound to one unchanged
    configuration identity — it does not, by itself, establish Operator GO,
    production authority or a currently enabled deployment.
    """

    if not evidences:
        raise ContinuityObservationConfigurationError(
            "observation session summary requires at least one evidence record"
        )
    for entry in evidences:
        if not isinstance(entry, ContinuityBoundedObservationEvidence):
            raise ContinuityObservationConfigurationError(
                "observation session summary requires ContinuityBoundedObservationEvidence"
            )
    ordered = tuple(sorted(evidences, key=lambda item: item.observation_sequence))
    configuration_ids = {item.configuration_id for item in ordered}
    no_drift = len(configuration_ids) == 1
    all_passed = all(item.all_invariants_passed() for item in ordered)
    saw_enabled = False
    saw_disabled_after_enabled = False
    for item in ordered:
        if item.observed_state == ContinuityEnablementState.ENABLED.value:
            saw_enabled = True
        elif (
            saw_enabled
            and item.observed_state == ContinuityEnablementState.DISABLED.value
        ):
            saw_disabled_after_enabled = True
    rollback_verified = no_drift and saw_enabled and saw_disabled_after_enabled
    return ContinuityObservationSessionSummary(
        configuration_id=next(iter(configuration_ids)) if no_drift else "",
        observation_count=len(ordered),
        all_invariants_passed=all_passed,
        saw_enabled=saw_enabled,
        saw_disabled_after_enabled=saw_disabled_after_enabled,
        no_configuration_drift=no_drift,
        rollback_verified=rollback_verified,
    )


class ContinuityBoundedObservationController:
    """Read-only, content-free observer bound to one controlled-enablement controller.

    This controller owns no runtime, no storage path and no authority. It
    never calls ``persist_accepted_admission`` or ``replay``, and it never
    applies, revokes or evaluates an activation decision. Its only two effects
    are: reading the enablement controller's public diagnostic surface, and
    appending one deterministic evidence row per bounded observation into a
    dedicated table inside the already-selected tenant-bound SQLite database.
    """

    def __init__(
        self,
        *,
        configuration: ContinuityRuntimeConfiguration,
        enablement_controller: ContinuityControlledEnablementController,
    ) -> None:
        if not isinstance(configuration, ContinuityRuntimeConfiguration):
            raise ContinuityObservationConfigurationError(
                "observation controller requires ContinuityRuntimeConfiguration"
            )
        if not isinstance(
            enablement_controller, ContinuityControlledEnablementController
        ):
            raise ContinuityObservationConfigurationError(
                "observation controller requires"
                " ContinuityControlledEnablementController"
            )
        if enablement_controller.configuration_id != configuration.configuration_id:
            raise ContinuityObservationConfigurationError(
                "observation controller binding mismatch"
            )
        self._configuration = configuration
        self._enablement_controller = enablement_controller
        self._pinned_configuration_id = configuration.configuration_id
        self._lifecycle = ContinuityObservationLifecycle.NEW
        self._lock = RLock()

    @property
    def lifecycle(self) -> ContinuityObservationLifecycle:
        with self._lock:
            return self._lifecycle

    @property
    def configuration_id(self) -> str:
        return self._pinned_configuration_id

    def open(self) -> None:
        """Ensure the dedicated observation-evidence table exists; idempotent."""

        with self._lock:
            self._assert_binding()
            if self._lifecycle is ContinuityObservationLifecycle.READY:
                return
            if self._lifecycle is ContinuityObservationLifecycle.CLOSED:
                raise ContinuityObservationStateError(
                    "bounded observation controller was already closed"
                )
            self._ensure_observation_schema()
            self._lifecycle = ContinuityObservationLifecycle.READY

    def close(self) -> ContinuityObservationLifecycle:
        with self._lock:
            self._lifecycle = ContinuityObservationLifecycle.CLOSED
            return self._lifecycle

    def observe(
        self,
        *,
        observation_sequence: int,
        observed_at: datetime,
    ) -> ContinuityBoundedObservationEvidence:
        """Record one deterministic, content-free observation.

        Idempotent for a repeated ``observation_sequence`` with identical
        content; fails closed on a stale or conflicting sequence.
        """

        with self._lock:
            if self._lifecycle is not ContinuityObservationLifecycle.READY:
                raise ContinuityObservationStateError(
                    "bounded observation controller is not open"
                )
            self._assert_binding()
            moment = _aware_utc(observed_at, "observed_at")
            sequence = _positive_int(observation_sequence, "observation_sequence")
            diagnostic = self._enablement_controller.diagnostic()
            self._assert_binding(diagnostic)
            if diagnostic.state in (
                ContinuityEnablementState.NEW,
                ContinuityEnablementState.STOPPED,
            ):
                raise ContinuityObservationStateError(
                    "cannot observe a Continuity runtime that has not started"
                    " or has already shut down"
                )
            lease_valid = (
                self._enablement_controller.lease_valid_at(moment)
                if diagnostic.applied_decision_id is not None
                else False
            )
            invariants = self._evaluate_invariants(diagnostic, lease_valid)
            candidate = ContinuityBoundedObservationEvidence.create(
                observation_sequence=sequence,
                configuration=self._configuration,
                diagnostic=diagnostic,
                lease_valid=lease_valid,
                invariants=invariants,
                observed_at=moment,
            )
            records = self._read_persisted_records()
            latest = records[-1] if records else None
            if latest is not None:
                if sequence < latest.observation_sequence:
                    raise ContinuityObservationConflictError(
                        "observation sequence is stale"
                    )
                if sequence == latest.observation_sequence:
                    if candidate.observation_id != latest.observation_id:
                        raise ContinuityObservationConflictError(
                            "observation sequence conflicts with persisted evidence"
                        )
                    return latest
            self._insert_record(candidate, recorded_at=moment)
            return candidate

    def _evaluate_invariants(
        self,
        diagnostic: ContinuityEnablementDiagnosticEvidence,
        lease_valid: bool,
    ) -> dict[str, bool]:
        decision_binding_consistent = (diagnostic.applied_decision_id is None) == (
            diagnostic.applied_decision_sequence is None
        )
        return {
            "configuration_binding_stable": (
                diagnostic.configuration_id == self._pinned_configuration_id
            ),
            "storage_location_unchanged": (
                diagnostic.storage_location_id
                == _storage_location_id(self._configuration)
            ),
            "single_lifecycle_owner": (
                diagnostic.lifecycle_owner_id == self._configuration.lifecycle_owner_id
                and diagnostic.lifecycle_owner_version
                == self._configuration.lifecycle_owner_version
            ),
            "decision_binding_consistent": decision_binding_consistent,
            "lease_valid_when_enabled": (
                diagnostic.state is not ContinuityEnablementState.ENABLED
                or lease_valid
            ),
            "runtime_authority_absent": diagnostic.runtime_authority is False,
            "side_effect_authority_absent": diagnostic.side_effect_authority is False,
        }

    def _assert_binding(
        self,
        diagnostic: ContinuityEnablementDiagnosticEvidence | None = None,
    ) -> None:
        if self._configuration.configuration_id != self._pinned_configuration_id:
            raise ContinuityObservationConfigurationError(
                "runtime configuration was substituted after observation composition"
            )
        if self._enablement_controller.configuration_id != self._pinned_configuration_id:
            raise ContinuityObservationConfigurationError(
                "enablement controller was substituted after observation composition"
            )
        if diagnostic is None:
            return
        if diagnostic.configuration_id != self._pinned_configuration_id:
            raise ContinuityObservationConfigurationError(
                "observed configuration identity was substituted"
            )
        if diagnostic.storage_location_id != _storage_location_id(self._configuration):
            raise ContinuityObservationConfigurationError(
                "observed storage location was substituted"
            )
        if (
            diagnostic.lifecycle_owner_id != self._configuration.lifecycle_owner_id
            or diagnostic.lifecycle_owner_version
            != self._configuration.lifecycle_owner_version
        ):
            raise ContinuityObservationConfigurationError(
                "observed lifecycle owner was substituted"
            )

    def _ensure_observation_schema(self) -> None:
        database_path = self._configuration.database_path()
        try:
            with sqlite3.connect(database_path) as connection:
                connection.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {_OBSERVATION_TABLE}(
                        observation_id TEXT PRIMARY KEY,
                        schema_version TEXT NOT NULL,
                        observation_sequence INTEGER NOT NULL UNIQUE,
                        configuration_id TEXT NOT NULL,
                        lifecycle_owner_id TEXT NOT NULL,
                        lifecycle_owner_version TEXT NOT NULL,
                        storage_location_id TEXT NOT NULL,
                        observed_state TEXT NOT NULL,
                        applied_decision_id TEXT,
                        applied_decision_sequence INTEGER,
                        lease_valid INTEGER NOT NULL,
                        evidence_json TEXT NOT NULL,
                        evidence_sha256 TEXT NOT NULL,
                        observed_at TEXT NOT NULL,
                        no_new_authority_granted INTEGER NOT NULL,
                        evidence_is_not_permission INTEGER NOT NULL,
                        recorded_at TEXT NOT NULL
                    )
                    """
                )
                rows = connection.execute(
                    f"PRAGMA table_info({_OBSERVATION_TABLE})"
                ).fetchall()
                actual = tuple(str(row[1]) for row in rows)
                if actual != _EXPECTED_OBSERVATION_COLUMNS:
                    raise ContinuityBoundedObservationError(
                        "bounded-observation SQLite state is incompatible"
                    )
        except ContinuityBoundedObservationError:
            raise
        except sqlite3.Error as exc:
            raise ContinuityBoundedObservationError(
                "bounded-observation SQLite initialization failed"
            ) from exc

    def _read_persisted_records(
        self,
    ) -> tuple[ContinuityBoundedObservationEvidence, ...]:
        database_path = self._configuration.database_path()
        try:
            with sqlite3.connect(database_path) as connection:
                rows = connection.execute(
                    f"""
                    SELECT
                        observation_id,
                        schema_version,
                        observation_sequence,
                        configuration_id,
                        lifecycle_owner_id,
                        lifecycle_owner_version,
                        storage_location_id,
                        observed_state,
                        applied_decision_id,
                        applied_decision_sequence,
                        lease_valid,
                        evidence_json,
                        evidence_sha256,
                        observed_at,
                        no_new_authority_granted,
                        evidence_is_not_permission,
                        recorded_at
                    FROM {_OBSERVATION_TABLE}
                    ORDER BY observation_sequence, observation_id
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            raise ContinuityBoundedObservationError(
                "bounded-observation SQLite read failed"
            ) from exc
        records: list[ContinuityBoundedObservationEvidence] = []
        previous_sequence = 0
        for row in rows:
            record = self._record_from_row(row)
            if record.observation_sequence <= previous_sequence:
                raise ContinuityBoundedObservationError(
                    "persisted observation sequence ordering is malformed"
                )
            previous_sequence = record.observation_sequence
            records.append(record)
        return tuple(records)

    def _record_from_row(self, row: tuple[Any, ...]) -> ContinuityBoundedObservationEvidence:
        (
            observation_id,
            schema_version,
            observation_sequence,
            configuration_id,
            lifecycle_owner_id,
            lifecycle_owner_version,
            storage_location_id,
            observed_state,
            applied_decision_id,
            applied_decision_sequence,
            lease_valid,
            evidence_json,
            evidence_sha256,
            observed_at,
            no_new_authority_granted,
            evidence_is_not_permission,
            recorded_at,
        ) = row
        _parse_timestamp(recorded_at, "persisted recorded_at")
        if no_new_authority_granted != 1 or evidence_is_not_permission != 1:
            raise ContinuityBoundedObservationError(
                "persisted observation authority markers are malformed"
            )
        if evidence_sha256 != observation_id:
            raise ContinuityBoundedObservationError(
                "persisted observation digest mismatch"
            )
        if _digest_text(evidence_json) != observation_id:
            raise ContinuityBoundedObservationError(
                "persisted observation evidence digest mismatch"
            )
        try:
            payload = json.loads(evidence_json)
        except (TypeError, ValueError) as exc:
            raise ContinuityBoundedObservationError(
                "persisted observation evidence is malformed JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise ContinuityBoundedObservationError(
                "persisted observation evidence must be a JSON object"
            )
        invariants_raw = payload.get("invariants")
        if not isinstance(invariants_raw, list):
            raise ContinuityBoundedObservationError(
                "persisted observation invariants are malformed"
            )
        try:
            invariants = tuple(
                (str(name), bool(passed)) for name, passed in invariants_raw
            )
        except (TypeError, ValueError) as exc:
            raise ContinuityBoundedObservationError(
                "persisted observation invariants are malformed"
            ) from exc
        record = ContinuityBoundedObservationEvidence(
            observation_id=observation_id,
            schema_version=schema_version,
            observation_sequence=observation_sequence,
            configuration_id=configuration_id,
            lifecycle_owner_id=lifecycle_owner_id,
            lifecycle_owner_version=lifecycle_owner_version,
            storage_location_id=storage_location_id,
            observed_state=observed_state,
            applied_decision_id=applied_decision_id,
            applied_decision_sequence=applied_decision_sequence,
            lease_valid=bool(lease_valid),
            invariants=invariants,
            observed_at=observed_at,
        )
        indexed = (
            record.observation_id,
            record.schema_version,
            record.observation_sequence,
            record.configuration_id,
            record.lifecycle_owner_id,
            record.lifecycle_owner_version,
            record.storage_location_id,
            record.observed_state,
            record.applied_decision_id,
            record.applied_decision_sequence,
        )
        stored = (
            observation_id,
            schema_version,
            observation_sequence,
            configuration_id,
            lifecycle_owner_id,
            lifecycle_owner_version,
            storage_location_id,
            observed_state,
            applied_decision_id,
            applied_decision_sequence,
        )
        if indexed != stored:
            raise ContinuityBoundedObservationError(
                "persisted observation indexed state is malformed"
            )
        if record.configuration_id != self._pinned_configuration_id:
            raise ContinuityBoundedObservationError(
                "persisted observation evidence does not match this controller's binding"
            )
        return record

    def _insert_record(
        self,
        record: ContinuityBoundedObservationEvidence,
        *,
        recorded_at: datetime,
    ) -> None:
        evidence_json = record.canonical_evidence()
        try:
            with sqlite3.connect(self._configuration.database_path()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    f"""
                    INSERT INTO {_OBSERVATION_TABLE}(
                        observation_id,
                        schema_version,
                        observation_sequence,
                        configuration_id,
                        lifecycle_owner_id,
                        lifecycle_owner_version,
                        storage_location_id,
                        observed_state,
                        applied_decision_id,
                        applied_decision_sequence,
                        lease_valid,
                        evidence_json,
                        evidence_sha256,
                        observed_at,
                        no_new_authority_granted,
                        evidence_is_not_permission,
                        recorded_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.observation_id,
                        record.schema_version,
                        record.observation_sequence,
                        record.configuration_id,
                        record.lifecycle_owner_id,
                        record.lifecycle_owner_version,
                        record.storage_location_id,
                        record.observed_state,
                        record.applied_decision_id,
                        record.applied_decision_sequence,
                        1 if record.lease_valid else 0,
                        evidence_json,
                        record.observation_id,
                        record.observed_at,
                        1,
                        1,
                        _format_timestamp(recorded_at),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ContinuityObservationConflictError(
                "observation sequence conflicts with persisted evidence"
            ) from exc
        except sqlite3.Error as exc:
            raise ContinuityBoundedObservationError(
                "bounded-observation SQLite write failed"
            ) from exc


def compose_bounded_observation(
    *,
    configuration: ContinuityRuntimeConfiguration,
    enablement_controller: ContinuityControlledEnablementController,
) -> ContinuityBoundedObservationController:
    """Compose one observation controller bound to an already-composed controller.

    This never enables anything, never supplies Operator GO and never starts
    or stops the enablement controller; it only binds a read-only observer to
    the exact same configuration identity.
    """

    return ContinuityBoundedObservationController(
        configuration=configuration,
        enablement_controller=enablement_controller,
    )


__all__ = [
    "BOUNDED_OBSERVATION_SCHEMA_VERSION",
    "ContinuityBoundedObservationController",
    "ContinuityBoundedObservationError",
    "ContinuityBoundedObservationEvidence",
    "ContinuityObservationConfigurationError",
    "ContinuityObservationConflictError",
    "ContinuityObservationLifecycle",
    "ContinuityObservationSessionSummary",
    "ContinuityObservationStateError",
    "compose_bounded_observation",
    "summarize_observation_session",
]
