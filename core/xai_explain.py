"""
XAI-from-TRACE (Crystal RFC0058 / I34).

Объяснение ответа строится ТОЛЬКО из реального TRACE / reasoning_traces.
Генерация «почему» через LLM без TRACE — запрещена.

Важно: наличие fact_id в TRACE фиксирует trace membership / доступность на
наблюдаемом пути, но само по себе не доказывает semantic use, answer support
или decision authority.
"""

from __future__ import annotations

from typing import Any

from core.feature_config import get_config
from core.trace import build_trace, format_trace, trace_summary


def is_xai_enabled() -> bool:
    return bool(getattr(get_config().app, "enable_xai", False))


def explain_from_trace_elements(
    trace: list[dict[str, Any]],
    *,
    query: str = "",
    answer_preview: str = "",
    level: str = "brief",
) -> dict[str, Any]:
    """Собрать bounded-объяснение из уже построенной trace-цепочки (без LLM)."""
    summary = trace_summary(trace)
    if not trace:
        return {
            "ok": False,
            "error": "empty_trace",
            "message": "Нет TRACE — объяснение невозможно (I34).",
            "level": level,
            "query": query,
            "llm_used": False,
            "policy": "xai_from_trace_only",
        }

    facts_brief = []
    for el in trace[:12]:
        facts_brief.append(
            {
                "fact_id": el.get("fact_id"),
                "epistemic_state": el.get("epistemic_state"),
                "source": el.get("source"),
                "retrieval_score": el.get("retrieval_score"),
                "source_confidence": el.get("source_confidence"),
                "claim": el.get("claim"),
            }
        )

    states = summary.get("states") or {}
    validated_n = int(states.get("Validated", 0)) + int(states.get("ImmutableCore", 0))
    lines = [
        f"TRACE содержит {summary['count']} факт(ов), связанных с путём ответа; это не доказывает их semantic use или поддержку ответа.",
        f"Из них Validated/ImmutableCore: {validated_n}.",
    ]
    if summary.get("sources"):
        lines.append("Источники: " + ", ".join(summary["sources"][:8]) + ".")
    if query:
        lines.append(f"Запрос: {query[:200]}")
    if answer_preview and level in ("detailed", "full_trace"):
        lines.append(f"Фрагмент ответа: {answer_preview[:200]}")

    out: dict[str, Any] = {
        "ok": True,
        "level": level,
        "query": query,
        "human_summary": " ".join(lines),
        "trace_summary": summary,
        "facts": facts_brief,
        "policy": "xai_from_trace_only",
        "llm_used": False,
    }
    if level == "full_trace":
        out["trace"] = trace
        out["trace_text"] = format_trace(trace)
    elif level == "detailed":
        out["trace"] = trace
    return out


def explain_from_facts(
    facts: list[dict[str, Any]],
    *,
    query: str = "",
    answer_preview: str = "",
    level: str = "brief",
) -> dict[str, Any]:
    """Построить TRACE из retrieved-фактов и объяснить (без LLM)."""
    # enrich claim into trace elements for human readability
    retrieved = []
    for f in facts:
        item = dict(f)
        if "id" not in item and "fact_id" in item:
            item["id"] = item["fact_id"]
        retrieved.append(item)
    trace = build_trace(retrieved)
    # attach claims for XAI display
    by_id = {
        (f.get("fact_id") or f.get("id")): f
        for f in facts
        if f.get("fact_id") or f.get("id")
    }
    for el in trace:
        src = by_id.get(el.get("fact_id")) or {}
        el["claim"] = (src.get("claim") or src.get("content") or "")[:240]
    return explain_from_trace_elements(
        trace,
        query=query,
        answer_preview=answer_preview,
        level=level,
    )


def explain_reasoning_trace(
    stored: dict[str, Any],
    *,
    level: str = "brief",
    resolve_facts: bool = True,
) -> dict[str, Any]:
    """Объяснить сохранённый reasoning_traces row (memory_ops)."""
    fact_ids = list(stored.get("source_fact_ids") or [])
    facts: list[dict[str, Any]] = []
    if resolve_facts and fact_ids:
        from core.memory import get_fact

        for fid in fact_ids:
            f = get_fact(fid)
            if f:
                facts.append(f)
            else:
                facts.append(
                    {
                        "fact_id": fid,
                        "claim": "",
                        "source": "trace",
                        "epistemic_state": "unknown",
                        "confidence": 0.0,
                    }
                )
    elif fact_ids:
        facts = [
            {
                "fact_id": fid,
                "claim": "",
                "source": "trace",
                "epistemic_state": "Observed",
                "confidence": 0.5,
            }
            for fid in fact_ids
        ]

    result = explain_from_facts(
        facts,
        query=str(stored.get("query") or ""),
        answer_preview=str(stored.get("answer") or ""),
        level=level,
    )
    result["trace_id"] = stored.get("trace_id")
    result["mode"] = stored.get("mode")
    result["rejected_fact_ids"] = list(stored.get("rejected_fact_ids") or [])
    if stored.get("notes"):
        result["notes"] = stored["notes"]
    return result


__all__ = [
    "explain_from_facts",
    "explain_from_trace_elements",
    "explain_reasoning_trace",
    "is_xai_enabled",
]
