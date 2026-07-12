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
    _EXCLUDED_EPISTEMIC_STATES,
    is_fact_allowed_for_recall,
    filter_facts_for_recall,
    get_facts_for_recall,
    list_facts_for_recall,
    search_facts_for_recall,
)


class TestExcludedEpistemicStates:
    """Тесты для исключаемых эпистемических состояний."""
    
    def test_excluded_epistemic_states(self):
        """Проверяем, что исключаемые состояния правильно определены."""
        assert "Collapsed" in _EXCLUDED_EPISTEMIC_STATES
        assert "Deprecated" in _EXCLUDED_EPISTEMIC_STATES
        assert "Validated" not in _EXCLUDED_EPISTEMIC_STATES
        assert "Supported" not in _EXCLUDED_EPISTEMIC_STATES
        assert "Observed" not in _EXCLUDED_EPISTEMIC_STATES


class TestIsFactAllowedForRecall:
    """Тесты для функции is_fact_allowed_for_recall."""
    
    def test_is_fact_allowed_for_recall_valid_fact(self):
        """Тест: валидный факт разрешен для recall."""
        valid_fact = {
            "fact_id": "fact_001",
            "claim": "Test claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Validated",
            "metadata": {}
        }
        
        assert is_fact_allowed_for_recall(valid_fact) is True
    
    def test_is_fact_allowed_for_recall_restricted_fact(self):
        """Тест: restricted-факт запрещен для recall."""
        restricted_fact = {
            "fact_id": "fact_002",
            "claim": "Restricted claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Validated",
            "metadata": {"restricted": "2026-07-12T10:00:00Z"}
        }
        
        assert is_fact_allowed_for_recall(restricted_fact) is False
    
    def test_is_fact_allowed_for_recall_restricted_false(self):
        """Тест: факт с restricted=false разрешен."""
        fact = {
            "fact_id": "fact_003",
            "claim": "Non-restricted claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Validated",
            "metadata": {"restricted": None}
        }
        
        assert is_fact_allowed_for_recall(fact) is True
    
    def test_is_fact_allowed_for_recall_collapsed_state(self):
        """Тест: факт в состоянии Collapsed запрещен."""
        collapsed_fact = {
            "fact_id": "fact_004",
            "claim": "Collapsed claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Collapsed",
            "metadata": {}
        }
        
        assert is_fact_allowed_for_recall(collapsed_fact) is False
    
    def test_is_fact_allowed_for_recall_deprecated_state(self):
        """Тест: факт в состоянии Deprecated запрещен."""
        deprecated_fact = {
            "fact_id": "fact_005",
            "claim": "Deprecated claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Deprecated",
            "metadata": {}
        }
        
        assert is_fact_allowed_for_recall(deprecated_fact) is False
    
    def test_is_fact_allowed_for_recall_erasure_status_inactive(self):
        """Тест: факт с erasure_status != active запрещен."""
        erased_fact = {
            "fact_id": "fact_006",
            "claim": "Erased claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Validated",
            "metadata": {"erasure_status": "erased"}
        }
        
        assert is_fact_allowed_for_recall(erased_fact) is False
    
    def test_is_fact_allowed_for_recall_erasure_status_active(self):
        """Тест: факт с erasure_status = active разрешен."""
        active_fact = {
            "fact_id": "fact_007",
            "claim": "Active claim",
            "source": "test_source",
            "confidence": 0.9,
            "epistemic_state": "Validated",
            "metadata": {"erasure_status": "active"}
        }
        
        assert is_fact_allowed_for_recall(active_fact) is True
    
    def test_is_fact_allowed_for_recall_empty_fact(self):
        """Тест: пустой факт запрещен."""
        assert is_fact_allowed_for_recall({}) is False
        assert is_fact_allowed_for_recall(None) is False


class TestFilterFactsForRecall:
    """Тесты для функции filter_facts_for_recall."""
    
    def test_filter_facts_mixed(self):
        """Тест: фильтрация смешанного списка фактов."""
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
        
        filtered = filter_facts_for_recall(facts)
        
        # Должны остаться только fact_001 и fact_005
        assert len(filtered) == 2
        assert filtered[0]["fact_id"] == "fact_001"
        assert filtered[1]["fact_id"] == "fact_005"
    
    def test_filter_facts_empty_list(self):
        """Тест: фильтрация пустого списка."""
        assert filter_facts_for_recall([]) == []


class TestGetFactsForRecall:
    """Тесты для функции get_facts_for_recall."""
    
    def test_get_facts_for_recall_filters(self):
        """Тест: get_facts_for_recall фильтрует restricted факты."""
        def mock_get_all_facts(epistemic_state=None, domain=None):
            return [
                {"fact_id": "fact_001", "epistemic_state": "Validated", "metadata": {}},
                {"fact_id": "fact_002", "epistemic_state": "Validated", "metadata": {"restricted": "2026-07-12T10:00:00Z"}},
                {"fact_id": "fact_003", "epistemic_state": "Collapsed", "metadata": {}}
            ]
        
        result = get_facts_for_recall(mock_get_all_facts)
        assert len(result) == 1
        assert result[0]["fact_id"] == "fact_001"
    
    def test_get_facts_for_recall_with_args(self):
        """Тест: get_facts_for_recall передает аргументы функции."""
        def mock_get_all_facts(epistemic_state=None, domain=None):
            if epistemic_state == "Validated":
                return [
                    {"fact_id": "fact_001", "epistemic_state": "Validated", "metadata": {}},
                    {"fact_id": "fact_002", "epistemic_state": "Validated", "metadata": {"restricted": "2026-07-12T10:00:00Z"}}
                ]
            return []
        
        result = get_facts_for_recall(mock_get_all_facts, epistemic_state="Validated")
        assert len(result) == 1
        assert result[0]["fact_id"] == "fact_001"


class TestListFactsForRecall:
    """Тесты для функции list_facts_for_recall."""
    
    def test_list_facts_for_recall_with_mock_store(self):
        """Тест: list_facts_for_recall работает с mock store."""
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
            if epistemic_state == "Validated":
                return [
                    {"fact_id": "fact_001", "epistemic_state": "Validated", "metadata": {}},
                    {"fact_id": "fact_002", "epistemic_state": "Validated", "metadata": {"restricted": "2026-07-12T10:00:00Z"}}
                ]
            return []
        
        result = list_facts_for_recall(mock_get_all_facts, epistemic_state="Validated")
        assert len(result) == 1
        assert result[0]["fact_id"] == "fact_001"


class TestSearchFactsForRecall:
    """Тесты для функции search_facts_for_recall."""
    
    def test_search_facts_for_recall_with_mock_search(self):
        """Тест: search_facts_for_recall работает с mock search функцией."""
        def mock_search(query, top_k=5, domain=None):
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
        fact = {
            "fact_id": "fact_001",
            "epistemic_state": "Validated",
            "metadata": None
        }
        
        assert is_fact_allowed_for_recall(fact) is True
    
    def test_metadata_empty_dict(self):
        """Тест: факт с пустым metadata."""
        fact = {
            "fact_id": "fact_001",
            "epistemic_state": "Validated",
            "metadata": {}
        }
        
        assert is_fact_allowed_for_recall(fact) is True
    
    def test_restricted_empty_string(self):
        """Тест: restricted как пустая строка."""
        fact = {
            "fact_id": "fact_001",
            "epistemic_state": "Validated",
            "metadata": {"restricted": ""}
        }
        
        assert is_fact_allowed_for_recall(fact) is True
    
    def test_restricted_zero(self):
        """Тест: restricted как 0."""
        fact = {
            "fact_id": "fact_001",
            "epistemic_state": "Validated",
            "metadata": {"restricted": 0}
        }
        
        assert is_fact_allowed_for_recall(fact) is True
    
    def test_multiple_exclusion_reasons(self):
        """Тест: факт с несколькими причинами для исключения."""
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
        
        filtered = filter_facts_for_recall(facts)
        assert len(filtered) == 0
