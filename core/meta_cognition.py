"""
🧘 core/meta_cognition.py — Meta-Cognitive Loop (V8.7 Titan)

Рефлексия о ПРОЦЕССЕ мышления, а не только о результате.
Не «правильный ли ответ» — а «правильный ли ПУТЬ к ответу».

После генерации ответа (Slow Path):
    1. БЫЛ ЛИ ПУТЬ ОПТИМАЛЬНЫМ? Можно было ответить из L0 без retrieval?
    2. ПОНИМАЕТ ЛИ СИСТЕМА ГЛУБИНУ? Ответ поверхностный или глубокий?
    3. ЧТО Я НЕ ЗНАЮ? Какие пробелы помешали полному ответу?

Инварианты:
    I-MC1: Meta-Cognitive Loop — только Slow Path. Не блокирует ответ.
    I-MC2: Не меняет факты. Только предоставляет рекомендации.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.meta_cognition")


@dataclass
class MetaCognitiveReport:
    """Результат мета-когнитивного анализа."""
    query: str
    facts_used: int

    # Оценки
    was_retrieval_needed: bool = True       # можно было ответить без retrieval?
    was_depth_adequate: bool = True          # глубина ответа соответствует запросу?
    was_path_optimal: bool = True            # оптимальный ли путь выбран?

    # Пробелы
    knowledge_gaps: List[str] = field(default_factory=list)
    suggested_curiosity: List[str] = field(default_factory=list)

    # Рекомендации
    recommendations: List[str] = field(default_factory=list)
    surface_level_warning: bool = False      # ответ поверхностный
    overthinking_warning: bool = False       # переусложнение

    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query[:200],
            "facts_used": self.facts_used,
            "retrieval_needed": self.was_retrieval_needed,
            "depth_adequate": self.was_depth_adequate,
            "path_optimal": self.was_path_optimal,
            "knowledge_gaps": self.knowledge_gaps[:5],
            "suggested_curiosity": self.suggested_curiosity[:3],
            "recommendations": self.recommendations[:5],
            "surface_warning": self.surface_level_warning,
            "overthinking_warning": self.overthinking_warning,
        }


class MetaCognitiveLoop:
    """
    Цикл мета-когнитивной рефлексии.

    Вызывается ПОСЛЕ генерации ответа.
    Анализирует процесс и даёт рекомендации на будущее.
    """

    def reflect(
        self,
        query: str,
        facts: List[Dict[str, Any]],
        response: str,
        *,
        intent: Optional[str] = None,
        depth: Optional[str] = None,
    ) -> MetaCognitiveReport:
        """
        Проанализировать процесс мышления.

        Args:
            query: исходный запрос.
            facts: использованные факты.
            response: сгенерированный ответ.
            intent: определённый intent (из question_formula).
            depth: выбранная глубина reasoning.
        """
        report = MetaCognitiveReport(
            query=query,
            facts_used=len(facts),
        )

        # 1. Нужен ли был retrieval?
        ql = query.lower().strip()
        self_check_keywords = ["привет", "как дела", "спасибо", "пока", "hello", "hi", "thanks", "bye"]
        if any(ql.startswith(w) for w in self_check_keywords) or len(ql) < 5:
            if len(facts) > 0:
                report.was_retrieval_needed = False
                report.recommendations.append("Запрос-приветствие не требовал retrieval. Можно отвечать из L0/CoreMemoryBlocks.")
                report.overthinking_warning = True

        # 2. Поверхностный ответ?
        if len(response) < 50 and len(facts) >= 3:
            report.was_depth_adequate = False
            report.surface_level_warning = True
            report.recommendations.append(f"Ответ поверхностный ({len(response)} символов) при {len(facts)} фактах. Возможно стоило использовать causal_chain вместо direct_lookup.")

        # 3. Слишком сложный путь для простого запроса?
        if len(facts) > 10 and len(query) < 30:
            report.was_path_optimal = False
            report.overthinking_warning = True
            report.recommendations.append(f"Переусложнение: {len(facts)} фактов для короткого запроса. Попробовать k=3 вместо k=10.")

        # 4. Пробелы в знаниях
        if len(facts) < 3:
            report.knowledge_gaps.append(f"Мало фактов ({len(facts)}) для ответа на '{query[:60]}'")
            report.suggested_curiosity.append(f"Исследовать тему: {query[:60]}")

        # 5. Несовпадение intent и глубины
        if intent and depth:
            deep_intents = {"i004", "i007", "i011", "i012", "i023"}  # WHY, HOW_WORKS, WHAT_IF, PREDICT, DEBATE
            if intent in deep_intents and depth in ("shallow", "basic"):
                report.was_depth_adequate = False
                report.recommendations.append(f"Intent={intent} требует глубокого анализа, использована глубина={depth}.")

        logger.debug("MetaCognitive: %s facts=%d depth_ok=%s path_ok=%s", query[:40], len(facts), report.was_depth_adequate, report.was_path_optimal)
        return report


# Глобальный экземпляр
_loop: Optional[MetaCognitiveLoop] = None


def get_meta_cognitive_loop() -> MetaCognitiveLoop:
    global _loop
    if _loop is None:
        _loop = MetaCognitiveLoop()
    return _loop


__all__ = ["MetaCognitiveLoop", "MetaCognitiveReport", "get_meta_cognitive_loop"]
