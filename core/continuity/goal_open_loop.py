"""Read-only goal snapshots and typed open-loop projections.

The legacy GoalStack remains the storage owner. This module snapshots it
without writing and requires explicit evidence attestation before a goal is
admitted as a continuity projection. Open loops are created only from typed
signals supplied by upstream code; no intent, blocker, or commitment is
inferred from raw text.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Protocol
import unicodedata

from core.goal_stack import Goal

GOAL_SNAPSHOT_SCHEMA_VERSION = "continuity.goal_snapshot.v1"
GOAL_PROJECTION_SCHEMA_VERSION = "continuity.goal_projection.v1"
OPEN_LOOP_SCHEMA_VERSION = "continuity.open_loop_projection.v1"
GOAL_OPEN_LOOP_POLICY_VERSION = "continuity.goal_open_loop.policy.v1"


class GoalOpenLoopError(ValueError):
    """Goal or open-loop input violates a projection invariant."""


class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "done"
    CANCELLED = "cancelled"


class GoalBasis(str, Enum):
    EXPLICIT_INTENT = "explicit_intent"
    ACCEPTED_DECISION = "accepted_decision"
    CONFIRMED_TASK = "confirmed_task"
    ACCEPTED_PLAN = "accepted_plan"


class GoalDecisionDisposition(str, Enum):
    INCLUDED = "included"
    EXCLUDED = "excluded"


class GoalDecisionReason(str, Enum):
    EXPLICIT_ATTESTATION = "explicit_attestation"
    MISSING_ATTESTATION = "missing_attestation"
    LEGACY_SOURCE_SNAPSHOT = "legacy_source_snapshot"


class OpenLoopKind(str, Enum):
    UNANSWERED_QUESTION = "unanswered_question"
    ACTION_WITHOUT_OUTCOME = "action_without_outcome"
    DEFERRED_DECISION = "deferred_decision"
    BLOCKER = "blocker"
    COMMITMENT_WITHOUT_COMPLETION = "commitment_without_completion"
    EXPLICIT_REVISIT_REQUEST = "explicit_revisit_request"


class OpenLoopStatus(str, Enum):
    NOT_YET_OPEN = "not_yet_open"
    OPEN = "open"
    OVERDUE = "overdue"
    RESOLVED = "resolved"


class OpenLoopReason(str, Enum):
    TYPED_SOURCE_SIGNAL = "typed_source_signal"
    OPENED_AS_OF_REQUEST = "opened_as_of_request"
    FUTURE_OPEN_TIME = "future_open_time"
    DEADLINE_PASSED = "deadline_passed"
    RESOLUTION_EVIDENCE_PRESENT = "resolution_evidence_present"


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GoalOpenLoopError(f"{name} must be a non-empty string")
    return unicodedata.normalize("NFC", value.strip())


def _aware(value: object, name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise GoalOpenLoopError(f"{name} must be timezone-aware")
    return value


def _parse_time(value: object, name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise GoalOpenLoopError(
            f"{name} must be a non-empty ISO timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GoalOpenLoopError(
            f"{name} must be a valid ISO timestamp"
        ) from exc
    return _aware(parsed, name)


def _dt(value: datetime) -> str:
    return (
        _aware(value, "datetime")
        .astimezone(UTC)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _hash(payload: object) -> str:
    return sha256(_json(payload).encode("utf-8")).hexdigest()


def _refs(values: Iterable[str], name: str) -> tuple[str, ...]:
    result = tuple(_text(value, name) for value in values)
    if len(result) != len(set(result)):
        raise GoalOpenLoopError(f"{name} cannot contain duplicates")
    return tuple(sorted(result))


def _merge_refs(*groups: Iterable[str]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                _text(value, "source_ref")
                for group in groups
                for value in group
            }
        )
    )


def _keywords(values: Iterable[str]) -> tuple[str, ...]:
    result = tuple(_text(value, "keyword").lower() for value in values)
    if len(result) != len(set(result)):
        raise GoalOpenLoopError("keywords cannot contain duplicates")
    return tuple(sorted(result))


class GoalStackReader(Protocol):
    """Read boundary implemented by the existing GoalStack."""

    def list_goals(
        self,
        user_id: str = "default",
        *,
        status: str | None = "active",
        limit: int = 50,
    ) -> list[Goal]: ...


@dataclass(frozen=True, slots=True)
class GoalRecordSnapshot:
    snapshot_id: str
    schema_version: str
    goal_ref: str
    user_id: str
    title: str
    description: str
    status: GoalStatus
    priority: int
    keywords: tuple[str, ...]
    created_at: datetime
    updated_at: datetime
    source_ref: str

    @classmethod
    def from_goal(cls, goal: Goal) -> GoalRecordSnapshot:
        if not isinstance(goal, Goal):
            raise GoalOpenLoopError("goal must be a Goal")
        try:
            status = GoalStatus(goal.status)
        except ValueError as exc:
            raise GoalOpenLoopError(
                f"unsupported goal status: {goal.status}"
            ) from exc
        if isinstance(goal.priority, bool) or not isinstance(
            goal.priority, int
        ):
            raise GoalOpenLoopError("priority must be an int")
        goal_ref = _text(goal.goal_id, "goal_id")
        created_at = _parse_time(goal.created_at, "created_at")
        updated_at = _parse_time(goal.updated_at, "updated_at")
        if updated_at.astimezone(UTC) < created_at.astimezone(UTC):
            raise GoalOpenLoopError(
                "updated_at cannot precede created_at"
            )
        values = {
            "schema_version": GOAL_SNAPSHOT_SCHEMA_VERSION,
            "goal_ref": goal_ref,
            "user_id": _text(goal.user_id, "user_id"),
            "title": _text(goal.title, "title"),
            "description": unicodedata.normalize(
                "NFC", goal.description.strip()
            ),
            "status": status.value,
            "priority": goal.priority,
            "keywords": list(_keywords(tuple(goal.keywords))),
            "created_at": _dt(created_at),
            "updated_at": _dt(updated_at),
            "source_ref": f"goal_stack:{goal_ref}",
        }
        return cls(
            snapshot_id=_hash(values),
            schema_version=GOAL_SNAPSHOT_SCHEMA_VERSION,
            goal_ref=goal_ref,
            user_id=str(values["user_id"]),
            title=str(values["title"]),
            description=str(values["description"]),
            status=status,
            priority=goal.priority,
            keywords=tuple(str(value) for value in values["keywords"]),
            created_at=created_at,
            updated_at=updated_at,
            source_ref=str(values["source_ref"]),
        )


class GoalStackSnapshotBridge:
    """Read legacy GoalStack records without creating or updating goals."""

    def __init__(self, reader: GoalStackReader) -> None:
        self._reader = reader

    def snapshots(
        self,
        user_id: str = "default",
        *,
        limit: int = 200,
    ) -> tuple[GoalRecordSnapshot, ...]:
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= 200
        ):
            raise GoalOpenLoopError("limit must be an int in [1, 200]")
        records = self._reader.list_goals(
            _text(user_id, "user_id"),
            status=None,
            limit=limit,
        )
        by_goal: dict[str, GoalRecordSnapshot] = {}
        for record in records:
            snapshot = GoalRecordSnapshot.from_goal(record)
            existing_snapshot = by_goal.get(snapshot.goal_ref)
            if (
                existing_snapshot is not None
                and existing_snapshot != snapshot
            ):
                raise GoalOpenLoopError(
                    f"conflicting goal snapshots: {snapshot.goal_ref}"
                )
            by_goal[snapshot.goal_ref] = snapshot
        return tuple(
            sorted(
                by_goal.values(),
                key=lambda value: (
                    -value.priority,
                    -value.updated_at.timestamp(),
                    value.goal_ref,
                ),
            )
        )


@dataclass(frozen=True, slots=True)
class GoalAttestation:
    attestation_id: str
    goal_ref: str
    basis: GoalBasis
    source_refs: tuple[str, ...]
    confirmed_at: datetime

    @classmethod
    def create(
        cls,
        *,
        goal_ref: str,
        basis: GoalBasis,
        source_refs: Iterable[str],
        confirmed_at: datetime,
    ) -> GoalAttestation:
        if not isinstance(basis, GoalBasis):
            raise GoalOpenLoopError("basis must be a GoalBasis")
        goal_id = _text(goal_ref, "goal_ref")
        sources = _refs(source_refs, "source_refs")
        if not sources:
            raise GoalOpenLoopError("source_refs cannot be empty")
        point = _aware(confirmed_at, "confirmed_at")
        payload = {
            "goal_ref": goal_id,
            "basis": basis.value,
            "source_refs": list(sources),
            "confirmed_at": _dt(point),
        }
        return cls(_hash(payload), goal_id, basis, sources, point)


@dataclass(frozen=True, slots=True)
class GoalProjection:
    projection_id: str
    schema_version: str
    policy_version: str
    goal_ref: str
    source_snapshot_id: str
    attestation_id: str
    basis: GoalBasis
    status: GoalStatus
    title: str
    description: str
    priority: int
    keywords: tuple[str, ...]
    source_refs: tuple[str, ...]
    updated_at: datetime

    @classmethod
    def create(
        cls,
        snapshot: GoalRecordSnapshot,
        attestation: GoalAttestation,
        *,
        policy_version: str = GOAL_OPEN_LOOP_POLICY_VERSION,
    ) -> GoalProjection:
        if snapshot.goal_ref != attestation.goal_ref:
            raise GoalOpenLoopError(
                "attestation goal_ref does not match snapshot"
            )
        if (
            attestation.confirmed_at.astimezone(UTC)
            < snapshot.created_at.astimezone(UTC)
        ):
            raise GoalOpenLoopError(
                "attestation cannot precede goal creation"
            )
        policy = _text(policy_version, "policy_version")
        sources = _merge_refs(
            (snapshot.source_ref,), attestation.source_refs
        )
        payload = {
            "schema_version": GOAL_PROJECTION_SCHEMA_VERSION,
            "policy_version": policy,
            "goal_ref": snapshot.goal_ref,
            "source_snapshot_id": snapshot.snapshot_id,
            "attestation_id": attestation.attestation_id,
            "basis": attestation.basis.value,
            "status": snapshot.status.value,
            "title": snapshot.title,
            "description": snapshot.description,
            "priority": snapshot.priority,
            "keywords": list(snapshot.keywords),
            "source_refs": list(sources),
            "updated_at": _dt(snapshot.updated_at),
        }
        return cls(
            projection_id=_hash(payload),
            schema_version=GOAL_PROJECTION_SCHEMA_VERSION,
            policy_version=policy,
            goal_ref=snapshot.goal_ref,
            source_snapshot_id=snapshot.snapshot_id,
            attestation_id=attestation.attestation_id,
            basis=attestation.basis,
            status=snapshot.status,
            title=snapshot.title,
            description=snapshot.description,
            priority=snapshot.priority,
            keywords=snapshot.keywords,
            source_refs=sources,
            updated_at=snapshot.updated_at,
        )


@dataclass(frozen=True, slots=True)
class GoalProjectionDecision:
    goal_ref: str
    disposition: GoalDecisionDisposition
    reason_codes: tuple[GoalDecisionReason, ...]
    source_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GoalProjectionResult:
    result_id: str
    policy_version: str
    projections: tuple[GoalProjection, ...]
    decisions: tuple[GoalProjectionDecision, ...]


class GoalProjector:
    """Admit only legacy goals backed by explicit typed attestations."""

    def project(
        self,
        snapshots: Iterable[GoalRecordSnapshot],
        attestations: Iterable[GoalAttestation],
        *,
        policy_version: str = GOAL_OPEN_LOOP_POLICY_VERSION,
    ) -> GoalProjectionResult:
        policy = _text(policy_version, "policy_version")
        snapshot_by_goal: dict[str, GoalRecordSnapshot] = {}
        for snapshot in snapshots:
            if not isinstance(snapshot, GoalRecordSnapshot):
                raise GoalOpenLoopError(
                    "snapshots contain an invalid value"
                )
            existing_snapshot = snapshot_by_goal.get(snapshot.goal_ref)
            if (
                existing_snapshot is not None
                and existing_snapshot != snapshot
            ):
                raise GoalOpenLoopError(
                    f"conflicting goal snapshots: {snapshot.goal_ref}"
                )
            snapshot_by_goal[snapshot.goal_ref] = snapshot

        attestation_by_goal: dict[str, GoalAttestation] = {}
        for attestation_value in attestations:
            if not isinstance(attestation_value, GoalAttestation):
                raise GoalOpenLoopError(
                    "attestations contain an invalid value"
                )
            if attestation_value.goal_ref not in snapshot_by_goal:
                raise GoalOpenLoopError(
                    "attestation references unknown goal: "
                    f"{attestation_value.goal_ref}"
                )
            existing_attestation = attestation_by_goal.get(
                attestation_value.goal_ref
            )
            if (
                existing_attestation is not None
                and existing_attestation != attestation_value
            ):
                raise GoalOpenLoopError(
                    "multiple attestations for goal: "
                    f"{attestation_value.goal_ref}"
                )
            attestation_by_goal[
                attestation_value.goal_ref
            ] = attestation_value

        projections: list[GoalProjection] = []
        decisions: list[GoalProjectionDecision] = []
        for goal_ref, snapshot in sorted(snapshot_by_goal.items()):
            goal_attestation = attestation_by_goal.get(goal_ref)
            if goal_attestation is None:
                decisions.append(
                    GoalProjectionDecision(
                        goal_ref=goal_ref,
                        disposition=GoalDecisionDisposition.EXCLUDED,
                        reason_codes=(
                            GoalDecisionReason.MISSING_ATTESTATION,
                        ),
                        source_refs=(snapshot.source_ref,),
                    )
                )
                continue
            projection = GoalProjection.create(
                snapshot,
                goal_attestation,
                policy_version=policy,
            )
            projections.append(projection)
            decisions.append(
                GoalProjectionDecision(
                    goal_ref=goal_ref,
                    disposition=GoalDecisionDisposition.INCLUDED,
                    reason_codes=(
                        GoalDecisionReason.EXPLICIT_ATTESTATION,
                        GoalDecisionReason.LEGACY_SOURCE_SNAPSHOT,
                    ),
                    source_refs=projection.source_refs,
                )
            )

        ordered_projections = tuple(
            sorted(projections, key=lambda value: value.projection_id)
        )
        ordered_decisions = tuple(
            sorted(decisions, key=lambda value: value.goal_ref)
        )
        payload = {
            "policy_version": policy,
            "projection_ids": [
                value.projection_id for value in ordered_projections
            ],
            "decisions": [
                {
                    "goal_ref": value.goal_ref,
                    "disposition": value.disposition.value,
                    "reason_codes": [
                        reason.value for reason in value.reason_codes
                    ],
                    "source_refs": list(value.source_refs),
                }
                for value in ordered_decisions
            ],
        }
        return GoalProjectionResult(
            result_id=_hash(payload),
            policy_version=policy,
            projections=ordered_projections,
            decisions=ordered_decisions,
        )


@dataclass(frozen=True, slots=True)
class OpenLoopSignal:
    signal_id: str
    loop_key: str
    kind: OpenLoopKind
    summary: str
    source_refs: tuple[str, ...]
    opened_at: datetime
    due_at: datetime | None
    related_goal_ref: str | None

    @classmethod
    def create(
        cls,
        *,
        loop_key: str,
        kind: OpenLoopKind,
        summary: str,
        source_refs: Iterable[str],
        opened_at: datetime,
        due_at: datetime | None = None,
        related_goal_ref: str | None = None,
    ) -> OpenLoopSignal:
        if not isinstance(kind, OpenLoopKind):
            raise GoalOpenLoopError("kind must be an OpenLoopKind")
        key = _text(loop_key, "loop_key")
        text = _text(summary, "summary")
        sources = _refs(source_refs, "source_refs")
        if not sources:
            raise GoalOpenLoopError("source_refs cannot be empty")
        opened = _aware(opened_at, "opened_at")
        due = _aware(due_at, "due_at") if due_at is not None else None
        if due is not None and due.astimezone(UTC) < opened.astimezone(UTC):
            raise GoalOpenLoopError("due_at cannot precede opened_at")
        goal_ref = (
            _text(related_goal_ref, "related_goal_ref")
            if related_goal_ref is not None
            else None
        )
        payload = {
            "loop_key": key,
            "kind": kind.value,
            "summary": text,
            "source_refs": list(sources),
            "opened_at": _dt(opened),
            "due_at": _dt(due) if due is not None else None,
            "related_goal_ref": goal_ref,
        }
        return cls(
            _hash(payload),
            key,
            kind,
            text,
            sources,
            opened,
            due,
            goal_ref,
        )


@dataclass(frozen=True, slots=True)
class OpenLoopResolution:
    resolution_id: str
    loop_key: str
    source_refs: tuple[str, ...]
    resolved_at: datetime

    @classmethod
    def create(
        cls,
        *,
        loop_key: str,
        source_refs: Iterable[str],
        resolved_at: datetime,
    ) -> OpenLoopResolution:
        key = _text(loop_key, "loop_key")
        sources = _refs(source_refs, "source_refs")
        if not sources:
            raise GoalOpenLoopError("source_refs cannot be empty")
        point = _aware(resolved_at, "resolved_at")
        payload = {
            "loop_key": key,
            "source_refs": list(sources),
            "resolved_at": _dt(point),
        }
        return cls(_hash(payload), key, sources, point)


@dataclass(frozen=True, slots=True)
class OpenLoopProjection:
    projection_id: str
    schema_version: str
    policy_version: str
    loop_key: str
    signal_id: str
    kind: OpenLoopKind
    summary: str
    status: OpenLoopStatus
    source_refs: tuple[str, ...]
    resolution_ids: tuple[str, ...]
    opened_at: datetime
    due_at: datetime | None
    related_goal_ref: str | None
    reason_codes: tuple[OpenLoopReason, ...]
    review_required: bool


@dataclass(frozen=True, slots=True)
class OpenLoopProjectionResult:
    result_id: str
    policy_version: str
    as_of: datetime
    projections: tuple[OpenLoopProjection, ...]


class OpenLoopProjector:
    """Project typed open-loop signals and explicit resolution evidence."""

    def project(
        self,
        signals: Iterable[OpenLoopSignal],
        resolutions: Iterable[OpenLoopResolution],
        *,
        as_of: datetime,
        policy_version: str = GOAL_OPEN_LOOP_POLICY_VERSION,
    ) -> OpenLoopProjectionResult:
        point = _aware(as_of, "as_of")
        policy = _text(policy_version, "policy_version")
        signal_by_key = self._signal_map(signals)
        resolutions_by_key = self._resolution_map(
            resolutions,
            signal_by_key,
        )
        projections = tuple(
            self._project_one(
                signal,
                resolutions_by_key.get(loop_key, ()),
                as_of=point,
                policy_version=policy,
            )
            for loop_key, signal in sorted(signal_by_key.items())
        )
        payload = {
            "policy_version": policy,
            "as_of": _dt(point),
            "projection_ids": [
                value.projection_id for value in projections
            ],
        }
        return OpenLoopProjectionResult(
            result_id=_hash(payload),
            policy_version=policy,
            as_of=point,
            projections=projections,
        )

    @staticmethod
    def _signal_map(
        signals: Iterable[OpenLoopSignal],
    ) -> dict[str, OpenLoopSignal]:
        result: dict[str, OpenLoopSignal] = {}
        for signal in signals:
            if not isinstance(signal, OpenLoopSignal):
                raise GoalOpenLoopError("signals contain an invalid value")
            existing_signal = result.get(signal.loop_key)
            if existing_signal is not None and existing_signal != signal:
                raise GoalOpenLoopError(
                    "conflicting signals for loop_key: "
                    f"{signal.loop_key}"
                )
            result[signal.loop_key] = signal
        return result

    @staticmethod
    def _resolution_map(
        resolutions: Iterable[OpenLoopResolution],
        signals: dict[str, OpenLoopSignal],
    ) -> dict[str, tuple[OpenLoopResolution, ...]]:
        grouped: dict[str, dict[str, OpenLoopResolution]] = {}
        for resolution in resolutions:
            if not isinstance(resolution, OpenLoopResolution):
                raise GoalOpenLoopError(
                    "resolutions contain an invalid value"
                )
            if resolution.loop_key not in signals:
                raise GoalOpenLoopError(
                    "resolution references unknown loop: "
                    f"{resolution.loop_key}"
                )
            grouped.setdefault(resolution.loop_key, {})[
                resolution.resolution_id
            ] = resolution
        return {
            key: tuple(
                sorted(
                    values.values(),
                    key=lambda value: (
                        value.resolved_at.astimezone(UTC),
                        value.resolution_id,
                    ),
                )
            )
            for key, values in grouped.items()
        }

    @staticmethod
    def _project_one(
        signal: OpenLoopSignal,
        resolutions: tuple[OpenLoopResolution, ...],
        *,
        as_of: datetime,
        policy_version: str,
    ) -> OpenLoopProjection:
        if any(
            value.resolved_at.astimezone(UTC)
            < signal.opened_at.astimezone(UTC)
            for value in resolutions
        ):
            raise GoalOpenLoopError(
                f"resolution precedes open time: {signal.loop_key}"
            )
        effective = tuple(
            value
            for value in resolutions
            if value.resolved_at.astimezone(UTC)
            <= as_of.astimezone(UTC)
        )
        reasons = {OpenLoopReason.TYPED_SOURCE_SIGNAL}
        if signal.opened_at.astimezone(UTC) > as_of.astimezone(UTC):
            status = OpenLoopStatus.NOT_YET_OPEN
            reasons.add(OpenLoopReason.FUTURE_OPEN_TIME)
        elif effective:
            status = OpenLoopStatus.RESOLVED
            reasons.add(OpenLoopReason.RESOLUTION_EVIDENCE_PRESENT)
        elif (
            signal.due_at is not None
            and signal.due_at.astimezone(UTC) < as_of.astimezone(UTC)
        ):
            status = OpenLoopStatus.OVERDUE
            reasons.add(OpenLoopReason.DEADLINE_PASSED)
        else:
            status = OpenLoopStatus.OPEN
            reasons.add(OpenLoopReason.OPENED_AS_OF_REQUEST)

        resolution_ids = _refs(
            (value.resolution_id for value in effective),
            "resolution_ids",
        )
        source_refs = _merge_refs(
            signal.source_refs,
            (
                ref
                for resolution in effective
                for ref in resolution.source_refs
            ),
        )
        reason_codes = tuple(
            sorted(reasons, key=lambda value: value.value)
        )
        review_required = status in {
            OpenLoopStatus.OPEN,
            OpenLoopStatus.OVERDUE,
        }
        payload = {
            "schema_version": OPEN_LOOP_SCHEMA_VERSION,
            "policy_version": policy_version,
            "loop_key": signal.loop_key,
            "signal_id": signal.signal_id,
            "kind": signal.kind.value,
            "summary": signal.summary,
            "status": status.value,
            "source_refs": list(source_refs),
            "resolution_ids": list(resolution_ids),
            "opened_at": _dt(signal.opened_at),
            "due_at": _dt(signal.due_at) if signal.due_at else None,
            "related_goal_ref": signal.related_goal_ref,
            "reason_codes": [value.value for value in reason_codes],
            "review_required": review_required,
        }
        return OpenLoopProjection(
            projection_id=_hash(payload),
            schema_version=OPEN_LOOP_SCHEMA_VERSION,
            policy_version=policy_version,
            loop_key=signal.loop_key,
            signal_id=signal.signal_id,
            kind=signal.kind,
            summary=signal.summary,
            status=status,
            source_refs=source_refs,
            resolution_ids=resolution_ids,
            opened_at=signal.opened_at,
            due_at=signal.due_at,
            related_goal_ref=signal.related_goal_ref,
            reason_codes=reason_codes,
            review_required=review_required,
        )


__all__ = [
    "GOAL_OPEN_LOOP_POLICY_VERSION",
    "GOAL_PROJECTION_SCHEMA_VERSION",
    "GOAL_SNAPSHOT_SCHEMA_VERSION",
    "OPEN_LOOP_SCHEMA_VERSION",
    "GoalAttestation",
    "GoalBasis",
    "GoalDecisionDisposition",
    "GoalDecisionReason",
    "GoalOpenLoopError",
    "GoalProjection",
    "GoalProjectionDecision",
    "GoalProjectionResult",
    "GoalProjector",
    "GoalRecordSnapshot",
    "GoalStackReader",
    "GoalStackSnapshotBridge",
    "GoalStatus",
    "OpenLoopKind",
    "OpenLoopProjection",
    "OpenLoopProjectionResult",
    "OpenLoopProjector",
    "OpenLoopReason",
    "OpenLoopResolution",
    "OpenLoopSignal",
    "OpenLoopStatus",
]
