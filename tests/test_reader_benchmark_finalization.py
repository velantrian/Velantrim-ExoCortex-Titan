from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from hashlib import sha256

import pytest

from core.knowledge_capsule import ClaimModality, SourceSpan
from core.reader_benchmark_batch import ReaderBenchmarkBatchPlanner
from core.reader_benchmark_executor import (
    ReaderLocalBenchmarkCase,
    ReaderLocalPipelineResult,
)
from core.reader_benchmark_finalization import (
    ReaderBenchmarkFinalizationError,
    ReaderCompletedBatchFinalizer,
)
from core.reader_benchmark_preparation import (
    ReaderBenchmarkPreparationBundle,
    ReaderPreparedBenchmarkCase,
)
from core.reader_benchmark_scoring import (
    ReaderClaimPrediction,
    ReaderDocumentPrediction,
    ReaderExecutionMeasurement,
)
from core.reader_corpus_adjudication import (
    CorpusDocumentDescriptor,
    CorpusPrivacyClass,
    CorpusUsageBasis,
    HumanClaimLabel,
    HumanLabelSet,
    LabelSetRole,
)
from core.reader_evaluation import (
    EvaluationCorpusKind,
    EvaluationCorpusManifest,
    EvaluationEnvironment,
    PromotionDecision,
    ReaderEvaluationCaseManifest,
    ReaderPromotionThresholds,
)
from core.reader_prepared_batch_runner import (
    PreparedBatchExecutionStatus,
    ReaderPreparedBatchRunner,
)


class _DeterministicPipeline:
    def __init__(
        self,
        *,
        failures_before_success: dict[str, int] | None = None,
    ) -> None:
        self._failures_remaining = dict(failures_before_success or {})
        self.calls: dict[str, int] = defaultdict(int)

    def run_case(
        self,
        case: ReaderLocalBenchmarkCase,
        *,
        replay_index: int,
    ) -> ReaderLocalPipelineResult:
        self.calls[case.case_id] += 1
        if replay_index == 1 and self._failures_remaining.get(case.case_id, 0) > 0:
            self._failures_remaining[case.case_id] -= 1
            raise RuntimeError(f"planned failure: {case.case_id}")
        claims = tuple(
            sorted(
                (
                    ReaderClaimPrediction.create(
                        source_claim_id=claim.label_id,
                        document_id=case.descriptor.document_id,
                        source_revision=case.descriptor.source_revision,
                        modality=claim.modality,
                        source_spans=claim.source_spans,
                        qualifier_codes=claim.qualifier_codes,
                        applicability_codes=claim.applicability_codes,
                    )
                    for claim in case.gold.claims
                ),
                key=lambda item: item.prediction_id,
            )
        )
        prediction = ReaderDocumentPrediction(
            document_descriptor_id=case.descriptor.descriptor_id,
            document_id=case.descriptor.document_id,
            source_revision=case.descriptor.source_revision,
            claims=claims,
            artifact_ids=(f"prediction-artifact:{case.case_id}",),
        )
        measurement = ReaderExecutionMeasurement(
            section_latencies_ms=(5,),
            session_wall_time_ms=10,
            model_tokens=0,
            projection_bytes=128,
            rebuild_time_ms=2,
            query_path_latency_delta_ms=0,
            resume_reused_units=0,
            resume_eligible_units=0,
        )
        return ReaderLocalPipelineResult(
            prediction=prediction,
            measurement=measurement,
            run_artifact_ids=(f"run-artifact:{case.case_id}",),
        )


def _environment() -> EvaluationEnvironment:
    return EvaluationEnvironment(
        commit_sha="commit-finalization-001",
        runner_id="runner-finalization-001",
        python_version="3.11",
        hardware_profile="test-cpu",
        config_digest="config-finalization-001",
    )


def _thresholds(*, min_total_cases: int = 1) -> ReaderPromotionThresholds:
    return ReaderPromotionThresholds(
        min_total_cases=min_total_cases,
        min_synthetic_cases=0,
        min_real_cases=0,
        min_human_labelled_cases=1,
        min_claim_fidelity=1.0,
        min_source_span_precision=1.0,
        min_source_span_recall=1.0,
        min_critical_exception_recall=0.0,
        min_relation_recall=0.0,
        max_false_relation_rate=1.0,
        min_contradiction_recall=0.0,
        max_orphan_claim_rate=1.0,
        min_qualifier_connectivity=0.0,
        max_unsupported_synthesis_rate=1.0,
        min_replay_match_rate=1.0,
        min_resume_reuse_ratio=0.0,
        max_query_path_latency_delta_ms=0,
    )


def _prepared_case(index: int) -> ReaderPreparedBenchmarkCase:
    document_id = f"finalization-document-{index:02d}"
    raw_text = f"Claim for finalization case {index}."
    revision = sha256(raw_text.encode("utf-8")).hexdigest()
    descriptor = CorpusDocumentDescriptor(
        document_id=document_id,
        relative_path=f"documents/{document_id}.txt",
        source_revision=revision,
        content_sha256=revision,
        byte_size=len(raw_text.encode("utf-8")),
        char_count=len(raw_text),
        media_type="text/plain; charset=utf-8",
        usage_basis=CorpusUsageBasis.SYNTHETIC,
        rights_reference="project-authored-test-fixture",
        privacy_class=CorpusPrivacyClass.PUBLIC,
        redistribution_allowed=True,
    )
    span = SourceSpan.from_text(
        document_id=document_id,
        raw_text=raw_text,
        start_offset=0,
        end_offset=len(raw_text),
        source_revision=revision,
    )
    claim = HumanClaimLabel.create(
        document_id=document_id,
        source_revision=revision,
        modality=ClaimModality.WORLD_FACT,
        source_spans=(span,),
    )
    gold = HumanLabelSet(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=document_id,
        source_revision=revision,
        annotator_id="adjudicator-finalization",
        guideline_version="guideline-finalization-v1",
        label_version="labels-finalization-v1",
        role=LabelSetRole.ADJUDICATED,
        claims=(claim,),
    )
    local_case = ReaderLocalBenchmarkCase(
        case_id=document_id,
        descriptor=descriptor,
        gold=gold,
    )
    case_manifest = ReaderEvaluationCaseManifest(
        case_id=document_id,
        corpus_kind=EvaluationCorpusKind.HUMAN_LABELLED,
        label_version=gold.label_version,
        expected_claim_count=1,
        expected_source_span_count=1,
        expected_exception_count=0,
        expected_relation_count=0,
        expected_contradiction_count=0,
        expected_qualifier_count=0,
        tags=("finalization-test", "human-adjudicated"),
    )
    return ReaderPreparedBenchmarkCase(
        evidence_case_id=f"evidence-finalization-{index:02d}",
        benchmark_case=local_case,
        evaluation_manifest=case_manifest,
    )


def _preparation(
    environment: EvaluationEnvironment,
    thresholds: ReaderPromotionThresholds,
    *,
    case_count: int = 1,
    max_attempts_per_case: int = 1,
) -> ReaderBenchmarkPreparationBundle:
    cases = tuple(_prepared_case(index) for index in range(case_count))
    manifest = EvaluationCorpusManifest(
        corpus_name="finalization-fixture",
        corpus_version="1.0.0",
        cases=tuple(item.evaluation_manifest for item in cases),
    )
    plan = ReaderBenchmarkBatchPlanner.create_plan(
        corpus_id=manifest.corpus_id,
        environment_id=environment.environment_id,
        threshold_policy_id=thresholds.thresholds_id,
        case_ids=tuple(item.benchmark_case.case_id for item in cases),
        max_attempts_per_case=max_attempts_per_case,
    )
    return ReaderBenchmarkPreparationBundle(
        evidence_pack_id="evidence-pack-finalization-001",
        evidence_import_bundle_id="evidence-import-finalization-001",
        evaluation_manifest=manifest,
        prepared_cases=cases,
        batch_plan=plan,
        initial_checkpoint=ReaderBenchmarkBatchPlanner.empty_checkpoint(plan),
    )


def _complete_state(
    preparation: ReaderBenchmarkPreparationBundle,
    environment: EvaluationEnvironment,
):
    runner = ReaderPreparedBatchRunner()
    initial = runner.initial_state(
        preparation=preparation,
        environment=environment,
    )
    return runner.run_pass(
        preparation=preparation,
        state=initial,
        pipeline=_DeterministicPipeline(),
    )


def test_complete_state_builds_authenticated_evidence() -> None:
    environment = _environment()
    thresholds = _thresholds()
    preparation = _preparation(environment, thresholds, case_count=2)
    state = _complete_state(preparation, environment)
    finalizer = ReaderCompletedBatchFinalizer()

    evidence = finalizer.finalize(
        preparation=preparation,
        state=state,
        thresholds=thresholds,
        key_id="benchmark-key-test",
        secret=b"benchmark-secret-test",
    )

    assert state.status is PreparedBatchExecutionStatus.COMPLETE_SUCCESS
    assert evidence.preparation_id == preparation.preparation_id
    assert evidence.execution_state == state
    assert evidence.benchmark_bundle.manifest == preparation.evaluation_manifest
    assert evidence.benchmark_bundle.thresholds == thresholds
    assert evidence.bundle_signature.bundle_id == evidence.benchmark_bundle.bundle_id
    assert evidence.receipt_ids == tuple(
        item.receipt_id for item in state.checkpoint.receipts
    )
    assert evidence.failed_attempt_receipt_ids == ()
    assert finalizer.verify(evidence, secret=b"benchmark-secret-test") is True
    assert finalizer.verify(evidence, secret=b"wrong-secret") is False
    assert evidence.decision is PromotionDecision.INSUFFICIENT_EVIDENCE
    assert evidence.operator_go_required is True
    assert evidence.live_integration_authorized is False


def test_finalization_is_deterministic() -> None:
    environment = _environment()
    thresholds = _thresholds()
    preparation = _preparation(environment, thresholds)
    state = _complete_state(preparation, environment)
    finalizer = ReaderCompletedBatchFinalizer()

    first = finalizer.finalize(
        preparation=preparation,
        state=state,
        thresholds=thresholds,
        key_id="benchmark-key-test",
        secret=b"benchmark-secret-test",
    )
    second = finalizer.finalize(
        preparation=preparation,
        state=state,
        thresholds=thresholds,
        key_id="benchmark-key-test",
        secret=b"benchmark-secret-test",
    )

    assert first == second
    assert first.evidence_id == second.evidence_id


def test_incomplete_and_exhausted_failed_batches_are_rejected() -> None:
    environment = _environment()
    thresholds = _thresholds()
    preparation = _preparation(environment, thresholds)
    runner = ReaderPreparedBatchRunner()
    initial = runner.initial_state(
        preparation=preparation,
        environment=environment,
    )
    case_id = preparation.batch_plan.case_ids[0]
    failed = runner.run_pass(
        preparation=preparation,
        state=initial,
        pipeline=_DeterministicPipeline(
            failures_before_success={case_id: 1}
        ),
    )
    finalizer = ReaderCompletedBatchFinalizer()

    with pytest.raises(
        ReaderBenchmarkFinalizationError,
        match="complete successful",
    ):
        finalizer.finalize(
            preparation=preparation,
            state=initial,
            thresholds=thresholds,
            key_id="benchmark-key-test",
            secret=b"benchmark-secret-test",
        )
    with pytest.raises(
        ReaderBenchmarkFinalizationError,
        match="complete successful",
    ):
        finalizer.finalize(
            preparation=preparation,
            state=failed,
            thresholds=thresholds,
            key_id="benchmark-key-test",
            secret=b"benchmark-secret-test",
        )


def test_threshold_policy_and_preparation_ownership_are_enforced() -> None:
    environment = _environment()
    thresholds = _thresholds()
    preparation = _preparation(environment, thresholds)
    state = _complete_state(preparation, environment)
    foreign_thresholds = _thresholds(min_total_cases=2)
    foreign_preparation = replace(
        preparation,
        evidence_import_bundle_id="foreign-import-bundle",
        preparation_id="",
    )
    finalizer = ReaderCompletedBatchFinalizer()

    with pytest.raises(
        ReaderBenchmarkFinalizationError,
        match="threshold policy",
    ):
        finalizer.finalize(
            preparation=preparation,
            state=state,
            thresholds=foreign_thresholds,
            key_id="benchmark-key-test",
            secret=b"benchmark-secret-test",
        )
    with pytest.raises(
        ReaderBenchmarkFinalizationError,
        match="different preparation",
    ):
        finalizer.finalize(
            preparation=foreign_preparation,
            state=state,
            thresholds=thresholds,
            key_id="benchmark-key-test",
            secret=b"benchmark-secret-test",
        )


def test_retry_history_is_retained_in_signed_evidence() -> None:
    environment = _environment()
    thresholds = _thresholds()
    preparation = _preparation(
        environment,
        thresholds,
        max_attempts_per_case=2,
    )
    case_id = preparation.batch_plan.case_ids[0]
    pipeline = _DeterministicPipeline(
        failures_before_success={case_id: 1}
    )
    runner = ReaderPreparedBatchRunner()
    initial = runner.initial_state(
        preparation=preparation,
        environment=environment,
    )
    failed = runner.run_pass(
        preparation=preparation,
        state=initial,
        pipeline=pipeline,
    )
    completed = runner.run_pass(
        preparation=preparation,
        state=failed,
        pipeline=pipeline,
    )

    evidence = ReaderCompletedBatchFinalizer().finalize(
        preparation=preparation,
        state=completed,
        thresholds=thresholds,
        key_id="benchmark-key-test",
        secret=b"benchmark-secret-test",
    )

    assert len(evidence.receipt_ids) == 2
    assert evidence.failed_attempt_receipt_ids == (
        completed.checkpoint.receipts[0].receipt_id,
    )
    expected_artifacts = tuple(
        sorted(
            {
                artifact_id
                for receipt in completed.checkpoint.receipts
                for artifact_id in receipt.artifact_ids
            }
        )
    )
    assert evidence.artifact_ids == expected_artifacts


def test_tampered_signature_and_evidence_indexes_fail_closed() -> None:
    environment = _environment()
    thresholds = _thresholds()
    preparation = _preparation(
        environment,
        thresholds,
        max_attempts_per_case=2,
    )
    case_id = preparation.batch_plan.case_ids[0]
    runner = ReaderPreparedBatchRunner()
    initial = runner.initial_state(
        preparation=preparation,
        environment=environment,
    )
    pipeline = _DeterministicPipeline(
        failures_before_success={case_id: 1}
    )
    failed = runner.run_pass(
        preparation=preparation,
        state=initial,
        pipeline=pipeline,
    )
    completed = runner.run_pass(
        preparation=preparation,
        state=failed,
        pipeline=pipeline,
    )
    finalizer = ReaderCompletedBatchFinalizer()
    evidence = finalizer.finalize(
        preparation=preparation,
        state=completed,
        thresholds=thresholds,
        key_id="benchmark-key-test",
        secret=b"benchmark-secret-test",
    )
    tampered_signature = replace(
        evidence.bundle_signature,
        signature_hex="0" * 64,
        signature_id="",
    )
    tampered_evidence = replace(
        evidence,
        bundle_signature=tampered_signature,
        evidence_id="",
    )

    assert finalizer.verify(
        tampered_evidence,
        secret=b"benchmark-secret-test",
    ) is False
    with pytest.raises(
        ReaderBenchmarkFinalizationError,
        match="receipt_ids",
    ):
        replace(
            evidence,
            receipt_ids=tuple(reversed(evidence.receipt_ids)),
            evidence_id="",
        )
    with pytest.raises(
        ReaderBenchmarkFinalizationError,
        match="artifact index",
    ):
        replace(
            evidence,
            artifact_ids=(),
            evidence_id="",
        )
    with pytest.raises(
        ReaderBenchmarkFinalizationError,
        match="evidence_id",
    ):
        replace(evidence, evidence_id="forged-evidence")
