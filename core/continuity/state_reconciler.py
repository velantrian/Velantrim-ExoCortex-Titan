"""Deterministic current-state projections over immutable assertions.

Projection only: no ESM mutation, TruthGate call, Canon write, retrieval,
advisory decision, action authorization, or processing-mode ownership.
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
    """State inputs cannot be reconciled without ambiguity or invariant loss."""


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


_LIFECYCLE = {
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
        raise StateReconciliationError(f"{name} cannot contain duplicates")
    return tuple(sorted(result))


def _reasons(values: Iterable[StateReason]) -> tuple[StateReason, ...]:
    result = tuple(values)
    if any(not isinstance(value, StateReason) for value in result):
        raise StateReconciliationError("reason_codes contain an invalid value")
    mapping = {value.value: value for value in result}
    if len(mapping) != len(result):
        raise StateReconciliationError("reason_codes cannot contain duplicates")
    return tuple(mapping[key] for key in sorted(mapping))


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
    return _json({"type": type_name, "value": value})


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
        "schema_version": STATE_PROJECTION_SCHEMA_VERSION,
        "policy_version": policy_version,
        "subject_ref": subject_ref.identity_payload(),
        "predicate": predicate,
        "as_of": _dt(as_of),
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
        if not isinstance(subject_ref, SubjectRef):
            raise StateReconciliationError("subject_ref must be a SubjectRef")
        if not isinstance(status, ProjectionStatus):
            raise StateReconciliationError("status must be a ProjectionStatus")
        if not isinstance(review_required, bool):
            raise StateReconciliationError("review_required must be a bool")
        predicate_value = _text(predicate, "predicate")
        point = _aware(as_of, "as_of")
        policy = _text(policy_version, "policy_version")
        selected = (
            _text(selected_assertion_ref, "selected_assertion_ref")
            if selected_assertion_ref is not None
            else None
        )
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
        all_refs = set(candidates + supporting + contradictions)
        all_refs.update(superseded + retracted + expired + future)
        if selected is not None and selected not in all_refs:
            raise StateReconciliationError(
                "selected_assertion_ref must be represented in projection refs"
            )
        if status is ProjectionStatus.CURRENT and selected is None:
            raise StateReconciliationError(
                "CURRENT projection requires a selected assertion"
            )
        if status in (
            ProjectionStatus.EXPIRED,
            ProjectionStatus.UNRESOLVED,
        ) and selected is not None:
            raise StateReconciliationError(
                "EXPIRED/UNRESOLVED projection cannot select an assertion"
            )
        payload = _projection_payload(
            policy_version=policy,
            subject_ref=subject_ref,
            predicate=predicate_value,
            as_of=point,
            status=status,
            selected_assertion_ref=selected,
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
            projection_id=_hash(payload),
            schema_version=STATE_PROJECTION_SCHEMA_VERSION,
            policy_version=policy,
            subject_ref=subject_ref,
            predicate=predicate_value,
            as_of=point,
            status=status,
            selected_assertion_ref=selected,
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
        return _json(self.payload()).encode("utf-8")


@dataclass(frozen=True, slots=True)
class StateReconciliationResult:
    result_id: str
    policy_version: str
    as_of: datetime
    assertion_refs: tuple[str, ...]
    relation_refs: tuple[str, ...]
    projections: tuple[CurrentStateProjection, ...]

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
        assertion_ids = _refs(assertion_refs, "assertion_refs")
        relation_ids = _refs(relation_refs, "relation_refs")
        values = tuple(projections)
        if any(
            not isinstance(value, CurrentStateProjection)
            for value in values
        ):
            raise StateReconciliationError(
                "projections must contain CurrentStateProjection values"
            )
        ordered = tuple(
            sorted(
                values,
                key=lambda value: (
                    value.subject_ref.subject_id,
                    value.subject_ref.kind.value,
                    value.predicate,
                ),
            )
        )
        payload = {
            "policy_version": policy,
            "as_of": _dt(point),
            "assertion_refs": list(assertion_ids),
            "relation_refs": list(relation_ids),
            "projection_ids": [value.projection_id for value in ordered],
        }
        return cls(
            result_id=_hash(payload),
            policy_version=policy,
            as_of=point,
            assertion_refs=assertion_ids,
            relation_refs=relation_ids,
            projections=ordered,
        )

    def payload(self) -> dict[str, object]:
        return {
            "policy_version": self.policy_version,
            "as_of": _dt(self.as_of),
            "assertion_refs": list(self.assertion_refs),
            "relation_refs": list(self.relation_refs),
            "projection_ids": [
                value.projection_id for value in self.projections
            ],
        }

    def canonical_bytes(self) -> bytes:
        return _json(self.payload()).encode("utf-8")


class StateReconciler:
    """Build deterministic rebuildable projections from immutable inputs."""

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
        assertion_by_id = self._assertion_map(assertions)
        relation_by_id = self._relation_map(relations)
        self._validate_relations(assertion_by_id, relation_by_id)

        grouped: dict[tuple[str, str, str], list[AssertionRecord]] = {}
        for assertion in assertion_by_id.values():
            grouped.setdefault(_state_key(assertion), []).append(assertion)
        relation_values = tuple(relation_by_id.values())
        projections = tuple(
            self._reconcile_group(
                group,
                relation_values,
                assertion_by_id,
                as_of=point,
                policy_version=policy,
            )
            for _, group in sorted(grouped.items())
        )
        return StateReconciliationResult.create(
            as_of=point,
            assertion_refs=assertion_by_id,
            relation_refs=relation_by_id,
            projections=projections,
            policy_version=policy,
        )

    @staticmethod
    def _assertion_map(
        assertions: Iterable[AssertionRecord],
    ) -> dict[str, AssertionRecord]:
        result: dict[str, AssertionRecord] = {}
        for assertion in assertions:
            if not isinstance(assertion, AssertionRecord):
                raise StateReconciliationError(
                    "assertions must contain AssertionRecord values"
                )
            previous = result.get(assertion.assertion_id)
            if previous is not None and previous != assertion:
                raise StateReconciliationError(
                    f"conflicting assertion snapshot: {assertion.assertion_id}"
                )
            result[assertion.assertion_id] = assertion
        return result

    @staticmethod
    def _relation_map(
        relations: Iterable[AssertionRelation],
    ) -> dict[str, AssertionRelation]:
        result: dict[str, AssertionRelation] = {}
        for relation in relations:
            if not isinstance(relation, AssertionRelation):
                raise StateReconciliationError(
                    "relations must contain AssertionRelation values"
                )
            previous = result.get(relation.relation_id)
            if previous is not None and previous != relation:
                raise StateReconciliationError(
                    f"conflicting relation snapshot: {relation.relation_id}"
                )
            result[relation.relation_id] = relation
        return result

    @staticmethod
    def _validate_relations(
        assertions: dict[str, AssertionRecord],
        relations: dict[str, AssertionRelation],
    ) -> None:
        for relation in relations.values():
            source = assertions.get(relation.source_assertion_ref)
            target = assertions.get(relation.target_assertion_ref)
            if source is None or target is None:
                raise StateReconciliationError(
                    f"relation endpoint missing: {relation.relation_id}"
                )
            if relation.relation_type not in _LIFECYCLE:
                continue
            if _state_key(source) != _state_key(target):
                raise StateReconciliationError(
                    "lifecycle relations must stay within one state key"
                )
            if (
                source.origin_type is OriginType.MODEL_INFERRED
                and target.origin_type is not OriginType.MODEL_INFERRED
            ):
                raise StateReconciliationError(
                    "MODEL_INFERRED cannot displace a non-inferred assertion"
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
        subject = ordered[0].subject_ref
        predicate = ordered[0].predicate
        group_ids = {value.assertion_id for value in ordered}
        active = tuple(value for value in ordered if _is_active(value, as_of))
        expired = tuple(value for value in ordered if _is_expired(value, as_of))
        future = tuple(value for value in ordered if _is_future(value, as_of))
        active_ids = {value.assertion_id for value in active}

        superseded: set[str] = set()
        retracted: set[str] = set()
        correction_sources: set[str] = set()
        supersession_sources: set[str] = set()
        support_sources: dict[str, set[str]] = {}
        contradiction_pairs: set[tuple[str, str]] = set()
        reasons: set[StateReason] = set()

        for relation in relations:
            if relation.created_at.astimezone(UTC) > as_of.astimezone(UTC):
                continue
            if (
                relation.source_assertion_ref not in group_ids
                and relation.target_assertion_ref not in group_ids
            ):
                continue
            source = assertion_by_id[relation.source_assertion_ref]
            target = assertion_by_id[relation.target_assertion_ref]
            kind = relation.relation_type
            if kind is AssertionRelationType.CORRECTS:
                if source.assertion_id in active_ids:
                    superseded.add(target.assertion_id)
                    correction_sources.add(source.assertion_id)
                    reasons.add(StateReason.EXPLICIT_CORRECTION)
            elif kind is AssertionRelationType.SUPERSEDES:
                if source.assertion_id in active_ids:
                    superseded.add(target.assertion_id)
                    supersession_sources.add(source.assertion_id)
                    reasons.add(StateReason.EXPLICIT_SUPERSESSION)
            elif kind is AssertionRelationType.RETRACTS:
                if source.assertion_id in active_ids:
                    retracted.add(target.assertion_id)
                    reasons.add(StateReason.EXPLICIT_RETRACTION)
            elif kind is AssertionRelationType.SUPPORTS:
                if _is_active(source, as_of) and _is_active(target, as_of):
                    support_sources.setdefault(target.assertion_id, set()).add(
                        source.assertion_id
                    )
            elif kind is AssertionRelationType.CONTRADICTS:
                if _is_active(source, as_of) and _is_active(target, as_of):
                    first_id, second_id = sorted(
                        (source.assertion_id, target.assertion_id)
                    )
                    contradiction_pairs.add((first_id, second_id))

        self._apply_user_succession(
            active,
            superseded,
            supersession_sources,
            reasons,
        )
        viable = tuple(
            value
            for value in active
            if value.assertion_id not in superseded
            and value.assertion_id not in retracted
        )
        if not viable:
            return self._empty_projection(
                subject=subject,
                predicate=predicate,
                as_of=as_of,
                active=active,
                expired=expired,
                future=future,
                superseded=superseded,
                retracted=retracted,
                reasons=reasons,
                policy_version=policy_version,
            )

        reasons.add(StateReason.ACTIVE_ASSERTION)
        non_inferred = tuple(
            value
            for value in viable
            if value.origin_type is not OriginType.MODEL_INFERRED
        )
        pool = non_inferred or viable
        user_values = tuple(
            value
            for value in pool
            if value.origin_type is OriginType.USER_STATED
        )
        inferred = tuple(
            value
            for value in viable
            if value.origin_type is OriginType.MODEL_INFERRED
        )
        if user_values and inferred:
            reasons.add(
                StateReason.USER_STATEMENT_PREFERRED_OVER_INFERENCE
            )

        candidates = {value.assertion_id for value in viable}
        pool_values = {_value_key(value) for value in pool}
        if len(pool_values) > 1:
            reasons.add(StateReason.ACTIVE_VALUE_CONFLICT)
            if contradiction_pairs:
                reasons.add(StateReason.EXPLICIT_CONTRADICTION)
            return CurrentStateProjection.create(
                subject_ref=subject,
                predicate=predicate,
                as_of=as_of,
                status=ProjectionStatus.CONTESTED,
                selected_assertion_ref=None,
                candidate_assertion_refs=candidates,
                contradiction_assertion_refs=(
                    value.assertion_id for value in pool
                ),
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

        selected = max(
            pool,
            key=lambda value: self._selection_key(
                value,
                correction_sources,
                supersession_sources,
            ),
        )
        supporting: set[str] = set()
        contradictions: set[str] = set()
        selected_value = _value_key(selected)
        for value in viable:
            if value.assertion_id == selected.assertion_id:
                continue
            if _value_key(value) == selected_value:
                supporting.add(value.assertion_id)
            else:
                contradictions.add(value.assertion_id)
        supporting.update(support_sources.get(selected.assertion_id, set()))
        supporting.discard(selected.assertion_id)
        for pair in contradiction_pairs:
            if selected.assertion_id in pair:
                contradictions.update(pair)
                contradictions.discard(selected.assertion_id)

        if supporting:
            reasons.add(StateReason.SAME_VALUE_CORROBORATION)
        if contradictions:
            reasons.add(StateReason.ACTIVE_VALUE_CONFLICT)
        if any(selected.assertion_id in pair for pair in contradiction_pairs):
            reasons.add(StateReason.EXPLICIT_CONTRADICTION)
        status = (
            ProjectionStatus.CONTESTED
            if contradictions
            else ProjectionStatus.CURRENT
        )
        return CurrentStateProjection.create(
            subject_ref=subject,
            predicate=predicate,
            as_of=as_of,
            status=status,
            selected_assertion_ref=selected.assertion_id,
            candidate_assertion_refs=candidates,
            supporting_assertion_refs=supporting,
            contradiction_assertion_refs=contradictions,
            superseded_assertion_refs=superseded,
            retracted_assertion_refs=retracted,
            expired_assertion_refs=(
                value.assertion_id for value in expired
            ),
            future_assertion_refs=(value.assertion_id for value in future),
            reason_codes=reasons,
            review_required=status is ProjectionStatus.CONTESTED,
            policy_version=policy_version,
        )

    @staticmethod
    def _apply_user_succession(
        active: tuple[AssertionRecord, ...],
        superseded: set[str],
        sources: set[str],
        reasons: set[StateReason],
    ) -> None:
        by_actor: dict[tuple[str, str], list[AssertionRecord]] = {}
        for assertion in active:
            if assertion.origin_type is OriginType.USER_STATED:
                key = (
                    assertion.asserted_by.actor_id,
                    assertion.asserted_by.kind.value,
                )
                by_actor.setdefault(key, []).append(assertion)
        for values in by_actor.values():
            ordered = sorted(
                values,
                key=lambda value: (
                    value.valid_from.astimezone(UTC),
                    value.recorded_at.astimezone(UTC),
                    value.assertion_id,
                ),
            )
            if len(ordered) < 2:
                continue
            latest = ordered[-1]
            for older in ordered[:-1]:
                if (
                    older.valid_from.astimezone(UTC)
                    < latest.valid_from.astimezone(UTC)
                ):
                    superseded.add(older.assertion_id)
                    sources.add(latest.assertion_id)
                    reasons.add(StateReason.NEWER_USER_STATEMENT)

    @staticmethod
    def _selection_key(
        value: AssertionRecord,
        correction_sources: set[str],
        supersession_sources: set[str],
    ) -> tuple[int, datetime, datetime, str]:
        priority = 0
        if value.assertion_id in correction_sources:
            priority = 3
        elif value.assertion_id in supersession_sources:
            priority = 2
        return (
            priority,
            value.valid_from.astimezone(UTC),
            value.recorded_at.astimezone(UTC),
            value.assertion_id,
        )

    @staticmethod
    def _empty_projection(
        *,
        subject: SubjectRef,
        predicate: str,
        as_of: datetime,
        active: tuple[AssertionRecord, ...],
        expired: tuple[AssertionRecord, ...],
        future: tuple[AssertionRecord, ...],
        superseded: set[str],
        retracted: set[str],
        reasons: set[StateReason],
        policy_version: str,
    ) -> CurrentStateProjection:
        if active:
            status = ProjectionStatus.SUPERSEDED
            reasons.add(StateReason.ALL_ACTIVE_ASSERTIONS_DISPLACED)
        elif expired and future:
            status = ProjectionStatus.STALE
            reasons.update(
                {
                    StateReason.ONLY_EXPIRED_ASSERTIONS,
                    StateReason.ONLY_FUTURE_ASSERTIONS,
                }
            )
        elif expired:
            status = ProjectionStatus.EXPIRED
            reasons.add(StateReason.ONLY_EXPIRED_ASSERTIONS)
        else:
            status = ProjectionStatus.UNRESOLVED
            reasons.add(StateReason.ONLY_FUTURE_ASSERTIONS)
        return CurrentStateProjection.create(
            subject_ref=subject,
            predicate=predicate,
            as_of=as_of,
            status=status,
            selected_assertion_ref=None,
            superseded_assertion_refs=superseded,
            retracted_assertion_refs=retracted,
            expired_assertion_refs=(
                value.assertion_id for value in expired
            ),
            future_assertion_refs=(value.assertion_id for value in future),
            reason_codes=reasons,
            review_required=status
            in {
                ProjectionStatus.STALE,
                ProjectionStatus.CONTESTED,
                ProjectionStatus.UNRESOLVED,
            },
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
