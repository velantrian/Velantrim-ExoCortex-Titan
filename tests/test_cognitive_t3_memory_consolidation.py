"""T3 cognitive baseline: explicit memory consolidation boundaries.

T3 does not introduce a new memory manager. It measures the policy already exposed
by Titan's console path for the same high-confidence memory candidate:

    suggest only -> block memory -> durable system fact

The test keeps three concepts separate:

- retention horizon: transient/block/durable;
- write permission: whether ``persist_to_system`` is explicitly enabled;
- epistemic state: Observed/Hypothesized/Supported/Validated.

A durable write must not silently imply epistemic validation.
"""
from __future__ import annotations

import os
import sys

import pytest

T3_MARKER = "T3_CONSOLIDATION_CEDAR_73"
T3_MESSAGE = f"Remember that my project launch codename is {T3_MARKER}."


@pytest.fixture
def t3_client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "t3.db")
    ngram_db_path = str(tmp_path / "t3_ngram.db")

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

    saved_server = sys.modules.pop("server", None)
    clear_config_cache()

    try:
        import server as srv

        with TestClient(srv.app) as client:
            client.headers.update({"X-Api-Key": "test-key"})
            yield client
    finally:
        isolated_store.close()
        sys.modules.pop("server", None)
        if saved_server is not None:
            sys.modules["server"] = saved_server
        clear_config_cache()


def _fact_rows(client) -> list[dict]:
    response = client.get("/facts", params={"limit": 100})
    assert response.status_code == 200, response.text
    return list(response.json().get("facts", []))


def _facts_with_marker(client) -> list[dict]:
    return [row for row in _fact_rows(client) if T3_MARKER in str(row.get("claim", ""))]


def _chat(client, *, auto_save_memory: bool, persist_to_system: bool) -> dict:
    response = client.post(
        "/chat",
        json={
            "message": T3_MESSAGE,
            "profile": "research",
            "use_memory": False,
            "llm_enabled": False,
            "ui_lang": "en",
            "auto_save_memory": auto_save_memory,
            "persist_to_system": persist_to_system,
            "block_memory": [],
            "chat_history": [],
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_auto_save_off_produces_suggestion_without_durable_write(t3_client) -> None:
    data = _chat(t3_client, auto_save_memory=False, persist_to_system=False)

    assert data.get("memory_auto_status") == "off"
    assert data.get("memory_saved") == []
    suggestions = data.get("memory_suggestions") or []
    assert any(T3_MARKER in str(item.get("claim", "")) for item in suggestions), data
    assert _facts_with_marker(t3_client) == []


def test_auto_save_without_system_permission_stays_in_block_memory(t3_client) -> None:
    data = _chat(t3_client, auto_save_memory=True, persist_to_system=False)

    saved = data.get("memory_saved") or []
    assert any(T3_MARKER in str(item.get("claim", "")) for item in saved), data
    assert all(item.get("memory_store") == "block" for item in saved), data
    assert _facts_with_marker(t3_client) == []


def test_explicit_system_persistence_creates_durable_observed_fact(t3_client) -> None:
    data = _chat(t3_client, auto_save_memory=True, persist_to_system=True)

    saved = data.get("memory_saved") or []
    assert any(T3_MARKER in str(item.get("claim", "")) for item in saved), data

    durable = _facts_with_marker(t3_client)
    assert len(durable) == 1, data
    assert durable[0].get("epistemic_state") == "Observed"


def test_durable_persistence_does_not_equal_truth_promotion(t3_client) -> None:
    _chat(t3_client, auto_save_memory=True, persist_to_system=True)
    durable = _facts_with_marker(t3_client)

    assert len(durable) == 1
    assert durable[0].get("epistemic_state") != "Validated"
    assert durable[0].get("epistemic_state") == "Observed"
