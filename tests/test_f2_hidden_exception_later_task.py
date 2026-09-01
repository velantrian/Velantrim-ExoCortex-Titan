"""F2 Hidden Exception: bounded later-task representation-sufficiency fixture.

This fixture intentionally does not add a reopen mechanism.  It establishes the
narrow boundary discovered in the 2026-09-01 memory-boundary audit:

* a compact T1 representation can be valid for T1 while omitting source material
  that becomes material for a later T2;
* omission from the compact representation must not be interpreted as absence
  from the source; and
* the current ReaderProductPipeline result is not a durable resume state, so an
  end-to-end later-task reopen policy remains NOT_ESTABLISHED.

The fixture is evidence for a TEST/CONTRACT GAP only.  It grants no runtime,
Canon, persistence, or architecture authority.
"""

from __future__ import annotations

from core.document_structure import DocumentStructureFormat
from core.hierarchical_section_planner import SectionPlanningBudget
from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.reader_product_pipeline import ReaderProductConfig, ReaderProductPipeline
from core.semantic_reader import (
    RawSource,
    ReaderBudget,
    ReaderMode,
    ReaderResult,
    SemanticReader,
)


class _ExactSourceReader:
    """Deterministic test reader that preserves exact unit text as one claim."""

    reader_id = "tests.f2-exact-source-reader"
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
        # Force a legitimate compact T1 view that cannot contain every source
        # claim.  The pipeline already records unsupported_source_claim_ids for
        # this bounded truncation case.
        max_digest_chars=96,
    )


def _source() -> RawSource:
    return RawSource(
        document_id="f2-hidden-exception-later-task",
        text=(
            "Policy R: standard requests may be approved after ordinary review.\n\n"
            "Operational context: the ordinary path is the dominant case and is "
            "sufficient for routine T1 summarization.\n\n"
            "Hidden exception X: requests involving a revoked credential must never "
            "be approved, even when ordinary review would otherwise pass."
        ),
    )


async def _run_t1():
    reader = _ExactSourceReader()
    assert isinstance(reader, SemanticReader)
    return await ReaderProductPipeline(reader, config=_config()).read(
        _source(),
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )


async def test_f2_t1_compact_view_can_omit_later_material_exception() -> None:
    """T1 sufficiency does not establish T2 sufficiency."""

    result = await _run_t1()

    assert result.complete is True
    assert result.synthesis is not None

    exception_text = "revoked credential"

    # X is genuinely present in the source and in source-linked Reader material.
    assert exception_text in result.source.text
    assert any(
        exception_text in card_claim.claim.text
        for card in result.cards
        for card_claim in card.claims
    )

    # But the bounded compact T1 digest can legally omit X.
    assert exception_text not in result.source_grounded_digest

    central = next(
        claim
        for claim in result.synthesis.claims
        if claim.synthesis_claim_id == result.synthesis.central_theme_claim_id
    )
    assert result.synthesis.unsupported_source_claim_ids
    assert set(central.supporting_claim_ids).isdisjoint(
        set(result.synthesis.unsupported_source_claim_ids)
    )


def test_f2_omitted_from_compact_view_is_not_absent_from_source() -> None:
    """The discriminating law is NOT REPRESENTED != ABSENT."""

    source = _source()
    assert "revoked credential" in source.text


async def test_f2_later_task_reopen_policy_remains_not_established() -> None:
    """Current product result explicitly stops short of durable later-task resume.

    This is intentionally a passing localization test, not an expected-failure
    implementation demand.  A future owner-local later-task reopen contract may
    replace this assertion only with separate evidence and authorization.
    """

    result = await _run_t1()

    assert "session_snapshot_is_in_memory_not_durable_resume_state" in result.warnings

    # Provenance required for a possible future bounded reopen is preserved in
    # the current run; that is weaker than having a durable T2 reopen policy.
    assert all(card.source_revision == result.source.source_revision for card in result.cards)
    assert all(card.unit_source_span.document_id == result.source.document_id for card in result.cards)
