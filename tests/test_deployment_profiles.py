"""Тесты профилей развёртывания (витрина / router)."""

from __future__ import annotations

import sys

import pytest


@pytest.fixture(autouse=True)
def _clear_cfg():
    from core.feature_config import clear_config_cache

    clear_config_cache()
    yield
    clear_config_cache()


def test_list_profiles_has_seven():
    from core.deployment_profiles import list_profiles

    ids = {p["id"] for p in list_profiles()}
    assert ids == {
        "citizen",
        "personal",
        "company",
        "science",
        "education",
        "research",
        "developer",
    }


def test_resolve_query_citizen_defaults():
    from core.deployment_profiles import resolve_query_params

    eff, landmark = resolve_query_params(
        profile="citizen",
        mode="BALANCED",
        response_lens="VELANTRIM",
        domain=None,
        top_k=3,
        use_llm=True,
    )
    assert eff["response_lens"] == "PERSONAL"
    assert eff["domain"] == "personal"
    assert landmark["profile"] == "citizen"


def test_explicit_mode_overrides_profile():
    from core.deployment_profiles import resolve_query_params

    eff, _ = resolve_query_params(
        profile="citizen",
        mode="PRECISION",
        response_lens="VELANTRIM",
        domain=None,
        top_k=3,
        use_llm=True,
    )
    assert eff["mode"] == "PRECISION"


def test_profiles_api(tmp_path, monkeypatch):
    monkeypatch.setenv("VELANTRIM_API_KEY", "prof-key")
    monkeypatch.setenv("VELANTRIM_DB_PATH", str(tmp_path / "p.db"))
    monkeypatch.setenv("VELANTRIM_NGRAM_DB", str(tmp_path / "n.db"))
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
    monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "false")
    monkeypatch.setenv("VELANTRIM_PROFILE", "personal")

    for mod in list(sys.modules.keys()):
        if mod.startswith(("server", "core.", "api.")):
            del sys.modules[mod]

    from fastapi.testclient import TestClient

    import server as srv

    with TestClient(srv.app) as c:
        r = c.get("/profiles")
        assert r.status_code == 200
        body = r.json()
        assert len(body["profiles"]) == 7
        assert body["current"]["id"] == "personal"

        r2 = c.get("/profiles/citizen")
        assert r2.status_code == 200
        assert r2.json()["emoji"] == "🏠"

        r3 = c.post(
            "/query",
            headers={"X-Api-Key": "prof-key"},
            json={"profile": "citizen", "query": "тест профиля"},
        )
        assert r3.status_code == 200
        data = r3.json()
        assert data.get("profile_landmark", {}).get("profile") == "citizen"
        assert data.get("effective_params", {}).get("response_lens") == "PERSONAL"
