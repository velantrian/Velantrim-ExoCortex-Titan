"""
🔄 core/negative_reinforcement.py — Negative Reinforcement + Anti-pattern Detection (V8.7 Titan)

Дополняет ReasoningBank (Thompson Sampling) явным механизмом:
    1. Confidence penalty за провалы
    2. Escalating penalty — частые провалы усиливают штраф
    3. Anti-pattern detection — извлечение «никогда не делай X когда Y»

Инварианты:
    I-NR1: Confidence penalty применяется только к strategy.confidence, не к truth.
    I-NR2: Anti-patterns — read-only рекомендации. Не блокируют стратегии.
    I-NR3: Penalty escalation — макс penalty = 0.3 (стратегия не умирает полностью).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.negative_reinforcement")

# ─── Anti-pattern ─────────────────────────────────────────────────────────────

@dataclass
class AntiPattern:
    """
    Извлечённый урок из провалов: «никогда не делай X когда Y».
    """
    anti_pattern_id: str
    condition: str          # «когда Y» (context)
    bad_action: str         # «X» (что привело к провалу)
    failure_count: int = 1
    severity: float = 0.5   # 0..1 — насколько серьёзно
    extracted_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anti_pattern_id": self.anti_pattern_id,
            "condition": self.condition,
            "bad_action": self.bad_action,
            "failure_count": self.failure_count,
            "severity": self.severity,
            "extracted_at": self.extracted_at,
        }

    def rule(self) -> str:
        return f"Когда {self.condition} → НЕ {self.bad_action}"


# ─── Negative Reinforcement Engine ────────────────────────────────────────────

@dataclass
class PenaltyConfig:
    base_penalty: float = 0.15         # базовый штраф за один провал
    max_penalty: float = 0.30          # максимум штрафа (не убиваем стратегию)
    escalation_threshold: int = 5      # после этого числа провалов — усиление
    escalation_factor: float = 1.2     # множитель штрафа при эскалации
    recovery_boost: float = 0.05       # бонус при успехе после серии провалов


class NegativeReinforcementEngine:
    """
    Движок negative reinforcement для ReasoningBank.

    Использование:
        engine = NegativeReinforcementEngine()

        # При провале стратегии
        engine.on_failure(strategy_id="strat_5", context="user_query_about_code",
                          action="tried_llm_first", reason="llm_hallucinated")

        # При успехе
        engine.on_success(strategy_id="strat_5")

        # Извлечение анти-паттернов
        patterns = engine.extract_anti_patterns()
    """

    def __init__(self, config: Optional[PenaltyConfig] = None):
        self._config = config or PenaltyConfig()
        self._failure_history: Dict[str, List[Dict[str, Any]]] = {}
        self._anti_patterns: Dict[str, AntiPattern] = {}
        self._strategy_penalties: Dict[str, float] = {}  # strategy_id → accumulated penalty

    # ── События ───────────────────────────────────────────────────────────

    def on_failure(
        self,
        *,
        strategy_id: str,
        context: str = "",
        action: str = "",
        reason: str = "",
    ) -> Dict[str, Any]:
        """
        Записать провал стратегии. Возвращает penalty_info.
        """
        # Запись в историю
        failure = {
            "strategy_id": strategy_id,
            "context": context[:200],
            "action": action[:200],
            "reason": reason[:200],
            "at": datetime.now(timezone.utc).isoformat(),
        }
        self._failure_history.setdefault(strategy_id, []).append(failure)

        # Вычислить penalty
        fail_count = len(self._failure_history[strategy_id])
        penalty = self._config.base_penalty

        if fail_count > self._config.escalation_threshold:
            escalation_steps = fail_count - self._config.escalation_threshold
            penalty = min(
                self._config.max_penalty,
                self._config.base_penalty * (self._config.escalation_factor ** escalation_steps),
            )

        self._strategy_penalties[strategy_id] = penalty

        # Попытка извлечь анти-паттерн
        if fail_count >= 3:
            self._try_extract_anti_pattern(strategy_id, context, action)

        logger.debug(
            "NegativeReinforcement: %s failure #%d (penalty=%.2f)",
            strategy_id, fail_count, penalty,
        )

        return {
            "strategy_id": strategy_id,
            "failure_count": fail_count,
            "penalty": penalty,
            "escalated": fail_count > self._config.escalation_threshold,
        }

    def on_success(self, *, strategy_id: str) -> Dict[str, Any]:
        """
        Записать успех. Немного снижает накопленный penalty.
        """
        current = self._strategy_penalties.get(strategy_id, 0.0)
        if current > 0:
            current = max(0.0, current - self._config.recovery_boost)
            self._strategy_penalties[strategy_id] = current

        # Если была серия провалов, а теперь успех — очистить часть истории
        if strategy_id in self._failure_history and len(self._failure_history[strategy_id]) > 3:
            # Оставить последние 3 (недавний опыт)
            self._failure_history[strategy_id] = self._failure_history[strategy_id][-3:]

        return {
            "strategy_id": strategy_id,
            "penalty_after_recovery": current,
        }

    # ── Anti-pattern detection ────────────────────────────────────────────

    def _try_extract_anti_pattern(
        self, strategy_id: str, context: str, action: str
    ) -> None:
        """Попытаться извлечь анти-паттерн из серии провалов."""
        failures = self._failure_history.get(strategy_id, [])
        if len(failures) < 3:
            return

        # Проверить: все провалы в похожем контексте?
        contexts = [f["context"] for f in failures[-5:] if f["context"]]
        actions = [f["action"] for f in failures[-5:] if f["action"]]

        if not contexts or not actions:
            return

        # Найти самый частый контекст и действие
        from collections import Counter
        top_context = Counter(contexts).most_common(1)[0]
        top_action = Counter(actions).most_common(1)[0]

        # Если контекст повторяется ≥3 раз — это анти-паттерн
        if top_context[1] >= 3:
            pattern_id = f"ap_{strategy_id}_{hash(top_context[0] + top_action[0]) % 10000:04d}"
            severity = min(0.9, 0.4 + 0.1 * top_context[1])

            self._anti_patterns[pattern_id] = AntiPattern(
                anti_pattern_id=pattern_id,
                condition=top_context[0][:120],
                bad_action=top_action[0][:120],
                failure_count=top_context[1],
                severity=severity,
            )
            logger.info(
                "🛡️ Anti-pattern detected: %s (%d failures, severity=%.2f)",
                self._anti_patterns[pattern_id].rule(),
                top_context[1],
                severity,
            )

    def extract_anti_patterns(
        self, *, min_severity: float = 0.5
    ) -> List[AntiPattern]:
        """Получить все анти-паттерны с severity ≥ min_severity."""
        return [
            ap for ap in self._anti_patterns.values()
            if ap.severity >= min_severity
        ]

    # ── Статистика ────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        return {
            "strategies_tracked": len(self._failure_history),
            "total_failures": sum(len(v) for v in self._failure_history.values()),
            "anti_patterns_detected": len(self._anti_patterns),
            "active_penalties": {
                k: round(v, 3)
                for k, v in self._strategy_penalties.items()
                if v > 0
            },
        }

    def get_penalty(self, strategy_id: str) -> float:
        """Текущий penalty для стратегии."""
        return self._strategy_penalties.get(strategy_id, 0.0)


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_engine: Optional[NegativeReinforcementEngine] = None


def get_negative_reinforcement_engine() -> NegativeReinforcementEngine:
    global _engine
    if _engine is None:
        _engine = NegativeReinforcementEngine()
    return _engine


__all__ = [
    "AntiPattern",
    "NegativeReinforcementEngine",
    "PenaltyConfig",
    "get_negative_reinforcement_engine",
]
