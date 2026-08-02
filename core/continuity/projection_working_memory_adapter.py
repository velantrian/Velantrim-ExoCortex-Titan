"""Typed adapter from continuity projections into the existing Synaptic Gate.

This adapter converts already-built state, goal, and open-loop projections into
source-linked KnowledgeCapsules and WorkingMemoryCandidates. It does not score,
retrieve, persist, write Canon, invoke the Gate, build ContextPack, or alter the
answer path.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import math
from typing import Iterable

from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.working_memory_gate import WorkingMemoryCandidate

from .contracts import AssertionRecord, OriginType
from .goal_open_loop import (
    GoalProjection,
    GoalStatus,
    OpenLoopProjection,
    OpenLoopStatus,
)
from .state_reconciler import CurrentStateProjection, ProjectionStatus

PROJECTION_ADAPTER_ID = "continuity-projection-working-memory-adapter"
PROJECTION_ADAPTER_VERSION = "continuity-projection-working-memory-adapter.v1"


class ProjectionWorkingMemoryAdapterError(ValueError):
    """Projection input cannot be adapted without violating a boundary."""


class ProjectionKind(str, Enum):
    CURRENT_STATE = "current_state"
    GOAL = "goal"
    OPEN_LOOP = "open_loop"


class ProjectionOmissionReason(str, Enum):
    STATE_HAS_NO_SELECTED_ASSERTION = "state_has_no_selected_assertion"
    STATE_NOT_CURRENTLY_USABLE = "state_not_currently_usable"
    GOAL_NOT_ACTIVE = "goal_not_active"
    OPEN_LOOP_NOT_ACTIVE = "open_loop_not_active"


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectionWorkingMemoryAdapterError(
            f"{name} must be a non-empty string"
        )
    return value


def _score(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProjectionWorkingMemoryAdapterError(
            f"{name} must be a finite number in [0, 1]"
        )
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ProjectionWorkingMemoryAdapterError(
            f"{name} must be a finite number in [0, 1]"
        )
    return result


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ProjectionWorkingMemoryAdapterError(f"{name} must be a bool")
    return value


def _render_value(value: str | int | float | bool | None) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


@dataclass(frozen=True, slots=True)
class ProjectionGatePolicy:
    projection_id: str
    attention_score: float
    recall_allowed: bool
    eligible: bool
    restricted: bool
    erased: bool
    protected: bool
    conflict: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "projection_id", _text(self.projection_id, "projection_id")
        )
        object.__setattr__(
            self,
            "attention_score",
            _score(self.attention_score, "attention_score"),
        )
        for name in (
            "recall_allowed",
            "eligible",
            "restricted",
            "erased",
            "protected",
            "conflict",
        ):
            object.__setattr__(
                self, name, _strict_bool(getattr(self, name), name)
            )


@dataclass(frozen=True, slots=True)
class ProjectionBinding:
    projection_id: str
    projection_kind: ProjectionKind
    capsule_id: str
    virtual_document_id: str
    source_span_id: str
    source_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectionOmission:
    projection_id: str
    projection_kind: ProjectionKind
    reason: ProjectionOmissionReason


@dataclass(frozen=True, slots=True)
class ProjectionWorkingMemoryBatch:
    candidates: tuple[WorkingMemoryCandidate, ...]
    bindings: tuple[ProjectionBinding, ...]
    omissions: tuple[ProjectionOmission, ...]

    def __post_init__(self) -> None:
        candidates = tuple(
            sorted(
                self.candidates,
                key=lambda value: str(value.metadata["projection_id"]),
            )
        )
        bindings = tuple(
            sorted(self.bindings, key=lambda value: value.projection_id)
        )
        omissions = tuple(
            sorted(self.omissions, key=lambda value: value.projection_id)
        )
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "bindings", bindings)
        object.__setattr__(self, "omissions", omissions)
        candidate_ids = tuple(
            str(value.metadata["projection_id"]) for value in candidates
        )
        binding_ids = tuple(value.projection_id for value in bindings)
        if candidate_ids != binding_ids:
            raise ProjectionWorkingMemoryAdapterError(
                "every candidate must have exactly one ordered binding"
            )
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ProjectionWorkingMemoryAdapterError(
                "candidate projection ids must be unique"
            )
        omitted_ids = {value.projection_id for value in omissions}
        if set(candidate_ids) & omitted_ids:
            raise ProjectionWorkingMemoryAdapterError(
                "a projection cannot be adapted and omitted"
            )

    @property
    def capsules(self) -> tuple[KnowledgeCapsule, ...]:
        return tuple(value.capsule for value in self.candidates)


def _modality_for_origin(origin: OriginType) -> ClaimModality:
    if origin is OriginType.USER_STATED:
        return ClaimModality.USER_REPORT
    if origin is OriginType.MODEL_INFERRED:
        return ClaimModality.HYPOTHESIS
    if origin in {OriginType.SYSTEM_OBSERVED, OriginType.SYSTEM_MEASURED}:
        return ClaimModality.OBSERVATION
    return ClaimModality.INTERPRETATION


def _capsule(
    *,
    projection_id: str,
    kind: ProjectionKind,
    text: str,
    modality: ClaimModality,
    source_refs: tuple[str, ...],
    uncertainty_codes: tuple[str, ...],
    created_at,
) -> tuple[KnowledgeCapsule, SourceSpan]:
    document_id = f"continuity_projection:{kind.value}:{projection_id}"
    span = SourceSpan.from_text(
        document_id=document_id,
        raw_text=text,
        start_offset=0,
        end_offset=len(text),
        source_revision=projection_id,
    )
    claim = CapsuleClaim.create(
        text=text,
        modality=modality,
        source_spans=(span,),
        extraction_confidence=1.0,
        truth_confidence=None,
        qualifiers=tuple(f"source_ref:{value}" for value in source_refs),
        uncertainties=("projection_not_canon", *uncertainty_codes),
    )
    capsule = KnowledgeCapsule.create(
        source_document_id=document_id,
        essence=text,
        claims=(claim,),
        reader_id=PROJECTION_ADAPTER_ID,
        reader_version=PROJECTION_ADAPTER_VERSION,
        coverage_score=1.0,
        compression_ratio=1.0,
        created_at=created_at,
    )
    return capsule, span


class ProjectionWorkingMemoryAdapter:
    """Convert typed projections into policy-ready Gate candidates."""

    def adapt(
        self,
        *,
        state_projections: Iterable[CurrentStateProjection] = (),
        assertions: Iterable[AssertionRecord] = (),
        goal_projections: Iterable[GoalProjection] = (),
        open_loop_projections: Iterable[OpenLoopProjection] = (),
        policies: Iterable[ProjectionGatePolicy] = (),
    ) -> ProjectionWorkingMemoryBatch:
        assertion_map = self._assertion_map(assertions)
        states = self._unique_projection_map(
            state_projections, CurrentStateProjection, "state projection"
        )
        goals = self._unique_projection_map(
            goal_projections, GoalProjection, "goal projection"
        )
        loops = self._unique_projection_map(
            open_loop_projections, OpenLoopProjection, "open-loop projection"
        )
        all_ids = set(states) | set(goals) | set(loops)
        if len(all_ids) != len(states) + len(goals) + len(loops):
            raise ProjectionWorkingMemoryAdapterError(
                "projection ids must be globally unique"
            )

        adaptable_ids = self._adaptable_ids(states, goals, loops)
        policy_map: dict[str, ProjectionGatePolicy] = {}
        for policy in policies:
            if not isinstance(policy, ProjectionGatePolicy):
                raise ProjectionWorkingMemoryAdapterError(
                    "policies contain an invalid value"
                )
            if policy.projection_id in policy_map:
                raise ProjectionWorkingMemoryAdapterError(
                    f"duplicate policy: {policy.projection_id}"
                )
            policy_map[policy.projection_id] = policy
        if set(policy_map) != adaptable_ids:
            missing = sorted(adaptable_ids - set(policy_map))
            unexpected = sorted(set(policy_map) - adaptable_ids)
            raise ProjectionWorkingMemoryAdapterError(
                f"policy/projection mismatch: missing={missing}, "
                f"unexpected={unexpected}"
            )

        candidates: list[WorkingMemoryCandidate] = []
        bindings: list[ProjectionBinding] = []
        omissions: list[ProjectionOmission] = []

        for projection in states.values():
            if projection.selected_assertion_ref is None:
                reason = (
                    ProjectionOmissionReason.STATE_HAS_NO_SELECTED_ASSERTION
                    if projection.status is ProjectionStatus.CONTESTED
                    else ProjectionOmissionReason.STATE_NOT_CURRENTLY_USABLE
                )
                omissions.append(
                    ProjectionOmission(
                        projection.projection_id,
                        ProjectionKind.CURRENT_STATE,
                        reason,
                    )
                )
                continue
            assertion = assertion_map.get(projection.selected_assertion_ref)
            if assertion is None:
                raise ProjectionWorkingMemoryAdapterError(
                    "selected state assertion is missing"
                )
            if (
                assertion.subject_ref != projection.subject_ref
                or assertion.predicate != projection.predicate
            ):
                raise ProjectionWorkingMemoryAdapterError(
                    "selected assertion does not match state projection"
                )
            text = f"{projection.predicate}: {_render_value(assertion.value)}"
            source_refs = tuple(sorted(set(assertion.source_refs)))
            uncertainty = (
                f"projection_status:{projection.status.value}",
                *(f"state_reason:{value.value}" for value in projection.reason_codes),
            )
            capsule, span = _capsule(
                projection_id=projection.projection_id,
                kind=ProjectionKind.CURRENT_STATE,
                text=text,
                modality=_modality_for_origin(assertion.origin_type),
                source_refs=source_refs,
                uncertainty_codes=tuple(uncertainty),
                created_at=assertion.recorded_at,
            )
            policy = policy_map[projection.projection_id]
            candidate = self._candidate(
                capsule,
                policy,
                projection.projection_id,
                ProjectionKind.CURRENT_STATE,
                source_refs,
                forced_conflict=projection.status is ProjectionStatus.CONTESTED,
            )
            candidates.append(candidate)
            bindings.append(
                self._binding(
                    projection.projection_id,
                    ProjectionKind.CURRENT_STATE,
                    capsule,
                    span,
                    source_refs,
                )
            )

        for projection in goals.values():
            if projection.status is not GoalStatus.ACTIVE:
                omissions.append(
                    ProjectionOmission(
                        projection.projection_id,
                        ProjectionKind.GOAL,
                        ProjectionOmissionReason.GOAL_NOT_ACTIVE,
                    )
                )
                continue
            text = projection.title
            if projection.description:
                text = f"{projection.title}\n{projection.description}"
            uncertainty = (
                "goal_projection_requires_currentness_check",
                f"goal_basis:{projection.basis.value}",
            )
            capsule, span = _capsule(
                projection_id=projection.projection_id,
                kind=ProjectionKind.GOAL,
                text=text,
                modality=ClaimModality.GOAL,
                source_refs=projection.source_refs,
                uncertainty_codes=uncertainty,
                created_at=projection.updated_at,
            )
            policy = policy_map[projection.projection_id]
            candidates.append(
                self._candidate(
                    capsule,
                    policy,
                    projection.projection_id,
                    ProjectionKind.GOAL,
                    projection.source_refs,
                )
            )
            bindings.append(
                self._binding(
                    projection.projection_id,
                    ProjectionKind.GOAL,
                    capsule,
                    span,
                    projection.source_refs,
                )
            )

        for projection in loops.values():
            if projection.status not in {
                OpenLoopStatus.OPEN,
                OpenLoopStatus.OVERDUE,
            }:
                omissions.append(
                    ProjectionOmission(
                        projection.projection_id,
                        ProjectionKind.OPEN_LOOP,
                        ProjectionOmissionReason.OPEN_LOOP_NOT_ACTIVE,
                    )
                )
                continue
            uncertainty = (
                f"open_loop_status:{projection.status.value}",
                *(f"open_loop_reason:{value.value}" for value in projection.reason_codes),
            )
            capsule, span = _capsule(
                projection_id=projection.projection_id,
                kind=ProjectionKind.OPEN_LOOP,
                text=projection.summary,
                modality=ClaimModality.INTERPRETATION,
                source_refs=projection.source_refs,
                uncertainty_codes=tuple(uncertainty),
                created_at=projection.opened_at,
            )
            policy = policy_map[projection.projection_id]
            candidates.append(
                self._candidate(
                    capsule,
                    policy,
                    projection.projection_id,
                    ProjectionKind.OPEN_LOOP,
                    projection.source_refs,
                )
            )
            bindings.append(
                self._binding(
                    projection.projection_id,
                    ProjectionKind.OPEN_LOOP,
                    capsule,
                    span,
                    projection.source_refs,
                )
            )

        return ProjectionWorkingMemoryBatch(
            tuple(candidates), tuple(bindings), tuple(omissions)
        )

    @staticmethod
    def _assertion_map(
        assertions: Iterable[AssertionRecord],
    ) -> dict[str, AssertionRecord]:
        result: dict[str, AssertionRecord] = {}
        for assertion in assertions:
            if not isinstance(assertion, AssertionRecord):
                raise ProjectionWorkingMemoryAdapterError(
                    "assertions contain an invalid value"
                )
            existing = result.get(assertion.assertion_id)
            if existing is not None and existing != assertion:
                raise ProjectionWorkingMemoryAdapterError(
                    f"conflicting assertion: {assertion.assertion_id}"
                )
            result[assertion.assertion_id] = assertion
        return result

    @staticmethod
    def _unique_projection_map(values, expected_type, label):
        result = {}
        for value in values:
            if not isinstance(value, expected_type):
                raise ProjectionWorkingMemoryAdapterError(
                    f"{label}s contain an invalid value"
                )
            existing = result.get(value.projection_id)
            if existing is not None and existing != value:
                raise ProjectionWorkingMemoryAdapterError(
                    f"conflicting {label}: {value.projection_id}"
                )
            result[value.projection_id] = value
        return result

    @staticmethod
    def _adaptable_ids(states, goals, loops) -> set[str]:
        result = {
            value.projection_id
            for value in states.values()
            if value.selected_assertion_ref is not None
        }
        result.update(
            value.projection_id
            for value in goals.values()
            if value.status is GoalStatus.ACTIVE
        )
        result.update(
            value.projection_id
            for value in loops.values()
            if value.status in {OpenLoopStatus.OPEN, OpenLoopStatus.OVERDUE}
        )
        return result

    @staticmethod
    def _candidate(
        capsule: KnowledgeCapsule,
        policy: ProjectionGatePolicy,
        projection_id: str,
        kind: ProjectionKind,
        source_refs: tuple[str, ...],
        *,
        forced_conflict: bool = False,
    ) -> WorkingMemoryCandidate:
        return WorkingMemoryCandidate(
            capsule=capsule,
            attention_score=policy.attention_score,
            recall_allowed=policy.recall_allowed,
            eligible=policy.eligible,
            restricted=policy.restricted,
            erased=policy.erased,
            protected=policy.protected,
            conflict=policy.conflict or forced_conflict,
            metadata={
                "projection_id": projection_id,
                "projection_kind": kind.value,
                "source_refs": source_refs,
            },
        )

    @staticmethod
    def _binding(
        projection_id: str,
        kind: ProjectionKind,
        capsule: KnowledgeCapsule,
        span: SourceSpan,
        source_refs: tuple[str, ...],
    ) -> ProjectionBinding:
        return ProjectionBinding(
            projection_id=projection_id,
            projection_kind=kind,
            capsule_id=capsule.capsule_id,
            virtual_document_id=capsule.source_document_id,
            source_span_id=span.span_id,
            source_refs=tuple(sorted(set(source_refs))),
        )


__all__ = [
    "PROJECTION_ADAPTER_ID",
    "PROJECTION_ADAPTER_VERSION",
    "ProjectionBinding",
    "ProjectionGatePolicy",
    "ProjectionKind",
    "ProjectionOmission",
    "ProjectionOmissionReason",
    "ProjectionWorkingMemoryAdapter",
    "ProjectionWorkingMemoryAdapterError",
    "ProjectionWorkingMemoryBatch",
]
