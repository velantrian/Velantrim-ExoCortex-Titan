"""
L6 MVP — EventBus → WelfareMonitor (Velantrim V8.6 Complex).
"""

from __future__ import annotations

import logging
from typing import Any

from core.runtime_flags import is_event_bus_enabled, is_l6_welfare_enabled

logger = logging.getLogger(__name__)

_l6_registered = False


async def _maybe_publish_welfare_change(
    user_id: str,
    snap_dict: dict[str, Any],
    *,
    previous_level: str,
) -> None:
    if snap_dict.get("level") == previous_level:
        return
    try:
        from core.event_bridge import publish_event

        await publish_event(
            "WELFARE_STATE_CHANGED",
            {
                "user_id": user_id,
                "previous_level": previous_level,
                "level": snap_dict.get("level"),
                "reasons": snap_dict.get("reasons", []),
                "distress_signal": snap_dict.get("distress_signal"),
            },
            source="l6_welfare",
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("welfare event: %s", exc)


def register_l6_handlers() -> None:
    global _l6_registered
    from core.event_bus import get_event_bus
    from core.welfare_monitor import get_welfare_monitor

    if not is_l6_welfare_enabled() or not is_event_bus_enabled() or _l6_registered:
        return

    bus = get_event_bus()
    _l6_registered = True

    async def _on_chat_turn(event: dict[str, Any]) -> None:
        p = event.get("payload") or {}
        uid = p.get("user_id", "default")
        mon = get_welfare_monitor(uid)
        prev = mon._last_level  # noqa: SLF001
        snap = mon.record("chat", meta={"importance": float(p.get("importance", 0.5))})
        mon.apply_level(snap)
        await _maybe_publish_welfare_change(uid, snap.to_dict(), previous_level=prev)

    async def _on_truth_gate(event: dict[str, Any]) -> None:
        p = event.get("payload") or {}
        uid = p.get("user_id", "default")
        mon = get_welfare_monitor(uid)
        prev = mon._last_level  # noqa: SLF001
        snap = mon.record_truth_gate(passed=bool(p.get("passed")))
        mon.apply_level(snap)
        await _maybe_publish_welfare_change(uid, snap.to_dict(), previous_level=prev)

    async def _on_volition(event: dict[str, Any]) -> None:
        p = event.get("payload") or {}
        uid = p.get("user_id", "default")
        mon = get_welfare_monitor(uid)
        prev = mon._last_level  # noqa: SLF001
        snap = mon.record_volition()
        mon.apply_level(snap)
        await _maybe_publish_welfare_change(uid, snap.to_dict(), previous_level=prev)

    async def _on_response(event: dict[str, Any]) -> None:
        p = event.get("payload") or {}
        uid = p.get("user_id", "default")
        mon = get_welfare_monitor(uid)
        prev = mon._last_level  # noqa: SLF001
        snap = mon.record("response", meta={"len": len(p.get("reply_preview", ""))})
        mon.apply_level(snap)
        await _maybe_publish_welfare_change(uid, snap.to_dict(), previous_level=prev)

    bus.subscribe("CHAT_TURN", _on_chat_turn)
    bus.subscribe("TRUTH_GATE_VERDICT", _on_truth_gate)
    bus.subscribe("MEMORY_VOLITION", _on_volition)
    bus.subscribe("RESPONSE_GENERATED", _on_response)


def record_runtime_error(user_id: str = "default", message: str = "") -> None:
    if not is_l6_welfare_enabled():
        return
    from core.welfare_monitor import get_welfare_monitor

    mon = get_welfare_monitor(user_id)
    snap = mon.record_error(message)
    mon.apply_level(snap)


def reset_l6_handlers() -> None:
    global _l6_registered
    _l6_registered = False


__all__ = ["register_l6_handlers", "record_runtime_error", "reset_l6_handlers"]
