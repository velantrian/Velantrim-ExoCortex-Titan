"""Bounded owner-local contract for later-task source reopen planning.

This module deliberately stops at planning. It does not execute a Reader run,
register a scheduler, persist resume state, write memory/Canon, or grant answer
or decision authority.

The contract answers one narrow question:

    Given an explicit later task, an explicit set of claims selected for
    reconsideration, and an earlier source-linked ReaderProduct result,
    which exact source spans, if any, may be reopened safely and within budget?

An unsupported source claim is only a trigger candidate. The planner does not
infer task relevance: requested claim IDs must be supplied explicitly and must
also be present in the prior synthesis' unsupported set.
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
    requested_claim_ids: tuple[str, ...]
    unsupported_source_claim_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("task_text", "document_id", "source_revision"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise LaterTaskReopenError(f"{name} must be a non-empty string")
        for field_name in ("requested_claim_ids", "unsupported_source_claim_ids"):
            claim_ids = tuple(getattr(self, field_name))
            if any(not isinstance(value, str) or not value.strip() for value in claim_ids):
                raise LaterTaskReopenError(
                    f"{field_name} must contain non-empty strings"
                )
            if len(set(claim_ids)) != len(claim_ids):
                raise LaterTaskReopenError(f"{field_name} must be unique")
            object.__setattr__(self, field_name, claim_ids)


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


def _target_key(target: LaterTaskReopenTarget) -> tuple[int, int, str, str, str, str]:
    return (
        target.source_span.start_offset,
        target.source_span.end_offset,
        target.source_span.span_id,
        target.card_id,
        target.unit_id,
        target.claim_id,
    )


class LaterTaskReopenPlanner:
    """Select exact source-linked claims for bounded later-task reopen.

    Selection is deterministic and deliberately conservative:

    * task relevance is not inferred here; callers must explicitly provide the
      claim IDs selected for reconsideration;
    * only the intersection of requested claim IDs and prior synthesis
      unsupported claim IDs is eligible;
    * the card document/revision must exactly match the explicit request;
    * claim provenance must include an exact SourceSpan for that revision;
    * duplicate claim occurrences across cards collapse to one canonical target;
    * targets are ordered by stable source/provenance properties;
    * if the hard budget cannot cover all eligible targets, the plan returns
      UNKNOWN rather than silently broadening or truncating semantic scope.
    """

    planner_version = "later-task-reopen.v0.3"

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

        if not request.requested_claim_ids:
            return LaterTaskReopenPlan(
                disposition=LaterTaskReopenDisposition.UNKNOWN,
                reason_code="no_later_task_claim_selection",
                task_text=request.task_text,
                document_id=request.document_id,
                source_revision=request.source_revision,
            )
        if not request.unsupported_source_claim_ids:
            return LaterTaskReopenPlan(
                disposition=LaterTaskReopenDisposition.UNKNOWN,
                reason_code="no_unsupported_claim_signal",
                task_text=request.task_text,
                document_id=request.document_id,
                source_revision=request.source_revision,
            )

        eligible = set(request.requested_claim_ids).intersection(
            request.unsupported_source_claim_ids
        )
        if not eligible:
            return LaterTaskReopenPlan(
                disposition=LaterTaskReopenDisposition.UNKNOWN,
                reason_code="requested_claims_not_marked_unsupported",
                task_text=request.task_text,
                document_id=request.document_id,
                source_revision=request.source_revision,
            )

        candidates_by_claim: dict[str, list[LaterTaskReopenTarget]] = {
            claim_id: [] for claim_id in eligible
        }
        saw_same_document_card = False
        saw_requested_revision_card = False

        for card in cards:
            if not isinstance(card, SectionCard):
                raise LaterTaskReopenError("cards must contain only SectionCard values")
            if card.document_id != request.document_id:
                continue
            saw_same_document_card = True
            if card.source_revision != request.source_revision:
                continue
            saw_requested_revision_card = True

            for card_claim in card.claims:
                claim_id = card_claim.claim.claim_id
                if claim_id not in eligible:
                    continue
                for span in card_claim.claim.source_spans:
                    if (
                        span.document_id == request.document_id
                        and span.source_revision == request.source_revision
                    ):
                        candidates_by_claim[claim_id].append(
                            LaterTaskReopenTarget(
                                claim_id=claim_id,
                                card_id=card.card_id,
                                unit_id=card.unit_id,
                                source_span=span,
                            )
                        )

        candidates = [
            min(claim_candidates, key=_target_key)
            for claim_candidates in candidates_by_claim.values()
            if claim_candidates
        ]

        if not candidates:
            if saw_same_document_card and not saw_requested_revision_card:
                disposition = LaterTaskReopenDisposition.REFUSED
                reason_code = "source_revision_mismatch"
            else:
                disposition = LaterTaskReopenDisposition.UNKNOWN
                reason_code = "eligible_claims_not_reopenable_from_cards"
            return LaterTaskReopenPlan(
                disposition=disposition,
                reason_code=reason_code,
                task_text=request.task_text,
                document_id=request.document_id,
                source_revision=request.source_revision,
            )

        candidates.sort(key=_target_key)
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
