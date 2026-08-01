"""Portable completed-batch finalization envelopes for PR-RDR-22.

The envelope contains only post-execution material required to reproduce RDR-21
finalization: the exact preparation ID, evaluation manifest, batch plan, and
complete-success execution state. Strict JSON loading reconstructs every typed
contract and requires byte-for-byte canonical serialization.

It does not contain source documents, human annotation working sets, pipeline
adapters, signing secrets, Operator decisions, or runtime authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, cast

from core.reader_benchmark_batch import (
    BatchCaseStatus,
    ReaderBenchmarkBatchCheckpoint,
    ReaderBenchmarkBatchPlan,
    ReaderBenchmarkCaseReceipt,
)
from core.reader_benchmark_preparation import ReaderBenchmarkPreparationBundle
from core.reader_benchmark_runner import (
    ReaderBenchmarkObservation,
    canonical_json_bytes,
    write_canonical_json,
)
from core.reader_core_contracts import stable_reader_core_id
from core.reader_evaluation import (
    EvaluationCorpusKind,
    EvaluationCorpusManifest,
    EvaluationEnvironment,
    ReaderEvaluationCaseManifest,
)
from core.reader_prepared_batch_runner import (
    PreparedBatchExecutionStatus,
    ReaderPreparedBatchExecutionState,
)

READER_BENCHMARK_FINALIZATION_ENVELOPE_SCHEMA_VERSION = (
    "reader-core.benchmark-finalization-envelope.v1"
)


class ReaderBenchmarkPortabilityError(ValueError):
    """Raised when a portable envelope is malformed, foreign, or noncanonical."""


@dataclass(frozen=True, slots=True)
class ReaderBenchmarkFinalizationEnvelope:
    preparation_id: str
    evaluation_manifest: EvaluationCorpusManifest
    batch_plan: ReaderBenchmarkBatchPlan
    execution_state: ReaderPreparedBatchExecutionState
    schema_version: str = READER_BENCHMARK_FINALIZATION_ENVELOPE_SCHEMA_VERSION
    envelope_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.preparation_id, "preparation_id")
        if (
            self.schema_version
            != READER_BENCHMARK_FINALIZATION_ENVELOPE_SCHEMA_VERSION
        ):
            raise ReaderBenchmarkPortabilityError(
                "unsupported benchmark finalization envelope schema"
            )
        if not isinstance(self.evaluation_manifest, EvaluationCorpusManifest):
            raise ReaderBenchmarkPortabilityError(
                "evaluation_manifest must be an EvaluationCorpusManifest"
            )
        if not isinstance(self.batch_plan, ReaderBenchmarkBatchPlan):
            raise ReaderBenchmarkPortabilityError(
                "batch_plan must be a ReaderBenchmarkBatchPlan"
            )
        if not isinstance(
            self.execution_state,
            ReaderPreparedBatchExecutionState,
        ):
            raise ReaderBenchmarkPortabilityError(
                "execution_state must be a ReaderPreparedBatchExecutionState"
            )
        state = self.execution_state
        if state.status is not PreparedBatchExecutionStatus.COMPLETE_SUCCESS:
            raise ReaderBenchmarkPortabilityError(
                "portable finalization requires complete successful execution"
            )
        if state.preparation_id != self.preparation_id:
            raise ReaderBenchmarkPortabilityError(
                "execution state belongs to a different preparation"
            )
        if state.checkpoint.plan != self.batch_plan:
            raise ReaderBenchmarkPortabilityError(
                "execution checkpoint belongs to a different batch plan"
            )
        if self.evaluation_manifest.corpus_id != self.batch_plan.corpus_id:
            raise ReaderBenchmarkPortabilityError(
                "evaluation manifest does not match batch-plan corpus"
            )
        manifest_case_ids = tuple(
            item.case_id for item in self.evaluation_manifest.cases
        )
        if manifest_case_ids != self.batch_plan.case_ids:
            raise ReaderBenchmarkPortabilityError(
                "evaluation manifest must exactly cover planned cases"
            )
        if state.environment.environment_id != self.batch_plan.environment_id:
            raise ReaderBenchmarkPortabilityError(
                "execution environment does not match batch plan"
            )
        latest = state.checkpoint.latest_receipts
        if set(latest) != set(self.batch_plan.case_ids):
            raise ReaderBenchmarkPortabilityError(
                "execution state must contain one latest receipt per case"
            )
        if any(
            item.status is not BatchCaseStatus.SUCCEEDED
            for item in latest.values()
        ):
            raise ReaderBenchmarkPortabilityError(
                "every latest case receipt must be successful"
            )
        if tuple(item.case_id for item in state.observations) != (
            self.batch_plan.case_ids
        ):
            raise ReaderBenchmarkPortabilityError(
                "execution observations must exactly cover planned cases"
            )
        expected = stable_reader_core_id(
            "reader-benchmark-finalization-envelope",
            self.identity_payload(include_id=False),
        )
        if self.envelope_id:
            if self.envelope_id != expected:
                raise ReaderBenchmarkPortabilityError(
                    "envelope_id does not match envelope content"
                )
        else:
            object.__setattr__(self, "envelope_id", expected)

    @classmethod
    def from_completed(
        cls,
        *,
        preparation: ReaderBenchmarkPreparationBundle,
        state: ReaderPreparedBatchExecutionState,
    ) -> ReaderBenchmarkFinalizationEnvelope:
        if not isinstance(preparation, ReaderBenchmarkPreparationBundle):
            raise ReaderBenchmarkPortabilityError(
                "preparation must be a ReaderBenchmarkPreparationBundle"
            )
        if not isinstance(state, ReaderPreparedBatchExecutionState):
            raise ReaderBenchmarkPortabilityError(
                "state must be a ReaderPreparedBatchExecutionState"
            )
        if state.preparation_id != preparation.preparation_id:
            raise ReaderBenchmarkPortabilityError(
                "state belongs to a different preparation"
            )
        if state.checkpoint.plan != preparation.batch_plan:
            raise ReaderBenchmarkPortabilityError(
                "state checkpoint belongs to a different batch plan"
            )
        if preparation.initial_checkpoint.plan != preparation.batch_plan:
            raise ReaderBenchmarkPortabilityError(
                "preparation initial checkpoint does not match batch plan"
            )
        if preparation.initial_checkpoint.receipts:
            raise ReaderBenchmarkPortabilityError(
                "preparation initial checkpoint must be empty"
            )
        return cls(
            preparation_id=preparation.preparation_id,
            evaluation_manifest=preparation.evaluation_manifest,
            batch_plan=preparation.batch_plan,
            execution_state=state,
        )

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "preparation_id": self.preparation_id,
            "evaluation_corpus_id": self.evaluation_manifest.corpus_id,
            "batch_plan_id": self.batch_plan.plan_id,
            "execution_state_id": self.execution_state.state_id,
        }
        if include_id:
            payload["envelope_id"] = self.envelope_id
        return payload


def write_finalization_envelope(
    path: str | Path,
    envelope: ReaderBenchmarkFinalizationEnvelope,
) -> None:
    if not isinstance(envelope, ReaderBenchmarkFinalizationEnvelope):
        raise ReaderBenchmarkPortabilityError(
            "envelope must be a ReaderBenchmarkFinalizationEnvelope"
        )
    write_canonical_json(path, envelope)


def load_finalization_envelope(
    path: str | Path,
) -> ReaderBenchmarkFinalizationEnvelope:
    source = Path(path)
    try:
        raw = source.read_bytes()
        text = raw.decode("utf-8")
        value: Any = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
        )
        envelope = _parse_envelope(_mapping(value, "envelope"))
    except ReaderBenchmarkPortabilityError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ReaderBenchmarkPortabilityError(
            f"cannot load finalization envelope from {source}: {exc}"
        ) from exc
    expected_bytes = canonical_json_bytes(envelope) + b"\n"
    if raw != expected_bytes:
        raise ReaderBenchmarkPortabilityError(
            "finalization envelope must use canonical JSON encoding"
        )
    return envelope


def _parse_envelope(
    payload: Mapping[str, object],
) -> ReaderBenchmarkFinalizationEnvelope:
    _keys(
        payload,
        required={
            "preparation_id",
            "evaluation_manifest",
            "batch_plan",
            "execution_state",
            "schema_version",
            "envelope_id",
        },
        field_name="envelope",
    )
    return ReaderBenchmarkFinalizationEnvelope(
        preparation_id=_text(payload["preparation_id"], "preparation_id"),
        evaluation_manifest=_parse_manifest(
            _mapping(payload["evaluation_manifest"], "evaluation_manifest")
        ),
        batch_plan=_parse_plan(_mapping(payload["batch_plan"], "batch_plan")),
        execution_state=_parse_state(
            _mapping(payload["execution_state"], "execution_state")
        ),
        schema_version=_text(payload["schema_version"], "schema_version"),
        envelope_id=_text(payload["envelope_id"], "envelope_id"),
    )


def _parse_manifest(payload: Mapping[str, object]) -> EvaluationCorpusManifest:
    _keys(
        payload,
        required={
            "corpus_name",
            "corpus_version",
            "cases",
            "schema_version",
            "corpus_id",
        },
        field_name="evaluation_manifest",
    )
    cases = _list(payload["cases"], "cases")
    return EvaluationCorpusManifest(
        corpus_name=_text(payload["corpus_name"], "corpus_name"),
        corpus_version=_text(payload["corpus_version"], "corpus_version"),
        cases=tuple(
            _parse_case_manifest(_mapping(item, f"cases[{index}]"))
            for index, item in enumerate(cases)
        ),
        schema_version=_text(payload["schema_version"], "schema_version"),
        corpus_id=_text(payload["corpus_id"], "corpus_id"),
    )


def _parse_case_manifest(
    payload: Mapping[str, object],
) -> ReaderEvaluationCaseManifest:
    _keys(
        payload,
        required={
            "case_id",
            "corpus_kind",
            "label_version",
            "expected_claim_count",
            "expected_source_span_count",
            "expected_exception_count",
            "expected_relation_count",
            "expected_contradiction_count",
            "expected_qualifier_count",
            "tags",
            "manifest_id",
        },
        field_name="case_manifest",
    )
    return ReaderEvaluationCaseManifest(
        case_id=_text(payload["case_id"], "case_id"),
        corpus_kind=_enum(
            EvaluationCorpusKind,
            payload["corpus_kind"],
            "corpus_kind",
        ),
        label_version=_text(payload["label_version"], "label_version"),
        expected_claim_count=_int(
            payload["expected_claim_count"],
            "expected_claim_count",
        ),
        expected_source_span_count=_int(
            payload["expected_source_span_count"],
            "expected_source_span_count",
        ),
        expected_exception_count=_int(
            payload["expected_exception_count"],
            "expected_exception_count",
        ),
        expected_relation_count=_int(
            payload["expected_relation_count"],
            "expected_relation_count",
        ),
        expected_contradiction_count=_int(
            payload["expected_contradiction_count"],
            "expected_contradiction_count",
        ),
        expected_qualifier_count=_int(
            payload["expected_qualifier_count"],
            "expected_qualifier_count",
        ),
        tags=_text_array(payload["tags"], "tag"),
        manifest_id=_text(payload["manifest_id"], "manifest_id"),
    )


def _parse_plan(payload: Mapping[str, object]) -> ReaderBenchmarkBatchPlan:
    _keys(
        payload,
        required={
            "corpus_id",
            "environment_id",
            "threshold_policy_id",
            "case_ids",
            "max_attempts_per_case",
            "schema_version",
            "plan_id",
        },
        field_name="batch_plan",
    )
    return ReaderBenchmarkBatchPlan(
        corpus_id=_text(payload["corpus_id"], "corpus_id"),
        environment_id=_text(payload["environment_id"], "environment_id"),
        threshold_policy_id=_text(
            payload["threshold_policy_id"],
            "threshold_policy_id",
        ),
        case_ids=_text_array(payload["case_ids"], "case_id"),
        max_attempts_per_case=_int(
            payload["max_attempts_per_case"],
            "max_attempts_per_case",
        ),
        schema_version=_text(payload["schema_version"], "schema_version"),
        plan_id=_text(payload["plan_id"], "plan_id"),
    )


def _parse_state(
    payload: Mapping[str, object],
) -> ReaderPreparedBatchExecutionState:
    _keys(
        payload,
        required={
            "preparation_id",
            "environment",
            "checkpoint",
            "observations",
            "pass_count",
            "schema_version",
            "state_id",
        },
        field_name="execution_state",
    )
    observations = _list(payload["observations"], "observations")
    return ReaderPreparedBatchExecutionState(
        preparation_id=_text(payload["preparation_id"], "preparation_id"),
        environment=_parse_environment(
            _mapping(payload["environment"], "environment")
        ),
        checkpoint=_parse_checkpoint(
            _mapping(payload["checkpoint"], "checkpoint")
        ),
        observations=tuple(
            _parse_observation(_mapping(item, f"observations[{index}]"))
            for index, item in enumerate(observations)
        ),
        pass_count=_int(payload["pass_count"], "pass_count"),
        schema_version=_text(payload["schema_version"], "schema_version"),
        state_id=_text(payload["state_id"], "state_id"),
    )


def _parse_environment(payload: Mapping[str, object]) -> EvaluationEnvironment:
    _keys(
        payload,
        required={
            "commit_sha",
            "runner_id",
            "python_version",
            "hardware_profile",
            "config_digest",
            "model_id",
            "model_version",
            "environment_id",
        },
        field_name="environment",
    )
    return EvaluationEnvironment(
        commit_sha=_text(payload["commit_sha"], "commit_sha"),
        runner_id=_text(payload["runner_id"], "runner_id"),
        python_version=_text(payload["python_version"], "python_version"),
        hardware_profile=_text(
            payload["hardware_profile"],
            "hardware_profile",
        ),
        config_digest=_text(payload["config_digest"], "config_digest"),
        model_id=_optional_text(payload["model_id"], "model_id"),
        model_version=_optional_text(
            payload["model_version"],
            "model_version",
        ),
        environment_id=_text(payload["environment_id"], "environment_id"),
    )


def _parse_checkpoint(
    payload: Mapping[str, object],
) -> ReaderBenchmarkBatchCheckpoint:
    _keys(
        payload,
        required={"plan", "receipts", "checkpoint_id"},
        field_name="checkpoint",
    )
    receipts = _list(payload["receipts"], "receipts")
    return ReaderBenchmarkBatchCheckpoint(
        plan=_parse_plan(_mapping(payload["plan"], "checkpoint.plan")),
        receipts=tuple(
            _parse_receipt(_mapping(item, f"receipts[{index}]"))
            for index, item in enumerate(receipts)
        ),
        checkpoint_id=_text(payload["checkpoint_id"], "checkpoint_id"),
    )


def _parse_receipt(
    payload: Mapping[str, object],
) -> ReaderBenchmarkCaseReceipt:
    _keys(
        payload,
        required={
            "plan_id",
            "case_id",
            "status",
            "attempt",
            "observation_id",
            "error_code",
            "artifact_ids",
            "receipt_id",
        },
        field_name="receipt",
    )
    return ReaderBenchmarkCaseReceipt(
        plan_id=_text(payload["plan_id"], "plan_id"),
        case_id=_text(payload["case_id"], "case_id"),
        status=_enum(BatchCaseStatus, payload["status"], "status"),
        attempt=_int(payload["attempt"], "attempt"),
        observation_id=_optional_text(
            payload["observation_id"],
            "observation_id",
        ),
        error_code=_optional_text(payload["error_code"], "error_code"),
        artifact_ids=_text_array(payload["artifact_ids"], "artifact_id"),
        receipt_id=_text(payload["receipt_id"], "receipt_id"),
    )


def _parse_observation(
    payload: Mapping[str, object],
) -> ReaderBenchmarkObservation:
    required = {
        "case_id",
        "predicted_claim_count",
        "matched_claim_count",
        "predicted_source_span_count",
        "correct_source_span_count",
        "predicted_exception_count",
        "matched_exception_count",
        "predicted_relation_count",
        "matched_relation_count",
        "false_relation_count",
        "matched_contradiction_count",
        "connected_qualifier_count",
        "source_claim_count",
        "orphan_source_claim_count",
        "synthesis_claim_count",
        "unsupported_synthesis_claim_count",
        "first_artifact_ids",
        "second_artifact_ids",
        "section_latencies_ms",
        "session_wall_time_ms",
        "model_tokens",
        "projection_bytes",
        "rebuild_time_ms",
        "query_path_latency_delta_ms",
        "resume_reused_units",
        "resume_eligible_units",
        "truth_gate_bypass_count",
        "query_path_write_count",
        "direct_canon_write_count",
        "untrusted_instruction_execution_count",
        "warnings",
        "observation_id",
    }
    _keys(payload, required=required, field_name="observation")
    integer_fields = (
        "predicted_claim_count",
        "matched_claim_count",
        "predicted_source_span_count",
        "correct_source_span_count",
        "predicted_exception_count",
        "matched_exception_count",
        "predicted_relation_count",
        "matched_relation_count",
        "false_relation_count",
        "matched_contradiction_count",
        "connected_qualifier_count",
        "source_claim_count",
        "orphan_source_claim_count",
        "synthesis_claim_count",
        "unsupported_synthesis_claim_count",
        "session_wall_time_ms",
        "model_tokens",
        "projection_bytes",
        "rebuild_time_ms",
        "query_path_latency_delta_ms",
        "resume_reused_units",
        "resume_eligible_units",
        "truth_gate_bypass_count",
        "query_path_write_count",
        "direct_canon_write_count",
        "untrusted_instruction_execution_count",
    )
    values = {name: _int(payload[name], name) for name in integer_fields}
    return ReaderBenchmarkObservation(
        case_id=_text(payload["case_id"], "case_id"),
        predicted_claim_count=values["predicted_claim_count"],
        matched_claim_count=values["matched_claim_count"],
        predicted_source_span_count=values["predicted_source_span_count"],
        correct_source_span_count=values["correct_source_span_count"],
        predicted_exception_count=values["predicted_exception_count"],
        matched_exception_count=values["matched_exception_count"],
        predicted_relation_count=values["predicted_relation_count"],
        matched_relation_count=values["matched_relation_count"],
        false_relation_count=values["false_relation_count"],
        matched_contradiction_count=values["matched_contradiction_count"],
        connected_qualifier_count=values["connected_qualifier_count"],
        source_claim_count=values["source_claim_count"],
        orphan_source_claim_count=values["orphan_source_claim_count"],
        synthesis_claim_count=values["synthesis_claim_count"],
        unsupported_synthesis_claim_count=values[
            "unsupported_synthesis_claim_count"
        ],
        first_artifact_ids=_text_array(
            payload["first_artifact_ids"],
            "first_artifact_id",
        ),
        second_artifact_ids=_text_array(
            payload["second_artifact_ids"],
            "second_artifact_id",
        ),
        section_latencies_ms=_int_array(
            payload["section_latencies_ms"],
            "section_latency_ms",
        ),
        session_wall_time_ms=values["session_wall_time_ms"],
        model_tokens=values["model_tokens"],
        projection_bytes=values["projection_bytes"],
        rebuild_time_ms=values["rebuild_time_ms"],
        query_path_latency_delta_ms=values["query_path_latency_delta_ms"],
        resume_reused_units=values["resume_reused_units"],
        resume_eligible_units=values["resume_eligible_units"],
        truth_gate_bypass_count=values["truth_gate_bypass_count"],
        query_path_write_count=values["query_path_write_count"],
        direct_canon_write_count=values["direct_canon_write_count"],
        untrusted_instruction_execution_count=values[
            "untrusted_instruction_execution_count"
        ],
        warnings=_text_array(payload["warnings"], "warning"),
        observation_id=_text(payload["observation_id"], "observation_id"),
    )


def _reject_duplicate_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ReaderBenchmarkPortabilityError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _keys(
    payload: Mapping[str, object],
    *,
    required: set[str],
    field_name: str,
) -> None:
    actual = set(payload)
    missing = sorted(required - actual)
    unknown = sorted(actual - required)
    if missing or unknown:
        raise ReaderBenchmarkPortabilityError(
            f"{field_name} keys mismatch; missing={missing}, unknown={unknown}"
        )


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) for key in value
    ):
        raise ReaderBenchmarkPortabilityError(
            f"{field_name} must be a JSON object with string keys"
        )
    return cast(Mapping[str, object], value)


def _list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ReaderBenchmarkPortabilityError(
            f"{field_name} must be a JSON array"
        )
    return cast(list[object], value)


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderBenchmarkPortabilityError(
            f"{field_name} must be non-empty text"
        )
    return value


def _require_text(value: object, field_name: str) -> str:
    return _text(value, field_name)


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _text(value, field_name)


def _int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReaderBenchmarkPortabilityError(
            f"{field_name} must be an integer"
        )
    return value


def _text_array(value: object, field_name: str) -> tuple[str, ...]:
    return tuple(_text(item, field_name) for item in _list(value, field_name))


def _int_array(value: object, field_name: str) -> tuple[int, ...]:
    return tuple(_int(item, field_name) for item in _list(value, field_name))


def _enum(enum_type: type[Any], value: object, field_name: str) -> Any:
    text = _text(value, field_name)
    try:
        return enum_type(text)
    except ValueError as exc:
        raise ReaderBenchmarkPortabilityError(
            f"unsupported {field_name}: {text}"
        ) from exc


__all__ = [
    "READER_BENCHMARK_FINALIZATION_ENVELOPE_SCHEMA_VERSION",
    "ReaderBenchmarkFinalizationEnvelope",
    "ReaderBenchmarkPortabilityError",
    "load_finalization_envelope",
    "write_finalization_envelope",
]
