"""Bounded foreground execution for an explicit later-task reopen plan.

This is a thin execution adapter over the existing ``SemanticReader`` contract.
It accepts only a previously planned ``READY`` reopen, verifies the exact source
identity and every planned ``SourceSpan`` against the caller-supplied immutable
``RawSource``, then re-reads only those exact spans.

Reader providers receive an exact source slice, so accepted Reader provenance is
validated in slice-local coordinates and rebased back onto the immutable full
source before it is exposed to downstream callers.

It deliberately does not select task relevance, create a scheduler, resolve a
source from storage/network, persist Reader state, synthesize an answer, write
memory/Canon, or grant evidence/decision authority.

    READY PLAN != REOPEN EXECUTED
    REOPEN EXECUTED != EVIDENCE
    REOPEN RESULT != SEMANTIC USE != ANSWER SUPPORT != DECISION AUTHORITY
"""

from __future__ import annotations

from dataclasses import dataclass

from core.knowledge_capsule import CapsuleClaim, KnowledgeCapsule, SourceSpan
from core.later_task_reopen import (
    LaterTaskReopenDisposition,
    LaterTaskReopenError,
    LaterTaskReopenPlan,
    LaterTaskReopenTarget,
)
from core.semantic_reader import (
    RawSource,
    ReaderBudget,
    ReaderMode,
    ReaderResult,
    ReaderStatus,
    SemanticReader,
)


@dataclass(frozen=True, slots=True)
class LaterTaskReopenObservation:
    """One target-bound read-side Reader observation."""

    target: LaterTaskReopenTarget
    reader_result: ReaderResult

    @property
    def accepted(self) -> bool:
        return self.reader_result.accepted


@dataclass(frozen=True, slots=True)
class LaterTaskReopenExecutionResult:
    """Bounded execution result; never an answer/evidence/authority receipt."""

    plan: LaterTaskReopenPlan
    executed: bool
    reason_code: str
    observations: tuple[LaterTaskReopenObservation, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return (
            self.executed
            and bool(self.observations)
            and len(self.observations) == len(self.plan.targets)
            and all(item.accepted for item in self.observations)
        )


class LaterTaskReopenExecutor:
    """Execute one explicit READY plan against one exact caller-supplied source."""

    executor_version = "later-task-reopen-execution.v0.3"

    async def execute(
        self,
        plan: LaterTaskReopenPlan,
        source: RawSource,
        reader: SemanticReader,
        *,
        mode: ReaderMode = ReaderMode.DEEP,
        budget: ReaderBudget | None = None,
    ) -> LaterTaskReopenExecutionResult:
        if not isinstance(plan, LaterTaskReopenPlan):
            raise LaterTaskReopenError("plan must be a LaterTaskReopenPlan")
        if not isinstance(source, RawSource):
            raise LaterTaskReopenError("source must be a RawSource")
        if not isinstance(reader, SemanticReader):
            raise LaterTaskReopenError("reader must implement SemanticReader")
        if not isinstance(mode, ReaderMode):
            raise LaterTaskReopenError("mode must be a ReaderMode")
        resolved_budget = budget or ReaderBudget()
        if not isinstance(resolved_budget, ReaderBudget):
            raise LaterTaskReopenError("budget must be a ReaderBudget")

        if plan.disposition is not LaterTaskReopenDisposition.READY:
            return LaterTaskReopenExecutionResult(
                plan=plan,
                executed=False,
                reason_code="reopen_plan_not_ready",
                warnings=("no_reader_call_for_non_ready_plan",),
            )
        if not plan.targets:
            return LaterTaskReopenExecutionResult(
                plan=plan,
                executed=False,
                reason_code="ready_plan_has_no_targets",
                warnings=("no_reader_call_for_empty_ready_plan",),
            )
        if (
            source.document_id != plan.document_id
            or source.source_revision != plan.source_revision
        ):
            return LaterTaskReopenExecutionResult(
                plan=plan,
                executed=False,
                reason_code="source_identity_mismatch",
                warnings=("no_reader_call_for_source_identity_mismatch",),
            )

        span_payload_by_id: dict[str, tuple[str, str | None, int, int, str]] = {}
        for target in plan.targets:
            span = target.source_span
            if (
                span.document_id != plan.document_id
                or span.source_revision != plan.source_revision
            ):
                return LaterTaskReopenExecutionResult(
                    plan=plan,
                    executed=False,
                    reason_code="target_source_identity_mismatch",
                    warnings=("no_reader_call_for_target_identity_mismatch",),
                )
            if not span.verify(source.text):
                return LaterTaskReopenExecutionResult(
                    plan=plan,
                    executed=False,
                    reason_code="target_source_span_verification_failed",
                    warnings=("no_reader_call_for_unverified_source_span",),
                )
            if span.end_offset - span.start_offset > resolved_budget.max_source_chars:
                return LaterTaskReopenExecutionResult(
                    plan=plan,
                    executed=False,
                    reason_code="reader_budget_too_small_for_planned_span",
                    warnings=("no_reader_call_when_reader_budget_cannot_cover_target",),
                )
            payload = _span_payload(span)
            existing_payload = span_payload_by_id.get(span.span_id)
            if existing_payload is not None and existing_payload != payload:
                return LaterTaskReopenExecutionResult(
                    plan=plan,
                    executed=False,
                    reason_code="conflicting_span_id_payload",
                    warnings=("no_reader_call_for_conflicting_span_id_payload",),
                )
            span_payload_by_id[span.span_id] = payload

        results_by_span: dict[tuple[str, str | None, int, int, str], ReaderResult] = {}
        warnings: list[str] = [
            "reopen_result_is_read_side_not_evidence_or_answer_support"
        ]
        for target in plan.targets:
            span = target.source_span
            span_key = _span_payload(span)
            if span_key in results_by_span:
                continue
            exact_source = RawSource(
                document_id=plan.document_id,
                text=source.text[span.start_offset : span.end_offset],
                source_revision=plan.source_revision,
            )
            try:
                result = await reader.extract(
                    exact_source,
                    mode=mode,
                    budget=resolved_budget,
                )
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as exc:
                result = ReaderResult.failed(
                    ReaderStatus.PROVIDER_ERROR,
                    code=f"later_task_reopen_reader_exception:{type(exc).__name__}",
                    safe_message="Later-task source reopen reader execution failed.",
                    retryable=False,
                )
            if not isinstance(result, ReaderResult):
                result = ReaderResult.failed(
                    ReaderStatus.INVALID_OUTPUT,
                    code="later_task_reopen_invalid_reader_result",
                    safe_message="Later-task source reopen returned an invalid Reader result.",
                    retryable=False,
                )
            if result.accepted:
                result = _rebase_reader_result(
                    result,
                    exact_source=exact_source,
                    full_source=source,
                    target=target,
                )
            results_by_span[span_key] = result
            if not result.accepted:
                code = result.failure.code if result.failure is not None else result.status.value
                warnings.append(f"reopen_target:{span.span_id}:reader_rejected:{code}")

        observations = tuple(
            LaterTaskReopenObservation(
                target=target,
                reader_result=results_by_span[_span_payload(target.source_span)],
            )
            for target in plan.targets
        )
        complete = bool(observations) and all(item.accepted for item in observations)
        return LaterTaskReopenExecutionResult(
            plan=plan,
            executed=True,
            reason_code=(
                "later_task_reopen_executed"
                if complete
                else "later_task_reopen_execution_incomplete"
            ),
            observations=observations,
            warnings=tuple(dict.fromkeys(warnings)),
        )


def _span_payload(span: SourceSpan) -> tuple[str, str | None, int, int, str]:
    """Return the immutable source identity used for execution deduplication."""

    return (
        span.document_id,
        span.source_revision,
        span.start_offset,
        span.end_offset,
        span.content_hash,
    )


def _rebase_reader_result(
    result: ReaderResult,
    *,
    exact_source: RawSource,
    full_source: RawSource,
    target: LaterTaskReopenTarget,
) -> ReaderResult:
    capsule = result.capsule
    if capsule is None or capsule.source_document_id != full_source.document_id:
        return _span_validation_failure("reader_capsule_source_identity_mismatch")

    rebased_claims: list[CapsuleClaim] = []
    for claim in capsule.claims:
        rebased_spans: list[SourceSpan] = []
        for local_span in claim.source_spans:
            # source_revision is the immutable full-source identity; offsets are
            # interpreted in the coordinate space of exact_source.text here.
            if (
                local_span.document_id != full_source.document_id
                or local_span.source_revision != full_source.source_revision
                or not local_span.verify(exact_source.text)
            ):
                return _span_validation_failure("reader_local_span_verification_failed")
            absolute_start = target.source_span.start_offset + local_span.start_offset
            absolute_end = target.source_span.start_offset + local_span.end_offset
            if absolute_end > target.source_span.end_offset:
                return _span_validation_failure("reader_local_span_exceeds_reopen_target")
            rebased_spans.append(
                SourceSpan.from_text(
                    document_id=full_source.document_id,
                    raw_text=full_source.text,
                    start_offset=absolute_start,
                    end_offset=absolute_end,
                    source_revision=full_source.source_revision,
                )
            )
        rebased_claims.append(
            CapsuleClaim.create(
                text=claim.text,
                modality=claim.modality,
                source_spans=tuple(rebased_spans),
                extraction_confidence=claim.extraction_confidence,
                truth_confidence=claim.truth_confidence,
                qualifiers=claim.qualifiers,
                uncertainties=claim.uncertainties,
                applicability_conditions=claim.applicability_conditions,
                temporal_scope=claim.temporal_scope,
            )
        )

    rebased_capsule = KnowledgeCapsule.create(
        source_document_id=full_source.document_id,
        essence=capsule.essence,
        claims=tuple(rebased_claims),
        reader_id=capsule.reader_id,
        reader_version=capsule.reader_version,
        entities=capsule.entities,
        omitted_questions=capsule.omitted_questions,
        coverage_score=capsule.coverage_score,
        compression_ratio=capsule.compression_ratio,
        prompt_version=capsule.prompt_version,
        created_at=capsule.created_at,
    )
    if result.status is ReaderStatus.PARTIAL:
        return ReaderResult.partial(rebased_capsule, warnings=result.warnings)
    return ReaderResult.success(rebased_capsule)


def _span_validation_failure(code: str) -> ReaderResult:
    return ReaderResult.failed(
        ReaderStatus.SPAN_VALIDATION_FAILED,
        code=code,
        safe_message="Later-task source reopen provenance could not be verified.",
        retryable=False,
    )


__all__ = [
    "LaterTaskReopenExecutionResult",
    "LaterTaskReopenExecutor",
    "LaterTaskReopenObservation",
]
