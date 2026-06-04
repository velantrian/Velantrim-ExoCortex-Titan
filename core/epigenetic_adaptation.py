"""
🧬 core/epigenetic_adaptation.py — Epigenetic Adaptation (V8.7 Titan, из Crystal fork)

RFC0071: эпигенетическая адаптация без переобучения.
Вдохновлено растительной эпигенетической памятью и бактериальной CRISPR-адаптацией.

4 эпигенетических тега:
    verification  — выше → больше проверок фактов (TruthGate строже)
    creativity    — выше → более творческие ответы
    conservatism  — выше → предпочтение известных паттернов
    exploration   — выше → пробовать новые связи

При стрессе (hallucination, ошибка, конфликт): verification↑, creativity↓.
При спокойствии: exploration↑, creativity↑.

Инварианты:
    I-EP1: Эпигенетические теги меняют ТОЛЬКО параметры поведения. Не truth.
    I-EP2: Адаптация обратима — relaxation после стресса.
    I-EP3: Не пишет в граф. Только in-memory + эфемерно.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.epigenetic_adaptation")


@dataclass
class EpigeneticState:
    """Текущее эпигенетическое состояние системы."""
    verification: float = 0.5    # 0..1 — строгость TruthGate
    creativity: float = 0.5      # 0..1 — творческий режим
    conservatism: float = 0.5    # 0..1 — предпочтение известного
    exploration: float = 0.5     # 0..1 — исследование нового
    stress_level: float = 0.0    # 0..1 — текущий уровень стресса
    tags_updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verification": round(self.verification, 2),
            "creativity": round(self.creativity, 2),
            "conservatism": round(self.conservatism, 2),
            "exploration": round(self.exploration, 2),
            "stress_level": round(self.stress_level, 2),
            "tags_updated_at": self.tags_updated_at,
        }

    @property
    def truth_gate_multiplier(self) -> float:
        """Множитель для порогов TruthGate. 1.0 = без изменений."""
        return 1.0 + (self.verification - 0.5) * 0.4

    @property
    def temperature_modifier(self) -> float:
        """Модификатор температуры LLM."""
        return 0.6 + (self.creativity - 0.5) * 0.4


class EpigeneticAdaptationEngine:
    """
    Движок эпигенетической адаптации.

    Использование:
        engine = EpigeneticAdaptationEngine()

        # При ошибке/галлюцинации:
        engine.record_stress(0.7, context="hallucination_detected")

        # При спокойной работе:
        engine.record_stress(0.1, context="normal_operation")

        # Применить к TruthGate:
        multiplier = engine.state.truth_gate_multiplier
        effective_threshold = base_threshold * multiplier
    """

    ADAPTATION_THRESHOLD = 0.6
    RELAXATION_RATE = 0.03   # за каждый спокойный цикл

    def __init__(self):
        self.state = EpigeneticState()
        self._stress_history: List[Dict[str, Any]] = []
        self._cycles_since_stress = 0

    def record_stress(self, stress_level: float, context: str = "general") -> None:
        """
        Записать стрессовое событие. Обновляет эпигенетические теги.

        stress_level > ADAPTATION_THRESHOLD → verification↑, creativity↓, conservatism↑
        stress_level < ADAPTATION_THRESHOLD → exploration↑, creativity↑
        """
        s = max(0.0, min(1.0, stress_level))
        self.state.stress_level = s
        self.state.tags_updated_at = datetime.now(timezone.utc).isoformat()

        self._stress_history.append({
            "level": s,
            "context": context,
            "at": self.state.tags_updated_at,
        })
        if len(self._stress_history) > 100:
            self._stress_history = self._stress_history[-100:]

        if s > self.ADAPTATION_THRESHOLD:
            # Стресс → защитный режим
            self.state.verification = min(1.0, self.state.verification + 0.12)
            self.state.creativity = max(0.1, self.state.creativity - 0.10)
            self.state.conservatism = min(1.0, self.state.conservatism + 0.08)
            self._cycles_since_stress = 0
            logger.info("Epigenetic: STRESS %.2f — verification=%.2f creativity=%.2f", s, self.state.verification, self.state.creativity)
        else:
            # Спокойствие → исследовательский режим
            self.state.exploration = min(1.0, self.state.exploration + 0.06)
            self.state.creativity = min(1.0, self.state.creativity + 0.04)
            self._cycles_since_stress += 1

    def relax(self) -> None:
        """Постепенное возвращение к baseline после стресса."""
        if self._cycles_since_stress < 3:
            return
        rr = self.RELAXATION_RATE
        self.state.verification = max(0.5, self.state.verification - rr)
        self.state.conservatism = max(0.5, self.state.conservatism - rr * 0.7)
        self.state.creativity = min(1.0, self.state.creativity + rr * 0.5)
        self.state.tags_updated_at = datetime.now(timezone.utc).isoformat()

    def adapt_truth_gate(self, base_threshold: float) -> float:
        """Адаптированный порог TruthGate."""
        return min(1.0, max(0.1, base_threshold * self.state.truth_gate_multiplier))

    def adapt_temperature(self, base_temp: float = 0.7) -> float:
        """Адаптированная температура LLM."""
        return min(1.2, max(0.1, base_temp + (self.state.creativity - 0.5) * 0.3))

    def stats(self) -> Dict[str, Any]:
        return {
            "state": self.state.to_dict(),
            "stress_events": len(self._stress_history),
            "cycles_since_stress": self._cycles_since_stress,
        }


# Глобальный экземпляр
_engine: Optional[EpigeneticAdaptationEngine] = None


def get_epigenetic_engine() -> EpigeneticAdaptationEngine:
    global _engine
    if _engine is None:
        _engine = EpigeneticAdaptationEngine()
    return _engine


__all__ = ["EpigeneticAdaptationEngine", "EpigeneticState", "get_epigenetic_engine"]
