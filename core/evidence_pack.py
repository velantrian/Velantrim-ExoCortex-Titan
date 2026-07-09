"""
📦 core/evidence_pack.py — Evidence Pack (V8.8, Codex audit)
==============================================================

Каждый retrieval-ответ должен возвращать не просто список фактов,
а evidence pack: факты + score breakdown + provenance + graph context.

Контракт (Codex audit):
  final_score = rrf(bm25, dense, graph) * truth_state_weight
               * source_trust * freshness * domain_match * contradiction_penalty

Использование:
    packer = EvidencePacker()
    evidence = packer.pack(facts=retrieved_facts, query="...", query_type="causal")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.hybrid_retriever import RetrievedFact

logger = logging.getLogger("velantrim.evidence_pack")

SOURCE_TRUST: dict[str, float] = {
    "manual": 1.00, "physics": 0.95, "chemistry": 0.95, "mathematics": 0.95,
    "biology": 0.90, "medicine": 0.85, "astronomy": 0.90, "engineering": 0.85,
    "peer_reviewed": 0.95, "textbook": 0.90, "encyclopedia": 0.85,
    "wikipedia": 0.70, "web": 0.50, "llm_output": 0.40, "inferred": 0.35, "unknown": 0.30,
}

TRUTH_STATE_WEIGHT: dict[str, float] = {
    "ImmutableCore": 1.00, "Validated": 0.95, "Supported": 0.70,
    "Hypothesized": 0.40, "Observed": 0.25, "Contradicted": 0.05,
    "Deprecated": 0.02, "Collapsed": 0.00,
}

FRESHNESS_HALF_LIFE_DAYS = 180


@dataclass
class EvidenceItem:
    """Один элемент evidence pack — факт + полный контекст."""
    fact_id: str
    claim: str
    source: str
    confidence: float
    epistemic_state: str
    bm25_score: float = 0.0
    dense_score: float = 0.0
    rrf_score: float = 0.0
    graph_score: float = 0.0
    truth_weight: float = 1.0
    source_trust: float = 0.5
    freshness: float = 1.0
    contradiction_penalty: float = 0.0
    final_score: float = 0.0
    relations: list[dict] = field(default_factory=list)
    graph_path: Optional[str] = None
    created_at: str = ""
    evidence_ref: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "claim": self.claim[:200],
            "source": self.source,
            "confidence": self.confidence,
            "epistemic_state": self.epistemic_state,
            "score_breakdown": {
                "bm25": round(self.bm25_score, 4),
                "dense": round(self.dense_score, 4),
                "rrf": round(self.rrf_score, 4),
                "graph": round(self.graph_score, 4),
                "truth_weight": round(self.truth_weight, 4),
                "source_trust": round(self.source_trust, 4),
                "freshness": round(self.freshness, 4),
                "contradiction_penalty": round(self.contradiction_penalty, 4),
                "final": round(self.final_score, 4),
            },
            "relations": self.relations[:5],
            "graph_path": self.graph_path,
            "created_at": self.created_at,
        }


@dataclass
class EvidencePack:
    """Полный evidence pack для ответа."""
    query: str
    query_type: str = "unknown"
    facts: List[EvidenceItem] = field(default_factory=list)
    total_candidates: int = 0
    filtered_out: int = 0
    compute_time_ms: float = 0.0
    strategy: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "query_type": self.query_type,
            "facts": [f.to_dict() for f in self.facts],
            "total_candidates": self.total_candidates,
            "filtered_out": self.filtered_out,
            "summary": f"{len(self.facts)} from {self.total_candidates}",
        }

    def to_llm_context(self) -> str:
        lines = [f"=== EVIDENCE ({len(self.facts)} facts) ==="]
        for f in self.facts:
            trust = "G" if f.epistemic_state in ("Validated", "ImmutableCore") else \
                    "Y" if f.epistemic_state in ("Supported", "Hypothesized") else "R"
            lines.append(
                f"[{f.fact_id}] {trust} {f.claim[:150]} "
                f"(src={f.source}, conf={f.confidence:.2f}, score={f.final_score:.2f})"
            )
        return "\n".join(lines)


class EvidencePacker:
    """Сборщик evidence pack с полным score breakdown."""

    def pack(
        self,
        facts: List[RetrievedFact],
        query: str,
        query_type: str = "unknown",
        *,
        total_candidates: int = 0,
        strategy: Dict[str, Any] | None = None,
    ) -> EvidencePack:
        items: List[EvidenceItem] = []
        for fact in facts:
            items.append(self._enrich(fact))
        return EvidencePack(
            query=query, query_type=query_type, facts=items,
            total_candidates=total_candidates,
            filtered_out=max(0, total_candidates - len(items)),
            strategy=strategy or {},
        )

    def _enrich(self, fact: RetrievedFact) -> EvidenceItem:
        state = fact.metadata.get("epistemic_state", "Observed") if fact.metadata else "Observed"
        source = fact.source or "unknown"
        created = (fact.metadata or {}).get("created_at", "")

        source_key = source.lower().split("/")[0].split(":")[-1]
        source_trust = SOURCE_TRUST.get(source_key, 0.5)
        truth_weight = TRUTH_STATE_WEIGHT.get(state, 0.25)
        freshness = self._freshness(created)

        contra_penalty = 0.0
        try:
            from core.causal_graph import get_causal_graph
            cg = get_causal_graph()
            if cg is not None and cg.find_contradictions(fact.fact_id):
                contra_penalty = 0.3
        except Exception:
            pass

        relations: list[dict] = []
        graph_score = 0.0
        try:
            from core.causal_graph import get_causal_graph
            cg = get_causal_graph()
            if cg is not None:
                rels = cg.get_relations_from(fact.fact_id, min_confidence=0.3)
                relations = [
                    {"to": r.to_fact_id, "type": r.relation_type, "conf": r.confidence}
                    for r in rels[:5]
                ]
                graph_score = min(0.3, len(rels) * 0.03)
        except Exception:
            pass

        graph_path = None
        if relations:
            parts = [f"[{r['type']}]" for r in relations[:3]]
            graph_path = " ".join(parts)

        final_score = (
            fact.final_score * truth_weight * source_trust * freshness
            * (1.0 - contra_penalty) + graph_score
        )
        final_score = max(0.0, min(1.0, final_score))

        return EvidenceItem(
            fact_id=fact.fact_id, claim=fact.claim, source=source,
            confidence=fact.confidence, epistemic_state=state,
            bm25_score=fact.bm25_score, dense_score=fact.dense_score,
            rrf_score=fact.rrf_score, graph_score=round(graph_score, 4),
            truth_weight=truth_weight, source_trust=source_trust,
            freshness=round(freshness, 4), contradiction_penalty=contra_penalty,
            final_score=round(final_score, 4), relations=relations,
            graph_path=graph_path, created_at=created,
        )

    @staticmethod
    def _freshness(created_at: str) -> float:
        if not created_at:
            return 0.5
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - created).total_seconds() / 86400
            return 2.0 ** (-age_days / FRESHNESS_HALF_LIFE_DAYS)
        except (ValueError, TypeError):
            return 0.5


_packer: Optional[EvidencePacker] = None


def get_evidence_packer() -> EvidencePacker:
    global _packer
    if _packer is None:
        _packer = EvidencePacker()
    return _packer


__all__ = ["EvidencePacker", "EvidencePack", "EvidenceItem", "get_evidence_packer"]
