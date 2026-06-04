"""
core/events.py — canonical event vocabulary + typed payload builders.

Ported (adapted) from a DeepSeek design that used frozen dataclasses. Canon's bus is
string-keyed — `core/event_bridge.publish_event(event_type: str, payload: dict)` over
`core/event_bus.EventBus.publish` — so this module provides the **event-name constants**
plus **payload builder functions** that fit that bus, instead of dataclasses that don't.

Purpose: stop ad-hoc event-name strings scattered across event_bridge.py; give one place
that defines the event catalogue and the shape of each payload. Additive — importing this
changes nothing; publishers opt in by using the constants + builders.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _now() -> str:
    return datetime.now(UTC).isoformat()


# ── Event names (UPPER_SNAKE — matches existing event_bridge usage) ─────────────
FACT_CREATED = "FACT_CREATED"
FACT_UPDATED = "FACT_UPDATED"
FACT_LINKED = "FACT_LINKED"
FACT_DEPRECATED = "FACT_DEPRECATED"
FACT_COLLAPSED = "FACT_COLLAPSED"
FACT_CONSOLIDATED = "FACT_CONSOLIDATED"
FACT_CONTRADICTED = "FACT_CONTRADICTED"
ESM_TRANSITION = "ESM_TRANSITION"
CHAT_TURN = "CHAT_TURN"
RETRIEVER_DIRTY = "RETRIEVER_DIRTY"

ALL_EVENTS = (
    FACT_CREATED, FACT_UPDATED, FACT_LINKED, FACT_DEPRECATED, FACT_COLLAPSED,
    FACT_CONSOLIDATED, FACT_CONTRADICTED, ESM_TRANSITION, CHAT_TURN, RETRIEVER_DIRTY,
)


# ── Payload builders (return plain dicts ready for publish_event) ────────────────

def make_fact_created(fact_id: str, source: str) -> dict[str, Any]:
    return {"fact_id": fact_id, "source": source, "timestamp": _now()}


def make_fact_updated(fact_id: str, field: str, old_value: Any, new_value: Any) -> dict[str, Any]:
    return {"fact_id": fact_id, "field": field, "old_value": old_value,
            "new_value": new_value, "timestamp": _now()}


def make_fact_linked(from_fact_id: str, to_fact_id: str, relation_type: str,
                     knowledge_status: str = "inferred") -> dict[str, Any]:
    return {"from_fact_id": from_fact_id, "to_fact_id": to_fact_id,
            "relation_type": relation_type, "knowledge_status": knowledge_status,
            "timestamp": _now()}


def make_fact_deprecated(fact_id: str, reason: str) -> dict[str, Any]:
    return {"fact_id": fact_id, "reason": reason, "timestamp": _now()}


def make_fact_collapsed(fact_id: str) -> dict[str, Any]:
    return {"fact_id": fact_id, "timestamp": _now()}


def make_fact_consolidated(source_ids: list[str], result_id: str,
                           operation: str = "merge") -> dict[str, Any]:
    return {"source_ids": list(source_ids), "result_id": result_id,
            "operation": operation, "timestamp": _now()}


def make_fact_contradicted(fact_id_a: str, fact_id_b: str, detected_by: str) -> dict[str, Any]:
    return {"fact_id_a": fact_id_a, "fact_id_b": fact_id_b,
            "detected_by": detected_by, "timestamp": _now()}


def make_esm_transition(fact_id: str, old_state: str, new_state: str,
                        triggered_by: str = "unknown") -> dict[str, Any]:
    return {"fact_id": fact_id, "old_state": old_state, "new_state": new_state,
            "triggered_by": triggered_by, "timestamp": _now()}


def make_chat_turn(query: str, trace_fact_ids: list[str] | None = None,
                   mode: str = "BALANCED") -> dict[str, Any]:
    return {"query": query, "trace_fact_ids": list(trace_fact_ids or []),
            "mode": mode, "timestamp": _now()}


def make_retriever_dirty(reason: str = "fact_change",
                         fact_id: str | None = None) -> dict[str, Any]:
    return {"reason": reason, "fact_id": fact_id, "timestamp": _now()}


# event_name → builder (for tests / introspection)
BUILDERS = {
    FACT_CREATED: make_fact_created,
    FACT_UPDATED: make_fact_updated,
    FACT_LINKED: make_fact_linked,
    FACT_DEPRECATED: make_fact_deprecated,
    FACT_COLLAPSED: make_fact_collapsed,
    FACT_CONSOLIDATED: make_fact_consolidated,
    FACT_CONTRADICTED: make_fact_contradicted,
    ESM_TRANSITION: make_esm_transition,
    CHAT_TURN: make_chat_turn,
    RETRIEVER_DIRTY: make_retriever_dirty,
}

__all__ = [
    *ALL_EVENTS, "ALL_EVENTS", "BUILDERS",
    "make_fact_created", "make_fact_updated", "make_fact_linked",
    "make_fact_deprecated", "make_fact_collapsed", "make_fact_consolidated",
    "make_fact_contradicted", "make_esm_transition", "make_chat_turn",
    "make_retriever_dirty",
]
