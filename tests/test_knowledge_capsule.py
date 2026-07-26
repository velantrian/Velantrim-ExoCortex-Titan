"""PR-SYN-01 — immutable KnowledgeCapsule contract."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.knowledge_capsule import (
    CapsuleClaim,
    CapsuleValidationError,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)


def _span(raw: str = "The door may be open.", *, start: int = 4, end: int = 20) -> SourceSpan:
    return SourceSpan.from_text(
        document_id="doc-1",
        raw_text=raw,
        start_offset=start,
        end_offset=end,
        source_revision="rev-1",
    )


def _claim(span: SourceSpan | None = None, **overrides) -> CapsuleClaim:
    data = {
        "text": "The door may be open.",
        "modality": ClaimModality.HYPOTHESIS,
        "source_spans": (_span() if span is None else span,),
        "extraction_confidence": 0.95,
        "truth_confidence": 0.4,
        "qualifiers": ("may",),
        "uncertainties": ("The source does not confirm the current state.",),
        "applicability_conditions": ("At the time described by the source.",),
        "temporal_scope": "source time",
    }
    data.update(overrides)
    return CapsuleClaim.create(**data)


def _capsule(*, claim: CapsuleClaim | None = None, created_at: datetime | None = None):
    return KnowledgeCapsule.create(
        source_document_id="doc-1",
        essence="The source presents a qualified possibility about the door.",
        claims=(_claim() if claim is None else claim,),
        entities=("door",),
        omitted_questions=("Is the door open now?",),
        coverage_score=0.8,
        compression_ratio=3.5,
        reader_id="extractive-reader",
        reader_version="1.0.0",
        created_at=created_at,
    )


class TestSourceSpan:
    def test_from_text_preserves_exact_unicode_span_and_hash(self):
        raw = "До 🚪 дверь может быть открыта. После"
        start = raw.index("🚪")
        end = raw.index(". После") + 1

        span = SourceSpan.from_text(
            document_id="doc-unicode",
            raw_text=raw,
            start_offset=start,
            end_offset=end,
            source_revision="r1",
        )

        assert raw[span.start_offset : span.end_offset] == "🚪 дверь может быть открыта."
        assert span.verify(raw) is True
        assert span.verify(raw.replace("открыта", "закрыта")) is False

    @pytest.mark.parametrize(
        ("start", "end"),
        [(-1, 2), (0, 0), (3, 2), (0, 999)],
    )
    def test_from_text_rejects_invalid_offsets(self, start, end):
        with pytest.raises(CapsuleValidationError):
            SourceSpan.from_text(
                document_id="doc-1",
                raw_text="abc",
                start_offset=start,
                end_offset=end,
            )

    def test_direct_constructor_rejects_non_sha256_hash(self):
        with pytest.raises(CapsuleValidationError, match="SHA-256"):
            SourceSpan(
                span_id="span-1",
                document_id="doc-1",
                start_offset=0,
                end_offset=1,
                content_hash="not-a-hash",
            )


class TestCapsuleClaim:
    def test_claim_requires_source_span(self):
        with pytest.raises(CapsuleValidationError, match="at least one SourceSpan"):
            CapsuleClaim.create(
                text="Unsupported extraction",
                modality=ClaimModality.WORLD_FACT,
                source_spans=(),
                extraction_confidence=0.5,
            )

    def test_extraction_and_truth_confidence_are_independent(self):
        claim = _claim(extraction_confidence=0.99, truth_confidence=0.1)

        assert claim.extraction_confidence == 0.99
        assert claim.truth_confidence == 0.1

    def test_hypothesis_cannot_start_as_absolute_truth(self):
        with pytest.raises(CapsuleValidationError, match="hypothesis"):
            _claim(truth_confidence=1.0)

    @pytest.mark.parametrize("field_name", ["extraction_confidence", "truth_confidence"])
    @pytest.mark.parametrize("value", [-0.01, 1.01, float("inf"), float("nan")])
    def test_confidence_must_be_finite_probability(self, field_name, value):
        with pytest.raises(CapsuleValidationError):
            _claim(**{field_name: value})


class TestKnowledgeCapsule:
    def test_capsule_and_nested_records_are_immutable(self):
        capsule = _capsule()

        with pytest.raises(FrozenInstanceError):
            capsule.essence = "mutated"  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            capsule.claims[0].text = "mutated"  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            capsule.claims[0].source_spans[0].start_offset = 0  # type: ignore[misc]

    def test_identical_content_has_stable_identity_despite_time_and_claim_id(self):
        first_claim = _claim(claim_id="caller-id-a")
        second_claim = _claim(claim_id="caller-id-b")
        first = _capsule(claim=first_claim, created_at=datetime(2026, 7, 26, tzinfo=UTC))
        second = _capsule(
            claim=second_claim,
            created_at=datetime(2026, 7, 27, tzinfo=UTC),
        )

        assert first.capsule_id == second.capsule_id

    def test_reader_metadata_does_not_change_semantic_identity(self):
        first = _capsule()
        second = KnowledgeCapsule.create(
            source_document_id="doc-1",
            essence=first.essence,
            claims=first.claims,
            entities=first.entities,
            omitted_questions=first.omitted_questions,
            coverage_score=0.2,
            compression_ratio=99.0,
            reader_id="different-provider",
            reader_version="42",
            prompt_version="prompt-new",
        )

        assert first.capsule_id == second.capsule_id

    def test_span_change_changes_capsule_identity(self):
        raw = "The door may be open. Another sentence."
        first = _capsule(claim=_claim(_span(raw, start=4, end=20)))
        second_span = SourceSpan.from_text(
            document_id="doc-1",
            raw_text=raw,
            start_offset=4,
            end_offset=21,
            source_revision="rev-1",
        )
        second = _capsule(claim=_claim(second_span))

        assert first.capsule_id != second.capsule_id

    def test_manual_id_mismatch_fails_closed(self):
        capsule = _capsule()

        with pytest.raises(CapsuleValidationError, match="capsule_id"):
            replace(capsule, capsule_id="0" * 64)

    def test_all_spans_must_belong_to_capsule_document(self):
        raw = "The door may be open."
        other_span = SourceSpan.from_text(
            document_id="doc-2",
            raw_text=raw,
            start_offset=4,
            end_offset=20,
        )

        with pytest.raises(CapsuleValidationError, match="source_document_id"):
            KnowledgeCapsule.create(
                source_document_id="doc-1",
                essence="A mismatched source.",
                claims=(_claim(other_span),),
                reader_id="extractive-reader",
                reader_version="1.0.0",
            )

    def test_created_at_must_be_timezone_aware(self):
        with pytest.raises(CapsuleValidationError, match="timezone-aware"):
            _capsule(created_at=datetime(2026, 7, 26))

    def test_order_of_claims_does_not_change_content_identity(self):
        base_span = _span()
        first_claim = _claim(base_span, text="Claim A", claim_id="a")
        second_claim = _claim(base_span, text="Claim B", claim_id="b")

        first = KnowledgeCapsule.create(
            source_document_id="doc-1",
            essence="Two claims.",
            claims=(first_claim, second_claim),
            reader_id="extractive-reader",
            reader_version="1.0.0",
        )
        second = KnowledgeCapsule.create(
            source_document_id="doc-1",
            essence="Two claims.",
            claims=(second_claim, first_claim),
            reader_id="extractive-reader",
            reader_version="1.0.0",
            created_at=datetime.now(UTC) + timedelta(days=1),
        )

        assert first.capsule_id == second.capsule_id
