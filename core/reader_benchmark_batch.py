"""Deterministic local batch orchestration contracts for PR-RDR-13.

This module plans and checkpoints corpus benchmark work. It does not execute a
model, access the network, schedule background work, write memory or Canon, or
authorize live integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from core.reader_core_contracts import stable_reader_core_id

READER_BENCHMARK_BATCH_SCHEMA_VERSION = "reader-core.benchmark-batch.v1"


class ReaderBenchmarkBatchError(ValueError):
    """Raised when batch state or identity invariants are invalid."""


class BatchCaseStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


TERMINAL_CASE_STATUSES = frozenset(
    {BatchCaseStatus.SUCCEEDED, BatchCaseStatus.FAILED, BatchCaseStatus.SKIPPED}
)


@dataclass(frozen=True, slots=True)
class ReaderBenchmarkBatchPlan:
    corpus_id: str
    environment_id: str
    threshold_policy_id: str
    case_ids: tuple[str, ...]
    max_attempts_per_case: int = 1
    schema_version: str = READER_BENCHMARK_BATCH_SCHEMA_VERSION
    plan_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.corpus_id, "corpus_id")
        _require_text(self.environment_id, "environment_id")
        _require_text(self.threshold_policy_id, "threshold_policy_id")
        if self.schema_version != READER_BENCHMARK_BATCH_SCHEMA_VERSION:
            raise ReaderBenchmarkBatchError("unsupported batch schema")
        if (
            isinstance(self.max_attempts_per_case, bool)
            or not isinstance(self.max_attempts_per_case, int)
            or self.max_attempts_per_case < 1
        ):
            raise ReaderBenchmarkBatchError(
                "max_attempts_per_case must be a positive integer"
            )
        case_ids = _unique_sorted_text(self.case_ids, "case_id")
        if not case_ids:
            raise ReaderBenchmarkBatchError("case_ids must not be empty")
        object.__setattr__(self, "case_ids", case_ids)
        expected = stable_reader_core_id(
            "reader-benchmark-batch-plan",
            self.identity_payload(include_id=False),
        )
        if self.plan_id:
            if self.plan_id != expected:
                raise ReaderBenchmarkBatchError(
                    "plan_id does not match batch plan content"
                )
        else:
            object.__setattr__(self, "plan_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "corpus_id": self.corpus_id,
            "environment_id": self.environment_id,
            "threshold_policy_id": self.threshold_policy_id,
            "case_ids": list(self.case_ids),
            "max_attempts_per_case": self.max_attempts_per_case,
        }
        if include_id:
            payload["plan_id"] = self.plan_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderBenchmarkCaseReceipt:
    plan_id: str
    case_id: str
    status: BatchCaseStatus
    attempt: int
    observation_id: str | None = None
    error_code: str | None = None
    artifact_ids: tuple[str, ...] = ()
    receipt_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.plan_id, "plan_id")
        _require_text(self.case_id, "case_id")
        if not isinstance(self.status, BatchCaseStatus):
            raise ReaderBenchmarkBatchError("status must be a BatchCaseStatus")
        if (
            isinstance(self.attempt, bool)
            or not isinstance(self.attempt, int)
            or self.attempt < 1
        ):
            raise ReaderBenchmarkBatchError("attempt must be a positive integer")
        artifacts = _unique_sorted_text(self.artifact_ids, "artifact_id")
        object.__setattr__(self, "artifact_ids", artifacts)
        if self.status is BatchCaseStatus.SUCCEEDED:
            _require_text(self.observation_id, "observation_id")
            if self.error_code is not None:
                raise ReaderBenchmarkBatchError(
                    "successful receipt cannot contain error_code"
                )
        elif self.status is BatchCaseStatus.FAILED:
            _require_text(self.error_code, "error_code")
            if self.observation_id is not None:
                raise ReaderBenchmarkBatchError(
                    "failed receipt cannot contain observation_id"
                )
        elif self.status is BatchCaseStatus.SKIPPED:
            _require_text(self.error_code, "error_code")
            if self.observation_id is not None:
                raise ReaderBenchmarkBatchError(
                    "skipped receipt cannot contain observation_id"
                )
        else:
            if self.observation_id is not None or self.error_code is not None:
                raise ReaderBenchmarkBatchError(
                    "non-terminal receipt cannot contain result fields"
                )
        expected = stable_reader_core_id(
            "reader-benchmark-case-receipt",
            self.identity_payload(include_id=False),
        )
        if self.receipt_id:
            if self.receipt_id != expected:
                raise ReaderBenchmarkBatchError(
                    "receipt_id does not match receipt content"
                )
        else:
            object.__setattr__(self, "receipt_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "plan_id": self.plan_id,
            "case_id": self.case_id,
            "status": self.status.value,
            "attempt": self.attempt,
            "observation_id": self.observation_id,
            "error_code": self.error_code,
            "artifact_ids": list(self.artifact_ids),
        }
        if include_id:
            payload["receipt_id"] = self.receipt_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderBenchmarkBatchCheckpoint:
    plan: ReaderBenchmarkBatchPlan
    receipts: tuple[ReaderBenchmarkCaseReceipt, ...]
    checkpoint_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.plan, ReaderBenchmarkBatchPlan):
            raise ReaderBenchmarkBatchError(
                "plan must be a ReaderBenchmarkBatchPlan"
            )
        receipts = tuple(
            sorted(
                self.receipts,
                key=lambda item: (item.case_id, item.attempt, item.receipt_id),
            )
        )
        if any(
            not isinstance(item, ReaderBenchmarkCaseReceipt) for item in receipts
        ):
            raise ReaderBenchmarkBatchError(
                "receipts must contain ReaderBenchmarkCaseReceipt values"
            )
        seen_attempts: set[tuple[str, int]] = set()
        latest: dict[str, ReaderBenchmarkCaseReceipt] = {}
        for receipt in receipts:
            if receipt.plan_id != self.plan.plan_id:
                raise ReaderBenchmarkBatchError(
                    "receipt belongs to a different batch plan"
                )
            if receipt.case_id not in self.plan.case_ids:
                raise ReaderBenchmarkBatchError(
                    "receipt case_id is not present in the batch plan"
                )
            key = (receipt.case_id, receipt.attempt)
            if key in seen_attempts:
                raise ReaderBenchmarkBatchError(
                    "duplicate case attempt in checkpoint"
                )
            seen_attempts.add(key)
            if receipt.attempt > self.plan.max_attempts_per_case:
                raise ReaderBenchmarkBatchError(
                    "receipt attempt exceeds batch plan limit"
                )
            previous = latest.get(receipt.case_id)
            if previous is not None:
                if previous.status not in TERMINAL_CASE_STATUSES:
                    raise ReaderBenchmarkBatchError(
                        "a new attempt requires a terminal previous attempt"
                    )
                if receipt.attempt != previous.attempt + 1:
                    raise ReaderBenchmarkBatchError(
                        "case attempts must be contiguous"
                    )
            elif receipt.attempt != 1:
                raise ReaderBenchmarkBatchError(
                    "first case attempt must be attempt 1"
                )
            latest[receipt.case_id] = receipt
        object.__setattr__(self, "receipts", receipts)
        expected = stable_reader_core_id(
            "reader-benchmark-batch-checkpoint",
            self.identity_payload(include_id=False),
        )
        if self.checkpoint_id:
            if self.checkpoint_id != expected:
                raise ReaderBenchmarkBatchError(
                    "checkpoint_id does not match checkpoint content"
                )
        else:
            object.__setattr__(self, "checkpoint_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "plan_id": self.plan.plan_id,
            "receipt_ids": [item.receipt_id for item in self.receipts],
        }
        if include_id:
            payload["checkpoint_id"] = self.checkpoint_id
        return payload

    @property
    def latest_receipts(self) -> dict[str, ReaderBenchmarkCaseReceipt]:
        latest: dict[str, ReaderBenchmarkCaseReceipt] = {}
        for receipt in self.receipts:
            latest[receipt.case_id] = receipt
        return latest

    @property
    def pending_case_ids(self) -> tuple[str, ...]:
        latest = self.latest_receipts
        pending: list[str] = []
        for case_id in self.plan.case_ids:
            receipt = latest.get(case_id)
            if receipt is None:
                pending.append(case_id)
                continue
            if receipt.status in {BatchCaseStatus.PENDING, BatchCaseStatus.RUNNING}:
                pending.append(case_id)
            elif (
                receipt.status is BatchCaseStatus.FAILED
                and receipt.attempt < self.plan.max_attempts_per_case
            ):
                pending.append(case_id)
        return tuple(pending)

    @property
    def is_complete(self) -> bool:
        if self.pending_case_ids:
            return False
        latest = self.latest_receipts
        return len(latest) == len(self.plan.case_ids) and all(
            item.status in TERMINAL_CASE_STATUSES for item in latest.values()
        )

    @property
    def successful_observation_ids(self) -> tuple[str, ...]:
        if not self.is_complete:
            raise ReaderBenchmarkBatchError(
                "observations are unavailable until the batch is complete"
            )
        values = [
            item.observation_id
            for item in self.latest_receipts.values()
            if item.status is BatchCaseStatus.SUCCEEDED
        ]
        return tuple(sorted(item for item in values if item is not None))


class ReaderBenchmarkBatchPlanner:
    """Pure helpers for deterministic batch planning and checkpoint extension."""

    @staticmethod
    def create_plan(
        *,
        corpus_id: str,
        environment_id: str,
        threshold_policy_id: str,
        case_ids: Iterable[str],
        max_attempts_per_case: int = 1,
    ) -> ReaderBenchmarkBatchPlan:
        return ReaderBenchmarkBatchPlan(
            corpus_id=corpus_id,
            environment_id=environment_id,
            threshold_policy_id=threshold_policy_id,
            case_ids=tuple(case_ids),
            max_attempts_per_case=max_attempts_per_case,
        )

    @staticmethod
    def empty_checkpoint(
        plan: ReaderBenchmarkBatchPlan,
    ) -> ReaderBenchmarkBatchCheckpoint:
        return ReaderBenchmarkBatchCheckpoint(plan=plan, receipts=())

    @staticmethod
    def append_receipt(
        checkpoint: ReaderBenchmarkBatchCheckpoint,
        receipt: ReaderBenchmarkCaseReceipt,
    ) -> ReaderBenchmarkBatchCheckpoint:
        if checkpoint.is_complete:
            raise ReaderBenchmarkBatchError(
                "cannot append to a completed batch checkpoint"
            )
        return ReaderBenchmarkBatchCheckpoint(
            plan=checkpoint.plan,
            receipts=(*checkpoint.receipts, receipt),
        )


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderBenchmarkBatchError(f"{field_name} must be non-empty text")
    return value


def _unique_sorted_text(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    items = tuple(values)
    for item in items:
        _require_text(item, field_name)
    if len(set(items)) != len(items):
        raise ReaderBenchmarkBatchError(f"{field_name} values must be unique")
    return tuple(sorted(items))
