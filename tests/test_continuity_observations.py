"""Structural validation tests for ContinuitySignalObservation."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from core.continuity.observations import (
    OBSERVATION_SCHEMA_VERSION,
    ContinuitySignalObservation,
    ContinuitySignalObservationError,
    ContinuitySignalType,
)

_NOW = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)


def _make(**overrides: object) -> ContinuitySignalObservation:
    defaults: dict[str, object] = dict(
        signal_type=ContinuitySignalType.CONTEXT_DEGRADED,
        value=True,
        confidence=0.9,
        producer="reader-a",
        source_type="shadow_projection",
        source_id="S-1",
        observed_at=_NOW,
        evidence_refs=("ev:1",),
        reason_codes=("observed_directly",),
    )
    defaults.update(overrides)
    return ContinuitySignalObservation.create(**defaults)  # type: ignore[arg-type]


def test_create_produces_deterministic_content_addressed_id() -> None:
    first = _make()
    second = _make()
    assert first.observation_id == second.observation_id
    assert first == second


def test_schema_version_defaults_and_is_recorded() -> None:
    observation = _make()
    assert observation.schema_version == OBSERVATION_SCHEMA_VERSION


@pytest.mark.parametrize(
    "field_name",
    ["producer", "source_type", "source_id"],
)
def test_empty_required_strings_are_rejected(field_name: str) -> None:
    with pytest.raises(ContinuitySignalObservationError):
        _make(**{field_name: ""})


def test_unsupported_signal_type_is_rejected() -> None:
    with pytest.raises(ContinuitySignalObservationError):
        _make(signal_type="not_a_real_type")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_value", [1, 0, "true", None])
def test_boolean_signal_rejects_non_bool_value(bad_value: object) -> None:
    with pytest.raises(ContinuitySignalObservationError):
        _make(signal_type=ContinuitySignalType.CONTEXT_DEGRADED, value=bad_value)


def test_active_contradiction_requires_value_true() -> None:
    with pytest.raises(ContinuitySignalObservationError):
        _make(signal_type=ContinuitySignalType.ACTIVE_CONTRADICTION, value=False)
    observation = _make(
        signal_type=ContinuitySignalType.ACTIVE_CONTRADICTION,
        value=True,
        scope="contradiction:1",
    )
    assert observation.value is True


@pytest.mark.parametrize("bad_value", ["degraded", "partial", "current", 1])
def test_context_freshness_rejects_unknown_string_values(bad_value: object) -> None:
    with pytest.raises(ContinuitySignalObservationError):
        _make(signal_type=ContinuitySignalType.CONTEXT_FRESHNESS, value=bad_value)


@pytest.mark.parametrize(
    "value", ["unknown", "fresh", "stale", "critical_stale"]
)
def test_context_freshness_accepts_real_enum_values(value: str) -> None:
    observation = _make(
        signal_type=ContinuitySignalType.CONTEXT_FRESHNESS, value=value
    )
    assert observation.value == value


@pytest.mark.parametrize("bad_value", ["urgent", "none", 1, True])
def test_sensitivity_rejects_unknown_string_values(bad_value: object) -> None:
    with pytest.raises(ContinuitySignalObservationError):
        _make(signal_type=ContinuitySignalType.SENSITIVITY, value=bad_value)


@pytest.mark.parametrize("value", ["low", "medium", "high", "critical"])
def test_sensitivity_accepts_real_enum_values(value: str) -> None:
    observation = _make(signal_type=ContinuitySignalType.SENSITIVITY, value=value)
    assert observation.value == value


@pytest.mark.parametrize("bad_confidence", [True, False, "0.5", 1.5, -0.1])
def test_confidence_must_be_finite_bool_excluded_and_in_range(
    bad_confidence: object,
) -> None:
    with pytest.raises(ContinuitySignalObservationError):
        _make(confidence=bad_confidence)


def test_confidence_rejects_nan_and_infinity() -> None:
    with pytest.raises(ContinuitySignalObservationError):
        _make(confidence=float("nan"))
    with pytest.raises(ContinuitySignalObservationError):
        _make(confidence=float("inf"))
    with pytest.raises(ContinuitySignalObservationError):
        _make(confidence=float("-inf"))


def test_observed_at_must_be_timezone_aware() -> None:
    with pytest.raises(ContinuitySignalObservationError):
        _make(observed_at=datetime(2026, 8, 5, 12, 0))


def test_evidence_refs_are_sorted() -> None:
    observation = _make(evidence_refs=("b", "a"))
    assert observation.evidence_refs == ("a", "b")


def test_duplicate_evidence_refs_are_rejected() -> None:
    with pytest.raises(ContinuitySignalObservationError, match="duplicates"):
        _make(evidence_refs=("a", "a"))


def test_reason_codes_are_sorted() -> None:
    observation = _make(reason_codes=("z", "a"))
    assert observation.reason_codes == ("a", "z")


def test_duplicate_reason_codes_are_rejected() -> None:
    with pytest.raises(ContinuitySignalObservationError, match="duplicates"):
        _make(reason_codes=("z", "z"))


def test_scope_defaults_to_none_and_is_normalized() -> None:
    assert _make().scope is None
    with pytest.raises(ContinuitySignalObservationError):
        _make(scope="   ")


def test_observation_is_frozen() -> None:
    observation = _make()
    with pytest.raises(FrozenInstanceError):
        observation.confidence = 0.1  # type: ignore[misc]


def test_mutable_evidence_refs_input_does_not_alias_caller_list() -> None:
    caller_refs = ["ev:1", "ev:2"]
    observation = _make(evidence_refs=caller_refs)
    caller_refs.append("ev:3")
    assert observation.evidence_refs == ("ev:1", "ev:2")


def test_to_dict_includes_observation_id_and_matches_identity_payload() -> None:
    observation = _make()
    as_dict = observation.to_dict()
    assert as_dict["observation_id"] == observation.observation_id
    assert as_dict["signal_type"] == observation.signal_type.value
    for forbidden in (
        "answer",
        "action",
        "tool",
        "execute",
        "canon_write",
        "retrieval_write",
        "final_decision",
        "runtime_override",
    ):
        assert forbidden not in as_dict


def test_direct_constructor_rejects_tampered_id() -> None:
    observation = _make()
    with pytest.raises(ContinuitySignalObservationError):
        ContinuitySignalObservation(
            observation_id="0" * 64,
            schema_version=observation.schema_version,
            signal_type=observation.signal_type,
            value=observation.value,
            confidence=observation.confidence,
            producer=observation.producer,
            source_type=observation.source_type,
            source_id=observation.source_id,
            observed_at=observation.observed_at,
            evidence_refs=observation.evidence_refs,
            reason_codes=observation.reason_codes,
            scope=observation.scope,
        )
