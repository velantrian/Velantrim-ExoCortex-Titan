"""Calendar-streak and detector-lifetime regressions; no provider or graph calls."""

from datetime import UTC, datetime

import pytest

from core import salience


TEXT = "bridge inspection schedule"


@pytest.fixture(autouse=True)
def reset_default_history():
    salience.reset_salience_detector()
    yield
    salience.reset_salience_detector()


def observe(detector, days):
    return [
        detector.analyze(TEXT, f"episode-{i}", now=datetime(2026, 10, day, tzinfo=UTC))
        for i, day in enumerate(days)
    ]


@pytest.mark.parametrize(
    ("days", "expected_streak"),
    [
        ([1, 2, 3], True),
        ([1, 2, 3, 10], False),
        ([1, 2, 4], False),
        ([1, 2, 3, 10, 11, 12], True),
        ([1, 1, 1], False),
    ],
)
def test_streak_must_end_on_current_observation(days, expected_streak):
    result = observe(salience.SalienceDetector(), days)[-1]
    assert ("topic_streak_3d" in result.signals) is expected_streak


def test_detector_instances_do_not_share_topic_history():
    first = salience.SalienceDetector()
    second = salience.SalienceDetector()
    observe(first, [1, 2])

    fresh_result = observe(second, [3])[-1]
    assert fresh_result.signals == []
    assert fresh_result.weight == 1.0

    # Positive control: the original detector retains its own consecutive days.
    assert "topic_streak_3d" in observe(first, [3])[-1].signals


def test_new_topic_does_not_inherit_another_topic_streak():
    detector = salience.SalienceDetector()
    observe(detector, [1, 2, 3])
    result = detector.analyze(
        "garden irrigation calendar", "garden", now=datetime(2026, 10, 3, tzinfo=UTC)
    )
    assert result.signals == []
    assert "topic_streak_3d" in observe(detector, [4])[-1].signals


def test_default_detector_retains_history_until_explicit_reset():
    salience.reset_salience_detector()
    try:
        initial = salience.get_salience_detector()
        for day in [1, 2, 3]:
            result = salience.analyze_episode_salience(
                TEXT, f"default-{day}", now=datetime(2026, 10, day, tzinfo=UTC)
            )
        assert salience.get_salience_detector() is initial
        assert "topic_streak_3d" in result.signals

        salience.reset_salience_detector()
        assert salience.get_salience_detector() is not initial
        assert observe(salience.get_salience_detector(), [3])[-1].signals == []
    finally:
        salience.reset_salience_detector()


def test_existing_text_signals_and_weight_cap_are_preserved():
    result = salience.SalienceDetector().analyze(
        "ВАЖНО! clarify bridge inspection", "text", now=datetime(2026, 10, 1, tzinfo=UTC)
    )
    assert result.signals == ["caps_lock", "exclamation", "priority_words", "clarification"]
    assert result.weight == pytest.approx(1.5 * 1.3 * 1.4 * 1.2)
    capped = salience.SalienceDetector(salience.SalienceParams(max_weight=2.0)).analyze(
        "ВАЖНО! clarify bridge inspection", "capped", now=datetime(2026, 10, 1, tzinfo=UTC)
    )
    assert capped.weight == 2.0
