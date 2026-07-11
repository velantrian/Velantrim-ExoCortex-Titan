"""Тесты профилей развёртывания (витрина / router)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

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


# ── PR-A follow-up: VELANTRIM_APP_ROOT path resolution ─────────────────────
# core/deployment_profiles.py computed ROOT as Path(__file__).parents[1],
# which broke once core/ is installed as a non-editable wheel (Docker):
# config/profiles/*.env is copied to /app/config/profiles/, but __file__
# pointed into site-packages, so VELANTRIM_PROFILE=personal/research etc.
# silently failed to load in the container. See core/app_paths.


def test_root_falls_back_to_source_checkout_without_env(monkeypatch):
    import core.deployment_profiles as dp

    monkeypatch.delenv("VELANTRIM_APP_ROOT", raising=False)
    root = dp._root()
    assert root == Path(dp.__file__).resolve().parents[1]
    assert (root / "config" / "profiles" / "citizen.env").is_file()


def test_load_profile_env_uses_app_root_override(monkeypatch, tmp_path):
    """Simulated Docker layout: config/profiles/ lives under a directory
    that has nothing to do with dp.__file__'s location."""
    import core.deployment_profiles as dp

    fake_root = tmp_path / "app"
    profiles_dir = fake_root / "config" / "profiles"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "citizen.env").write_text("VELANTRIM_PROFILE_TEST_MARKER=1\n")

    monkeypatch.setenv("VELANTRIM_APP_ROOT", str(fake_root))
    monkeypatch.setattr(dp, "ROOT", dp._root())
    # load_profile_env() sets VELANTRIM_PROFILE directly via os.environ,
    # bypassing monkeypatch's own tracking. monkeypatch.delenv(..., raising=
    # False) on an already-absent key is a no-op that registers NO teardown
    # action at all (nothing to "undo"), so it would NOT have cleaned up
    # after that raw assignment — leaking VELANTRIM_PROFILE=citizen into
    # every test that runs afterward. monkeypatch.setenv always records a
    # rollback (to "absent") regardless of prior state, so use that instead.
    monkeypatch.setenv("VELANTRIM_PROFILE", "")

    path = dp.load_profile_env("citizen")
    assert path == fake_root.resolve() / "config" / "profiles" / "citizen.env"
    assert os.environ.pop("VELANTRIM_PROFILE_TEST_MARKER", None) == "1"


def test_load_profile_env_missing_file_raises_cleanly(monkeypatch, tmp_path):
    import core.deployment_profiles as dp

    empty_root = tmp_path / "app-without-config"
    empty_root.mkdir()
    monkeypatch.setenv("VELANTRIM_APP_ROOT", str(empty_root))
    monkeypatch.setattr(dp, "ROOT", dp._root())

    with pytest.raises(FileNotFoundError):
        dp.load_profile_env("citizen")
