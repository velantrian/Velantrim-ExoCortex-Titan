"""
PolyWeltRegistry — реестр 6 Umwelt-перцепторов (V10 / контур P).

Метаданные агентов для router, API и seed; не полная multi-agent политика.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PolyWeltAgent:
    agent_id: str
    label_ru: str
    emoji: str
    category: str
    priority: int = 5
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "label_ru": self.label_ru,
            "emoji": self.emoji,
            "category": self.category,
            "priority": self.priority,
            "description": self.description,
        }


# Шесть MVP-перцепторов (engineer, scientist, sparrow, observer, cat, poet)
POLYWELT_AGENTS: tuple[PolyWeltAgent, ...] = (
    PolyWeltAgent(
        "agent:engineer",
        "Инженер",
        "👷",
        "human_role",
        0,
        "Материал, нагрузка, нормы, безопасность",
    ),
    PolyWeltAgent(
        "agent:scientist",
        "Учёный",
        "🔬",
        "human_role",
        1,
        "Экосистема, измерение, гипотезы",
    ),
    PolyWeltAgent(
        "agent:passer_domesticus",
        "Воробей",
        "🐦",
        "small_bird",
        2,
        "Укрытие, гнездо, добыча",
    ),
    PolyWeltAgent(
        "agent:observer",
        "Наблюдатель",
        "👁️",
        "human_role",
        3,
        "Мульти-агентный узел без сведения к одной роли",
    ),
    PolyWeltAgent(
        "agent:felis_catus",
        "Кошка",
        "🐱",
        "domestic_mammal",
        4,
        "Территория, обзор, охота, укрытие",
    ),
    PolyWeltAgent(
        "agent:poet",
        "Поэт",
        "✒️",
        "human_role",
        5,
        "Образ, метафора, переживание места",
    ),
)

_BY_ID: Dict[str, PolyWeltAgent] = {a.agent_id: a for a in POLYWELT_AGENTS}


def list_agents() -> List[Dict[str, Any]]:
    return [a.to_dict() for a in POLYWELT_AGENTS]


def get_agent(agent_id: str) -> Optional[PolyWeltAgent]:
    return _BY_ID.get(agent_id)


def agent_display(agent_id: str, fallback_name: str = "") -> tuple[str, str]:
    """(emoji, label) для линзы."""
    a = _BY_ID.get(agent_id)
    if a:
        return a.emoji, a.label_ru
    return "🌍", fallback_name or agent_id


def priority_order() -> Dict[str, int]:
    return {a.agent_id: a.priority for a in POLYWELT_AGENTS}


def all_agent_ids() -> frozenset[str]:
    return frozenset(_BY_ID.keys())


__all__ = [
    "POLYWELT_AGENTS",
    "PolyWeltAgent",
    "agent_display",
    "agent_to_axis",
    "all_agent_ids",
    "get_agent",
    "list_agents",
    "priority_order",
]


# ─── V8.7: Мост перцептор → когнитивная ось ──────────────────────────────────

from core.ontological_axes import CognitiveAxis

_AGENT_TO_AXIS: Dict[str, CognitiveAxis] = {
    "agent:engineer":            CognitiveAxis.ENGINEERING,
    "agent:scientist":           CognitiveAxis.SYSTEMIC,
    "agent:passer_domesticus":  CognitiveAxis.BIOLOGICAL,
    "agent:observer":            CognitiveAxis.SPATIAL,
    "agent:felis_catus":        CognitiveAxis.SOCIAL,
    "agent:poet":                CognitiveAxis.CHEMICAL,
}

def agent_to_axis(agent_id: str) -> Optional[CognitiveAxis]:
    """Какую когнитивную ось представляет перцептор."""
    return _AGENT_TO_AXIS.get(agent_id)
