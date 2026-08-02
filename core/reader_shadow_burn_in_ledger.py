"""Deterministic shadow burn-in result ledger for PR-RDR-27.

The ledger accepts authenticated, pre-measured work receipts from a separately
reviewed isolated harness. It binds every receipt to one exact RDR-26 READY
status and enforces campaign work-item, attempt, wall-time, token, artifact-byte,
and consecutive-failure limits. It never executes a pipeline, schedules work,
routes production traffic, or grants persistent/live authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
from typing import Iterable

from core.reader_benchmark_runner import canonical_json_bytes
from core.reader_core_contracts import stable_reader_core_id
from core.reader_shadow_burn_in import (
    ReaderShadowBurnInPlan,
    ReaderShadowBurnInPlanSignature,
    ReaderShadowBurnInPlanSigner,
    ReaderShadowBurnInStatusReceipt,
    ShadowBurnInStatus,
)

READER_SHADOW_WORK_RECEIPT_SCHEMA_VERSION = (
    "reader-core.shadow-work-receipt.v1"
)
READER_SHADOW_WORK_SIGNATURE_SCHEMA_VERSION = (
    "reader-core.shadow-work-signature.v1"
)
READER_SHADOW_BURN_IN_LEDGER_SCHEMA_VERSION = (
    "reader-core.shadow-burn-in-ledger.v1"
)
READER_SHADOW_WORK_SIGNATURE_ALGORITHM = "hmac-sha256"


class ReaderShadowBurnInLedgerError(ValueError):
    """Raised when measured shadow evidence violates ledger invariants."""


class ShadowWorkResult(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ShadowBurnInLedgerStatus(str, Enum):
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETE_SUCCESS = "complete_success"
    COMPLETE_WITH_FAILURES = "complete_with_failures"
    BUDGET_EXHAUSTED = "budget_exhausted"
    FAILURE_LIMIT_REACHED = "failure_limit_reached"


@dataclass(frozen=True, slots=True)
class ReaderShadowWorkReceipt:
    plan_id: str
    plan_signature_id: str
    status_id: str
    environment_id: str
    harness_digest: str
    work_item_id: str
    attempt: int
    started_at_utc: str
    completed_at_utc: str
    result: ShadowWorkResult
    wall_time_ms: int
    model_tokens: int
    artifact_bytes: int
    artifact_ids: tuple[str, ...] = ()
    error_code: str | None = None
    production_traffic_observed: bool = False
    user_visible_output_emitted: bool = False
    background_scheduling_used: bool = False
    query_path_writes: int = 0
    canon_writes: int = 0
    memory_writes: int = 0
    graph_writes: int = 0
    tool_executions: int = 0
    schema_version: str = READER_SHADOW_WORK_RECEIPT_SCHEMA_VERSION
    receipt_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "plan_id",
            "plan_signature_id",
            "status_id",
            "environment_id",
            "harness_digest",
            "work_item_id",
        ):
            _text(getattr(self, name), name)
        _positive_int(self.attempt, "attempt")
        started = _utc(self.started_at_utc, "started_at_utc")
        completed = _utc(self.completed_at_utc, "completed_at_utc")
        if completed <= started:
            raise ReaderShadowBurnInLedgerError(
                "completed_at_utc must be after started_at_utc"
            )
        elapsed_ms = int((completed - started).total_seconds() * 1000)
        _nonnegative_int(self.wall_time_ms, "wall_time_ms")
        if self.wall_time_ms != elapsed_ms:
            raise ReaderShadowBurnInLedgerError(
                "wall_time_ms must exactly match receipt timestamps"
            )
        for name in ("model_tokens", "artifact_bytes"):
            _nonnegative_int(getattr(self, name), name)
        if not isinstance(self.result, ShadowWorkResult):
            raise ReaderShadowBurnInLedgerError(
                "result must be a ShadowWorkResult"
            )
        artifacts = _canonical_texts(self.artifact_ids, "artifact_id")
        if self.result is ShadowWorkResult.SUCCEEDED:
            if self.error_code is not None:
                raise ReaderShadowBurnInLedgerError(
                    "successful work receipt cannot include error_code"
                )
        else:
            _text(self.error_code, "error_code")
        for name in (
            "query_path_writes",
            "canon_writes",
            "memory_writes",
            "graph_writes",
            "tool_executions",
        ):
            _nonnegative_int(getattr(self, name), name)
            if getattr(self, name) != 0:
                raise ReaderShadowBurnInLedgerError(
                    f"{name} must remain zero in shadow burn-in"
                )
        for name in (
            "production_traffic_observed",
            "user_visible_output_emitted",
            "background_scheduling_used",
        ):
            if getattr(self, name) is not False:
                raise ReaderShadowBurnInLedgerError(
                    f"{name} must remain false in shadow burn-in"
                )
        if self.schema_version != READER_SHADOW_WORK_RECEIPT_SCHEMA_VERSION:
            raise ReaderShadowBurnInLedgerError(
                "unsupported shadow work receipt schema"
            )
        object.__setattr__(self, "artifact_ids", artifacts)
        expected = stable_reader_core_id(
            "reader-shadow-work-receipt",
            self.identity_payload(include_id=False),
        )
        if self.receipt_id:
            if self.receipt_id != expected:
                raise ReaderShadowBurnInLedgerError(
                    "receipt_id does not match shadow work receipt content"
                )
        else:
            object.__setattr__(self, "receipt_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "plan_signature_id": self.plan_signature_id,
            "status_id": self.status_id,
            "environment_id": self.environment_id,
            "harness_digest": self.harness_digest,
            "work_item_id": self.work_item_id,
            "attempt": self.attempt,
            "started_at_utc": self.started_at_utc,
            "completed_at_utc": self.completed_at_utc,
            "result": self.result.value,
            "wall_time_ms": self.wall_time_ms,
            "model_tokens": self.model_tokens,
            "artifact_bytes": self.artifact_bytes,
            "artifact_ids": list(self.artifact_ids),
            "error_code": self.error_code,
            "production_traffic_observed": self.production_traffic_observed,
            "user_visible_output_emitted": self.user_visible_output_emitted,
            "background_scheduling_used": self.background_scheduling_used,
            "query_path_writes": self.query_path_writes,
            "canon_writes": self.canon_writes,
            "memory_writes": self.memory_writes,
            "graph_writes": self.graph_writes,
            "tool_executions": self.tool_executions,
        }
        if include_id:
            payload["receipt_id"] = self.receipt_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderShadowWorkSignature:
    receipt_id: str
    key_id: str
    receipt_sha256: str
    signature_hex: str
    algorithm: str = READER_SHADOW_WORK_SIGNATURE_ALGORITHM
    schema_version: str = READER_SHADOW_WORK_SIGNATURE_SCHEMA_VERSION
    signature_id: str = ""

    def __post_init__(self) -> None:
        _text(self.receipt_id, "receipt_id")
        _text(self.key_id, "key_id")
        _sha256(self.receipt_sha256, "receipt_sha256")
        _sha256(self.signature_hex, "signature_hex")
        if self.algorithm != READER_SHADOW_WORK_SIGNATURE_ALGORITHM:
            raise ReaderShadowBurnInLedgerError(
                "unsupported shadow work signature algorithm"
            )
        if self.schema_version != READER_SHADOW_WORK_SIGNATURE_SCHEMA_VERSION:
            raise ReaderShadowBurnInLedgerError(
                "unsupported shadow work signature schema"
            )
        expected = stable_reader_core_id(
            "reader-shadow-work-signature",
            self.identity_payload(include_id=False),
        )
        if self.signature_id:
            if self.signature_id != expected:
                raise ReaderShadowBurnInLedgerError(
                    "signature_id does not match shadow work signature content"
                )
        else:
            object.__setattr__(self, "signature_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "algorithm": self.algorithm,
            "receipt_id": self.receipt_id,
            "key_id": self.key_id,
            "receipt_sha256": self.receipt_sha256,
            "signature_hex": self.signature_hex,
        }
        if include_id:
            payload["signature_id"] = self.signature_id
        return payload


class ReaderShadowWorkSigner:
    @staticmethod
    def sign(
        receipt: ReaderShadowWorkReceipt,
        *,
        key_id: str,
        secret: bytes,
    ) -> ReaderShadowWorkSignature:
        if not isinstance(receipt, ReaderShadowWorkReceipt):
            raise ReaderShadowBurnInLedgerError(
                "receipt must be a ReaderShadowWorkReceipt"
            )
        _text(key_id, "key_id")
        _secret(secret)
        payload = canonical_json_bytes(receipt)
        return ReaderShadowWorkSignature(
            receipt_id=receipt.receipt_id,
            key_id=key_id,
            receipt_sha256=hashlib.sha256(payload).hexdigest(),
            signature_hex=hmac.new(secret, payload, hashlib.sha256).hexdigest(),
        )

    @staticmethod
    def verify(
        receipt: ReaderShadowWorkReceipt,
        signature: ReaderShadowWorkSignature,
        *,
        secret: bytes,
    ) -> bool:
        if not isinstance(receipt, ReaderShadowWorkReceipt):
            raise ReaderShadowBurnInLedgerError(
                "receipt must be a ReaderShadowWorkReceipt"
            )
        if not isinstance(signature, ReaderShadowWorkSignature):
            raise ReaderShadowBurnInLedgerError(
                "signature must be a ReaderShadowWorkSignature"
            )
        _secret(secret)
        if signature.receipt_id != receipt.receipt_id:
            return False
        payload = canonical_json_bytes(receipt)
        digest = hashlib.sha256(payload).hexdigest()
        if not hmac.compare_digest(signature.receipt_sha256, digest):
            return False
        expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature.signature_hex, expected)


@dataclass(frozen=True, slots=True)
class ReaderShadowBurnInLedger:
    plan_id: str
    plan_signature_id: str
    environment_id: str
    harness_digest: str
    work_item_ids: tuple[str, ...]
    max_attempts_per_work_item: int
    per_work_item_timeout_ms: int
    max_total_wall_time_ms: int
    max_total_model_tokens: int
    max_total_artifact_bytes: int
    max_consecutive_failures: int
    receipts: tuple[ReaderShadowWorkReceipt, ...] = ()
    receipt_signature_ids: tuple[str, ...] = ()
    schema_version: str = READER_SHADOW_BURN_IN_LEDGER_SCHEMA_VERSION
    ledger_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "plan_id",
            "plan_signature_id",
            "environment_id",
            "harness_digest",
        ):
            _text(getattr(self, name), name)
        work_items = _canonical_texts(self.work_item_ids, "work_item_id")
        if not work_items:
            raise ReaderShadowBurnInLedgerError(
                "ledger requires at least one work item"
            )
        for name in (
            "max_attempts_per_work_item",
            "per_work_item_timeout_ms",
            "max_total_wall_time_ms",
            "max_total_model_tokens",
            "max_total_artifact_bytes",
            "max_consecutive_failures",
        ):
            _positive_int(getattr(self, name), name)
        receipts = tuple(self.receipts)
        if any(not isinstance(item, ReaderShadowWorkReceipt) for item in receipts):
            raise ReaderShadowBurnInLedgerError(
                "receipts require ReaderShadowWorkReceipt values"
            )
        signature_ids = tuple(self.receipt_signature_ids)
        if len(signature_ids) != len(receipts):
            raise ReaderShadowBurnInLedgerError(
                "every ledger receipt requires one signature ID"
            )
        for signature_id in signature_ids:
            _text(signature_id, "receipt_signature_id")
        if len(set(signature_ids)) != len(signature_ids):
            raise ReaderShadowBurnInLedgerError(
                "receipt signature IDs must be unique"
            )
        self._validate_receipt_chain(receipts)
        if self.schema_version != READER_SHADOW_BURN_IN_LEDGER_SCHEMA_VERSION:
            raise ReaderShadowBurnInLedgerError(
                "unsupported shadow burn-in ledger schema"
            )
        object.__setattr__(self, "work_item_ids", work_items)
        object.__setattr__(self, "receipts", receipts)
        object.__setattr__(self, "receipt_signature_ids", signature_ids)
        expected = stable_reader_core_id(
            "reader-shadow-burn-in-ledger",
            self.identity_payload(include_id=False),
        )
        if self.ledger_id:
            if self.ledger_id != expected:
                raise ReaderShadowBurnInLedgerError(
                    "ledger_id does not match shadow burn-in ledger content"
                )
        else:
            object.__setattr__(self, "ledger_id", expected)

    def _validate_receipt_chain(
        self,
        receipts: tuple[ReaderShadowWorkReceipt, ...],
    ) -> None:
        allowed = set(self.work_item_ids)
        expected_attempt: dict[str, int] = {item: 1 for item in allowed}
        succeeded: set[str] = set()
        previous_order: tuple[datetime, str, int] | None = None
        for receipt in receipts:
            if (
                receipt.plan_id != self.plan_id
                or receipt.plan_signature_id != self.plan_signature_id
                or receipt.environment_id != self.environment_id
                or receipt.harness_digest != self.harness_digest
            ):
                raise ReaderShadowBurnInLedgerError(
                    "receipt belongs to a different shadow campaign"
                )
            if receipt.work_item_id not in allowed:
                raise ReaderShadowBurnInLedgerError(
                    "receipt work item is outside the campaign plan"
                )
            if receipt.work_item_id in succeeded:
                raise ReaderShadowBurnInLedgerError(
                    "successful work item cannot receive later attempts"
                )
            expected = expected_attempt[receipt.work_item_id]
            if receipt.attempt != expected:
                raise ReaderShadowBurnInLedgerError(
                    "work item attempts must be contiguous and start at one"
                )
            if receipt.attempt > self.max_attempts_per_work_item:
                raise ReaderShadowBurnInLedgerError(
                    "work item attempt exceeds campaign limit"
                )
            expected_attempt[receipt.work_item_id] += 1
            if receipt.result is ShadowWorkResult.SUCCEEDED:
                succeeded.add(receipt.work_item_id)
            order = (
                _utc(receipt.completed_at_utc, "completed_at_utc"),
                receipt.work_item_id,
                receipt.attempt,
            )
            if previous_order is not None and order <= previous_order:
                raise ReaderShadowBurnInLedgerError(
                    "receipts must use strict canonical completion ordering"
                )
            previous_order = order

    @property
    def total_wall_time_ms(self) -> int:
        return sum(item.wall_time_ms for item in self.receipts)

    @property
    def total_model_tokens(self) -> int:
        return sum(item.model_tokens for item in self.receipts)

    @property
    def total_artifact_bytes(self) -> int:
        return sum(item.artifact_bytes for item in self.receipts)

    @property
    def successful_work_item_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                item.work_item_id
                for item in self.receipts
                if item.result is ShadowWorkResult.SUCCEEDED
            )
        )

    @property
    def pending_work_item_ids(self) -> tuple[str, ...]:
        success = set(self.successful_work_item_ids)
        attempts: dict[str, int] = {item: 0 for item in self.work_item_ids}
        for receipt in self.receipts:
            attempts[receipt.work_item_id] += 1
        return tuple(
            item
            for item in self.work_item_ids
            if item not in success
            and attempts[item] < self.max_attempts_per_work_item
        )

    @property
    def consecutive_failure_count(self) -> int:
        count = 0
        for receipt in reversed(self.receipts):
            if receipt.result is ShadowWorkResult.SUCCEEDED:
                break
            count += 1
        return count

    @property
    def exhaustion_codes(self) -> tuple[str, ...]:
        codes: list[str] = []
        if any(
            item.wall_time_ms > self.per_work_item_timeout_ms
            for item in self.receipts
        ):
            codes.append("per_work_item_timeout_exceeded")
        if self.total_wall_time_ms >= self.max_total_wall_time_ms:
            codes.append("total_wall_time_exhausted")
        if self.total_model_tokens >= self.max_total_model_tokens:
            codes.append("total_model_tokens_exhausted")
        if self.total_artifact_bytes >= self.max_total_artifact_bytes:
            codes.append("total_artifact_bytes_exhausted")
        return tuple(codes)

    @property
    def status(self) -> ShadowBurnInLedgerStatus:
        if len(self.successful_work_item_ids) == len(self.work_item_ids):
            return ShadowBurnInLedgerStatus.COMPLETE_SUCCESS
        if self.exhaustion_codes:
            return ShadowBurnInLedgerStatus.BUDGET_EXHAUSTED
        if self.consecutive_failure_count >= self.max_consecutive_failures:
            return ShadowBurnInLedgerStatus.FAILURE_LIMIT_REACHED
        if not self.pending_work_item_ids:
            return ShadowBurnInLedgerStatus.COMPLETE_WITH_FAILURES
        if self.receipts:
            return ShadowBurnInLedgerStatus.IN_PROGRESS
        return ShadowBurnInLedgerStatus.READY

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            ShadowBurnInLedgerStatus.COMPLETE_SUCCESS,
            ShadowBurnInLedgerStatus.COMPLETE_WITH_FAILURES,
            ShadowBurnInLedgerStatus.BUDGET_EXHAUSTED,
            ShadowBurnInLedgerStatus.FAILURE_LIMIT_REACHED,
        }

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "plan_signature_id": self.plan_signature_id,
            "environment_id": self.environment_id,
            "harness_digest": self.harness_digest,
            "work_item_ids": list(self.work_item_ids),
            "max_attempts_per_work_item": self.max_attempts_per_work_item,
            "per_work_item_timeout_ms": self.per_work_item_timeout_ms,
            "max_total_wall_time_ms": self.max_total_wall_time_ms,
            "max_total_model_tokens": self.max_total_model_tokens,
            "max_total_artifact_bytes": self.max_total_artifact_bytes,
            "max_consecutive_failures": self.max_consecutive_failures,
            "receipt_ids": [item.receipt_id for item in self.receipts],
            "receipt_signature_ids": list(self.receipt_signature_ids),
        }
        if include_id:
            payload["ledger_id"] = self.ledger_id
        return payload


class ReaderShadowBurnInLedgerBuilder:
    """Create and append to one authenticated, bounded result ledger."""

    @staticmethod
    def empty(
        *,
        plan: ReaderShadowBurnInPlan,
        plan_signature: ReaderShadowBurnInPlanSignature,
        status: ReaderShadowBurnInStatusReceipt,
        secret: bytes,
    ) -> ReaderShadowBurnInLedger:
        _validate_ready_campaign(plan, plan_signature, status, secret)
        source = plan.source
        return ReaderShadowBurnInLedger(
            plan_id=plan.plan_id,
            plan_signature_id=plan_signature.signature_id,
            environment_id=source.environment_id,
            harness_digest=source.harness_digest,
            work_item_ids=source.work_item_ids,
            max_attempts_per_work_item=source.max_attempts_per_work_item,
            per_work_item_timeout_ms=source.per_work_item_timeout_ms,
            max_total_wall_time_ms=source.max_total_wall_time_ms,
            max_total_model_tokens=source.max_total_model_tokens,
            max_total_artifact_bytes=source.max_total_artifact_bytes,
            max_consecutive_failures=source.max_consecutive_failures,
        )

    @staticmethod
    def append(
        *,
        plan: ReaderShadowBurnInPlan,
        plan_signature: ReaderShadowBurnInPlanSignature,
        status: ReaderShadowBurnInStatusReceipt,
        ledger: ReaderShadowBurnInLedger,
        receipt: ReaderShadowWorkReceipt,
        receipt_signature: ReaderShadowWorkSignature,
        secret: bytes,
    ) -> ReaderShadowBurnInLedger:
        _validate_ready_campaign(plan, plan_signature, status, secret)
        if not isinstance(ledger, ReaderShadowBurnInLedger):
            raise ReaderShadowBurnInLedgerError(
                "ledger must be a ReaderShadowBurnInLedger"
            )
        expected_empty = ReaderShadowBurnInLedgerBuilder.empty(
            plan=plan,
            plan_signature=plan_signature,
            status=status,
            secret=secret,
        )
        for name in (
            "plan_id",
            "plan_signature_id",
            "environment_id",
            "harness_digest",
            "work_item_ids",
            "max_attempts_per_work_item",
            "per_work_item_timeout_ms",
            "max_total_wall_time_ms",
            "max_total_model_tokens",
            "max_total_artifact_bytes",
            "max_consecutive_failures",
        ):
            if getattr(ledger, name) != getattr(expected_empty, name):
                raise ReaderShadowBurnInLedgerError(
                    "ledger belongs to a different shadow campaign"
                )
        if ledger.is_terminal:
            raise ReaderShadowBurnInLedgerError(
                "cannot append to terminal shadow burn-in ledger"
            )
        if not ReaderShadowWorkSigner.verify(
            receipt,
            receipt_signature,
            secret=secret,
        ):
            raise ReaderShadowBurnInLedgerError(
                "shadow work receipt signature verification failed"
            )
        if (
            receipt.status_id != status.status_id
            or receipt.started_at_utc != status.as_of_utc
        ):
            raise ReaderShadowBurnInLedgerError(
                "receipt must bind exact READY admission status and time"
            )
        return ReaderShadowBurnInLedger(
            plan_id=ledger.plan_id,
            plan_signature_id=ledger.plan_signature_id,
            environment_id=ledger.environment_id,
            harness_digest=ledger.harness_digest,
            work_item_ids=ledger.work_item_ids,
            max_attempts_per_work_item=ledger.max_attempts_per_work_item,
            per_work_item_timeout_ms=ledger.per_work_item_timeout_ms,
            max_total_wall_time_ms=ledger.max_total_wall_time_ms,
            max_total_model_tokens=ledger.max_total_model_tokens,
            max_total_artifact_bytes=ledger.max_total_artifact_bytes,
            max_consecutive_failures=ledger.max_consecutive_failures,
            receipts=(*ledger.receipts, receipt),
            receipt_signature_ids=(
                *ledger.receipt_signature_ids,
                receipt_signature.signature_id,
            ),
        )


def _validate_ready_campaign(
    plan: ReaderShadowBurnInPlan,
    plan_signature: ReaderShadowBurnInPlanSignature,
    status: ReaderShadowBurnInStatusReceipt,
    secret: bytes,
) -> None:
    if not isinstance(plan, ReaderShadowBurnInPlan):
        raise ReaderShadowBurnInLedgerError(
            "plan must be a ReaderShadowBurnInPlan"
        )
    if not isinstance(plan_signature, ReaderShadowBurnInPlanSignature):
        raise ReaderShadowBurnInLedgerError(
            "plan_signature must be a ReaderShadowBurnInPlanSignature"
        )
    if not ReaderShadowBurnInPlanSigner.verify(
        plan,
        plan_signature,
        secret=secret,
    ):
        raise ReaderShadowBurnInLedgerError(
            "shadow burn-in plan signature verification failed"
        )
    if not isinstance(status, ReaderShadowBurnInStatusReceipt):
        raise ReaderShadowBurnInLedgerError(
            "status must be a ReaderShadowBurnInStatusReceipt"
        )
    if (
        status.plan_id != plan.plan_id
        or status.plan_signature_id != plan_signature.signature_id
    ):
        raise ReaderShadowBurnInLedgerError(
            "status belongs to a different shadow burn-in plan"
        )
    if (
        status.status is not ShadowBurnInStatus.READY
        or status.shadow_evaluation_authorized is not True
    ):
        raise ReaderShadowBurnInLedgerError(
            "shadow work requires exact READY RDR-26 status"
        )


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderShadowBurnInLedgerError(
            f"{field_name} must be non-empty text"
        )
    return value


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ReaderShadowBurnInLedgerError(
            f"{field_name} must be an integer greater than zero"
        )
    return value


def _nonnegative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReaderShadowBurnInLedgerError(
            f"{field_name} must be a non-negative integer"
        )
    return value


def _canonical_texts(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    items = tuple(values)
    for item in items:
        _text(item, field_name)
    if len(set(items)) != len(items):
        raise ReaderShadowBurnInLedgerError(
            f"{field_name} values must be unique"
        )
    if items != tuple(sorted(items)):
        raise ReaderShadowBurnInLedgerError(
            f"{field_name} values must use canonical ordering"
        )
    return items


def _utc(value: object, field_name: str) -> datetime:
    text = _text(value, field_name)
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise ReaderShadowBurnInLedgerError(
            f"{field_name} must use canonical UTC format "
            "YYYY-MM-DDTHH:MM:SSZ"
        ) from exc


def _sha256(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    if len(text) != 64 or text.lower() != text:
        raise ReaderShadowBurnInLedgerError(
            f"{field_name} must be lowercase SHA-256 hex"
        )
    try:
        int(text, 16)
    except ValueError as exc:
        raise ReaderShadowBurnInLedgerError(
            f"{field_name} must be lowercase SHA-256 hex"
        ) from exc
    return text


def _secret(value: object) -> bytes:
    if not isinstance(value, bytes) or len(value) < 32:
        raise ReaderShadowBurnInLedgerError(
            "HMAC secret must be bytes and at least 32 bytes long"
        )
    return value


__all__ = [
    "READER_SHADOW_BURN_IN_LEDGER_SCHEMA_VERSION",
    "READER_SHADOW_WORK_RECEIPT_SCHEMA_VERSION",
    "READER_SHADOW_WORK_SIGNATURE_ALGORITHM",
    "READER_SHADOW_WORK_SIGNATURE_SCHEMA_VERSION",
    "ReaderShadowBurnInLedger",
    "ReaderShadowBurnInLedgerBuilder",
    "ReaderShadowBurnInLedgerError",
    "ReaderShadowWorkReceipt",
    "ReaderShadowWorkSignature",
    "ReaderShadowWorkSigner",
    "ShadowBurnInLedgerStatus",
    "ShadowWorkResult",
]
