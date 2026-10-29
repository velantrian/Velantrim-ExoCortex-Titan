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


def test_explicit_legacy_singleton_retains_history_until_reset():
    initial = salience.get_salience_detector()
    results = observe(initial, [1, 2, 3])
    assert salience.get_salience_detector() is initial
    assert "topic_streak_3d" in results[-1].signals

    salience.reset_salience_detector()
    assert salience.get_salience_detector() is not initial
    assert observe(salience.get_salience_detector(), [3])[-1].signals == []


def test_unscoped_api_does_not_borrow_another_callers_history():
    # A uses the legacy singleton, while B calls the public helper with no
    # trustworthy scope. A's observations must not affect B's first episode.
    a = salience.get_salience_detector()
    observe(a, [1, 2])
    b = salience.analyze_episode_salience(
        TEXT, "B-first", now=datetime(2026, 10, 3, tzinfo=UTC)
    )
    assert b.signals == []
    assert b.weight == 1.0
    assert salience.get_salience_detector() is a

    # Two anonymous calls also cannot combine into a false third-day streak.
    for day in [1, 2, 3]:
        anonymous = salience.analyze_episode_salience(
            TEXT, f"anonymous-{day}", now=datetime(2026, 10, day, tzinfo=UTC)
        )
        assert "topic_streak_3d" not in anonymous.signals
        assert "topic_return_24h" not in anonymous.signals


def test_explicit_callers_keep_independent_temporal_history():
    first = salience.SalienceDetector()
    second = salience.SalienceDetector()
    for day in [1, 2]:
        salience.analyze_episode_salience(
            TEXT, f"A-{day}", now=datetime(2026, 10, day, tzinfo=UTC),
            detector=first,
        )
    b = salience.analyze_episode_salience(
        TEXT, "B-3", now=datetime(2026, 10, 3, tzinfo=UTC), detector=second
    )
    a = salience.analyze_episode_salience(
        TEXT, "A-3", now=datetime(2026, 10, 3, tzinfo=UTC), detector=first
    )
    assert b.signals == []
    assert b.weight == 1.0
    assert "topic_streak_3d" in a.signals
    assert "topic_return_24h" in a.signals
    assert a.weight == 3.2


def test_unscoped_api_keeps_text_signals_without_temporal_history():
    result = salience.analyze_episode_salience(
        "ВАЖНО! clarify bridge inspection", "B-text",
        now=datetime(2026, 10, 3, tzinfo=UTC),
    )
    assert result.signals == ["caps_lock", "exclamation", "priority_words", "clarification"]
    assert result.weight == pytest.approx(1.5 * 1.3 * 1.4 * 1.2)


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
