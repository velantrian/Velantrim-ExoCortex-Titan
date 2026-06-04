"""
🎯 core/ontological_axes.py — Ontological Axes (V8.7 Titan, из velantrim_v8_7 форка)

V8.7: расширяет poly_welt_registry.py 6 структурированными когнитивными осями.
Каждая ось определяет:
    - focus — что воспринимает
    - extractable_properties — какие свойства извлекать
    - affordance_categories — какие аффордансы возможны
    - prompt_hint — для LLM-экстрактора (JSON-mode constrained)

6 осей: SPATIAL · ENGINEERING · BIOLOGICAL · SYSTEMIC · SOCIAL · CHEMICAL

Отличие от poly_welt_registry:
    poly_welt — МЕТАДАННЫЕ перцепторов (кто это, приоритет, эмодзи).
    ontological_axes — ЧТО ИМЕННО извлекать из факта через каждую ось.

Использование:
    from core.ontological_axes import AXES, CognitiveAxis
    axis = AXES[CognitiveAxis.SPATIAL]
    print(axis.extractable_properties)
    # → ['geometry', 'dimensions', 'mass', 'density', ...]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class CognitiveAxis(str, Enum):
    SPATIAL     = "SPATIAL"      # Пространственно-структурная
    ENGINEERING = "ENGINEERING"  # Инженерно-практическая
    BIOLOGICAL  = "BIOLOGICAL"   # Биолого-метаболическая
    SYSTEMIC    = "SYSTEMIC"     # Системно-экологическая
    SOCIAL      = "SOCIAL"       # Социально-поведенческая
    CHEMICAL    = "CHEMICAL"     # Химико-реактивная


@dataclass(frozen=True)
class AxisDefinition:
    axis:                   CognitiveAxis
    focus:                  str
    description:            str
    extractable_properties: List[str]
    affordance_categories:  List[str]
    prompt_hint:            str

    def to_dict(self) -> Dict:
        return {
            "axis": self.axis.value,
            "focus": self.focus,
            "description": self.description,
            "extractable_properties": self.extractable_properties,
            "affordance_categories": self.affordance_categories,
            "prompt_hint": self.prompt_hint,
        }


# ─── Определения осей ─────────────────────────────────────────────────────────

AXES: Dict[CognitiveAxis, AxisDefinition] = {

    CognitiveAxis.SPATIAL: AxisDefinition(
        axis=CognitiveAxis.SPATIAL,
        focus="Топология, геометрия, структура, физические свойства",
        description="Как объект занимает пространство, его форма, связи компонентов, механика.",
        extractable_properties=[
            "geometry", "dimensions", "mass", "density", "topology",
            "structural_connections", "center_of_gravity", "fractality",
        ],
        affordance_categories=[
            "structural_support", "volume_occupation", "load_bearing",
            "spatial_organization", "physical_constraints",
        ],
        prompt_hint=(
            "Extract ONLY spatial and structural properties. "
            "Include geometry, dimensions, topology, structural connections. "
            "Ignore biology, social use, and chemistry."
        ),
    ),

    CognitiveAxis.ENGINEERING: AxisDefinition(
        axis=CognitiveAxis.ENGINEERING,
        focus="Аффордансы, применение, прочность, модульность, интерфейсы",
        description="Как объект можно использовать, его утилитарные свойства, интерфейсы, КПД.",
        extractable_properties=[
            "affordances", "modularity", "strength_limits", "energy_efficiency",
            "usability", "interfaces", "maintenance_requirements", "failure_modes",
        ],
        affordance_categories=[
            "tool", "material", "support_structure", "energy_source",
            "insulator", "container", "mechanism",
        ],
        prompt_hint=(
            "Focus on practical use, strength, modularity, and interfaces. "
            "What can this be used for? What are its engineering properties? "
            "Do not describe biological processes."
        ),
    ),

    CognitiveAxis.BIOLOGICAL: AxisDefinition(
        axis=CognitiveAxis.BIOLOGICAL,
        focus="Гомеостаз, метаболизм, жизненный цикл, симбиоз",
        description="Как объект живёт, обменивается энергией, воспроизводится, взаимодействует с другими живыми системами.",
        extractable_properties=[
            "metabolic_rate", "lifespan", "reproduction_method", "homeostasis",
            "symbiotic_relations", "growth_pattern", "energy_flow",
        ],
        affordance_categories=[
            "nutrient_source", "habitat", "symbiont", "energy_producer",
            "decomposer", "oxygen_producer",
        ],
        prompt_hint=(
            "Extract ONLY biological and metabolic properties. "
            "How does it live? How does it reproduce? What does it exchange with environment? "
            "Ignore engineering properties and social use."
        ),
    ),

    CognitiveAxis.SYSTEMIC: AxisDefinition(
        axis=CognitiveAxis.SYSTEMIC,
        focus="Экосистемные связи, циклы, потоки, обратные связи, эмерджентность",
        description="Как объект является частью большей системы, его роль в циклах, системные эффекты.",
        extractable_properties=[
            "ecosystem_role", "feedback_loops", "material_cycles",
            "energy_cycles", "emergent_properties", "system_hierarchy",
        ],
        affordance_categories=[
            "ecosystem_service", "keystone_role", "cycle_regulator",
            "biodiversity_support", "climate_regulator",
        ],
        prompt_hint=(
            "Extract ONLY systemic and ecological properties. "
            "What role does it play in the larger system? What cycles is it part of? "
            "What emergent properties arise from its interactions? "
            "Ignore individual biology and practical engineering."
        ),
    ),

    CognitiveAxis.SOCIAL: AxisDefinition(
        axis=CognitiveAxis.SOCIAL,
        focus="Социальное поведение, иерархии, коммуникация, культурные паттерны",
        description="Как объект/субъект взаимодействует в социальной среде, культурный контекст.",
        extractable_properties=[
            "social_hierarchy", "communication_patterns", "group_dynamics",
            "cultural_significance", "power_structure", "rituals",
        ],
        affordance_categories=[
            "communication_tool", "cultural_symbol", "social_organizer",
            "power_mediator", "community_builder",
        ],
        prompt_hint=(
            "Extract ONLY social and behavioral properties. "
            "How does it interact socially? What cultural significance does it have? "
            "Ignore physical structure and biological processes."
        ),
    ),

    CognitiveAxis.CHEMICAL: AxisDefinition(
        axis=CognitiveAxis.CHEMICAL,
        focus="Химический состав, реакции, катализ, фазовые переходы",
        description="Молекулярная природа, реакционная способность, химические превращения.",
        extractable_properties=[
            "chemical_formula", "reactivity", "catalysis", "pH",
            "oxidation_state", "solubility", "phase_transitions",
        ],
        affordance_categories=[
            "catalyst", "reactant", "solvent", "stabilizer",
            "energy_storage", "signal_molecule",
        ],
        prompt_hint=(
            "Extract ONLY chemical and molecular properties. "
            "What is its chemical nature? How does it react? "
            "What phase transitions does it undergo? "
            "Ignore biological metabolism and social use."
        ),
    ),

}


# ─── Утилиты ──────────────────────────────────────────────────────────────────

def get_axis(axis_name: str) -> AxisDefinition:
    """Получить определение оси по имени (или значению CognitiveAxis)."""
    try:
        key = CognitiveAxis(axis_name.upper())
        return AXES[key]
    except (KeyError, ValueError):
        available = ", ".join(a.value for a in CognitiveAxis)
        raise ValueError(f"Неизвестная ось: {axis_name}. Доступны: {available}")


def list_axes() -> List[Dict]:
    """Список всех осей для API/консоли."""
    return [
        {"id": a.axis.value, "focus": a.focus, "properties_count": len(a.extractable_properties)}
        for a in AXES.values()
    ]


def get_extractable_properties(axis_name: str) -> List[str]:
    """Только извлекаемые свойства для оси."""
    return list(get_axis(axis_name).extractable_properties)


def get_affordances(axis_name: str) -> List[str]:
    """Только аффорданс-категории для оси."""
    return list(get_axis(axis_name).affordance_categories)


__all__ = [
    "CognitiveAxis",
    "AxisDefinition",
    "AXES",
    "get_axis",
    "list_axes",
    "get_extractable_properties",
    "get_affordances",
]
