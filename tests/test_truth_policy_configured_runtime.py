"""Configured TruthPolicy resolution must never convert failure to permission."""

from __future__ import annotations

from core.truth_policy import TruthVerdict
from core.truth_policy_runtime import evaluate_configured_truth_policy_runtime


def test_disabled_resolver_preserves_disabled_behavior() -> None:
    called = False

    def decider(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("disabled policy must not execute")

    result = evaluate_configured_truth_policy_runtime(
        "query",
        [],
        mode="BALANCED",
        enabled_resolver=lambda: False,
        decider=decider,
    )

    assert called is False
    assert result.enabled is False
    assert result.evaluated is False
    assert result.blocks_llm is False
    assert result.truth_block is None


def test_enabled_resolver_uses_measured_verdict() -> None:
    result = evaluate_configured_truth_policy_runtime(
        "query",
        [],
        mode="BALANCED",
        enabled_resolver=lambda: True,
        decider=lambda *args, **kwargs: TruthVerdict(
            decision="allow",
            truth_status="supported",
        ),
    )

    assert result.enabled is True
    assert result.evaluated is True
    assert result.blocks_llm is False
    assert result.truth_block["decision"] == "allow"


def test_enabled_resolver_exception_fails_closed_without_payload_leak() -> None:
    def resolver() -> bool:
        raise RuntimeError("/private/config.env SECRET_TOKEN")

    result = evaluate_configured_truth_policy_runtime(
        "private query",
        [{"claim": "sensitive claim"}],
        mode="BALANCED",
        enabled_resolver=resolver,
    )

    assert result.enabled is True
    assert result.evaluated is False
    assert result.blocks_llm is True
    assert result.reason_code == "truth_policy_unavailable"
    assert result.truth_block["decision"] == "reject"
    serialized = str(result.truth_block)
    assert "private" not in serialized
    assert "SECRET" not in serialized
    assert "sensitive" not in serialized


def test_non_boolean_resolver_result_fails_closed() -> None:
    result = evaluate_configured_truth_policy_runtime(
        "query",
        [],
        mode="BALANCED",
        enabled_resolver=lambda: "yes",  # type: ignore[return-value]
    )

    assert result.enabled is True
    assert result.evaluated is False
    assert result.blocks_llm is True
    assert result.truth_block["truth_status"] == "policy_unavailable"


def test_enabled_decider_failure_remains_fail_closed_through_wrapper() -> None:
    def decider(*args, **kwargs):
        raise ValueError("unknown policy state")

    result = evaluate_configured_truth_policy_runtime(
        "query",
        [],
        mode="BALANCED",
        enabled_resolver=lambda: True,
        decider=decider,
    )

    assert result.enabled is True
    assert result.evaluated is False
    assert result.blocks_llm is True
    assert result.reason_code == "truth_policy_unavailable"
