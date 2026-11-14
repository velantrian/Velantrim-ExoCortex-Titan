"""Offline integration tests for prompt-grounded, observational Observer input."""
from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest


def _fact(fact_id: str, claim: str) -> dict:
    return {
        "fact_id": fact_id,
        "claim": claim,
        "source": "src:synthetic",
        "confidence": 0.95,
        "epistemic_state": "Validated",
        "metadata": {"evidence_refs": [{"source_id": "synthetic", "span": "1-2"}]},
    }


def _query_harness(monkeypatch, facts, answer):
    """Drive server.query with an in-process fake LLM; no provider is contacted."""
    srv = importlib.import_module("server")
    pipeline = importlib.import_module("core.pipeline")
    router = importlib.import_module("core.llm_router")
    memory_ops = importlib.import_module("core.memory_ops")
    events = importlib.import_module("core.event_bridge")
    truth = importlib.import_module("core.truth_policy_runtime")
    goal_stack = importlib.import_module("core.goal_stack")

    monkeypatch.setattr(memory_ops, "_GLOBAL_MEMORY_OPS", None)
    monkeypatch.setattr(goal_stack, "_stack", None)
    persisted = {
        fact["fact_id"]: {
            **fact,
            "claim_type": "WORLD_FACT",
            "origin_type": "USER_REPORTED",
            "metadata": {},
        }
        for fact in facts
    }
    monkeypatch.setattr(
        pipeline,
        "retrieve",
        lambda q, domain=None: [
            {"id": fact["fact_id"], "text": fact["claim"], "retrieval_score": 0.9}
            for fact in facts
        ],
    )
    monkeypatch.setattr(
        pipeline,
        "get_fact",
        lambda fact_id: dict(persisted[fact_id]) if fact_id in persisted else None,
    )
    monkeypatch.setattr(
        truth,
        "evaluate_configured_truth_policy_runtime",
        lambda *a, **k: SimpleNamespace(truth_block=None, blocks_llm=False),
    )
    monkeypatch.setattr(
        memory_ops.MemoryOpsStore,
        "save_trace",
        lambda self, **kwargs: {"trace_id": "synthetic-observer-test"},
    )

    async def done(**kwargs):
        return None

    monkeypatch.setattr(events, "on_query_completed", done)
    config = router.LlmCallConfig(
        provider="openai", api_key="synthetic-valid-key", model="gpt-4o"
    )
    monkeypatch.setattr(srv, "_resolve_llm_config_for_request", lambda req: config)
    prompts = []

    async def fake_chat(received_config, prompt, system="", **kwargs):
        prompts.append(system)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(router, "chat_complete", fake_chat)
    return srv, prompts


def test_observer_receives_only_records_kept_by_real_prompt_builder(monkeypatch):
    srv = importlib.import_module("server")
    budget = importlib.import_module("core.llm_context_budget")
    faithfulness = importlib.import_module("core.output_faithfulness")
    observer = importlib.import_module("core.observer")
    facts = [
        _fact("sent-1", "first prompt record"),
        _fact("omitted", "record omitted from prompt " + "Ж" * 6000),
        _fact("sent-3", "third prompt record"),
    ]
    monkeypatch.setenv(budget.DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "4000")

    # Same prompt-builder/context-report path as an unlabelled server.query request.
    report = budget.ContextReport.for_provider("deepseek")
    system = srv._build_system_prompt(facts, report=report)
    assert report.sent_fact_positions == [0, 2]
    assert report.memory_records_total == 3
    assert report.memory_records_sent == 2
    assert [item["fact_id"] for item in report.memory_records_omitted] == ["omitted"]
    assert "first prompt record" in system and "third prompt record" in system
    assert "record omitted from prompt" not in system

    captured: dict[str, object] = {}

    def capture_check(self, response, source_facts, **kwargs):
        captured["facts"] = list(source_facts)
        return faithfulness.FaithfulnessResult(
            score=1.0, grounded_claims=1, total_claims=1
        )

    monkeypatch.setattr(faithfulness.OutputFaithfulnessChecker, "check", capture_check)
    monkeypatch.setattr(
        "core.gap_detector.query_goal_alignment", lambda q, u="default": 0.5
    )
    model_input = srv._observer_model_input(
        "model response",
        facts,
        report,
        model_call_started=True,
        model_error=False,
    )
    assert model_input is not None
    answer, observer_facts = model_input
    assert answer == "model response"
    assert observer_facts == report.sent_facts(facts)
    verdict = observer.observe("q", observer_facts, answer)

    expected_ids = ["sent-1", "sent-3"]
    assert [fact["fact_id"] for fact in captured["facts"]] == expected_ids
    assert [fact["fact_id"] for fact in observer_facts] == expected_ids
    assert verdict.details["semantic_support"]["records_checked"] == 2


def test_observer_input_is_absent_without_a_successful_call():
    srv = importlib.import_module("server")
    facts = [_fact("a", "synthetic memory")]
    assert srv._observer_model_input(
        "pipeline answer", facts, None, model_call_started=False, model_error=False
    ) is None
    assert srv._observer_model_input(
        "error text", facts, None, model_call_started=True, model_error=True
    ) is None
    assert srv._observer_model_input(
        "answer", facts, None, model_call_started=True, model_error=False
    ) is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("answer", "use_llm"),
    [
        ("pipeline-only answer", False),
        ("", True),
        (" \t\n ", True),
        ("(пустой ответ Gemini)", True),
        (RuntimeError("synthetic provider failure"), True),
    ],
)
async def test_query_skips_observer_without_successful_model_answer(
    monkeypatch, answer, use_llm
):
    facts = [_fact("route-fact", "synthetic route fact")]
    srv, prompts = _query_harness(monkeypatch, facts, answer)
    runtime_flags = importlib.import_module("core.runtime_flags")
    observer = importlib.import_module("core.observer")
    monkeypatch.setattr(runtime_flags, "is_observer_enabled", lambda: True)
    calls = []
    monkeypatch.setattr(observer, "observe", lambda *a, **k: calls.append((a, k)))

    response = await srv.query(srv.QueryRequest(query="q", use_llm=use_llm))

    assert response.observer is None
    assert calls == []
    assert bool(prompts) is use_llm
