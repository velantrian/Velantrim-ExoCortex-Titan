from __future__ import annotations

import pytest

from core.document_structure import DocumentStructureFormat
from core.hierarchical_section_planner import SectionPlanningBudget
from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.later_task_reopen import (
    LaterTaskReopenBudget,
    LaterTaskReopenDisposition,
    LaterTaskReopenPlanner,
    LaterTaskReopenRequest,
)
from core.reader_product_pipeline import ReaderProductConfig, ReaderProductPipeline
from core.semantic_reader import (
    RawSource,
    ReaderBudget,
    ReaderMode,
    ReaderResult,
    SemanticReader,
)

_EXCEPTION_EVIDENCE = "revoked credential"
_T2 = "May a request involving a revoked credential be approved?"


class _ExactSourceReader:
    reader_id = "tests.later-task-reopen-exact-reader"
    reader_version = "1"

    async def extract(
        self,
        source: RawSource,
        *,
        mode: ReaderMode,
        budget: ReaderBudget,
    ) -> ReaderResult:
        assert isinstance(mode, ReaderMode)
        assert isinstance(budget, ReaderBudget)
        text = source.text.strip()
        start = source.text.index(text)
        span = SourceSpan.from_text(
            document_id=source.document_id,
            raw_text=source.text,
            start_offset=start,
            end_offset=start + len(text),
            source_revision=source.source_revision,
        )
        claim = CapsuleClaim.create(
            text=text,
            modality=ClaimModality.OBSERVATION,
            source_spans=(span,),
            extraction_confidence=1.0,
        )
        capsule = KnowledgeCapsule.create(
            source_document_id=source.document_id,
            essence=text,
            claims=(claim,),
            reader_id=self.reader_id,
            reader_version=self.reader_version,
            coverage_score=1.0,
        )
        return ReaderResult.success(capsule)


def _source() -> RawSource:
    return RawSource(
        document_id="later-task-reopen-fixture",
        text=(
            "Policy R: standard requests may be approved after ordinary review.\n\n"
            "Operational context: the ordinary path is the dominant case and is "
            "sufficient for routine T1 summarization.\n\n"
            "Hidden exception X: requests involving a revoked credential must never "
            "be approved, even when ordinary review would otherwise pass."
        ),
    )


def _config() -> ReaderProductConfig:
    return ReaderProductConfig(
        initial_mode=ReaderMode.STANDARD,
        section_budget=SectionPlanningBudget(
            max_unit_chars=90,
            min_unit_chars=20,
            boundary_search_chars=70,
        ),
        reader_budget=ReaderBudget(
            max_source_chars=2_000,
            max_claims=16,
            max_essence_chars=1_000,
        ),
        max_digest_chars=96,
    )


async def _t1_result():
    reader = _ExactSourceReader()
    assert isinstance(reader, SemanticReader)
    return await ReaderProductPipeline(reader, config=_config()).read(
        _source(),
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )


def _request(result, *, revision: str | None = None, claim_ids=None):
    assert result.synthesis is not None
    return LaterTaskReopenRequest(
        task_text=_T2,
        document_id=result.source.document_id,
        source_revision=revision or result.source.source_revision,
        unsupported_source_claim_ids=(
            tuple(result.synthesis.unsupported_source_claim_ids)
            if claim_ids is None
            else tuple(claim_ids)
        ),
    )


@pytest.mark.asyncio
async def test_later_task_reopen_selects_exact_unsupported_t2_source_span() -> None:
    result = await _t1_result()
    assert result.synthesis is not None
    assert _EXCEPTION_EVIDENCE not in result.source_grounded_digest

    t2_claim_ids = tuple(
        card_claim.claim.claim_id
        for card in result.cards
        for card_claim in card.claims
        if _EXCEPTION_EVIDENCE in card_claim.claim.text
    )
    assert t2_claim_ids
    assert set(t2_claim_ids).issubset(result.synthesis.unsupported_source_claim_ids)

    plan = LaterTaskReopenPlanner().plan(_request(result), result.cards)

    assert plan.disposition is LaterTaskReopenDisposition.READY
    assert plan.reason_code == "explicit_later_task_with_reopenable_unsupported_claims"
    assert plan.targets
    assert set(t2_claim_ids).issubset({target.claim_id for target in plan.targets})
    assert all(target.source_span.document_id == result.source.document_id for target in plan.targets)
    assert all(target.source_span.source_revision == result.source.source_revision for target in plan.targets)
    assert all(target.source_span.verify(result.source.text) for target in plan.targets)


@pytest.mark.asyncio
async def test_later_task_reopen_does_not_trigger_without_unsupported_signal() -> None:
    result = await _t1_result()

    plan = LaterTaskReopenPlanner().plan(
        _request(result, claim_ids=()),
        result.cards,
    )

    assert plan.disposition is LaterTaskReopenDisposition.UNKNOWN
    assert plan.reason_code == "no_unsupported_claim_signal"
    assert plan.targets == ()


@pytest.mark.asyncio
async def test_later_task_reopen_refuses_wrong_source_revision() -> None:
    result = await _t1_result()

    plan = LaterTaskReopenPlanner().plan(
        _request(result, revision="sha256:not-the-original-revision"),
        result.cards,
    )

    assert plan.disposition is LaterTaskReopenDisposition.REFUSED
    assert plan.reason_code == "source_revision_mismatch"
    assert plan.targets == ()


@pytest.mark.asyncio
async def test_later_task_reopen_returns_unknown_when_budget_cannot_cover_targets() -> None:
    result = await _t1_result()

    plan = LaterTaskReopenPlanner().plan(
        _request(result),
        result.cards,
        budget=LaterTaskReopenBudget(max_spans=1, max_total_chars=1),
    )

    assert plan.disposition is LaterTaskReopenDisposition.UNKNOWN
    assert plan.reason_code == "reopen_budget_insufficient"
    assert plan.targets == ()
