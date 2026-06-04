"""
📊 core/evidence_counter.py — Evidence Counter (V8.7 Titan)

Убивает мёртвый код: поле evidence_count в TruthGate ВСЕГДА было 0,
потому что его никто не заполнял. Теперь заполняется.

Правила подсчёта:
  1. Каждый уникальный source = +1 evidence
  2. Каждое каузальное ребро К факту = +1
  3. Каждый факт того же домена с похожим claim = +1
  4. Каждый explicit reference в metadata = +1

Вызывается при store_fact() → обогащает metadata.evidence_count.

Инвариант: не меняет truth_status, не пишет в L3 напрямую.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.evidence_counter")


def _similar_claim(claim_a: str, claim_b: str, threshold: float = 0.6) -> bool:
    """Проверка схожести двух claim (jaccard по токенам, CPU-only)."""
    if not claim_a or not claim_b:
        return False
    toks_a = set(claim_a.lower().split())
    toks_b = set(claim_b.lower().split())
    if not toks_a or not toks_b:
        return False
    intersection = toks_a & toks_b
    union = toks_a | toks_b
    return len(intersection) / len(union) >= threshold


def count_evidence(
    fact: Dict[str, Any],
    all_facts: List[Dict[str, Any]],
    *,
    causal_relations: Optional[List[Dict[str, Any]]] = None,
) -> int:
    """
    Подсчитать evidence_count для одного факта.

    Args:
        fact: словарь факта (claim, source, fact_id, metadata).
        all_facts: ВСЕ факты в store.
        causal_relations: рёбра causal graph (опционально).

    Returns:
        evidence_count (int).
    """
    fact_id = fact.get("fact_id")
    source = fact.get("source", "")
    claim = fact.get("claim", "")
    metadata = fact.get("metadata", {})

    if isinstance(metadata, str):
        import json
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}

    evidence = 0

    # 1. Каждый уникальный source → +1
    unique_sources: set = set()
    for f in all_facts:
        if f.get("fact_id") == fact_id:
            continue
        s = f.get("source", "")
        if s and s == source:
            unique_sources.add(s)
    evidence += len(unique_sources)

    # 2. Каузальные рёбра → +1 за каждое
    if causal_relations:
        for rel in causal_relations:
            target = rel.get("target_fact_id") or rel.get("to_fact_id")
            if target == fact_id:
                evidence += 1

    # 3. Похожие claim в том же домене
    my_domain = metadata.get("domain", "")
    for f in all_facts:
        if f.get("fact_id") == fact_id:
            continue
        f_meta = f.get("metadata", {})
        if isinstance(f_meta, str):
            import json
            try:
                f_meta = json.loads(f_meta)
            except json.JSONDecodeError:
                f_meta = {}
        f_domain = f_meta.get("domain", "")
        if my_domain and f_domain == my_domain:
            if _similar_claim(claim, f.get("claim", "")):
                evidence += 1

    # 4. Explicit references в metadata
    refs = metadata.get("references", metadata.get("evidence", []))
    if isinstance(refs, list):
        evidence += len(refs)
    if metadata.get("source_url"):
        evidence += 1

    return evidence


def enrich_fact_with_evidence(
    fact: Dict[str, Any],
    all_facts: List[Dict[str, Any]],
    *,
    causal_relations: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Обогатить факт evidence_count и вернуть обновлённый словарь.
    """
    cnt = count_evidence(fact, all_facts, causal_relations=causal_relations)

    metadata = fact.get("metadata", {})
    if isinstance(metadata, str):
        import json
        metadata = json.loads(metadata)

    metadata["evidence_count"] = cnt
    metadata["evidence_counted_at"] = None  # заполнится при store

    from datetime import datetime, timezone
    metadata["evidence_counted_at"] = datetime.now(timezone.utc).isoformat()

    result = dict(fact)
    result["metadata"] = metadata
    return result


def batch_enrich(
    facts: List[Dict[str, Any]],
    all_facts: List[Dict[str, Any]],
    *,
    causal_relations: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Пакетное обогащение всех фактов evidence_count."""
    return [
        enrich_fact_with_evidence(f, all_facts, causal_relations=causal_relations)
        for f in facts
    ]


__all__ = [
    "count_evidence",
    "enrich_fact_with_evidence",
    "batch_enrich",
]
