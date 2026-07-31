"""PR-ARM-03: deterministic, read-only selective-memory candidates."""

from __future__ import annotations

import itertools

import pytest

import core.selective_memory_candidates as smc


def extract(text: str, **kwargs):
    return smc.extract_memory_candidates(text, source_ref="conversation:test", **kwargs)


def test_same_input_produces_same_ids_and_trace():
    text = "I prefer concise reports. My goal is to finish the project tomorrow."
    first = extract(text)
    second = extract(text)
    assert first == second
    assert [c.candidate_id for c in first.candidates] == [c.candidate_id for c in second.candidates]


def test_extractor_version_changes_identity():
    text = "I prefer concise reports."
    a = extract(text, policy=smc.CandidateExtractionPolicy(extractor_version="v1"))
    b = extract(text, policy=smc.CandidateExtractionPolicy(extractor_version="v2"))
    assert a.candidates[0].candidate_id != b.candidates[0].candidate_id


def test_source_offsets_change_identity():
    a = extract("I prefer tea.")
    b = extract("Prefix. I prefer tea.")
    assert a.candidates[0].candidate_id != b.candidates[1].candidate_id


def test_exact_source_spans_round_trip():
    text = "Привет. Я предпочитаю отчёты по пятницам. Затем продолжим."
    result = extract(text)
    assert result.candidates
    for candidate in result.candidates:
        assert smc.validate_source_span(text, candidate.source_span)
        span = candidate.source_span
        assert text[span.start_char : span.end_char] == span.text


def test_invalid_span_is_rejected_by_validator():
    span = smc.SourceSpan(0, 4, "nope", "source")
    assert not smc.validate_source_span("test", span)


def test_unicode_offsets_are_character_based():
    text = "🙂 Я люблю кофе."
    result = extract(text)
    candidate = result.candidates[0]
    assert candidate.source_span.text == text[candidate.source_span.start_char : candidate.source_span.end_char]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("I prefer dark mode.", smc.CandidateType.PREFERENCE),
        ("My goal is to ship the release tomorrow.", smc.CandidateType.GOAL),
        ("I promise I will send the report.", smc.CandidateType.COMMITMENT),
        ("We must not use remote providers.", smc.CandidateType.CONSTRAINT),
        ("My sister works in Berlin.", smc.CandidateType.RELATIONSHIP),
        ("This repository uses SQLite.", smc.CandidateType.PROJECT_CONTEXT),
        ("The workflow has three steps.", smc.CandidateType.PROCEDURE_HINT),
        ("My name is Mira.", smc.CandidateType.PERSONAL_FACT),
    ],
)
def test_candidate_typing(text, expected):
    result = extract(text)
    assert result.candidates[0].candidate_type is expected


def test_negation_is_preserved_and_changes_dedup_key():
    positive = extract("I like coffee.").candidates[0]
    negative = extract("I do not like coffee.").candidates[0]
    assert "not" in negative.normalized_text
    assert positive.dedup_key != negative.dedup_key


def test_uncertain_other_statement_is_not_promoted_to_fact():
    candidate = extract("Maybe the server is in Europe.").candidates[0]
    assert candidate.candidate_type is smc.CandidateType.OTHER
    assert candidate.confidence < 0.5


@pytest.mark.parametrize(
    ("text", "scope"),
    [
        ("I plan to finish this tomorrow.", smc.TemporalScope.FUTURE_INTENT),
        ("For now I prefer weekly reports.", smc.TemporalScope.TEMPORARY),
        ("I used to live in Oslo.", smc.TemporalScope.HISTORICAL),
        ("I currently work remotely.", smc.TemporalScope.CURRENT),
        ("I prefer tea.", smc.TemporalScope.TIMELESS),
    ],
)
def test_temporal_scopes(text, scope):
    assert extract(text).candidates[0].temporal_scope is scope


def test_exact_duplicate_is_rejected_with_explainable_reason():
    result = extract("I prefer tea. I prefer tea.")
    assert len(result.candidates) == 1
    assert any(item.reason is smc.RejectionReason.DUPLICATE_WITHIN_INPUT for item in result.rejected)


def test_whitespace_normalized_duplicate_is_rejected():
    result = extract("I prefer tea. I   prefer   tea.")
    assert len(result.candidates) == 1
    assert result.rejected[0].reason is smc.RejectionReason.DUPLICATE_WITHIN_INPUT


def test_different_dates_do_not_deduplicate():
    result = extract("I will travel on 2026-08-01. I will travel on 2026-08-02.")
    assert len(result.candidates) == 2
    assert result.candidates[0].dedup_key != result.candidates[1].dedup_key


def test_credential_is_blocked_and_redacted():
    secret = "ghp_abcdefghijklmnopqrstuvwxyz123456"
    result = extract(f"My token: {secret}.")
    assert result.candidates == ()
    assert result.rejected[0].reason is smc.RejectionReason.CREDENTIAL_DETECTED
    assert secret not in result.rejected[0].source_span.text
    assert secret not in repr(result.trace)


def test_medical_statement_is_marked_high_risk_but_remains_proposal():
    result = extract("My diagnosis is diabetes.")
    candidate = result.candidates[0]
    assert smc.SensitivityFlag.MEDICAL in candidate.sensitivity
    assert smc.SensitivityFlag.HIGH_RISK in candidate.sensitivity
    assert result.trace.memory_write_count == 0


def test_contact_data_is_redacted_in_candidate_payload():
    result = extract("My email is person@example.com.")
    candidate = result.candidates[0]
    assert candidate.normalized_text == "My email is [REDACTED_CONTACT]."
    assert smc.SensitivityFlag.CONTACT in candidate.sensitivity


def test_candidate_budget_is_bounded_and_deterministic():
    text = " ".join(f"I prefer option {i}." for i in range(10))
    policy = smc.CandidateExtractionPolicy(max_candidates_per_input=3)
    first = extract(text, policy=policy)
    second = extract(text, policy=policy)
    assert len(first.candidates) == 3
    assert first.truncated
    assert first == second
    assert any(item.reason is smc.RejectionReason.BUDGET_EXCEEDED for item in first.rejected)


def test_total_character_budget_is_bounded():
    policy = smc.CandidateExtractionPolicy(max_total_candidate_chars=25)
    result = extract("I prefer short reports. I prefer detailed weekly reports.", policy=policy)
    assert result.truncated
    assert sum(len(c.normalized_text) for c in result.candidates) <= 25


def test_overlong_sentence_is_rejected_without_crash():
    policy = smc.CandidateExtractionPolicy(max_candidate_chars=20)
    result = extract("I prefer " + "x" * 100 + ".", policy=policy)
    assert result.candidates == ()
    assert result.rejected[0].reason is smc.RejectionReason.TOO_LONG


def test_empty_and_whitespace_inputs_are_safe():
    assert extract("").candidates == ()
    assert extract("   \n").candidates == ()


def test_invalid_policy_is_rejected_early():
    with pytest.raises(ValueError):
        smc.CandidateExtractionPolicy(max_candidates_per_input=0)


def test_clock_is_injectable_and_does_not_affect_default_determinism():
    ticks = iter((1.0, 1.025))
    result = smc.extract_memory_candidates(
        "I prefer tea.",
        source_ref="conversation:test",
        clock=lambda: next(ticks),
    )
    assert result.trace.elapsed_ms == 25.0
    assert extract("I prefer tea.").trace.elapsed_ms == 0.0


def test_shadow_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("ENABLE_SELECTIVE_MEMORY_CANDIDATE_SHADOW", raising=False)
    result = smc.run_shadow_extraction("I prefer tea.", source_ref="conversation:test")
    assert result.candidates == ()
    assert result.warnings == ("selective_memory_candidate_shadow_disabled",)


def test_shadow_flag_on_returns_proposals_only(monkeypatch):
    monkeypatch.setenv("ENABLE_SELECTIVE_MEMORY_CANDIDATE_SHADOW", "1")
    result = smc.run_shadow_extraction("I prefer tea.", source_ref="conversation:test")
    assert len(result.candidates) == 1
    assert result.trace.canon_write_count == 0
    assert result.trace.memory_write_count == 0
    assert result.trace.write_gate_call_count == 0
    assert result.trace.truth_gate_bypass_count == 0


def test_result_has_no_write_capability():
    result = extract("I prefer tea.")
    assert not hasattr(result, "store")
    assert not hasattr(result, "admit")
    assert not hasattr(result, "write")


def test_order_of_internal_sensitivity_flags_is_stable():
    text = "My diagnosis is diabetes and my email is person@example.com."
    expected = tuple(sorted(extract(text).candidates[0].sensitivity, key=lambda item: item.value))
    for _ in range(5):
        assert extract(text).candidates[0].sensitivity == expected


def test_span_order_is_source_order():
    text = "I prefer tea. My goal is to learn Rust. We must not use the network."
    result = extract(text)
    starts = [candidate.source_span.start_char for candidate in result.candidates]
    assert starts == sorted(starts)


def test_permutation_of_distinct_sentences_changes_source_identity_not_content_keys():
    sentences = ("I prefer tea.", "My goal is to learn Rust.")
    dedup_sets = []
    id_sets = []
    for ordering in itertools.permutations(sentences):
        result = extract(" ".join(ordering))
        dedup_sets.append({candidate.dedup_key for candidate in result.candidates})
        id_sets.append({candidate.candidate_id for candidate in result.candidates})
    assert dedup_sets[0] == dedup_sets[1]
    assert id_sets[0] != id_sets[1]
