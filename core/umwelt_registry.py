"""
Umwelt MVP — извлечение объекта из запроса и сбор перспектив из store.
"""

from __future__ import annotations

import re
from typing import Any

from core.umwelt_store import UmweltPerception, get_umwelt_store

_WS = re.compile(r"\s+")

# object_key → паттерны в запросе (ru/en)
OBJECT_DETECTORS: list[tuple[str, re.Pattern]] = [
    ("tree", re.compile(r"дерев|лес|древес|растен|\btree\b", re.I)),
    ("rain", re.compile(r"дожд|\brain\b|осадк", re.I)),
    ("house", re.compile(r"дом|строен|здан|\bhouse\b", re.I)),
]

try:
    from core.poly_welt_registry import agent_display, all_agent_ids, priority_order

    MVP_PERCEIVER_IDS = all_agent_ids()
    _AGENT_DISPLAY = {
        aid: agent_display(aid, "") for aid in MVP_PERCEIVER_IDS
    }
    _PRIORITY_ORDER = priority_order()
except ImportError:
    MVP_PERCEIVER_IDS = frozenset(
        {
            "agent:engineer",
            "agent:scientist",
            "agent:observer",
            "agent:passer_domesticus",
        }
    )
    _AGENT_DISPLAY = {
        "agent:engineer": ("👷", "Инженер"),
        "agent:scientist": ("🔬", "Учёный"),
        "agent:observer": ("👁️", "Наблюдатель"),
        "agent:passer_domesticus": ("🐦", "Воробей"),
    }
    _PRIORITY_ORDER = {
        "agent:engineer": 0,
        "agent:scientist": 1,
        "agent:passer_domesticus": 2,
        "agent:observer": 3,
    }

UMWELT_MAX_PERCEIVERS = 6


def detect_object_key(query: str) -> str | None:
    for key, pattern in OBJECT_DETECTORS:
        if pattern.search(query or ""):
            return key
    return None


def resolve_perceptions(
    query: str,
    *,
    object_key: str | None = None,
    max_perceivers: int = UMWELT_MAX_PERCEIVERS,
) -> tuple[str | None, list[UmweltPerception]]:
    """Найти object_key и загрузить perceptions из БД."""
    obj = object_key or detect_object_key(query)
    if not obj:
        return None, []
    store = get_umwelt_store()
    if store.count() == 0:
        return obj, []
    items = store.list_by_object(obj, limit=max_perceivers * 2)
    order = _PRIORITY_ORDER
    items.sort(key=lambda p: (order.get(p.perceiver_id, 9), -p.confidence))
    seen: set[str] = set()
    out: list[UmweltPerception] = []
    for p in items:
        if p.perceiver_id in seen:
            continue
        seen.add(p.perceiver_id)
        out.append(p)
        if len(out) >= max_perceivers:
            break
    return obj, out


def perceptions_to_lens_format(
    perceptions: list[UmweltPerception],
) -> list[dict[str, Any]]:
    """Формат для ModeRouter / QueryResponse."""
    result: list[dict[str, Any]] = []
    for p in perceptions:
        if p.perceiver_id in _AGENT_DISPLAY:
            emoji, label = _AGENT_DISPLAY[p.perceiver_id]
        else:
            try:
                from core.poly_welt_registry import agent_display as _ad

                emoji, label = _ad(p.perceiver_id, p.perceiver)
            except ImportError:
                emoji, label = "🌍", p.perceiver
        result.append(
            {
                "perception_id": p.perception_id,
                "agent_id": p.perceiver_id,
                "label": f"{emoji} {label}",
                "object": p.object_key,
                "object_label_ru": p.object_label_ru,
                "statement": p.statement,
                "affordances": p.affordances,
                "affordance": p.statement,
                "knowledge_status": p.knowledge_status,
                "confidence": p.confidence,
                "layer": p.layer,
                "source": "umwelt_store",
            }
        )
    return result


def ensure_seed_loaded() -> bool:
    """Автозагрузка seed при пустой таблице (если ENABLE_UMWELT_AUTO_SEED)."""
    import os

    if os.getenv("ENABLE_UMWELT_AUTO_SEED", "1").strip().lower() not in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return False
    store = get_umwelt_store()
    if store.count() > 0:
        return False
    try:
        from core.umwelt_store import load_seed_file

        load_seed_file()
        return True
    except Exception:
        return False


__all__ = [
    "detect_object_key",
    "ensure_seed_loaded",
    "perceptions_to_lens_format",
    "resolve_perceptions",
    "MVP_PERCEIVER_IDS",
]
