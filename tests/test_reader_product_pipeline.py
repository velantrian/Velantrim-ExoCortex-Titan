from __future__ import annotations

from collections import defaultdict

import pytest

from core.document_structure import DocumentStructureFormat
from core.hierarchical_section_planner import SectionPlanningBudget
from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.reader_product_pipeline import ReaderProductConfig, ReaderProductPipeline
from core.reader_core_contracts import SessionState
from core.semantic_reader import (
    RawSource,
    ReaderBudget,
    ReaderMode,
    ReaderResult,
    ReaderStatus,
    SemanticReader,
)


class _ExactQuoteReader:
    reader_id = "tests.exact-quote-reader"
    reader_version = "1"

    def __init__(self, *, fail_first_for: str | None = None, always_fail_for: str | None = None) -> None:
        self.fail_first_for = fail_first_for
        self.always_fail_for = always_fail_for
        self.calls: dict[str, int] = defaultdict(int)
        self.modes: list[ReaderMode] = []

    async def extract(
        self,
        source: RawSource,
        *,
        mode: ReaderMode,
        budget: ReaderBudget,
    ) -> ReaderResult:
        assert isinstance(budget, ReaderBudget)
        self.modes.append(mode)
        self.calls[source.text] += 1
        if self.always_fail_for and self.always_fail_for in source.text:
            return ReaderResult.failed(
                ReaderStatus.PROVIDER_ERROR,
                code="TEST_PERMANENT_FAILURE",
                safe_message="test failure",
            )
        if (
            self.fail_first_for
            and self.fail_first_for in source.text
            and self.calls[source.text] == 1
        ):
            return ReaderResult.failed(
                ReaderStatus.PROVIDER_ERROR,
                code="TEST_FIRST_FAILURE",
                safe_message="test first failure",
                retryable=True,
            )

        claim_text = source.text.strip()
        start = source.text.index(claim_text)
        span = SourceSpan.from_text(
            document_id=source.document_id,
            raw_text=source.text,
            start_offset=start,
            end_offset=start + len(claim_text),
            source_revision=source.source_revision,
        )
        claim = CapsuleClaim.create(
            text=claim_text,
            modality=ClaimModality.OBSERVATION,
            source_spans=(span,),
            extraction_confidence=1.0,
        )
        capsule = KnowledgeCapsule.create(
            source_document_id=source.document_id,
            essence=claim_text,
            claims=(claim,),
            reader_id=self.reader_id,
            reader_version=self.reader_version,
            coverage_score=1.0,
        )
        return ReaderResult.success(capsule)


def _config() -> ReaderProductConfig:
    return ReaderProductConfig(
        initial_mode=ReaderMode.STANDARD,
        section_budget=SectionPlanningBudget(
            max_unit_chars=70,
            min_unit_chars=20,
            boundary_search_chars=60,
        ),
        reader_budget=ReaderBudget(
            max_source_chars=1_000,
            max_claims=16,
            max_essence_chars=500,
        ),
        max_digest_chars=2_000,
    )


def _source() -> RawSource:
    return RawSource(
        document_id="reader-product-test",
        text=(
            "The first section establishes the main premise and its context.\n\n"
            "The second section records an important qualification for the premise.\n\n"
            "The third section closes the example with a bounded conclusion."
        ),
    )


@pytest.mark.asyncio
async def test_complete_read_builds_source_linked_synthesis_without_writes() -> None:
    reader = _ExactQuoteReader()
    result = await ReaderProductPipeline(reader, config=_config()).read(
        _source(),
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )

    assert result.complete is True
    assert result.total_units >= 3
    assert result.completed_units == result.total_units
    assert result.session.state is SessionState.COMPLETED
    assert result.synthesis is not None
    assert result.synthesis.central_theme_claim_id
    assert result.source_grounded_digest
    assert result.reader_attempts == result.total_units
    assert result.reread_attempts == 0
    assert not result.remaining_reread_plan.tasks
    assert "synthesis_is_interpretation_candidate_not_truth" in result.warnings
    assert "relation_detection_not_auto_inferred_in_product_v1" in result.warnings


@pytest.mark.asyncio
async def test_failed_unit_is_retried_once_from_selective_reread_plan() -> None:
    reader = _ExactQuoteReader(fail_first_for="second section")
    result = await ReaderProductPipeline(reader, config=_config()).read(_source())

    assert result.complete is True
    assert result.session.state is SessionState.COMPLETED
    assert result.reread_attempts == 1
    assert result.reader_attempts == result.total_units + 1
    assert ReaderMode.DEEP in reader.modes
    assert not result.remaining_reread_plan.tasks


@pytest.mark.asyncio
async def test_permanent_reader_gap_degrades_and_skips_global_synthesis() -> None:
    reader = _ExactQuoteReader(always_fail_for="second section")
    result = await ReaderProductPipeline(reader, config=_config()).read(_source())

    assert result.complete is False
    assert result.completed_units < result.total_units
    assert result.session.state is SessionState.DEGRADED
    assert result.session.pending_unit_ids
    assert result.synthesis is None
    assert result.relations is None
    assert result.reread_attempts == 1
    assert result.remaining_reread_plan.tasks
    assert "global_synthesis_skipped_incomplete_reading" in result.warnings
    assert "remaining_reread_work_requires_explicit_new_run" in result.warnings


@pytest.mark.asyncio
async def test_markdown_structure_is_reused_instead_of_new_parser_logic() -> None:
    source = RawSource(
        document_id="reader-product-markdown",
        text=(
            "# Chapter One\n"
            "The first chapter has a grounded observation.\n\n"
            "# Chapter Two\n"
            "The second chapter has another grounded observation.\n"
        ),
    )
    reader = _ExactQuoteReader()
    result = await ReaderProductPipeline(reader, config=_config()).read(
        source,
        document_format=DocumentStructureFormat.MARKDOWN,
    )

    assert result.complete is True
    section_ids = {unit.section_id for unit in result.reading_plan.units}
    assert len(section_ids) == 2
    assert result.synthesis is not None


def test_pipeline_requires_semantic_reader_contract() -> None:
    with pytest.raises(Exception, match="SemanticReader"):
        ReaderProductPipeline(object())  # type: ignore[arg-type]

    assert isinstance(_ExactQuoteReader(), SemanticReader)
