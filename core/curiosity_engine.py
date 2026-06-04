"""
🧠 core/curiosity_engine.py — CuriosityEngine (V8.7 Titan, из Claude Code L4,L5)

Детерминированный движок «что я ХОЧУ узнать». 0 токенов LLM.
Не пассивный детектор — активный стимул к исследованию.

4 типа любознательности:
    KNOWLEDGE_GAP   (0.8) — обнаружен пробел в знаниях. Самый сильный стимул.
    CONTRADICTION   (0.9) — противоречие в графе. ОЧЕНЬ интересно!
    UNEXPLORED      (0.6) — тема, которую пользователь не исследовал.
    COMPLEXITY      (0.5) — сложная тема, требующая глубокого погружения.

Использование:
    engine = CuriosityEngine()

    # Подать сигналы от pipeline
    triggers = engine.process_signals(
        gap_count=3,
        contradiction_count=1,
        unvisited_topics=["квантовая физика", "биоинформатика"],
    )

    # В SleepTimeWorker
    suggestions = engine.suggest_next(top_n=3)
    # → ["квантовая физика", "противоречие: фотосинтез vs хемосинтез", "биоинформатика"]

Инвариант:
    I-CU1: CuriosityEngine — только предлагает. Не пишет в граф.
    I-CU2: Предложение не повторяется раньше 7 дней (suppression).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.curiosity_engine")


# ─── Типы триггеров ──────────────────────────────────────────────────────────

@dataclass
class CuriosityTrigger:
    """Один триггер любознательности."""
    trigger_id: str
    trigger_type: str         # KNOWLEDGE_GAP / CONTRADICTION / UNEXPLORED / COMPLEXITY
    description: str
    topic: str                # тема, которую предлагается исследовать
    intensity: float          # 0..1, насколько сильно хочется узнать
    source: str = "system"    # что породило триггер
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "type": self.trigger_type,
            "description": self.description,
            "topic": self.topic,
            "intensity": round(self.intensity, 2),
            "source": self.source,
        }


# ─── Веса типов ──────────────────────────────────────────────────────────────

_TRIGGER_WEIGHTS = {
    "CONTRADICTION": 0.90,    # Противоречия — самые интересные
    "KNOWLEDGE_GAP": 0.80,    # Пробелы в знаниях — сильный стимул
    "UNEXPLORED": 0.60,       # Неисследованное — умеренный интерес
    "COMPLEXITY": 0.50,       # Сложность — слабый стимул
}


# ─── Основной класс ──────────────────────────────────────────────────────────

class CuriosityEngine:
    """
    Движок любознательности VELANTRIM.

    Работает в SleepTimeWorker (Slow Path). Получает сигналы от pipeline/observer
    и предлагает темы для исследования. Не пишет в граф — только возвращает список тем.

    Suppression: предложенная тема не повторяется раньше 7 дней.
    """

    def __init__(self, suppression_days: int = 7):
        self._triggers: List[CuriosityTrigger] = []
        self._suggested: Dict[str, float] = {}  # topic → timestamp последнего предложения
        self._suppression_sec = suppression_days * 86400

    # ── Сигналы ──────────────────────────────────────────────────────────

    def process_signals(
        self,
        *,
        gap_topics: Optional[List[str]] = None,
        contradiction_topics: Optional[List[str]] = None,
        unvisited_topics: Optional[List[str]] = None,
        complexity_topics: Optional[List[str]] = None,
    ) -> List[CuriosityTrigger]:
        """
        Обработать сигналы от pipeline/observer/gap_detector.

        Каждый сигнал → CuriosityTrigger с intensity = weight × base.
        """
        new_triggers: List[CuriosityTrigger] = []
        ts = int(time.time() * 1_000_000)

        # KNOWLEDGE_GAP
        for topic in (gap_topics or []):
            trigger = CuriosityTrigger(
                trigger_id=f"cq_gap_{ts}_{hash(topic) % 10000:04d}",
                trigger_type="KNOWLEDGE_GAP",
                description=f"Пробел в знаниях: {topic}",
                topic=topic,
                intensity=_TRIGGER_WEIGHTS["KNOWLEDGE_GAP"],
                source="gap_detector",
            )
            new_triggers.append(trigger)

        # CONTRADICTION
        for topic in (contradiction_topics or []):
            trigger = CuriosityTrigger(
                trigger_id=f"cq_cnt_{ts}_{hash(topic) % 10000:04d}",
                trigger_type="CONTRADICTION",
                description=f"Противоречие: {topic}",
                topic=topic,
                intensity=_TRIGGER_WEIGHTS["CONTRADICTION"],
                source="contradiction_registry",
            )
            new_triggers.append(trigger)

        # UNEXPLORED
        for topic in (unvisited_topics or []):
            trigger = CuriosityTrigger(
                trigger_id=f"cq_unx_{ts}_{hash(topic) % 10000:04d}",
                trigger_type="UNEXPLORED",
                description=f"Неисследованная тема: {topic}",
                topic=topic,
                intensity=_TRIGGER_WEIGHTS["UNEXPLORED"],
                source="cross_domain",
            )
            new_triggers.append(trigger)

        # COMPLEXITY
        for topic in (complexity_topics or []):
            trigger = CuriosityTrigger(
                trigger_id=f"cq_cpx_{ts}_{hash(topic) % 10000:04d}",
                trigger_type="COMPLEXITY",
                description=f"Сложная тема: {topic}",
                topic=topic,
                intensity=_TRIGGER_WEIGHTS["COMPLEXITY"],
                source="essence",
            )
            new_triggers.append(trigger)

        self._triggers.extend(new_triggers)
        return new_triggers

    # ── Предложения ──────────────────────────────────────────────────────

    def suggest_next(self, top_n: int = 3) -> List[str]:
        """
        Предложить top_n тем для исследования.

        Фильтрует:
            - Уже предложенные в течение suppression_days (подавление)
            - Сортирует по intensity (убывание)

        Returns:
            Список тем (description).
        """
        now = time.time()
        active = [
            t for t in self._triggers
            if t.topic not in self._suggested
            or now - self._suggested.get(t.topic, 0) > self._suppression_sec
        ]

        if not active:
            return []

        # Сортировка по intensity
        active.sort(key=lambda t: t.intensity, reverse=True)

        suggestions: List[str] = []
        for trigger in active[:top_n]:
            suggestions.append(trigger.description)
            self._suggested[trigger.topic] = now

        logger.debug(
            "CuriosityEngine: %d активных триггеров → %d предложений",
            len(active), len(suggestions),
        )
        return suggestions

    def suggest_by_type(self, trigger_type: str, top_n: int = 3) -> List[str]:
        """Предложить темы только одного типа."""
        now = time.time()
        filtered = [
            t for t in self._triggers
            if t.trigger_type == trigger_type
            and (
                t.topic not in self._suggested
                or now - self._suggested.get(t.topic, 0) > self._suppression_sec
            )
        ]
        filtered.sort(key=lambda t: t.intensity, reverse=True)

        suggestions: List[str] = []
        for trigger in filtered[:top_n]:
            suggestions.append(trigger.description)
            self._suggested[trigger.topic] = now

        return suggestions

    # ── Статистика ────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        total_intensity = 0.0
        for t in self._triggers:
            by_type[t.trigger_type] = by_type.get(t.trigger_type, 0) + 1
            total_intensity += t.intensity

        return {
            "total_triggers": len(self._triggers),
            "by_type": by_type,
            "avg_intensity": round(total_intensity / max(1, len(self._triggers)), 2),
            "suggested_count": len(self._suggested),
        }

    def cleanup(self, max_age_days: int = 30) -> int:
        """Удалить старые триггеры."""
        cutoff = time.time() - max_age_days * 86400
        before = len(self._triggers)
        self._triggers = [t for t in self._triggers if t.created_at > cutoff]
        removed = before - len(self._triggers)
        if removed:
            logger.debug("CuriosityEngine: очищено %d старых триггеров", removed)
        return removed

    def active_triggers(self) -> List[CuriosityTrigger]:
        """Все активные триггеры (без подавленных)."""
        now = time.time()
        return [
            t for t in self._triggers
            if t.topic not in self._suggested
            or now - self._suggested.get(t.topic, 0) > self._suppression_sec
        ]


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_engine: Optional[CuriosityEngine] = None


def get_curiosity_engine() -> CuriosityEngine:
    global _engine
    if _engine is None:
        _engine = CuriosityEngine()
    return _engine


__all__ = [
    "CuriosityEngine",
    "CuriosityTrigger",
    "get_curiosity_engine",
]
