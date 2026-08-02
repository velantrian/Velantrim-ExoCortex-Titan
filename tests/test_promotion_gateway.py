from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from core.promotion_gateway import (
    PROMOTION_POLICY_VERSION,
    PromotionContractError,
    PromotionGateway,
    PromotionRequest,
)
from core.truth_gate import CognitiveMode, TruthGateVerdict


class FakePromotionStore:
    def __init__(
        self,
        verdict: TruthGateVerdict | object,
        *,
        error: Exception | None = None,
    ) -> None:
        self.verdict = verdict
        self.error = error
        self.calls: list[tuple[str, str, Any]] = []

    def validate_and_promote(
        self,
        fact_id: str,
        by: str = "truth_gate",
        mode: Any = None,
    ) -> Any:
        self.calls.append((fact_id, by, mode))
        if self.error is not None:
            raise self.error
        return self.verdict


def _verdict(
    *,
    passed: bool,
    reason: str,
    fact_id: str = "fact-1",
    by: str = "api_transition",
    mode: CognitiveMode = CognitiveMode.BALANCED,
    confidence: float = 0.8,
    evidence_count: int = 2,
) -> TruthGateVerdict:
    return TruthGateVerdict(
        passed=passed,
        fact_id=fact_id,
        reason=reason,
        justification="not persisted in gateway receipt",
        by=by,
        mode=mode,
        confidence=confidence,
        evidence_count=evidence_count,
        contradictions=[],
        checked_at="2026-08-02T17:55:00+00:00",
    )


def test_request_identity_is_deterministic_and_content_minimized() -> None:
    first = PromotionRequest(
        fact_id="fact-1",
        requested_by="api_transition",
        mode=CognitiveMode.BALANCED,
    )
    second = PromotionRequest(
        fact_id="fact-1",
        requested_by="api_transition",
        mode=CognitiveMode.BALANCED,
    )

    assert first.request_id == second.request_id
    assert first.request_id.startswith("promotion_")
    assert first.fact_ref.startswith("fact_")
    assert "fact-1" not in first.fact_ref


def test_request_rejects_invalid_target_actor_and_identifier() -> None:
    with pytest.raises(ValueError, match="only 'Validated'"):
        PromotionRequest(
            fact_id="fact-1",
            requested_by="api_transition",
            target_state="Supported",
        )
    with pytest.raises(ValueError, match="actor code"):
        PromotionRequest(fact_id="fact-1", requested_by="API transition")
    with pytest.raises(ValueError, match="non-empty"):
        PromotionRequest(fact_id="", requested_by="api_transition")
    with pytest.raises(TypeError, match="CognitiveMode"):
        PromotionRequest(  # type: ignore[arg-type]
            fact_id="fact-1",
            requested_by="api_transition",
            mode="BALANCED",
        )


def test_passed_verdict_records_one_committed_promotion() -> None:
    store = FakePromotionStore(_verdict(passed=True, reason="passed"))
    request = PromotionRequest(
        fact_id="fact-1",
        requested_by="api_transition",
    )

    outcome = PromotionGateway(store).promote(request)

    assert store.calls == [
        ("fact-1", "api_transition", CognitiveMode.BALANCED)
    ]
    assert outcome.fact_id == "fact-1"
    assert outcome.verdict.passed is True
    assert outcome.receipt.passed is True
    assert outcome.receipt.committed is True
    assert outcome.receipt.idempotent is False
    assert outcome.receipt.reason_code == "passed"
    assert outcome.receipt.policy_version == PROMOTION_POLICY_VERSION


def test_already_validated_is_idempotent_without_new_commit() -> None:
    store = FakePromotionStore(
        _verdict(passed=True, reason="already_validated")
    )

    outcome = PromotionGateway(store).promote(
        PromotionRequest(fact_id="fact-1", requested_by="api_transition")
    )

    assert outcome.receipt.passed is True
    assert outcome.receipt.committed is False
    assert outcome.receipt.idempotent is True


@pytest.mark.parametrize(
    "reason",
    ["low_confidence", "insufficient_evidence", "concurrent_modification"],
)
def test_rejected_verdict_never_claims_commit(reason: str) -> None:
    store = FakePromotionStore(_verdict(passed=False, reason=reason))

    outcome = PromotionGateway(store).promote(
        PromotionRequest(fact_id="fact-1", requested_by="api_transition")
    )

    assert outcome.receipt.passed is False
    assert outcome.receipt.committed is False
    assert outcome.receipt.idempotent is False
    assert outcome.receipt.reason_code == reason


def test_outcome_is_frozen_and_receipt_excludes_justification() -> None:
    store = FakePromotionStore(_verdict(passed=True, reason="passed"))
    outcome = PromotionGateway(store).promote(
        PromotionRequest(fact_id="fact-1", requested_by="api_transition")
    )

    with pytest.raises(FrozenInstanceError):
        setattr(outcome.receipt, "committed", False)
    assert not hasattr(outcome.receipt, "justification")
    assert not hasattr(outcome.receipt, "claim")
    assert not hasattr(outcome.receipt, "evidence_refs")


def test_gateway_propagates_store_failure_without_fabricating_receipt() -> None:
    store = FakePromotionStore(
        _verdict(passed=False, reason="unused"),
        error=RuntimeError("database unavailable"),
    )

    with pytest.raises(RuntimeError, match="database unavailable"):
        PromotionGateway(store).promote(
            PromotionRequest(fact_id="fact-1", requested_by="api_transition")
        )
    assert len(store.calls) == 1


@pytest.mark.parametrize(
    "verdict",
    [
        object(),
        _verdict(passed=True, reason="future_pass_semantic"),
        _verdict(passed=True, reason="passed", fact_id="other-fact"),
        _verdict(passed=True, reason="passed", by="different_actor"),
        _verdict(
            passed=True,
            reason="passed",
            mode=CognitiveMode.PRECISION,
        ),
        _verdict(passed=True, reason="passed", confidence=float("nan")),
        _verdict(passed=True, reason="passed", evidence_count=-1),
    ],
)
def test_gateway_fails_closed_on_invalid_underlying_contract(verdict: object) -> None:
    store = FakePromotionStore(verdict)

    with pytest.raises(PromotionContractError):
        PromotionGateway(store).promote(
            PromotionRequest(fact_id="fact-1", requested_by="api_transition")
        )


def test_gateway_exposes_no_raw_transition_shortcut() -> None:
    gateway = PromotionGateway(
        FakePromotionStore(_verdict(passed=True, reason="passed"))
    )

    assert not hasattr(gateway, "transition_esm")
    assert not hasattr(gateway, "promote_esm_to")
    assert not hasattr(gateway, "store_fact")
