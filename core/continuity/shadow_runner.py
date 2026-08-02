"""Disabled-by-default orchestration for the complete Milestone 1 shadow path.

The runner composes existing continuity, working-memory, context, compute,
evaluation, and advisory components. It has no answer, persistence, Canon,
network, tool, or action interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from hashlib import sha256
import json
import math
from typing import Iterable, TypeVar

from core.compute_controller import (
    ComputeDecision,
    ContinuityComputeSignals,
    decide_compute_path,
)
from core.context_pack import ContextPack, ContextPackBudget, ContextPackBuilder
from core.working_memory_gate import (
    WorkingMemoryBudget,
    WorkingMemoryGate,
    WorkingMemoryPlan,
)

from .advisory_shadow import (
    AdvisoryShadowGate,
    AdvisoryShadowRequest,
    AdvisoryShadowResult,
    AdvisorySignal,
    AdvisorySignalKind,
)
from .context_pack import ContinuityAssemblyResult, ContinuityContextAssembler
from .contracts import AssertionRecord, AssertionRelation
from .conversation_bridge import ConversationEpisode
from .evaluation import (
    ReplayEvaluationReport,
    ShadowRunSnapshot,
    ShadowSafetyObservation,
)
from .goal_open_loop import (
    GoalAttestation,
    GoalProjection,
    GoalProjectionResult,
    GoalProjector,
    GoalRecordSnapshot,
    OpenLoopProjection,
    OpenLoopProjectionResult,
    OpenLoopProjector,
    OpenLoopResolution,
    OpenLoopSignal,
)
from .projection_working_memory_adapter import (
    ProjectionGatePolicy,
    ProjectionWorkingMemoryAdapter,
    ProjectionWorkingMemoryBatch,
)
from .state_reconciler import (
    CurrentStateProjection,
    StateReconciler,
    StateReconciliationResult,
)
from .thread_weaver import ThreadWeaveResult, ThreadWeaver
from .working_memory_adapter import (
    ContinuityItemGatePolicy,
    ContinuityWorkingMemoryAdapter,
    ContinuityWorkingMemoryBatch,
)

SHADOW_RUNNER_SCHEMA_VERSION = "continuity.complete_shadow_runner.v1"
SHADOW_RUNNER_POLICY_VERSION = "continuity.complete_shadow_runner.policy.v1"

_T = TypeVar("_T")


class CompleteShadowRunnerError(ValueError):
    """The complete shadow runner received an invalid or ambiguous input."""


class ShadowRunnerStatus(str, Enum):
    DISABLED = "disabled"
    COMPLETED = "completed"


class ShadowRunnerReason(str, Enum):
    FEATURE_DISABLED = "feature_disabled"
    BASELINE_COMPLETED = "baseline_completed"
    REPLAY_COMPLETED = "replay_completed"
    REPLAY_EVALUATED = "replay_evaluated"
    MAIN_ANSWER_UNTOUCHED = "main_answer_untouched"
    CANON_UNCHANGED = "canon_unchanged"
    ADVISORY_SHADOW_ONLY = "advisory_shadow_only"


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CompleteShadowRunnerError(f"{name} must be a non-empty string")
    return value.strip()


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise CompleteShadowRunnerError(f"{name} must be a bool")
    return value


def _score(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CompleteShadowRunnerError(f"{name} must be a finite number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise CompleteShadowRunnerError(f"{name} must be a finite number in [0, 1]")
    return result


def _aware(value: object, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise CompleteShadowRunnerError(f"{name} must be timezone-aware")
    return value


def _ordered(values: Iterable[_T], *, reverse: bool) -> tuple[_T, ...]:
    items = tuple(values)
    return tuple(reversed(items)) if reverse else items


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(payload: object) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ShadowRunnerConfig:
    enabled: bool = False
    scenario_id: str = "titan-milestone-1-shadow"
    policy_version: str = SHADOW_RUNNER_POLICY_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", _strict_bool(self.enabled, "enabled"))
        object.__setattr__(
            self,
            "scenario_id",
            _text(self.scenario_id, "scenario_id"),
        )
        object.__setattr__(
            self,
            "policy_version",
            _text(self.policy_version, "policy_version"),
        )


@dataclass(frozen=True, slots=True)
class ShadowGatePolicyTemplate:
    """Explicit caller policy copied into scoped Gate policy records."""

    attention_score: float = 0.8
    recall_allowed: bool = True
    eligible: bool = True
    restricted: bool = False
    erased: bool = False
    protected: bool = False
    conflict: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "attention_score",
            _score(self.attention_score, "attention_score"),
        )
        for name in (
            "recall_allowed",
            "eligible",
            "restricted",
            "erased",
            "protected",
            "conflict",
        ):
            object.__setattr__(
                self,
                name,
                _strict_bool(getattr(self, name), name),
            )

    def for_continuity_item(self, item_id: str) -> ContinuityItemGatePolicy:
        return ContinuityItemGatePolicy(
            item_id=_text(item_id, "item_id"),
            attention_score=self.attention_score,
            recall_allowed=self.recall_allowed,
            eligible=self.eligible,
            restricted=self.restricted,
            erased=self.erased,
            protected=self.protected,
            conflict=self.conflict,
        )

    def for_projection(self, projection_id: str) -> ProjectionGatePolicy:
        return ProjectionGatePolicy(
            projection_id=_text(projection_id, "projection_id"),
            attention_score=self.attention_score,
            recall_allowed=self.recall_allowed,
            eligible=self.eligible,
            restricted=self.restricted,
            erased=self.erased,
            protected=self.protected,
            conflict=self.conflict,
        )


@dataclass(frozen=True, slots=True)
class AdvisoryIntent:
    """Explicit relevance signal resolved only after projections exist."""

    kind: AdvisorySignalKind
    target_ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AdvisorySignalKind):
            raise CompleteShadowRunnerError(
                "kind must be an AdvisorySignalKind"
            )
        object.__setattr__(
            self,
            "target_ref",
            _text(self.target_ref, "target_ref"),
        )


@dataclass(frozen=True, slots=True)
class CompleteShadowRunInput:
    request_ref: str
    query: str
    current_episode: ConversationEpisode
    episodes: tuple[ConversationEpisode, ...]
    as_of: datetime
    advisory_request: AdvisoryShadowRequest
    state_assertions: tuple[AssertionRecord, ...] = ()
    state_relations: tuple[AssertionRelation, ...] = ()
    goal_snapshots: tuple[GoalRecordSnapshot, ...] = ()
    goal_attestations: tuple[GoalAttestation, ...] = ()
    open_loop_signals: tuple[OpenLoopSignal, ...] = ()
    open_loop_resolutions: tuple[OpenLoopResolution, ...] = ()
    advisory_intents: tuple[AdvisoryIntent, ...] = ()
    gate_policy: ShadowGatePolicyTemplate = field(
        default_factory=ShadowGatePolicyTemplate
    )
    working_memory_budget: WorkingMemoryBudget = field(
        default_factory=WorkingMemoryBudget
    )
    context_pack_budget: ContextPackBudget = field(
        default_factory=ContextPackBudget
    )
    compute_signals: ContinuityComputeSignals = field(
        default_factory=ContinuityComputeSignals
    )
    observation: ShadowSafetyObservation = field(
        default_factory=ShadowSafetyObservation
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "request_ref",
            _text(self.request_ref, "request_ref"),
        )
        object.__setattr__(self, "query", _text(self.query, "query"))
        object.__setattr__(self, "as_of", _aware(self.as_of, "as_of"))
        if not isinstance(self.current_episode, ConversationEpisode):
            raise CompleteShadowRunnerError(
                "current_episode must be a ConversationEpisode"
            )
        episodes = tuple(self.episodes)
        if not episodes or any(
            not isinstance(value, ConversationEpisode) for value in episodes
        ):
            raise CompleteShadowRunnerError(
                "episodes must contain ConversationEpisode values"
            )
        if self.current_episode not in episodes:
            raise CompleteShadowRunnerError(
                "current_episode must be present in episodes"
            )
        object.__setattr__(self, "episodes", episodes)
        if not isinstance(self.advisory_request, AdvisoryShadowRequest):
            raise CompleteShadowRunnerError(
                "advisory_request must be AdvisoryShadowRequest"
            )
        if self.advisory_request.request_ref != self.request_ref:
            raise CompleteShadowRunnerError(
                "advisory_request.request_ref must match request_ref"
            )
        for name in (
            "state_assertions",
            "state_relations",
            "goal_snapshots",
            "goal_attestations",
            "open_loop_signals",
            "open_loop_resolutions",
            "advisory_intents",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        if not isinstance(self.gate_policy, ShadowGatePolicyTemplate):
            raise CompleteShadowRunnerError(
                "gate_policy must be ShadowGatePolicyTemplate"
            )
        if not isinstance(self.working_memory_budget, WorkingMemoryBudget):
            raise CompleteShadowRunnerError(
                "working_memory_budget must be WorkingMemoryBudget"
            )
        if not isinstance(self.context_pack_budget, ContextPackBudget):
            raise CompleteShadowRunnerError(
                "context_pack_budget must be ContextPackBudget"
            )
        if not isinstance(self.compute_signals, ContinuityComputeSignals):
            raise CompleteShadowRunnerError(
                "compute_signals must be ContinuityComputeSignals"
            )
        if not isinstance(self.observation, ShadowSafetyObservation):
            raise CompleteShadowRunnerError(
                "observation must be ShadowSafetyObservation"
            )


@dataclass(frozen=True, slots=True)
class ShadowPassArtifacts:
    weave_result: ThreadWeaveResult
    continuity_result: ContinuityAssemblyResult
    state_result: StateReconciliationResult
    goal_result: GoalProjectionResult
    open_loop_result: OpenLoopProjectionResult
    continuity_batch: ContinuityWorkingMemoryBatch
    projection_batch: ProjectionWorkingMemoryBatch
    working_memory_plan: WorkingMemoryPlan
    context_pack: ContextPack
    compute_decision: ComputeDecision
    snapshot: ShadowRunSnapshot


@dataclass(frozen=True, slots=True)
class CompleteShadowRunReceipt:
    receipt_id: str
    schema_version: str
    policy_version: str
    status: ShadowRunnerStatus
    scenario_id: str
    request_ref: str | None
    baseline_snapshot_id: str | None
    replay_snapshot_id: str | None
    evaluation_report_id: str | None
    advisory_result_id: str | None
    reason_codes: tuple[ShadowRunnerReason, ...]

    @classmethod
    def create(
        cls,
        *,
        policy_version: str,
        status: ShadowRunnerStatus,
        scenario_id: str,
        request_ref: str | None,
        baseline_snapshot_id: str | None,
        replay_snapshot_id: str | None,
        evaluation_report_id: str | None,
        advisory_result_id: str | None,
        reason_codes: Iterable[ShadowRunnerReason],
    ) -> "CompleteShadowRunReceipt":
        if not isinstance(status, ShadowRunnerStatus):
            raise CompleteShadowRunnerError(
                "status must be a ShadowRunnerStatus"
            )
        policy = _text(policy_version, "policy_version")
        scenario = _text(scenario_id, "scenario_id")
        request = (
            _text(request_ref, "request_ref")
            if request_ref is not None
            else None
        )
        baseline_id = (
            _text(baseline_snapshot_id, "baseline_snapshot_id")
            if baseline_snapshot_id is not None
            else None
        )
        replay_id = (
            _text(replay_snapshot_id, "replay_snapshot_id")
            if replay_snapshot_id is not None
            else None
        )
        report_id = (
            _text(evaluation_report_id, "evaluation_report_id")
            if evaluation_report_id is not None
            else None
        )
        advisory_id = (
            _text(advisory_result_id, "advisory_result_id")
            if advisory_result_id is not None
            else None
        )
        reasons = tuple(sorted(set(reason_codes), key=lambda value: value.value))
        if not reasons or any(
            not isinstance(value, ShadowRunnerReason) for value in reasons
        ):
            raise CompleteShadowRunnerError(
                "reason_codes must contain ShadowRunnerReason values"
            )
        boundary_reasons = {
            ShadowRunnerReason.MAIN_ANSWER_UNTOUCHED,
            ShadowRunnerReason.CANON_UNCHANGED,
            ShadowRunnerReason.ADVISORY_SHADOW_ONLY,
        }
        if not boundary_reasons.issubset(reasons):
            raise CompleteShadowRunnerError(
                "receipt must preserve all shadow boundary reasons"
            )
        if status is ShadowRunnerStatus.DISABLED:
            if any(
                value is not None
                for value in (
                    request,
                    baseline_id,
                    replay_id,
                    report_id,
                    advisory_id,
                )
            ):
                raise CompleteShadowRunnerError(
                    "disabled receipt cannot reference evaluated artifacts"
                )
            if ShadowRunnerReason.FEATURE_DISABLED not in reasons:
                raise CompleteShadowRunnerError(
                    "disabled receipt requires FEATURE_DISABLED"
                )
        else:
            if any(
                value is None
                for value in (
                    request,
                    baseline_id,
                    replay_id,
                    report_id,
                    advisory_id,
                )
            ):
                raise CompleteShadowRunnerError(
                    "completed receipt requires all artifact references"
                )
        payload = {
            "schema_version": SHADOW_RUNNER_SCHEMA_VERSION,
            "policy_version": policy,
            "status": status.value,
            "scenario_id": scenario,
            "request_ref": request,
            "baseline_snapshot_id": baseline_id,
            "replay_snapshot_id": replay_id,
            "evaluation_report_id": report_id,
            "advisory_result_id": advisory_id,
            "reason_codes": [value.value for value in reasons],
        }
        return cls(
            receipt_id=_digest(payload),
            schema_version=SHADOW_RUNNER_SCHEMA_VERSION,
            policy_version=policy,
            status=status,
            scenario_id=scenario,
            request_ref=request,
            baseline_snapshot_id=baseline_id,
            replay_snapshot_id=replay_id,
            evaluation_report_id=report_id,
            advisory_result_id=advisory_id,
            reason_codes=reasons,
        )


@dataclass(frozen=True, slots=True)
class CompleteShadowRunResult:
    result_id: str
    status: ShadowRunnerStatus
    baseline: ShadowPassArtifacts | None
    replay: ShadowPassArtifacts | None
    evaluation: ReplayEvaluationReport | None
    advisory: AdvisoryShadowResult | None
    receipt: CompleteShadowRunReceipt

    @classmethod
    def create(
        cls,
        *,
        status: ShadowRunnerStatus,
        baseline: ShadowPassArtifacts | None,
        replay: ShadowPassArtifacts | None,
        evaluation: ReplayEvaluationReport | None,
        advisory: AdvisoryShadowResult | None,
        receipt: CompleteShadowRunReceipt,
    ) -> "CompleteShadowRunResult":
        if receipt.status is not status:
            raise CompleteShadowRunnerError(
                "result status must match receipt status"
            )
        if status is ShadowRunnerStatus.DISABLED:
            if any(
                value is not None
                for value in (baseline, replay, evaluation, advisory)
            ):
                raise CompleteShadowRunnerError(
                    "disabled result cannot contain evaluated artifacts"
                )
        else:
            if any(
                value is None
                for value in (baseline, replay, evaluation, advisory)
            ):
                raise CompleteShadowRunnerError(
                    "completed result requires all evaluated artifacts"
                )
        payload = {
            "status": status.value,
            "receipt_id": receipt.receipt_id,
            "baseline_snapshot_id": (
                baseline.snapshot.snapshot_id if baseline else None
            ),
            "replay_snapshot_id": (
                replay.snapshot.snapshot_id if replay else None
            ),
            "evaluation_report_id": (
                evaluation.report_id if evaluation else None
            ),
            "advisory_result_id": advisory.result_id if advisory else None,
        }
        return cls(
            result_id=_digest(payload),
            status=status,
            baseline=baseline,
            replay=replay,
            evaluation=evaluation,
            advisory=advisory,
            receipt=receipt,
        )


class CompleteShadowRunner:
    """Compose the complete deterministic Milestone 1 shadow path."""

    def run(
        self,
        config: ShadowRunnerConfig | None = None,
        inputs: CompleteShadowRunInput | None = None,
    ) -> CompleteShadowRunResult:
        resolved_config = config if config is not None else ShadowRunnerConfig()
        if not isinstance(resolved_config, ShadowRunnerConfig):
            raise CompleteShadowRunnerError(
                "config must be a ShadowRunnerConfig"
            )
        config = resolved_config
        if not config.enabled:
            receipt = CompleteShadowRunReceipt.create(
                policy_version=config.policy_version,
                status=ShadowRunnerStatus.DISABLED,
                scenario_id=config.scenario_id,
                request_ref=None,
                baseline_snapshot_id=None,
                replay_snapshot_id=None,
                evaluation_report_id=None,
                advisory_result_id=None,
                reason_codes=(
                    ShadowRunnerReason.FEATURE_DISABLED,
                    ShadowRunnerReason.MAIN_ANSWER_UNTOUCHED,
                    ShadowRunnerReason.CANON_UNCHANGED,
                    ShadowRunnerReason.ADVISORY_SHADOW_ONLY,
                ),
            )
            return CompleteShadowRunResult.create(
                status=ShadowRunnerStatus.DISABLED,
                baseline=None,
                replay=None,
                evaluation=None,
                advisory=None,
                receipt=receipt,
            )
        if not isinstance(inputs, CompleteShadowRunInput):
            raise CompleteShadowRunnerError(
                "enabled runner requires CompleteShadowRunInput"
            )

        baseline = self._run_pass(config, inputs, reverse=False)
        replay = self._run_pass(config, inputs, reverse=True)
        evaluation = ReplayEvaluationReport.compare(
            baseline.snapshot,
            replay.snapshot,
        )
        advisory_signals = self._resolve_advisory_intents(
            inputs.advisory_intents,
            baseline.state_result,
            baseline.goal_result,
            baseline.open_loop_result,
        )
        advisory = AdvisoryShadowGate().evaluate(
            request=inputs.advisory_request,
            hard_gate_report=evaluation,
            signals=advisory_signals,
            state_projections=baseline.state_result.projections,
            goal_projections=baseline.goal_result.projections,
            open_loop_projections=baseline.open_loop_result.projections,
        )
        receipt = CompleteShadowRunReceipt.create(
            policy_version=config.policy_version,
            status=ShadowRunnerStatus.COMPLETED,
            scenario_id=config.scenario_id,
            request_ref=inputs.request_ref,
            baseline_snapshot_id=baseline.snapshot.snapshot_id,
            replay_snapshot_id=replay.snapshot.snapshot_id,
            evaluation_report_id=evaluation.report_id,
            advisory_result_id=advisory.result_id,
            reason_codes=(
                ShadowRunnerReason.BASELINE_COMPLETED,
                ShadowRunnerReason.REPLAY_COMPLETED,
                ShadowRunnerReason.REPLAY_EVALUATED,
                ShadowRunnerReason.MAIN_ANSWER_UNTOUCHED,
                ShadowRunnerReason.CANON_UNCHANGED,
                ShadowRunnerReason.ADVISORY_SHADOW_ONLY,
            ),
        )
        return CompleteShadowRunResult.create(
            status=ShadowRunnerStatus.COMPLETED,
            baseline=baseline,
            replay=replay,
            evaluation=evaluation,
            advisory=advisory,
            receipt=receipt,
        )

    @staticmethod
    def _run_pass(
        config: ShadowRunnerConfig,
        inputs: CompleteShadowRunInput,
        *,
        reverse: bool,
    ) -> ShadowPassArtifacts:
        episodes = _ordered(inputs.episodes, reverse=reverse)
        weave_result = ThreadWeaver().weave(episodes)
        continuity_result = ContinuityContextAssembler().assemble(
            request_ref=inputs.request_ref,
            current_episode=inputs.current_episode,
            episodes=episodes,
            weave_result=weave_result,
        )
        continuity_policies = tuple(
            inputs.gate_policy.for_continuity_item(item.item_id)
            for item in continuity_result.pack.items
        )
        continuity_batch = ContinuityWorkingMemoryAdapter().adapt(
            continuity_result.pack,
            episodes,
            _ordered(continuity_policies, reverse=reverse),
        )

        state_result = StateReconciler().reconcile(
            _ordered(inputs.state_assertions, reverse=reverse),
            _ordered(inputs.state_relations, reverse=reverse),
            as_of=inputs.as_of,
        )
        goal_result = GoalProjector().project(
            _ordered(inputs.goal_snapshots, reverse=reverse),
            _ordered(inputs.goal_attestations, reverse=reverse),
        )
        open_loop_result = OpenLoopProjector().project(
            _ordered(inputs.open_loop_signals, reverse=reverse),
            _ordered(inputs.open_loop_resolutions, reverse=reverse),
            as_of=inputs.as_of,
        )

        projection_ids = (
            *(value.projection_id for value in state_result.projections),
            *(value.projection_id for value in goal_result.projections),
            *(value.projection_id for value in open_loop_result.projections),
        )
        projection_policies = tuple(
            inputs.gate_policy.for_projection(value)
            for value in projection_ids
        )
        projection_batch = ProjectionWorkingMemoryAdapter().adapt(
            state_projections=_ordered(
                state_result.projections,
                reverse=reverse,
            ),
            assertions=_ordered(inputs.state_assertions, reverse=reverse),
            goal_projections=_ordered(
                goal_result.projections,
                reverse=reverse,
            ),
            open_loop_projections=_ordered(
                open_loop_result.projections,
                reverse=reverse,
            ),
            policies=_ordered(projection_policies, reverse=reverse),
        )

        candidates = _ordered(
            (
                *continuity_batch.candidates,
                *projection_batch.candidates,
            ),
            reverse=reverse,
        )
        capsules = _ordered(
            (
                *continuity_batch.capsules,
                *projection_batch.capsules,
            ),
            reverse=reverse,
        )
        working_memory_plan = WorkingMemoryGate().plan(
            candidates,
            budget=inputs.working_memory_budget,
        )
        context_pack = ContextPackBuilder().build(
            working_memory_plan,
            capsules,
            budget=inputs.context_pack_budget,
        )
        compute_decision = decide_compute_path(
            inputs.query,
            candidate_count=len(candidates),
            continuity=inputs.compute_signals,
        )
        snapshot = ShadowRunSnapshot.create(
            scenario_id=config.scenario_id,
            continuity_pack=continuity_result.pack,
            continuity_receipt=continuity_result.receipt,
            state_result=state_result,
            goal_result=goal_result,
            open_loop_result=open_loop_result,
            working_memory_plan=working_memory_plan,
            context_pack=context_pack,
            compute_decision=compute_decision,
            observation=inputs.observation,
        )
        return ShadowPassArtifacts(
            weave_result=weave_result,
            continuity_result=continuity_result,
            state_result=state_result,
            goal_result=goal_result,
            open_loop_result=open_loop_result,
            continuity_batch=continuity_batch,
            projection_batch=projection_batch,
            working_memory_plan=working_memory_plan,
            context_pack=context_pack,
            compute_decision=compute_decision,
            snapshot=snapshot,
        )

    @staticmethod
    def _resolve_advisory_intents(
        intents: Iterable[AdvisoryIntent],
        state_result: StateReconciliationResult,
        goal_result: GoalProjectionResult,
        open_loop_result: OpenLoopProjectionResult,
    ) -> tuple[AdvisorySignal, ...]:
        signals: list[AdvisorySignal] = []
        seen: set[tuple[AdvisorySignalKind, str]] = set()
        for intent in intents:
            if not isinstance(intent, AdvisoryIntent):
                raise CompleteShadowRunnerError(
                    "advisory_intents contain an invalid value"
                )
            key = (intent.kind, intent.target_ref)
            if key in seen:
                raise CompleteShadowRunnerError(
                    "advisory_intents cannot contain duplicates"
                )
            seen.add(key)
            projection_id = CompleteShadowRunner._resolve_projection_id(
                intent,
                state_result.projections,
                goal_result.projections,
                open_loop_result.projections,
            )
            signals.append(
                AdvisorySignal.create(
                    kind=intent.kind,
                    projection_id=projection_id,
                )
            )
        return tuple(sorted(signals, key=lambda value: value.signal_id))

    @staticmethod
    def _resolve_projection_id(
        intent: AdvisoryIntent,
        states: Iterable[CurrentStateProjection],
        goals: Iterable[GoalProjection],
        loops: Iterable[OpenLoopProjection],
    ) -> str:
        matches: list[str] = []
        if intent.kind is AdvisorySignalKind.PRIORITY_MAY_HAVE_CHANGED:
            matches.extend(
                projection.projection_id
                for projection in states
                if (
                    intent.target_ref == projection.selected_assertion_ref
                    or intent.target_ref in projection.candidate_assertion_refs
                )
            )
        elif intent.kind is AdvisorySignalKind.GOAL_RELEVANT:
            matches.extend(
                projection.projection_id
                for projection in goals
                if projection.goal_ref == intent.target_ref
            )
        else:
            matches.extend(
                projection.projection_id
                for projection in loops
                if projection.loop_key == intent.target_ref
            )
        if len(matches) != 1:
            raise CompleteShadowRunnerError(
                "advisory intent must resolve to exactly one projection"
            )
        return matches[0]


__all__ = [
    "SHADOW_RUNNER_POLICY_VERSION",
    "SHADOW_RUNNER_SCHEMA_VERSION",
    "AdvisoryIntent",
    "CompleteShadowRunInput",
    "CompleteShadowRunReceipt",
    "CompleteShadowRunResult",
    "CompleteShadowRunner",
    "CompleteShadowRunnerError",
    "ShadowGatePolicyTemplate",
    "ShadowPassArtifacts",
    "ShadowRunnerConfig",
    "ShadowRunnerReason",
    "ShadowRunnerStatus",
]
