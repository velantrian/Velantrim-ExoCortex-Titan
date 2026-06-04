"""
utils/text_utils.py — Единый модуль токенизации (v8.5.1)
=========================================================
FIX (Gemini): раньше было 3 разных реализации tokenize():
  - core/pipeline.py       — em-dash, пунктуация
  - core/living_context.py — pymorphy2 лемматизация
  - core/affordance_linker.py — regex + pymorphy2

Теперь один источник истины. Все модули импортируют отсюда.

Использование:
    from utils.text_utils import tokenize, tokenize_lemmatized

    tokens = tokenize("Дерево растёт в лесу")
    # → ["дерево", "растёт", "лесу"]

    lemmas = tokenize_lemmatized("Птицы вьют гнёзда")
    # → ["птица", "вить", "гнездо"]  (если pymorphy2 установлен)
    # → ["птицы", "вьют", "гнёзда"]  (fallback без pymorphy2)
"""
from __future__ import annotations

import re

# Разделители: пробелы, дефис, тире, пунктуация
_TOKEN_SPLIT = re.compile(r'[\s\-–—,;:!?.«»"\'()\[\]{}<>]+')
_TOKEN_STRIP = ".,;:!?-–—\"'«»()[]{}/<>|\\@#$%^&*+="
_MIN_TOKEN_LEN = 2

# Lazy-loaded morphological analyser
_morph = None
_morph_available: bool | None = None


def _get_morph():
    """Lazy load pymorphy2 — не тормозим старт если не нужен."""
    global _morph, _morph_available
    if _morph_available is None:
        try:
            import pymorphy2
            _morph = pymorphy2.MorphAnalyzer()
            _morph_available = True
        except ImportError:
            _morph_available = False
    return _morph


def tokenize(text: str, min_len: int = _MIN_TOKEN_LEN) -> list[str]:
    """
    Базовая токенизация: split по разделителям + lowercase + фильтр по длине.

    Args:
        text: исходный текст
        min_len: минимальная длина токена (по умолчанию 2)

    Returns:
        список lowercase токенов

    Пример:
        tokenize("Вода кипит при 100°C!")
        → ["вода", "кипит", "при", "100°c"]
    """
    if not text:
        return []
    tokens = []
    for raw in _TOKEN_SPLIT.split(text):
        t = raw.lower().strip(_TOKEN_STRIP)
        if t and len(t) >= min_len:
            tokens.append(t)
    return tokens


def tokenize_lemmatized(text: str, min_len: int = _MIN_TOKEN_LEN) -> list[str]:
    """
    Токенизация с лемматизацией (если pymorphy2 установлен).
    Иначе — fallback на обычную токенизацию.

    Args:
        text: исходный текст
        min_len: минимальная длина токена

    Returns:
        список лемм (нормальных форм) или обычных токенов

    Пример с pymorphy2:
        tokenize_lemmatized("Птицы вьют гнёзда")
        → ["птица", "вить", "гнездо"]

    Пример без pymorphy2:
        tokenize_lemmatized("Птицы вьют гнёзда")
        → ["птицы", "вьют", "гнёзда"]
    """
    tokens = tokenize(text, min_len)
    morph = _get_morph()
    if morph is None:
        return tokens
    lemmas = []
    for token in tokens:
        try:
            lemma = morph.parse(token)[0].normal_form
            if len(lemma) >= min_len:
                lemmas.append(lemma)
        except Exception:
            lemmas.append(token)
    return lemmas


def is_morphology_available() -> bool:
    """Проверяет доступность pymorphy2."""
    return _get_morph() is not None
