"""
🎭 core/perspectives.py — Multi-Perspective Reasoning Roles (V8.7 Titan)

7 встроенных ролей. Каждая — стратегия retrieval + стиль ответа + фокус.

По умолчанию: 3 роли параллельно (engineer + analyst + critic) → синтез.
Опционально: одна роль → ответ в её стиле.

Роли:
    ENGINEER    — инженер: материал, нагрузка, нормы, безопасность, практическое применение
    SCIENTIST   — учёный: гипотезы, экосистема, измерение, валидация
    ANALYST     — аналитик: данные, метрики, сравнение, причинность
    CRITIC      — критик: риски, слабые места, противоречия, что может пойти не так
    ADVISOR     — советник: рекомендации, лучшие практики, что делать
    FRIEND      — друг: поддерживающий тон, простые слова, человеческий подход
    PHILOSOPHER — философ: суть, смысл, метафора, принципы, этика

Инвариант:
    I-PR1: Роль меняет ТОЛЬКО retrieval + prompt. Не влияет на truth_status.
    I-PR2: По умолчанию — 3 роли параллельно, синтез лучшего.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PerspectiveRole:
    role_id: str
    label_ru: str
    emoji: str
    focus: str           # что для этой роли важно
    retrieval_hints: Dict[str, str]  # подсказки для hybrid_retriever
    prompt_modifier: str  # добавка в system prompt
    priority: int = 5     # приоритет при синтезе (чем выше, тем весомее голос)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "label_ru": self.label_ru,
            "emoji": self.emoji,
            "focus": self.focus,
            "retrieval_hints": self.retrieval_hints,
            "priority": self.priority,
        }


# ─── 7 ВСТРОЕННЫХ РОЛЕЙ ──────────────────────────────────────────────────────

PERSPECTIVE_ROLES: Dict[str, PerspectiveRole] = {

    "ENGINEER": PerspectiveRole(
        role_id="ENGINEER",
        label_ru="Инженер",
        emoji="👷",
        focus="Материал, нагрузка, нормы, безопасность, применение на практике",
        retrieval_hints={
            "retrieval_k": "4",
            "use_causal": "true",
            "use_ego": "false",
            "prefer_memory_type": "procedural",
            "prefer_axis": "ENGINEERING",
        },
        prompt_modifier=(
            "Ты — инженер. Отвечай с практической точки зрения. "
            "Что можно построить? Какие материалы использовать? "
            "Какие нагрузки выдержит? Как это применить в реальном проекте? "
            "Будь конкретен. Избегай абстрактных рассуждений."
        ),
        priority=8,
    ),

    "SCIENTIST": PerspectiveRole(
        role_id="SCIENTIST",
        label_ru="Учёный",
        emoji="🔬",
        focus="Гипотезы, экосистема, измерение, валидация, научный метод",
        retrieval_hints={
            "retrieval_k": "6",
            "use_causal": "true",
            "use_ego": "true",
            "prefer_memory_type": "semantic",
            "prefer_axis": "SYSTEMIC",
        },
        prompt_modifier=(
            "Ты — учёный. Рассматривай вопрос с научной точки зрения. "
            "Какие есть гипотезы? Что говорят исследования? "
            "Какие измерения можно провести? Где границы текущего знания? "
            "Будь точен. Указывай степень уверенности."
        ),
        priority=7,
    ),

    "ANALYST": PerspectiveRole(
        role_id="ANALYST",
        label_ru="Аналитик",
        emoji="📊",
        focus="Данные, метрики, сравнение, причинность, паттерны",
        retrieval_hints={
            "retrieval_k": "7",
            "use_causal": "true",
            "use_ego": "true",
            "prefer_memory_type": "semantic",
            "prefer_axis": "SPATIAL",
        },
        prompt_modifier=(
            "Ты — аналитик. Разбери вопрос на составляющие. "
            "Сравни варианты. Найди закономерности. "
            "Где данные подтверждают вывод? Где — противоречат? "
            "Дай структурированный ответ с явными критериями."
        ),
        priority=7,
    ),

    "CRITIC": PerspectiveRole(
        role_id="CRITIC",
        label_ru="Критик",
        emoji="⚔️",
        focus="Риски, слабые места, противоречия, что может пойти не так",
        retrieval_hints={
            "retrieval_k": "5",
            "use_causal": "true",
            "use_ego": "false",
            "prefer_memory_type": "semantic",
            "prefer_axis": "ENGINEERING",
        },
        prompt_modifier=(
            "Ты — критик. Найди слабые места в рассуждении. "
            "Что может пойти не так? Какие риски не учтены? "
            "Где логика ломается? Что противоречит已知ным фактам? "
            "Будь конструктивен — критика ради улучшения, не ради разрушения."
        ),
        priority=6,
    ),

    "ADVISOR": PerspectiveRole(
        role_id="ADVISOR",
        label_ru="Советник",
        emoji="🧭",
        focus="Рекомендации, лучшие практики, что делать, стратегия",
        retrieval_hints={
            "retrieval_k": "5",
            "use_causal": "false",
            "use_ego": "false",
            "prefer_memory_type": "procedural",
            "prefer_axis": "SYSTEMIC",
        },
        prompt_modifier=(
            "Ты — советник. Дай практическую рекомендацию. "
            "Что делать в этой ситуации? Какие есть варианты действий? "
            "Какой вариант лучше и почему? "
            "Будь полезен. Дай конкретный план."
        ),
        priority=7,
    ),

    "FRIEND": PerspectiveRole(
        role_id="FRIEND",
        label_ru="Друг",
        emoji="🤝",
        focus="Поддержка, простые слова, человеческий подход, эмпатия",
        retrieval_hints={
            "retrieval_k": "3",
            "use_causal": "false",
            "use_ego": "false",
            "prefer_memory_type": "episodic",
            "prefer_axis": "SOCIAL",
        },
        prompt_modifier=(
            "Ты — друг. Говори по-человечески. Простыми словами. "
            "Поддержи. Пойми что человек чувствует. "
            "Не лезь в технические детали если не просят. "
            "Будь тёплым, но честным."
        ),
        priority=5,
    ),

    "PHILOSOPHER": PerspectiveRole(
        role_id="PHILOSOPHER",
        label_ru="Философ",
        emoji="🏛️",
        focus="Суть, смысл, метафора, принципы, этика, глубина",
        retrieval_hints={
            "retrieval_k": "5",
            "use_causal": "true",
            "use_ego": "true",
            "prefer_memory_type": "semantic",
            "prefer_axis": "SYSTEMIC",
        },
        prompt_modifier=(
            "Ты — философ. Смотри в суть. "
            "Почему это важно? Какой в этом смысл? "
            "Какие принципы здесь работают? Что об этом говорит мудрость? "
            "Дай метафору. Покажи связь с большим."
        ),
        priority=5,
    ),

    "CREATIVE": PerspectiveRole(
        role_id="CREATIVE",
        label_ru="Творец",
        emoji="🎨",
        focus="Метафоры, аналогии, нестандартные связи, воображение, красота",
        retrieval_hints={
            "retrieval_k": "6",
            "use_causal": "true",
            "use_ego": "true",
            "prefer_memory_type": "semantic",
            "prefer_axis": "SYSTEMIC",
        },
        prompt_modifier=(
            "Ты — творец. Мысли нестандартно. "
            "Найди красивую аналогию. Свяжи несвязанное. "
            "Дай метафору которая запомнится. "
            "Разреши себе быть поэтичным. Но не теряй смысл за красотой."
        ),
        priority=5,
    ),

    "CHILD": PerspectiveRole(
        role_id="CHILD",
        label_ru="Ребёнок",
        emoji="🌟",
        focus="Простота, удивление, базовые вопросы, игра, честность",
        retrieval_hints={
            "retrieval_k": "3",
            "use_causal": "false",
            "use_ego": "false",
            "prefer_memory_type": "semantic",
            "prefer_axis": "SOCIAL",
        },
        prompt_modifier=(
            "Ты — ребёнок. Объясни так, чтобы понял пятилетний. "
            "Простыми словами. С удивлением и радостью. "
            "Если сложно — скажи честно «я не понимаю, объясни проще». "
            "Никаких терминов. Только суть. Как будто рассказываешь другу на площадке."
        ),
        priority=4,
    ),
}


# ─── Конфигурации по умолчанию ────────────────────────────────────────────────

# По умолчанию: инженер + аналитик + критик
DEFAULT_TRIAD = ["ANALYST", "ENGINEER", "CRITIC"]

# Для сложных вопросов: учёный + аналитик + философ
DEEP_TRIAD = ["SCIENTIST", "ANALYST", "PHILOSOPHER"]

# Для практических: инженер + советник + критик
PRACTICAL_TRIAD = ["ENGINEER", "ADVISOR", "CRITIC"]

# Для творческих: творец + философ + аналитик
CREATIVE_TRIAD = ["CREATIVE", "PHILOSOPHER", "ANALYST"]

# Для объяснения простым языком: ребёнок + друг
SIMPLE_DUO = ["CHILD", "FRIEND"]


# ─── API ──────────────────────────────────────────────────────────────────────

def get_role(role_id: str) -> Optional[PerspectiveRole]:
    """Получить роль по ID. Регистро-независимо."""
    return PERSPECTIVE_ROLES.get(role_id.upper())


def list_roles() -> List[Dict[str, Any]]:
    """Список всех ролей для API/консоли."""
    return [
        {"role_id": r.role_id, "label_ru": r.label_ru, "emoji": r.emoji, "focus": r.focus}
        for r in PERSPECTIVE_ROLES.values()
    ]


def get_default_roles() -> List[PerspectiveRole]:
    """Роли по умолчанию: аналитик + инженер + критик."""
    return [PERSPECTIVE_ROLES[r] for r in DEFAULT_TRIAD if r in PERSPECTIVE_ROLES]


def get_roles_for_query(query: str) -> List[PerspectiveRole]:
    """
    Автоматически выбрать роли по запросу.

    Эвристика (0 токенов LLM):
        - «как сделать» / «построить» → инженер + советник
        - «почему» / «причина» → учёный + аналитик
        - «что если» / «представь» → философ + аналитик
        - «посоветуй» / «выбрать» → советник + аналитик + критик
        - «проблема» / «ошибка» / «не работает» → инженер + критик
        - эмоциональный запрос → друг + советник
        - default → аналитик + инженер + критик
    """
    q = query.lower().strip()

    if any(w in q for w in ["как сделать", "построить", "создать", "реализовать",
                              "how to build", "implement", "create"]):
        return [PERSPECTIVE_ROLES["ENGINEER"], PERSPECTIVE_ROLES["ADVISOR"]]

    if any(w in q for w in ["почему", "причина", "отчего", "why", "cause"]):
        return [PERSPECTIVE_ROLES["SCIENTIST"], PERSPECTIVE_ROLES["ANALYST"]]

    if any(w in q for w in ["что если", "представь", "а если", "what if", "imagine"]):
        return [PERSPECTIVE_ROLES["PHILOSOPHER"], PERSPECTIVE_ROLES["ANALYST"]]

    if any(w in q for w in ["творчески", "креативно", "придумай", "сочини", "метафору",
                              "creative", "metaphor", "imagine", "poem", "стих"]):
        return [PERSPECTIVE_ROLES["CREATIVE"], PERSPECTIVE_ROLES["PHILOSOPHER"]]

    if any(w in q for w in ["объясни просто", "для ребёнка", "для чайников", "на пальцах",
                              "простым языком", "как ребёнку", "explain simply", "eli5",
                              "как пятилетнему"]):
        return [PERSPECTIVE_ROLES["CHILD"], PERSPECTIVE_ROLES["FRIEND"]]

    if any(w in q for w in ["посоветуй", "выбрать", "рекомендуй", "advise", "recommend", "choose"]):
        return [PERSPECTIVE_ROLES["ADVISOR"], PERSPECTIVE_ROLES["ANALYST"], PERSPECTIVE_ROLES["CRITIC"]]

    if any(w in q for w in ["проблема", "ошибка", "не работает", "баг", "сломалось",
                              "problem", "error", "bug", "broken", "issue"]):
        return [PERSPECTIVE_ROLES["ENGINEER"], PERSPECTIVE_ROLES["CRITIC"]]

    if any(w in q for w in ["чувствую", "грустно", "страшно", "одиноко", "радостно",
                              "feel", "sad", "scared", "lonely", "happy"]):
        return [PERSPECTIVE_ROLES["FRIEND"], PERSPECTIVE_ROLES["ADVISOR"]]

    # Default triad
    return [PERSPECTIVE_ROLES[r] for r in DEFAULT_TRIAD if r in PERSPECTIVE_ROLES]


def resolve_roles(
    query: str,
    *,
    requested_roles: Optional[List[str]] = None,
) -> List[PerspectiveRole]:
    """
    Определить какие роли использовать.

    Приоритет:
        1. Явно запрошенные роли (requested_roles)
        2. Авто-определение по запросу (get_roles_for_query)

    Returns:
        Список из 1-3 ролей.
    """
    if requested_roles:
        roles = []
        for rid in requested_roles[:3]:
            role = get_role(rid)
            if role:
                roles.append(role)
        if roles:
            return roles

    return get_roles_for_query(query)


__all__ = [
    "CREATIVE_TRIAD",
    "DEFAULT_TRIAD",
    "DEEP_TRIAD",
    "LIGHT_DUO",
    "PERSPECTIVE_ROLES",
    "PRACTICAL_TRIAD",
    "SIMPLE_DUO",
    "PerspectiveRole",
    "get_default_roles",
    "get_role",
    "get_roles_for_query",
    "list_roles",
    "resolve_roles",
]
