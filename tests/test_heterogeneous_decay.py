"""Tests for heterogeneous (volatility-aware) decay (Increment 3)."""
from __future__ import annotations

from core.fsrs import (
    VOLATILITY_MULTIPLIERS,
    decay_edge_weight,
    decay_edge_weight_v,
    volatility_stability,
)

# ── volatility_stability ─────────────────────────────────────────────────────────

def test_medium_is_identity():
    assert volatility_stability(7.0, "medium") == 7.0


def test_stable_increases_volatile_decreases():
    assert volatility_stability(7.0, "stable") > 7.0
    assert volatility_stability(7.0, "volatile") < 7.0


def test_unknown_class_defaults_medium():
    assert volatility_stability(7.0, "nonsense") == 7.0


def test_multiplier_table_sane():
    assert VOLATILITY_MULTIPLIERS["stable"] > VOLATILITY_MULTIPLIERS["medium"] \
        > VOLATILITY_MULTIPLIERS["volatile"]


# ── decay_edge_weight_v backward-compat + ordering ──────────────────────────────

def test_medium_matches_baseline_exactly():
    base = decay_edge_weight(1.0, t_days=10.0, stability=7.0)
    hetero = decay_edge_weight_v(1.0, t_days=10.0, stability=7.0, volatility_class="medium")
    assert hetero == base  # default must reproduce current math EXACTLY


def test_volatile_decays_faster_than_stable():
    w_stable = decay_edge_weight_v(1.0, t_days=30.0, stability=7.0, volatility_class="stable")
    w_volatile = decay_edge_weight_v(1.0, t_days=30.0, stability=7.0, volatility_class="volatile")
    assert w_volatile < w_stable  # at equal age, volatile retains less


def test_orchestrator_default_unchanged():
    # DecayTarget defaults to medium ⇒ volatility branch is a no-op
    from core.decay_orchestrator import DecayTarget

    t = DecayTarget(weight=1.0, t_days=10.0, stability_days=7.0)
    assert getattr(t, "volatility_class", "medium") == "medium"
