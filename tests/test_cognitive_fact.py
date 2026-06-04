"""CognitiveFact v9.1 + domain tags."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mem_db(tmp_path, monkeypatch):
    import core.memory as mem

    db = str(tmp_path / "cf.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db)
    monkeypatch.setenv("ENABLE_DOMAIN_TAGS", "1")
    monkeypatch.setenv("ENABLE_COGNITIVE_FACT", "1")
    monkeypatch.setenv("ENABLE_COGNITIVE_STORE", "0")
    from core.feature_config import clear_config_cache

    clear_config_cache()
    store = mem.make_store(db)
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
    monkeypatch.setattr(mem, "_L0", store._l0)
    yield store
    clear_config_cache()


class TestDomainTags:
    def test_infer_engineering(self):
        from core.domain_tags import infer_domain

        assert infer_domain(claim="Kuzu граф для Neo4j") == "engineering"

    def test_store_sets_domain(self, mem_db):
        from core.memory import get_fact, store_fact

        store_fact(
            {
                "fact_id": "f_eng",
                "claim": "Инженер проектирует конструкцию моста",
                "source": "manual",
                "confidence": 0.9,
                "metadata": {"domain": "engineering"},
            }
        )
        f = get_fact("f_eng")
        assert f["metadata"]["domain"] == "engineering"

    def test_filter_by_domain(self, mem_db):
        from core.memory import get_all_facts, store_fact

        store_fact(
            {
                "fact_id": "f1",
                "claim": "научный эксперимент",
                "source": "s",
                "metadata": {"domain": "science"},
            }
        )
        store_fact(
            {
                "fact_id": "f2",
                "claim": "инженерный расчёт",
                "source": "s",
                "metadata": {"domain": "engineering"},
            }
        )
        sci = get_all_facts(domain="science")
        assert len(sci) == 1
        assert sci[0]["fact_id"] == "f1"


class TestCognitiveFact:
    def test_roundtrip(self, mem_db):
        from core.cognitive_fact import (
            cognitive_fact_from_store,
            store_dict_from_cognitive,
        )
        from core.memory import get_fact, store_fact

        store_fact(
            {
                "fact_id": "cf1",
                "claim": "Velantrim ExoCortex v8.6",
                "source": "test",
                "confidence": 0.85,
                "metadata": {"domain": "system"},
            }
        )
        raw = get_fact("cf1")
        cf = cognitive_fact_from_store(raw)
        assert cf.id == "cf1"
        assert cf.domain == "system"
        back = store_dict_from_cognitive(cf)
        assert back["fact_id"] == "cf1"
        assert back["claim"] == raw["claim"]


class TestCognitiveFactAPI:
    @pytest.fixture
    def client(self, mem_db, monkeypatch):
        monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
        monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
        monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "0")
        for mod in list(sys.modules.keys()):
            if mod.startswith(("server", "core.")):
                del sys.modules[mod]
        from fastapi.testclient import TestClient

        import server as srv

        with TestClient(srv.app) as c:
            c.headers.update({"X-Api-Key": "test-key"})
            yield c

    def test_cognitive_endpoint(self, client):
        client.post(
            "/facts",
            json={
                "claim": "Учёный изучает экосистему леса",
                "source": "api",
                "domain": "science",
            },
        )
        listed = client.get("/facts", params={"domain": "science"})
        assert listed.status_code == 200
        fid = listed.json()["facts"][0]["fact_id"]
        r = client.get(f"/facts/{fid}/cognitive")
        assert r.status_code == 200
        assert r.json()["cognitive_fact"]["domain"] == "science"
