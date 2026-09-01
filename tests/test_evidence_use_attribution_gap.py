"""Bounded negative-authority fixture for Titan evidence attribution.

This fixture does NOT claim to measure model internals. It checks a narrower,
observable property of Titan's current /query trace path:

- changing the set of pipeline facts can change ``source_fact_ids``;
- the reported answer can remain identical under that controlled change;
- therefore ``source_fact_ids`` cannot, by itself, establish semantic use (U)
  or answer support (A).

The fixture is intentionally test-only. It does not introduce an attribution
engine, change runtime behavior, or promote counterfactual answer invariance to
proof about a real model's hidden causal process.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import server
import core.event_bridge as event_bridge
import core.memory_ops as memory_ops
import core.truth_policy_runtime as truth_policy_runtime


class _TraceRecorder:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def save_trace(self, **kwargs):
        self.calls.append(kwargs)
        return {"trace_id": f"fixture-trace-{len(self.calls)}"}


@pytest.mark.asyncio
async def test_source_fact_ids_do_not_establish_use_or_answer_support(monkeypatch):
    """Availability trace can change while the controlled answer stays fixed."""
    recorder = _TraceRecorder()
    runs = iter(
        [
            [
                {
                    "fact_id": "UA-FACT-ALPHA",
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
            "answer": "CONTROLLED-ANSWER-UNCHANGED",
            "error": None,
        }

    async def fake_query_completed(**kwargs):
        del kwargs

    monkeypatch.setattr(server, "pipeline_run", fake_pipeline_run)
    monkeypatch.setattr(memory_ops, "get_memory_ops", lambda: recorder)
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

    with_fact = await server.query(request)
    without_fact = await server.query(request)

    # Controlled counterfactual: the answer is invariant when the supplied
    # pipeline fact is removed. This is behavioral evidence about this fixture,
    # not proof of a real model's hidden causal mechanism.
    assert with_fact.answer == "CONTROLLED-ANSWER-UNCHANGED"
    assert without_fact.answer == "CONTROLLED-ANSWER-UNCHANGED"
    assert with_fact.answer == without_fact.answer

    # Titan's current auto-trace records every pipeline fact ID even though the
    # controlled answer did not depend on that fact in this test harness.
    assert len(recorder.calls) == 2
    assert recorder.calls[0]["source_fact_ids"] == ["UA-FACT-ALPHA"]
    assert recorder.calls[1]["source_fact_ids"] == []

    # The observable conclusion is deliberately narrow:
    # source_fact_ids records availability/selection, not established U or A.
    assert recorder.calls[0]["answer"] == recorder.calls[1]["answer"]
