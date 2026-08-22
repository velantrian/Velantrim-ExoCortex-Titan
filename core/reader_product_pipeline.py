"""Bounded user-facing orchestration for Titan Reader Core.

This module composes existing Reader Core primitives into one explicit foreground
operation:

    RawSource -> structure -> reading units -> SemanticReader -> SectionCards
    -> exception scan -> CoverageMap -> bounded selective reread
    -> completed ReadingSession -> source-linked GlobalDocumentSynthesis

It deliberately adds no scheduler, persistence adapter, memory admission, Canon
write, TruthGate call, graph authority, or production activation.  A synthesis is
an interpretation candidate built from source-grounded Reader claims; it is not
truth and is never written anywhere by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import time
from typing import Iterable

from core.critical_exceptions import (
    CriticalExceptionCandidate,
    DeterministicCriticalExceptionScanner,
    ExceptionScanResult,
)
from core.document_structure import (
    DeterministicDocumentStructureParser,
    DocumentStructureFormat,
)
from core.global_synthesis import (
    GlobalDocumentSynthesis,
    GlobalDocumentSynthesisBuilder,
    SynthesisClaimKind,
    SynthesisClaimProposal,
)
from core.hierarchical_section_planner import (
    HierarchicalSectionPlan,
    HierarchicalSectionPlanner,
    ReadingUnit,
    SectionPlanningBudget,
)
from core.reader_coverage import CoverageMap, CoverageMapBuilder
from core.reading_session import (
    ReadingSession,
    ReadingSessionManager,
    ReadingSessionUsage,
)
from core.section_card import (
    SectionCard,
    SectionCardBuilder,
    SectionCardError,
    SpanCoordinateSpace,
)
from core.section_relation_builder import DeterministicSectionRelationBuilder
from core.section_relations import CrossSectionRelationSet
from core.selective_reread import (
    SelectiveReReadBudget,
    SelectiveReReadPlan,
    SelectiveReReadPlanner,
)
from core.semantic_reader import (
    RawSource,
    ReaderBudget,
    ReaderMode,
    ReaderResult,
    SemanticReader,
)


class ReaderProductPipelineError(RuntimeError):
    """Raised when the explicit foreground reading operation cannot start safely."""


@dataclass(frozen=True, slots=True)
class ReaderProductConfig:
    """Hard bounds for one explicit document-reading operation."""

    initial_mode: ReaderMode = ReaderMode.STANDARD
    section_budget: SectionPlanningBudget = SectionPlanningBudget()
    reader_budget: ReaderBudget = ReaderBudget()
    reread_budget: SelectiveReReadBudget = SelectiveReReadBudget(
        max_tasks=16,
        max_total_chars=80_000,
        max_task_chars=20_000,
        max_tasks_per_section=4,
    )
    max_digest_chars: int = 8_000

    def __post_init__(self) -> None:
        if not isinstance(self.initial_mode, ReaderMode):
            raise ReaderProductPipelineError("initial_mode must be a ReaderMode")
        if not isinstance(self.section_budget, SectionPlanningBudget):
            raise ReaderProductPipelineError(
                "section_budget must be a SectionPlanningBudget"
            )
        if not isinstance(self.reader_budget, ReaderBudget):
            raise ReaderProductPipelineError("reader_budget must be a ReaderBudget")
        if not isinstance(self.reread_budget, SelectiveReReadBudget):
            raise ReaderProductPipelineError(
                "reread_budget must be a SelectiveReReadBudget"
            )
        if (
            isinstance(self.max_digest_chars, bool)
            or not isinstance(self.max_digest_chars, int)
            or self.max_digest_chars <= 0
        ):
            raise ReaderProductPipelineError(
                "max_digest_chars must be a positive integer"
            )


@dataclass(frozen=True, slots=True)
class ReaderProductResult:
    """Read-side result.  Nothing here is automatically admitted to memory/Canon."""

    source: RawSource
    reading_plan: HierarchicalSectionPlan
    cards: tuple[SectionCard, ...]
    exception_scans: tuple[ExceptionScanResult, ...]
    coverage_map: CoverageMap
    initial_reread_plan: SelectiveReReadPlan
    remaining_reread_plan: SelectiveReReadPlan
    relations: CrossSectionRelationSet | None
    session: ReadingSession
    synthesis: GlobalDocumentSynthesis | None
    source_grounded_digest: str
    reader_attempts: int
    reread_attempts: int
    warnings: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return self.synthesis is not None and not self.session.pending_unit_ids

    @property
    def completed_units(self) -> int:
        return len(self.cards)

    @property
    def total_units(self) -> int:
        return len(self.reading_plan.units)


class ReaderProductPipeline:
    """Compose the existing Reader Core into one bounded foreground operation."""

    pipeline_version = "reader-product-pipeline.v1"

    def __init__(
        self,
        reader: SemanticReader,
        *,
        config: ReaderProductConfig | None = None,
    ) -> None:
        if not isinstance(reader, SemanticReader):
            raise ReaderProductPipelineError("reader must implement SemanticReader")
        self._reader = reader
        self._config = config or ReaderProductConfig()
        self._structure_parser = DeterministicDocumentStructureParser()
        self._section_planner = HierarchicalSectionPlanner()
        self._card_builder = SectionCardBuilder()
        self._exception_scanner = DeterministicCriticalExceptionScanner()
        self._coverage_builder = CoverageMapBuilder()
        self._reread_planner = SelectiveReReadPlanner()
        self._relation_builder = DeterministicSectionRelationBuilder()
        self._session_manager = ReadingSessionManager()
        self._synthesis_builder = GlobalDocumentSynthesisBuilder()

    async def read(
        self,
        source: RawSource,
        *,
        document_format: DocumentStructureFormat = DocumentStructureFormat.PLAIN_TEXT,
        session_key: str | None = None,
    ) -> ReaderProductResult:
        if not isinstance(source, RawSource):
            raise ReaderProductPipelineError("source must be a RawSource")
        if not source.text.strip():
            raise ReaderProductPipelineError("document contains no readable text")
        if not isinstance(document_format, DocumentStructureFormat):
            raise ReaderProductPipelineError(
                "document_format must be a DocumentStructureFormat"
            )

        normalized = _normalize_source_revision(source)
        structure = self._structure_parser.parse(
            normalized,
            document_format=document_format,
        )
        plan = self._section_planner.plan(
            normalized,
            structure,
            budget=self._config.section_budget,
        )

        now_ms = _now_ms()
        resolved_session_key = session_key or _default_session_key(normalized, plan)
        session = self._session_manager.create(
            plan,
            session_key=resolved_session_key,
            policy_snapshot_id=self.pipeline_version,
            policy_version=self.pipeline_version,
        )
        session = self._session_manager.claim(
            session,
            runner_id=self.pipeline_version,
            expires_at_ms=now_ms + 3_600_000,
            now_ms=now_ms,
        )
        lease = session.active_lease
        if lease is None:
            raise ReaderProductPipelineError("reading session lease was not created")
        session = self._session_manager.start(session, lease, now_ms=now_ms + 1)

        cards_by_unit: dict[str, SectionCard] = {}
        warnings: list[str] = []
        reader_attempts = 0
        for unit in plan.units:
            reader_attempts += 1
            card, warning = await self._read_unit(
                normalized,
                plan,
                unit,
                mode=self._config.initial_mode,
            )
            if card is not None:
                cards_by_unit[unit.unit_id] = card
            if warning is not None:
                warnings.append(warning)

        cards = _cards_in_plan_order(plan, cards_by_unit)
        scans = self._scan_cards(normalized, cards)
        coverage = self._coverage_builder.build(
            normalized,
            structure,
            plan,
            cards=cards,
            exception_scans=scans,
        )
        exceptions = _exception_candidates(scans)
        initial_reread_plan = self._reread_planner.plan(
            normalized,
            plan,
            coverage,
            exception_candidates=exceptions,
            budget=self._config.reread_budget,
        )

        reread_attempts = 0
        for task in initial_reread_plan.tasks:
            if task.reader_mode is None:
                warnings.append(
                    f"reread:task:{task.task_id}:requires_non_reader_action"
                )
                continue
            unit = _unit_by_id(plan, task.unit_id)
            reread_attempts += 1
            reader_attempts += 1
            card, warning = await self._read_unit(
                normalized,
                plan,
                unit,
                mode=task.reader_mode,
            )
            if card is not None:
                cards_by_unit[unit.unit_id] = card
            if warning is not None:
                warnings.append(f"reread:{warning}")

        cards = _cards_in_plan_order(plan, cards_by_unit)
        scans = self._scan_cards(normalized, cards)
        coverage = self._coverage_builder.build(
            normalized,
            structure,
            plan,
            cards=cards,
            exception_scans=scans,
        )
        exceptions = _exception_candidates(scans)
        remaining_reread_plan = self._reread_planner.plan(
            normalized,
            plan,
            coverage,
            exception_candidates=exceptions,
            budget=self._config.reread_budget,
        )

        if cards:
            session = self._session_manager.record_cards(
                session,
                lease,
                cards,
                usage_delta=ReadingSessionUsage(
                    processed_units=len(cards),
                    source_chars=sum(
                        card.unit_source_span.end_offset
                        - card.unit_source_span.start_offset
                        for card in cards
                    ),
                    wall_time_ms=max(1, _now_ms() - now_ms),
                ),
                now_ms=_next_ms(now_ms, 2),
            )

        digest = _source_grounded_digest(
            cards,
            max_chars=self._config.max_digest_chars,
        )

        if session.pending_unit_ids:
            session = self._session_manager.attach_artifacts(
                session,
                lease,
                coverage_map_id=coverage.coverage_map_id,
                reread_plan_id=remaining_reread_plan.reread_plan_id,
                now_ms=_next_ms(now_ms, 3),
            )
            session = self._session_manager.degrade(
                session,
                lease,
                reason_code="reader_product_incomplete_after_bounded_reread",
                now_ms=_next_ms(now_ms, 4),
            )
            warnings.append("global_synthesis_skipped_incomplete_reading")
            warnings.append("remaining_reread_work_requires_explicit_new_run")
            return ReaderProductResult(
                source=normalized,
                reading_plan=plan,
                cards=cards,
                exception_scans=scans,
                coverage_map=coverage,
                initial_reread_plan=initial_reread_plan,
                remaining_reread_plan=remaining_reread_plan,
                relations=None,
                session=session,
                synthesis=None,
                source_grounded_digest=digest,
                reader_attempts=reader_attempts,
                reread_attempts=reread_attempts,
                warnings=tuple(dict.fromkeys(warnings)),
            )

        relations = self._relation_builder.build(
            cards,
            evaluated_pairs=(),
            proposals=(),
        )
        session = self._session_manager.attach_artifacts(
            session,
            lease,
            coverage_map_id=coverage.coverage_map_id,
            reread_plan_id=remaining_reread_plan.reread_plan_id,
            relation_set_id=relations.relation_set_id,
            now_ms=_next_ms(now_ms, 3),
        )
        session = self._session_manager.complete(
            session,
            lease,
            now_ms=_next_ms(now_ms, 4),
        )

        synthesis = self._build_synthesis(
            session=session,
            coverage=coverage,
            relations=relations,
            cards=cards,
            exceptions=exceptions,
            digest=digest,
        )
        if remaining_reread_plan.tasks or remaining_reread_plan.deferred_items:
            warnings.append("bounded_reread_completed_with_remaining_advisory_work")
        warnings.append("synthesis_is_interpretation_candidate_not_truth")
        warnings.append("relation_detection_not_auto_inferred_in_product_v1")
        warnings.append("session_snapshot_is_in_memory_not_durable_resume_state")
        return ReaderProductResult(
            source=normalized,
            reading_plan=plan,
            cards=cards,
            exception_scans=scans,
            coverage_map=coverage,
            initial_reread_plan=initial_reread_plan,
            remaining_reread_plan=remaining_reread_plan,
            relations=relations,
            session=session,
            synthesis=synthesis,
            source_grounded_digest=digest,
            reader_attempts=reader_attempts,
            reread_attempts=reread_attempts,
            warnings=tuple(dict.fromkeys(warnings)),
        )

    async def _read_unit(
        self,
        source: RawSource,
        plan: HierarchicalSectionPlan,
        unit: ReadingUnit,
        *,
        mode: ReaderMode,
    ) -> tuple[SectionCard | None, str | None]:
        unit_source = RawSource(
            document_id=source.document_id,
            text=source.text[unit.start_offset : unit.end_offset],
            source_revision=source.source_revision,
        )
        try:
            result = await self._reader.extract(
                unit_source,
                mode=mode,
                budget=self._config.reader_budget,
            )
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as exc:
            return None, f"unit:{unit.unit_id}:reader_exception:{type(exc).__name__}"
        if not isinstance(result, ReaderResult):
            return None, f"unit:{unit.unit_id}:invalid_reader_result"
        if not result.accepted:
            code = result.failure.code if result.failure is not None else result.status.value
            return None, f"unit:{unit.unit_id}:reader_rejected:{code}"
        try:
            card = self._card_builder.build(
                source,
                unit,
                result,
                plan_id=plan.plan_id,
                coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
            )
        except SectionCardError as exc:
            return None, f"unit:{unit.unit_id}:card_rejected:{type(exc).__name__}"
        return card, None

    def _scan_cards(
        self,
        source: RawSource,
        cards: Iterable[SectionCard],
    ) -> tuple[ExceptionScanResult, ...]:
        return tuple(self._exception_scanner.scan(source, card) for card in cards)

    def _build_synthesis(
        self,
        *,
        session: ReadingSession,
        coverage: CoverageMap,
        relations: CrossSectionRelationSet,
        cards: tuple[SectionCard, ...],
        exceptions: tuple[CriticalExceptionCandidate, ...],
        digest: str,
    ) -> GlobalDocumentSynthesis:
        supporting_claim_ids = tuple(
            sorted(
                card_claim.claim.claim_id
                for card in cards
                for card_claim in card.claims
            )
        )
        if not supporting_claim_ids or not digest:
            raise ReaderProductPipelineError(
                "completed reading produced no source-grounded synthesis material"
            )
        proposal = SynthesisClaimProposal(
            proposal_key="source-grounded-digest",
            kind=SynthesisClaimKind.CENTRAL_THEME,
            text=digest,
            supporting_claim_ids=supporting_claim_ids,
            inference_reason=(
                "deterministic_ordered_rollup_of_source_grounded_section_essences"
            ),
        )
        return self._synthesis_builder.build(
            session,
            coverage,
            relations,
            cards=cards,
            exception_candidates=exceptions,
            claim_proposals=(proposal,),
            central_theme_proposal_key=proposal.proposal_key,
        )


def _normalize_source_revision(source: RawSource) -> RawSource:
    if source.source_revision is not None:
        return source
    digest = sha256(source.text.encode("utf-8")).hexdigest()
    return RawSource(
        document_id=source.document_id,
        text=source.text,
        source_revision=f"sha256:{digest}",
    )


def _default_session_key(source: RawSource, plan: HierarchicalSectionPlan) -> str:
    material = f"{source.document_id}\n{source.source_revision}\n{plan.plan_id}"
    return f"reader-product:{sha256(material.encode('utf-8')).hexdigest()}"


def _cards_in_plan_order(
    plan: HierarchicalSectionPlan,
    cards_by_unit: dict[str, SectionCard],
) -> tuple[SectionCard, ...]:
    return tuple(
        cards_by_unit[unit.unit_id]
        for unit in plan.units
        if unit.unit_id in cards_by_unit
    )


def _unit_by_id(plan: HierarchicalSectionPlan, unit_id: str) -> ReadingUnit:
    for unit in plan.units:
        if unit.unit_id == unit_id:
            return unit
    raise ReaderProductPipelineError(f"reread task references unknown unit: {unit_id}")


def _exception_candidates(
    scans: Iterable[ExceptionScanResult],
) -> tuple[CriticalExceptionCandidate, ...]:
    return tuple(candidate for scan in scans for candidate in scan.candidates)


def _source_grounded_digest(
    cards: Iterable[SectionCard],
    *,
    max_chars: int,
) -> str:
    parts: list[str] = []
    used = 0
    for card in cards:
        text = card.local_essence.strip()
        if not text:
            continue
        separator = "\n\n" if parts else ""
        available = max_chars - used - len(separator)
        if available <= 0:
            break
        if len(text) > available:
            text = text[:available].rstrip()
        if text:
            parts.append(text)
            used += len(separator) + len(text)
        if used >= max_chars:
            break
    return "\n\n".join(parts)


def _now_ms() -> int:
    return max(1, int(time.time() * 1000))


def _next_ms(base_ms: int, step: int) -> int:
    return max(_now_ms(), base_ms + step)


__all__ = [
    "ReaderProductConfig",
    "ReaderProductPipeline",
    "ReaderProductPipelineError",
    "ReaderProductResult",
]
