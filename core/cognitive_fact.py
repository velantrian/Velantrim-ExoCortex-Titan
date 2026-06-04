"""
CognitiveFact v9.2 — единый объект факта (мост dict/SQLite → V10).

V8.7: +MemoryType (EPISODIC/SEMANTIC/PROCEDURAL — когнитивная типизация из Synapse).
Не заменяет store_fact; даёт типизацию и мапперы для API/тестов.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from core.memory import ESM_STATES


# ─── MemoryType (V8.7 Synapse P1-1) ────────────────────────────────────────

class MemoryType(str, Enum):
    """Когнитивная типизация памяти. Backward compatible: None → EPISODIC."""
    EPISODIC   = "episodic"    # события, диалоги, конкретные эпизоды
    SEMANTIC   = "semantic"    # факты, концепции, определения
    PROCEDURAL = "procedural"  # навыки, workflows, алгоритмы


def classify_memory_type(content: str, tags: list = None) -> MemoryType:
    """
    Rule-based классификация без LLM. Вызывается при store_fact.
    0 токенов. Backward compatible.
    """
    tags = tags or []
    c = (content or "").lower()
    if any(w in c for w in [
        "шаг", "процедура", "workflow", "алгоритм", "рецепт",
        "step", "procedure", "how to", "инструкция",
        "сначала", "затем", "после", "потом",
    ]):
        return MemoryType.PROCEDURAL
    if any(w in c for w in [
        "определение", "закон", "правило", "означает",
        "definition", "concept", "fact", "is a", "это",
        "является", "состоит из", "относится к",
    ]):
        return MemoryType.SEMANTIC
    return MemoryType.EPISODIC


@dataclass
class FactRelation:
    """Упрощённое ребро (полный CausalGraph — отдельно)."""

    relation_type: str
    target_fact_id: str
    relation_id: Optional[str] = None
    knowledge_status: str = "known"
    from_fact_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class CognitiveFact:
    """
    Нативный факт Velantrim (подмножество V10 spec, совместимо с L1 dict).
    """

    id: str
    canonical_text: str
    source: str
    epistemic_state: str = "Observed"
    confidence: float = 0.8

    # v8.7 P0: модальность и происхождение
    claim_type: str = "UNKNOWN"    # ClaimType.* — ЧТО это по природе
    origin_type: str = "UNKNOWN"   # OriginType.* — ОТКУДА пришло

    # v8.7 Synapse: когнитивная типизация (MemoryType.*)
    memory_type: str = "episodic"  # episodic | semantic | procedural

    # v8.7 Crystal: биологическая типизация узлов (Fuzzy-Trace Theory)
    # FACT | CONCEPT | PRINCIPLE | INVARIANT | DOMAIN
    # ортогонально memory_type и claim_type — разные измерения
    node_type: str = "FACT"

    # v8.7 Identity: ось «Я» vs «Мир» (self_axis 0..1)
    # 1.0 = это про меня, 0.0 = чистый факт о мире
    self_axis: float = 0.0

    # v8.7 Scope: в каких координатах истинен этот факт
    # personal_identity | world_fact | shared_knowledge | cultural_belief
    truth_scope: str = "world_fact"

    # v8.7 Traceability: связь с исходным сообщением
    source_message_id: Optional[str] = None
    source_session_id: Optional[str] = None

    # v8.7 Provenance: цепочка источников (всегда присутствует)
    provenance: List[str] = field(default_factory=list)

    raw_input: Optional[str] = None
    derived_from: Optional[str] = None

    t_event_valid_start: Optional[str] = None
    t_event_valid_end: Optional[str] = None
    t_ingestion_start: Optional[str] = None
    t_ingestion_end: Optional[str] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    relations: List[FactRelation] = field(default_factory=list)

    semantic_vector: Optional[List[float]] = None
    semantic_tokens: Optional[List[str]] = None
    usage_count: int = 0
    last_used_at: Optional[str] = None
    retrieval_scores: List[float] = field(default_factory=list)

    @property
    def domain(self) -> str:
        from core.domain_tags import normalize_domain

        return normalize_domain(
            self.metadata.get("domain") or self.metadata.get("content_domain")
        )

    @property
    def layer(self) -> Optional[int]:
        layer = self.metadata.get("layer")
        if layer is None:
            return None
        try:
            return int(layer)
        except (TypeError, ValueError):
            return None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["relations"] = [r.to_dict() for r in self.relations]
        d["domain"] = self.domain
        d["layer"] = self.layer
        return d

    def to_store_dict(self) -> Dict[str, Any]:
        """Формат для memory.store_fact / API fact."""
        return {
            "fact_id": self.id,
            "claim": self.canonical_text,
            "source": self.source,
            "confidence": self.confidence,
            "epistemic_state": self.epistemic_state,
            "claim_type": self.claim_type,
            "origin_type": self.origin_type,
            "metadata": self.metadata,
            "history": self.history,
            "derived_from": self.derived_from,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "t_event_valid_start": self.t_event_valid_start,
            "t_event_valid_end": self.t_event_valid_end,
            "t_ingestion_start": self.t_ingestion_start,
            "t_ingestion_end": self.t_ingestion_end,
        }


def _parse_metadata(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def cognitive_fact_from_store(
    fact: Dict[str, Any],
    *,
    raw_input: Optional[str] = None,
    relations: Optional[List[FactRelation]] = None,
) -> CognitiveFact:
    """Собрать CognitiveFact из dict get_fact / get_all_facts."""
    meta = _parse_metadata(fact.get("metadata"))
    hist = fact.get("history") or []
    if isinstance(hist, str):
        try:
            hist = json.loads(hist)
        except json.JSONDecodeError:
            hist = []

    state = fact.get("epistemic_state", "Observed")
    if state not in ESM_STATES:
        state = "Observed"

    from core.validators import normalize_claim_type, normalize_origin_type
    return CognitiveFact(
        id=str(fact.get("fact_id") or fact.get("id") or ""),
        canonical_text=str(fact.get("claim") or ""),
        source=str(fact.get("source") or "unknown"),
        epistemic_state=state,
        confidence=float(fact.get("confidence") or 0.5),
        claim_type=normalize_claim_type(fact.get("claim_type")),
        origin_type=normalize_origin_type(fact.get("origin_type")),
        raw_input=raw_input,
        derived_from=fact.get("derived_from"),
        t_event_valid_start=fact.get("t_event_valid_start"),
        t_event_valid_end=fact.get("t_event_valid_end"),
        t_ingestion_start=fact.get("t_ingestion_start"),
        t_ingestion_end=fact.get("t_ingestion_end"),
        created_at=fact.get("created_at"),
        updated_at=fact.get("updated_at"),
        metadata=meta,
        history=hist if isinstance(hist, list) else [],
        relations=list(relations or []),
        retrieval_scores=list(fact.get("retrieval_scores") or []),
    )


def store_dict_from_cognitive(cf: CognitiveFact) -> Dict[str, Any]:
    """Обратный маппер для записи в L1."""
    return cf.to_store_dict()


def load_relations_for_fact(fact_id: str, limit: int = 20) -> List[FactRelation]:
    """Подтянуть рёбра CausalGraph для факта (v9.7 preview, спринт 3.3)."""
    if not fact_id or limit <= 0:
        return []

    out: List[FactRelation] = []
    seen: set[str] = set()

    def _append(edge: Any, *, default_from: str) -> None:
        rid = getattr(edge, "relation_id", None) or ""
        key = rid or f"{getattr(edge, 'from_fact_id', default_from)}:{getattr(edge, 'to_fact_id', '')}:{getattr(edge, 'relation_type', '')}"
        if key in seen:
            return
        seen.add(key)
        out.append(
            FactRelation(
                relation_id=rid or None,
                relation_type=getattr(edge, "relation_type", "implies"),
                from_fact_id=getattr(edge, "from_fact_id", default_from),
                target_fact_id=getattr(edge, "to_fact_id", ""),
                knowledge_status=getattr(edge, "knowledge_status", "known"),
            )
        )

    try:
        from core.causal_graph import get_causal_graph

        cg = get_causal_graph()
        for e in cg.get_relations_from(fact_id) + cg.get_relations_to(fact_id):
            _append(e, default_from=fact_id)
            if len(out) >= limit:
                break
    except Exception:
        return out[:limit]

    return out[:limit]


def is_relations_preview_enabled() -> bool:
    """Preview relations[] в CognitiveFact (3.3)."""
    try:
        from core.feature_config import get_config

        cfg = get_config().app
        return bool(cfg.enable_cognitive_fact and cfg.enable_causal_graph)
    except Exception:
        return False


__all__ = [
    "CognitiveFact",
    "FactRelation",
    "cognitive_fact_from_store",
    "is_relations_preview_enabled",
    "load_relations_for_fact",
    "store_dict_from_cognitive",
]
