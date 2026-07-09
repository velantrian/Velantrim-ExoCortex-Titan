# core/causal_retrieval.py
# Velantrim ExoCortex — Causal Subgraph Retrieval (R51)
# v8.6 transfer pack from v8.17.9
#
# Источник идеи: ChatGPT Design Review + Pavlyshyn 2026 (context graph + causal graph)
#   «Похоже» ≠ «причинно связано»
#   Кофе связан с бодростью, но не всегда является причиной продуктивности.
#
# Принцип:
#   • Для WHY-запросов разрешено: CAUSES, ENABLES, PREVENTS, REQUIRES, LEADS_TO
#   • Запрещено доказательство через: ANALOGOUS_TO, SIMILAR_TO, SUPPORTS_NUMERICALLY
#
# Это расширение R40 MAGMA Traversal Policy: добавляем CAUSAL query type
# с строгой semantic boundary.
#
# Use case:
#   • Медицина: «почему пациент в коме?» — нужны CAUSES, не похожесть симптомов
#   • Право: «почему этот контракт нарушен?» — нужны DEPENDS_ON / CAUSES
#   • Наука: «что вызывает X?» — нужны CAUSES, ENABLES — НЕ ANALOGOUS_TO
#
# Инварианты:
#   CR-01: CAUSAL retrieval НИКОГДА не возвращает факты только по ANALOGOUS_TO
#   CR-02: CAUSAL результаты включают metadata.evidence_kind = "causal"
#   CR-03: Если ни одного causal-ребра не найдено — возвращает пустой список
#          (лучше "не знаю" чем "вот похожее, может быть причина")

from __future__ import annotations

import re
from typing import Any

# Все 13 типов рёбер из RELATION_KINDS
CAUSAL_KINDS: set[str] = {
    "CAUSES",        # X вызывает Y
    "ENABLES",       # X делает Y возможным
    "DEPENDS_ON",    # X зависит от Y (Y — причина возможности X)
    "TEMPORAL_SEQUENCE",  # X предшествует Y во времени
}

# НЕЛЬЗЯ использовать как доказательство причинности
FORBIDDEN_FOR_CAUSAL: set[str] = {
    "ANALOGOUS_TO",  # структурное сходство ≠ причинность
    "SUPPORTS",      # X подтверждает Y семантически ≠ причинно
    "GENERALIZES",
    "SPECIALIZES",
    "PART_OF",
    "INSTANTIATES",
    "ABSTRACTS_FROM",
}


def is_causal_query(query: str) -> bool:
    """
    Определить является ли запрос причинным (WHY-вопрос).
    Возвращает True если запрос ищет CAUSAL evidence.
    """
    q = query.lower().strip()

    # Английские маркеры
    en_markers = [
        "why ", "why?", "what causes", "what caused",
        "what leads to", "what triggers", "reason for",
        "cause of", "because of", "due to",
    ]
    # Немецкие
    de_markers = [
        "warum", "wieso", "weshalb",
        "was verursacht", "was führt zu",
        "ursache von", "grund für",
    ]
    # Русские
    ru_markers = [
        "почему", "зачем", "из-за чего",
        "что вызывает", "что приводит к",
        "причина ", "причина чего", "по какой причине",
    ]

    return any(m in q for m in en_markers + de_markers + ru_markers)


def filter_causal_edges(
    relations: list[Any],
    strict: bool = True,
) -> list[Any]:
    """
    Отфильтровать список рёбер, оставив только causal.

    Args:
      strict=True: только CAUSAL_KINDS
      strict=False: всё кроме FORBIDDEN_FOR_CAUSAL (для weak causal evidence)
    """
    def _kind(rel: Any) -> str:
        value = getattr(rel, "kind", None) or getattr(rel, "relation_type", "")
        return str(value).upper()

    if strict:
        return [r for r in relations if _kind(r) in CAUSAL_KINDS]
    return [r for r in relations if _kind(r) not in FORBIDDEN_FOR_CAUSAL]


def _retrieve_candidates(query: str, store: Any, top_k: int) -> list[dict[str, Any]]:
    """Use V8.6 store.search when available; fall back to a tiny token scorer."""
    if hasattr(store, "search"):
        try:
            rows = store.search(query, limit=top_k)
        except TypeError:
            rows = store.search(query, k=top_k)
        candidates = []
        for row in rows:
            item = dict(row)
            item["retrieval_score"] = float(
                item.get("retrieval_score") or item.get("_search_score") or 0.0
            )
            candidates.append(item)
        if candidates:
            return candidates

    terms = [
        re.sub(r"[^\w]", "", t)
        for t in query.lower().split()
        if len(re.sub(r"[^\w]", "", t)) > 2
    ]
    candidates = []
    for fact in store.get_all_facts():
        claim = str(fact.get("claim", "")).lower()
        score = sum(1 for term in terms if term in claim)
        if score:
            item = dict(fact)
            item["retrieval_score"] = float(score)
            candidates.append(item)
    candidates.sort(key=lambda item: item["retrieval_score"], reverse=True)
    return candidates[:top_k]


def _relations_for(rel_store: Any, fact_id: str) -> tuple[list[Any], list[Any]]:
    """Support the new RelationStore API without touching V8.6 CausalGraph."""
    outgoing = rel_store.outgoing(fact_id) if hasattr(rel_store, "outgoing") else []
    incoming = rel_store.incoming(fact_id) if hasattr(rel_store, "incoming") else []
    return outgoing, incoming


def causal_retrieve(
    query:       str,
    store,
    rel_store,
    top_k:       int = 5,
    strict:      bool = True,
) -> list[dict[str, Any]]:
    """
    R51: Causal subgraph retrieval.

    Возвращает только факты подключенные через CAUSAL_KINDS рёбра.
    Если ни одного — возвращает пустой список (CR-03 — лучше «не знаю»).

    Использование:
        if is_causal_query(query):
            facts = causal_retrieve(query, store, rel_store)
        else:
            facts = retrieve_hybrid(query, store.get_all_facts(), rel_store, k=top_k)
    """
    # 1. Сначала обычный hybrid retrieval как pre-filter
    candidates = _retrieve_candidates(query, store, top_k * 3)

    if not candidates:
        return []

    # 2. Из кандидатов оставляем только те, у которых есть causal-связи
    {f.get("fact_id") for f in candidates}
    causal_facts = []

    for fact in candidates:
        fid = fact.get("fact_id")
        if fid is None:
            continue
        outgoing, incoming = _relations_for(rel_store, fid)

        # Есть ли хотя бы одно causal ребро?
        causal_out = filter_causal_edges(outgoing, strict=strict)
        causal_in  = filter_causal_edges(incoming, strict=strict)

        if causal_out or causal_in:
            fact_copy = dict(fact)
            fact_copy["evidence_kind"] = "causal"  # CR-02
            fact_copy["causal_edges_count"] = len(causal_out) + len(causal_in)
            causal_facts.append(fact_copy)

    # 3. Сортируем по числу causal-связей и retrieval score
    causal_facts.sort(
        key=lambda f: (
            f.get("causal_edges_count", 0),
            f.get("retrieval_score", 0.0),
        ),
        reverse=True,
    )

    return causal_facts[:top_k]


def explain_causal_decision(
    query:    str,
    results:  list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Объяснить почему именно эти факты были выбраны как causal evidence.
    Для GDPR Article 22 reasoning trace.
    """
    return {
        "query":             query,
        "is_causal":         is_causal_query(query),
        "policy":            "CAUSAL — strict causal-edge filter (R51)",
        "allowed_edges":     sorted(CAUSAL_KINDS),
        "forbidden_edges":   sorted(FORBIDDEN_FOR_CAUSAL),
        "result_count":      len(results),
        "facts": [
            {
                "fact_id":          f.get("fact_id"),
                "causal_edges":     f.get("causal_edges_count", 0),
                "retrieval_score":  f.get("retrieval_score", 0.0),
            }
            for f in results
        ],
        "principle": (
            "Velantrim does not infer causation from similarity. "
            "If no causal edges exist, the answer is 'I don't know' "
            "rather than 'here is something similar'."
        ),
    }
