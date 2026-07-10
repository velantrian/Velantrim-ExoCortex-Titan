"""
🧾 core/stimulus_map.py — Stimulus Map (V8.7 Titan, из ChatGPT предложений)

Двусторонняя трассируемость: стимул → факт → TruthGate → ответ.
Не Telegram-specific — обобщённый InputEventMap.

Связывает:
    input_event_id → memory_id → claim_type → source_status → trace_id → response

Четыре направления поиска:
    1. По факту → исходный стимул  (откуда это знание?)
    2. По стимулу → все факты       (что родилось из этого сообщения?)
    3. По факту → ответы с ним      (в каких ответах использовался?)
    4. Полная цепь стимул→факт→ответ (аудит происхождения)

SQLite таблица (та же БД velantrim.db):
    stimulus_map (stimulus_id, memory_id, claim_type, source_status, trace_id, response_id)

Инварианты:
    I-SM1: stimulus_map — append-only. Запись не удаляется, не изменяется.
    I-SM2: Каждая запись в stimulus_map имеет stimulus_id и memory_id.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.stimulus_map")

SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim_house.db")

_SM_DDL = """
CREATE TABLE IF NOT EXISTS stimulus_map (
    stimulus_id   TEXT NOT NULL,       -- input_event_id, message_id, file_id
    stimulus_type TEXT NOT NULL DEFAULT 'message',  -- message | file | chunk | tool | ingest
    memory_id     TEXT NOT NULL,       -- fact_id в памяти
    memory_type   TEXT DEFAULT 'fact', -- fact | identity | procedure
    claim_type    TEXT DEFAULT NULL,
    source_status TEXT DEFAULT NULL,
    trace_id      TEXT DEFAULT NULL,
    response_id   TEXT DEFAULT NULL,   -- ID ответа пользователю (если был)
    created_at    TEXT NOT NULL,
    PRIMARY KEY (stimulus_id, memory_id)
);
CREATE INDEX IF NOT EXISTS idx_sm_memory
    ON stimulus_map(memory_id);
CREATE INDEX IF NOT EXISTS idx_sm_stimulus
    ON stimulus_map(stimulus_id);
CREATE INDEX IF NOT EXISTS idx_sm_response
    ON stimulus_map(response_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StimulusMap:
    """
    Двусторонняя карта: стимул ↔ факт ↔ ответ.

    Использование:
        sm = StimulusMap()

        # При создании факта:
        sm.link(stimulus_id="msg_473", memory_id="fact_abc123", stimulus_type="message")

        # При генерации ответа:
        sm.attach_response(memory_id="fact_abc123", response_id="resp_882")

        # Поиск:
        sm.find_by_stimulus("msg_473")   → все факты из этого сообщения
        sm.find_by_memory("fact_abc123") → исходный стимул + все ответы с этим фактом
        sm.full_trace("fact_abc123")     → полная цепь: стимул → извлечение → ответы
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
            conn.executescript(_SM_DDL)
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning("StimulusMap DDL: %s", exc)

    # ── Запись ─────────────────────────────────────────────────────────────

    def link(
        self,
        *,
        stimulus_id: str,
        memory_id: str,
        stimulus_type: str = "message",
        memory_type: str = "fact",
        claim_type: Optional[str] = None,
        source_status: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> bool:
        """
        Связать стимул (сообщение, файл, chunk) с фактом в памяти.

        Идемпотентно: повторный вызов с тем же (stimulus_id, memory_id) — ok.
        """
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute(
                """INSERT OR REPLACE INTO stimulus_map
                   (stimulus_id, stimulus_type, memory_id, memory_type,
                    claim_type, source_status, trace_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    stimulus_id,
                    stimulus_type,
                    memory_id,
                    memory_type,
                    claim_type,
                    source_status,
                    trace_id,
                    _now(),
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as exc:
            logger.error("StimulusMap.link: %s", exc)
            return False

    def attach_response(
        self,
        *,
        memory_id: str,
        response_id: str,
    ) -> bool:
        """
        Привязать ID ответа к факту. Вызывается после генерации ответа LLM.

        Обновляет ВСЕ записи с этим memory_id (один факт может быть
        рождён из нескольких стимулов).
        """
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute(
                "UPDATE stimulus_map SET response_id = ? WHERE memory_id = ?",
                (response_id, memory_id),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as exc:
            logger.error("StimulusMap.attach_response: %s", exc)
            return False

    # ── Поиск ─────────────────────────────────────────────────────────────

    def find_by_stimulus(self, stimulus_id: str) -> List[Dict[str, Any]]:
        """Все факты, рождённые из этого стимула."""
        return self._query(
            "SELECT * FROM stimulus_map WHERE stimulus_id = ? ORDER BY created_at",
            (stimulus_id,),
        )

    def find_by_memory(self, memory_id: str) -> List[Dict[str, Any]]:
        """Все стимулы, породившие этот факт, + все ответы с ним."""
        return self._query(
            "SELECT * FROM stimulus_map WHERE memory_id = ? ORDER BY created_at",
            (memory_id,),
        )

    def find_by_response(self, response_id: str) -> List[Dict[str, Any]]:
        """Все факты, использованные в этом ответе."""
        return self._query(
            "SELECT * FROM stimulus_map WHERE response_id = ?",
            (response_id,),
        )

    def full_trace(self, memory_id: str) -> Dict[str, Any]:
        """
        Полная цепь: стимул → извлечение → ответы.

        Возвращает:
            {
                memory_id, claim_type, source_status,
                stimuli: [{stimulus_id, stimulus_type, created_at}],
                responses: [response_id],
            }
        """
        rows = self.find_by_memory(memory_id)
        if not rows:
            return {"memory_id": memory_id, "stimuli": [], "responses": []}

        stimuli = list({
            (r["stimulus_id"], r["stimulus_type"], r["created_at"])
            for r in rows
        })
        responses = list({
            r["response_id"]
            for r in rows
            if r.get("response_id")
        })

        return {
            "memory_id": memory_id,
            "claim_type": rows[0].get("claim_type"),
            "source_status": rows[0].get("source_status"),
            "trace_id": rows[0].get("trace_id"),
            "stimuli": [
                {"id": s[0], "type": s[1], "at": s[2]}
                for s in sorted(stimuli, key=lambda x: x[2])
            ],
            "responses": sorted(responses),
        }

    def stats(self) -> Dict[str, Any]:
        """Статистика stimulus_map."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            total = conn.execute("SELECT COUNT(*) FROM stimulus_map").fetchone()[0]
            with_response = conn.execute(
                "SELECT COUNT(*) FROM stimulus_map WHERE response_id IS NOT NULL"
            ).fetchone()[0]
            by_type = {}
            for row in conn.execute(
                "SELECT stimulus_type, COUNT(*) as cnt FROM stimulus_map GROUP BY stimulus_type"
            ).fetchall():
                by_type[row["stimulus_type"]] = row["cnt"]
            conn.close()
            return {
                "total_links": total,
                "with_response": with_response,
                "by_stimulus_type": by_type,
            }
        except Exception:
            return {"total_links": 0, "with_response": 0, "by_stimulus_type": {}}

    def _query(
        self, sql: str, params: tuple = ()
    ) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_map: Optional[StimulusMap] = None


def get_stimulus_map() -> StimulusMap:
    global _map
    if _map is None:
        _map = StimulusMap()
    return _map


__all__ = [
    "StimulusMap",
    "get_stimulus_map",
]
