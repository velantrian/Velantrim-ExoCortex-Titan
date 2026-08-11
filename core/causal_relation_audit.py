"""Same-transaction AuditChain evidence for canonical causal relation rows.

Issue #286 / parent #50.

This module is intentionally narrow: it does not own ``relations`` persistence and it
is not a second write protocol. ``CausalGraph`` remains the canonical causal mutation
owner. The helper only prepares the existing AuditChain schema before a relation
transaction starts and appends structured relation lifecycle events inside that caller-
owned SQLite transaction.

Each physical ``relations`` row gets a stable chain identity derived only from its
``relation_id``. No claim text, prompt text, model output, or free-text reason is copied
into AuditChain.
"""
from __future__ import annotations

import sqlite3

from core.audit_chain import AuditChain

CAUSAL_AUDIT_SCHEMA_CHAIN = "causal-relations:schema"
CAUSAL_RELATION_CHAIN_PREFIX = "causal-relation:"

EVENT_RELATION_CREATED = "relation_created"
EVENT_RELATION_REMOVED = "relation_removed"

ACTOR_CAUSAL_GRAPH = "causal_graph"
REASON_CANONICAL_RELATION_WRITE = "canonical_relation_write"


def ensure_causal_audit_ready(conn: sqlite3.Connection) -> None:
    """Prepare AuditChain schema before the canonical relation transaction opens."""
    if conn.in_transaction:
        raise RuntimeError(
            "causal audit readiness must run before the relation transaction opens"
        )
    AuditChain.verify_schema_ready(conn, chain_id=CAUSAL_AUDIT_SCHEMA_CHAIN)


def append_relation_event(
    conn: sqlite3.Connection,
    *,
    relation_id: str,
    event_type: str,
) -> None:
    """Append one structured relation event inside the caller-owned transaction."""
    if event_type not in {EVENT_RELATION_CREATED, EVENT_RELATION_REMOVED}:
        raise ValueError(f"unsupported causal relation audit event: {event_type!r}")
    if not relation_id:
        raise ValueError("relation_id is required for causal relation audit")
    if not conn.in_transaction:
        raise RuntimeError(
            "causal relation audit event requires an active caller-owned transaction"
        )

    AuditChain(
        conn,
        chain_id=f"{CAUSAL_RELATION_CHAIN_PREFIX}{relation_id}",
        _skip_schema_check=True,
    ).log_in_transaction(
        event_type=event_type,
        actor=ACTOR_CAUSAL_GRAPH,
        reason=REASON_CANONICAL_RELATION_WRITE,
    )


__all__ = [
    "ACTOR_CAUSAL_GRAPH",
    "CAUSAL_AUDIT_SCHEMA_CHAIN",
    "CAUSAL_RELATION_CHAIN_PREFIX",
    "EVENT_RELATION_CREATED",
    "EVENT_RELATION_REMOVED",
    "REASON_CANONICAL_RELATION_WRITE",
    "append_relation_event",
    "ensure_causal_audit_ready",
]
