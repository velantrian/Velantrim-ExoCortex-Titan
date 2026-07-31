"""Deterministic critical-exception signals for Reader Core PR-RDR-04.

The scanner locates source-linked linguistic signals such as ``unless`` and
``does not apply to`` inside validated SectionCards. A match is only an
unvalidated interpretation candidate. It grants no truth, Canon, memory,
policy, tool, TruthGate, or Write Gate authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Iterable

from core.knowledge_capsule import SourceSpan
from core.reader_core_contracts import stable_reader_core_id
from core.section_card import SectionCard
from core.semantic_reader import RawSource

CRITICAL_EXCEPTION_SCHEMA_VERSION = "reader-core.critical-exception.v1"


class CriticalExceptionError(ValueError):
    """Raised when an exception candidate or scan violates its contract."""


class ExceptionCategory(str, Enum):
    """Conservative category assigned from an exact deterministic signal."""

    CONDITION = "condition"
    EXCLUSION = "exclusion"
    CONTRAST = "contrast"
    SCOPE_LIMITATION = "scope_limitation"
    SUPERSESSION = "supersession"
    VERSION_LIMITATION = "version_limitation"
    APPROVAL_REQUIREMENT = "approval_requirement"


class ExceptionValidationStatus(str, Enum):
    """Human or later-validator status; the scanner emits only UNVALIDATED."""

    UNVALIDATED = "unvalidated"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class CriticalExceptionCandidate:
    """One exact source-linked signal that may limit or qualify a claim."""

    candidate_id: str
    schema_version: str
    scanner_version: str
    document_id: str
    source_revision: str
    card_id: str
    unit_id: str
    section_id: str
    category: ExceptionCategory
    trigger_phrase: str
    trigger_span: SourceSpan
    statement_span: SourceSpan
    statement_text: str
    target_claim_refs: tuple[str, ...]
    validation_status: ExceptionValidationStatus = (
        ExceptionValidationStatus.UNVALIDATED
    )
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "candidate_id",
            "schema_version",
            "scanner_version",
            "document_id",
            "source_revision",
            "card_id",
            "unit_id",
            "section_id",
            "trigger_phrase",
            "statement_text",
        ):
            _require_text(getattr(self, name), name)
        if self.schema_version != CRITICAL_EXCEPTION_SCHEMA_VERSION:
            raise CriticalExceptionError(
                "unsupported CriticalExceptionCandidate schema_version"
            )
        if not isinstance(self.category, ExceptionCategory):
            raise CriticalExceptionError("category must be an ExceptionCategory")
        if not isinstance(self.validation_status, ExceptionValidationStatus):
            raise CriticalExceptionError(
                "validation_status must be an ExceptionValidationStatus"
            )
        if not isinstance(self.trigger_span, SourceSpan):
            raise CriticalExceptionError("trigger_span must be a SourceSpan")
        if not isinstance(self.statement_span, SourceSpan):
            raise CriticalExceptionError("statement_span must be a SourceSpan")
        self._validate_span(self.trigger_span, "trigger_span")
        self._validate_span(self.statement_span, "statement_span")
        if (
            self.trigger_span.start_offset < self.statement_span.start_offset
            or self.trigger_span.end_offset > self.statement_span.end_offset
        ):
            raise CriticalExceptionError(
                "trigger_span must be contained in statement_span"
            )
        target_refs = _unique_text_tuple(
            self.target_claim_refs,
            "target_claim_ref",
        )
        warnings = _unique_text_tuple(self.warnings, "warning")
        object.__setattr__(self, "target_claim_refs", target_refs)
        object.__setattr__(self, "warnings", warnings)
        if not target_refs and "unresolved_target_claim" not in warnings:
            raise CriticalExceptionError(
                "candidate without target claims must declare unresolved_target_claim"
            )
        expected_id = _candidate_identity(
            schema_version=self.schema_version,
            scanner_version=self.scanner_version,
            document_id=self.document_id,
            source_revision=self.source_revision,
            card_id=self.card_id,
            unit_id=self.unit_id,
            section_id=self.section_id,
            category=self.category,
            trigger_phrase=self.trigger_phrase,
            trigger_span=self.trigger_span,
            statement_span=self.statement_span,
            statement_text=self.statement_text,
            target_claim_refs=target_refs,
            validation_status=self.validation_status,
            warnings=warnings,
        )
        if self.candidate_id != expected_id:
            raise CriticalExceptionError(
                "candidate_id does not match candidate content"
            )

    def _validate_span(self, span: SourceSpan, field_name: str) -> None:
        if span.document_id != self.document_id:
            raise CriticalExceptionError(
                f"{field_name} document_id must match candidate"
            )
        if span.source_revision != self.source_revision:
            raise CriticalExceptionError(
                f"{field_name} source_revision must match candidate"
            )


@dataclass(frozen=True, slots=True)
class ExceptionScanReceipt:
    """Observable record that one complete SectionCard unit was scanned."""

    receipt_id: str
    scanner_version: str
    document_id: str
    source_revision: str
    card_id: str
    unit_id: str
    scanned_span: SourceSpan
    trigger_match_count: int
    candidate_ids: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "scanner_version",
            "document_id",
            "source_revision",
            "card_id",
            "unit_id",
        ):
            _require_text(getattr(self, name), name)
        if not isinstance(self.scanned_span, SourceSpan):
            raise CriticalExceptionError("scanned_span must be a SourceSpan")
        if self.scanned_span.document_id != self.document_id:
            raise CriticalExceptionError(
                "scanned_span document_id must match receipt"
            )
        if self.scanned_span.source_revision != self.source_revision:
            raise CriticalExceptionError(
                "scanned_span source_revision must match receipt"
            )
        if self.scanned_span.span_id != self.unit_id:
            raise CriticalExceptionError(
                "scanned_span span_id must equal unit_id"
            )
        if (
            isinstance(self.trigger_match_count, bool)
            or not isinstance(self.trigger_match_count, int)
            or self.trigger_match_count < 0
        ):
            raise CriticalExceptionError(
                "trigger_match_count must be an integer >= 0"
            )
        candidate_ids = _unique_text_tuple(self.candidate_ids, "candidate_id")
        warnings = _unique_text_tuple(self.warnings, "warning")
        if self.trigger_match_count != len(candidate_ids):
            raise CriticalExceptionError(
                "trigger_match_count must equal candidate_ids length"
            )
        object.__setattr__(self, "candidate_ids", candidate_ids)
        object.__setattr__(self, "warnings", warnings)
        expected_id = _scan_receipt_identity(
            scanner_version=self.scanner_version,
            document_id=self.document_id,
            source_revision=self.source_revision,
            card_id=self.card_id,
            unit_id=self.unit_id,
            scanned_span=self.scanned_span,
            candidate_ids=candidate_ids,
            warnings=warnings,
        )
        if self.receipt_id != expected_id:
            raise CriticalExceptionError(
                "receipt_id does not match scan receipt content"
            )


@dataclass(frozen=True, slots=True)
class ExceptionScanResult:
    """Candidates and the receipt proving which card unit was scanned."""

    candidates: tuple[CriticalExceptionCandidate, ...]
    receipt: ExceptionScanReceipt

    def __post_init__(self) -> None:
        candidates = tuple(self.candidates)
        if any(
            not isinstance(candidate, CriticalExceptionCandidate)
            for candidate in candidates
        ):
            raise CriticalExceptionError(
                "candidates must contain CriticalExceptionCandidate values"
            )
        if not isinstance(self.receipt, ExceptionScanReceipt):
            raise CriticalExceptionError(
                "receipt must be an ExceptionScanReceipt"
            )
        candidate_ids = tuple(candidate.candidate_id for candidate in candidates)
        if candidate_ids != self.receipt.candidate_ids:
            raise CriticalExceptionError(
                "receipt candidate_ids must match scan candidates"
            )
        for candidate in candidates:
            if (
                candidate.document_id != self.receipt.document_id
                or candidate.source_revision != self.receipt.source_revision
                or candidate.card_id != self.receipt.card_id
                or candidate.unit_id != self.receipt.unit_id
            ):
                raise CriticalExceptionError(
                    "every candidate must match its scan receipt"
                )
        object.__setattr__(self, "candidates", candidates)


@dataclass(frozen=True, slots=True)
class _SignalRule:
    pattern: re.Pattern[str]
    category: ExceptionCategory


@dataclass(frozen=True, slots=True)
class _SignalMatch:
    start_offset: int
    end_offset: int
    category: ExceptionCategory


_SIGNAL_RULES = (
    _SignalRule(
        re.compile(r"\brequires?\s+manual\s+approval\b", re.IGNORECASE),
        ExceptionCategory.APPROVAL_REQUIREMENT,
    ),
    _SignalRule(
        re.compile(r"\bdoes\s+not\s+apply\s+to\b", re.IGNORECASE),
        ExceptionCategory.EXCLUSION,
    ),
    _SignalRule(
        re.compile(r"\b(?:is|are|was|were)\s+invalid\s+for\s+versions?\b", re.IGNORECASE),
        ExceptionCategory.VERSION_LIMITATION,
    ),
    _SignalRule(
        re.compile(r"\bsuperseded\s+by\b", re.IGNORECASE),
        ExceptionCategory.SUPERSESSION,
    ),
    _SignalRule(
        re.compile(r"\bsubject\s+to\b", re.IGNORECASE),
        ExceptionCategory.SCOPE_LIMITATION,
    ),
    _SignalRule(
        re.compile(r"\bprovided\s+that\b", re.IGNORECASE),
        ExceptionCategory.CONDITION,
    ),
    _SignalRule(
        re.compile(r"\bonly\s+if\b", re.IGNORECASE),
        ExceptionCategory.CONDITION,
    ),
    _SignalRule(
        re.compile(r"\bunless\b", re.IGNORECASE),
        ExceptionCategory.CONDITION,
    ),
    _SignalRule(
        re.compile(r"\bexcept(?:\s+for)?\b", re.IGNORECASE),
        ExceptionCategory.EXCLUSION,
    ),
    _SignalRule(
        re.compile(r"\bbut\s+not\b", re.IGNORECASE),
        ExceptionCategory.EXCLUSION,
    ),
    _SignalRule(
        re.compile(r"\bhowever\b", re.IGNORECASE),
        ExceptionCategory.CONTRAST,
    ),
)


class DeterministicCriticalExceptionScanner:
    """Scan validated SectionCard units for conservative exception signals."""

    scanner_version = "1.0.0"

    def __init__(self, *, target_claim_window_chars: int = 500) -> None:
        if (
            isinstance(target_claim_window_chars, bool)
            or not isinstance(target_claim_window_chars, int)
            or target_claim_window_chars < 0
        ):
            raise CriticalExceptionError(
                "target_claim_window_chars must be an integer >= 0"
            )
        self._target_claim_window_chars = target_claim_window_chars

    def scan(self, source: RawSource, card: SectionCard) -> ExceptionScanResult:
        """Return unvalidated candidates for one exact source-linked card unit."""

        self._validate_source_and_card(source, card)
        unit_start = card.unit_source_span.start_offset
        unit_end = card.unit_source_span.end_offset
        unit_text = source.text[unit_start:unit_end]
        matches = self._signal_matches(unit_text, base_offset=unit_start)

        candidates: list[CriticalExceptionCandidate] = []
        for signal in matches:
            statement_start, statement_end = _statement_bounds(
                source.text,
                signal.start_offset,
                signal.end_offset,
                lower_bound=unit_start,
                upper_bound=unit_end,
            )
            trigger_span = SourceSpan.from_text(
                document_id=card.document_id,
                raw_text=source.text,
                start_offset=signal.start_offset,
                end_offset=signal.end_offset,
                source_revision=card.source_revision,
            )
            statement_span = SourceSpan.from_text(
                document_id=card.document_id,
                raw_text=source.text,
                start_offset=statement_start,
                end_offset=statement_end,
                source_revision=card.source_revision,
            )
            target_claim_refs = self._target_claim_refs(
                card,
                statement_start=statement_start,
                statement_end=statement_end,
            )
            warnings: tuple[str, ...] = ()
            if not target_claim_refs:
                warnings = ("unresolved_target_claim",)
            trigger_phrase = source.text[signal.start_offset:signal.end_offset]
            statement_text = source.text[statement_start:statement_end]
            candidate_id = _candidate_identity(
                schema_version=CRITICAL_EXCEPTION_SCHEMA_VERSION,
                scanner_version=self.scanner_version,
                document_id=card.document_id,
                source_revision=card.source_revision,
                card_id=card.card_id,
                unit_id=card.unit_id,
                section_id=card.section_id,
                category=signal.category,
                trigger_phrase=trigger_phrase,
                trigger_span=trigger_span,
                statement_span=statement_span,
                statement_text=statement_text,
                target_claim_refs=target_claim_refs,
                validation_status=ExceptionValidationStatus.UNVALIDATED,
                warnings=warnings,
            )
            candidates.append(
                CriticalExceptionCandidate(
                    candidate_id=candidate_id,
                    schema_version=CRITICAL_EXCEPTION_SCHEMA_VERSION,
                    scanner_version=self.scanner_version,
                    document_id=card.document_id,
                    source_revision=card.source_revision,
                    card_id=card.card_id,
                    unit_id=card.unit_id,
                    section_id=card.section_id,
                    category=signal.category,
                    trigger_phrase=trigger_phrase,
                    trigger_span=trigger_span,
                    statement_span=statement_span,
                    statement_text=statement_text,
                    target_claim_refs=target_claim_refs,
                    warnings=warnings,
                )
            )

        candidate_ids = tuple(candidate.candidate_id for candidate in candidates)
        receipt_id = _scan_receipt_identity(
            scanner_version=self.scanner_version,
            document_id=card.document_id,
            source_revision=card.source_revision,
            card_id=card.card_id,
            unit_id=card.unit_id,
            scanned_span=card.unit_source_span,
            candidate_ids=candidate_ids,
            warnings=(),
        )
        receipt = ExceptionScanReceipt(
            receipt_id=receipt_id,
            scanner_version=self.scanner_version,
            document_id=card.document_id,
            source_revision=card.source_revision,
            card_id=card.card_id,
            unit_id=card.unit_id,
            scanned_span=card.unit_source_span,
            trigger_match_count=len(candidate_ids),
            candidate_ids=candidate_ids,
        )
        return ExceptionScanResult(candidates=tuple(candidates), receipt=receipt)

    @staticmethod
    def _validate_source_and_card(source: RawSource, card: SectionCard) -> None:
        if not isinstance(source, RawSource):
            raise CriticalExceptionError("source must be a RawSource")
        if not isinstance(card, SectionCard):
            raise CriticalExceptionError("card must be a SectionCard")
        if source.document_id != card.document_id:
            raise CriticalExceptionError("source document_id must match card")
        source_revision = source.source_revision
        if source_revision is None:
            from hashlib import sha256

            content_hash = sha256(source.text.encode("utf-8")).hexdigest()
            source_revision = f"sha256:{content_hash}"
        if source_revision != card.source_revision:
            raise CriticalExceptionError("source revision must match card")
        if not card.unit_source_span.verify(source.text):
            raise CriticalExceptionError(
                "card unit_source_span must verify against source"
            )

    @staticmethod
    def _signal_matches(text: str, *, base_offset: int) -> tuple[_SignalMatch, ...]:
        matches: dict[tuple[int, int], _SignalMatch] = {}
        for rule in _SIGNAL_RULES:
            for match in rule.pattern.finditer(text):
                absolute_start = base_offset + match.start()
                absolute_end = base_offset + match.end()
                key = (absolute_start, absolute_end)
                matches.setdefault(
                    key,
                    _SignalMatch(
                        start_offset=absolute_start,
                        end_offset=absolute_end,
                        category=rule.category,
                    ),
                )
        return tuple(
            sorted(
                matches.values(),
                key=lambda item: (item.start_offset, item.end_offset),
            )
        )

    def _target_claim_refs(
        self,
        card: SectionCard,
        *,
        statement_start: int,
        statement_end: int,
    ) -> tuple[str, ...]:
        overlapping: list[str] = []
        preceding: list[tuple[int, str]] = []
        for card_claim in card.claims:
            spans = card_claim.claim.source_spans
            if any(
                span.start_offset < statement_end
                and span.end_offset > statement_start
                for span in spans
            ):
                overlapping.append(card_claim.claim.claim_id)
                continue
            preceding_end = max(span.end_offset for span in spans)
            if preceding_end <= statement_start:
                distance = statement_start - preceding_end
                if distance <= self._target_claim_window_chars:
                    preceding.append((distance, card_claim.claim.claim_id))
        if overlapping:
            return tuple(dict.fromkeys(overlapping))
        if preceding:
            minimum_distance = min(distance for distance, _ in preceding)
            return tuple(
                claim_id
                for distance, claim_id in preceding
                if distance == minimum_distance
            )
        return ()


def _statement_bounds(
    text: str,
    trigger_start: int,
    trigger_end: int,
    *,
    lower_bound: int,
    upper_bound: int,
) -> tuple[int, int]:
    delimiters = ".!?\n"
    left = trigger_start
    while left > lower_bound and text[left - 1] not in delimiters:
        left -= 1
    while left < trigger_start and text[left].isspace():
        left += 1

    right = trigger_end
    while right < upper_bound and text[right] not in delimiters:
        right += 1
    if right < upper_bound and text[right] in ".!?":
        right += 1
    while right > trigger_end and text[right - 1].isspace():
        right -= 1
    if right <= left:
        return trigger_start, trigger_end
    return left, right


def _candidate_identity(
    *,
    schema_version: str,
    scanner_version: str,
    document_id: str,
    source_revision: str,
    card_id: str,
    unit_id: str,
    section_id: str,
    category: ExceptionCategory,
    trigger_phrase: str,
    trigger_span: SourceSpan,
    statement_span: SourceSpan,
    statement_text: str,
    target_claim_refs: tuple[str, ...],
    validation_status: ExceptionValidationStatus,
    warnings: tuple[str, ...],
) -> str:
    return stable_reader_core_id(
        "critical-exception-candidate",
        {
            "schema_version": schema_version,
            "scanner_version": scanner_version,
            "document_id": document_id,
            "source_revision": source_revision,
            "card_id": card_id,
            "unit_id": unit_id,
            "section_id": section_id,
            "category": category.value,
            "trigger_phrase": trigger_phrase,
            "trigger_span": trigger_span.identity_payload(),
            "statement_span": statement_span.identity_payload(),
            "statement_text": statement_text,
            "target_claim_refs": list(target_claim_refs),
            "validation_status": validation_status.value,
            "warnings": list(warnings),
        },
    )


def _scan_receipt_identity(
    *,
    scanner_version: str,
    document_id: str,
    source_revision: str,
    card_id: str,
    unit_id: str,
    scanned_span: SourceSpan,
    candidate_ids: tuple[str, ...],
    warnings: tuple[str, ...],
) -> str:
    return stable_reader_core_id(
        "critical-exception-scan-receipt",
        {
            "scanner_version": scanner_version,
            "document_id": document_id,
            "source_revision": source_revision,
            "card_id": card_id,
            "unit_id": unit_id,
            "scanned_span": scanned_span.identity_payload(),
            "candidate_ids": list(candidate_ids),
            "warnings": list(warnings),
        },
    )


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CriticalExceptionError(f"{field_name} must be a non-empty string")
    return value


def _unique_text_tuple(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    if len(set(result)) != len(result):
        raise CriticalExceptionError(f"{field_name} values must be unique")
    return result


__all__ = [
    "CRITICAL_EXCEPTION_SCHEMA_VERSION",
    "CriticalExceptionCandidate",
    "CriticalExceptionError",
    "DeterministicCriticalExceptionScanner",
    "ExceptionCategory",
    "ExceptionScanReceipt",
    "ExceptionScanResult",
    "ExceptionValidationStatus",
]
