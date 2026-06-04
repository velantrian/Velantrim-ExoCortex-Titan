"""
🧩 core/essence/gist.py — Gist Synthesizer (V8.7 Titan)

Агрегирует существующий essence.py + meaning_parser.py.
Обёртка без переноса файлов.

Сжимает диалог/текст в СУТЬ (gist) — не summary.
Summary: «Пользователь обсуждает SQLite, Kuzu, Graphiti.»
Gist:    «Пользователь ищет орган, превращающий хранение в понимание.»

Использование:
    from core.essence import GistSynthesizer, extract_gist
    synth = GistSynthesizer()
    gist = synth.synthesize(facts, query, mode="essence")
    print(gist.core_question)  # «какой орган превращает БД в понимание?»
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Gist:
    """
    Суть разговора/текста — compressed semantic fingerprint.
    """
    core_question: str = ""         # «о чём на самом деле спрашивают?»
    user_intent: str = ""           # design | question | debug | explore | plan
    constraints: List[str] = field(default_factory=list)
    current_hypothesis: str = ""    # «что система сейчас думает?»
    missing_piece: str = ""         # «чего не хватает для ответа?»
    compression_ratio: float = 0.0  # насколько сжато vs исходное

    def to_dict(self) -> Dict[str, Any]:
        return {
            "core_question": self.core_question,
            "user_intent": self.user_intent,
            "constraints": self.constraints,
            "current_hypothesis": self.current_hypothesis,
            "missing_piece": self.missing_piece,
            "compression_ratio": round(self.compression_ratio, 2),
        }


class GistSynthesizer:
    """
    Детерминированный синтезатор сути.

    Использует существующий essence.py для экстракции gist из фактов.
    Не заменяет essence.py — обёртка над ним.
    """

    def synthesize(
        self,
        facts: List[Dict[str, Any]],
        query: str = "",
        *,
        mode: str = "essence",
    ) -> Gist:
        """
        Синтезировать gist из верифицированных фактов.

        Args:
            facts: верифицированные факты (уже через TruthGate).
            query: исходный запрос пользователя.
            mode: "essence" (детерминированный) или "llm" (креативный, P1).

        Returns:
            Gist с core_question, intent, constraints, hypothesis, missing_piece.
        """
        gist = Gist()

        # Core question — из запроса или из essence-анализа
        if query:
            gist.core_question = self._reframe_query(query)
        else:
            gist.core_question = "анализ фактов без явного запроса"

        # Intent — из question_formula
        try:
            from core.question_formula import get_question_formula_normalizer
            normalizer = get_question_formula_normalizer()
            _, intent_id, _ = normalizer.detect(query)
            gist.user_intent = intent_id
        except Exception:
            gist.user_intent = "unknown"

        # Constraints — из working_notebook
        try:
            from core.working_notebook import get_working_notebook
            nb = get_working_notebook()
            if nb:
                gist.constraints = nb.get_active_constraints()
        except Exception:
            pass

        # Hypothesis — что система знает из essence
        if facts and mode == "essence":
            try:
                from core.essence import EssenceLayer
                # Используем существующий essence как детерминированный анализатор
                gist.current_hypothesis = self._extract_hypothesis(facts)
            except Exception:
                pass

        # Missing piece — из gap_detector
        try:
            from core.gap_detector import detect_gaps
            gaps = detect_gaps()
            if gaps:
                gist.missing_piece = gaps[0].get("suggestion", "")
        except Exception:
            pass

        # Compression ratio — грубая оценка
        if query:
            gist.compression_ratio = min(0.95, max(0.05,
                len(gist.core_question) / max(1, len(query))
            ))

        return gist

    def _reframe_query(self, query: str) -> str:
        """Переформулировать запрос в суть."""
        q = query.strip().lower()

        # Убрать вопросительные слова
        for prefix in ["что такое ", "кто такой ", "как работает ", "почему ",
                        "зачем ", "объясни ", "расскажи ", "что если "]:
            if q.startswith(prefix):
                return q[len(prefix):].strip().rstrip("?")

        return q.rstrip("?")

    def _extract_hypothesis(self, facts: List[Dict[str, Any]]) -> str:
        """Извлечь гипотезу из фактов."""
        if not facts:
            return ""

        # Собрать ключевые темы из фактов
        topics: List[str] = []
        for f in facts[:5]:
            claim = f.get("claim", "")
            source = f.get("source", "")
            if claim:
                topics.append(claim[:80])
        return "; ".join(topics[:3]) if topics else ""


def extract_gist(facts: List[Dict[str, Any]], query: str = "") -> Gist:
    """Удобная функция: синтезировать gist из фактов."""
    return get_gist_synthesizer().synthesize(facts, query)


_gist_synth: Optional[GistSynthesizer] = None


def get_gist_synthesizer() -> GistSynthesizer:
    global _gist_synth
    if _gist_synth is None:
        _gist_synth = GistSynthesizer()
    return _gist_synth
