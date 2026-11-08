"""End-to-end: distinct memory records must reach the system prompt sent to the model.

Path under test (no real LLM, no network):

    server.query → core.pipeline.run → build_facts_pack → FactsPackBuilder
    → server._build_system_prompt → server._llm_generate → core.llm_router.chat_complete

Only retrieval/persistence inputs and the provider boundary are replaced. A fix
in FactsPack alone is not enough: this checks the prompt that actually leaves
``server.query`` for the provider, plus the remote-egress sanitizer applied to it.

Scope note: this test checks claim text and the fact ids returned to the API
caller. It deliberately does not require ``fact_id`` or ``epistemic_state`` in
the prompt: ``tests/test_prompt_epistemic_boundary.py`` (PR #453) currently
keeps them out of the prompt serialization, and changing that contract is a
separate policy decision.
"""
from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from core.llm_router import LlmCallConfig
from core.remote_egress import sanitize_remote_system_prompt

# Pairs of distinct records whose wording overlaps. In each pair the second record
# has the lower confidence, so the former token-overlap dedup dropped it.
RECORDS = [
    ("e2e-neg-a", "Руслан одобрил миграцию на PostgreSQL", 0.90),
    ("e2e-neg-b", "Руслан не одобрил миграцию на PostgreSQL", 0.80),
    ("e2e-cond-a", "Удаление архива разрешено", 0.90),
    ("e2e-cond-b", "Удаление архива разрешено только после подтверждения владельца", 0.70),
    ("e2e-id-a", "Правило хранения действует на уровне L1", 0.90),
    ("e2e-id-b", "Правило хранения действует на уровне L2", 0.85),
    ("e2e-status-a", "Статус решения ADR-12: принято", 0.90),
    ("e2e-status-b", "Статус решения ADR-12: отменено", 0.80),
    ("e2e-num-a", "Срок хранения логов 30 дней", 0.90),
    ("e2e-num-b", "Срок хранения логов 7 дней", 0.80),
    ("e2e-role-a", "Alice paid Bob", 0.90),
    ("e2e-role-b", "Bob paid Alice", 0.80),
]

QUERY = "Что известно о правилах хранения, миграции и решении ADR-12?"


@pytest.mark.asyncio
async def test_distinct_overlapping_records_reach_the_provider_prompt(monkeypatch):
    # Import at call time: earlier tests may reload server / core.* modules.
    srv = importlib.import_module("server")
    pipeline_mod = importlib.import_module("core.pipeline")
    llm_router_mod = importlib.import_module("core.llm_router")
    memory_ops_mod = importlib.import_module("core.memory_ops")
    event_bridge_mod = importlib.import_module("core.event_bridge")
    truth_policy_runtime_mod = importlib.import_module("core.truth_policy_runtime")

    persisted = {
        fid: {
            "fact_id": fid,
            "claim": claim,
            "source": "src:e2e",
            "confidence": conf,
            "epistemic_state": "Validated",
            "claim_type": "WORLD_FACT",
            "origin_type": "USER_REPORTED",
            "metadata": {},
        }
        for fid, claim, conf in RECORDS
    }
    retrieved = [
        {"id": fid, "text": claim, "retrieval_score": 0.9}
        for fid, claim, _ in RECORDS
    ]

    monkeypatch.setattr(pipeline_mod, "retrieve", lambda query, domain=None: list(retrieved))
    monkeypatch.setattr(pipeline_mod, "get_fact", lambda fid: dict(persisted[fid]) if fid in persisted else None)
    monkeypatch.setattr(
        truth_policy_runtime_mod,
        "evaluate_configured_truth_policy_runtime",
        lambda *args, **kwargs: SimpleNamespace(truth_block=None, blocks_llm=False),
    )
    monkeypatch.setattr(
        memory_ops_mod.MemoryOpsStore,
        "save_trace",
        lambda self, **kwargs: {"trace_id": "e2e-trace"},
    )

    async def _noop_query_completed(**kwargs):
        del kwargs

    monkeypatch.setattr(event_bridge_mod, "on_query_completed", _noop_query_completed)

    cfg = LlmCallConfig(provider="openai", api_key="synthetic-test-key", model="gpt-4o")
    monkeypatch.setattr(srv, "_resolve_llm_config_for_request", lambda req: cfg)

    seen_systems: list[str] = []

    async def fake_chat_complete(received_cfg, prompt, system="", **kwargs):
        del received_cfg, prompt, kwargs
        seen_systems.append(system)
        return "SYNTHETIC MODEL ANSWER"

    monkeypatch.setattr(llm_router_mod, "chat_complete", fake_chat_complete)

    response = await srv.query(srv.QueryRequest(query=QUERY, use_llm=True))

    assert response.error is None
    assert response.llm_answer == "SYNTHETIC MODEL ANSWER"
    assert len(seen_systems) == 1, "the provider boundary was not reached exactly once"

    expected_ids = {fid for fid, _, _ in RECORDS}
    assert {f["fact_id"] for f in response.facts} == expected_ids

    system_prompt = seen_systems[0]
    sanitized = sanitize_remote_system_prompt(system_prompt)
    # Line-exact match: "Удаление архива разрешено" is a prefix of its conditional
    # variant, so a plain substring check could pass on the wrong record.
    for fid, claim, _ in RECORDS:
        line = f"] {claim}\n"
        assert line in system_prompt + "\n", f"{fid} missing from provider prompt"
        assert line in sanitized + "\n", f"{fid} missing after remote-egress sanitization"
