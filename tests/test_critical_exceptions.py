from dataclasses import replace

import pytest

from core.critical_exceptions import (
    CriticalExceptionError,
    DeterministicCriticalExceptionScanner,
    ExceptionCategory,
    ExceptionValidationStatus,
)
from core.document_structure import (
    DeterministicDocumentStructureParser,
    DocumentStructureFormat,
)
from core.hierarchical_section_planner import HierarchicalSectionPlanner, ReadingUnit
from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.section_card import SectionCard, SectionCardBuilder, SpanCoordinateSpace
from core.semantic_reader import RawSource, ReaderResult


def _card_for_claim(text: str, claim_text: str) -> tuple[RawSource, ReadingUnit, SectionCard]:
    source = RawSource(
        document_id="exception-doc",
        text=text,
        source_revision="revision-1",
    )
    structure = DeterministicDocumentStructureParser().parse(
        source,
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )
    plan = HierarchicalSectionPlanner().plan(source, structure)
    unit = plan.units[0]
    local_text = source.text[unit.start_offset : unit.end_offset]
    local_start = local_text.index(claim_text)
    span = SourceSpan.from_text(
        document_id=unit.document_id,
        raw_text=local_text,
        start_offset=local_start,
        end_offset=local_start + len(claim_text),
        source_revision=unit.source_revision,
    )
    claim = CapsuleClaim.create(
        text=claim_text,
        modality=ClaimModality.OBSERVATION,
        source_spans=(span,),
        extraction_confidence=1.0,
    )
    capsule = KnowledgeCapsule.create(
        source_document_id=unit.document_id,
        essence="Local exception fixture.",
        claims=(claim,),
        reader_id="fixture-reader",
        reader_version="1",
    )
    card = SectionCardBuilder().build(
        source,
        unit,
        ReaderResult.success(capsule),
        plan_id=plan.plan_id,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )
    return source, unit, card


def test_scanner_emits_exact_unvalidated_source_linked_candidates() -> None:
    text = (
        "The system may write cache files. "
        "However, it does not apply to secrets unless approval is granted."
    )
    source, unit, card = _card_for_claim(
        text,
        "The system may write cache files",
    )

    result = DeterministicCriticalExceptionScanner().scan(source, card)

    assert [candidate.category for candidate in result.candidates] == [
        ExceptionCategory.CONTRAST,
        ExceptionCategory.EXCLUSION,
        ExceptionCategory.CONDITION,
    ]
    assert [candidate.trigger_phrase.lower() for candidate in result.candidates] == [
        "however",
        "does not apply to",
        "unless",
    ]
    assert result.receipt.scanned_span == unit.source_span
    assert result.receipt.trigger_match_count == 3
    assert result.receipt.candidate_ids == tuple(
        candidate.candidate_id for candidate in result.candidates
    )

    expected_target = card.claims[0].claim.claim_id
    for candidate in result.candidates:
        assert candidate.validation_status is ExceptionValidationStatus.UNVALIDATED
        assert candidate.target_claim_refs == (expected_target,)
        assert candidate.trigger_span.verify(source.text)
        assert candidate.statement_span.verify(source.text)
        assert source.text[
            candidate.trigger_span.start_offset : candidate.trigger_span.end_offset
        ] == candidate.trigger_phrase
        assert source.text[
            candidate.statement_span.start_offset : candidate.statement_span.end_offset
        ] == candidate.statement_text
        assert (
            candidate.statement_span.start_offset
            <= candidate.trigger_span.start_offset
            < candidate.trigger_span.end_offset
            <= candidate.statement_span.end_offset
        )


def test_candidate_without_preceding_or_overlapping_claim_is_explicitly_unresolved() -> None:
    text = "Unless approved, operation stops. A later claim appears here."
    source, _, card = _card_for_claim(text, "A later claim")

    result = DeterministicCriticalExceptionScanner(
        target_claim_window_chars=500
    ).scan(source, card)

    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.target_claim_refs == ()
    assert candidate.warnings == ("unresolved_target_claim",)


def test_scan_with_no_signals_still_produces_a_complete_receipt() -> None:
    text = "The system writes one local cache file."
    source, unit, card = _card_for_claim(text, "one local cache file")

    result = DeterministicCriticalExceptionScanner().scan(source, card)

    assert result.candidates == ()
    assert result.receipt.unit_id == unit.unit_id
    assert result.receipt.trigger_match_count == 0
    assert result.receipt.candidate_ids == ()


def test_scan_identity_is_deterministic() -> None:
    text = "A rule applies only if the source is verified."
    source, _, card = _card_for_claim(text, "A rule applies")
    scanner = DeterministicCriticalExceptionScanner()

    first = scanner.scan(source, card)
    second = scanner.scan(source, card)

    assert first == second


def test_candidate_content_cannot_change_under_a_stale_id() -> None:
    text = "The operation is allowed unless policy rejects it."
    source, _, card = _card_for_claim(text, "The operation is allowed")
    candidate = DeterministicCriticalExceptionScanner().scan(
        source,
        card,
    ).candidates[0]

    with pytest.raises(CriticalExceptionError, match="candidate_id"):
        replace(candidate, trigger_phrase="forged")


def test_scanner_rejects_stale_source_revision() -> None:
    text = "The operation is allowed unless policy rejects it."
    source, _, card = _card_for_claim(text, "The operation is allowed")
    stale = RawSource(
        document_id=source.document_id,
        text=source.text,
        source_revision="revision-2",
    )

    with pytest.raises(CriticalExceptionError, match="revision"):
        DeterministicCriticalExceptionScanner().scan(stale, card)
