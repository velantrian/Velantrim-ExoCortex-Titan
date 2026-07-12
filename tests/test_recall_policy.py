"""
🧪 tests/test_recall_policy.py — Tests for Recall Policy (P0-1 Fix)

Тесты для проверки фильтрации restricted-фактов из recall-path.

Требования из ТЗ:
1. restricted-факт существует в БД;
2. admin/raw endpoint при разрешённой политике может его увидеть;
3. recall API не возвращает restricted-факт;
4. "/chat" fallback не включает restricted-факт;
5. "/chat/stream" fallback не включает restricted-факт;
6. unrestricted-факты продолжают работать.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from core.recall_policy import (
    RecallPolicy,
    get_recall_policy,
    get_fact_for_recall,
    get_facts_for_recall,
    list_facts_for_recall,
    search_facts_for_recall,
    _EXCLUDED_EPISTEMIC_STATES
)


class TestRecallPolicy:
    """Тесты для класса RecallPolicy."""
    
    def test_excluded_epistemic_states(self):
        """Проверяем, что исключаемые состояния правильно определены."""
        assert "Collapsed" in _EXCLUDED_EPISTEMIC_STATES
        assert "Deprecated" in _EXCLUDED_EPISTEMIC_STATES
        assert "Validated" not in _EXCLUDED_EPISTEMIC_STATES
        assert "Supported" not in _EXCLUDED_EPISTEMIC_STATES
        assert "Observed" not in _EXCLUDED_EPISTEMIC_STATES
    
    def test_is_fact_allowed_for_recall_valid_fact(self):
        """Тест: валидный факт разрешен для recall."""
        policy = RecallPolicy()
        
        # Создаем валидный факт
        valid_fact = {
            "fact_id": "fact_001",
            "claim": "Test claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Validated",
            "metadata": {}
        }
        
        assert policy.is_fact_allowed_for_recall(valid_fact) is True
    
    def test_is_fact_allowed_for_recall_restricted_fact(self):
        """Тест: restricted-факт запрещен для recall."""
        policy = RecallPolicy()
        
        # Создаем restricted факт
        restricted_fact = {
            "fact_id": "fact_002",
            "claim": "Restricted claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Validated",
            "metadata": {"restricted": "2026-07-12T10:00:00Z"}
        }
        
        assert policy.is_fact_allowed_for_recall(restricted_fact) is False
    
    def test_is_fact_allowed_for_recall_restricted_false(self):
        """Тест: факт с restricted=false разрешен."""
        policy = RecallPolicy()
        
        # Создаем факт с restricted=false (удаленное значение)
        fact = {
            "fact_id": "fact_003",
            "claim": "Non-restricted claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Validated",
            "metadata": {"restricted": None}
        }
        
        assert policy.is_fact_allowed_for_recall(fact) is True
    
    def test_is_fact_allowed_for_recall_collapsed_state(self):
        """Тест: факт в состоянии Collapsed запрещен."""
        policy = RecallPolicy()
        
        collapsed_fact = {
            "fact_id": "fact_004",
            "claim": "Collapsed claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Collapsed",
            "metadata": {}
        }
        
        assert policy.is_fact_allowed_for_recall(collapsed_fact) is False
    
    def test_is_fact_allowed_for_recall_deprecated_state(self):
        """Тест: факт в состоянии Deprecated запрещен."""
        policy = RecallPolicy()
        
        deprecated_fact = {
            "fact_id": "fact_005",
            "claim": "Deprecated claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Deprecated",
            "metadata": {}
        }
        
        assert policy.is_fact_allowed_for_recall(deprecated_fact) is False
    
    def test_is_fact_allowed_for_recall_erasure_status_inactive(self):
        """Тест: факт с erasure_status != active запрещен."""
        policy = RecallPolicy()
        
        erased_fact = {
            "fact_id": "fact_006",
            "claim": "Erased claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Validated",
            "metadata": {"erasure_status": "erased"}
        }
        
        assert policy.is_fact_allowed_for_recall(erased_fact) is False
    
    def test_is_fact_allowed_for_recall_erasure_status_active(self):
        """Тест: факт с erasure_status = active разрешен."""
        policy = RecallPolicy()
        
        active_fact = {
            "fact_id": "fact_007",
            "claim": "Active claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Validated",
            "metadata": {"erasure_status": "active"}
        }
        
        assert policy.is_fact_allowed_for_recall(active_fact) is True
    
    def test_is_fact_allowed_for_recall_empty_fact(self):
        """Тест: пустой факт запрещен."""
        policy = RecallPolicy()
        
        assert policy.is_fact_allowed_for_recall({}) is False
        assert policy.is_fact_allowed_for_recall(None) is False
    
    def test_filter_facts_mixed(self):
        """Тест: фильтрация смешанного списка фактов."""
        policy = RecallPolicy()
        
        facts = [
            {
                "fact_id": "fact_001",
                "epistemic_state": "Validated",
                "metadata": {}
            },
            {
                "fact_id": "fact_002",
                "epistemic_state": "Validated", 
                "metadata": {"restricted": "2026-07-12T10:00:00Z"}
            },
            {
                "fact_id": "fact_003",
                "epistemic_state": "Collapsed",
                "metadata": {}
            },
            {
                "fact_id": "fact_004",
                "epistemic_state": "Deprecated",
                "metadata": {}
            },
            {
                "fact_id": "fact_005",
                "epistemic_state": "Supported",
                "metadata": {}
            }
        ]
        
        filtered = policy.filter_facts(facts)
        
        # Должны остаться только fact_001 и fact_005
        assert len(filtered) == 2
        assert filtered[0]["fact_id"] == "fact_001"
        assert filtered[1]["fact_id"] == "fact_005"
    
    def test_filter_facts_empty_list(self):
        """Тест: фильтрация пустого списка."""
        policy = RecallPolicy()
        
        assert policy.filter_facts([]) == []


class TestGlobalPolicy:
    """Тесты для глобального экземпляра политики."""
    
    def test_get_recall_policy_singleton(self):
        """Тест: get_recall_policy возвращает singleton."""
        policy1 = get_recall_policy()
        policy2 = get_recall_policy()
        
        assert policy1 is policy2


class TestConvenienceFunctions:
    """Тесты для удобных функций."""
    
    def test_get_fact_for_recall_allowed(self):
        """Тест: get_fact_for_recall возвращает разрешенный факт."""
        valid_fact = {
            "fact_id": "fact_001",
            "epistemic_state": "Validated",
            "metadata": {}
        }
        
        result = get_fact_for_recall(valid_fact)
        assert result == valid_fact
    
    def test_get_fact_for_recall_restricted(self):
        """Тест: get_fact_for_recall возвращает None для restricted факта."""
        restricted_fact = {
            "fact_id": "fact_002",
            "epistemic_state": "Validated",
            "metadata": {"restricted": "2026-07-12T10:00:00Z"}
        }
        
        result = get_fact_for_recall(restricted_fact)
        assert result is None
    
    def test_get_facts_for_recall_filters(self):
        """Тест: get_facts_for_recall фильтрует restricted факты."""
        facts = [
            {"fact_id": "fact_001", "epistemic_state": "Validated", "metadata": {}},
            {"fact_id": "fact_002", "epistemic_state": "Validated", "metadata": {"restricted": "2026-07-12T10:00:00Z"}},
            {"fact_id": "fact_003", "epistemic_state": "Collapsed", "metadata": {}}
        ]
        
        result = get_facts_for_recall(facts)
        assert len(result) == 1
        assert result[0]["fact_id"] == "fact_001"
    
    def test_list_facts_for_recall_with_mock_store(self):
        """Тест: list_facts_for_recall работает с mock store."""
        # Создаем mock функцию get_all_facts
        def mock_get_all_facts(epistemic_state=None, domain=None):
            return [
                {"fact_id": "fact_001", "epistemic_state": "Validated", "metadata": {}},
                {"fact_id": "fact_002", "epistemic_state": "Validated", "metadata": {"restricted": "2026-07-12T10:00:00Z"}},
                {"fact_id": "fact_003", "epistemic_state": "Collapsed", "metadata": {}}
            ]
        
        result = list_facts_for_recall(mock_get_all_facts)
        assert len(result) == 1
        assert result[0]["fact_id"] == "fact_001"
    
    def test_list_facts_for_recall_with_args(self):
        """Тест: list_facts_for_recall передает аргументы функции."""
        def mock_get_all_facts(epistemic_state=None, domain=None):
            # Возвращаем только Validated факты, если указан epistemic_state
            if epistemic_state == "Validated":
                return [
                    {"fact_id": "fact_001", "epistemic_state": "Validated", "metadata": {}},
                    {"fact_id": "fact_002", "epistemic_state": "Validated", "metadata": {"restricted": "2026-07-12T10:00:00Z"}}
                ]
            return []
        
        result = list_facts_for_recall(mock_get_all_facts, epistemic_state="Validated")
        assert len(result) == 1
        assert result[0]["fact_id"] == "fact_001"
    
    def test_search_facts_for_recall_with_mock_search(self):
        """Тест: search_facts_for_recall работает с mock search функцией."""
        def mock_search(query, top_k=5):
            return [
                {"fact_id": "fact_001", "epistemic_state": "Validated", "metadata": {}},
                {"fact_id": "fact_002", "epistemic_state": "Validated", "metadata": {"restricted": "2026-07-12T10:00:00Z"}}
            ]
        
        result = search_facts_for_recall(mock_search, "test query", top_k=5)
        assert len(result) == 1
        assert result[0]["fact_id"] == "fact_001"


class TestEdgeCases:
    """Тесты для крайних случаев."""
    
    def test_metadata_none(self):
        """Тест: факт с metadata=None."""
        policy = RecallPolicy()
        
        fact = {
            "fact_id": "fact_001",
            "epistemic_state": "Validated",
            "metadata": None
        }
        
        assert policy.is_fact_allowed_for_recall(fact) is True
    
    def test_metadata_empty_dict(self):
        """Тест: факт с пустым metadata."""
        policy = RecallPolicy()
        
        fact = {
            "fact_id": "fact_001",
            "epistemic_state": "Validated",
            "metadata": {}
        }
        
        assert policy.is_fact_allowed_for_recall(fact) is True
    
    def test_restricted_empty_string(self):
        """Тест: restricted как пустая строка."""
        policy = RecallPolicy()
        
        fact = {
            "fact_id": "fact_001",
            "epistemic_state": "Validated",
            "metadata": {"restricted": ""}
        }
        
        # Пустая строка считается falsy в Python
        assert policy.is_fact_allowed_for_recall(fact) is True
    
    def test_restricted_zero(self):
        """Тест: restricted как 0."""
        policy = RecallPolicy()
        
        fact = {
            "fact_id": "fact_001",
            "epistemic_state": "Validated",
            "metadata": {"restricted": 0}
        }
        
        # 0 считается falsy в Python
        assert policy.is_fact_allowed_for_recall(fact) is True
    
    def test_multiple_exclusion_reasons(self):
        """Тест: факт с несколькими причинами для исключения."""
        policy = RecallPolicy()
        
        # Факты, которые должны быть исключены по нескольким причинам
        facts = [
            {
                "fact_id": "fact_001",
                "epistemic_state": "Collapsed",
                "metadata": {"restricted": "2026-07-12T10:00:00Z"}
            },
            {
                "fact_id": "fact_002", 
                "epistemic_state": "Deprecated",
                "metadata": {"erasure_status": "erased"}
            }
        ]
        
        filtered = policy.filter_facts(facts)
        assert len(filtered) == 0
