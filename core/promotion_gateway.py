"""Typed promotion ownership boundary over the existing TruthGate + CAS path.

The first increment is deliberately narrow:

- it does not replace ``SQLiteGraphStore.validate_and_promote``;
- it does not add a feature flag, scheduler, retry loop, network call, or new ESM path;
- it produces deterministic, content-minimized receipts for later replay/outbox work.

A caller reaches Canon only through the store's already-hardened
``validate_and_promote`` implementation. This module validates the returned
contract and records whether the call committed, was an idempotent replay, or
was rejected.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Protocol

from core.truth_gate import CognitiveMode, TruthGateVerdict

PROMOTION_POLICY_VERSION = "promotion-gateway-v1"
_ALLOWED_TARGET = "Validated"
_ALLOWED_PASSED_REASONS = frozenset({"passed", "already_validated"})
_ACTOR_CODE = re.compile(r"^[a-z0-9_.:-]{1,64}$")
_TRUTH_DECIDER = "truth_gate"


class PromotionContractError(RuntimeError):
    """The underlying promotion authority returned an invalid result."""


class PromotionStore(Protocol):
    """Minimal authority required by :class:`PromotionGateway`."""

    def validate_and_promote(
        self,
        fact_id: str,
        by: str = "truth_gate",
        mode: Any = None,
    ) -> TruthGateVerdict: ...


@dataclass(frozen=True, slots=True)
class PromotionRequest:
    """One explicit request for the only v1 target: ``Validated``."""

    fact_id: str
    requested_by: str
    mode: CognitiveMode = CognitiveMode.BALANCED
    target_state: str = _ALLOWED_TARGET

    def __post_init__(self) -> None:
        if not isinstance(self.fact_id, str) or not self.fact_id.strip():
            raise ValueError("PromotionRequest.fact_id must be a non-empty string")
        if len(self.fact_id) > 256 or any(
            ord(ch) < 32 or ord(ch) == 127 for ch in self.fact_id
        ):
            raise ValueError("PromotionRequest.fact_id is not a safe technical identifier")
        if not isinstance(self.requested_by, str) or not _ACTOR_CODE.fullmatch(
            self.requested_by
        ):
            raise ValueError(
                "PromotionRequest.requested_by must be a safe lower-case actor code"
            )
        if not isinstance(self.mode, CognitiveMode):
            raise TypeError("PromotionRequest.mode must be CognitiveMode")
        if self.target_state != _ALLOWED_TARGET:
            raise ValueError("PromotionGateway v1 can target only 'Validated'")

    @property
    def request_id(self) -> str:
        payload = {
            "fact_id": self.fact_id,
            "mode": self.mode.value,
            "policy_version": PROMOTION_POLICY_VERSION,
            "requested_by": self.requested_by,
            "target_state": self.target_state,
        }
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return f"promotion_{hashlib.sha256(canonical).hexdigest()[:24]}"

    @property
    def fact_ref(self) -> str:
        digest = hashlib.sha256(self.fact_id.encode("utf-8")).hexdigest()
        return f"fact_{digest[:24]}"


@dataclass(frozen=True, slots=True)
class PromotionVerdictSnapshot:
    """Immutable snapshot of safe, decision-relevant verdict fields."""

    passed: bool
    reason_code: str
    requested_by: str
    decided_by: str
    mode: CognitiveMode
    confidence: float
    evidence_count: int
    contradiction_refs: tuple[str, ...]
    checked_at: str


@dataclass(frozen=True, slots=True)
class PromotionReceipt:
    """Content-minimized replay evidence; no claim or justification text."""

    request_id: str
    fact_ref: str
    requested_by: str
    decided_by: str
    target_state: str
    mode: CognitiveMode
    policy_version: str
    passed: bool
    committed: bool
    idempotent: bool
    reason_code: str


@dataclass(frozen=True, slots=True)
class PromotionOutcome:
    """Gateway result for an internal caller.

    ``fact_id`` remains available to the caller, while the replayable receipt
    uses only ``fact_ref``. The receipt cannot reconstruct claim content.
    """

    fact_id: str
    verdict: PromotionVerdictSnapshot
    receipt: PromotionReceipt


class PromotionGateway:
    """Validate one promotion request against the existing store authority.

    The gateway owns no thresholds and performs no ESM mutation itself. It
    delegates exactly once to ``validate_and_promote`` and fails closed when
    the returned verdict violates the current contract.
    """

    def __init__(self, store: PromotionStore) -> None:
        self._store = store

    def promote(self, request: PromotionRequest) -> PromotionOutcome:
        verdict = self._store.validate_and_promote(
            request.fact_id,
            by=request.requested_by,
            mode=request.mode,
        )
        self._validate_verdict(request, verdict)

        idempotent = verdict.passed and verdict.reason == "already_validated"
        committed = verdict.passed and not idempotent
        snapshot = PromotionVerdictSnapshot(
            passed=verdict.passed,
            reason_code=verdict.reason,
            requested_by=request.requested_by,
            decided_by=verdict.by,
            mode=verdict.mode,
            confidence=float(verdict.confidence),
            evidence_count=int(verdict.evidence_count),
            contradiction_refs=tuple(verdict.contradictions),
            checked_at=verdict.checked_at,
        )
        receipt = PromotionReceipt(
            request_id=request.request_id,
            fact_ref=request.fact_ref,
            requested_by=request.requested_by,
            decided_by=verdict.by,
            target_state=request.target_state,
            mode=request.mode,
            policy_version=PROMOTION_POLICY_VERSION,
            passed=verdict.passed,
            committed=committed,
            idempotent=idempotent,
            reason_code=verdict.reason,
        )
        return PromotionOutcome(
            fact_id=request.fact_id,
            verdict=snapshot,
            receipt=receipt,
        )

    @staticmethod
    def _validate_verdict(
        request: PromotionRequest,
        verdict: TruthGateVerdict,
    ) -> None:
        if not isinstance(verdict, TruthGateVerdict):
            raise PromotionContractError(
                "validate_and_promote returned a non-TruthGateVerdict result"
            )
        if verdict.fact_id != request.fact_id:
            raise PromotionContractError("promotion verdict fact_id mismatch")
        if not isinstance(verdict.by, str) or not _ACTOR_CODE.fullmatch(verdict.by):
            raise PromotionContractError("promotion verdict actor is invalid")
        if verdict.by not in {request.requested_by, _TRUTH_DECIDER}:
            raise PromotionContractError("promotion verdict actor mismatch")
        if verdict.passed and verdict.by != request.requested_by:
            raise PromotionContractError(
                "passed promotion verdict must be attributed to the requesting actor"
            )
        if verdict.mode != request.mode:
            raise PromotionContractError("promotion verdict mode mismatch")
        if not isinstance(verdict.reason, str) or not verdict.reason:
            raise PromotionContractError("promotion verdict has no reason code")
        if verdict.passed and verdict.reason not in _ALLOWED_PASSED_REASONS:
            raise PromotionContractError(
                "passed promotion verdict has an unknown commit semantic"
            )
        if (
            not isinstance(verdict.evidence_count, int)
            or isinstance(verdict.evidence_count, bool)
            or verdict.evidence_count < 0
        ):
            raise PromotionContractError("promotion verdict evidence_count is invalid")
        confidence = verdict.confidence
        if (
            not isinstance(confidence, (int, float))
            or isinstance(confidence, bool)
            or not math.isfinite(float(confidence))
            or not 0.0 <= float(confidence) <= 1.0
        ):
            raise PromotionContractError("promotion verdict confidence is invalid")
        if not isinstance(verdict.contradictions, list) or any(
            not isinstance(ref, str) or not ref for ref in verdict.contradictions
        ):
            raise PromotionContractError("promotion verdict contradictions are invalid")
        if not isinstance(verdict.checked_at, str) or not verdict.checked_at:
            raise PromotionContractError("promotion verdict checked_at is invalid")


__all__ = [
    "PROMOTION_POLICY_VERSION",
    "PromotionContractError",
    "PromotionGateway",
    "PromotionOutcome",
    "PromotionReceipt",
    "PromotionRequest",
    "PromotionStore",
    "PromotionVerdictSnapshot",
]
