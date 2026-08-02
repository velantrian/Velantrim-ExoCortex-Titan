from __future__ import annotations

from core.promotion_gateway import PromotionGateway, PromotionRequest
from core.truth_gate import CognitiveMode, TruthGateVerdict


class RejectingStore:
    def validate_and_promote(
        self,
        fact_id: str,
        by: str = "truth_gate",
        mode: CognitiveMode | None = None,
    ) -> TruthGateVerdict:
        selected_mode = mode or CognitiveMode.BALANCED
        return TruthGateVerdict(
            passed=False,
            fact_id=fact_id,
            reason="insufficient_evidence",
            justification="Нужно больше независимых evidence_refs",
            by="truth_gate",
            mode=selected_mode,
            confidence=0.8,
            evidence_count=1,
            contradictions=[],
            checked_at="2026-08-02T19:10:00+00:00",
        )


def test_justification_is_available_only_on_transient_snapshot() -> None:
    outcome = PromotionGateway(RejectingStore()).promote(
        PromotionRequest(
            fact_id="fact-api-1",
            requested_by="api:1234abcd",
        )
    )

    assert outcome.verdict.justification == "Нужно больше независимых evidence_refs"
    assert outcome.verdict.reason_code == "insufficient_evidence"
    assert not hasattr(outcome.receipt, "justification")
    assert not hasattr(outcome.receipt, "claim")
    assert not hasattr(outcome.receipt, "evidence_refs")
