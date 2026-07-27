"""Immutable, source-linked semantic capsule contracts.

This module implements the first executable slice of the Synaptic Exo-Cortex
profile.  A capsule is an extraction proposal with exact provenance; it is not
Canon and it grants no write authority.

Offsets are Python string (Unicode code-point) offsets, not byte offsets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
import json
import math
import re
from typing import Iterable
import unicodedata

SCHEMA_VERSION = "synaptic.knowledge-capsule.v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CapsuleValidationError(ValueError):
    """Raised when a capsule contract invariant is violated."""


class ClaimModality(str, Enum):
    """Epistemic role of text extracted from a source."""

    OBSERVATION = "observation"
    WORLD_FACT = "world_fact"
    USER_REPORT = "user_report"
    OPINION = "opinion"
    HYPOTHESIS = "hypothesis"
    INTERPRETATION = "interpretation"
    INSTRUCTION = "instruction"
    GOAL = "goal"


def _require_non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CapsuleValidationError(f"{field_name} must be a non-empty string")
    return value


def _validate_probability(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CapsuleValidationError(f"{field_name} must be a number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise CapsuleValidationError(f"{field_name} must be finite and in [0, 1]")
    return result


def _normalize_text(value: str) -> str:
    """Return a deterministic representation for content identity only."""

    return " ".join(unicodedata.normalize("NFC", value).split())


def _string_tuple(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_non_empty(value, field_name)
    return result


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """Exact character range inside one immutable source revision."""

    span_id: str
    document_id: str
    start_offset: int
    end_offset: int
    content_hash: str
    source_revision: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.span_id, "span_id")
        _require_non_empty(self.document_id, "document_id")
        if self.source_revision is not None:
            _require_non_empty(self.source_revision, "source_revision")
        if isinstance(self.start_offset, bool) or not isinstance(self.start_offset, int):
            raise CapsuleValidationError("start_offset must be an integer")
        if isinstance(self.end_offset, bool) or not isinstance(self.end_offset, int):
            raise CapsuleValidationError("end_offset must be an integer")
        if self.start_offset < 0 or self.end_offset <= self.start_offset:
            raise CapsuleValidationError(
                "source span must satisfy 0 <= start_offset < end_offset"
            )
        if not isinstance(self.content_hash, str) or not _SHA256_RE.fullmatch(
            self.content_hash
        ):
            raise CapsuleValidationError("content_hash must be a lowercase SHA-256 hex digest")

    @classmethod
    def from_text(
        cls,
        *,
        document_id: str,
        raw_text: str,
        start_offset: int,
        end_offset: int,
        source_revision: str | None = None,
        span_id: str | None = None,
    ) -> SourceSpan:
        """Build a span and derive both its hash and stable identifier."""

        _require_non_empty(document_id, "document_id")
        if not isinstance(raw_text, str):
            raise CapsuleValidationError("raw_text must be a string")
        if (
            isinstance(start_offset, bool)
            or not isinstance(start_offset, int)
            or isinstance(end_offset, bool)
            or not isinstance(end_offset, int)
            or start_offset < 0
            or end_offset <= start_offset
            or end_offset > len(raw_text)
        ):
            raise CapsuleValidationError(
                "source span must satisfy 0 <= start_offset < end_offset <= len(raw_text)"
            )
        if source_revision is not None:
            _require_non_empty(source_revision, "source_revision")

        content_hash = sha256(raw_text[start_offset:end_offset].encode("utf-8")).hexdigest()
        resolved_span_id = span_id or _stable_digest(
            {
                "document_id": document_id,
                "source_revision": source_revision,
                "start_offset": start_offset,
                "end_offset": end_offset,
                "content_hash": content_hash,
            }
        )
        return cls(
            span_id=resolved_span_id,
            document_id=document_id,
            start_offset=start_offset,
            end_offset=end_offset,
            content_hash=content_hash,
            source_revision=source_revision,
        )

    def verify(self, raw_text: str) -> bool:
        """Verify bounds and content hash against the supplied source revision."""

        if not isinstance(raw_text, str) or self.end_offset > len(raw_text):
            return False
        content = raw_text[self.start_offset : self.end_offset]
        return sha256(content.encode("utf-8")).hexdigest() == self.content_hash

    def identity_payload(self) -> dict[str, object]:
        """Canonical data used by parent content identities."""

        return {
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True, slots=True)
class CapsuleClaim:
    """One source-linked extraction proposal.

    ``extraction_confidence`` describes fidelity to the source.  It is distinct
    from ``truth_confidence``, which describes external evidential support.
    """

    claim_id: str
    text: str
    modality: ClaimModality
    source_spans: tuple[SourceSpan, ...]
    extraction_confidence: float
    truth_confidence: float | None = None
    qualifiers: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()
    applicability_conditions: tuple[str, ...] = ()
    temporal_scope: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.claim_id, "claim_id")
        _require_non_empty(self.text, "text")
        if not isinstance(self.modality, ClaimModality):
            raise CapsuleValidationError("modality must be a ClaimModality")

        spans = tuple(self.source_spans)
        if not spans or any(not isinstance(span, SourceSpan) for span in spans):
            raise CapsuleValidationError("every claim must contain at least one SourceSpan")
        object.__setattr__(self, "source_spans", spans)

        object.__setattr__(
            self,
            "extraction_confidence",
            _validate_probability(self.extraction_confidence, "extraction_confidence"),
        )
        if self.truth_confidence is not None:
            truth_confidence = _validate_probability(
                self.truth_confidence, "truth_confidence"
            )
            if self.modality is ClaimModality.HYPOTHESIS and truth_confidence == 1.0:
                raise CapsuleValidationError(
                    "a hypothesis cannot be created with truth_confidence=1.0"
                )
            object.__setattr__(self, "truth_confidence", truth_confidence)

        object.__setattr__(self, "qualifiers", _string_tuple(self.qualifiers, "qualifier"))
        object.__setattr__(
            self, "uncertainties", _string_tuple(self.uncertainties, "uncertainty")
        )
        object.__setattr__(
            self,
            "applicability_conditions",
            _string_tuple(self.applicability_conditions, "applicability_condition"),
        )
        if self.temporal_scope is not None:
            _require_non_empty(self.temporal_scope, "temporal_scope")

    @classmethod
    def create(
        cls,
        *,
        text: str,
        modality: ClaimModality,
        source_spans: Iterable[SourceSpan],
        extraction_confidence: float,
        truth_confidence: float | None = None,
        qualifiers: Iterable[str] = (),
        uncertainties: Iterable[str] = (),
        applicability_conditions: Iterable[str] = (),
        temporal_scope: str | None = None,
        claim_id: str | None = None,
    ) -> CapsuleClaim:
        """Create a claim with a deterministic default identifier."""

        spans = tuple(source_spans)
        qualifiers_tuple = tuple(qualifiers)
        uncertainties_tuple = tuple(uncertainties)
        conditions_tuple = tuple(applicability_conditions)
        extraction_value = _validate_probability(
            extraction_confidence, "extraction_confidence"
        )
        truth_value = (
            _validate_probability(truth_confidence, "truth_confidence")
            if truth_confidence is not None
            else None
        )
        resolved_claim_id = claim_id or _stable_digest(
            {
                "text": _normalize_text(text),
                "modality": modality.value if isinstance(modality, ClaimModality) else modality,
                "source_spans": sorted(
                    (span.identity_payload() for span in spans),
                    key=_canonical_json,
                ),
                "qualifiers": sorted(_normalize_text(item) for item in qualifiers_tuple),
                "uncertainties": sorted(_normalize_text(item) for item in uncertainties_tuple),
                "applicability_conditions": sorted(
                    _normalize_text(item) for item in conditions_tuple
                ),
                "temporal_scope": (
                    _normalize_text(temporal_scope) if temporal_scope is not None else None
                ),
                "extraction_confidence": extraction_value,
                "truth_confidence": truth_value,
            }
        )
        return cls(
            claim_id=resolved_claim_id,
            text=text,
            modality=modality,
            source_spans=spans,
            extraction_confidence=extraction_value,
            truth_confidence=truth_value,
            qualifiers=qualifiers_tuple,
            uncertainties=uncertainties_tuple,
            applicability_conditions=conditions_tuple,
            temporal_scope=temporal_scope,
        )

    def identity_payload(self) -> dict[str, object]:
        """Canonical semantic and provenance payload, excluding claim_id."""

        return {
            "text": _normalize_text(self.text),
            "modality": self.modality.value,
            "source_spans": sorted(
                (span.identity_payload() for span in self.source_spans), key=_canonical_json
            ),
            "extraction_confidence": self.extraction_confidence,
            "truth_confidence": self.truth_confidence,
            "qualifiers": sorted(_normalize_text(item) for item in self.qualifiers),
            "uncertainties": sorted(_normalize_text(item) for item in self.uncertainties),
            "applicability_conditions": sorted(
                _normalize_text(item) for item in self.applicability_conditions
            ),
            "temporal_scope": (
                _normalize_text(self.temporal_scope) if self.temporal_scope is not None else None
            ),
        }


@dataclass(frozen=True, slots=True)
class KnowledgeCapsule:
    """Immutable source-linked extraction proposal.

    ``capsule_id`` is a semantic/provenance identity.  It excludes timestamps,
    caller-supplied claim IDs, Reader metadata, and quality metrics so identical
    extracted meaning deduplicates across replaceable Reader providers.
    """

    capsule_id: str
    schema_version: str
    source_document_id: str
    essence: str
    claims: tuple[CapsuleClaim, ...]
    entities: tuple[str, ...]
    omitted_questions: tuple[str, ...]
    coverage_score: float
    compression_ratio: float
    reader_id: str
    reader_version: str
    prompt_version: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        _require_non_empty(self.capsule_id, "capsule_id")
        _require_non_empty(self.schema_version, "schema_version")
        _require_non_empty(self.source_document_id, "source_document_id")
        _require_non_empty(self.essence, "essence")
        _require_non_empty(self.reader_id, "reader_id")
        _require_non_empty(self.reader_version, "reader_version")
        if self.prompt_version is not None:
            _require_non_empty(self.prompt_version, "prompt_version")

        claims = tuple(self.claims)
        if not claims or any(not isinstance(claim, CapsuleClaim) for claim in claims):
            raise CapsuleValidationError("a capsule must contain at least one CapsuleClaim")
        for claim in claims:
            for span in claim.source_spans:
                if span.document_id != self.source_document_id:
                    raise CapsuleValidationError(
                        "all claim source spans must match source_document_id"
                    )
        object.__setattr__(self, "claims", claims)
        object.__setattr__(self, "entities", _string_tuple(self.entities, "entity"))
        object.__setattr__(
            self,
            "omitted_questions",
            _string_tuple(self.omitted_questions, "omitted_question"),
        )
        object.__setattr__(
            self,
            "coverage_score",
            _validate_probability(self.coverage_score, "coverage_score"),
        )

        if isinstance(self.compression_ratio, bool) or not isinstance(
            self.compression_ratio, (int, float)
        ):
            raise CapsuleValidationError("compression_ratio must be a finite number >= 0")
        compression_ratio = float(self.compression_ratio)
        if not math.isfinite(compression_ratio) or compression_ratio < 0.0:
            raise CapsuleValidationError("compression_ratio must be a finite number >= 0")
        object.__setattr__(self, "compression_ratio", compression_ratio)

        if not isinstance(self.created_at, datetime) or self.created_at.tzinfo is None:
            raise CapsuleValidationError("created_at must be a timezone-aware datetime")

        expected_id = self.compute_content_id(
            schema_version=self.schema_version,
            source_document_id=self.source_document_id,
            essence=self.essence,
            claims=claims,
            entities=self.entities,
            omitted_questions=self.omitted_questions,
        )
        if self.capsule_id != expected_id:
            raise CapsuleValidationError("capsule_id does not match capsule content")

    @classmethod
    def create(
        cls,
        *,
        source_document_id: str,
        essence: str,
        claims: Iterable[CapsuleClaim],
        reader_id: str,
        reader_version: str,
        entities: Iterable[str] = (),
        omitted_questions: Iterable[str] = (),
        coverage_score: float = 0.0,
        compression_ratio: float = 0.0,
        prompt_version: str | None = None,
        schema_version: str = SCHEMA_VERSION,
        created_at: datetime | None = None,
    ) -> KnowledgeCapsule:
        """Create a validated capsule with deterministic content identity."""

        claims_tuple = tuple(claims)
        entities_tuple = tuple(entities)
        omitted_questions_tuple = tuple(omitted_questions)
        capsule_id = cls.compute_content_id(
            schema_version=schema_version,
            source_document_id=source_document_id,
            essence=essence,
            claims=claims_tuple,
            entities=entities_tuple,
            omitted_questions=omitted_questions_tuple,
        )
        return cls(
            capsule_id=capsule_id,
            schema_version=schema_version,
            source_document_id=source_document_id,
            essence=essence,
            claims=claims_tuple,
            entities=entities_tuple,
            omitted_questions=omitted_questions_tuple,
            coverage_score=coverage_score,
            compression_ratio=compression_ratio,
            reader_id=reader_id,
            reader_version=reader_version,
            prompt_version=prompt_version,
            created_at=created_at or datetime.now(UTC),
        )

    @staticmethod
    def compute_content_id(
        *,
        schema_version: str,
        source_document_id: str,
        essence: str,
        claims: Iterable[CapsuleClaim],
        entities: Iterable[str],
        omitted_questions: Iterable[str],
    ) -> str:
        """Compute the canonical content identity for a capsule."""

        claims_tuple = tuple(claims)
        return _stable_digest(
            {
                "schema_version": schema_version,
                "source_document_id": source_document_id,
                "essence": _normalize_text(essence),
                "claims": sorted(
                    (claim.identity_payload() for claim in claims_tuple), key=_canonical_json
                ),
                "entities": sorted(_normalize_text(item) for item in entities),
                "omitted_questions": sorted(
                    _normalize_text(item) for item in omitted_questions
                ),
            }
        )


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _stable_digest(payload: object) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


__all__ = [
    "SCHEMA_VERSION",
    "CapsuleClaim",
    "CapsuleValidationError",
    "ClaimModality",
    "KnowledgeCapsule",
    "SourceSpan",
]
