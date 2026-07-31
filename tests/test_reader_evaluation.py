from dataclasses import replace
import json
from pathlib import Path

import pytest

from core.reader_evaluation import (
    EvaluationCorpusKind,
    EvaluationCorpusManifest,
    EvaluationEnvironment,
    PromotionDecision,
    ReaderCoreEvaluationAggregator,
    ReaderCorePromotionReviewer,
    ReaderEvaluationCaseManifest,
    ReaderEvaluationCaseResult,
    ReaderEvaluationError,
    ReaderPromotionThresholds,
    ReaderReplayComparator,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "reader_core"
    / "rdr_09_synthetic_evaluation.json"
)


def _environment() -> EvaluationEnvironment:
    return EvaluationEnvironment(
        commit_sha="commit-sha-fixture",
        runner_id="runner-linux-x86",
        python_version="3.11",
        hardware_profile="cpu-8-memory-32gb",
        config_digest="config-digest-fixture",
        model_id="fixture-model",
        model_version="1",
    )


def _manifest(
    case_id: str,
    corpus_kind: EvaluationCorpusKind,
    *,
    expected_claim_count: int = 4,
    expected_source_span_count: int = 4,
    expected_exception_count: int = 1,
    expected_relation_count: int = 2,
    expected_contradiction_count: int = 1,
    expected_qualifier_count: int = 1,
) -> ReaderEvaluationCaseManifest:
    return ReaderEvaluationCaseManifest(
        case_id=case_id,
        corpus_kind=corpus_kind,
        label_version="labels-v1",
        expected_claim_count=expected_claim_count,
        expected_source_span_count=expected_source_span_count,
        expected_exception_count=expected_exception_count,
        expected_relation_count=expected_relation_count,
        expected_contradiction_count=expected_contradiction_count,
        expected_qualifier_count=expected_qualifier_count,
        tags=("reader-core",),
    )


def _result(
    manifest: ReaderEvaluationCaseManifest,
    *,
    matched_claim_count: int | None = None,
    correct_source_span_count: int | None = None,
    matched_exception_count: int | None = None,
    matched_relation_count: int | None = None,
    false_relation_count: int = 0,
    matched_contradiction_count: int | None = None,
    connected_qualifier_count: int | None = None,
    orphan_source_claim_count: int = 0,
    unsupported_synthesis_claim_count: int = 0,
    replay_match: bool = True,
    truth_gate_bypass_count: int = 0,
    query_path_write_count: int = 0,
    direct_canon_write_count: int = 0,
    untrusted_instruction_execution_count: int = 0,
) -> ReaderEvaluationCaseResult:
    matched_claims = (
        manifest.expected_claim_count
        if matched_claim_count is None
        else matched_claim_count
    )
    correct_spans = (
        manifest.expected_source_span_count
        if correct_source_span_count is None
        else correct_source_span_count
    )
    matched_exceptions = (
        manifest.expected_exception_count
        if matched_exception_count is None
        else matched_exception_count
    )
    matched_relations = (
        manifest.expected_relation_count
        if matched_relation_count is None
        else matched_relation_count
    )
    matched_contradictions = (
        manifest.expected_contradiction_count
        if matched_contradiction_count is None
        else matched_contradiction_count
    )
    connected_qualifiers = (
        manifest.expected_qualifier_count
        if connected_qualifier_count is None
        else connected_qualifier_count
    )
    replay = ReaderReplayComparator.compare(
        manifest.case_id,
        ("structure", "cards", "coverage", "synthesis"),
        (
            ("structure", "cards", "coverage", "synthesis")
            if replay_match
            else ("structure", "cards", "different-synthesis")
        ),
    )
    return ReaderEvaluationCaseResult(
        manifest=manifest,
        predicted_claim_count=manifest.expected_claim_count,
        matched_claim_count=matched_claims,
        predicted_source_span_count=manifest.expected_source_span_count,
        correct_source_span_count=correct_spans,
        predicted_exception_count=manifest.expected_exception_count,
        matched_exception_count=matched_exceptions,
        predicted_relation_count=manifest.expected_relation_count,
        matched_relation_count=matched_relations,
        false_relation_count=false_relation_count,
        matched_contradiction_count=matched_contradictions,
        connected_qualifier_count=connected_qualifiers,
        source_claim_count=max(manifest.expected_claim_count, 1),
        orphan_source_claim_count=orphan_source_claim_count,
        synthesis_claim_count=2,
        unsupported_synthesis_claim_count=unsupported_synthesis_claim_count,
        replay=replay,
        section_latencies_ms=(20, 30, 40),
        session_wall_time_ms=150,
        model_tokens=600,
        projection_bytes=4_096,
        rebuild_time_ms=25,
        query_path_latency_delta_ms=2,
        resume_reused_units=1,
        resume_eligible_units=1,
        truth_gate_bypass_count=truth_gate_bypass_count,
        query_path_write_count=query_path_write_count,
        direct_canon_write_count=direct_canon_write_count,
        untrusted_instruction_execution_count=(
            untrusted_instruction_execution_count
        ),
    )


def _mixed_results() -> tuple[ReaderEvaluationCaseResult, ...]:
    return (
        _result(_manifest("synthetic-case", EvaluationCorpusKind.SYNTHETIC)),
        _result(_manifest("real-case", EvaluationCorpusKind.REAL)),
        _result(
            _manifest("human-case", EvaluationCorpusKind.HUMAN_LABELLED)
        ),
    )


def _thresholds() -> ReaderPromotionThresholds:
    return ReaderPromotionThresholds(
        min_total_cases=3,
        min_synthetic_cases=1,
        min_real_cases=1,
        min_human_labelled_cases=1,
        min_claim_fidelity=0.95,
        min_source_span_precision=0.95,
        min_source_span_recall=0.95,
        min_critical_exception_recall=0.95,
        min_relation_recall=0.90,
        max_false_relation_rate=0.05,
        min_contradiction_recall=0.95,
        max_orphan_claim_rate=0.05,
        min_qualifier_connectivity=0.95,
        max_unsupported_synthesis_rate=0.05,
        min_replay_match_rate=1.0,
        min_resume_reuse_ratio=0.90,
        max_query_path_latency_delta_ms=5,
        max_section_latency_p95_ms=100,
        max_model_tokens_per_case=1_000,
    )


def test_synthetic_manifest_fixture_is_canonical_and_source_controlled() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "reader-core.evaluation-manifest.v1"
    cases = tuple(
        ReaderEvaluationCaseManifest(
            case_id=item["case_id"],
            corpus_kind=EvaluationCorpusKind(item["corpus_kind"]),
            label_version=item["label_version"],
            expected_claim_count=item["expected_claim_count"],
            expected_source_span_count=item["expected_source_span_count"],
            expected_exception_count=item["expected_exception_count"],
            expected_relation_count=item["expected_relation_count"],
            expected_contradiction_count=item[
                "expected_contradiction_count"
            ],
            expected_qualifier_count=item["expected_qualifier_count"],
            tags=tuple(item["tags"]),
        )
        for item in payload["cases"]
    )
    manifest = EvaluationCorpusManifest(
        corpus_name=payload["corpus_name"],
        corpus_version=payload["corpus_version"],
        cases=cases,
    )
    assert len(manifest.cases) == 4
    assert {case.case_id for case in manifest.cases} == {
        "distant-contradiction",
        "hidden-critical-exception",
        "revision-reuse-ambiguity",
        "untrusted-document-instruction",
    }
    assert all(
        case.corpus_kind is EvaluationCorpusKind.SYNTHETIC
        for case in manifest.cases
    )


def test_replay_comparison_is_order_sensitive_and_self_verifying() -> None:
    same = ReaderReplayComparator.compare(
        "case-a",
        ("a", "b", "c"),
        ("a", "b", "c"),
    )
    reordered = ReaderReplayComparator.compare(
        "case-a",
        ("a", "b", "c"),
        ("b", "a", "c"),
    )
    assert same.matched is True
    assert reordered.matched is False
    with pytest.raises(ReaderEvaluationError, match="comparison_id"):
        replace(same, first_digest="forged")


def test_aggregation_is_deterministic_and_computes_transparent_metrics() -> None:
    results = _mixed_results()
    aggregator = ReaderCoreEvaluationAggregator()
    first = aggregator.build_report(_environment(), results)
    second = aggregator.build_report(_environment(), tuple(reversed(results)))

    assert first == second
    assert first.metrics.total_case_count == 3
    assert first.metrics.synthetic_case_count == 1
    assert first.metrics.real_case_count == 1
    assert first.metrics.human_labelled_case_count == 1
    assert first.metrics.claim_fidelity == 1.0
    assert first.metrics.source_span_precision == 1.0
    assert first.metrics.source_span_recall == 1.0
    assert first.metrics.critical_exception_recall == 1.0
    assert first.metrics.false_relation_rate == 0.0
    assert first.metrics.replay_match_rate == 1.0
    assert first.metrics.section_latency_p50_ms == 30
    assert first.metrics.section_latency_p95_ms == 40
    assert first.metrics.model_tokens_per_case == 600.0


def test_passing_metrics_only_become_eligible_for_operator_review() -> None:
    report = ReaderCoreEvaluationAggregator().build_report(
        _environment(),
        _mixed_results(),
    )
    review = ReaderCorePromotionReviewer().review(report, _thresholds())

    assert review.decision is PromotionDecision.ELIGIBLE_FOR_OPERATOR_REVIEW
    assert review.failed_gate_codes == ()
    assert review.insufficient_evidence_codes == ()
    assert review.operator_go_required is True
    assert review.live_integration_authorized is False


def test_safety_counter_forces_no_go_even_with_perfect_metrics() -> None:
    results = list(_mixed_results())
    results[0] = replace(
        results[0],
        case_result_id="",
        truth_gate_bypass_count=1,
    )
    report = ReaderCoreEvaluationAggregator().build_report(
        _environment(),
        results,
    )
    review = ReaderCorePromotionReviewer().review(report, _thresholds())

    assert review.decision is PromotionDecision.NO_GO
    assert review.failed_gate_codes == (
        "truth_gate_bypass_count_nonzero",
    )
    assert review.live_integration_authorized is False


def test_missing_real_and_human_corpora_is_insufficient_evidence() -> None:
    result = _result(
        _manifest("synthetic-only", EvaluationCorpusKind.SYNTHETIC)
    )
    report = ReaderCoreEvaluationAggregator().build_report(
        _environment(),
        (result,),
    )
    review = ReaderCorePromotionReviewer().review(report, _thresholds())

    assert review.decision is PromotionDecision.INSUFFICIENT_EVIDENCE
    assert "total_case_count_below_minimum" in review.insufficient_evidence_codes
    assert "real_case_count_below_minimum" in review.insufficient_evidence_codes
    assert (
        "human_labelled_case_count_below_minimum"
        in review.insufficient_evidence_codes
    )
    assert "real_corpus_not_evaluated" in report.warnings
    assert "human_labelled_corpus_not_evaluated" in report.warnings


def test_unmeasured_denominators_are_not_converted_to_fake_zeroes() -> None:
    manifest = _manifest(
        "zero-denominators",
        EvaluationCorpusKind.SYNTHETIC,
        expected_claim_count=0,
        expected_source_span_count=0,
        expected_exception_count=0,
        expected_relation_count=0,
        expected_contradiction_count=0,
        expected_qualifier_count=0,
    )
    result = ReaderEvaluationCaseResult(
        manifest=manifest,
        predicted_claim_count=0,
        matched_claim_count=0,
        predicted_source_span_count=0,
        correct_source_span_count=0,
        predicted_exception_count=0,
        matched_exception_count=0,
        predicted_relation_count=0,
        matched_relation_count=0,
        false_relation_count=0,
        matched_contradiction_count=0,
        connected_qualifier_count=0,
        source_claim_count=0,
        orphan_source_claim_count=0,
        synthesis_claim_count=0,
        unsupported_synthesis_claim_count=0,
        replay=ReaderReplayComparator.compare("zero-denominators", (), ()),
        section_latencies_ms=(),
        session_wall_time_ms=0,
        model_tokens=0,
        projection_bytes=0,
        rebuild_time_ms=0,
        query_path_latency_delta_ms=0,
        resume_reused_units=0,
        resume_eligible_units=0,
    )
    report = ReaderCoreEvaluationAggregator().build_report(
        _environment(),
        (result,),
    )
    metrics = report.metrics
    assert metrics.claim_fidelity is None
    assert metrics.source_span_precision is None
    assert metrics.critical_exception_recall is None
    assert metrics.false_relation_rate is None
    assert metrics.resume_reuse_ratio is None

    thresholds = replace(
        _thresholds(),
        thresholds_id="",
        min_total_cases=1,
        min_synthetic_cases=1,
        min_real_cases=0,
        min_human_labelled_cases=0,
        max_section_latency_p95_ms=None,
        max_model_tokens_per_case=None,
    )
    review = ReaderCorePromotionReviewer().review(report, thresholds)
    assert review.decision is PromotionDecision.INSUFFICIENT_EVIDENCE
    assert "claim_fidelity_not_measured" in review.insufficient_evidence_codes
    assert "resume_reuse_ratio_not_measured" in review.insufficient_evidence_codes


def test_quality_and_latency_threshold_failures_produce_no_go() -> None:
    results = list(_mixed_results())
    weak = results[1]
    results[1] = replace(
        weak,
        case_result_id="",
        matched_exception_count=0,
        matched_contradiction_count=0,
        false_relation_count=1,
        orphan_source_claim_count=1,
        unsupported_synthesis_claim_count=1,
        query_path_latency_delta_ms=20,
    )
    report = ReaderCoreEvaluationAggregator().build_report(
        _environment(),
        results,
    )
    review = ReaderCorePromotionReviewer().review(report, _thresholds())

    assert review.decision is PromotionDecision.NO_GO
    assert "critical_exception_recall_below_threshold" in review.failed_gate_codes
    assert "contradiction_recall_below_threshold" in review.failed_gate_codes
    assert "false_relation_rate_above_threshold" in review.failed_gate_codes
    assert "orphan_claim_rate_above_threshold" in review.failed_gate_codes
    assert (
        "unsupported_synthesis_rate_above_threshold"
        in review.failed_gate_codes
    )
    assert "query_path_latency_delta_above_threshold" in review.failed_gate_codes


def test_report_rejects_forged_metrics_and_ids() -> None:
    report = ReaderCoreEvaluationAggregator().build_report(
        _environment(),
        _mixed_results(),
    )
    forged_metrics = replace(
        report.metrics,
        metrics_id="",
        total_model_tokens=report.metrics.total_model_tokens + 1,
    )
    with pytest.raises(ReaderEvaluationError, match="exactly match"):
        replace(
            report,
            report_id="",
            metrics=forged_metrics,
        )
    with pytest.raises(ReaderEvaluationError, match="report_id"):
        replace(report, warnings=("forged",))


def test_promotion_review_can_never_authorize_live_integration() -> None:
    report = ReaderCoreEvaluationAggregator().build_report(
        _environment(),
        _mixed_results(),
    )
    review = ReaderCorePromotionReviewer().review(report, _thresholds())
    with pytest.raises(ReaderEvaluationError, match="cannot authorize"):
        replace(
            review,
            review_id="",
            live_integration_authorized=True,
        )
