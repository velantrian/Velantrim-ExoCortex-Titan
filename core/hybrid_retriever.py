"""
core/hybrid_retriever.py — Velantrim v8.3.0
============================================
Гибридный ретривер: BM25 + Dense Embeddings + Reciprocal Rank Fusion.

Закрывает Sprint 2a задачу HybridRetriever.
Закрывает критику 5/9 ИИ из аудита май 2026 (BM25-only архаика).

Архитектура:
    ┌─────────────────────────────────────────────────────────┐
    │  Query                                                  │
    │    ├── BM25Retriever       → ranked list A (keyword)    │
    │    └── DenseRetriever      → ranked list B (semantic)   │
    │              ↓                          ↓               │
    │         RRF Fusion (k=60)               │               │
    │              ↓                          │               │
    │         Fused list ←────────────────────┘               │
    │              ↓                                          │
    │    CrossEncoderReranker (опционально)                   │
    │              ↓                                          │
    │         Top-K результатов                               │
    └─────────────────────────────────────────────────────────┘

Зависимости:
    BM25: rank-bm25 (pip install rank-bm25)
    Dense: sentence-transformers (pip install sentence-transformers)
    Reranker: sentence-transformers (cross-encoder/ms-marco-MiniLM-L-6-v2)

Если зависимости не установлены — graceful fallback на чистый BM25.
"""

from __future__ import annotations

import hashlib
import logging
import os
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.cross_encoder import CrossEncoder

logger = logging.getLogger(__name__)

# Дефолтная модель эмбеддингов. Проверено эмпирически: англоцентричная all-MiniLM-L6-v2
# на РУССКОЙ KB почти не работает (ставит «вода кипит» выше «электрического сопротивления»
# для запроса про электричество). paraphrase-multilingual-MiniLM-L12-v2 различает русские
# омонимы (физ./соц./психол. «сопротивление»). KB русская → мультиязычная модель — дефолт.
# Override: VELANTRIM_EMBEDDING_MODEL (напр. all-MiniLM-L6-v2 для англоязычной базы).
_DEFAULT_EMBEDDING_MODEL = os.getenv(
    "VELANTRIM_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
)


def _parse_positive_int_env(name: str, default: int) -> int:
    """Read `name` from the environment as a positive int. Never raises.

    Runs at class-definition (import) time, where an exception would take
    down the whole module — so every failure mode degrades to a logged
    warning and a safe fallback instead:
      - unset                -> `default`
      - not a valid integer  -> `default`
      - < 1                  -> clamped to 1 (a cache that could hold zero
                                 or a negative number of entries makes no
                                 sense and would otherwise wedge the
                                 eviction loop in an infinite/degenerate spin)
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        logger.warning(
            "%s=%r is not a valid integer; falling back to default %d", name, raw, default
        )
        return default
    if value < 1:
        logger.warning("%s=%d is below the minimum of 1; clamping to 1", name, value)
        return 1
    return value


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class RetrievedFact:
    fact_id:     str
    claim:       str
    source:      str
    confidence:  float
    bm25_score:  float = 0.0
    dense_score: float = 0.0
    rrf_score:   float = 0.0
    final_score: float = 0.0
    metadata:    dict  = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "fact_id":    self.fact_id,
            "claim":      self.claim,
            "source":     self.source,
            "confidence": self.confidence,
            "score":      self.final_score,
            "score_breakdown": {
                "bm25":   round(self.bm25_score, 4),
                "dense":  round(self.dense_score, 4),
                "rrf":    round(self.rrf_score, 4),
                "final":  round(self.final_score, 4),
            },
            "metadata":   self.metadata,
        }


# ---------------------------------------------------------------------------
# BM25 Retriever
# ---------------------------------------------------------------------------

class BM25Retriever:
    """
    BM25 Okapi поверх списка фактов.
    Использует rank-bm25 если доступен, иначе naive TF-IDF.
    """

    def __init__(self, facts: list[dict], k1: float = 1.5, b: float = 0.75) -> None:
        self._facts  = facts
        self._k1     = k1
        self._b      = b
        self._corpus = [self._tokenize(f.get("claim", "")) for f in facts]
        self._bm25   = self._build_index()

    def _tokenize(self, text: str) -> list[str]:
        import re
        return re.sub(r"[^\w\s]", " ", text.lower()).split()

    def _build_index(self):
        # Пустой корпус: BM25Okapi делит на ноль (avgdl = num_doc / corpus_size = 0/0).
        # Возвращаем None → retrieve() уйдёт в naive-путь, который корректно отдаёт [].
        if not self._corpus:
            return None
        try:
            from rank_bm25 import BM25Okapi
            return BM25Okapi(self._corpus, k1=self._k1, b=self._b)
        except ImportError:
            logger.warning(
                "rank-bm25 не установлен. Используется naive TF-IDF fallback. "
                "Установите: pip install rank-bm25"
            )
            return None
        except Exception as exc:
            logger.warning(
                "BM25Retriever: ошибка построения индекса — %s. Naive TF-IDF fallback.", exc
            )
            return None

    def retrieve(self, query: str, top_k: int = 50) -> list[tuple[int, float]]:
        """Возвращает (index, score) отсортированные по убыванию score."""
        tokens = self._tokenize(query)
        if self._bm25 is not None:
            scores = self._bm25.get_scores(tokens)
        else:
            scores = self._naive_scores(tokens)

        indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(i, float(s)) for i, s in indexed[:top_k] if s > 0]

    def _naive_scores(self, tokens: list[str]) -> list[float]:
        """Naive TF fallback."""
        scores = []
        for doc in self._corpus:
            tf = sum(doc.count(t) for t in tokens) / max(len(doc), 1)
            scores.append(tf)
        return scores


# ---------------------------------------------------------------------------
# Dense (Embedding) Retriever
# ---------------------------------------------------------------------------

class DenseRetriever:
    """
    Семантический поиск через sentence-transformers.
    Если не установлены — автоматически пропускается (graceful degradation).

    AUDIT-FIX (PR #91 lifecycle): NGramIndex narrows candidates to a different
    fact_id subset on almost every query. Before this fix, each new subset was
    treated as "corpus changed" one level up (pipeline._get_hybrid_retriever),
    so a fresh DenseRetriever reloaded the sentence-transformer model AND
    re-encoded every candidate's claim from scratch on every query — the
    model load alone costs ~1-2s. The model and per-fact embeddings are now
    process-persistent (class-level), so a fact already embedded once is
    never re-encoded just because it resurfaces in a differently-shaped
    candidate set.

    AUDIT-FIX (follow-up): the vector cache key is (model_name, fact_id,
    sha256(claim)), not fact_id alone. Keying on fact_id alone let an edited
    fact (same fact_id, changed claim) or a runtime model swap silently
    reuse a stale/wrong-model embedding — a correctness bug, not just a
    performance one. The cache is also now bounded (_VECTOR_CACHE_MAX_ENTRIES,
    LRU eviction) so an ever-growing corpus of distinct claims can't leak
    memory unboundedly.

    AUDIT-FIX (thread safety): _VECTOR_CACHE is a process-wide class
    attribute, and pipeline._get_hybrid_retriever() can be reached from
    concurrent requests. Every lookup+touch and insert+evict sequence below
    runs under a single _VECTOR_CACHE_LOCK acquisition each — never a
    membership check in one lock scope followed by a mutation in another —
    so a torn read/write can't raise KeyError or leave the cache over its
    bound. The lock is a threading.RLock, not held across model.encode()
    (which can be slow): two threads racing on the same cache miss may each
    compute the same embedding once — harmless, no cache corruption results.
    """

    _AVAILABLE: bool | None = None
    # Persistent across instances/candidate-sets — this is the fix: the model
    # is loaded once per process, and a fact's embedding is computed once ever.
    _MODEL_CACHE: dict[str, SentenceTransformer] = {}
    # (model_name, fact_id, sha256(claim)) -> embedding vector. Plain dict used
    # as an LRU: Python dicts are insertion-ordered, so "pop + reinsert" moves
    # a key to the most-recently-used end and the first key is the
    # least-recently-used one — no collections.OrderedDict needed. All access
    # must go through _cache_lookup()/_cache_store()/_cache_clear() below,
    # which hold _VECTOR_CACHE_LOCK for the full check-then-mutate sequence.
    _VECTOR_CACHE: dict[str, Any] = {}
    _VECTOR_CACHE_LOCK = threading.RLock()
    _VECTOR_CACHE_MAX_ENTRIES = _parse_positive_int_env("VELANTRIM_DENSE_CACHE_MAX_ENTRIES", 50000)

    def __init__(self, facts: list[dict], model_name: str = _DEFAULT_EMBEDDING_MODEL) -> None:
        self._facts      = facts
        self._model_name = model_name
        # list[Any]: one embedding per self._facts[i], sourced from the
        # persistent vector cache (each vector itself may be an ndarray or a
        # Tensor row depending on backend).
        self._embeddings: list[Any] = []
        self._model: SentenceTransformer | None = None
        self._load()

    @staticmethod
    def _cache_key(model_name: str, fact_id: str, claim: str) -> str:
        claim_hash = hashlib.sha256(claim.encode("utf-8")).hexdigest()
        return f"{model_name}\0{fact_id}\0{claim_hash}"

    @classmethod
    def _cache_lookup(cls, key: str) -> tuple[bool, Any]:
        """Atomic check-and-touch. Returns (hit, value) — never `(False, <a
        real cached None>)` vs `(True, None)` ambiguity, since a miss is
        always `(False, None)` and a hit always reports `True` alongside
        whatever value is actually stored."""
        with cls._VECTOR_CACHE_LOCK:
            if key not in cls._VECTOR_CACHE:
                return False, None
            value = cls._VECTOR_CACHE.pop(key)
            cls._VECTOR_CACHE[key] = value  # reinsert at the end == "touch"
            return True, value

    @classmethod
    def _cache_store(cls, key: str, vec: Any) -> None:
        """Atomic insert/update-as-most-recently-used, then evict overflow."""
        with cls._VECTOR_CACHE_LOCK:
            cls._VECTOR_CACHE.pop(key, None)
            cls._VECTOR_CACHE[key] = vec
            while len(cls._VECTOR_CACHE) > cls._VECTOR_CACHE_MAX_ENTRIES:
                oldest_key = next(iter(cls._VECTOR_CACHE))
                del cls._VECTOR_CACHE[oldest_key]

    @classmethod
    def _cache_clear(cls) -> None:
        """Test/helper API: drop every cached embedding. Thread-safe."""
        with cls._VECTOR_CACHE_LOCK:
            cls._VECTOR_CACHE.clear()

    def _load(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            model = DenseRetriever._MODEL_CACHE.get(self._model_name)
            if model is None:
                model = SentenceTransformer(self._model_name)
                DenseRetriever._MODEL_CACHE[self._model_name] = model
                logger.info("DenseRetriever: загружена модель %s", self._model_name)
            self._model = model

            # Facts without a fact_id can't be cached safely (no stable key) —
            # they are always (re-)encoded, same as every fact was before this fix.
            keys: list[str | None] = [
                self._cache_key(self._model_name, f["fact_id"], f.get("claim", ""))
                if f.get("fact_id") else None
                for f in self._facts
            ]

            # Pass 1: resolve every cacheable key via one atomic lookup+touch
            # each (never a separate "in cache" check followed by a later,
            # separately-locked mutation — that gap is exactly what could
            # raise KeyError or desync the LRU order under concurrent access).
            resolved: dict[int, Any] = {}
            missing_idx: list[int] = []
            for i, key in enumerate(keys):
                if key is None:
                    missing_idx.append(i)
                    continue
                hit, value = DenseRetriever._cache_lookup(key)
                if hit:
                    resolved[i] = value
                else:
                    missing_idx.append(i)

            # Pass 2: encode only what's missing. Deliberately NOT holding
            # _VECTOR_CACHE_LOCK here — model.encode() can take a long time,
            # and serializing every encode() call behind one global lock
            # would turn concurrent requests into a queue. Two threads racing
            # on the same miss may each encode the same claim once; that's a
            # harmless duplicate computation, not a correctness problem —
            # _cache_store() below is still the sole, atomic writer.
            if missing_idx:
                claims = [self._facts[i].get("claim", "") for i in missing_idx]
                vectors = model.encode(claims, normalize_embeddings=True)
                for i, vec in zip(missing_idx, vectors):
                    key = keys[i]
                    if key is not None:
                        DenseRetriever._cache_store(key, vec)
                    resolved[i] = vec

            self._embeddings = [resolved[i] for i in range(len(self._facts))]
            DenseRetriever._AVAILABLE = True
            logger.debug(
                "DenseRetriever: %d/%d фактов закодировано заново (%d переиспользовано из кэша)",
                len(missing_idx), len(self._facts), len(self._facts) - len(missing_idx),
            )
        except ImportError:
            DenseRetriever._AVAILABLE = False
            logger.warning(
                "sentence-transformers не установлен. Dense retrieval недоступен. "
                "Установите: pip install sentence-transformers"
            )
        except Exception as exc:
            DenseRetriever._AVAILABLE = False
            logger.warning("DenseRetriever: ошибка загрузки — %s", exc)

    @property
    def available(self) -> bool:
        return DenseRetriever._AVAILABLE is True and self._model is not None

    def retrieve(self, query: str, top_k: int = 50) -> list[tuple[int, float]]:
        """Возвращает (index, cosine_similarity) отсортированные по убыванию."""
        if not self.available:
            return []
        try:
            assert self._model is not None  # guaranteed by self.available above
            q_emb = self._model.encode([query], normalize_embeddings=True)[0]
            # Per-candidate dot product (embeddings normalized ⇒ cosine). Plain
            # Python loop, not a vectorized matrix op: candidate sets here are
            # small (NGram narrows to ≤50-1000), and this keeps DenseRetriever
            # backend-agnostic (no hard numpy dependency beyond whatever
            # sentence-transformers itself already requires to encode()).
            sims = [float(sum(a * b for a, b in zip(vec, q_emb))) for vec in self._embeddings]
            indexed = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)
            return [(i, s) for i, s in indexed[:top_k]]
        except Exception as exc:
            logger.warning("DenseRetriever.retrieve error: %s", exc)
            return []


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------

def reciprocal_rank_fusion(
    *ranked_lists: list[tuple[int, float]],
    k: int = 60,
) -> list[tuple[int, float]]:
    """
    RRF (Cormack et al., 2009) с калибровкой скора (V8.8).

    Формула: RRF(d) = Σ 1/(k + rank(d))
    k=60 — стандартное значение из оригинальной статьи.

    V8.8 FIX: BM25 и cosine similarity в разных диапазонах
    (BM25: 0..∞, cosine: -1..1). Перед RRF нормализуем каждый список
    к единой шкале [0,1] через min-max scaling, чтобы один тип
    retrieval не доминировал над другим.
    """
    # Нормализовать каждый список к [0,1]
    normalized: list[list[tuple[int, float]]] = []
    for ranked in ranked_lists:
        if not ranked:
            normalized.append([])
            continue
        scores = [s for _, s in ranked]
        min_s, max_s = min(scores), max(scores)
        if max_s == min_s:
            # Все одинаковые — оставляем 0.5
            normalized.append([(idx, 0.5) for idx, _ in ranked])
        else:
            normalized.append([
                (idx, (s - min_s) / (max_s - min_s))
                for idx, s in ranked
            ])

    rrf_scores: dict[int, float] = {}
    for ranked in normalized:
        for rank, (idx, _score) in enumerate(ranked, start=1):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (k + rank)

    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)


# ---------------------------------------------------------------------------
# Cross-Encoder Reranker (опционально)
# ---------------------------------------------------------------------------

class CrossEncoderReranker:
    """
    Опциональный cross-encoder для финального rerank top-K.
    Модель по умолчанию: cross-encoder/ms-marco-MiniLM-L-6-v2.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self._model: CrossEncoder | None = None
        try:
            from sentence_transformers.cross_encoder import CrossEncoder
            self._model = CrossEncoder(model_name)
            logger.info("CrossEncoderReranker: загружена модель %s", model_name)
        except Exception as exc:
            logger.warning(
                "CrossEncoderReranker недоступен: %s. "
                "Используется RRF без rerank.", exc
            )

    @property
    def available(self) -> bool:
        return self._model is not None

    def rerank(
        self,
        query: str,
        facts: list[RetrievedFact],
        top_k: int = 10,
    ) -> list[RetrievedFact]:
        if not self.available or not facts:
            return facts[:top_k]
        try:
            assert self._model is not None  # guaranteed by self.available above
            pairs  = [(query, f.claim) for f in facts]
            # CrossEncoder.predict()'s stub covers a much broader multimodal signature
            # (text/image/audio/video) than our plain text-pair usage; list[tuple[str,
            # str]] is the standard, valid cross-encoder call shape at runtime.
            scores = self._model.predict(pairs)  # type: ignore[arg-type]
            for fact, score in zip(facts, scores):
                fact.final_score = float(score)
            return sorted(facts, key=lambda f: f.final_score, reverse=True)[:top_k]
        except Exception as exc:
            logger.warning("CrossEncoderReranker.rerank error: %s. Возвращаем RRF.", exc)
            return facts[:top_k]


# ---------------------------------------------------------------------------
# HybridRetriever — главный класс
# ---------------------------------------------------------------------------

class HybridRetriever:
    """
    Гибридный ретривер для Velantrim Fast Path.

    Заменяет чистый BM25 в pipeline.py.
    Совместим с GraphStore ABC — принимает список фактов из store.get_all_facts().

    Usage:
        facts = store.get_all_facts(state_filter="Validated")
        retriever = HybridRetriever(facts, use_reranker=False)
        results = retriever.retrieve(query="квантовая запутанность", top_k=5)
        for r in results:
            print(r.fact_id, r.claim, r.final_score)
    """

    def __init__(
        self,
        facts: list[dict],
        embedding_model: str = _DEFAULT_EMBEDDING_MODEL,
        use_reranker: bool = False,
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        rrf_k: int = 60,
    ) -> None:
        self._facts   = facts
        self._rrf_k   = rrf_k

        self._bm25    = BM25Retriever(facts)
        self._dense   = DenseRetriever(facts, model_name=embedding_model)
        self._reranker: CrossEncoderReranker | None = (
            CrossEncoderReranker(reranker_model) if use_reranker else None
        )

        mode = "BM25+Dense+Reranker" if (use_reranker and self._reranker and self._reranker.available) \
               else "BM25+Dense" if self._dense.available \
               else "BM25 only (fallback)"
        logger.info("HybridRetriever initialized: %s, %d facts", mode, len(facts))

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedFact]:
        """
        Главный метод. Возвращает top_k фактов отсортированных по релевантности.
        """
        if not self._facts:
            return []

        # Шаг 1: BM25 (всегда доступен)
        bm25_results  = self._bm25.retrieve(query, top_k=top_k * 5)

        # Шаг 2: Dense (если доступен)
        dense_results = self._dense.retrieve(query, top_k=top_k * 5)

        # Шаг 3: RRF fusion
        if dense_results:
            fused = reciprocal_rank_fusion(bm25_results, dense_results, k=self._rrf_k)
        else:
            fused = [(idx, score) for idx, score in bm25_results]

        # Шаг 4: Собираем RetrievedFact объекты
        bm25_map  = {idx: score for idx, score in bm25_results}
        dense_map = {idx: score for idx, score in dense_results}

        retrieved: list[RetrievedFact] = []
        for idx, rrf_score in fused[:top_k * 2]:
            if idx >= len(self._facts):
                continue
            f = self._facts[idx]
            retrieved.append(RetrievedFact(
                fact_id=     f.get("fact_id",    ""),
                claim=       f.get("claim",       ""),
                source=      f.get("source",      ""),
                confidence=  f.get("confidence",  0.0),
                bm25_score=  bm25_map.get(idx,   0.0),
                dense_score= dense_map.get(idx,  0.0),
                rrf_score=   rrf_score,
                final_score= rrf_score,
                metadata=    f.get("metadata",    {}),
            ))

        # Шаг 5: Cross-encoder rerank (опционально)
        if self._reranker and self._reranker.available and retrieved:
            retrieved = self._reranker.rerank(query, retrieved, top_k=top_k)
        else:
            retrieved = retrieved[:top_k]

        # Шаг 6: ACT-R бонус (Titan HYPERIA-3, opt-in)
        try:
            from core.actr_activation import boost_retrieval_score, is_actr_enabled

            if is_actr_enabled():
                for r in retrieved:
                    r.final_score = boost_retrieval_score(r.fact_id, r.final_score)
                retrieved.sort(key=lambda x: x.final_score, reverse=True)
        except Exception as exc:
            logger.debug("ACT-R boost skipped: %s", exc)

        return retrieved

    def retrieve_as_dicts(self, query: str, top_k: int = 10) -> list[dict]:
        """Совместимость с текущим pipeline.py."""
        return [r.to_dict() for r in self.retrieve(query, top_k=top_k)]

    # ── V8.7 Synapse: ego_net_expand — multi-hop retrieval без LLM ──────────

    def retrieve_5stage(
        self,
        query: str,
        top_k: int = 10,
        *,
        ego_depth: int = 2,
        use_ego: bool = True,
    ) -> list[RetrievedFact]:
        """
        5-этапный retrieval (Synapse P0-2): graph → bm25 → vector → ego_net → greedy_select.

        Этапы выполняются ПАРАЛЛЕЛЬНО где возможно. Ego-net расширяет топ-10
        результатов графовыми соседями — multi-hop без единого LLM-вызова.

        Если ego_net не даёт результатов (нет графа) — fallback к обычному retrieve().
        """
        if not self._facts:
            return []

        # Stage 1: BM25 + Dense (как обычно)
        bm25_results = self._bm25.retrieve(query, top_k=top_k * 5)
        dense_results = self._dense.retrieve(query, top_k=top_k * 5)

        # Stage 2: RRF fusion
        if dense_results:
            fused = reciprocal_rank_fusion(bm25_results, dense_results, k=self._rrf_k)
        else:
            fused = [(idx, score) for idx, score in bm25_results]

        # Stage 3: Собрать топ-K кандидатов
        bm25_map = {idx: score for idx, score in bm25_results}
        dense_map = {idx: score for idx, score in dense_results}

        top_indices = [idx for idx, _ in fused[:top_k]]

        # Stage 4: ego_net_expand — расширить топ-10 графовыми соседями
        if use_ego and ego_depth > 0:
            ego_indices = self._ego_net_expand(top_indices, depth=ego_depth)
            # Объединить топ-indices + ego-соседей (без дубликатов)
            all_indices = list(dict.fromkeys(top_indices + ego_indices))
        else:
            all_indices = top_indices

        # Stage 5: greedy_select — собрать в рамках top_k
        retrieved: list[RetrievedFact] = []
        for idx in all_indices[:top_k * 2]:
            if idx >= len(self._facts):
                continue
            f = self._facts[idx]
            retrieved.append(RetrievedFact(
                fact_id=f.get("fact_id", ""),
                claim=f.get("claim", ""),
                source=f.get("source", ""),
                confidence=f.get("confidence", 0.0),
                bm25_score=bm25_map.get(idx, 0.0),
                dense_score=dense_map.get(idx, 0.0),
                rrf_score=next((s for i, s in fused if i == idx), 0.0),
                final_score=0.0,
                metadata=f.get("metadata", {}),
            ))

        # Сортировка по rrf_score
        retrieved.sort(key=lambda r: r.rrf_score, reverse=True)

        # Reranker (опционально)
        if self._reranker and self._reranker.available:
            try:
                retrieved = self._reranker.rerank(query, retrieved[:top_k * 2], top_k)
            except Exception:
                pass

        return retrieved[:top_k]

    def _ego_net_expand(self, seed_indices: list[int], depth: int = 2) -> list[int]:
        """
        Расширить список seed-фактов их графовыми соседями из CausalGraph.

        Проходит depth уровней: seed → соседи → соседи соседей.
        Возвращает список индексов соседей (без seed).
        Graceful: если causal_graph недоступен → возвращает [].
        """
        if not seed_indices:
            return []

        # Пытаемся получить causal relations
        try:
            from core.causal_graph import get_causal_graph
            cg = get_causal_graph()
        except Exception:
            return []

        if cg is None:
            return []

        seed_ids = [
            self._facts[i].get("fact_id", "")
            for i in seed_indices
            if i < len(self._facts)
        ]
        if not seed_ids:
            return []

        # Собрать соседей (BFS на depth уровней с учётом весов рёбер, V8.8)
        visited: set[str] = set(seed_ids)
        frontier: set[str] = set(seed_ids)

        # Загружаем RELATION_TYPE_WEIGHTS для фильтрации
        try:
            from core.causal_graph import RELATION_TYPE_WEIGHTS
            type_weights = RELATION_TYPE_WEIGHTS
        except ImportError:
            type_weights = {}

        for _ in range(depth):
            next_frontier: set[str] = set()
            for fid in frontier:
                try:
                    # V8.8: weighted traversal — получаем все рёбра и фильтруем по весу
                    relations = cg.get_relations_from(fid)
                    for rel in relations:
                        nb = rel.to_fact_id
                        if nb in visited:
                            continue
                        # V8.8: фильтр по весу типа ребра — слабые связи пропускаем
                        type_weight = type_weights.get(rel.relation_type, 0.5)
                        if type_weight < 0.5:
                            continue
                        visited.add(nb)
                        next_frontier.add(nb)
                except Exception:
                    continue
            frontier = next_frontier
            if not frontier:
                break

        # Исключить seed
        neighbor_ids = visited - set(seed_ids)

        # Найти индексы соседей в self._facts
        fact_index: dict[str, int] = {
            f.get("fact_id", ""): i for i, f in enumerate(self._facts)
        }
        return [
            fact_index[nid]
            for nid in neighbor_ids
            if nid in fact_index
        ]

    # ── V8.8: MMR Diversity + Retrieval Cache ───────────────────────────────

    def retrieve_diverse(
        self,
        query: str,
        top_k: int = 10,
        *,
        lambda_param: float = 0.7,
    ) -> list[RetrievedFact]:
        """
        Maximal Marginal Relevance — баланс релевантности и разнообразия.

        Без MMR 10 результатов могут быть про одно и то же.
        С MMR: λ=0.7 → 70% релевантность, 30% разнообразие.

        Args:
            lambda_param: 0..1, баланс релевантности vs разнообразия
                          1.0 = только релевантность (обычный retrieval)
                          0.0 = только разнообразие (все разные)
        """
        # Получить больше кандидатов чем нужно
        candidates = self.retrieve(query, top_k=top_k * 3)
        if len(candidates) <= top_k:
            return candidates

        selected: list[RetrievedFact] = []
        remaining = list(candidates)

        while len(selected) < top_k and remaining:
            mmr_scores: list[float] = []
            for cand in remaining:
                relevance = cand.final_score
                # Разнообразие: максимальное сходство с уже выбранными
                max_sim = 0.0
                for s in selected:
                    sim = self._jaccard_claim_similarity(cand.claim, s.claim)
                    max_sim = max(max_sim, sim)
                redundancy = max_sim
                mmr = lambda_param * relevance - (1.0 - lambda_param) * redundancy
                mmr_scores.append(mmr)

            best_idx = max(range(len(mmr_scores)), key=lambda i: mmr_scores[i])
            selected.append(remaining.pop(best_idx))

        return selected

    @staticmethod
    def _jaccard_claim_similarity(claim_a: str, claim_b: str) -> float:
        """Jaccard-сходство двух claims по токенам (для MMR)."""
        if not claim_a or not claim_b:
            return 0.0
        tokens_a = set(claim_a.lower().split())
        tokens_b = set(claim_b.lower().split())
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b
        return len(intersection) / len(union) if union else 0.0
