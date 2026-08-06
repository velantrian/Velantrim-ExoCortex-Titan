"""Regression tests for independent review findings on Continuity signals."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import pytest

import core.continuity.signal_producer as signal_producer_module
from core.continuity import (
    ContinuitySignalObservation,
    ContinuitySignalObservationError,
    ContinuitySignalPolicy,
    ContinuitySignalProducerError,
    ContinuitySignalType,
    produce_continuity_compute_signals,
)

_NOW = datetime(2026, 8, 6, 5, 0, tzinfo=UTC)


def _observation(
    signal_type: ContinuitySignalType,
    value: object,
    *,
    producer: str = "trusted-a",
    source_id: str = "source-1",
    evidence_ref: str = "evidence-1",
    confidence: float = 0.9,
    scope: str | None = None,
) -> ContinuitySignalObservation:
    return ContinuitySignalObservation.create(
        signal_type=signal_type,
        value=value,
        confidence=confidence,
        producer=producer,
        source_type="typed-test",
        source_id=source_id,
        observed_at=_NOW,
        evidence_refs=(evidence_ref,),
        reason_codes=("review-regression",),
        scope=scope,
    )


def _policy(*, confirmations: int = 2) -> ContinuitySignalPolicy:
    return ContinuitySignalPolicy.create(
        trusted_producers=("trusted-a", "trusted-b"),
        allowed_source_types=("typed-test",),
        minimum_confidence=0.5,
        require_evidence_refs=True,
        minimum_confirmations=confirmations,
        max_contradiction_count=10,
    )


def _provenance(result: object, signal_type: ContinuitySignalType):
    provenance = getattr(result, "provenance")
    return next(item for item in provenance if item.signal_type is signal_type)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("evidence_refs", "evidence-1"),
        ("evidence_refs", cast(Any, b"evidence-1")),
        ("evidence_refs", cast(Any, 123)),
        ("reason_codes", "review-regression"),
        ("reason_codes", cast(Any, b"review-regression")),
        ("reason_codes", cast(Any, 123)),
    ],
)
def test_observation_rejects_scalar_reference_collections(
    field: str, value: object
) -> None:
    kwargs: dict[str, object] = {
        "signal_type": ContinuitySignalType.CONTEXT_DEGRADED,
        "value": True,
        "confidence": 0.9,
        "producer": "trusted-a",
        "source_type": "typed-test",
        "source_id": "source-1",
        "observed_at": _NOW,
        "evidence_refs": ("evidence-1",),
        "reason_codes": ("review-regression",),
    }
    kwargs[field] = value
    with pytest.raises(ContinuitySignalObservationError):
        ContinuitySignalObservation.create(**cast(Any, kwargs))


def test_observation_accepts_one_shot_reference_iterables() -> None:
    observation = ContinuitySignalObservation.create(
        signal_type=ContinuitySignalType.CONTEXT_DEGRADED,
        value=True,
        confidence=0.9,
        producer="trusted-a",
        source_type="typed-test",
        source_id="source-1",
        observed_at=_NOW,
        evidence_refs=(value for value in ("z", "a")),
        reason_codes=(value for value in ("r2", "r1")),
    )
    assert observation.evidence_refs == ("a", "z")
    assert observation.reason_codes == ("r1", "r2")


def test_false_only_warning_retains_complete_provenance() -> None:
    observation = _observation(
        ContinuitySignalType.CONTEXT_DEGRADED,
        False,
        evidence_ref="evidence-false",
        confidence=0.8,
    )
    result = produce_continuity_compute_signals(
        [observation], policy=_policy()
    )
    item = _provenance(result, ContinuitySignalType.CONTEXT_DEGRADED)
    assert result.signals.context_degraded is False
    assert item.observation_ids == (observation.observation_id,)
    assert item.producers == ("trusted-a",)
    assert item.evidence_refs == ("evidence-false",)
    assert item.confidence == 0.8
    assert item.rule == "trusted_false_observations_only"


def test_mixed_warning_true_wins_without_losing_negative_provenance() -> None:
    positive = _observation(
        ContinuitySignalType.IMPORTANT_CLAIM,
        True,
        producer="trusted-a",
        source_id="positive",
        evidence_ref="evidence-positive",
    )
    negative = _observation(
        ContinuitySignalType.IMPORTANT_CLAIM,
        False,
        producer="trusted-b",
        source_id="negative",
        evidence_ref="evidence-negative",
        confidence=0.7,
    )
    result = produce_continuity_compute_signals(
        [positive, negative], policy=_policy()
    )
    item = _provenance(result, ContinuitySignalType.IMPORTANT_CLAIM)
    assert result.signals.important_claim is True
    assert item.observation_ids == tuple(
        sorted((positive.observation_id, negative.observation_id))
    )
    assert item.producers == ("trusted-a", "trusted-b")
    assert item.evidence_refs == (
        "evidence-negative",
        "evidence-positive",
    )
    assert item.confidence == 0.7
    assert item.rule == "trusted_true_observation_or"


def test_false_only_availability_retains_negative_provenance() -> None:
    negative = _observation(
        ContinuitySignalType.CONTINUITY_AVAILABLE,
        False,
        producer="trusted-b",
        source_id="negative-availability",
        evidence_ref="evidence-unavailable",
        confidence=0.75,
    )
    result = produce_continuity_compute_signals(
        [negative], policy=_policy()
    )
    item = _provenance(
        result, ContinuitySignalType.CONTINUITY_AVAILABLE
    )
    assert result.signals.continuity_available is False
    assert item.observation_ids == (negative.observation_id,)
    assert item.producers == ("trusted-b",)
    assert item.evidence_refs == ("evidence-unavailable",)
    assert item.confidence == 0.75
    assert item.rule == "trusted_negative_observations_fail_conservative"


def test_empty_availability_has_empty_default_provenance() -> None:
    result = produce_continuity_compute_signals([], policy=_policy())
    item = _provenance(
        result, ContinuitySignalType.CONTINUITY_AVAILABLE
    )
    assert result.signals.continuity_available is False
    assert item.observation_ids == ()
    assert item.producers == ()
    assert item.evidence_refs == ()
    assert item.confidence == 0.0
    assert item.rule == "no_trusted_observations"



def test_tampered_observation_id_is_reason_coded_rejection() -> None:
    observation = _observation(
        ContinuitySignalType.CONTEXT_DEGRADED,
        True,
    )
    object.__setattr__(observation, "observation_id", "0" * 64)

    result = produce_continuity_compute_signals(
        [observation], policy=_policy()
    )

    assert result.observation_ids == ()
    assert result.ignored_or_rejected_ids == ("0" * 64,)
    assert len(result.rejected_observations) == 1
    rejected = result.rejected_observations[0]
    assert rejected.reason_code == "OBSERVATION_ID_MISMATCH"
    assert "canonical observation content" in rejected.message


def test_tampered_categorical_value_fails_with_controlled_error() -> None:
    observation = _observation(
        ContinuitySignalType.CONTEXT_FRESHNESS,
        "fresh",
    )
    object.__setattr__(observation, "value", "impossible")
    object.__setattr__(
        observation,
        "observation_id",
        signal_producer_module._digest(observation.identity_payload()),
    )

    with pytest.raises(
        ContinuitySignalProducerError,
        match="unsupported context_freshness observation value",
    ):
        produce_continuity_compute_signals(
            [observation], policy=_policy()
        )


def test_duplicate_contradiction_scope_keeps_complete_provenance() -> None:
    first = _observation(
        ContinuitySignalType.ACTIVE_CONTRADICTION,
        True,
        producer="trusted-a",
        source_id="contradiction-a",
        evidence_ref="evidence-a",
        confidence=0.9,
        scope="claim:1",
    )
    second = _observation(
        ContinuitySignalType.ACTIVE_CONTRADICTION,
        True,
        producer="trusted-b",
        source_id="contradiction-b",
        evidence_ref="evidence-b",
        confidence=0.7,
        scope="claim:1",
    )

    result = produce_continuity_compute_signals(
        [first, second], policy=_policy()
    )
    item = _provenance(
        result, ContinuitySignalType.ACTIVE_CONTRADICTION
    )

    assert result.signals.active_contradictions == 1
    assert item.observation_ids == tuple(
        sorted((first.observation_id, second.observation_id))
    )
    assert item.producers == ("trusted-a", "trusted-b")
    assert item.evidence_refs == ("evidence-a", "evidence-b")
    assert item.confidence == 0.7
    assert item.rule == "unique_scopes_deduped_from_2_observations"
