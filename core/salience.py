"""
Salience Detector — RFC0016 (Sprint 3+ / #23).

CPU-only детектор значимости эпизода. Вызывается ДО Velum.observe_episode.

Сигналы (мультипликативные, cap на max_weight):
  - caps_lock      ×1.5  (≥3 заглавных подряд)
  - exclamation    ×1.3
  - priority_words ×1.4  (важно, критично, никогда, всегда)
  - topic_streak   ×2.0  (тема 3+ календарных дня подряд)
  - topic_return   ×1.6  (возврат к теме после ≥24ч)
  - clarification  ×1.2  (переспрос / уточнение)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from core.feature_config import get_config

logger = logging.getLogger(__name__)

_CAPS_RE = re.compile(r"[A-ZА-ЯЁ]{3,}")
_EXCLAMATION_RE = re.compile(r"!{1,}")
_PRIORITY_WORDS = (
    "важно",
    "критично",
    "критический",
    "никогда",
    "всегда",
    "срочно",
    "обязательно",
)
_CLARIFICATION_MARKERS = (
    "уточни",
    "переспрос",
    "ещё раз",
    "еще раз",
    "поясни",
    "clarify",
    "again",
    "repeat",
)
_TOKEN_RE = re.compile(r"[\wА-Яа-яЁё]{4,}", re.UNICODE)


@dataclass(frozen=True)
class SalienceParams:
    multiplier_caps: float = 1.5
    multiplier_exclamation: float = 1.3
    multiplier_priority_words: float = 1.4
    multiplier_topic_streak: float = 2.0
    multiplier_topic_return: float = 1.6
    multiplier_clarification: float = 1.2
    topic_streak_days: int = 3
    topic_return_hours: float = 24.0
    max_weight: float = 4.0
    base_weight: float = 1.0


@dataclass
class SalienceResult:
    episode_id: str
    weight: float
    signals: list[str] = field(default_factory=list)
    topic_key: str = ""

    def to_metadata(self) -> dict[str, object]:
        return {
            "salience_weight": round(self.weight, 4),
            "salience_signals": json.dumps(self.signals, ensure_ascii=False),
            "salience_topic_key": self.topic_key,
        }


class _TopicTracker:
    """In-memory трекер тем для streak / return (Velum.I4-style)."""

    def __init__(self) -> None:
        self._last_seen: dict[str, datetime] = {}
        self._day_sets: dict[str, set[date]] = {}

    def observe(self, topic_key: str, now: datetime) -> tuple[bool, bool]:
        """
        Returns:
            (topic_streak_3plus_days, topic_return_after_pause)
        """
        today = now.date()
        days = self._day_sets.setdefault(topic_key, set())
        days.add(today)
        # Храним только последние 14 дней
        cutoff = today - timedelta(days=14)
        self._day_sets[topic_key] = {d for d in days if d >= cutoff}

        streak = _consecutive_days_count(self._day_sets[topic_key]) >= 3

        return_after_pause = False
        prev = self._last_seen.get(topic_key)
        if prev is not None:
            hours = (now - prev).total_seconds() / 3600.0
            if hours >= 24.0:
                return_after_pause = True
        self._last_seen[topic_key] = now
        return streak, return_after_pause


_topic_tracker = _TopicTracker()


def _consecutive_days_count(days: set[date]) -> int:
    if not days:
        return 0
    sorted_days = sorted(days)
    best = 1
    cur = 1
    for i in range(1, len(sorted_days)):
        if (sorted_days[i] - sorted_days[i - 1]).days == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def _topic_key_from_text(text: str) -> str:
    tokens = _TOKEN_RE.findall((text or "").lower())
    if not tokens:
        return "empty"
    # Топ-5 лексем по алфавиту — стабильный ключ темы
    key_tokens = sorted(set(tokens))[:5]
    return "|".join(key_tokens)


class SalienceDetector:
    def __init__(self, params: SalienceParams | None = None) -> None:
        self._params = params or SalienceParams()
        self._tracker = _topic_tracker

    def analyze(
        self,
        text: str,
        episode_id: str,
        *,
        now: datetime | None = None,
    ) -> SalienceResult:
        if now is None:
            now = datetime.now(UTC)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        p = self._params
        t = text or ""
        t_lower = t.lower()
        weight = p.base_weight
        signals: list[str] = []

        if _CAPS_RE.search(t):
            weight *= p.multiplier_caps
            signals.append("caps_lock")

        if _EXCLAMATION_RE.search(t):
            weight *= p.multiplier_exclamation
            signals.append("exclamation")

        if any(w in t_lower for w in _PRIORITY_WORDS):
            weight *= p.multiplier_priority_words
            signals.append("priority_words")

        if any(m in t_lower for m in _CLARIFICATION_MARKERS):
            weight *= p.multiplier_clarification
            signals.append("clarification")

        topic_key = _topic_key_from_text(t)
        streak, returned = self._tracker.observe(topic_key, now)
        if streak:
            weight *= p.multiplier_topic_streak
            signals.append("topic_streak_3d")
        if returned:
            weight *= p.multiplier_topic_return
            signals.append("topic_return_24h")

        weight = min(p.max_weight, max(p.base_weight, weight))

        if signals:
            logger.debug(
                "salience: episode=%s weight=%.2f signals=%s topic=%s",
                episode_id,
                weight,
                signals,
                topic_key[:40],
            )

        return SalienceResult(
            episode_id=episode_id,
            weight=weight,
            signals=signals,
            topic_key=topic_key,
        )


_detector: SalienceDetector | None = None


def get_salience_detector() -> SalienceDetector:
    global _detector
    if _detector is None:
        _detector = SalienceDetector()
    return _detector


def reset_salience_detector() -> None:
    global _detector, _topic_tracker
    _detector = None
    _topic_tracker = _TopicTracker()


def is_salience_enabled() -> bool:
    return bool(get_config().app.enable_salience)


def analyze_episode_salience(
    text: str,
    episode_id: str,
    *,
    now: datetime | None = None,
) -> SalienceResult:
    return get_salience_detector().analyze(text, episode_id, now=now)


async def persist_salience_metadata(
    graphiti,
    *,
    episode_uuid: str,
    result: SalienceResult,
) -> bool:
    if not episode_uuid or graphiti is None:
        return False
    try:
        driver = graphiti.driver
        meta = result.to_metadata()
        await driver.execute_query(
            """
            MATCH (e:Episodic {uuid: $uuid})
            SET e.salience_weight = $weight,
                e.salience_signals = $signals,
                e.salience_topic_key = $topic_key
            """,
            uuid=episode_uuid,
            weight=meta["salience_weight"],
            signals=meta["salience_signals"],
            topic_key=meta["salience_topic_key"],
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("persist_salience_metadata failed %s: %s", episode_uuid, exc)
        return False


__all__ = [
    "SalienceDetector",
    "SalienceParams",
    "SalienceResult",
    "analyze_episode_salience",
    "get_salience_detector",
    "is_salience_enabled",
    "persist_salience_metadata",
    "reset_salience_detector",
]
