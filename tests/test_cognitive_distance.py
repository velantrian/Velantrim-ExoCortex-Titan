"""Unit tests for core/cognitive_distance.py (v0 baseline scoring)."""
from __future__ import annotations

from core.cognitive_distance import (
    DEFAULT_WEIGHTS,
    cognitive_distance,
    epistemic_weight,
    rank_by_distance,
)


def _fact(state="Validated", **extra):
    f = {"fact_id": extra.get("fact_id", "f"), "epistemic_state": state}
    f.update(extra)
    return f


def test_weights_sum_to_one():
    assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 1e-9


def test_epistemic_monotonic():
    assert (epistemic_weight("ImmutableCore") > epistemic_weight("Validated")
            > epistemic_weight("Observed") > epistemic_weight("Contradicted"))


def test_distance_in_range():
    d = cognitive_distance(_fact())
    assert 0.0 <= d <= 1.0


def test_validated_beats_contradicted():
    hi = cognitive_distance(_fact(state="Validated"))
    lo = cognitive_distance(_fact(state="Contradicted"))
    assert hi > lo


def test_temporal_decay_lowers_score():
    fresh = cognitive_distance(_fact(t_event_valid_start="2026-06-01T00:00:00+00:00"))
    old = cognitive_distance(_fact(t_event_valid_start="2020-01-01T00:00:00+00:00"))
    assert fresh > old


def test_rank_orders_by_distance():
    facts = [_fact(fact_id="a", state="Observed"),
             _fact(fact_id="b", state="ImmutableCore"),
             _fact(fact_id="c", state="Contradicted")]
    ranked = rank_by_distance(facts, top_k=3)
    assert [r["fact_id"] for r in ranked][0] == "b"
    assert ranked[0]["cognitive_distance"] >= ranked[-1]["cognitive_distance"]


def test_never_raises_on_sparse_fact():
    assert isinstance(cognitive_distance({}), float)  # missing everything → no crash
