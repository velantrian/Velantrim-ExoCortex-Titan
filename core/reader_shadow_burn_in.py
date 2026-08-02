"""Signed shadow burn-in campaign control contracts for PR-RDR-26.

This module defines a deterministic control plane for an isolated Reader Core
shadow campaign. It does not execute a pipeline, route production traffic,
schedule background work, expose user-visible output, or grant persistent
write/tool authority.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import json
from pathlib import Path
from typing import Any, TypeVar, cast

from core.reader_benchmark_runner import canonical_json_bytes, write_canonical_json
from core.reader_core_contracts import stable_reader_core_id
from core.reader_operator_decision import (
    OperatorDecisionDisposition,
    OperatorDecisionStatus,
    ReaderOperatorDecisionEvaluator,
    ReaderOperatorDecisionRecord,
    ReaderOperatorDecisionRevocation,
    ReaderOperatorDecisionSignature,
    ReaderOperatorRevocationSignature,
)

READER_SHADOW_BURN_IN_SOURCE_SCHEMA_VERSION = (
    "reader-core.shadow-burn-in-source.v1"
)
READER_SHADOW_BURN_IN_PLAN_SCHEMA_VERSION = "reader-core.shadow-burn-in-plan.v1"
READER_SHADOW_BURN_IN_PLAN_SIGNATURE_SCHEMA_VERSION = (
    "reader-core.shadow-burn-in-plan-signature.v1"
)
READER_SHADOW_BURN_IN_CONTROL_SOURCE_SCHEMA_VERSION = (
    "reader-core.shadow-burn-in-control-source.v1"
)
READER_SHADOW_BURN_IN_CONTROL_RECEIPT_SCHEMA_VERSION = (
    "reader-core.shadow-burn-in-control-receipt.v1"
)
READER_SHADOW_BURN_IN_CONTROL_SIGNATURE_SCHEMA_VERSION = (
    "reader-core.shadow-burn-in-control-signature.v1"
)
READER_SHADOW_BURN_IN_STATUS_SCHEMA_VERSION = (
    "reader-core.shadow-burn-in-status.v1"
)
READER_SHADOW_BURN_IN_SIGNATURE_ALGORITHM = "hmac-sha256"


class ReaderShadowBurnInError(ValueError):
    """Raised when shadow burn-in evidence is malformed or inconsistent."""


class ShadowBurnInControlAction(str, Enum):
    ARM = "arm"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    KILL = "kill"


class ShadowBurnInControlState(str, Enum):
    ARMED = "armed"
    PAUSED = "paused"
    STOPPED = "stopped"
    KILLED = "killed"


class ShadowBurnInStatus(str, Enum):
    NOT_YET_VALID = "not_yet_valid"
    READY = "ready"
    PAUSED = "paused"
    STOPPED = "stopped"
    KILLED = "killed"
    EXPIRED = "expired"
    APPROVAL_REVOKED = "approval_revoked"
    APPROVAL_INACTIVE = "approval_inactive"


@dataclass(frozen=True, slots=True)
class ReaderShadowBurnInSource:
    campaign_name: str
    environment_id: str
    harness_digest: str
    planned_start_utc: str
    planned_end_utc: str
    work_item_ids: tuple[str, ...]
    max_attempts_per_work_item: int
    per_work_item_timeout_ms: int
    max_total_wall_time_ms: int
    max_total_model_tokens: int
    max_total_artifact_bytes: int
    max_consecutive_failures: int
    condition_codes: tuple[str, ...]
    schema_version: str = READER_SHADOW_BURN_IN_SOURCE_SCHEMA_VERSION
    source_id: str = ""

    def __post_init__(self) -> None:
        for name in ("campaign_name", "environment_id", "harness_digest"):
            _text(getattr(self, name), name)
        start = _utc(self.planned_start_utc, "planned_start_utc")
        end = _utc(self.planned_end_utc, "planned_end_utc")
        if start >= end:
            raise ReaderShadowBurnInError(
                "planned_end_utc must be after planned_start_utc"
            )
        work_items = _canonical_texts(self.work_item_ids, "work_item_id")
        if not work_items:
            raise ReaderShadowBurnInError(
                "work_item_ids require at least one explicit reference"
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
        conditions = _canonical_texts(self.condition_codes, "condition_code")
        if not conditions:
            raise ReaderShadowBurnInError(
                "shadow burn-in requires explicit condition codes"
            )
        if self.schema_version != READER_SHADOW_BURN_IN_SOURCE_SCHEMA_VERSION:
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in source schema"
            )
        object.__setattr__(self, "work_item_ids", work_items)
        object.__setattr__(self, "condition_codes", conditions)
        _set_or_verify_id(self, "source_id", "reader-shadow-burn-in-source")

    def source_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "campaign_name": self.campaign_name,
            "environment_id": self.environment_id,
            "harness_digest": self.harness_digest,
            "planned_start_utc": self.planned_start_utc,
            "planned_end_utc": self.planned_end_utc,
            "work_item_ids": list(self.work_item_ids),
            "max_attempts_per_work_item": self.max_attempts_per_work_item,
            "per_work_item_timeout_ms": self.per_work_item_timeout_ms,
            "max_total_wall_time_ms": self.max_total_wall_time_ms,
            "max_total_model_tokens": self.max_total_model_tokens,
            "max_total_artifact_bytes": self.max_total_artifact_bytes,
            "max_consecutive_failures": self.max_consecutive_failures,
            "condition_codes": list(self.condition_codes),
        }

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload = self.source_payload()
        if include_id:
            payload["source_id"] = self.source_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderShadowBurnInPlan:
    source: ReaderShadowBurnInSource
    decision_id: str
    decision_signature_id: str
    decision_status_id: str
    evidence_id: str
    benchmark_verification_id: str
    retention_manifest_id: str
    retention_verification_id: str
    shadow_evaluation_authorized: bool = True
    production_traffic_authorized: bool = False
    user_visible_output_authorized: bool = False
    background_scheduling_authorized: bool = False
    query_path_wiring_authorized: bool = False
    canon_write_authorized: bool = False
    memory_write_authorized: bool = False
    graph_write_authorized: bool = False
    tool_execution_authorized: bool = False
    schema_version: str = READER_SHADOW_BURN_IN_PLAN_SCHEMA_VERSION
    plan_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.source, ReaderShadowBurnInSource):
            raise ReaderShadowBurnInError(
                "source must be a ReaderShadowBurnInSource"
            )
        for name in (
            "decision_id",
            "decision_signature_id",
            "decision_status_id",
            "evidence_id",
            "benchmark_verification_id",
            "retention_manifest_id",
            "retention_verification_id",
        ):
            _text(getattr(self, name), name)
        if self.shadow_evaluation_authorized is not True:
            raise ReaderShadowBurnInError(
                "shadow_evaluation_authorized must be true for a plan"
            )
        _validate_no_live_authority(self)
        if self.schema_version != READER_SHADOW_BURN_IN_PLAN_SCHEMA_VERSION:
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in plan schema"
            )
        _set_or_verify_id(self, "plan_id", "reader-shadow-burn-in-plan")

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload = {
            "schema_version": self.schema_version,
            "source": self.source.identity_payload(),
            "decision_id": self.decision_id,
            "decision_signature_id": self.decision_signature_id,
            "decision_status_id": self.decision_status_id,
            "evidence_id": self.evidence_id,
            "benchmark_verification_id": self.benchmark_verification_id,
            "retention_manifest_id": self.retention_manifest_id,
            "retention_verification_id": self.retention_verification_id,
            "shadow_evaluation_authorized": self.shadow_evaluation_authorized,
            **_authority_payload(self),
        }
        if include_id:
            payload["plan_id"] = self.plan_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderShadowBurnInPlanSignature:
    plan_id: str
    key_id: str
    plan_sha256: str
    signature_hex: str
    algorithm: str = READER_SHADOW_BURN_IN_SIGNATURE_ALGORITHM
    schema_version: str = READER_SHADOW_BURN_IN_PLAN_SIGNATURE_SCHEMA_VERSION
    signature_id: str = ""

    def __post_init__(self) -> None:
        _text(self.plan_id, "plan_id")
        _text(self.key_id, "key_id")
        _sha256(self.plan_sha256, "plan_sha256")
        _sha256(self.signature_hex, "signature_hex")
        if self.algorithm != READER_SHADOW_BURN_IN_SIGNATURE_ALGORITHM:
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in signature algorithm"
            )
        if (
            self.schema_version
            != READER_SHADOW_BURN_IN_PLAN_SIGNATURE_SCHEMA_VERSION
        ):
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in plan signature schema"
            )
        _set_or_verify_id(
            self,
            "signature_id",
            "reader-shadow-burn-in-plan-signature",
        )

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "algorithm": self.algorithm,
            "plan_id": self.plan_id,
            "key_id": self.key_id,
            "plan_sha256": self.plan_sha256,
            "signature_hex": self.signature_hex,
        }
        if include_id:
            payload["signature_id"] = self.signature_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderShadowBurnInControlSource:
    operator_id: str
    action: ShadowBurnInControlAction
    issued_at_utc: str
    reason_codes: tuple[str, ...]
    previous_receipt_id: str | None = None
    schema_version: str = READER_SHADOW_BURN_IN_CONTROL_SOURCE_SCHEMA_VERSION
    source_id: str = ""

    def __post_init__(self) -> None:
        _text(self.operator_id, "operator_id")
        if not isinstance(self.action, ShadowBurnInControlAction):
            raise ReaderShadowBurnInError(
                "action must be a ShadowBurnInControlAction"
            )
        _utc(self.issued_at_utc, "issued_at_utc")
        reasons = _canonical_texts(self.reason_codes, "reason_code")
        if not reasons:
            raise ReaderShadowBurnInError(
                "control actions require explicit reason codes"
            )
        if self.previous_receipt_id is not None:
            _text(self.previous_receipt_id, "previous_receipt_id")
        if self.action in {
            ShadowBurnInControlAction.PAUSE,
            ShadowBurnInControlAction.RESUME,
            ShadowBurnInControlAction.STOP,
        } and self.previous_receipt_id is None:
            raise ReaderShadowBurnInError(
                "pause, resume, and stop require previous_receipt_id"
            )
        if (
            self.action is ShadowBurnInControlAction.ARM
            and self.previous_receipt_id is not None
        ):
            raise ReaderShadowBurnInError(
                "arm must not reference a previous receipt"
            )
        if (
            self.schema_version
            != READER_SHADOW_BURN_IN_CONTROL_SOURCE_SCHEMA_VERSION
        ):
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in control source schema"
            )
        object.__setattr__(self, "reason_codes", reasons)
        _set_or_verify_id(
            self,
            "source_id",
            "reader-shadow-burn-in-control-source",
        )

    def source_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "operator_id": self.operator_id,
            "action": self.action.value,
            "issued_at_utc": self.issued_at_utc,
            "reason_codes": list(self.reason_codes),
            "previous_receipt_id": self.previous_receipt_id,
        }

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload = self.source_payload()
        if include_id:
            payload["source_id"] = self.source_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderShadowBurnInControlReceipt:
    plan_id: str
    plan_signature_id: str
    source: ReaderShadowBurnInControlSource
    state: ShadowBurnInControlState
    control_allows_shadow: bool
    production_traffic_authorized: bool = False
    user_visible_output_authorized: bool = False
    background_scheduling_authorized: bool = False
    query_path_wiring_authorized: bool = False
    canon_write_authorized: bool = False
    memory_write_authorized: bool = False
    graph_write_authorized: bool = False
    tool_execution_authorized: bool = False
    schema_version: str = READER_SHADOW_BURN_IN_CONTROL_RECEIPT_SCHEMA_VERSION
    receipt_id: str = ""

    def __post_init__(self) -> None:
        _text(self.plan_id, "plan_id")
        _text(self.plan_signature_id, "plan_signature_id")
        if not isinstance(self.source, ReaderShadowBurnInControlSource):
            raise ReaderShadowBurnInError(
                "source must be a ReaderShadowBurnInControlSource"
            )
        if not isinstance(self.state, ShadowBurnInControlState):
            raise ReaderShadowBurnInError(
                "state must be a ShadowBurnInControlState"
            )
        expected = self.state is ShadowBurnInControlState.ARMED
        if self.control_allows_shadow is not expected:
            raise ReaderShadowBurnInError(
                "control_allows_shadow must exactly match armed state"
            )
        _validate_no_live_authority(self)
        if (
            self.schema_version
            != READER_SHADOW_BURN_IN_CONTROL_RECEIPT_SCHEMA_VERSION
        ):
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in control receipt schema"
            )
        _set_or_verify_id(
            self,
            "receipt_id",
            "reader-shadow-burn-in-control-receipt",
        )

    @property
    def issued_at_utc(self) -> str:
        return self.source.issued_at_utc

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload = {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "plan_signature_id": self.plan_signature_id,
            "source": self.source.identity_payload(),
            "state": self.state.value,
            "control_allows_shadow": self.control_allows_shadow,
            **_authority_payload(self),
        }
        if include_id:
            payload["receipt_id"] = self.receipt_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderShadowBurnInControlSignature:
    receipt_id: str
    key_id: str
    receipt_sha256: str
    signature_hex: str
    algorithm: str = READER_SHADOW_BURN_IN_SIGNATURE_ALGORITHM
    schema_version: str = READER_SHADOW_BURN_IN_CONTROL_SIGNATURE_SCHEMA_VERSION
    signature_id: str = ""

    def __post_init__(self) -> None:
        _text(self.receipt_id, "receipt_id")
        _text(self.key_id, "key_id")
        _sha256(self.receipt_sha256, "receipt_sha256")
        _sha256(self.signature_hex, "signature_hex")
        if self.algorithm != READER_SHADOW_BURN_IN_SIGNATURE_ALGORITHM:
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in signature algorithm"
            )
        if (
            self.schema_version
            != READER_SHADOW_BURN_IN_CONTROL_SIGNATURE_SCHEMA_VERSION
        ):
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in control signature schema"
            )
        _set_or_verify_id(
            self,
            "signature_id",
            "reader-shadow-burn-in-control-signature",
        )

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


@dataclass(frozen=True, slots=True)
class ReaderShadowBurnInStatusReceipt:
    plan_id: str
    plan_signature_id: str
    control_receipt_id: str
    control_signature_id: str
    decision_status_id: str
    as_of_utc: str
    status: ShadowBurnInStatus
    shadow_evaluation_authorized: bool
    production_traffic_authorized: bool = False
    user_visible_output_authorized: bool = False
    background_scheduling_authorized: bool = False
    query_path_wiring_authorized: bool = False
    canon_write_authorized: bool = False
    memory_write_authorized: bool = False
    graph_write_authorized: bool = False
    tool_execution_authorized: bool = False
    schema_version: str = READER_SHADOW_BURN_IN_STATUS_SCHEMA_VERSION
    status_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "plan_id",
            "plan_signature_id",
            "control_receipt_id",
            "control_signature_id",
            "decision_status_id",
        ):
            _text(getattr(self, name), name)
        _utc(self.as_of_utc, "as_of_utc")
        if not isinstance(self.status, ShadowBurnInStatus):
            raise ReaderShadowBurnInError(
                "status must be a ShadowBurnInStatus"
            )
        expected = self.status is ShadowBurnInStatus.READY
        if self.shadow_evaluation_authorized is not expected:
            raise ReaderShadowBurnInError(
                "shadow authorization must exactly match ready status"
            )
        _validate_no_live_authority(self)
        if self.schema_version != READER_SHADOW_BURN_IN_STATUS_SCHEMA_VERSION:
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in status schema"
            )
        _set_or_verify_id(self, "status_id", "reader-shadow-burn-in-status")

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload = {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "plan_signature_id": self.plan_signature_id,
            "control_receipt_id": self.control_receipt_id,
            "control_signature_id": self.control_signature_id,
            "decision_status_id": self.decision_status_id,
            "as_of_utc": self.as_of_utc,
            "status": self.status.value,
            "shadow_evaluation_authorized": self.shadow_evaluation_authorized,
            **_authority_payload(self),
        }
        if include_id:
            payload["status_id"] = self.status_id
        return payload


class ReaderShadowBurnInPlanBuilder:
    """Build a non-executing plan from an active shadow-only decision."""

    def build(
        self,
        *,
        source: ReaderShadowBurnInSource,
        decision: ReaderOperatorDecisionRecord,
        decision_signature: ReaderOperatorDecisionSignature,
        secret: bytes,
        revocation: ReaderOperatorDecisionRevocation | None = None,
        revocation_signature: ReaderOperatorRevocationSignature | None = None,
    ) -> ReaderShadowBurnInPlan:
        if not isinstance(source, ReaderShadowBurnInSource):
            raise ReaderShadowBurnInError(
                "source must be a ReaderShadowBurnInSource"
            )
        if not isinstance(decision, ReaderOperatorDecisionRecord):
            raise ReaderShadowBurnInError(
                "decision must be a ReaderOperatorDecisionRecord"
            )
        if not isinstance(
            decision_signature,
            ReaderOperatorDecisionSignature,
        ):
            raise ReaderShadowBurnInError(
                "decision_signature must be a decision signature"
            )
        if (
            decision.disposition
            is not OperatorDecisionDisposition.APPROVE_SHADOW_ONLY
            or decision.shadow_evaluation_authorized is not True
        ):
            raise ReaderShadowBurnInError(
                "shadow burn-in requires approve_shadow_only decision"
            )
        decision_status = ReaderOperatorDecisionEvaluator().evaluate(
            decision=decision,
            decision_signature=decision_signature,
            secret=secret,
            as_of_utc=source.planned_start_utc,
            revocation=revocation,
            revocation_signature=revocation_signature,
        )
        if (
            decision_status.status
            is not OperatorDecisionStatus.ACTIVE_SHADOW_APPROVAL
        ):
            raise ReaderShadowBurnInError(
                "shadow burn-in start requires active shadow approval"
            )
        campaign_start = _utc(source.planned_start_utc, "planned_start_utc")
        campaign_end = _utc(source.planned_end_utc, "planned_end_utc")
        approval_start = _utc(
            decision.source.valid_from_utc,
            "decision.valid_from_utc",
        )
        approval_end = _utc(
            decision.source.valid_until_utc,
            "decision.valid_until_utc",
        )
        if campaign_start < approval_start or campaign_end > approval_end:
            raise ReaderShadowBurnInError(
                "campaign window must remain inside operator approval window"
            )
        return ReaderShadowBurnInPlan(
            source=source,
            decision_id=decision.decision_id,
            decision_signature_id=decision_signature.signature_id,
            decision_status_id=decision_status.status_id,
            evidence_id=decision.evidence_id,
            benchmark_verification_id=decision.benchmark_verification_id,
            retention_manifest_id=decision.retention_manifest_id,
            retention_verification_id=decision.retention_verification_id,
        )


class ReaderShadowBurnInPlanSigner:
    @staticmethod
    def sign(
        plan: ReaderShadowBurnInPlan,
        *,
        key_id: str,
        secret: bytes,
    ) -> ReaderShadowBurnInPlanSignature:
        if not isinstance(plan, ReaderShadowBurnInPlan):
            raise ReaderShadowBurnInError(
                "plan must be a ReaderShadowBurnInPlan"
            )
        _text(key_id, "key_id")
        _secret(secret)
        payload = canonical_json_bytes(plan)
        return ReaderShadowBurnInPlanSignature(
            plan_id=plan.plan_id,
            key_id=key_id,
            plan_sha256=hashlib.sha256(payload).hexdigest(),
            signature_hex=hmac.new(secret, payload, hashlib.sha256).hexdigest(),
        )

    @staticmethod
    def verify(
        plan: ReaderShadowBurnInPlan,
        signature: ReaderShadowBurnInPlanSignature,
        *,
        secret: bytes,
    ) -> bool:
        if not isinstance(plan, ReaderShadowBurnInPlan):
            raise ReaderShadowBurnInError(
                "plan must be a ReaderShadowBurnInPlan"
            )
        if not isinstance(signature, ReaderShadowBurnInPlanSignature):
            raise ReaderShadowBurnInError(
                "signature must be a plan signature"
            )
        _secret(secret)
        return _verify_signature(
            value=plan,
            value_id=plan.plan_id,
            signed_id=signature.plan_id,
            recorded_sha256=signature.plan_sha256,
            recorded_signature=signature.signature_hex,
            secret=secret,
        )


class ReaderShadowBurnInControlSigner:
    @staticmethod
    def sign(
        receipt: ReaderShadowBurnInControlReceipt,
        *,
        key_id: str,
        secret: bytes,
    ) -> ReaderShadowBurnInControlSignature:
        if not isinstance(receipt, ReaderShadowBurnInControlReceipt):
            raise ReaderShadowBurnInError(
                "receipt must be a ReaderShadowBurnInControlReceipt"
            )
        _text(key_id, "key_id")
        _secret(secret)
        payload = canonical_json_bytes(receipt)
        return ReaderShadowBurnInControlSignature(
            receipt_id=receipt.receipt_id,
            key_id=key_id,
            receipt_sha256=hashlib.sha256(payload).hexdigest(),
            signature_hex=hmac.new(secret, payload, hashlib.sha256).hexdigest(),
        )

    @staticmethod
    def verify(
        receipt: ReaderShadowBurnInControlReceipt,
        signature: ReaderShadowBurnInControlSignature,
        *,
        secret: bytes,
    ) -> bool:
        if not isinstance(receipt, ReaderShadowBurnInControlReceipt):
            raise ReaderShadowBurnInError(
                "receipt must be a ReaderShadowBurnInControlReceipt"
            )
        if not isinstance(signature, ReaderShadowBurnInControlSignature):
            raise ReaderShadowBurnInError(
                "signature must be a control signature"
            )
        _secret(secret)
        return _verify_signature(
            value=receipt,
            value_id=receipt.receipt_id,
            signed_id=signature.receipt_id,
            recorded_sha256=signature.receipt_sha256,
            recorded_signature=signature.signature_hex,
            secret=secret,
        )


class ReaderShadowBurnInController:
    """Apply one explicit transition to a signed campaign plan."""

    def apply(
        self,
        *,
        plan: ReaderShadowBurnInPlan,
        plan_signature: ReaderShadowBurnInPlanSignature,
        source: ReaderShadowBurnInControlSource,
        secret: bytes,
        previous_receipt: ReaderShadowBurnInControlReceipt | None = None,
        previous_signature: ReaderShadowBurnInControlSignature | None = None,
    ) -> ReaderShadowBurnInControlReceipt:
        if not ReaderShadowBurnInPlanSigner.verify(
            plan,
            plan_signature,
            secret=secret,
        ):
            raise ReaderShadowBurnInError(
                "shadow burn-in plan signature verification failed"
            )
        if not isinstance(source, ReaderShadowBurnInControlSource):
            raise ReaderShadowBurnInError(
                "source must be a ReaderShadowBurnInControlSource"
            )
        if (previous_receipt is None) != (previous_signature is None):
            raise ReaderShadowBurnInError(
                "previous receipt and signature must be both present or absent"
            )
        issued_at = _utc(source.issued_at_utc, "issued_at_utc")
        campaign_end = _utc(plan.source.planned_end_utc, "planned_end_utc")
        if issued_at >= campaign_end:
            raise ReaderShadowBurnInError(
                "control action must be issued before campaign end"
            )
        if previous_receipt is None:
            state = _initial_state(source)
        else:
            if previous_signature is None:
                raise ReaderShadowBurnInError(
                    "previous signature is required with previous receipt"
                )
            _validate_previous_control(
                plan=plan,
                plan_signature=plan_signature,
                source=source,
                issued_at=issued_at,
                previous_receipt=previous_receipt,
                previous_signature=previous_signature,
                secret=secret,
            )
            state = _next_state(previous_receipt.state, source.action)
        return ReaderShadowBurnInControlReceipt(
            plan_id=plan.plan_id,
            plan_signature_id=plan_signature.signature_id,
            source=source,
            state=state,
            control_allows_shadow=state is ShadowBurnInControlState.ARMED,
        )


class ReaderShadowBurnInEvaluator:
    """Evaluate a signed campaign/control chain at one explicit UTC instant."""

    def evaluate(
        self,
        *,
        plan: ReaderShadowBurnInPlan,
        plan_signature: ReaderShadowBurnInPlanSignature,
        decision: ReaderOperatorDecisionRecord,
        decision_signature: ReaderOperatorDecisionSignature,
        control_receipt: ReaderShadowBurnInControlReceipt,
        control_signature: ReaderShadowBurnInControlSignature,
        secret: bytes,
        as_of_utc: str,
        revocation: ReaderOperatorDecisionRevocation | None = None,
        revocation_signature: ReaderOperatorRevocationSignature | None = None,
    ) -> ReaderShadowBurnInStatusReceipt:
        if not ReaderShadowBurnInPlanSigner.verify(
            plan,
            plan_signature,
            secret=secret,
        ):
            raise ReaderShadowBurnInError(
                "shadow burn-in plan signature verification failed"
            )
        if (
            plan.decision_id != decision.decision_id
            or plan.decision_signature_id != decision_signature.signature_id
        ):
            raise ReaderShadowBurnInError(
                "plan belongs to a different operator decision"
            )
        if (
            control_receipt.plan_id != plan.plan_id
            or control_receipt.plan_signature_id != plan_signature.signature_id
        ):
            raise ReaderShadowBurnInError(
                "control receipt belongs to a different plan"
            )
        if not ReaderShadowBurnInControlSigner.verify(
            control_receipt,
            control_signature,
            secret=secret,
        ):
            raise ReaderShadowBurnInError(
                "shadow burn-in control signature verification failed"
            )
        as_of = _utc(as_of_utc, "as_of_utc")
        if as_of < _utc(control_receipt.issued_at_utc, "issued_at_utc"):
            raise ReaderShadowBurnInError(
                "status cannot be evaluated before latest control action"
            )
        decision_status = ReaderOperatorDecisionEvaluator().evaluate(
            decision=decision,
            decision_signature=decision_signature,
            secret=secret,
            as_of_utc=as_of_utc,
            revocation=revocation,
            revocation_signature=revocation_signature,
        )
        status = _evaluate_status(
            plan=plan,
            control_state=control_receipt.state,
            decision_status=decision_status.status,
            as_of=as_of,
        )
        return ReaderShadowBurnInStatusReceipt(
            plan_id=plan.plan_id,
            plan_signature_id=plan_signature.signature_id,
            control_receipt_id=control_receipt.receipt_id,
            control_signature_id=control_signature.signature_id,
            decision_status_id=decision_status.status_id,
            as_of_utc=as_of_utc,
            status=status,
            shadow_evaluation_authorized=status is ShadowBurnInStatus.READY,
        )


def write_shadow_burn_in_source(
    path: str | Path,
    source: ReaderShadowBurnInSource,
) -> None:
    if not isinstance(source, ReaderShadowBurnInSource):
        raise ReaderShadowBurnInError(
            "source must be a ReaderShadowBurnInSource"
        )
    write_canonical_json(path, source.source_payload())


def write_shadow_burn_in_control_source(
    path: str | Path,
    source: ReaderShadowBurnInControlSource,
) -> None:
    if not isinstance(source, ReaderShadowBurnInControlSource):
        raise ReaderShadowBurnInError(
            "source must be a ReaderShadowBurnInControlSource"
        )
    write_canonical_json(path, source.source_payload())


def load_shadow_burn_in_source(
    path: str | Path,
) -> ReaderShadowBurnInSource:
    payload, raw = _load_object(path, "shadow burn-in source")
    source = _parse_source(payload, require_id=False)
    _require_canonical(raw, source.source_payload(), "shadow burn-in source")
    return source


def load_shadow_burn_in_plan(path: str | Path) -> ReaderShadowBurnInPlan:
    payload, raw = _load_object(path, "shadow burn-in plan")
    _keys(payload, _PLAN_KEYS, "shadow burn-in plan")
    plan = ReaderShadowBurnInPlan(
        source=_parse_source(_mapping(payload["source"], "source"), True),
        decision_id=_text(payload["decision_id"], "decision_id"),
        decision_signature_id=_text(
            payload["decision_signature_id"],
            "decision_signature_id",
        ),
        decision_status_id=_text(
            payload["decision_status_id"],
            "decision_status_id",
        ),
        evidence_id=_text(payload["evidence_id"], "evidence_id"),
        benchmark_verification_id=_text(
            payload["benchmark_verification_id"],
            "benchmark_verification_id",
        ),
        retention_manifest_id=_text(
            payload["retention_manifest_id"],
            "retention_manifest_id",
        ),
        retention_verification_id=_text(
            payload["retention_verification_id"],
            "retention_verification_id",
        ),
        shadow_evaluation_authorized=_bool_field(
            payload,
            "shadow_evaluation_authorized",
        ),
        **_parse_authority(payload),
        schema_version=_text(payload["schema_version"], "schema_version"),
        plan_id=_text(payload["plan_id"], "plan_id"),
    )
    _require_canonical(raw, plan, "shadow burn-in plan")
    return plan


def load_shadow_burn_in_plan_signature(
    path: str | Path,
) -> ReaderShadowBurnInPlanSignature:
    payload, raw = _load_object(path, "shadow burn-in plan signature")
    _keys(payload, _PLAN_SIGNATURE_KEYS, "shadow burn-in plan signature")
    signature = ReaderShadowBurnInPlanSignature(
        plan_id=_text(payload["plan_id"], "plan_id"),
        key_id=_text(payload["key_id"], "key_id"),
        plan_sha256=_text(payload["plan_sha256"], "plan_sha256"),
        signature_hex=_text(payload["signature_hex"], "signature_hex"),
        algorithm=_text(payload["algorithm"], "algorithm"),
        schema_version=_text(payload["schema_version"], "schema_version"),
        signature_id=_text(payload["signature_id"], "signature_id"),
    )
    _require_canonical(raw, signature, "shadow burn-in plan signature")
    return signature


def load_shadow_burn_in_control_source(
    path: str | Path,
) -> ReaderShadowBurnInControlSource:
    payload, raw = _load_object(path, "shadow burn-in control source")
    source = _parse_control_source(payload, require_id=False)
    _require_canonical(
        raw,
        source.source_payload(),
        "shadow burn-in control source",
    )
    return source


def load_shadow_burn_in_control_receipt(
    path: str | Path,
) -> ReaderShadowBurnInControlReceipt:
    payload, raw = _load_object(path, "shadow burn-in control receipt")
    _keys(payload, _CONTROL_RECEIPT_KEYS, "shadow burn-in control receipt")
    receipt = ReaderShadowBurnInControlReceipt(
        plan_id=_text(payload["plan_id"], "plan_id"),
        plan_signature_id=_text(
            payload["plan_signature_id"],
            "plan_signature_id",
        ),
        source=_parse_control_source(
            _mapping(payload["source"], "source"),
            True,
        ),
        state=_enum(ShadowBurnInControlState, payload["state"], "state"),
        control_allows_shadow=_bool_field(payload, "control_allows_shadow"),
        **_parse_authority(payload),
        schema_version=_text(payload["schema_version"], "schema_version"),
        receipt_id=_text(payload["receipt_id"], "receipt_id"),
    )
    _require_canonical(raw, receipt, "shadow burn-in control receipt")
    return receipt


def load_shadow_burn_in_control_signature(
    path: str | Path,
) -> ReaderShadowBurnInControlSignature:
    payload, raw = _load_object(path, "shadow burn-in control signature")
    _keys(
        payload,
        _CONTROL_SIGNATURE_KEYS,
        "shadow burn-in control signature",
    )
    signature = ReaderShadowBurnInControlSignature(
        receipt_id=_text(payload["receipt_id"], "receipt_id"),
        key_id=_text(payload["key_id"], "key_id"),
        receipt_sha256=_text(payload["receipt_sha256"], "receipt_sha256"),
        signature_hex=_text(payload["signature_hex"], "signature_hex"),
        algorithm=_text(payload["algorithm"], "algorithm"),
        schema_version=_text(payload["schema_version"], "schema_version"),
        signature_id=_text(payload["signature_id"], "signature_id"),
    )
    _require_canonical(raw, signature, "shadow burn-in control signature")
    return signature


def load_shadow_burn_in_status(
    path: str | Path,
) -> ReaderShadowBurnInStatusReceipt:
    payload, raw = _load_object(path, "shadow burn-in status")
    _keys(payload, _STATUS_KEYS, "shadow burn-in status")
    status = ReaderShadowBurnInStatusReceipt(
        plan_id=_text(payload["plan_id"], "plan_id"),
        plan_signature_id=_text(
            payload["plan_signature_id"],
            "plan_signature_id",
        ),
        control_receipt_id=_text(
            payload["control_receipt_id"],
            "control_receipt_id",
        ),
        control_signature_id=_text(
            payload["control_signature_id"],
            "control_signature_id",
        ),
        decision_status_id=_text(
            payload["decision_status_id"],
            "decision_status_id",
        ),
        as_of_utc=_text(payload["as_of_utc"], "as_of_utc"),
        status=_enum(ShadowBurnInStatus, payload["status"], "status"),
        shadow_evaluation_authorized=_bool_field(
            payload,
            "shadow_evaluation_authorized",
        ),
        **_parse_authority(payload),
        schema_version=_text(payload["schema_version"], "schema_version"),
        status_id=_text(payload["status_id"], "status_id"),
    )
    _require_canonical(raw, status, "shadow burn-in status")
    return status


def _initial_state(
    source: ReaderShadowBurnInControlSource,
) -> ShadowBurnInControlState:
    if source.previous_receipt_id is not None:
        raise ReaderShadowBurnInError(
            "initial control action cannot reference previous receipt"
        )
    if source.action is ShadowBurnInControlAction.ARM:
        return ShadowBurnInControlState.ARMED
    if source.action is ShadowBurnInControlAction.KILL:
        return ShadowBurnInControlState.KILLED
    raise ReaderShadowBurnInError(
        "initial control action must be arm or kill"
    )


def _validate_previous_control(
    *,
    plan: ReaderShadowBurnInPlan,
    plan_signature: ReaderShadowBurnInPlanSignature,
    source: ReaderShadowBurnInControlSource,
    issued_at: datetime,
    previous_receipt: ReaderShadowBurnInControlReceipt,
    previous_signature: ReaderShadowBurnInControlSignature,
    secret: bytes,
) -> None:
    if not ReaderShadowBurnInControlSigner.verify(
        previous_receipt,
        previous_signature,
        secret=secret,
    ):
        raise ReaderShadowBurnInError(
            "previous control signature verification failed"
        )
    if (
        previous_receipt.plan_id != plan.plan_id
        or previous_receipt.plan_signature_id != plan_signature.signature_id
    ):
        raise ReaderShadowBurnInError(
            "previous control receipt belongs to a different plan"
        )
    if source.previous_receipt_id != previous_receipt.receipt_id:
        raise ReaderShadowBurnInError(
            "control source does not reference exact previous receipt"
        )
    previous_time = _utc(
        previous_receipt.issued_at_utc,
        "previous issued_at_utc",
    )
    if issued_at <= previous_time:
        raise ReaderShadowBurnInError(
            "control actions must use strictly increasing times"
        )


def _next_state(
    previous: ShadowBurnInControlState,
    action: ShadowBurnInControlAction,
) -> ShadowBurnInControlState:
    if previous in {
        ShadowBurnInControlState.STOPPED,
        ShadowBurnInControlState.KILLED,
    }:
        raise ReaderShadowBurnInError(
            "stopped or killed campaign cannot transition"
        )
    if action is ShadowBurnInControlAction.KILL:
        return ShadowBurnInControlState.KILLED
    transitions = {
        (
            ShadowBurnInControlState.ARMED,
            ShadowBurnInControlAction.PAUSE,
        ): ShadowBurnInControlState.PAUSED,
        (
            ShadowBurnInControlState.ARMED,
            ShadowBurnInControlAction.STOP,
        ): ShadowBurnInControlState.STOPPED,
        (
            ShadowBurnInControlState.PAUSED,
            ShadowBurnInControlAction.RESUME,
        ): ShadowBurnInControlState.ARMED,
        (
            ShadowBurnInControlState.PAUSED,
            ShadowBurnInControlAction.STOP,
        ): ShadowBurnInControlState.STOPPED,
    }
    try:
        return transitions[(previous, action)]
    except KeyError as exc:
        raise ReaderShadowBurnInError(
            f"invalid control transition: {previous.value} -> {action.value}"
        ) from exc


def _evaluate_status(
    *,
    plan: ReaderShadowBurnInPlan,
    control_state: ShadowBurnInControlState,
    decision_status: OperatorDecisionStatus,
    as_of: datetime,
) -> ShadowBurnInStatus:
    if decision_status is OperatorDecisionStatus.REVOKED:
        return ShadowBurnInStatus.APPROVAL_REVOKED
    if decision_status is not OperatorDecisionStatus.ACTIVE_SHADOW_APPROVAL:
        return ShadowBurnInStatus.APPROVAL_INACTIVE
    start = _utc(plan.source.planned_start_utc, "planned_start_utc")
    end = _utc(plan.source.planned_end_utc, "planned_end_utc")
    if as_of < start:
        return ShadowBurnInStatus.NOT_YET_VALID
    if as_of >= end:
        return ShadowBurnInStatus.EXPIRED
    return {
        ShadowBurnInControlState.ARMED: ShadowBurnInStatus.READY,
        ShadowBurnInControlState.PAUSED: ShadowBurnInStatus.PAUSED,
        ShadowBurnInControlState.STOPPED: ShadowBurnInStatus.STOPPED,
        ShadowBurnInControlState.KILLED: ShadowBurnInStatus.KILLED,
    }[control_state]


def _verify_signature(
    *,
    value: object,
    value_id: str,
    signed_id: str,
    recorded_sha256: str,
    recorded_signature: str,
    secret: bytes,
) -> bool:
    if signed_id != value_id:
        return False
    payload = canonical_json_bytes(value)
    digest = hashlib.sha256(payload).hexdigest()
    if not hmac.compare_digest(recorded_sha256, digest):
        return False
    expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(recorded_signature, expected)


def _set_or_verify_id(value: object, field: str, namespace: str) -> None:
    identity_method = getattr(value, "identity_payload", None)
    if not callable(identity_method):
        raise ReaderShadowBurnInError(
            "content-addressed value requires identity_payload"
        )
    payload = identity_method(include_id=False)
    expected = stable_reader_core_id(namespace, payload)
    current = getattr(value, field)
    if current:
        if current != expected:
            raise ReaderShadowBurnInError(
                f"{field} does not match content"
            )
    else:
        object.__setattr__(value, field, expected)


def _authority_payload(value: object) -> dict[str, object]:
    return {
        name: getattr(value, name)
        for name in _AUTHORITY_FIELDS
    }


def _validate_no_live_authority(value: object) -> None:
    for name in _AUTHORITY_FIELDS:
        if getattr(value, name) is not False:
            raise ReaderShadowBurnInError(f"{name} must remain false")


def _parse_authority(payload: Mapping[str, object]) -> dict[str, bool]:
    return {name: _bool_field(payload, name) for name in _AUTHORITY_FIELDS}


def _parse_source(
    payload: Mapping[str, object],
    require_id: bool,
) -> ReaderShadowBurnInSource:
    required = set(_SOURCE_KEYS)
    if require_id:
        required.add("source_id")
    _keys(payload, required, "shadow burn-in source")
    return ReaderShadowBurnInSource(
        campaign_name=_text(payload["campaign_name"], "campaign_name"),
        environment_id=_text(payload["environment_id"], "environment_id"),
        harness_digest=_text(payload["harness_digest"], "harness_digest"),
        planned_start_utc=_text(
            payload["planned_start_utc"],
            "planned_start_utc",
        ),
        planned_end_utc=_text(payload["planned_end_utc"], "planned_end_utc"),
        work_item_ids=_text_array(payload["work_item_ids"], "work_item_id"),
        max_attempts_per_work_item=_int_field(
            payload,
            "max_attempts_per_work_item",
        ),
        per_work_item_timeout_ms=_int_field(
            payload,
            "per_work_item_timeout_ms",
        ),
        max_total_wall_time_ms=_int_field(
            payload,
            "max_total_wall_time_ms",
        ),
        max_total_model_tokens=_int_field(
            payload,
            "max_total_model_tokens",
        ),
        max_total_artifact_bytes=_int_field(
            payload,
            "max_total_artifact_bytes",
        ),
        max_consecutive_failures=_int_field(
            payload,
            "max_consecutive_failures",
        ),
        condition_codes=_text_array(
            payload["condition_codes"],
            "condition_code",
        ),
        schema_version=_text(payload["schema_version"], "schema_version"),
        source_id=(
            _text(payload["source_id"], "source_id") if require_id else ""
        ),
    )


def _parse_control_source(
    payload: Mapping[str, object],
    require_id: bool,
) -> ReaderShadowBurnInControlSource:
    required = set(_CONTROL_SOURCE_KEYS)
    if require_id:
        required.add("source_id")
    _keys(payload, required, "shadow burn-in control source")
    return ReaderShadowBurnInControlSource(
        operator_id=_text(payload["operator_id"], "operator_id"),
        action=_enum(
            ShadowBurnInControlAction,
            payload["action"],
            "action",
        ),
        issued_at_utc=_text(payload["issued_at_utc"], "issued_at_utc"),
        reason_codes=_text_array(payload["reason_codes"], "reason_code"),
        previous_receipt_id=_optional_text(
            payload["previous_receipt_id"],
            "previous_receipt_id",
        ),
        schema_version=_text(payload["schema_version"], "schema_version"),
        source_id=(
            _text(payload["source_id"], "source_id") if require_id else ""
        ),
    )


def _load_object(
    path: str | Path,
    label: str,
) -> tuple[dict[str, object], bytes]:
    source = Path(path)
    try:
        raw = source.read_bytes()
        value: Any = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_constant,
        )
    except ReaderShadowBurnInError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReaderShadowBurnInError(
            f"cannot load {label} from {source}: {exc}"
        ) from exc
    payload = dict(_mapping(value, label))
    _require_canonical(raw, payload, label)
    return payload, raw


def _require_canonical(raw: bytes, value: object, label: str) -> None:
    if raw != canonical_json_bytes(value) + b"\n":
        raise ReaderShadowBurnInError(
            f"{label} must use canonical JSON encoding"
        )


def _reject_duplicate_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ReaderShadowBurnInError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ReaderShadowBurnInError(
        f"non-finite JSON number is not allowed: {value}"
    )


def _keys(
    payload: Mapping[str, object],
    required: set[str],
    label: str,
) -> None:
    actual = set(payload)
    missing = sorted(required - actual)
    unknown = sorted(actual - required)
    if missing or unknown:
        raise ReaderShadowBurnInError(
            f"{label} keys mismatch; missing={missing}, unknown={unknown}"
        )


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) for key in value
    ):
        raise ReaderShadowBurnInError(
            f"{field_name} must be a JSON object with string keys"
        )
    return cast(Mapping[str, object], value)


def _array(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ReaderShadowBurnInError(
            f"{field_name} must be a JSON array"
        )
    return cast(list[object], value)


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderShadowBurnInError(
            f"{field_name} must be non-empty text"
        )
    return value


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _text(value, field_name)


def _bool_field(payload: Mapping[str, object], name: str) -> bool:
    value = payload[name]
    if not isinstance(value, bool):
        raise ReaderShadowBurnInError(f"{name} must be a boolean")
    return value


def _int_field(payload: Mapping[str, object], name: str) -> int:
    value = payload[name]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReaderShadowBurnInError(f"{name} must be an integer")
    return value


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ReaderShadowBurnInError(
            f"{field_name} must be an integer greater than zero"
        )
    return value


def _text_array(value: object, field_name: str) -> tuple[str, ...]:
    return tuple(_text(item, field_name) for item in _array(value, field_name))


def _canonical_texts(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    items = tuple(values)
    for item in items:
        _text(item, field_name)
    if len(set(items)) != len(items):
        raise ReaderShadowBurnInError(
            f"{field_name} values must be unique"
        )
    if items != tuple(sorted(items)):
        raise ReaderShadowBurnInError(
            f"{field_name} values must use canonical ordering"
        )
    return items


EnumT = TypeVar("EnumT", bound=Enum)


def _enum(
    enum_type: type[EnumT],
    value: object,
    field_name: str,
) -> EnumT:
    text = _text(value, field_name)
    try:
        return enum_type(text)
    except ValueError as exc:
        raise ReaderShadowBurnInError(
            f"unsupported {field_name}: {text}"
        ) from exc


def _utc(value: object, field_name: str) -> datetime:
    text = _text(value, field_name)
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise ReaderShadowBurnInError(
            f"{field_name} must use canonical UTC format "
            "YYYY-MM-DDTHH:MM:SSZ"
        ) from exc


def _sha256(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    if len(text) != 64 or text.lower() != text:
        raise ReaderShadowBurnInError(
            f"{field_name} must be lowercase SHA-256 hex"
        )
    try:
        int(text, 16)
    except ValueError as exc:
        raise ReaderShadowBurnInError(
            f"{field_name} must be lowercase SHA-256 hex"
        ) from exc
    return text


def _secret(value: object) -> bytes:
    if not isinstance(value, bytes) or len(value) < 32:
        raise ReaderShadowBurnInError(
            "HMAC secret must be bytes and at least 32 bytes long"
        )
    return value


_AUTHORITY_FIELDS = (
    "production_traffic_authorized",
    "user_visible_output_authorized",
    "background_scheduling_authorized",
    "query_path_wiring_authorized",
    "canon_write_authorized",
    "memory_write_authorized",
    "graph_write_authorized",
    "tool_execution_authorized",
)
_SOURCE_KEYS = {
    "schema_version",
    "campaign_name",
    "environment_id",
    "harness_digest",
    "planned_start_utc",
    "planned_end_utc",
    "work_item_ids",
    "max_attempts_per_work_item",
    "per_work_item_timeout_ms",
    "max_total_wall_time_ms",
    "max_total_model_tokens",
    "max_total_artifact_bytes",
    "max_consecutive_failures",
    "condition_codes",
}
_PLAN_KEYS = {
    "schema_version",
    "source",
    "decision_id",
    "decision_signature_id",
    "decision_status_id",
    "evidence_id",
    "benchmark_verification_id",
    "retention_manifest_id",
    "retention_verification_id",
    "shadow_evaluation_authorized",
    *_AUTHORITY_FIELDS,
    "plan_id",
}
_PLAN_SIGNATURE_KEYS = {
    "schema_version",
    "algorithm",
    "plan_id",
    "key_id",
    "plan_sha256",
    "signature_hex",
    "signature_id",
}
_CONTROL_SOURCE_KEYS = {
    "schema_version",
    "operator_id",
    "action",
    "issued_at_utc",
    "reason_codes",
    "previous_receipt_id",
}
_CONTROL_RECEIPT_KEYS = {
    "schema_version",
    "plan_id",
    "plan_signature_id",
    "source",
    "state",
    "control_allows_shadow",
    *_AUTHORITY_FIELDS,
    "receipt_id",
}
_CONTROL_SIGNATURE_KEYS = {
    "schema_version",
    "algorithm",
    "receipt_id",
    "key_id",
    "receipt_sha256",
    "signature_hex",
    "signature_id",
}
_STATUS_KEYS = {
    "schema_version",
    "plan_id",
    "plan_signature_id",
    "control_receipt_id",
    "control_signature_id",
    "decision_status_id",
    "as_of_utc",
    "status",
    "shadow_evaluation_authorized",
    *_AUTHORITY_FIELDS,
    "status_id",
}


__all__ = [
    "READER_SHADOW_BURN_IN_CONTROL_RECEIPT_SCHEMA_VERSION",
    "READER_SHADOW_BURN_IN_CONTROL_SIGNATURE_SCHEMA_VERSION",
    "READER_SHADOW_BURN_IN_CONTROL_SOURCE_SCHEMA_VERSION",
    "READER_SHADOW_BURN_IN_PLAN_SCHEMA_VERSION",
    "READER_SHADOW_BURN_IN_PLAN_SIGNATURE_SCHEMA_VERSION",
    "READER_SHADOW_BURN_IN_SIGNATURE_ALGORITHM",
    "READER_SHADOW_BURN_IN_SOURCE_SCHEMA_VERSION",
    "READER_SHADOW_BURN_IN_STATUS_SCHEMA_VERSION",
    "ReaderShadowBurnInControlReceipt",
    "ReaderShadowBurnInControlSignature",
    "ReaderShadowBurnInControlSigner",
    "ReaderShadowBurnInControlSource",
    "ReaderShadowBurnInController",
    "ReaderShadowBurnInError",
    "ReaderShadowBurnInEvaluator",
    "ReaderShadowBurnInPlan",
    "ReaderShadowBurnInPlanBuilder",
    "ReaderShadowBurnInPlanSignature",
    "ReaderShadowBurnInPlanSigner",
    "ReaderShadowBurnInSource",
    "ReaderShadowBurnInStatusReceipt",
    "ShadowBurnInControlAction",
    "ShadowBurnInControlState",
    "ShadowBurnInStatus",
    "load_shadow_burn_in_control_receipt",
    "load_shadow_burn_in_control_signature",
    "load_shadow_burn_in_control_source",
    "load_shadow_burn_in_plan",
    "load_shadow_burn_in_plan_signature",
    "load_shadow_burn_in_source",
    "load_shadow_burn_in_status",
    "write_shadow_burn_in_control_source",
    "write_shadow_burn_in_source",
]
