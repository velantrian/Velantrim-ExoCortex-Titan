"""
Response Guardian — пост-генерационная проверка ответа (Titan HYPERIA-2).

Отдельно от структурного pipeline.guardian() (FactsPack + trace).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.feature_config import get_config

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.6
MIN_TRACE_LENGTH = 1

_DEPRECATED_STATES = frozenset({"Deprecated", "Collapsed", "Contradicted"})
_HYPOTHESIS_STATES = frozenset({"Hypothesized", "Observed"})


class GuardianDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    WARN = "warn"


@dataclass
class GuardianResult:
    decision: GuardianDecision
    reason: str
    confidence: float
    response: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "confidence": round(self.confidence, 4),
            "response": self.response,
        }


def is_response_guardian_enabled() -> bool:
    return get_config().app.enable_response_guardian


class ResponseGuardian:
    """Валидатор ответа после генерации (Fast Path, синхронный, без токенов)."""

    def validate(
        self,
        response: str,
        confidence: float,
        trace: list[str],
        sources: list[dict[str, Any]] | None = None,
    ) -> GuardianResult:
        if confidence < CONFIDENCE_THRESHOLD:
            logger.info("ResponseGuardian: REJECT — low confidence (%.2f)", confidence)
            return GuardianResult(
                decision=GuardianDecision.REJECT,
                reason=f"confidence too low ({confidence:.2f})",
                confidence=confidence,
                response=(
                    "Я не уверен в достаточной мере, чтобы дать точный ответ. "
                    "Могу поискать больше информации или уточнить детали."
                ),
            )

        if not trace or len(trace) < MIN_TRACE_LENGTH:
            logger.info("ResponseGuardian: REJECT — empty trace")
            return GuardianResult(
                decision=GuardianDecision.REJECT,
                reason="no reasoning trace",
                confidence=confidence,
                response=(
                    "У меня нет достаточно подтверждённых данных по этому вопросу. "
                    "Расскажи подробнее — это поможет найти нужную информацию."
                ),
            )

        if sources:
            non_deprecated = [
                s
                for s in sources
                if s.get("epistemic_state") not in _DEPRECATED_STATES
            ]
            if not non_deprecated:
                logger.info("ResponseGuardian: REJECT — all sources deprecated")
                return GuardianResult(
                    decision=GuardianDecision.REJECT,
                    reason="all memory sources are deprecated",
                    confidence=confidence,
                    response=(
                        "Информация по этой теме в памяти устарела. "
                        "Уточни актуальные данные — обновлю."
                    ),
                )

            hypothesis_count = sum(
                1 for s in sources if s.get("epistemic_state") in _HYPOTHESIS_STATES
            )
            if hypothesis_count > len(sources) / 2:
                logger.info(
                    "ResponseGuardian: WARN — %d/%d hypothesis sources",
                    hypothesis_count,
                    len(sources),
                )
                return GuardianResult(
                    decision=GuardianDecision.WARN,
                    reason=f"{hypothesis_count}/{len(sources)} sources unconfirmed",
                    confidence=confidence,
                    response=f"[Частично предположение] {response}",
                )

        return GuardianResult(
            decision=GuardianDecision.APPROVE,
            reason="all checks passed",
            confidence=confidence,
            response=response,
        )


_guardian: ResponseGuardian | None = None


def get_response_guardian() -> ResponseGuardian:
    global _guardian
    if _guardian is None:
        _guardian = ResponseGuardian()
    return _guardian


def apply_response_guardian(
    answer: str,
    facts: list[dict[str, Any]],
    trace: list[dict[str, Any]],
) -> GuardianResult:
    """Применить пост-Guardian; если выключен — APPROVE с исходным ответом."""
    trace_ids = [t.get("fact_id") or t.get("id") for t in trace if t.get("fact_id") or t.get("id")]
    avg_conf = 0.0
    if facts:
        avg_conf = sum(float(f.get("confidence", 0.5)) for f in facts) / len(facts)
    if not is_response_guardian_enabled():
        return GuardianResult(
            decision=GuardianDecision.APPROVE,
            reason="response_guardian disabled",
            confidence=avg_conf,
            response=answer,
        )
    return get_response_guardian().validate(
        response=answer,
        confidence=avg_conf,
        trace=[str(x) for x in trace_ids if x],
        sources=facts,
    )


__all__ = [
    "GuardianDecision",
    "GuardianResult",
    "ResponseGuardian",
    "apply_response_guardian",
    "get_response_guardian",
    "is_response_guardian_enabled",
]
