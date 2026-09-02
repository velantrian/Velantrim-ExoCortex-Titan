from __future__ import annotations

import pytest

from core.knowledge_capsule import CapsuleClaim, ClaimModality, KnowledgeCapsule, SourceSpan
from core.later_task_reopen import (
    LaterTaskReopenDisposition,
    LaterTaskReopenPlan,
    LaterTaskReopenTarget,
)
from core.later_task_reopen_execution import LaterTaskReopenExecutor
from core.semantic_reader import RawSource, ReaderBudget, ReaderMode, ReaderResult


_DOC = "f2-later-task-execution"
_REV = "rev-f2-1"
_TEXT = (
    "Policy R: standard requests may be approved after ordinary review.\n\n"
    "Hidden exception X: requests involving a revoked credential must never be approved."
)
_EXCEPTION = "requests involving a revoked credential must never be approved"


class _RecordingReader:
    reader_id = "tests.later-task-reopen-recording-reader"
    reader_version = "1"

    def __init__(self, *, fail: bool = False) -> None:
        self.sources: list[RawSource] = []
        self.fail = fail

    async def extract(
        self,
        source: RawSource,
        *,
        mode: ReaderMode,
        budget: ReaderBudget,
    ) -> ReaderResult:
        self.sources.append(source)
        assert mode is ReaderMode.DEEP
        assert isinstance(budget, ReaderBudget)
        if self.fail:
            raise RuntimeError("synthetic provider failure")
        span = SourceSpan.from_text(
            document_id=source.document_id,
            raw_text=source.text,
            start_offset=0,
            end_offset=len(source.text),
            source_revision=source.source_revision,
        )
        claim = CapsuleClaim.create(
            text=source.text,
            modality=ClaimModality.OBSERVATION,
            source_spans=(span,),
            extraction_confidence=1.0,
        )
        capsule = KnowledgeCapsule.create(
            source_document_id=source.document_id,
            essence=source.text,
            claims=(claim,),
            reader_id=self.reader_id,
            reader_version=self.reader_version,
            coverage_score=1.0,
        )
        return ReaderResult.success(capsule)


def _source(*, text: str = _TEXT, revision: str = _REV) -> RawSource:
    return RawSource(document_id=_DOC, text=text, source_revision=revision)


def _ready_plan(source: RawSource | None = None) -> LaterTaskReopenPlan:
    resolved = source or _source()
    start = resolved.text.index(_EXCEPTION)
    end = start + len(_EXCEPTION)
    span = SourceSpan.from_text(
        document_id=resolved.document_id,
        raw_text=resolved.text,
        start_offset=start,
        end_offset=end,
        source_revision=resolved.source_revision,
    )
    return LaterTaskReopenPlan(
        disposition=LaterTaskReopenDisposition.READY,
        reason_code="explicit_later_task_with_reopenable_unsupported_claims",
        task_text="May a request involving a revoked credential be approved?",
        document_id=resolved.document_id,
        source_revision=resolved.source_revision or "",
        targets=(
            LaterTaskReopenTarget(
                claim_id="claim-hidden-x",
                card_id="card-hidden-x",
                unit_id="unit-hidden-x",
                source_span=span,
            ),
        ),
    )


@pytest.mark.asyncio
async def test_ready_plan_executes_only_the_exact_verified_source_span() -> None:
    source = _source()
    plan = _ready_plan(source)
    reader = _RecordingReader()

    result = await LaterTaskReopenExecutor().execute(plan, source, reader)

    assert result.executed is True
    assert result.complete is True
    assert result.reason_code == "later_task_reopen_executed"
    assert len(reader.sources) == 1
    assert reader.sources[0].text == _EXCEPTION
    assert reader.sources[0].document_id == _DOC
    assert reader.sources[0].source_revision == _REV
    observation = result.observations[0]
    assert observation.target == plan.targets[0]
    assert observation.accepted is True
    assert observation.reader_result.capsule is not None
    rebased_span = observation.reader_result.capsule.claims[0].source_spans[0]
    assert rebased_span.start_offset == plan.targets[0].source_span.start_offset
    assert rebased_span.end_offset == plan.targets[0].source_span.end_offset
    assert rebased_span.verify(source.text)
    assert "reopen_result_is_read_side_not_evidence_or_answer_support" in result.warnings


@pytest.mark.asyncio
async def test_non_ready_plan_never_calls_reader() -> None:
    source = _source()
    ready = _ready_plan(source)
    plan = LaterTaskReopenPlan(
        disposition=LaterTaskReopenDisposition.UNKNOWN,
        reason_code="reopen_budget_insufficient",
        task_text=ready.task_text,
        document_id=ready.document_id,
        source_revision=ready.source_revision,
    )
    reader = _RecordingReader()

    result = await LaterTaskReopenExecutor().execute(plan, source, reader)

    assert result.executed is False
    assert result.complete is False
    assert result.reason_code == "reopen_plan_not_ready"
    assert reader.sources == []


@pytest.mark.asyncio
async def test_source_revision_mismatch_fails_closed_before_reader_call() -> None:
    source = _source()
    plan = _ready_plan(source)
    reader = _RecordingReader()

    result = await LaterTaskReopenExecutor().execute(
        plan,
        _source(revision="rev-f2-2"),
        reader,
    )

    assert result.executed is False
    assert result.reason_code == "source_identity_mismatch"
    assert reader.sources == []


@pytest.mark.asyncio
async def test_changed_source_text_fails_span_verification_before_reader_call() -> None:
    source = _source()
    plan = _ready_plan(source)
    reader = _RecordingReader()
    changed = _source(text=_TEXT.replace("must never", "may sometimes"))

    result = await LaterTaskReopenExecutor().execute(plan, changed, reader)

    assert result.executed is False
    assert result.reason_code == "target_source_span_verification_failed"
    assert reader.sources == []


@pytest.mark.asyncio
async def test_reader_failure_is_observable_without_promoting_execution_to_success() -> None:
    source = _source()
    plan = _ready_plan(source)
    reader = _RecordingReader(fail=True)

    result = await LaterTaskReopenExecutor().execute(plan, source, reader)

    assert result.executed is True
    assert result.complete is False
    assert result.reason_code == "later_task_reopen_execution_incomplete"
    assert len(reader.sources) == 1
    observation = result.observations[0]
    assert observation.accepted is False
    assert observation.reader_result.failure is not None
    assert observation.reader_result.failure.code.startswith(
        "later_task_reopen_reader_exception:"
    )
