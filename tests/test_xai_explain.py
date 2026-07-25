"""XAI-from-TRACE: без TRACE нет объяснения; LLM не используется."""

from __future__ import annotations

from core.xai_explain import explain_from_facts, explain_from_trace_elements


def test_empty_trace_denied():
    out = explain_from_trace_elements([], query="почему?")
    assert out["ok"] is False
    assert out["error"] == "empty_trace"
    assert out["llm_used"] is False


def test_explain_from_facts_no_llm():
    facts = [
        {
            "fact_id": "f1",
            "claim": "Вода кипит при 100C на уровне моря",
            "source": "textbook",
            "epistemic_state": "Validated",
            "confidence": 0.95,
            "retrieval_score": 0.8,
        },
        {
            "fact_id": "f2",
            "claim": "Давление влияет на температуру кипения",
            "source": "textbook",
            "epistemic_state": "Supported",
            "confidence": 0.7,
            "retrieval_score": 0.6,
        },
    ]
    out = explain_from_facts(facts, query="почему вода кипит?", level="detailed")
    assert out["ok"] is True
    assert out["llm_used"] is False
    assert out["policy"] == "xai_from_trace_only"
    assert out["trace_summary"]["count"] == 2
    assert "Validated/ImmutableCore" in out["human_summary"]
    assert len(out["facts"]) == 2
    assert "trace" in out


def test_full_trace_includes_text():
    facts = [
        {
            "fact_id": "f9",
            "claim": "graph equals truth",
            "source": "canon",
            "epistemic_state": "ImmutableCore",
            "confidence": 1.0,
        }
    ]
    out = explain_from_facts(facts, level="full_trace")
    assert out["ok"] is True
    assert "TRACE:" in out["trace_text"]
