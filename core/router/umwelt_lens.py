"""
Линза UMWELT — перспективы из umwelt_store (layer 99) + fallback-шаблоны.
"""

from __future__ import annotations

import re
from typing import Any

_WS = re.compile(r"\s+")

_AGENTS: list[dict[str, str]] = [
    {
        "id": "agent:engineer",
        "label": "Инженер",
        "emoji": "👷",
        "axis": "engineering",
        "affordance_template": "материал, нагрузка, конструкция, безопасность",
    },
    {
        "id": "agent:scientist",
        "label": "Учёный",
        "emoji": "🔬",
        "axis": "biological",
        "affordance_template": "процессы, экосистема, измеримые свойства",
    },
    {
        "id": "agent:observer",
        "label": "Наблюдатель",
        "emoji": "👁️",
        "axis": "systemic",
        "affordance_template": "контекст, риски, взаимосвязи между агентами",
    },
]

_TOPIC_TRIGGERS: list[tuple[re.Pattern, list[str]]] = [
    (re.compile(r"дерев|лес|растен", re.I), ["agent:engineer", "agent:scientist"]),
    (re.compile(r"дом|стро|инжен|конструк", re.I), ["agent:engineer", "agent:observer"]),
    (re.compile(r"дожд|вода|климат", re.I), ["agent:scientist", "agent:observer"]),
    (re.compile(r"памят|факт|граф|kuzu|neo4j", re.I), ["agent:engineer", "agent:observer"]),
]


def _select_agents(query: str) -> list[dict[str, str]]:
    chosen_ids: list[str] = []
    for pattern, ids in _TOPIC_TRIGGERS:
        if pattern.search(query):
            for aid in ids:
                if aid not in chosen_ids:
                    chosen_ids.append(aid)
    if not chosen_ids:
        chosen_ids = ["agent:engineer", "agent:scientist"]
    by_id = {a["id"]: a for a in _AGENTS}
    return [by_id[i] for i in chosen_ids if i in by_id]


def _project_fallback(
    query: str,
    facts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    q = _WS.sub(" ", (query or "").strip())
    topic = q[:120] if q else "объект"
    perspectives: list[dict[str, Any]] = []
    claim_hint = ""
    for f in facts[:3]:
        claim_hint = (f.get("claim") or "")[:80]
        break
    for agent in _select_agents(query):
        perspectives.append(
            {
                "agent_id": agent["id"],
                "label": f"{agent['emoji']} {agent['label']}",
                "axis": agent["axis"],
                "affordance": (
                    f"Для {agent['label']} «{topic}» релевантно: "
                    f"{agent['affordance_template']}."
                    + (f" Контекст из памяти: {claim_hint}" if claim_hint else "")
                ),
                "knowledge_status": "interpreted",
                "source": "umwelt_template",
            }
        )
    return perspectives


def project(
    query: str,
    facts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Перспективы Umwelt: store (layer 99) или шаблон."""
    try:
        from core.runtime_flags import is_umwelt_store_enabled

        if is_umwelt_store_enabled():
            from core.umwelt_registry import (
                ensure_seed_loaded,
                perceptions_to_lens_format,
                resolve_perceptions,
            )

            ensure_seed_loaded()
            obj_key, perceptions = resolve_perceptions(query)
            if perceptions:
                formatted = perceptions_to_lens_format(perceptions)
                for item in formatted:
                    item["object_key"] = obj_key
                return formatted
    except Exception:
        pass
    return _project_fallback(query, facts)


def filter_facts(
    facts: list[dict[str, Any]],
    query: str,
    user_id: str = "default",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Сохраняем факты; при store — boost perception-фактов layer 99."""
    _ = user_id
    perspectives = project(query, facts)
    boosted = list(facts)
    try:
        from core.runtime_flags import is_umwelt_store_enabled

        if is_umwelt_store_enabled():
            from core.umwelt_registry import detect_object_key

            obj = detect_object_key(query)
            if obj:
                perc_facts = [
                    f
                    for f in facts
                    if (f.get("metadata") or {}).get("layer") == 99
                    or (f.get("metadata") or {}).get("domain") == "perception"
                ]
                if perc_facts:
                    seen = {f.get("fact_id") for f in boosted}
                    for pf in perc_facts:
                        if pf.get("fact_id") not in seen:
                            boosted.insert(0, pf)
    except Exception:
        pass

    meta = {
        "perspectives": perspectives,
        "perspective_count": len(perspectives),
        "object_key": perspectives[0].get("object_key") if perspectives else None,
        "data_source": perspectives[0].get("source", "unknown")
        if perspectives
        else "none",
        "note": "Параллельные истины разных Umwelt не являются противоречиями.",
    }
    return boosted, meta


def system_instructions(user_id: str = "default") -> str:
    _ = user_id
    return (
        "Режим UMWELT: покажи, как один и тот же объект выглядит "
        "для разных субъектов (инженер, учёный, воробей и др.). "
        "Используй affordances из perception-записей. "
        "Не своди перспективы к одной «объективной» истине."
    )


__all__ = ["filter_facts", "project", "system_instructions", "_AGENTS"]
