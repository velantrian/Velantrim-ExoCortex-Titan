from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from hashlib import sha256

import pytest

from core.knowledge_capsule import ClaimModality, SourceSpan
from core.reader_benchmark_batch import (
    BatchCaseStatus,
    ReaderBenchmarkBatchPlanner,
)
from core.reader_benchmark_executor import (
    ReaderLocalBenchmarkCase,
    ReaderLocalPipelineResult,
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
    ReaderEvaluationCaseManifest,
)
from core.reader_prepared_batch_runner import (
    PreparedBatchExecutionStatus,
    ReaderPreparedBatchExecutionState,
    ReaderPreparedBatchRunner,
    ReaderPreparedBatchRunnerError,
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
        claim_predictions = tuple(
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
            claims=claim_predictions,
            artifact_ids=(f"artifact:{case.case_id}",),
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
            run_artifact_ids=(f"run:{case.case_id}",),
        )


def _environment(*, runner_id: str = "runner-local-001") -> EvaluationEnvironment:
    return EvaluationEnvironment(
        commit_sha="commit-fixed-001",
        runner_id=runner_id,
        python_version="3.11",
        hardware_profile="test-cpu",
        config_digest="config-fixed-001",
    )


def _prepared_case(index: int) -> ReaderPreparedBenchmarkCase:
    document_id = f"prepared-document-{index:02d}"
    raw_text = f"Claim for prepared case {index}."
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
        annotator_id="adjudicator-test",
        guideline_version="guideline-test-v1",
        label_version="labels-test-v1",
        role=LabelSetRole.ADJUDICATED,
        claims=(claim,),
    )
    local_case = ReaderLocalBenchmarkCase(
        case_id=document_id,
        descriptor=descriptor,
        gold=gold,
    )
    manifest = ReaderEvaluationCaseManifest(
        case_id=document_id,
        corpus_kind=EvaluationCorpusKind.HUMAN_LABELLED,
        label_version=gold.label_version,
        expected_claim_count=1,
        expected_source_span_count=1,
        expected_exception_count=0,
        expected_relation_count=0,
        expected_contradiction_count=0,
        expected_qualifier_count=0,
        tags=("human-adjudicated", "runner-test"),
    )
    return ReaderPreparedBenchmarkCase(
        evidence_case_id=f"evidence-case-{index:02d}",
        benchmark_case=local_case,
        evaluation_manifest=manifest,
    )


def _preparation(
    environment: EvaluationEnvironment,
    *,
    case_count: int = 1,
    max_attempts_per_case: int = 1,
) -> ReaderBenchmarkPreparationBundle:
    prepared_cases = tuple(_prepared_case(index) for index in range(case_count))
    evaluation_manifest = EvaluationCorpusManifest(
        corpus_name="prepared-runner-fixture",
        corpus_version="1.0.0",
        cases=tuple(item.evaluation_manifest for item in prepared_cases),
    )
    batch_plan = ReaderBenchmarkBatchPlanner.create_plan(
        corpus_id=evaluation_manifest.corpus_id,
        environment_id=environment.environment_id,
        threshold_policy_id="threshold-policy-test-001",
        case_ids=tuple(
            item.benchmark_case.case_id for item in prepared_cases
        ),
        max_attempts_per_case=max_attempts_per_case,
    )
    checkpoint = ReaderBenchmarkBatchPlanner.empty_checkpoint(batch_plan)
    return ReaderBenchmarkPreparationBundle(
        evidence_pack_id="evidence-pack-test-001",
        evidence_import_bundle_id="evidence-import-test-001",
        evaluation_manifest=evaluation_manifest,
        prepared_cases=prepared_cases,
        batch_plan=batch_plan,
        initial_checkpoint=checkpoint,
    )


def test_initial_state_is_empty_and_not_reportable() -> None:
    environment = _environment()
    preparation = _preparation(environment)

    state = ReaderPreparedBatchRunner.initial_state(
        preparation=preparation,
        environment=environment,
    )

    assert state.status is PreparedBatchExecutionStatus.READY
    assert state.pass_count == 0
    assert state.checkpoint.receipts == ()
    assert state.observations == ()
    with pytest.raises(
        ReaderPreparedBatchRunnerError,
        match="complete successful",
    ):
        state.to_benchmark_input()


def test_successful_pass_builds_complete_benchmark_input() -> None:
    environment = _environment()
    preparation = _preparation(environment, case_count=2)
    runner = ReaderPreparedBatchRunner()
    initial = runner.initial_state(
        preparation=preparation,
        environment=environment,
    )

    completed = runner.run_pass(
        preparation=preparation,
        state=initial,
        pipeline=_DeterministicPipeline(),
    )

    assert completed.status is PreparedBatchExecutionStatus.COMPLETE_SUCCESS
    assert completed.pass_count == 1
    assert len(completed.checkpoint.receipts) == 2
    assert all(
        item.status is BatchCaseStatus.SUCCEEDED
        for item in completed.checkpoint.receipts
    )
    assert completed.successful_case_ids == preparation.batch_plan.case_ids
    benchmark_input = completed.to_benchmark_input()
    assert benchmark_input.environment == environment
    assert tuple(
        item.case_id for item in benchmark_input.observations
    ) == preparation.batch_plan.case_ids


def test_max_cases_bounds_each_explicit_pass() -> None:
    environment = _environment()
    preparation = _preparation(environment, case_count=2)
    runner = ReaderPreparedBatchRunner()
    initial = runner.initial_state(
        preparation=preparation,
        environment=environment,
    )
    pipeline = _DeterministicPipeline()

    first = runner.run_pass(
        preparation=preparation,
        state=initial,
        pipeline=pipeline,
        max_cases=1,
    )
    second = runner.run_pass(
        preparation=preparation,
        state=first,
        pipeline=pipeline,
        max_cases=1,
    )

    assert first.status is PreparedBatchExecutionStatus.IN_PROGRESS
    assert len(first.checkpoint.receipts) == 1
    assert len(first.observations) == 1
    assert second.status is PreparedBatchExecutionStatus.COMPLETE_SUCCESS
    assert len(second.checkpoint.receipts) == 2
    assert second.pass_count == 2


def test_failed_case_retries_only_on_next_explicit_pass() -> None:
    environment = _environment()
    preparation = _preparation(
        environment,
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

    assert failed.status is PreparedBatchExecutionStatus.IN_PROGRESS
    assert failed.failed_case_ids == (case_id,)
    assert failed.observations == ()
    assert len(failed.checkpoint.receipts) == 1
    assert failed.checkpoint.receipts[0].attempt == 1
    assert pipeline.calls[case_id] == 1

    completed = runner.run_pass(
        preparation=preparation,
        state=failed,
        pipeline=pipeline,
    )

    assert completed.status is PreparedBatchExecutionStatus.COMPLETE_SUCCESS
    assert len(completed.checkpoint.receipts) == 2
    assert tuple(item.attempt for item in completed.checkpoint.receipts) == (1, 2)
    assert tuple(item.status for item in completed.checkpoint.receipts) == (
        BatchCaseStatus.FAILED,
        BatchCaseStatus.SUCCEEDED,
    )
    assert completed.failed_case_ids == ()
    assert completed.successful_case_ids == (case_id,)
    assert pipeline.calls[case_id] == 3


def test_exhausted_failure_is_complete_but_not_reportable() -> None:
    environment = _environment()
    preparation = _preparation(environment, max_attempts_per_case=1)
    case_id = preparation.batch_plan.case_ids[0]
    runner = ReaderPreparedBatchRunner()
    initial = runner.initial_state(
        preparation=preparation,
        environment=environment,
    )

    failed = runner.run_pass(
        preparation=preparation,
        state=initial,
        pipeline=_DeterministicPipeline(
            failures_before_success={case_id: 1}
        ),
    )

    assert (
        failed.status
        is PreparedBatchExecutionStatus.COMPLETE_WITH_FAILURES
    )
    assert failed.failed_case_ids == (case_id,)
    assert failed.observations == ()
    with pytest.raises(
        ReaderPreparedBatchRunnerError,
        match="complete successful",
    ):
        failed.to_benchmark_input()
    with pytest.raises(
        ReaderPreparedBatchRunnerError,
        match="completed",
    ):
        runner.run_pass(
            preparation=preparation,
            state=failed,
            pipeline=_DeterministicPipeline(),
        )


def test_one_pass_never_exhausts_multiple_retry_attempts() -> None:
    environment = _environment()
    preparation = _preparation(environment, max_attempts_per_case=3)
    case_id = preparation.batch_plan.case_ids[0]
    runner = ReaderPreparedBatchRunner()
    initial = runner.initial_state(
        preparation=preparation,
        environment=environment,
    )

    first = runner.run_pass(
        preparation=preparation,
        state=initial,
        pipeline=_DeterministicPipeline(
            failures_before_success={case_id: 3}
        ),
    )

    assert first.status is PreparedBatchExecutionStatus.IN_PROGRESS
    assert len(first.checkpoint.receipts) == 1
    assert first.checkpoint.receipts[0].attempt == 1
    assert first.checkpoint.pending_case_ids == (case_id,)


def test_state_rejects_observation_without_success_receipt() -> None:
    environment = _environment()
    preparation = _preparation(environment)
    runner = ReaderPreparedBatchRunner()
    initial = runner.initial_state(
        preparation=preparation,
        environment=environment,
    )
    completed = runner.run_pass(
        preparation=preparation,
        state=initial,
        pipeline=_DeterministicPipeline(),
    )

    with pytest.raises(
        ReaderPreparedBatchRunnerError,
        match="exactly match",
    ):
        replace(
            completed,
            checkpoint=preparation.initial_checkpoint,
            state_id="",
        )


def test_foreign_environment_and_state_are_rejected() -> None:
    environment = _environment()
    preparation = _preparation(environment)
    runner = ReaderPreparedBatchRunner()
    foreign_environment = _environment(runner_id="runner-foreign")

    with pytest.raises(
        ReaderPreparedBatchRunnerError,
        match="does not match",
    ):
        runner.initial_state(
            preparation=preparation,
            environment=foreign_environment,
        )

    initial = runner.initial_state(
        preparation=preparation,
        environment=environment,
    )
    foreign_preparation = replace(
        preparation,
        preparation_id="",
        evidence_import_bundle_id="foreign-import-bundle",
    )
    with pytest.raises(
        ReaderPreparedBatchRunnerError,
        match="different preparation",
    ):
        runner.run_pass(
            preparation=foreign_preparation,
            state=initial,
            pipeline=_DeterministicPipeline(),
        )


def test_forged_state_identity_and_invalid_max_cases_are_rejected() -> None:
    environment = _environment()
    preparation = _preparation(environment)
    runner = ReaderPreparedBatchRunner()
    state = runner.initial_state(
        preparation=preparation,
        environment=environment,
    )

    with pytest.raises(ReaderPreparedBatchRunnerError, match="state_id"):
        replace(state, state_id="forged-state")
    with pytest.raises(ReaderPreparedBatchRunnerError, match="max_cases"):
        runner.run_pass(
            preparation=preparation,
            state=state,
            pipeline=_DeterministicPipeline(),
            max_cases=0,
        )
