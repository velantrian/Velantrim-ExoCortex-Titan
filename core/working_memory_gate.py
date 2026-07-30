"""Deterministic, read-only Working Memory Gate for Synaptic Exo-Cortex.

The Gate consumes policy-approved ``KnowledgeCapsule`` candidates and an
attention score computed upstream. It does not retrieve, rescore, persist,
promote, delete, or mutate knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from types import MappingProxyType
from typing import Iterable, Mapping

from core.knowledge_capsule import KnowledgeCapsule


class GateDisposition(str, Enum):
    """Exactly one bounded disposition for every candidate capsule."""

    ACTIVE = "active"
    COMPRESS = "compress"
    DEFER = "defer"
    QUARANTINE = "quarantine"
    EXCLUDE = "exclude"


class GateReason(str, Enum):
    """Structured, stable explanations for Gate decisions."""

    ERASED = "erased"
    RESTRICTED = "restricted"
    RECALL_DENIED = "recall_denied"
    INELIGIBLE = "ineligible"
    CONFLICT = "conflict"
    PROTECTED = "protected"
    FULL_CONTENT_SELECTED = "full_content_selected"
    ESSENCE_SELECTED = "essence_selected"
    ESSENCE_NOT_SOURCE_LINKED = "essence_not_source_linked"
    COMPRESSED_SEMANTICS_UNSUPPORTED = "compressed_semantics_unsupported"
    SCORE_BELOW_ACTIVE = "score_below_active"
    SCORE_BELOW_COMPRESS = "score_below_compress"
    FULL_CONTENT_OVER_BUDGET = "full_content_over_budget"
    ITEM_BUDGET_EXHAUSTED = "item_budget_exhausted"
    CHAR_BUDGET_EXHAUSTED = "char_budget_exhausted"


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _score(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return result


def _non_negative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a bool")
    return value


@dataclass(frozen=True, slots=True)
class WorkingMemoryBudget:
    """Hard cap for selected ACTIVE and COMPRESS representations."""

    max_items: int = 12
    max_chars: int = 4_000

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "max_items", _positive_int(self.max_items, "max_items")
        )
        object.__setattr__(
            self, "max_chars", _positive_int(self.max_chars, "max_chars")
        )


@dataclass(frozen=True, slots=True)
class WorkingMemoryCandidate:
    """Typed Gate input; ranking and policy facts are supplied upstream."""

    capsule: KnowledgeCapsule
    attention_score: float
    recall_allowed: bool
    eligible: bool
    restricted: bool
    erased: bool
    protected: bool
    conflict: bool
    metadata: Mapping[str, object] = field(
        default_factory=dict, compare=False, repr=False
    )

    def __post_init__(self) -> None:
        if not isinstance(self.capsule, KnowledgeCapsule):
            raise ValueError("capsule must be a KnowledgeCapsule")
        object.__setattr__(
            self, "attention_score", _score(self.attention_score, "attention_score")
        )
        for name in (
            "recall_allowed",
            "eligible",
            "restricted",
            "erased",
            "protected",
            "conflict",
        ):
            object.__setattr__(self, name, _strict_bool(getattr(self, name), name))
        if not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class GateDecision:
    """One explainable disposition and its budget effect."""

    capsule_id: str
    disposition: GateDisposition
    reasons: tuple[GateReason, ...]
    attention_score: float
    protected: bool
    rank: int | None
    full_char_cost: int
    compressed_char_cost: int
    reserved_chars: int

    def __post_init__(self) -> None:
        if not isinstance(self.capsule_id, str) or not self.capsule_id.strip():
            raise ValueError("capsule_id must be a non-empty string")
        if not isinstance(self.disposition, GateDisposition):
            raise ValueError("disposition must be a GateDisposition")
        reasons = tuple(self.reasons)
        if not reasons or any(not isinstance(reason, GateReason) for reason in reasons):
            raise ValueError("reasons must contain at least one GateReason")
        object.__setattr__(self, "reasons", reasons)
        object.__setattr__(
            self, "attention_score", _score(self.attention_score, "attention_score")
        )
        object.__setattr__(self, "protected", _strict_bool(self.protected, "protected"))
        if self.rank is not None:
            object.__setattr__(self, "rank", _positive_int(self.rank, "rank"))
        object.__setattr__(
            self,
            "full_char_cost",
            _non_negative_int(self.full_char_cost, "full_char_cost"),
        )
        object.__setattr__(
            self,
            "compressed_char_cost",
            _non_negative_int(self.compressed_char_cost, "compressed_char_cost"),
        )
        object.__setattr__(
            self,
            "reserved_chars",
            _non_negative_int(self.reserved_chars, "reserved_chars"),
        )

        if self.disposition is GateDisposition.ACTIVE:
            if (
                self.rank is None
                or self.reserved_chars <= 0
                or self.reserved_chars != self.full_char_cost
            ):
                raise ValueError("ACTIVE must reserve full content at a positive rank")
        elif self.disposition is GateDisposition.COMPRESS:
            if (
                self.rank is None
                or self.reserved_chars <= 0
                or self.reserved_chars != self.compressed_char_cost
                or self.compressed_char_cost >= self.full_char_cost
            ):
                raise ValueError("COMPRESS must reserve smaller essence at a positive rank")
        elif self.disposition is GateDisposition.DEFER:
            if self.rank is None or self.reserved_chars != 0:
                raise ValueError("DEFER must have a positive rank and reserve zero chars")
        elif self.rank is not None or self.reserved_chars != 0:
            raise ValueError("terminal dispositions must be unranked and reserve zero chars")

    def to_dict(self) -> dict[str, object]:
        return {
            "capsule_id": self.capsule_id,
            "disposition": self.disposition.value,
            "reasons": [reason.value for reason in self.reasons],
            "attention_score": self.attention_score,
            "protected": self.protected,
            "rank": self.rank,
            "full_char_cost": self.full_char_cost,
            "compressed_char_cost": self.compressed_char_cost,
            "reserved_chars": self.reserved_chars,
        }


@dataclass(frozen=True, slots=True)
class WorkingMemoryPlan:
    """Deterministic Gate output; no candidate is omitted from the plan."""

    budget: WorkingMemoryBudget
    decisions: tuple[GateDecision, ...]
    used_items: int
    used_chars: int

    def __post_init__(self) -> None:
        if not isinstance(self.budget, WorkingMemoryBudget):
            raise ValueError("budget must be a WorkingMemoryBudget")
        decisions = tuple(self.decisions)
        if any(not isinstance(item, GateDecision) for item in decisions):
            raise ValueError("every decision must be a GateDecision")
        decisions = tuple(sorted(decisions, key=lambda item: item.capsule_id))
        if len({item.capsule_id for item in decisions}) != len(decisions):
            raise ValueError("decision capsule_ids must be unique")
        object.__setattr__(self, "decisions", decisions)
        object.__setattr__(
            self, "used_items", _non_negative_int(self.used_items, "used_items")
        )
        object.__setattr__(
            self, "used_chars", _non_negative_int(self.used_chars, "used_chars")
        )
        selected = tuple(
            item
            for item in decisions
            if item.disposition in {GateDisposition.ACTIVE, GateDisposition.COMPRESS}
        )
        if self.used_items != len(selected):
            raise ValueError("used_items must equal selected decision count")
        if self.used_chars != sum(item.reserved_chars for item in selected):
            raise ValueError("used_chars must equal selected reserved characters")
        if self.used_items > self.budget.max_items:
            raise ValueError("used_items exceeds max_items")
        if self.used_chars > self.budget.max_chars:
            raise ValueError("used_chars exceeds max_chars")
        ranks = sorted(item.rank for item in decisions if item.rank is not None)
        if ranks != list(range(1, len(ranks) + 1)):
            raise ValueError("ranked decisions must use unique contiguous ranks")

    def by_disposition(
        self, disposition: GateDisposition
    ) -> tuple[GateDecision, ...]:
        """Return ranked decisions; unranked terminal decisions sort by identity."""

        if not isinstance(disposition, GateDisposition):
            raise ValueError("disposition must be a GateDisposition")
        matching = (
            decision
            for decision in self.decisions
            if decision.disposition is disposition
        )
        return tuple(
            sorted(
                matching,
                key=lambda decision: (
                    decision.rank is None,
                    decision.rank if decision.rank is not None else 0,
                    decision.capsule_id,
                ),
            )
        )

    @property
    def active(self) -> tuple[GateDecision, ...]:
        return self.by_disposition(GateDisposition.ACTIVE)

    @property
    def compressed(self) -> tuple[GateDecision, ...]:
        return self.by_disposition(GateDisposition.COMPRESS)

    @property
    def deferred(self) -> tuple[GateDecision, ...]:
        return self.by_disposition(GateDisposition.DEFER)

    @property
    def quarantined(self) -> tuple[GateDecision, ...]:
        return self.by_disposition(GateDisposition.QUARANTINE)

    @property
    def excluded(self) -> tuple[GateDecision, ...]:
        return self.by_disposition(GateDisposition.EXCLUDE)

    def to_dict(self) -> dict[str, object]:
        return {
            "budget": {
                "max_items": self.budget.max_items,
                "max_chars": self.budget.max_chars,
            },
            "used_items": self.used_items,
            "used_chars": self.used_chars,
            "counts": {
                disposition.value: len(self.by_disposition(disposition))
                for disposition in GateDisposition
            },
            "decisions": [decision.to_dict() for decision in self.decisions],
        }


def _full_char_cost(capsule: KnowledgeCapsule) -> int:
    """Estimate complete semantic text without truncating any field."""

    parts: list[str] = []
    for claim in capsule.claims:
        parts.append(claim.text)
        parts.extend(claim.qualifiers)
        parts.extend(claim.uncertainties)
        parts.extend(claim.applicability_conditions)
        if claim.temporal_scope is not None:
            parts.append(claim.temporal_scope)
    return sum(len(part) for part in parts) + max(0, len(parts) - 1)


def _claims_in_source_order(capsule: KnowledgeCapsule) -> tuple[str, ...]:
    ordered = sorted(
        capsule.claims,
        key=lambda claim: (
            min(span.start_offset for span in claim.source_spans),
            claim.text,
        ),
    )
    return tuple(claim.text for claim in ordered)


def _essence_is_source_linked(capsule: KnowledgeCapsule) -> bool:
    """Accept only complete claim texts in source order, never free summary prose."""

    target = capsule.essence
    positions: set[int] = {0}
    for claim_text in _claims_in_source_order(capsule):
        next_positions = set(positions)
        for position in positions:
            fragment = claim_text if position == 0 else " " + claim_text
            if target.startswith(fragment, position):
                next_positions.add(position + len(fragment))
        positions = next_positions
    return bool(target) and len(target) in positions


def _compressed_semantics_supported(capsule: KnowledgeCapsule) -> bool:
    """Fail closed until ContextPack defines how compressed metadata is carried."""

    if capsule.entities or capsule.omitted_questions:
        return False
    return all(
        not claim.qualifiers
        and not claim.uncertainties
        and not claim.applicability_conditions
        and claim.temporal_scope is None
        for claim in capsule.claims
    )


def _pre_budget_decision(candidate: WorkingMemoryCandidate) -> GateDecision | None:
    reasons: list[GateReason] = []
    if candidate.erased:
        reasons.append(GateReason.ERASED)
    if candidate.restricted:
        reasons.append(GateReason.RESTRICTED)
    if reasons:
        return _decision(candidate, GateDisposition.EXCLUDE, reasons, rank=None)

    if not candidate.recall_allowed:
        reasons.append(GateReason.RECALL_DENIED)
    if not candidate.eligible:
        reasons.append(GateReason.INELIGIBLE)
    if reasons:
        return _decision(candidate, GateDisposition.EXCLUDE, reasons, rank=None)

    if candidate.conflict:
        return _decision(
            candidate,
            GateDisposition.QUARANTINE,
            (GateReason.CONFLICT,),
            rank=None,
        )
    return None


def _decision(
    candidate: WorkingMemoryCandidate,
    disposition: GateDisposition,
    reasons: Iterable[GateReason],
    *,
    rank: int | None,
    reserved_chars: int = 0,
) -> GateDecision:
    return GateDecision(
        capsule_id=candidate.capsule.capsule_id,
        disposition=disposition,
        reasons=tuple(reasons),
        attention_score=candidate.attention_score,
        protected=candidate.protected,
        rank=rank,
        full_char_cost=_full_char_cost(candidate.capsule),
        compressed_char_cost=len(candidate.capsule.essence),
        reserved_chars=reserved_chars,
    )


class WorkingMemoryGate:
    """Pure planner over already-ranked and policy-checked capsules."""

    def __init__(
        self,
        *,
        min_active_score: float = 0.55,
        min_compress_score: float = 0.25,
    ) -> None:
        self._min_active_score = _score(min_active_score, "min_active_score")
        self._min_compress_score = _score(
            min_compress_score, "min_compress_score"
        )
        if self._min_compress_score > self._min_active_score:
            raise ValueError("min_compress_score cannot exceed min_active_score")

    def plan(
        self,
        candidates: Iterable[WorkingMemoryCandidate],
        *,
        budget: WorkingMemoryBudget | None = None,
    ) -> WorkingMemoryPlan:
        if budget is None:
            resolved_budget = WorkingMemoryBudget()
        elif isinstance(budget, WorkingMemoryBudget):
            resolved_budget = budget
        else:
            raise ValueError("budget must be a WorkingMemoryBudget or None")

        materialized = tuple(candidates)
        if any(
            not isinstance(candidate, WorkingMemoryCandidate)
            for candidate in materialized
        ):
            raise ValueError("every candidate must be a WorkingMemoryCandidate")

        by_id: dict[str, WorkingMemoryCandidate] = {}
        for candidate in materialized:
            capsule_id = candidate.capsule.capsule_id
            if capsule_id in by_id:
                raise ValueError(f"duplicate capsule_id: {capsule_id}")
            by_id[capsule_id] = candidate

        decisions: dict[str, GateDecision] = {}
        eligible_pool: list[WorkingMemoryCandidate] = []
        for candidate in sorted(
            materialized, key=lambda item: item.capsule.capsule_id
        ):
            pre_decision = _pre_budget_decision(candidate)
            if pre_decision is None:
                eligible_pool.append(candidate)
            else:
                decisions[candidate.capsule.capsule_id] = pre_decision

        ranked = sorted(
            eligible_pool,
            key=lambda item: (
                not item.protected,
                -item.attention_score,
                item.capsule.capsule_id,
            ),
        )

        used_items = 0
        used_chars = 0
        for rank, candidate in enumerate(ranked, start=1):
            full_cost = _full_char_cost(candidate.capsule)
            compressed_cost = len(candidate.capsule.essence)
            essence_source_linked = _essence_is_source_linked(candidate.capsule)
            compressed_semantics_supported = _compressed_semantics_supported(
                candidate.capsule
            )
            remaining_chars = resolved_budget.max_chars - used_chars
            reasons: list[GateReason] = []
            if candidate.protected:
                reasons.append(GateReason.PROTECTED)

            if used_items >= resolved_budget.max_items:
                reasons.append(GateReason.ITEM_BUDGET_EXHAUSTED)
                decisions[candidate.capsule.capsule_id] = _decision(
                    candidate, GateDisposition.DEFER, reasons, rank=rank
                )
                continue

            active_eligible = (
                candidate.protected
                or candidate.attention_score >= self._min_active_score
            )
            compress_eligible = (
                candidate.protected
                or candidate.attention_score >= self._min_compress_score
            )

            if active_eligible and full_cost <= remaining_chars:
                reasons.append(GateReason.FULL_CONTENT_SELECTED)
                decisions[candidate.capsule.capsule_id] = _decision(
                    candidate,
                    GateDisposition.ACTIVE,
                    reasons,
                    rank=rank,
                    reserved_chars=full_cost,
                )
                used_items += 1
                used_chars += full_cost
                continue

            if not active_eligible:
                reasons.append(GateReason.SCORE_BELOW_ACTIVE)
            if full_cost > remaining_chars:
                reasons.append(GateReason.FULL_CONTENT_OVER_BUDGET)
                if not essence_source_linked:
                    reasons.append(GateReason.ESSENCE_NOT_SOURCE_LINKED)
                if not compressed_semantics_supported:
                    reasons.append(GateReason.COMPRESSED_SEMANTICS_UNSUPPORTED)

            if (
                full_cost > remaining_chars
                and essence_source_linked
                and compressed_semantics_supported
                and compress_eligible
                and compressed_cost <= remaining_chars
            ):
                reasons.append(GateReason.ESSENCE_SELECTED)
                decisions[candidate.capsule.capsule_id] = _decision(
                    candidate,
                    GateDisposition.COMPRESS,
                    reasons,
                    rank=rank,
                    reserved_chars=compressed_cost,
                )
                used_items += 1
                used_chars += compressed_cost
                continue

            if not compress_eligible:
                reasons.append(GateReason.SCORE_BELOW_COMPRESS)
            elif (
                full_cost > remaining_chars
                and essence_source_linked
                and compressed_semantics_supported
            ):
                reasons.append(GateReason.CHAR_BUDGET_EXHAUSTED)
            decisions[candidate.capsule.capsule_id] = _decision(
                candidate, GateDisposition.DEFER, reasons, rank=rank
            )

        ordered_decisions = tuple(decisions[key] for key in sorted(decisions))
        return WorkingMemoryPlan(
            budget=resolved_budget,
            decisions=ordered_decisions,
            used_items=used_items,
            used_chars=used_chars,
        )


__all__ = [
    "GateDecision",
    "GateDisposition",
    "GateReason",
    "WorkingMemoryBudget",
    "WorkingMemoryCandidate",
    "WorkingMemoryGate",
    "WorkingMemoryPlan",
]
