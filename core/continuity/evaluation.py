"""Deterministic replay snapshots and zero-tolerance continuity hard gates.

This module evaluates already-built shadow artifacts. It does not execute the
answer path, retrieve data, mutate ESM, write Canon, authorize advice/actions,
or persist evaluation results.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json

from core.compute_controller import ComputeDecision
from core.context_pack import ContextPack
from core.knowledge_capsule import ClaimModality
from core.working_memory_gate import WorkingMemoryPlan

from .context_pack import ContinuityContextPack, ContinuityReceipt
from .goal_open_loop import GoalProjectionResult, OpenLoopProjectionResult
from .state_reconciler import StateReconciliationResult

EVALUATION_SCHEMA_VERSION = "continuity.replay_evaluation.v1"
EVALUATION_POLICY_VERSION = "continuity.replay_evaluation.policy.v1"


class ReplayEvaluationError(ValueError):
    """Evaluation inputs violate a deterministic replay boundary."""


class HardGate(str, Enum):
    PRIVACY_LEAKAGE = "privacy_leakage"
    INFERENCE_AS_FACT = "inference_as_fact"
    MISSING_PROVENANCE = "missing_provenance"
    BUDGET_OVERFLOW = "budget_overflow"
    QUERY_TIME_CANON_WRITE = "query_time_canon_write"
    REPLAY_DIVERGENCE = "replay_divergence"
    SILENT_OVERWRITE = "silent_overwrite"


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReplayEvaluationError(f"{name} must be a non-empty string")
    return value


def _count(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReplayEvaluationError(f"{name} must be a non-negative int")
    return value


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
class ShadowSafetyObservation:
    """Explicit counters for effects not derivable from pure artifacts."""

    privacy_leakage: int = 0
    inference_as_fact: int = 0
    missing_provenance: int = 0
    budget_overflow: int = 0
    query_time_canon_write: int = 0
    silent_overwrite: int = 0

    def __post_init__(self) -> None:
        for field_name in (
            "privacy_leakage",
            "inference_as_fact",
            "missing_provenance",
            "budget_overflow",
            "query_time_canon_write",
            "silent_overwrite",
        ):
            object.__setattr__(
                self,
                field_name,
                _count(getattr(self, field_name), field_name),
            )


@dataclass(frozen=True, slots=True)
class HardGateCounters:
    privacy_leakage: int = 0
    inference_as_fact: int = 0
    missing_provenance: int = 0
    budget_overflow: int = 0
    query_time_canon_write: int = 0
    replay_divergence: int = 0
    silent_overwrite: int = 0

    def __post_init__(self) -> None:
        for field_name in (
            "privacy_leakage",
            "inference_as_fact",
            "missing_provenance",
            "budget_overflow",
            "query_time_canon_write",
            "replay_divergence",
            "silent_overwrite",
        ):
            object.__setattr__(
                self,
                field_name,
                _count(getattr(self, field_name), field_name),
            )

    @property
    def passed(self) -> bool:
        return all(value == 0 for value in self.to_dict().values())

    @property
    def failed_gates(self) -> tuple[HardGate, ...]:
        values = self.to_dict()
        return tuple(gate for gate in HardGate if values[gate.value] > 0)

    def to_dict(self) -> dict[str, int]:
        return {
            HardGate.PRIVACY_LEAKAGE.value: self.privacy_leakage,
            HardGate.INFERENCE_AS_FACT.value: self.inference_as_fact,
            HardGate.MISSING_PROVENANCE.value: self.missing_provenance,
            HardGate.BUDGET_OVERFLOW.value: self.budget_overflow,
            HardGate.QUERY_TIME_CANON_WRITE.value: self.query_time_canon_write,
            HardGate.REPLAY_DIVERGENCE.value: self.replay_divergence,
            HardGate.SILENT_OVERWRITE.value: self.silent_overwrite,
        }

    def max_with(
        self,
        other: HardGateCounters,
        *,
        replay_divergence: int | None = None,
    ) -> HardGateCounters:
        if not isinstance(other, HardGateCounters):
            raise ReplayEvaluationError("other must be HardGateCounters")
        divergence = max(self.replay_divergence, other.replay_divergence)
        if replay_divergence is not None:
            divergence = max(
                divergence,
                _count(replay_divergence, "replay_divergence"),
            )
        return HardGateCounters(
            privacy_leakage=max(
                self.privacy_leakage,
                other.privacy_leakage,
            ),
            inference_as_fact=max(
                self.inference_as_fact,
                other.inference_as_fact,
            ),
            missing_provenance=max(
                self.missing_provenance,
                other.missing_provenance,
            ),
            budget_overflow=max(
                self.budget_overflow,
                other.budget_overflow,
            ),
            query_time_canon_write=max(
                self.query_time_canon_write,
                other.query_time_canon_write,
            ),
            replay_divergence=divergence,
            silent_overwrite=max(
                self.silent_overwrite,
                other.silent_overwrite,
            ),
        )


def _artifact_counters(
    plan: WorkingMemoryPlan,
    context_pack: ContextPack,
    observation: ShadowSafetyObservation,
) -> HardGateCounters:
    inferred_as_fact = sum(
        1
        for claim in context_pack.claims
        if claim.modality is ClaimModality.HYPOTHESIS
        and claim.truth_confidence is not None
    )
    missing_provenance = sum(
        1 for claim in context_pack.claims if not claim.evidence
    )
    budget_overflow = int(
        plan.used_items > plan.budget.max_items
        or plan.used_chars > plan.budget.max_chars
        or context_pack.token_cost > context_pack.max_tokens
    )
    return HardGateCounters(
        privacy_leakage=observation.privacy_leakage,
        inference_as_fact=(
            observation.inference_as_fact + inferred_as_fact
        ),
        missing_provenance=(
            observation.missing_provenance + missing_provenance
        ),
        budget_overflow=observation.budget_overflow + budget_overflow,
        query_time_canon_write=observation.query_time_canon_write,
        silent_overwrite=observation.silent_overwrite,
    )


@dataclass(frozen=True, slots=True)
class ShadowRunSnapshot:
    snapshot_id: str
    schema_version: str
    policy_version: str
    scenario_id: str
    continuity_pack_id: str | None
    continuity_receipt_id: str | None
    state_result_id: str | None
    goal_result_id: str | None
    open_loop_result_id: str | None
    working_memory_plan_hash: str
    context_pack_id: str
    compute_decision_hash: str
    hard_gates: HardGateCounters

    @classmethod
    def create(
        cls,
        *,
        scenario_id: str,
        working_memory_plan: WorkingMemoryPlan,
        context_pack: ContextPack,
        compute_decision: ComputeDecision,
        continuity_pack: ContinuityContextPack | None = None,
        continuity_receipt: ContinuityReceipt | None = None,
        state_result: StateReconciliationResult | None = None,
        goal_result: GoalProjectionResult | None = None,
        open_loop_result: OpenLoopProjectionResult | None = None,
        observation: ShadowSafetyObservation | None = None,
        policy_version: str = EVALUATION_POLICY_VERSION,
    ) -> ShadowRunSnapshot:
        scenario = _text(scenario_id, "scenario_id")
        policy = _text(policy_version, "policy_version")
        if not isinstance(working_memory_plan, WorkingMemoryPlan):
            raise ReplayEvaluationError(
                "working_memory_plan must be a WorkingMemoryPlan"
            )
        if not isinstance(context_pack, ContextPack):
            raise ReplayEvaluationError("context_pack must be a ContextPack")
        if not isinstance(compute_decision, ComputeDecision):
            raise ReplayEvaluationError(
                "compute_decision must be a ComputeDecision"
            )
        if continuity_pack is not None and not isinstance(
            continuity_pack,
            ContinuityContextPack,
        ):
            raise ReplayEvaluationError(
                "continuity_pack must be ContinuityContextPack or None"
            )
        if continuity_receipt is not None and not isinstance(
            continuity_receipt,
            ContinuityReceipt,
        ):
            raise ReplayEvaluationError(
                "continuity_receipt must be ContinuityReceipt or None"
            )
        if (
            continuity_pack is not None
            and continuity_receipt is not None
            and continuity_receipt.pack_id != continuity_pack.pack_id
        ):
            raise ReplayEvaluationError(
                "continuity receipt does not reference continuity pack"
            )
        if state_result is not None and not isinstance(
            state_result,
            StateReconciliationResult,
        ):
            raise ReplayEvaluationError(
                "state_result must be StateReconciliationResult or None"
            )
        if goal_result is not None and not isinstance(
            goal_result,
            GoalProjectionResult,
        ):
            raise ReplayEvaluationError(
                "goal_result must be GoalProjectionResult or None"
            )
        if open_loop_result is not None and not isinstance(
            open_loop_result,
            OpenLoopProjectionResult,
        ):
            raise ReplayEvaluationError(
                "open_loop_result must be OpenLoopProjectionResult or None"
            )
        observed = observation or ShadowSafetyObservation()
        if not isinstance(observed, ShadowSafetyObservation):
            raise ReplayEvaluationError(
                "observation must be ShadowSafetyObservation or None"
            )

        continuity_pack_id = (
            continuity_pack.pack_id if continuity_pack is not None else None
        )
        continuity_receipt_id = (
            continuity_receipt.receipt_id
            if continuity_receipt is not None
            else None
        )
        state_result_id = (
            state_result.result_id if state_result is not None else None
        )
        goal_result_id = (
            goal_result.result_id if goal_result is not None else None
        )
        open_loop_result_id = (
            open_loop_result.result_id
            if open_loop_result is not None
            else None
        )
        plan_hash = _digest(working_memory_plan.to_dict())
        decision_hash = _digest(compute_decision.to_dict())
        hard_gates = _artifact_counters(
            working_memory_plan,
            context_pack,
            observed,
        )
        payload = {
            "schema_version": EVALUATION_SCHEMA_VERSION,
            "policy_version": policy,
            "scenario_id": scenario,
            "continuity_pack_id": continuity_pack_id,
            "continuity_receipt_id": continuity_receipt_id,
            "state_result_id": state_result_id,
            "goal_result_id": goal_result_id,
            "open_loop_result_id": open_loop_result_id,
            "working_memory_plan_hash": plan_hash,
            "context_pack_id": context_pack.pack_id,
            "compute_decision_hash": decision_hash,
            "hard_gates": hard_gates.to_dict(),
        }
        return cls(
            snapshot_id=_digest(payload),
            schema_version=EVALUATION_SCHEMA_VERSION,
            policy_version=policy,
            scenario_id=scenario,
            continuity_pack_id=continuity_pack_id,
            continuity_receipt_id=continuity_receipt_id,
            state_result_id=state_result_id,
            goal_result_id=goal_result_id,
            open_loop_result_id=open_loop_result_id,
            working_memory_plan_hash=plan_hash,
            context_pack_id=context_pack.pack_id,
            compute_decision_hash=decision_hash,
            hard_gates=hard_gates,
        )

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "policy_version": self.policy_version,
            "scenario_id": self.scenario_id,
            "continuity_pack_id": self.continuity_pack_id,
            "continuity_receipt_id": self.continuity_receipt_id,
            "state_result_id": self.state_result_id,
            "goal_result_id": self.goal_result_id,
            "open_loop_result_id": self.open_loop_result_id,
            "working_memory_plan_hash": self.working_memory_plan_hash,
            "context_pack_id": self.context_pack_id,
            "compute_decision_hash": self.compute_decision_hash,
            "hard_gates": self.hard_gates.to_dict(),
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_json(self.payload()).encode("utf-8")


@dataclass(frozen=True, slots=True)
class ReplayEvaluationReport:
    report_id: str
    schema_version: str
    policy_version: str
    scenario_id: str
    baseline_snapshot_id: str
    replay_snapshot_id: str
    replay_equal: bool
    hard_gates: HardGateCounters
    passed: bool

    @classmethod
    def compare(
        cls,
        baseline: ShadowRunSnapshot,
        replay: ShadowRunSnapshot,
        *,
        policy_version: str = EVALUATION_POLICY_VERSION,
    ) -> ReplayEvaluationReport:
        if not isinstance(baseline, ShadowRunSnapshot):
            raise ReplayEvaluationError(
                "baseline must be a ShadowRunSnapshot"
            )
        if not isinstance(replay, ShadowRunSnapshot):
            raise ReplayEvaluationError(
                "replay must be a ShadowRunSnapshot"
            )
        if baseline.scenario_id != replay.scenario_id:
            raise ReplayEvaluationError(
                "baseline and replay must use the same scenario_id"
            )
        policy = _text(policy_version, "policy_version")
        replay_equal = baseline.canonical_bytes() == replay.canonical_bytes()
        hard_gates = baseline.hard_gates.max_with(
            replay.hard_gates,
            replay_divergence=0 if replay_equal else 1,
        )
        passed = hard_gates.passed
        payload = {
            "schema_version": EVALUATION_SCHEMA_VERSION,
            "policy_version": policy,
            "scenario_id": baseline.scenario_id,
            "baseline_snapshot_id": baseline.snapshot_id,
            "replay_snapshot_id": replay.snapshot_id,
            "replay_equal": replay_equal,
            "hard_gates": hard_gates.to_dict(),
            "passed": passed,
        }
        return cls(
            report_id=_digest(payload),
            schema_version=EVALUATION_SCHEMA_VERSION,
            policy_version=policy,
            scenario_id=baseline.scenario_id,
            baseline_snapshot_id=baseline.snapshot_id,
            replay_snapshot_id=replay.snapshot_id,
            replay_equal=replay_equal,
            hard_gates=hard_gates,
            passed=passed,
        )

    @property
    def failed_gates(self) -> tuple[HardGate, ...]:
        return self.hard_gates.failed_gates

    def to_dict(self) -> dict[str, object]:
        return {
            "report_id": self.report_id,
            "schema_version": self.schema_version,
            "policy_version": self.policy_version,
            "scenario_id": self.scenario_id,
            "baseline_snapshot_id": self.baseline_snapshot_id,
            "replay_snapshot_id": self.replay_snapshot_id,
            "replay_equal": self.replay_equal,
            "hard_gates": self.hard_gates.to_dict(),
            "failed_gates": [value.value for value in self.failed_gates],
            "passed": self.passed,
        }


__all__ = [
    "EVALUATION_POLICY_VERSION",
    "EVALUATION_SCHEMA_VERSION",
    "HardGate",
    "HardGateCounters",
    "ReplayEvaluationError",
    "ReplayEvaluationReport",
    "ShadowRunSnapshot",
    "ShadowSafetyObservation",
]
