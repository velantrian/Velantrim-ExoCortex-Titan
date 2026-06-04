"""
LSM — Liquid State Machine rhythm predictor (read-only, L5.5 вход).

Эвристика ритма сессий по episodic timestamps. MVP без NumPy (I35).
"""

from __future__ import annotations

import logging
import statistics
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


def _parse_ts(raw: Any) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        dt = raw
    elif isinstance(raw, str):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        if hasattr(raw, "to_native"):
            dt = raw.to_native()
        else:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def rhythm_stability_from_intervals(hours: list[float]) -> float:
    """
    Стабильность ритма 0..1: низкая дисперсия интервалов → выше stability.
    """
    if len(hours) < 2:
        return 0.5
    try:
        mean_h = statistics.mean(hours)
        if mean_h <= 0:
            return 0.5
        stdev = statistics.pstdev(hours)
        cv = stdev / mean_h
        return max(0.0, min(1.0, 1.0 - cv))
    except statistics.StatisticsError:
        return 0.5


async def predict_rhythm_topic(
    episodes: Iterable[dict[str, Any]],
    *,
    query: str = "",
) -> dict[str, Any]:
    """
    LSM prediction: {topic, confidence, timing, rhythm_stability}.
    """
    eps = list(episodes)
    timestamps: list[datetime] = []
    topics: list[str] = []

    for ep in eps:
        for key in ("created_at", "valid_at", "timestamp"):
            ts = _parse_ts(ep.get(key))
            if ts:
                timestamps.append(ts)
                break
        name = (ep.get("name") or ep.get("source_description") or "").strip()
        if name:
            topics.append(name.lower()[:80])

    rhythm_stability = 0.5
    topic: str | None = None
    confidence = 0.3
    timing: dict[str, Any] = {}

    if len(timestamps) >= 2:
        timestamps.sort()
        gaps_h = [
            (timestamps[i] - timestamps[i - 1]).total_seconds() / 3600.0
            for i in range(1, len(timestamps))
        ]
        rhythm_stability = rhythm_stability_from_intervals(gaps_h)
        timing = {
            "last_gap_hours": gaps_h[-1] if gaps_h else None,
            "session_count": len(timestamps),
        }

    if topics:
        common = Counter(topics).most_common(1)[0][0]
        topic = common.split()[0] if common else None
        confidence = min(0.85, 0.35 + 0.1 * len(topics))

    if not topic and query:
        q = query.strip().lower()
        if len(q) >= 4:
            topic = q.split()[0]
            confidence = 0.4

    if rhythm_stability > 0.7:
        confidence = min(0.9, confidence + 0.15)

    return {
        "topic": topic,
        "confidence": confidence,
        "timing": timing,
        "rhythm_stability": rhythm_stability,
        "source": "lsm",
    }


__all__ = ["predict_rhythm_topic", "rhythm_stability_from_intervals"]
