"""
L4.5 EventBus handlers — ResponseAudit + FocusEngine (Slow Path, I28).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_l45_registered = False


def register_l45_handlers() -> None:
    global _l45_registered
    from core.event_bus import get_event_bus, is_event_bus_enabled

    if not is_event_bus_enabled() or _l45_registered:
        return

    bus = get_event_bus()
    _l45_registered = True

    async def _on_response_generated(event: dict[str, Any]) -> None:
        from core.response_audit import audit_response_generated, is_response_audit_enabled

        if not is_response_audit_enabled():
            return
        p = event.get("payload") or {}
        await audit_response_generated(
            conversation_id=p.get("conversation_id", ""),
            response_id=p.get("response_id", ""),
            reply_preview=p.get("reply_preview", ""),
            fact_ids=p.get("fact_ids"),
        )

    async def _on_chat_turn(event: dict[str, Any]) -> None:
        from core.focus_engine import get_focus_engine, is_focus_engine_enabled

        if not is_focus_engine_enabled():
            return
        p = event.get("payload") or {}
        uid = p.get("user_id", "default")
        fe = get_focus_engine(uid)
        fe.update_from_episode(
            query_hint=p.get("message", ""),
            domain=p.get("domain", ""),
            importance=float(p.get("importance", 0.5)),
        )
        if fe.vector.updates % 5 == 0:
            fe.snapshot()

    async def _on_etir(event: dict[str, Any]) -> None:
        logger.debug("Etir event: %s", (event.get("payload") or {}).get("edges"))

    bus.subscribe("RESPONSE_GENERATED", _on_response_generated)
    bus.subscribe("CHAT_TURN", _on_chat_turn)
    bus.subscribe("ETIR_OBSERVED", _on_etir)


__all__ = ["register_l45_handlers"]
