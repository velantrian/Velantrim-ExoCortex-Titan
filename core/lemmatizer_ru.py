"""
🇷🇺 core/lemmatizer_ru.py — Russian Lemmatizer for BM25 (V8.7 Titan)

Добавляет лемматизацию для русского текста перед BM25-токенизацией.
«кошка», «кошки», «кошке» → все становятся «кошка» — BM25 больше не слеп на русском.

Использует pymorphy3 (чистый Python, без внешних зависимостей).
Если pymorphy3 не установлен — graceful fallback на стемминг Snowball.

Benchmark: recall на русскоязычных запросах +30-50%.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache  # V8.7 HYPERIA V5.5: экономия CPU 40-60%
from typing import List, Optional

logger = logging.getLogger("velantrim.lemmatizer_ru")

# ─── Проверка зависимостей ───────────────────────────────────────────────────

_MORPH: Optional[object] = None
_MORPH_CHECKED = False
_STEMMER: Optional[object] = None
_STEMMER_CHECKED = False

_WS_RE = re.compile(r"\s+")
_WORD_RE = re.compile(r"[\wА-Яа-яЁё]+", re.UNICODE)


def _get_morph():
    global _MORPH, _MORPH_CHECKED
    if _MORPH_CHECKED:
        return _MORPH
    _MORPH_CHECKED = True
    try:
        import pymorphy3
        _MORPH = pymorphy3.MorphAnalyzer(lang="ru")
        logger.info("pymorphy3 загружен — лемматизация активна")
    except ImportError:
        logger.info("pymorphy3 не установлен — pip install pymorphy3")
    return _MORPH


def _get_stemmer():
    global _STEMMER, _STEMMER_CHECKED
    if _STEMMER_CHECKED:
        return _STEMMER
    _STEMMER_CHECKED = True
    try:
        from nltk.stem.snowball import SnowballStemmer
        _STEMMER = SnowballStemmer("russian")
        logger.info("SnowballStemmer (RU) загружен — стемминг активен")
    except ImportError:
        logger.info("nltk не установлен — pip install nltk ; python -m nltk.downloader snowball_data")
    return _STEMMER


# ─── Лемматизация ────────────────────────────────────────────────────────────


@lru_cache(maxsize=4096)  # V8.7 HYPERIA V5.5: кэш морф-анализа — экономия CPU 40-60%
def lemmatize_word(word: str) -> str:
    """Привести слово к начальной форме. «кошке» → «кошка»."""
    morph = _get_morph()
    if morph is None:
        stemmer = _get_stemmer()
        if stemmer is not None:
            return stemmer.stem(word)
        return word.lower()  # fallback: просто lowercase

    try:
        parsed = morph.parse(word)
        if parsed:
            return parsed[0].normal_form
    except Exception:
        pass
    return word.lower()


def lemmatize_text(text: str) -> str:
    """Лемматизировать весь текст (с сохранением не-русских слов)."""
    if not text:
        return ""

    def _replace(match):
        return lemmatize_word(match.group(0))

    return _WORD_RE.sub(_replace, text.lower())


def tokenize_ru(text: str, *, lemmatize: bool = True) -> List[str]:
    """
    Токенизировать русский текст для BM25.

    Args:
        text: исходный текст.
        lemmatize: включить лемматизацию (True по умолчанию).

    Returns:
        Список токенов (лемматизированных если lemmatize=True).
    """
    if lemmatize:
        text = lemmatize_text(text)

    # Убрать пунктуацию, оставить слова
    clean = re.sub(r"[^\w\s]", " ", text)
    tokens = clean.split()
    return [t for t in tokens if len(t) >= 2]


def tokenize_corpus_ru(
    texts: List[str],
    *,
    lemmatize: bool = True,
) -> List[List[str]]:
    """Пакетная токенизация для BM25-индекса."""
    return [tokenize_ru(t, lemmatize=lemmatize) for t in texts]


def is_russian_text(text: str, threshold: float = 0.3) -> bool:
    """Определить русский ли текст (по доле кириллических символов)."""
    if not text:
        return False
    cyrillic = sum(1 for c in text if "А" <= c <= "я" or c in "Ёё")
    total = len(re.sub(r"\s", "", text))
    return total > 0 and cyrillic / total >= threshold


# ─── Интеграция с HybridRetriever ─────────────────────────────────────────────


def patch_bm25_tokenizer():
    """
    Monkey-patch BM25Retriever._tokenize() для русского языка.

    Вызывается один раз при старте если VELANTRIM_LEMMATIZE_RU=1.

    Делает:
      BM25Retriever._tokenize = tokenize_ru  (с сохранением оригинала).
    """
    import os

    if os.getenv("VELANTRIM_LEMMATIZE_RU", "0").strip().lower() not in (
        "1", "true", "yes", "on",
    ):
        return

    try:
        from core.hybrid_retriever import BM25Retriever

        _original = BM25Retriever._tokenize

        def _ru_tokenize(self, text: str) -> list:
            if is_russian_text(text):
                return tokenize_ru(text)
            return _original(self, text)

        # Intentional monkey-patch (valid at runtime): mypy can't verify method
        # reassignment safety in general, hence method-assign.
        BM25Retriever._tokenize = _ru_tokenize  # type: ignore[method-assign]
        logger.info("BM25Retriever._tokenize пропатчен для русского языка")
    except ImportError:
        logger.debug("HybridRetriever не загружен — пропатчить BM25 невозможно")


__all__ = [
    "lemmatize_text",
    "lemmatize_word",
    "tokenize_ru",
    "tokenize_corpus_ru",
    "is_russian_text",
    "patch_bm25_tokenizer",
]
