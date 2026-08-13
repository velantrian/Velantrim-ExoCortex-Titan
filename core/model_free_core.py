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

import math
from dataclasses import dataclass
from typing import Any

from core.query_router import QueryRouter, get_query_router
from core.recall_policy import is_fact_allowed_for_recall
from core.trace import build_trace

_INSUFFICIENT_ANSWER = "Недостаточно подтверждённых локальных данных."
_ALLOWED_MODES = frozenset({"PRECISION", "BALANCED", "EXPLORATION", "CREATIVE"})


class ModelFreeGraphReadError(RuntimeError):
    """The optional graph was present but could not be read reliably."""


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
        if isinstance(self.top_k, bool) or not isinstance(self.top_k, int):
            raise TypeError("L2Query.top_k must be an integer")
        if not 1 <= self.top_k <= 100:
            raise ValueError("L2Query.top_k must be between 1 and 100")
        if self.domain is not None:
            if not isinstance(self.domain, str):
                raise TypeError("L2Query.domain must be a string or None")
            if not self.domain.strip():
                raise ValueError("L2Query.domain must not be empty")
        if not isinstance(self.cognitive_mode, str):
            raise TypeError("L2Query.cognitive_mode must be a string")
        if not isinstance(self.include_graph, bool):
            raise TypeError("L2Query.include_graph must be a boolean")
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
    def from_fact(cls, fact: dict[str, Any]) -> L2Evidence:
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
    inference_source: str | None
    evidence_ref: str | None
    metadata: dict[str, Any]

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
            "inference_source": self.inference_source,
            "evidence_ref": self.evidence_ref,
            "metadata": dict(self.metadata),
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
            allow_cognitive_rerank=False,
        )
        if not retrieved:
            return self._insufficient(
                request, query_type, "no_local_lexical_retrieval_results"
            )

        try:
            facts_pack = pipeline.build_facts_pack(
                retrieved,
                request.text,
                cognitive_mode=request.cognitive_mode,
                require_policy=True,
            )
        except Exception:
            return self._insufficient(
                request,
                query_type,
                "facts_pack_policy_unavailable",
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
        try:
            relations = (
                self._collect_relations(
                    pipeline,
                    evidence,
                    cognitive_mode=request.cognitive_mode,
                )
                if request.include_graph
                else ()
            )
        except ModelFreeGraphReadError:
            return self._insufficient(
                request,
                query_type,
                "causal_graph_read_failed",
                guardian_passed=True,
                truth_gate_passed=True,
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
        *,
        cognitive_mode: str,
    ) -> tuple[L2Relation, ...]:
        if not evidence:
            return ()
        try:
            graph = pipeline._peek_causal_graph()
        except Exception as exc:
            raise ModelFreeGraphReadError("causal graph lookup failed") from exc
        if graph is None:
            return ()

        evidence_ids = {item.fact_id for item in evidence}
        candidates_by_id: dict[str, Any] = {}
        for fact_id in sorted(evidence_ids):
            try:
                candidates = graph.get_relations_from(fact_id) + graph.get_relations_to(
                    fact_id
                )
            except Exception as exc:
                raise ModelFreeGraphReadError(
                    f"causal graph read failed for fact {fact_id!r}"
                ) from exc
            for relation in candidates:
                relation_id = str(getattr(relation, "relation_id", "") or "")
                if not relation_id:
                    continue
                candidates_by_id.setdefault(relation_id, relation)

        try:
            decoded_by_id = {
                relation_id: ModelFreeCore._decode_relation(relation)
                for relation_id, relation in candidates_by_id.items()
            }
            ModelFreeCore._validate_inverse_identity(decoded_by_id)
        except Exception as exc:
            raise ModelFreeGraphReadError(
                "causal relation row could not be decoded"
            ) from exc

        endpoint_ids = {
            endpoint
            for relation in decoded_by_id.values()
            for endpoint in (relation.from_fact_id, relation.to_fact_id)
            if endpoint
        }
        try:
            recallable = pipeline.get_facts_by_ids(sorted(endpoint_ids))
            eligible_ids: set[str] = set()
            for fact in recallable:
                fact_id = fact.get("fact_id")
                if not fact_id:
                    continue
                endpoint_pack = pipeline.build_facts_pack(
                    [
                        {
                            "id": fact_id,
                            "retrieval_score": 1.0,
                            "metadata": fact.get("metadata", {}),
                        }
                    ],
                    "model-free relation endpoint policy",
                    cognitive_mode=cognitive_mode,
                    require_policy=True,
                )
                eligible_ids.update(
                    str(packed.get("fact_id"))
                    for packed in endpoint_pack.get("facts", [])
                    if packed.get("fact_id")
                    and is_fact_allowed_for_recall(packed)
                )
        except Exception as exc:
            raise ModelFreeGraphReadError(
                "causal relation endpoint policy could not be evaluated"
            ) from exc

        semantic_relations: dict[str, L2Relation] = {}
        for relation_id, relation in decoded_by_id.items():
            if (
                relation.from_fact_id not in eligible_ids
                or relation.to_fact_id not in eligible_ids
            ):
                continue
            inverse_of = relation.metadata.get("inverse_of")
            semantic_id = (
                str(inverse_of)
                if isinstance(inverse_of, str) and inverse_of
                else relation_id
            )
            existing = semantic_relations.get(semantic_id)
            if existing is None:
                semantic_relations[semantic_id] = relation
                continue
            if existing.metadata.get("inverse_of"):
                if not relation.metadata.get("inverse_of"):
                    semantic_relations[semantic_id] = relation

        rows = list(semantic_relations.values())
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
    def _decode_relation(relation: Any) -> L2Relation:
        raw_metadata = getattr(relation, "metadata", None)
        if raw_metadata is None:
            metadata: dict[str, Any] = {}
        elif isinstance(raw_metadata, dict):
            metadata = dict(raw_metadata)
        else:
            raise ValueError("relation metadata must be a dict or None")
        inverse_of = metadata.get("inverse_of")
        if inverse_of is not None and (
            not isinstance(inverse_of, str) or not inverse_of
        ):
            raise ValueError("relation inverse identity must be a non-empty string")
        raw_confidence = getattr(relation, "confidence", 0.0)
        if isinstance(raw_confidence, bool):
            raise ValueError("relation confidence must not be boolean")
        confidence = float(raw_confidence or 0.0)
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ValueError("relation confidence must be finite and bounded")
        return L2Relation(
            relation_id=str(getattr(relation, "relation_id", "") or ""),
            from_fact_id=str(getattr(relation, "from_fact_id", "") or ""),
            to_fact_id=str(getattr(relation, "to_fact_id", "") or ""),
            relation_type=str(getattr(relation, "relation_type", "") or ""),
            confidence=confidence,
            knowledge_status=str(
                getattr(relation, "knowledge_status", "unknown") or "unknown"
            ),
            truth_status=str(
                getattr(relation, "truth_status", "pending") or "pending"
            ),
            review_state=str(
                getattr(relation, "review_state", "pending") or "pending"
            ),
            inference_source=(
                str(getattr(relation, "inference_source"))
                if getattr(relation, "inference_source", None) is not None
                else None
            ),
            evidence_ref=(
                str(getattr(relation, "evidence_ref"))
                if getattr(relation, "evidence_ref", None) is not None
                else None
            ),
            metadata=metadata,
        )

    @staticmethod
    def _validate_inverse_identity(decoded_by_id: dict[str, L2Relation]) -> None:
        """Validate generated inverse backlinks before semantic pair collapse.

        Canonical inverse rows point to the forward row through ``inverse_of``.
        Legacy/corrupt pointers must never be trusted as collapse keys: a target
        must exist, be the reciprocal relation tuple, and have exactly one
        backlink. Otherwise read-side evidence fails closed rather than hiding a
        physical relation or contradiction.
        """
        from core.causal_graph import INVERSE_RELATIONS

        linked_targets: set[str] = set()
        for relation_id, relation in decoded_by_id.items():
            inverse_of = relation.metadata.get("inverse_of")
            if not inverse_of:
                continue
            if inverse_of == relation_id:
                raise ValueError("relation inverse identity cannot point to itself")
            target = decoded_by_id.get(inverse_of)
            if target is None:
                raise ValueError("relation inverse identity target is missing")
            if target.metadata.get("inverse_of") is not None:
                raise ValueError("relation inverse identity target has a conflicting backlink")
            if inverse_of in linked_targets:
                raise ValueError("relation inverse identity target has multiple backlinks")

            expected_inverse_type = INVERSE_RELATIONS.get(target.relation_type)
            reciprocal_tuple = (
                target.from_fact_id == relation.to_fact_id
                and target.to_fact_id == relation.from_fact_id
                and expected_inverse_type == relation.relation_type
                and target.inference_source == relation.inference_source
            )
            if not reciprocal_tuple:
                raise ValueError("relation inverse identity target is not the reciprocal tuple")
            linked_targets.add(inverse_of)

    @staticmethod
    def _render(
        evidence: tuple[L2Evidence, ...],
        conflicts: tuple[L2Relation, ...],
    ) -> str:
        verified = tuple(
            fact for fact in evidence if fact.truth_status.upper() == "VERIFIED"
        )
        unverified = tuple(
            fact for fact in evidence if fact.truth_status.upper() != "VERIFIED"
        )
        lines: list[str] = []
        if verified:
            lines.append("Подтверждённые локальные факты:")
            for fact in verified:
                lines.append(
                    f"- [{ModelFreeCore._single_line(fact.fact_id)}] "
                    f"({ModelFreeCore._single_line(fact.epistemic_state)}) "
                    f"{ModelFreeCore._single_line(fact.claim)}"
                )
        if unverified:
            if lines:
                lines.append("")
            lines.append("Атрибутированные, но не подтверждённые как факты записи:")
            for fact in unverified:
                lines.append(
                    f"- [{ModelFreeCore._single_line(fact.fact_id)}] "
                    f"(источник: {ModelFreeCore._single_line(fact.source)}) "
                    f"{ModelFreeCore._single_line(fact.claim)}"
                )
        if conflicts:
            lines.append(f"⚠️ Известные локальные противоречия: {len(conflicts)}.")
        return "\n".join(lines)

    @staticmethod
    def _single_line(value: object) -> str:
        """Render an evidence field without allowing line/heading injection."""
        return r"\n".join(str(value).splitlines())

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
    "ModelFreeGraphReadError",
    "L2Query",
    "L2Relation",
    "L2Result",
    "ModelFreeCore",
]
