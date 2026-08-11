"""
Реальные обработчики инструментов для core.tool_registry (P1 hardening).

Тонкие обёртки над существующими модулями — без дублирования бизнес-логики.
"""
from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from core import memory as memory_api
from core.pipeline import retrieve
from core.promotion_gateway import PromotionGateway, PromotionRequest
from core.tool_registry import PrincipalContext


class _CurrentMemoryPromotionStore:
    """Reload-safe adapter over the currently canonical memory module."""

    def validate_and_promote(
        self,
        fact_id: str,
        by: str = "truth_gate",
        mode: Any = None,
    ) -> Any:
        from core import memory as current_memory_api

        return current_memory_api.validate_and_promote(
            fact_id, by=by, mode=mode
        )


_tool_promotion_gateway = PromotionGateway(_CurrentMemoryPromotionStore())


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
    """
    SECURITY/CORRECTNESS (confirmed issue #4): fact_living_context is created
    by migrations/008_add_relations.sql, not by SQLiteGraphStore's own DDL —
    a store that hasn't had migrations applied (a fresh test DB, an
    unmigrated deployment) raises sqlite3.OperationalError ("no such table")
    instead of the documented Optional[dict] contract. This tool must degrade
    to None, not crash the MCP call, when the table is simply absent.
    """
    from core.living_context import LivingContextStore
    from core.memory import get_store

    try:
        with get_store()._db() as conn:
            ctx = LivingContextStore(conn).get(fact_id)
    except sqlite3.OperationalError:
        return None
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
    """
    SECURITY/CORRECTNESS (confirmed issue #3): store_fact() only accepts new
    facts in epistemic_state='Observed' (I50) — it raises ValueError for any
    other initial state (except the Ring Zero seed special-case). Passing
    epistemic_state='Hypothesized' directly here made every call to this
    tool raise instead of ever creating a hypothesis. Fixed: insert as
    Observed first, then legally advance via transition_esm() (Observed ->
    Hypothesized is the only legal first step in ESM_TRANSITIONS).
    """
    fact_id = f"hyp.{uuid.uuid4().hex[:12]}"
    fact = {
        "fact_id": fact_id,
        "claim": claim,
        "source": source,
        "confidence": confidence,
        "epistemic_state": "Observed",
        "metadata": metadata or {},
    }
    inserted = memory_api.store_fact(fact)
    promoted = memory_api.transition_esm(
        fact_id, "Hypothesized", by="tool:propose_hypothesis",
    )
    return {
        "fact_id": fact_id,
        "inserted": inserted,
        "epistemic_state": "Hypothesized" if promoted else "Observed",
    }


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
    """Validate one guardian-tool fact through PromotionGateway.

    The gateway delegates to the existing TruthGate + CAS authority. The
    reload-safe adapter resolves the currently canonical memory module when
    the call executes, so test/runtime store reconstruction cannot leave this
    handler pinned to an obsolete SQLiteGraphStore instance.
    """
    outcome = _tool_promotion_gateway.promote(
        PromotionRequest(fact_id=fact_id, requested_by=by)
    )
    verdict = outcome.verdict
    return {
        "fact_id": fact_id,
        "validated": verdict.passed,
        "epistemic_state": "Validated" if verdict.passed else None,
        "reason": verdict.reason_code,
        "justification": verdict.justification,
    }


def contradict_fact(fact_id: str, *, by: str = "tool:contradict_fact") -> dict[str, Any]:
    ok = memory_api.transition_esm(fact_id, "Contradicted", by=by)
    return {"fact_id": fact_id, "contradicted": ok, "epistemic_state": "Contradicted" if ok else None}


def supersede_fact(old_fact_id: str, new_fact: dict[str, Any]) -> dict[str, Any]:
    """
    SECURITY (confirmed Codex finding): must route through the atomic
    core.truth_maintenance.supersede() CAS flow built in PR #11 — it
    validates the replacement through TruthGate and commits old (Deprecated)
    + new (Validated) together in one transaction. The previous version only
    transitioned old_fact_id to Deprecated and never validated, created, or
    linked new_fact_id at all — it could report success even when the
    replacement never existed.
    """
    if not isinstance(new_fact, dict) or not str(new_fact.get("fact_id") or "").strip():
        return {
            "old_fact_id": old_fact_id,
            "new_fact_id": None,
            "superseded": False,
            "error": "invalid_new_fact",
            "message": "new_fact must be an object with a non-empty 'fact_id'",
        }

    from core.truth_maintenance import supersede as _supersede

    new_fact_id = new_fact["fact_id"]
    try:
        result = _supersede(old_fact_id, new_fact)
    except ValueError as exc:
        return {
            "old_fact_id": old_fact_id,
            "new_fact_id": new_fact_id,
            "superseded": False,
            "error": "invalid_request",
            "message": str(exc),
        }

    return {
        "old_fact_id": old_fact_id,
        "new_fact_id": new_fact_id,
        "superseded": result is not None,
    }


def forget_all(
    *,
    user_id: str,
    principal: PrincipalContext,
    reason: str = "gdpr_request",
    dry_run: bool = False,
    force: bool = False,
    scope: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """GDPR Art. 17 batch erasure (FORGET_ALL): durable, resumable batch
    saga via core.erasure_batch_coordinator — see there for the full
    state machine.

    `principal` is REQUIRED and is never something this function invents
    or assumes: core.tool_registry registers this tool with
    `needs_principal=True`, so core.mcp_transport injects the REAL
    server-verified capability/credential_fingerprint for THIS call (see
    core.tool_registry.PrincipalContext) — this handler has no
    "actor_capability='admin'" literal of its own to fake a check with.
    A caller that invokes this function directly (bypassing the MCP
    dispatch entirely) must supply its own PrincipalContext explicitly;
    there is no way to reach this function without one, and no default
    that silently grants admin.
    """
    from core.erasure_batch_coordinator import forget_all_durable

    return forget_all_durable(
        user_id,
        reason=reason,
        actor=principal.credential_fingerprint,
        actor_capability=principal.capability,
        force=force,
        scope=scope,
        dry_run=dry_run,
        idempotency_key=idempotency_key,
    )


def reset_graph(*, confirm: bool = False) -> dict[str, Any]:
    if not confirm:
        return {
            "ok": False,
            "error": "destructive_action",
            "message": "Pass confirm=True to delete all relations",
        }
    from core.causal_graph import get_causal_graph

    deleted = get_causal_graph().reset_relations()
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
