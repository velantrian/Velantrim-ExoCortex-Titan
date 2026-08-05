"""Latency and dependency invariants for ARM-03 selective-memory shadow work."""

from __future__ import annotations

import inspect

import core.selective_memory_candidates as smc
from core.feature_config import clear_config_cache


def test_flag_off_never_invokes_candidate_extraction(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_SELECTIVE_MEMORY_CANDIDATE_SHADOW", raising=False)
    clear_config_cache()

    def forbidden_extraction(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("flag-off shadow path invoked extraction")

    monkeypatch.setattr(smc, "extract_memory_candidates", forbidden_extraction)
    try:
        result = smc.run_shadow_extraction(
            "I prefer concise answers.",
            source_ref="conversation:speed-contract",
        )
    finally:
        clear_config_cache()

    assert result.candidates == ()
    assert result.warnings == ("selective_memory_candidate_shadow_disabled",)
    assert result.trace.canon_write_count == 0
    assert result.trace.memory_write_count == 0


def test_default_policy_is_strictly_bounded() -> None:
    policy = smc.CandidateExtractionPolicy()
    assert policy.max_source_spans == 64
    assert policy.max_candidates_per_input == 12
    assert policy.max_candidate_chars == 500
    assert policy.max_total_candidate_chars == 2_000


def test_extractor_has_no_async_model_or_network_execution_surface() -> None:
    source = inspect.getsource(smc)
    forbidden_markers = (
        "asyncio",
        "await ",
        "ThreadPoolExecutor",
        "ProcessPoolExecutor",
        "sentence_transformers",
        "chat_complete",
        "httpx",
        "requests",
        "urllib",
        "socket",
    )
    for marker in forbidden_markers:
        assert marker not in source


def test_truncation_bounds_output_even_for_large_input() -> None:
    text = " ".join(
        f"I prefer deterministic option {index}." for index in range(500)
    )
    policy = smc.CandidateExtractionPolicy(
        max_source_spans=20,
        max_candidates_per_input=5,
        max_total_candidate_chars=180,
    )
    result = smc.extract_memory_candidates(
        text,
        source_ref="conversation:bounded-large-input",
        policy=policy,
    )

    assert len(result.candidates) <= 5
    assert sum(len(item.normalized_text) for item in result.candidates) <= 180
    assert result.trace.canon_write_count == 0
    assert result.trace.memory_write_count == 0
    assert result.trace.write_gate_call_count == 0
    assert result.trace.truth_gate_bypass_count == 0


def test_large_sensitive_input_safe_serialization_is_bounded() -> None:
    text = " ".join(
        f"My email is person{index}@example.com." for index in range(200)
    )
    policy = smc.CandidateExtractionPolicy(
        max_source_spans=16,
        max_candidates_per_input=4,
        max_total_candidate_chars=160,
    )
    result = smc.extract_memory_candidates(
        text,
        source_ref="conversation:sensitive-large",
        policy=policy,
    )
    portable = repr(result.to_safe_dict())
    assert "@example.com" not in portable
    assert len(result.candidates) <= 4
