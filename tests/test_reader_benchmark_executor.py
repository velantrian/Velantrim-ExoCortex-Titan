from dataclasses import replace
from hashlib import sha256

import pytest

from core.knowledge_capsule import ClaimModality, SourceSpan
from core.reader_benchmark_batch import (
    BatchCaseStatus,
    ReaderBenchmarkBatchCheckpoint,
    ReaderBenchmarkBatchPlanner,
)
from core.reader_benchmark_executor import (
    ReaderLocalBenchmarkCase,
    ReaderLocalBenchmarkExecutor,
    ReaderLocalExecutionError,
    ReaderLocalPipelineResult,
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


TEXT = "Alpha is required."
REVISION = sha256(TEXT.encode("utf-8")).hexdigest()


def _descriptor() -> CorpusDocumentDescriptor:
    return CorpusDocumentDescriptor(
        document_id="doc-a",
        relative_path="doc-a.txt",
        source_revision=REVISION,
        content_sha256=REVISION,
        byte_size=len(TEXT.encode("utf-8")),
        char_count=len(TEXT),
        media_type="text/plain",
        usage_basis=CorpusUsageBasis.SYNTHETIC,
        rights_reference="fixture",
        privacy_class=CorpusPrivacyClass.PUBLIC,
        redistribution_allowed=True,
    )


def _span() -> SourceSpan:
    return SourceSpan.from_text(
        document_id="doc-a",
        raw_text=TEXT,
        start_offset=0,
        end_offset=len(TEXT),
        source_revision=REVISION,
    )


def _gold(descriptor: CorpusDocumentDescriptor) -> HumanLabelSet:
    claim = HumanClaimLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=ClaimModality.WORLD_FACT,
        source_spans=(_span(),),
    )
    return HumanLabelSet(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        annotator_id="adjudicator",
        guideline_version="g1",
        label_version="l1",
        role=LabelSetRole.ADJUDICATED,
        claims=(claim,),
    )


def _prediction(descriptor: CorpusDocumentDescriptor) -> ReaderDocumentPrediction:
    claim = ReaderClaimPrediction.create(
        source_claim_id="claim-a",
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=ClaimModality.WORLD_FACT,
        source_spans=(_span(),),
    )
    return ReaderDocumentPrediction(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        claims=(claim,),
        artifact_ids=("artifact-a",),
    )


def _measurement() -> ReaderExecutionMeasurement:
    return ReaderExecutionMeasurement(
        section_latencies_ms=(5,),
        session_wall_time_ms=10,
        model_tokens=0,
        projection_bytes=100,
        rebuild_time_ms=2,
        query_path_latency_delta_ms=0,
        resume_reused_units=0,
        resume_eligible_units=0,
    )


def _case() -> ReaderLocalBenchmarkCase:
    descriptor = _descriptor()
    return ReaderLocalBenchmarkCase(
        case_id="case-a",
        descriptor=descriptor,
        gold=_gold(descriptor),
    )


def _checkpoint(case: ReaderLocalBenchmarkCase) -> ReaderBenchmarkBatchCheckpoint:
    plan = ReaderBenchmarkBatchPlanner.create_plan(
        corpus_id="corpus-a",
        environment_id="environment-a",
        threshold_policy_id="thresholds-a",
        case_ids=(case.case_id,),
        max_attempts_per_case=2,
    )
    return ReaderBenchmarkBatchPlanner.empty_checkpoint(plan)


class _Pipeline:
    def __init__(self, case: ReaderLocalBenchmarkCase) -> None:
        self.case = case
        self.calls: list[int] = []

    def run_case(
        self,
        case: ReaderLocalBenchmarkCase,
        *,
        replay_index: int,
    ) -> ReaderLocalPipelineResult:
        assert case == self.case
        self.calls.append(replay_index)
        return ReaderLocalPipelineResult(
            prediction=_prediction(case.descriptor),
            measurement=_measurement(),
            run_artifact_ids=(f"run-{replay_index}",),
        )


class _FailingPipeline:
    def run_case(
        self,
        case: ReaderLocalBenchmarkCase,
        *,
        replay_index: int,
    ) -> ReaderLocalPipelineResult:
        raise RuntimeError(f"failed-{case.case_id}-{replay_index}")


def test_executor_runs_twice_scores_and_emits_success_receipt() -> None:
    case = _case()
    checkpoint = _checkpoint(case)
    pipeline = _Pipeline(case)

    result = ReaderLocalBenchmarkExecutor().execute_case(
        checkpoint=checkpoint,
        case=case,
        pipeline=pipeline,
    )

    assert pipeline.calls == [1, 2]
    assert result.receipt.status is BatchCaseStatus.SUCCEEDED
    assert result.observation is not None
    assert result.receipt.observation_id == result.observation.observation_id
    assert result.observation.matched_claim_count == 1
    assert "run-1" in result.receipt.artifact_ids
    assert "run-2" in result.receipt.artifact_ids


def test_executor_converts_pipeline_failure_to_stable_failed_receipt() -> None:
    case = _case()
    result = ReaderLocalBenchmarkExecutor().execute_case(
        checkpoint=_checkpoint(case),
        case=case,
        pipeline=_FailingPipeline(),
    )

    assert result.receipt.status is BatchCaseStatus.FAILED
    assert result.receipt.error_code is not None
    assert result.observation is None


def test_retry_attempt_is_derived_from_checkpoint() -> None:
    case = _case()
    checkpoint = _checkpoint(case)
    first = ReaderLocalBenchmarkExecutor().execute_case(
        checkpoint=checkpoint,
        case=case,
        pipeline=_FailingPipeline(),
    )
    retriable = ReaderBenchmarkBatchPlanner.append_receipt(
        checkpoint,
        first.receipt,
    )

    second = ReaderLocalBenchmarkExecutor().execute_case(
        checkpoint=retriable,
        case=case,
        pipeline=_Pipeline(case),
    )
    assert second.receipt.attempt == 2
    assert second.receipt.status is BatchCaseStatus.SUCCEEDED


def test_executor_rejects_non_pending_case() -> None:
    case = _case()
    checkpoint = _checkpoint(case)
    success = ReaderLocalBenchmarkExecutor().execute_case(
        checkpoint=checkpoint,
        case=case,
        pipeline=_Pipeline(case),
    )
    complete = ReaderBenchmarkBatchPlanner.append_receipt(
        checkpoint,
        success.receipt,
    )

    with pytest.raises(ReaderLocalExecutionError, match="not pending"):
        ReaderLocalBenchmarkExecutor().execute_case(
            checkpoint=complete,
            case=case,
            pipeline=_Pipeline(case),
        )


def test_case_rejects_non_adjudicated_gold() -> None:
    descriptor = _descriptor()
    gold = replace(
        _gold(descriptor),
        role=LabelSetRole.ANNOTATOR,
        label_set_id="",
    )
    with pytest.raises(ReaderLocalExecutionError, match="adjudicated"):
        ReaderLocalBenchmarkCase(
            case_id="case-a",
            descriptor=descriptor,
            gold=gold,
        )


def test_foreign_prediction_becomes_failed_receipt() -> None:
    case = _case()

    class ForeignPipeline:
        def run_case(
            self,
            case: ReaderLocalBenchmarkCase,
            *,
            replay_index: int,
        ) -> ReaderLocalPipelineResult:
            prediction = replace(
                _prediction(case.descriptor),
                document_descriptor_id="foreign",
                prediction_id="",
            )
            return ReaderLocalPipelineResult(
                prediction=prediction,
                measurement=_measurement(),
            )

    result = ReaderLocalBenchmarkExecutor().execute_case(
        checkpoint=_checkpoint(case),
        case=case,
        pipeline=ForeignPipeline(),
    )
    assert result.receipt.status is BatchCaseStatus.FAILED
    assert result.observation is None
