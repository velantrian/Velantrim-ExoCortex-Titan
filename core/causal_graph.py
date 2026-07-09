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
    # Patch 13 — оригинальные 12 типов
    "causes", "prevents", "requires", "enables",
    "implies", "contradicts", "generalizes", "specializes",
    "precedes", "follows", "composes", "analogous_to",
    # FIX v8.5.1 — добавлены типы из understanding_layer.py
    # Без них UnderstandingLayer.afford_to_causal() → ValueError
    "becomes",       # трансформация (дерево → дрова)
    "affords",       # прямая affordance связь
    "inhabited_by",  # кто там живёт / кто использует
})

BACKWARD_RELATION_TYPES = frozenset({
    "caused_by",     # inverse of causes
    "prevented_by",  # inverse of prevents
    "required_by",   # inverse of requires
    "enabled_by",    # inverse of enables
    "implied_by",    # inverse of implies
    "composed_of",   # inverse of composes
    # Симметричные (contradicts, analogous_to) НЕ дублируются — они сами себе inverse.
    # generalizes ↔ specializes и precedes ↔ follows — взаимные forward-типы,
    # тоже не нуждаются в отдельных backward.
})

# Storage-уровень: что вообще может находиться в таблице relations.
VALID_RELATION_TYPES = FORWARD_RELATION_TYPES | BACKWARD_RELATION_TYPES

VALID_KNOWLEDGE_STATUSES = frozenset({
    "known", "inferred", "hypothetical", "unknown",
})

VALID_INFERENCE_SOURCES = frozenset({
    "manual", "autolinker", "counterfactual_engine",
    "llm_extraction", "atlas_sync", "affordance_inference",
    "cross_domain",
})

# Автоматические обратные типы
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
    "contradicts":  "contradicts",    # симметрично
    "analogous_to": "analogous_to",   # симметрично
}

# Типы используемые при обходе implications
IMPLICATION_TYPES = frozenset({"implies", "causes", "enables"})

# Типы для backward reasoning (explain)
BACKWARD_TYPES: dict[str, str] = {
    "causes":      "caused_by",
    "implies":     "implied_by",
    "requires":    "required_by",
    "enables":     "enabled_by",
}

# ── Веса типов рёбер для ранжирования traversal ───────────────────────────────
#
# Из статьи Wiki-MCP-Server (Хабр, апрель 2026): типы рёбер — не украшение,
# а архитектура. Вес ребра влияет на осмысленность hop-результатов.
# depends_on=0.95 → сильная связь; mentions=0.3 → слабая ассоциация.
#
# Использование:
#   weighted_conf = rel.confidence * RELATION_TYPE_WEIGHTS.get(rel.relation_type, 0.5)
#   ChainResult.weighted_confidence — учитывает и тип, и confidence.
#
RELATION_TYPE_WEIGHTS: dict[str, float] = {
    # Причинные — максимальный вес (это НЕ ассоциация, это механика)
    "causes":        0.95,
    "caused_by":     0.95,
    "prevents":      0.90,
    "prevented_by":  0.90,
    "requires":      0.90,
    "required_by":   0.90,
    # Логические
    "implies":       0.85,
    "implied_by":    0.85,
    "contradicts":   0.95,  # противоречие — сильный сигнал
    # Структурные
    "composes":      0.80,
    "composed_of":   0.80,
    "enables":       0.75,
    "enabled_by":    0.75,
    "becomes":       0.70,
    "specializes":   0.65,
    "generalizes":   0.60,
    # Темпоральные
    "precedes":      0.50,
    "follows":       0.50,
    # Affordance
    "affords":       0.40,
    "inhabited_by":  0.35,
    # Ассоциативные — минимальный вес (слабая связь)
    "analogous_to":  0.30,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Relation:
    """Типизированное отношение между двумя фактами."""
    relation_id:      str
    from_fact_id:     str
    to_fact_id:       str
    relation_type:    str
    confidence:       float

    # v2: явный статус знания (не путать с confidence!)
    knowledge_status: str = "known"
    # 'known'       — проверено вручную или из надёжного источника
    # 'inferred'    — автоматически выведено
    # 'hypothetical'— предположение, не проверено
    # 'unknown'     — статус неизвестен

    # v2: кем/чем выведено
    inference_source: str | None = None

    # Совместимость с Variant B
    truth_status:  str = "validated"
    review_state:  str = "approved"

    evidence_ref:  str | None = None
    created_at:    str = ""
    valid_from:    str = ""
    valid_to:      str | None = None
    metadata:      dict | None = None

    def is_reliable(self, min_confidence: float = 0.5) -> bool:
        """Ребро надёжно: уверенность достаточная И статус known/inferred."""
        return (
            self.confidence >= min_confidence
            and self.knowledge_status in ("known", "inferred")
        )

    def to_dict(self) -> dict:
        return {
            "relation_id":     self.relation_id,
            "from_fact_id":    self.from_fact_id,
            "to_fact_id":      self.to_fact_id,
            "relation_type":   self.relation_type,
            "confidence":      self.confidence,
            "knowledge_status": self.knowledge_status,
            "inference_source": self.inference_source,
            "truth_status":    self.truth_status,
            "review_state":    self.review_state,
            "evidence_ref":    self.evidence_ref,
            "created_at":      self.created_at,
            "valid_from":      self.valid_from,
            "valid_to":        self.valid_to,
            "metadata":        self.metadata,
        }


@dataclass
class ChainResult:
    """
    v2: Результат обхода цепочки с честной статистикой уверенности.

    Две модели уверенности по цепи:
      min_confidence     — conservative: слабое звено определяет цепь
      product_confidence — probabilistic: перемножаем вероятности

    Используй min_confidence для critical decisions,
    product_confidence для ranking/sorting.
    """
    chain:              list[Relation]
    min_confidence:     float
    product_confidence: float
    has_hypothetical:   bool   # есть ли непроверенные рёбра
    unknown_count:      int    # количество 'unknown' рёбер

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
            "chain":              [r.to_dict() for r in self.chain],
            "min_confidence":     self.min_confidence,
            "product_confidence": self.product_confidence,
            "has_hypothetical":   self.has_hypothetical,
            "unknown_count":      self.unknown_count,
            "trustworthy":        self.is_trustworthy(),
        }

    @property
    def weighted_confidence(self) -> float:
        """Уверенность с учётом весов типов рёбер (RELATION_TYPE_WEIGHTS).

        Используй для сортировки/ранжирования цепочек —
        причинная цепь (causes, weight=0.95) получает приоритет
        над ассоциативной (analogous_to, weight=0.30).
        """
        if not self.chain:
            return 1.0
        total = 1.0
        for rel in self.chain:
            type_weight = RELATION_TYPE_WEIGHTS.get(rel.relation_type, 0.5)
            total *= rel.confidence * type_weight
        return round(total, 4)

    def explain_path(self) -> str:
        """Человекочитаемое объяснение цепочки.

        Пример:
            'A →[causes, 0.95]→ B →[enables, 0.75]→ C (3 узла, уверенность 0.71)'

        Используется Essence Layer для ответа на «как связано X и Y?».
        """
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


# ═══════════════════════════════════════════════════════════════════════════════
# CausalGraph
# ═══════════════════════════════════════════════════════════════════════════════

class CausalGraph:
    """
    Каузальный граф — слой над Velantrim memory.

    ПРИНЦИП: система обязана знать, чего она НЕ знает.
    Каждое ребро несёт knowledge_status (откуда это знание) —
    отдельно от confidence (вероятность наблюдения).

    Хранение: SQLite таблица relations (миграция 008_add_relations.sql).
    """

    def __init__(self, db_conn) -> None:
        """
        Args:
            db_conn: sqlite3.Connection с включёнными foreign keys.
                     Рекомендуется: conn.execute('PRAGMA foreign_keys = ON')
        """
        self._conn = db_conn
        self._ensure_pragmas()

    def _ensure_pragmas(self) -> None:
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.commit()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def add_relation(
        self,
        from_fact_id:     str,
        to_fact_id:       str,
        relation_type:    str,
        confidence:       float = 0.8,
        knowledge_status: str = "known",
        inference_source: str | None = None,
        evidence_ref:     str | None = None,
        metadata:         dict | None = None,
        truth_status:     str = "validated",
        review_state:     str = "approved",
    ) -> str:
        """
        Добавить отношение между двумя фактами.
        Автоматически создаёт inverse relation.

        Returns: relation_id
        Raises:
            ValueError: если relation_type или knowledge_status невалидны,
                        или from_fact_id == to_fact_id
        """
        # Валидация
        if from_fact_id == to_fact_id:
            raise ValueError("Петли запрещены: from_fact_id == to_fact_id")

        # FIX v8.5.2 (Claude audit): пользователь передаёт ТОЛЬКО forward-типы.
        # Backward-типы (caused_by и т.д.) создаются автоматически как inverse
        # и не должны передаваться напрямую. Если кто-то пытается — это
        # архитектурная ошибка вызывающего кода.
        if relation_type not in FORWARD_RELATION_TYPES:
            if relation_type in BACKWARD_RELATION_TYPES:
                raise ValueError(
                    f"relation_type={relation_type!r} — это backward-тип, "
                    f"он создаётся автоматически как inverse. "
                    f"Передавай соответствующий forward-тип "
                    f"(например, для 'caused_by' передавай 'causes' с обратным "
                    f"порядком фактов)."
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

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"confidence должен быть в [0.0, 1.0], получено: {confidence}")

        now = datetime.now(UTC).isoformat()
        relation_id = f"rel_{uuid.uuid4().hex[:12]}"

        self._conn.execute(
            """
            INSERT OR IGNORE INTO relations (
                relation_id, from_fact_id, to_fact_id, relation_type,
                confidence, knowledge_status, inference_source,
                truth_status, review_state,
                evidence_ref, created_at, valid_from, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                relation_id, from_fact_id, to_fact_id, relation_type,
                confidence, knowledge_status, inference_source,
                truth_status, review_state,
                evidence_ref, now, now,
                json.dumps(metadata) if metadata else None,
            ),
        )

        # Автоматическое создание inverse relation
        inverse_type = INVERSE_RELATIONS.get(relation_type)
        if inverse_type and inverse_type in VALID_RELATION_TYPES:
            inverse_id = f"rel_{uuid.uuid4().hex[:12]}"
            self._conn.execute(
                """
                INSERT OR IGNORE INTO relations (
                    relation_id, from_fact_id, to_fact_id, relation_type,
                    confidence, knowledge_status, inference_source,
                    truth_status, review_state,
                    evidence_ref, created_at, valid_from, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inverse_id, to_fact_id, from_fact_id, inverse_type,
                    confidence, knowledge_status, inference_source,
                    truth_status, review_state,
                    evidence_ref, now, now,
                    json.dumps({"inverse_of": relation_id}) if not metadata else None,
                ),
            )

        self._conn.commit()
        return relation_id

    def get_relations_from(
        self,
        fact_id:          str,
        relation_type:    str | None = None,
        knowledge_status: str | None = None,
        min_confidence:   float = 0.0,
        only_approved:    bool = True,
    ) -> list[Relation]:
        """Исходящие отношения от факта."""
        sql = """
            SELECT relation_id, from_fact_id, to_fact_id, relation_type,
                   confidence, knowledge_status, inference_source,
                   truth_status, review_state,
                   evidence_ref, created_at, valid_from, valid_to, metadata
            FROM relations
            WHERE from_fact_id = ?
              AND confidence >= ?
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
        fact_id:          str,
        relation_type:    str | None = None,
        knowledge_status: str | None = None,
        min_confidence:   float = 0.0,
        only_approved:    bool = True,
    ) -> list[Relation]:
        """Входящие отношения к факту."""
        sql = """
            SELECT relation_id, from_fact_id, to_fact_id, relation_type,
                   confidence, knowledge_status, inference_source,
                   truth_status, review_state,
                   evidence_ref, created_at, valid_from, valid_to, metadata
            FROM relations
            WHERE to_fact_id = ?
              AND confidence >= ?
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

    def remove_relation(self, relation_id: str) -> bool:
        """Удалить отношение. Returns True если удалено."""
        cur = self._conn.execute(
            "DELETE FROM relations WHERE relation_id = ?",
            (relation_id,),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def get_relation(self, relation_id: str) -> Relation | None:
        """Получить одно отношение по ID."""
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

    # ── Confidence propagation ─────────────────────────────────────────────────

    @staticmethod
    def _chain_confidence(relations: list[Relation]) -> ChainResult:
        """
        Честная оценка уверенности по цепочке.

        Пример: A→(0.9)→B→(0.7)→C→(0.8)→D
          min_confidence     = 0.7   (слабое звено)
          product_confidence = 0.504 (0.9 × 0.7 × 0.8)
        """
        if not relations:
            return ChainResult(
                chain=[], min_confidence=1.0, product_confidence=1.0,
                has_hypothetical=False, unknown_count=0,
            )

        confidences = [r.confidence for r in relations]
        statuses = [r.knowledge_status for r in relations]

        return ChainResult(
            chain=relations,
            min_confidence=min(confidences),
            product_confidence=math.prod(confidences),
            has_hypothetical=any(s == "hypothetical" for s in statuses),
            unknown_count=sum(1 for s in statuses if s == "unknown"),
        )

    # ── Графовый обход ─────────────────────────────────────────────────────────

    def causal_chain(
        self,
        from_fact_id:   str,
        max_depth:      int = 5,
        min_confidence: float = 0.5,
        only_known:     bool = False,
    ) -> list[ChainResult]:
        """
        Найти все каузальные цепочки от факта вглубь (BFS).
        Использует 'causes' и 'enables' рёбра.

        only_known=True — игнорировать 'inferred' и 'hypothetical' рёбра.
        """
        results: list[ChainResult] = []
        # BFS: (current_fact_id, path_so_far, visited)
        # TASK-11: deque.popleft() = O(1) vs list.pop(0) = O(n)
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
                    if only_known and rel.knowledge_status not in ("known",):
                        continue

                    new_path = path + [rel]
                    chain = self._chain_confidence(new_path)
                    results.append(chain)

                    queue.append((
                        rel.to_fact_id,
                        new_path,
                        visited | {rel.to_fact_id},
                    ))

        return results

    def implications(
        self,
        fact_id:        str,
        depth:          int = 3,
        min_confidence: float = 0.5,
    ) -> list[tuple[str, ChainResult]]:
        """
        Что логически следует из этого факта?
        Обход по 'implies' и 'causes'.
        Returns: [(implied_fact_id, chain_result), ...]
        """
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
        """
        Почему этот факт верен? Backward reasoning.
        Обход по ОБРАТНЫМ рёбрам: caused_by, implied_by, required_by.

        FIX P0 (v8.5.2 audit): после того как add_relation() начал
        сохранять backward-типы (caused_by, required_by, implied_by)
        как авто-inverse, explain() должен искать именно их, а не
        forward-типы (causes, requires, implies). До фикса всегда
        возвращал пустые списки.
        """
        causes: list[dict] = []
        requires: list[dict] = []
        implied_by: list[dict] = []

        for rel in self.get_relations_to(fact_id, relation_type="caused_by"):
            causes.append({"fact_id": rel.from_fact_id, "confidence": rel.confidence,
                           "status": rel.knowledge_status})

        for rel in self.get_relations_to(fact_id, relation_type="required_by"):
            requires.append({"fact_id": rel.from_fact_id, "confidence": rel.confidence,
                             "status": rel.knowledge_status})

        for rel in self.get_relations_to(fact_id, relation_type="implied_by"):
            implied_by.append({"fact_id": rel.from_fact_id, "confidence": rel.confidence,
                               "status": rel.knowledge_status})

        return {
            "fact_id":    fact_id,
            "caused_by":  causes,
            "required_by": requires,
            "implied_by": implied_by,
            "has_explanation": bool(causes or requires or implied_by),
        }

    def propagate_change(self, fact_id: str, change: str) -> list[dict]:
        """
        Что произойдёт если изменить этот факт? (Pearl Level 2)
        Propagate по 'causes' и 'enables' цепочкам.
        """
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
                        "path_length":      len(chain.chain),
                        "min_confidence":   chain.min_confidence,
                        "has_hypothetical": chain.has_hypothetical,
                        "relation_types":   [r.relation_type for r in chain.chain],
                    })

        return sorted(effects, key=lambda x: -x["min_confidence"])

    # ── Multi-level abstraction ────────────────────────────────────────────────

    def abstraction_ladder(
        self,
        fact_id: str,
        levels: int = 3,
    ) -> list[list[str]]:
        """
        Все уровни абстракции одновременно.
        Вверх: 'generalizes' (от конкретного к общему)
        Вниз: 'specializes' (от общего к конкретному)
        """
        ladder: list[list[str]] = [[fact_id]]

        # Вверх по уровням абстракции
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

        # Вниз (конкретизации)
        current_level = [fact_id]
        concrete: list[str] = []
        for rel in self.get_relations_from(fact_id, relation_type="specializes"):
            concrete.append(rel.to_fact_id)
        if concrete:
            ladder.insert(0, concrete)

        return ladder

    # ── Counterfactual ─────────────────────────────────────────────────────────

    def counterfactual(
        self,
        fact_id:    str,
        hypothesis: str,
    ) -> dict:
        """
        Pearl Level 2: интервенция (не контрфактуал Level 3).
        Клонирует подграф, применяет изменение, прогоняет implications.
        Клон НЕ изменяет оригинал.
        """
        effects = self.propagate_change(fact_id, hypothesis)

        return {
            "fact_id":       fact_id,
            "hypothesis":    hypothesis,
            "pearl_level":   2,
            "causal_chain":  effects,
            "affected_count": len(effects),
            "note": (
                "Pearl Level 2 (intervention). "
                "Для полного do-calculus (Level 3) нужна SCM с уравнениями."
            ),
        }

    # ── Analogical reasoning ───────────────────────────────────────────────────

    def find_analogies(
        self,
        fact_id:      str,
        cross_domain: bool = True,
    ) -> list[tuple[str, float]]:
        """
        Структурное сходство с другими фактами.
        Основано на паттерне исходящих отношений.
        """
        # Получаем профиль типов у исходного факта
        own_rels = self.get_relations_from(fact_id)
        own_types = frozenset(r.relation_type for r in own_rels)

        if not own_types:
            return []

        # Прямые analogous_to отношения — самый надёжный сигнал
        direct_analogies = self.get_relations_from(
            fact_id, relation_type="analogous_to",
        )
        results: list[tuple[str, float]] = [
            (r.to_fact_id, r.confidence) for r in direct_analogies
        ]
        seen = {fact_id} | {r.to_fact_id for r in direct_analogies}

        # Структурные аналогии: другие факты с похожим набором типов
        candidates_sql = """
            SELECT DISTINCT from_fact_id
            FROM relations
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
            # Jaccard similarity по типам
            intersection = len(own_types & cand_types)
            union = len(own_types | cand_types)
            similarity = intersection / union if union > 0 else 0.0
            if similarity >= 0.3:
                results.append((candidate_id, similarity))

        return sorted(results, key=lambda x: -x[1])[:10]

    # ── Contradiction detection ────────────────────────────────────────────────

    def find_contradictions(
        self,
        fact_id: str,
        _visited_facts: set | None = None,
    ) -> list[Relation]:
        """
        Найти все факты, противоречащие данному.
        Прямые (contradicts) + транзитивные (через implies).

        TASK-10: _visited_facts — защита от циклических графов.
        Передаётся через рекурсию, не предназначен для внешних вызовов.
        """
        # TASK-10: инициализируем visited при первом вызове
        if _visited_facts is None:
            _visited_facts = set()
        if fact_id in _visited_facts:
            return []  # цикл — выходим без бесконечной рекурсии
        _visited_facts.add(fact_id)

        direct = self.get_relations_from(fact_id, relation_type="contradicts")
        direct += self.get_relations_to(fact_id, relation_type="contradicts")

        # Дедупликация по relation_id
        seen_ids: set[str] = {r.relation_id for r in direct}
        result = list(direct)

        # Транзитивные: если B implies C и C contradicts A
        for impl_rel in self.get_relations_to(fact_id, relation_type="implies"):
            for contra_rel in self.find_contradictions(
                impl_rel.from_fact_id,
                _visited_facts=_visited_facts,  # TASK-10: передаём visited
            ):
                if contra_rel.relation_id not in seen_ids:
                    seen_ids.add(contra_rel.relation_id)
                    result.append(contra_rel)

        return result

    # ── Knowledge boundary ─────────────────────────────────────────────────────

    def knowledge_summary(self, fact_id: str) -> dict:
        """
        Честный отчёт о том, что система знает и не знает
        про данный факт и его связи.
        """
        all_rels = self.get_relations_from(fact_id) + self.get_relations_to(fact_id)

        status_counts = {"known": 0, "inferred": 0, "hypothetical": 0, "unknown": 0}
        for rel in all_rels:
            status_counts[rel.knowledge_status] = (
                status_counts.get(rel.knowledge_status, 0) + 1
            )

        confidences = [r.confidence for r in all_rels]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        min_conf = min(confidences) if confidences else 0.0

        has_contradictions = bool(self.find_contradictions(fact_id))

        # Рекомендация
        if status_counts["unknown"] > 0:
            recommendation = "incomplete"
        elif status_counts["inferred"] > 0 or status_counts["hypothetical"] > 0:
            recommendation = "verify"
        elif avg_conf >= 0.8 and not has_contradictions:
            recommendation = "reliable"
        else:
            recommendation = "verify"

        return {
            "fact_id":                fact_id,
            "total_relations":        len(all_rels),
            "known_relations":        status_counts["known"],
            "inferred_relations":     status_counts["inferred"],
            "hypothetical_relations": status_counts["hypothetical"],
            "unknown_relations":      status_counts["unknown"],
            "avg_confidence":         round(avg_conf, 4),
            "min_confidence":         round(min_conf, 4),
            "has_contradictions":     has_contradictions,
            "recommendation":         recommendation,
        }

    # ── Import (Neo4j / Graphiti, спринт 2.5) ─────────────────────────────────

    def import_snapshots(
        self,
        rows: list[dict],
        *,
        merge: bool = True,
    ) -> int:
        """
        Загрузить рёбра из внешнего графа (Neo4j snapshot).

        merge=True: пропускать дубликаты по relation_id; merge=False: очистка не делается
        (вызывающий должен reset_causal_graph() до импорта).
        """
        imported = 0
        for row in rows:
            from_id = row.get("from_fact_id")
            to_id = row.get("to_fact_id")
            rtype = row.get("relation_type")
            if not from_id or not to_id or not rtype:
                continue
            rid = row.get("relation_id")
            if rid and merge:
                existing = self.get_relation(str(rid))
                if existing:
                    continue
            try:
                self.add_relation(
                    str(from_id),
                    str(to_id),
                    str(rtype),
                    confidence=float(row.get("confidence") or 0.8),
                    knowledge_status=str(row.get("knowledge_status") or "known"),
                )
                imported += 1
            except ValueError as exc:
                logger.warning("import_snapshots: пропущено ребро %s→%s (%s): %s",
                               from_id, to_id, rtype, exc)
                continue
            except Exception as exc:
                logger.error("import_snapshots: ошибка при импорте %s→%s: %s",
                             from_id, to_id, exc)
                continue
        return imported

    # ── Statistics ─────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Статистика графа."""
        total = self._conn.execute(
            "SELECT COUNT(*) FROM relations"
        ).fetchone()[0]

        by_type = {}
        for row in self._conn.execute(
            "SELECT relation_type, COUNT(*) FROM relations GROUP BY relation_type"
        ):
            by_type[row[0]] = row[1]

        by_status = {}
        for row in self._conn.execute(
            "SELECT knowledge_status, COUNT(*) FROM relations GROUP BY knowledge_status"
        ):
            by_status[row[0]] = row[1]

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

    # ── Integrity Diagnostics (из Wiki-MCP-Server, апрель 2026) ─────────────────
    #
    # Набор инструментов для наблюдаемости графа. Из статьи:
    #   wiki_graph_stats, wiki_graph_contradictions, graph_dedup_edges —
    #   орфан-ноды, dangling-рёбра, дубли, противоречия.
    #
    # Для Velantrim это фундамент observability/auditability.

    def find_orphan_nodes(self, limit: int = 100) -> list[str]:
        """
        Найти факты с нулевым числом рёбер (изолированные узлы).

        Орфаны — факты в графе, которые не связаны ни с одним другим фактом.
        При namespace-линковщике (link_by_namespace) их должно быть <1%.
        Если >5% — линковщик не покрывает граф.
        """
        rows = self._conn.execute("""
            SELECT f.fact_id
            FROM facts f
            WHERE f.fact_id NOT IN (
                SELECT from_fact_id FROM relations
                UNION
                SELECT to_fact_id FROM relations
            )
            AND f.epistemic_state != 'Collapsed'
            LIMIT ?
        """, (limit,)).fetchall()
        return [r[0] for r in rows]

    def count_orphan_nodes(self) -> int:
        """Количество изолированных узлов."""
        row = self._conn.execute("""
            SELECT COUNT(*)
            FROM facts f
            WHERE f.fact_id NOT IN (
                SELECT from_fact_id FROM relations
                UNION
                SELECT to_fact_id FROM relations
            )
            AND f.epistemic_state != 'Collapsed'
        """).fetchone()
        return row[0] if row else 0

    def find_dangling_edges(self, limit: int = 100) -> list[dict]:
        """
        Найти рёбра, ссылающиеся на несуществующие факты.

        Dangling edge — база говорит что A→B связаны, но B (или A) нет в facts.
        Это симптом: либо факт удалён без каскада, либо баг в ingest.
        """
        rows = self._conn.execute("""
            SELECT r.relation_id, r.from_fact_id, r.to_fact_id, r.relation_type
            FROM relations r
            WHERE r.from_fact_id NOT IN (SELECT fact_id FROM facts)
               OR r.to_fact_id   NOT IN (SELECT fact_id FROM facts)
            LIMIT ?
        """, (limit,)).fetchall()
        result: list[dict] = []
        for row in rows:
            result.append({
                "relation_id": row[0],
                "from_fact_id": row[1],
                "to_fact_id": row[2],
                "relation_type": row[3],
                "missing_from": row[1] not in self._get_fact_ids_set(),
                "missing_to": row[2] not in self._get_fact_ids_set(),
            })
        return result

    def count_dangling_edges(self) -> int:
        """Количество рёбер с несуществующими узлами."""
        row = self._conn.execute("""
            SELECT COUNT(*)
            FROM relations r
            WHERE r.from_fact_id NOT IN (SELECT fact_id FROM facts)
               OR r.to_fact_id   NOT IN (SELECT fact_id FROM facts)
        """).fetchone()
        return row[0] if row else 0

    def find_duplicate_edges(self, limit: int = 100) -> list[dict]:
        """
        Найти дублирующиеся рёбра (одинаковые from+to+type).
        dedup_edges() в knowledge_linker предотвращает создание,
        но если кто-то пишет напрямую в relations — могут появиться.
        """
        rows = self._conn.execute("""
            SELECT from_fact_id, to_fact_id, relation_type, COUNT(*) AS cnt
            FROM relations
            GROUP BY from_fact_id, to_fact_id, relation_type
            HAVING cnt > 1
            LIMIT ?
        """, (limit,)).fetchall()
        return [
            {"from": r[0], "to": r[1], "type": r[2], "count": r[3]}
            for r in rows
        ]

    def find_missing_evidence(self, limit: int = 100) -> list[dict]:
        """
        Рёбра без evidence_ref (не подкреплены источником).

        Для Guardian/TruthGate: рёбра без evidence — кандидаты на downgrade
        knowledge_status до 'inferred' или 'hypothetical'.
        """
        rows = self._conn.execute("""
            SELECT relation_id, from_fact_id, to_fact_id, relation_type,
                   knowledge_status, confidence
            FROM relations
            WHERE (evidence_ref IS NULL OR evidence_ref = '')
              AND knowledge_status = 'known'
            LIMIT ?
        """, (limit,)).fetchall()
        return [
            {
                "relation_id": r[0],
                "from": r[1], "to": r[2], "type": r[3],
                "status": r[4], "confidence": r[5],
            }
            for r in rows
        ]

    def integrity_report(self) -> dict:
        """
        Полный отчёт о целостности графа.

        Объединяет все диагностики в один вызов — как wiki_graph_stats
        из статьи, но для Velantrim. Используется для:
          - CI/CD (блокировать деплой при >X орфанов)
          - Guardian dashboard (observability)
          - Аудит (грант: «система знает о своём состоянии»)
        """
        orphans = self.count_orphan_nodes()
        dangling = self.count_dangling_edges()
        s = self.stats()
        total_facts = self._conn.execute(
            "SELECT COUNT(*) FROM facts"
        ).fetchone()[0]

        orphan_pct = round(orphans / max(total_facts, 1) * 100, 2)
        integrity_score = 100.0

        issues: list[str] = []
        if orphans > 0:
            issues.append(f"{orphans} орфан-узлов ({orphan_pct}% фактов изолированы)")
            integrity_score -= min(30, orphan_pct * 10)
        if dangling > 0:
            issues.append(f"{dangling} dangling-рёбер (ссылаются на несуществующие факты)")
            integrity_score -= min(40, dangling * 2)

        # Проверка на критические проблемы
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

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _get_fact_ids_set(self) -> frozenset[str]:
        """Кэшируемый набор всех fact_id (для диагностик)."""
        rows = self._conn.execute(
            "SELECT fact_id FROM facts"
        ).fetchall()
        return frozenset(r[0] for r in rows)

    @staticmethod
    def _row_to_relation(row) -> Relation:
        """Конвертирует SQLite row в Relation dataclass."""
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


# ── Singleton API (V8.6 — для causal_bridge и ingest) ─────────────────────────

def is_causal_graph_enabled() -> bool:
    """Флаг ENABLE_CAUSAL_GRAPH из feature_config (дефолт True)."""
    try:
        from core.feature_config import get_config

        return get_config().app.enable_causal_graph
    except Exception:  # noqa: BLE001
        # F-02: раньше возвращали True МОЛЧА. Дефолт остаётся True (совпадает с
        # feature_config.enable_causal_graph=True), но сбой чтения конфига теперь виден,
        # а не маскируется. (Ср. write_gate.is_write_gate_enabled → fail-closed к False,
        # т.к. там дефолт OFF: направление fallback'а = задокументированный дефолт флага.)
        logger.warning(
            "is_causal_graph_enabled: config read failed, falling back to default=True",
            exc_info=True,
        )
        return True


def get_causal_graph() -> CausalGraph:
    """
    Делегирует в pipeline._get_causal_graph (общая БД с facts).
    """
    from core.pipeline import _get_causal_graph

    graph = _get_causal_graph()
    if graph is None:
        raise RuntimeError("CausalGraph недоступен (проверьте миграции relations)")
    return graph


def reset_causal_graph() -> None:
    """Сброс CausalGraph (полный re-import из Neo4j)."""
    from core.pipeline import reset_causal_graph as _reset

    _reset()


__all__ = [
    "CausalGraph",
    "FORWARD_RELATION_TYPES",
    "get_causal_graph",
    "is_causal_graph_enabled",
    "reset_causal_graph",
]
