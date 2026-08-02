"""Signed shadow burn-in campaign control contracts for PR-RDR-26.

The module plans and controls only an isolated Reader Core shadow campaign.
It consumes an active PR-RDR-25 shadow-only operator decision, applies explicit
budgets and work-item references, and records signed arm/pause/resume/stop/kill
state. It does not execute a pipeline, connect to /query, schedule background
work, emit user-visible output, or grant persistent authority.
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
from typing import Any, cast

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
        work_items = _unique_sorted_text(self.work_item_ids, "work_item_id")
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
        conditions = _unique_sorted_text(self.condition_codes, "condition_code")
        if not conditions:
            raise ReaderShadowBurnInError(
                "shadow burn-in requires explicit condition codes"
            )
        object.__setattr__(self, "work_item_ids", work_items)
        object.__setattr__(self, "condition_codes", conditions)
        if self.schema_version != READER_SHADOW_BURN_IN_SOURCE_SCHEMA_VERSION:
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in source schema"
            )
        expected = stable_reader_core_id(
            "reader-shadow-burn-in-source",
            self.identity_payload(include_id=False),
        )
        if self.source_id:
            if self.source_id != expected:
                raise ReaderShadowBurnInError(
                    "source_id does not match shadow burn-in source content"
                )
        else:
            object.__setattr__(self, "source_id", expected)

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
        _forbidden_authority(
            production=self.production_traffic_authorized,
            user_visible=self.user_visible_output_authorized,
            background=self.background_scheduling_authorized,
            query=self.query_path_wiring_authorized,
            canon=self.canon_write_authorized,
            memory=self.memory_write_authorized,
            graph=self.graph_write_authorized,
            tools=self.tool_execution_authorized,
        )
        if self.schema_version != READER_SHADOW_BURN_IN_PLAN_SCHEMA_VERSION:
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in plan schema"
            )
        expected = stable_reader_core_id(
            "reader-shadow-burn-in-plan",
            self.identity_payload(include_id=False),
        )
        if self.plan_id:
            if self.plan_id != expected:
                raise ReaderShadowBurnInError(
                    "plan_id does not match shadow burn-in plan content"
                )
        else:
            object.__setattr__(self, "plan_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
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
            "production_traffic_authorized": self.production_traffic_authorized,
            "user_visible_output_authorized": (
                self.user_visible_output_authorized
            ),
            "background_scheduling_authorized": (
                self.background_scheduling_authorized
            ),
            "query_path_wiring_authorized": (
                self.query_path_wiring_authorized
            ),
            "canon_write_authorized": self.canon_write_authorized,
            "memory_write_authorized": self.memory_write_authorized,
            "graph_write_authorized": self.graph_write_authorized,
            "tool_execution_authorized": self.tool_execution_authorized,
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
        expected = stable_reader_core_id(
            "reader-shadow-burn-in-plan-signature",
            self.identity_payload(include_id=False),
        )
        if self.signature_id:
            if self.signature_id != expected:
                raise ReaderShadowBurnInError(
                    "signature_id does not match plan signature content"
                )
        else:
            object.__setattr__(self, "signature_id", expected)

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
        reasons = _unique_sorted_text(self.reason_codes, "reason_code")
        if not reasons:
            raise ReaderShadowBurnInError(
                "control actions require explicit reason codes"
            )
        if self.previous_receipt_id is not None:
            _text(self.previous_receipt_id, "previous_receipt_id")
        if (
            self.action
            in {
                ShadowBurnInControlAction.PAUSE,
                ShadowBurnInControlAction.RESUME,
                ShadowBurnInControlAction.STOP,
            }
            and self.previous_receipt_id is None
        ):
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
        object.__setattr__(self, "reason_codes", reasons)
        if (
            self.schema_version
            != READER_SHADOW_BURN_IN_CONTROL_SOURCE_SCHEMA_VERSION
        ):
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in control source schema"
            )
        expected = stable_reader_core_id(
            "reader-shadow-burn-in-control-source",
            self.identity_payload(include_id=False),
        )
        if self.source_id:
            if self.source_id != expected:
                raise ReaderShadowBurnInError(
                    "source_id does not match control source content"
                )
        else:
            object.__setattr__(self, "source_id", expected)

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
        expected_allows = self.state is ShadowBurnInControlState.ARMED
        if self.control_allows_shadow is not expected_allows:
            raise ReaderShadowBurnInError(
                "control_allows_shadow must exactly match armed state"
            )
        _forbidden_authority(
            production=self.production_traffic_authorized,
            user_visible=self.user_visible_output_authorized,
            background=self.background_scheduling_authorized,
            query=self.query_path_wiring_authorized,
            canon=self.canon_write_authorized,
            memory=self.memory_write_authorized,
            graph=self.graph_write_authorized,
            tools=self.tool_execution_authorized,
        )
        if (
            self.schema_version
            != READER_SHADOW_BURN_IN_CONTROL_RECEIPT_SCHEMA_VERSION
        ):
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in control receipt schema"
            )
        expected = stable_reader_core_id(
            "reader-shadow-burn-in-control-receipt",
            self.identity_payload(include_id=False),
        )
        if self.receipt_id:
            if self.receipt_id != expected:
                raise ReaderShadowBurnInError(
                    "receipt_id does not match control receipt content"
                )
        else:
            object.__setattr__(self, "receipt_id", expected)

    @property
    def issued_at_utc(self) -> str:
        return self.source.issued_at_utc

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "plan_signature_id": self.plan_signature_id,
            "source": self.source.identity_payload(),
            "state": self.state.value,
            "control_allows_shadow": self.control_allows_shadow,
            "production_traffic_authorized": self.production_traffic_authorized,
            "user_visible_output_authorized": (
                self.user_visible_output_authorized
            ),
            "background_scheduling_authorized": (
                self.background_scheduling_authorized
            ),
            "query_path_wiring_authorized": (
                self.query_path_wiring_authorized
            ),
            "canon_write_authorized": self.canon_write_authorized,
            "memory_write_authorized": self.memory_write_authorized,
            "graph_write_authorized": self.graph_write_authorized,
            "tool_execution_authorized": self.tool_execution_authorized,
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
        expected = stable_reader_core_id(
            "reader-shadow-burn-in-control-signature",
            self.identity_payload(include_id=False),
        )
        if self.signature_id:
            if self.signature_id != expected:
                raise ReaderShadowBurnInError(
                    "signature_id does not match control signature content"
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
        expected_shadow = self.status is ShadowBurnInStatus.READY
        if self.shadow_evaluation_authorized is not expected_shadow:
            raise ReaderShadowBurnInError(
                "shadow authorization must exactly match ready status"
            )
        _forbidden_authority(
            production=self.production_traffic_authorized,
            user_visible=self.user_visible_output_authorized,
            background=self.background_scheduling_authorized,
            query=self.query_path_wiring_authorized,
            canon=self.canon_write_authorized,
            memory=self.memory_write_authorized,
            graph=self.graph_write_authorized,
            tools=self.tool_execution_authorized,
        )
        if self.schema_version != READER_SHADOW_BURN_IN_STATUS_SCHEMA_VERSION:
            raise ReaderShadowBurnInError(
                "unsupported shadow burn-in status schema"
            )
        expected = stable_reader_core_id(
            "reader-shadow-burn-in-status",
            self.identity_payload(include_id=False),
        )
        if self.status_id:
            if self.status_id != expected:
                raise ReaderShadowBurnInError(
                    "status_id does not match shadow burn-in status content"
                )
        else:
            object.__setattr__(self, "status_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "plan_signature_id": self.plan_signature_id,
            "control_receipt_id": self.control_receipt_id,
            "control_signature_id": self.control_signature_id,
            "decision_status_id": self.decision_status_id,
            "as_of_utc": self.as_of_utc,
            "status": self.status.value,
            "shadow_evaluation_authorized": (
                self.shadow_evaluation_authorized
            ),
            "production_traffic_authorized": self.production_traffic_authorized,
            "user_visible_output_authorized": (
                self.user_visible_output_authorized
            ),
            "background_scheduling_authorized": (
                self.background_scheduling_authorized
            ),
            "query_path_wiring_authorized": (
                self.query_path_wiring_authorized
            ),
            "canon_write_authorized": self.canon_write_authorized,
            "memory_write_authorized": self.memory_write_authorized,
            "graph_write_authorized": self.graph_write_authorized,
            "tool_execution_authorized": self.tool_execution_authorized,
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
        if decision_status.status is not OperatorDecisionStatus.ACTIVE_SHADOW_APPROVAL:
            raise ReaderShadowBurnInError(
                "shadow burn-in start requires active shadow approval"
            )
        start = _utc(source.planned_start_utc, "planned_start_utc")
        end = _utc(source.planned_end_utc, "planned_end_utc")
        decision_start = _utc(
            decision.source.valid_from_utc,
            "decision.valid_from_utc",
        )
        decision_end = _utc(
            decision.source.valid_until_utc,
            "decision.valid_until_utc",
        )
        if start < decision_start or end > decision_end:
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
        if signature.plan_id != plan.plan_id:
            return False
        payload = canonical_json_bytes(plan)
        digest = hashlib.sha256(payload).hexdigest()
        if not hmac.compare_digest(signature.plan_sha256, digest):
            return False
        expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature.signature_hex, expected)


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
        if signature.receipt_id != receipt.receipt_id:
            return False
        payload = canonical_json_bytes(receipt)
        digest = hashlib.sha256(payload).hexdigest()
        if not hmac.compare_digest(signature.receipt_sha256, digest):
            return False
        expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature.signature_hex, expected)


class ReaderShadowBurnInController:
    """Apply one explicit signed-chain control transition."""

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
        issued = _utc(source.issued_at_utc, "issued_at_utc")
        campaign_end = _utc(plan.source.planned_end_utc, "planned_end_utc")
        if issued >= campaign_end:
            raise ReaderShadowBurnInError(
                "control action must be issued before campaign end"
            )
        if previous_receipt is None:
            if source.previous_receipt_id is not None:
                raise ReaderShadowBurnInError(
                    "initial control action cannot reference previous receipt"
                )
            if source.action is ShadowBurnInControlAction.ARM:
                state = ShadowBurnInControlState.ARMED
            elif source.action is ShadowBurnInControlAction.KILL:
                state = ShadowBurnInControlState.KILLED
            else:
                raise ReaderShadowBurnInError(
                    "initial control action must be arm or kill"
                )
        else:
            assert previous_signature is not None
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
                or previous_receipt.plan_signature_id
                != plan_signature.signature_id
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
            if issued <= previous_time:
                raise ReaderShadowBurnInError(
                    "control actions must use strictly increasing times"
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
        control_time = _utc(control_receipt.issued_at_utc, "issued_at_utc")
        if as_of < control_time:
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
        if decision_status.status is OperatorDecisionStatus.REVOKED:
            status = ShadowBurnInStatus.APPROVAL_REVOKED
        elif (
            decision_status.status
            is not OperatorDecisionStatus.ACTIVE_SHADOW_APPROVAL
        ):
            status = ShadowBurnInStatus.APPROVAL_INACTIVE
        else:
            start = _utc(plan.source.planned_start_utc, "planned_start_utc")
            end = _utc(plan.source.planned_end_utc, "planned_end_utc")
            if as_of < start:
                status = ShadowBurnInStatus.NOT_YET_VALID
            elif as_of >= end:
                status = ShadowBurnInStatus.EXPIRED
            else:
                status = _status_from_control(control_receipt.state)
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


def load_shadow_burn_in_source(
    path: str | Path,
) -> ReaderShadowBurnInSource:
    payload, raw = _load_object(path, "shadow burn-in source")
    source = _parse_source(payload, require_id=False)
    if raw != canonical_json_bytes(source.source_payload()) + b"\n":
        raise ReaderShadowBurnInError(
            "shadow burn-in source is not canonical"
        )
    return source


def load_shadow_burn_in_plan(path: str | Path) -> ReaderShadowBurnInPlan:
    payload, raw = _load_object(path, "shadow burn-in plan")
    _keys(
        payload,
        required={
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
            "production_traffic_authorized",
            "user_visible_output_authorized",
            "background_scheduling_authorized",
            "query_path_wiring_authorized",
            "canon_write_authorized",
            "memory_write_authorized",
            "graph_write_authorized",
            "tool_execution_authorized",
            "plan_id",
        },
        field_name="shadow burn-in plan",
    )
    plan = ReaderShadowBurnInPlan(
        source=_parse_source(
            _mapping(payload["source"], "source"),
            require_id=True,
        ),
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
        shadow_evaluation_authorized=_bool(
            payload["shadow_evaluation_authorized"],
            "shadow_evaluation_authorized",
        ),
        production_traffic_authorized=_bool(
            payload["production_traffic_authorized"],
            "production_traffic_authorized",
        ),
        user_visible_output_authorized=_bool(
            payload["user_visible_output_authorized"],
            "user_visible_output_authorized",
        ),
        background_scheduling_authorized=_bool(
            payload["background_scheduling_authorized"],
            "background_scheduling_authorized",
        ),
        query_path_wiring_authorized=_bool(
            payload["query_path_wiring_authorized"],
            "query_path_wiring_authorized",
        ),
        canon_write_authorized=_bool(
            payload["canon_write_authorized"],
            "canon_write_authorized",
        ),
        memory_write_authorized=_bool(
            payload["memory_write_authorized"],
            "memory_write_authorized",
        ),
        graph_write_authorized=_bool(
            payload["graph_write_authorized"],
            "graph_write_authorized",
        ),
        tool_execution_authorized=_bool(
            payload["tool_execution_authorized"],
            "tool_execution_authorized",
        ),
        schema_version=_text(payload["schema_version"], "schema_version"),
        plan_id=_text(payload["plan_id"], "plan_id"),
    )
    if raw != canonical_json_bytes(plan) + b"\n":
        raise ReaderShadowBurnInError("shadow burn-in plan is not canonical")
    return plan


def load_shadow_burn_in_plan_signature(
    path: str | Path,
) -> ReaderShadowBurnInPlanSignature:
    payload, raw = _load_object(path, "shadow burn-in plan signature")
    _keys(
        payload,
        required={
            "schema_version",
            "algorithm",
            "plan_id",
            "key_id",
            "plan_sha256",
            "signature_hex",
            "signature_id",
        },
        field_name="shadow burn-in plan signature",
    )
    signature = ReaderShadowBurnInPlanSignature(
        plan_id=_text(payload["plan_id"], "plan_id"),
        key_id=_text(payload["key_id"], "key_id"),
        plan_sha256=_text(payload["plan_sha256"], "plan_sha256"),
        signature_hex=_text(payload["signature_hex"], "signature_hex"),
        algorithm=_text(payload["algorithm"], "algorithm"),
        schema_version=_text(payload["schema_version"], "schema_version"),
        signature_id=_text(payload["signature_id"], "signature_id"),
    )
    if raw != canonical_json_bytes(signature) + b"\n":
        raise ReaderShadowBurnInError(
            "shadow burn-in plan signature is not canonical"
        )
    return signature


def write_shadow_burn_in_control_source(
    path: str | Path,
    source: ReaderShadowBurnInControlSource,
) -> None:
    if not isinstance(source, ReaderShadowBurnInControlSource):
        raise ReaderShadowBurnInError(
            "source must be a ReaderShadowBurnInControlSource"
        )
    write_canonical_json(path, source.source_payload())


def load_shadow_burn_in_control_source(
    path: str | Path,
) -> ReaderShadowBurnInControlSource:
    payload, raw = _load_object(path, "shadow burn-in control source")
    source = _parse_control_source(payload, require_id=False)
    if raw != canonical_json_bytes(source.source_payload()) + b"\n":
        raise ReaderShadowBurnInError(
            "shadow burn-in control source is not canonical"
        )
    return source


def load_shadow_burn_in_control_receipt(
    path: str | Path,
) -> ReaderShadowBurnInControlReceipt:
    payload, raw = _load_object(path, "shadow burn-in control receipt")
    _keys(
        payload,
        required={
            "schema_version",
            "plan_id",
            "plan_signature_id",
            "source",
            "state",
            "control_allows_shadow",
            "production_traffic_authorized",
            "user_visible_output_authorized",
            "background_scheduling_authorized",
            "query_path_wiring_authorized",
            "canon_write_authorized",
            "memory_write_authorized",
            "graph_write_authorized",
            "tool_execution_authorized",
            "receipt_id",
        },
        field_name="shadow burn-in control receipt",
    )
    receipt = ReaderShadowBurnInControlReceipt(
        plan_id=_text(payload["plan_id"], "plan_id"),
        plan_signature_id=_text(
            payload["plan_signature_id"],
            "plan_signature_id",
        ),
        source=_parse_control_source(
            _mapping(payload["source"], "source"),
            require_id=True,
        ),
        state=_enum(
            ShadowBurnInControlState,
            payload["state"],
            "state",
        ),
        control_allows_shadow=_bool(
            payload["control_allows_shadow"],
            "control_allows_shadow",
        ),
        production_traffic_authorized=_bool(
            payload["production_traffic_authorized"],
            "production_traffic_authorized",
        ),
        user_visible_output_authorized=_bool(
            payload["user_visible_output_authorized"],
            "user_visible_output_authorized",
        ),
        background_scheduling_authorized=_bool(
            payload["background_scheduling_authorized"],
            "background_scheduling_authorized",
        ),
        query_path_wiring_authorized=_bool(
            payload["query_path_wiring_authorized"],
            "query_path_wiring_authorized",
        ),
        canon_write_authorized=_bool(
            payload["canon_write_authorized"],
            "canon_write_authorized",
        ),
        memory_write_authorized=_bool(
            payload["memory_write_authorized"],
            "memory_write_authorized",
        ),
        graph_write_authorized=_bool(
            payload["graph_write_authorized"],
            "graph_write_authorized",
        ),
        tool_execution_authorized=_bool(
            payload["tool_execution_authorized"],
            "tool_execution_authorized",
        ),
        schema_version=_text(payload["schema_version"], "schema_version"),
        receipt_id=_text(payload["receipt_id"], "receipt_id"),
    )
    if raw != canonical_json_bytes(receipt) + b"\n":
        raise ReaderShadowBurnInError(
            "shadow burn-in control receipt is not canonical"
        )
    return receipt


def load_shadow_burn_in_control_signature(
    path: str | Path,
) -> ReaderShadowBurnInControlSignature:
    payload, raw = _load_object(path, "shadow burn-in control signature")
    _keys(
        payload,
        required={
            "schema_version",
            "algorithm",
            "receipt_id",
            "key_id",
            "receipt_sha256",
            "signature_hex",
            "signature_id",
        },
        field_name="shadow burn-in control signature",
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
    if raw != canonical_json_bytes(signature) + b"\n":
        raise ReaderShadowBurnInError(
            "shadow burn-in control signature is not canonical"
        )
    return signature


def load_shadow_burn_in_status(
    path: str | Path,
) -> ReaderShadowBurnInStatusReceipt:
    payload, raw = _load_object(path, "shadow burn-in status")
    _keys(
        payload,
        required={
            "schema_version",
            "plan_id",
            "plan_signature_id",
            "control_receipt_id",
            "control_signature_id",
            "decision_status_id",
            "as_of_utc",
            "status",
            "shadow_evaluation_authorized",
            "production_traffic_authorized",
            "user_visible_output_authorized",
            "background_scheduling_authorized",
            "query_path_wiring_authorized",
            "canon_write_authorized",
            "memory_write_authorized",
            "graph_write_authorized",
            "tool_execution_authorized",
            "status_id",
        },
        field_name="shadow burn-in status",
    )
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
        shadow_evaluation_authorized=_bool(
            payload["shadow_evaluation_authorized"],
            "shadow_evaluation_authorized",
        ),
        production_traffic_authorized=_bool(
            payload["production_traffic_authorized"],
            "production_traffic_authorized",
        ),
        user_visible_output_authorized=_bool(
            payload["user_visible_output_authorized"],
            "user_visible_output_authorized",
        ),
        background_scheduling_authorized=_bool(
            payload["background_scheduling_authorized"],
            "background_scheduling_authorized",
        ),
        query_path_wiring_authorized=_bool(
            payload["query_path_wiring_authorized"],
            "query_path_wiring_authorized",
        ),
        canon_write_authorized=_bool(
            payload["canon_write_authorized"],
            "canon_write_authorized",
        ),
        memory_write_authorized=_bool(
            payload["memory_write_authorized"],
            "memory_write_authorized",
        ),
        graph_write_authorized=_bool(
            payload["graph_write_authorized"],
            "graph_write_authorized",
        ),
        tool_execution_authorized=_bool(
            payload["tool_execution_authorized"],
            "tool_execution_authorized",
        ),
        schema_version=_text(payload["schema_version"], "schema_version"),
        status_id=_text(payload["status_id"], "status_id"),
    )
    if raw != canonical_json_bytes(status) + b"\n":
        raise ReaderShadowBurnInError(
            "shadow burn-in status is not canonical"
        )
    return status


def _parse_source(
    payload: Mapping[str, object],
    *,
    require_id: bool,
) -> ReaderShadowBurnInSource:
    required = {
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
    if require_id:
        required.add("source_id")
    _keys(payload, required=required, field_name="shadow burn-in source")
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
        max_attempts_per_work_item=_int(
            payload["max_attempts_per_work_item"],
            "max_attempts_per_work_item",
        ),
        per_work_item_timeout_ms=_int(
            payload["per_work_item_timeout_ms"],
            "per_work_item_timeout_ms",
        ),
        max_total_wall_time_ms=_int(
            payload["max_total_wall_time_ms"],
            "max_total_wall_time_ms",
        ),
        max_total_model_tokens=_int(
            payload["max_total_model_tokens"],
            "max_total_model_tokens",
        ),
        max_total_artifact_bytes=_int(
            payload["max_total_artifact_bytes"],
            "max_total_artifact_bytes",
        ),
        max_consecutive_failures=_int(
            payload["max_consecutive_failures"],
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
    *,
    require_id: bool,
) -> ReaderShadowBurnInControlSource:
    required = {
        "schema_version",
        "operator_id",
        "action",
        "issued_at_utc",
        "reason_codes",
        "previous_receipt_id",
    }
    if require_id:
        required.add("source_id")
    _keys(payload, required=required, field_name="shadow burn-in control source")
    previous = payload["previous_receipt_id"]
    if previous is not None:
        previous = _text(previous, "previous_receipt_id")
    return ReaderShadowBurnInControlSource(
        operator_id=_text(payload["operator_id"], "operator_id"),
        action=_enum(
            ShadowBurnInControlAction,
            payload["action"],
            "action",
        ),
        issued_at_utc=_text(payload["issued_at_utc"], "issued_at_utc"),
        reason_codes=_text_array(payload["reason_codes"], "reason_code"),
        previous_receipt_id=cast(str | None, previous),
        schema_version=_text(payload["schema_version"], "schema_version"),
        source_id=(
            _text(payload["source_id"], "source_id") if require_id else ""
        ),
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


def _status_from_control(
    state: ShadowBurnInControlState,
) -> ShadowBurnInStatus:
    return {
        ShadowBurnInControlState.ARMED: ShadowBurnInStatus.READY,
        ShadowBurnInControlState.PAUSED: ShadowBurnInStatus.PAUSED,
        ShadowBurnInControlState.STOPPED: ShadowBurnInStatus.STOPPED,
        ShadowBurnInControlState.KILLED: ShadowBurnInStatus.KILLED,
    }[state]


def _load_object(
    path: str | Path,
    field_name: str,
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
            f"cannot load {field_name} from {source}: {exc}"
        ) from exc
    payload = dict(_mapping(value, field_name))
    if raw != canonical_json_bytes(payload) + b"\n":
        raise ReaderShadowBurnInError(
            f"{field_name} must use canonical JSON encoding"
        )
    return payload, raw


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
    *,
    required: set[str],
    field_name: str,
) -> None:
    actual = set(payload)
    missing = sorted(required - actual)
    unknown = sorted(actual - required)
    if missing or unknown:
        raise ReaderShadowBurnInError(
            f"{field_name} keys mismatch; missing={missing}, unknown={unknown}"
        )


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) for key in value
    ):
        raise ReaderShadowBurnInError(
            f"{field_name} must be a JSON object with string keys"
        )
    return cast(Mapping[str, object], value)


def _list(value: object, field_name: str) -> list[object]:
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


def _bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ReaderShadowBurnInError(
            f"{field_name} must be a boolean"
        )
    return value


def _int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReaderShadowBurnInError(
            f"{field_name} must be an integer"
        )
    return value


def _positive_int(value: object, field_name: str) -> int:
    number = _int(value, field_name)
    if number <= 0:
        raise ReaderShadowBurnInError(
            f"{field_name} must be greater than zero"
        )
    return number


def _text_array(value: object, field_name: str) -> tuple[str, ...]:
    return tuple(_text(item, field_name) for item in _list(value, field_name))


def _unique_sorted_text(
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
    ordered = tuple(sorted(items))
    if items != ordered:
        raise ReaderShadowBurnInError(
            f"{field_name} values must use canonical ordering"
        )
    return items


def _enum(enum_type: type[Any], value: object, field_name: str) -> Any:
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


def _forbidden_authority(
    *,
    production: object,
    user_visible: object,
    background: object,
    query: object,
    canon: object,
    memory: object,
    graph: object,
    tools: object,
) -> None:
    for value, name in (
        (production, "production_traffic_authorized"),
        (user_visible, "user_visible_output_authorized"),
        (background, "background_scheduling_authorized"),
        (query, "query_path_wiring_authorized"),
        (canon, "canon_write_authorized"),
        (memory, "memory_write_authorized"),
        (graph, "graph_write_authorized"),
        (tools, "tool_execution_authorized"),
    ):
        if value is not False:
            raise ReaderShadowBurnInError(f"{name} must remain false")


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
