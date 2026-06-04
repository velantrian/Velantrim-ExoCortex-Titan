"""
NoeticCore - essence, causality, prediction, and uncertainty contract.

NoeticCore does not create truth. It reads FactsPack-like facts and relation
metadata, then returns marked statements: facts, inferences, predictions,
hypotheses, and unknowns. Predictions are never promoted to facts here.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum


class StatementType(str, Enum):
    FACT = "fact"
    INFERENCE = "inference"
    PREDICTION = "prediction"
    HYPOTHESIS = "hypothesis"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class NoeticStatement:
    statement: str
    kind: StatementType
    confidence: float = 0.0
    basis: list[str] = field(default_factory=list)
    uncertainty: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "statement": self.statement,
            "kind": self.kind.value,
            "confidence": round(self.confidence, 4),
            "basis": list(self.basis),
            "uncertainty": list(self.uncertainty),
        }


@dataclass(frozen=True)
class NoeticResult:
    query: str
    essence: str
    causal_chain: list[str]
    predictions: list[NoeticStatement]
    uncertainties: list[str]
    salience: list[str]
    affordances: list[str]
    guardrail: str = "Predictions are hypotheses, not facts."

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "essence": self.essence,
            "causal_chain": list(self.causal_chain),
            "predictions": [p.to_dict() for p in self.predictions],
            "uncertainties": list(self.uncertainties),
            "salience": list(self.salience),
            "affordances": list(self.affordances),
            "guardrail": self.guardrail,
        }


_CAUSAL_TYPES = {
    "causes",
    "enables",
    "prevents",
    "requires",
    "implies",
    "becomes",
}


def _fact_id(fact: dict) -> str:
    return str(fact.get("fact_id") or fact.get("id") or "")


def _claim(fact: dict) -> str:
    return str(fact.get("claim") or "").strip()


def _confidence(item: dict, default: float = 0.5) -> float:
    try:
        return max(0.0, min(1.0, float(item.get("confidence", default))))
    except (TypeError, ValueError):
        return default


class NoeticCore:
    """Build a small causal-essence view from retrieved facts."""

    def analyze(
        self,
        query: str,
        facts: Iterable[dict],
        relations: Iterable[dict] | None = None,
        *,
        max_predictions: int = 5,
    ) -> NoeticResult:
        fact_list = list(facts)
        relation_list = list(relations or [])
        fact_by_id = {_fact_id(f): f for f in fact_list if _fact_id(f)}

        uncertainties: list[str] = []
        if not fact_list:
            uncertainties.append("no_facts_available")
        if not relation_list:
            uncertainties.append("no_relations_available")

        essence = self._essence(fact_list)
        causal_chain = self._causal_chain(relation_list, fact_by_id)
        predictions = self._predictions(relation_list, fact_by_id, max_predictions)
        salience = self._salience(fact_list)
        affordances = self._affordances(fact_list)

        if not predictions:
            uncertainties.append("no_prediction_basis")

        return NoeticResult(
            query=query,
            essence=essence,
            causal_chain=causal_chain,
            predictions=predictions,
            uncertainties=list(dict.fromkeys(uncertainties)),
            salience=salience,
            affordances=affordances,
        )

    @staticmethod
    def _essence(facts: list[dict]) -> str:
        usable = [_claim(f) for f in facts if _claim(f)]
        if not usable:
            return "No grounded essence can be extracted without facts."
        top = usable[:3]
        if len(top) == 1:
            return top[0]
        return " | ".join(top)

    @staticmethod
    def _causal_chain(relations: list[dict], fact_by_id: dict[str, dict]) -> list[str]:
        chain: list[str] = []
        for rel in relations:
            rtype = str(rel.get("relation_type") or rel.get("type") or "")
            if rtype not in _CAUSAL_TYPES:
                continue
            src = str(rel.get("from_fact_id") or rel.get("from") or "")
            dst = str(rel.get("to_fact_id") or rel.get("to") or "")
            src_label = _claim(fact_by_id.get(src, {})) or src
            dst_label = _claim(fact_by_id.get(dst, {})) or dst
            if src_label and dst_label:
                chain.append(f"{src_label} --{rtype}--> {dst_label}")
        return chain[:8]

    @staticmethod
    def _predictions(
        relations: list[dict],
        fact_by_id: dict[str, dict],
        max_predictions: int,
    ) -> list[NoeticStatement]:
        out: list[NoeticStatement] = []
        for rel in relations:
            rtype = str(rel.get("relation_type") or rel.get("type") or "")
            if rtype not in {"causes", "enables", "prevents", "implies"}:
                continue
            src = str(rel.get("from_fact_id") or rel.get("from") or "")
            dst = str(rel.get("to_fact_id") or rel.get("to") or "")
            src_claim = _claim(fact_by_id.get(src, {})) or src
            dst_claim = _claim(fact_by_id.get(dst, {})) or dst
            if not src_claim or not dst_claim:
                continue
            conf = min(_confidence(rel), _confidence(fact_by_id.get(src, {}), 0.5))
            out.append(NoeticStatement(
                statement=f"If '{src_claim}' holds, then '{dst_claim}' may follow via {rtype}.",
                kind=StatementType.PREDICTION,
                confidence=round(conf, 4),
                basis=[x for x in (src, dst) if x],
                uncertainty=["prediction_requires_review"],
            ))
            if len(out) >= max_predictions:
                break
        return out

    @staticmethod
    def _salience(facts: list[dict]) -> list[str]:
        scored = []
        for f in facts:
            claim = _claim(f)
            if not claim:
                continue
            score = _confidence(f) + float(f.get("salience", 0.0) or 0.0)
            scored.append((score, claim))
        scored.sort(reverse=True)
        return [claim for _, claim in scored[:5]]

    @staticmethod
    def _affordances(facts: list[dict]) -> list[str]:
        out: list[str] = []
        for f in facts:
            living = f.get("living_context") or {}
            if isinstance(living, dict):
                for item in living.get("how", []) or living.get("affordances", []) or []:
                    if isinstance(item, str) and item not in out:
                        out.append(item)
        return out[:8]


def analyze_noetic(
    query: str,
    facts: Iterable[dict],
    relations: Iterable[dict] | None = None,
) -> NoeticResult:
    return NoeticCore().analyze(query, facts, relations)


__all__ = [
    "NoeticCore",
    "NoeticResult",
    "NoeticStatement",
    "StatementType",
    "analyze_noetic",
]
