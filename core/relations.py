# core/relations.py
# Velantrim ExoCortex — Fact Relations (the actual graph)
# v8.9.0
#
# До v8.8 "facts" — это плоская таблица. "Graph = Truth" был слоганом.
# Этот модуль превращает её в граф: явные направленные связи между фактами.
#
# v8.8.1: P1 (R-05) — collapse_for_fact вызывается GC перед hard_delete.
# v8.9.0: P6 — _l0 переведён на class-level per db_path.
#          Два RelationStore на один db_path теперь делят L0-кэш.
#          До патча: GC обновлял свой instance → другой instance читал stale.
#
# Связи — first-class объекты со своим жизненным циклом (ESM-зеркало):
#   - Каждая связь имеет epistemic_state (Observed/Supported/Validated/...).
#   - История переходов записывается (R-04).
#   - Один и тот же relation между одной парой (from, to, kind) уникален (R-02).
#
# Инварианты:
#   R-01: создание новой связи возможно только в Observed (зеркало I50).
#   R-02: UNIQUE (from_id, to_id, kind) — один тип связи на пару фактов.
#   R-03: epistemic_state меняется только через transition() (зеркало TASK-01).
#   R-04: каждое изменение epistemic_state дописывает запись в history.
#   R-05: relations не могут указывать на удалённые факты — при hard_delete
#         факта связи помечаются Collapsed (caller отвечает).
#
# Зачем:
#   - Contradicted-факт указывает на того, кто его опроверг (CONTRADICTS).
#   - TruthGate v2: Validated требует ≥2 SUPPORTS связей (RFC0001).
#   - HippoRAG / PageRank — есть граф для traversal.
#   - Consolidation предлагает ANALOGOUS_TO между удалёнными фактами.

from __future__ import annotations

import copy
import json
import os
import sqlite3
import threading
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from core.memory import ESM_STATES, ESM_TRANSITIONS, _validate_confidence

# Канонические типы связей. Расширяемо — это не enum намеренно,
# чтобы можно было заводить domain-specific связи без правки ядра.
RELATION_KINDS = {
    "SUPPORTS",           # X подтверждает Y
    "CONTRADICTS",        # X противоречит Y
    "SPECIALIZES",        # X — частный случай Y
    "GENERALIZES",        # X — обобщение Y
    "CAUSES",             # X вызывает Y (causal)
    "DEPENDS_ON",         # X зависит от Y (epistemic dependency)
    "ANALOGOUS_TO",       # X структурно похож на Y (через домены)
    "DERIVED_FROM",       # X получен из Y (provenance link)
    # R40 MAGMA: дополнительные типы для Traversal Policy
    "TEMPORAL_SEQUENCE",  # X предшествует Y во времени (temporal)
    "ENABLES",            # X делает Y возможным (influence/enabling)
    "PART_OF",            # X является частью Y (hierarchical membership)
    # R48 Abstraction Hierarchy (ChatGPT Design Review, май 2026)
    "INSTANTIATES",       # X — конкретный пример Y (факт→паттерн)
    "ABSTRACTS_FROM",     # X — абстракция от Y (паттерн→принцип→ценность)
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Relation:
    """
    Направленная связь from_id ──kind──> to_id.
    Зеркалит структуру Projection / Fact: те же ESM, audit trail, confidence.

    v8.17.5 R35: добавлены поля Hebbian LTP/LTD:
      strength    — живой вес связи [0.1, 10.0], начинается с 1.0
      ltp_count   — число активаций (LTP events)
      ltd_count   — число decay-циклов (LTD events)
    """
    relation_id:     str
    from_id:         str
    to_id:           str
    kind:            str
    confidence:      float                  = 0.5
    epistemic_state: str                    = "Observed"
    source:          str                    = "unknown"
    created_at:      str                    = field(default_factory=_now)
    updated_at:      str                    = field(default_factory=_now)
    history:         list[dict[str, Any]]   = field(default_factory=list)
    metadata:        dict[str, Any]         = field(default_factory=dict)
    # R35 Hebbian fields
    strength:        float                  = 1.0
    ltp_count:       int                    = 0
    ltd_count:       int                    = 0


class RelationStore:
    """
    CRUD + transitions для таблицы fact_relations.
    Живёт в том же SQLite-файле что и facts.

    R-02: UNIQUE (from_id, to_id, kind) — индекс.
    R-03: state меняется только через transition().

    v8.9.0 P6: _l0 теперь class-level per db_path.
    Два экземпляра для одного db_path делят один и тот же L0-кэш,
    что исключает stale reads после записи через другой instance.
    """

    L0_CAP = 512
    _ddl_initialized_paths: set = set()
    # v8.9.0 P6: shared L0 registry — db_path → OrderedDict[key, Relation]
    _l0_by_path: dict = {}
    # C1/T0.2: shared lock per db_path — protects _l0 mutations across threads
    _l0_lock_by_path: dict = {}

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.use_json_insert = sqlite3.sqlite_version_info >= (3, 38, 0)
        if db_path not in RelationStore._l0_by_path:
            RelationStore._l0_by_path[db_path] = OrderedDict()
        if db_path not in RelationStore._l0_lock_by_path:
            RelationStore._l0_lock_by_path[db_path] = threading.RLock()
        self._l0 = RelationStore._l0_by_path[db_path]
        self._l0_lock = RelationStore._l0_lock_by_path[db_path]

    @classmethod
    def _reset_l0(cls, db_path: str) -> None:
        """Test hook: clear L0 cache for a specific db_path."""
        if db_path in cls._l0_by_path:
            cls._l0_by_path[db_path].clear()

    @contextmanager
    def _db(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA foreign_keys = ON")

        if self.db_path not in RelationStore._ddl_initialized_paths:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fact_relations (
                    relation_id     TEXT PRIMARY KEY,
                    from_id         TEXT NOT NULL,
                    to_id           TEXT NOT NULL,
                    kind            TEXT NOT NULL,
                    confidence      REAL DEFAULT 0.5,
                    epistemic_state TEXT DEFAULT 'Observed',
                    source          TEXT NOT NULL,
                    created_at      TEXT NOT NULL,
                    updated_at      TEXT NOT NULL,
                    history         TEXT DEFAULT '[]',
                    metadata        TEXT DEFAULT '{}',
                    strength        REAL DEFAULT 1.0,
                    ltp_count       INTEGER DEFAULT 0,
                    ltd_count       INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_rel_triple
                ON fact_relations (from_id, to_id, kind)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rel_from ON fact_relations (from_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rel_to ON fact_relations (to_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rel_kind ON fact_relations (kind)
            """)
            cols = [r[1] for r in conn.execute("PRAGMA table_info(fact_relations)").fetchall()]
            if "strength" not in cols:
                conn.execute("ALTER TABLE fact_relations ADD COLUMN strength REAL DEFAULT 1.0")
            if "ltp_count" not in cols:
                conn.execute("ALTER TABLE fact_relations ADD COLUMN ltp_count INTEGER DEFAULT 0")
            if "ltd_count" not in cols:
                conn.execute("ALTER TABLE fact_relations ADD COLUMN ltd_count INTEGER DEFAULT 0")
            conn.commit()
            RelationStore._ddl_initialized_paths.add(self.db_path)

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ─── CRUD ──────────────────────────────────────────────────────────────────

    def add(
        self,
        from_id:    str,
        to_id:      str,
        kind:       str,
        confidence: float = 0.5,
        source:     str   = "unknown",
        metadata:   dict[str, Any] | None = None,
    ) -> Relation:
        """
        R-01: новая связь создаётся в Observed.
        Идемпотентно по (from_id, to_id, kind): при повторе обновит confidence/source.
        """
        if kind not in RELATION_KINDS:
            raise ValueError(
                f"add: unknown relation kind '{kind}'. "
                f"Allowed: {sorted(RELATION_KINDS)}"
            )
        if from_id == to_id:
            raise ValueError("add: self-loop relations are not allowed")

        _validate_confidence(confidence)

        existing = self.get(from_id, to_id, kind)
        if existing is not None:
            old_source = existing.source
            existing.confidence = _validate_confidence(confidence)
            existing.source     = source
            existing.metadata   = metadata or existing.metadata
            existing.updated_at = _now()
            if old_source != source:
                existing.history.append({
                    "event": "source_changed",
                    "from": old_source,
                    "to": source,
                    "at": existing.updated_at,
                })
            self._persist(existing, is_new=False)
            return existing

        rel = Relation(
            relation_id = str(uuid4()),
            from_id     = from_id,
            to_id       = to_id,
            kind        = kind,
            confidence  = _validate_confidence(confidence),
            source      = source,
            metadata    = metadata or {},
        )
        self._persist(rel, is_new=True)
        return rel

    def get(
        self, from_id: str, to_id: str, kind: str,
    ) -> Relation | None:
        key = f"{from_id}|{to_id}|{kind}"
        if key in self._l0:
            return copy.deepcopy(self._l0[key])
        with self._db() as conn:
            row = conn.execute(
                """SELECT * FROM fact_relations
                   WHERE from_id=? AND to_id=? AND kind=?""",
                (from_id, to_id, kind),
            ).fetchone()
            if not row:
                return None
            rel = self._row_to_relation(row)
            self._l0[key] = rel
            return copy.deepcopy(rel)

    def by_id(self, relation_id: str) -> Relation | None:
        with self._db() as conn:
            row = conn.execute(
                "SELECT * FROM fact_relations WHERE relation_id=?",
                (relation_id,),
            ).fetchone()
            return self._row_to_relation(row) if row else None

    def outgoing(
        self, from_id: str, kind: str | None = None,
        state: str | None = None,
    ) -> list[Relation]:
        return self._list_filtered(from_id=from_id, kind=kind, state=state)

    def incoming(
        self, to_id: str, kind: str | None = None,
        state: str | None = None,
    ) -> list[Relation]:
        return self._list_filtered(to_id=to_id, kind=kind, state=state)

    def neighbors(self, fact_id: str, kind: str | None = None) -> list[Relation]:
        """Все связи где fact_id участвует как from или to."""
        out_rels = self.outgoing(fact_id, kind=kind)
        in_rels  = self.incoming(fact_id, kind=kind)
        return out_rels + in_rels

    def _list_filtered(
        self,
        from_id: str | None = None,
        to_id:   str | None = None,
        kind:    str | None = None,
        state:   str | None = None,
    ) -> list[Relation]:
        where = []
        params: list[Any] = []
        if from_id is not None: where.append("from_id=?"); params.append(from_id)
        if to_id   is not None: where.append("to_id=?");   params.append(to_id)
        if kind    is not None: where.append("kind=?");    params.append(kind)
        if state   is not None: where.append("epistemic_state=?"); params.append(state)
        sql = "SELECT * FROM fact_relations"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY confidence DESC, created_at ASC"
        with self._db() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_relation(r) for r in rows]

    # ─── Transitions (R-03, R-04) ──────────────────────────────────────────────

    def transition(
        self,
        relation_id: str,
        new_state:   str,
        by:          str = "RelationStore.transition",
    ) -> bool:
        """
        Единственный путь смены epistemic_state для связи.
        Зеркало TASK-01 / P-01 / L-03.
        """
        if new_state not in ESM_STATES:
            raise ValueError(f"transition: invalid state '{new_state}'")

        rel = self.by_id(relation_id)
        if not rel:
            return False

        allowed = ESM_TRANSITIONS.get(rel.epistemic_state, set())
        if new_state not in allowed:
            raise ValueError(
                f"transition: {rel.epistemic_state} → {new_state} not allowed"
            )

        now   = _now()
        entry = {"state": new_state, "from": rel.epistemic_state, "at": now, "by": by}
        if self.use_json_insert:
            with self._db() as conn:
                conn.execute(
                    """UPDATE fact_relations
                       SET epistemic_state=?, updated_at=?,
                           history = json_insert(history, '$[#]', json(?))
                       WHERE relation_id=?""",
                    (new_state, now, json.dumps(entry), relation_id),
                )
        else:
            history = list(rel.history)
            history.append(entry)
            with self._db() as conn:
                conn.execute(
                    """UPDATE fact_relations
                       SET epistemic_state=?, updated_at=?, history=?
                       WHERE relation_id=?""",
                    (new_state, now, json.dumps(history), relation_id),
                )

        # Invalidate L0 cache
        key = f"{rel.from_id}|{rel.to_id}|{rel.kind}"
        if key in self._l0:
            self._l0[key].epistemic_state = new_state
            self._l0[key].updated_at      = now
            self._l0[key].history.append(entry)
        return True

    # ─── Bulk operations ──────────────────────────────────────────────────────

    def collapse_for_fact(self, fact_id: str, by: str = "collapse_for_fact") -> int:
        """
        R-05: при hard_delete факта вызывается отсюда — все связи где он
        участвует переводятся в Collapsed (terminal).
        Возвращает число затронутых связей.
        """
        affected = self.neighbors(fact_id)
        count = 0
        for rel in affected:
            if rel.epistemic_state == "Collapsed":
                continue
            try:
                # Direct path Observed/Supported/Validated/... → Collapsed allowed by ESM
                self.transition(rel.relation_id, "Collapsed", by=by)
                count += 1
            except ValueError:
                # Skip relations in terminal-incompatible states
                pass
        return count

    # ─── Persistence helpers ──────────────────────────────────────────────────

    def _persist(self, rel: Relation, is_new: bool) -> None:
        key = f"{rel.from_id}|{rel.to_id}|{rel.kind}"
        if is_new:
            with self._db() as conn:
                conn.execute(
                    """INSERT INTO fact_relations
                        (relation_id, from_id, to_id, kind, confidence,
                         epistemic_state, source, created_at, updated_at,
                         history, metadata, strength, ltp_count, ltd_count)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (rel.relation_id, rel.from_id, rel.to_id, rel.kind,
                     rel.confidence, rel.epistemic_state, rel.source,
                     rel.created_at, rel.updated_at,
                     json.dumps(rel.history), json.dumps(rel.metadata),
                     rel.strength, rel.ltp_count, rel.ltd_count),
                )
        else:
            # UPSERT path: keep state unchanged, persist metadata/provenance history.
            with self._db() as conn:
                conn.execute(
                    """UPDATE fact_relations
                       SET confidence=?, source=?, updated_at=?, metadata=?, history=?
                       WHERE relation_id=?""",
                    (rel.confidence, rel.source, rel.updated_at,
                     json.dumps(rel.metadata), json.dumps(rel.history), rel.relation_id),
                )
        with self._l0_lock:                    # C1/T0.2: atomic LRU update
            self._l0[key] = rel
            if len(self._l0) > self.L0_CAP:
                self._l0.popitem(last=False)

    # ─── R35: Hebbian LTP / LTD ──────────────────────────────────────────────

    def ltp_activate(
        self,
        relation_id: str,
        multiplier: float = 1.05,
        max_strength: float = 10.0,
    ) -> float:
        """
        R35 Hebbian LTP: активировать связь — strength × multiplier.
        Инвариант: strength ≤ max_strength.
        Возвращает новое значение strength.
        """
        with self._db() as conn:
            row = conn.execute(
                "SELECT strength, ltp_count FROM fact_relations WHERE relation_id=?",
                (relation_id,),
            ).fetchone()
            if not row:
                return 0.0
            new_s = min(max_strength, row["strength"] * multiplier)
            conn.execute(
                """UPDATE fact_relations SET strength=?, ltp_count=ltp_count+1
                   WHERE relation_id=?""",
                (round(new_s, 4), relation_id),
            )
        # Инвалидируем L0-кэш для этой связи
        with self._l0_lock:                    # C1/T0.2: snapshot before iteration
            stale = [k for k in self._l0 if self._l0[k].relation_id == relation_id]
            for k in stale:
                del self._l0[k]
        return round(new_s, 4)

    def ltp_with_inhibition(
        self,
        relation_id:     str,
        ltp_multiplier:  float = 1.05,
        inhibit_factor:  float = 0.95,
        protect_threshold: float = 0.4,
        max_strength:    float = 10.0,
    ) -> float:
        """
        R41 SYNAPSE Lateral Inhibition (arXiv:2601.02744, Jan 2026).

        При усилении ребра (A→B):
          1. strength(A→B) × ltp_multiplier  ← Hebbian LTP (R35)
          2. Все слабые рёбра из A к другим узлам: strength × inhibit_factor
             Защищены рёбра с strength ≥ protect_threshold

        Биологический аналог: усиление одного синапса подавляет конкурирующие.
        Предотвращает «Hub Explosion» — частый узел тянет за собой шум.

        Источник: SYNAPSE (arXiv:2601.02744) Lateral Inhibition mechanism.
        SYNAPSE shows +23% multi-hop accuracy, −95% tokens vs full-context.

        Инвариант LI-01: protect_threshold предохраняет уже сильные связи.
        Инвариант LI-02: ослабляются только active/non-Collapsed рёбра из from_id.
        Инвариант LI-03: самоингибиция не применяется (A→B не ослабляет сама себя).

        Возвращает новое значение strength усиленной связи.
        """
        # Сначала найдём from_id активируемой связи
        with self._db() as conn:
            row = conn.execute(
                "SELECT from_id, strength FROM fact_relations WHERE relation_id=?",
                (relation_id,),
            ).fetchone()
            if not row:
                return 0.0
            from_id = row["from_id"]

        # 1. Hebbian LTP на целевой связи
        new_strength = self.ltp_activate(relation_id, ltp_multiplier, max_strength)

        # 2. Lateral inhibition: ослабить конкурирующие рёбра из того же from_id
        with self._db() as conn:
            competitors = conn.execute(
                """SELECT relation_id, strength FROM fact_relations
                   WHERE from_id=?
                     AND relation_id != ?
                     AND strength < ?
                     AND epistemic_state NOT IN ('Collapsed', 'Deprecated')""",
                (from_id, relation_id, protect_threshold),
            ).fetchall()

            for comp in competitors:
                new_comp_s = max(0.1, comp["strength"] * inhibit_factor)
                conn.execute(
                    "UPDATE fact_relations SET strength=? WHERE relation_id=?",
                    (round(new_comp_s, 4), comp["relation_id"]),
                )
            # LI инвалидирует весь L0 кэш для from_id
            with self._l0_lock:                # C1/T0.2: snapshot before iteration
                stale = [k for k in self._l0 if self._l0[k].from_id == from_id]
                for k in stale:
                    del self._l0[k]

        return new_strength

    def ltd_decay_all(
        self,
        multiplier: float = 0.98,
        min_strength: float = 0.1,
    ) -> int:
        """
        R35 Hebbian LTD: снизить strength всех активных связей на multiplier.
        Вызывается из sleep-cycle консолидации.
        Возвращает число обновлённых связей.
        """
        with self._db() as conn:
            rows = conn.execute(
                """SELECT relation_id, strength FROM fact_relations
                   WHERE epistemic_state NOT IN ('Collapsed', 'Deprecated')"""
            ).fetchall()
            count = 0
            for row in rows:
                new_s = max(min_strength, row["strength"] * multiplier)
                conn.execute(
                    """UPDATE fact_relations SET strength=?, ltd_count=ltd_count+1
                       WHERE relation_id=?""",
                    (round(new_s, 4), row["relation_id"]),
                )
                count += 1
        with self._l0_lock:
            self._l0.clear()  # инвалидируем весь L0-кэш после batch update
        return count

    @staticmethod
    def _row_to_relation(row) -> Relation:
        r = dict(row)
        return Relation(
            relation_id     = r["relation_id"],
            from_id         = r["from_id"],
            to_id           = r["to_id"],
            kind            = r["kind"],
            confidence      = r["confidence"],
            epistemic_state = r["epistemic_state"],
            source          = r["source"],
            created_at      = r["created_at"],
            updated_at      = r["updated_at"],
            history         = json.loads(r.get("history") or "[]"),
            metadata        = json.loads(r.get("metadata") or "{}"),
            strength        = float(r.get("strength") or 1.0),
            ltp_count       = int(r.get("ltp_count") or 0),
            ltd_count       = int(r.get("ltd_count") or 0),
        )
