# core/version_store.py
# Velantrim ExoCortex — Bi-temporal VersionStore API (R50)
# v8.6 transfer pack from v8.17.9
#
# Источник идеи: ChatGPT Design Review (май 2026) + документы Perplexity
#   «UPDATE → CREATE NEW VERSION»
#   «прошлое нельзя переписать, только надстроить»
#
# Архитектурное решение:
#   • Не ломаем существующую таблицу `facts` V8.6
#   • Новая таблица `fact_versions` хранит ВСЕ исторические версии
#   • Старая таблица `facts` остаётся single-row-per-id (текущее состояние)
#   • `memory.SQLiteGraphStore` вызывает snapshot перед изменениями факта.
#
# Это даёт bi-temporal version records for instrumented changes:
#   • valid_time:       когда факт был верен в реальном мире
#   • transaction_time: когда система знала об этом
#
# Use case (GDPR Article 22 + recoverable audit):
#   «Что система знала о пациенте X 15 марта 2026 в 14:30?»
#   «Какая регуляторная база была у консультанта в момент совета?»
#   «Какие прецеденты были активны в графе при принятии решения?»
#
# Инварианты:
#   VS-01: новая версия НЕ удаляет старую — только закрывает её (superseded_at)
#   VS-02: caused_by записывается для каждой версии (audit-friendly)
#   VS-03: VersionStore не модифицирует facts напрямую — только пишет в fact_versions
#   VS-04: get_fact_as_of(t) детерминирован: один результат для (fact_id, t)

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


def get_db_path() -> str:
    """V8.6 uses VELANTRIM_DB_PATH as the canonical SQLite env var."""
    return os.getenv("VELANTRIM_DB_PATH", "./data/velantrim.db")


def _metadata_json(value: Any) -> str:
    if isinstance(value, str):
        try:
            parsed = json.loads(value or "{}")
        except json.JSONDecodeError:
            parsed = {"raw": value}
        return json.dumps(parsed, ensure_ascii=False, sort_keys=True)
    return json.dumps(value or {}, ensure_ascii=False, sort_keys=True)

_SCHEMA_INIT_LOCK = threading.Lock()
_SCHEMA_READY: set[str] = set()

# ═══════════════════════════════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════════════════════════════

VERSIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS fact_versions (
    version_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    fact_id         TEXT    NOT NULL,
    version_num     INTEGER NOT NULL,
    claim           TEXT,
    source          TEXT,
    confidence      REAL,
    epistemic_state TEXT,
    metadata        TEXT,

    -- VALID TIME (когда верно в мире)
    valid_from      TEXT,
    valid_to        TEXT,

    -- TRANSACTION TIME (когда знала система)
    recorded_at     TEXT    NOT NULL,
    superseded_at   TEXT,

    -- Provenance
    caused_by       TEXT,       -- "store_fact" | "transition_esm" | etc.
    checksum        TEXT,       -- SHA-256 целостность

    UNIQUE(fact_id, version_num)
);

CREATE INDEX IF NOT EXISTS idx_versions_fact_id    ON fact_versions(fact_id);
CREATE INDEX IF NOT EXISTS idx_versions_recorded   ON fact_versions(recorded_at);
CREATE INDEX IF NOT EXISTS idx_versions_superseded ON fact_versions(superseded_at);
CREATE INDEX IF NOT EXISTS idx_versions_valid_from ON fact_versions(valid_from);
"""


# ═══════════════════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class FactVersion:
    """
    PR-C1d (Issue #39): `version_id == 0` marks a MATERIALIZED, not-persisted
    version — the live `facts` row, read-time-projected into this shape by
    VersionStore._materialize_current() because it was the applicable
    version at a queried transaction_time that falls after the last closed
    fact_versions snapshot (or when no snapshot exists at all). It is never
    inserted into fact_versions; a real historical row always has
    version_id > 0 (AUTOINCREMENT starts at 1).
    """

    version_id:      int
    fact_id:         str
    version_num:     int
    claim:           str
    source:          str
    confidence:      float
    epistemic_state: str
    metadata:        dict[str, Any] | None
    valid_from:      str | None
    valid_to:        str | None
    recorded_at:     str
    superseded_at:   str | None
    caused_by:       str | None
    checksum:        str | None

    def is_current(self) -> bool:
        """True если эта версия не была заменена."""
        return self.superseded_at is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_id":      self.version_id,
            "fact_id":         self.fact_id,
            "version_num":     self.version_num,
            "claim":           self.claim,
            "source":          self.source,
            "confidence":      self.confidence,
            "epistemic_state": self.epistemic_state,
            "metadata":        self.metadata,
            "valid_from":      self.valid_from,
            "valid_to":        self.valid_to,
            "recorded_at":     self.recorded_at,
            "superseded_at":   self.superseded_at,
            "caused_by":       self.caused_by,
            "checksum":        self.checksum,
        }


# ═══════════════════════════════════════════════════════════════════════════
# VersionStore
# ═══════════════════════════════════════════════════════════════════════════

class VersionStore:
    """
    R50: Standalone bi-temporal VersionStore API.

    Использование:
        vs = VersionStore(get_db_path())

        # Перед каждым обновлением факта — снапшот старого состояния
        vs.snapshot_before_change("fact_dna_001", old_fact_data, caused_by="store_fact")

        # Запросы через время
        old = vs.get_fact_as_of("fact_dna_001", "2026-03-15T14:30:00+00:00")
        history = vs.get_fact_history("fact_dna_001")
        snapshot = vs.get_graph_as_of("2026-01-01T00:00:00+00:00")
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or get_db_path()
        self._ensure_schema()

    @contextmanager
    def _db(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("PRAGMA foreign_keys = ON")
        # Версионный/аудит-леджер — дюрабилити важнее скорости: synchronous=FULL
        # гарантирует сохранность последней транзакции даже при потере питания
        # (объём записи низкий, так что перф-стоимость fsync здесь незаметна).
        conn.execute("PRAGMA synchronous = FULL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with _SCHEMA_INIT_LOCK:
            if self.db_path in _SCHEMA_READY:
                return
            with self._db() as conn:
                conn.executescript(VERSIONS_SCHEMA)
            _SCHEMA_READY.add(self.db_path)

    # ── INSTRUMENTATION HOOK ────────────────────────────────────────────

    def snapshot_before_change(
        self,
        fact_id:    str,
        fact_data:  dict[str, Any],
        caused_by:  str = "unknown",
        now_iso:    str | None = None,
    ) -> int:
        """
        VS-01: вызывается ПЕРЕД изменением факта в основной таблице.
        Создаёт версию с superseded_at = now (старая версия заменяется новой).

        Возвращает version_id созданной snapshot-записи.
        """
        now = now_iso or datetime.now(UTC).isoformat()

        metadata_json = _metadata_json(fact_data.get("metadata", {}) or {})
        valid_from = (
            fact_data.get("valid_from")
            or fact_data.get("t_event_valid_start")
        )
        valid_to = (
            fact_data.get("valid_to")
            or fact_data.get("t_event_valid_end")
        )
        # PR-C1d (Issue #39): recorded_at must reflect when THIS version
        # (the one now being closed) itself became current — that is
        # fact_data["updated_at"], the timestamp of the write that produced
        # it. t_ingestion_start is frozen at the fact's ORIGINAL creation and
        # never advances, so using it here made every historical snapshot of
        # the same fact_id share an identical recorded_at regardless of how
        # many updates had actually happened. updated_at equals created_at
        # at creation time, so version_num==1 is unaffected by this change;
        # only version_num>1 (previously wrong) is corrected.
        recorded_at = (
            fact_data.get("updated_at")
            or fact_data.get("t_ingestion_start")
            or fact_data.get("created_at")
            or now
        )

        with self._db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT MAX(version_num) as mx FROM fact_versions WHERE fact_id=?",
                (fact_id,),
            ).fetchone()
            next_v = (row["mx"] or 0) + 1
            checksum = self._checksum(fact_data, next_v, now)
            cur = conn.execute(
                """INSERT INTO fact_versions (
                    fact_id, version_num,
                    claim, source, confidence, epistemic_state, metadata,
                    valid_from, valid_to,
                    recorded_at, superseded_at,
                    caused_by, checksum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    fact_id, next_v,
                    fact_data.get("claim", ""),
                    fact_data.get("source", ""),
                    fact_data.get("confidence", 0.5),
                    fact_data.get("epistemic_state", "Observed"),
                    metadata_json,
                    valid_from,
                    valid_to,
                    recorded_at,
                    now,             # ← superseded_at теперь, так как версия заменяется
                    caused_by,
                    checksum,
                ),
            )
            return cur.lastrowid

    def snapshot_current_fact(
        self,
        fact_id: str,
        caused_by: str = "snapshot_current_fact",
        now_iso: str | None = None,
    ) -> int | None:
        """Read the current V8.6 fact row and snapshot it into fact_versions."""
        with self._db() as conn:
            row = conn.execute("SELECT * FROM facts WHERE fact_id=?", (fact_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        try:
            data["metadata"] = json.loads(data.get("metadata") or "{}")
        except json.JSONDecodeError:
            data["metadata"] = {}
        return self.snapshot_before_change(
            fact_id,
            data,
            caused_by=caused_by,
            now_iso=now_iso,
        )

    def _checksum(self, data: dict[str, Any], version_num: int, ts: str) -> str:
        """SHA-256 целостности версии."""
        h = hashlib.sha256()
        payload = json.dumps({
            "fact_id":         data.get("fact_id", ""),
            "version_num":     version_num,
            "claim":           data.get("claim", ""),
            "source":          data.get("source", ""),
            "confidence":      data.get("confidence", 0.0),
            "epistemic_state": data.get("epistemic_state", ""),
            "metadata":        data.get("metadata", {}) or {},
            "valid_from":      data.get("valid_from") or data.get("t_event_valid_start"),
            "valid_to":        data.get("valid_to") or data.get("t_event_valid_end"),
            "ts":              ts,
        }, sort_keys=True, ensure_ascii=False)
        h.update(payload.encode("utf-8"))
        return h.hexdigest()

    def verify_versions_integrity(self, fact_id: str | None = None) -> dict[str, Any]:
        """
        Recompute stored checksums for fact_versions.

        This verifies accidental or direct-SQL tampering of version rows. It is
        not a hash-chain and does not replace external anchoring.
        """
        with self._db() as conn:
            if fact_id:
                rows = conn.execute(
                    "SELECT * FROM fact_versions WHERE fact_id=? ORDER BY version_id ASC",
                    (fact_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM fact_versions ORDER BY version_id ASC"
                ).fetchall()

        for row in rows:
            try:
                metadata = json.loads(row["metadata"] or "{}")
            except json.JSONDecodeError:
                return {
                    "ok": False,
                    "version_id": row["version_id"],
                    "fact_id": row["fact_id"],
                    "reason": "metadata json invalid",
                }
            data = {
                "fact_id":         row["fact_id"],
                "claim":           row["claim"],
                "source":          row["source"],
                "confidence":      row["confidence"],
                "epistemic_state": row["epistemic_state"],
                "metadata":        metadata,
                "valid_from":      row["valid_from"],
                "valid_to":        row["valid_to"],
            }
            recomputed = self._checksum(data, row["version_num"], row["superseded_at"])
            if recomputed != (row["checksum"] or ""):
                return {
                    "ok": False,
                    "version_id": row["version_id"],
                    "fact_id": row["fact_id"],
                    "reason": "checksum mismatch",
                }
        return {"ok": True, "checked": len(rows), "fact_id": fact_id}

    # ── TIME-TRAVEL QUERIES ─────────────────────────────────────────────

    # Selects one fact_versions row per fact_id whose *effective* transaction-
    # time interval contains a given instant. The interval is NOT taken from
    # the row's own `recorded_at` column directly (see PR-C1d/Issue #39) —
    # a version's effective start is the PREVIOUS version's superseded_at
    # (via the LAG window function over version_num), falling back to the
    # row's own recorded_at only for version_num == 1. This makes selection
    # correct even for legacy rows already sitting in a database, written
    # by the old snapshot_before_change(), where multiple versions of the
    # same fact_id share an identical (frozen) recorded_at: only the
    # version_num == 1 row's recorded_at is ever consulted directly, so a
    # stale/duplicate value on a LATER version can no longer cause it to be
    # selected too early. No migration or backfill of existing rows.
    _EFFECTIVE_INTERVAL_CTE = """
        WITH ranked AS (
            SELECT v.*,
                   LAG(v.superseded_at) OVER (
                       PARTITION BY v.fact_id ORDER BY v.version_num
                   ) AS prev_superseded
            FROM fact_versions v
            {where_fact}
        )
        SELECT * FROM ranked
        WHERE COALESCE(prev_superseded, recorded_at) <= ?
          AND (superseded_at IS NULL OR superseded_at > ?)
    """

    def get_fact_as_of(
        self,
        fact_id:          str,
        transaction_time: str,
    ) -> FactVersion | None:
        """
        Получить версию факта какой её знала система в момент `transaction_time`.

        Сначала ищем среди закрытых (superseded) историчских версий по их
        эффективному transaction-time интервалу (см. _EFFECTIVE_INTERVAL_CTE).
        Если ни одна не подходит, проверяем текущую facts-строку — она могла
        стать актуальной уже ПОСЛЕ последнего snapshot'а (см.
        _materialize_current()). Возвращает None, если факт на момент
        transaction_time ещё не существовал или уже не действовал.
        """
        with self._db() as conn:
            hist_row = conn.execute(
                self._EFFECTIVE_INTERVAL_CTE.format(where_fact="WHERE v.fact_id = ?")
                + " ORDER BY version_num DESC LIMIT 1",
                (fact_id, transaction_time, transaction_time),
            ).fetchone()
            if hist_row is not None:
                return self._row_to_version(hist_row)

            row = conn.execute(
                "SELECT * FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchone()
            if row is None:
                return None
            return self._materialize_current(conn, row, transaction_time)

    def get_fact_history(self, fact_id: str) -> list[FactVersion]:
        """Полная история версий факта, отсортированная по version_num."""
        with self._db() as conn:
            rows = conn.execute(
                """SELECT * FROM fact_versions
                   WHERE fact_id = ?
                   ORDER BY version_num ASC""",
                (fact_id,),
            ).fetchall()
        return [self._row_to_version(r) for r in rows]

    def get_graph_as_of(
        self,
        transaction_time: str,
        limit: int = 1000,
    ) -> list[FactVersion]:
        """
        Состояние всего графа на момент transaction_time.
        Возвращает по одной версии на fact_id — либо закрытую историческую
        (см. _EFFECTIVE_INTERVAL_CTE), либо, если исторической нет, текущую
        facts-строку, материализованную по тем же правилам, что и
        get_fact_as_of() (см. _materialize_current()).

        PR-C1d (Issue #39): limit применяется ПОСЛЕ дедупликации до одной
        версии на fact_id, а не до неё — раньше LIMIT обрезал результат
        SQL-запроса напрямую, что могло вернуть меньше уникальных фактов,
        чем реально подходило под transaction_time. Не открывает отдельное
        SQLite-соединение на каждый fact_id — обе стадии используют одно
        соединение `conn`, открытое один раз для всего вызова.
        """
        with self._db() as conn:
            hist_rows = conn.execute(
                self._EFFECTIVE_INTERVAL_CTE.format(where_fact=""),
                (transaction_time, transaction_time),
            ).fetchall()

            # One row per fact_id: highest version_num wins if more than one
            # historical row somehow matches (should not happen under a
            # well-formed, non-overlapping interval invariant, but kept as a
            # deterministic tie-breaker).
            best_hist: dict[str, sqlite3.Row] = {}
            for row in hist_rows:
                fid = row["fact_id"]
                current_best = best_hist.get(fid)
                if current_best is None or row["version_num"] > current_best["version_num"]:
                    best_hist[fid] = row

            results: list[FactVersion] = [
                self._row_to_version(row) for row in best_hist.values()
            ]

            facts_rows = conn.execute("SELECT * FROM facts").fetchall()
            for row in facts_rows:
                fid = row["fact_id"]
                if fid in best_hist:
                    continue
                current = self._materialize_current(conn, row, transaction_time)
                if current is not None:
                    results.append(current)

        results.sort(key=lambda fv: fv.fact_id)
        return results[:limit]

    def count_versions(self, fact_id: str | None = None) -> int:
        with self._db() as conn:
            if fact_id:
                row = conn.execute(
                    "SELECT COUNT(*) as n FROM fact_versions WHERE fact_id=?",
                    (fact_id,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) as n FROM fact_versions"
                ).fetchone()
        return row["n"] if row else 0

    def get_contradictions_over_time(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        Найти факты у которых были версии с разным эпистемическим состоянием.
        Полезно для аудита: «когда система меняла мнение о факте?»
        """
        with self._db() as conn:
            rows = conn.execute(
                """SELECT fact_id,
                          COUNT(DISTINCT epistemic_state) as state_changes,
                          MIN(recorded_at) as first_seen,
                          MAX(recorded_at) as last_change
                   FROM fact_versions
                   GROUP BY fact_id
                   HAVING state_changes > 1
                   ORDER BY state_changes DESC, last_change DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── INTERNAL ────────────────────────────────────────────────────────

    def _row_to_version(self, row: sqlite3.Row) -> FactVersion:
        meta = None
        if row["metadata"]:
            try:
                meta = json.loads(row["metadata"])
            except Exception:
                meta = None
        return FactVersion(
            version_id      = row["version_id"],
            fact_id         = row["fact_id"],
            version_num     = row["version_num"],
            claim           = row["claim"] or "",
            source          = row["source"] or "",
            confidence      = row["confidence"] or 0.5,
            epistemic_state = row["epistemic_state"] or "Observed",
            metadata        = meta,
            valid_from      = row["valid_from"],
            valid_to        = row["valid_to"],
            recorded_at     = row["recorded_at"],
            superseded_at   = row["superseded_at"],
            caused_by       = row["caused_by"],
            checksum        = row["checksum"],
        )

    def _materialize_current(
        self,
        conn: sqlite3.Connection,
        facts_row: sqlite3.Row,
        transaction_time: str,
    ) -> FactVersion | None:
        """
        PR-C1d (Issue #39, part C): build a synthetic, NOT-persisted
        FactVersion (version_id == 0 — see FactVersion docstring) from the
        live `facts` row, for a query time that falls after the last closed
        historical snapshot (or when there is no history at all).

        current_start:
          • the latest historical superseded_at for this fact_id, if any
            snapshot exists;
          • else t_ingestion_start, then created_at, then updated_at.

        current_end:
          • t_ingestion_end, if the fact has reached a terminal belief
            state; otherwise the interval is open-ended (None).

        Returns None if transaction_time falls outside
        [current_start, current_end) — i.e. before the fact existed, or
        after the system stopped believing it. Never writes to
        fact_versions; read-time only.
        """
        fact_id = facts_row["fact_id"]
        latest_superseded = conn.execute(
            "SELECT MAX(superseded_at) AS m FROM fact_versions WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()["m"]
        current_start = (
            latest_superseded
            or facts_row["t_ingestion_start"]
            or facts_row["created_at"]
            or facts_row["updated_at"]
        )
        current_end = facts_row["t_ingestion_end"]

        if current_start is None or current_start > transaction_time:
            return None
        if current_end is not None and current_end <= transaction_time:
            return None

        max_version_num = conn.execute(
            "SELECT MAX(version_num) AS m FROM fact_versions WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()["m"] or 0

        try:
            metadata = json.loads(facts_row["metadata"] or "{}")
        except json.JSONDecodeError:
            metadata = {}

        return FactVersion(
            version_id      = 0,
            fact_id         = fact_id,
            version_num     = max_version_num + 1,
            claim           = facts_row["claim"] or "",
            source          = facts_row["source"] or "",
            confidence      = facts_row["confidence"] if facts_row["confidence"] is not None else 0.5,
            epistemic_state = facts_row["epistemic_state"] or "Observed",
            metadata        = metadata,
            valid_from      = facts_row["t_event_valid_start"],
            valid_to        = facts_row["t_event_valid_end"],
            recorded_at     = current_start,
            superseded_at   = current_end,
            caused_by       = "facts.current",
            checksum        = None,
        )
