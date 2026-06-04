"""ModeRouter MVP — PERSONAL / VELANTRIM / UMWELT."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def _enable_router(monkeypatch):
    monkeypatch.setenv("ENABLE_MODE_ROUTER", "1")
    monkeypatch.setenv("ENABLE_INNENWELT", "1")
    from core.feature_config import clear_config_cache

    clear_config_cache()
    yield
    clear_config_cache()


class TestModeRouterCore:
    def test_normalize_invalid(self):
        from core.router.mode_router import normalize_lens

        with pytest.raises(ValueError):
            normalize_lens("INVALID")

    def test_velantrim_filters_validated(self):
        from core.router.mode_router import apply_lens

        facts = [
            {
                "fact_id": "a",
                "claim": "гипотеза",
                "epistemic_state": "Observed",
                "confidence": 0.9,
            },
            {
                "fact_id": "b",
                "claim": "проверено",
                "epistemic_state": "Validated",
                "confidence": 0.9,
            },
        ]
        routed = apply_lens("тест", facts, "VELANTRIM")
        assert routed.lens == "VELANTRIM"
        assert any(f["fact_id"] == "b" for f in routed.facts)

    def test_umwelt_perspectives(self):
        from core.router.mode_router import apply_lens, format_lens_answer

        routed = apply_lens("дерево у дома", [], "UMWELT")
        assert routed.lens == "UMWELT"
        assert len(routed.lens_meta.get("perspectives", [])) >= 2
        text = format_lens_answer("базовый ответ", routed)
        assert "Umwelt" in text
        assert "Инженер" in text or "инженер" in text.lower()


class TestModeRouterAPI:
    @pytest.fixture
    def client(self, tmp_path, monkeypatch):
        db = str(tmp_path / "router.db")
        monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
        monkeypatch.setenv("VELANTRIM_DB_PATH", db)
        monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "false")
        monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
        monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "0")
        monkeypatch.setenv("LLM_PROVIDER", "none")
        from core.feature_config import clear_config_cache
        from core.goal_stack import reset_goal_stack

        clear_config_cache()
        reset_goal_stack()
        for mod in list(sys.modules.keys()):
            if mod.startswith(("server", "core.")):
                del sys.modules[mod]
        from fastapi.testclient import TestClient

        import server as srv

        with TestClient(srv.app) as c:
            c.headers.update({"X-Api-Key": "test-key"})
            yield c

    def test_router_modes(self, client):
        r = client.get("/router/modes")
        assert r.status_code == 200
        body = r.json()
        assert body["enabled"] is True
        ids = {m["id"] for m in body["modes"]}
        assert ids == {"PERSONAL", "VELANTRIM", "UMWELT"}

    def test_router_route_umwelt(self, client):
        r = client.post(
            "/router/route",
            json={"query": "дождь и дерево", "response_lens": "UMWELT"},
        )
        assert r.status_code == 200
        assert r.json()["lens"] == "UMWELT"
        assert len(r.json()["lens_meta"]["perspectives"]) >= 2
