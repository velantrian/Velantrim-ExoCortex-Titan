"""Bounded owner-local contract for later-task source reopen planning.

This module deliberately stops at planning. It does not execute a Reader run,
register a scheduler, persist resume state, write memory/Canon, or grant answer
or decision authority.

The contract answers one narrow question:

    Given a later task and an earlier source-linked ReaderProduct result,
    which exact source spans, if any, may be reopened safely and within budget?

An unsupported source claim is a trigger candidate, not truth, semantic use,
answer support, or decision authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from core.knowledge_capsule import SourceSpan
from core.section_card import SectionCard


class LaterTaskReopenError(ValueError):
    """Raised when later-task reopen contract inputs are malformed."""


class LaterTaskReopenDisposition(str, Enum):
    """Outcome of bounded later-task reopen planning."""

    READY = "ready"
    UNKNOWN = "unknown"
    REFUSED = "refused"


@dataclass(frozen=True, slots=True)
class LaterTaskReopenBudget:
    """Hard deterministic bounds for one explicit later-task reopen proposal."""

    max_spans: int = 4
    max_total_chars: int = 20_000

    def __post_init__(self) -> None:
        for name in ("max_spans", "max_total_chars"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise LaterTaskReopenError(f"{name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class LaterTaskReopenRequest:
    """Explicit later-task request; never inferred from background activity."""

    task_text: str
    document_id: str
    source_revision: str
    unsupported_source_claim_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("task_text", "document_id", "source_revision"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise LaterTaskReopenError(f"{name} must be a non-empty string")
        claim_ids = tuple(self.unsupported_source_claim_ids)
        if any(not isinstance(value, str) or not value.strip() for value in claim_ids):
            raise LaterTaskReopenError(
                "unsupported_source_claim_ids must contain non-empty strings"
            )
        if len(set(claim_ids)) != len(claim_ids):
            raise LaterTaskReopenError(
                "unsupported_source_claim_ids must be unique"
            )
        object.__setattr__(self, "unsupported_source_claim_ids", claim_ids)


@dataclass(frozen=True, slots=True)
class LaterTaskReopenTarget:
    """One exact source span proposed for explicit foreground reopen."""

    claim_id: str
    card_id: str
    unit_id: str
    source_span: SourceSpan

    @property
    def char_count(self) -> int:
        return self.source_span.end_offset - self.source_span.start_offset


@dataclass(frozen=True, slots=True)
class LaterTaskReopenPlan:
    """Pure planning result. READY does not execute a reopen."""

    disposition: LaterTaskReopenDisposition
    reason_code: str
    task_text: str
    document_id: str
    source_revision: str
    targets: tuple[LaterTaskReopenTarget, ...] = ()

    @property
    def total_chars(self) -> int:
        return sum(target.char_count for target in self.targets)


class LaterTaskReopenPlanner:
    """Select exact source-linked unsupported claims for bounded reopen.

    Selection is deterministic and deliberately conservative:

    * only claim IDs explicitly surfaced as unsupported by the prior synthesis
      are eligible;
    * the card document/revision must exactly match the explicit request;
    * claim provenance must include at least one exact SourceSpan for the same
      document/revision;
    * targets are ordered by source offsets, then claim ID;
    * targets beyond the hard budget are not silently broadened into a partial
      semantic answer: the plan returns UNKNOWN instead.
    """

    planner_version = "later-task-reopen.v0.1"

    def plan(
        self,
        request: LaterTaskReopenRequest,
        cards: Iterable[SectionCard],
        *,
        budget: LaterTaskReopenBudget | None = None,
    ) -> LaterTaskReopenPlan:
        if not isinstance(request, LaterTaskReopenRequest):
            raise LaterTaskReopenError("request must be a LaterTaskReopenRequest")
        resolved_budget = budget or LaterTaskReopenBudget()
        if not isinstance(resolved_budget, LaterTaskReopenBudget):
            raise LaterTaskReopenError("budget must be a LaterTaskReopenBudget")

        unsupported = set(request.unsupported_source_claim_ids)
        if not unsupported:
            return LaterTaskReopenPlan(
                disposition=LaterTaskReopenDisposition.UNKNOWN,
                reason_code="no_unsupported_claim_signal",
                task_text=request.task_text,
                document_id=request.document_id,
                source_revision=request.source_revision,
            )

        candidates: list[LaterTaskReopenTarget] = []
        seen_claim_ids: set[str] = set()
        saw_revision_mismatch = False

        for card in cards:
            if not isinstance(card, SectionCard):
                raise LaterTaskReopenError("cards must contain only SectionCard values")
            if card.document_id != request.document_id:
                continue
            if card.source_revision != request.source_revision:
                saw_revision_mismatch = True
                continue

            for card_claim in card.claims:
                claim_id = card_claim.claim.claim_id
                if claim_id not in unsupported or claim_id in seen_claim_ids:
                    continue
                spans = tuple(
                    span
                    for span in card_claim.claim.source_spans
                    if span.document_id == request.document_id
                    and span.source_revision == request.source_revision
                )
                if not spans:
                    continue
                source_span = min(
                    spans,
                    key=lambda span: (span.start_offset, span.end_offset, span.span_id),
                )
                candidates.append(
                    LaterTaskReopenTarget(
                        claim_id=claim_id,
                        card_id=card.card_id,
                        unit_id=card.unit_id,
                        source_span=source_span,
                    )
                )
                seen_claim_ids.add(claim_id)

        if not candidates:
            return LaterTaskReopenPlan(
                disposition=(
                    LaterTaskReopenDisposition.REFUSED
                    if saw_revision_mismatch
                    else LaterTaskReopenDisposition.UNKNOWN
                ),
                reason_code=(
                    "source_revision_mismatch"
                    if saw_revision_mismatch
                    else "unsupported_claims_not_reopenable_from_cards"
                ),
                task_text=request.task_text,
                document_id=request.document_id,
                source_revision=request.source_revision,
            )

        candidates.sort(
            key=lambda target: (
                target.source_span.start_offset,
                target.source_span.end_offset,
                target.claim_id,
            )
        )
        total_chars = sum(target.char_count for target in candidates)
        if (
            len(candidates) > resolved_budget.max_spans
            or total_chars > resolved_budget.max_total_chars
        ):
            return LaterTaskReopenPlan(
                disposition=LaterTaskReopenDisposition.UNKNOWN,
                reason_code="reopen_budget_insufficient",
                task_text=request.task_text,
                document_id=request.document_id,
                source_revision=request.source_revision,
            )

        return LaterTaskReopenPlan(
            disposition=LaterTaskReopenDisposition.READY,
            reason_code="explicit_later_task_with_reopenable_unsupported_claims",
            task_text=request.task_text,
            document_id=request.document_id,
            source_revision=request.source_revision,
            targets=tuple(candidates),
        )
