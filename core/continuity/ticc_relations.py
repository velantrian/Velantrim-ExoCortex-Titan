"""Exact-source TICC relation adapter for shadow evaluation only.

This module does not discover relation targets. It only materializes an existing
Titan ``AssertionRelation`` when the caller supplies both exact assertion
endpoints and an explicitly permitted lifecycle relation type.

No persistence, retrieval, semantic similarity, LLM classification, Canon,
TruthGate, identity, reply, tool/action, network, or runtime authority is added.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .contracts import (
    ActorRef,
    AssertionRecord,
    AssertionRelation,
    AssertionRelationType,
)


class TICCRelationError(ValueError):
    """Raised when an exact TICC relation invariant is violated."""


class TICCRelationDisposition(str, Enum):
    MATERIALIZED = "materialized"
    DEFERRED = "deferred"


_ALLOWED_TYPES = {
    AssertionRelationType.CORRECTS,
    AssertionRelationType.RETRACTS,
}


@dataclass(frozen=True, slots=True)
class TICCRelationRequest:
    relation_type: AssertionRelationType
    source_assertion: AssertionRecord
    target_assertion: AssertionRecord
    evidence_refs: tuple[str, ...]
    actor_ref: ActorRef
    created_at: datetime

    def __post_init__(self) -> None:
        if self.relation_type not in _ALLOWED_TYPES:
            raise TICCRelationError("only CORRECTS/RETRACTS are permitted in v0")
        if not isinstance(self.source_assertion, AssertionRecord):
            raise TICCRelationError("source_assertion must be AssertionRecord")
        if not isinstance(self.target_assertion, AssertionRecord):
            raise TICCRelationError("target_assertion must be AssertionRecord")
        if self.source_assertion.assertion_id == self.target_assertion.assertion_id:
            raise TICCRelationError("relation endpoints must be distinct")
        if not isinstance(self.actor_ref, ActorRef):
            raise TICCRelationError("actor_ref must be ActorRef")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise TICCRelationError("created_at must be timezone-aware")
        refs = tuple(self.evidence_refs)
        if not refs:
            raise TICCRelationError("evidence_refs cannot be empty")
        if any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise TICCRelationError("evidence_refs must contain non-empty strings")
        if len(refs) != len(set(refs)):
            raise TICCRelationError("evidence_refs cannot contain duplicates")


@dataclass(frozen=True, slots=True)
class TICCRelationResult:
    disposition: TICCRelationDisposition
    relation: AssertionRelation | None
    reason: str


def materialize_exact_relation(request: TICCRelationRequest) -> TICCRelationResult:
    """Create one existing Titan AssertionRelation from exact supplied endpoints.

    This function performs no target discovery and no semantic inference.
    Cross-state-key and origin/authority policy remain owned by StateReconciler.
    """
    if not isinstance(request, TICCRelationRequest):
        raise TICCRelationError("request must be TICCRelationRequest")

    relation = AssertionRelation.create(
        relation_type=request.relation_type,
        source_assertion_ref=request.source_assertion.assertion_id,
        target_assertion_ref=request.target_assertion.assertion_id,
        evidence_refs=request.evidence_refs,
        actor_ref=request.actor_ref,
        created_at=request.created_at,
    )
    return TICCRelationResult(
        disposition=TICCRelationDisposition.MATERIALIZED,
        relation=relation,
        reason="exact_endpoints_supplied",
    )


__all__ = [
    "TICCRelationDisposition",
    "TICCRelationError",
    "TICCRelationRequest",
    "TICCRelationResult",
    "materialize_exact_relation",
]
