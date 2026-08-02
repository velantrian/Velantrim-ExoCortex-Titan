from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.promotion_gateway import PromotionGateway, PromotionRequest


class ReloadedMode(str, Enum):
    BALANCED = "BALANCED"


@dataclass
class ReloadedVerdict:
    """Structurally valid verdict from a reloaded module/class identity."""

    passed: bool = False
    fact_id: str = "fact-1"
    reason: str = "insufficient_evidence"
    justification: str = "structural test only"
    by: str = "truth_gate"
    mode: ReloadedMode = ReloadedMode.BALANCED
    confidence: float = 0.9
    evidence_count: int = 1
    contradictions: list[str] = field(default_factory=list)
    checked_at: str = "2026-08-02T18:41:58+00:00"


class ReloadedVerdictStore:
    def validate_and_promote(
        self,
        fact_id: str,
        by: str = "truth_gate",
        mode: Any = None,
    ) -> Any:
        return ReloadedVerdict(fact_id=fact_id)


def test_structural_verdict_survives_module_reload_identity_change() -> None:
    outcome = PromotionGateway(ReloadedVerdictStore()).promote(
        PromotionRequest(
            fact_id="fact-1",
            requested_by="graduated_promotion",
        )
    )

    assert outcome.receipt.passed is False
    assert outcome.receipt.committed is False
    assert outcome.receipt.requested_by == "graduated_promotion"
    assert outcome.receipt.decided_by == "truth_gate"
    assert outcome.receipt.reason_code == "insufficient_evidence"
