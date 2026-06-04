"""
ModeRouter — dispatch по линзам PERSONAL / VELANTRIM / UMWELT.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.router import personal_lens, system_lens, umwelt_lens

LENS_MODES = frozenset({"PERSONAL", "VELANTRIM", "UMWELT"})

_LENS_CATALOG: list[dict[str, Any]] = [
    {
        "id": "PERSONAL",
        "title": "Персональный",
        "description": "Цели пользователя, поддерживающий тон",
        "module": "personal_lens",
    },
    {
        "id": "VELANTRIM",
        "title": "Системный Velantrim",
        "description": "Graph=Truth, только проверенные факты",
        "module": "system_lens",
    },
    {
        "id": "UMWELT",
        "title": "Полиперспектива",
        "description": "2–3 Umwelt-агента (инженер, учёный, наблюдатель)",
        "module": "umwelt_lens",
    },
]


@dataclass
class RoutedContext:
    lens: str
    facts: list[dict[str, Any]]
    system_instructions: str
    lens_meta: dict[str, Any] = field(default_factory=dict)
    cognitive_mode_hint: str | None = None


def is_mode_router_enabled() -> bool:
    from core.feature_config import get_config

    return get_config().app.enable_mode_router


def normalize_lens(lens: str | None) -> str:
    raw = (lens or "VELANTRIM").strip().upper()
    if raw not in LENS_MODES:
        raise ValueError(f"response_lens должен быть одним из: {sorted(LENS_MODES)}")
    return raw


def list_lens_modes() -> list[dict[str, Any]]:
    return [dict(m) for m in _LENS_CATALOG]


def apply_lens(
    query: str,
    facts: list[dict[str, Any]],
    lens: str | None = None,
    *,
    user_id: str = "default",
    cognitive_mode: str | None = None,
) -> RoutedContext:
    """
    Применить линзу к фактам и собрать инструкции для LLM/ответа.
    """
    mode = normalize_lens(lens)
    if mode == "PERSONAL":
        filtered, meta = personal_lens.filter_facts(facts, query, user_id)
        instr = personal_lens.system_instructions(user_id)
        hint = cognitive_mode or "BALANCED"
    elif mode == "UMWELT":
        filtered, meta = umwelt_lens.filter_facts(facts, query, user_id)
        instr = umwelt_lens.system_instructions(user_id)
        hint = cognitive_mode or "EXPLORATION"
    else:
        filtered, meta = system_lens.filter_facts(facts, query, user_id)
        instr = system_lens.system_instructions(user_id)
        hint = cognitive_mode or "PRECISION"

    return RoutedContext(
        lens=mode,
        facts=filtered,
        system_instructions=instr,
        lens_meta=meta,
        cognitive_mode_hint=hint,
    )


def format_lens_answer(
    base_answer: str | None,
    routed: RoutedContext,
) -> str | None:
    """Оформить текстовый ответ с учётом линзы (без LLM)."""
    if not base_answer:
        return base_answer
    if routed.lens != "UMWELT":
        return base_answer
    perspectives = routed.lens_meta.get("perspectives") or []
    if not perspectives:
        return base_answer
    lines = [base_answer, "", "——— Umwelt ———"]
    for p in perspectives:
        lines.append(f"{p.get('label', '?')}: {p.get('affordance', '')}")
    return "\n".join(lines)


__all__ = [
    "LENS_MODES",
    "RoutedContext",
    "apply_lens",
    "format_lens_answer",
    "is_mode_router_enabled",
    "list_lens_modes",
    "normalize_lens",
]
