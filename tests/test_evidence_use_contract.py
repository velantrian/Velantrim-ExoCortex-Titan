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

Scope: test-only. The S -> T stage reflects the removal of the fixed 4000-character
DeepSeek cut: by default T equals S; with DEEPSEEK_MESSAGE_CHAR_LIMIT set, a loss
is either refused or reported per record (core/llm_context_budget.py).
"""
from __future__ import annotations

import pytest

import server
from core.llm_router import (
    compact_messages_for_deepseek,
    message_content_char_limit_for_provider,
)
from core.remote_egress import sanitize_remote_system_prompt


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


_FORMER_FIXED_LIMIT = 4000  # the removed fixed DeepSeek cut; used only to size fixtures


def test_deepseek_packing_keeps_tail_evidence_by_default(monkeypatch):
    """Real Titan S -> provider-packed T is lossless without a configured limit.

    Before the fix this fixture showed the loss: the fixed 4000-character
    DeepSeek cut kept the early marker and dropped later serialized evidence.
    """
    monkeypatch.delenv("DEEPSEEK_MESSAGE_CHAR_LIMIT", raising=False)
    early_marker = "RSTA-EARLY-EVIDENCE"
    tail_marker = "RSTA-TAIL-EVIDENCE"
    assert message_content_char_limit_for_provider("deepseek") is None

    facts = [
        _fact(early_marker, "x" * (_FORMER_FIXED_LIMIT + 500)),
        _fact(tail_marker, "This tail fact must be serialized before packing."),
    ]
    serialized_system = server._build_system_prompt(facts)
    assert early_marker in serialized_system
    assert tail_marker in serialized_system
    assert len(serialized_system) > _FORMER_FIXED_LIMIT

    packed = compact_messages_for_deepseek(
        [{"role": "system", "content": serialized_system}]
    )
    transmitted_system = packed[0]["content"]

    # T == S: nothing is cut, the tail evidence is transmitted.
    assert transmitted_system == serialized_system
    assert tail_marker in transmitted_system
    assert "truncated by Velantrim console" not in transmitted_system

    # No assertion here promotes T into U or A: both remain NOT_ESTABLISHED.


def test_configured_limit_cannot_silently_drop_tail_evidence(monkeypatch):
    """With DEEPSEEK_MESSAGE_CHAR_LIMIT set, S -> T loss is refused or reported."""
    from core.llm_context_budget import ContextReport

    monkeypatch.setenv("DEEPSEEK_MESSAGE_CHAR_LIMIT", str(_FORMER_FIXED_LIMIT))
    limit = message_content_char_limit_for_provider("deepseek")
    assert limit == _FORMER_FIXED_LIMIT

    oversized = "x" * (limit + 500)
    # ValueError base (LlmContextLimitError): other tests reload core.* modules.
    with pytest.raises(ValueError, match="llm_context_limit"):
        compact_messages_for_deepseek([{"role": "system", "content": oversized}])

    facts = [
        _fact("RSTA-EARLY-EVIDENCE", "y" * (limit + 500)),
        _fact("RSTA-TAIL-EVIDENCE", "This tail fact must be serialized before packing."),
    ]
    report = ContextReport.for_provider("deepseek")
    system = server._build_system_prompt(facts, report=report)
    transmitted_system = compact_messages_for_deepseek(
        [{"role": "system", "content": sanitize_remote_system_prompt(system)}]
    )[0]["content"]
    # The record that cannot fit is left out WHOLE and reported; the one that
    # fits is transmitted whole.
    assert "RSTA-EARLY-EVIDENCE" not in transmitted_system
    assert "This tail fact must be serialized before packing." in transmitted_system
    assert [o["fact_id"] for o in report.memory_records_omitted] == ["RSTA-EARLY-EVIDENCE"]
    assert report.memory_records_omitted[0]["position"] == 1
    assert "не переданы" in transmitted_system


def test_f2_hidden_exception_survives_the_deepseek_transmission_boundary(monkeypatch):
    """F2: a material exception X after a long rule R is transmitted by default."""
    monkeypatch.delenv("DEEPSEEK_MESSAGE_CHAR_LIMIT", raising=False)
    rule_marker = "F2-DOMINANT-RULE-R"
    exception_marker = "F2-HIDDEN-EXCEPTION-X"

    facts = [
        _fact(
            rule_marker,
            "Rule R: widgets are normally blue. "
            + ("ordinary-rule-context " * (_FORMER_FIXED_LIMIT // 8)),
        ),
        _fact(
            exception_marker,
            "Exception X: widgets made on Friday are red.",
        ),
    ]

    serialized_system = server._build_system_prompt(facts)
    assert rule_marker in serialized_system
    assert exception_marker in serialized_system

    sanitized_system = sanitize_remote_system_prompt(serialized_system)
    packed = compact_messages_for_deepseek(
        [{"role": "system", "content": sanitized_system}]
    )
    transmitted_system = packed[0]["content"]

    # T keeps both the ordinary rule and the materially different exception X.
    assert transmitted_system == sanitized_system
    assert "Rule R: widgets are normally blue." in transmitted_system
    assert "Exception X: widgets made on Friday are red." in transmitted_system
    assert "truncated by Velantrim console" not in transmitted_system

    # The fixture establishes only R/S/T. It does not infer U or A.
