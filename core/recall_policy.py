"""
🔒 core/recall_policy.py — Recall Policy (P0-1 Fix)

Единый source of truth для фильтрации фактов в recall-path.

Фильтрует факты по:
- metadata.restricted установлен
- erasure_status существует и не равен "active"
- epistemic_state == Collapsed
- epistemic_state == Deprecated

Fail-closed: при любых ошибках или невалидных данных факт исключается.

Использование:
    from core.recall_policy import (
        is_fact_allowed_for_recall,
        filter_facts_for_recall,
        get_facts_for_recall,
        list_facts_for_recall,
        search_facts_for_recall,
    )
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Iterable, Mapping

logger = logging.getLogger("velantrim.recall_policy")

# Приватная константа - не экспортируется через __all__
_EXCLUDED_EPISTEMIC_STATES: frozenset[str] = frozenset({"Collapsed", "Deprecated"})


def is_fact_allowed_for_recall(fact: Mapping[str, Any] | None) -> bool:
    """
    Проверить, разрешен ли факт для recall.
    
    Fail-closed: при любых сомнениях возвращает False.
    
    Критерии исключения:
    - metadata.restricted установлен (truthy значение)
    - erasure_status существует и не равен "active"
    - epistemic_state в {"Collapsed", "Deprecated"}
    - невалидный или пустой факт
    - невалидная metadata (не dict)
    
    Args:
        fact: Словарь с полями fact_id, metadata, epistemic_state или None
        
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
        logger.warning(
            "Fact %s excluded: malformed metadata type %s", 
            fact.get("fact_id", "?"),
            type(metadata).__name__
        )
        return False
    
    # 1. Проверяем restricted flag в metadata
    if metadata.get("restricted"):
        logger.debug(
            "Fact %s excluded: restricted=%s", 
            fact.get("fact_id", "?"),
            metadata.get("restricted")
        )
        return False
    
    # 2. Проверяем erasure_status в metadata
    erasure_status = metadata.get("erasure_status")
    if erasure_status is not None and erasure_status != "active":
        logger.debug(
            "Fact %s excluded: erasure_status=%s", 
            fact.get("fact_id", "?"),
            erasure_status
        )
        return False
    
    # 3. Проверяем epistemic_state
    epistemic_state = fact.get("epistemic_state", "Observed")
    if epistemic_state in _EXCLUDED_EPISTEMIC_STATES:
        logger.debug(
            "Fact %s excluded: epistemic_state=%s", 
            fact.get("fact_id", "?"),
            epistemic_state
        )
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
        Отфильтрованный список фактов (копии оригинальных словарей)
    """
    result: list[dict[str, Any]] = []
    for fact in facts:
        try:
            if is_fact_allowed_for_recall(fact):
                result.append(dict(fact))
        except Exception as exc:
            logger.warning("Fact excluded due to filtering error: %s", exc)
            # Fail-closed: при ошибке фильтрации исключаем факт
            continue
    return result


def get_facts_for_recall(
    get_all_facts_func: Callable[..., list[dict[str, Any]]],
    *,
    epistemic_state: str | None = None,
    domain: str | None = None,
) -> list[dict[str, Any]]:
    """
    Получить факты для recall с применением политики фильтрации.
    
    Исключает факты, которые не должны быть доступны для:
    - пользовательского recall
    - answer-generation
    - chat/stream fallbacks
    - console fallback
    
    Args:
        get_all_facts_func: Функция для получения всех фактов (сигнатура совместима с memory.get_all_facts)
        epistemic_state: Фильтр по эпистемическому состоянию
        domain: Фильтр по домену
        
    Returns:
        Список фактов, разрешенных для recall
    """
    all_facts = get_all_facts_func(epistemic_state=epistemic_state, domain=domain)
    return filter_facts_for_recall(all_facts)


def list_facts_for_recall(
    get_all_facts_func: Callable[..., list[dict[str, Any]]],
    *,
    epistemic_state: str | None = None,
    domain: str | None = None,
) -> list[dict[str, Any]]:
    """
    Алиас для get_facts_for_recall для совместимости.
    
    Args:
        get_all_facts_func: Функция для получения всех фактов
        epistemic_state: Фильтр по эпистемическому состоянию
        domain: Фильтр по домену
        
    Returns:
        Список фактов, разрешенных для recall
    """
    return get_facts_for_recall(
        get_all_facts_func,
        epistemic_state=epistemic_state,
        domain=domain
    )


def search_facts_for_recall(
    search_func: Callable[..., list[dict[str, Any]]],
    query: str,
    *,
    top_k: int = 5,
    domain: str | None = None,
) -> list[dict[str, Any]]:
    """
    Поиск фактов для recall с применением политики фильтрации.
    
    Args:
        search_func: Функция поиска (сигнатура совместима с memory.search или store.search)
        query: Поисковый запрос
        top_k: Максимальное количество результатов
        domain: Фильтр по домену
        
    Returns:
        Список фактов, разрешенных для recall и соответствующих запросу
    """
    all_facts = search_func(query=query, top_k=top_k, domain=domain)
    return filter_facts_for_recall(all_facts)