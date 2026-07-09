"""CognitiveFactStore v9.2–9.3."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mem_db(tmp_path, monkeypatch):
    import core.memory as mem
    from core.cognitive_store import reset_cognitive_store

    db = str(tmp_path / "cstore.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db)
    monkeypatch.setenv("ENABLE_COGNITIVE_STORE", "1")
    monkeypatch.setenv("ENABLE_DOMAIN_TAGS", "1")
    monkeypatch.setenv("ENABLE_EVENT_BUS", "0")
    from core.feature_config import clear_config_cache

    clear_config_cache()
    reset_cognitive_store()
    store = mem.make_store(db)
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
    monkeypatch.setattr(mem, "_L0", store._l0)
    yield store
    reset_cognitive_store()
    clear_config_cache()


class TestCognitiveStore:
    def test_save_and_get_with_raw(self, mem_db):
        from core.cognitive_store import CognitiveFactStore, get_cognitive_store

        cf = CognitiveFactStore.create_observed(
            "Текст для L0 и L1",
            "test",
            metadata={"domain": "science"},
        )
        assert get_cognitive_store().save(cf) is True
        loaded = get_cognitive_store().get(cf.id, include_raw=True)
        assert loaded is not None
        assert loaded.canonical_text == cf.canonical_text
        assert loaded.raw_input == "Текст для L0 и L1"
        assert loaded.domain == "science"

    def test_list_by_domain(self, mem_db):
        from core.cognitive_store import CognitiveFactStore, get_cognitive_store

        get_cognitive_store().save(
            CognitiveFactStore.create_observed(
                "инженерный расчёт", "s", metadata={"domain": "engineering"}
            )
        )
        get_cognitive_store().save(
            CognitiveFactStore.create_observed(
                "научный факт", "s", metadata={"domain": "science"}
            )
        )
        eng = get_cognitive_store().list(domain="engineering")
        assert len(eng) == 1
        assert eng[0].domain == "engineering"

    def test_transition(self, mem_db):
        from core.cognitive_store import CognitiveFactStore, get_cognitive_store

        cf = CognitiveFactStore.create_observed("x", "s")
        get_cognitive_store().save(cf)
        get_cognitive_store().transition(cf.id, "Hypothesized")
        get_cognitive_store().transition(cf.id, "Supported")
        updated = get_cognitive_store().transition(cf.id, "Validated")
        assert updated is not None
        assert updated.epistemic_state == "Validated"


class TestCognitiveStoreAPI:
    @pytest.fixture
    def client(self, mem_db, monkeypatch):
        monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
        monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
        monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "0")
        for mod in list(sys.modules.keys()):
            if mod.startswith(("server", "core.", "app.")):
                del sys.modules[mod]
        from fastapi.testclient import TestClient

        import server as srv

        with TestClient(srv.app) as c:
            c.headers.update({"X-Api-Key": "test-key"})
            yield c

    def test_cognitive_facts_crud(self, client):
        r = client.post(
            "/cognitive/facts",
            json={
                "claim": "Velantrim CognitiveFactStore работает",
                "source": "test",
                "domain": "system",
            },
        )
        assert r.status_code == 201
        fid = r.json()["cognitive_fact"]["id"]
        assert r.json()["cognitive_fact"]["raw_input"] is not None
        r2 = client.get(f"/facts/{fid}/cognitive", params={"include_raw": "true"})
        assert r2.status_code == 200
        r3 = client.get("/cognitive/facts", params={"domain": "system"})
        assert r3.status_code == 200
        assert r3.json()["total"] >= 1
