"""
Консоль: категории долгой памяти, извлечение фактов из текста, гайд для LLM.
"""

from __future__ import annotations

import re
from typing import Any

# id → emoji, ru label, en label
MEMORY_CATEGORIES: dict[str, dict[str, str]] = {
    "personal": {"emoji": "🧑", "ru": "Личное", "en": "Personal"},
    "family": {"emoji": "👨‍👩‍👧", "ru": "Родные", "en": "Family"},
    "work": {"emoji": "💼", "ru": "Работа", "en": "Work"},
    "project": {"emoji": "📁", "ru": "Проекты", "en": "Projects"},
    "date": {"emoji": "📅", "ru": "Даты", "en": "Dates"},
    "contact": {"emoji": "📇", "ru": "Контакты", "en": "Contact"},
    "health": {"emoji": "🩺", "ru": "Здоровье", "en": "Health"},
    "preference": {"emoji": "⭐", "ru": "Предпочтения", "en": "Preferences"},
    "general": {"emoji": "💾", "ru": "Память", "en": "Memory"},
}

_CATEGORY_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "family",
        re.compile(
            r"(мама|папа|отец|мать|брат|сестра|жена|муж|сын|дочь|"
            r"mother|father|wife|husband|son|daughter|sibling|relative)",
            re.I,
        ),
    ),
    (
        "work",
        re.compile(
            r"(работаю|работал|компани|должност|офис|коллег|"
            r"work at|employer|company|job title|карьер)",
            re.I,
        ),
    ),
    (
        "project",
        re.compile(r"(проект|project|стартап|startup|репозитор|repository)", re.I),
    ),
    (
        "date",
        re.compile(
            r"(день рождения|родился|родилась|birthday|born on|"
            r"\d{1,2}[./]\d{1,2}[./]\d{2,4}|завтра|послезавтра)",
            re.I,
        ),
    ),
    (
        "contact",
        re.compile(
            r"(@[\w.-]+|\+\d{10,}|tel:|phone|email|почта|телефон|telegram)",
            re.I,
        ),
    ),
    (
        "personal",
        re.compile(
            r"(меня зовут|моё имя|мое имя|my name is|i am called|фамилия|surname)",
            re.I,
        ),
    ),
    (
        "health",
        re.compile(r"(аллерг|болею|диагноз|лекарств|allergy|diagnosis)", re.I),
    ),
    (
        "preference",
        re.compile(r"(люблю|не люблю|предпочитаю|prefer|favorite|нравится)", re.I),
    ),
]

_EXPLICIT_REMEMBER = re.compile(
    r"(?:запомни(?:те)?|remember|сохрани в память|save to memory|запомнить)"
    r"(?:\s+(?:что|that))?\s*[:\-—]?\s*(.+)",
    re.I | re.S,
)

# Короткие факты: «зовут Иван», «ДР 12 мая»
_SHORT_FACT = re.compile(
    r"(?:меня зовут|моё имя|мое имя|my name is|фамилия|surname|"
    r"день рождения|birthday|родился|родилась|мне \d{1,3} лет|"
    r"работаю в|i work at|живу в|i live in|мой email|my email|"
    r"я из |i'm from|i am from|мой телефон|my phone|любимый цвет|favorite)",
    re.I,
)

_CLAUSE_SPLIT = re.compile(r"[.!?\n;]+")


def category_label(category: str, lang: str = "ru") -> str:
    meta = MEMORY_CATEGORIES.get(category) or MEMORY_CATEGORIES["general"]
    return meta["en" if lang == "en" else "ru"]


def category_emoji(category: str) -> str:
    meta = MEMORY_CATEGORIES.get(category) or MEMORY_CATEGORIES["general"]
    return meta["emoji"]


def classify_fact(claim: str) -> str:
    text = (claim or "").strip()
    if not text:
        return "general"
    for cat, pat in _CATEGORY_PATTERNS:
        if pat.search(text):
            return cat
    return "general"


def _normalize_claim(text: str) -> str:
    s = " ".join((text or "").split())
    return s[:500] if len(s) > 500 else s


def _dedup_key(text: str) -> str:
    from core.fact_integrity import normalize_claim_for_dedup

    return normalize_claim_for_dedup(text) or (text or "").strip().lower()


def extract_memory_candidates(message: str) -> list[dict[str, Any]]:
    """
    Эвристическое извлечение долгих фактов из сообщения пользователя.
  Возвращает [{claim, category, emoji, confidence, reason}, ...]
    """
    raw = (message or "").strip()
    if len(raw) < 4:
        return []

    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(claim: str, confidence: float, reason: str) -> None:
        c = _normalize_claim(claim)
        min_len = 3 if reason == "explicit_remember" else 5
        if len(c) < min_len:
            return
        key = _dedup_key(c)
        if not key or key in seen:
            return
        seen.add(key)
        cat = classify_fact(c)
        out.append(
            {
                "claim": c,
                "category": cat,
                "emoji": category_emoji(cat),
                "confidence": round(min(1.0, max(0.0, confidence)), 2),
                "reason": reason,
            }
        )

    m = _EXPLICIT_REMEMBER.search(raw)
    if m:
        add(m.group(1).strip(), 0.95, "explicit_remember")
        # An explicit remember command is already the user's consolidation
        # instruction. Re-scanning the same message as generic clauses can
        # create a second near-duplicate candidate (for example when the
        # remembered statement also matches the project category). Treat the
        # explicit payload as the authoritative candidate for this message.
        return out[:8]

    if _SHORT_FACT.search(raw) and len(raw) >= 5:
        add(raw, 0.88, "short_fact_pattern")

    for part in _CLAUSE_SPLIT.split(raw):
        part = part.strip()
        if len(part) < 8:
            continue
        cat = classify_fact(part)
        if cat != "general":
            add(part, 0.85, f"pattern_{cat}")
        elif _SHORT_FACT.search(part):
            add(part, 0.84, "short_fact_clause")
        elif re.search(
            r"(всегда|никогда|важно|important|never forget|навсегда|"
            r"не забудь|don't forget)",
            part,
            re.I,
        ):
            add(part, 0.78, "importance_marker")

    return out[:8]


def fact_to_highlight(fact: dict[str, Any], lang: str = "ru") -> dict[str, Any]:
    claim = fact.get("claim") or ""
    cat = classify_fact(claim)
    meta = fact.get("metadata") or {}
    if isinstance(meta, str):
        try:
            import json

            meta = json.loads(meta)
        except Exception:
            meta = {}
    cat = meta.get("memory_category") or cat
    return {
        "fact_id": fact.get("fact_id", ""),
        "claim": claim,
        "category": cat,
        "emoji": category_emoji(cat),
        "category_label": category_label(cat, lang),
        "source": fact.get("source", ""),
        "confidence": float(fact.get("confidence") or 0),
        "epistemic_state": fact.get("epistemic_state", ""),
    }


def build_block_memory_for_prompt(
    block_memory: list[dict[str, Any]] | None,
    lang: str = "ru",
) -> str:
    """Блок временной памяти (консоль, не POST /facts)."""
    if not block_memory:
        return ""
    lines: list[str] = []
    for item in block_memory[:40]:
        claim = " ".join((item.get("claim") or "").split())
        if not claim:
            continue
        cat = (item.get("category_label") or item.get("category") or "").strip()
        lines.append(f"• [{cat}] {claim}" if cat else f"• {claim}")
    if not lines:
        return ""
    if lang == "en":
        return (
            "MEMORY BLOCK (user notes — always consider; separate from long-term DB):\n"
            + "\n".join(lines)
        )
    return (
        "БЛОК ПАМЯТИ (заметки пользователя — всегда учитывай; отдельно от долгой БД):\n"
        + "\n".join(lines)
    )


def build_chat_context_for_prompt(
    history: list[dict[str, Any]] | None,
    previous_summary: str | None,
    lang: str = "ru",
    block_memory: list[dict[str, Any]] | None = None,
) -> str:
    """Блок контекста диалога для system prompt."""
    parts: list[str] = []
    block_ctx = build_block_memory_for_prompt(block_memory, lang)
    if block_ctx:
        parts.append(block_ctx)
    if previous_summary and previous_summary.strip():
        if lang == "en":
            parts.append(
                "PREVIOUS CHAT (user started a new session; keep continuity):\n"
                + previous_summary.strip()[:4000]
            )
        else:
            parts.append(
                "ПРЕДЫДУЩИЙ ЧАТ (пользователь открыл новую сессию; сохраняй связность):\n"
                + previous_summary.strip()[:4000]
            )
    if history:
        lines: list[str] = []
        for turn in history[-20:]:
            role = (turn.get("role") or "user").lower()
            content = " ".join((turn.get("content") or "").split())[:600]
            if not content:
                continue
            if lang == "en":
                label = "User" if role == "user" else "Assistant"
            else:
                label = "Пользователь" if role == "user" else "Ассистент"
            lines.append(f"{label}: {content}")
        if lines:
            header = (
                "CURRENT DIALOGUE (this session):"
                if lang == "en"
                else "ТЕКУЩИЙ ДИАЛОГ (эта сессия):"
            )
            parts.append(header + "\n" + "\n".join(lines))
    return "\n\n".join(parts)


def build_console_operator_guide(lang: str = "ru", profile: str | None = None) -> str:
    """Инструкция для LLM: как устроена Velantrim и что делать с материалом пользователя."""
    en = lang == "en"
    prof = f" Active profile: {profile}." if profile else ""
    if en:
        return (
            "VELANTRIM CONSOLE — how the system works"
            + prof
            + "\n\n"
            "1) Long-term memory: durable facts (birthdays, names, work, family, projects) "
            "are stored via POST /facts and retrieved before each reply (RAG).\n"
            "2) When the user shares important personal info, acknowledge it and suggest "
            "saving if it should persist; the console may auto-save high-confidence facts.\n"
            "3) User text in chat is visible to the pipeline; use retrieved facts + user message.\n"
            "4) Operator instructions (right panel) override tone and priorities when present.\n"
            "5) Epistemic states: Observed → Supported → Validated; do not invent facts "
            "not in memory or the current message.\n"
            "6) For documents/long text: summarize key claims the user may want saved.\n"
        )
    return (
        "КОНСОЛЬ VELANTRIM — как работает система"
        + (f" Профиль: {profile}." if profile else "")
        + "\n\n"
        "1) Долгая память: важные факты (дни рождения, имена, работа, родные, проекты) "
        "хранятся через POST /facts и подмешиваются в ответ (RAG).\n"
        "2) Если пользователь сообщает важное — подтвердите и при необходимости предложите "
        "сохранить; консоль может автоматически сохранять уверенные факты.\n"
        "3) Текст в чате виден системе; опирайтесь на факты из памяти и текущее сообщение.\n"
        "4) Инструкции оператора (правая колонка) задают тон и приоритеты.\n"
        "5) Не выдумывайте факты вне памяти и текущего сообщения.\n"
        "6) Для длинного текста: выделите ключевые тезисы, которые стоит сохранить.\n"
    )


__all__ = [
    "MEMORY_CATEGORIES",
    "build_chat_context_for_prompt",
    "build_console_operator_guide",
    "category_emoji",
    "category_label",
    "classify_fact",
    "extract_memory_candidates",
    "fact_to_highlight",
]
