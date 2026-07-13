"""
🔒 core/recall_policy.py — Recall Policy (P0-1 Fix)

Единый source of truth для фильтрации фактов в recall-path.

Фильтрует факты по:
- metadata.restricted установлен
- erasure_status (в metadata ИЛИ на верхнем уровне факта) существует и не
  равен "active", либо имеет неверный тип
- epistemic_state отсутствует, неизвестен, либо равен Collapsed/Deprecated

Fail-closed: при любых ошибках, отсутствующих полях или невалидных данных
факт исключается. Ничего не допускается «по умолчанию».

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

# Локальная копия core.memory.ESM_STATES. Не импортируем core.memory здесь —
# core/memory.py импортирует этот модуль, поэтому обратный импорт создал бы
# цикл. Держать в синхронизации с core.memory.ESM_STATES вручную.
_KNOWN_EPISTEMIC_STATES: frozenset[str] = frozenset({
    "Observed",
    "Hypothesized",
    "Supported",
    "Validated",
    "Contradicted",
    "Deprecated",
    "Collapsed",
    "ImmutableCore",
})

# Приватная константа - не экспортируется через __all__
_EXCLUDED_EPISTEMIC_STATES: frozenset[str] = frozenset({"Collapsed", "Deprecated"})


def _erasure_status_blocks(value: Any) -> bool:
    """
    Проверить одно значение erasure_status.

    Fail-closed: отсутствующее значение (None) не блокирует. Любое
    присутствующее, но не-строковое значение блокирует (повреждённый тип).
    Строковое значение блокирует, если после normalize (strip+lower) оно не
    равно "active".
    """
    if value is None:
        return False
    if not isinstance(value, str):
        return True
    return value.strip().lower() != "active"


def is_fact_allowed_for_recall(fact: Mapping[str, Any] | None) -> bool:
    """
    Проверить, разрешен ли факт для recall.

    Fail-closed: при любых сомнениях возвращает False. Никогда не бросает
    исключение — любой невалидный вход обрабатывается явной проверкой типа.

    Критерии исключения:
    - metadata.restricted установлен (truthy значение)
    - erasure_status (metadata ИЛИ top-level) присутствует и не равен "active",
      либо имеет не-строковый тип
    - epistemic_state отсутствует, неизвестен или в {"Collapsed", "Deprecated"}
    - невалидный или пустой факт
    - невалидная metadata (не Mapping)

    Args:
        fact: Словарь с полями fact_id, metadata, epistemic_state или None

    Returns:
        True если факт разрешен для recall, False иначе
    """
    if not fact or not isinstance(fact, Mapping):
        logger.debug("Fact excluded: invalid or None input")
        return False

    fact_id = fact.get("fact_id", "?")

    # Нормализуем metadata
    metadata = fact.get("metadata")
    if metadata is None:
        metadata = {}
    elif not isinstance(metadata, Mapping):
        # Поврежденная metadata - fail-closed
        logger.warning(
            "Fact %s excluded: malformed metadata type %s",
            fact_id,
            type(metadata).__name__,
        )
        return False

    # 1. Проверяем restricted flag в metadata
    if metadata.get("restricted"):
        logger.debug("Fact %s excluded: restricted=%s", fact_id, metadata.get("restricted"))
        return False

    # 2. Проверяем erasure_status в обоих расположениях: metadata и top-level.
    #    Любое из них, если присутствует и не "active" (или не строка), блокирует.
    if _erasure_status_blocks(metadata.get("erasure_status")):
        logger.debug(
            "Fact %s excluded: metadata.erasure_status=%r", fact_id, metadata.get("erasure_status")
        )
        return False
    if _erasure_status_blocks(fact.get("erasure_status")):
        logger.debug(
            "Fact %s excluded: erasure_status=%r", fact_id, fact.get("erasure_status")
        )
        return False

    # 3. Проверяем epistemic_state. Fail-closed: отсутствующее или неизвестное
    #    состояние НЕ допускается по умолчанию (в отличие от прежней логики,
    #    подставлявшей "Observed").
    epistemic_state = fact.get("epistemic_state")
    if not isinstance(epistemic_state, str):
        logger.debug("Fact %s excluded: missing/invalid epistemic_state=%r", fact_id, epistemic_state)
        return False
    if epistemic_state not in _KNOWN_EPISTEMIC_STATES:
        logger.debug("Fact %s excluded: unknown epistemic_state=%r", fact_id, epistemic_state)
        return False
    if epistemic_state in _EXCLUDED_EPISTEMIC_STATES:
        logger.debug("Fact %s excluded: epistemic_state=%s", fact_id, epistemic_state)
        return False

    return True


def filter_facts_for_recall(
    facts: Iterable[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """
    Отфильтровать список фактов по политике recall.

    is_fact_allowed_for_recall() сама корректно обрабатывает все невалидные
    типы входа и никогда не бросает исключение, поэтому здесь нет broad
    except: реальная programming error (например, в dict(fact) для
    экзотического Mapping) должна быть видимой, а не тихо превращаться в
    "факт исключён".

    Args:
        facts: Итерируемый набор фактов для фильтрации

    Returns:
        Отфильтрованный список фактов (копии оригинальных словарей)
    """
    return [dict(fact) for fact in facts if is_fact_allowed_for_recall(fact)]


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
