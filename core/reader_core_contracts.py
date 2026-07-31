"""Immutable proposal-only contracts for Reader Core PR-RDR-00.

These values describe derived, rebuildable reading artifacts. They do not grant
Canon, memory, tool, policy, TruthGate, or Write Gate authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import math
import re
import unicodedata
from typing import Iterable

from core.knowledge_capsule import SourceSpan

READER_CORE_SCHEMA_VERSION = "reader-core.contracts.v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ReaderCoreContractError(ValueError):
    """Raised when a Reader Core contract invariant is violated."""


class ContentKind(str, Enum):
    TEXT = "text"
    HEADING = "heading"
    TABLE = "table"
    FIGURE = "figure"
    CAPTION = "caption"
    FOOTNOTE = "footnote"
    APPENDIX = "appendix"
    CODE = "code"
    UNKNOWN = "unknown"


class CoverageAxis(str, Enum):
    STRUCTURAL = "structural"
    CLAIM = "claim"
    EXCEPTION = "exception"
    RELATION = "relation"
    TABLE_FIGURE = "table_figure"
    VALIDATION = "validation"


class SessionState(str, Enum):
    CREATED = "created"
    STRUCTURING = "structuring"
    READING = "reading"
    PAUSED = "paused"
    DEGRADED = "degraded"
    COMPLETED = "completed"
    FAILED = "failed"
    STALE = "stale"
    CANCELLED = "cancelled"


class RelationKind(str, Enum):
    SUPPORTS = "supports"
    REFINES = "refines"
    LIMITS = "limits"
    EXEMPLIFIES = "exemplifies"
    DEPENDS_ON = "depends_on"
    CONTRADICTS = "contradicts"
    SUPERSEDES = "supersedes"
    EXCEPTION_TO = "exception_to"
    DEFINES_TERM_USED_BY = "defines_term_used_by"


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderCoreContractError(f"{field_name} must be a non-empty string")
    return value


def _tuple_of_text(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    return result


def _probability(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReaderCoreContractError(f"{field_name} must be a number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ReaderCoreContractError(f"{field_name} must be finite and in [0, 1]")
    return result


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def stable_reader_core_id(kind: str, payload: object) -> str:
    """Return deterministic SHA-256 identity over canonical UTF-8 JSON."""

    _require_text(kind, "kind")
    canonical = _canonical_json({"kind": kind, "payload": payload})
    return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class DocumentSection:
    section_id: str
    document_id: str
    source_revision: str
    order_index: int
    heading: str
    level: int
    start_offset: int
    end_offset: int
    content_kind: ContentKind = ContentKind.TEXT
    parent_section_id: str | None = None
    previous_section_id: str | None = None
    next_section_id: str | None = None
    parser_warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.section_id, "section_id")
        _require_text(self.document_id, "document_id")
        _require_text(self.source_revision, "source_revision")
        _require_text(self.heading, "heading")
        if isinstance(self.order_index, bool) or not isinstance(self.order_index, int) or self.order_index < 0:
            raise ReaderCoreContractError("order_index must be an integer >= 0")
        if isinstance(self.level, bool) or not isinstance(self.level, int) or self.level < 0:
            raise ReaderCoreContractError("level must be an integer >= 0")
        if (
            isinstance(self.start_offset, bool)
            or not isinstance(self.start_offset, int)
            or isinstance(self.end_offset, bool)
            or not isinstance(self.end_offset, int)
            or self.start_offset < 0
            or self.end_offset <= self.start_offset
        ):
            raise ReaderCoreContractError("section must satisfy 0 <= start_offset < end_offset")
        if not isinstance(self.content_kind, ContentKind):
            raise ReaderCoreContractError("content_kind must be a ContentKind")
        for field_name in ("parent_section_id", "previous_section_id", "next_section_id"):
            value = getattr(self, field_name)
            if value is not None:
                _require_text(value, field_name)
        object.__setattr__(self, "parser_warnings", _tuple_of_text(self.parser_warnings, "parser_warning"))

    @classmethod
    def create(cls, **kwargs: object) -> DocumentSection:
        payload = {
            "document_id": kwargs["document_id"],
            "source_revision": kwargs["source_revision"],
            "order_index": kwargs["order_index"],
            "heading": _normalize(str(kwargs["heading"])),
            "level": kwargs["level"],
            "start_offset": kwargs["start_offset"],
            "end_offset": kwargs["end_offset"],
            "content_kind": (
                kwargs.get("content_kind", ContentKind.TEXT).value
                if isinstance(kwargs.get("content_kind", ContentKind.TEXT), ContentKind)
                else kwargs.get("content_kind")
            ),
        }
        return cls(section_id=stable_reader_core_id("document-section", payload), **kwargs)


@dataclass(frozen=True, slots=True)
class DocumentStructureMap:
    map_id: str
    schema_version: str
    document_id: str
    source_revision: str
    parser_id: str
    parser_version: str
    content_hash: str
    sections: tuple[DocumentSection, ...]
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("map_id", "schema_version", "document_id", "source_revision", "parser_id", "parser_version"):
            _require_text(getattr(self, name), name)
        if not isinstance(self.content_hash, str) or not _SHA256_RE.fullmatch(self.content_hash):
            raise ReaderCoreContractError("content_hash must be lowercase SHA-256 hex")
        sections = tuple(self.sections)
        if not sections or any(not isinstance(section, DocumentSection) for section in sections):
            raise ReaderCoreContractError("sections must contain at least one DocumentSection")
        if len({section.section_id for section in sections}) != len(sections):
            raise ReaderCoreContractError("section_id values must be unique")
        if [section.order_index for section in sections] != sorted(section.order_index for section in sections):
            raise ReaderCoreContractError("sections must be ordered by order_index")
        for section in sections:
            if section.document_id != self.document_id or section.source_revision != self.source_revision:
                raise ReaderCoreContractError("all sections must match document_id and source_revision")
        object.__setattr__(self, "sections", sections)
        object.__setattr__(self, "warnings", _tuple_of_text(self.warnings, "warning"))


@dataclass(frozen=True, slots=True)
class CoverageValue:
    axis: CoverageAxis
    processed_units: int
    known_units: int
    unresolved_unit_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.axis, CoverageAxis):
            raise ReaderCoreContractError("axis must be a CoverageAxis")
        for name in ("processed_units", "known_units"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ReaderCoreContractError(f"{name} must be an integer >= 0")
        if self.processed_units > self.known_units:
            raise ReaderCoreContractError("processed_units cannot exceed known_units")
        object.__setattr__(self, "unresolved_unit_ids", _tuple_of_text(self.unresolved_unit_ids, "unresolved_unit_id"))

    @property
    def ratio(self) -> float | None:
        return None if self.known_units == 0 else self.processed_units / self.known_units


@dataclass(frozen=True, slots=True)
class SectionRelationCandidate:
    relation_id: str
    kind: RelationKind
    source_claim_refs: tuple[str, ...]
    target_claim_refs: tuple[str, ...]
    source_spans: tuple[SourceSpan, ...]
    reason_code: str
    extraction_confidence: float

    def __post_init__(self) -> None:
        _require_text(self.relation_id, "relation_id")
        if not isinstance(self.kind, RelationKind):
            raise ReaderCoreContractError("kind must be a RelationKind")
        object.__setattr__(self, "source_claim_refs", _tuple_of_text(self.source_claim_refs, "source_claim_ref"))
        object.__setattr__(self, "target_claim_refs", _tuple_of_text(self.target_claim_refs, "target_claim_ref"))
        if not self.source_claim_refs or not self.target_claim_refs:
            raise ReaderCoreContractError("relations require source and target claim refs")
        spans = tuple(self.source_spans)
        if not spans or any(not isinstance(span, SourceSpan) for span in spans):
            raise ReaderCoreContractError("relations require at least one SourceSpan")
        object.__setattr__(self, "source_spans", spans)
        _require_text(self.reason_code, "reason_code")
        object.__setattr__(self, "extraction_confidence", _probability(self.extraction_confidence, "extraction_confidence"))


@dataclass(frozen=True, slots=True)
class ReadingSessionCheckpoint:
    session_id: str
    document_id: str
    source_revision: str
    state: SessionState
    completed_section_ids: tuple[str, ...] = ()
    pending_section_ids: tuple[str, ...] = ()
    receipt_ids: tuple[str, ...] = ()
    policy_version: str | None = None

    def __post_init__(self) -> None:
        for name in ("session_id", "document_id", "source_revision"):
            _require_text(getattr(self, name), name)
        if not isinstance(self.state, SessionState):
            raise ReaderCoreContractError("state must be a SessionState")
        completed = _tuple_of_text(self.completed_section_ids, "completed_section_id")
        pending = _tuple_of_text(self.pending_section_ids, "pending_section_id")
        if set(completed) & set(pending):
            raise ReaderCoreContractError("completed and pending section IDs must be disjoint")
        object.__setattr__(self, "completed_section_ids", completed)
        object.__setattr__(self, "pending_section_ids", pending)
        object.__setattr__(self, "receipt_ids", _tuple_of_text(self.receipt_ids, "receipt_id"))
        if self.policy_version is not None:
            _require_text(self.policy_version, "policy_version")


__all__ = [
    "ContentKind",
    "CoverageAxis",
    "CoverageValue",
    "DocumentSection",
    "DocumentStructureMap",
    "READER_CORE_SCHEMA_VERSION",
    "ReaderCoreContractError",
    "ReadingSessionCheckpoint",
    "RelationKind",
    "SectionRelationCandidate",
    "SessionState",
    "stable_reader_core_id",
]
