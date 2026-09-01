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
    LaterTaskReopenError,
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


def _source(
    *,
    document_id: str = "later-task-reopen-fixture",
    source_revision: str | None = None,
) -> RawSource:
    return RawSource(
        document_id=document_id,
        source_revision=source_revision,
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


async def _t1_result(source: RawSource | None = None):
    reader = _ExactSourceReader()
    assert isinstance(reader, SemanticReader)
    return await ReaderProductPipeline(reader, config=_config()).read(
        source or _source(),
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )


def _t2_claim_ids(result) -> tuple[str, ...]:
    return tuple(
        card_claim.claim.claim_id
        for card in result.cards
        for card_claim in card.claims
        if _EXCEPTION_EVIDENCE in card_claim.claim.text
    )


def _request(
    result,
    *,
    requested_claim_ids=None,
    unsupported_claim_ids=None,
    revision: str | None = None,
    document_id: str | None = None,
):
    assert result.synthesis is not None
    requested = (
        _t2_claim_ids(result)
        if requested_claim_ids is None
        else tuple(requested_claim_ids)
    )
    unsupported = (
        tuple(result.synthesis.unsupported_source_claim_ids)
        if unsupported_claim_ids is None
        else tuple(unsupported_claim_ids)
    )
    return LaterTaskReopenRequest(
        task_text=_T2,
        document_id=document_id or result.source.document_id,
        source_revision=revision or result.source.source_revision,
        requested_claim_ids=requested,
        unsupported_source_claim_ids=unsupported,
    )


@pytest.mark.asyncio
async def test_later_task_reopen_selects_exact_requested_unsupported_t2_span() -> None:
    result = await _t1_result()
    assert result.synthesis is not None
    assert _EXCEPTION_EVIDENCE not in result.source_grounded_digest

    t2_claim_ids = _t2_claim_ids(result)
    assert t2_claim_ids
    assert set(t2_claim_ids).issubset(result.synthesis.unsupported_source_claim_ids)

    plan = LaterTaskReopenPlanner().plan(_request(result), result.cards)

    assert plan.disposition is LaterTaskReopenDisposition.READY
    assert plan.reason_code == "explicit_later_task_with_reopenable_unsupported_claims"
    assert {target.claim_id for target in plan.targets} == set(t2_claim_ids)
    assert all(target.source_span.document_id == result.source.document_id for target in plan.targets)
    assert all(target.source_span.source_revision == result.source.source_revision for target in plan.targets)
    assert all(target.source_span.verify(result.source.text) for target in plan.targets)


@pytest.mark.asyncio
async def test_later_task_reopen_only_selects_requested_subset_of_unsupported() -> None:
    result = await _t1_result()
    assert result.synthesis is not None
    unsupported = tuple(result.synthesis.unsupported_source_claim_ids)
    assert len(unsupported) >= 2
    requested = (unsupported[0],)

    plan = LaterTaskReopenPlanner().plan(
        _request(
            result,
            requested_claim_ids=requested,
            unsupported_claim_ids=unsupported,
        ),
        result.cards,
    )

    assert plan.disposition is LaterTaskReopenDisposition.READY
    assert {target.claim_id for target in plan.targets} == set(requested)
    assert unsupported[1] not in {target.claim_id for target in plan.targets}


@pytest.mark.asyncio
async def test_later_task_reopen_does_not_infer_task_relevance_without_claim_selection() -> None:
    result = await _t1_result()
    plan = LaterTaskReopenPlanner().plan(
        _request(result, requested_claim_ids=()),
        result.cards,
    )
    assert plan.disposition is LaterTaskReopenDisposition.UNKNOWN
    assert plan.reason_code == "no_later_task_claim_selection"
    assert plan.targets == ()


@pytest.mark.asyncio
async def test_later_task_reopen_does_not_trigger_without_unsupported_signal() -> None:
    result = await _t1_result()
    plan = LaterTaskReopenPlanner().plan(
        _request(result, unsupported_claim_ids=()),
        result.cards,
    )
    assert plan.disposition is LaterTaskReopenDisposition.UNKNOWN
    assert plan.reason_code == "no_unsupported_claim_signal"
    assert plan.targets == ()


@pytest.mark.asyncio
async def test_later_task_reopen_requires_requested_claim_to_be_unsupported() -> None:
    result = await _t1_result()
    t2_claim_ids = _t2_claim_ids(result)
    assert t2_claim_ids
    plan = LaterTaskReopenPlanner().plan(
        _request(result, unsupported_claim_ids=("unrelated-claim-id",)),
        result.cards,
    )
    assert plan.disposition is LaterTaskReopenDisposition.UNKNOWN
    assert plan.reason_code == "requested_claims_not_marked_unsupported"
    assert plan.targets == ()


@pytest.mark.asyncio
async def test_later_task_reopen_refuses_when_document_has_only_wrong_revision_cards() -> None:
    current = await _t1_result()
    old = await _t1_result(_source(source_revision="revision-old"))
    plan = LaterTaskReopenPlanner().plan(_request(current), old.cards)
    assert plan.disposition is LaterTaskReopenDisposition.REFUSED
    assert plan.reason_code == "source_revision_mismatch"
    assert plan.targets == ()


@pytest.mark.asyncio
async def test_later_task_reopen_mixed_revisions_use_only_exact_requested_revision() -> None:
    current = await _t1_result(_source(source_revision="revision-current"))
    old = await _t1_result(_source(source_revision="revision-old"))

    plan = LaterTaskReopenPlanner().plan(
        _request(current),
        tuple(old.cards) + tuple(current.cards),
    )

    assert plan.disposition is LaterTaskReopenDisposition.READY
    assert plan.targets
    assert all(target.source_span.source_revision == "revision-current" for target in plan.targets)


@pytest.mark.asyncio
async def test_later_task_reopen_current_revision_without_eligible_claim_is_unknown_not_refused() -> None:
    current = await _t1_result(_source(source_revision="revision-current"))
    old = await _t1_result(_source(source_revision="revision-old"))
    current_without_requested = tuple(
        card
        for card in current.cards
        if not any(
            claim.claim.claim_id in set(_t2_claim_ids(current))
            for claim in card.claims
        )
    )
    assert current_without_requested

    plan = LaterTaskReopenPlanner().plan(
        _request(current),
        tuple(old.cards) + current_without_requested,
    )

    assert plan.disposition is LaterTaskReopenDisposition.UNKNOWN
    assert plan.reason_code == "eligible_claims_not_reopenable_from_cards"


@pytest.mark.asyncio
async def test_later_task_reopen_wrong_document_is_unknown() -> None:
    result = await _t1_result()
    plan = LaterTaskReopenPlanner().plan(
        _request(result, document_id="other-document"),
        result.cards,
    )
    assert plan.disposition is LaterTaskReopenDisposition.UNKNOWN
    assert plan.reason_code == "eligible_claims_not_reopenable_from_cards"
    assert plan.targets == ()


@pytest.mark.asyncio
async def test_later_task_reopen_empty_cards_is_unknown() -> None:
    result = await _t1_result()
    plan = LaterTaskReopenPlanner().plan(_request(result), ())
    assert plan.disposition is LaterTaskReopenDisposition.UNKNOWN
    assert plan.reason_code == "eligible_claims_not_reopenable_from_cards"
    assert plan.targets == ()


@pytest.mark.asyncio
async def test_later_task_reopen_rejects_non_section_card_input() -> None:
    result = await _t1_result()
    with pytest.raises(LaterTaskReopenError):
        LaterTaskReopenPlanner().plan(_request(result), (object(),))


@pytest.mark.asyncio
async def test_later_task_reopen_is_independent_of_card_input_order() -> None:
    result = await _t1_result()
    request = _request(result)
    planner = LaterTaskReopenPlanner()
    forward = planner.plan(request, result.cards)
    reverse = planner.plan(request, tuple(reversed(result.cards)))
    assert forward == reverse


@pytest.mark.asyncio
async def test_later_task_reopen_returns_unknown_when_char_budget_cannot_cover_targets() -> None:
    result = await _t1_result()
    plan = LaterTaskReopenPlanner().plan(
        _request(result),
        result.cards,
        budget=LaterTaskReopenBudget(max_spans=100, max_total_chars=1),
    )
    assert plan.disposition is LaterTaskReopenDisposition.UNKNOWN
    assert plan.reason_code == "reopen_budget_insufficient"
    assert plan.targets == ()


@pytest.mark.asyncio
async def test_later_task_reopen_returns_unknown_when_span_budget_cannot_cover_targets() -> None:
    result = await _t1_result()
    assert result.synthesis is not None
    unsupported = tuple(result.synthesis.unsupported_source_claim_ids)
    assert len(unsupported) >= 2
    plan = LaterTaskReopenPlanner().plan(
        _request(
            result,
            requested_claim_ids=unsupported,
            unsupported_claim_ids=unsupported,
        ),
        result.cards,
        budget=LaterTaskReopenBudget(max_spans=1, max_total_chars=100_000),
    )
    assert plan.disposition is LaterTaskReopenDisposition.UNKNOWN
    assert plan.reason_code == "reopen_budget_insufficient"
    assert plan.targets == ()
