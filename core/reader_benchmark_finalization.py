"""Finalize completed Reader Core benchmark batches for PR-RDR-21/RDR-22.

The finalizer can consume either an in-memory RDR-19 preparation plus RDR-20
state or an RDR-22 portable completed-batch envelope. Both paths use the same
existing RDR-10 benchmark runner, promotion reviewer, and detached authenticator.
It never executes a pipeline, calibrates thresholds, records Operator GO, or
authorizes shadow/live integration.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.reader_benchmark_batch import BatchCaseStatus
from core.reader_benchmark_portability import (
    ReaderBenchmarkFinalizationEnvelope,
    ReaderBenchmarkPortabilityError,
)
from core.reader_benchmark_preparation import ReaderBenchmarkPreparationBundle
from core.reader_benchmark_runner import (
    ReaderBenchmarkBundle,
    ReaderBenchmarkError,
    ReaderBenchmarkRunner,
    ReaderBenchmarkSignature,
    ReaderBenchmarkSigner,
)
from core.reader_core_contracts import stable_reader_core_id
from core.reader_evaluation import PromotionDecision, ReaderPromotionThresholds
from core.reader_prepared_batch_runner import (
    PreparedBatchExecutionStatus,
    ReaderPreparedBatchExecutionState,
    ReaderPreparedBatchRunnerError,
)

READER_BENCHMARK_FINALIZATION_SCHEMA_VERSION = (
    "reader-core.benchmark-finalization.v1"
)


class ReaderBenchmarkFinalizationError(ValueError):
    """Raised when completed benchmark evidence cannot be finalized safely."""


@dataclass(frozen=True, slots=True)
class ReaderSignedBenchmarkEvidence:
    """Authenticated benchmark bundle plus its complete execution evidence index."""

    preparation_id: str
    execution_state: ReaderPreparedBatchExecutionState
    benchmark_bundle: ReaderBenchmarkBundle
    bundle_signature: ReaderBenchmarkSignature
    receipt_ids: tuple[str, ...]
    failed_attempt_receipt_ids: tuple[str, ...]
    artifact_ids: tuple[str, ...]
    schema_version: str = READER_BENCHMARK_FINALIZATION_SCHEMA_VERSION
    evidence_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.preparation_id, "preparation_id")
        if self.schema_version != READER_BENCHMARK_FINALIZATION_SCHEMA_VERSION:
            raise ReaderBenchmarkFinalizationError(
                "unsupported benchmark finalization schema"
            )
        if not isinstance(
            self.execution_state,
            ReaderPreparedBatchExecutionState,
        ):
            raise ReaderBenchmarkFinalizationError(
                "execution_state must be a ReaderPreparedBatchExecutionState"
            )
        if not isinstance(self.benchmark_bundle, ReaderBenchmarkBundle):
            raise ReaderBenchmarkFinalizationError(
                "benchmark_bundle must be a ReaderBenchmarkBundle"
            )
        if not isinstance(self.bundle_signature, ReaderBenchmarkSignature):
            raise ReaderBenchmarkFinalizationError(
                "bundle_signature must be a ReaderBenchmarkSignature"
            )
        state = self.execution_state
        bundle = self.benchmark_bundle
        plan = state.checkpoint.plan
        if state.status is not PreparedBatchExecutionStatus.COMPLETE_SUCCESS:
            raise ReaderBenchmarkFinalizationError(
                "signed evidence requires complete successful execution"
            )
        if state.preparation_id != self.preparation_id:
            raise ReaderBenchmarkFinalizationError(
                "execution state belongs to a different preparation"
            )
        if bundle.manifest.corpus_id != plan.corpus_id:
            raise ReaderBenchmarkFinalizationError(
                "benchmark bundle corpus does not match execution plan"
            )
        if bundle.benchmark_input.environment != state.environment:
            raise ReaderBenchmarkFinalizationError(
                "benchmark bundle environment does not match execution state"
            )
        if bundle.thresholds.thresholds_id != plan.threshold_policy_id:
            raise ReaderBenchmarkFinalizationError(
                "benchmark thresholds do not match execution plan"
            )
        try:
            expected_input = state.to_benchmark_input()
        except ReaderPreparedBatchRunnerError as exc:
            raise ReaderBenchmarkFinalizationError(str(exc)) from exc
        if bundle.benchmark_input != expected_input:
            raise ReaderBenchmarkFinalizationError(
                "benchmark bundle input does not exactly match execution state"
            )
        if self.bundle_signature.bundle_id != bundle.bundle_id:
            raise ReaderBenchmarkFinalizationError(
                "bundle signature references a different benchmark bundle"
            )
        expected_receipt_ids = tuple(
            item.receipt_id for item in state.checkpoint.receipts
        )
        receipt_ids = _text_tuple(self.receipt_ids, "receipt_id")
        if receipt_ids != expected_receipt_ids:
            raise ReaderBenchmarkFinalizationError(
                "receipt_ids must exactly preserve checkpoint receipt order"
            )
        expected_failed_receipt_ids = tuple(
            item.receipt_id
            for item in state.checkpoint.receipts
            if item.status is BatchCaseStatus.FAILED
        )
        failed_receipt_ids = _text_tuple(
            self.failed_attempt_receipt_ids,
            "failed_attempt_receipt_id",
        )
        if failed_receipt_ids != expected_failed_receipt_ids:
            raise ReaderBenchmarkFinalizationError(
                "failed attempt receipt index does not match checkpoint history"
            )
        expected_artifact_ids = tuple(
            sorted(
                {
                    artifact_id
                    for receipt in state.checkpoint.receipts
                    for artifact_id in receipt.artifact_ids
                }
            )
        )
        artifact_ids = _unique_sorted_text(self.artifact_ids, "artifact_id")
        if artifact_ids != expected_artifact_ids:
            raise ReaderBenchmarkFinalizationError(
                "artifact index must exactly match all checkpoint receipts"
            )
        if not bundle.review.operator_go_required:
            raise ReaderBenchmarkFinalizationError(
                "finalized evidence must preserve Operator GO requirement"
            )
        if bundle.review.live_integration_authorized:
            raise ReaderBenchmarkFinalizationError(
                "finalized evidence cannot authorize live integration"
            )
        object.__setattr__(self, "receipt_ids", receipt_ids)
        object.__setattr__(
            self,
            "failed_attempt_receipt_ids",
            failed_receipt_ids,
        )
        object.__setattr__(self, "artifact_ids", artifact_ids)
        expected = stable_reader_core_id(
            "reader-signed-benchmark-evidence",
            self.identity_payload(include_id=False),
        )
        if self.evidence_id:
            if self.evidence_id != expected:
                raise ReaderBenchmarkFinalizationError(
                    "evidence_id does not match finalized evidence content"
                )
        else:
            object.__setattr__(self, "evidence_id", expected)

    @property
    def decision(self) -> PromotionDecision:
        return self.benchmark_bundle.review.decision

    @property
    def operator_go_required(self) -> bool:
        return self.benchmark_bundle.review.operator_go_required

    @property
    def live_integration_authorized(self) -> bool:
        return self.benchmark_bundle.review.live_integration_authorized

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "preparation_id": self.preparation_id,
            "execution_state_id": self.execution_state.state_id,
            "checkpoint_id": self.execution_state.checkpoint.checkpoint_id,
            "benchmark_bundle_id": self.benchmark_bundle.bundle_id,
            "bundle_signature_id": self.bundle_signature.signature_id,
            "receipt_ids": list(self.receipt_ids),
            "failed_attempt_receipt_ids": list(
                self.failed_attempt_receipt_ids
            ),
            "artifact_ids": list(self.artifact_ids),
            "decision": self.decision.value,
            "operator_go_required": self.operator_go_required,
            "live_integration_authorized": self.live_integration_authorized,
        }
        if include_id:
            payload["evidence_id"] = self.evidence_id
        return payload


class ReaderCompletedBatchFinalizer:
    """Build and authenticate evidence from one complete successful batch."""

    def __init__(self, runner: ReaderBenchmarkRunner | None = None) -> None:
        self._runner = runner or ReaderBenchmarkRunner()

    def finalize(
        self,
        *,
        preparation: ReaderBenchmarkPreparationBundle,
        state: ReaderPreparedBatchExecutionState,
        thresholds: ReaderPromotionThresholds,
        key_id: str,
        secret: bytes,
    ) -> ReaderSignedBenchmarkEvidence:
        try:
            envelope = ReaderBenchmarkFinalizationEnvelope.from_completed(
                preparation=preparation,
                state=state,
            )
        except ReaderBenchmarkPortabilityError as exc:
            raise ReaderBenchmarkFinalizationError(str(exc)) from exc
        return self.finalize_envelope(
            envelope=envelope,
            thresholds=thresholds,
            key_id=key_id,
            secret=secret,
        )

    def finalize_envelope(
        self,
        *,
        envelope: ReaderBenchmarkFinalizationEnvelope,
        thresholds: ReaderPromotionThresholds,
        key_id: str,
        secret: bytes,
    ) -> ReaderSignedBenchmarkEvidence:
        _validate_envelope_finalization(
            envelope=envelope,
            thresholds=thresholds,
        )
        state = envelope.execution_state
        try:
            benchmark_input = state.to_benchmark_input()
            bundle = self._runner.run(
                envelope.evaluation_manifest,
                benchmark_input,
                thresholds,
            )
            signature = ReaderBenchmarkSigner.sign(
                bundle,
                key_id=key_id,
                secret=secret,
            )
        except (ReaderBenchmarkError, ReaderPreparedBatchRunnerError) as exc:
            raise ReaderBenchmarkFinalizationError(str(exc)) from exc
        receipt_ids = tuple(
            item.receipt_id for item in state.checkpoint.receipts
        )
        failed_receipt_ids = tuple(
            item.receipt_id
            for item in state.checkpoint.receipts
            if item.status is BatchCaseStatus.FAILED
        )
        artifact_ids = tuple(
            sorted(
                {
                    artifact_id
                    for receipt in state.checkpoint.receipts
                    for artifact_id in receipt.artifact_ids
                }
            )
        )
        return ReaderSignedBenchmarkEvidence(
            preparation_id=envelope.preparation_id,
            execution_state=state,
            benchmark_bundle=bundle,
            bundle_signature=signature,
            receipt_ids=receipt_ids,
            failed_attempt_receipt_ids=failed_receipt_ids,
            artifact_ids=artifact_ids,
        )

    @staticmethod
    def verify(
        evidence: ReaderSignedBenchmarkEvidence,
        *,
        secret: bytes,
    ) -> bool:
        if not isinstance(evidence, ReaderSignedBenchmarkEvidence):
            raise ReaderBenchmarkFinalizationError(
                "evidence must be ReaderSignedBenchmarkEvidence"
            )
        try:
            return ReaderBenchmarkSigner.verify(
                evidence.benchmark_bundle,
                evidence.bundle_signature,
                secret=secret,
            )
        except ReaderBenchmarkError as exc:
            raise ReaderBenchmarkFinalizationError(str(exc)) from exc


def _validate_envelope_finalization(
    *,
    envelope: ReaderBenchmarkFinalizationEnvelope,
    thresholds: ReaderPromotionThresholds,
) -> None:
    if not isinstance(envelope, ReaderBenchmarkFinalizationEnvelope):
        raise ReaderBenchmarkFinalizationError(
            "envelope must be a ReaderBenchmarkFinalizationEnvelope"
        )
    if not isinstance(thresholds, ReaderPromotionThresholds):
        raise ReaderBenchmarkFinalizationError(
            "thresholds must be ReaderPromotionThresholds"
        )
    if (
        thresholds.thresholds_id
        != envelope.batch_plan.threshold_policy_id
    ):
        raise ReaderBenchmarkFinalizationError(
            "threshold policy does not match batch plan"
        )
    if (
        envelope.execution_state.status
        is not PreparedBatchExecutionStatus.COMPLETE_SUCCESS
    ):
        raise ReaderBenchmarkFinalizationError(
            "finalization requires complete successful execution"
        )


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderBenchmarkFinalizationError(
            f"{field_name} must be non-empty text"
        )
    return value


def _text_tuple(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    items = tuple(values)
    for item in items:
        _require_text(item, field_name)
    return items


def _unique_sorted_text(
    values: tuple[str, ...],
    field_name: str,
) -> tuple[str, ...]:
    items = _text_tuple(values, field_name)
    if len(set(items)) != len(items):
        raise ReaderBenchmarkFinalizationError(
            f"{field_name} values must be unique"
        )
    ordered = tuple(sorted(items))
    if items != ordered:
        raise ReaderBenchmarkFinalizationError(
            f"{field_name} values must use canonical ordering"
        )
    return items


__all__ = [
    "READER_BENCHMARK_FINALIZATION_SCHEMA_VERSION",
    "ReaderBenchmarkFinalizationError",
    "ReaderCompletedBatchFinalizer",
    "ReaderSignedBenchmarkEvidence",
]
