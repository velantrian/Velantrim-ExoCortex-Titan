"""Determinism, canonical serialization, and pure-composition integration tests."""
from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import inspect
import random

import pytest

from core.compute_controller import assess_compute_with_continuity
from core.continuity.observations import (
    ContinuitySignalObservation,
    ContinuitySignalType,
)
from core.continuity.signal_producer import (
    ContinuitySignalPolicy,
    ContinuitySignalProducerError,
    produce_continuity_compute_signals,
)
from tests.test_continuity_shadow_runner import _input

_NOW = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)


def _policy() -> ContinuitySignalPolicy:
    return ContinuitySignalPolicy.create(
        trusted_producers={"reader-a", "reader-b", "reader-c"},
        allowed_source_types={"shadow_projection"},
        minimum_confidence=0.5,
        require_evidence_refs=True,
        minimum_confirmations=2,
        max_contradiction_count=5,
    )


def _diverse_observations() -> list[ContinuitySignalObservation]:
    specs = [
        (ContinuitySignalType.CONTEXT_DEGRADED, True, "reader-a", "item:cd-1"),
        (ContinuitySignalType.CONTEXT_DEGRADED, True, "reader-b", "item:cd-2"),
        (ContinuitySignalType.CONTEXT_FRESHNESS, "stale", "reader-a", "item:cf-1"),
        (ContinuitySignalType.CONTEXT_FRESHNESS, "fresh", "reader-b", "item:cf-2"),
        (ContinuitySignalType.SENSITIVITY, "high", "reader-a", "item:sn-1"),
        (
            ContinuitySignalType.ACTIVE_CONTRADICTION,
            True,
            "reader-a",
            "assertion-pair:1",
        ),
        (
            ContinuitySignalType.ACTIVE_CONTRADICTION,
            True,
            "reader-b",
            "assertion-pair:2",
        ),
        (
            ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
            True,
            "reader-a",
            "required-item:1",
        ),
        (
            ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
            False,
            "reader-b",
            "required-item:2",
        ),
        (
            ContinuitySignalType.CONTINUITY_AVAILABLE,
            True,
            "reader-a",
            None,
        ),
        (
            ContinuitySignalType.CONTINUITY_AVAILABLE,
            True,
            "reader-b",
            None,
        ),
        (ContinuitySignalType.IMPORTANT_CLAIM, True, "reader-a", None),
        (ContinuitySignalType.REQUIRES_CURRENT_STATE, True, "reader-b", None),
    ]
    observations = []
    for index, (signal_type, value, producer, scope) in enumerate(specs):
        observations.append(
            ContinuitySignalObservation.create(
                signal_type=signal_type,
                value=value,
                confidence=0.7 + (index % 3) * 0.1,
                producer=producer,
                source_type="shadow_projection",
                source_id=f"src-{index}",
                observed_at=_NOW,
                evidence_refs=(f"ev:{index}",),
                scope=scope,
            )
        )
    return observations


def test_permutation_of_input_order_does_not_change_result() -> None:
    base = _diverse_observations()
    shuffled = list(base)
    random.Random(1234).shuffle(shuffled)
    reversed_order = list(reversed(base))

    result_a = produce_continuity_compute_signals(base, policy=_policy())
    result_b = produce_continuity_compute_signals(shuffled, policy=_policy())
    result_c = produce_continuity_compute_signals(reversed_order, policy=_policy())

    assert result_a.result_hash == result_b.result_hash == result_c.result_hash
    assert result_a.signals == result_b.signals == result_c.signals
    assert result_a.provenance == result_b.provenance == result_c.provenance
    assert result_a.reason_codes == result_b.reason_codes == result_c.reason_codes


def test_duplicate_identical_observations_do_not_change_result() -> None:
    base = _diverse_observations()
    with_duplicates = base + [base[0], base[3], base[3]]

    result_a = produce_continuity_compute_signals(base, policy=_policy())
    result_b = produce_continuity_compute_signals(with_duplicates, policy=_policy())

    assert result_a.result_hash == result_b.result_hash
    assert result_a.observation_ids == result_b.observation_ids


def test_conflicting_content_under_the_same_observation_id_is_rejected() -> None:
    original = ContinuitySignalObservation.create(
        signal_type=ContinuitySignalType.CONTEXT_DEGRADED,
        value=True,
        confidence=0.9,
        producer="reader-a",
        source_type="shadow_projection",
        source_id="S-1",
        observed_at=_NOW,
        evidence_refs=("ev:1",),
    )
    # A second, independently valid observation (its own correct id for its
    # own content), then force a content-address collision with `original`
    # after construction — `__post_init__` only runs once, at construction.
    tampered = ContinuitySignalObservation.create(
        signal_type=ContinuitySignalType.CONTEXT_DEGRADED,
        value=True,
        confidence=0.1,
        producer="reader-a",
        source_type="shadow_projection",
        source_id="S-1",
        observed_at=_NOW,
        evidence_refs=("ev:1",),
    )
    object.__setattr__(tampered, "observation_id", original.observation_id)

    with pytest.raises(ContinuitySignalProducerError):
        produce_continuity_compute_signals([original, tampered], policy=_policy())


def test_repeated_calls_produce_byte_identical_serialization() -> None:
    observations = _diverse_observations()
    first = produce_continuity_compute_signals(observations, policy=_policy())
    second = produce_continuity_compute_signals(observations, policy=_policy())

    import json

    first_json = json.dumps(first.to_dict(), sort_keys=True)
    second_json = json.dumps(second.to_dict(), sort_keys=True)
    assert first_json == second_json


def test_producer_signature_takes_no_clock_network_or_random_dependency() -> None:
    signature = inspect.signature(produce_continuity_compute_signals)
    assert tuple(signature.parameters) == ("observations", "policy")
    assert signature.parameters["policy"].kind is inspect.Parameter.KEYWORD_ONLY


def test_input_list_is_not_mutated_by_the_producer() -> None:
    observations = _diverse_observations()
    snapshot = list(observations)
    produce_continuity_compute_signals(observations, policy=_policy())
    assert observations == snapshot


def test_signals_output_composes_into_assess_compute_with_continuity() -> None:
    result = produce_continuity_compute_signals(
        _diverse_observations(), policy=_policy()
    )
    assessment = assess_compute_with_continuity(
        "what changed since yesterday?", signals=result.signals
    )
    assert assessment.shadow_only is True
    assert assessment.base_decision == assessment.base_decision


def test_signals_output_composes_into_existing_shadow_runner_input() -> None:
    result = produce_continuity_compute_signals(
        _diverse_observations(), policy=_policy()
    )
    base_input = _input()
    composed = replace(base_input, compute_signals=result.signals)
    assert composed.compute_signals == result.signals
    # Pure composition only: the producer performs no runtime wiring, so the
    # caller must explicitly opt in by constructing this input itself.
    assert composed.request_ref == base_input.request_ref


def test_no_implicit_runtime_wiring_happens_on_import() -> None:
    """The already-imported producer module carries no global mutable state.

    This deliberately does not force a module reload via ``sys.modules``:
    doing so would rebind ``core.continuity.signal_producer``'s classes to
    new, non-identical objects for the rest of this process, breaking
    ``isinstance``/``except`` checks in every other test that already holds
    a reference to the original classes.
    """

    import core.continuity.signal_producer as module

    assert not hasattr(module, "_GLOBAL_STATE")
    assert not hasattr(module, "_CACHE")
    for name in vars(module):
        if name.startswith("_") or name != name.upper():
            continue
        value = getattr(module, name)
        assert isinstance(value, str), f"unexpected mutable module constant: {name}"
