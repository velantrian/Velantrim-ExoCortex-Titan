"""
🔒 core/recall_policy.py — Recall Policy (P0-1 Fix)

Единый source of truth для фильтрации фактов в recall-path.

Фильтрует факты по:
- metadata.restricted установлен
- erasure_status существует и не равен "active"
- epistemic_state == Collapsed
- epistemic_state == Deprecated

Использование:
    from core.recall_policy import filter_facts_for_recall, is_fact_allowed_for_recall
"""

from __future__ import annotations

import logging
from typing import Any, Iterable, Mapping

logger = logging.getLogger("velantrim.recall_policy")

# Состояния, которые должны быть исключены из recall
_EXCLUDED_EPISTEMIC_STATES = frozenset({"Collapsed", "Deprecated"})


def is_fact_allowed_for_recall(fact: Mapping[str, Any]) -> bool:
    """
    Проверить, разрешен ли факт для recall.
    
    Fail-closed: при любых сомнениях возвращает False.
    
    Args:
        fact: Словарь с полями fact_id, metadata, epistemic_state
        
    Returns:
        True если факт разрешен для recall, False иначе
    """
    if not fact or not isinstance(fact, Mapping):
        logger.debug("Fact excluded: invalid or None input")
        return False
    
    # Нормализуем metadata
    metadata = fact.get("metadata")
    if metadata is None:
        metadata = {}
    elif not isinstance(metadata, Mapping):
        # Поврежденная metadata - fail-closed
        logger.warning("Fact %s excluded: malformed metadata type %s", 
                      fact.get("fact_id", "?"), type(metadata).__name__)
        return False
    
    # 1. Проверяем restricted flag в metadata
    if metadata.get("restricted"):
        logger.debug("Fact %s excluded: restricted=%s", 
                    fact.get("fact_id", "?"), metadata.get("restricted"))
        return False
    
    # 2. Проверяем erasure_status в metadata
    erasure_status = metadata.get("erasure_status")
    if erasure_status is not None and erasure_status != "active":
        logger.debug("Fact %s excluded: erasure_status=%s", 
                    fact.get("fact_id", "?"), erasure_status)
        return False
    
    # 3. Проверяем epistemic_state
    epistemic_state = fact.get("epistemic_state", "Observed")
    if epistemic_state in _EXCLUDED_EPISTEMIC_STATES:
        logger.debug("Fact %s excluded: epistemic_state=%s", 
                    fact.get("fact_id", "?"), epistemic_state)
        return False
    
    return True


def filter_facts_for_recall(
    facts: Iterable[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """
    Отфильтровать список фактов по политике recall.
    
    Fail-closed: при ошибках фильтрации факт исключается.
    
    Args:
        facts: Итерируемый набор фактов для фильтрации
        
    Returns:
        Отфильтрованный список фактов
    """
    result = []
    for fact in facts:
        try:
            if is_fact_allowed_for_recall(fact):
                result.append(dict(fact))
        except Exception as exc:
            logger.warning("Fact excluded due to filtering error: %s", exc)
            # Fail-closed: при ошибке фильтрации исключаем факт
            continue
    return result
