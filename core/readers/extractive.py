"""Deterministic extractive Semantic Reader.

The reader intentionally performs no generative summarisation.  It selects exact
source sentences, keeps their character offsets, assigns conservative modalities
from explicit lexical signals, and leaves ``truth_confidence`` unset.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from core.knowledge_capsule import (
    CapsuleClaim,
    CapsuleValidationError,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.readers.base import BaseSemanticReader
from core.semantic_reader import (
    RawSource,
    ReaderBudget,
    ReaderMode,
    ReaderResult,
    ReaderStatus,
    ReaderWarning,
)

_SENTENCE_ENDINGS = frozenset(".!?。！？")
_UNCERTAINTY_MARKERS = (
    "maybe",
    "perhaps",
    "possibly",
    "may",
    "might",
    "could",
    "likely",
    "unlikely",
    "appears",
    "suggests",
    "возможно",
    "вероятно",
    "может",
    "могут",
    "предположительно",
    "кажется",
    "по-видимому",
)
_OPINION_MARKERS = (
    "i think",
    "i believe",
    "we think",
    "we believe",
    "in my opinion",
    "по моему мнению",
    "я думаю",
    "я считаю",
    "мы считаем",
)
_GOAL_PREFIXES = ("goal:", "objective:", "цель:", "задача:")
_INSTRUCTION_PREFIXES = (
    "ignore ",
    "disregard ",
    "please ",
    "do ",
    "write ",
    "create ",
    "delete ",
    "remember ",
    "игнорируй ",
    "не следуй ",
    "пожалуйста, ",
    "сделай ",
    "запиши ",
    "создай ",
    "удали ",
    "запомни ",
)
_CONDITION_PREFIXES = (
    "if ",
    "when ",
    "provided that ",
    "in case ",
    "under ",
    "если ",
    "когда ",
    "в случае ",
    "при ",
)
_MODAL_WORDS = (
    "may",
    "might",
    "can",
    "could",
    "will",
    "может",
    "могут",
    "будет",
    "должен",
    "должна",
    "должны",
)


class ExtractiveReader(BaseSemanticReader):
    """Fast, deterministic baseline that never invents claim text."""

    reader_id = "titan.extractive"
    reader_version = "1.0.0"
    supported_modes = frozenset({ReaderMode.FAST})

    async def extract(
        self,
        source: RawSource,
        *,
        mode: ReaderMode = ReaderMode.FAST,
        budget: ReaderBudget | None = None,
    ) -> ReaderResult:
        resolved_budget = budget or ReaderBudget()
        if not self.supports_mode(mode):
            return self.unsupported_mode_result(mode)
        if not source.text.strip():
            return ReaderResult.failed(
                ReaderStatus.REJECTED,
                code="EMPTY_SOURCE",
                safe_message="Source contains no extractable text",
            )
        if len(source.text) > resolved_budget.max_source_chars:
            return ReaderResult.failed(
                ReaderStatus.BUDGET_EXCEEDED,
                code="SOURCE_CHAR_BUDGET_EXCEEDED",
                safe_message="Source exceeds the configured character budget",
            )

        candidate_spans = tuple(_iter_sentence_spans(source.text))
        if not candidate_spans:
            return ReaderResult.failed(
                ReaderStatus.REJECTED,
                code="NO_EXTRACTABLE_CLAIMS",
                safe_message="Source contains no extractable claims",
            )

        selected = candidate_spans[: resolved_budget.max_claims]
        try:
            claims = tuple(self._build_claim(source, start, end) for start, end in selected)
            essence, essence_budget_exhausted = _build_essence(
                (claim.text for claim in claims), resolved_budget.max_essence_chars
            )
            if not essence:
                return ReaderResult.failed(
                    ReaderStatus.BUDGET_EXCEEDED,
                    code="ESSENCE_CHAR_BUDGET_EXCEEDED",
                    safe_message=(
                        "Essence budget cannot contain the first complete extracted claim"
                    ),
                )
            covered_non_whitespace = sum(
                sum(not char.isspace() for char in source.text[start:end])
                for start, end in selected
            )
            total_non_whitespace = sum(not char.isspace() for char in source.text)
            coverage_score = (
                covered_non_whitespace / total_non_whitespace
                if total_non_whitespace
                else 0.0
            )
            capsule = KnowledgeCapsule.create(
                source_document_id=source.document_id,
                essence=essence,
                claims=claims,
                reader_id=self.reader_id,
                reader_version=self.reader_version,
                coverage_score=min(1.0, coverage_score),
                # Compression factor: source characters per retained essence character.
                compression_ratio=len(source.text) / len(essence),
            )
        except CapsuleValidationError:
            return ReaderResult.failed(
                ReaderStatus.SPAN_VALIDATION_FAILED,
                code="CAPSULE_VALIDATION_FAILED",
                safe_message="Extracted capsule failed source-provenance validation",
            )

        warnings: list[ReaderWarning] = []
        if len(candidate_spans) > len(selected):
            warnings.append(
                ReaderWarning(
                    code="CLAIM_BUDGET_EXHAUSTED",
                    safe_message="Additional source claims were omitted by the claim budget",
                )
            )
        if essence_budget_exhausted:
            warnings.append(
                ReaderWarning(
                    code="ESSENCE_BUDGET_EXHAUSTED",
                    safe_message=(
                        "Essence contains only complete claims that fit the character budget"
                    ),
                )
            )
        if warnings:
            return ReaderResult.partial(capsule, warnings=tuple(warnings))
        return ReaderResult.success(capsule)

    def _build_claim(self, source: RawSource, start: int, end: int) -> CapsuleClaim:
        text = source.text[start:end]
        modality, qualifiers, uncertainties, conditions = _classify(text)
        span = SourceSpan.from_text(
            document_id=source.document_id,
            raw_text=source.text,
            start_offset=start,
            end_offset=end,
            source_revision=source.source_revision,
        )
        return CapsuleClaim.create(
            text=text,
            modality=modality,
            source_spans=(span,),
            extraction_confidence=1.0,
            truth_confidence=None,
            qualifiers=qualifiers,
            uncertainties=uncertainties,
            applicability_conditions=conditions,
        )


def _iter_sentence_spans(text: str) -> Iterator[tuple[int, int]]:
    """Yield trimmed, non-empty sentence spans using exact Python offsets."""

    line_start = 0
    for line in text.splitlines(keepends=True):
        content_end = line_start + len(line.rstrip("\r\n"))
        yield from _split_line(text, line_start, content_end)
        line_start += len(line)
    if line_start < len(text):
        yield from _split_line(text, line_start, len(text))


def _split_line(text: str, start: int, end: int) -> Iterator[tuple[int, int]]:
    cursor = start
    while cursor < end:
        while cursor < end and text[cursor].isspace():
            cursor += 1
        if cursor >= end:
            return
        segment_start = cursor
        while cursor < end:
            if text[cursor] in _SENTENCE_ENDINGS:
                boundary = cursor + 1
                while boundary < end and text[boundary] in _SENTENCE_ENDINGS:
                    boundary += 1
                if boundary == end or text[boundary].isspace():
                    yield segment_start, boundary
                    cursor = boundary
                    break
            cursor += 1
        else:
            segment_end = end
            while segment_end > segment_start and text[segment_end - 1].isspace():
                segment_end -= 1
            if segment_end > segment_start:
                yield segment_start, segment_end
            return


def _classify(
    text: str,
) -> tuple[ClaimModality, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    folded = " ".join(text.casefold().split())
    uncertainties = tuple(
        marker for marker in _UNCERTAINTY_MARKERS if _contains_phrase(folded, marker)
    )
    conditions = _extract_conditions(text, folded)
    qualifiers = conditions

    if folded.startswith(_GOAL_PREFIXES):
        modality = ClaimModality.GOAL
    elif folded.startswith(_INSTRUCTION_PREFIXES):
        modality = ClaimModality.INSTRUCTION
    elif any(_contains_phrase(folded, marker) for marker in _OPINION_MARKERS):
        modality = ClaimModality.OPINION
    elif uncertainties:
        modality = ClaimModality.HYPOTHESIS
    else:
        modality = ClaimModality.OBSERVATION
    return modality, qualifiers, uncertainties, conditions


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) is not None


def _extract_conditions(text: str, folded: str) -> tuple[str, ...]:
    if not folded.startswith(_CONDITION_PREFIXES):
        return ()
    comma_index = text.find(",")
    if 0 < comma_index <= 160:
        return (text[:comma_index].strip(),)

    modal_pattern = "|".join(re.escape(word) for word in _MODAL_WORDS)
    subject_match = re.search(
        rf"\s([A-ZА-ЯЁ][\w-]*)\s+(?:{modal_pattern})\b",
        text,
        flags=re.UNICODE,
    )
    if subject_match is not None:
        condition = text[: subject_match.start(1)].strip()
        if condition:
            return (condition,)
    return (text.strip(),)


def _build_essence(claim_texts: Iterator[str], max_chars: int) -> tuple[str, bool]:
    """Build an essence from complete claims only.

    Returns the retained essence and whether at least one complete claim was omitted
    because it did not fit the configured character budget.
    """

    parts: list[str] = []
    current_length = 0
    budget_exhausted = False
    for text in claim_texts:
        separator = 1 if parts else 0
        if current_length + separator + len(text) > max_chars:
            budget_exhausted = True
            break
        parts.append(text)
        current_length += separator + len(text)
    return " ".join(parts), budget_exhausted


__all__ = ["ExtractiveReader"]
