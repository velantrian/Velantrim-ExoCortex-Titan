"""Multi-axis Reader Core coverage accounting for PR-RDR-04.

CoverageMap records observable processing coverage. It deliberately has no
global score and never equates source processing with correctness,
understanding, confidence, truth, Canon admission, or memory authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Iterable

from core.critical_exceptions import (
    CriticalExceptionCandidate,
    ExceptionScanResult,
)
from core.hierarchical_section_planner import (
    HierarchicalSectionPlan,
    ReadingUnit,
)
from core.knowledge_capsule import SourceSpan
from core.reader_core_contracts import (
    ContentKind,
    CoverageAxis,
    DocumentSection,
    DocumentStructureMap,
    stable_reader_core_id,
)
from core.section_card import SectionCard
from core.semantic_reader import RawSource, ReaderStatus

COVERAGE_MAP_SCHEMA_VERSION = "reader-core.coverage-map.v1"
_TABLE_FIGURE_KINDS = frozenset(
    {ContentKind.TABLE, ContentKind.FIGURE, ContentKind.CAPTION}
)


class CoverageMapError(ValueError):
    """Raised when coverage inputs or derived accounting are inconsistent."""


class CoverageMeasureKind(str, Enum):
    """Observable population measured by one coverage axis."""

    READING_UNIT = "reading_unit"
    SOURCE_CHARACTER = "source_character"
    CLAIM_SOURCE_SPAN = "claim_source_span"
    TABLE_FIGURE_UNIT = "table_figure_unit"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CoverageAxisReceipt:
    """One independently interpretable coverage measurement."""

    receipt_id: str
    axis: CoverageAxis
    measure_kind: CoverageMeasureKind
    processed_count: int
    denominator_count: int | None
    basis_code: str
    unresolved_ids: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.receipt_id, "receipt_id")
        if not isinstance(self.axis, CoverageAxis):
            raise CoverageMapError("axis must be a CoverageAxis")
        if not isinstance(self.measure_kind, CoverageMeasureKind):
            raise CoverageMapError(
                "measure_kind must be a CoverageMeasureKind"
            )
        _require_non_negative_int(self.processed_count, "processed_count")
        denominator = self.denominator_count
        if denominator is not None:
            _require_non_negative_int(denominator, "denominator_count")
            if self.processed_count > denominator:
                raise CoverageMapError(
                    "processed_count cannot exceed denominator_count"
                )
        _require_text(self.basis_code, "basis_code")
        unresolved_ids = _unique_text_tuple(
            self.unresolved_ids,
            "unresolved_id",
        )
        warnings = _unique_text_tuple(self.warnings, "warning")
        object.__setattr__(self, "unresolved_ids", unresolved_ids)
        object.__setattr__(self, "warnings", warnings)
        expected_id = _axis_receipt_identity(
            axis=self.axis,
            measure_kind=self.measure_kind,
            processed_count=self.processed_count,
            denominator_count=denominator,
            basis_code=self.basis_code,
            unresolved_ids=unresolved_ids,
            warnings=warnings,
        )
        if self.receipt_id != expected_id:
            raise CoverageMapError(
                "receipt_id does not match axis receipt content"
            )

    @property
    def ratio(self) -> float | None:
        """Return a ratio only when a non-empty denominator is known."""

        denominator = self.denominator_count
        if denominator is None or denominator == 0:
            return None
        return self.processed_count / denominator


@dataclass(frozen=True, slots=True)
class UnresolvedCoverageRegion:
    """Exact source region explaining why one axis is incomplete."""

    region_id: str
    axis: CoverageAxis
    unit_id: str
    section_id: str
    source_span: SourceSpan
    reason_code: str

    def __post_init__(self) -> None:
        _require_text(self.region_id, "region_id")
        if not isinstance(self.axis, CoverageAxis):
            raise CoverageMapError("axis must be a CoverageAxis")
        _require_text(self.unit_id, "unit_id")
        _require_text(self.section_id, "section_id")
        _require_text(self.reason_code, "reason_code")
        if not isinstance(self.source_span, SourceSpan):
            raise CoverageMapError("source_span must be a SourceSpan")
        if self.source_span.span_id != self.unit_id:
            raise CoverageMapError("source_span span_id must equal unit_id")
        expected_id = _unresolved_region_identity(
            axis=self.axis,
            unit_id=self.unit_id,
            section_id=self.section_id,
            source_span=self.source_span,
            reason_code=self.reason_code,
        )
        if self.region_id != expected_id:
            raise CoverageMapError(
                "region_id does not match unresolved region content"
            )


@dataclass(frozen=True, slots=True)
class UnsupportedAssetRegion:
    """Atomic asset preserved but outside the planner's normal budget."""

    asset_id: str
    unit_id: str
    section_id: str
    content_kind: ContentKind
    source_span: SourceSpan
    reason_code: str

    def __post_init__(self) -> None:
        _require_text(self.asset_id, "asset_id")
        _require_text(self.unit_id, "unit_id")
        _require_text(self.section_id, "section_id")
        _require_text(self.reason_code, "reason_code")
        if not isinstance(self.content_kind, ContentKind):
            raise CoverageMapError("content_kind must be a ContentKind")
        if not isinstance(self.source_span, SourceSpan):
            raise CoverageMapError("source_span must be a SourceSpan")
        if self.source_span.span_id != self.unit_id:
            raise CoverageMapError("source_span span_id must equal unit_id")
        expected_id = _unsupported_asset_identity(
            unit_id=self.unit_id,
            section_id=self.section_id,
            content_kind=self.content_kind,
            source_span=self.source_span,
            reason_code=self.reason_code,
        )
        if self.asset_id != expected_id:
            raise CoverageMapError(
                "asset_id does not match unsupported asset content"
            )


@dataclass(frozen=True, slots=True)
class CoverageMap:
    """Immutable independent coverage axes for one exact reading plan."""

    coverage_map_id: str
    schema_version: str
    builder_version: str
    document_id: str
    source_revision: str
    structure_map_id: str
    plan_id: str
    axes: tuple[CoverageAxisReceipt, ...]
    card_ids: tuple[str, ...]
    exception_candidate_ids: tuple[str, ...]
    exception_scan_receipt_ids: tuple[str, ...]
    unresolved_regions: tuple[UnresolvedCoverageRegion, ...] = ()
    unsupported_assets: tuple[UnsupportedAssetRegion, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "coverage_map_id",
            "schema_version",
            "builder_version",
            "document_id",
            "source_revision",
            "structure_map_id",
            "plan_id",
        ):
            _require_text(getattr(self, name), name)
        if self.schema_version != COVERAGE_MAP_SCHEMA_VERSION:
            raise CoverageMapError("unsupported CoverageMap schema_version")

        axes = tuple(self.axes)
        if any(not isinstance(item, CoverageAxisReceipt) for item in axes):
            raise CoverageMapError(
                "axes must contain CoverageAxisReceipt values"
            )
        if tuple(item.axis for item in axes) != tuple(CoverageAxis):
            raise CoverageMapError(
                "axes must contain every CoverageAxis exactly once in enum order"
            )

        card_ids = _unique_text_tuple(self.card_ids, "card_id")
        candidate_ids = _unique_text_tuple(
            self.exception_candidate_ids,
            "exception_candidate_id",
        )
        scan_ids = _unique_text_tuple(
            self.exception_scan_receipt_ids,
            "exception_scan_receipt_id",
        )

        regions = tuple(self.unresolved_regions)
        if any(not isinstance(item, UnresolvedCoverageRegion) for item in regions):
            raise CoverageMapError(
                "unresolved_regions must contain UnresolvedCoverageRegion values"
            )
        if len({item.region_id for item in regions}) != len(regions):
            raise CoverageMapError("unresolved region IDs must be unique")
        for region in regions:
            _require_map_span_identity(
                region.source_span,
                document_id=self.document_id,
                source_revision=self.source_revision,
                field_name="unresolved region",
            )

        assets = tuple(self.unsupported_assets)
        if any(not isinstance(item, UnsupportedAssetRegion) for item in assets):
            raise CoverageMapError(
                "unsupported_assets must contain UnsupportedAssetRegion values"
            )
        if len({item.asset_id for item in assets}) != len(assets):
            raise CoverageMapError("unsupported asset IDs must be unique")
        for asset in assets:
            _require_map_span_identity(
                asset.source_span,
                document_id=self.document_id,
                source_revision=self.source_revision,
                field_name="unsupported asset",
            )

        warnings = _unique_text_tuple(self.warnings, "warning")
        object.__setattr__(self, "axes", axes)
        object.__setattr__(self, "card_ids", card_ids)
        object.__setattr__(self, "exception_candidate_ids", candidate_ids)
        object.__setattr__(self, "exception_scan_receipt_ids", scan_ids)
        object.__setattr__(self, "unresolved_regions", regions)
        object.__setattr__(self, "unsupported_assets", assets)
        object.__setattr__(self, "warnings", warnings)

        expected_id = _coverage_map_identity(
            schema_version=self.schema_version,
            builder_version=self.builder_version,
            document_id=self.document_id,
            source_revision=self.source_revision,
            structure_map_id=self.structure_map_id,
            plan_id=self.plan_id,
            axes=axes,
            card_ids=card_ids,
            exception_candidate_ids=candidate_ids,
            exception_scan_receipt_ids=scan_ids,
            unresolved_regions=regions,
            unsupported_assets=assets,
            warnings=warnings,
        )
        if self.coverage_map_id != expected_id:
            raise CoverageMapError(
                "coverage_map_id does not match CoverageMap content"
            )

    def axis(self, axis: CoverageAxis) -> CoverageAxisReceipt:
        """Return one independent axis without creating a global score."""

        if not isinstance(axis, CoverageAxis):
            raise CoverageMapError("axis must be a CoverageAxis")
        return self.axes[list(CoverageAxis).index(axis)]


class CoverageMapBuilder:
    """Build coverage from exact structure, plan, cards, and scan receipts."""

    builder_version = "1.2.0"

    def build(
        self,
        source: RawSource,
        structure_map: DocumentStructureMap,
        plan: HierarchicalSectionPlan,
        *,
        cards: Iterable[SectionCard] = (),
        exception_scans: Iterable[ExceptionScanResult] = (),
    ) -> CoverageMap:
        """Build all six axes without inferring correctness or understanding."""

        self._validate_source_structure_plan(source, structure_map, plan)
        units_by_id = {unit.unit_id: unit for unit in plan.units}
        sections_by_id = {
            section.section_id: section for section in structure_map.sections
        }
        cards_by_unit = self._validate_cards(
            tuple(cards),
            plan=plan,
            units_by_id=units_by_id,
        )
        scans_by_unit = self._validate_scans(
            source,
            tuple(exception_scans),
            cards_by_unit=cards_by_unit,
            units_by_id=units_by_id,
        )

        ordered_cards = tuple(
            cards_by_unit[unit.unit_id]
            for unit in plan.units
            if unit.unit_id in cards_by_unit
        )
        ordered_scans = tuple(
            scans_by_unit[unit.unit_id]
            for unit in plan.units
            if unit.unit_id in scans_by_unit
        )
        candidates: tuple[CriticalExceptionCandidate, ...] = tuple(
            candidate
            for scan in ordered_scans
            for candidate in scan.candidates
        )
        regions = self._unresolved_regions(
            plan,
            cards_by_unit=cards_by_unit,
            scans_by_unit=scans_by_unit,
        )
        assets = self._unsupported_assets(
            plan,
            sections_by_id=sections_by_id,
        )
        axes = self._axis_receipts(
            source,
            structure_map,
            plan,
            cards_by_unit=cards_by_unit,
            scans_by_unit=scans_by_unit,
        )

        warnings = ["relation_axis_unavailable_until_rdr_06"]
        if not any(
            section.content_kind in _TABLE_FIGURE_KINDS
            for section in structure_map.sections
        ):
            warnings.append("no_table_figure_assets_in_structure")
        if assets:
            warnings.append("unsupported_atomic_assets_present")
        if any(
            card.build_receipt.reader_status is ReaderStatus.PARTIAL
            for card in ordered_cards
        ):
            warnings.append("partial_reader_results_present")
        warning_tuple = tuple(warnings)

        card_ids = tuple(card.card_id for card in ordered_cards)
        candidate_ids = tuple(candidate.candidate_id for candidate in candidates)
        scan_ids = tuple(scan.receipt.receipt_id for scan in ordered_scans)
        coverage_map_id = _coverage_map_identity(
            schema_version=COVERAGE_MAP_SCHEMA_VERSION,
            builder_version=self.builder_version,
            document_id=plan.document_id,
            source_revision=plan.source_revision,
            structure_map_id=plan.structure_map_id,
            plan_id=plan.plan_id,
            axes=axes,
            card_ids=card_ids,
            exception_candidate_ids=candidate_ids,
            exception_scan_receipt_ids=scan_ids,
            unresolved_regions=regions,
            unsupported_assets=assets,
            warnings=warning_tuple,
        )
        return CoverageMap(
            coverage_map_id=coverage_map_id,
            schema_version=COVERAGE_MAP_SCHEMA_VERSION,
            builder_version=self.builder_version,
            document_id=plan.document_id,
            source_revision=plan.source_revision,
            structure_map_id=plan.structure_map_id,
            plan_id=plan.plan_id,
            axes=axes,
            card_ids=card_ids,
            exception_candidate_ids=candidate_ids,
            exception_scan_receipt_ids=scan_ids,
            unresolved_regions=regions,
            unsupported_assets=assets,
            warnings=warning_tuple,
        )

    @staticmethod
    def _validate_source_structure_plan(
        source: RawSource,
        structure_map: DocumentStructureMap,
        plan: HierarchicalSectionPlan,
    ) -> None:
        if not isinstance(source, RawSource):
            raise CoverageMapError("source must be a RawSource")
        if not isinstance(structure_map, DocumentStructureMap):
            raise CoverageMapError(
                "structure_map must be a DocumentStructureMap"
            )
        if not isinstance(plan, HierarchicalSectionPlan):
            raise CoverageMapError(
                "plan must be a HierarchicalSectionPlan"
            )
        content_hash = sha256(source.text.encode("utf-8")).hexdigest()
        source_revision = source.source_revision or f"sha256:{content_hash}"
        if source.document_id != structure_map.document_id:
            raise CoverageMapError(
                "source document_id must match structure map"
            )
        if source_revision != structure_map.source_revision:
            raise CoverageMapError(
                "source revision must match structure map"
            )
        if content_hash != structure_map.content_hash:
            raise CoverageMapError(
                "source content hash must match structure map"
            )
        if (
            plan.document_id != structure_map.document_id
            or plan.source_revision != structure_map.source_revision
            or plan.structure_map_id != structure_map.map_id
        ):
            raise CoverageMapError(
                "plan must match structure map document, revision, and ID"
            )

    @staticmethod
    def _validate_cards(
        cards: tuple[SectionCard, ...],
        *,
        plan: HierarchicalSectionPlan,
        units_by_id: dict[str, ReadingUnit],
    ) -> dict[str, SectionCard]:
        cards_by_unit: dict[str, SectionCard] = {}
        card_ids: set[str] = set()
        for card in cards:
            if not isinstance(card, SectionCard):
                raise CoverageMapError("cards must contain SectionCard values")
            if card.card_id in card_ids:
                raise CoverageMapError("card IDs must be unique")
            card_ids.add(card.card_id)
            if card.unit_id in cards_by_unit:
                raise CoverageMapError(
                    "only one SectionCard may represent a ReadingUnit"
                )
            unit = units_by_id.get(card.unit_id)
            if unit is None:
                raise CoverageMapError("card must reference a plan ReadingUnit")
            if (
                card.document_id != plan.document_id
                or card.source_revision != plan.source_revision
                or card.structure_map_id != plan.structure_map_id
                or card.plan_id != plan.plan_id
                or card.section_id != unit.section_id
                or card.unit_source_span != unit.source_span
            ):
                raise CoverageMapError(
                    "card identity and provenance must match its plan unit"
                )
            cards_by_unit[card.unit_id] = card
        return cards_by_unit

    @staticmethod
    def _validate_scans(
        source: RawSource,
        scans: tuple[ExceptionScanResult, ...],
        *,
        cards_by_unit: dict[str, SectionCard],
        units_by_id: dict[str, ReadingUnit],
    ) -> dict[str, ExceptionScanResult]:
        scans_by_unit: dict[str, ExceptionScanResult] = {}
        candidate_ids: set[str] = set()
        for scan in scans:
            if not isinstance(scan, ExceptionScanResult):
                raise CoverageMapError(
                    "exception_scans must contain ExceptionScanResult values"
                )
            unit_id = scan.receipt.unit_id
            if unit_id in scans_by_unit:
                raise CoverageMapError(
                    "only one exception scan may represent a ReadingUnit"
                )
            card = cards_by_unit.get(unit_id)
            unit = units_by_id.get(unit_id)
            if card is None or unit is None:
                raise CoverageMapError(
                    "exception scan requires a known SectionCard and plan unit"
                )
            if (
                scan.receipt.card_id != card.card_id
                or scan.receipt.scanned_span != unit.source_span
            ):
                raise CoverageMapError(
                    "exception scan receipt must match its card and unit"
                )
            known_claim_ids = {
                card_claim.claim.claim_id for card_claim in card.claims
            }
            for candidate in scan.candidates:
                if candidate.candidate_id in candidate_ids:
                    raise CoverageMapError(
                        "exception candidate IDs must be unique"
                    )
                candidate_ids.add(candidate.candidate_id)
                _validate_candidate(
                    source,
                    candidate,
                    card=card,
                    unit=unit,
                    known_claim_ids=known_claim_ids,
                )
            scans_by_unit[unit_id] = scan
        return scans_by_unit

    @staticmethod
    def _axis_receipts(
        source: RawSource,
        structure_map: DocumentStructureMap,
        plan: HierarchicalSectionPlan,
        *,
        cards_by_unit: dict[str, SectionCard],
        scans_by_unit: dict[str, ExceptionScanResult],
    ) -> tuple[CoverageAxisReceipt, ...]:
        unit_ids = tuple(unit.unit_id for unit in plan.units)
        missing_cards = tuple(
            unit_id for unit_id in unit_ids if unit_id not in cards_by_unit
        )
        missing_scans = tuple(
            unit_id for unit_id in unit_ids if unit_id not in scans_by_unit
        )
        claim_spans = tuple(
            span
            for card in cards_by_unit.values()
            for card_claim in card.claims
            for span in card_claim.claim.source_spans
        )
        claim_chars = _covered_non_whitespace_count(source.text, claim_spans)
        source_chars = sum(
            1 for character in source.text if not character.isspace()
        )
        section_kinds = {
            section.section_id: section.content_kind
            for section in structure_map.sections
        }
        asset_units = tuple(
            unit.unit_id
            for unit in plan.units
            if section_kinds[unit.section_id] in _TABLE_FIGURE_KINDS
        )
        processed_assets = tuple(
            unit_id for unit_id in asset_units if unit_id in cards_by_unit
        )
        missing_assets = tuple(
            unit_id for unit_id in asset_units if unit_id not in cards_by_unit
        )
        validated_spans = sum(
            1 for span in claim_spans if span.verify(source.text)
        )

        return (
            _make_axis_receipt(
                CoverageAxis.STRUCTURAL,
                CoverageMeasureKind.READING_UNIT,
                len(cards_by_unit),
                len(plan.units),
                "section_cards_per_planned_reading_unit",
                missing_cards,
                (),
            ),
            _make_axis_receipt(
                CoverageAxis.CLAIM,
                CoverageMeasureKind.SOURCE_CHARACTER,
                claim_chars,
                source_chars,
                "unique_non_whitespace_characters_linked_by_card_claim_spans",
                missing_cards,
                ("claim_axis_is_provenance_footprint_not_claim_recall",),
            ),
            _make_axis_receipt(
                CoverageAxis.EXCEPTION,
                CoverageMeasureKind.READING_UNIT,
                len(scans_by_unit),
                len(plan.units),
                "exception_scan_receipts_per_planned_reading_unit",
                missing_scans,
                ("exception_axis_is_scan_coverage_not_exception_recall",),
            ),
            _make_axis_receipt(
                CoverageAxis.RELATION,
                CoverageMeasureKind.UNKNOWN,
                0,
                None,
                "relation_analysis_not_implemented",
                (),
                ("relation_axis_unavailable_until_rdr_06",),
            ),
            _make_axis_receipt(
                CoverageAxis.TABLE_FIGURE,
                CoverageMeasureKind.TABLE_FIGURE_UNIT,
                len(processed_assets),
                len(asset_units),
                "cards_per_table_figure_or_caption_reading_unit",
                missing_assets,
                (
                    ("no_table_figure_assets_in_structure",)
                    if not asset_units
                    else ()
                ),
            ),
            _make_axis_receipt(
                CoverageAxis.VALIDATION,
                CoverageMeasureKind.CLAIM_SOURCE_SPAN,
                validated_spans,
                len(claim_spans),
                "verified_absolute_claim_source_spans_per_card_claim_span",
                (),
                ("validation_axis_covers_emitted_claim_spans_only",),
            ),
        )

    @staticmethod
    def _unresolved_regions(
        plan: HierarchicalSectionPlan,
        *,
        cards_by_unit: dict[str, SectionCard],
        scans_by_unit: dict[str, ExceptionScanResult],
    ) -> tuple[UnresolvedCoverageRegion, ...]:
        regions: list[UnresolvedCoverageRegion] = []
        units_by_id = {unit.unit_id: unit for unit in plan.units}
        for unit in plan.units:
            if unit.unit_id not in cards_by_unit:
                regions.extend(
                    (
                        _make_unresolved_region(
                            CoverageAxis.STRUCTURAL,
                            unit,
                            "missing_section_card",
                        ),
                        _make_unresolved_region(
                            CoverageAxis.CLAIM,
                            unit,
                            "unread_unit_has_no_claim_provenance",
                        ),
                    )
                )
            if unit.unit_id not in scans_by_unit:
                regions.append(
                    _make_unresolved_region(
                        CoverageAxis.EXCEPTION,
                        unit,
                        "exception_scan_missing",
                    )
                )
        for unit_id, card in cards_by_unit.items():
            if card.build_receipt.reader_status is ReaderStatus.PARTIAL:
                regions.append(
                    _make_unresolved_region(
                        CoverageAxis.VALIDATION,
                        units_by_id[unit_id],
                        "partial_reader_result",
                    )
                )
        return tuple(regions)

    @staticmethod
    def _unsupported_assets(
        plan: HierarchicalSectionPlan,
        *,
        sections_by_id: dict[str, DocumentSection],
    ) -> tuple[UnsupportedAssetRegion, ...]:
        assets: list[UnsupportedAssetRegion] = []
        for unit in plan.units:
            if "atomic_section_exceeds_budget" not in unit.warnings:
                continue
            section = sections_by_id[unit.section_id]
            asset_id = _unsupported_asset_identity(
                unit_id=unit.unit_id,
                section_id=unit.section_id,
                content_kind=section.content_kind,
                source_span=unit.source_span,
                reason_code="atomic_section_exceeds_budget",
            )
            assets.append(
                UnsupportedAssetRegion(
                    asset_id=asset_id,
                    unit_id=unit.unit_id,
                    section_id=unit.section_id,
                    content_kind=section.content_kind,
                    source_span=unit.source_span,
                    reason_code="atomic_section_exceeds_budget",
                )
            )
        return tuple(assets)


def _validate_candidate(
    source: RawSource,
    candidate: CriticalExceptionCandidate,
    *,
    card: SectionCard,
    unit: ReadingUnit,
    known_claim_ids: set[str],
) -> None:
    if (
        candidate.section_id != card.section_id
        or candidate.card_id != card.card_id
        or candidate.unit_id != card.unit_id
    ):
        raise CoverageMapError(
            "exception candidate must match its card and unit"
        )
    if (
        candidate.statement_span.start_offset < unit.start_offset
        or candidate.statement_span.end_offset > unit.end_offset
    ):
        raise CoverageMapError(
            "candidate statement_span must fit inside its unit"
        )
    if not candidate.trigger_span.verify(source.text):
        raise CoverageMapError(
            "candidate trigger_span must verify against source"
        )
    if not candidate.statement_span.verify(source.text):
        raise CoverageMapError(
            "candidate statement_span must verify against source"
        )
    trigger_text = source.text[
        candidate.trigger_span.start_offset : candidate.trigger_span.end_offset
    ]
    if trigger_text != candidate.trigger_phrase:
        raise CoverageMapError(
            "candidate trigger_phrase must match source"
        )
    statement_text = source.text[
        candidate.statement_span.start_offset : candidate.statement_span.end_offset
    ]
    if statement_text != candidate.statement_text:
        raise CoverageMapError(
            "candidate statement_text must match source"
        )
    if not set(candidate.target_claim_refs).issubset(known_claim_ids):
        raise CoverageMapError(
            "candidate target claims must belong to its card"
        )


def _make_axis_receipt(
    axis: CoverageAxis,
    measure_kind: CoverageMeasureKind,
    processed_count: int,
    denominator_count: int | None,
    basis_code: str,
    unresolved_ids: tuple[str, ...],
    warnings: tuple[str, ...],
) -> CoverageAxisReceipt:
    receipt_id = _axis_receipt_identity(
        axis=axis,
        measure_kind=measure_kind,
        processed_count=processed_count,
        denominator_count=denominator_count,
        basis_code=basis_code,
        unresolved_ids=unresolved_ids,
        warnings=warnings,
    )
    return CoverageAxisReceipt(
        receipt_id=receipt_id,
        axis=axis,
        measure_kind=measure_kind,
        processed_count=processed_count,
        denominator_count=denominator_count,
        basis_code=basis_code,
        unresolved_ids=unresolved_ids,
        warnings=warnings,
    )


def _make_unresolved_region(
    axis: CoverageAxis,
    unit: ReadingUnit,
    reason_code: str,
) -> UnresolvedCoverageRegion:
    region_id = _unresolved_region_identity(
        axis=axis,
        unit_id=unit.unit_id,
        section_id=unit.section_id,
        source_span=unit.source_span,
        reason_code=reason_code,
    )
    return UnresolvedCoverageRegion(
        region_id=region_id,
        axis=axis,
        unit_id=unit.unit_id,
        section_id=unit.section_id,
        source_span=unit.source_span,
        reason_code=reason_code,
    )


def _covered_non_whitespace_count(
    text: str,
    spans: Iterable[SourceSpan],
) -> int:
    return sum(
        1
        for start, end in _merged_intervals(spans)
        for character in text[start:end]
        if not character.isspace()
    )


def _merged_intervals(
    spans: Iterable[SourceSpan],
) -> tuple[tuple[int, int], ...]:
    intervals = sorted((span.start_offset, span.end_offset) for span in spans)
    if not intervals:
        return ()
    merged: list[tuple[int, int]] = []
    current_start, current_end = intervals[0]
    for start, end in intervals[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end
    merged.append((current_start, current_end))
    return tuple(merged)


def _require_map_span_identity(
    span: SourceSpan,
    *,
    document_id: str,
    source_revision: str,
    field_name: str,
) -> None:
    if span.document_id != document_id:
        raise CoverageMapError(
            f"{field_name} document_id must match CoverageMap"
        )
    if span.source_revision != source_revision:
        raise CoverageMapError(
            f"{field_name} source_revision must match CoverageMap"
        )


def _axis_receipt_identity(
    *,
    axis: CoverageAxis,
    measure_kind: CoverageMeasureKind,
    processed_count: int,
    denominator_count: int | None,
    basis_code: str,
    unresolved_ids: tuple[str, ...],
    warnings: tuple[str, ...],
) -> str:
    return stable_reader_core_id(
        "coverage-axis-receipt",
        {
            "axis": axis.value,
            "measure_kind": measure_kind.value,
            "processed_count": processed_count,
            "denominator_count": denominator_count,
            "basis_code": basis_code,
            "unresolved_ids": list(unresolved_ids),
            "warnings": list(warnings),
        },
    )


def _unresolved_region_identity(
    *,
    axis: CoverageAxis,
    unit_id: str,
    section_id: str,
    source_span: SourceSpan,
    reason_code: str,
) -> str:
    return stable_reader_core_id(
        "unresolved-coverage-region",
        {
            "axis": axis.value,
            "unit_id": unit_id,
            "section_id": section_id,
            "source_span": source_span.identity_payload(),
            "reason_code": reason_code,
        },
    )


def _unsupported_asset_identity(
    *,
    unit_id: str,
    section_id: str,
    content_kind: ContentKind,
    source_span: SourceSpan,
    reason_code: str,
) -> str:
    return stable_reader_core_id(
        "unsupported-asset-region",
        {
            "unit_id": unit_id,
            "section_id": section_id,
            "content_kind": content_kind.value,
            "source_span": source_span.identity_payload(),
            "reason_code": reason_code,
        },
    )


def _coverage_map_identity(
    *,
    schema_version: str,
    builder_version: str,
    document_id: str,
    source_revision: str,
    structure_map_id: str,
    plan_id: str,
    axes: tuple[CoverageAxisReceipt, ...],
    card_ids: tuple[str, ...],
    exception_candidate_ids: tuple[str, ...],
    exception_scan_receipt_ids: tuple[str, ...],
    unresolved_regions: tuple[UnresolvedCoverageRegion, ...],
    unsupported_assets: tuple[UnsupportedAssetRegion, ...],
    warnings: tuple[str, ...],
) -> str:
    return stable_reader_core_id(
        "coverage-map",
        {
            "schema_version": schema_version,
            "builder_version": builder_version,
            "document_id": document_id,
            "source_revision": source_revision,
            "structure_map_id": structure_map_id,
            "plan_id": plan_id,
            "axis_receipt_ids": [item.receipt_id for item in axes],
            "card_ids": list(card_ids),
            "exception_candidate_ids": list(exception_candidate_ids),
            "exception_scan_receipt_ids": list(exception_scan_receipt_ids),
            "unresolved_region_ids": [
                item.region_id for item in unresolved_regions
            ],
            "unsupported_asset_ids": [
                item.asset_id for item in unsupported_assets
            ],
            "warnings": list(warnings),
        },
    )


def _require_non_negative_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CoverageMapError(f"{field_name} must be an integer >= 0")
    return value


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CoverageMapError(f"{field_name} must be a non-empty string")
    return value


def _unique_text_tuple(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    if len(set(result)) != len(result):
        raise CoverageMapError(f"{field_name} values must be unique")
    return result


__all__ = [
    "COVERAGE_MAP_SCHEMA_VERSION",
    "CoverageAxisReceipt",
    "CoverageMap",
    "CoverageMapBuilder",
    "CoverageMapError",
    "CoverageMeasureKind",
    "UnresolvedCoverageRegion",
    "UnsupportedAssetRegion",
]
