"""
Публикация доменных событий в EventBus (Velantrim V8.6 Complex).
"""

from __future__ import annotations

import logging
from typing import Any

from core.event_bus import get_event_bus, use_background_dispatch
from core.feature_config import get_config


def _enabled() -> bool:
    return get_config().app.enable_event_bus

logger = logging.getLogger(__name__)

_handlers_registered = False


async def publish_event(
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    source: str = "velantrim",
) -> bool:
    if not _enabled():
        return False
    try:
        event = {"type": event_type, "source": source, "payload": payload or {}}
        return await get_event_bus().publish(
            event, dispatch=not use_background_dispatch()
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("publish_event: %s", exc)
        return False


async def on_truth_gate_verdict(
    *,
    episode_uuid: str,
    passed: bool,
    reason: str,
    epistemic_state: str,
    user_id: str = "default",
) -> None:
    await publish_event(
        "TRUTH_GATE_VERDICT",
        {
            "episode_uuid": episode_uuid,
            "passed": passed,
            "reason": reason,
            "epistemic_state": epistemic_state,
            "user_id": user_id,
        },
    )


async def on_causal_relation(
    relation_id: str,
    from_fact_id: str,
    to_fact_id: str,
    relation_type: str,
) -> None:
    """Slow Path: новое каузальное ребро (ingest heuristic / bridge)."""
    await publish_event(
        "CAUSAL_RELATION_ADDED",
        {
            "relation_id": relation_id,
            "from_fact_id": from_fact_id,
            "to_fact_id": to_fact_id,
            "relation_type": relation_type,
        },
    )


async def on_concept_born(protos_born: list[Any], session_id: str) -> None:
    """Slow Path: эмерджентный прото-концепт «родился» (ConceptEmergence)."""
    await publish_event(
        "CONCEPT_BORN",
        {"protos": list(protos_born), "session_id": session_id},
    )


async def on_query_completed(
    *,
    user_id: str = "default",
    query: str,
    answer_preview: str = "",
    importance: float = 0.5,
) -> None:
    await publish_event(
        "RESPONSE_GENERATED",
        {
            "user_id": user_id,
            "conversation_id": user_id,
            "response_id": "",
            "reply_preview": answer_preview[:500],
            "query": query[:200],
            "importance": importance,
        },
    )


def register_default_handlers() -> None:
    global _handlers_registered
    if not _enabled() or _handlers_registered:
        return
    _handlers_registered = True
    try:
        from core.l6_bridge import register_l6_handlers

        register_l6_handlers()
    except Exception as exc:  # noqa: BLE001
        logger.debug("l6 handlers: %s", exc)

    try:
        from core.l45_bridge import register_l45_handlers

        register_l45_handlers()
    except Exception as exc:  # noqa: BLE001
        logger.debug("l45 handlers: %s", exc)

    try:
        from core.cognitive_runtime import register_cognitive_runtime_handlers

        register_cognitive_runtime_handlers()
    except Exception as exc:  # noqa: BLE001
        logger.debug("cognitive runtime handlers: %s", exc)


def reset_event_handlers() -> None:
    global _handlers_registered
    _handlers_registered = False
    try:
        from core.l6_bridge import reset_l6_handlers

        reset_l6_handlers()
    except Exception:  # noqa: BLE001
        pass


__all__ = [
    "on_causal_relation",
    "on_query_completed",
    "on_truth_gate_verdict",
    "publish_event",
    "register_default_handlers",
    "reset_event_handlers",
]
