"""
🔒 core/recall_policy.py — Recall Policy Layer (P0-1 Fix)

Единый policy-aware слой чтения для пользовательского recall.

Проблема: Некоторые read-path фильтруют restricted-факты, но get_all_facts() 
возвращает их без фильтрации. Console/chat fallback может использовать полный 
список памяти и повторно включать restricted-факты в генерацию ответа.

Решение: Создать единый RecallPolicy, который фильтрует факты по:
- metadata.restricted == true
- erasure_status != active (если есть такое поле)
- epistemic_state == Collapsed
- epistemic_state == Deprecated

Использование:
    from core.recall_policy import RecallPolicy, get_fact_for_recall, get_facts_for_recall
    
    # Получение одного факта с фильтрацией
    fact = get_fact_for_recall(fact)
    
    # Получение всех фактов с фильтрацией
    facts = get_facts_for_recall(all_facts)
    
    # Прямое использование политики
    policy = RecallPolicy()
    filtered_facts = policy.filter_facts(all_facts)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.recall_policy")


# Состояния, которые должны быть исключены из recall
_EXCLUDED_EPISTEMIC_STATES = frozenset({"Collapsed", "Deprecated"})


class RecallPolicy:
    """
    Политика фильтрации фактов для recall-path.
    
    Исключает факты, которые не должны быть доступны для:
    - пользовательского recall
    - answer-generation
    - chat/stream fallbacks
    - console fallback
    """
    
    def __init__(self):
        """Инициализация политики с дефолтными настройками."""
        self.excluded_epistemic_states = _EXCLUDED_EPISTEMIC_STATES
    
    def is_fact_allowed_for_recall(self, fact: Dict[str, Any]) -> bool:
        """
        Проверить, разрешен ли факт для recall.
        
        Args:
            fact: Словарь с полями fact_id, metadata, epistemic_state
            
        Returns:
            True если факт разрешен для recall, False иначе
        """
        if not fact:
            return False
        
        # 1. Проверяем restricted flag в metadata
        metadata = fact.get("metadata", {})
        if metadata and metadata.get("restricted"):
            logger.debug("Fact %s excluded: restricted=%s", 
                        fact.get("fact_id", "?"), metadata.get("restricted"))
            return False
        
        # 2. Проверяем erasure_status (если есть)
        # Поле erasure_status может быть в metadata или на уровне факта
        erasure_status = metadata.get("erasure_status") if metadata else None
        if erasure_status and erasure_status != "active":
            logger.debug("Fact %s excluded: erasure_status=%s", 
                        fact.get("fact_id", "?"), erasure_status)
            return False
        
        # 3. Проверяем epistemic_state
        epistemic_state = fact.get("epistemic_state", "Observed")
        if epistemic_state in self.excluded_epistemic_states:
            logger.debug("Fact %s excluded: epistemic_state=%s", 
                        fact.get("fact_id", "?"), epistemic_state)
            return False
        
        return True
    
    def filter_facts(self, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Отфильтровать список фактов по политике recall.
        
        Args:
            facts: Список фактов для фильтрации
            
        Returns:
            Отфильтрованный список фактов
        """
        return [fact for fact in facts if self.is_fact_allowed_for_recall(fact)]
    
    def ensure_recall_compliance(self, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Гарантировать соответствие политике recall.
        Алиас для filter_facts для ясности кода.
        """
        return self.filter_facts(facts)


# Глобальный экземпляр политики
_POLICY: Optional[RecallPolicy] = None


def get_recall_policy() -> RecallPolicy:
    """Получить глобальный экземпляр RecallPolicy."""
    global _POLICY
    if _POLICY is None:
        _POLICY = RecallPolicy()
    return _POLICY


# Удобные функции для использования в коде

def get_fact_for_recall(fact: Dict[str, Any], policy: Optional[RecallPolicy] = None) -> Optional[Dict[str, Any]]:
    """
    Проверить и вернуть факт, если он разрешен для recall.
    
    Args:
        fact: Факт для проверки
        policy: Экземпляр RecallPolicy (если None, используется глобальный)
        
    Returns:
        Факт, если разрешен, None иначе
    """
    if policy is None:
        policy = get_recall_policy()
    
    if policy.is_fact_allowed_for_recall(fact):
        return fact
    return None


def get_facts_for_recall(facts: List[Dict[str, Any]], policy: Optional[RecallPolicy] = None) -> List[Dict[str, Any]]:
    """
    Отфильтровать факты по политике recall.
    
    Args:
        facts: Список фактов для фильтрации
        policy: Экземпляр RecallPolicy (если None, используется глобальный)
        
    Returns:
        Отфильтрованный список фактов
    """
    if policy is None:
        policy = get_recall_policy()
    
    return policy.filter_facts(facts)


def list_facts_for_recall(
    get_all_facts_func, 
    policy: Optional[RecallPolicy] = None,
    *args, 
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Получить все факты с применением политики recall.
    
    Args:
        get_all_facts_func: Функция для получения всех фактов (например, store.get_all_facts)
        policy: Экземпляр RecallPolicy (если None, используется глобальный)
        *args, **kwargs: Аргументы для get_all_facts_func
        
    Returns:
        Отфильтрованный список фактов
    """
    if policy is None:
        policy = get_recall_policy()
    
    all_facts = get_all_facts_func(*args, **kwargs)
    return policy.filter_facts(all_facts)


def search_facts_for_recall(
    search_func,
    policy: Optional[RecallPolicy] = None,
    *args, 
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Выполнить поиск фактов с применением политики recall.
    
    Args:
        search_func: Функция поиска фактов
        policy: Экземпляр RecallPolicy (если None, используется глобальный)
        *args, **kwargs: Аргументы для search_func
        
    Returns:
        Отфильтрованный список фактов
    """
    if policy is None:
        policy = get_recall_policy()
    
    search_results = search_func(*args, **kwargs)
    return policy.filter_facts(search_results)


__all__ = [
    "RecallPolicy",
    "get_recall_policy", 
    "get_fact_for_recall",
    "get_facts_for_recall", 
    "list_facts_for_recall",
    "search_facts_for_recall",
    "_EXCLUDED_EPISTEMIC_STATES",
]