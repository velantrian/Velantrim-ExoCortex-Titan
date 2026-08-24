"""T1 cognitive-loop baseline: context -> retrieval -> answer without new writes.

This is intentionally narrow. It exercises existing Titan user/query surfaces with
an isolated local store and no external LLM. It does not add routing, memory tiers,
new authority, or cross-project runtime composition.

T1 questions:
1. Can an evidence-backed controlled memory item be retrieved through the real query path?
2. Can the user-facing chat surface use that memory offline?
3. Does read/answer activity avoid creating additional facts when auto-save is off?

The controlled context is admitted through Titan's existing public ESM + TruthGate
path before retrieval. The test does not weaken policy merely to make retrieval pass.

Run:
    pytest tests/test_cognitive_t1_baseline.py -v
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

T1_FACT_ID = "t1_context_fact"
T1_MARKER = "T1_COBALT_ORCHARD_7F31"
T1_CLAIM = f"The active project codename is {T1_MARKER}."


@pytest.fixture
def t1_client(tmp_path, monkeypatch):
    """Isolated Titan server with deterministic local-only behavior.

    Keep the already-collected ``core.*`` module graph canonical. Re-importing all
    core modules in-process creates duplicate class/module singletons while pytest
    test modules still hold references to the originals; that contaminates later
    tests. Titan already exposes ``memory.make_store()`` specifically for isolated
    test dependency injection, so T1 swaps only the documented mutable singletons
    and reloads the top-level server module that snapshots environment settings.
    """
    db_path = str(tmp_path / "t1.db")
    ngram_db_path = str(tmp_path / "t1_ngram.db")

    monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db_path)
    monkeypatch.setenv("VELANTRIM_NGRAM_DB", ngram_db_path)
    monkeypatch.setenv("CORE_BLOCKS_DB", str(tmp_path / "blocks.db"))
    monkeypatch.setenv("NOTEBOOK_DB", str(tmp_path / "notebook.db"))
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
    monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "false")
    monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "0")
    monkeypatch.setenv("ENABLE_VELUM", "0")
    monkeypatch.setenv("ENABLE_ETIR", "0")

    try:
        from fastapi.testclient import TestClient

        import core.memory as memory_api
        import core.ngram_index as ngram_api
        from core.feature_config import clear_config_cache
    except ImportError as exc:
        pytest.skip(f"Titan server unavailable: {exc}")

    isolated_store = memory_api.make_store(db_path)
    isolated_ngram = ngram_api.NGramIndex(ngram_db_path)

    monkeypatch.setattr(memory_api, "_GLOBAL_STORE", isolated_store)
    monkeypatch.setattr(memory_api, "_L0", isolated_store._l0)
    monkeypatch.setattr(
        memory_api,
        "_DDL_INITIALIZED",
        isolated_store._ddl_initialized_paths,
    )
    monkeypatch.setattr(ngram_api, "_GLOBAL_NGRAM", isolated_ngram)

    # server.py snapshots env and the current injected global store at import time.
    # Reload only this top-level module; never reload core.* or api.* in-process.
    saved_server = sys.modules.pop("server", None)
    clear_config_cache()

    try:
        import server as srv

        with TestClient(srv.app) as client:
            client.headers.update({"X-Api-Key": "test-key"})
            yield client, srv
    finally:
        isolated_store.close()
        sys.modules.pop("server", None)
        if saved_server is not None:
            sys.modules["server"] = saved_server
        # Clear the env-derived cache while the fixture is unwinding. The next
        # caller will rebuild it from the environment restored by monkeypatch.
        clear_config_cache()


def _fact_count(client) -> int:
    response = client.get("/facts", params={"limit": 100})
    assert response.status_code == 200, response.text
    return int(response.json().get("total", 0))


def _transition(client, new_state: str) -> None:
    response = client.patch(
        f"/facts/{T1_FACT_ID}/transition",
        json={"new_state": new_state},
    )
    assert response.status_code == 200, response.text
    assert response.json().get("epistemic_state") == new_state


def _seed_context(client) -> None:
    response = client.post(
        "/facts",
        json={
            "fact_id": T1_FACT_ID,
            "claim": T1_CLAIM,
            "source": "t1_controlled_context",
            "confidence": 0.95,
            "metadata": {
                "memory_category": "project",
                "evidence_refs": ["t1-source-a", "t1-source-b"],
            },
        },
    )
    assert response.status_code in (200, 201), response.text

    _transition(client, "Hypothesized")
    _transition(client, "Supported")
    _transition(client, "Validated")


class TestCognitiveT1Baseline:
    def test_query_retrieves_controlled_context_without_external_llm(self, t1_client):
        client, _ = t1_client
        _seed_context(client)

        response = client.post(
            "/query",
            json={
                "query": "What is the active project codename?",
                "profile": "research",
                "mode": "BALANCED",
                "use_llm": False,
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()

        claims = [str(fact.get("claim", "")) for fact in data.get("facts", [])]
        assert any(T1_MARKER in claim for claim in claims), data
        assert data.get("llm_answer") is None

    def test_user_chat_uses_context_and_read_path_does_not_create_facts(self, t1_client):
        client, _ = t1_client
        _seed_context(client)
        before = _fact_count(client)

        response = client.post(
            "/chat",
            json={
                "message": "What is the active project codename?",
                "profile": "research",
                "use_memory": True,
                "llm_enabled": False,
                "ui_lang": "en",
                "auto_save_memory": False,
                "block_memory": [],
                "chat_history": [],
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()

        assert data.get("error") is None
        assert T1_MARKER in str(data.get("reply", "")), data
        assert int(data.get("facts_count", 0)) >= 1

        after = _fact_count(client)
        assert after == before, (
            "T1 read/answer path created durable facts even though auto_save_memory=false: "
            f"before={before}, after={after}"
        )

    def test_irrelevant_query_does_not_fabricate_the_control_marker(self, t1_client):
        client, _ = t1_client
        _seed_context(client)
        unrelated = "Tell me the capital of an imaginary planet called Nereid-9."

        query_response = client.post(
            "/query",
            json={
                "query": unrelated,
                "profile": "research",
                "mode": "BALANCED",
                "use_llm": False,
            },
        )
        assert query_response.status_code == 200, query_response.text
        query_data = query_response.json()

        response = client.post(
            "/chat",
            json={
                "message": unrelated,
                "profile": "research",
                "use_memory": True,
                "llm_enabled": False,
                "ui_lang": "en",
                "auto_save_memory": False,
                "block_memory": [],
                "chat_history": [],
            },
        )
        assert response.status_code == 200, response.text
        reply = str(response.json().get("reply", ""))

        assert T1_MARKER not in reply, (
            "Unrelated query leaked the controlled project-context marker into the answer; "
            f"query_facts={query_data.get('facts', [])!r}"
        )
