"""Local, explicit Reader Core benchmark execution for PR-RDR-14.

The executor binds one verified corpus descriptor and one adjudicated label set to
an external local pipeline adapter. It runs the adapter twice for replay,
normalizes both outputs, scores them with PR-RDR-12, and emits a PR-RDR-13 batch
receipt. It grants no network, query, memory, Canon, graph, tool, scheduler, or
live-integration authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.reader_benchmark_batch import (
    BatchCaseStatus,
    ReaderBenchmarkBatchCheckpoint,
    ReaderBenchmarkCaseReceipt,
)
from core.reader_benchmark_runner import ReaderBenchmarkObservation
from core.reader_benchmark_scoring import (
    DeterministicReaderGoldScorer,
    ReaderDocumentPrediction,
    ReaderExecutionMeasurement,
)
from core.reader_core_contracts import stable_reader_core_id
from core.reader_corpus_adjudication import (
    CorpusDocumentDescriptor,
    HumanLabelSet,
    LabelSetRole,
)

READER_LOCAL_EXECUTOR_SCHEMA_VERSION = "reader-core.local-executor.v1"


class ReaderLocalExecutionError(ValueError):
    """Raised when local execution inputs or outputs violate invariants."""


@dataclass(frozen=True, slots=True)
class ReaderLocalBenchmarkCase:
    case_id: str
    descriptor: CorpusDocumentDescriptor
    gold: HumanLabelSet
    schema_version: str = READER_LOCAL_EXECUTOR_SCHEMA_VERSION
    case_spec_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
        if self.schema_version != READER_LOCAL_EXECUTOR_SCHEMA_VERSION:
            raise ReaderLocalExecutionError("unsupported local executor schema")
        if not isinstance(self.descriptor, CorpusDocumentDescriptor):
            raise ReaderLocalExecutionError(
                "descriptor must be a CorpusDocumentDescriptor"
            )
        if not isinstance(self.gold, HumanLabelSet):
            raise ReaderLocalExecutionError("gold must be a HumanLabelSet")
        if self.gold.role is not LabelSetRole.ADJUDICATED:
            raise ReaderLocalExecutionError("gold labels must be adjudicated")
        if (
            self.gold.document_descriptor_id != self.descriptor.descriptor_id
            or self.gold.document_id != self.descriptor.document_id
            or self.gold.source_revision != self.descriptor.source_revision
        ):
            raise ReaderLocalExecutionError(
                "gold labels must match corpus descriptor identity"
            )
        expected = stable_reader_core_id(
            "reader-local-benchmark-case",
            self.identity_payload(include_id=False),
        )
        if self.case_spec_id:
            if self.case_spec_id != expected:
                raise ReaderLocalExecutionError(
                    "case_spec_id does not match case content"
                )
        else:
            object.__setattr__(self, "case_spec_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "descriptor_id": self.descriptor.descriptor_id,
            "gold_label_set_id": self.gold.label_set_id,
        }
        if include_id:
            payload["case_spec_id"] = self.case_spec_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderLocalPipelineResult:
    prediction: ReaderDocumentPrediction
    measurement: ReaderExecutionMeasurement
    run_artifact_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.prediction, ReaderDocumentPrediction):
            raise ReaderLocalExecutionError(
                "prediction must be a ReaderDocumentPrediction"
            )
        if not isinstance(self.measurement, ReaderExecutionMeasurement):
            raise ReaderLocalExecutionError(
                "measurement must be a ReaderExecutionMeasurement"
            )
        artifacts = _unique_sorted_text(
            self.run_artifact_ids,
            "run_artifact_id",
        )
        object.__setattr__(self, "run_artifact_ids", artifacts)


class ReaderLocalPipeline(Protocol):
    """Explicit local adapter implemented outside this authority-free layer."""

    def run_case(
        self,
        case: ReaderLocalBenchmarkCase,
        *,
        replay_index: int,
    ) -> ReaderLocalPipelineResult: ...


@dataclass(frozen=True, slots=True)
class ReaderLocalExecutionResult:
    receipt: ReaderBenchmarkCaseReceipt
    observation: ReaderBenchmarkObservation | None

    def __post_init__(self) -> None:
        if not isinstance(self.receipt, ReaderBenchmarkCaseReceipt):
            raise ReaderLocalExecutionError(
                "receipt must be a ReaderBenchmarkCaseReceipt"
            )
        if self.receipt.status is BatchCaseStatus.SUCCEEDED:
            if self.observation is None:
                raise ReaderLocalExecutionError(
                    "successful execution requires an observation"
                )
            if self.receipt.observation_id != self.observation.observation_id:
                raise ReaderLocalExecutionError(
                    "receipt observation_id must match observation"
                )
        elif self.observation is not None:
            raise ReaderLocalExecutionError(
                "non-success execution cannot expose an observation"
            )


class ReaderLocalBenchmarkExecutor:
    """Execute exactly one pending case through an explicit local adapter."""

    def __init__(self, scorer: DeterministicReaderGoldScorer | None = None) -> None:
        self._scorer = scorer or DeterministicReaderGoldScorer()

    def execute_case(
        self,
        *,
        checkpoint: ReaderBenchmarkBatchCheckpoint,
        case: ReaderLocalBenchmarkCase,
        pipeline: ReaderLocalPipeline,
    ) -> ReaderLocalExecutionResult:
        if not isinstance(checkpoint, ReaderBenchmarkBatchCheckpoint):
            raise ReaderLocalExecutionError(
                "checkpoint must be a ReaderBenchmarkBatchCheckpoint"
            )
        if case.case_id not in checkpoint.plan.case_ids:
            raise ReaderLocalExecutionError("case is not present in the batch plan")
        if case.case_id not in checkpoint.pending_case_ids:
            raise ReaderLocalExecutionError("case is not pending in the checkpoint")

        previous = checkpoint.latest_receipts.get(case.case_id)
        attempt = 1 if previous is None else previous.attempt + 1
        if attempt > checkpoint.plan.max_attempts_per_case:
            raise ReaderLocalExecutionError("case attempt exceeds batch plan limit")

        try:
            first = pipeline.run_case(case, replay_index=1)
            replay = pipeline.run_case(case, replay_index=2)
            self._validate_pipeline_result(case, first)
            self._validate_pipeline_result(case, replay)
            observation = self._scorer.score(
                gold=case.gold,
                first=first.prediction,
                replay=replay.prediction,
                measurement=first.measurement,
            )
            artifact_ids = tuple(
                sorted(
                    {
                        case.case_spec_id,
                        first.prediction.prediction_id,
                        replay.prediction.prediction_id,
                        *first.run_artifact_ids,
                        *replay.run_artifact_ids,
                    }
                )
            )
            receipt = ReaderBenchmarkCaseReceipt(
                plan_id=checkpoint.plan.plan_id,
                case_id=case.case_id,
                status=BatchCaseStatus.SUCCEEDED,
                attempt=attempt,
                observation_id=observation.observation_id,
                artifact_ids=artifact_ids,
            )
            return ReaderLocalExecutionResult(
                receipt=receipt,
                observation=observation,
            )
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as exc:
            error_code = _stable_error_code(exc)
            receipt = ReaderBenchmarkCaseReceipt(
                plan_id=checkpoint.plan.plan_id,
                case_id=case.case_id,
                status=BatchCaseStatus.FAILED,
                attempt=attempt,
                error_code=error_code,
                artifact_ids=(case.case_spec_id,),
            )
            return ReaderLocalExecutionResult(receipt=receipt, observation=None)

    @staticmethod
    def _validate_pipeline_result(
        case: ReaderLocalBenchmarkCase,
        result: ReaderLocalPipelineResult,
    ) -> None:
        if not isinstance(result, ReaderLocalPipelineResult):
            raise ReaderLocalExecutionError(
                "pipeline must return ReaderLocalPipelineResult"
            )
        prediction = result.prediction
        if (
            prediction.document_descriptor_id != case.descriptor.descriptor_id
            or prediction.document_id != case.descriptor.document_id
            or prediction.source_revision != case.descriptor.source_revision
        ):
            raise ReaderLocalExecutionError(
                "pipeline prediction must match benchmark case identity"
            )


def _stable_error_code(exc: Exception) -> str:
    return stable_reader_core_id(
        "reader-local-execution-error",
        {
            "exception_type": type(exc).__name__,
            "message": str(exc),
        },
    )


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderLocalExecutionError(f"{field_name} must be non-empty text")
    return value


def _unique_sorted_text(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    items = tuple(values)
    for item in items:
        _require_text(item, field_name)
    if len(set(items)) != len(items):
        raise ReaderLocalExecutionError(f"{field_name} values must be unique")
    return tuple(sorted(items))
