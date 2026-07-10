"""
Реальные обработчики инструментов для core.tool_registry (P1 hardening).

Тонкие обёртки над существующими модулями — без дублирования бизнес-логики.
"""
from __future__ import annotations

import uuid
from typing import Any

from core import memory as memory_api
from core.pipeline import retrieve


def search_facts(query: str, *, k: int = 5, domain: str | None = None) -> list[dict[str, Any]]:
    return retrieve(query, k=k, domain=domain)


def get_fact(fact_id: str) -> dict[str, Any] | None:
    return memory_api.get_fact(fact_id)


def causal_chain(
    fact_id: str,
    *,
    max_depth: int = 5,
    min_confidence: float = 0.5,
) -> list[dict[str, Any]]:
    from core.causal_graph import get_causal_graph

    graph = get_causal_graph()
    chains = graph.causal_chain(
        fact_id,
        max_depth=max_depth,
        min_confidence=min_confidence,
    )
    return [c.to_dict() for c in chains]


def explain_fact(fact_id: str) -> dict[str, Any]:
    from core.causal_graph import get_causal_graph

    return get_causal_graph().explain(fact_id)


def explain_path(
    fact_a: str,
    fact_b: str,
    *,
    max_depth: int = 5,
    min_confidence: float = 0.3,
) -> dict[str, Any] | None:
    from core.essence_facade.causal import explain_path as _explain_path

    return _explain_path(
        fact_a,
        fact_b,
        max_depth=max_depth,
        min_confidence=min_confidence,
    )


def graph_stats() -> dict[str, Any]:
    from core.causal_graph import get_causal_graph

    graph = get_causal_graph()
    stats = graph.stats()
    stats["orphan_nodes"] = graph.count_orphan_nodes()
    return stats


def get_entities_for_fact(fact_id: str) -> list[dict[str, Any]]:
    from core.entity_resolver import get_entity_resolver

    return get_entity_resolver().get_entities_for_fact(fact_id)


def get_facts_for_entity(entity_name: str, *, limit: int = 50) -> list[str]:
    from core.entity_resolver import get_entity_resolver

    return get_entity_resolver().get_facts_for_entity(entity_name, limit=limit)


def get_living_context(fact_id: str) -> dict[str, Any] | None:
    from core.living_context import LivingContextStore
    from core.memory import get_store

    with get_store()._db() as conn:
        ctx = LivingContextStore(conn).get(fact_id)
    if ctx is None:
        return None
    return ctx.to_dict()


def propose_hypothesis(
    claim: str,
    *,
    source: str = "tool:propose_hypothesis",
    confidence: float = 0.5,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fact_id = f"hyp.{uuid.uuid4().hex[:12]}"
    fact = {
        "fact_id": fact_id,
        "claim": claim,
        "source": source,
        "confidence": confidence,
        "epistemic_state": "Hypothesized",
        "metadata": metadata or {},
    }
    inserted = memory_api.store_fact(fact)
    return {"fact_id": fact_id, "inserted": inserted, "epistemic_state": "Hypothesized"}


def find_analogies(fact_id: str, *, cross_domain: bool = True) -> list[dict[str, Any]]:
    from core.causal_graph import get_causal_graph

    pairs = get_causal_graph().find_analogies(fact_id, cross_domain=cross_domain)
    return [{"fact_id": fid, "score": score} for fid, score in pairs]


def store_fact(fact: dict[str, Any]) -> dict[str, Any]:
    payload = dict(fact)
    payload.setdefault("epistemic_state", "Observed")
    inserted = memory_api.store_fact(payload)
    return {
        "fact_id": payload.get("fact_id"),
        "inserted": inserted,
        "epistemic_state": payload.get("epistemic_state"),
    }


def link_entity(
    fact_id: str,
    entity_name: str,
    *,
    mention_type: str = "subject",
    confidence: float = 0.8,
) -> dict[str, Any]:
    from core.entity_resolver import get_entity_resolver

    mention_id = get_entity_resolver().link_entity(
        fact_id,
        entity_name,
        mention_type=mention_type,
        confidence=confidence,
    )
    return {"fact_id": fact_id, "entity": entity_name, "mention_id": mention_id}


def validate_fact(fact_id: str, *, by: str = "tool:validate_fact") -> dict[str, Any]:
    ok = memory_api.promote_to_validated(fact_id, by=by)
    return {"fact_id": fact_id, "validated": ok, "epistemic_state": "Validated" if ok else None}


def contradict_fact(fact_id: str, *, by: str = "tool:contradict_fact") -> dict[str, Any]:
    ok = memory_api.transition_esm(fact_id, "Contradicted", by=by)
    return {"fact_id": fact_id, "contradicted": ok, "epistemic_state": "Contradicted" if ok else None}


def supersede_fact(
    old_fact_id: str,
    new_fact_id: str,
    *,
    by: str = "tool:supersede_fact",
) -> dict[str, Any]:
    ok = memory_api.transition_esm(old_fact_id, "Deprecated", by=by)
    return {
        "old_fact_id": old_fact_id,
        "new_fact_id": new_fact_id,
        "deprecated": ok,
    }


def forget_all(
    *,
    user_id: str,
    reason: str = "gdpr_request",
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    from core.forgetting import get_forgetting_engine

    verdict = get_forgetting_engine().forget_all(
        user_id=user_id,
        reason=reason,
        dry_run=dry_run,
        force=force,
    )
    return verdict.to_dict()


def reset_graph(*, confirm: bool = False) -> dict[str, Any]:
    if not confirm:
        return {
            "ok": False,
            "error": "destructive_action",
            "message": "Pass confirm=True to delete all relations",
        }
    from core.causal_graph import get_causal_graph

    graph = get_causal_graph()
    deleted = graph._conn.execute("DELETE FROM relations").rowcount
    graph._conn.commit()
    return {"ok": True, "relations_deleted": deleted}


__all__ = [
    "search_facts",
    "get_fact",
    "causal_chain",
    "explain_fact",
    "explain_path",
    "graph_stats",
    "get_entities_for_fact",
    "get_facts_for_entity",
    "get_living_context",
    "propose_hypothesis",
    "find_analogies",
    "store_fact",
    "link_entity",
    "validate_fact",
    "contradict_fact",
    "supersede_fact",
    "forget_all",
    "reset_graph",
]
