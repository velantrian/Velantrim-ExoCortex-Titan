"""
🌐 core/multilingual_router.py — Multilingual Router (V8.7 Titan)

Авто-детект языка + dual-index retrieval + лемматизация RU.
Без интернета. Всё локально.

Pipeline:
    1. detect_language(query) → RU / EN / MIXED
    2. Если RU → лемматизировать запрос (pymorphy3)
    3. Искать в claim_ru (основной) + claim_en (перевод, если есть)
    4. Merge результатов → отдать в pipeline

Инварианты:
    I-ML1: Лемматизация не меняет смысл — только нормализует словоформы.
    I-ML2: При отсутствии pymorphy3 — fallback на naive lowercase.
    I-ML3: Не требует интернета.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Tuple

logger = logging.getLogger("velantrim.multilingual_router")


# ─── Детектор языка ──────────────────────────────────────────────────────────
def detect_language(text: str) -> str:
    """
    Определить язык текста.
    Returns: 'RU', 'EN', 'MIXED' или 'UNKNOWN'.
    """
    if not text or not text.strip():
        return "UNKNOWN"

    cyrillic = sum(1 for c in text if "А" <= c <= "я" or c in "Ёё")
    latin = sum(1 for c in text if c.isascii() and c.isalpha())

    total = cyrillic + latin
    if total == 0:
        return "UNKNOWN"

    if cyrillic / total >= 0.4:
        return "RU"
    if latin / total >= 0.6:
        return "EN"
    return "MIXED"


# ─── Лемматизация русского текста ─────────────────────────────────────────────
def _get_lemmatizer():
    """Lazy-загрузка pymorphy3. Fallback — naive lowercase."""
    try:
        import pymorphy3
        return pymorphy3.MorphAnalyzer(lang="ru")
    except ImportError:
        return None


def lemmatize_ru_text(text: str) -> str:
    """
    Лемматизировать русский текст.
    «кошке», «кошки», «кошку» → «кошка».
    """
    morph = _get_lemmatizer()
    if morph is None:
        return text.lower()

    import re
    word_re = re.compile(r"[\wА-Яа-яЁё]+", re.UNICODE)

    def _lemma(match):
        word = match.group(0)
        try:
            parsed = morph.parse(word)
            if parsed:
                return parsed[0].normal_form
        except Exception:
            pass
        return word.lower()

    return word_re.sub(_lemma, text.lower())


def lemmatize_ru_query(query: str) -> str:
    """
    Подготовить русский запрос к retrieval.
    Убрать стоп-слова после лемматизации.
    """
    lemmatized = lemmatize_ru_text(query)

    stopwords = {
        "и", "в", "на", "с", "по", "для", "от", "до", "при", "из",
        "к", "у", "за", "над", "под", "перед", "около", "через",
        "это", "как", "что", "кто", "где", "когда", "почему", "зачем",
        "который", "весь", "мой", "твой", "свой", "его", "её", "их",
        "бы", "же", "ли", "то", "не", "нет", "да",
    }
    tokens = lemmatized.split()
    return " ".join(t for t in tokens if t not in stopwords)


# ─── Dual-index retrieval ────────────────────────────────────────────────────
def retrieve_multilingual(
    query: str,
    *,
    top_k: int = 5,
    use_ngram: bool = True,
) -> List[Dict[str, Any]]:
    """
    Поиск с учётом языка запроса.

    Стратегия:
        RU-запрос  → ищем в claim_ru (основной), claim_en (fallback)
        EN-запрос  → ищем в claim_en (основной), claim_ru (fallback)
        MIXED      → оба направления, merge

    Returns: список фактов, готовых для pipeline.
    """
    lang = detect_language(query)

    # 1. Лемматизировать если RU
    if lang in ("RU", "MIXED"):
        processed_query = lemmatize_ru_query(query)
    else:
        processed_query = query.lower()

    # 2. Retrieval из основной БД
    try:
        from core.memory import get_all_facts
        facts = get_all_facts() or []
    except Exception:
        facts = []

    if not facts:
        return []

    # 3. Ранжирование по релевантности
    scored: List[Tuple[float, Dict[str, Any]]] = []

    for fact in facts:
        claim = fact.get("claim", "")
        score = _relevance_score(processed_query, claim, lang)
        if score > 0:
            scored.append((score, fact))

    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored[:top_k]]


def _relevance_score(query: str, claim: str, lang: str) -> float:
    """
    Оценка релевантности факта запросу.
    Учитывает: token overlap + language match.
    """
    if not query or not claim:
        return 0.0

    claim_lower = claim.lower()
    query_tokens = set(query.lower().split())
    claim_tokens = set(claim_lower.split())

    if not query_tokens:
        return 0.0

    # Token overlap
    overlap = len(query_tokens & claim_tokens)
    if overlap == 0:
        return 0.0

    # Jaccard similarity
    union = len(query_tokens | claim_tokens)
    jaccard = overlap / union if union > 0 else 0.0

    # Language bonus: RU-запрос + RU-факт → bonus
    claim_is_ru = any("А" <= c <= "я" or c in "Ёё" for c in claim)
    lang_match = (
        (lang == "RU" and claim_is_ru) or
        (lang == "EN" and not claim_is_ru)
    )
    bonus = 1.2 if lang_match else 1.0

    return jaccard * bonus


# ─── Интеграция в pipeline ──────────────────────────────────────────────────
# Храним identity ровно одного wrapper, которым владеет этот модуль. Это
# предотвращает накопление closure-слоёв при повторном lifespan/setup в одном
# процессе и позволяет безопасно вернуть точный pre-install retrieve.
_original_retrieve: Any | None = None
_installed_retrieve: Any | None = None


def _clear_patch_state() -> None:
    global _installed_retrieve, _original_retrieve
    _original_retrieve = None
    _installed_retrieve = None


def patch_pipeline_retrieval() -> bool:
    """Install multilingual retrieval once and report whether this call owns it.

    Repeated setup is idempotent while the exact wrapper installed by this
    module remains active. If another component replaced ``pipeline.retrieve``
    after our install, we do not pretend ownership of that replacement; stale
    bookkeeping is dropped before a new explicit install captures the current
    callable as its new original.
    """
    global _installed_retrieve, _original_retrieve

    try:
        from core import pipeline

        if _installed_retrieve is not None:
            if pipeline.retrieve is _installed_retrieve:
                return False
            logger.warning(
                "Multilingual retrieval patch lost ownership; resetting stale state"
            )
            _clear_patch_state()

        original = pipeline.retrieve

        def multilingual_retrieve(query, k=3, database=None, domain=None):
            if database is not None:
                return original(query, k, database, domain)
            return retrieve_multilingual(query, top_k=k)

        pipeline.retrieve = multilingual_retrieve
        _original_retrieve = original
        _installed_retrieve = multilingual_retrieve
        logger.info("Pipeline retrieval patched for multilingual support")
        return True
    except Exception as exc:
        logger.warning("Failed to patch pipeline: %s", exc)
        return False


def unpatch_pipeline_retrieval() -> bool:
    """Restore the exact pre-install retrieve only while this module owns it.

    External replacements are never overwritten. In that case internal stale
    state is cleared and the function returns ``False``.
    """
    global _installed_retrieve, _original_retrieve

    if _installed_retrieve is None or _original_retrieve is None:
        _clear_patch_state()
        return False

    try:
        from core import pipeline

        if pipeline.retrieve is not _installed_retrieve:
            logger.warning(
                "Multilingual retrieval patch no longer owns pipeline.retrieve; "
                "external replacement preserved"
            )
            _clear_patch_state()
            return False

        pipeline.retrieve = _original_retrieve
        _clear_patch_state()
        logger.info("Pipeline multilingual retrieval patch removed")
        return True
    except Exception as exc:
        logger.warning("Failed to unpatch pipeline: %s", exc)
        return False


def is_multilingual_enabled() -> bool:
    raw = (os.getenv("VELANTRIM_MULTILINGUAL", "1") or "1").strip().lower()
    return raw in ("1", "true", "yes", "on")


__all__ = [
    "detect_language",
    "is_multilingual_enabled",
    "lemmatize_ru_query",
    "lemmatize_ru_text",
    "patch_pipeline_retrieval",
    "retrieve_multilingual",
    "unpatch_pipeline_retrieval",
]
