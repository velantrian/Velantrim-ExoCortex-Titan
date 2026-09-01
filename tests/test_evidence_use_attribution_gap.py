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

from types import SimpleNamespace

import pytest

import server
import core.event_bridge as event_bridge
import core.truth_policy_runtime as truth_policy_runtime
from core.memory_ops import MemoryOpsStore

CONTROLLED_ANSWER = "CONTROLLED-ANSWER-UNCHANGED"
FACT_A_ID = "fact-A"


@pytest.mark.asyncio
async def test_source_fact_ids_do_not_establish_use_or_answer_support(monkeypatch):
    """source_fact_ids alone are insufficient evidence to establish U or A."""
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

    monkeypatch.setattr(server, "pipeline_run", fake_pipeline_run)
    monkeypatch.setattr(MemoryOpsStore, "save_trace", spy_save_trace)
    monkeypatch.setattr(event_bridge, "on_query_completed", fake_query_completed)
    monkeypatch.setattr(
        truth_policy_runtime,
        "evaluate_configured_truth_policy_runtime",
        lambda *args, **kwargs: SimpleNamespace(
            truth_block=None,
            blocks_llm=False,
        ),
    )

    request = server.QueryRequest(
        query="bounded attribution fixture",
        use_llm=False,
    )

    response_a = await server.query(request)
    response_b = await server.query(request)

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

    assert len(captured) == 2
    assert captured[0]["source_fact_ids"] == [FACT_A_ID]
    assert captured[1]["source_fact_ids"] == []
    assert captured[0]["source_fact_ids"] != captured[1]["source_fact_ids"]
    assert captured[0]["answer"] == captured[1]["answer"] == CONTROLLED_ANSWER
