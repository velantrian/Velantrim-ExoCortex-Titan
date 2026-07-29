"""
🧬 core/semantic_dedup.py — семантическая дедупликация → корроборация (P0)
=========================================================================

Цель: факты, означающие ОДНО И ТО ЖЕ разными словами
  «Вода кипит при 100°C»  ≈  «Boiling point of water is 100°C»
считать ОДНИМ концептом с НЕСКОЛЬКИМИ источниками. Это сразу даёт **корроборацию**
(рост доверия через независимые подтверждения) — по СМЫСЛУ, а не по дословному
совпадению, как лексический `promotion_policy.compute_corroboration`.

    дедуп по смыслу → evidence_count↑ → выше основания для Supported / Validated

Дисциплина:
  • аддитивно, за флагом `ENABLE_SEMANTIC_DEDUP` (по умолчанию ВЫКЛ);
  • НИКАКИХ мутаций стора здесь — возвращает кластеры / корроборацию / планы слияния (dry-run);
    реальное слияние (deprecate дублей + merged_into) — отдельный, более инвазивный шаг;
  • graceful: нет `sentence-transformers` → лексический фолбэк (нормализованный claim);
  • embed_fn инъектируется → детерминированно тестируется без загрузки модели.
"""
from __future__ import annotations

import json
import logging
import math
import os
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


# Порог косинуса для «один смысл». ЗАВИСИТ ОТ МОДЕЛИ/ЯЗЫКА — откалиброван по корпусу.
# Калибровка RU 2026-05-31 (scripts/calibrate_semantic_dedup.py, многоязычная модель):
#   «разные» пары в одном домене: p99=0.685, max=0.872 (mean 0.32) — хорошо отделены;
#   sweep: 0.90 → 5 кластеров, max размер 2 (нет цепочек). Англо-центричная
#   all-MiniLM-L6-v2 «сжимала» RU-сходство вверх → при 0.78 цепочки по 40+ (переслияние).
# 0.90 выше max «разных» пар → сливаются только настоящие парафразы. Env: SEMANTIC_DEDUP_THRESHOLD.
DEFAULT_THRESHOLD = _env_float("SEMANTIC_DEDUP_THRESHOLD", 0.90)
# Over-merge guard: компонент крупнее этого — артефакт (порог/транзитивность), НЕ сливаем.
_MAX_CLUSTER_SIZE = int(_env_float("SEMANTIC_DEDUP_MAX_CLUSTER", 8))
# Ранг ESM для выбора канонического факта в кластере (выше = каноничнее).
_ESM_RANK = {"Validated": 3, "Supported": 2, "Hypothesized": 1, "Observed": 0}

EmbedFn = Callable[[Sequence[str]], list[Sequence[float]]]


def is_semantic_dedup_enabled() -> bool:
    return os.getenv("ENABLE_SEMANTIC_DEDUP", "false").strip().lower() in {"1", "true", "yes", "on"}


def _normalize_claim(claim: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", (claim or "").lower())).strip()


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    s = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return s / (na * nb)


def default_embedder(model_name: str | None = None) -> EmbedFn | None:
    """
    claims → нормализованные векторы на sentence-transformers; None если пакет недоступен.
    Модель настраивается через env `SEMANTIC_DEDUP_MODEL`. Для русского/кросс-языка поставить
    многоязычную, напр.: SEMANTIC_DEDUP_MODEL=paraphrase-multilingual-MiniLM-L12-v2
    (тогда ru↔en сольются; MiniLM-L6 англо-центричен, ru↔en cosine ~0.22).
    """
    model_name = model_name or os.getenv(
        "SEMANTIC_DEDUP_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(model_name)

        def _embed(claims: Sequence[str]) -> list[Sequence[float]]:
            vecs = model.encode(list(claims), normalize_embeddings=True)
            return [list(map(float, v)) for v in vecs]

        return _embed
    except Exception:  # noqa: BLE001
        return None


# D4: выше этого размера блока пробуем приближённый поиск соседей (sklearn),
# иначе полное попарное сравнение внутри блока (точное, но O(B²)).
_ANN_BLOCK_LIMIT = 500
_ANN_K = 24


def _domain_of(f: dict[str, Any]) -> str:
    """Домен факта для блокировки сравнений (metadata.domain/content_domain)."""
    md = f.get("metadata") or {}
    if isinstance(md, str):
        try:
            md = json.loads(md)
        except (json.JSONDecodeError, TypeError):
            md = {}
    if not isinstance(md, dict):
        md = {}
    return str(md.get("domain") or md.get("content_domain") or f.get("domain") or "").strip().lower()


def _connected_components(positions: list[int], edges: list[tuple]) -> list[list[int]]:
    """Union-Find: рёбра (сходство ≥ порога) → связные компоненты. Детерминированно."""
    parent = {p: p for p in positions}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    comps: dict[int, list[int]] = {}
    for p in positions:
        comps.setdefault(find(p), []).append(p)
    return list(comps.values())


def _similar_pairs(positions: list[int], vecs: Sequence[Sequence[float]],
                   threshold: float) -> list[tuple]:
    """Пары позиций с cosine ≥ threshold. numpy-матрица (или ANN для больших блоков);
    при отсутствии numpy — чистый stdlib-фолбэк. Возвращает неориентированные рёбра."""
    m = len(positions)
    if m < 2:
        return []
    edges: list[tuple] = []
    try:
        import numpy as np

        V = np.asarray([list(vecs[p]) for p in positions], dtype=float)
        nrm = np.linalg.norm(V, axis=1, keepdims=True)
        nrm[nrm == 0] = 1.0
        Vn = V / nrm
        if m > _ANN_BLOCK_LIMIT:
            try:
                from sklearn.neighbors import NearestNeighbors

                k = min(_ANN_K, m)
                nn = NearestNeighbors(n_neighbors=k, metric="cosine").fit(Vn)
                dist, idx = nn.kneighbors(Vn)
                for a in range(m):
                    for b, d in zip(idx[a], dist[a]):
                        if b > a and (1.0 - float(d)) >= threshold:   # sim = 1 - cosine-distance
                            edges.append((positions[a], positions[b]))
                return edges
            except Exception:  # noqa: BLE001
                pass  # ANN недоступен/сбой → точное попарное ниже
        S = Vn @ Vn.T
        for a in range(m):
            row = S[a]
            for b in range(a + 1, m):
                if row[b] >= threshold:
                    edges.append((positions[a], positions[b]))
        return edges
    except Exception:  # noqa: BLE001 — нет numpy → чистый stdlib
        for a in range(m):
            for b in range(a + 1, m):
                if _cosine(vecs[positions[a]], vecs[positions[b]]) >= threshold:
                    edges.append((positions[a], positions[b]))
        return edges


def cluster_by_meaning(
    facts: Sequence[dict[str, Any]],
    threshold: float = DEFAULT_THRESHOLD,
    embed_fn: EmbedFn | None = None,
) -> list[list[int]]:
    """
    Сгруппировать индексы фактов по смыслу — ДЕТЕРМИНИРОВАННО (фикс audit M3).

    Алгоритм (D4): сортируем факты по fact_id → блокируем по домену (сужает сравнения)
    → внутри блока строим рёбра (cosine ≥ threshold) → связные компоненты (union-find).
    Связные компоненты решают проблему транзитивности (A≈B, B≈C ⇒ один кластер) и не
    зависят от порядка входа, в отличие от прежней жадной single-rep кластеризации.

    Без `embed_fn` → лексический фолбэк (равный нормализованный claim = один кластер).
    Пустые claim пропускаются. Для блоков > _ANN_BLOCK_LIMIT — sklearn-ANN (если есть),
    иначе точное попарное сравнение.
    """
    norm = [_normalize_claim(f.get("claim", "")) for f in facts]
    idxs = [i for i, n in enumerate(norm) if n]
    # детерминированный порядок: по fact_id, затем по индексу
    idxs.sort(key=lambda i: (str(facts[i].get("fact_id", "")), i))

    if embed_fn is None:
        groups: dict[str, list[int]] = {}
        for i in idxs:
            groups.setdefault(norm[i], []).append(i)
        return [sorted(v) for _, v in sorted(groups.items())]

    vecs = embed_fn([facts[i].get("claim", "") for i in idxs])

    # блокировка по домену: сравниваем только внутри одного домена (graceful: нет
    # домена → все в блоке "" → корректно, просто без выигрыша по скорости)
    blocks: dict[str, list[int]] = {}
    for pos, i in enumerate(idxs):
        blocks.setdefault(_domain_of(facts[i]), []).append(pos)

    clusters: list[list[int]] = []
    for dom in sorted(blocks):
        positions = blocks[dom]
        edges = _similar_pairs(positions, vecs, threshold)
        for comp in _connected_components(positions, edges):
            members = sorted(idxs[p] for p in comp)
            # OVER-MERGE GUARD (RU-калибровка): аномально большой компонент — почти всегда
            # артефакт низкого порога + транзитивности (цепочка сцепляет разные факты).
            # НЕ сливаем такой кластер: разбиваем на одиночные (флаг на ручную проверку).
            if len(members) > _MAX_CLUSTER_SIZE:
                logger.warning(
                    "semantic_dedup: компонент размера %d > %d в домене %r → НЕ сливаю "
                    "(over-merge guard; поднимите порог / проверьте модель)",
                    len(members), _MAX_CLUSTER_SIZE, dom,
                )
                clusters.extend([m] for m in members)
            else:
                clusters.append(members)

    # детерминированный порядок кластеров: по наименьшему fact_id
    clusters.sort(key=lambda c: (str(facts[c[0]].get("fact_id", "")), c[0]))
    return clusters


def _claim_polarity(claim: str) -> int:
    """Полярность (+1/−1) — переиспользует negation-детектор из contradiction_resolver."""
    try:
        from core.contradiction_resolver import _polarity
        return _polarity(claim)
    except Exception:  # noqa: BLE001
        return 1


def compute_semantic_corroboration(
    facts: Sequence[dict[str, Any]],
    threshold: float = DEFAULT_THRESHOLD,
    embed_fn: EmbedFn | None = None,
) -> dict[str, int]:
    """
    fact_id → число РАЗНЫХ источников в его смысловом кластере.
    Drop-in семантическая замена `promotion_policy.compute_corroboration`
    (там — по нормализованному тексту; здесь — по смыслу).
    """
    out: dict[str, int] = {}
    for cl in cluster_by_meaning(facts, threshold, embed_fn):
        # Разделить кластер по ПОЛЯРНОСТИ: «X» и «не X» попадают в один смысловой кластер,
        # но НЕ корроборируют друг друга (это противоречие, см. contradiction_resolver).
        # Корроборация считается только среди СОГЛАСНЫХ (одной полярности). (audit-фикс P1)
        by_pol: dict[int, list[int]] = {}
        for i in cl:
            by_pol.setdefault(_claim_polarity(facts[i].get("claim", "")), []).append(i)
        for members in by_pol.values():
            sources = {str(facts[i].get("source", "")).strip().lower() for i in members}
            n = len(sources) or 1
            for i in members:
                fid = facts[i].get("fact_id")
                if fid:
                    out[str(fid)] = n
    return out


@dataclass
class MergePlan:
    """План слияния кластера (dry-run; ничего не мутирует)."""
    canonical_id: str
    absorbed_ids: list[str]
    sources_after: list[str]
    size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "absorbed_ids": list(self.absorbed_ids),
            "sources_after": list(self.sources_after),
            "size": self.size,
        }


def plan_dedup(
    facts: Sequence[dict[str, Any]],
    threshold: float = DEFAULT_THRESHOLD,
    embed_fn: EmbedFn | None = None,
) -> list[MergePlan]:
    """
    Планы слияния для кластеров размера >= 2. Канонический факт выбирается по
    (ранг ESM ↑, confidence ↑, порядок входа); остальные — кандидаты на Deprecated
    с ребром merged_into (исполняет ОТДЕЛЬНЫЙ шаг, не этот модуль). No-DELETE.
    """
    plans: list[MergePlan] = []
    for cl in cluster_by_meaning(facts, threshold, embed_fn):
        if len(cl) < 2:
            continue

        def _rank(i: int):
            f = facts[i]
            return (_ESM_RANK.get(str(f.get("epistemic_state", "")), 0),
                    float(f.get("confidence", 0.0) or 0.0))

        ordered = sorted(cl, key=_rank, reverse=True)
        canon = ordered[0]
        sources = sorted({str(facts[i].get("source", "")).strip()
                          for i in cl if str(facts[i].get("source", "")).strip()})
        plans.append(MergePlan(
            canonical_id=str(facts[canon].get("fact_id", "")),
            absorbed_ids=[str(facts[i].get("fact_id", "")) for i in ordered[1:]],
            sources_after=sources,
            size=len(cl),
        ))
    return plans


__all__ = [
    "DEFAULT_THRESHOLD",
    "EmbedFn",
    "MergePlan",
    "cluster_by_meaning",
    "compute_semantic_corroboration",
    "default_embedder",
    "is_semantic_dedup_enabled",
    "plan_dedup",
]
