"""Explicit local prepared-batch execution for Reader Core PR-RDR-20.

The runner consumes an RDR-19 preparation bundle and a caller-supplied local
pipeline adapter. Each pass processes every selected pending case at most once,
appends the resulting RDR-13 receipt, and retains successful observations. It
never selects a provider, schedules background work, hides failures, or grants
promotion or live authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.reader_benchmark_batch import (
    BatchCaseStatus,
    ReaderBenchmarkBatchCheckpoint,
    ReaderBenchmarkBatchPlanner,
)
from core.reader_benchmark_executor import (
    ReaderLocalBenchmarkExecutor,
    ReaderLocalPipeline,
)
from core.reader_benchmark_preparation import ReaderBenchmarkPreparationBundle
from core.reader_benchmark_runner import (
    ReaderBenchmarkInput,
    ReaderBenchmarkObservation,
)
from core.reader_core_contracts import stable_reader_core_id
from core.reader_evaluation import EvaluationEnvironment

READER_PREPARED_BATCH_RUNNER_SCHEMA_VERSION = (
    "reader-core.prepared-batch-runner.v1"
)


class ReaderPreparedBatchRunnerError(ValueError):
    """Raised when prepared execution state or pass invariants are invalid."""


class PreparedBatchExecutionStatus(str, Enum):
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETE_SUCCESS = "complete_success"
    COMPLETE_WITH_FAILURES = "complete_with_failures"


@dataclass(frozen=True, slots=True)
class ReaderPreparedBatchExecutionState:
    preparation_id: str
    environment: EvaluationEnvironment
    checkpoint: ReaderBenchmarkBatchCheckpoint
    observations: tuple[ReaderBenchmarkObservation, ...] = ()
    pass_count: int = 0
    schema_version: str = READER_PREPARED_BATCH_RUNNER_SCHEMA_VERSION
    state_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.preparation_id, "preparation_id")
        if self.schema_version != READER_PREPARED_BATCH_RUNNER_SCHEMA_VERSION:
            raise ReaderPreparedBatchRunnerError(
                "unsupported prepared batch runner schema"
            )
        if not isinstance(self.environment, EvaluationEnvironment):
            raise ReaderPreparedBatchRunnerError(
                "environment must be an EvaluationEnvironment"
            )
        if not isinstance(self.checkpoint, ReaderBenchmarkBatchCheckpoint):
            raise ReaderPreparedBatchRunnerError(
                "checkpoint must be a ReaderBenchmarkBatchCheckpoint"
            )
        if (
            self.environment.environment_id
            != self.checkpoint.plan.environment_id
        ):
            raise ReaderPreparedBatchRunnerError(
                "environment must match checkpoint batch plan"
            )
        if (
            isinstance(self.pass_count, bool)
            or not isinstance(self.pass_count, int)
            or self.pass_count < 0
        ):
            raise ReaderPreparedBatchRunnerError(
                "pass_count must be a non-negative integer"
            )
        observations = tuple(self.observations)
        if any(
            not isinstance(item, ReaderBenchmarkObservation)
            for item in observations
        ):
            raise ReaderPreparedBatchRunnerError(
                "observations require ReaderBenchmarkObservation values"
            )
        ordered = tuple(sorted(observations, key=lambda item: item.case_id))
        if observations != ordered:
            raise ReaderPreparedBatchRunnerError(
                "observations must use canonical case ordering"
            )
        if len({item.case_id for item in observations}) != len(observations):
            raise ReaderPreparedBatchRunnerError(
                "observation case IDs must be unique"
            )
        plan_case_ids = set(self.checkpoint.plan.case_ids)
        if any(item.case_id not in plan_case_ids for item in observations):
            raise ReaderPreparedBatchRunnerError(
                "observation belongs to a case outside the batch plan"
            )
        observation_by_case = {item.case_id: item for item in observations}
        successful_latest_receipts = {
            case_id: receipt
            for case_id, receipt in self.checkpoint.latest_receipts.items()
            if receipt.status is BatchCaseStatus.SUCCEEDED
        }
        if set(observation_by_case) != set(successful_latest_receipts):
            raise ReaderPreparedBatchRunnerError(
                "observations must exactly match latest successful receipts"
            )
        for case_id, receipt in successful_latest_receipts.items():
            observation = observation_by_case[case_id]
            if receipt.observation_id != observation.observation_id:
                raise ReaderPreparedBatchRunnerError(
                    "receipt observation_id must match retained observation"
                )
        object.__setattr__(self, "observations", observations)
        expected = stable_reader_core_id(
            "reader-prepared-batch-execution-state",
            self.identity_payload(include_id=False),
        )
        if self.state_id:
            if self.state_id != expected:
                raise ReaderPreparedBatchRunnerError(
                    "state_id does not match prepared execution state"
                )
        else:
            object.__setattr__(self, "state_id", expected)

    @property
    def status(self) -> PreparedBatchExecutionStatus:
        if self.checkpoint.is_complete:
            latest = self.checkpoint.latest_receipts
            if all(
                item.status is BatchCaseStatus.SUCCEEDED
                for item in latest.values()
            ):
                return PreparedBatchExecutionStatus.COMPLETE_SUCCESS
            return PreparedBatchExecutionStatus.COMPLETE_WITH_FAILURES
        if self.checkpoint.receipts:
            return PreparedBatchExecutionStatus.IN_PROGRESS
        return PreparedBatchExecutionStatus.READY

    @property
    def successful_case_ids(self) -> tuple[str, ...]:
        return tuple(item.case_id for item in self.observations)

    @property
    def failed_case_ids(self) -> tuple[str, ...]:
        return tuple(
            case_id
            for case_id, receipt in sorted(
                self.checkpoint.latest_receipts.items()
            )
            if receipt.status is BatchCaseStatus.FAILED
        )

    @property
    def skipped_case_ids(self) -> tuple[str, ...]:
        return tuple(
            case_id
            for case_id, receipt in sorted(
                self.checkpoint.latest_receipts.items()
            )
            if receipt.status is BatchCaseStatus.SKIPPED
        )

    def to_benchmark_input(self) -> ReaderBenchmarkInput:
        if self.status is not PreparedBatchExecutionStatus.COMPLETE_SUCCESS:
            raise ReaderPreparedBatchRunnerError(
                "benchmark input requires complete successful execution"
            )
        return ReaderBenchmarkInput(
            environment=self.environment,
            observations=self.observations,
        )

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "preparation_id": self.preparation_id,
            "environment_id": self.environment.environment_id,
            "checkpoint_id": self.checkpoint.checkpoint_id,
            "observation_ids": [
                item.observation_id for item in self.observations
            ],
            "pass_count": self.pass_count,
        }
        if include_id:
            payload["state_id"] = self.state_id
        return payload


class ReaderPreparedBatchRunner:
    """Run deterministic, explicit passes over a prepared local batch."""

    def __init__(
        self,
        executor: ReaderLocalBenchmarkExecutor | None = None,
    ) -> None:
        self._executor = executor or ReaderLocalBenchmarkExecutor()

    @staticmethod
    def initial_state(
        *,
        preparation: ReaderBenchmarkPreparationBundle,
        environment: EvaluationEnvironment,
    ) -> ReaderPreparedBatchExecutionState:
        _validate_preparation(preparation)
        if not isinstance(environment, EvaluationEnvironment):
            raise ReaderPreparedBatchRunnerError(
                "environment must be an EvaluationEnvironment"
            )
        if environment.environment_id != preparation.batch_plan.environment_id:
            raise ReaderPreparedBatchRunnerError(
                "environment does not match prepared batch plan"
            )
        if preparation.initial_checkpoint.receipts:
            raise ReaderPreparedBatchRunnerError(
                "preparation initial checkpoint must be empty"
            )
        return ReaderPreparedBatchExecutionState(
            preparation_id=preparation.preparation_id,
            environment=environment,
            checkpoint=preparation.initial_checkpoint,
        )

    def run_pass(
        self,
        *,
        preparation: ReaderBenchmarkPreparationBundle,
        state: ReaderPreparedBatchExecutionState,
        pipeline: ReaderLocalPipeline,
        max_cases: int | None = None,
    ) -> ReaderPreparedBatchExecutionState:
        _validate_preparation(preparation)
        _validate_state_ownership(preparation, state)
        if state.checkpoint.is_complete:
            raise ReaderPreparedBatchRunnerError(
                "cannot run a completed prepared batch"
            )
        if max_cases is not None and (
            isinstance(max_cases, bool)
            or not isinstance(max_cases, int)
            or max_cases < 1
        ):
            raise ReaderPreparedBatchRunnerError(
                "max_cases must be a positive integer when provided"
            )
        pending_snapshot = state.checkpoint.pending_case_ids
        selected_case_ids = (
            pending_snapshot
            if max_cases is None
            else pending_snapshot[:max_cases]
        )
        if not selected_case_ids:
            raise ReaderPreparedBatchRunnerError(
                "prepared batch has no pending cases"
            )
        cases_by_id = {
            item.case_id: item for item in preparation.local_cases
        }
        checkpoint = state.checkpoint
        observations_by_case = {
            item.case_id: item for item in state.observations
        }
        for case_id in selected_case_ids:
            case = cases_by_id.get(case_id)
            if case is None:
                raise ReaderPreparedBatchRunnerError(
                    "pending case is missing from preparation bundle"
                )
            result = self._executor.execute_case(
                checkpoint=checkpoint,
                case=case,
                pipeline=pipeline,
            )
            checkpoint = ReaderBenchmarkBatchPlanner.append_receipt(
                checkpoint,
                result.receipt,
            )
            if result.observation is not None:
                observations_by_case[case_id] = result.observation
        return ReaderPreparedBatchExecutionState(
            preparation_id=preparation.preparation_id,
            environment=state.environment,
            checkpoint=checkpoint,
            observations=tuple(
                sorted(
                    observations_by_case.values(),
                    key=lambda item: item.case_id,
                )
            ),
            pass_count=state.pass_count + 1,
        )


def _validate_preparation(
    preparation: ReaderBenchmarkPreparationBundle,
) -> None:
    if not isinstance(preparation, ReaderBenchmarkPreparationBundle):
        raise ReaderPreparedBatchRunnerError(
            "preparation must be a ReaderBenchmarkPreparationBundle"
        )
    if preparation.initial_checkpoint.plan != preparation.batch_plan:
        raise ReaderPreparedBatchRunnerError(
            "preparation checkpoint must match batch plan"
        )
    if preparation.initial_checkpoint.receipts:
        raise ReaderPreparedBatchRunnerError(
            "preparation checkpoint must be empty"
        )
    if preparation.batch_plan.case_ids != tuple(
        item.case_id for item in preparation.local_cases
    ):
        raise ReaderPreparedBatchRunnerError(
            "preparation cases must exactly match batch plan"
        )


def _validate_state_ownership(
    preparation: ReaderBenchmarkPreparationBundle,
    state: ReaderPreparedBatchExecutionState,
) -> None:
    if not isinstance(state, ReaderPreparedBatchExecutionState):
        raise ReaderPreparedBatchRunnerError(
            "state must be a ReaderPreparedBatchExecutionState"
        )
    if state.preparation_id != preparation.preparation_id:
        raise ReaderPreparedBatchRunnerError(
            "state belongs to a different preparation bundle"
        )
    if state.checkpoint.plan != preparation.batch_plan:
        raise ReaderPreparedBatchRunnerError(
            "state checkpoint belongs to a different batch plan"
        )
    if state.environment.environment_id != preparation.batch_plan.environment_id:
        raise ReaderPreparedBatchRunnerError(
            "state environment does not match prepared batch plan"
        )


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderPreparedBatchRunnerError(
            f"{field_name} must be non-empty text"
        )
    return value
