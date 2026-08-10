"""
🧬 core/causal_graph.py — Velantrim Causal Graph (Patch 13 v2)
===============================================================
От памяти к пониманию: типизированные каузальные отношения между фактами.

12 типов отношений покрывают 90% человеческого reasoning.
Каждое ребро несёт knowledge_status — система знает чего она НЕ знает.

Спек: VELANTRIM_CAUSAL_GRAPH_SPEC_v2.md
Version: v8.5.0
"""
from __future__ import annotations

import json
import logging
import math
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime

from core.causal_relation_audit import (
    EVENT_RELATION_CREATED,
    EVENT_RELATION_REMOVED,
    append_relation_event,
    ensure_causal_audit_ready,
)
from core.write_gate import ensure_writes_allowed

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Константы
# ═══════════════════════════════════════════════════════════════════════════════

# ─── Relation type ontology ───────────────────────────────────────────────────
#
# Архитектурное различение, введённое в v8.5.2 (Claude audit):
#
#   FORWARD_RELATION_TYPES   = типы, которые пользователь может передать
#                              в add_relation() напрямую (15 типов).
#   BACKWARD_RELATION_TYPES  = типы, которые создаются автоматически как
#                              inverse_of forward-отношений. Пользователь
#                              их НЕ передаёт напрямую — это нарушение
#                              API-контракта.
#   VALID_RELATION_TYPES     = объединение, проверка на storage-уровне
#                              (что вообще может оказаться в БД).
#
# До v8.5.2 был один frozenset VALID_RELATION_TYPES без BACKWARD-типов.
# В add_relation() условие `if inverse_type in VALID_RELATION_TYPES`
# было ВСЕГДА False для caused_by/prevented_by/required_by/enabled_by/
# implied_by/composed_of → авто-inverse рёбра тихо НЕ сохранялись.
# Результат: 6 из 12 backward-обходов графа физически невозможны.
# Тест test_causal_chain_depth_3 падал именно поэтому.
#
FORWARD_RELATION_TYPES = frozenset({
    "causes", "prevents", "requires", "enables",
    "implies", "contradicts", "generalizes", "specializes",
    "precedes", "follows", "composes", "analogous_to",
    "becomes",
    "affords",
    "inhabited_by",
})

BACKWARD_RELATION_TYPES = frozenset({
    "caused_by",
    "prevented_by",
    "required_by",
    "enabled_by",
    "implied_by",
    "composed_of",
})

VALID_RELATION_TYPES = FORWARD_RELATION_TYPES | BACKWARD_RELATION_TYPES

VALID_KNOWLEDGE_STATUSES = frozenset({
    "known", "inferred", "hypothetical", "unknown",
})

VALID_INFERENCE_SOURCES = frozenset({
    "manual", "autolinker", "counterfactual_engine",
    "llm_extraction", "atlas_sync", "affordance_inference",
    "cross_domain",
})

VALID_TRUTH_STATUSES = frozenset({"validated", "hypothesis", "pending"})
VALID_REVIEW_STATES = frozenset({"approved", "pending", "rejected"})

INVERSE_RELATIONS: dict[str, str] = {
    "causes":       "caused_by",
    "prevents":     "prevented_by",
    "requires":     "required_by",
    "enables":      "enabled_by",
    "implies":      "implied_by",
    "generalizes":  "specializes",
    "specializes":  "generalizes",
    "precedes":     "follows",
    "follows":      "precedes",
    "composes":     "composed_of",
    "contradicts":  "contradicts",
    "analogous_to": "analogous_to",
}

IMPLICATION_TYPES = frozenset({"implies", "causes", "enables"})

BACKWARD_TYPES: dict[str, str] = {
    "causes":      "caused_by",
    "implies":     "implied_by",
    "requires":    "required_by",
    "enables":     "enabled_by",
}

RELATION_TYPE_WEIGHTS: dict[str, float] = {
    "causes":        0.95,
    "caused_by":     0.95,
    "prevents":      0.90,
    "prevented_by":  0.90,
    "requires":      0.90,
    "required_by":   0.90,
    "implies":       0.85,
    "implied_by":    0.85,
    "contradicts":   0.95,
    "composes":      0.80,
    "composed_of":   0.80,
    "enables":       0.75,
    "enabled_by":    0.75,
    "becomes":       0.70,
    "specializes":   0.65,
    "generalizes":   0.60,
    "precedes":      0.50,
    "follows":       0.50,
    "affords":       0.40,
    "inhabited_by":  0.35,
    "analogous_to":  0.30,
}


@dataclass
class Relation:
    """Типизированное отношение между двумя фактами."""
    relation_id:      str
    from_fact_id:     str
    to_fact_id:       str
    relation_type:    str
    confidence:       float
    knowledge_status: str = "known"
    inference_source: str | None = None
    truth_status:  str = "validated"
    review_state:  str = "approved"
    evidence_ref:  str | None = None
    created_at:    str = ""
    valid_from:    str = ""
    valid_to:      str | None = None
    metadata:      dict | None = None

    def is_reliable(self, min_confidence: float = 0.5) -> bool:
        return (
            self.confidence >= min_confidence
            and self.knowledge_status in ("known", "inferred")
        )

    def to_dict(self) -> dict:
        return {
            "relation_id": self.relation_id,
            "from_fact_id": self.from_fact_id,
            "to_fact_id": self.to_fact_id,
            "relation_type": self.relation_type,
            "confidence": self.confidence,
            "knowledge_status": self.knowledge_status,
            "inference_source": self.inference_source,
            "truth_status": self.truth_status,
            "review_state": self.review_state,
            "evidence_ref": self.evidence_ref,
            "created_at": self.created_at,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "metadata": self.metadata,
        }


@dataclass
class ChainResult:
    chain:              list[Relation]
    min_confidence:     float
    product_confidence: float
    has_hypothetical:   bool
    unknown_count:      int

    def is_trustworthy(
        self,
        min_confidence: float = 0.5,
        allow_hypothetical: bool = False,
    ) -> bool:
        if self.has_hypothetical and not allow_hypothetical:
            return False
        return self.min_confidence >= min_confidence

    def to_dict(self) -> dict:
        return {
            "chain": [r.to_dict() for r in self.chain],
            "min_confidence": self.min_confidence,
            "product_confidence": self.product_confidence,
            "has_hypothetical": self.has_hypothetical,
            "unknown_count": self.unknown_count,
            "trustworthy": self.is_trustworthy(),
        }

    @property
    def weighted_confidence(self) -> float:
        if not self.chain:
            return 1.0
        total = 1.0
        for rel in self.chain:
            type_weight = RELATION_TYPE_WEIGHTS.get(rel.relation_type, 0.5)
            total *= rel.confidence * type_weight
        return round(total, 4)

    def explain_path(self) -> str:
        if not self.chain:
            return "(пустая цепочка)"
        steps: list[str] = []
        for rel in self.chain:
            tw = RELATION_TYPE_WEIGHTS.get(rel.relation_type, 0.5)
            steps.append(
                f"{rel.from_fact_id} →[{rel.relation_type}, "
                f"conf={rel.confidence:.2f}, w={tw:.0%}]→ {rel.to_fact_id}"
            )
        path = " и затем ".join(steps)
        return (
            f"{path} "
            f"({len(self.chain)} рёбер, "
            f"мин.уверенность={self.min_confidence:.2f}, "
            f"взвешенная={self.weighted_confidence:.2f})"
        )


class CausalGraph:
    """Canonical causal Truth-edge layer over SQLite ``relations``.

    Issue #286 / parent #50: this class is the one canonical mutation owner for
    ``relations``. Every public create/delete/reset operation is WriteGate-protected,
    transaction-owned here, and bound to same-transaction AuditChain evidence. Read-only
    graph projections (NetworkX/Neo4j copies) do not gain write authority from this API.
    """

    def __init__(self, db_conn) -> None:
        self._conn = db_conn
        self._ensure_pragmas()

    def _ensure_pragmas(self) -> None:
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.commit()

    def _prepare_mutation(self) -> None:
        ensure_writes_allowed()
        if self._conn.in_transaction:
            raise RuntimeError(
                "CausalGraph canonical mutation requires an idle connection; "
                "caller-owned relation transactions are not supported"
            )
        ensure_causal_audit_ready(self._conn)

    @staticmethod
    def _resolve_truth_review(
        *,
        knowledge_status: str,
        inference_source: str | None,
        truth_status: str | None,
        review_state: str | None,
    ) -> tuple[str, str]:
        automatic = (
            knowledge_status != "known"
            or inference_source not in (None, "manual")
        )
        resolved_truth = (
            truth_status
            if truth_status is not None
            else ("hypothesis" if automatic else "validated")
        )
        resolved_review = (
            review_state
            if review_state is not None
            else ("pending" if automatic else "approved")
        )
        if resolved_truth not in VALID_TRUTH_STATUSES:
            raise ValueError(
                f"Неизвестный truth_status: {resolved_truth!r}. "
                f"Допустимые: {sorted(VALID_TRUTH_STATUSES)}"
            )
        if resolved_review not in VALID_REVIEW_STATES:
            raise ValueError(
                f"Неизвестный review_state: {resolved_review!r}. "
                f"Допустимые: {sorted(VALID_REVIEW_STATES)}"
            )
        return resolved_truth, resolved_review

    @staticmethod
    def _validate_relation_input(
        *,
        from_fact_id: str,
        to_fact_id: str,
        relation_type: str,
        confidence: object,
        knowledge_status: str,
        inference_source: str | None,
        truth_status: str | None,
        review_state: str | None,
    ) -> tuple[str, str]:
        if from_fact_id == to_fact_id:
            raise ValueError("Петли запрещены: from_fact_id == to_fact_id")
        if relation_type not in FORWARD_RELATION_TYPES:
            if relation_type in BACKWARD_RELATION_TYPES:
                raise ValueError(
                    f"relation_type={relation_type!r} — это backward-тип, "
                    "он создаётся автоматически как inverse"
                )
            raise ValueError(
                f"Неизвестный relation_type: {relation_type!r}. "
                f"Допустимые: {sorted(FORWARD_RELATION_TYPES)}"
            )
        if knowledge_status not in VALID_KNOWLEDGE_STATUSES:
            raise ValueError(
                f"Неизвестный knowledge_status: {knowledge_status!r}. "
                f"Допустимые: {sorted(VALID_KNOWLEDGE_STATUSES)}"
            )
        if inference_source is not None and inference_source not in VALID_INFERENCE_SOURCES:
            raise ValueError(
                f"Неизвестный inference_source: {inference_source!r}. "
                f"Допустимые: {sorted(VALID_INFERENCE_SOURCES)}"
            )
        if isinstance(confidence, bool):
            raise ValueError("confidence не может быть bool")
        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError) as exc:
            raise ValueError("confidence должен быть числом в [0.0, 1.0]") from exc
        if not math.isfinite(confidence_value) or not 0.0 <= confidence_value <= 1.0:
            raise ValueError(f"confidence должен быть в [0.0, 1.0], получено: {confidence}")
        return CausalGraph._resolve_truth_review(
            knowledge_status=knowledge_status,
            inference_source=inference_source,
            truth_status=truth_status,
            review_state=review_state,
        )

    @staticmethod
    def _metadata_json(metadata: dict | None) -> str | None:
        if not metadata:
            return None
        return json.dumps(metadata, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _inverse_metadata(metadata: dict | None, *, relation_id: str) -> dict:
        out = dict(metadata or {})
        out["inverse_of"] = relation_id
        return out

    @staticmethod
    def _inverse_type_for_stored(relation_type: str) -> str | None:
        direct = INVERSE_RELATIONS.get(relation_type)
        if direct:
            return direct
        for forward, inverse in INVERSE_RELATIONS.items():
            if inverse == relation_type:
                return forward
        return None

    @staticmethod
    def _find_existing_relation_id(
        conn,
        *,
        from_fact_id: str,
        to_fact_id: str,
        relation_type: str,
        inference_source: str | None,
    ) -> str | None:
        row = conn.execute(
            """
            SELECT relation_id FROM relations
            WHERE from_fact_id = ? AND to_fact_id = ?
              AND relation_type = ? AND inference_source IS ?
            ORDER BY relation_id LIMIT 1
            """,
            (from_fact_id, to_fact_id, relation_type, inference_source),
        ).fetchone()
        return str(row[0]) if row else None

    @staticmethod
    def _insert_relation_row(
        conn,
        *,
        relation_id: str,
        from_fact_id: str,
        to_fact_id: str,
        relation_type: str,
        confidence: float,
        knowledge_status: str,
        inference_source: str | None,
        truth_status: str,
        review_state: str,
        evidence_ref: str | None,
        now: str,
        metadata: dict | None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO relations (
                relation_id, from_fact_id, to_fact_id, relation_type,
                confidence, knowledge_status, inference_source,
                truth_status, review_state,
                evidence_ref, created_at, valid_from, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                relation_id, from_fact_id, to_fact_id, relation_type,
                float(confidence), knowledge_status, inference_source,
                truth_status, review_state, evidence_ref, now, now,
                CausalGraph._metadata_json(metadata),
            ),
        )

    @staticmethod
    def _normalized_row(row: dict) -> dict:
        required = ("from_fact_id", "to_fact_id", "relation_type")
        missing = [key for key in required if not row.get(key)]
        if missing:
            raise ValueError(f"relation row missing required fields: {missing}")
        knowledge_status = str(row.get("knowledge_status") or "known")
        inference_source = row.get("inference_source")
        raw_confidence = row.get("confidence", 0.8)
        truth_status, review_state = CausalGraph._validate_relation_input(
            from_fact_id=str(row["from_fact_id"]),
            to_fact_id=str(row["to_fact_id"]),
            relation_type=str(row["relation_type"]),
            confidence=raw_confidence,
            knowledge_status=knowledge_status,
            inference_source=(str(inference_source) if inference_source is not None else None),
            truth_status=row.get("truth_status"),
            review_state=row.get("review_state"),
        )
        metadata = row.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("relation metadata must be a dict or None")
        return {
            "from_fact_id": str(row["from_fact_id"]),
            "to_fact_id": str(row["to_fact_id"]),
            "relation_type": str(row["relation_type"]),
            "confidence": float(raw_confidence),
            "knowledge_status": knowledge_status,
            "inference_source": (
                str(inference_source) if inference_source is not None else None
            ),
            "evidence_ref": (
                str(row["evidence_ref"]) if row.get("evidence_ref") is not None else None
            ),
            "metadata": metadata,
            "truth_status": truth_status,
            "review_state": review_state,
        }

    def _add_one_in_transaction(self, row: dict, *, now: str) -> tuple[str, int]:
        existing_id = self._find_existing_relation_id(
            self._conn,
            from_fact_id=row["from_fact_id"],
            to_fact_id=row["to_fact_id"],
            relation_type=row["relation_type"],
            inference_source=row["inference_source"],
        )
        physical_created = 0
        if existing_id is None:
            relation_id = f"rel_{uuid.uuid4().hex[:12]}"
            self._insert_relation_row(
                self._conn,
                relation_id=relation_id,
                from_fact_id=row["from_fact_id"],
                to_fact_id=row["to_fact_id"],
                relation_type=row["relation_type"],
                confidence=row["confidence"],
                knowledge_status=row["knowledge_status"],
                inference_source=row["inference_source"],
                truth_status=row["truth_status"],
                review_state=row["review_state"],
                evidence_ref=row["evidence_ref"],
                now=now,
                metadata=row["metadata"],
            )
            append_relation_event(
                self._conn, relation_id=relation_id, event_type=EVENT_RELATION_CREATED
            )
            physical_created += 1
        else:
            relation_id = existing_id

        inverse_type = INVERSE_RELATIONS.get(row["relation_type"])
        if inverse_type and inverse_type in VALID_RELATION_TYPES:
            inverse_existing = self._find_existing_relation_id(
                self._conn,
                from_fact_id=row["to_fact_id"],
                to_fact_id=row["from_fact_id"],
                relation_type=inverse_type,
                inference_source=row["inference_source"],
            )
            if inverse_existing is None:
                inverse_id = f"rel_{uuid.uuid4().hex[:12]}"
                self._insert_relation_row(
                    self._conn,
                    relation_id=inverse_id,
                    from_fact_id=row["to_fact_id"],
                    to_fact_id=row["from_fact_id"],
                    relation_type=inverse_type,
                    confidence=row["confidence"],
                    knowledge_status=row["knowledge_status"],
                    inference_source=row["inference_source"],
                    truth_status=row["truth_status"],
                    review_state=row["review_state"],
                    evidence_ref=row["evidence_ref"],
                    now=now,
                    metadata=self._inverse_metadata(row["metadata"], relation_id=relation_id),
                )
                append_relation_event(
                    self._conn, relation_id=inverse_id, event_type=EVENT_RELATION_CREATED
                )
                physical_created += 1
        return relation_id, physical_created

    def add_relation(
        self,
        from_fact_id: str,
        to_fact_id: str,
        relation_type: str,
        confidence: float = 0.8,
        knowledge_status: str = "known",
        inference_source: str | None = None,
        evidence_ref: str | None = None,
        metadata: dict | None = None,
        truth_status: str | None = None,
        review_state: str | None = None,
    ) -> str:
        result = self.add_relations_batch([{
            "from_fact_id": from_fact_id,
            "to_fact_id": to_fact_id,
            "relation_type": relation_type,
            "confidence": confidence,
            "knowledge_status": knowledge_status,
            "inference_source": inference_source,
            "evidence_ref": evidence_ref,
            "metadata": metadata,
            "truth_status": truth_status,
            "review_state": review_state,
        }])
        return result["relation_ids"][0]

    def add_relations_batch(self, rows: list[dict]) -> dict:
        if not rows:
            return {
                "requested": 0, "created": 0, "existing": 0,
                "physical_rows_created": 0, "relation_ids": [],
            }
        normalized = [self._normalized_row(dict(row)) for row in rows]
        self._prepare_mutation()
        now = datetime.now(UTC).isoformat()
        relation_ids: list[str] = []
        semantic_created = 0
        physical_created = 0
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            for row in normalized:
                before = self._find_existing_relation_id(
                    self._conn,
                    from_fact_id=row["from_fact_id"],
                    to_fact_id=row["to_fact_id"],
                    relation_type=row["relation_type"],
                    inference_source=row["inference_source"],
                )
                relation_id, created_rows = self._add_one_in_transaction(row, now=now)
                relation_ids.append(relation_id)
                if before is None:
                    semantic_created += 1
                physical_created += created_rows
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return {
            "requested": len(normalized),
            "created": semantic_created,
            "existing": len(normalized) - semantic_created,
            "physical_rows_created": physical_created,
            "relation_ids": relation_ids,
        }

    def get_relations_from(
        self,
        fact_id: str,
        relation_type: str | None = None,
        knowledge_status: str | None = None,
        min_confidence: float = 0.0,
        only_approved: bool = True,
    ) -> list[Relation]:
        sql = """
            SELECT relation_id, from_fact_id, to_fact_id, relation_type,
                   confidence, knowledge_status, inference_source,
                   truth_status, review_state,
                   evidence_ref, created_at, valid_from, valid_to, metadata
            FROM relations
            WHERE from_fact_id = ? AND confidence >= ?
        """
        params: list = [fact_id, min_confidence]
        if relation_type:
            sql += " AND relation_type = ?"
            params.append(relation_type)
        if knowledge_status:
            sql += " AND knowledge_status = ?"
            params.append(knowledge_status)
        if only_approved:
            sql += " AND review_state = 'approved'"
        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_relation(r) for r in rows]

    def get_relations_to(
        self,
        fact_id: str,
        relation_type: str | None = None,
        knowledge_status: str | None = None,
        min_confidence: float = 0.0,
        only_approved: bool = True,
    ) -> list[Relation]:
        sql = """
            SELECT relation_id, from_fact_id, to_fact_id, relation_type,
                   confidence, knowledge_status, inference_source,
                   truth_status, review_state,
                   evidence_ref, created_at, valid_from, valid_to, metadata
            FROM relations
            WHERE to_fact_id = ? AND confidence >= ?
        """
        params: list = [fact_id, min_confidence]
        if relation_type:
            sql += " AND relation_type = ?"
            params.append(relation_type)
        if knowledge_status:
            sql += " AND knowledge_status = ?"
            params.append(knowledge_status)
        if only_approved:
            sql += " AND review_state = 'approved'"
        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_relation(r) for r in rows]

    def _expand_remove_ids_in_transaction(self, relation_ids: list[str]) -> list[str]:
        expanded: set[str] = set()
        for relation_id in relation_ids:
            row = self._conn.execute(
                """
                SELECT relation_id, from_fact_id, to_fact_id, relation_type,
                       inference_source FROM relations WHERE relation_id = ?
                """,
                (relation_id,),
            ).fetchone()
            if row is None:
                continue
            expanded.add(str(row[0]))
            inverse_type = self._inverse_type_for_stored(str(row[3]))
            if inverse_type:
                inverse_rows = self._conn.execute(
                    """
                    SELECT relation_id FROM relations
                    WHERE from_fact_id = ? AND to_fact_id = ?
                      AND relation_type = ? AND inference_source IS ?
                    """,
                    (row[2], row[1], inverse_type, row[4]),
                ).fetchall()
                expanded.update(str(r[0]) for r in inverse_rows)
        return sorted(expanded)

    def remove_relations(self, relation_ids: list[str]) -> int:
        requested = list(dict.fromkeys(str(rid) for rid in relation_ids if rid))
        if not requested:
            return 0
        self._prepare_mutation()
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            expanded = self._expand_remove_ids_in_transaction(requested)
            removed = 0
            for relation_id in expanded:
                cur = self._conn.execute(
                    "DELETE FROM relations WHERE relation_id = ?", (relation_id,)
                )
                if cur.rowcount == 1:
                    append_relation_event(
                        self._conn,
                        relation_id=relation_id,
                        event_type=EVENT_RELATION_REMOVED,
                    )
                    removed += 1
            self._conn.commit()
            return removed
        except Exception:
            self._conn.rollback()
            raise

    def remove_relation(self, relation_id: str) -> bool:
        return self.remove_relations([relation_id]) > 0

    def reset_relations(self) -> int:
        self._prepare_mutation()
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            relation_ids = [
                str(row[0])
                for row in self._conn.execute(
                    "SELECT relation_id FROM relations ORDER BY relation_id"
                ).fetchall()
            ]
            if not relation_ids:
                self._conn.commit()
                return 0
            self._conn.execute("DELETE FROM relations")
            for relation_id in relation_ids:
                append_relation_event(
                    self._conn,
                    relation_id=relation_id,
                    event_type=EVENT_RELATION_REMOVED,
                )
            self._conn.commit()
            return len(relation_ids)
        except Exception:
            self._conn.rollback()
            raise

    def get_relation(self, relation_id: str) -> Relation | None:
        row = self._conn.execute(
            """
            SELECT relation_id, from_fact_id, to_fact_id, relation_type,
                   confidence, knowledge_status, inference_source,
                   truth_status, review_state,
                   evidence_ref, created_at, valid_from, valid_to, metadata
            FROM relations WHERE relation_id = ?
            """,
            (relation_id,),
        ).fetchone()
        return self._row_to_relation(row) if row else None

    @staticmethod
    def _chain_confidence(relations: list[Relation]) -> ChainResult:
        if not relations:
            return ChainResult([], 1.0, 1.0, False, 0)
        confidences = [r.confidence for r in relations]
        statuses = [r.knowledge_status for r in relations]
        return ChainResult(
            chain=relations,
            min_confidence=min(confidences),
            product_confidence=math.prod(confidences),
            has_hypothetical=any(s == "hypothetical" for s in statuses),
            unknown_count=sum(1 for s in statuses if s == "unknown"),
        )

    def causal_chain(
        self,
        from_fact_id: str,
        max_depth: int = 5,
        min_confidence: float = 0.5,
        only_known: bool = False,
    ) -> list[ChainResult]:
        results: list[ChainResult] = []
        queue: deque[tuple[str, list[Relation], set[str]]] = deque([
            (from_fact_id, [], {from_fact_id}),
        ])
        while queue:
            current_id, path, visited = queue.popleft()
            if len(path) >= max_depth:
                continue
            for rel_type in ("causes", "enables"):
                relations = self.get_relations_from(
                    current_id,
                    relation_type=rel_type,
                    min_confidence=min_confidence,
                )
                for rel in relations:
                    if rel.to_fact_id in visited:
                        continue
                    if only_known and rel.knowledge_status != "known":
                        continue
                    new_path = path + [rel]
                    results.append(self._chain_confidence(new_path))
                    queue.append((rel.to_fact_id, new_path, visited | {rel.to_fact_id}))
        return results

    def implications(
        self,
        fact_id: str,
        depth: int = 3,
        min_confidence: float = 0.5,
    ) -> list[tuple[str, ChainResult]]:
        results: list[tuple[str, ChainResult]] = []
        visited: set[str] = {fact_id}
        queue: list[tuple[str, list[Relation]]] = [(fact_id, [])]
        for _ in range(depth):
            next_queue: list[tuple[str, list[Relation]]] = []
            for current_id, path in queue:
                for rel_type in IMPLICATION_TYPES:
                    for rel in self.get_relations_from(
                        current_id,
                        relation_type=rel_type,
                        min_confidence=min_confidence,
                    ):
                        if rel.to_fact_id in visited:
                            continue
                        new_path = path + [rel]
                        chain = self._chain_confidence(new_path)
                        results.append((rel.to_fact_id, chain))
                        visited.add(rel.to_fact_id)
                        next_queue.append((rel.to_fact_id, new_path))
            queue = next_queue
        return results

    def explain(self, fact_id: str) -> dict:
        causes: list[dict] = []
        requires: list[dict] = []
        implied_by: list[dict] = []
        for rel in self.get_relations_from(fact_id, relation_type="caused_by"):
            causes.append({"fact_id": rel.to_fact_id, "confidence": rel.confidence,
                           "status": rel.knowledge_status})
        for rel in self.get_relations_to(fact_id, relation_type="causes"):
            causes.append({"fact_id": rel.from_fact_id, "confidence": rel.confidence,
                           "status": rel.knowledge_status})
        for rel in self.get_relations_from(fact_id, relation_type="required_by"):
            requires.append({"fact_id": rel.to_fact_id, "confidence": rel.confidence,
                             "status": rel.knowledge_status})
        for rel in self.get_relations_to(fact_id, relation_type="requires"):
            requires.append({"fact_id": rel.from_fact_id, "confidence": rel.confidence,
                             "status": rel.knowledge_status})
        for rel in self.get_relations_from(fact_id, relation_type="implied_by"):
            implied_by.append({"fact_id": rel.to_fact_id, "confidence": rel.confidence,
                               "status": rel.knowledge_status})
        for rel in self.get_relations_to(fact_id, relation_type="implies"):
            implied_by.append({"fact_id": rel.from_fact_id, "confidence": rel.confidence,
                               "status": rel.knowledge_status})
        return {
            "fact_id": fact_id,
            "caused_by": causes,
            "required_by": requires,
            "implied_by": implied_by,
            "has_explanation": bool(causes or requires or implied_by),
        }

    def propagate_change(self, fact_id: str, change: str) -> list[dict]:
        chains = self.causal_chain(fact_id, max_depth=4, min_confidence=0.3)
        effects: list[dict] = []
        seen: set[str] = set()
        for chain in chains:
            if chain.chain:
                last = chain.chain[-1]
                if last.to_fact_id not in seen:
                    seen.add(last.to_fact_id)
                    effects.append({
                        "affected_fact_id": last.to_fact_id,
                        "path_length": len(chain.chain),
                        "min_confidence": chain.min_confidence,
                        "has_hypothetical": chain.has_hypothetical,
                        "relation_types": [r.relation_type for r in chain.chain],
                    })
        return sorted(effects, key=lambda x: -x["min_confidence"])

    def abstraction_ladder(self, fact_id: str, levels: int = 3) -> list[list[str]]:
        ladder: list[list[str]] = [[fact_id]]
        current_level = [fact_id]
        for _ in range(levels):
            next_level: list[str] = []
            for fid in current_level:
                for rel in self.get_relations_from(fid, relation_type="generalizes"):
                    if rel.to_fact_id not in [x for lvl in ladder for x in lvl]:
                        next_level.append(rel.to_fact_id)
            if next_level:
                ladder.append(next_level)
                current_level = next_level
            else:
                break
        concrete = [
            rel.to_fact_id
            for rel in self.get_relations_from(fact_id, relation_type="specializes")
        ]
        if concrete:
            ladder.insert(0, concrete)
        return ladder

    def counterfactual(self, fact_id: str, hypothesis: str) -> dict:
        effects = self.propagate_change(fact_id, hypothesis)
        return {
            "fact_id": fact_id,
            "hypothesis": hypothesis,
            "pearl_level": 2,
            "causal_chain": effects,
            "affected_count": len(effects),
            "note": (
                "Pearl Level 2 (intervention). "
                "Для полного do-calculus (Level 3) нужна SCM с уравнениями."
            ),
        }

    def find_analogies(
        self, fact_id: str, cross_domain: bool = True
    ) -> list[tuple[str, float]]:
        own_rels = self.get_relations_from(fact_id)
        own_types = frozenset(r.relation_type for r in own_rels)
        if not own_types:
            return []
        direct_analogies = self.get_relations_from(fact_id, relation_type="analogous_to")
        results: list[tuple[str, float]] = [
            (r.to_fact_id, r.confidence) for r in direct_analogies
        ]
        seen = {fact_id} | {r.to_fact_id for r in direct_analogies}
        candidates_sql = """
            SELECT DISTINCT from_fact_id FROM relations
            WHERE from_fact_id != ?
              AND from_fact_id NOT IN ({})
              AND relation_type IN ({})
        """.format(
            ", ".join("?" * len(seen)),
            ", ".join("?" * len(own_types)),
        )
        params = [fact_id] + list(seen) + list(own_types)
        candidate_rows = self._conn.execute(candidates_sql, params).fetchall()
        for (candidate_id,) in candidate_rows:
            cand_rels = self.get_relations_from(candidate_id)
            cand_types = frozenset(r.relation_type for r in cand_rels)
            if not cand_types:
                continue
            intersection = len(own_types & cand_types)
            union = len(own_types | cand_types)
            similarity = intersection / union if union > 0 else 0.0
            if similarity >= 0.3:
                results.append((candidate_id, similarity))
        return sorted(results, key=lambda x: -x[1])[:10]

    def find_contradictions(
        self,
        fact_id: str,
        _visited_facts: set | None = None,
    ) -> list[Relation]:
        if _visited_facts is None:
            _visited_facts = set()
        if fact_id in _visited_facts:
            return []
        _visited_facts.add(fact_id)
        direct = self.get_relations_from(fact_id, relation_type="contradicts")
        direct += self.get_relations_to(fact_id, relation_type="contradicts")
        seen_ids: set[str] = {r.relation_id for r in direct}
        result = list(direct)
        for impl_rel in self.get_relations_to(fact_id, relation_type="implies"):
            for contra_rel in self.find_contradictions(
                impl_rel.from_fact_id, _visited_facts=_visited_facts
            ):
                if contra_rel.relation_id not in seen_ids:
                    seen_ids.add(contra_rel.relation_id)
                    result.append(contra_rel)
        return result

    def knowledge_summary(self, fact_id: str) -> dict:
        """Diagnostic boundary: count approved and pending relation knowledge."""
        all_rels = self.get_relations_from(
            fact_id, only_approved=False
        ) + self.get_relations_to(fact_id, only_approved=False)
        status_counts = {"known": 0, "inferred": 0, "hypothetical": 0, "unknown": 0}
        for rel in all_rels:
            status_counts[rel.knowledge_status] = (
                status_counts.get(rel.knowledge_status, 0) + 1
            )
        confidences = [r.confidence for r in all_rels]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        min_conf = min(confidences) if confidences else 0.0
        has_contradictions = bool(self.find_contradictions(fact_id))
        if status_counts["unknown"] > 0:
            recommendation = "incomplete"
        elif status_counts["inferred"] > 0 or status_counts["hypothetical"] > 0:
            recommendation = "verify"
        elif avg_conf >= 0.8 and not has_contradictions:
            recommendation = "reliable"
        else:
            recommendation = "verify"
        return {
            "fact_id": fact_id,
            "total_relations": len(all_rels),
            "known_relations": status_counts["known"],
            "inferred_relations": status_counts["inferred"],
            "hypothetical_relations": status_counts["hypothetical"],
            "unknown_relations": status_counts["unknown"],
            "avg_confidence": round(avg_conf, 4),
            "min_confidence": round(min_conf, 4),
            "has_contradictions": has_contradictions,
            "recommendation": recommendation,
        }

    def import_snapshots(self, rows: list[dict], *, merge: bool = True) -> int:
        prepared: list[dict] = []
        for row in rows:
            from_id = row.get("from_fact_id")
            to_id = row.get("to_fact_id")
            rtype = row.get("relation_type")
            if not from_id or not to_id or not rtype:
                continue
            rid = row.get("relation_id")
            if rid and merge and self.get_relation(str(rid)):
                continue
            raw_confidence = row.get("confidence")
            prepared.append({
                "from_fact_id": str(from_id),
                "to_fact_id": str(to_id),
                "relation_type": str(rtype),
                "confidence": 0.8 if raw_confidence is None else raw_confidence,
                "knowledge_status": str(row.get("knowledge_status") or "inferred"),
                "inference_source": row.get("inference_source") or "atlas_sync",
                "truth_status": row.get("truth_status"),
                "review_state": row.get("review_state"),
                "evidence_ref": row.get("evidence_ref"),
                "metadata": row.get("metadata") if isinstance(row.get("metadata"), dict) else None,
            })
        if not prepared:
            return 0
        try:
            result = self.add_relations_batch(prepared)
            return int(result["created"])
        except ValueError as exc:
            logger.warning("import_snapshots: snapshot batch rejected: %s", exc)
            return 0
        except Exception:
            logger.exception("import_snapshots: canonical snapshot import failed")
            return 0

    def stats(self) -> dict:
        total = self._conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
        by_type = {
            row[0]: row[1]
            for row in self._conn.execute(
                "SELECT relation_type, COUNT(*) FROM relations GROUP BY relation_type"
            )
        }
        by_status = {
            row[0]: row[1]
            for row in self._conn.execute(
                "SELECT knowledge_status, COUNT(*) FROM relations GROUP BY knowledge_status"
            )
        }
        unique_facts = self._conn.execute(
            "SELECT COUNT(DISTINCT from_fact_id) FROM relations"
        ).fetchone()[0]
        return {
            "total_relations": total,
            "unique_source_facts": unique_facts,
            "by_relation_type": by_type,
            "by_knowledge_status": by_status,
            "density": round(total / max(unique_facts, 1), 2),
        }

    def find_orphan_nodes(self, limit: int = 100) -> list[str]:
        rows = self._conn.execute("""
            SELECT f.fact_id FROM facts f
            WHERE f.fact_id NOT IN (
                SELECT from_fact_id FROM relations
                UNION SELECT to_fact_id FROM relations
            ) AND f.epistemic_state != 'Collapsed'
            LIMIT ?
        """, (limit,)).fetchall()
        return [r[0] for r in rows]

    def count_orphan_nodes(self) -> int:
        row = self._conn.execute("""
            SELECT COUNT(*) FROM facts f
            WHERE f.fact_id NOT IN (
                SELECT from_fact_id FROM relations
                UNION SELECT to_fact_id FROM relations
            ) AND f.epistemic_state != 'Collapsed'
        """).fetchone()
        return row[0] if row else 0

    def find_dangling_edges(self, limit: int = 100) -> list[dict]:
        rows = self._conn.execute("""
            SELECT r.relation_id, r.from_fact_id, r.to_fact_id, r.relation_type
            FROM relations r
            WHERE r.from_fact_id NOT IN (SELECT fact_id FROM facts)
               OR r.to_fact_id NOT IN (SELECT fact_id FROM facts)
            LIMIT ?
        """, (limit,)).fetchall()
        fact_ids = self._get_fact_ids_set()
        return [{
            "relation_id": row[0],
            "from_fact_id": row[1],
            "to_fact_id": row[2],
            "relation_type": row[3],
            "missing_from": row[1] not in fact_ids,
            "missing_to": row[2] not in fact_ids,
        } for row in rows]

    def count_dangling_edges(self) -> int:
        row = self._conn.execute("""
            SELECT COUNT(*) FROM relations r
            WHERE r.from_fact_id NOT IN (SELECT fact_id FROM facts)
               OR r.to_fact_id NOT IN (SELECT fact_id FROM facts)
        """).fetchone()
        return row[0] if row else 0

    def find_duplicate_edges(self, limit: int = 100) -> list[dict]:
        rows = self._conn.execute("""
            SELECT from_fact_id, to_fact_id, relation_type, COUNT(*) AS cnt
            FROM relations
            GROUP BY from_fact_id, to_fact_id, relation_type
            HAVING cnt > 1 LIMIT ?
        """, (limit,)).fetchall()
        return [
            {"from": r[0], "to": r[1], "type": r[2], "count": r[3]}
            for r in rows
        ]

    def find_missing_evidence(self, limit: int = 100) -> list[dict]:
        rows = self._conn.execute("""
            SELECT relation_id, from_fact_id, to_fact_id, relation_type,
                   knowledge_status, confidence
            FROM relations
            WHERE (evidence_ref IS NULL OR evidence_ref = '')
              AND knowledge_status = 'known'
            LIMIT ?
        """, (limit,)).fetchall()
        return [{
            "relation_id": r[0],
            "from": r[1], "to": r[2], "type": r[3],
            "status": r[4], "confidence": r[5],
        } for r in rows]

    def integrity_report(self) -> dict:
        orphans = self.count_orphan_nodes()
        dangling = self.count_dangling_edges()
        s = self.stats()
        total_facts = self._conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
        orphan_pct = round(orphans / max(total_facts, 1) * 100, 2)
        integrity_score = 100.0
        issues: list[str] = []
        if orphans > 0:
            issues.append(f"{orphans} орфан-узлов ({orphan_pct}% фактов изолированы)")
            integrity_score -= min(30, orphan_pct * 10)
        if dangling > 0:
            issues.append(f"{dangling} dangling-рёбер (ссылаются на несуществующие факты)")
            integrity_score -= min(40, dangling * 2)
        critical = orphan_pct > 20 or dangling > 10
        return {
            "integrity_score": round(max(0, integrity_score), 1),
            "healthy": integrity_score >= 80 and not critical,
            "total_facts": total_facts,
            "total_relations": s["total_relations"],
            "orphan_nodes": orphans,
            "orphan_pct": orphan_pct,
            "dangling_edges": dangling,
            "issues": issues,
            "by_relation_type": s.get("by_relation_type", {}),
            "by_knowledge_status": s.get("by_knowledge_status", {}),
            "contradictions_detected": self._conn.execute(
                "SELECT COUNT(*) FROM relations WHERE relation_type = 'contradicts'"
            ).fetchone()[0],
            "recommendation": (
                "cleanup_required" if critical
                else "verify" if orphans > 0 or dangling > 0
                else "healthy"
            ),
        }

    def _get_fact_ids_set(self) -> frozenset[str]:
        rows = self._conn.execute("SELECT fact_id FROM facts").fetchall()
        return frozenset(r[0] for r in rows)

    @staticmethod
    def _row_to_relation(row) -> Relation:
        meta = None
        if row[13]:
            try:
                meta = json.loads(row[13])
            except (json.JSONDecodeError, TypeError):
                meta = None
        return Relation(
            relation_id=row[0],
            from_fact_id=row[1],
            to_fact_id=row[2],
            relation_type=row[3],
            confidence=row[4],
            knowledge_status=row[5] or "known",
            inference_source=row[6],
            truth_status=row[7] or "validated",
            review_state=row[8] or "approved",
            evidence_ref=row[9],
            created_at=row[10] or "",
            valid_from=row[11] or "",
            valid_to=row[12],
            metadata=meta,
        )


def is_causal_graph_enabled() -> bool:
    try:
        from core.feature_config import get_config
        return get_config().app.enable_causal_graph
    except Exception:  # noqa: BLE001
        logger.warning(
            "is_causal_graph_enabled: config read failed, falling back to default=True",
            exc_info=True,
        )
        return True


def get_causal_graph() -> CausalGraph:
    from core.pipeline import _get_causal_graph
    graph = _get_causal_graph()
    if graph is None:
        raise RuntimeError("CausalGraph недоступен (проверьте миграции relations)")
    return graph


def reset_causal_graph() -> None:
    """Audited reset plus singleton detach; never call the legacy raw wipe."""
    from core import pipeline as _pipeline

    graph = _pipeline._get_causal_graph()
    if graph is not None:
        graph.reset_relations()
        try:
            graph._conn.close()
        except Exception:  # noqa: BLE001
            logger.debug("CausalGraph close after reset failed", exc_info=True)
    _pipeline._CAUSAL_GRAPH = None
    _pipeline._CAUSAL_GRAPH_DB_PATH = ""


__all__ = [
    "CausalGraph",
    "FORWARD_RELATION_TYPES",
    "get_causal_graph",
    "is_causal_graph_enabled",
    "reset_causal_graph",
]
