"""F2 Hidden Exception: bounded later-task representation-sufficiency fixture.

This fixture intentionally does not add a reopen mechanism. It establishes the
narrow boundary discovered in the 2026-09-01 memory-boundary audit:

* a compact T1 representation can be valid for T1 while omitting source material
  that becomes material for a later T2;
* omission from the compact representation must not be interpreted as absence
  from the source; and
* the current ReaderProductPipeline result is not a durable resume state, so an
  end-to-end later-task reopen policy remains NOT_ESTABLISHED.

The fixture is evidence for a TEST/CONTRACT GAP only. It grants no runtime,
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


_EXCEPTION_EVIDENCE = "revoked credential"
_T2 = "May a request involving a revoked credential be approved?"


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
        # claim. The pipeline already records unsupported_source_claim_ids for
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


def _has_t2_material(text: str, task: str) -> bool:
    """Bounded fixture predicate: does this representation expose T2's key evidence?"""

    assert task == _T2
    return _EXCEPTION_EVIDENCE in text


def _t2_material_claim_ids(result) -> tuple[str, ...]:
    """Return source-linked claim IDs whose exact claim text contains T2 material."""

    return tuple(
        card_claim.claim.claim_id
        for card in result.cards
        for card_claim in card.claims
        if _has_t2_material(card_claim.claim.text, _T2)
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

    # X is genuinely present in the source and in source-linked Reader material.
    assert _EXCEPTION_EVIDENCE in result.source.text
    assert any(
        _EXCEPTION_EVIDENCE in card_claim.claim.text
        for card in result.cards
        for card_claim in card.claims
    )

    # But the bounded compact T1 digest can legally omit X.
    assert _EXCEPTION_EVIDENCE not in result.source_grounded_digest

    central = next(
        claim
        for claim in result.synthesis.claims
        if claim.synthesis_claim_id == result.synthesis.central_theme_claim_id
    )
    assert result.synthesis.unsupported_source_claim_ids
    assert set(central.supporting_claim_ids).isdisjoint(
        set(result.synthesis.unsupported_source_claim_ids)
    )


async def test_f2_new_t2_exposes_compact_view_insufficiency_without_proving_absence() -> None:
    """A later task needs evidence omitted by the otherwise valid T1 compact view."""

    result = await _run_t1()

    # The genuinely new T2 is answerable from the source-linked material...
    assert _has_t2_material(result.source.text, _T2) is True
    assert any(
        _has_t2_material(card_claim.claim.text, _T2)
        for card in result.cards
        for card_claim in card.claims
    )

    # ...but not from the compact T1 representation alone.
    assert _has_t2_material(result.source_grounded_digest, _T2) is False

    # The existing synthesis contract already exposes the omitted T2-material
    # claim as unsupported rather than silently treating the omission as absence.
    t2_claim_ids = _t2_material_claim_ids(result)
    assert t2_claim_ids
    assert set(t2_claim_ids).issubset(
        set(result.synthesis.unsupported_source_claim_ids)
    )
    assert "source_claims_not_represented_in_synthesis" in result.synthesis.warnings

    # Therefore omission from T1 cannot be treated as evidence that X is absent.
    assert _EXCEPTION_EVIDENCE in result.source.text
    assert _EXCEPTION_EVIDENCE not in result.source_grounded_digest


async def test_f2_later_task_reopen_policy_remains_not_established() -> None:
    """Current product result explicitly stops short of durable later-task resume.

    This is intentionally a passing localization test, not an expected-failure
    implementation demand. A future owner-local later-task reopen contract may
    replace this assertion only with separate evidence and authorization.
    """

    result = await _run_t1()

    assert "session_snapshot_is_in_memory_not_durable_resume_state" in result.warnings

    # Provenance required for a possible future bounded reopen is preserved in
    # the current run; that is weaker than having a durable T2 reopen policy.
    assert all(card.source_revision == result.source.source_revision for card in result.cards)
    assert all(card.unit_source_span.document_id == result.source.document_id for card in result.cards)
