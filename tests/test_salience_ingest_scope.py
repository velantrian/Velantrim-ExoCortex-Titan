"""Offline synthetic guards for SalienceDetector lifetime at the ingest bridge.

These tests deliberately do NOT construct an owner from an episode ID, source,
metadata, a shared API-key fingerprint, or any unverified user label.
"""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from core import salience, velum_bridge


TOPIC = "bridge inspection schedule"


class _Clock(datetime):
    current = datetime(2026, 10, 1, 10, tzinfo=UTC)

    @classmethod
    def now(cls, tz=None):
        if tz is None:
            return cls.current
        return cls.current.astimezone(tz)


class _VelumSpy:
    def __init__(self):
        self.weights: list[tuple[str, float]] = []

    async def observe_episode(self, episode_id, entities, *, salience_weight=1.0):
        self.weights.append((episode_id, salience_weight))
        return SimpleNamespace(
            edges_touched=0,
            entities_seen=len(entities),
            signals=[],
        )


@pytest.fixture
def ingest_spy(monkeypatch: pytest.MonkeyPatch) -> _VelumSpy:
    """Keep the real salience analyzer but prohibit external/persistent calls."""
    spy = _VelumSpy()
    _Clock.current = datetime(2026, 10, 1, 10, tzinfo=UTC)
    monkeypatch.setattr(salience, "datetime", _Clock)
    monkeypatch.setattr(salience, "is_salience_enabled", lambda: True)
    monkeypatch.setattr(velum_bridge, "get_velum", lambda: spy)
    return spy


async def _ingest(label: str, day: int, *, text: str = TOPIC) -> None:
    _Clock.current = datetime(2026, 10, day, 10, tzinfo=UTC)
    await velum_bridge.observe_episode_from_ingest(
        episode_id=label,
        entity_names=[],
        graphiti=None,
        episode_text=text,
    )


@pytest.mark.parametrize(
    "observations",
    [
        [("caller-A-1", 1), ("caller-A-2", 2), ("caller-B-3", 3), ("caller-A-3", 3)],
        [("caller-A-1", 1), ("caller-B-5", 5), ("caller-A-8", 8)],
    ],
)
def test_ingest_without_trusted_owner_cannot_mix_or_infer_temporal_history(
    ingest_spy: _VelumSpy,
    observations: list[tuple[str, int]],
) -> None:
    """Even matching text across putative callers is one-shot at this boundary."""

    async def run() -> None:
        for label, day in observations:
            await _ingest(label, day)

    asyncio.run(run())
    assert [weight for _, weight in ingest_spy.weights] == [1.0] * len(observations)


def test_ingest_does_not_borrow_explicit_legacy_singleton(
    ingest_spy: _VelumSpy,
) -> None:
    """An unrelated first observation must not inherit an old process history."""
    salience.reset_salience_detector()
    try:
        legacy = salience.get_salience_detector()
        for day in (1, 2):
            legacy.analyze(
                TOPIC,
                f"legacy-A-{day}",
                now=datetime(2026, 10, day, 10, tzinfo=UTC),
            )

        asyncio.run(_ingest("fresh-caller-B-3", 3))
        assert ingest_spy.weights == [("fresh-caller-B-3", 1.0)]
        assert salience.get_salience_detector() is legacy
    finally:
        salience.reset_salience_detector()


def test_ingest_preserves_text_signals_without_temporal_inheritance(
    ingest_spy: _VelumSpy,
) -> None:
    """Lexical weights work on each independent call, with no hidden state."""

    async def run() -> None:
        await _ingest("caller-A-1", 1, text="ВАЖНО! clarify bridge inspection")
        await _ingest("caller-B-3", 3, text="ВАЖНО! clarify bridge inspection")

    asyncio.run(run())
    expected = 1.5 * 1.3 * 1.4 * 1.2
    assert [value for _, value in ingest_spy.weights] == pytest.approx(
        [expected, expected]
    )


def test_explicit_synthetic_owners_accumulate_their_own_streaks() -> None:
    """Positive control: owned detectors work; the bridge still lacks an owner."""
    owner_a = salience.SalienceDetector()
    owner_b = salience.SalienceDetector()

    for day in (1, 2):
        salience.analyze_episode_salience(
            TOPIC,
            f"A-{day}",
            now=datetime(2026, 10, day, 10, tzinfo=UTC),
            detector=owner_a,
        )

    first_b = salience.analyze_episode_salience(
        TOPIC,
        "B-3",
        now=datetime(2026, 10, 3, 10, tzinfo=UTC),
        detector=owner_b,
    )
    third_a = salience.analyze_episode_salience(
        TOPIC,
        "A-3",
        now=datetime(2026, 10, 3, 10, tzinfo=UTC),
        detector=owner_a,
    )
    assert first_b.weight == 1.0
    assert first_b.signals == []
    assert third_a.weight == 3.2
    assert "topic_streak_3d" in third_a.signals
    assert "topic_return_24h" in third_a.signals

    for day in (4, 5):
        last_b = salience.analyze_episode_salience(
            TOPIC,
            f"B-{day}",
            now=datetime(2026, 10, day, 10, tzinfo=UTC),
            detector=owner_b,
        )
    assert last_b.weight == 3.2
    assert "topic_streak_3d" in last_b.signals


def test_explicit_synthetic_owners_keep_return_timers_separate() -> None:
    """A's return after 25h cannot be manufactured by B's observations."""
    owner_a = salience.SalienceDetector()
    owner_b = salience.SalienceDetector()

    a_first = salience.analyze_episode_salience(
        TOPIC, "A-1", now=datetime(2026, 10, 1, 10, tzinfo=UTC), detector=owner_a
    )
    b_first = salience.analyze_episode_salience(
        TOPIC, "B-1", now=datetime(2026, 10, 2, 10, tzinfo=UTC), detector=owner_b
    )
    a_return = salience.analyze_episode_salience(
        TOPIC, "A-2", now=datetime(2026, 10, 2, 11, tzinfo=UTC), detector=owner_a
    )
    b_short_gap = salience.analyze_episode_salience(
        TOPIC, "B-2", now=datetime(2026, 10, 2, 11, tzinfo=UTC), detector=owner_b
    )
    assert a_first.signals == []
    assert b_first.signals == []
    assert "topic_return_24h" in a_return.signals
    assert "topic_return_24h" not in b_short_gap.signals
