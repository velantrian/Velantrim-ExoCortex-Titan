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


# ─── Principal context (server-verified caller identity) ─────────────────────

@dataclass(frozen=True)
class PrincipalContext:
    """Server-verified caller context, injected by core.mcp_transport into
    any tool registered with `needs_principal=True` — NEVER constructed
    from client-supplied JSON.

    `capability` is the exact value core.mcp_transport.resolve_authorized_
    capability() computed for THIS call (already clamped to the deployment's
    server-side ceiling) — a tool receiving this can trust it, unlike a
    hardcoded literal or a client-supplied field.

    `actor_id` is a pseudonymous, server-derived identity
    ("api:" + sha256(api_key)[:8]) — mirrors the existing precedent in
    server.py's PATCH /facts/{fact_id}/transition (`req.by` is ignored the
    same way for the same reason: a client must never be able to forge who
    performed a sensitive action just by naming themselves in a JSON body).

    This is intentionally NOT a general identity/session system — this
    codebase has no authenticated-user concept (a single shared API key
    grants one server-wide capability ceiling to every caller); it is only
    a way to stop a handler from having to pretend it verified something
    the dispatch layer already verified for real.
    """
    capability: str
    actor_id: str


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
    # True for tools whose handler must receive a real PrincipalContext
    # (see above) instead of trusting client-supplied params for identity/
    # capability — core.mcp_transport._tools_call() injects it as a
    # `principal=` kwarg when this is set.
    needs_principal: bool = False

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
        needs_principal: bool = False,
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
            needs_principal: True если fn должен получить PrincipalContext
                (см. выше) как kwarg `principal=` — для инструментов, которым
                нельзя доверять capability/identity, заявленные в клиентском
                JSON, а нужно то, что реально проверил transport-слой

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
            needs_principal=needs_principal,
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
    # GDPR Art. 17 erasure handler (lazy import → no circular import at module
    # load). Production tools call the durable coordinator directly — NOT
    # core.erasure.erase_fact(), which is a deprecated compatibility shim
    # that cannot prove deletion across the embeddings/ngram stores or
    # survive a crash mid-erasure. See core/erasure_coordinator.py.
    from core.erasure_coordinator import erase_fact_durable as _erase_fact_durable
    from core import tool_handlers as h

    # ─── reader ───────────────────────────────────────────────────────────

    # Поиск фактов
    registry.register(
        "search_facts", h.search_facts, capability="reader",
        description="Поиск фактов в базе знаний (гибридный: BM25 + dense + граф)",
    )

    # Получение факта
    registry.register(
        "get_fact", h.get_fact, capability="reader",
        description="Получить факт по ID",
    )

    # Каузальные цепочки
    registry.register(
        "causal_chain", h.causal_chain, capability="reader",
        description="Найти причинно-следственные цепочки от факта",
    )

    # Backward reasoning
    registry.register(
        "explain_fact", h.explain_fact, capability="reader",
        description="Объяснить почему факт верен (backward reasoning: caused_by/required_by)",
    )

    # Путь в графе
    registry.register(
        "explain_path", h.explain_path, capability="reader",
        description="Объяснить как связаны два факта в графе (BFS-путь с весами рёбер)",
    )

    # Статистика графа
    registry.register(
        "graph_stats", h.graph_stats, capability="reader",
        description="Статистика графа: число рёбер, типы, статусы, сироты",
    )

    # Сущности
    registry.register(
        "get_entities_for_fact", h.get_entities_for_fact, capability="reader",
        description="Все сущности, связанные с фактом",
    )

    registry.register(
        "get_facts_for_entity", h.get_facts_for_entity, capability="reader",
        description="Все факты, упоминающие сущность",
    )

    # Living Context
    registry.register(
        "get_living_context", h.get_living_context, capability="reader",
        description="Живой контекст факта: WHERE/WHO/HOW/WHAT/FEEL/ROLE/TIME/DEEP",
    )

    # ─── researcher ───────────────────────────────────────────────────────

    registry.register(
        "propose_hypothesis", h.propose_hypothesis, capability="researcher",
        description="Предложить гипотезу (сохраняется как Hypothesized, требует проверки)",
    )

    registry.register(
        "find_analogies", h.find_analogies, capability="researcher",
        description="Найти структурные аналогии между фактами (Jaccard similarity по типам рёбер)",
    )

    # ─── ingester ─────────────────────────────────────────────────────────

    registry.register(
        "store_fact", h.store_fact, capability="ingester",
        description="Сохранить новый факт (epistemic_state=Observed, пройдёт TruthGate)",
        audit=True,
    )

    registry.register(
        "link_entity", h.link_entity, capability="ingester",
        description="Связать факт с сущностью (entity-centric retrieval)",
    )

    # ─── guardian ─────────────────────────────────────────────────────────

    registry.register(
        "validate_fact", h.validate_fact, capability="guardian",
        description="Валидировать факт (переход ESM: Hypothesized/Supported → Validated)",
        audit=True,
    )

    registry.register(
        "contradict_fact", h.contradict_fact, capability="guardian",
        description="Пометить факт как противоречащий (transition → Contradicted)",
        audit=True,
    )

    registry.register(
        "supersede_fact", h.supersede_fact, capability="guardian",
        description=(
            "Атомарно заменить факт новым (core.truth_maintenance.supersede): "
            "новый кандидат проходит TruthGate, старый факт переходит в "
            "Deprecated ТОЛЬКО вместе с успешной вставкой нового — либо оба "
            "меняются, либо ничего"
        ),
        params={
            "type": "object",
            "properties": {
                "old_fact_id": {"type": "string", "description": "ID заменяемого факта"},
                "new_fact": {
                    "type": "object",
                    "description": "Полный новый факт (fact_id обязателен; claim/source/confidence/metadata — как в store_fact)",
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
    )

    # ─── admin ────────────────────────────────────────────────────────────

    registry.register(
        "forget_fact", _erase_fact_durable, capability="admin",
        description=(
            "Удалить факт (GDPR Art. 17): durable erasure saga через "
            "core.erasure_coordinator — атомарное same-DB удаление + "
            "проверенная очистка embeddings/ngram, honest outcome "
            "(COMPLETE/PARTIAL/FAILED/NOT_FOUND) + tombstone только при COMPLETE"
        ),
        params={
            "type": "object",
            "properties": {
                "fact_id": {"type": "string", "description": "ID факта для удаления"},
                "reason": {
                    "type": "string",
                    "description": "Причина удаления (для Art. 30 audit trail)",
                    "default": "data_subject_request",
                },
                "actor": {
                    "type": "string",
                    "description": "Кто инициировал удаление",
                    "default": "operator",
                },
            },
            "required": ["fact_id"],
        },
        destructive=True, audit=True,
    )

    registry.register(
        "forget_all", h.forget_all, capability="admin",
        description=(
            "Удалить все факты пользователя (GDPR Article 17): durable, "
            "resumable batch erasure saga через core.erasure_batch_coordinator "
            "— снимок затрагиваемых fact_id фиксируется до удаления, каждый "
            "факт удаляется через существующую per-fact saga (forget_fact), "
            "ImmutableCore с персональными данными сообщается как CRITICAL "
            "(не пропускается молча). capability и actor берутся из "
            "server-verified PrincipalContext (needs_principal=True), а не "
            "из клиентского JSON — force=True реально требует admin, а не "
            "жёстко прошитого допущения"
        ),
        needs_principal=True,
        params={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "ID пользователя, чьи факты удаляются",
                },
                "reason": {
                    "type": "string",
                    "description": "Причина удаления (для Art. 30 audit trail)",
                    "default": "gdpr_request",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Только предпросмотр — ничего не удаляет и не создаёт batch",
                    "default": False,
                },
                "force": {
                    "type": "boolean",
                    "description": (
                        "Разрешить удаление при пустом/'default' user_id. "
                        "Требует scope и доступен только admin-capability"
                    ),
                    "default": False,
                },
                "scope": {
                    "type": "string",
                    "description": "Явное описание масштаба удаления — обязателен при force=True",
                },
                "idempotency_key": {
                    "type": "string",
                    "description": "Повторный вызов с тем же ключом возобновляет тот же batch, не создаёт новый",
                },
            },
            "required": ["user_id"],
        },
        destructive=True, audit=True,
    )

    registry.register(
        "reset_graph", h.reset_graph, capability="admin",
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
