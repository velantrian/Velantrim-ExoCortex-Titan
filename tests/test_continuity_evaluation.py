"""Replay evaluation and zero-tolerance hard-gate tests for Continuity R5A."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.compute_controller import (
    ComputeSensitivity,
    ContextFreshness,
    ContinuityComputeSignals,
    assess_compute_with_continuity,
    decide_compute_path,
)
from core.context_pack import ContextClaim, ContextEvidence, ContextPack
from core.continuity.evaluation import (
    HardGate,
    HardGateCounters,
    ReplayEvaluationError,
    ReplayEvaluationReport,
    ShadowRunSnapshot,
    ShadowSafetyObservation,
)
from core.goal_frame import GoalFrame, GoalIntent, RiskLevel
from core.knowledge_capsule import ClaimModality
from core.working_memory_gate import (
    GateDisposition,
    GateReason,
    WorkingMemoryBudget,
    WorkingMemoryPlan,
)


def _plan() -> WorkingMemoryPlan:
    return WorkingMemoryPlan(
        budget=WorkingMemoryBudget(max_items=4, max_chars=1_000),
        decisions=(),
        used_items=0,
        used_chars=0,
    )


def _empty_pack(*, max_tokens: int = 2_000) -> ContextPack:
    return ContextPack.create(
        max_tokens=max_tokens,
        claims=(),
        notes=(),
        conflicts=(),
        deferred=(),
        warnings=(),
        deferred_total=0,
        excluded_count=0,
    )


def _hypothesis_pack() -> ContextPack:
    evidence = ContextEvidence(
        span_id="span-1",
        document_id="doc-1",
        start_offset=0,
        end_offset=8,
        content_hash="a" * 64,
    )
    claim = ContextClaim(
        capsule_id="capsule-1",
        claim_id="claim-1",
        text="Hypothesis treated as truth",
        modality=ClaimModality.HYPOTHESIS,
        evidence=(evidence,),
        extraction_confidence=0.9,
        truth_confidence=0.8,
        disposition=GateDisposition.ACTIVE,
        reasons=(GateReason.FULL_CONTENT_SELECTED,),
        attention_score=0.9,
        protected=False,
        rank=1,
    )
    return ContextPack.create(
        max_tokens=2_000,
        claims=(claim,),
        notes=(),
        conflicts=(),
        deferred=(),
        warnings=(),
        deferred_total=0,
        excluded_count=0,
    )


def _snapshot(
    *,
    scenario_id: str = "scenario-1",
    observation: ShadowSafetyObservation | None = None,
    pack: ContextPack | None = None,
    decision=None,
) -> ShadowRunSnapshot:
    return ShadowRunSnapshot.create(
        scenario_id=scenario_id,
        working_memory_plan=_plan(),
        context_pack=pack or _empty_pack(),
        compute_decision=decision or decide_compute_path("answer briefly"),
        observation=observation,
    )


def test_same_artifacts_produce_same_snapshot_and_passing_replay() -> None:
    first = _snapshot()
    second = _snapshot()
    report = ReplayEvaluationReport.compare(first, second)

    assert first == second
    assert first.snapshot_id == second.snapshot_id
    assert first.canonical_bytes() == second.canonical_bytes()
    assert report.replay_equal is True
    assert report.passed is True
    assert report.failed_gates == ()


def test_changed_compute_decision_fails_replay_gate() -> None:
    baseline = _snapshot(decision=decide_compute_path("answer briefly"))
    replay = _snapshot(decision=decide_compute_path("verify medical claim"))
    report = ReplayEvaluationReport.compare(baseline, replay)

    assert report.replay_equal is False
    assert report.passed is False
    assert report.hard_gates.replay_divergence == 1
    assert HardGate.REPLAY_DIVERGENCE in report.failed_gates


def test_r4_assessment_final_decision_is_replayable_without_runtime_wiring() -> None:
    assessment = assess_compute_with_continuity(
        "answer briefly",
        goal=GoalFrame(
            query="answer briefly",
            intent=GoalIntent.UNKNOWN,
            risk_level=RiskLevel.LOW,
            output_style="short",
        ),
        signals=ContinuityComputeSignals(
            context_freshness=ContextFreshness.FRESH,
            continuity_available=True,
            active_contradictions=1,
            important_claim=True,
            sensitivity=ComputeSensitivity.MEDIUM,
        ),
    )
    baseline = _snapshot(decision=assessment.decision)
    replay = _snapshot(decision=assessment.decision)

    report = ReplayEvaluationReport.compare(baseline, replay)

    assert assessment.changed_legacy_decision is True
    assert report.passed is True
    assert baseline.compute_decision_hash == replay.compute_decision_hash


@pytest.mark.parametrize(
    ("field_name", "gate"),
    [
        ("privacy_leakage", HardGate.PRIVACY_LEAKAGE),
        ("inference_as_fact", HardGate.INFERENCE_AS_FACT),
        ("missing_provenance", HardGate.MISSING_PROVENANCE),
        ("budget_overflow", HardGate.BUDGET_OVERFLOW),
        ("query_time_canon_write", HardGate.QUERY_TIME_CANON_WRITE),
        ("silent_overwrite", HardGate.SILENT_OVERWRITE),
    ],
)
def test_explicit_safety_observation_is_zero_tolerance(
    field_name: str,
    gate: HardGate,
) -> None:
    observation = ShadowSafetyObservation(**{field_name: 1})
    baseline = _snapshot(observation=observation)
    replay = _snapshot(observation=observation)

    report = ReplayEvaluationReport.compare(baseline, replay)

    assert report.replay_equal is True
    assert report.passed is False
    assert gate in report.failed_gates


def test_hypothesis_with_truth_confidence_is_detected_as_inference_as_fact() -> None:
    baseline = _snapshot(pack=_hypothesis_pack())
    replay = _snapshot(pack=_hypothesis_pack())

    report = ReplayEvaluationReport.compare(baseline, replay)

    assert baseline.hard_gates.inference_as_fact == 1
    assert report.passed is False
    assert HardGate.INFERENCE_AS_FACT in report.failed_gates


def test_report_combines_maximum_gate_counters_from_both_runs() -> None:
    baseline = _snapshot(
        observation=ShadowSafetyObservation(privacy_leakage=1)
    )
    replay = _snapshot(
        observation=ShadowSafetyObservation(query_time_canon_write=2)
    )

    report = ReplayEvaluationReport.compare(baseline, replay)

    assert report.hard_gates.privacy_leakage == 1
    assert report.hard_gates.query_time_canon_write == 2
    assert report.hard_gates.replay_divergence == 1
    assert report.passed is False


def test_different_scenario_ids_fail_closed() -> None:
    with pytest.raises(ReplayEvaluationError, match="same scenario_id"):
        ReplayEvaluationReport.compare(
            _snapshot(scenario_id="scenario-a"),
            _snapshot(scenario_id="scenario-b"),
        )


def test_observation_rejects_bool_negative_and_non_integer_counts() -> None:
    with pytest.raises(ReplayEvaluationError, match="privacy_leakage"):
        ShadowSafetyObservation(privacy_leakage=True)  # type: ignore[arg-type]
    with pytest.raises(ReplayEvaluationError, match="budget_overflow"):
        ShadowSafetyObservation(budget_overflow=-1)
    with pytest.raises(ReplayEvaluationError, match="silent_overwrite"):
        ShadowSafetyObservation(silent_overwrite=1.5)  # type: ignore[arg-type]


def test_hard_gate_counter_merge_is_deterministic() -> None:
    left = HardGateCounters(privacy_leakage=1, replay_divergence=0)
    right = HardGateCounters(privacy_leakage=2, silent_overwrite=1)

    merged = left.max_with(right, replay_divergence=3)

    assert merged == HardGateCounters(
        privacy_leakage=2,
        replay_divergence=3,
        silent_overwrite=1,
    )
    assert merged.passed is False


def test_snapshot_and_report_are_immutable() -> None:
    snapshot = _snapshot()
    report = ReplayEvaluationReport.compare(snapshot, snapshot)

    with pytest.raises(FrozenInstanceError):
        snapshot.scenario_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.passed = False  # type: ignore[misc]


def test_evaluation_payload_has_no_runtime_or_authority_fields() -> None:
    snapshot = _snapshot()
    report = ReplayEvaluationReport.compare(snapshot, snapshot)
    payload = report.to_dict()

    forbidden = {
        "answer",
        "advice",
        "action",
        "tool",
        "persist",
        "canon_write",
        "truth_status",
        "execute",
        "runtime_enable",
    }
    assert forbidden.isdisjoint(payload)
