"""
⚖️ core/fact_decayer.py — Fact-Level Decay (V8.8, V9 Contract #22 extension)
=============================================================================

Проблема: DecayOrchestrator работает только на уровне Velum-синапсов
(entity-entity связи). На уровне фактов decay отсутствует:
  - 19 000+ фактов World Skills — все имеют одинаковый «вес»
  - Нет vintage-decay: факт 2024 года и факт 2026 года равны
  - Нет salience-based retention: важные и неважные равны

Решение: FactDecayer добавляет два измерения decay на уровне фактов:
  1. Vintage — чем старше, тем ниже relevance_weight (но НЕ confidence!)
  2. Salience — Ring Zero защита для критически важных фактов

Используется в ConsolidationEngine, SleepTimeWorker, retrieval ranking.

Использование:
    decayer = FactDecayer()
    weight = decayer.decay_weight(fact)
    # → 0.95 для свежего факта, 0.60 для старого,
    #   1.0 для Ring Zero / ImmutableCore
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("velantrim.fact_decayer")

# Пороги
RING_ZERO_IDS = {"VALUES_CORE", "RING_ZERO"}
IMMUTABLE_STATES = {"ImmutableCore"}
HIGH_SALIENCE_THRESHOLD = 0.85  # Ring Zero защита
VINTAGE_DECAY_RATE = 0.0005     # мягкий decay: 0.05% в день
VINTAGE_HALF_LIFE_DAYS = 365    # через год relevance падает на 50%
UNUSED_DECAY_DAYS = 30          # неиспользуемые факты начинают затухать через 30 дней


@dataclass
class FactDecayResult:
    """Результат decay-оценки факта."""
    fact_id: str
    relevance_weight: float      # 0..1, итоговый вес факта для retrieval
    vintage_factor: float        # 0..1, фактор возраста
    salience_factor: float       # 0..1, фактор значимости
    protected: bool              # Ring Zero / ImmutableCore
    age_days: float              # сколько дней факту


class FactDecayer:
    """
    Оценка relevance-веса факта с учётом vintage и salience.

    НЕ меняет confidence (это отдельная ось проверки истинности).
    Меняет ТОЛЬКО relevance_weight — используется при ранжировании retrieval.
    """

    def __init__(
        self,
        *,
        vintage_rate: float = VINTAGE_DECAY_RATE,
        unused_days: int = UNUSED_DECAY_DAYS,
    ) -> None:
        self._vintage_rate = vintage_rate
        self._unused_days = unused_days

    def decay_weight(self, fact: Dict[str, Any]) -> FactDecayResult:
        """
        Вычислить relevance-вес факта.

        Args:
            fact: dict с полями fact_id, created_at, significance,
                  epistemic_state, usage_count (опционально)

        Returns:
            FactDecayResult с relevance_weight 0..1
        """
        fact_id = str(fact.get("fact_id", ""))
        state = str(fact.get("epistemic_state", ""))

        # Ring Zero / ImmutableCore — всегда protected
        if fact_id in RING_ZERO_IDS or state in IMMUTABLE_STATES:
            return FactDecayResult(
                fact_id=fact_id,
                relevance_weight=1.0,
                vintage_factor=1.0,
                salience_factor=1.0,
                protected=True,
                age_days=0,
            )

        # Vintage: возраст факта
        created = fact.get("created_at", "")
        age_days = self._compute_age_days(created)

        # vintage_factor = 1 / (1 + rate * days)
        # Через 365 дней: 1 / (1 + 0.0005 * 365) = 1 / 1.1825 = 0.846
        vintage_factor = 1.0 / (1.0 + self._vintage_rate * age_days)

        # Salience: значимость + usage
        significance = float(fact.get("significance", 0.5))
        usage_count = int(fact.get("usage_count", 0))

        # Базовый salience_factor = significance
        salience_factor = significance

        # High salience → Ring Zero защита
        if significance >= HIGH_SALIENCE_THRESHOLD:
            salience_factor = 1.0

        # Неиспользуемые факты (usage=0 + старые) — дополнительный decay
        if usage_count == 0 and age_days > self._unused_days:
            unused_factor = 1.0 / (1.0 + 0.001 * (age_days - self._unused_days))
            salience_factor *= unused_factor

        # Итоговый вес
        relevance_weight = vintage_factor * salience_factor

        # Нормализация
        relevance_weight = max(0.1, min(1.0, relevance_weight))
        protected = significance >= HIGH_SALIENCE_THRESHOLD

        return FactDecayResult(
            fact_id=fact_id,
            relevance_weight=round(relevance_weight, 4),
            vintage_factor=round(vintage_factor, 4),
            salience_factor=round(salience_factor, 4),
            protected=protected,
            age_days=round(age_days, 1),
        )

    def decay_batch(self, facts: list[Dict[str, Any]]) -> Dict[str, FactDecayResult]:
        """Пакетная оценка. Возвращает dict[fact_id → result]."""
        return {
            str(f.get("fact_id", "")): self.decay_weight(f)
            for f in facts
        }

    def is_relevant(self, fact: Dict[str, Any], min_weight: float = 0.3) -> bool:
        """Достаточно ли факт релевантен для retrieval?"""
        result = self.decay_weight(fact)
        return result.relevance_weight >= min_weight

    @staticmethod
    def _compute_age_days(created_at: str) -> float:
        """Дней с момента создания факта."""
        if not created_at:
            return 0
        try:
            # Пробуем ISO-формат
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            # Приводим к UTC если нужно
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            delta = now - created
            return delta.total_seconds() / 86400.0
        except (ValueError, TypeError):
            return 0


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_decayer: Optional[FactDecayer] = None


def get_fact_decayer() -> FactDecayer:
    global _decayer
    if _decayer is None:
        _decayer = FactDecayer()
    return _decayer


__all__ = [
    "FactDecayer",
    "FactDecayResult",
    "get_fact_decayer",
]
