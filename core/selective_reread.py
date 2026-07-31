"""Deterministic selective reread planning for Reader Core PR-RDR-05.

The planner converts exact CoverageMap gaps, unsupported assets, and unresolved
exception-target candidates into a bounded, deduplicated proposal queue. It
schedules nothing, executes no Reader, and grants no Canon, memory, policy,
tool, TruthGate, or Write Gate authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from hashlib import sha256
from typing import Iterable

from core.critical_exceptions import CriticalExceptionCandidate
from core.hierarchical_section_planner import HierarchicalSectionPlan, ReadingUnit
from core.knowledge_capsule import SourceSpan
from core.reader_core_contracts import stable_reader_core_id
from core.reader_coverage import CoverageMap
from core.semantic_reader import RawSource, ReaderMode

SELECTIVE_REREAD_SCHEMA_VERSION = "reader-core.selective-reread.v1"


class SelectiveReReadError(ValueError):
    """Raised when reread inputs or queue invariants are inconsistent."""


class ReReadTrigger(str, Enum):
    MISSING_SECTION_CARD = "missing_section_card"
    CLAIM_PROVENANCE_MISSING = "claim_provenance_missing"
    EXCEPTION_SCAN_MISSING = "exception_scan_missing"
    PARTIAL_READER_RESULT = "partial_reader_result"
    UNRESOLVED_EXCEPTION_TARGET = "unresolved_exception_target"
    ATOMIC_ASSET_EXCEEDS_BUDGET = "atomic_asset_exceeds_budget"


class ReReadAction(str, Enum):
    READ_UNIT = "read_unit"
    DEEPEN_UNIT = "deepen_unit"
    RESCAN_EXCEPTIONS = "rescan_exceptions"
    RESOLVE_EXCEPTION_TARGET = "resolve_exception_target"
    INSPECT_ATOMIC_ASSET = "inspect_atomic_asset"


class ReReadPriority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class ReReadDeferralReason(str, Enum):
    TASK_CHAR_LIMIT = "task_char_limit"
    TOTAL_CHAR_LIMIT = "total_char_limit"
    TASK_COUNT_LIMIT = "task_count_limit"
    SECTION_TASK_LIMIT = "section_task_limit"


@dataclass(frozen=True, slots=True)
class SelectiveReReadBudget:
    max_tasks: int = 32
    max_total_chars: int = 100_000
    max_task_chars: int = 20_000
    max_tasks_per_section: int = 4

    def __post_init__(self) -> None:
        for name in (
            "max_tasks",
            "max_total_chars",
            "max_task_chars",
            "max_tasks_per_section",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise SelectiveReReadError(f"{name} must be a positive integer")
        if self.max_task_chars > self.max_total_chars:
            raise SelectiveReReadError(
                "max_task_chars cannot exceed max_total_chars"
            )


@dataclass(frozen=True, slots=True)
class ReReadTask:
    task_id: str
    document_id: str
    source_revision: str
    structure_map_id: str
    plan_id: str
    coverage_map_id: str
    unit_id: str
    section_id: str
    source_span: SourceSpan
    priority: ReReadPriority
    actions: tuple[ReReadAction, ...]
    trigger_codes: tuple[ReReadTrigger, ...]
    evidence_refs: tuple[str, ...]
    reader_mode: ReaderMode | None
    queue_index: int

    def __post_init__(self) -> None:
        _validate_common_item(self)
        if isinstance(self.queue_index, bool) or not isinstance(self.queue_index, int):
            raise SelectiveReReadError("queue_index must be an integer >= 0")
        if self.queue_index < 0:
            raise SelectiveReReadError("queue_index must be an integer >= 0")
        if self.task_id != _task_identity_from_item(self):
            raise SelectiveReReadError("task_id does not match reread task content")

    @property
    def char_count(self) -> int:
        return self.source_span.end_offset - self.source_span.start_offset


@dataclass(frozen=True, slots=True)
class DeferredReReadItem:
    item_id: str
    document_id: str
    source_revision: str
    structure_map_id: str
    plan_id: str
    coverage_map_id: str
    unit_id: str
    section_id: str
    source_span: SourceSpan
    priority: ReReadPriority
    actions: tuple[ReReadAction, ...]
    trigger_codes: tuple[ReReadTrigger, ...]
    evidence_refs: tuple[str, ...]
    reader_mode: ReaderMode | None
    deferral_reason: ReReadDeferralReason

    def __post_init__(self) -> None:
        _validate_common_item(self)
        if not isinstance(self.deferral_reason, ReReadDeferralReason):
            raise SelectiveReReadError(
                "deferral_reason must be a ReReadDeferralReason"
            )
        if self.item_id != _deferred_identity_from_item(self):
            raise SelectiveReReadError(
                "item_id does not match deferred item content"
            )


@dataclass(frozen=True, slots=True)
class SelectiveReReadPlan:
    reread_plan_id: str
    schema_version: str
    planner_version: str
    document_id: str
    source_revision: str
    structure_map_id: str
    plan_id: str
    coverage_map_id: str
    budget: SelectiveReReadBudget
    tasks: tuple[ReReadTask, ...]
    deferred_items: tuple[DeferredReReadItem, ...]
    triggered_unit_ids: tuple[str, ...]
    total_queued_chars: int
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "reread_plan_id",
            "schema_version",
            "planner_version",
            "document_id",
            "source_revision",
            "structure_map_id",
            "plan_id",
            "coverage_map_id",
        ):
            _require_text(getattr(self, name), name)
        if self.schema_version != SELECTIVE_REREAD_SCHEMA_VERSION:
            raise SelectiveReReadError(
                "unsupported SelectiveReReadPlan schema_version"
            )
        if not isinstance(self.budget, SelectiveReReadBudget):
            raise SelectiveReReadError("budget must be a SelectiveReReadBudget")

        tasks = tuple(self.tasks)
        deferred = tuple(self.deferred_items)
        if any(not isinstance(item, ReReadTask) for item in tasks):
            raise SelectiveReReadError("tasks must contain ReReadTask values")
        if any(not isinstance(item, DeferredReReadItem) for item in deferred):
            raise SelectiveReReadError(
                "deferred_items must contain DeferredReReadItem values"
            )
        if tuple(task.queue_index for task in tasks) != tuple(range(len(tasks))):
            raise SelectiveReReadError(
                "task queue_index values must be consecutive from zero"
            )
        if len({task.task_id for task in tasks}) != len(tasks):
            raise SelectiveReReadError("task IDs must be unique")
        if len({task.unit_id for task in tasks}) != len(tasks):
            raise SelectiveReReadError(
                "the queue may contain at most one task per unit"
            )
        if len({item.item_id for item in deferred}) != len(deferred):
            raise SelectiveReReadError("deferred item IDs must be unique")
        if len({item.unit_id for item in deferred}) != len(deferred):
            raise SelectiveReReadError(
                "deferred_items may contain at most one item per unit"
            )
        for task in tasks:
            self._validate_item_identity(task)
        for item in deferred:
            self._validate_item_identity(item)
        if {task.unit_id for task in tasks} & {item.unit_id for item in deferred}:
            raise SelectiveReReadError(
                "a unit cannot be both queued and deferred"
            )

        triggered = _unique_text_tuple(
            self.triggered_unit_ids,
            "triggered_unit_id",
        )
        task_keys = tuple(
            (task.priority, task.source_span.start_offset, task.unit_id)
            for task in tasks
        )
        deferred_keys = tuple(
            (item.priority, item.source_span.start_offset, item.unit_id)
            for item in deferred
        )
        expected_triggered = tuple(
            unit_id
            for _, _, unit_id in sorted((*task_keys, *deferred_keys))
        )
        if triggered != expected_triggered:
            raise SelectiveReReadError(
                "triggered_unit_ids must follow canonical priority/source order"
            )

        calculated_chars = sum(task.char_count for task in tasks)
        if self.total_queued_chars != calculated_chars:
            raise SelectiveReReadError(
                "total_queued_chars must equal queued task source lengths"
            )
        if len(tasks) > self.budget.max_tasks:
            raise SelectiveReReadError("queued tasks exceed max_tasks")
        if calculated_chars > self.budget.max_total_chars:
            raise SelectiveReReadError(
                "queued source characters exceed max_total_chars"
            )
        section_counts: dict[str, int] = {}
        for task in tasks:
            if task.char_count > self.budget.max_task_chars:
                raise SelectiveReReadError("queued task exceeds max_task_chars")
            section_counts[task.section_id] = section_counts.get(task.section_id, 0) + 1
        if any(
            count > self.budget.max_tasks_per_section
            for count in section_counts.values()
        ):
            raise SelectiveReReadError(
                "queued tasks exceed max_tasks_per_section"
            )

        warnings = _unique_text_tuple(self.warnings, "warning")
        object.__setattr__(self, "tasks", tasks)
        object.__setattr__(self, "deferred_items", deferred)
        object.__setattr__(self, "triggered_unit_ids", triggered)
        object.__setattr__(self, "warnings", warnings)
        if self.reread_plan_id != _plan_identity(self):
            raise SelectiveReReadError(
                "reread_plan_id does not match plan content"
            )

    def _validate_item_identity(
        self,
        item: ReReadTask | DeferredReReadItem,
    ) -> None:
        if (
            item.document_id != self.document_id
            or item.source_revision != self.source_revision
            or item.structure_map_id != self.structure_map_id
            or item.plan_id != self.plan_id
            or item.coverage_map_id != self.coverage_map_id
        ):
            raise SelectiveReReadError(
                "every task and deferred item must match its reread plan"
            )


@dataclass(frozen=True, slots=True)
class _TriggerEvidence:
    trigger: ReReadTrigger
    action: ReReadAction
    priority: ReReadPriority
    evidence_ref: str


@dataclass(frozen=True, slots=True)
class _TaskProposal:
    unit: ReadingUnit
    priority: ReReadPriority
    actions: tuple[ReReadAction, ...]
    triggers: tuple[ReReadTrigger, ...]
    evidence_refs: tuple[str, ...]
    reader_mode: ReaderMode | None


_REASON_RULES: dict[str, tuple[ReReadTrigger, ReReadAction, ReReadPriority]] = {
    "missing_section_card": (
        ReReadTrigger.MISSING_SECTION_CARD,
        ReReadAction.READ_UNIT,
        ReReadPriority.HIGH,
    ),
    "unread_unit_has_no_claim_provenance": (
        ReReadTrigger.CLAIM_PROVENANCE_MISSING,
        ReReadAction.READ_UNIT,
        ReReadPriority.HIGH,
    ),
    "exception_scan_missing": (
        ReReadTrigger.EXCEPTION_SCAN_MISSING,
        ReReadAction.RESCAN_EXCEPTIONS,
        ReReadPriority.NORMAL,
    ),
    "partial_reader_result": (
        ReReadTrigger.PARTIAL_READER_RESULT,
        ReReadAction.DEEPEN_UNIT,
        ReReadPriority.HIGH,
    ),
}
_ACTION_ORDER = tuple(ReReadAction)
_TRIGGER_ORDER = tuple(ReReadTrigger)


class SelectiveReReadPlanner:
    planner_version = "1.1.1"

    def plan(
        self,
        source: RawSource,
        reading_plan: HierarchicalSectionPlan,
        coverage_map: CoverageMap,
        *,
        exception_candidates: Iterable[CriticalExceptionCandidate] = (),
        budget: SelectiveReReadBudget | None = None,
    ) -> SelectiveReReadPlan:
        resolved_budget = budget or SelectiveReReadBudget()
        self._validate_inputs(source, reading_plan, coverage_map)
        units_by_id = {unit.unit_id: unit for unit in reading_plan.units}
        candidates = self._validate_candidates(
            source,
            coverage_map,
            tuple(exception_candidates),
            units_by_id=units_by_id,
        )
        evidence = self._collect_evidence(
            coverage_map,
            candidates,
            units_by_id=units_by_id,
        )
        proposals = self._proposals(reading_plan, evidence_by_unit=evidence)
        tasks, deferred = self._apply_budget(
            proposals,
            coverage_map=coverage_map,
            budget=resolved_budget,
        )
        triggered = tuple(proposal.unit.unit_id for proposal in proposals)
        warnings: list[str] = []
        if not proposals:
            warnings.append("no_reread_triggers")
        if deferred:
            warnings.append("reread_work_deferred_by_budget")
        total_chars = sum(task.char_count for task in tasks)
        draft = SelectiveReReadPlan(
            reread_plan_id="pending",
            schema_version=SELECTIVE_REREAD_SCHEMA_VERSION,
            planner_version=self.planner_version,
            document_id=reading_plan.document_id,
            source_revision=reading_plan.source_revision,
            structure_map_id=reading_plan.structure_map_id,
            plan_id=reading_plan.plan_id,
            coverage_map_id=coverage_map.coverage_map_id,
            budget=resolved_budget,
            tasks=tasks,
            deferred_items=deferred,
            triggered_unit_ids=triggered,
            total_queued_chars=total_chars,
            warnings=tuple(warnings),
        )
        return SelectiveReReadPlan(
            **{
                **draft.__dict__,
                "reread_plan_id": _plan_identity(draft),
            }
        )

    @staticmethod
    def _validate_inputs(
        source: RawSource,
        reading_plan: HierarchicalSectionPlan,
        coverage_map: CoverageMap,
    ) -> None:
        if not isinstance(source, RawSource):
            raise SelectiveReReadError("source must be a RawSource")
        if not isinstance(reading_plan, HierarchicalSectionPlan):
            raise SelectiveReReadError(
                "reading_plan must be a HierarchicalSectionPlan"
            )
        if not isinstance(coverage_map, CoverageMap):
            raise SelectiveReReadError("coverage_map must be a CoverageMap")
        source_revision = source.source_revision
        if source_revision is None:
            digest = sha256(source.text.encode("utf-8")).hexdigest()
            source_revision = f"sha256:{digest}"
        if source.document_id != reading_plan.document_id:
            raise SelectiveReReadError(
                "source document_id must match reading plan"
            )
        if source_revision != reading_plan.source_revision:
            raise SelectiveReReadError("source revision must match reading plan")
        if (
            coverage_map.document_id != reading_plan.document_id
            or coverage_map.source_revision != reading_plan.source_revision
            or coverage_map.structure_map_id != reading_plan.structure_map_id
            or coverage_map.plan_id != reading_plan.plan_id
        ):
            raise SelectiveReReadError(
                "CoverageMap must match reading plan identity"
            )
        for unit in reading_plan.units:
            if not unit.source_span.verify(source.text):
                raise SelectiveReReadError(
                    "every reading unit span must verify against source"
                )

    @staticmethod
    def _validate_candidates(
        source: RawSource,
        coverage_map: CoverageMap,
        candidates: tuple[CriticalExceptionCandidate, ...],
        *,
        units_by_id: dict[str, ReadingUnit],
    ) -> tuple[CriticalExceptionCandidate, ...]:
        by_id: dict[str, CriticalExceptionCandidate] = {}
        for candidate in candidates:
            if not isinstance(candidate, CriticalExceptionCandidate):
                raise SelectiveReReadError(
                    "exception_candidates must contain CriticalExceptionCandidate values"
                )
            if candidate.candidate_id in by_id:
                raise SelectiveReReadError(
                    "exception candidate IDs must be unique"
                )
            unit = units_by_id.get(candidate.unit_id)
            if unit is None:
                raise SelectiveReReadError(
                    "exception candidate must reference a reading-plan unit"
                )
            if (
                candidate.document_id != coverage_map.document_id
                or candidate.source_revision != coverage_map.source_revision
                or candidate.section_id != unit.section_id
            ):
                raise SelectiveReReadError(
                    "exception candidate must match coverage and unit identity"
                )
            if (
                candidate.statement_span.start_offset < unit.start_offset
                or candidate.statement_span.end_offset > unit.end_offset
            ):
                raise SelectiveReReadError(
                    "candidate statement_span must fit inside its unit"
                )
            if not candidate.trigger_span.verify(source.text):
                raise SelectiveReReadError(
                    "candidate trigger_span must verify against source"
                )
            if not candidate.statement_span.verify(source.text):
                raise SelectiveReReadError(
                    "candidate statement_span must verify against source"
                )
            by_id[candidate.candidate_id] = candidate
        if set(by_id) != set(coverage_map.exception_candidate_ids):
            raise SelectiveReReadError(
                "exception_candidates must exactly match CoverageMap candidate IDs"
            )
        return tuple(by_id[item_id] for item_id in coverage_map.exception_candidate_ids)

    @staticmethod
    def _collect_evidence(
        coverage_map: CoverageMap,
        candidates: tuple[CriticalExceptionCandidate, ...],
        *,
        units_by_id: dict[str, ReadingUnit],
    ) -> dict[str, list[_TriggerEvidence]]:
        result: dict[str, list[_TriggerEvidence]] = {}
        for region in coverage_map.unresolved_regions:
            if region.unit_id not in units_by_id:
                raise SelectiveReReadError(
                    "unresolved coverage region must reference a plan unit"
                )
            rule = _REASON_RULES.get(region.reason_code)
            if rule is None:
                raise SelectiveReReadError(
                    f"unsupported unresolved coverage reason_code: {region.reason_code}"
                )
            trigger, action, priority = rule
            result.setdefault(region.unit_id, []).append(
                _TriggerEvidence(trigger, action, priority, region.region_id)
            )
        for asset in coverage_map.unsupported_assets:
            if asset.unit_id not in units_by_id:
                raise SelectiveReReadError(
                    "unsupported asset must reference a plan unit"
                )
            result.setdefault(asset.unit_id, []).append(
                _TriggerEvidence(
                    ReReadTrigger.ATOMIC_ASSET_EXCEEDS_BUDGET,
                    ReReadAction.INSPECT_ATOMIC_ASSET,
                    ReReadPriority.CRITICAL,
                    asset.asset_id,
                )
            )
        for candidate in candidates:
            if not candidate.target_claim_refs:
                result.setdefault(candidate.unit_id, []).append(
                    _TriggerEvidence(
                        ReReadTrigger.UNRESOLVED_EXCEPTION_TARGET,
                        ReReadAction.RESOLVE_EXCEPTION_TARGET,
                        ReReadPriority.CRITICAL,
                        candidate.candidate_id,
                    )
                )
        return result

    @staticmethod
    def _proposals(
        reading_plan: HierarchicalSectionPlan,
        *,
        evidence_by_unit: dict[str, list[_TriggerEvidence]],
    ) -> tuple[_TaskProposal, ...]:
        proposals: list[_TaskProposal] = []
        for unit in reading_plan.units:
            evidence = evidence_by_unit.get(unit.unit_id)
            if not evidence:
                continue
            actions = tuple(
                action
                for action in _ACTION_ORDER
                if any(item.action is action for item in evidence)
            )
            triggers = tuple(
                trigger
                for trigger in _TRIGGER_ORDER
                if any(item.trigger is trigger for item in evidence)
            )
            proposals.append(
                _TaskProposal(
                    unit=unit,
                    priority=min(item.priority for item in evidence),
                    actions=actions,
                    triggers=triggers,
                    evidence_refs=tuple(
                        dict.fromkeys(item.evidence_ref for item in evidence)
                    ),
                    reader_mode=_reader_mode_for_actions(actions),
                )
            )
        return tuple(
            sorted(proposals, key=lambda item: (item.priority, item.unit.order_index))
        )

    @staticmethod
    def _apply_budget(
        proposals: tuple[_TaskProposal, ...],
        *,
        coverage_map: CoverageMap,
        budget: SelectiveReReadBudget,
    ) -> tuple[tuple[ReReadTask, ...], tuple[DeferredReReadItem, ...]]:
        tasks: list[ReReadTask] = []
        deferred: list[DeferredReReadItem] = []
        total_chars = 0
        section_counts: dict[str, int] = {}
        for proposal in proposals:
            reason: ReReadDeferralReason | None = None
            char_count = proposal.unit.char_count
            if char_count > budget.max_task_chars:
                reason = ReReadDeferralReason.TASK_CHAR_LIMIT
            elif len(tasks) >= budget.max_tasks:
                reason = ReReadDeferralReason.TASK_COUNT_LIMIT
            elif section_counts.get(proposal.unit.section_id, 0) >= budget.max_tasks_per_section:
                reason = ReReadDeferralReason.SECTION_TASK_LIMIT
            elif total_chars + char_count > budget.max_total_chars:
                reason = ReReadDeferralReason.TOTAL_CHAR_LIMIT

            common = dict(
                document_id=coverage_map.document_id,
                source_revision=coverage_map.source_revision,
                structure_map_id=coverage_map.structure_map_id,
                plan_id=coverage_map.plan_id,
                coverage_map_id=coverage_map.coverage_map_id,
                unit_id=proposal.unit.unit_id,
                section_id=proposal.unit.section_id,
                source_span=proposal.unit.source_span,
                priority=proposal.priority,
                actions=proposal.actions,
                trigger_codes=proposal.triggers,
                evidence_refs=proposal.evidence_refs,
                reader_mode=proposal.reader_mode,
            )
            if reason is not None:
                deferred.append(
                    DeferredReReadItem(
                        item_id=_deferred_identity(**common, deferral_reason=reason),
                        deferral_reason=reason,
                        **common,
                    )
                )
                continue
            tasks.append(
                ReReadTask(
                    task_id=_task_identity(**common),
                    queue_index=len(tasks),
                    **common,
                )
            )
            total_chars += char_count
            section_counts[proposal.unit.section_id] = (
                section_counts.get(proposal.unit.section_id, 0) + 1
            )
        return tuple(tasks), tuple(deferred)


def _validate_common_item(item: ReReadTask | DeferredReReadItem) -> None:
    for name in (
        "document_id",
        "source_revision",
        "structure_map_id",
        "plan_id",
        "coverage_map_id",
        "unit_id",
        "section_id",
    ):
        _require_text(getattr(item, name), name)
    if not isinstance(item.source_span, SourceSpan):
        raise SelectiveReReadError("source_span must be a SourceSpan")
    if item.source_span.document_id != item.document_id:
        raise SelectiveReReadError("source_span document_id must match item")
    if item.source_span.source_revision != item.source_revision:
        raise SelectiveReReadError("source_span source_revision must match item")
    if item.source_span.span_id != item.unit_id:
        raise SelectiveReReadError("source_span span_id must equal unit_id")
    if not isinstance(item.priority, ReReadPriority):
        raise SelectiveReReadError("priority must be a ReReadPriority")
    actions = _action_tuple(item.actions)
    triggers = _trigger_tuple(item.trigger_codes)
    refs = _unique_text_tuple(item.evidence_refs, "evidence_ref")
    if not refs:
        raise SelectiveReReadError(
            "a reread item requires at least one evidence reference"
        )
    object.__setattr__(item, "actions", actions)
    object.__setattr__(item, "trigger_codes", triggers)
    object.__setattr__(item, "evidence_refs", refs)
    _validate_reader_mode(actions, item.reader_mode)


def _reader_mode_for_actions(actions: tuple[ReReadAction, ...]) -> ReaderMode | None:
    if ReReadAction.DEEPEN_UNIT in actions:
        return ReaderMode.DEEP
    if ReReadAction.READ_UNIT in actions:
        return ReaderMode.STANDARD
    return None


def _validate_reader_mode(
    actions: tuple[ReReadAction, ...],
    reader_mode: ReaderMode | None,
) -> None:
    if reader_mode is not None and not isinstance(reader_mode, ReaderMode):
        raise SelectiveReReadError("reader_mode must be a ReaderMode or None")
    if reader_mode != _reader_mode_for_actions(actions):
        raise SelectiveReReadError(
            "reader_mode must match semantic reread actions"
        )


def _task_identity_from_item(item: ReReadTask) -> str:
    return _task_identity(
        document_id=item.document_id,
        source_revision=item.source_revision,
        structure_map_id=item.structure_map_id,
        plan_id=item.plan_id,
        coverage_map_id=item.coverage_map_id,
        unit_id=item.unit_id,
        section_id=item.section_id,
        source_span=item.source_span,
        priority=item.priority,
        actions=item.actions,
        trigger_codes=item.trigger_codes,
        evidence_refs=item.evidence_refs,
        reader_mode=item.reader_mode,
    )


def _deferred_identity_from_item(item: DeferredReReadItem) -> str:
    return _deferred_identity(
        document_id=item.document_id,
        source_revision=item.source_revision,
        structure_map_id=item.structure_map_id,
        plan_id=item.plan_id,
        coverage_map_id=item.coverage_map_id,
        unit_id=item.unit_id,
        section_id=item.section_id,
        source_span=item.source_span,
        priority=item.priority,
        actions=item.actions,
        trigger_codes=item.trigger_codes,
        evidence_refs=item.evidence_refs,
        reader_mode=item.reader_mode,
        deferral_reason=item.deferral_reason,
    )


def _task_identity(**values: object) -> str:
    return _item_identity("selective-reread-task", values)


def _deferred_identity(**values: object) -> str:
    return _item_identity("deferred-selective-reread-item", values)


def _item_identity(kind: str, values: dict[str, object]) -> str:
    span = values["source_span"]
    priority = values["priority"]
    actions = values["actions"]
    triggers = values["trigger_codes"]
    refs = values["evidence_refs"]
    reader_mode = values["reader_mode"]
    if not isinstance(span, SourceSpan) or not isinstance(priority, ReReadPriority):
        raise SelectiveReReadError("invalid reread identity values")
    if not isinstance(actions, tuple) or not isinstance(triggers, tuple):
        raise SelectiveReReadError("invalid reread identity values")
    if not isinstance(refs, tuple):
        raise SelectiveReReadError("invalid reread identity values")
    payload = {
        "document_id": values["document_id"],
        "source_revision": values["source_revision"],
        "structure_map_id": values["structure_map_id"],
        "plan_id": values["plan_id"],
        "coverage_map_id": values["coverage_map_id"],
        "unit_id": values["unit_id"],
        "section_id": values["section_id"],
        "source_span": span.identity_payload(),
        "priority": int(priority),
        "actions": [item.value for item in actions if isinstance(item, ReReadAction)],
        "trigger_codes": [
            item.value for item in triggers if isinstance(item, ReReadTrigger)
        ],
        "evidence_refs": list(refs),
        "reader_mode": reader_mode.value if isinstance(reader_mode, ReaderMode) else None,
    }
    reason = values.get("deferral_reason")
    if isinstance(reason, ReReadDeferralReason):
        payload["deferral_reason"] = reason.value
    return stable_reader_core_id(kind, payload)


def _plan_identity(plan: SelectiveReReadPlan) -> str:
    return stable_reader_core_id(
        "selective-reread-plan",
        {
            "schema_version": plan.schema_version,
            "planner_version": plan.planner_version,
            "document_id": plan.document_id,
            "source_revision": plan.source_revision,
            "structure_map_id": plan.structure_map_id,
            "plan_id": plan.plan_id,
            "coverage_map_id": plan.coverage_map_id,
            "budget": {
                "max_tasks": plan.budget.max_tasks,
                "max_total_chars": plan.budget.max_total_chars,
                "max_task_chars": plan.budget.max_task_chars,
                "max_tasks_per_section": plan.budget.max_tasks_per_section,
            },
            "task_ids": [task.task_id for task in plan.tasks],
            "deferred_item_ids": [item.item_id for item in plan.deferred_items],
            "triggered_unit_ids": list(plan.triggered_unit_ids),
            "total_queued_chars": plan.total_queued_chars,
            "warnings": list(plan.warnings),
        },
    )


def _action_tuple(values: Iterable[ReReadAction]) -> tuple[ReReadAction, ...]:
    result = tuple(values)
    if not result or any(not isinstance(value, ReReadAction) for value in result):
        raise SelectiveReReadError("action values must belong to ReReadAction")
    canonical = tuple(action for action in _ACTION_ORDER if action in result)
    if result != canonical or len(set(result)) != len(result):
        raise SelectiveReReadError(
            "action values must be unique and use canonical enum order"
        )
    return result


def _trigger_tuple(values: Iterable[ReReadTrigger]) -> tuple[ReReadTrigger, ...]:
    result = tuple(values)
    if not result or any(not isinstance(value, ReReadTrigger) for value in result):
        raise SelectiveReReadError(
            "trigger_code values must belong to ReReadTrigger"
        )
    canonical = tuple(trigger for trigger in _TRIGGER_ORDER if trigger in result)
    if result != canonical or len(set(result)) != len(result):
        raise SelectiveReReadError(
            "trigger_code values must be unique and use canonical enum order"
        )
    return result


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SelectiveReReadError(f"{field_name} must be a non-empty string")
    return value


def _unique_text_tuple(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    if len(set(result)) != len(result):
        raise SelectiveReReadError(f"{field_name} values must be unique")
    return result


__all__ = [
    "DeferredReReadItem",
    "ReReadAction",
    "ReReadDeferralReason",
    "ReReadPriority",
    "ReReadTask",
    "ReReadTrigger",
    "SELECTIVE_REREAD_SCHEMA_VERSION",
    "SelectiveReReadBudget",
    "SelectiveReReadError",
    "SelectiveReReadPlan",
    "SelectiveReReadPlanner",
]
