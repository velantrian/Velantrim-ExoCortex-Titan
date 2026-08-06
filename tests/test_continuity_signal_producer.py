"""Aggregation, trust, fail-closed, and security tests for the trusted producer."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from core.compute_controller import ComputeSensitivity, ContextFreshness
from core.continuity.observations import (
    ContinuitySignalObservation,
    ContinuitySignalType,
)
from core.continuity.signal_producer import (
    ContinuitySignalPolicy,
    ContinuitySignalProducerError,
    produce_continuity_compute_signals,
)

_NOW = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
_FORBIDDEN_KEYS = (
    "answer",
    "response",
    "action",
    "tool",
    "execute",
    "canon_write",
    "retrieval_write",
    "system_prompt",
    "final_decision",
    "runtime_override",
)


def policy(**overrides: object) -> ContinuitySignalPolicy:
    defaults: dict[str, object] = {
        "trusted_producers": {"reader-a", "reader-b", "reader-c"},
        "allowed_source_types": {"shadow_projection"},
        "minimum_confidence": 0.5,
        "require_evidence_refs": True,
        "minimum_confirmations": 2,
        "max_contradiction_count": 5,
    }
    defaults.update(overrides)
    return ContinuitySignalPolicy.create(**defaults)  # type: ignore[arg-type]


def observation(
    signal_type: ContinuitySignalType,
    value: object,
    *,
    producer: str = "reader-a",
    confidence: float = 0.9,
    source_type: str = "shadow_projection",
    scope: str | None = None,
    evidence_refs: tuple[str, ...] = ("ev:1",),
    source_id: str | None = None,
) -> ContinuitySignalObservation:
    return ContinuitySignalObservation.create(
        signal_type=signal_type,
        value=value,
        confidence=confidence,
        producer=producer,
        source_type=source_type,
        source_id=source_id or f"{producer}:{signal_type.value}:{scope or 'none'}",
        observed_at=_NOW,
        evidence_refs=evidence_refs,
        scope=scope,
    )


# ---- policy validation and public Iterable[str] contract ----


def test_policy_id_is_deterministic_and_content_addressed() -> None:
    assert policy().policy_id == policy().policy_id


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ["reader-a", "reader-b"],
        lambda: ("reader-a", "reader-b"),
        lambda: {"reader-a", "reader-b"},
        lambda: frozenset({"reader-a", "reader-b"}),
        lambda: (item for item in ("reader-a", "reader-b")),
    ],
)
def test_policy_accepts_all_advertised_iterable_shapes(factory: object) -> None:
    values = factory()  # type: ignore[operator]
    result = policy(trusted_producers=values)
    assert result.trusted_producers == frozenset({"reader-a", "reader-b"})


def test_policy_normalizes_source_iterable_too() -> None:
    result = policy(allowed_source_types=["shadow_projection", "projection"])
    assert result.allowed_source_types == frozenset(
        {"shadow_projection", "projection"}
    )


@pytest.mark.parametrize("value", ["reader-a", b"reader-a", 42, None])
def test_policy_rejects_text_and_non_iterable_collections(value: object) -> None:
    with pytest.raises(ContinuitySignalProducerError):
        policy(trusted_producers=value)


def test_policy_requires_non_empty_collections() -> None:
    with pytest.raises(ContinuitySignalProducerError):
        policy(trusted_producers=[])
    with pytest.raises(ContinuitySignalProducerError):
        policy(allowed_source_types=iter(()))


def test_policy_rejects_non_string_collection_items() -> None:
    with pytest.raises(ContinuitySignalProducerError):
        policy(trusted_producers=["reader-a", 1])


def test_policy_rejects_invalid_numeric_fields() -> None:
    with pytest.raises(ContinuitySignalProducerError):
        policy(minimum_confirmations=0)
    with pytest.raises(ContinuitySignalProducerError):
        policy(minimum_confidence=1.5)
    with pytest.raises(ContinuitySignalProducerError):
        policy(max_contradiction_count=-1)


def test_policy_has_no_authority_toggle_field() -> None:
    fields = policy().to_dict()
    for forbidden in _FORBIDDEN_KEYS + ("shadow_only", "enable_runtime", "activate"):
        assert forbidden not in fields


# ---- producer-level validation and trust filtering ----


def test_producer_rejects_malformed_top_level_inputs() -> None:
    with pytest.raises(ContinuitySignalProducerError):
        produce_continuity_compute_signals([], policy="not-a-policy")  # type: ignore[arg-type]
    with pytest.raises(ContinuitySignalProducerError):
        produce_continuity_compute_signals(["not-an-observation"], policy=policy())  # type: ignore[list-item]
    with pytest.raises(ContinuitySignalProducerError):
        produce_continuity_compute_signals("oops", policy=policy())  # type: ignore[arg-type]


def test_empty_observation_set_is_neutral() -> None:
    result = produce_continuity_compute_signals([], policy=policy())
    assert result.signals.context_degraded is False
    assert result.signals.context_freshness is ContextFreshness.UNKNOWN
    assert result.signals.evidence_coverage == 1.0
    assert result.signals.active_contradictions == 0
    assert result.signals.sensitivity is ComputeSensitivity.LOW
    assert result.signals.continuity_available is False
    assert result.signals.important_claim is False
    assert result.signals.requires_current_state is False
    assert "no_observations_provided" in result.reason_codes


@pytest.mark.parametrize(
    ("item", "reason"),
    [
        (
            lambda: observation(
                ContinuitySignalType.CONTEXT_DEGRADED,
                True,
                producer="mallory",
            ),
            "UNTRUSTED_PRODUCER",
        ),
        (
            lambda: observation(
                ContinuitySignalType.CONTEXT_DEGRADED,
                True,
                source_type="raw_user_text",
            ),
            "UNSUPPORTED_SOURCE_TYPE",
        ),
        (
            lambda: observation(
                ContinuitySignalType.CONTEXT_DEGRADED,
                True,
                confidence=0.1,
            ),
            "CONFIDENCE_BELOW_THRESHOLD",
        ),
        (
            lambda: observation(
                ContinuitySignalType.CONTEXT_DEGRADED,
                True,
                evidence_refs=(),
            ),
            "MISSING_EVIDENCE_REFS",
        ),
        (
            lambda: observation(
                ContinuitySignalType.ACTIVE_CONTRADICTION,
                True,
                scope=None,
            ),
            "MISSING_REQUIRED_SCOPE",
        ),
    ],
)
def test_trust_rejections_are_reason_coded(item: object, reason: str) -> None:
    result = produce_continuity_compute_signals(
        [item()],  # type: ignore[operator]
        policy=policy(),
    )
    assert result.rejected_observations[0].reason_code == reason
    assert "observations_rejected" in result.reason_codes


def test_unknown_schema_version_is_rejected() -> None:
    tampered = observation(ContinuitySignalType.CONTEXT_DEGRADED, True)
    object.__setattr__(
        tampered, "schema_version", "continuity.signal_producer.observation.v0"
    )
    result = produce_continuity_compute_signals([tampered], policy=policy())
    assert result.rejected_observations[0].reason_code == "UNKNOWN_SCHEMA_VERSION"


# ---- warning booleans preserve any applicable trusted warning ----


@pytest.mark.parametrize(
    ("signal_type", "field"),
    [
        (ContinuitySignalType.CONTEXT_DEGRADED, "context_degraded"),
        (ContinuitySignalType.IMPORTANT_CLAIM, "important_claim"),
        (ContinuitySignalType.REQUIRES_CURRENT_STATE, "requires_current_state"),
    ],
)
def test_one_trusted_warning_true_is_preserved(
    signal_type: ContinuitySignalType, field: str
) -> None:
    result = produce_continuity_compute_signals(
        [observation(signal_type, True)],
        policy=policy(minimum_confirmations=3),
    )
    assert getattr(result.signals, field) is True
    item = next(entry for entry in result.provenance if entry.signal_type is signal_type)
    assert item.rule == "trusted_true_observation_or"


@pytest.mark.parametrize(
    ("signal_type", "field"),
    [
        (ContinuitySignalType.CONTEXT_DEGRADED, "context_degraded"),
        (ContinuitySignalType.IMPORTANT_CLAIM, "important_claim"),
        (ContinuitySignalType.REQUIRES_CURRENT_STATE, "requires_current_state"),
    ],
)
def test_warning_false_only_does_not_raise_signal(
    signal_type: ContinuitySignalType, field: str
) -> None:
    result = produce_continuity_compute_signals(
        [observation(signal_type, False)],
        policy=policy(minimum_confirmations=1),
    )
    assert getattr(result.signals, field) is False


def test_important_claim_is_not_derived_from_sensitivity() -> None:
    result = produce_continuity_compute_signals(
        [observation(ContinuitySignalType.SENSITIVITY, "critical")],
        policy=policy(),
    )
    assert result.signals.sensitivity is ComputeSensitivity.CRITICAL
    assert result.signals.important_claim is False


# ---- continuity_available remains confirmation-gated and fail-conservative ----


def test_one_positive_availability_observation_is_insufficient() -> None:
    result = produce_continuity_compute_signals(
        [observation(ContinuitySignalType.CONTINUITY_AVAILABLE, True)],
        policy=policy(minimum_confirmations=2),
    )
    assert result.signals.continuity_available is False


def test_two_distinct_producers_confirm_availability() -> None:
    result = produce_continuity_compute_signals(
        [
            observation(
                ContinuitySignalType.CONTINUITY_AVAILABLE,
                True,
                producer="reader-a",
            ),
            observation(
                ContinuitySignalType.CONTINUITY_AVAILABLE,
                True,
                producer="reader-b",
            ),
        ],
        policy=policy(minimum_confirmations=2),
    )
    assert result.signals.continuity_available is True


def test_duplicate_observations_from_one_producer_do_not_confirm_availability() -> None:
    flooding = [
        observation(
            ContinuitySignalType.CONTINUITY_AVAILABLE,
            True,
            producer="reader-a",
            evidence_refs=(f"ev:{index}",),
            source_id=f"availability:{index}",
        )
        for index in range(20)
    ]
    result = produce_continuity_compute_signals(
        flooding,
        policy=policy(minimum_confirmations=2),
    )
    assert result.signals.continuity_available is False


def test_availability_conflict_is_fail_conservative() -> None:
    result = produce_continuity_compute_signals(
        [
            observation(
                ContinuitySignalType.CONTINUITY_AVAILABLE,
                True,
                producer="reader-a",
            ),
            observation(
                ContinuitySignalType.CONTINUITY_AVAILABLE,
                True,
                producer="reader-b",
            ),
            observation(
                ContinuitySignalType.CONTINUITY_AVAILABLE,
                False,
                producer="reader-c",
            ),
        ],
        policy=policy(minimum_confirmations=2),
    )
    assert result.signals.continuity_available is False
    assert "continuity_available_conflict" in result.reason_codes


# ---- categorical, contradiction, and evidence aggregation ----


def test_context_freshness_and_sensitivity_pick_most_severe_values() -> None:
    result = produce_continuity_compute_signals(
        [
            observation(ContinuitySignalType.CONTEXT_FRESHNESS, "fresh"),
            observation(
                ContinuitySignalType.CONTEXT_FRESHNESS,
                "critical_stale",
                producer="reader-b",
            ),
            observation(ContinuitySignalType.SENSITIVITY, "low"),
            observation(
                ContinuitySignalType.SENSITIVITY,
                "high",
                producer="reader-b",
            ),
        ],
        policy=policy(),
    )
    assert result.signals.context_freshness is ContextFreshness.CRITICAL_STALE
    assert result.signals.sensitivity is ComputeSensitivity.HIGH


def test_contradictions_are_deduplicated_by_scope_and_capped() -> None:
    observations = [
        observation(
            ContinuitySignalType.ACTIVE_CONTRADICTION,
            True,
            producer="reader-a",
            scope="pair:1",
            source_id="a:1",
        ),
        observation(
            ContinuitySignalType.ACTIVE_CONTRADICTION,
            True,
            producer="reader-b",
            scope="pair:1",
            source_id="b:1",
        ),
        observation(
            ContinuitySignalType.ACTIVE_CONTRADICTION,
            True,
            producer="reader-a",
            scope="pair:2",
            source_id="a:2",
        ),
    ]
    result = produce_continuity_compute_signals(
        observations,
        policy=policy(max_contradiction_count=1),
    )
    assert result.signals.active_contradictions == 1
    assert "contradiction_count_capped" in result.reason_codes


def test_evidence_coverage_formula_and_conflict_behavior() -> None:
    result = produce_continuity_compute_signals(
        [
            observation(
                ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
                True,
                scope="item:1",
                source_id="a:1",
            ),
            observation(
                ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
                True,
                scope="item:2",
                source_id="a:2",
            ),
            observation(
                ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
                False,
                producer="reader-b",
                scope="item:2",
                source_id="b:2",
            ),
        ],
        policy=policy(),
    )
    assert result.signals.evidence_coverage == 0.5


def test_nonempty_input_without_coverage_observations_is_fail_closed() -> None:
    result = produce_continuity_compute_signals(
        [observation(ContinuitySignalType.CONTEXT_DEGRADED, True)],
        policy=policy(),
    )
    assert result.signals.evidence_coverage == 0.0


# ---- provenance, determinism, and authority isolation ----


def test_provenance_covers_all_signal_dimensions() -> None:
    result = produce_continuity_compute_signals([], policy=policy())
    assert {item.signal_type for item in result.provenance} == set(
        ContinuitySignalType
    )


def test_provenance_references_warning_observation() -> None:
    item = observation(ContinuitySignalType.CONTEXT_DEGRADED, True)
    result = produce_continuity_compute_signals([item], policy=policy())
    provenance = next(
        entry
        for entry in result.provenance
        if entry.signal_type is ContinuitySignalType.CONTEXT_DEGRADED
    )
    assert item.observation_id in provenance.observation_ids
    assert item.producer in provenance.producers
    assert set(item.evidence_refs) <= set(provenance.evidence_refs)


def test_result_has_no_authority_bearing_fields() -> None:
    serialized = produce_continuity_compute_signals(
        [observation(ContinuitySignalType.CONTEXT_DEGRADED, True)],
        policy=policy(),
    ).to_dict()

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                assert key not in _FORBIDDEN_KEYS
                walk(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)

    walk(serialized)


def test_result_hash_is_reproducible() -> None:
    item = observation(ContinuitySignalType.CONTEXT_DEGRADED, True)
    first = produce_continuity_compute_signals([item], policy=policy())
    second = produce_continuity_compute_signals([item], policy=policy())
    assert first.result_hash == second.result_hash
