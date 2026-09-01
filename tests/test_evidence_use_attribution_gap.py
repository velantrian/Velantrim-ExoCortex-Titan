"""Bounded negative-authority fixture for Titan evidence attribution.

This fixture does NOT claim to measure model internals. It checks a narrower,
observable property of Titan's current /query trace path:

- changing the set of pipeline facts can change ``source_fact_ids``;
- a harness-controlled answer can remain identical under that change;
- therefore ``source_fact_ids`` cannot, by itself, establish semantic use (U)
  or answer support (A).

Trace membership records selected/available fact IDs on the current query
path. It does not by itself establish semantic use or answer support.

The fixture is intentionally test-only. It does not introduce an attribution
engine, change runtime behavior, or promote harness answer invariance to
proof of non-use or a real model's hidden causal process.
"""
from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

CONTROLLED_ANSWER = "CONTROLLED-ANSWER-UNCHANGED"
FACT_A_ID = "fact-A"


@pytest.mark.asyncio
async def test_source_fact_ids_do_not_establish_use_or_answer_support(monkeypatch):
    """source_fact_ids alone are insufficient evidence to establish U or A."""
    # Import at call time so the spy attaches to the live modules used by
    # server.query after earlier tests reload server/core.*.
    srv = importlib.import_module("server")
    memory_ops_mod = importlib.import_module("core.memory_ops")
    event_bridge_mod = importlib.import_module("core.event_bridge")
    truth_policy_runtime_mod = importlib.import_module("core.truth_policy_runtime")

    captured: list[dict] = []
    runs = iter(
        [
            [
                {
                    "fact_id": FACT_A_ID,
                    "source": "fixture",
                    "confidence": 0.99,
                    "claim": "Alpha evidence is present in the pipeline fact set.",
                }
            ],
            [],
        ]
    )

    def fake_pipeline_run(query: str, mode: str, domain: str | None):
        del query, mode, domain
        return {
            "facts": next(runs),
            "answer": CONTROLLED_ANSWER,
            "error": None,
        }

    def spy_save_trace(self, **kwargs):
        # Production seam used by server.query:
        # get_memory_ops().save_trace(...) → MemoryOpsStore.save_trace
        del self
        captured.append(kwargs)
        return {"trace_id": f"fixture-trace-{len(captured)}"}

    async def fake_query_completed(**kwargs):
        del kwargs

    monkeypatch.setattr(srv, "pipeline_run", fake_pipeline_run)
    monkeypatch.setattr(memory_ops_mod.MemoryOpsStore, "save_trace", spy_save_trace)
    monkeypatch.setattr(event_bridge_mod, "on_query_completed", fake_query_completed)
    monkeypatch.setattr(
        truth_policy_runtime_mod,
        "evaluate_configured_truth_policy_runtime",
        lambda *args, **kwargs: SimpleNamespace(
            truth_block=None,
            blocks_llm=False,
        ),
    )

    request = srv.QueryRequest(
        query="bounded attribution fixture",
        use_llm=False,
    )

    response_a = await srv.query(request)
    response_b = await srv.query(request)

    # Anti-silent-failure canary: production wraps save_trace in except-skip.
    assert response_a.reasoning_trace_id is not None
    assert response_b.reasoning_trace_id is not None
    assert response_a.reasoning_trace_id != response_b.reasoning_trace_id

    # Answer equality is harness-controlled and does not prove evidence
    # non-use or causal irrelevance. It only shows that different trace
    # membership can coexist with the same externally observed answer.
    assert response_a.answer == CONTROLLED_ANSWER
    assert response_b.answer == CONTROLLED_ANSWER
    assert response_a.answer == response_b.answer

    assert len(captured) == 2, (
        "production MemoryOpsStore.save_trace was not intercepted; "
        f"reasoning_trace_id={response_a.reasoning_trace_id!r}/"
        f"{response_b.reasoning_trace_id!r}"
    )
    assert captured[0]["source_fact_ids"] == [FACT_A_ID]
    assert captured[1]["source_fact_ids"] == []
    assert captured[0]["source_fact_ids"] != captured[1]["source_fact_ids"]
    assert captured[0]["answer"] == captured[1]["answer"] == CONTROLLED_ANSWER
