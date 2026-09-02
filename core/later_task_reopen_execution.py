"""Bounded foreground execution for an explicit later-task reopen plan.

This is a thin execution adapter over the existing ``SemanticReader`` contract.
It accepts only a previously planned ``READY`` reopen, verifies the exact source
identity and every planned ``SourceSpan`` against the caller-supplied immutable
``RawSource``, then re-reads only those exact spans.

It deliberately does not select task relevance, create a scheduler, resolve a
source from storage/network, persist Reader state, synthesize an answer, write
memory/Canon, or grant evidence/decision authority.

    READY PLAN != REOPEN EXECUTED
    REOPEN EXECUTED != EVIDENCE
    REOPEN RESULT != SEMANTIC USE != ANSWER SUPPORT != DECISION AUTHORITY
"""

from __future__ import annotations

from dataclasses import dataclass

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

    executor_version = "later-task-reopen-execution.v0.1"

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

        results_by_span_id: dict[str, ReaderResult] = {}
        warnings: list[str] = [
            "reopen_result_is_read_side_not_evidence_or_answer_support"
        ]
        for target in plan.targets:
            span = target.source_span
            if span.span_id in results_by_span_id:
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
            results_by_span_id[span.span_id] = result
            if not result.accepted:
                code = result.failure.code if result.failure is not None else result.status.value
                warnings.append(f"reopen_target:{span.span_id}:reader_rejected:{code}")

        observations = tuple(
            LaterTaskReopenObservation(
                target=target,
                reader_result=results_by_span_id[target.source_span.span_id],
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


__all__ = [
    "LaterTaskReopenExecutionResult",
    "LaterTaskReopenExecutor",
    "LaterTaskReopenObservation",
]
