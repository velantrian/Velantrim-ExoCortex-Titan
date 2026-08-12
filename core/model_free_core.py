"""Explicit model-free read contract for Titan issue #53 Phase 1.

This module is a facade over existing, already-authoritative primitives. It does
not own retrieval ranking, truth policy, graph mutation, canonical writes, model
selection, runtime activation, or network access.

The bounded contract is intentionally boring:

    deterministic QueryRouter
      -> existing lexical-only retrieval path
      -> existing FactsPack / Guardian / TruthGate
      -> existing local CausalGraph read surface (when present)
      -> deterministic evidence renderer

No DenseRetriever, RRF, reranker, LLM, remote provider, ADAO, or CapabilityRegistry
is selected by this facade.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.query_router import QueryRouter, get_query_router
from core.trace import build_trace

_INSUFFICIENT_ANSWER = "Недостаточно подтверждённых локальных данных."
_ALLOWED_MODES = frozenset({"PRECISION", "BALANCED", "EXPLORATION", "CREATIVE"})


@dataclass(frozen=True)
class L2Query:
    """Typed model-free query contract."""

    text: str
    top_k: int = 10
    domain: str | None = None
    cognitive_mode: str = "BALANCED"
    include_graph: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("L2Query.text must be a string")
        if not 1 <= self.top_k <= 100:
            raise ValueError("L2Query.top_k must be between 1 and 100")
        normalized_mode = self.cognitive_mode.upper()
        if normalized_mode not in _ALLOWED_MODES:
            raise ValueError(
                f"Unsupported cognitive_mode {self.cognitive_mode!r}; "
                f"expected one of {sorted(_ALLOWED_MODES)}"
            )
        object.__setattr__(self, "cognitive_mode", normalized_mode)


@dataclass(frozen=True)
class L2Evidence:
    fact_id: str
    claim: str
    source: str
    epistemic_state: str
    confidence: float
    retrieval_score: float
    claim_type: str
    origin_type: str
    truth_status: str

    @classmethod
    def from_fact(cls, fact: dict[str, Any]) -> "L2Evidence":
        return cls(
            fact_id=str(fact.get("fact_id") or ""),
            claim=str(fact.get("claim") or ""),
            source=str(fact.get("source") or "unknown"),
            epistemic_state=str(fact.get("epistemic_state") or "Observed"),
            confidence=float(fact.get("confidence", 0.0) or 0.0),
            retrieval_score=float(fact.get("retrieval_score", 0.0) or 0.0),
            claim_type=str(fact.get("claim_type") or "UNKNOWN"),
            origin_type=str(fact.get("origin_type") or "UNKNOWN"),
            truth_status=str(fact.get("truth_status") or "UNVERIFIED"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "claim": self.claim,
            "source": self.source,
            "epistemic_state": self.epistemic_state,
            "confidence": self.confidence,
            "retrieval_score": self.retrieval_score,
            "claim_type": self.claim_type,
            "origin_type": self.origin_type,
            "truth_status": self.truth_status,
        }


@dataclass(frozen=True)
class L2Relation:
    relation_id: str
    from_fact_id: str
    to_fact_id: str
    relation_type: str
    confidence: float
    knowledge_status: str
    truth_status: str
    review_state: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "from_fact_id": self.from_fact_id,
            "to_fact_id": self.to_fact_id,
            "relation_type": self.relation_type,
            "confidence": self.confidence,
            "knowledge_status": self.knowledge_status,
            "truth_status": self.truth_status,
            "review_state": self.review_state,
        }


@dataclass(frozen=True)
class L2Result:
    query: str
    query_type: str
    retrieval_mode: str
    execution_mode: str
    evidence: tuple[L2Evidence, ...]
    relations: tuple[L2Relation, ...]
    conflicts: tuple[L2Relation, ...]
    answer: str
    insufficient_evidence: bool
    reason_code: str | None
    guardian_passed: bool
    truth_gate_passed: bool

    @property
    def optional_capabilities_used(self) -> tuple[str, ...]:
        return ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "query_type": self.query_type,
            "retrieval_mode": self.retrieval_mode,
            "execution_mode": self.execution_mode,
            "evidence": [item.to_dict() for item in self.evidence],
            "relations": [item.to_dict() for item in self.relations],
            "conflicts": [item.to_dict() for item in self.conflicts],
            "answer": self.answer,
            "insufficient_evidence": self.insufficient_evidence,
            "reason_code": self.reason_code,
            "guardian_passed": self.guardian_passed,
            "truth_gate_passed": self.truth_gate_passed,
            "optional_capabilities_used": [],
        }


class ModelFreeCore:
    """Typed, deterministic facade over Titan's existing model-free read path."""

    def __init__(self, router: QueryRouter | None = None) -> None:
        self._router = router or get_query_router()

    def query(self, request: L2Query) -> L2Result:
        """Execute the bounded Phase-1 path without model/network escalation."""

        import core.pipeline as pipeline

        query_type = self._router.classify(request.text).value
        if not request.text.strip():
            return self._insufficient(request, query_type, "empty_query")

        retrieved = pipeline._retrieve_from_store(
            request.text,
            k=request.top_k,
            domain=request.domain,
            retrieval_mode="lexical",
        )
        if not retrieved:
            return self._insufficient(
                request, query_type, "no_local_lexical_retrieval_results"
            )

        facts_pack = pipeline.build_facts_pack(
            retrieved,
            request.text,
            cognitive_mode=request.cognitive_mode,
        )
        facts = list(facts_pack.get("facts") or [])
        if not facts:
            return self._insufficient(
                request, query_type, "no_policy_eligible_local_evidence"
            )

        trace_input = [
            {
                "id": fact["fact_id"],
                "source": fact["source"],
                "origin": "model_free_lexical",
                "epistemic_state": fact["epistemic_state"],
                "retrieval_score": fact["retrieval_score"],
                "confidence": fact["confidence"],
            }
            for fact in facts
        ]
        trace = build_trace(trace_input)

        guardian_ok, guardian_reason = pipeline.guardian(facts_pack, trace)
        if not guardian_ok:
            return self._insufficient(
                request,
                query_type,
                "guardian_rejected",
                guardian_passed=False,
                detail=guardian_reason,
            )

        gate_ok, gate_reason = pipeline.truth_gate(
            facts_pack,
            mode=request.cognitive_mode,
        )
        if not gate_ok:
            return self._insufficient(
                request,
                query_type,
                "truth_gate_rejected",
                guardian_passed=True,
                truth_gate_passed=False,
                detail=gate_reason,
            )

        evidence = tuple(L2Evidence.from_fact(fact) for fact in facts)
        relations = (
            self._collect_relations(pipeline, evidence)
            if request.include_graph
            else ()
        )
        conflicts = tuple(
            relation for relation in relations if relation.relation_type == "contradicts"
        )
        return L2Result(
            query=request.text,
            query_type=query_type,
            retrieval_mode="lexical",
            execution_mode="model_free",
            evidence=evidence,
            relations=relations,
            conflicts=conflicts,
            answer=self._render(evidence, conflicts),
            insufficient_evidence=False,
            reason_code=None,
            guardian_passed=True,
            truth_gate_passed=True,
        )

    @staticmethod
    def _collect_relations(
        pipeline: Any,
        evidence: tuple[L2Evidence, ...],
    ) -> tuple[L2Relation, ...]:
        if not evidence:
            return ()
        try:
            graph = pipeline._get_causal_graph()
        except Exception:
            return ()
        if graph is None:
            return ()

        evidence_ids = {item.fact_id for item in evidence}
        seen: set[str] = set()
        rows: list[L2Relation] = []
        for fact_id in sorted(evidence_ids):
            try:
                candidates = graph.get_relations_from(fact_id) + graph.get_relations_to(
                    fact_id
                )
            except Exception:
                continue
            for relation in candidates:
                relation_id = str(getattr(relation, "relation_id", "") or "")
                if not relation_id or relation_id in seen:
                    continue
                seen.add(relation_id)
                rows.append(
                    L2Relation(
                        relation_id=relation_id,
                        from_fact_id=str(getattr(relation, "from_fact_id", "") or ""),
                        to_fact_id=str(getattr(relation, "to_fact_id", "") or ""),
                        relation_type=str(getattr(relation, "relation_type", "") or ""),
                        confidence=float(getattr(relation, "confidence", 0.0) or 0.0),
                        knowledge_status=str(
                            getattr(relation, "knowledge_status", "unknown") or "unknown"
                        ),
                        truth_status=str(
                            getattr(relation, "truth_status", "pending") or "pending"
                        ),
                        review_state=str(
                            getattr(relation, "review_state", "pending") or "pending"
                        ),
                    )
                )
        rows.sort(
            key=lambda row: (
                row.relation_type,
                row.from_fact_id,
                row.to_fact_id,
                row.relation_id,
            )
        )
        return tuple(rows)

    @staticmethod
    def _render(
        evidence: tuple[L2Evidence, ...],
        conflicts: tuple[L2Relation, ...],
    ) -> str:
        lines = ["Подтверждённые локальные данные:"]
        for fact in evidence:
            lines.append(f"- [{fact.fact_id}] ({fact.epistemic_state}) {fact.claim}")
        if conflicts:
            lines.append(f"⚠️ Известные локальные противоречия: {len(conflicts)}.")
        return "\n".join(lines)

    @staticmethod
    def _insufficient(
        request: L2Query,
        query_type: str,
        reason_code: str,
        *,
        guardian_passed: bool = False,
        truth_gate_passed: bool = False,
        detail: str | None = None,
    ) -> L2Result:
        if detail:
            reason_code = f"{reason_code}:{detail}"
        return L2Result(
            query=request.text,
            query_type=query_type,
            retrieval_mode="lexical",
            execution_mode="model_free",
            evidence=(),
            relations=(),
            conflicts=(),
            answer=_INSUFFICIENT_ANSWER,
            insufficient_evidence=True,
            reason_code=reason_code,
            guardian_passed=guardian_passed,
            truth_gate_passed=truth_gate_passed,
        )


__all__ = [
    "L2Evidence",
    "L2Query",
    "L2Relation",
    "L2Result",
    "ModelFreeCore",
]
