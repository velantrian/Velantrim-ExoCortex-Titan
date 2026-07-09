"""
📚 core/multi_index_retriever.py — Multi-Index Domain-Aware Retrieval (V8.8)
=============================================================================

Проблема: HybridRetriever держит ВСЕ 19 000+ фактов в одном индексе.
Каждый запрос → линейный проход по всей базе. Domain-specific запрос
про «термодинамику» сканирует и биологию, и лингвистику.

Решение: разделить индексы по доменам.
  - Для domain-specific запросов → только релевантный индекс (10x быстрее)
  - Для кросс-доменных → глобальный индекс
  - Порог: домен должен иметь >100 фактов чтобы получить свой индекс

Использование:
    facts = store.get_all_facts()
    retriever = MultiIndexRetriever(facts)
    results = retriever.retrieve("термодинамика цикл Карно", top_k=10, domain="phys")
    # → только phys-индекс (900 фактов вместо 19 000)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Optional

from core.hybrid_retriever import HybridRetriever, RetrievedFact

logger = logging.getLogger(__name__)

MIN_FACTS_FOR_DOMAIN_INDEX = 100  # меньше → не заводим отдельный индекс
MAX_DOMAIN_INDEXES = 20  # защита от взрыва индексов


def _extract_domain(fact_id: str) -> str:
    """Первый сегмент ID: agro.crop.wheat → agro."""
    if not fact_id:
        return "unknown"
    return fact_id.split(".")[0].lower()


def _extract_domains(facts: list[dict]) -> list[str]:
    """Все домены с >MIN_FACTS_FOR_DOMAIN_INDEX фактами."""
    counts: dict[str, int] = defaultdict(int)
    for f in facts:
        dom = _extract_domain(str(f.get("fact_id", "")))
        counts[dom] += 1

    # Топ-N доменов по размеру
    return sorted(
        [d for d, c in counts.items() if c >= MIN_FACTS_FOR_DOMAIN_INDEX],
        key=lambda d: -counts[d],
    )[:MAX_DOMAIN_INDEXES]


class MultiIndexRetriever:
    """
    Domain-aware retrieval с раздельными индексами.

    Стратегия:
      - Если передан domain И для него есть индекс → быстрый путь
      - Если доменов несколько → склеиваем результаты нескольких индексов через RRF
      - Иначе → глобальный индекс (как раньше)
    """

    def __init__(
        self,
        facts: list[dict],
        *,
        embedding_model: str | None = None,
        use_reranker: bool = False,
    ) -> None:
        self._facts = facts
        self._global = HybridRetriever(facts, use_reranker=use_reranker)

        domains = _extract_domains(facts)
        self._by_domain: dict[str, HybridRetriever] = {}
        self._domain_fact_ids: dict[str, set[str]] = {}

        for domain in domains:
            domain_facts = [
                f for f in facts
                if _extract_domain(str(f.get("fact_id", ""))) == domain
            ]
            if len(domain_facts) >= MIN_FACTS_FOR_DOMAIN_INDEX:
                self._by_domain[domain] = HybridRetriever(
                    domain_facts, use_reranker=use_reranker,
                )
                self._domain_fact_ids[domain] = {
                    str(f["fact_id"]) for f in domain_facts
                }

        logger.info(
            "MultiIndexRetriever: %d доменных индексов (%s) + 1 глобальный (%d фактов)",
            len(self._by_domain),
            ", ".join(sorted(self._by_domain.keys())),
            len(facts),
        )

    @property
    def domains(self) -> list[str]:
        return sorted(self._by_domain.keys())

    def domain_stats(self) -> dict[str, int]:
        return {
            d: len(facts)
            for d, facts in self._domain_fact_ids.items()
        }

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        *,
        domain: str | list[str] | None = None,
    ) -> list[RetrievedFact]:
        """
        Доменно-осознанный retrieval.

        Args:
            query: текст запроса
            top_k: число результатов
            domain: None → глобальный; "phys" → phys-индекс;
                    ["phys", "chem"] → склеить phys + chem через RRF

        Returns:
            Список RetrievedFact
        """
        if not self._facts:
            return []

        # Нормализовать domain
        domains: list[str] = []
        if isinstance(domain, str):
            domains = [domain.lower()]
        elif isinstance(domain, list):
            domains = [d.lower() for d in domain]

        # Найти доступные индексы
        available = [d for d in domains if d in self._by_domain]

        if available:
            return self._retrieve_multi_domain(query, top_k, available)

        # Если домен указан но индекса нет → глобальный
        return self._global.retrieve(query, top_k=top_k)

    def _retrieve_multi_domain(
        self, query: str, top_k: int, domains: list[str],
    ) -> list[RetrievedFact]:
        """Склеить результаты нескольких доменных индексов."""
        # Собрать результаты из каждого домена
        per_domain: list[list[RetrievedFact]] = []
        k_per_domain = max(5, top_k // len(domains))

        for d in domains:
            if d in self._by_domain:
                results = self._by_domain[d].retrieve(query, top_k=k_per_domain * 2)
                per_domain.append(results)

        if not per_domain:
            return self._global.retrieve(query, top_k=top_k)

        # Ручной RRF-fusion между доменами
        if len(per_domain) == 1:
            return per_domain[0][:top_k]

        # RRF: склеиваем по fact_id
        rrf_scores: dict[str, float] = {}
        rrf_k = 60.0
        for domain_results in per_domain:
            for rank, r in enumerate(domain_results, start=1):
                fid = r.fact_id
                rrf_scores[fid] = rrf_scores.get(fid, 0.0) + 1.0 / (rrf_k + rank)

        # Сортировать по RRF
        all_facts: dict[str, RetrievedFact] = {}
        for domain_results in per_domain:
            for r in domain_results:
                if r.fact_id not in all_facts:
                    all_facts[r.fact_id] = r

        sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)
        result = []
        for fid in sorted_ids[:top_k]:
            if fid in all_facts:
                all_facts[fid].rrf_score = rrf_scores[fid]
                all_facts[fid].final_score = rrf_scores[fid]
                result.append(all_facts[fid])

        return result

    def retrieve_5stage(
        self,
        query: str,
        top_k: int = 10,
        *,
        ego_depth: int = 2,
        use_ego: bool = True,
        domain: str | list[str] | None = None,
    ) -> list[RetrievedFact]:
        """5-stage retrieval с domain-awareness."""
        if domain and isinstance(domain, str) and domain in self._by_domain:
            return self._by_domain[domain].retrieve_5stage(
                query, top_k, ego_depth=ego_depth, use_ego=use_ego,
            )
        return self._global.retrieve_5stage(
            query, top_k, ego_depth=ego_depth, use_ego=use_ego,
        )


def build_multi_index(facts: list[dict]) -> MultiIndexRetriever:
    """Фабрика: создать MultiIndexRetriever из списка фактов."""
    return MultiIndexRetriever(facts)


__all__ = [
    "MultiIndexRetriever",
    "build_multi_index",
    "_extract_domain",
]
