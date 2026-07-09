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

Использование:
    registry = ToolRegistry()

    @registry.register("search_facts", capability="reader")
    def search_facts(query: str) -> list[dict]: ...

    tools = registry.for_capability("ingester")
    # → {"search_facts": search_facts, "propose_hypothesis": ..., "store_fact": ...}

    # admin видит всё, reader — только read-only
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("velantrim.tool_registry")

# ─── Capability levels ───────────────────────────────────────────────────────

# Иерархия: каждый уровень включает все нижележащие
CAPABILITY_CHAIN: tuple[str, ...] = (
    "reader",       # только чтение
    "researcher",   # чтение + гипотезы
    "ingester",     # чтение + запись в L1/L2
    "guardian",     # чтение + валидация + перевод состояний
    "admin",        # всё, включая деструктивные операции
)

# Какие уровни имеют доступ к инструменту с данной capability
# Инструмент уровня "ingester" → доступен ingester, guardian, admin (но НЕ reader!)
def _accessible_levels(capability: str) -> Set[str]:
    """Уровни, для которых доступен инструмент с данной capability (вверх по цепочке)."""
    try:
        idx = CAPABILITY_CHAIN.index(capability)
    except ValueError:
        return set()
    return set(CAPABILITY_CHAIN[idx:])  # от текущего до admin


# ─── Tool descriptor ─────────────────────────────────────────────────────────

@dataclass
class ToolDef:
    """Описание зарегистрированного инструмента."""
    name: str
    description: str
    capability: str          # минимальный уровень
    fn: Callable
    params: Dict[str, Any] = field(default_factory=dict)  # JSON Schema параметров
    destructive: bool = False  # требует admin
    audit: bool = True        # логировать вызов в provenance

    def to_manifest(self) -> Dict[str, Any]:
        """MCP-совместимый манифест инструмента."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.params,
            "capability": self.capability,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ToolRegistry
# ═══════════════════════════════════════════════════════════════════════════════

class ToolRegistry:
    """
    Реестр инструментов с фильтрацией по capability level.

    Паттерн из Wiki-MCP-Server v3:
    - Инструменты регистрируются с указанием минимального уровня доступа
    - При запросе набора для роли — фильтруются по capability
    - Инструмент, недоступный роли, ПРОСТО НЕ ПОЯВЛЯЕТСЯ в списке
    - Агент/модель физически не может его вызвать
    """

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
    ) -> Callable:
        """
        Зарегистрировать инструмент. Можно использовать как декоратор.

        Args:
            name: уникальное имя инструмента
            fn: функция-обработчик
            capability: минимальный уровень доступа (reader/researcher/ingester/guardian/admin)
            description: человекочитаемое описание
            params: JSON Schema параметров (для MCP-манифеста)
            destructive: True если инструмент необратимо меняет данные
            audit: True если вызов нужно логировать в provenance

        Returns:
            fn (для использования как декоратор)
        """
        if capability not in CAPABILITY_CHAIN:
            raise ValueError(
                f"Неизвестный capability: {capability!r}. "
                f"Допустимые: {CAPABILITY_CHAIN}"
            )

        tool = ToolDef(
            name=name,
            description=description or fn.__doc__ or "",
            capability=capability,
            fn=fn,
            params=params or {},
            destructive=destructive,
            audit=audit,
        )
        self._tools[name] = tool

        # Индексировать по всем доступным уровням (вверх по цепочке)
        for level in _accessible_levels(capability):
            self._by_capability.setdefault(level, []).append(name)

        logger.debug("Зарегистрирован инструмент %s (cap=%s, destr=%s)", name, capability, destructive)
        return fn

    def for_capability(self, capability: str) -> Dict[str, ToolDef]:
        """
        Все инструменты, доступные для данной роли.

        Возвращает dict[name → ToolDef]. Инструменты, недоступные роли,
        просто отсутствуют — агент их не видит.

        Args:
            capability: reader / researcher / ingester / guardian / admin
        """
        if capability not in CAPABILITY_CHAIN:
            raise ValueError(f"Неизвестный capability: {capability!r}")

        names = self._by_capability.get(capability, [])
        return {name: self._tools[name] for name in names if name in self._tools}

    def get_tool(self, name: str) -> Optional[ToolDef]:
        """Получить инструмент по имени."""
        return self._tools.get(name)

    def list_tools(self, capability: str | None = None) -> List[Dict[str, Any]]:
        """
        Список инструментов (манифест) — для API/UI.

        Если capability=None — все инструменты (admin view).
        """
        if capability:
            tools = self.for_capability(capability)
        else:
            tools = self._tools
        return [t.to_manifest() for t in tools.values()]

    def has_tool(self, name: str, capability: str = "reader") -> bool:
        """Есть ли у роли доступ к этому инструменту?

        Роль имеет доступ если capability роли >= capability инструмента
        (admin > guardian > ingester > researcher > reader).
        """
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
        """Статистика реестра."""
        by_cap = {}
        for cap in CAPABILITY_CHAIN:
            by_cap[cap] = len(self.for_capability(cap))
        return {
            "total_tools": len(self._tools),
            "by_capability": by_cap,
            "destructive_count": sum(1 for t in self._tools.values() if t.destructive),
        }


# ─── Стандартные наборы инструментов (из Wiki-MCP-Server + Velantrim) ─────────

def register_velantrim_tools(registry: ToolRegistry) -> None:
    """
    Зарегистрировать стандартный набор инструментов Velantrim.

    Разбивка по уровням как в статье: reader видит только read-инструменты,
    admin видит всё. Инструменты, недоступные роли, физически отсутствуют
    в её наборе — модель не может их вызвать даже случайно.
    """
    # GDPR Art. 17 erasure handler (lazy import → no circular import at module load).
    from core.erasure import erase_fact as _erase_fact

    # ─── reader ───────────────────────────────────────────────────────────

    # Поиск фактов
    registry.register(
        "search_facts", lambda: None, capability="reader",
        description="Поиск фактов в базе знаний (гибридный: BM25 + dense + граф)",
    )

    # Получение факта
    registry.register(
        "get_fact", lambda: None, capability="reader",
        description="Получить факт по ID",
    )

    # Каузальные цепочки
    registry.register(
        "causal_chain", lambda: None, capability="reader",
        description="Найти причинно-следственные цепочки от факта",
    )

    # Backward reasoning
    registry.register(
        "explain_fact", lambda: None, capability="reader",
        description="Объяснить почему факт верен (backward reasoning: caused_by/required_by)",
    )

    # Путь в графе
    registry.register(
        "explain_path", lambda: None, capability="reader",
        description="Объяснить как связаны два факта в графе (BFS-путь с весами рёбер)",
    )

    # Статистика графа
    registry.register(
        "graph_stats", lambda: None, capability="reader",
        description="Статистика графа: число рёбер, типы, статусы, сироты",
    )

    # Сущности
    registry.register(
        "get_entities_for_fact", lambda: None, capability="reader",
        description="Все сущности, связанные с фактом",
    )

    registry.register(
        "get_facts_for_entity", lambda: None, capability="reader",
        description="Все факты, упоминающие сущность",
    )

    # Living Context
    registry.register(
        "get_living_context", lambda: None, capability="reader",
        description="Живой контекст факта: WHERE/WHO/HOW/WHAT/FEEL/ROLE/TIME/DEEP",
    )

    # ─── researcher ───────────────────────────────────────────────────────

    registry.register(
        "propose_hypothesis", lambda: None, capability="researcher",
        description="Предложить гипотезу (сохраняется как Hypothesized, требует проверки)",
    )

    registry.register(
        "find_analogies", lambda: None, capability="researcher",
        description="Найти структурные аналогии между фактами (Jaccard similarity по типам рёбер)",
    )

    # ─── ingester ─────────────────────────────────────────────────────────

    registry.register(
        "store_fact", lambda: None, capability="ingester",
        description="Сохранить новый факт (epistemic_state=Observed, пройдёт TruthGate)",
        audit=True,
    )

    registry.register(
        "link_entity", lambda: None, capability="ingester",
        description="Связать факт с сущностью (entity-centric retrieval)",
    )

    # ─── guardian ─────────────────────────────────────────────────────────

    registry.register(
        "validate_fact", lambda: None, capability="guardian",
        description="Валидировать факт (переход ESM: Hypothesized/Supported → Validated)",
        audit=True,
    )

    registry.register(
        "contradict_fact", lambda: None, capability="guardian",
        description="Пометить факт как противоречащий (transition → Contradicted)",
        audit=True,
    )

    registry.register(
        "supersede_fact", lambda: None, capability="guardian",
        description="Заменить факт новым (старый → Deprecated, указатель на новый)",
        audit=True,
    )

    # ─── admin ────────────────────────────────────────────────────────────

    registry.register(
        "forget_fact", lambda fact_id, **kw: _erase_fact(fact_id, **kw), capability="admin",
        description="Удалить факт (GDPR Art. 17: физическое стирание L0+L1 + tombstone)",
        destructive=True, audit=True,
    )

    registry.register(
        "forget_all", lambda: None, capability="admin",
        description="Удалить все факты пользователя (GDPR Article 17)",
        destructive=True, audit=True,
    )

    registry.register(
        "reset_graph", lambda: None, capability="admin",
        description="Сбросить граф (полная очистка relations)",
        destructive=True, audit=True,
    )


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

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
