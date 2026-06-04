"""Innenwelt MVP: goals, gaps, somatic_marker, welfare."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mem_db(tmp_path, monkeypatch):
    import core.memory as mem
    from core.goal_stack import reset_goal_stack

    db = str(tmp_path / "innenwelt.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db)
    monkeypatch.setenv("ENABLE_INNENWELT", "1")
    monkeypatch.setenv("ENABLE_L6_WELFARE", "1")
    from core.feature_config import clear_config_cache

    clear_config_cache()
    store = mem.make_store(db)
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
    monkeypatch.setattr(mem, "_L0", store._l0)
    reset_goal_stack()
    yield store
    reset_goal_stack()
    clear_config_cache()


class TestGoalStack:
    def test_create_and_list(self, mem_db):
        from core.goal_stack import get_goal_stack

        g = get_goal_stack().create(
            user_id="u1",
            title="Изучить Kuzu",
            description="Граф памяти для L3",
            keywords=["kuzu", "граф"],
        )
        listed = get_goal_stack().list_goals("u1")
        assert len(listed) == 1
        assert listed[0].goal_id == g.goal_id


class TestGapDetector:
    def test_gap_when_no_facts(self, mem_db):
        from core.gap_detector import detect_gaps
        from core.goal_stack import get_goal_stack

        get_goal_stack().create(
            title="Настроить Neo4j",
            keywords=["neo4j", "graphiti"],
        )
        gaps = detect_gaps("default")
        assert len(gaps) >= 1
        assert gaps[0]["gap_type"] == "no_supporting_facts"

    def test_no_gap_when_fact_matches(self, mem_db):
        from core.gap_detector import detect_gaps
        from core.goal_stack import get_goal_stack
        from core.memory import store_fact

        get_goal_stack().create(title="Kuzu граф", keywords=["kuzu"])
        store_fact(
            {
                "fact_id": "f_kuzu",
                "claim": "Velantrim использует Kuzu для графа знаний",
                "source": "test",
                "confidence": 0.9,
            }
        )
        gaps = detect_gaps("default")
        assert gaps == []


class TestInteroception:
    def test_somatic_metadata(self):
        from core.interoception import attach_somatic_metadata

        meta, marker = attach_somatic_metadata(
            {"somatic_marker": "anxiety", "somatic_intensity": 0.8}
        )
        assert marker == "anxiety"
        assert meta["somatic_distress"] > 0.4

    def test_store_fact_somatic(self, mem_db):
        from core.memory import get_fact, store_fact

        store_fact(
            {
                "fact_id": "f_som",
                "claim": "Тема вызывает дискомфорт при обсуждении",
                "source": "user",
                "confidence": 0.7,
                "metadata": {"somatic_marker": "discomfort"},
            }
        )
        f = get_fact("f_som")
        assert f["metadata"]["somatic_marker"] == "discomfort"
        assert "somatic_distress" in f["metadata"]


class TestInnenweltAPI:
    @pytest.fixture
    def client(self, mem_db, monkeypatch):
        monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
        monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "true")
        from core.feature_config import clear_config_cache

        clear_config_cache()
        import importlib

        import server as srv

        importlib.reload(srv)
        from fastapi.testclient import TestClient

        with TestClient(srv.app) as c:
            yield c

    def test_goals_crud(self, client):
        r = client.post(
            "/goals",
            json={"title": "MHI healthy", "keywords": ["mhi", "health"]},
            headers={"X-API-Key": "test-key"},
        )
        assert r.status_code == 201
        gid = r.json()["goal_id"]
        r2 = client.get("/goals", headers={"X-API-Key": "test-key"})
        assert r2.status_code == 200
        assert r2.json()["total"] >= 1
        r3 = client.get("/gaps", headers={"X-API-Key": "test-key"})
        assert r3.status_code == 200
        assert "gaps" in r3.json()
        r4 = client.patch(
            f"/goals/{gid}",
            json={"status": "done"},
            headers={"X-API-Key": "test-key"},
        )
        assert r4.status_code == 200

    def test_innenwelt_snapshot(self, client):
        r = client.get("/innenwelt", headers={"X-API-Key": "test-key"})
        assert r.status_code == 200
        body = r.json()
        assert body["enabled"] is True
        assert "active_goals" in body
