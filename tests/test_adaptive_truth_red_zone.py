"""
Regression test for the adaptive_truth.py RED-zone softening fix (Claude
audit 2026-07-28, Low).

AdaptiveTruthEngine is not wired into any production call site — this is
about the module's internal correctness, not live behavior. RED domains
(medicine, law, physics, finance, security, ...) are meant to be strict
regardless of user reaction: `_apply_satisfaction` previously lowered
min_confidence whenever satisfaction was high and domain trust was high,
with no exception for the RED zone — so a user being "happy" with a wrong
medical/legal claim would lower the very threshold meant to catch it.
"""
from __future__ import annotations

from core.adaptive_truth import AdaptiveTruthEngine


def test_high_satisfaction_does_not_soften_red_zone_threshold():
    engine = AdaptiveTruthEngine()
    for _ in range(10):
        engine.record_satisfaction("medicine", 0.95)  # trust > 0.6

    th = engine.get_threshold(domain="medicine", user_satisfaction=0.9)
    assert th.zone == "red"
    assert th.min_confidence == engine.RED.min_confidence, (
        "RED zone must not be softened by user satisfaction, "
        f"got min_confidence={th.min_confidence}"
    )


def test_low_satisfaction_can_still_tighten_red_zone_threshold():
    """The other branch (dissatisfaction → stricter) is untouched by this fix."""
    engine = AdaptiveTruthEngine()
    th = engine.get_threshold(domain="medicine", user_satisfaction=0.1)
    assert th.zone == "red"
    assert th.min_confidence > engine.RED.min_confidence


def test_high_satisfaction_still_softens_green_zone_threshold():
    """Sibling assertion: the softening behavior itself must survive for
    non-RED zones — this fix only carves out an exception for RED."""
    engine = AdaptiveTruthEngine()
    for _ in range(10):
        engine.record_satisfaction("ecology", 0.95)

    th = engine.get_threshold(domain="ecology", user_satisfaction=0.9)
    assert th.zone == "green"
    assert th.min_confidence < engine.GREEN.min_confidence
