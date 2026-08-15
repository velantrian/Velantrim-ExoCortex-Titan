from __future__ import annotations

import importlib
import os
import sys

import pytest

from core.branch_manager import BranchManager
from core.llm_router import LlmCallConfig


_FACTS = [
    {
        "fact_id": "fact_query_roles_1",
        "claim": "SQLite serializes writes through explicit transactions.",
        "source": "test",
        "epistemic_state": "Validated",
        "confidence": 0.95,
    }
]


@pytest.mark.asyncio
async def test_no_llm_config_uses_typed_essence_without_remote_call(monkeypatch):
    import core.llm_router as llm_router

    calls: list[object] = []

    async def forbidden_chat_complete(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("chat_complete must not be called without caller-owned config")

    monkeypatch.setattr(llm_router, "chat_complete", forbidden_chat_complete)

    result = await BranchManager().reason(
        query="Как устроена изоляция SQLite?",
        roles=["ENGINEER"],
        facts=_FACTS,
        llm_config=None,
    )

    assert calls == []
    assert result.all_branches_used_llm is False
    assert result.branches[0].used_llm is False
    assert result.branches[0].confidence == 0.6
    assert result.response.startswith("Суть: SQLite serializes writes")
    assert result.branches[0].to_dict()["used_llm"] is False


@pytest.mark.asyncio
async def test_valid_caller_config_reaches_chat_complete_and_marks_real_llm(monkeypatch):
    import core.llm_router as llm_router

    cfg = LlmCallConfig(
        provider="openai",
        api_key="synthetic-test-key",
        model="gpt-4o",
        max_tokens=500,
    )
    seen: list[tuple[LlmCallConfig, str]] = []

    async def fake_chat_complete(received_cfg, prompt, system="", **kwargs):
        seen.append((received_cfg, prompt))
        return "REAL MODEL RESPONSE"

    monkeypatch.setattr(llm_router, "chat_complete", fake_chat_complete)

    result = await BranchManager().reason(
        query="Как устроена изоляция SQLite?",
        roles=["ENGINEER"],
        facts=_FACTS,
        llm_config=cfg,
    )

    assert len(seen) == 1
    assert seen[0][0] is cfg
    assert "Как устроена изоляция SQLite?" in seen[0][1]
    assert result.response == "REAL MODEL RESPONSE"
    assert result.branches[0].used_llm is True
    assert result.all_branches_used_llm is True
    assert result.branches[0].confidence == 0.8


@pytest.mark.asyncio
async def test_provider_failure_degrades_to_essence_without_fake_llm(monkeypatch):
    import core.llm_router as llm_router

    cfg = LlmCallConfig(
        provider="openai",
        api_key="synthetic-test-key",
        model="gpt-4o",
        max_tokens=500,
    )

    async def failing_chat_complete(*args, **kwargs):
        raise RuntimeError("synthetic provider failure")

    monkeypatch.setattr(llm_router, "chat_complete", failing_chat_complete)

    result = await BranchManager().reason(
        query="Как устроена изоляция SQLite?",
        roles=["ENGINEER"],
        facts=_FACTS,
        llm_config=cfg,
    )

    assert result.response.startswith("Суть: SQLite serializes writes")
    assert result.branches[0].used_llm is False
    assert result.all_branches_used_llm is False
    assert result.branches[0].confidence == 0.6


@pytest.mark.asyncio
async def test_empty_fact_fallback_is_honest_and_non_llm():
    result = await BranchManager().reason(
        query="Как устроена изоляция SQLite?",
        roles=["ENGINEER"],
        facts=[],
        llm_config=None,
    )

    assert result.response == "Нет проверенных фактов — вывод невозможен."
    assert result.branches[0].used_llm is False
    assert result.all_branches_used_llm is False
    assert result.branches[0].confidence == 0.6


@pytest.mark.asyncio
async def test_mixed_multi_branch_synthesis_is_not_all_llm(monkeypatch):
    import core.llm_router as llm_router

    cfg = LlmCallConfig(
        provider="openai",
        api_key="synthetic-test-key",
        model="gpt-4o",
        max_tokens=500,
    )
    call_count = 0

    async def partly_failing_chat_complete(received_cfg, prompt, system="", **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return "MODEL BRANCH"
        raise RuntimeError("synthetic second-branch failure")

    monkeypatch.setattr(llm_router, "chat_complete", partly_failing_chat_complete)

    result = await BranchManager().reason(
        query="Проверь архитектуру критически",
        roles=["ENGINEER", "CRITIC"],
        facts=_FACTS,
        llm_config=cfg,
    )

    assert len(result.branches) == 2
    assert {branch.used_llm for branch in result.branches} == {True, False}
    assert result.all_branches_used_llm is False


@pytest.fixture
def query_roles_client(tmp_path, monkeypatch):
    """Isolated authenticated server fixture with no external LLM by default."""
    monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
    monkeypatch.setenv("VELANTRIM_DB_PATH", str(tmp_path / "query_roles.db"))
    monkeypatch.setenv("VELANTRIM_NGRAM_DB", str(tmp_path / "query_roles_ngram.db"))
    monkeypatch.setenv("CORE_BLOCKS_DB", str(tmp_path / "blocks.db"))
    monkeypatch.setenv("NOTEBOOK_DB", str(tmp_path / "notebook.db"))
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
    monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "0")
    monkeypatch.setenv("VELANTRIM_MULTILINGUAL", "0")

    for mod in list(sys.modules):
        if mod == "server" or mod.startswith("server."):
            del sys.modules[mod]

    try:
        from fastapi.testclient import TestClient

        srv = importlib.import_module("server")
    except ImportError as exc:
        pytest.skip(f"server test dependencies unavailable: {exc}")

    client = TestClient(srv.app)
    client.headers.update({"X-Api-Key": "test-key"})
    yield client, srv
    client.close()


def test_query_roles_endpoint_deterministic_fallback_is_not_llm_answer(
    query_roles_client,
    monkeypatch,
):
    client, srv = query_roles_client
    monkeypatch.setattr(srv, "_env_llm_config", lambda: None)

    response = client.post(
        "/query/roles",
        json={"query": "Как устроена изоляция SQLite?", "roles": "ENGINEER"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Нет проверенных фактов — вывод невозможен."
    assert body["llm_answer"] is None
    assert body["mode"] == "multi_perspective"
    assert body["lens_context"]["all_branches_used_llm"] is False
    assert body["lens_context"]["branches"][0]["used_llm"] is False


def test_query_roles_endpoint_sets_llm_answer_only_after_real_model_call(
    query_roles_client,
    monkeypatch,
):
    client, srv = query_roles_client
    import core.llm_router as llm_router

    cfg = LlmCallConfig(
        provider="openai",
        api_key="synthetic-test-key",
        model="gpt-4o",
        max_tokens=500,
    )
    monkeypatch.setattr(srv, "_env_llm_config", lambda: cfg)

    async def fake_chat_complete(received_cfg, prompt, system="", **kwargs):
        assert received_cfg is cfg
        return "REAL ENDPOINT MODEL RESPONSE"

    monkeypatch.setattr(llm_router, "chat_complete", fake_chat_complete)

    response = client.post(
        "/query/roles",
        json={"query": "Как устроена изоляция SQLite?", "roles": "ENGINEER"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "REAL ENDPOINT MODEL RESPONSE"
    assert body["llm_answer"] == "REAL ENDPOINT MODEL RESPONSE"
    assert body["lens_context"]["all_branches_used_llm"] is True
    assert body["lens_context"]["branches"][0]["used_llm"] is True
