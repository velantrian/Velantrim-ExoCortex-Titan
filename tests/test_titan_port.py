"""
Тесты переноса компонентов Titan v7.5 → V8.6.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


@pytest.fixture(autouse=True)
def _reset_titan_state():
    from core.actr_activation import reset_actr_store
    from core.circuit_breaker import reset_circuit_breakers
    from core.feature_config import clear_config_cache

    reset_actr_store()
    reset_circuit_breakers()
    clear_config_cache()
    yield
    reset_actr_store()
    reset_circuit_breakers()
    clear_config_cache()


class TestOutputFaithfulness:
    def test_grounded_response_high_score(self, monkeypatch):
        monkeypatch.setenv("ENABLE_OUTPUT_FAITHFULNESS", "1")
        from core.feature_config import clear_config_cache
        from core.output_faithfulness import check_response_faithfulness

        clear_config_cache()
        fr = check_response_faithfulness(
            "Квантовая запутанность связана с физикой.",
            [{"claim": "Квантовая запутанность — физическое явление."}],
        )
        assert fr is not None
        assert fr.score >= 0.5

    def test_disabled_returns_none(self, monkeypatch):
        monkeypatch.delenv("ENABLE_OUTPUT_FAITHFULNESS", raising=False)
        from core.feature_config import clear_config_cache
        from core.output_faithfulness import check_response_faithfulness

        clear_config_cache()
        assert check_response_faithfulness("x", [{"claim": "x"}]) is None


class TestMemoryBudget:
    def test_hard_limit_blocks_insert(self, monkeypatch):
        monkeypatch.setenv("ENABLE_MEMORY_BUDGET", "1")
        monkeypatch.setenv("MEMORY_BUDGET_FACT_HARD", "1")
        from core.feature_config import clear_config_cache
        from core.memory import store_fact
        from core.memory_budget import MemoryBudgetExceededError

        clear_config_cache()
        state = {"n": 0}

        def fake_count():
            return state["n"]

        monkeypatch.setattr("core.memory_budget.count_facts", fake_count)

        store_fact(
            {
                "fact_id": "budget_f1_titan",
                "claim": "первый",
                "source": "test",
                "confidence": 0.8,
                "epistemic_state": "Observed",
            }
        )
        state["n"] = 1
        with pytest.raises(MemoryBudgetExceededError):
            store_fact(
                {
                    "fact_id": "budget_f2_titan",
                    "claim": "второй",
                    "source": "test",
                    "confidence": 0.8,
                    "epistemic_state": "Observed",
                }
            )


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_opens_after_failures(self, monkeypatch):
        monkeypatch.setenv("ENABLE_CIRCUIT_BREAKER", "1")
        from core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

        cb = CircuitBreaker("test", failure_threshold=2, timeout=60)

        async def fail():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            await cb.call(fail)
        with pytest.raises(RuntimeError):
            await cb.call(fail)
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(fail)


class TestResponseGuardian:
    def test_reject_low_confidence(self, monkeypatch):
        monkeypatch.setenv("ENABLE_RESPONSE_GUARDIAN", "1")
        from core.feature_config import clear_config_cache
        from core.response_guardian import GuardianDecision, get_response_guardian

        clear_config_cache()
        res = get_response_guardian().validate(
            response="ответ",
            confidence=0.2,
            trace=["f1"],
            sources=[{"epistemic_state": "Validated"}],
        )
        assert res.decision == GuardianDecision.REJECT

    def test_warn_majority_hypothesis(self, monkeypatch):
        monkeypatch.setenv("ENABLE_RESPONSE_GUARDIAN", "1")
        from core.feature_config import clear_config_cache
        from core.response_guardian import GuardianDecision, get_response_guardian

        clear_config_cache()
        res = get_response_guardian().validate(
            response="ответ",
            confidence=0.9,
            trace=["f1", "f2"],
            sources=[
                {"epistemic_state": "Observed"},
                {"epistemic_state": "Hypothesized"},
            ],
        )
        assert res.decision == GuardianDecision.WARN
        assert "[Частично предположение]" in (res.response or "")


class TestActrActivation:
    def test_more_access_higher_activation(self, monkeypatch):
        monkeypatch.setenv("ENABLE_ACTR_ACTIVATION", "1")
        from core.actr_activation import (
            compute_actr_activation,
            record_fact_access,
            reset_actr_store,
        )

        reset_actr_store()
        now = datetime.now(UTC)
        record_fact_access("f_actr", now - timedelta(hours=1))
        record_fact_access("f_actr", now - timedelta(minutes=30))
        record_fact_access("f_actr", now - timedelta(minutes=5))
        b_many = compute_actr_activation(
            [
                now - timedelta(hours=1),
                now - timedelta(minutes=30),
                now - timedelta(minutes=5),
            ]
        )
        b_one = compute_actr_activation([now - timedelta(hours=1)])
        assert b_many > b_one

    def test_boost_increases_score(self, monkeypatch):
        monkeypatch.setenv("ENABLE_ACTR_ACTIVATION", "1")
        from core.actr_activation import boost_retrieval_score, record_fact_access

        record_fact_access("f_boost")
        boosted = boost_retrieval_score("f_boost", 0.5)
        assert boosted >= 0.5


class TestTitanStatusEndpoint:
    def test_titan_status_api(self, tmp_path, monkeypatch):
        monkeypatch.setenv("VELANTRIM_API_KEY", "titan-test-key")
        monkeypatch.setenv("VELANTRIM_DB_PATH", str(tmp_path / "titan.db"))
        monkeypatch.setenv("VELANTRIM_NGRAM_DB", str(tmp_path / "titan_ngram.db"))
        monkeypatch.setenv("LLM_PROVIDER", "none")
        monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
        monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "false")
        monkeypatch.setenv("ENABLE_MEMORY_BUDGET", "1")
        monkeypatch.setenv("ENABLE_CIRCUIT_BREAKER", "1")

        import sys

        for mod in list(sys.modules.keys()):
            if mod.startswith(("server", "core.", "api.")):
                del sys.modules[mod]

        from core.feature_config import clear_config_cache

        clear_config_cache()

        from fastapi.testclient import TestClient

        import server as srv

        with TestClient(srv.app) as client:
            r = client.get("/titan/status")
            assert r.status_code == 401
            r = client.get("/titan/status", headers={"X-Api-Key": "titan-test-key"})
            assert r.status_code == 200
            body = r.json()
            assert body["flags"]["memory_budget"] is True
            assert "memory_budget" in body
            assert body["memory_budget"]["enabled"] is True
            assert "fact_count" in body["memory_budget"]
            assert body["circuit_breakers"]["enabled"] is True
            assert "circuits" in body["circuit_breakers"]
            assert "llm" in body["circuit_breakers"]["circuits"]


class TestPipelineIntegration:
    def test_pipeline_faithfulness_when_enabled(self, monkeypatch):
        monkeypatch.setenv("ENABLE_OUTPUT_FAITHFULNESS", "1")
        monkeypatch.setenv("VELANTRIM_DEV_MOCK", "true")
        from core.feature_config import clear_config_cache
        from core.pipeline import run

        clear_config_cache()
        result = run("тест запрос")
        if result.get("answer"):
            assert "faithfulness" in result or result.get("error")
