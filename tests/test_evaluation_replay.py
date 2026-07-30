"""Tests for the offline deterministic replay evaluation foundation."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from core.evaluation_replay import (
    CaseEvaluationReceipt,
    EvaluationCase,
    EvaluationPackage,
    EvaluationRun,
    ExperimentFork,
    StabilityClass,
    canonical_json,
    compare_case_receipts,
    compare_runs,
    evaluate_fixture,
    main,
    stable_digest,
)

FIXTURE = Path(__file__).parent / "fixtures" / "evaluation_replay" / "minimal.json"


def _receipt(**overrides):
    data = {
        "case_id": "case-1",
        "input_digest": "input-digest",
        "extracted_claims": ("claim-1",),
        "evidence_refs": ("span-1",),
        "retrieval_result": ("claim-1",),
        "memory_dispositions": {"claim-1": "EXCLUDE"},
        "route": "hybrid",
        "answer": "Supported answer.",
        "policy_reason_codes": ("EVIDENCE_PRESENT",),
        "latency_ms": {"total": 20.0},
        "resource_counts": {"dense_call_count": 1.0},
    }
    data.update(overrides)
    return CaseEvaluationReceipt(**data)


def _run(run_id: str, receipt: CaseEvaluationReceipt, **overrides):
    data = {
        "run_id": run_id,
        "package_id": "package-1",
        "code_revision": "revision-1",
        "case_receipts": (receipt,),
        "configuration_snapshot": {"retrieval": {"mode": "hybrid"}},
        "feature_flags": {"ENABLE_BUDGET_PLANNER": True},
        "policy_snapshot_fixture": {"truth_gate_required": True},
        "environment_manifest": {"network": "disabled", "clock": "fixed"},
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:01Z",
    }
    data.update(overrides)
    return EvaluationRun(**data)


def _fork() -> ExperimentFork:
    return ExperimentFork(
        parent_run_id="baseline",
        fork_id="fork-1",
        changed_dimension="retrieval.mode",
        before_value="hybrid",
        after_value="lexical",
    )


def test_canonical_json_is_stable_across_mapping_order():
    left = {"b": 2, "a": {"y": 1, "x": 0}}
    right = {"a": {"x": 0, "y": 1}, "b": 2}

    assert canonical_json(left) == canonical_json(right)
    assert stable_digest(left) == stable_digest(right)


def test_canonical_json_rejects_nonfinite_numbers():
    with pytest.raises(ValueError, match="NaN or infinite"):
        canonical_json({"bad": float("nan")})


def test_package_rejects_duplicate_case_ids():
    case = EvaluationCase(
        case_id="case-1",
        task_class="direct_fact",
        risk_class="low",
        question="Question?",
    )

    with pytest.raises(ValueError, match="cases.case_id"):
        EvaluationPackage(package_id="package-1", cases=(case, case))


def test_run_digest_ignores_run_id_timestamps_and_mapping_order():
    receipt = _receipt()
    baseline = _run("baseline", receipt)
    replay = _run(
        "replay-with-another-id",
        receipt,
        configuration_snapshot={"retrieval": {"mode": "hybrid"}},
        environment_manifest={"clock": "fixed", "network": "disabled"},
        started_at="2035-12-31T23:59:58Z",
        completed_at="2036-01-01T00:00:00Z",
    )

    assert baseline.result_digest == replay.result_digest


def test_fork_requires_an_actual_change():
    with pytest.raises(ValueError, match="must differ"):
        ExperimentFork(
            parent_run_id="baseline",
            fork_id="fork-1",
            changed_dimension="retrieval.mode",
            before_value={"mode": "hybrid", "k": 3},
            after_value={"k": 3, "mode": "hybrid"},
        )


def test_answer_only_change_is_structurally_equivalent():
    baseline = _receipt()
    candidate = replace(baseline, answer="Same evidence, different wording.")

    diff = compare_case_receipts(baseline, candidate)

    assert diff.answer_changed is True
    assert diff.stability is StabilityClass.STRUCTURALLY_EQUIVALENT
    assert not diff.critical_regressions


def test_structural_diff_detects_route_memory_and_cost_changes():
    baseline = _receipt()
    candidate = replace(
        baseline,
        extracted_claims=("claim-1", "claim-2"),
        evidence_refs=("span-1", "span-2"),
        memory_dispositions={"claim-1": "ACTIVE", "claim-2": "DEFER"},
        route="lexical",
        latency_ms={"total": 8.0},
        resource_counts={"dense_call_count": 0.0},
    )

    diff = compare_case_receipts(baseline, candidate)

    assert diff.claims_added == ("claim-2",)
    assert diff.evidence_added == ("span-2",)
    assert diff.route_before == "hybrid"
    assert diff.route_after == "lexical"
    assert diff.memory_disposition_changes["claim-1"] == {
        "baseline": "EXCLUDE",
        "candidate": "ACTIVE",
    }
    assert diff.metric_delta["latency_ms.total"] == -12.0
    assert diff.metric_delta["resource_counts.dense_call_count"] == -1.0
    assert diff.stability is StabilityClass.REVIEW_REQUIRED


def test_critical_query_write_classifies_candidate_as_regression():
    baseline_receipt = _receipt()
    candidate_receipt = replace(baseline_receipt, query_path_write_count=1)
    baseline = _run("baseline", baseline_receipt)
    candidate = _run("candidate", candidate_receipt)

    diff = compare_runs(baseline, candidate, _fork())

    assert diff.stability is StabilityClass.REGRESSION
    assert "query_path_write_count=1" in diff.critical_regressions[0]


def test_compare_runs_rejects_mismatched_case_sets():
    baseline = _run("baseline", _receipt())
    candidate = _run("candidate", replace(_receipt(), case_id="case-2"))

    with pytest.raises(ValueError, match="run case sets differ"):
        compare_runs(baseline, candidate, _fork())


def test_repository_fixture_produces_machine_readable_diff():
    report = evaluate_fixture(FIXTURE)
    diff = report["diff"]

    assert report["protocol_version"] == "erp-1"
    assert report["package_id"] == "erp-minimal-routing-v1"
    assert len(report["package_digest"]) == 64
    assert diff.stability is StabilityClass.REVIEW_REQUIRED
    assert diff.aggregate_delta["latency_ms.total"] == -24.0
    assert diff.aggregate_delta["resource_counts.dense_call_count"] == -1.0
    assert not diff.critical_regressions


def test_cli_prints_canonical_json(capsys):
    assert main([str(FIXTURE)]) == 0
    output = capsys.readouterr().out
    parsed = json.loads(output)

    assert parsed["diff"]["stability"] == "REVIEW_REQUIRED"
    assert parsed["diff"]["case_diffs"][0]["route_before"] == "hybrid"
    assert parsed["diff"]["case_diffs"][0]["route_after"] == "lexical"
    assert output == canonical_json(parsed) + "\n"
