"""
🎯 core/question_formula.py — QuestionFormulaNormalizer (V8.7 Titan, из Claude Code L4,L5)

29 формул вопроса. Rule-based распознавание ПАТТЕРНА вопроса — без LLM, 0 токенов.

Определяет:
    1. formula_id   — qf001 (CLARIFY), qf004 (WHY), qf005 (HOW), qf006 (COMPARE), ...
    2. intent_id    — i001 (CLARIFY), i004 (WHY), i005 (HOW), i006 (COMPARE), ...
    3. depth        — SHALLOW / BASIC / INTERMEDIATE / DEEP / PRACTICAL
    4. strategy     — какая retrieval-стратегия нужна

Применение в pipeline:
    Перед retrieval → детектируем формулу → выбираем стратегию поиска.
    COMPARE → causal graph traversal. DEFINE → прямой поиск факта. HOW → процедурная память.

Инвариант:
    I-QF1: QuestionFormulaNormalizer — только классификация. Не влияет на truth_status.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ReasoningDepth(Enum):
    SHALLOW = "shallow"        # Быстрый ответ, 1 шаг
    BASIC = "basic"            # Определение + пример
    INTERMEDIATE = "intermediate"  # Объяснение + связи
    DEEP = "deep"              # Полный анализ
    PRACTICAL = "practical"    # Фокус на применении


@dataclass
class QuestionFormula:
    formula_id: str
    name: str
    patterns: List[str]           # ключевые слова/паттерны
    intent_id: str                # maps_to intent
    depth: ReasoningDepth = ReasoningDepth.BASIC
    strategy: str = "basic_lookup"  # retrieval strategy

    def matches(self, query: str) -> Tuple[bool, float]:
        """
        Проверить совпадение query с этой формулой.
        Returns: (matched, confidence 0..1)
        """
        q = query.lower().strip()
        for pattern in self.patterns:
            p = pattern.lower().replace("{x}", "").replace("{y}", "").strip()
            if p and p in q:
                confidence = min(len(p) / max(1, len(q)) * 1.5, 1.0)
                return True, confidence
        return False, 0.0


# ─── 29 Question Formulas ────────────────────────────────────────────────────

_QUESTION_FORMULAS: List[QuestionFormula] = [
    # ── CLARIFY / DEFINE ──────────────────────────────────────────────────
    QuestionFormula(
        "qf001", "CLARIFY",
        ["что такое", "кто такой", "что значит", "что означает",
         "дай определение", "определение", "что это", "who is", "what is"],
        "i001", ReasoningDepth.BASIC, "direct_lookup",
    ),
    QuestionFormula(
        "qf002", "EXPLAIN_SIMPLE",
        ["объясни просто", "расскажи просто", "объясни на пальцах",
         "для чайников", "простыми словами", "explain simply"],
        "i002", ReasoningDepth.BASIC, "direct_lookup",
    ),
    QuestionFormula(
        "qf003", "EXPLAIN_DETAILED",
        ["объясни подробно", "расскажи подробно", "explain in detail",
         "расскажи мне о", "что ты знаешь о"],
        "i003", ReasoningDepth.INTERMEDIATE, "graph_expansion",
    ),

    # ── WHY / CAUSE ────────────────────────────────────────────────────────
    QuestionFormula(
        "qf004", "WHY",
        ["почему", "зачем", "отчего", "в чём причина", "по какой причине",
         "why", "what causes"],
        "i004", ReasoningDepth.INTERMEDIATE, "causal_chain",
    ),
    QuestionFormula(
        "qf005", "WHY_NOT",
        ["почему не", "зачем не", "почему нельзя", "why can't",
         "why not", "что мешает", "почему невозможно"],
        "i005", ReasoningDepth.DEEP, "causal_chain",
    ),

    # ── HOW / METHOD ──────────────────────────────────────────────────────
    QuestionFormula(
        "qf006", "HOW",
        ["как", "каким образом", "каким способом", "способ",
         "метод", "how to", "how do", "как сделать"],
        "i006", ReasoningDepth.PRACTICAL, "procedural",
    ),
    QuestionFormula(
        "qf007", "HOW_WORKS",
        ["как работает", "принцип работы", "механизм", "как устроен",
         "how does it work", "how it works"],
        "i007", ReasoningDepth.INTERMEDIATE, "causal_chain",
    ),
    QuestionFormula(
        "qf008", "HOW_TO_ACHIEVE",
        ["как достичь", "как добиться", "как получить", "как стать",
         "how to achieve", "how to get", "как построить"],
        "i008", ReasoningDepth.PRACTICAL, "procedural",
    ),

    # ── COMPARE ───────────────────────────────────────────────────────────
    QuestionFormula(
        "qf009", "COMPARE",
        ["сравни", "отличие", "разница", "что лучше", "против",
         "vs", "versus", "сравнение", "compare", "difference"],
        "i009", ReasoningDepth.INTERMEDIATE, "graph_expansion",
    ),
    QuestionFormula(
        "qf010", "SIMILARITY",
        ["что общего", "похожи", "аналогичны", "сходство",
         "чем похожи", "similar", "common", "same as"],
        "i010", ReasoningDepth.INTERMEDIATE, "graph_expansion",
    ),

    # ── WHAT_IF / HYPOTHETICAL ────────────────────────────────────────────
    QuestionFormula(
        "qf011", "WHAT_IF",
        ["что если", "что будет если", "представь что", "а если",
         "допустим", "what if", "suppose", "imagine"],
        "i011", ReasoningDepth.DEEP, "counterfactual",
    ),
    QuestionFormula(
        "qf012", "PREDICT",
        ["предскажи", "спрогнозируй", "к чему приведёт", "каковы последствия",
         "predict", "forecast", "what will happen"],
        "i012", ReasoningDepth.DEEP, "predictive_fusion",
    ),

    # ── RELATION ──────────────────────────────────────────────────────────
    QuestionFormula(
        "qf013", "RELATION",
        ["как связано", "связь между", "взаимосвязь", "зависимость",
         "relationship", "connection", "как относится"],
        "i013", ReasoningDepth.INTERMEDIATE, "causal_chain",
    ),
    QuestionFormula(
        "qf014", "HIERARCHY",
        ["из чего состоит", "частью чего является", "что включает",
         "структура", "иерархия", "состоит из", "contains", "part of"],
        "i014", ReasoningDepth.BASIC, "graph_expansion",
    ),

    # ── CLASSIFY / TAXONOMY ───────────────────────────────────────────────
    QuestionFormula(
        "qf015", "CLASSIFY",
        ["классифицируй", "какие бывают", "виды", "типы", "категории",
         "разновидности", "classify", "types of", "kinds of"],
        "i015", ReasoningDepth.BASIC, "graph_expansion",
    ),

    # ── EXAMPLE ───────────────────────────────────────────────────────────
    QuestionFormula(
        "qf016", "EXAMPLE",
        ["пример", "приведи пример", "например", "покажи на примере",
         "example", "give an example", "для примера"],
        "i016", ReasoningDepth.BASIC, "direct_lookup",
    ),

    # ── RECALL / MEMORY ───────────────────────────────────────────────────
    QuestionFormula(
        "qf017", "RECALL",
        ["помнишь", "вспомни", "что я говорил", "мы обсуждали",
         "в прошлый раз", "do you remember", "recall", "what did I say"],
        "i017", ReasoningDepth.SHALLOW, "episodic",
    ),
    QuestionFormula(
        "qf018", "WHEN",
        ["когда", "в каком году", "в каком веке", "дата",
         "when", "what year", "what time"],
        "i018", ReasoningDepth.SHALLOW, "direct_lookup",
    ),

    # ── WHERE ─────────────────────────────────────────────────────────────
    QuestionFormula(
        "qf019", "WHERE",
        ["где", "в каком месте", "откуда", "куда",
         "where", "location", "place"],
        "i019", ReasoningDepth.SHALLOW, "direct_lookup",
    ),

    # ── DECIDE / CHOOSE ───────────────────────────────────────────────────
    QuestionFormula(
        "qf020", "DECIDE",
        ["выбери", "что выбрать", "какой вариант", "посоветуй",
         "рекомендуй", "стоит ли", "which", "choose", "recommend", "decision"],
        "i020", ReasoningDepth.INTERMEDIATE, "reasoning_bank",
    ),

    # ── EVALUATE ──────────────────────────────────────────────────────────
    QuestionFormula(
        "qf021", "EVALUATE",
        ["оцени", "насколько хорошо", "качество", "эффективность",
         "плюсы и минусы", "за и против", "evaluate", "assess", "pros and cons"],
        "i021", ReasoningDepth.DEEP, "reasoning_bank",
    ),

    # ── SUMMARIZE ─────────────────────────────────────────────────────────
    QuestionFormula(
        "qf022", "SUMMARIZE",
        ["суммируй", "кратко", "в двух словах", "резюмируй",
         "вывод", "итог", "summarize", "summary", "tldr", "brief"],
        "i022", ReasoningDepth.SHALLOW, "direct_lookup",
    ),

    # ── DEBATE / ARGUE ────────────────────────────────────────────────────
    QuestionFormula(
        "qf023", "DEBATE",
        ["докажи", "обоснуй", "аргументируй", "почему ты так думаешь",
         "убеди", "prove", "justify", "argue"],
        "i023", ReasoningDepth.DEEP, "evidence_chain",
    ),

    # ── FIX / DEBUG ───────────────────────────────────────────────────────
    QuestionFormula(
        "qf024", "FIX",
        ["исправь", "почини", "ошибка", "не работает", "баг",
         "fix", "debug", "bug", "error", "broken"],
        "i024", ReasoningDepth.PRACTICAL, "procedural",
    ),

    # ── OPTIMIZE ──────────────────────────────────────────────────────────
    QuestionFormula(
        "qf025", "OPTIMIZE",
        ["оптимизируй", "улучши", "ускорь", "сделай быстрее",
         "optimize", "improve", "speed up", "performance"],
        "i025", ReasoningDepth.PRACTICAL, "reasoning_bank",
    ),

    # ── CREATE / GENERATE ─────────────────────────────────────────────────
    QuestionFormula(
        "qf026", "CREATE",
        ["создай", "напиши", "сгенерируй", "сделай", "построй",
         "create", "generate", "build", "write", "make"],
        "i026", ReasoningDepth.PRACTICAL, "procedural",
    ),

    # ── TRANSLATE ─────────────────────────────────────────────────────────
    QuestionFormula(
        "qf027", "TRANSLATE",
        ["переведи", "перевод", "на русский", "на английский",
         "translate", "translation", "in english", "in russian"],
        "i027", ReasoningDepth.SHALLOW, "direct_lookup",
    ),

    # ── CHAT / GREETING ───────────────────────────────────────────────────
    QuestionFormula(
        "qf028", "CHAT",
        ["привет", "здравствуй", "как дела", "спасибо", "пока",
         "hello", "hi", "how are you", "thanks", "bye", "good morning"],
        "i028", ReasoningDepth.SHALLOW, "none",
    ),

    # ── UNKNOWN / COMPLEX ─────────────────────────────────────────────────
    QuestionFormula(
        "qf029", "COMPLEX",
        [],  # fallback — не имеет паттернов
        "i029", ReasoningDepth.INTERMEDIATE, "hybrid",
    ),
]


# ─── Стратегии retrieval → pipeline hint ──────────────────────────────────────

_STRATEGY_HINTS: Dict[str, Dict[str, str]] = {
    "direct_lookup": {
        "retrieval_k": "3",
        "use_causal": "false",
        "use_ego": "false",
        "description": "Прямой поиск фактов",
    },
    "graph_expansion": {
        "retrieval_k": "8",
        "use_causal": "true",
        "use_ego": "true",
        "description": "Расширение графа вокруг фактов",
    },
    "causal_chain": {
        "retrieval_k": "5",
        "use_causal": "true",
        "use_ego": "true",
        "description": "Поиск причинно-следственных цепочек",
    },
    "counterfactual": {
        "retrieval_k": "5",
        "use_causal": "true",
        "use_ego": "false",
        "description": "Контрфактуальный анализ",
    },
    "procedural": {
        "retrieval_k": "5",
        "use_causal": "false",
        "use_ego": "false",
        "description": "Поиск процедур и методов (PROCEDURAL память)",
    },
    "episodic": {
        "retrieval_k": "10",
        "use_causal": "false",
        "use_ego": "false",
        "description": "Поиск в эпизодической памяти",
    },
    "evidence_chain": {
        "retrieval_k": "7",
        "use_causal": "true",
        "use_ego": "true",
        "description": "Построение цепочки доказательств",
    },
    "reasoning_bank": {
        "retrieval_k": "7",
        "use_causal": "true",
        "use_ego": "false",
        "description": "Консультация ReasoningBank (стратегии)",
    },
    "predictive_fusion": {
        "retrieval_k": "5",
        "use_causal": "true",
        "use_ego": "true",
        "description": "PredictiveFusion SAE+LSM",
    },
    "hybrid": {
        "retrieval_k": "7",
        "use_causal": "true",
        "use_ego": "true",
        "description": "Гибридный поиск (все источники)",
    },
    "basic_lookup": {
        "retrieval_k": "3",
        "use_causal": "false",
        "use_ego": "false",
        "description": "Базовый поиск",
    },
    "none": {
        "retrieval_k": "0",
        "use_causal": "false",
        "use_ego": "false",
        "description": "Без retrieval (чат/приветствие)",
    },
}


# ─── Главный класс ────────────────────────────────────────────────────────────

class QuestionFormulaNormalizer:
    """
    Распознаватель паттерна вопроса из 29 формул.

    Использование:
        normalizer = QuestionFormulaNormalizer()

        formula, intent, confidence = normalizer.detect("почему вода кипит при 100°C?")
        # → ("qf004", "i004", 0.65) — WHY, causal_chain

        strategy = normalizer.get_strategy("i004")
        # → "causal_chain"

        hints = normalizer.get_retrieval_hints("i004")
        # → {"retrieval_k": "5", "use_causal": "true", "use_ego": "true"}
    """

    _FALLBACK_FORMULA_ID = "qf029"
    _FALLBACK_INTENT_ID = "i029"

    def __init__(self) -> None:
        self._formulas: Dict[str, QuestionFormula] = {
            f.formula_id: f for f in _QUESTION_FORMULAS
        }

    def detect(self, query: str) -> Tuple[str, str, float]:
        """
        Определить формулу вопроса.

        Returns: (formula_id, intent_id, confidence 0..1)
        """
        if not query or not query.strip():
            return self._FALLBACK_FORMULA_ID, self._FALLBACK_INTENT_ID, 0.0

        best_formula: Optional[QuestionFormula] = None
        best_confidence = 0.0

        for formula in _QUESTION_FORMULAS:
            matched, confidence = formula.matches(query)
            if matched and confidence > best_confidence:
                best_confidence = confidence
                best_formula = formula

        if best_formula and best_confidence > 0.0:
            return best_formula.formula_id, best_formula.intent_id, round(best_confidence, 2)

        # Fallback: эвристики
        return self._fallback_detect(query) or (
            self._FALLBACK_FORMULA_ID, self._FALLBACK_INTENT_ID, 0.2
        )

    def _fallback_detect(self, query: str) -> Optional[Tuple[str, str, float]]:
        """Эвристическое определение когда точный паттерн не найден."""
        q = query.lower().strip()

        if q.startswith(("что ", "кто ", "какой ", "какая ", "какие ")):
            return ("qf001", "i001", 0.4)
        if q.startswith(("почему ", "зачем ", "отчего ")):
            return ("qf004", "i004", 0.4)
        if q.startswith(("как ", "каким образом ")):
            return ("qf005", "i005", 0.4)
        if "сравни" in q or "отличие" in q or "разница" in q:
            return ("qf009", "i009", 0.4)
        if "объясни" in q or "расскажи" in q:
            if "просто" in q or "понятно" in q:
                return ("qf002", "i002", 0.45)
            return ("qf003", "i003", 0.4)
        if "пример" in q:
            return ("qf016", "i016", 0.35)

        return None

    def get_formula(self, formula_id: str) -> Optional[QuestionFormula]:
        return self._formulas.get(formula_id)

    def get_strategy(self, intent_id: str) -> str:
        """Получить retrieval-стратегию для intent."""
        formula = next(
            (f for f in _QUESTION_FORMULAS if f.intent_id == intent_id),
            None,
        )
        return formula.strategy if formula else "basic_lookup"

    def get_depth(self, intent_id: str) -> ReasoningDepth:
        """Глубина reasoning для intent."""
        formula = next(
            (f for f in _QUESTION_FORMULAS if f.intent_id == intent_id),
            None,
        )
        return formula.depth if formula else ReasoningDepth.BASIC

    def get_retrieval_hints(self, intent_id: str) -> Dict[str, str]:
        """
        Подсказки для pipeline: какой retrieval_k, использовать ли causal graph,
        нужно ли ego_net_expand.

        Использование в pipeline.py:
            hints = normalizer.get_retrieval_hints(intent_id)
            k = int(hints["retrieval_k"])
            use_causal = hints["use_causal"] == "true"
        """
        strategy = self.get_strategy(intent_id)
        return _STRATEGY_HINTS.get(strategy, _STRATEGY_HINTS["basic_lookup"])

    def list_formulas(self) -> List[Dict[str, str]]:
        """Список всех 29 формул (для API/консоли)."""
        return [
            {
                "id": f.formula_id,
                "name": f.name,
                "intent": f.intent_id,
                "depth": f.depth.value,
                "strategy": f.strategy,
                "patterns": f.patterns[:5],
            }
            for f in _QUESTION_FORMULAS
        ]


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_normalizer: Optional[QuestionFormulaNormalizer] = None


def get_question_formula_normalizer() -> QuestionFormulaNormalizer:
    global _normalizer
    if _normalizer is None:
        _normalizer = QuestionFormulaNormalizer()
    return _normalizer


__all__ = [
    "QuestionFormulaNormalizer",
    "QuestionFormula",
    "ReasoningDepth",
    "get_question_formula_normalizer",
]
