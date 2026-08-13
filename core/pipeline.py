# core/pipeline.py
# Velantrim ExoCortex — Core Pipeline
# v8.2.0 (Sprint 2a: HybridRetriever + NGramIndex + real TruthGate wired in)
#
# Принцип: Canonical Local Memory = Truth · projections are rebuildable
# Пайплайн: Query → [NGram pre-filter] → Retrieve → FactsPack → Trace
#                 → Guardian → TruthGate → Answer
#
# История изменений:
#   v8.0.2-sprint1: tokenize по split() (терял em-dash, пунктуация),
#                   confidence = retrieval_score (искажало семантику),
#                   Guardian только len-проверка,
#                   run() крашится на повторном вызове (Validated→Validated).
#   v8.0.3-p0:     tokenize с em-dash и пунктуацией,
#                  confidence = source confidence (стабильная),
#                  Guardian проверяет fact_id coverage.
#   v8.0.3-p0-FIX: AUDIT — pipeline.run() идемпотентен по ESM-состоянию.
#   v8.1.0 Sprint2a:
#     - HybridRetriever (BM25+Dense+RRF) заменяет inline BM25-класс.
#     - NGramIndex: pre-filter O(log N) перед Hybrid retrieval.
#     - Реальный TruthGate из truth_gate.py (CognitiveMode, evidence_count,
#       active contradictions) заменяет inline confidence-floor заглушку.
#     - DATABASE mock сохранён как fallback если store пустой.
#   v8.2.0 AUDIT-FIX (v8.4.0 release):
#     - HybridRetriever синглтон вместо per-request init. До v8.2.0
#       каждый retrieve() создавал новый HybridRetriever → загружал
#       sentence-transformer и считал embeddings всей базы заново.
#       Теперь singleton с _rebuild_retriever() при значимых изменениях.
#       Performance: 1-2s → 20-50ms (по обещанию README).
#
# Graceful degradation:
#   - NGramIndex недоступен (нет FTS5) → пропускаем pre-filter, идём дальше.
#   - HybridRetriever: Dense недоступен → fallback на BM25 only.
#   - TruthGate/policy dependency unavailable → fail closed.
#   - Query path never writes facts, ESM states, or causal relations.

import hashlib
import logging
import math
import re
import sqlite3
from collections import Counter
from typing import Any, Optional

from core.trace import build_trace, format_trace

try:
    from core.facts_pack import COGNITIVE_MODE_POLICIES, FactsPackBuilder
    _FACTS_PACK_BUILDER_AVAILABLE = True
except ImportError:
    _FACTS_PACK_BUILDER_AVAILABLE = False
from core.memory import (
    _GLOBAL_STORE,
    get_fact,
    get_fact_ids,
    get_facts_by_ids,
)

# ── Sprint 2a: новые импорты ──────────────────────────────────────────────────
try:
    from core.hybrid_retriever import HybridRetriever, RetrievedFact
    _HYBRID_AVAILABLE = True
except ImportError:
    _HYBRID_AVAILABLE = False

try:
    from core.ngram_index import NGramIndex
    _NGRAM_AVAILABLE = True
except ImportError:
    _NGRAM_AVAILABLE = False

try:
    from core.truth_gate import CognitiveMode, TruthGate
    _REAL_TRUTH_GATE_AVAILABLE = True
except ImportError:
    _REAL_TRUTH_GATE_AVAILABLE = False

try:
    from core.causal_graph import CausalGraph
    _CAUSAL_GRAPH_AVAILABLE = True
except ImportError:
    _CAUSAL_GRAPH_AVAILABLE = False

logger = logging.getLogger(__name__)


class FactsPackPolicyUnavailableError(RuntimeError):
    """The canonical read-policy pack could not be built fail closed."""

# ─── MOCK DATABASE (L3 заглушка) ──────────────────────────────────────────────
# Используется как fallback если store пустой (разработка, тесты без данных).
# FIX v8.5.1 (Gemini): DATABASE — ТОЛЬКО FALLBACK для dev/test.
# В production при пустом store НЕ используем эти данные — возвращаем пустой результат.
# TODO Sprint 2b: полностью убрать DATABASE после реализации реального GraphStore.
_DATABASE_DEV_ONLY = [
    {"id": "f1", "text": "Water boils at 100°C at sea level",      "source": "physics",      "confidence": 0.99},
    {"id": "f2", "text": "Quantum entanglement links particles",     "source": "physics",      "confidence": 0.85},
    {"id": "f3", "text": "Earth revolves around the Sun",           "source": "astronomy",    "confidence": 0.99},
    {"id": "f4", "text": "The human brain has ~86 billion neurons", "source": "neuroscience", "confidence": 0.90},
    {"id": "f5", "text": "DNA encodes genetic information",         "source": "biology",      "confidence": 0.99},
]

# FIX v8.5.2 (Claude audit): обратно-совместимый алиас для существующих
# тестов и внешнего кода, импортирующего `DATABASE`. Удалить в Sprint 2b
# вместе с самим mock-fallback. Не использовать в новом коде.
DATABASE = _DATABASE_DEV_ONLY


# ─── HybridRetriever singleton (AUDIT-FIX v8.4.0) ─────────────────────────────
# До v8.4.0 _retrieve_from_store создавал HybridRetriever на каждом запросе.
# Каждое создание грузит sentence-transformer (~80MB модель, 1-2 сек) и считает
# embeddings всей базы. На production это performance bomb.
# Сейчас держим singleton + признак "грязный" (_HYBRID_DIRTY), который вызывает
# rebuild при значимых изменениях базы. Authoritative writer вызывает
# mark_retriever_dirty() после изменения базы; QueryPipeline сам флаг не меняет.

_HYBRID_RETRIEVER: Optional["HybridRetriever"] = None
_HYBRID_DIRTY: bool = True   # при старте — нужно построить
_HYBRID_FACTS_COUNT: int = 0  # для лёгкой инвалидации
_HYBRID_FACT_IDS: frozenset = frozenset()  # TASK-06/07: детектируем смену фактов


def mark_retriever_dirty() -> None:
    """Пометить singleton как requiring rebuild (вызывать после store_fact)."""
    global _HYBRID_DIRTY
    _HYBRID_DIRTY = True


def _get_hybrid_retriever(facts: list[dict[str, Any]]) -> Optional["HybridRetriever"]:
    """
    Получить singleton HybridRetriever, перестраивая при необходимости.
    Перестройка происходит когда:
      - _HYBRID_DIRTY = True (явный вызов mark_retriever_dirty)
      - количество фактов изменилось значимо (>10% разница)
      - состав fact_id изменился (TASK-06/07: иные факты с тем же count)
    """
    global _HYBRID_RETRIEVER, _HYBRID_DIRTY, _HYBRID_FACTS_COUNT, _HYBRID_FACT_IDS

    if not _HYBRID_AVAILABLE:
        return None

    n = len(facts)
    current_ids = frozenset(f.get("fact_id", "") for f in facts)
    facts_changed = (
        abs(n - _HYBRID_FACTS_COUNT) > max(1, _HYBRID_FACTS_COUNT * 0.1)
        or current_ids != _HYBRID_FACT_IDS
    )

    if _HYBRID_RETRIEVER is None or _HYBRID_DIRTY or facts_changed:
        try:
            _HYBRID_RETRIEVER = HybridRetriever(facts)
            _HYBRID_DIRTY = False
            _HYBRID_FACTS_COUNT = n
            _HYBRID_FACT_IDS = current_ids
            logger.info("HybridRetriever singleton (re)built: %d facts", n)
        except Exception as exc:
            logger.warning("HybridRetriever build failed: %s", exc)
            return None

    return _HYBRID_RETRIEVER


# ─── CausalGraph singleton (TASK-08) ──────────────────────────────────────────
# Отслеживаем db_path чтобы пересоздавать при смене store (тесты с isolated_db).
_CAUSAL_GRAPH: Optional["CausalGraph"] = None
_CAUSAL_GRAPH_DB_PATH: str = ""

# Regex для определения каузальных паттернов (EN + RU)
_CAUSAL_REGEX = re.compile(
    r"\b(because|therefore|thus|hence|since|causes|leads to|results in|implies|"
    r"due to|consequently|as a result|"
    r"потому что|следовательно|из-за|поэтому|благодаря|вызывает|приводит к)\b",
    re.IGNORECASE,
)

_RELATIONS_DDL = """
    CREATE TABLE IF NOT EXISTS relations (
        relation_id      TEXT PRIMARY KEY,
        from_fact_id     TEXT NOT NULL REFERENCES facts(fact_id) ON DELETE CASCADE,
        to_fact_id       TEXT NOT NULL REFERENCES facts(fact_id) ON DELETE CASCADE,
        relation_type    TEXT NOT NULL,
        confidence       REAL NOT NULL DEFAULT 0.8,
        knowledge_status TEXT NOT NULL DEFAULT 'known'
            CHECK (knowledge_status IN ('known','inferred','hypothetical','unknown')),
        inference_source TEXT DEFAULT NULL,
        truth_status     TEXT DEFAULT 'validated',
        review_state     TEXT DEFAULT 'approved',
        evidence_ref     TEXT,
        created_at       TEXT NOT NULL DEFAULT (datetime('now')),
        valid_from       TEXT NOT NULL DEFAULT (datetime('now')),
        valid_to         TEXT,
        metadata         TEXT,
        CHECK (from_fact_id != to_fact_id),
        UNIQUE (from_fact_id, to_fact_id, relation_type, inference_source)
    );
    CREATE INDEX IF NOT EXISTS idx_relations_from
        ON relations(from_fact_id, relation_type);
    CREATE INDEX IF NOT EXISTS idx_relations_to
        ON relations(to_fact_id, relation_type);
    CREATE TABLE IF NOT EXISTS relation_paths (
        from_fact_id TEXT NOT NULL, to_fact_id TEXT NOT NULL,
        path_length INTEGER NOT NULL, path_json TEXT NOT NULL,
        total_confidence REAL NOT NULL, min_confidence REAL NOT NULL,
        has_hypothetical INTEGER NOT NULL DEFAULT 0,
        computed_at TEXT NOT NULL DEFAULT (datetime('now')),
        PRIMARY KEY (from_fact_id, to_fact_id, path_length)
    );
"""


def _get_causal_graph() -> Optional["CausalGraph"]:
    """
    TASK-08: Получить singleton CausalGraph.
    Пересоздаёт если db_path изменился (тесты с isolated_db).
    Создаёт таблицы если их нет (идемпотентно, как migration 008).
    """
    global _CAUSAL_GRAPH, _CAUSAL_GRAPH_DB_PATH

    if not _CAUSAL_GRAPH_AVAILABLE:
        return None

    import core.memory as _mem

    current_path = getattr(_mem._GLOBAL_STORE, "db_path", "")
    if _CAUSAL_GRAPH is not None and _CAUSAL_GRAPH_DB_PATH == current_path:
        return _CAUSAL_GRAPH

    # db_path изменился → пересоздаём (закрываем старое соединение)
    if _CAUSAL_GRAPH is not None:
        try:
            _CAUSAL_GRAPH._conn.close()
        except Exception:
            pass
        _CAUSAL_GRAPH = None

    try:
        conn = sqlite3.connect(current_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        for stmt in _RELATIONS_DDL.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(stmt)
        conn.commit()
        _CAUSAL_GRAPH = CausalGraph(conn)
        _CAUSAL_GRAPH_DB_PATH = current_path
        logger.info("CausalGraph singleton created: %s", current_path)
        return _CAUSAL_GRAPH
    except Exception as exc:
        logger.warning("CausalGraph init failed: %s", exc)
        return None


def _peek_causal_graph() -> Optional["CausalGraph"]:
    """Return an already-open graph for the current store without initializing it.

    Read-only facades use this boundary so a query cannot create tables, commit DDL,
    replace a singleton, or close another connection merely because graph evidence was
    requested. ``None`` means the optional graph capability is not already available.
    """
    if not _CAUSAL_GRAPH_AVAILABLE:
        return None

    import core.memory as _mem

    current_path = getattr(_mem._GLOBAL_STORE, "db_path", "")
    if _CAUSAL_GRAPH is not None and _CAUSAL_GRAPH_DB_PATH == current_path:
        return _CAUSAL_GRAPH
    return None


def reset_causal_graph() -> None:
    """Auditably clear canonical relations and detach the singleton."""
    global _CAUSAL_GRAPH, _CAUSAL_GRAPH_DB_PATH

    graph = _CAUSAL_GRAPH
    # Detach before attempting the audited reset. If WriteGate or AuditChain fails,
    # callers must never retain a singleton backed by the connection closed below.
    _CAUSAL_GRAPH = None
    _CAUSAL_GRAPH_DB_PATH = ""
    if graph is not None:
        try:
            graph.reset_relations()
        finally:
            try:
                graph._conn.close()
            except Exception:
                pass


def _extract_conflicts(
    facts: list[dict[str, Any]],
    graph: "CausalGraph",
) -> list[dict[str, Any]]:
    """
    TASK-16: Contradiction-First — извлечь существующие противоречия
    для фактов которые попали в ответ.

    Использует find_contradictions() из CausalGraph (с cycle protection из TASK-10).
    Не создаёт новые связи — только показывает уже существующие contradicts-рёбра.

    Не блокирует ответ. Просто аннотирует.
    """
    conflicts: list[dict[str, Any]] = []
    seen_pairs: set = set()  # дедупликация (A↔B одна пара)

    fact_ids_in_response = {f.get("fact_id") for f in facts if f.get("fact_id")}

    for fact in facts:
        fact_id = fact.get("fact_id")
        if not fact_id:
            continue

        try:
            contradictions = graph.find_contradictions(fact_id)
        except Exception as exc:
            logger.debug("find_contradictions failed for %s: %s", fact_id, exc)
            continue

        for rel in contradictions:
            # Определяем "другой конец" связи
            other_id = (
                rel.to_fact_id if rel.from_fact_id == fact_id
                else rel.from_fact_id
            )
            # Дедупликация: пара (A,B) == (B,A)
            pair_key = tuple(sorted([fact_id, other_id]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            # Если оба факта в ответе — показываем как "internal conflict"
            # Если только один — как "external conflict" с памятью
            kind = "internal" if other_id in fact_ids_in_response else "external"

            conflicts.append({
                "relation_id": rel.relation_id,
                "fact_a":      fact_id,
                "fact_a_claim": fact.get("claim", "")[:80],
                "fact_b":      other_id,
                "kind":        kind,
                "confidence":  getattr(rel, "confidence", 0.5),
                "review":      getattr(rel, "review_state", "unknown"),
            })

    return conflicts


def _extract_causal_hints(
    facts: list[dict[str, Any]],
    graph: Optional["CausalGraph"] = None,
) -> list[dict[str, Any]]:
    """
    TASK-08/P0: read-only regex extractor for causal proposals.

    Логика:
    - Если claim факта содержит каузальный паттерн → он "каузально нагружен"
    - Каузально нагруженные факты образуют AnalysisProposal для `implies`
    - QueryPipeline НИКОГДА не вызывает graph.add_relation()
    - Отдельный ingestion/review path позже может принять или отклонить proposal

    ``graph`` remains an ignored compatibility parameter for callers that used
    the old helper.  Supplying it cannot grant write authority.
    """
    causal_facts = [
        f for f in facts
        if _CAUSAL_REGEX.search(f.get("claim", ""))
    ]

    if len(causal_facts) < 2:
        return []

    hints: list[dict[str, Any]] = []
    for i, fa in enumerate(causal_facts):
        for fb in causal_facts[i + 1:]:
            proposal_key = "\0".join(
                (str(fa["fact_id"]), str(fb["fact_id"]), "implies", "autolinker")
            )
            proposal_id = (
                "causal-proposal:"
                + hashlib.sha256(proposal_key.encode("utf-8")).hexdigest()[:20]
            )
            hints.append({
                "proposal_id": proposal_id,
                "relation_id": None,
                "from":        fa["fact_id"],
                "from_claim":  fa["claim"][:60],
                "to":          fb["fact_id"],
                "to_claim":    fb["claim"][:60],
                "type":        "implies",
                "status":      "hypothetical",
                "confidence":  0.35,
                "review":      "pending",
                "disposition": "proposal_only",
            })
            logger.debug(
                "Causal proposal: %s → %s (implies, pending)",
                fa["fact_id"], fb["fact_id"],
            )

    return hints


# ─── NGramIndex singleton (Sprint 2a) ─────────────────────────────────────────
# Инициализируется один раз при загрузке модуля.
# Если FTS5 недоступен — _NGRAM_INDEX.available == False, pipeline пропускает.
_NGRAM_INDEX: Optional["NGramIndex"] = None
if _NGRAM_AVAILABLE:
    try:
        _NGRAM_INDEX = NGramIndex()
        logger.info("pipeline: NGramIndex инициализирован (FTS5 available: %s)",
                    _NGRAM_INDEX.available)
    except Exception as exc:
        logger.warning("pipeline: NGramIndex init failed: %s → fallback на полный поиск", exc)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

_TOKEN_SPLIT = re.compile(r"[\s\u2013\u2014\-_/]+")
_TOKEN_STRIP = ".,!?;:()[]{}\"'`"


def tokenize(text: str) -> list[str]:
    """Разбить текст на токены с поддержкой em-dash, en-dash, пунктуации."""
    return [t for raw in _TOKEN_SPLIT.split(text)
            if (t := raw.lower().strip(_TOKEN_STRIP))]


# ─── LEGACY BM25 (для DATABASE fallback) ──────────────────────────────────────
# Остаётся для обратной совместимости с тестами и DATABASE-режимом.
# При работе с реальным store используется HybridRetriever (Sprint 2a).

class BM25:
    """BM25 Okapi — legacy ранкер для DATABASE mock."""
    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self.N = len(corpus)
        self.corpus_tokens = corpus
        dl = [len(doc) for doc in corpus]
        self.avgdl = sum(dl) / self.N if self.N else 1.0
        self.dl = dl
        df: dict[str, int] = {}
        for doc in corpus:
            for term in set(doc):
                df[term] = df.get(term, 0) + 1
        self.df = df
        self.idf: dict[str, float] = {
            term: math.log((self.N - freq + 0.5) / (freq + 0.5) + 1)
            for term, freq in df.items()
        }

    def score(self, doc_idx: int, query_terms: list[str]) -> float:
        doc = self.corpus_tokens[doc_idx]
        tf_map = Counter(doc)
        doc_len = self.dl[doc_idx]
        total = 0.0
        for term in query_terms:
            if term not in self.idf:
                continue
            tf = tf_map.get(term, 0)
            if tf == 0:
                continue
            tf_norm = (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            )
            total += self.idf[term] * tf_norm
        return total


_DB_TOKENS: list[list[str]] = [tokenize(str(item["text"])) for item in _DATABASE_DEV_ONLY]
_BM25_INDEX = BM25(_DB_TOKENS)


# ─── RETRIEVAL ────────────────────────────────────────────────────────────────

def _cogdist_enabled() -> bool:
    try:
        from core.runtime_flags import is_cognitive_distance_enabled

        return is_cognitive_distance_enabled()
    except Exception:  # noqa: BLE001
        return False


def _maybe_cognitive_rerank(
    rows: list[dict[str, Any]], k: int
) -> list[dict[str, Any]]:
    """Opt-in re-rank of retrieval rows by cognitive_distance, then truncate to k.

    Flag off ⇒ returns rows[:k] unchanged (byte-identical). Read-only; never raises —
    on any failure falls back to the incoming order. Candidates are ENRICHED from the
    store first (real epistemic_state / relations / temporal), because the retrieval
    rows hardcode epistemic_state="Observed". v0 runs without a query embedding, so the
    semantic axis is 0 and the working signal is epistemic + relational + temporal
    (usage/semantic axes are inert until those fields exist in the schema).
    """
    if not _cogdist_enabled() or not rows:
        return rows[:k]
    try:
        from core.cognitive_distance import rank_by_distance

        ids = [str(r.get("id")) for r in rows if r.get("id")]
        enriched_by_id = {f.get("fact_id"): f for f in get_facts_by_ids(ids)} if ids else {}
        facts = []
        for r in rows:
            src = enriched_by_id.get(r.get("id"), {})
            facts.append({
                "fact_id": r.get("id"),
                "epistemic_state": src.get("epistemic_state", r.get("epistemic_state", "Observed")),
                "confidence": src.get("confidence", r.get("confidence", 0.5)),
                "relations": src.get("relations", []),
                "t_event_valid_start": src.get("t_event_valid_start"),
                "t_event_valid_end": src.get("t_event_valid_end"),
                "_row": r,  # carry original row through
            })
        ranked = rank_by_distance(facts, query_vector=None, top_k=k)
        out = []
        for f in ranked:
            row = dict(f["_row"])
            row["cognitive_distance"] = f.get("cognitive_distance")
            out.append(row)
        return out
    except Exception as exc:  # noqa: BLE001 — re-rank must never break retrieval
        logger.debug("cognitive rerank skipped: %s", exc)
        return rows[:k]


def _narrow_candidates(
    query: str, domain: str | None
) -> list[dict[str, Any]]:
    """Шаг 0: NGramIndex pre-filter → filtered_facts.

    Общий для lexical и hybrid маршрутов — единственное место, где кандидаты
    сужаются перед ранжированием (NGram → domain filter).

    TASK-06: вместо get_all_facts() (SELECT * — вся база в RAM) используем
    get_fact_ids() (SELECT fact_id — легко) + get_facts_by_ids() для кандидатов.
    При NGramIndex: загружаем только отфильтрованные N фактов.
    При отсутствии NGramIndex: cap=1000 (вместо неограниченного SELECT *).
    """
    _RETRIEVE_CAP = 1_000

    if _NGRAM_INDEX is not None and _NGRAM_INDEX.available:
        candidate_ids = list(_NGRAM_INDEX.query(query, limit=50))
        if candidate_ids:
            filtered_facts = get_facts_by_ids(candidate_ids)
            if not filtered_facts:
                filtered_facts = get_facts_by_ids(get_fact_ids(limit=_RETRIEVE_CAP))
                logger.debug("NGramIndex: кандидаты не в store → bounded fallback")
            else:
                logger.debug("NGramIndex(FTS5): %d кандидатов (прямой путь)", len(candidate_ids))
        else:
            filtered_facts = get_facts_by_ids(get_fact_ids(limit=_RETRIEVE_CAP))
            logger.debug("NGramIndex: 0 кандидатов → bounded fallback (cap=%d)", _RETRIEVE_CAP)
    else:
        filtered_facts = get_facts_by_ids(get_fact_ids(limit=_RETRIEVE_CAP))

    if not filtered_facts:
        return []

    if domain:
        from core.domain_tags import filter_facts_by_domain, normalize_domain

        filtered_facts = filter_facts_by_domain(
            filtered_facts, normalize_domain(domain)
        )

    return filtered_facts


def _bm25_rank_facts(
    filtered_facts: list[dict[str, Any]],
    query: str,
    k: int,
    *,
    origin: str = "bm25_fallback",
    allow_cognitive_rerank: bool = True,
) -> list[dict[str, Any]]:
    corpus = [tokenize(f.get("claim", "")) for f in filtered_facts]
    bm25 = BM25(corpus)
    query_terms = tokenize(query)
    query_term_set = set(query_terms)
    scored = []
    for i, fact in enumerate(filtered_facts):
        claim_tokens = set(tokenize(fact.get("claim", "")))
        if not (claim_tokens & query_term_set):
            continue
        score = bm25.score(i, query_terms)
        retrieval_score = round(max(score, 0.001) * fact.get("confidence", 1.0), 4)
        scored.append({
            "id": fact["fact_id"],
            "text": fact.get("claim", ""),
            "source": fact.get("source", "unknown"),
            "confidence": fact.get("confidence", 0.5),
            "retrieval_score": retrieval_score,
            "epistemic_state": "Observed",
            "origin": origin,
            "retrieval_mode": "lexical" if origin == "bm25_lexical" else "hybrid",
        })
    scored.sort(key=lambda x: x["retrieval_score"], reverse=True)
    if not allow_cognitive_rerank:
        return scored[:k]
    return _maybe_cognitive_rerank(scored, k)


def _retrieve_from_store(
    query: str,
    k: int = 3,
    domain: str | None = None,
    retrieval_mode: str = "hybrid",
    max_hops: int = 1,
    allow_cognitive_rerank: bool = True,
) -> list[dict[str, Any]]:
    if retrieval_mode == "none" or not query or not query.strip():
        return []
    filtered_facts = _narrow_candidates(query, domain)
    if not filtered_facts:
        return []
    if retrieval_mode == "lexical":
        return _bm25_rank_facts(
            filtered_facts,
            query,
            k,
            origin="bm25_lexical",
            allow_cognitive_rerank=allow_cognitive_rerank,
        )
    if _HYBRID_AVAILABLE:
        try:
            retriever = _get_hybrid_retriever(filtered_facts)
            if retriever is not None:
                fetch_k = k * 3 if allow_cognitive_rerank and _cogdist_enabled() else k
                results: list[RetrievedFact] = retriever.retrieve(query, top_k=fetch_k)
                out = []
                for r in results:
                    out.append({
                        "id": r.fact_id,
                        "text": r.claim,
                        "source": r.source,
                        "confidence": r.confidence,
                        "retrieval_score": round(r.final_score, 4),
                        "metadata": r.metadata or {},
                        "epistemic_state": "Observed",
                        "origin": "hybrid_retriever",
                        "retrieval_mode": "hybrid",
                    })
                if not allow_cognitive_rerank:
                    return out[:k]
                return _maybe_cognitive_rerank(out, k)
        except Exception as exc:
            logger.warning("HybridRetriever failed: %s → fallback на BM25", exc)
    return _bm25_rank_facts(
        filtered_facts,
        query,
        k,
        origin="bm25_fallback",
        allow_cognitive_rerank=allow_cognitive_rerank,
    )


def retrieve(
    query: str,
    k: int = 3,
    database: list[dict[str, Any]] | None = None,
    domain: str | None = None,
) -> list[dict[str, Any]]:
    import os
    eff_k = k
    execution_kwargs: dict[str, Any] = {"k": k}
    try:
        from core.runtime_flags import is_budget_planner_enabled
        if is_budget_planner_enabled():
            from core.budget_planner import plan as _budget_plan
            retrieval_plan = _budget_plan(query, base_k=k)
            eff_k = retrieval_plan.k
            execution_kwargs = retrieval_plan.to_execution_kwargs()
    except Exception as exc:  # noqa: BLE001
        logger.debug("budget planner skipped: %s", exc)
    if database is not None:
        return _retrieve_from_database(query, eff_k, database)
    store_results = _retrieve_from_store(query, domain=domain, **execution_kwargs)
    if store_results:
        return store_results
    if os.getenv("VELANTRIM_DEV_MOCK", "false").lower() == "true":
        logger.debug("retrieve: VELANTRIM_DEV_MOCK=true → DATABASE mock fallback")
        return _retrieve_from_database(query, eff_k, _DATABASE_DEV_ONLY)
    logger.debug("retrieve: store пустой, возвращаем []")
    return []


def _retrieve_from_database(
    query: str,
    k: int,
    db: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    query_terms = tokenize(query)
    if not query_terms:
        return []
    corpus = [tokenize(item["text"]) for item in db]
    bm25 = BM25(corpus)
    scored: list[dict[str, Any]] = []
    for i, item in enumerate(db):
        score = bm25.score(i, query_terms)
        if score <= 0:
            continue
        retrieval_score = round(score * item.get("confidence", 1.0), 4)
        scored.append({
            **item,
            "retrieval_score": retrieval_score,
            "epistemic_state": "Observed",
            "origin": "database_bm25",
        })
    scored.sort(key=lambda x: x["retrieval_score"], reverse=True)
    result = scored[:k]
    if len(result) < k:
        logger.debug("retrieve: запрошено k=%d, найдено %d", k, len(result))
    return result


def _is_safe_user_report(fact: dict[str, Any]) -> bool:
    return bool(
        fact.get("canonical_record")
        and fact.get("epistemic_state") == "Observed"
        and fact.get("origin_type") == "USER_REPORTED"
        and fact.get("claim_type") != "WORLD_FACT"
        and str(fact.get("source") or "").strip().lower() not in {"", "unknown"}
    )


def build_facts_pack(
    retrieved: list[dict[str, Any]],
    query: str,
    database: list[dict[str, Any]] | None = None,
    cognitive_mode: str | None = None,
    require_policy: bool = False,
) -> dict[str, Any]:
    raw_facts: list[dict[str, Any]] = []
    for item in retrieved:
        fact_id = item.get("id") or item.get("fact_id")
        if not fact_id:
            continue
        persisted = get_fact(fact_id) or {}
        canonical_record = bool(persisted)
        item_metadata = item.get("metadata", {})
        if not isinstance(item_metadata, dict):
            item_metadata = {}
        persisted_metadata = persisted.get("metadata", item_metadata)
        if not isinstance(persisted_metadata, dict):
            persisted_metadata = item_metadata
        claim = persisted.get("claim") if canonical_record else item.get("text") or item.get("claim", "")
        source = persisted.get("source") if canonical_record else item.get("source", "unknown")
        confidence = persisted.get("confidence") if canonical_record else item.get("confidence", 0.5)
        raw_facts.append({
            "fact_id": fact_id,
            "claim": claim or "",
            "source": source or "unknown",
            "confidence": confidence,
            "retrieval_score": item.get("retrieval_score", 0.0),
            "epistemic_state": persisted.get(
                "epistemic_state", item.get("epistemic_state", "Observed")
            ),
            "claim_type": persisted.get("claim_type", item.get("claim_type", "UNKNOWN")),
            "origin_type": persisted.get("origin_type", item.get("origin_type", "UNKNOWN")),
            "metadata": persisted_metadata,
            "canonical_record": canonical_record,
        })
    if _FACTS_PACK_BUILDER_AVAILABLE:
        mode = (cognitive_mode or "MVP").upper()
        if mode == "MVP" or mode not in COGNITIVE_MODE_POLICIES:
            mode = "BALANCED"
        try:
            fp = FactsPackBuilder(mode).add_facts(raw_facts).build(query)
            metadata_by_fact_id = {
                f.get("fact_id"): f.get("metadata", {})
                for f in raw_facts if f.get("fact_id")
            }
            modality_by_fact_id = {
                f.get("fact_id"): (f.get("claim_type", "UNKNOWN"), f.get("origin_type", "UNKNOWN"))
                for f in raw_facts if f.get("fact_id")
            }
            canonical_by_fact_id = {
                f.get("fact_id"): bool(f.get("canonical_record"))
                for f in raw_facts if f.get("fact_id")
            }
            facts = [{
                "fact_id": pf.fact_id,
                "claim": pf.claim,
                "source": pf.source,
                "confidence": pf.confidence,
                "retrieval_score": pf.retrieval_score,
                "epistemic_state": pf.epistemic_state,
                "claim_type": modality_by_fact_id.get(pf.fact_id, ("UNKNOWN", "UNKNOWN"))[0],
                "origin_type": modality_by_fact_id.get(pf.fact_id, ("UNKNOWN", "UNKNOWN"))[1],
                "metadata": metadata_by_fact_id.get(pf.fact_id, {}),
                "canonical_record": canonical_by_fact_id.get(pf.fact_id, False),
                "truth_status": "VERIFIED" if pf.epistemic_state == "Validated" else "UNVERIFIED",
            } for pf in fp.facts]
            included_ids = {f["fact_id"] for f in facts}
            reported_added = 0
            for raw in raw_facts:
                if raw["fact_id"] in included_ids or not _is_safe_user_report(raw):
                    continue
                facts.append({
                    "fact_id": raw["fact_id"],
                    "claim": raw["claim"],
                    "source": raw["source"],
                    "confidence": raw["confidence"],
                    "retrieval_score": raw["retrieval_score"],
                    "epistemic_state": raw["epistemic_state"],
                    "claim_type": raw["claim_type"],
                    "origin_type": raw["origin_type"],
                    "metadata": raw["metadata"],
                    "canonical_record": True,
                    "truth_status": "UNVERIFIED",
                    "reported_only": True,
                })
                reported_added += 1
            if fp.warning and not facts:
                logger.warning("FactsPackBuilder [%s]: %s", mode, fp.warning)
            return {
                "facts": facts,
                "query": query,
                "total": len(facts),
                "excluded": max(0, len(fp.excluded_facts) - reported_added),
                "mode": mode,
            }
        except Exception as exc:
            if require_policy:
                raise FactsPackPolicyUnavailableError(
                    f"FactsPackBuilder failed in required-policy mode: {exc}"
                ) from exc
            logger.warning("FactsPackBuilder failed (%s) → fallback: %s", mode, exc)
    elif require_policy:
        raise FactsPackPolicyUnavailableError(
            "FactsPackBuilder is unavailable in required-policy mode"
        )
    raw_facts.sort(key=lambda x: x["retrieval_score"], reverse=True)
    for f in raw_facts:
        f["truth_status"] = "VERIFIED" if f["epistemic_state"] == "Validated" else "UNVERIFIED"
    return {"facts": raw_facts, "query": query, "total": len(raw_facts)}


def guardian(
    facts_pack: dict[str, Any],
    trace: list[dict[str, Any]],
) -> tuple[bool, str | None]:
    facts = facts_pack.get("facts", [])
    if not facts:
        return False, "FactsPack пустой"
    if not trace:
        return False, "Trace пустой — провенанс отсутствует"
    trace_ids = {el.get("fact_id") for el in trace}
    for fact in facts:
        fid = fact.get("fact_id")
        if not fid:
            return False, f"Факт без fact_id: {fact}"
        if fid not in trace_ids:
            return False, f"Факт {fid} не покрыт trace"
        if not fact.get("claim"):
            return False, f"Факт без claim: {fid}"
        if not fact.get("source"):
            return False, f"Факт без source: {fid}"
    return True, None


def truth_gate(
    facts_pack: dict[str, Any],
    min_confidence: float = 0.5,
    mode: str | None = None,
) -> tuple[bool, str | None]:
    facts = facts_pack.get("facts", [])
    if not facts:
        return False, "Нет фактов для верификации"
    requested_mode = (mode or "MVP").upper()
    use_real_gate = requested_mode != "MVP"
    if use_real_gate:
        if not _REAL_TRUTH_GATE_AVAILABLE:
            reason = "real_truth_gate_unavailable"
            logger.error("TruthGate BLOCKED: %s", reason)
            return False, reason
        try:
            cognitive_mode = CognitiveMode(requested_mode)
        except ValueError:
            reason = f"unknown_cognitive_mode:{requested_mode}"
            logger.warning("TruthGate BLOCKED: %s", reason)
            return False, reason
    if use_real_gate:
        gate = TruthGate(_GLOBAL_STORE)
        failed_verdicts = []
        for fact in facts:
            if (
                fact.get("canonical_record")
                and fact.get("epistemic_state") in {"Validated", "ImmutableCore"}
            ):
                continue
            if _is_safe_user_report(fact):
                continue
            verdict = gate.evaluate(fact, mode=cognitive_mode)
            if not verdict.passed:
                failed_verdicts.append(f"{fact.get('fact_id')}: {verdict.reason}")
        if failed_verdicts:
            reason = "; ".join(failed_verdicts[:3])
            logger.warning("TruthGate(%s) BLOCKED: %s", mode, reason)
            return False, reason
        logger.debug("TruthGate(%s) PASSED: %d фактов", mode, len(facts))
        return True, None
    from core.validators import validate_confidence, validate_source
    for fact in facts:
        ok_src, err_src = validate_source(fact.get("source"))
        if not ok_src:
            reason = f"Факт {fact.get('fact_id')}: {err_src}"
            logger.warning("truth_gate BLOCKED: %s", reason)
            return False, reason
        conf = fact.get("confidence", 0)
        ok_conf, err_conf = validate_confidence(conf)
        if not ok_conf:
            reason = f"Факт {fact.get('fact_id')}: {err_conf}"
            logger.warning("truth_gate BLOCKED: %s", reason)
            return False, reason
        if conf <= 0:
            reason = f"Confidence нулевая или отрицательная: {fact.get('fact_id')}"
            logger.warning("truth_gate BLOCKED: %s", reason)
            return False, reason
        if conf < min_confidence:
            reason = (
                f"Confidence {conf:.3f} < порога {min_confidence}: "
                f"{fact.get('fact_id')}"
            )
            logger.warning("truth_gate BLOCKED: %s", reason)
            return False, reason
    return True, None


def _essence_relations_for(
    facts: list[dict[str, Any]],
    cg: Optional["CausalGraph"] = None,
) -> list[dict[str, Any]]:
    if cg is None:
        try:
            cg = _get_causal_graph()
        except Exception:  # noqa: BLE001
            cg = None
    if cg is None:
        return []
    ids = {str(f.get("fact_id")) for f in facts if f.get("fact_id")}
    if len(ids) < 2:
        return []
    rels: list[dict[str, Any]] = []
    seen: set = set()
    from core.knowledge_linker import relation_is_causal_for_essence
    for fid in ids:
        try:
            for r in cg.get_relations_from(fid):
                tgt = str(getattr(r, "to_fact_id", ""))
                if tgt not in ids or not r.is_reliable():
                    continue
                meta = getattr(r, "metadata", None) or {}
                if not relation_is_causal_for_essence(r.relation_type, meta):
                    continue
                key = (fid, tgt, r.relation_type)
                if key in seen:
                    continue
                seen.add(key)
                rels.append({
                    "source_id": fid,
                    "target_id": tgt,
                    "relation_type": r.relation_type,
                    "edge_basis": meta.get("edge_basis"),
                    "confidence": getattr(r, "confidence", None),
                    "evidence": meta.get("evidence"),
                })
        except Exception:  # noqa: BLE001
            continue
    return rels


_CLAIM_TYPE_LABELS: dict = {
    "EMOTION": "Вы сообщали о чувстве",
    "OPINION": "Ваше мнение",
    "INTERPRETATION": "Ваша интерпретация",
    "USER_EXPERIENCE": "Из вашего опыта",
    "PREFERENCE": "Ваше предпочтение",
    "GOAL": "Ваша цель",
    "SYSTEM_NOTE": "[Служебная заметка]",
    "WORLD_FACT": None,
    "UNKNOWN": None,
}


def _truth_policy_enabled() -> bool:
    try:
        from core.feature_config import get_config
        return bool(get_config().app.enable_truth_policy)
    except Exception:  # noqa: BLE001
        return False


def _graph_expansion_enabled() -> bool:
    try:
        from core.feature_config import get_config
        return bool(getattr(get_config().app, "enable_graph_expansion", False))
    except Exception:  # noqa: BLE001
        return False


def _graph_expansion_depth() -> int:
    import os
    try:
        d = int(os.getenv("VELANTRIM_GRAPH_EXPANSION_DEPTH", "1"))
    except ValueError:
        d = 1
    return max(1, min(3, d))


def _task_routing_enabled() -> bool:
    try:
        from core.feature_config import get_config
        return bool(getattr(get_config().app, "enable_task_routing", False))
    except Exception:  # noqa: BLE001
        return False


def _expand_with_graph_neighbors(
    facts: list[dict], max_neighbors: int = 8, depth: int | None = None,
) -> list[dict]:
    cg = _get_causal_graph()
    if cg is None or not facts:
        return facts
    if depth is None:
        depth = _graph_expansion_depth()
    have = {f.get("fact_id") for f in facts}
    out = list(facts)
    frontier = [str(f.get("fact_id")) for f in facts if f.get("fact_id")]
    added = 0
    for _level in range(max(1, depth)):
        if added >= max_neighbors or not frontier:
            break
        next_frontier: list[str] = []
        for fid in frontier:
            if added >= max_neighbors:
                break
            try:
                rels = cg.get_relations_from(fid)
            except Exception:  # noqa: BLE001
                continue
            for rel in rels:
                if added >= max_neighbors:
                    break
                tgt = getattr(rel, "to_fact_id", None)
                if not tgt or tgt in have:
                    continue
                try:
                    if not rel.is_reliable():
                        continue
                    meta = getattr(rel, "metadata", None) or {}
                    from core.knowledge_linker import relation_is_causal_for_essence
                    if not relation_is_causal_for_essence(rel.relation_type, meta):
                        continue
                except Exception:  # noqa: BLE001
                    continue
                nf = get_fact(tgt)
                if not nf or nf.get("epistemic_state") not in {"Validated", "Supported"}:
                    continue
                have.add(tgt)
                meta = nf.get("metadata")
                out.append({
                    "fact_id": tgt,
                    "claim": nf.get("claim", ""),
                    "source": nf.get("source", "unknown"),
                    "confidence": float(nf.get("confidence", 0.5)),
                    "retrieval_score": 0.0,
                    "epistemic_state": nf.get("epistemic_state", "Validated"),
                    "claim_type": nf.get("claim_type", "UNKNOWN"),
                    "origin_type": nf.get("origin_type", "UNKNOWN"),
                    "metadata": meta if isinstance(meta, dict) else {},
                    "truth_status": "VERIFIED" if nf.get("epistemic_state") == "Validated" else "UNVERIFIED",
                    "canonical_record": True,
                    "graph_expanded": True,
                })
                next_frontier.append(tgt)
                added += 1
        frontier = next_frontier
    return out


def _label_claim_for_answer(fact: dict) -> str:
    ct = fact.get("claim_type") or "UNKNOWN"
    label = _CLAIM_TYPE_LABELS.get(ct)
    claim = fact.get("claim", "")
    if label:
        return f"[{label}]: {claim}"
    return claim


def generate_answer(
    facts_pack: dict[str, Any],
    trace: list[dict[str, Any]],
) -> dict[str, Any]:
    validated_facts = [
        f for f in facts_pack["facts"]
        if (
            f.get("canonical_record", True)
            and f.get("epistemic_state") in {"Validated", "Supported"}
        )
    ]
    reported_facts = [f for f in facts_pack["facts"] if _is_safe_user_report(f)]
    answer_facts = validated_facts + [f for f in reported_facts if f not in validated_facts]
    if not answer_facts:
        logger.info(
            "generate_answer: no Validated/Supported evidence; returning bounded answer"
        )
        return {
            "answer": "Недостаточно подтверждённых локальных данных.",
            "facts": [],
            "candidate_facts": list(facts_pack["facts"]),
            "trace": trace,
            "trace_fmt": format_trace(trace),
            "total_facts": 0,
            "insufficient_evidence": True,
            "reason_code": "insufficient_validated_local_evidence",
        }
    from core.essence import compose_essence, is_essence_enabled
    if is_essence_enabled():
        do_expand = _graph_expansion_enabled()
        task_type = None
        if _task_routing_enabled():
            from core.task_type import REASONING_TYPES, classify_task_type
            task_type = classify_task_type(facts_pack.get("query", ""))
            do_expand = task_type in REASONING_TYPES
        facts_for_essence = (
            _expand_with_graph_neighbors(answer_facts) if do_expand else answer_facts
        )
        relations = _essence_relations_for(facts_for_essence)
        essence = compose_essence(facts_for_essence, relations)
        result = {
            "answer": essence.short_answer,
            "essence": essence.to_dict(),
            "facts": facts_for_essence,
            "trace": trace,
            "trace_fmt": format_trace(trace),
            "total_facts": len(facts_for_essence),
        }
        if task_type is not None:
            result["task_type"] = task_type
        return result
    answer = " | ".join(_label_claim_for_answer(f) for f in answer_facts)
    return {
        "answer": answer,
        "facts": answer_facts,
        "trace": trace,
        "trace_fmt": format_trace(trace),
        "total_facts": len(answer_facts),
        "has_subjective": any(
            f.get("claim_type") not in (None, "UNKNOWN", "WORLD_FACT")
            for f in answer_facts
        ),
    }


def run_with_notebook(
    query: str,
    session_id: str | None = None,
    cognitive_mode: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    result = run(query, cognitive_mode=cognitive_mode, domain=domain)
    if session_id:
        try:
            from core.working_notebook import (
                get_notebook,
                is_working_notebook_enabled,
                notebook_directive_for,
            )
            if is_working_notebook_enabled():
                result["notebook_directive"] = notebook_directive_for(session_id, query)
                result["notebook"] = get_notebook(session_id).to_dict()
        except Exception as exc:  # noqa: BLE001
            logger.debug("working_notebook wiring: %s", exc)
    return result


def run(
    query: str,
    cognitive_mode: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    cross_plan = None
    try:
        from core.cross_domain import (
            get_cross_domain_layer,
            is_cross_domain_enabled,
            plan_query,
        )
        if is_cross_domain_enabled():
            cross_plan = plan_query(query, domain)
            retrieved, cross_plan = get_cross_domain_layer().retrieve(
                query, k=3, domain=domain, plan=cross_plan
            )
        else:
            retrieved = retrieve(query, domain=domain)
    except Exception as exc:  # noqa: BLE001
        logger.debug("cross_domain retrieve: %s", exc)
        retrieved = retrieve(query, domain=domain)
    if not retrieved:
        return _insufficient_evidence(query, reason_code="no_local_retrieval_results")
    _retrieval_mode = retrieved[0].get("retrieval_mode") if retrieved else None
    facts_pack = build_facts_pack(retrieved, query, cognitive_mode=cognitive_mode)
    if not facts_pack.get("facts"):
        return _insufficient_evidence(
            query,
            reason_code="no_policy_eligible_local_evidence",
            facts_pack=facts_pack,
        )
    trace_input = []
    for f in facts_pack["facts"]:
        trace_input.append({
            "id": f["fact_id"],
            "source": f["source"],
            "origin": "retrieval",
            "epistemic_state": f["epistemic_state"],
            "retrieval_score": f["retrieval_score"],
        })
    trace = build_trace(trace_input)
    guardian_ok, guardian_reason = guardian(facts_pack, trace)
    if not guardian_ok:
        return _blocked(f"Guardian: {guardian_reason}", query, facts_pack, trace)
    effective_mode = cognitive_mode or "BALANCED"
    gate_ok, gate_reason = truth_gate(facts_pack, mode=effective_mode)
    if not gate_ok:
        return _insufficient_evidence(
            query,
            reason_code="truth_gate_rejected",
            detail=gate_reason,
            facts_pack=facts_pack,
            trace=trace,
        )
    _modality = _truth_policy_enabled()
    for fact in facts_pack["facts"]:
        if _modality:
            ct = fact.get("claim_type") or "UNKNOWN"
            fact["truth_status"] = (
                "VERIFIED"
                if (fact["epistemic_state"] == "Validated" and ct == "WORLD_FACT")
                else "UNVERIFIED"
            )
        else:
            fact["truth_status"] = (
                "VERIFIED" if fact.get("epistemic_state") == "Validated" else "UNVERIFIED"
            )
    causal_hints: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    validated_for_cg = [
        f for f in facts_pack["facts"]
        if (
            f.get("canonical_record")
            and f.get("epistemic_state") in {"Validated", "Supported"}
        )
    ]
    causal_hints = _extract_causal_hints(validated_for_cg)
    cg = _get_causal_graph()
    if cg is not None:
        try:
            conflicts = _extract_conflicts(facts_pack["facts"], cg)
        except Exception as exc:
            logger.warning("Contradiction extraction failed (non-blocking): %s", exc)
    result = generate_answer(facts_pack, trace)
    if _retrieval_mode:
        result["retrieval_mode"] = _retrieval_mode
    if causal_hints:
        result["causal_hints"] = causal_hints
    if conflicts:
        result["conflicts"] = conflicts
        result["honesty_marker"] = "conflicts_detected"
    try:
        from core.response_guardian import GuardianDecision, apply_response_guardian
        rg = apply_response_guardian(
            result.get("answer") or "",
            facts_pack.get("facts", []),
            trace,
        )
        result["response_guardian"] = rg.to_dict()
        if rg.decision == GuardianDecision.REJECT and rg.response:
            result["answer"] = rg.response
            result["guardian_blocked"] = True
        elif rg.decision == GuardianDecision.WARN and rg.response:
            result["answer"] = rg.response
    except Exception as exc:
        logger.debug("response_guardian: %s", exc)
    try:
        from core.output_faithfulness import check_response_faithfulness
        fr = check_response_faithfulness(
            result.get("answer") or "", facts_pack.get("facts", [])
        )
        if fr is not None:
            result["faithfulness"] = fr.to_dict()
    except Exception as exc:
        logger.debug("output_faithfulness: %s", exc)
    try:
        from core.async_utils import run_coroutine_sync
        from core.exocortex_hooks import enrich_query_context
        exo = run_coroutine_sync(
            enrich_query_context(query, facts_pack.get("facts", []))
        )
        if exo.get("sections"):
            result["exocortex_sections"] = exo["sections"]
    except Exception as exc:  # noqa: BLE001
        logger.debug("exocortex enrich: %s", exc)
    if cross_plan is not None:
        try:
            from core.cross_domain import get_cross_domain_layer
            section = get_cross_domain_layer().annotate_facts(
                facts_pack.get("facts", []), cross_plan,
            )
            if section:
                section["causal_links"] = []
                section["relation_disposition"] = "proposal_only"
                result["cross_domain"] = section
        except Exception as exc:  # noqa: BLE001
            logger.debug("cross_domain annotate: %s", exc)
    try:
        from core.graph_lab_bridge import enrich_with_graph_lab
        gl_result = enrich_with_graph_lab(query, "", len(facts_pack.get("facts", [])))
        if gl_result and gl_result.get("available"):
            result["graph_lab"] = {
                "node_count": gl_result.get("node_count", 0),
                "edge_count": gl_result.get("edge_count", 0),
                "communities": len(gl_result.get("communities", [])),
                "cycles_found": len(gl_result.get("cycles", [])),
            }
    except Exception as exc:  # noqa: BLE001
        logger.debug("graph_lab: %s", exc)
    return result


def _insufficient_evidence(
    query: str,
    *,
    reason_code: str,
    detail: str | None = None,
    facts_pack: dict | None = None,
    trace: list | None = None,
) -> dict[str, Any]:
    return {
        "error": None,
        "answer": "Недостаточно подтверждённых локальных данных.",
        "query": query,
        "facts": [],
        "candidate_facts": facts_pack.get("facts", []) if facts_pack else [],
        "trace": trace or [],
        "total_facts": 0,
        "insufficient_evidence": True,
        "reason_code": reason_code,
        **({"detail": detail} if detail else {}),
    }


def _blocked(
    reason: str,
    query: str,
    facts_pack: dict | None = None,
    trace: list | None = None,
) -> dict[str, Any]:
    return {
        "error": reason,
        "answer": None,
        "query": query,
        "facts": facts_pack.get("facts", []) if facts_pack else [],
        "trace": trace or [],
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(f"HybridRetriever: {'✅' if _HYBRID_AVAILABLE else '❌ недоступен'}")
    print(f"NGramIndex:      {'✅' if (_NGRAM_INDEX and _NGRAM_INDEX.available) else '❌ недоступен'}")
    print(f"Real TruthGate:  {'✅' if _REAL_TRUTH_GATE_AVAILABLE else '❌ недоступен'}")
    queries = [
        "What is quantum entanglement?",
        "How does DNA work?",
        "Tell me about the Sun",
    ]
    for q in queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {q}")
        result = run(q, cognitive_mode="BALANCED")
        print(f"ANSWER: {result.get('answer', 'BLOCKED')}")
        if result.get("error"):
            print(f"ERROR:  {result['error']}")
        if result.get("trace_fmt"):
            print(result["trace_fmt"])
