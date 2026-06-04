"""
L6 Horizons MVP — WelfareMonitor (Velantrim V8.6 Complex, RFC0069).
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from core.runtime_flags import get_welfare_settings, is_l6_welfare_enabled

logger = logging.getLogger(__name__)

_monitors: dict[str, WelfareMonitor] = {}


class WelfareLevel(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass
class WelfareSnapshot:
    level: str
    goal_alignment: float
    error_rate: float
    volition_rate: float
    truth_gate_fail_rate: float
    distress_signal: float
    event_count: int
    reasons: list[str] = field(default_factory=list)
    updated_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "goal_alignment": round(self.goal_alignment, 3),
            "error_rate": round(self.error_rate, 3),
            "volition_rate": round(self.volition_rate, 3),
            "truth_gate_fail_rate": round(self.truth_gate_fail_rate, 3),
            "distress_signal": round(self.distress_signal, 3),
            "event_count": self.event_count,
            "reasons": self.reasons,
            "updated_at": self.updated_at,
        }


class WelfareMonitor:
    def __init__(self, user_id: str = "default") -> None:
        self.user_id = user_id
        self._events: deque[tuple[float, str, dict[str, Any]]] = deque(maxlen=500)
        self._last_level: str = WelfareLevel.GREEN.value
        self._goal_alignment: float = 0.5

    def _prune(self, now: float) -> None:
        window = float(get_welfare_settings().welfare_window_seconds)
        while self._events and now - self._events[0][0] > window:
            self._events.popleft()

    def record(
        self,
        kind: str,
        *,
        meta: dict[str, Any] | None = None,
    ) -> WelfareSnapshot:
        now = time.time()
        self._events.append((now, kind, meta or {}))
        self._prune(now)
        if kind == "chat" and meta and meta.get("importance") is not None:
            imp = float(meta["importance"])
            self._goal_alignment = min(1.0, self._goal_alignment * 0.9 + imp * 0.1)
        if kind == "focus_sync" and meta and meta.get("goal_alignment") is not None:
            self._goal_alignment = float(meta["goal_alignment"])
        return self.snapshot()

    def record_error(self, message: str = "") -> WelfareSnapshot:
        return self.record("error", meta={"message": message[:200]})

    def record_truth_gate(self, *, passed: bool) -> WelfareSnapshot:
        return self.record("truth_ok" if passed else "truth_fail")

    def record_volition(self) -> WelfareSnapshot:
        return self.record("volition")

    def snapshot(self) -> WelfareSnapshot:
        now = time.time()
        self._prune(now)
        cfg = get_welfare_settings()
        window = max(1.0, float(cfg.welfare_window_seconds))

        errors = truth_fail = truth_total = volitions = somatic_stress = 0.0
        for _, kind, meta in self._events:
            if kind == "error":
                errors += 1
            elif kind == "somatic" and meta:
                somatic_stress += float(meta.get("distress", 0.2))
            elif kind == "truth_fail":
                truth_fail += 1
                truth_total += 1
            elif kind == "truth_ok":
                truth_total += 1
            elif kind == "volition":
                volitions += 1

        total = len(self._events)
        error_rate = errors / max(1, total)
        truth_gate_fail_rate = truth_fail / truth_total if truth_total else 0.0
        volition_rate = volitions / (window / 60.0)
        volition_burst = volitions > cfg.welfare_max_volitions_per_window

        distress = min(
            1.0,
            (1.0 - self._goal_alignment) * 0.35
            + error_rate * 0.35
            + truth_gate_fail_rate * 0.2
            + (0.15 if volition_burst else 0.0)
            + min(0.25, somatic_stress * 0.15),
        )

        reasons: list[str] = []
        level = WelfareLevel.GREEN.value

        if (
            distress >= cfg.welfare_distress_red
            or error_rate >= cfg.welfare_error_rate_red
            or volition_burst
        ):
            level = WelfareLevel.RED.value
            if distress >= cfg.welfare_distress_red:
                reasons.append("distress_high")
            if error_rate >= cfg.welfare_error_rate_red:
                reasons.append("error_rate_high")
            if volition_burst:
                reasons.append("volition_burst")
        elif (
            distress >= cfg.welfare_distress_yellow
            or error_rate >= cfg.welfare_error_rate_yellow
            or self._goal_alignment < cfg.welfare_goal_alignment_yellow
            or truth_gate_fail_rate >= cfg.welfare_truth_fail_rate_yellow
        ):
            level = WelfareLevel.YELLOW.value
            if error_rate >= cfg.welfare_error_rate_yellow:
                reasons.append("error_rate_elevated")
            if self._goal_alignment < cfg.welfare_goal_alignment_yellow:
                reasons.append("low_goal_alignment")
            if truth_gate_fail_rate >= cfg.welfare_truth_fail_rate_yellow:
                reasons.append("truth_gate_stress")

        return WelfareSnapshot(
            level=level,
            goal_alignment=self._goal_alignment,
            error_rate=error_rate,
            volition_rate=volition_rate,
            truth_gate_fail_rate=truth_gate_fail_rate,
            distress_signal=distress,
            event_count=total,
            reasons=reasons,
        )

    def apply_level(self, snap: WelfareSnapshot) -> None:
        if snap.level != self._last_level:
            logger.info(
                "Welfare %s: %s → %s (%s)",
                self.user_id,
                self._last_level,
                snap.level,
                snap.reasons,
            )
        self._last_level = snap.level


def get_welfare_monitor(user_id: str = "default") -> WelfareMonitor:
    uid = user_id or "default"
    if uid not in _monitors:
        _monitors[uid] = WelfareMonitor(uid)
    return _monitors[uid]


def reset_welfare_monitors() -> None:
    _monitors.clear()


__all__ = [
    "WelfareLevel",
    "WelfareMonitor",
    "WelfareSnapshot",
    "get_welfare_monitor",
    "is_l6_welfare_enabled",
    "reset_welfare_monitors",
]
