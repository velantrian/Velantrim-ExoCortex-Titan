"""
L6 MVP — VolitionGate (Velantrim V8.6 Complex).
"""

from __future__ import annotations

from typing import Any

from core.welfare_monitor import WelfareLevel, get_welfare_monitor


def check_volition_allowed(user_id: str = "default") -> tuple[bool, str, dict[str, Any]]:
    from core.runtime_flags import is_l6_welfare_enabled

    if not is_l6_welfare_enabled():
        return True, "", {}

    snap = get_welfare_monitor(user_id).snapshot()
    welfare = snap.to_dict()

    if snap.level == WelfareLevel.RED.value:
        reason = "welfare_red: " + (
            ", ".join(snap.reasons) if snap.reasons else "distress"
        )
        return False, reason, welfare

    if snap.level == WelfareLevel.YELLOW.value:
        welfare["warning"] = "welfare_yellow: volition allowed with caution"

    return True, "", welfare


__all__ = ["check_volition_allowed"]
