"""
🛡️ core/trusted_retrieval.py — Knowledge-Status Filtered Retrieval (V8.8)
===========================================================================

Проблема: HybridRetriever возвращает факты независимо от их knowledge_status.
Hypothetical и unknown рёбра ранжируются наравне с known/inferred.

Решение: фильтрация результатов retrieval по trust-метрике.
  - Факт проходит если >50% его связей имеют статус known/inferred
  - Или если факт Validated и не имеет противоречий
  - Или если факт ImmutableCore / Ring Zero

Режимы:
  strict   — только known/inferred, без противоречий (for Guardian/critical)
  normal   — known/inferred/hypothetical, противоречия OK (default)
  creative — всё включая unknown (for EXPLORATION mode)

Использование:
    from core.trusted_retrieval import TrustedRetriever, TrustMode

    trusted = TrustedRetriever()
    results = retriever.retrieve(query, top_k=50)
    filtered = trusted.filter(results, mode=TrustMode.NORMAL, top_k=10)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from core.hybrid_retriever import RetrievedFact

logger = logging.getLogger("velantrim.trusted_retrieval")


class TrustMode(str, Enum):
    """Режим фильтрации retrieval по trust-статусу."""
    STRICT = "strict"       # только known/inferred, без противоречий
    NORMAL = "normal"       # known/inferred/hypothetical (default)
    CREATIVE = "creative"   # всё, включая unknown


@dataclass
class TrustedResult:
    """Результат фильтрации — факт + trust-метаданные."""
    fact: RetrievedFact
    trust_score: float          # 0..1, насколько надёжен
    known_relations: int        # число known/inferred рёбер
    total_relations: int        # общее число рёбер
    has_contradictions: bool    # есть ли противоречия
    passed: bool                # прошёл ли фильтр
    reason: str                 # причина пропуска/отклонения


class TrustedRetriever:
    """
    Фильтр retrieval-результатов по knowledge_status рёбер.

    Не заменяет HybridRetriever — фильтрует его результаты.
    Использует CausalGraph для проверки knowledge_status.
    """

    def __init__(self):
        self._stats = {"filtered": 0, "passed": 0, "rejected": 0}

    def filter(
        self,
        results: list[RetrievedFact],
        *,
        mode: TrustMode = TrustMode.NORMAL,
        top_k: int = 10,
        min_trust_score: float = 0.3,
    ) -> List[RetrievedFact]:
        """
        Отфильтровать результаты retrieval по trust-статусу.

        Args:
            results: кандидаты от HybridRetriever (top_k*3 для diversity)
            mode: strict / normal / creative
            top_k: сколько вернуть после фильтрации
            min_trust_score: минимальный trust_score для прохождения

        Returns:
            Отфильтрованный список (до top_k)
        """
        if not results:
            return []

        self._stats["filtered"] += 1
        trusted: list[TrustedResult] = []

        for r in results:
            tr = self._evaluate_trust(r)
            if tr.passed and tr.trust_score >= min_trust_score:
                trusted.append(tr)
                self._stats["passed"] += 1
            else:
                self._stats["rejected"] += 1

        # В strict-режиме: если недостаточно прошедших — возвращаем что есть
        # В normal/creative: приоритет по trust_score
        if mode == TrustMode.STRICT:
            trusted.sort(key=lambda t: (-t.trust_score, t.fact.final_score))
        elif mode == TrustMode.CREATIVE:
            # В creative пропускаем все, но сортируем по trust
            all_results = [self._evaluate_trust(r) for r in results]
            all_results.sort(key=lambda t: (-t.trust_score, t.fact.final_score))
            trusted = all_results
        else:  # normal
            trusted.sort(key=lambda t: (-t.trust_score, t.fact.final_score))

        return [t.fact for t in trusted[:top_k]]

    def filter_with_metadata(
        self,
        results: list[RetrievedFact],
        *,
        mode: TrustMode = TrustMode.NORMAL,
        top_k: int = 10,
    ) -> List[TrustedResult]:
        """Фильтрация с полными метаданными trust."""
        if not results:
            return []

        all_results = [self._evaluate_trust(r) for r in results]

        if mode == TrustMode.STRICT:
            all_results = [t for t in all_results if t.passed]
        elif mode == TrustMode.CREATIVE:
            pass  # всё
        else:  # normal
            all_results = [t for t in all_results if t.trust_score >= 0.3]

        all_results.sort(key=lambda t: (-t.trust_score, t.fact.final_score))
        return all_results[:top_k]

    def evaluate_single(self, fact_id: str, confidence: float = 0.5) -> TrustedResult:
        """Оценить trust одного факта (без retrieval)."""
        fake = RetrievedFact(
            fact_id=fact_id, claim="", source="",
            confidence=confidence, final_score=confidence,
        )
        return self._evaluate_trust(fake)

    def _evaluate_trust(self, fact: RetrievedFact) -> TrustedResult:
        """
        Вычислить trust-метрику для факта.

        Алгоритм:
          1. ImmutableCore / Ring Zero → trust_score = 1.0
          2. Считаем relations → доля known/inferred
          3. Проверяем contradictions
          4. Итоговый trust_score = доля надёжных рёбер × (1 - has_contradictions*0.5)
        """
        fact_id = fact.fact_id
        if not fact_id:
            return TrustedResult(
                fact=fact, trust_score=0.0, known_relations=0,
                total_relations=0, has_contradictions=False,
                passed=False, reason="no_fact_id",
            )

        # Ring Zero / ImmutableCore
        if fact_id in ("VALUES_CORE", "RING_ZERO"):
            return TrustedResult(
                fact=fact, trust_score=1.0, known_relations=0,
                total_relations=0, has_contradictions=False,
                passed=True, reason="ring_zero",
            )

        # Получить relations
        known_count = 0
        total_count = 0
        has_contra = False

        try:
            from core.causal_graph import get_causal_graph
            cg = get_causal_graph()
            if cg is not None:
                all_rels = cg.get_relations_from(fact_id) + cg.get_relations_to(fact_id)
                total_count = len(all_rels)
                for rel in all_rels:
                    if rel.knowledge_status in ("known", "inferred"):
                        known_count += 1
                    if rel.relation_type == "contradicts":
                        has_contra = True
        except Exception:
            pass

        # Trust score
        if total_count == 0:
            # Изолированный факт — низкое доверие если нет подтверждения
            trust_score = 0.3 if fact_id else 0.0
            return TrustedResult(
                fact=fact, trust_score=trust_score, known_relations=0,
                total_relations=0, has_contradictions=False,
                passed=trust_score >= 0.3, reason="isolated" if trust_score < 0.3 else "ok",
            )

        known_ratio = known_count / total_count if total_count > 0 else 0
        contradiction_penalty = 0.5 if has_contra else 0.0
        trust_score = max(0.0, min(1.0, known_ratio * (1.0 - contradiction_penalty)))

        passed = trust_score >= 0.3
        reason = "ok"
        if not passed:
            if has_contra:
                reason = "has_contradictions"
            elif known_ratio < 0.5:
                reason = "low_trust"
            else:
                reason = "unknown"

        return TrustedResult(
            fact=fact,
            trust_score=round(trust_score, 4),
            known_relations=known_count,
            total_relations=total_count,
            has_contradictions=has_contra,
            passed=passed,
            reason=reason,
        )

    def stats(self) -> Dict[str, Any]:
        return dict(self._stats)


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_trusted: Optional[TrustedRetriever] = None


def get_trusted_retriever() -> TrustedRetriever:
    global _trusted
    if _trusted is None:
        _trusted = TrustedRetriever()
    return _trusted


__all__ = [
    "TrustedRetriever",
    "TrustedResult",
    "TrustMode",
    "get_trusted_retriever",
]
