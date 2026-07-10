"""
🧬 core/provenance_chain.py — Provenance Chain (V8.7 Titan, из Crystal I89/P1-5)

Append-only цепочка провенанса для каждого факта.
Как блокчейн для памяти AI-агента. Подделка математически обнаруживается.

Каждый факт получает provenance_chain — массив событий:
    [
        {source_type: "user_input", timestamp: "...", content_hash: "..."},
        {verified_by: "truth_gate", confidence: 0.85},
        {promoted_by: "esm_transition", from: "Supported", to: "Validated"}
    ]

Инварианты:
    I89 (ProvenanceAppendOnly): provenance_chain — append-only.
        Удаление записей из цепочки запрещено.
    I87 (KnowledgeTypeImmutable): knowledge_type — read-only после Validated.

Использование:
    chain = ProvenanceChain()
    chain.append(fact_id, event_type="fact_created", actor="user", ...)
    chain.verify(fact_id)  # проверка целостности
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("velantrim.provenance_chain")

SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim_house.db")
FALLBACK_JSON = "[]"

_PC_DDL = """
CREATE TABLE IF NOT EXISTS provenance_chains (
    fact_id     TEXT NOT NULL,
    seq         INTEGER NOT NULL DEFAULT 0,
    event_type  TEXT NOT NULL,
    actor       TEXT NOT NULL DEFAULT 'system',
    from_state  TEXT DEFAULT NULL,
    to_state    TEXT DEFAULT NULL,
    reason      TEXT DEFAULT NULL,
    payload_json TEXT DEFAULT '{}',
    event_hash  TEXT NOT NULL DEFAULT '',
    prev_hash   TEXT DEFAULT NULL,
    created_at  TEXT NOT NULL,
    PRIMARY KEY (fact_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_provenance_fact
    ON provenance_chains(fact_id, seq);
"""

GENESIS = "VELANTRIM_GENESIS_BLOCK"

# ─── Типы событий ─────────────────────────────────────────────────────────────

class EventType:
    FACT_CREATED              = "fact_created"
    FACT_UPDATED              = "fact_updated"
    ESM_TRANSITION            = "esm_transition"
    TRUTH_GATE_VERDICT        = "truth_gate_verdict"
    VOLUNTARY_WRITE           = "voluntary_write"
    IMMUTABLE_ATTEMPT_BLOCKED = "immutable_attempt_blocked"
    EVIDENCE_ADDED            = "evidence_added"
    CONTRADICTION_DETECTED    = "contradiction_detected"
    FACT_COLLAPSED            = "fact_collapsed"


# ─── Ядро ─────────────────────────────────────────────────────────────────────

class ProvenanceChain:
    """
    Append-only цепочка провенанса факта.

    Каждое событие связано с предыдущим через SHA-256.
    Подделка ЛЮБОГО события математически обнаруживается при verify().
    """

    def __init__(self, db_path: str = SQLITE_PATH):
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(_PC_DDL)
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning("ProvenanceChain DDL: %s", exc)

    # ── Запись ────────────────────────────────────────────────────────────

    def append(
        self,
        fact_id: str,
        *,
        event_type: str,
        actor: str = "system",
        from_state: Optional[str] = None,
        to_state: Optional[str] = None,
        reason: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Добавить событие в цепочку провенанса.

        FIX P1 (v8.7 audit): seq-чтение + INSERT теперь в одной транзакции
        (BEGIN IMMEDIATE). До фикса 50 параллельных append → только 2 успешно,
        48 падали на lock/unique из-за гонки между _next_seq() и INSERT.
        Теперь retry на SQLITE_BUSY с экспоненциальной задержкой.

        Возвращает (ok, event_hash).
        """
        if not fact_id:
            return False, "empty_fact_id"

        import time as _time

        max_retries = 5
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self._db_path, timeout=10.0)
                conn.execute("PRAGMA journal_mode=WAL")

                # BEGIN IMMEDIATE — захватываем write lock до чтения seq,
                # чтобы никто не прочитал тот же seq параллельно
                conn.execute("BEGIN IMMEDIATE")

                seq = self._next_seq(fact_id, conn)

                prev_hash = GENESIS
                if seq > 0:
                    row = conn.execute(
                        "SELECT event_hash FROM provenance_chains "
                        "WHERE fact_id = ? AND seq = ?",
                        (fact_id, seq - 1),
                    ).fetchone()
                    if row:
                        prev_hash = row[0]

                created_at = datetime.now(timezone.utc).isoformat()
                payload_str = json.dumps(payload or {}, sort_keys=True, ensure_ascii=False)
                event_hash = self._compute_hash(
                    prev_hash, event_type, fact_id,
                    actor=actor, reason=reason or "",
                    from_state=from_state, to_state=to_state,
                    payload_str=payload_str, created_at=created_at,
                )

                conn.execute(
                    """INSERT INTO provenance_chains
                       (fact_id, seq, event_type, actor, from_state, to_state,
                        reason, payload_json, event_hash, prev_hash, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        fact_id, seq, event_type, actor,
                        from_state, to_state,
                        reason, json.dumps(payload or {}, ensure_ascii=False),
                        event_hash, prev_hash, created_at,
                    ),
                )
                conn.commit()
                conn.close()
                logger.debug(
                    "Provenance: %s seq=%d type=%s hash=%s",
                    fact_id, seq, event_type, event_hash[:12],
                )
                return True, event_hash

            except sqlite3.OperationalError as exc:
                try:
                    conn.close()
                except Exception:
                    pass
                errmsg = str(exc)
                if "database is locked" in errmsg.lower() and attempt < max_retries - 1:
                    wait = 0.05 * (2 ** attempt)  # 50ms, 100ms, 200ms, 400ms, 800ms
                    _time.sleep(wait)
                    continue
                logger.error("Provenance append (attempt %d): %s", attempt + 1, exc)
                return False, str(exc)

            except Exception as exc:
                try:
                    conn.close()
                except Exception:
                    pass
                logger.error("Provenance append: %s", exc)
                return False, str(exc)

        return False, "max_retries_exceeded"

    # ── Чтение ────────────────────────────────────────────────────────────

    def get_chain(self, fact_id: str) -> List[Dict[str, Any]]:
        """Получить полную цепочку провенанса факта."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            rows = conn.execute(
                """SELECT fact_id, seq, event_type, actor, from_state, to_state,
                          reason, payload_json, event_hash, prev_hash, created_at
                   FROM provenance_chains
                   WHERE fact_id = ?
                   ORDER BY seq""",
                (fact_id,),
            ).fetchall()
            conn.close()

            return [
                {
                    "fact_id": r[0],
                    "seq": r[1],
                    "event_type": r[2],
                    "actor": r[3],
                    "from_state": r[4],
                    "to_state": r[5],
                    "reason": r[6],
                    "payload": json.loads(r[7]) if r[7] else {},
                    "event_hash": r[8],
                    "prev_hash": r[9],
                    "created_at": r[10],
                }
                for r in rows
            ]
        except Exception:
            return []

    def get_last_event(self, fact_id: str) -> Optional[Dict[str, Any]]:
        chain = self.get_chain(fact_id)
        return chain[-1] if chain else None

    # ── Проверка ──────────────────────────────────────────────────────────

    def verify(self, fact_id: str) -> Tuple[bool, str]:
        """
        Проверить целостность цепочки провенанса.
        Пересчитывает хеш каждого события и сравнивает с сохранённым.
        """
        chain = self.get_chain(fact_id)
        if not chain:
            return True, "empty_chain"

        expected_prev = GENESIS
        for i, event in enumerate(chain):
            payload_str = json.dumps(event["payload"], sort_keys=True, ensure_ascii=False)
            recalc = self._compute_hash(
                expected_prev,
                event["event_type"],
                event["fact_id"],
                actor=event.get("actor", "system"),
                reason=event.get("reason", ""),
                from_state=event.get("from_state"),
                to_state=event.get("to_state"),
                payload_str=payload_str,
                created_at=event["created_at"],
            )

            if recalc != event["event_hash"]:
                return False, (
                    f"hash_mismatch at seq={i}: "
                    f"stored={event['event_hash'][:12]}..., "
                    f"recalc={recalc[:12]}..."
                )

            expected_prev = event["event_hash"]

        return True, f"verified ({len(chain)} events)"

    # ── Вспомогательные ──────────────────────────────────────────────────

    @staticmethod
    def _compute_hash(
        prev_hash: str,
        event_type: str,
        fact_id: str,
        *,
        actor: str = "system",
        reason: str = "",
        from_state: Optional[str] = None,
        to_state: Optional[str] = None,
        payload_str: str = "",
        created_at: str = "",
    ) -> str:
        # FIX #6/#7 (Claude audit): включаем actor, reason в хеш-цепь.
        # Раньше хеш не зависел от того КТО сделал изменение и ПОЧЕМУ —
        # подделка actor/reason не обнаруживалась verify().
        data = "|".join([
            prev_hash,
            event_type,
            fact_id,
            actor or "system",
            reason or "",
            from_state or "",
            to_state or "",
            payload_str,
            created_at,
        ])
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def _next_seq(self, fact_id: str, conn: sqlite3.Connection | None = None) -> int:
        try:
            if conn is not None:
                row = conn.execute(
                    "SELECT MAX(seq) FROM provenance_chains WHERE fact_id = ?",
                    (fact_id,),
                ).fetchone()
                return (row[0] if row[0] is not None else -1) + 1
            c = sqlite3.connect(self._db_path, timeout=10.0)
            row = c.execute(
                "SELECT MAX(seq) FROM provenance_chains WHERE fact_id = ?",
                (fact_id,),
            ).fetchone()
            c.close()
            return (row[0] if row[0] is not None else -1) + 1
        except Exception:
            return 0

    def _get_event(self, fact_id: str, seq: int) -> Optional[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            row = conn.execute(
                """SELECT fact_id, seq, event_type, actor, from_state, to_state,
                          reason, payload_json, event_hash, prev_hash, created_at
                   FROM provenance_chains
                   WHERE fact_id = ? AND seq = ?""",
                (fact_id, seq),
            ).fetchone()
            conn.close()
            if row:
                return {
                    "fact_id": row[0],
                    "seq": row[1],
                    "event_type": row[2],
                    "actor": row[3],
                    "from_state": row[4],
                    "to_state": row[5],
                    "reason": row[6],
                    "payload": json.loads(row[7]) if row[7] else {},
                    "event_hash": row[8],
                    "prev_hash": row[9],
                    "created_at": row[10],
                }
        except Exception:
            pass
        return None


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_chain: Optional[ProvenanceChain] = None


def get_provenance_chain() -> ProvenanceChain:
    global _chain
    if _chain is None:
        _chain = ProvenanceChain()
    return _chain


__all__ = [
    "ProvenanceChain",
    "EventType",
    "get_provenance_chain",
]
