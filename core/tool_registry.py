"""
🛡️ core/tool_registry.py — Capability-Based Tool Access (V8.7, из Wiki-MCP-Server)

Идея из статьи (Хабр, апрель 2026): роли — это не просто «права», а разные
наборы инструментов. Если инструмент не зарегистрирован для роли — агент
ФИЗИЧЕСКИ не может его вызвать. Модель не видит опасный инструмент в списке.

Сильнее чем runtime-проверки (где модель всё ещё может попытаться вызвать
запрещённый инструмент и получить отказ).

Уровни доступа (capability levels):
    reader      — только чтение (search, get_fact, causal_chain, explain)
    researcher  — чтение + предложение гипотез
    ingester    — чтение + запись в L1/L2 (Observed/Hypothesized)
    guardian    — чтение + валидация (перевод в Validated, поиск противоречий)
    admin       — всё, включая деструктивные операции (удаление, сброс)
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("velantrim.tool_registry")

CAPABILITY_CHAIN: tuple[str, ...] = (
    "reader",
    "researcher",
    "ingester",
    "guardian",
    "admin",
)


def _accessible_levels(capability: str) -> Set[str]:
    try:
        idx = CAPABILITY_CHAIN.index(capability)
    except ValueError:
        return set()
    return set(CAPABILITY_CHAIN[idx:])


@dataclass(frozen=True)
class PrincipalContext:
    """Server-verified caller context injected by the MCP transport."""

    capability: str
    credential_fingerprint: str


@dataclass
class ToolDef:
    """Описание зарегистрированного инструмента."""

    name: str
    description: str
    capability: str
    fn: Callable
    params: Dict[str, Any] = field(default_factory=dict)
    destructive: bool = False
    audit: bool = True
    needs_principal: bool = False
    # Side-effect metadata is transport safety metadata only. It does not
    # grant write authority and does not imply exactly-once execution.
    side_effecting: bool = False
    # Optional operation-owned idempotency argument. When a transport key is
    # supplied, MCP may pass that same key into the operation instead of
    # inventing a second idempotency namespace.
    idempotency_arg: str | None = None

    def to_manifest(self) -> Dict[str, Any]:
        manifest = {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.params,
            "capability": self.capability,
            "sideEffecting": self.side_effecting,
        }
        if self.idempotency_arg:
            manifest["idempotencyArg"] = self.idempotency_arg
        return manifest


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDef] = OrderedDict()
        self._by_capability: Dict[str, List[str]] = {}

    def register(
        self,
        name: str,
        fn: Callable,
        *,
        capability: str = "reader",
        description: str = "",
        params: Dict[str, Any] | None = None,
        destructive: bool = False,
        audit: bool = True,
        needs_principal: bool = False,
        side_effecting: bool = False,
        idempotency_arg: str | None = None,
    ) -> Callable:
        if capability not in CAPABILITY_CHAIN:
            raise ValueError(
                f"Неизвестный capability: {capability!r}. Допустимые: {CAPABILITY_CHAIN}"
            )
        if idempotency_arg is not None:
            if not isinstance(idempotency_arg, str) or not idempotency_arg.strip():
                raise ValueError("idempotency_arg must be a non-empty string")
            if not side_effecting:
                raise ValueError("idempotency_arg requires side_effecting=True")
            idempotency_arg = idempotency_arg.strip()

        tool = ToolDef(
            name=name,
            description=description or fn.__doc__ or "",
            capability=capability,
            fn=fn,
            params=params or {},
            destructive=destructive,
            audit=audit,
            needs_principal=needs_principal,
            side_effecting=side_effecting,
            idempotency_arg=idempotency_arg,
        )
        self._tools[name] = tool

        for level in _accessible_levels(capability):
            self._by_capability.setdefault(level, []).append(name)

        logger.debug(
            "Зарегистрирован инструмент %s (cap=%s, destr=%s, side_effecting=%s)",
            name,
            capability,
            destructive,
            side_effecting,
        )
        return fn

    def for_capability(self, capability: str) -> Dict[str, ToolDef]:
        if capability not in CAPABILITY_CHAIN:
            raise ValueError(f"Неизвестный capability: {capability!r}")
        names = self._by_capability.get(capability, [])
        return {name: self._tools[name] for name in names if name in self._tools}

    def get_tool(self, name: str) -> Optional[ToolDef]:
        return self._tools.get(name)

    def list_tools(self, capability: str | None = None) -> List[Dict[str, Any]]:
        tools = self.for_capability(capability) if capability else self._tools
        return [t.to_manifest() for t in tools.values()]

    def has_tool(self, name: str, capability: str = "reader") -> bool:
        tool = self._tools.get(name)
        if tool is None:
            return False
        try:
            role_idx = CAPABILITY_CHAIN.index(capability)
            tool_idx = CAPABILITY_CHAIN.index(tool.capability)
            return role_idx >= tool_idx
        except ValueError:
            return False

    def stats(self) -> Dict[str, Any]:
        by_cap = {cap: len(self.for_capability(cap)) for cap in CAPABILITY_CHAIN}
        return {
            "total_tools": len(self._tools),
            "by_capability": by_cap,
            "destructive_count": sum(1 for t in self._tools.values() if t.destructive),
            "side_effecting_count": sum(1 for t in self._tools.values() if t.side_effecting),
        }


def register_velantrim_tools(registry: ToolRegistry) -> None:
    from core.erasure_coordinator import erase_fact_durable as _erase_fact_durable
    from core import tool_handlers as h

    registry.register(
        "search_facts", h.search_facts, capability="reader",
        description="Поиск фактов в базе знаний (гибридный: BM25 + dense + граф)",
    )
    registry.register(
        "get_fact", h.get_fact, capability="reader",
        description="Получить факт по ID",
    )
    registry.register(
        "causal_chain", h.causal_chain, capability="reader",
        description="Найти причинно-следственные цепочки от факта",
    )
    registry.register(
        "explain_fact", h.explain_fact, capability="reader",
        description="Объяснить почему факт верен (backward reasoning: caused_by/required_by)",
    )
    registry.register(
        "explain_path", h.explain_path, capability="reader",
        description="Объяснить как связаны два факта в графе (BFS-путь с весами рёбер)",
    )
    registry.register(
        "graph_stats", h.graph_stats, capability="reader",
        description="Статистика графа: число рёбер, типы, статусы, сироты",
    )
    registry.register(
        "get_entities_for_fact", h.get_entities_for_fact, capability="reader",
        description="Все сущности, связанные с фактом",
    )
    registry.register(
        "get_facts_for_entity", h.get_facts_for_entity, capability="reader",
        description="Все факты, упоминающие сущность",
    )
    registry.register(
        "get_living_context", h.get_living_context, capability="reader",
        description="Живой контекст факта: WHERE/WHO/HOW/WHAT/FEEL/ROLE/TIME/DEEP",
    )

    registry.register(
        "propose_hypothesis", h.propose_hypothesis, capability="researcher",
        description="Предложить гипотезу (сохраняется как Hypothesized, требует проверки)",
        side_effecting=True,
    )
    registry.register(
        "find_analogies", h.find_analogies, capability="researcher",
        description="Найти структурные аналогии между фактами (Jaccard similarity по типам рёбер)",
    )

    registry.register(
        "store_fact", h.store_fact, capability="ingester",
        description="Сохранить новый факт (epistemic_state=Observed, пройдёт TruthGate)",
        audit=True,
        side_effecting=True,
    )
    registry.register(
        "link_entity", h.link_entity, capability="ingester",
        description="Связать факт с сущностью (entity-centric retrieval)",
        side_effecting=True,
    )

    registry.register(
        "validate_fact", h.validate_fact, capability="guardian",
        description="Валидировать факт (переход ESM: Hypothesized/Supported → Validated)",
        audit=True,
        side_effecting=True,
    )
    registry.register(
        "contradict_fact", h.contradict_fact, capability="guardian",
        description="Пометить факт как противоречащий (transition → Contradicted)",
        audit=True,
        side_effecting=True,
    )
    registry.register(
        "supersede_fact", h.supersede_fact, capability="guardian",
        description=(
            "Атомарно заменить факт новым (core.truth_maintenance.supersede): "
            "новый кандидат проходит TruthGate, старый факт переходит в "
            "Deprecated ТОЛЬКО вместе с успешной вставкой нового"
        ),
        params={
            "type": "object",
            "properties": {
                "old_fact_id": {"type": "string", "description": "ID заменяемого факта"},
                "new_fact": {
                    "type": "object",
                    "description": "Полный новый факт",
                    "properties": {
                        "fact_id": {"type": "string"},
                        "claim": {"type": "string"},
                        "source": {"type": "string"},
                        "confidence": {"type": "number"},
                        "metadata": {"type": "object"},
                    },
                    "required": ["fact_id"],
                },
            },
            "required": ["old_fact_id", "new_fact"],
        },
        audit=True,
        side_effecting=True,
    )

    registry.register(
        "forget_fact", _erase_fact_durable, capability="admin",
        description=(
            "Удалить факт (GDPR Art. 17): durable erasure saga через "
            "core.erasure_coordinator"
        ),
        params={
            "type": "object",
            "properties": {
                "fact_id": {"type": "string", "description": "ID факта для удаления"},
                "reason": {"type": "string", "default": "data_subject_request"},
                "actor": {"type": "string", "default": "operator"},
            },
            "required": ["fact_id"],
        },
        destructive=True,
        audit=True,
        side_effecting=True,
    )
    registry.register(
        "forget_all", h.forget_all, capability="admin",
        description=(
            "Удалить все факты пользователя через durable, resumable batch erasure saga"
        ),
        needs_principal=True,
        params={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "reason": {"type": "string", "default": "gdpr_request"},
                "dry_run": {"type": "boolean", "default": False},
                "force": {"type": "boolean", "default": False},
                "scope": {"type": "string"},
                "idempotency_key": {
                    "type": "string",
                    "description": "Повторный вызов с тем же ключом возобновляет тот же batch",
                },
            },
            "required": ["user_id"],
        },
        destructive=True,
        audit=True,
        side_effecting=True,
        idempotency_arg="idempotency_key",
    )
    registry.register(
        "reset_graph", h.reset_graph, capability="admin",
        description="Сбросить граф (полная очистка relations)",
        destructive=True,
        audit=True,
        side_effecting=True,
    )


_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        register_velantrim_tools(_registry)
    return _registry


def reset_tool_registry() -> None:
    global _registry
    _registry = None


__all__ = [
    "ToolRegistry",
    "ToolDef",
    "CAPABILITY_CHAIN",
    "register_velantrim_tools",
    "get_tool_registry",
    "reset_tool_registry",
]
