"""Bounded measurement fixture for the Cognitive Evidence-Use Contract.

This fixture measures only stages that Titan can currently observe directly:

    R = retrieved / selected facts supplied to the answer path
    S = facts actually serialized into Titan's system prompt
    T = serialized evidence that survives provider-specific message packing

It intentionally does NOT claim:

    U = evidence demonstrably used by the model
    A = evidence demonstrably supporting the reported answer

U and A remain NOT_ESTABLISHED in this fixture. Those stages require separate
attribution evidence. Prompt presence, message transmission, model self-report,
or answer change are not treated here as proof of internal causal use or answer
support.

Scope: test-only. No runtime behavior is changed.
"""
from __future__ import annotations

import server
from core.llm_router import (
    compact_messages_for_deepseek,
    message_content_char_limit_for_provider,
)


def _fact(marker: str, claim: str) -> dict:
    return {
        "id": marker,
        "source": marker,
        "confidence": 0.91,
        "claim": claim,
    }


def test_retrieved_facts_are_serialized_into_the_answer_system_prompt():
    """R -> S is observable for facts supplied to the current prompt builder."""
    facts = [
        _fact("RSTA-FACT-ALPHA", "The alpha fixture value is 17."),
        _fact("RSTA-FACT-BETA", "The beta fixture value is 29."),
    ]

    system = server._build_system_prompt(facts)

    # R: both facts are present in the selected/retrieved input list.
    retrieved_markers = {fact["id"] for fact in facts}
    assert retrieved_markers == {"RSTA-FACT-ALPHA", "RSTA-FACT-BETA"}

    # S: both marker-bearing facts are actually serialized into the prompt.
    assert "RSTA-FACT-ALPHA" in system
    assert "The alpha fixture value is 17." in system
    assert "RSTA-FACT-BETA" in system
    assert "The beta fixture value is 29." in system

    # The legacy serializer preserves only a bounded projection of each fact.
    # Rich metadata not referenced by _build_system_prompt must not be inferred
    # to have reached S merely because it existed at R.
    enriched = [
        {
            **facts[0],
            "fact_id": "internal-alpha-id",
            "epistemic_state": "validated",
            "truth_status": "current",
            "metadata": {"qualifier": "fixture-only"},
        }
    ]
    enriched_system = server._build_system_prompt(enriched)
    assert "internal-alpha-id" not in enriched_system
    assert "epistemic_state" not in enriched_system
    assert "truth_status" not in enriched_system
    assert "fixture-only" not in enriched_system


def test_deepseek_packing_can_drop_tail_evidence_from_real_titan_serialization():
    """Real Titan S -> provider-packed T is observable and can be lossy."""
    early_marker = "RSTA-EARLY-EVIDENCE"
    tail_marker = "RSTA-TAIL-EVIDENCE"
    limit = message_content_char_limit_for_provider("deepseek")
    assert limit is not None

    # Build S through Titan's actual serializer, not a hand-built surrogate.
    # The first fact deliberately exceeds the provider message limit so a later
    # fact can be present in S while being absent from transmitted T.
    facts = [
        _fact(early_marker, "x" * (limit + 500)),
        _fact(tail_marker, "This tail fact must be serialized before packing."),
    ]
    serialized_system = server._build_system_prompt(facts)

    # S: both evidence markers are present in the actual Titan system prompt.
    assert early_marker in serialized_system
    assert tail_marker in serialized_system
    assert len(serialized_system) > limit

    packed = compact_messages_for_deepseek(
        [{"role": "system", "content": serialized_system}]
    )
    transmitted_system = packed[0]["content"]

    # T: existing DeepSeek packing preserves the early marker while dropping
    # later serialized evidence and recording the truncation explicitly.
    assert len(transmitted_system) <= limit
    assert early_marker in transmitted_system
    assert tail_marker not in transmitted_system
    assert "truncated by Velantrim console" in transmitted_system

    # No assertion here promotes T into U or A: both remain NOT_ESTABLISHED.
