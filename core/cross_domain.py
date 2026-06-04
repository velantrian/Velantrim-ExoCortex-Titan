"""
CrossDomainLayer + DomainOrchestrator (V10 / roadmap V3 MVP).

Связывает science ↔ engineering (и др.) при retrieval/query без отдельной БД.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from core.domain_tags import (
    fact_domain,
    infer_domain,
    normalize_domain,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DomainBridge:
    """Мост между двумя доменами знаний."""

    from_domain: str
    to_domain: str
    label_ru: str
    bridge_terms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_domain": self.from_domain,
            "to_domain": self.to_domain,
            "label_ru": self.label_ru,
            "bridge_terms": list(self.bridge_terms),
        }


# MVP: ключевые пары из docx v4 (science ↔ engineering)
DOMAIN_BRIDGES: tuple[DomainBridge, ...] = (
    DomainBridge(
        "science",
        "engineering",
        "Наука → инженерия",
        ("материал", "нагрузка", "прочность", "измерение", "эксперимент"),
    ),
    DomainBridge(
        "engineering",
        "science",
        "Инженерия → наука",
        ("гипотеза", "экосистем", "модель", "валидация", "биолог"),
    ),
    DomainBridge(
        "science",
        "perception",
        "Наука → восприятие",
        ("наблюдение", "организм", "среда", "поведение"),
    ),
    DomainBridge(
        "perception",
        "science",
        "Восприятие → наука",
        ("измерение", "факт", "эксперимент", "данные"),
    ),
    DomainBridge(
        "engineering",
        "system",
        "Инженерия → система Velantrim",
        ("api", "память", "граф", "pipeline", "хранилище"),
    ),
    DomainBridge(
        "system",
        "engineering",
        "Система → инженерия",
        ("архитектур", "модуль", "интеграц", "backend"),
    ),
)

_BY_FROM: dict[str, list[DomainBridge]] = {}
for _b in DOMAIN_BRIDGES:
    _BY_FROM.setdefault(_b.from_domain, []).append(_b)


def is_cross_domain_enabled() -> bool:
    from core.feature_config import get_config

    return bool(get_config().app.enable_cross_domain)


def is_cross_domain_causal_enabled() -> bool:
    from core.feature_config import get_config

    return bool(
        get_config().app.enable_cross_domain
        and get_config().app.enable_cross_domain_causal
    )


def is_cross_domain_llm_routing_enabled() -> bool:
    from core.feature_config import get_config

    return bool(
        get_config().app.enable_cross_domain
        and get_config().app.enable_cross_domain_llm_routing
    )


def _score_bridge(query: str, bridge: DomainBridge) -> float:
    q = (query or "").lower()
    return sum(1.0 for t in bridge.bridge_terms if t in q)


def _parse_llm_domain_plan(text: str) -> dict[str, Any] | None:
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[^{}]*primary_domain[^{}]*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


@dataclass
class CrossDomainPlan:
    """План retrieval по нескольким доменам."""

    query: str
    primary_domain: str
    secondary_domains: list[str] = field(default_factory=list)
    bridges: list[DomainBridge] = field(default_factory=list)
    cross_domain: bool = False

    routing: str = "heuristic"
    llm_raw: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "query": self.query,
            "primary_domain": self.primary_domain,
            "secondary_domains": self.secondary_domains,
            "cross_domain": self.cross_domain,
            "bridges": [b.to_dict() for b in self.bridges],
            "routing": self.routing,
        }
        if self.llm_raw:
            d["llm_raw"] = self.llm_raw[:500]
        return d


class DomainOrchestrator:
    """Выбор доменов для запроса."""

    def plan(
        self,
        query: str,
        explicit_domain: str | None = None,
        *,
        max_secondary: int = 2,
    ) -> CrossDomainPlan:
        primary = normalize_domain(explicit_domain) if explicit_domain else infer_domain(
            claim=query
        )
        if primary == "general":
            primary = infer_domain(claim=query)

        candidates = list(_BY_FROM.get(primary, []))
        candidates.sort(key=lambda b: -_score_bridge(query, b))
        bridges = candidates[:max_secondary]
        secondary = [b.to_domain for b in bridges]
        return CrossDomainPlan(
            query=query,
            primary_domain=primary,
            secondary_domains=secondary,
            bridges=bridges,
            cross_domain=len(secondary) > 0,
            routing="smart_terms",
        )

    def plan_from_llm_json(
        self,
        query: str,
        parsed: dict[str, Any],
        *,
        max_secondary: int = 2,
    ) -> CrossDomainPlan:
        primary = normalize_domain(parsed.get("primary_domain"))
        if primary == "general":
            return self.plan(query, None, max_secondary=max_secondary)

        raw_sec = parsed.get("secondary_domains") or []
        secondary: list[str] = []
        bridges: list[DomainBridge] = []
        for s in raw_sec:
            dom = normalize_domain(s)
            if dom == primary or dom == "general" or dom in secondary:
                continue
            for b in _BY_FROM.get(primary, []):
                if b.to_domain == dom:
                    bridges.append(b)
                    secondary.append(dom)
                    break
            else:
                secondary.append(dom)
            if len(secondary) >= max_secondary:
                break

        return CrossDomainPlan(
            query=query,
            primary_domain=primary,
            secondary_domains=secondary,
            bridges=bridges,
            cross_domain=len(secondary) > 0,
            routing="llm",
        )


class CrossDomainLayer:
    """Обогащение retrieval и ответа междоменными фактами."""

    def __init__(self) -> None:
        self._orchestrator = DomainOrchestrator()

    def plan(self, query: str, domain: str | None = None) -> CrossDomainPlan:
        return plan_query(query, domain)

    def retrieve(
        self,
        query: str,
        k: int = 3,
        domain: str | None = None,
        *,
        plan: CrossDomainPlan | None = None,
    ) -> tuple[list[dict[str, Any]], CrossDomainPlan]:
        from core.pipeline import retrieve

        plan = plan or plan_query(query, domain)
        if not plan.cross_domain or not is_cross_domain_enabled():
            return retrieve(query, k=k, domain=domain or plan.primary_domain), plan

        merged: list[dict[str, Any]] = []
        seen: set[str] = set()
        per_domain_k = max(1, k // (1 + len(plan.secondary_domains)))

        for dom in [plan.primary_domain, *plan.secondary_domains]:
            batch = retrieve(query, k=per_domain_k, domain=dom)
            for item in batch:
                fid = item.get("id") or item.get("fact_id")
                if fid and fid in seen:
                    continue
                if fid:
                    seen.add(fid)
                meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
                meta = dict(meta or {})
                meta.setdefault("domain", dom)
                meta["cross_domain_via"] = plan.primary_domain if dom != plan.primary_domain else dom
                item = dict(item)
                item["metadata"] = meta
                merged.append(item)
            if len(merged) >= k:
                break

        return merged[:k], plan

    def annotate_facts(
        self,
        facts: list[dict[str, Any]],
        plan: CrossDomainPlan,
    ) -> dict[str, Any]:
        """Сводка для QueryResponse."""
        by_dom: dict[str, int] = {}
        bridge_hits: list[dict[str, Any]] = []
        domains_present = {fact_domain(f) for f in facts}

        for b in plan.bridges:
            if b.to_domain in domains_present and b.from_domain in domains_present:
                bridge_hits.append(
                    {
                        **b.to_dict(),
                        "active": True,
                        "hint": f"В ответе есть факты из {b.from_domain} и {b.to_domain}",
                    }
                )

        for f in facts:
            d = fact_domain(f)
            by_dom[d] = by_dom.get(d, 0) + 1

        return {
            "enabled": True,
            "plan": plan.to_dict(),
            "facts_by_domain": by_dom,
            "bridges_active": bridge_hits,
            "total_domains": len(by_dom),
            "causal_links": [],
        }


def plan_query(query: str, domain: str | None = None) -> CrossDomainPlan:
    """Синхронный план: smart terms + опц. LLM через run_coroutine_sync."""
    if is_cross_domain_llm_routing_enabled():
        try:
            from core.async_utils import run_coroutine_sync

            return run_coroutine_sync(plan_query_async(query, domain))
        except Exception as exc:  # noqa: BLE001
            logger.debug("cross_domain LLM plan fallback: %s", exc)
    return DomainOrchestrator().plan(query, domain)


async def plan_query_async(
    query: str,
    domain: str | None = None,
    *,
    llm_complete: Callable[[str, str], Awaitable[str]] | None = None,
) -> CrossDomainPlan:
    orch = DomainOrchestrator()
    if not is_cross_domain_llm_routing_enabled():
        return orch.plan(query, domain)

    if llm_complete is None:
        try:
            import server as srv

            llm_complete = srv._llm_generate
        except Exception:
            return orch.plan(query, domain)

    from core.domain_tags import ALLOWED_DOMAINS

    system = (
        "Ты DomainOrchestrator Velantrim. Ответь ТОЛЬКО JSON без markdown: "
        '{"primary_domain":"...", "secondary_domains":["..."]}. '
        f"Допустимые домены: {sorted(ALLOWED_DOMAINS)}."
    )
    prompt = f"Запрос: {query}\nЯвный домен: {domain or 'auto'}"
    try:
        raw = await llm_complete(prompt, system)
        parsed = _parse_llm_domain_plan(raw)
        if parsed:
            plan = orch.plan_from_llm_json(query, parsed)
            plan.llm_raw = raw
            return plan
    except Exception as exc:  # noqa: BLE001
        logger.debug("plan_query_async: %s", exc)
    return orch.plan(query, domain)


def sync_cross_domain_edges(
    facts: list[dict[str, Any]],
    plan: CrossDomainPlan,
    *,
    max_links: int = 5,
) -> list[dict[str, Any]]:
    """
    Создать inferred analogous_to между фактами разных доменов (CausalGraph).
    """
    if not is_cross_domain_causal_enabled() or not plan.cross_domain:
        return []

    try:
        from core.causal_graph import get_causal_graph, is_causal_graph_enabled
    except Exception:
        return []

    if not is_causal_graph_enabled():
        return []

    cg = get_causal_graph()
    by_domain: dict[str, list[str]] = {}
    for f in facts:
        fid = f.get("fact_id")
        if not fid:
            continue
        by_domain.setdefault(fact_domain(f), []).append(str(fid))

    created: list[dict[str, Any]] = []
    for bridge in plan.bridges:
        a_list = by_domain.get(bridge.from_domain, [])[:2]
        b_list = by_domain.get(bridge.to_domain, [])[:2]
        if not a_list or not b_list:
            continue
        for from_id in a_list:
            for to_id in b_list:
                if from_id == to_id:
                    continue
                try:
                    rid = cg.add_relation(
                        from_id,
                        to_id,
                        "analogous_to",
                        confidence=0.65,
                        knowledge_status="inferred",
                        inference_source="cross_domain",
                        metadata={
                            "bridge": bridge.label_ru,
                            "from_domain": bridge.from_domain,
                            "to_domain": bridge.to_domain,
                        },
                    )
                    created.append(
                        {
                            "relation_id": rid,
                            "from_fact_id": from_id,
                            "to_fact_id": to_id,
                            "relation_type": "analogous_to",
                            "bridge": bridge.label_ru,
                        }
                    )
                    try:
                        from core.async_utils import run_coroutine_sync
                        from core.event_bridge import on_causal_relation

                        run_coroutine_sync(
                            on_causal_relation(
                                rid, from_id, to_id, "analogous_to"
                            )
                        )
                    except Exception:
                        pass
                except ValueError as exc:
                    logger.debug("cross_domain edge: %s", exc)
                if len(created) >= max_links:
                    return created
    return created


_layer: CrossDomainLayer | None = None


def get_cross_domain_layer() -> CrossDomainLayer:
    global _layer
    if _layer is None:
        _layer = CrossDomainLayer()
    return _layer


def list_bridges() -> list[dict[str, Any]]:
    return [b.to_dict() for b in DOMAIN_BRIDGES]


def retrieve_cross_domain(
    query: str,
    k: int = 3,
    domain: str | None = None,
) -> list[dict[str, Any]]:
    plan = plan_query(query, domain)
    items, _ = get_cross_domain_layer().retrieve(query, k=k, domain=domain, plan=plan)
    return items


__all__ = [
    "CrossDomainLayer",
    "CrossDomainPlan",
    "DomainBridge",
    "DomainOrchestrator",
    "DOMAIN_BRIDGES",
    "get_cross_domain_layer",
    "is_cross_domain_enabled",
    "is_cross_domain_causal_enabled",
    "is_cross_domain_llm_routing_enabled",
    "list_bridges",
    "plan_query",
    "plan_query_async",
    "retrieve_cross_domain",
    "sync_cross_domain_edges",
]
