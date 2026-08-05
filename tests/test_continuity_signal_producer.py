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
    defaults: dict[str, object] = dict(
        trusted_producers={"reader-a", "reader-b", "reader-c"},
        allowed_source_types={"shadow_projection"},
        minimum_confidence=0.5,
        require_evidence_refs=True,
        minimum_confirmations=2,
        max_contradiction_count=5,
    )
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
) -> ContinuitySignalObservation:
    return ContinuitySignalObservation.create(
        signal_type=signal_type,
        value=value,
        confidence=confidence,
        producer=producer,
        source_type=source_type,
        source_id=f"{producer}:{signal_type.value}:{scope or 'none'}",
        observed_at=_NOW,
        evidence_refs=evidence_refs,
        scope=scope,
    )


# ---- policy validation ----


def test_policy_id_is_deterministic_and_content_addressed() -> None:
    first = policy()
    second = policy()
    assert first.policy_id == second.policy_id


def test_policy_requires_non_empty_producer_and_source_sets() -> None:
    with pytest.raises(ContinuitySignalProducerError):
        policy(trusted_producers=set())
    with pytest.raises(ContinuitySignalProducerError):
        policy(allowed_source_types=set())


def test_policy_rejects_zero_minimum_confirmations() -> None:
    with pytest.raises(ContinuitySignalProducerError):
        policy(minimum_confirmations=0)


def test_policy_rejects_out_of_range_minimum_confidence() -> None:
    with pytest.raises(ContinuitySignalProducerError):
        policy(minimum_confidence=1.5)
    with pytest.raises(ContinuitySignalProducerError):
        policy(minimum_confidence=-0.1)


def test_policy_rejects_negative_max_contradiction_count() -> None:
    with pytest.raises(ContinuitySignalProducerError):
        policy(max_contradiction_count=-1)


def test_policy_has_no_authority_toggle_field() -> None:
    fields = policy().to_dict()
    for forbidden in _FORBIDDEN_KEYS + ("shadow_only", "enable_runtime", "activate"):
        assert forbidden not in fields


# ---- producer-level input validation ----


def test_producer_rejects_non_policy_second_argument() -> None:
    with pytest.raises(ContinuitySignalProducerError):
        produce_continuity_compute_signals([], policy="not-a-policy")  # type: ignore[arg-type]


def test_producer_rejects_non_observation_items() -> None:
    with pytest.raises(ContinuitySignalProducerError):
        produce_continuity_compute_signals(["not-an-observation"], policy=policy())  # type: ignore[list-item]


def test_producer_rejects_string_passed_as_observations() -> None:
    with pytest.raises(ContinuitySignalProducerError):
        produce_continuity_compute_signals("oops", policy=policy())  # type: ignore[arg-type]


def test_empty_observation_set_is_a_valid_neutral_result() -> None:
    result = produce_continuity_compute_signals([], policy=policy())
    assert result.signals.context_degraded is False
    assert result.signals.context_freshness is ContextFreshness.UNKNOWN
    assert result.signals.evidence_coverage == 1.0
    assert result.signals.active_contradictions == 0
    assert result.signals.sensitivity is ComputeSensitivity.LOW
    assert result.signals.continuity_available is False
    assert result.signals.important_claim is False
    assert result.signals.requires_current_state is False
    assert result.rejected_observations == ()
    assert "no_observations_provided" in result.reason_codes


# ---- trust / rejection reasons ----


def test_untrusted_producer_is_rejected_with_reason_code() -> None:
    result = produce_continuity_compute_signals(
        [observation(ContinuitySignalType.CONTEXT_DEGRADED, True, producer="mallory")],
        policy=policy(),
    )
    assert result.signals.context_degraded is False
    assert len(result.rejected_observations) == 1
    assert result.rejected_observations[0].reason_code == "UNTRUSTED_PRODUCER"
    assert "observations_rejected" in result.reason_codes


def test_unsupported_source_type_is_rejected() -> None:
    result = produce_continuity_compute_signals(
        [
            observation(
                ContinuitySignalType.CONTEXT_DEGRADED,
                True,
                source_type="raw_user_text",
            )
        ],
        policy=policy(),
    )
    assert result.rejected_observations[0].reason_code == "UNSUPPORTED_SOURCE_TYPE"


def test_confidence_below_threshold_is_rejected() -> None:
    result = produce_continuity_compute_signals(
        [observation(ContinuitySignalType.CONTEXT_DEGRADED, True, confidence=0.1)],
        policy=policy(minimum_confidence=0.5),
    )
    assert result.rejected_observations[0].reason_code == "CONFIDENCE_BELOW_THRESHOLD"


def test_missing_evidence_refs_is_rejected_when_required() -> None:
    result = produce_continuity_compute_signals(
        [
            observation(
                ContinuitySignalType.CONTEXT_DEGRADED, True, evidence_refs=()
            )
        ],
        policy=policy(require_evidence_refs=True),
    )
    assert result.rejected_observations[0].reason_code == "MISSING_EVIDENCE_REFS"


def test_missing_required_scope_is_rejected_for_contradiction_and_evidence() -> None:
    for signal_type, value in (
        (ContinuitySignalType.ACTIVE_CONTRADICTION, True),
        (ContinuitySignalType.EVIDENCE_COVERAGE_ITEM, True),
    ):
        result = produce_continuity_compute_signals(
            [observation(signal_type, value, scope=None)],
            policy=policy(),
        )
        assert result.rejected_observations[0].reason_code == "MISSING_REQUIRED_SCOPE"


def test_unknown_schema_version_is_rejected() -> None:
    # __post_init__ only runs once, at construction; forcing the field
    # afterwards simulates an observation minted under a foreign/legacy
    # schema without fighting the identity-digest check `replace()` would
    # trigger for a still-consistent object.
    tampered = observation(ContinuitySignalType.CONTEXT_DEGRADED, True)
    object.__setattr__(
        tampered, "schema_version", "continuity.signal_producer.observation.v0"
    )
    result = produce_continuity_compute_signals([tampered], policy=policy())
    assert result.rejected_observations[0].reason_code == "UNKNOWN_SCHEMA_VERSION"


# ---- boolean confirmation-gated fields ----


def test_context_degraded_requires_minimum_confirmations() -> None:
    single = produce_continuity_compute_signals(
        [observation(ContinuitySignalType.CONTEXT_DEGRADED, True, producer="reader-a")],
        policy=policy(minimum_confirmations=2),
    )
    assert single.signals.context_degraded is False

    double = produce_continuity_compute_signals(
        [
            observation(ContinuitySignalType.CONTEXT_DEGRADED, True, producer="reader-a"),
            observation(ContinuitySignalType.CONTEXT_DEGRADED, True, producer="reader-b"),
        ],
        policy=policy(minimum_confirmations=2),
    )
    assert double.signals.context_degraded is True


def test_one_malicious_producer_cannot_manufacture_confirmations() -> None:
    """A single producer submitting many observations must not cross a
    minimum_confirmations>1 threshold by itself."""

    flooding = [
        ContinuitySignalObservation.create(
            signal_type=ContinuitySignalType.IMPORTANT_CLAIM,
            value=True,
            confidence=0.99,
            producer="mallory-but-trusted",
            source_type="shadow_projection",
            source_id=f"flood-{index}",
            observed_at=_NOW,
            evidence_refs=(f"ev:{index}",),
        )
        for index in range(50)
    ]
    result = produce_continuity_compute_signals(
        flooding,
        policy=policy(
            trusted_producers={"mallory-but-trusted"}, minimum_confirmations=2
        ),
    )
    assert result.signals.important_claim is False


def test_important_claim_is_not_derived_from_sensitivity() -> None:
    result = produce_continuity_compute_signals(
        [
            observation(ContinuitySignalType.SENSITIVITY, "critical", producer="reader-a"),
            observation(ContinuitySignalType.SENSITIVITY, "critical", producer="reader-b"),
        ],
        policy=policy(minimum_confirmations=2),
    )
    assert result.signals.sensitivity is ComputeSensitivity.CRITICAL
    assert result.signals.important_claim is False


# ---- continuity_available fail-conservative conflict ----


def test_continuity_available_true_with_enough_confirmations() -> None:
    result = produce_continuity_compute_signals(
        [
            observation(ContinuitySignalType.CONTINUITY_AVAILABLE, True, producer="reader-a"),
            observation(ContinuitySignalType.CONTINUITY_AVAILABLE, True, producer="reader-b"),
        ],
        policy=policy(minimum_confirmations=2),
    )
    assert result.signals.continuity_available is True
    assert "continuity_available_conflict" not in result.reason_codes


def test_continuity_available_conflict_is_fail_conservative() -> None:
    result = produce_continuity_compute_signals(
        [
            observation(ContinuitySignalType.CONTINUITY_AVAILABLE, True, producer="reader-a"),
            observation(ContinuitySignalType.CONTINUITY_AVAILABLE, True, producer="reader-b"),
            observation(ContinuitySignalType.CONTINUITY_AVAILABLE, False, producer="reader-c"),
        ],
        policy=policy(minimum_confirmations=2),
    )
    assert result.signals.continuity_available is False
    assert "continuity_available_conflict" in result.reason_codes


# ---- context_freshness / sensitivity: most-severe-wins ----


def test_context_freshness_picks_most_severe_trusted_value() -> None:
    result = produce_continuity_compute_signals(
        [
            observation(ContinuitySignalType.CONTEXT_FRESHNESS, "fresh", producer="reader-a"),
            observation(
                ContinuitySignalType.CONTEXT_FRESHNESS, "critical_stale", producer="reader-b"
            ),
            observation(ContinuitySignalType.CONTEXT_FRESHNESS, "stale", producer="reader-c"),
        ],
        policy=policy(),
    )
    assert result.signals.context_freshness is ContextFreshness.CRITICAL_STALE


def test_sensitivity_picks_most_severe_trusted_value() -> None:
    result = produce_continuity_compute_signals(
        [
            observation(ContinuitySignalType.SENSITIVITY, "low", producer="reader-a"),
            observation(ContinuitySignalType.SENSITIVITY, "high", producer="reader-b"),
        ],
        policy=policy(),
    )
    assert result.signals.sensitivity is ComputeSensitivity.HIGH


# ---- active_contradictions: dedup + cap ----


def test_duplicate_contradiction_reports_do_not_inflate_count() -> None:
    result = produce_continuity_compute_signals(
        [
            observation(
                ContinuitySignalType.ACTIVE_CONTRADICTION,
                True,
                producer="reader-a",
                scope="assertion-pair:1",
            ),
            observation(
                ContinuitySignalType.ACTIVE_CONTRADICTION,
                True,
                producer="reader-b",
                scope="assertion-pair:1",
            ),
        ],
        policy=policy(),
    )
    assert result.signals.active_contradictions == 1


def test_distinct_contradictions_are_all_counted_until_the_cap() -> None:
    observations = [
        observation(
            ContinuitySignalType.ACTIVE_CONTRADICTION,
            True,
            producer="reader-a",
            scope=f"assertion-pair:{index}",
        )
        for index in range(3)
    ]
    result = produce_continuity_compute_signals(observations, policy=policy())
    assert result.signals.active_contradictions == 3


def test_contradiction_count_is_capped_by_policy() -> None:
    observations = [
        observation(
            ContinuitySignalType.ACTIVE_CONTRADICTION,
            True,
            producer="reader-a",
            scope=f"assertion-pair:{index}",
        )
        for index in range(10)
    ]
    result = produce_continuity_compute_signals(
        observations, policy=policy(max_contradiction_count=5)
    )
    assert result.signals.active_contradictions == 5
    assert "contradiction_count_capped" in result.reason_codes


def test_contradiction_count_is_a_non_negative_int() -> None:
    result = produce_continuity_compute_signals([], policy=policy())
    assert isinstance(result.signals.active_contradictions, int)
    assert result.signals.active_contradictions >= 0


# ---- evidence_coverage ----


def test_evidence_coverage_formula_covered_over_total() -> None:
    observations = [
        observation(
            ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
            True,
            producer="reader-a",
            scope="item:1",
        ),
        observation(
            ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
            False,
            producer="reader-a",
            scope="item:2",
        ),
    ]
    result = produce_continuity_compute_signals(observations, policy=policy())
    assert result.signals.evidence_coverage == 0.5


def test_evidence_coverage_is_fail_closed_when_no_evidence_observations_exist() -> None:
    """Non-empty input with zero evidence observations must not silently
    become full coverage."""

    result = produce_continuity_compute_signals(
        [observation(ContinuitySignalType.CONTEXT_DEGRADED, True, producer="reader-a")],
        policy=policy(minimum_confirmations=1),
    )
    assert result.signals.evidence_coverage == 0.0


def test_evidence_coverage_matches_shadow_default_for_fully_empty_input() -> None:
    result = produce_continuity_compute_signals([], policy=policy())
    assert result.signals.evidence_coverage == 1.0


def test_duplicate_source_evidence_for_same_item_does_not_inflate_coverage() -> None:
    observations = [
        observation(
            ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
            True,
            producer="reader-a",
            scope="item:1",
        ),
        observation(
            ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
            True,
            producer="reader-b",
            scope="item:1",
        ),
    ]
    result = produce_continuity_compute_signals(observations, policy=policy())
    assert result.signals.evidence_coverage == 1.0


def test_conflicting_evidence_for_same_item_does_not_count_as_covered() -> None:
    observations = [
        observation(
            ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
            True,
            producer="reader-a",
            scope="item:1",
        ),
        observation(
            ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
            False,
            producer="reader-b",
            scope="item:1",
        ),
    ]
    result = produce_continuity_compute_signals(observations, policy=policy())
    assert result.signals.evidence_coverage == 0.0


def test_evidence_coverage_stays_in_unit_range() -> None:
    result = produce_continuity_compute_signals(
        [
            observation(
                ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
                True,
                producer="reader-a",
                scope=f"item:{index}",
            )
            for index in range(4)
        ],
        policy=policy(),
    )
    assert 0.0 <= result.signals.evidence_coverage <= 1.0
    assert result.signals.evidence_coverage == 1.0


# ---- provenance ----


def test_provenance_covers_all_eight_signal_dimensions() -> None:
    result = produce_continuity_compute_signals([], policy=policy())
    signal_types = {item.signal_type for item in result.provenance}
    assert signal_types == set(ContinuitySignalType)


def test_provenance_references_contributing_observation_and_evidence() -> None:
    obs = observation(ContinuitySignalType.CONTEXT_DEGRADED, True)
    result = produce_continuity_compute_signals(
        [obs], policy=policy(minimum_confirmations=1)
    )
    degraded_prov = next(
        item
        for item in result.provenance
        if item.signal_type is ContinuitySignalType.CONTEXT_DEGRADED
    )
    assert obs.observation_id in degraded_prov.observation_ids
    assert set(obs.evidence_refs) <= set(degraded_prov.evidence_refs)
    assert obs.producer in degraded_prov.producers
    assert degraded_prov.value is True


def test_rejected_observations_report_reason_and_are_excluded_from_signals() -> None:
    trusted = observation(
        ContinuitySignalType.IMPORTANT_CLAIM, True, producer="reader-a"
    )
    untrusted = observation(
        ContinuitySignalType.IMPORTANT_CLAIM, True, producer="ghost"
    )
    result = produce_continuity_compute_signals(
        [trusted, untrusted], policy=policy(minimum_confirmations=1)
    )
    assert result.signals.important_claim is True
    assert len(result.rejected_observations) == 1
    assert result.rejected_observations[0].observation_id == untrusted.observation_id
    assert untrusted.observation_id not in result.observation_ids


# ---- security: no authority leakage anywhere in the result ----


def test_result_to_dict_has_no_authority_bearing_fields() -> None:
    obs = observation(ContinuitySignalType.CONTEXT_DEGRADED, True)
    result = produce_continuity_compute_signals(
        [obs], policy=policy(minimum_confirmations=1)
    )
    serialized = result.to_dict()

    def _walk(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                assert key not in _FORBIDDEN_KEYS
                _walk(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                _walk(item)

    _walk(serialized)


def test_result_hash_is_reproducible_for_identical_input() -> None:
    obs = observation(ContinuitySignalType.CONTEXT_DEGRADED, True)
    first = produce_continuity_compute_signals(
        [obs], policy=policy(minimum_confirmations=1)
    )
    second = produce_continuity_compute_signals(
        [obs], policy=policy(minimum_confirmations=1)
    )
    assert first.result_hash == second.result_hash
