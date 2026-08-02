"""Deterministic current-state projections over immutable continuity assertions.

This module is projection-only. It does not mutate assertions, change ESM
state, invoke TruthGate, write Canon, perform retrieval, or authorize advice or
actions. For CORRECTS, SUPERSEDES, and RETRACTS, the source assertion acts on
the target assertion.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable
import unicodedata

from .contracts import (
    AssertionRecord,
    AssertionRelation,
    AssertionRelationType,
    OriginType,
    SubjectRef,
)

STATE_PROJECTION_SCHEMA_VERSION = "continuity.current_state_projection.v1"
STATE_RECONCILIATION_POLICY_VERSION = "continuity.state_reconciler.v1"


class StateReconciliationError(ValueError):
    """Current state cannot be projected without violating an invariant."""


class ProjectionStatus(str, Enum):
    CURRENT = "current"
    STALE = "stale"
    SUPERSEDED = "superseded"
    CONTESTED = "contested"
    EXPIRED = "expired"
    UNRESOLVED = "unresolved"


class StateReason(str, Enum):
    ACTIVE_ASSERTION = "active_assertion"
    EXPLICIT_CORRECTION = "explicit_correction"
    EXPLICIT_SUPERSESSION = "explicit_supersession"
    EXPLICIT_RETRACTION = "explicit_retraction"
    NEWER_USER_STATEMENT = "newer_user_statement"
    USER_STATEMENT_PREFERRED_OVER_INFERENCE = (
        "user_statement_preferred_over_inference"
    )
    SAME_VALUE_CORROBORATION = "same_value_corroboration"
    ACTIVE_VALUE_CONFLICT = "active_value_conflict"
    EXPLICIT_CONTRADICTION = "explicit_contradiction"
    ONLY_EXPIRED_ASSERTIONS = "only_expired_assertions"
    ONLY_FUTURE_ASSERTIONS = "only_future_assertions"
    ALL_ACTIVE_ASSERTIONS_DISPLACED = "all_active_assertions_displaced"


_LIFECYCLE_RELATIONS = {
    AssertionRelationType.CORRECTS,
    AssertionRelationType.SUPERSEDES,
    AssertionRelationType.RETRACTS,
}


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StateReconciliationError(f"{name} must be a non-empty string")
    return unicodedata.normalize("NFC", value)


def _aware(value: object, name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise StateReconciliationError(f"{name} must be timezone-aware")
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


def _refs(values: Iterable[str], name: str) -> tuple[str, ...]:
    result = tuple(_text(value, name) for value in values)
    if len(result) != len(set(result)):
        raise StateReconciliationError(f"{name} cannot contain duplicates")
    return tuple(sorted(result))


def _reasons(values: Iterable[StateReason]) -> tuple[StateReason, ...]:
    result = tuple(values)
    if any(not isinstance(value, StateReason) for value in result):
        raise StateReconciliationError("reason_codes contain an invalid value")
    by_value = {value.value: value for value in result}
    if len(by_value) != len(result):
        raise StateReconciliationError("reason_codes cannot contain duplicates")
    return tuple(by_value[key] for key in sorted(by_value))


def _state_key(assertion: AssertionRecord) -> tuple[str, str, str]:
    return (
        assertion.subject_ref.subject_id,
        assertion.subject_ref.kind.value,
        unicodedata.normalize("NFC", assertion.predicate),
    )


def _value_key(assertion: AssertionRecord) -> str:
    value = assertion.value
    if value is None:
        type_name = "null"
    elif isinstance(value, bool):
        type_name = "bool"
    elif isinstance(value, int):
        type_name = "int"
    elif isinstance(value, float):
        type_name = "float"
    else:
        type_name = "str"
    return _canonical_json({"type": type_name, "value": value})


def _is_future(assertion: AssertionRecord, as_of: datetime) -> bool:
    return assertion.valid_from.astimezone(UTC) > as_of.astimezone(UTC)


def _is_expired(assertion: AssertionRecord, as_of: datetime) -> bool:
    return (
        assertion.valid_to is not None
        and assertion.valid_to.astimezone(UTC) < as_of.astimezone(UTC)
    )


def _is_active(assertion: AssertionRecord, as_of: datetime) -> bool:
    return not _is_future(assertion, as_of) and not _is_expired(
        assertion, as_of
    )


def _projection_payload(
    *,
    schema_version: str,
    policy_version: str,
    subject_ref: SubjectRef,
    predicate: str,
    as_of: datetime,
    status: ProjectionStatus,
    selected_assertion_ref: str | None,
    candidate_assertion_refs: tuple[str, ...],
    supporting_assertion_refs: tuple[str, ...],
    contradiction_assertion_refs: tuple[str, ...],
    superseded_assertion_refs: tuple[str, ...],
    retracted_assertion_refs: tuple[str, ...],
    expired_assertion_refs: tuple[str, ...],
    future_assertion_refs: tuple[str, ...],
    reason_codes: tuple[StateReason, ...],
    review_required: bool,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "policy_version": policy_version,
        "subject_ref": subject_ref.identity_payload(),
        "predicate": predicate,
        "as_of": _canonical_datetime(as_of),
        "status": status.value,
        "selected_assertion_ref": selected_assertion_ref,
        "candidate_assertion_refs": list(candidate_assertion_refs),
        "supporting_assertion_refs": list(supporting_assertion_refs),
        "contradiction_assertion_refs": list(
            contradiction_assertion_refs
        ),
        "superseded_assertion_refs": list(superseded_assertion_refs),
        "retracted_assertion_refs": list(retracted_assertion_refs),
        "expired_assertion_refs": list(expired_assertion_refs),
        "future_assertion_refs": list(future_assertion_refs),
        "reason_codes": [value.value for value in reason_codes],
        "review_required": review_required,
    }


@dataclass(frozen=True, slots=True)
class CurrentStateProjection:
    projection_id: str
    schema_version: str
    policy_version: str
    subject_ref: SubjectRef
    predicate: str
    as_of: datetime
    status: ProjectionStatus
    selected_assertion_ref: str | None
    candidate_assertion_refs: tuple[str, ...]
    supporting_assertion_refs: tuple[str, ...]
    contradiction_assertion_refs: tuple[str, ...]
    superseded_assertion_refs: tuple[str, ...]
    retracted_assertion_refs: tuple[str, ...]
    expired_assertion_refs: tuple[str, ...]
    future_assertion_refs: tuple[str, ...]
    reason_codes: tuple[StateReason, ...]
    review_required: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _text(self.schema_version, "schema_version"),
        )
        object.__setattr__(
            self,
            "policy_version",
            _text(self.policy_version, "policy_version"),
        )
        if not isinstance(self.subject_ref, SubjectRef):
            raise StateReconciliationError(
                "subject_ref must be a SubjectRef"
            )
        object.__setattr__(
            self, "predicate", _text(self.predicate, "predicate")
        )
        object.__setattr__(self, "as_of", _aware(self.as_of, "as_of"))
        if not isinstance(self.status, ProjectionStatus):
            raise StateReconciliationError(
                "status must be a ProjectionStatus"
            )
        if self.selected_assertion_ref is not None:
            object.__setattr__(
                self,
                "selected_assertion_ref",
                _text(
                    self.selected_assertion_ref,
                    "selected_assertion_ref",
                ),
            )
        for field_name in (
            "candidate_assertion_refs",
            "supporting_assertion_refs",
            "contradiction_assertion_refs",
            "superseded_assertion_refs",
            "retracted_assertion_refs",
            "expired_assertion_refs",
            "future_assertion_refs",
        ):
            object.__setattr__(
                self,
                field_name,
                _refs(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self, "reason_codes", _reasons(self.reason_codes)
        )
        if not isinstance(self.review_required, bool):
            raise StateReconciliationError(
                "review_required must be a bool"
            )

        all_refs = set(self.candidate_assertion_refs)
        all_refs.update(self.supporting_assertion_refs)
        all_refs.update(self.contradiction_assertion_refs)
        all_refs.update(self.superseded_assertion_refs)
        all_refs.update(self.retracted_assertion_refs)
        all_refs.update(self.expired_assertion_refs)
        all_refs.update(self.future_assertion_refs)
        if (
            self.selected_assertion_ref is not None
            and self.selected_assertion_ref not in all_refs
        ):
            raise StateReconciliationError(
                "selected_assertion_ref must be represented in projection refs"
            )
        if (
            self.status is ProjectionStatus.CURRENT
            and self.selected_assertion_ref is None
        ):
            raise StateReconciliationError(
                "CURRENT projection requires a selected assertion"
            )
        if (
            self.status
            in (ProjectionStatus.EXPIRED, ProjectionStatus.UNRESOLVED)
            and self.selected_assertion_ref is not None
        ):
            raise StateReconciliationError(
                "EXPIRED/UNRESOLVED projection cannot select an assertion"
            )
        if self.projection_id != _digest(self.payload()):
            raise StateReconciliationError(
                "projection_id does not match projection content"
            )

    @classmethod
    def create(
        cls,
        *,
        subject_ref: SubjectRef,
        predicate: str,
        as_of: datetime,
        status: ProjectionStatus,
        selected_assertion_ref: str | None,
        candidate_assertion_refs: Iterable[str] = (),
        supporting_assertion_refs: Iterable[str] = (),
        contradiction_assertion_refs: Iterable[str] = (),
        superseded_assertion_refs: Iterable[str] = (),
        retracted_assertion_refs: Iterable[str] = (),
        expired_assertion_refs: Iterable[str] = (),
        future_assertion_refs: Iterable[str] = (),
        reason_codes: Iterable[StateReason] = (),
        review_required: bool = False,
        policy_version: str = STATE_RECONCILIATION_POLICY_VERSION,
    ) -> CurrentStateProjection:
        predicate_value = _text(predicate, "predicate")
        point = _aware(as_of, "as_of")
        policy = _text(policy_version, "policy_version")
        candidates = _refs(
            candidate_assertion_refs, "candidate_assertion_refs"
        )
        supporting = _refs(
            supporting_assertion_refs, "supporting_assertion_refs"
        )
        contradictions = _refs(
            contradiction_assertion_refs,
            "contradiction_assertion_refs",
        )
        superseded = _refs(
            superseded_assertion_refs, "superseded_assertion_refs"
        )
        retracted = _refs(
            retracted_assertion_refs, "retracted_assertion_refs"
        )
        expired = _refs(
            expired_assertion_refs, "expired_assertion_refs"
        )
        future = _refs(future_assertion_refs, "future_assertion_refs")
        reasons = _reasons(reason_codes)
        payload = _projection_payload(
            schema_version=STATE_PROJECTION_SCHEMA_VERSION,
            policy_version=policy,
            subject_ref=subject_ref,
            predicate=predicate_value,
            as_of=point,
            status=status,
            selected_assertion_ref=selected_assertion_ref,
            candidate_assertion_refs=candidates,
            supporting_assertion_refs=supporting,
            contradiction_assertion_refs=contradictions,
            superseded_assertion_refs=superseded,
            retracted_assertion_refs=retracted,
            expired_assertion_refs=expired,
            future_assertion_refs=future,
            reason_codes=reasons,
            review_required=review_required,
        )
        return cls(
            projection_id=_digest(payload),
            schema_version=STATE_PROJECTION_SCHEMA_VERSION,
            policy_version=policy,
            subject_ref=subject_ref,
            predicate=predicate_value,
            as_of=point,
            status=status,
            selected_assertion_ref=selected_assertion_ref,
            candidate_assertion_refs=candidates,
            supporting_assertion_refs=supporting,
            contradiction_assertion_refs=contradictions,
            superseded_assertion_refs=superseded,
            retracted_assertion_refs=retracted,
            expired_assertion_refs=expired,
            future_assertion_refs=future,
            reason_codes=reasons,
            review_required=review_required,
        )

    def payload(self) -> dict[str, object]:
        return _projection_payload(
            schema_version=self.schema_version,
            policy_version=self.policy_version,
            subject_ref=self.subject_ref,
            predicate=self.predicate,
            as_of=self.as_of,
            status=self.status,
            selected_assertion_ref=self.selected_assertion_ref,
            candidate_assertion_refs=self.candidate_assertion_refs,
            supporting_assertion_refs=self.supporting_assertion_refs,
            contradiction_assertion_refs=self.contradiction_assertion_refs,
            superseded_assertion_refs=self.superseded_assertion_refs,
            retracted_assertion_refs=self.retracted_assertion_refs,
            expired_assertion_refs=self.expired_assertion_refs,
            future_assertion_refs=self.future_assertion_refs,
            reason_codes=self.reason_codes,
            review_required=self.review_required,
        )

    def canonical_bytes(self) -> bytes:
        return _canonical_json(self.payload()).encode("utf-8")


@dataclass(frozen=True, slots=True)
class StateReconciliationResult:
    result_id: str
    policy_version: str
    as_of: datetime
    assertion_refs: tuple[str, ...]
    relation_refs: tuple[str, ...]
    projections: tuple[CurrentStateProjection, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "policy_version",
            _text(self.policy_version, "policy_version"),
        )
        object.__setattr__(self, "as_of", _aware(self.as_of, "as_of"))
        object.__setattr__(
            self,
            "assertion_refs",
            _refs(self.assertion_refs, "assertion_refs"),
        )
        object.__setattr__(
            self,
            "relation_refs",
            _refs(self.relation_refs, "relation_refs"),
        )
        if any(
            not isinstance(value, CurrentStateProjection)
            for value in self.projections
        ):
            raise StateReconciliationError(
                "projections must contain CurrentStateProjection values"
            )
        projections = tuple(
            sorted(
                self.projections,
                key=lambda value: (
                    value.subject_ref.subject_id,
                    value.subject_ref.kind.value,
                    value.predicate,
                ),
            )
        )
        if len(projections) != len(
            {value.projection_id for value in projections}
        ):
            raise StateReconciliationError(
                "projections cannot contain duplicates"
            )
        object.__setattr__(self, "projections", projections)
        if self.result_id != _digest(self.payload()):
            raise StateReconciliationError(
                "result_id does not match result content"
            )

    @classmethod
    def create(
        cls,
        *,
        as_of: datetime,
        assertion_refs: Iterable[str],
        relation_refs: Iterable[str],
        projections: Iterable[CurrentStateProjection],
        policy_version: str = STATE_RECONCILIATION_POLICY_VERSION,
    ) -> StateReconciliationResult:
        point = _aware(as_of, "as_of")
        policy = _text(policy_version, "policy_version")
        assertions = _refs(assertion_refs, "assertion_refs")
        relations = _refs(relation_refs, "relation_refs")
        projection_values = tuple(projections)
        if any(
            not isinstance(value, CurrentStateProjection)
            for value in projection_values
        ):
            raise StateReconciliationError(
                "projections must contain CurrentStateProjection values"
            )
        ordered = tuple(
            sorted(
                projection_values,
                key=lambda value: (
                    value.subject_ref.subject_id,
                    value.subject_ref.kind.value,
                    value.predicate,
                ),
            )
        )
        payload = {
            "policy_version": policy,
            "as_of": _canonical_datetime(point),
            "assertion_refs": list(assertions),
            "relation_refs": list(relations),
            "projection_ids": [value.projection_id for value in ordered],
        }
        return cls(
            result_id=_digest(payload),
            policy_version=policy,
            as_of=point,
            assertion_refs=assertions,
            relation_refs=relations,
            projections=ordered,
        )

    def payload(self) -> dict[str, object]:
        return {
            "policy_version": self.policy_version,
            "as_of": _canonical_datetime(self.as_of),
            "assertion_refs": list(self.assertion_refs),
            "relation_refs": list(self.relation_refs),
            "projection_ids": [
                value.projection_id for value in self.projections
            ],
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_json(self.payload()).encode("utf-8")


class StateReconciler:
    """Build deterministic, rebuildable state projections."""

    def reconcile(
        self,
        assertions: Iterable[AssertionRecord],
        relations: Iterable[AssertionRelation],
        *,
        as_of: datetime,
        policy_version: str = STATE_RECONCILIATION_POLICY_VERSION,
    ) -> StateReconciliationResult:
        point = _aware(as_of, "as_of")
        policy = _text(policy_version, "policy_version")

        assertion_by_id: dict[str, AssertionRecord] = {}
        for assertion in assertions:
            if not isinstance(assertion, AssertionRecord):
                raise StateReconciliationError(
                    "assertions must contain AssertionRecord values"
                )
            previous = assertion_by_id.get(assertion.assertion_id)
            if previous is not None and previous != assertion:
                raise StateReconciliationError(
                    "conflicting assertion snapshot: "
                    f"{assertion.assertion_id}"
                )
            assertion_by_id[assertion.assertion_id] = assertion

        relation_by_id: dict[str, AssertionRelation] = {}
        for relation in relations:
            if not isinstance(relation, AssertionRelation):
                raise StateReconciliationError(
                    "relations must contain AssertionRelation values"
                )
            previous_relation = relation_by_id.get(relation.relation_id)
            if previous_relation is not None and previous_relation != relation:
                raise StateReconciliationError(
                    "conflicting relation snapshot: "
                    f"{relation.relation_id}"
                )
            relation_by_id[relation.relation_id] = relation

        for relation in relation_by_id.values():
            source = assertion_by_id.get(relation.source_assertion_ref)
            target = assertion_by_id.get(relation.target_assertion_ref)
            if source is None or target is None:
                raise StateReconciliationError(
                    f"relation endpoint missing: {relation.relation_id}"
                )
            if relation.relation_type in _LIFECYCLE_RELATIONS:
                if _state_key(source) != _state_key(target):
                    raise StateReconciliationError(
                        "lifecycle relations must stay within one state key"
                    )
                if (
                    source.origin_type is OriginType.MODEL_INFERRED
                    and target.origin_type is not OriginType.MODEL_INFERRED
                ):
                    raise StateReconciliationError(
                        "MODEL_INFERRED cannot displace a non-inferred "
                        "assertion"
                    )

        grouped: dict[tuple[str, str, str], list[AssertionRecord]] = {}
        for assertion in assertion_by_id.values():
            grouped.setdefault(_state_key(assertion), []).append(assertion)

        relation_values = tuple(relation_by_id.values())
        projections = tuple(
            self._reconcile_group(
                values,
                relation_values,
                assertion_by_id,
                as_of=point,
                policy_version=policy,
            )
            for _, values in sorted(grouped.items())
        )
        return StateReconciliationResult.create(
            as_of=point,
            assertion_refs=assertion_by_id,
            relation_refs=relation_by_id,
            projections=projections,
            policy_version=policy,
        )

    def _reconcile_group(
        self,
        assertions: list[AssertionRecord],
        relations: tuple[AssertionRelation, ...],
        assertion_by_id: dict[str, AssertionRecord],
        *,
        as_of: datetime,
        policy_version: str,
    ) -> CurrentStateProjection:
        ordered = tuple(
            sorted(assertions, key=lambda value: value.assertion_id)
        )
        subject_ref = ordered[0].subject_ref
        predicate = ordered[0].predicate
        group_ids = {value.assertion_id for value in ordered}
        active = tuple(
            value for value in ordered if _is_active(value, as_of)
        )
        expired = tuple(
            value for value in ordered if _is_expired(value, as_of)
        )
        future = tuple(
            value for value in ordered if _is_future(value, as_of)
        )
        active_ids = {value.assertion_id for value in active}

        superseded: set[str] = set()
        retracted: set[str] = set()
        contradiction_pairs: set[tuple[str, str]] = set()
        support_sources: dict[str, set[str]] = {}
        correction_sources: set[str] = set()
        supersession_sources: set[str] = set()
        reasons: set[StateReason] = set()

        for relation in relations:
            if relation.created_at.astimezone(UTC) > as_of.astimezone(UTC):
                continue
            source = assertion_by_id[relation.source_assertion_ref]
            target = assertion_by_id[relation.target_assertion_ref]
            if (
                relation.source_assertion_ref not in group_ids
                and relation.target_assertion_ref not in group_ids
            ):
                continue

            if relation.relation_type is AssertionRelationType.CORRECTS:
                if source.assertion_id in active_ids:
                    superseded.add(target.assertion_id)
                    correction_sources.add(source.assertion_id)
                    reasons.add(StateReason.EXPLICIT_CORRECTION)
            elif relation.relation_type is AssertionRelationType.SUPERSEDES:
                if source.assertion_id in active_ids:
                    superseded.add(target.assertion_id)
                    supersession_sources.add(source.assertion_id)
                    reasons.add(StateReason.EXPLICIT_SUPERSESSION)
            elif relation.relation_type is AssertionRelationType.RETRACTS:
                if source.assertion_id in active_ids:
                    retracted.add(target.assertion_id)
                    reasons.add(StateReason.EXPLICIT_RETRACTION)
            elif relation.relation_type is AssertionRelationType.CONTRADICTS:
                if _is_active(source, as_of) and _is_active(target, as_of):
                    contradiction_pairs.add(
                        tuple(sorted((source.assertion_id, target.assertion_id)))
                    )
            elif relation.relation_type is AssertionRelationType.SUPPORTS:
                if _is_active(source, as_of) and _is_active(target, as_of):
                    support_sources.setdefault(target.assertion_id, set()).add(
                        source.assertion_id
                    )

        user_by_actor: dict[tuple[str, str], list[AssertionRecord]] = {}
        for assertion in active:
            if assertion.origin_type is OriginType.USER_STATED:
                actor_key = (
                    assertion.asserted_by.actor_id,
                    assertion.asserted_by.kind.value,
                )
                user_by_actor.setdefault(actor_key, []).append(assertion)

        for actor_assertions in user_by_actor.values():
            by_time = sorted(
                actor_assertions,
                key=lambda value: (
                    value.valid_from.astimezone(UTC),
                    value.recorded_at.astimezone(UTC),
                    value.assertion_id,
                ),
            )
            if len(by_time) < 2:
                continue
            latest = by_time[-1]
            for older in by_time[:-1]:
                if (
                    older.valid_from.astimezone(UTC)
                    < latest.valid_from.astimezone(UTC)
                ):
                    superseded.add(older.assertion_id)
                    supersession_sources.add(latest.assertion_id)
                    reasons.add(StateReason.NEWER_USER_STATEMENT)

        viable = tuple(
            value
            for value in active
            if value.assertion_id not in superseded
            and value.assertion_id not in retracted
        )
        if not viable:
            if active:
                status = ProjectionStatus.SUPERSEDED
                reasons.add(StateReason.ALL_ACTIVE_ASSERTIONS_DISPLACED)
            elif expired and future:
                status = ProjectionStatus.STALE
                reasons.add(StateReason.ONLY_EXPIRED_ASSERTIONS)
                reasons.add(StateReason.ONLY_FUTURE_ASSERTIONS)
            elif expired:
                status = ProjectionStatus.EXPIRED
                reasons.add(StateReason.ONLY_EXPIRED_ASSERTIONS)
            else:
                status = ProjectionStatus.UNRESOLVED
                reasons.add(StateReason.ONLY_FUTURE_ASSERTIONS)
            return CurrentStateProjection.create(
                subject_ref=subject_ref,
                predicate=predicate,
                as_of=as_of,
                status=status,
                selected_assertion_ref=None,
                superseded_assertion_refs=superseded,
                retracted_assertion_refs=retracted,
                expired_assertion_refs=(
                    value.assertion_id for value in expired
                ),
                future_assertion_refs=(
                    value.assertion_id for value in future
                ),
                reason_codes=reasons,
                review_required=status
                in (
                    ProjectionStatus.STALE,
                    ProjectionStatus.CONTESTED,
                    ProjectionStatus.UNRESOLVED,
                ),
                policy_version=policy_version,
            )

        reasons.add(StateReason.ACTIVE_ASSERTION)
        non_inferred = tuple(
            value
            for value in viable
            if value.origin_type is not OriginType.MODEL_INFERRED
        )
        candidate_pool = non_inferred or viable
        user_candidates = tuple(
            value
            for value in candidate_pool
            if value.origin_type is OriginType.USER_STATED
        )
        inferred = tuple(
            value
            for value in viable
            if value.origin_type is OriginType.MODEL_INFERRED
        )
        if user_candidates and inferred:
            reasons.add(
                StateReason.USER_STATEMENT_PREFERRED_OVER_INFERENCE
            )

        candidate_refs = {value.assertion_id for value in viable}
        supporting_refs: set[str] = set()
        contradiction_refs: set[str] = set()
        candidate_values = {_value_key(value) for value in candidate_pool}

        if len(candidate_values) > 1:
            reasons.add(StateReason.ACTIVE_VALUE_CONFLICT)
            contradiction_refs.update(
                value.assertion_id for value in candidate_pool
            )
            if contradiction_pairs:
                reasons.add(StateReason.EXPLICIT_CONTRADICTION)
            return CurrentStateProjection.create(
                subject_ref=subject_ref,
                predicate=predicate,
                as_of=as_of,
                status=ProjectionStatus.CONTESTED,
                selected_assertion_ref=None,
                candidate_assertion_refs=candidate_refs,
                contradiction_assertion_refs=contradiction_refs,
                superseded_assertion_refs=superseded,
                retracted_assertion_refs=retracted,
                expired_assertion_refs=(
                    value.assertion_id for value in expired
                ),
                future_assertion_refs=(
                    value.assertion_id for value in future
                ),
                reason_codes=reasons,
                review_required=True,
                policy_version=policy_version,
            )

        def selection_key(
            value: AssertionRecord,
        ) -> tuple[int, datetime, datetime, str]:
            relation_priority = 0
            if value.assertion_id in correction_sources:
                relation_priority = 3
            elif value.assertion_id in supersession_sources:
                relation_priority = 2
            return (
                relation_priority,
                value.valid_from.astimezone(UTC),
                value.recorded_at.astimezone(UTC),
                value.assertion_id,
            )

        selected = max(candidate_pool, key=selection_key)
        selected_value = _value_key(selected)
        for value in viable:
            if value.assertion_id == selected.assertion_id:
                continue
            if _value_key(value) == selected_value:
                supporting_refs.add(value.assertion_id)
            else:
                contradiction_refs.add(value.assertion_id)

        supporting_refs.update(
            support_sources.get(selected.assertion_id, set())
        )
        supporting_refs.discard(selected.assertion_id)
        for pair in contradiction_pairs:
            if selected.assertion_id in pair:
                contradiction_refs.update(pair)
                contradiction_refs.discard(selected.assertion_id)

        if supporting_refs:
            reasons.add(StateReason.SAME_VALUE_CORROBORATION)
        if contradiction_refs:
            reasons.add(StateReason.ACTIVE_VALUE_CONFLICT)
        if any(selected.assertion_id in pair for pair in contradiction_pairs):
            reasons.add(StateReason.EXPLICIT_CONTRADICTION)

        status = (
            ProjectionStatus.CONTESTED
            if contradiction_refs
            else ProjectionStatus.CURRENT
        )
        return CurrentStateProjection.create(
            subject_ref=subject_ref,
            predicate=predicate,
            as_of=as_of,
            status=status,
            selected_assertion_ref=selected.assertion_id,
            candidate_assertion_refs=candidate_refs,
            supporting_assertion_refs=supporting_refs,
            contradiction_assertion_refs=contradiction_refs,
            superseded_assertion_refs=superseded,
            retracted_assertion_refs=retracted,
            expired_assertion_refs=(
                value.assertion_id for value in expired
            ),
            future_assertion_refs=(
                value.assertion_id for value in future
            ),
            reason_codes=reasons,
            review_required=status is ProjectionStatus.CONTESTED,
            policy_version=policy_version,
        )


__all__ = [
    "STATE_PROJECTION_SCHEMA_VERSION",
    "STATE_RECONCILIATION_POLICY_VERSION",
    "CurrentStateProjection",
    "ProjectionStatus",
    "StateReason",
    "StateReconciler",
    "StateReconciliationError",
    "StateReconciliationResult",
]
