"""Hierarchy-aware bounded reading-unit planning for Reader Core PR-RDR-02.

The planner converts an exact ``DocumentStructureMap`` into source-linked
reading units. It is deterministic, overlap-free, model-free, and has no write
or runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import re
from typing import Iterable

from core.knowledge_capsule import SourceSpan
from core.reader_core_contracts import (
    ContentKind,
    DocumentSection,
    DocumentStructureMap,
    stable_reader_core_id,
)
from core.semantic_reader import RawSource


class SectionPlanningError(ValueError):
    """Raised when a source and structure map cannot be planned safely."""


class UnitBoundaryKind(str, Enum):
    """Reason a reading unit ended at its exact source offset."""

    SECTION_END = "section_end"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"
    LINE = "line"
    HARD_LIMIT = "hard_limit"
    ATOMIC_OVERSIZE = "atomic_oversize"


@dataclass(frozen=True, slots=True)
class SectionPlanningBudget:
    """Deterministic character bounds for reading-unit planning."""

    max_unit_chars: int = 6_000
    min_unit_chars: int = 256
    boundary_search_chars: int = 1_000

    def __post_init__(self) -> None:
        for name in ("max_unit_chars", "min_unit_chars"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise SectionPlanningError(f"{name} must be a positive integer")
        if self.min_unit_chars > self.max_unit_chars:
            raise SectionPlanningError(
                "min_unit_chars cannot exceed max_unit_chars"
            )
        if (
            isinstance(self.boundary_search_chars, bool)
            or not isinstance(self.boundary_search_chars, int)
            or self.boundary_search_chars < 0
        ):
            raise SectionPlanningError(
                "boundary_search_chars must be an integer >= 0"
            )


@dataclass(frozen=True, slots=True)
class ReadingUnit:
    """One immutable source-linked unit scheduled for a SemanticReader."""

    unit_id: str
    document_id: str
    source_revision: str
    structure_map_id: str
    section_id: str
    parent_section_id: str | None
    order_index: int
    section_unit_index: int
    source_span: SourceSpan
    boundary_kind: UnitBoundaryKind
    previous_unit_id: str | None = None
    next_unit_id: str | None = None
    continuation_from_unit_id: str | None = None
    continuation_to_unit_id: str | None = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "unit_id",
            "document_id",
            "source_revision",
            "structure_map_id",
            "section_id",
        ):
            _require_text(getattr(self, name), name)
        for name in (
            "parent_section_id",
            "previous_unit_id",
            "next_unit_id",
            "continuation_from_unit_id",
            "continuation_to_unit_id",
        ):
            value = getattr(self, name)
            if value is not None:
                _require_text(value, name)
        for name in ("order_index", "section_unit_index"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise SectionPlanningError(f"{name} must be an integer >= 0")
        if not isinstance(self.source_span, SourceSpan):
            raise SectionPlanningError("source_span must be a SourceSpan")
        if self.source_span.document_id != self.document_id:
            raise SectionPlanningError("source_span document_id must match unit")
        if self.source_span.source_revision != self.source_revision:
            raise SectionPlanningError("source_span source_revision must match unit")
        if not isinstance(self.boundary_kind, UnitBoundaryKind):
            raise SectionPlanningError(
                "boundary_kind must be a UnitBoundaryKind"
            )
        object.__setattr__(self, "warnings", _text_tuple(self.warnings, "warning"))

    @property
    def start_offset(self) -> int:
        return self.source_span.start_offset

    @property
    def end_offset(self) -> int:
        return self.source_span.end_offset

    @property
    def char_count(self) -> int:
        return self.end_offset - self.start_offset


@dataclass(frozen=True, slots=True)
class ContinuationReceipt:
    """Explicit record that one section continues in a following reading unit."""

    receipt_id: str
    document_id: str
    source_revision: str
    section_id: str
    from_unit_id: str
    to_unit_id: str
    split_offset: int
    boundary_kind: UnitBoundaryKind
    forced_split: bool

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "document_id",
            "source_revision",
            "section_id",
            "from_unit_id",
            "to_unit_id",
        ):
            _require_text(getattr(self, name), name)
        if (
            isinstance(self.split_offset, bool)
            or not isinstance(self.split_offset, int)
            or self.split_offset <= 0
        ):
            raise SectionPlanningError("split_offset must be a positive integer")
        if not isinstance(self.boundary_kind, UnitBoundaryKind):
            raise SectionPlanningError(
                "boundary_kind must be a UnitBoundaryKind"
            )
        if not isinstance(self.forced_split, bool):
            raise SectionPlanningError("forced_split must be a bool")


@dataclass(frozen=True, slots=True)
class HierarchicalSectionPlan:
    """Deterministic plan and receipts for one exact structure-map revision."""

    plan_id: str
    document_id: str
    source_revision: str
    structure_map_id: str
    planner_version: str
    budget: SectionPlanningBudget
    units: tuple[ReadingUnit, ...]
    continuation_receipts: tuple[ContinuationReceipt, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "plan_id",
            "document_id",
            "source_revision",
            "structure_map_id",
            "planner_version",
        ):
            _require_text(getattr(self, name), name)
        if not isinstance(self.budget, SectionPlanningBudget):
            raise SectionPlanningError("budget must be a SectionPlanningBudget")
        units = tuple(self.units)
        if not units or any(not isinstance(unit, ReadingUnit) for unit in units):
            raise SectionPlanningError(
                "units must contain at least one ReadingUnit"
            )
        if len({unit.unit_id for unit in units}) != len(units):
            raise SectionPlanningError("unit_id values must be unique")
        if [unit.order_index for unit in units] != list(range(len(units))):
            raise SectionPlanningError(
                "unit order_index values must be consecutive from zero"
            )
        for unit in units:
            if (
                unit.document_id != self.document_id
                or unit.source_revision != self.source_revision
                or unit.structure_map_id != self.structure_map_id
            ):
                raise SectionPlanningError(
                    "all units must match plan document, revision, and map"
                )
        receipts = tuple(self.continuation_receipts)
        if any(not isinstance(item, ContinuationReceipt) for item in receipts):
            raise SectionPlanningError(
                "continuation_receipts must contain ContinuationReceipt values"
            )
        unit_ids = {unit.unit_id for unit in units}
        for receipt in receipts:
            if receipt.from_unit_id not in unit_ids or receipt.to_unit_id not in unit_ids:
                raise SectionPlanningError(
                    "continuation receipt must reference known units"
                )
        object.__setattr__(self, "units", units)
        object.__setattr__(self, "continuation_receipts", receipts)
        object.__setattr__(self, "warnings", _text_tuple(self.warnings, "warning"))


@dataclass(frozen=True, slots=True)
class _UnitDraft:
    section: DocumentSection
    section_unit_index: int
    start_offset: int
    end_offset: int
    boundary_kind: UnitBoundaryKind
    forced_split: bool = False
    warnings: tuple[str, ...] = ()


_PARAGRAPH_BOUNDARY_RE = re.compile(r"(?:\r?\n)[ \t]*(?:\r?\n)")
_SENTENCE_BOUNDARY_RE = re.compile(
    r"[.!?](?:[\"'”’\)\]]*)[ \t]*(?:\r?\n|[ \t]+)"
)
_ATOMIC_CONTENT_KINDS = frozenset(
    {
        ContentKind.TABLE,
        ContentKind.FIGURE,
        ContentKind.CAPTION,
        ContentKind.FOOTNOTE,
        ContentKind.CODE,
    }
)


class HierarchicalSectionPlanner:
    """Plan bounded reading units while preserving structure-map hierarchy."""

    planner_version = "1.0.0"

    def plan(
        self,
        source: RawSource,
        structure_map: DocumentStructureMap,
        *,
        budget: SectionPlanningBudget | None = None,
    ) -> HierarchicalSectionPlan:
        """Produce a deterministic, complete, overlap-free reading plan."""

        resolved_budget = budget or SectionPlanningBudget()
        self._validate_inputs(source, structure_map)

        drafts: list[_UnitDraft] = []
        plan_warnings: list[str] = []
        for section in structure_map.sections:
            section_drafts = self._plan_section(
                source.text,
                section,
                budget=resolved_budget,
            )
            drafts.extend(section_drafts)
            for draft in section_drafts:
                plan_warnings.extend(draft.warnings)

        self._validate_complete_partition(
            drafts,
            source_length=len(source.text),
        )
        unit_ids = self._unit_ids(
            drafts,
            structure_map=structure_map,
            budget=resolved_budget,
        )
        units = self._materialize_units(
            source,
            structure_map,
            drafts,
            unit_ids=unit_ids,
        )
        receipts = self._continuation_receipts(
            structure_map,
            drafts,
            unit_ids=unit_ids,
        )
        plan_id = stable_reader_core_id(
            "hierarchical-section-plan",
            {
                "document_id": structure_map.document_id,
                "source_revision": structure_map.source_revision,
                "structure_map_id": structure_map.map_id,
                "planner_version": self.planner_version,
                "budget": {
                    "max_unit_chars": resolved_budget.max_unit_chars,
                    "min_unit_chars": resolved_budget.min_unit_chars,
                    "boundary_search_chars": resolved_budget.boundary_search_chars,
                },
                "unit_ids": list(unit_ids),
                "receipt_ids": [receipt.receipt_id for receipt in receipts],
            },
        )
        return HierarchicalSectionPlan(
            plan_id=plan_id,
            document_id=structure_map.document_id,
            source_revision=structure_map.source_revision,
            structure_map_id=structure_map.map_id,
            planner_version=self.planner_version,
            budget=resolved_budget,
            units=units,
            continuation_receipts=receipts,
            warnings=tuple(dict.fromkeys(plan_warnings)),
        )

    def _plan_section(
        self,
        text: str,
        section: DocumentSection,
        *,
        budget: SectionPlanningBudget,
    ) -> tuple[_UnitDraft, ...]:
        section_length = section.end_offset - section.start_offset
        if section.content_kind in _ATOMIC_CONTENT_KINDS:
            warnings: tuple[str, ...] = ()
            boundary_kind = UnitBoundaryKind.SECTION_END
            if section_length > budget.max_unit_chars:
                warnings = ("atomic_section_exceeds_budget",)
                boundary_kind = UnitBoundaryKind.ATOMIC_OVERSIZE
            return (
                _UnitDraft(
                    section=section,
                    section_unit_index=0,
                    start_offset=section.start_offset,
                    end_offset=section.end_offset,
                    boundary_kind=boundary_kind,
                    warnings=warnings,
                ),
            )

        drafts: list[_UnitDraft] = []
        cursor = section.start_offset
        section_unit_index = 0
        while section.end_offset - cursor > budget.max_unit_chars:
            hard_end = cursor + budget.max_unit_chars
            search_start = max(
                cursor + budget.min_unit_chars,
                hard_end - budget.boundary_search_chars,
            )
            split_offset, boundary_kind = self._preferred_boundary(
                text,
                search_start=search_start,
                hard_end=hard_end,
            )
            forced_split = split_offset is None
            if split_offset is None:
                split_offset = hard_end
                boundary_kind = UnitBoundaryKind.HARD_LIMIT
            drafts.append(
                _UnitDraft(
                    section=section,
                    section_unit_index=section_unit_index,
                    start_offset=cursor,
                    end_offset=split_offset,
                    boundary_kind=boundary_kind,
                    forced_split=forced_split,
                    warnings=("forced_hard_limit_split",) if forced_split else (),
                )
            )
            cursor = split_offset
            section_unit_index += 1

        drafts.append(
            _UnitDraft(
                section=section,
                section_unit_index=section_unit_index,
                start_offset=cursor,
                end_offset=section.end_offset,
                boundary_kind=UnitBoundaryKind.SECTION_END,
            )
        )
        return tuple(drafts)

    @staticmethod
    def _preferred_boundary(
        text: str,
        *,
        search_start: int,
        hard_end: int,
    ) -> tuple[int | None, UnitBoundaryKind]:
        if search_start >= hard_end:
            return None, UnitBoundaryKind.HARD_LIMIT
        window = text[search_start:hard_end]

        paragraph_matches = tuple(_PARAGRAPH_BOUNDARY_RE.finditer(window))
        if paragraph_matches:
            return (
                search_start + paragraph_matches[-1].end(),
                UnitBoundaryKind.PARAGRAPH,
            )

        sentence_matches = tuple(_SENTENCE_BOUNDARY_RE.finditer(window))
        if sentence_matches:
            return (
                search_start + sentence_matches[-1].end(),
                UnitBoundaryKind.SENTENCE,
            )

        line_break = window.rfind("\n")
        if line_break >= 0:
            return search_start + line_break + 1, UnitBoundaryKind.LINE
        return None, UnitBoundaryKind.HARD_LIMIT

    def _unit_ids(
        self,
        drafts: list[_UnitDraft],
        *,
        structure_map: DocumentStructureMap,
        budget: SectionPlanningBudget,
    ) -> tuple[str, ...]:
        return tuple(
            stable_reader_core_id(
                "reading-unit",
                {
                    "structure_map_id": structure_map.map_id,
                    "planner_version": self.planner_version,
                    "section_id": draft.section.section_id,
                    "section_unit_index": draft.section_unit_index,
                    "start_offset": draft.start_offset,
                    "end_offset": draft.end_offset,
                    "boundary_kind": draft.boundary_kind.value,
                    "max_unit_chars": budget.max_unit_chars,
                    "min_unit_chars": budget.min_unit_chars,
                    "boundary_search_chars": budget.boundary_search_chars,
                },
            )
            for draft in drafts
        )

    def _materialize_units(
        self,
        source: RawSource,
        structure_map: DocumentStructureMap,
        drafts: list[_UnitDraft],
        *,
        unit_ids: tuple[str, ...],
    ) -> tuple[ReadingUnit, ...]:
        section_positions: dict[str, list[int]] = {}
        for index, draft in enumerate(drafts):
            section_positions.setdefault(draft.section.section_id, []).append(index)

        units: list[ReadingUnit] = []
        for index, draft in enumerate(drafts):
            positions = section_positions[draft.section.section_id]
            local_position = positions.index(index)
            continuation_from = (
                unit_ids[positions[local_position - 1]] if local_position > 0 else None
            )
            continuation_to = (
                unit_ids[positions[local_position + 1]]
                if local_position + 1 < len(positions)
                else None
            )
            span = SourceSpan.from_text(
                document_id=structure_map.document_id,
                raw_text=source.text,
                start_offset=draft.start_offset,
                end_offset=draft.end_offset,
                source_revision=structure_map.source_revision,
                span_id=unit_ids[index],
            )
            units.append(
                ReadingUnit(
                    unit_id=unit_ids[index],
                    document_id=structure_map.document_id,
                    source_revision=structure_map.source_revision,
                    structure_map_id=structure_map.map_id,
                    section_id=draft.section.section_id,
                    parent_section_id=draft.section.parent_section_id,
                    order_index=index,
                    section_unit_index=draft.section_unit_index,
                    source_span=span,
                    boundary_kind=draft.boundary_kind,
                    previous_unit_id=unit_ids[index - 1] if index > 0 else None,
                    next_unit_id=(
                        unit_ids[index + 1] if index + 1 < len(unit_ids) else None
                    ),
                    continuation_from_unit_id=continuation_from,
                    continuation_to_unit_id=continuation_to,
                    warnings=draft.warnings,
                )
            )
        return tuple(units)

    @staticmethod
    def _continuation_receipts(
        structure_map: DocumentStructureMap,
        drafts: list[_UnitDraft],
        *,
        unit_ids: tuple[str, ...],
    ) -> tuple[ContinuationReceipt, ...]:
        receipts: list[ContinuationReceipt] = []
        for index, draft in enumerate(drafts[:-1]):
            next_draft = drafts[index + 1]
            if next_draft.section.section_id != draft.section.section_id:
                continue
            receipt_id = stable_reader_core_id(
                "continuation-receipt",
                {
                    "structure_map_id": structure_map.map_id,
                    "section_id": draft.section.section_id,
                    "from_unit_id": unit_ids[index],
                    "to_unit_id": unit_ids[index + 1],
                    "split_offset": draft.end_offset,
                    "boundary_kind": draft.boundary_kind.value,
                    "forced_split": draft.forced_split,
                },
            )
            receipts.append(
                ContinuationReceipt(
                    receipt_id=receipt_id,
                    document_id=structure_map.document_id,
                    source_revision=structure_map.source_revision,
                    section_id=draft.section.section_id,
                    from_unit_id=unit_ids[index],
                    to_unit_id=unit_ids[index + 1],
                    split_offset=draft.end_offset,
                    boundary_kind=draft.boundary_kind,
                    forced_split=draft.forced_split,
                )
            )
        return tuple(receipts)

    @staticmethod
    def _validate_inputs(
        source: RawSource,
        structure_map: DocumentStructureMap,
    ) -> None:
        if not isinstance(source, RawSource):
            raise SectionPlanningError("source must be a RawSource")
        if not isinstance(structure_map, DocumentStructureMap):
            raise SectionPlanningError(
                "structure_map must be a DocumentStructureMap"
            )
        content_hash = sha256(source.text.encode("utf-8")).hexdigest()
        source_revision = source.source_revision or f"sha256:{content_hash}"
        if source.document_id != structure_map.document_id:
            raise SectionPlanningError(
                "source document_id must match structure map"
            )
        if source_revision != structure_map.source_revision:
            raise SectionPlanningError(
                "source revision must match structure map"
            )
        if content_hash != structure_map.content_hash:
            raise SectionPlanningError(
                "source content hash must match structure map"
            )
        sections = structure_map.sections
        if sections[0].start_offset != 0 or sections[-1].end_offset != len(source.text):
            raise SectionPlanningError(
                "structure sections must cover the complete source"
            )
        for previous, current in zip(sections, sections[1:]):
            if previous.end_offset != current.start_offset:
                raise SectionPlanningError(
                    "structure sections must be contiguous and non-overlapping"
                )

    @staticmethod
    def _validate_complete_partition(
        drafts: list[_UnitDraft],
        *,
        source_length: int,
    ) -> None:
        if not drafts:
            raise SectionPlanningError("planner produced no reading units")
        if drafts[0].start_offset != 0 or drafts[-1].end_offset != source_length:
            raise SectionPlanningError(
                "reading units must cover the complete source"
            )
        for previous, current in zip(drafts, drafts[1:]):
            if previous.end_offset != current.start_offset:
                raise SectionPlanningError(
                    "reading units must be contiguous and overlap-free"
                )


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SectionPlanningError(f"{field_name} must be a non-empty string")
    return value


def _text_tuple(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    return result


__all__ = [
    "ContinuationReceipt",
    "HierarchicalSectionPlan",
    "HierarchicalSectionPlanner",
    "ReadingUnit",
    "SectionPlanningBudget",
    "SectionPlanningError",
    "UnitBoundaryKind",
]
