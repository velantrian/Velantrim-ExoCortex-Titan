"""Umwelt MVP — store layer 99, seed, registry, query integration."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def umwelt_db(tmp_path, monkeypatch):
    import core.memory as mem
    from core.goal_stack import reset_goal_stack
    from core.umwelt_store import reset_umwelt_store

    db = str(tmp_path / "umwelt.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db)
    monkeypatch.setenv("ENABLE_UMWELT_STORE", "1")
    monkeypatch.setenv("ENABLE_UMWELT_AUTO_SEED", "0")
    monkeypatch.setenv("ENABLE_MODE_ROUTER", "1")
    from core.feature_config import clear_config_cache

    clear_config_cache()
    reset_umwelt_store()
    reset_goal_stack()
    store = mem.make_store(db)
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
    monkeypatch.setattr(mem, "_L0", store._l0)
    yield db
    reset_umwelt_store()
    clear_config_cache()


# ── PR-A follow-up: VELANTRIM_APP_ROOT path resolution ─────────────────────
# core/umwelt_store.py computed DEFAULT_SEED_PATH as Path(__file__).parents[1],
# which broke once core/ is installed as a non-editable wheel (Docker):
# docs/seed/umwelt_mvp_seed.json is copied to /app/docs/seed/, but __file__
# pointed into site-packages, so the default (ENABLE_UMWELT_AUTO_SEED=1)
# auto-seed at startup silently failed in the container. See core/app_paths.


def test_default_seed_path_falls_back_to_source_checkout(monkeypatch):
    import core.umwelt_store as store_mod

    monkeypatch.delenv("VELANTRIM_APP_ROOT", raising=False)
    from core.app_paths import resolve_app_root

    expected = resolve_app_root(store_mod.__file__) / "docs" / "seed" / "umwelt_mvp_seed.json"
    assert expected.is_file()


def test_load_seed_file_uses_app_root_override(tmp_path, umwelt_db):
    """Simulated Docker layout: docs/seed/ lives under a directory that
    has nothing to do with core/umwelt_store.py's own location."""
    from core.umwelt_store import get_umwelt_store, load_seed_file

    fake_root = tmp_path / "app"
    seed_dir = fake_root / "docs" / "seed"
    seed_dir.mkdir(parents=True)
    seed_path = seed_dir / "umwelt_mvp_seed.json"
    seed_path.write_text(
        '{"perceptions": [{"object": "rock", "perceiver_id": "agent:tester", '
        '"perceiver": "tester", "statement": "a rock is hard"}]}',
        encoding="utf-8",
    )

    # load_seed_file(path=...) takes an explicit path — this is the same
    # resolution DEFAULT_SEED_PATH does at import time via VELANTRIM_APP_ROOT,
    # exercised directly here without needing to reload the module.
    r = load_seed_file(path=seed_path)
    assert r["loaded"] == 1
    assert get_umwelt_store().count() == 1


def test_load_seed_file_missing_path_raises_cleanly(tmp_path, umwelt_db):
    from core.umwelt_store import load_seed_file

    with pytest.raises(FileNotFoundError):
        load_seed_file(path=tmp_path / "does-not-exist.json")


class TestUmweltStore:
    def test_load_seed(self, umwelt_db):
        from core.umwelt_store import get_umwelt_store, load_seed_file

        r = load_seed_file()
        assert r["loaded"] >= 8
        assert get_umwelt_store().count() >= 8

    def test_list_tree_perceptions(self, umwelt_db):
        from core.umwelt_registry import resolve_perceptions
        from core.umwelt_store import load_seed_file

        load_seed_file()
        obj, items = resolve_perceptions("расскажи про дерево")
        assert obj == "tree"
        assert len(items) >= 3
        ids = {p.perceiver_id for p in items}
        assert "agent:engineer" in ids
        assert "agent:scientist" in ids

    def test_sync_to_memory(self, umwelt_db):
        from core.memory import get_fact
        from core.umwelt_store import load_seed_file, sync_perceptions_to_memory

        load_seed_file()
        r = sync_perceptions_to_memory("tree")
        assert r["created"] >= 3
        f = get_fact("perception.tree.engineer")
        assert f is not None
        assert f["metadata"]["layer"] == 99


class TestUmweltLens:
    def test_project_from_store(self, umwelt_db):
        from core.router.umwelt_lens import project
        from core.umwelt_store import load_seed_file

        load_seed_file()
        persp = project("дерево у дома", [])
        assert len(persp) >= 3
        assert persp[0].get("source") == "umwelt_store"
        assert "statement" in persp[0] or "affordance" in persp[0]


class TestUmweltAPI:
    @pytest.fixture
    def client(self, umwelt_db, monkeypatch):
        monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
        monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "false")
        monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
        monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "0")
        monkeypatch.setenv("LLM_PROVIDER", "none")
        for mod in list(sys.modules.keys()):
            if mod.startswith(("server", "core.")):
                del sys.modules[mod]
        from fastapi.testclient import TestClient

        import server as srv

        with TestClient(srv.app) as c:
            c.headers.update({"X-Api-Key": "test-key"})
            yield c

    def test_seed_and_perceptions(self, client):
        r = client.post("/umwelt/seed", json={"sync_to_memory": True})
        assert r.status_code == 200
        assert r.json()["loaded"] >= 8
        r2 = client.get("/umwelt/perceptions", params={"object_key": "tree"})
        assert r2.status_code == 200
        body = r2.json()
        assert body["object_key"] == "tree"
        assert body["total"] >= 3

    def test_query_umwelt_lens(self, client):
        client.post("/umwelt/seed", json={})
        r = client.post(
            "/query",
            json={
                "query": "дерево",
                "response_lens": "UMWELT",
                "use_llm": False,
                "mode": "BALANCED",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("response_lens") == "UMWELT"
        ctx = data.get("lens_context") or {}
        persp = (ctx.get("meta") or {}).get("perspectives") or []
        assert len(persp) >= 3
        assert data.get("lens_context", {}).get("meta", {}).get("data_source") == "umwelt_store"
