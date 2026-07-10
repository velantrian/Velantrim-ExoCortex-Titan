# core/memory.py
# Velantrim ExoCortex — Memory Layer
# v8.2.1 (batch: добавлен store_facts_batch() — один SQLite transaction на N фактов,
#          -80% overhead при ingestion vs N отдельных store_fact() вызовов)
#
# Изменения v8.2.0 vs v8.1.1:
#   - Схема SQLite: добавлены 4 bi-temporal поля (I96, V9 Sprint 1 Contract)
#   - store_fact(): заполняет t_event_valid_start, t_ingestion_start при создании
#   - update_state(): при Collapsed/Contradicted устанавливает t_ingestion_end
#   - get_fact_at(): time-travel запрос (§2.1 V9)
#   - invalidate_edge(): инвалидация без DELETE (принцип V9 §2.1)
#   - search(): BM25-lite поиск по claim (заглушка до Sprint 2c Neo4j)
#   - _GLOBAL_STORE реэкспортируется как make_store() для тестовой изоляции

import hashlib
import logging
import re as _re_raw

logger = logging.getLogger("velantrim.memory")
import copy
import json
import os
import sqlite3
import threading
from collections import OrderedDict
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

from core.storage import GraphStore

# ─── ESM: матрицы и константы ─────────────────────────────────────────────────
ESM_STATES = {
    "Observed", "Hypothesized", "Supported", "Validated",
    "Contradicted", "Deprecated", "Collapsed", "ImmutableCore"
}

# FIX #2 (Claude audit): Python ESM_TRANSITIONS выровнены с DB-триггерами
# (migrations/009_truth_kernel.sql). До V8.8 Python разрешал Observed→Supported
# и Observed→Validated (минуя Hypothesized), но DB — нет.
# Теперь матрицы идентичны.
ESM_TRANSITIONS: dict[str, set] = {
    "Observed":      {"Hypothesized"},
    "Hypothesized":  {"Supported", "Contradicted", "Deprecated"},
    "Supported":     {"Validated", "Contradicted", "Hypothesized"},
    "Validated":     {"Contradicted", "ImmutableCore", "Deprecated"},
    "Contradicted":  {"Hypothesized", "Collapsed", "Deprecated"},
    "Deprecated":    {"Collapsed"},
    "Collapsed":     set(),
    "ImmutableCore": set(),
}

# Состояния при которых система «перестаёт верить» факту → t_ingestion_end
_TERMINAL_BELIEF_STATES = {"Collapsed", "Contradicted"}

# V8.8: Memory Type Taxonomy (Codex audit)
# Четыре типа памяти:
#   episodic   = "что произошло со мной/пользователем" (диалоги, события, опыт)
#   semantic   = стабильные знания/facts (World Skills Core, наука, факты)
#   procedural = how-to, skills, workflows (рецепты, алгоритмы, инструкции)
#   system     = настройки, роли, политики, capabilities (Ring Zero, конфигурация)
MEMORY_TYPES = frozenset({"episodic", "semantic", "procedural", "system"})

IMMUTABLE_FACT_IDS = {"VALUES_CORE", "RING_ZERO"}
L0_CAP = 128
SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim.db")


class ImmutableStateError(Exception):
    pass


def _validate_confidence(c: float) -> float:
    """
    Валидирует confidence для хранения в БД.

    FIX v8.5.2 (Claude audit): делегирует проверку в core.validators.assert_confidence
    (единый источник истины). Раньше эта функция принимала строки через `float(c)`
    и отвергала NaN/Inf только случайно — через семантику NaN-сравнений в диапазоне.
    Теперь явный type-check + явная проверка NaN/Inf + range. Поведение для
    валидных значений идентично прежнему (то же округление до 4 знаков).
    """
    from core.validators import assert_confidence
    c = assert_confidence(c, context="memory.store_fact")
    return round(c, 4)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _upgrade_erasure_log_schema(conn: sqlite3.Connection) -> None:
    """Миграция legacy erasure_log (fact_id PK, actor/content_hash) → схема 012."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='erasure_log'"
    ).fetchone()
    if rows is None:
        return
    cols = {r[1] for r in conn.execute("PRAGMA table_info(erasure_log)").fetchall()}
    if "erasure_id" in cols and "user_id" in cols:
        return
    conn.execute("ALTER TABLE erasure_log RENAME TO erasure_log_legacy")
    conn.execute("""
        CREATE TABLE erasure_log (
            erasure_id   TEXT PRIMARY KEY,
            fact_id      TEXT NOT NULL,
            user_id      TEXT NOT NULL DEFAULT 'default',
            reason       TEXT NOT NULL DEFAULT 'user_request',
            claim_hash   TEXT NOT NULL,
            erased_at    TEXT NOT NULL,
            request_ref  TEXT DEFAULT NULL
        )
    """)
    legacy_cols = {
        r[1] for r in conn.execute("PRAGMA table_info(erasure_log_legacy)").fetchall()
    }
    actor_col = "actor" if "actor" in legacy_cols else "user_id"
    hash_col = "content_hash" if "content_hash" in legacy_cols else "claim_hash"
    conn.execute(
        f"""
        INSERT INTO erasure_log (erasure_id, fact_id, user_id, reason, claim_hash, erased_at)
        SELECT
            'era_' || substr(hex(randomblob(6)), 1, 12),
            fact_id,
            COALESCE({actor_col}, 'default'),
            COALESCE(reason, 'user_request'),
            COALESCE({hash_col}, ''),
            erased_at
        FROM erasure_log_legacy
        """
    )
    conn.execute("DROP TABLE erasure_log_legacy")


# ─── SQLiteGraphStore ─────────────────────────────────────────────────────────
class SQLiteGraphStore(GraphStore):
    """
    Инкапсулированное хранилище графа на базе SQLite.
    Реализует GraphStore ABC включая bi-temporal операции (I96).

    Для тестовой изоляции: создавай отдельный экземпляр на каждый тест:
        store = SQLiteGraphStore(str(tmp_path / "test.db"))
    Не используй глобальный _GLOBAL_STORE в тестах напрямую.
    """

    def __init__(self, db_path: str = SQLITE_PATH, l0_cap: int = L0_CAP) -> None:
        self.db_path = db_path
        self.l0_cap = l0_cap
        self._l0: OrderedDict[str, dict] = OrderedDict()
        self._l0_lock = threading.RLock()  # C1: L0 мутируется из нескольких to_thread-потоков + sleep-worker
        self._ddl_initialized_paths: set = set()
        self._has_fact_version: bool | None = None
        self.use_json_insert = sqlite3.sqlite_version_info >= (3, 38, 0)
        self._closed = False
        # Одно WAL-соединение + RLock: исключает deadlock пула из 3 conn.
        self._sqlite_conn: sqlite3.Connection | None = None
        self._db_lock = threading.RLock()

    @contextmanager
    def _db(self):
        """Контекст БД: одно переиспользуемое соединение, сериализованное RLock."""
        if self._closed:
            raise RuntimeError(f"SQLiteGraphStore '{self.db_path}' уже закрыт")
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        with self._db_lock:
            conn = self._sqlite_conn
            if conn is None:
                conn = sqlite3.connect(
                    self.db_path, timeout=30.0, check_same_thread=False
                )
                conn.row_factory = sqlite3.Row
                self._sqlite_conn = conn
            else:
                try:
                    conn.execute("SELECT 1")
                except sqlite3.ProgrammingError:
                    conn = sqlite3.connect(
                        self.db_path, timeout=30.0, check_same_thread=False
                    )
                    conn.row_factory = sqlite3.Row
                    self._sqlite_conn = conn

            conn.execute("PRAGMA busy_timeout = 30000")
            try:
                conn.execute("PRAGMA journal_mode = WAL")
            except sqlite3.OperationalError:
                pass

            _sync = os.getenv("VELANTRIM_SQLITE_SYNCHRONOUS", "FULL").upper()
            if _sync not in ("FULL", "NORMAL", "OFF", "EXTRA"):
                _sync = "FULL"
            try:
                conn.execute(f"PRAGMA synchronous = {_sync}")
            except sqlite3.OperationalError:
                pass

            if self.db_path not in self._ddl_initialized_paths:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS facts (
                        fact_id               TEXT PRIMARY KEY,
                        claim                 TEXT NOT NULL,
                        source                TEXT NOT NULL,
                        confidence            REAL    DEFAULT 0.5,
                        epistemic_state       TEXT    DEFAULT 'Observed',
                        created_at            TEXT    NOT NULL,
                        updated_at            TEXT    NOT NULL,
                        metadata              TEXT    DEFAULT '{}',
                        history               TEXT    DEFAULT '[]',
                        -- Bi-temporal fields (I96, V9 Sprint 1 Contract)
                        t_event_valid_start   TEXT    DEFAULT NULL,
                        t_event_valid_end     TEXT    DEFAULT NULL,
                        t_ingestion_start     TEXT    DEFAULT NULL,
                        t_ingestion_end       TEXT    DEFAULT NULL,
                        -- Modality fields (v8.7, P0 claim-type spec)
                        claim_type            TEXT    NOT NULL DEFAULT 'UNKNOWN',
                        origin_type           TEXT    NOT NULL DEFAULT 'UNKNOWN',
                        -- Memory type taxonomy (v8.8 Codex audit): episodic/semantic/procedural/system
                        memory_type           TEXT    NOT NULL DEFAULT 'semantic'
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_facts_epistemic_state
                    ON facts (epistemic_state)
                """)
                # Bi-temporal индексы для time-travel запросов
                # Обёрнуты в try/except: legacy-БД без bi-temporal колонок
                # сначала получат ALTER TABLE ниже, а индексы создадутся при следующем open().
                try:
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_facts_ingestion
                        ON facts (fact_id, t_ingestion_start, t_ingestion_end)
                    """)
                except sqlite3.OperationalError:
                    pass
                try:
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_facts_event_valid
                        ON facts (fact_id, t_event_valid_start, t_event_valid_end)
                    """)
                except sqlite3.OperationalError:
                    pass
                # D1 (audit M5): expression index on claim_dedup_key → O(log N) dedup lookup
                try:
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_facts_claim_dedup
                        ON facts (json_extract(metadata, '$.claim_dedup_key'))
                    """)
                except sqlite3.OperationalError:
                    pass  # старая версия SQLite без индексов по выражению
                # V8.8: FTS5 полнотекстовый индекс для O(log N) search()
                try:
                    conn.execute("""
                        CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts
                        USING fts5(fact_id UNINDEXED, claim, source, tokenize='unicode61')
                    """)
                except sqlite3.OperationalError:
                    pass  # FTS5 не поддерживается этой сборкой SQLite
                # Миграция существующих БД — добавить колонки если их нет
                existing_cols = {
                    r[1] for r in conn.execute("PRAGMA table_info(facts)").fetchall()
                }
                for col in ("history", "t_event_valid_start", "t_event_valid_end",
                            "t_ingestion_start", "t_ingestion_end"):
                    if col not in existing_cols:
                        conn.execute(
                            f"ALTER TABLE facts ADD COLUMN {col} TEXT DEFAULT NULL"
                        )
                # v8.7 P0: modality fields — safe migration for existing databases
                if "claim_type" not in existing_cols:
                    conn.execute(
                        "ALTER TABLE facts ADD COLUMN claim_type TEXT NOT NULL DEFAULT 'UNKNOWN'"
                    )
                if "origin_type" not in existing_cols:
                    conn.execute(
                        "ALTER TABLE facts ADD COLUMN origin_type TEXT NOT NULL DEFAULT 'UNKNOWN'"
                    )

                # TASK-09: L0 Raw Memory (migration 010 DDL — идемпотентно)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS l0_raw_memory (
                        raw_id        TEXT PRIMARY KEY,
                        original_text TEXT NOT NULL,
                        content_hash  TEXT NOT NULL UNIQUE,
                        source        TEXT,
                        source_type   TEXT DEFAULT 'unknown',
                        language      TEXT DEFAULT 'unknown',
                        char_count    INTEGER NOT NULL DEFAULT 0,
                        word_count    INTEGER NOT NULL DEFAULT 0,
                        created_at    TEXT NOT NULL DEFAULT (datetime('now')),
                        metadata      TEXT DEFAULT '{}'
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_raw_hash
                    ON l0_raw_memory(content_hash)
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS l0_fact_provenance (
                        id              TEXT PRIMARY KEY,
                        raw_id          TEXT NOT NULL REFERENCES l0_raw_memory(raw_id),
                        fact_id         TEXT NOT NULL REFERENCES facts(fact_id),
                        derivation_type TEXT NOT NULL DEFAULT 'direct',
                        step_index      INTEGER NOT NULL DEFAULT 0,
                        transformation  TEXT,
                        linked_at       TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                """)
                # GDPR Art. 17/30: content-free erasure tombstones (right to be forgotten).
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS erasure_log (
                        erasure_id   TEXT PRIMARY KEY,
                        fact_id      TEXT NOT NULL,
                        user_id      TEXT NOT NULL DEFAULT 'default',
                        reason       TEXT NOT NULL DEFAULT 'user_request',
                        claim_hash   TEXT NOT NULL,
                        erased_at    TEXT NOT NULL,
                        request_ref  TEXT DEFAULT NULL
                    )
                """)
                _upgrade_erasure_log_schema(conn)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_erasure_user
                    ON erasure_log(user_id, erased_at)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_erasure_fact
                    ON erasure_log(fact_id)
                """)
                # TASK-09: derived_from на facts (указывает на l0_raw_memory.raw_id)
                if "derived_from" not in existing_cols:
                    conn.execute(
                        "ALTER TABLE facts ADD COLUMN derived_from TEXT DEFAULT NULL"
                    )

                # D1 (audit M5): backfill claim_dedup_key для legacy-фактов без него,
                # чтобы индексированный lookup был ПОЛНЫМ, а fallback не трогал keyed-факты.
                # Идемпотентно: после первого прохода запрос возвращает 0 строк (быстро по индексу).
                try:
                    from core.fact_integrity import compute_claim_dedup_key as _cdk
                    missing = conn.execute(
                        "SELECT fact_id, claim, metadata FROM facts "
                        "WHERE json_extract(metadata, '$.claim_dedup_key') IS NULL"
                    ).fetchall()
                    for _fid, _claim, _meta in missing:
                        try:
                            _md = json.loads(_meta or "{}")
                        except (json.JSONDecodeError, TypeError):
                            _md = {}
                        _md["claim_dedup_key"] = _cdk(_claim or "")
                        conn.execute(
                            "UPDATE facts SET metadata = ? WHERE fact_id = ?",
                            (json.dumps(_md), _fid),
                        )
                except Exception:
                    pass  # backfill — best-effort, не должен ломать запуск

                conn.commit()
                self._ddl_initialized_paths.add(self.db_path)

                # VersionStore — отдельное соединение; закрываем основное до DDL warmup.
                try:
                    if self._sqlite_conn is not None:
                        self._sqlite_conn.close()
                except Exception:
                    pass
                self._sqlite_conn = None
                try:
                    from core.version_store import VersionStore
                    VersionStore(self.db_path)
                except Exception:
                    logger.debug("VersionStore schema warmup skipped", exc_info=True)

                conn = self._sqlite_conn
                if conn is None:
                    conn = sqlite3.connect(
                        self.db_path, timeout=30.0, check_same_thread=False
                    )
                    conn.row_factory = sqlite3.Row
                    self._sqlite_conn = conn

            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                # Не держим файл открытым между вызовами — RelationStore/VersionStore
                # используют отдельные соединения к тому же db_path.
                try:
                    conn.close()
                except Exception:
                    pass
                self._sqlite_conn = None

    # ── L0 LRU кэш ─────────────────────────────────────────────────────────

    def _l0_put(self, fact_id: str, record: dict) -> None:
        with self._l0_lock:                       # C1: атомарный read-modify-write
            if fact_id in self._l0:
                del self._l0[fact_id]
            self._l0[fact_id] = record
            if len(self._l0) > self.l0_cap:
                self._l0.popitem(last=False)

    def _l0_get(self, fact_id: str) -> dict | None:
        with self._l0_lock:
            if fact_id not in self._l0:
                return None
            self._l0.move_to_end(fact_id)
            return self._l0[fact_id]

    # ── GDPR Art. 17 erasure + Art. 30 tombstones ────────────────────────────

    def _l0_del(self, fact_id: str) -> None:
        """Remove a fact from the L0 LRU cache (used by physical erasure)."""
        with self._l0_lock:
            self._l0.pop(fact_id, None)

    def _release_stray_locks(self) -> None:
        """Commit незавершённой транзакции на единственном соединении."""
        conn = self._sqlite_conn
        if conn is not None and conn.in_transaction:
            try:
                conn.commit()
            except Exception:  # noqa: BLE001 — best-effort lock release
                pass

    def delete_fact_l1(self, fact_id: str) -> bool:
        """Physically delete a fact from L0 cache + L1 SQLite and every dependent
        row (relations both directions, living context, affordances, L0
        provenance links, FTS index).

        Returns True if a `facts` row was removed. Ring Zero / VALUES_CORE are
        protected (I6) → ImmutableStateError. The append-only L0 raw store
        (l0_raw_memory) is intentionally NOT touched (anti-drift trigger); see
        core/erasure.py for the GDPR note on raw originals.
        """
        if fact_id in IMMUTABLE_FACT_IDS:
            raise ImmutableStateError(
                f"delete_fact_l1: '{fact_id}' is Ring Zero (I6) — deletion forbidden"
            )
        self._release_stray_locks()
        with self._db() as conn:
            present = conn.execute(
                "SELECT 1 FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchone() is not None
            # FK ON DELETE CASCADE is not relied upon — PRAGMA foreign_keys is OFF
            # on the runtime connection, so dependents are removed explicitly.
            # These tables come from SQL migrations (008/010/...), so they may be
            # absent on a store without migrations applied — guard every delete.
            try:
                conn.execute(
                    "DELETE FROM relations WHERE from_fact_id = ? OR to_fact_id = ?",
                    (fact_id, fact_id),
                )
            except sqlite3.OperationalError:
                pass  # relations table (migration 008) not present
            for _tbl, _col in (
                ("l0_fact_provenance", "fact_id"),
                ("raw_derivation_chain", "derived_fact_id"),
                ("fact_living_context", "fact_id"),
                ("fact_affordances", "fact_id"),
                ("fact_affordance_tokens", "fact_id"),
            ):
                try:
                    conn.execute(f"DELETE FROM {_tbl} WHERE {_col} = ?", (fact_id,))
                except sqlite3.OperationalError:
                    pass  # optional/legacy table absent in this DB
            try:
                conn.execute("DELETE FROM facts_fts WHERE fact_id = ?", (fact_id,))
            except sqlite3.OperationalError:
                pass  # FTS5 not available in this SQLite build
            conn.execute("DELETE FROM facts WHERE fact_id = ?", (fact_id,))
        self._l0_del(fact_id)
        return present

    def write_tombstone(
        self, fact_id: str, *, reason: str, actor: str,
        content_hash: str | None,
    ) -> None:
        """Record a content-free erasure tombstone (GDPR Art. 30)."""
        import uuid
        self._release_stray_locks()
        claim_hash = content_hash or ""
        with self._db() as conn:
            exists = conn.execute(
                "SELECT 1 FROM erasure_log WHERE fact_id = ? LIMIT 1", (fact_id,)
            ).fetchone()
            if exists:
                return
            conn.execute(
                "INSERT INTO erasure_log "
                "(erasure_id, fact_id, user_id, reason, claim_hash, erased_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    f"era_{uuid.uuid4().hex[:12]}",
                    fact_id,
                    actor,
                    reason,
                    claim_hash,
                    _now(),
                ),
            )

    def get_tombstone(self, fact_id: str) -> dict | None:
        with self._db() as conn:
            row = conn.execute(
                "SELECT erasure_id, fact_id, user_id, reason, claim_hash, erased_at "
                "FROM erasure_log WHERE fact_id = ? ORDER BY erased_at DESC LIMIT 1",
                (fact_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_tombstone(row)

    def get_tombstones(self) -> list[dict]:
        with self._db() as conn:
            rows = conn.execute(
                "SELECT erasure_id, fact_id, user_id, reason, claim_hash, erased_at "
                "FROM erasure_log ORDER BY erased_at"
            ).fetchall()
        return [self._row_to_tombstone(r) for r in rows]

    @staticmethod
    def _row_to_tombstone(row) -> dict:
        claim_hash = row[4] or ""
        return {
            "erasure_id": row[0],
            "fact_id": row[1],
            "user_id": row[2],
            "actor": row[2],
            "reason": row[3],
            "claim_hash": claim_hash,
            "content_hash": claim_hash,
            "erased_at": row[5],
        }

    def set_restricted(self, fact_id: str, restricted: bool) -> bool:
        """Mark/unmark a fact's processing restriction (GDPR Art. 18).

        The flag lives in the fact's metadata (`restricted` = ISO timestamp).
        A restricted fact stays stored but is excluded from recall
        (get_facts_by_ids). Returns True if the fact exists.
        """
        self._release_stray_locks()
        with self._db() as conn:
            row = conn.execute(
                "SELECT metadata FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchone()
            if row is None:
                return False
            try:
                meta = json.loads(row["metadata"] or "{}")
            except (json.JSONDecodeError, TypeError):
                meta = {}
            if restricted:
                meta["restricted"] = _now()
            else:
                meta.pop("restricted", None)
            conn.execute(
                "UPDATE facts SET metadata = ?, updated_at = ? WHERE fact_id = ?",
                (json.dumps(meta), _now(), fact_id),
            )
        self._l0_del(fact_id)  # invalidate cache so recall re-reads the flag
        return True

    def _fact_version_bump_sql(self, conn) -> str:
        """SET-фрагмент для bump fact_version (миграция 009 / Truth Kernel)."""
        if self._has_fact_version is None:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(facts)").fetchall()}
            self._has_fact_version = "fact_version" in cols
        if self._has_fact_version:
            return "fact_version = fact_version + 1, "
        return ""

    def _snapshot_before_change(
        self,
        fact_id: str,
        fact_data: dict[str, Any],
        caused_by: str,
    ) -> None:
        """
        Transfer Pack 1: write transaction-time history before mutating facts.

        The main V8.6 table keeps its 4-field bi-temporal contract. VersionStore
        is an additive audit/history layer; failures are logged and do not block
        the existing memory write path.
        """
        if (os.getenv("VELANTRIM_VERSION_SNAPSHOTS", "true") or "").lower() in {
            "0", "false", "no", "off",
        }:
            return
        try:
            # Закрываем основное соединение под lock, но VersionStore вызываем
            # ВНЕ lock — иначе второй поток блокируется на всё время snapshot I/O.
            with self._db_lock:
                if self._sqlite_conn is not None:
                    try:
                        if self._sqlite_conn.in_transaction:
                            self._sqlite_conn.commit()
                        self._sqlite_conn.close()
                    except Exception:
                        pass
                    self._sqlite_conn = None

            from core.version_store import VersionStore

            VersionStore(self.db_path).snapshot_before_change(
                fact_id,
                fact_data,
                caused_by=caused_by,
            )
        except Exception:
            logger.exception("VersionStore snapshot failed for %s", fact_id)

    # ── store_fact ──────────────────────────────────────────────────────────

    def store_fact(self, fact: dict) -> bool:
        """
        Сохранить факт. Возвращает True если был реальный INSERT (новый факт),
        False если факт уже существовал (UPSERT или no-op).

        TASK-04: возвращаемое значение используется pipeline для условного
        вызова mark_retriever_dirty() — только при реальных изменениях базы.
        TASK-05: no-op guard пропускает SQL если claim/source/confidence не изменились.
        """
        fact_id = fact.get("fact_id")
        if not fact_id:
            raise ValueError("store_fact: fact_id обязателен")

        existing_preview = self.get_fact(fact_id)
        is_new = existing_preview is None
        if is_new:
            from core.memory_budget import check_before_write

            check_before_write(is_new_insert=True)

        requested_state = fact.get("epistemic_state", "Observed")
        if requested_state not in ESM_STATES:
            raise ValueError(f"store_fact: недопустимое ESM-состояние '{requested_state}'")

        if requested_state != "Observed":
            is_ring_zero_seed = (fact_id in IMMUTABLE_FACT_IDS and
                                 requested_state == "Validated")
            if not is_ring_zero_seed:
                raise ValueError(
                    "store_fact: новые факты создаются только в 'Observed'."
                )

        confidence = _validate_confidence(fact.get("confidence", 0.5))
        metadata_dict = fact.get("metadata", {}) or {}
        now = _now()
        new_claim = fact.get("claim", "")
        source_val = fact.get("source", "unknown")

        # v8.7 P0: классификация модальности (детерминированная, без LLM)
        from core.validators import normalize_claim_type, normalize_origin_type
        _raw_ct = fact.get("claim_type")
        _raw_ot = fact.get("origin_type")
        if not _raw_ct or _raw_ct == "UNKNOWN":
            # Автоклассификация если явно не задано
            try:
                from core.claim_classifier import classify_claim as _classify
                _ct, _ot, _ = _classify(
                    new_claim, source_val,
                    explicit_claim_type=_raw_ct,
                    explicit_origin_type=_raw_ot,
                )
            except Exception:
                _ct = normalize_claim_type(_raw_ct)
                _ot = normalize_origin_type(_raw_ot)
        else:
            _ct = normalize_claim_type(_raw_ct)
            _ot = normalize_origin_type(_raw_ot) if not _raw_ot or _raw_ot == "UNKNOWN" else normalize_origin_type(_raw_ot)

        # v8.7 P0.5: Write Protocol Gate (флаг ENABLE_WRITE_GATE, default OFF) — единый
        # эпистемический контроль на write-пути: WORLD_FACT обязан нести провенанс,
        # LLM-world-fact — evidence. Reject → не пишем, лог, return False. Закрывает
        # «write-путь без truth-гейта». Субъективное/UNKNOWN допускаются (Observed).
        from core.write_gate import admit_fact, is_write_gate_enabled
        if is_write_gate_enabled():
            _wg_refs = (metadata_dict or {}).get("evidence_refs") or []
            _wg_ok, _wg_reason = admit_fact(
                claim_type=_ct, origin_type=_ot,
                source=source_val, has_evidence=bool(_wg_refs),
            )
            if not _wg_ok:
                logger.warning("WriteProtocolGate отклонил факт %s: %s", fact_id, _wg_reason)
                return False
            if _ot == "UNKNOWN" and _raw_ot:
                pass  # явное UNKNOWN — оставляем
            elif not _raw_ot:
                try:
                    from core.claim_classifier import classify_claim as _classify
                    _, _ot, _ = _classify(new_claim, source_val)
                except Exception:
                    _ot = normalize_origin_type(None)

        existing = self.get_fact(fact_id)
        state_for_checksum = (
            existing["epistemic_state"] if existing else requested_state
        )
        from core.fact_integrity import (
            assert_claim_update_allowed,
            attach_integrity_metadata,
        )

        if existing:
            assert_claim_update_allowed(existing, new_claim)

        metadata_dict = attach_integrity_metadata(
            metadata_dict,
            claim=new_claim,
            source=source_val,
            confidence=confidence,
            epistemic_state=state_for_checksum,
        )
        from core.interoception import attach_somatic_metadata, notify_somatic

        metadata_dict, somatic_marker = attach_somatic_metadata(metadata_dict)
        from core.domain_tags import apply_domain_to_metadata, is_domain_tags_enabled

        if is_domain_tags_enabled():
            explicit = metadata_dict.get("domain")
            metadata_dict = apply_domain_to_metadata(
                metadata_dict,
                claim=new_claim,
                source=source_val,
                explicit_domain=explicit,
                infer=True,
            )
        fact["metadata"] = metadata_dict

        record = {
            "fact_id":             fact_id,
            "claim":               new_claim,
            "source":              fact.get("source", "unknown"),
            "confidence":          confidence,
            "epistemic_state":     requested_state,
            "created_at":          now,
            "updated_at":          now,
            "metadata":            metadata_dict,
            "history":             [],
            # Bi-temporal: устанавливаются при создании, никогда не обновляются
            "t_event_valid_start": now,
            "t_event_valid_end":   None,
            "t_ingestion_start":   now,
            "t_ingestion_end":     None,
            # v8.7 P0: модальность (claim_type) и происхождение (origin_type)
            "claim_type":          _ct,
            "origin_type":         _ot,
            # v8.8: Memory type taxonomy (Codex audit): episodic/semantic/procedural/system
            "memory_type":         fact.get("memory_type", "semantic"),
        }

        if existing:
            # TASK-02: ЗАЩИТА ОТ SEMANTIC DRIFT
            if (existing["claim"] != new_claim and
                    existing["epistemic_state"] in {"Validated", "Supported"}):
                allowed = ESM_TRANSITIONS.get(existing["epistemic_state"], set())
                if "Contradicted" not in allowed:
                    raise ValueError(
                        f"store_fact: дрифт claim у '{fact_id}' в состоянии "
                        f"'{existing['epistemic_state']}' — переход в Contradicted "
                        f"запрещён матрицей. Используй transition_esm() явно."
                    )
                record["epistemic_state"] = "Contradicted"
                record["history"] = existing.get("history", [])
                record["history"].append({
                    "state": "Contradicted",
                    "from":  existing["epistemic_state"],
                    "at":    now,
                    "by":    "store_fact_upsert_drift_protection",
                })
            else:
                record["epistemic_state"] = existing["epistemic_state"]
                record["history"]         = existing.get("history", [])

            # Bi-temporal: сохраняем оригинальные start-времена
            record["created_at"]          = existing["created_at"]
            record["t_event_valid_start"]  = existing.get("t_event_valid_start", now)
            record["t_ingestion_start"]    = existing.get("t_ingestion_start", now)
            # end-времена: не трогаем (управляются через invalidate_edge)
            record["t_event_valid_end"]    = existing.get("t_event_valid_end")
            record["t_ingestion_end"]      = existing.get("t_ingestion_end")

            # TASK-05: no-op guard — пропускаем SQL если ничего не изменилось.
            # Если claim/source/confidence не изменились и drift protection не
            # сработала (она требует claim != existing_claim) → чистый no-op.
            # Примечание: drift protection возможна только при claim != new_claim,
            # поэтому условие record[epistemic_state] != Contradicted эквивалентно
            # claim == existing[claim] в этом контексте — safe to check напрямую.
            _is_noop = (
                existing["claim"]  == new_claim
                and existing["source"] == fact.get("source", "unknown")
                and abs(existing["confidence"] - confidence) < 1e-9
                and record["epistemic_state"] != "Contradicted"
            )
            if _is_noop:
                self._l0_put(fact_id, record)
                return False  # TASK-04: не новый факт, retriever актуален

        if existing:
            self._snapshot_before_change(
                fact_id,
                existing,
                caused_by="memory.store_fact",
            )

        # TASK-09: derived_from — провенанс из L0 Raw Memory
        derived_from = fact.get("derived_from")
        record["derived_from"] = derived_from

        l1_record = {
            **record,
            "metadata": json.dumps(metadata_dict),
            "history":  json.dumps(record["history"]),
        }

        # BUG-FIX v8.3.1: при срабатывании drift protection (TASK-02)
        # epistemic_state и history меняются в record. SQL ниже по умолчанию
        # ИХ НЕ ТРОГАЕТ — что приводило к split-brain L0/L1.
        # Поэтому отдельно сохраняем флаг и обновляем эти поля в SQL.
        _drift_detected = (
            existing is not None
            and record["epistemic_state"] == "Contradicted"
            and existing["epistemic_state"] != "Contradicted"
        )

        with self._db() as conn:
            conn.execute("""
                INSERT INTO facts
                    (fact_id, claim, source, confidence, epistemic_state,
                     created_at, updated_at, metadata, history,
                     t_event_valid_start, t_event_valid_end,
                     t_ingestion_start,   t_ingestion_end,
                     derived_from,
                     claim_type, origin_type, memory_type)
                VALUES
                    (:fact_id, :claim, :source, :confidence, :epistemic_state,
                     :created_at, :updated_at, :metadata, :history,
                     :t_event_valid_start, :t_event_valid_end,
                     :t_ingestion_start,   :t_ingestion_end,
                     :derived_from,
                     :claim_type, :origin_type, :memory_type)
                ON CONFLICT(fact_id) DO UPDATE SET
                    claim       = excluded.claim,
                    source      = excluded.source,
                    confidence  = excluded.confidence,
                    updated_at  = excluded.updated_at,
                    metadata    = excluded.metadata,
                    -- v8.7: обновляем модальность если передана явно (не UNKNOWN)
                    claim_type  = CASE WHEN excluded.claim_type != 'UNKNOWN'
                                  THEN excluded.claim_type
                                  ELSE facts.claim_type END,
                    origin_type = CASE WHEN excluded.origin_type != 'UNKNOWN'
                                  THEN excluded.origin_type
                                  ELSE facts.origin_type END,
                    -- v8.8: memory_type обновляем если передан не default
                    memory_type = CASE WHEN excluded.memory_type != 'semantic'
                                  THEN excluded.memory_type
                                  ELSE facts.memory_type END
                -- epistemic_state, history, t_*_start, derived_from намеренно исключены:
                -- управляются только через transition_esm() / invalidate_edge().
            """, l1_record)

            # v8.3.1 split-brain fix: если drift привёл к Contradicted —
            # синхронизируем L1 с L0 (drift protection — единственное
            # исключение из правила "epistemic_state только через transition_esm").
            if _drift_detected:
                conn.execute(
                    "UPDATE facts SET epistemic_state = ?, history = ? "
                    "WHERE fact_id = ?",
                    (record["epistemic_state"], l1_record["history"], fact_id),
                )

        # SPLIT-BRAIN FIX (audit C-2): L0-кэш пишем ТОЛЬКО ПОСЛЕ успешной записи в L1 (durable).
        # Раньше _l0_put шёл ДО INSERT → при сбое L1 в L0 оставался факт, которого нет в L1.
        # Теперь порядок L1→L0: если INSERT упал, L0 не загрязняется (соответствует инварианту D4).
        self._l0_put(fact_id, record)

        if somatic_marker:
            uid = str(metadata_dict.get("user_id") or "default")
            notify_somatic(
                somatic_marker,
                user_id=uid,
                distress=metadata_dict.get("somatic_distress"),
                source="store_fact",
            )

        # V8.8: синхронизировать FTS5 индекс
        try:
            with self._db() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO facts_fts(rowid, fact_id, claim, source) "
                    "VALUES ((SELECT rowid FROM facts WHERE fact_id=?), ?, ?, ?)",
                    (fact_id, fact_id, new_claim, source_val),
                )
        except sqlite3.OperationalError:
            pass  # FTS5 недоступен

        # TASK-04: True = реальный INSERT (новый факт) → retriever нужно обновить
        #          False = UPSERT существующего → retriever актуален
        return existing is None

    # ── get_fact ────────────────────────────────────────────────────────────

    def get_fact(self, fact_id: str) -> dict | None:
        cached = self._l0_get(fact_id)
        if cached is not None:
            return copy.deepcopy(cached)
        with self._db() as conn:
            row = conn.execute(
                "SELECT * FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchone()
            if row:
                result = dict(row)
                result["metadata"] = json.loads(result["metadata"])
                result["history"]  = json.loads(result.get("history") or "[]")
                self._l0_put(fact_id, result)
                return copy.deepcopy(result)
        return None

    def find_fact_id_by_episode_hash(self, episode_hash: str) -> str | None:
        """Pattern separation: найти факт с тем же episode_hash в metadata."""
        if not episode_hash:
            return None
        with self._db() as conn:
            row = conn.execute(
                """
                SELECT fact_id FROM facts
                WHERE json_extract(metadata, '$.episode_hash') = ?
                LIMIT 1
                """,
                (episode_hash,),
            ).fetchone()
            return row[0] if row else None

    def find_fact_id_by_claim_dedup(self, claim: str) -> str | None:
        """Дедуп по содержанию claim (игнорирует source и регистр)."""
        from core.fact_integrity import (
            compute_claim_dedup_key,
            normalize_claim_for_dedup,
        )

        dedup_key = compute_claim_dedup_key(claim)
        target = normalize_claim_for_dedup(claim)
        if not dedup_key or len(target) < 3:
            return None
        with self._db() as conn:
            if dedup_key:
                row = conn.execute(
                    """
                    SELECT fact_id FROM facts
                    WHERE json_extract(metadata, '$.claim_dedup_key') = ?
                    LIMIT 1
                    """,
                    (dedup_key,),
                ).fetchone()
                if row:
                    return row[0]
            # D1 (audit M5): основной lookup выше — индексирован и ПОЛНЫЙ для любого
            # факта с claim_dedup_key (его ставят store_fact и store_facts_batch, а
            # init бэкафиллит legacy). Сканируем ТОЛЬКО факты без ключа (после бэкафилла
            # их нет) — нет лимита 5000 (M5 закрыт) и нет O(N)-скана на горячем пути.
            for fid, stored_claim in conn.execute(
                """
                SELECT fact_id, claim FROM facts
                WHERE json_extract(metadata, '$.claim_dedup_key') IS NULL
                """
            ):
                if normalize_claim_for_dedup(stored_claim or "") == target:
                    return fid
        return None

    # ── get_all_facts ───────────────────────────────────────────────────────

    def get_all_facts(
        self,
        epistemic_state: str | None = None,
        domain: str | None = None,
    ) -> list[dict]:
        with self._db() as conn:
            if epistemic_state and domain:
                rows = conn.execute(
                    """
                    SELECT * FROM facts
                    WHERE epistemic_state = ?
                      AND (
                        json_extract(metadata, '$.domain') = ?
                        OR json_extract(metadata, '$.content_domain') = ?
                      )
                    ORDER BY created_at, fact_id
                    """,
                    (epistemic_state, domain, domain),
                ).fetchall()
            elif epistemic_state:
                rows = conn.execute(
                    "SELECT * FROM facts WHERE epistemic_state = ? "
                    "ORDER BY created_at, fact_id",
                    (epistemic_state,),
                ).fetchall()
            elif domain:
                rows = conn.execute(
                    """
                    SELECT * FROM facts
                    WHERE json_extract(metadata, '$.domain') = ?
                       OR json_extract(metadata, '$.content_domain') = ?
                    ORDER BY created_at, fact_id
                    """,
                    (domain, domain),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM facts ORDER BY created_at, fact_id"
                ).fetchall()
            result = []
            for row in rows:
                r = dict(row)
                r["metadata"] = json.loads(r["metadata"])
                r["history"]  = json.loads(r.get("history") or "[]")
                self._l0_put(r["fact_id"], r)
                result.append(copy.deepcopy(r))
            return result

    # ── L0 Raw Memory (TASK-09) ──────────────────────────────────────────────────

    def store_raw_text(
        self,
        text:        str,
        source:      str | None = None,
        source_type: str = "user_input",
    ) -> str:
        """
        TASK-09: Сохранить оригинальный текст в L0 Raw Memory (иммутабельно).
        Дедупликация по SHA256 — повторный вызов с тем же текстом → тот же raw_id.
        Возвращает raw_id.
        """
        if not text or not text.strip():
            raise ValueError("L0 Raw Memory: нельзя сохранить пустой текст")

        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        now = datetime.now(UTC).isoformat()
        word_count = len(_re_raw.findall(r"\S+", text))

        with self._db() as conn:
            existing = conn.execute(
                "SELECT raw_id FROM l0_raw_memory WHERE content_hash = ?",
                (content_hash,),
            ).fetchone()
            if existing:
                return existing[0]

            raw_id = f"raw_{content_hash[:16]}"
            conn.execute(
                """INSERT OR IGNORE INTO l0_raw_memory
                   (raw_id, original_text, content_hash,
                    source, source_type, char_count, word_count, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (raw_id, text, content_hash, source, source_type,
                 len(text), word_count, now),
            )
        return raw_id

    def link_raw_to_fact(
        self,
        raw_id:  str,
        fact_id: str,
        derivation_type: str = "direct",
    ) -> None:
        """
        TASK-09: Связать derived факт с оригинальным raw_id в провенанс-таблице.
        Также устанавливает facts.derived_from = raw_id и инвалидирует L0-кэш.
        """
        prov_id = f"prov_{hashlib.sha256((raw_id+fact_id).encode()).hexdigest()[:16]}"
        now = datetime.now(UTC).isoformat()
        with self._db() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO l0_fact_provenance
                   (id, raw_id, fact_id, derivation_type, linked_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (prov_id, raw_id, fact_id, derivation_type, now),
            )
            conn.execute(
                "UPDATE facts SET derived_from = ? WHERE fact_id = ? AND derived_from IS NULL",
                (raw_id, fact_id),
            )
        # Инвалидируем L0-кэш чтобы get_fact() увидел обновлённый derived_from
        with self._l0_lock:
            if fact_id in self._l0:
                del self._l0[fact_id]

    def get_raw_text_for_fact(self, fact_id: str) -> str | None:
        """TASK-09: Оригинальный L0-текст для derived факта."""
        with self._db() as conn:
            row = conn.execute(
                """
                SELECT r.original_text
                FROM l0_raw_memory r
                JOIN facts f ON f.derived_from = r.raw_id
                WHERE f.fact_id = ?
                """,
                (fact_id,),
            ).fetchone()
            if row:
                return row[0]
            row = conn.execute(
                "SELECT derived_from FROM facts WHERE fact_id = ?",
                (fact_id,),
            ).fetchone()
            if row and row[0]:
                raw_row = conn.execute(
                    "SELECT original_text FROM l0_raw_memory WHERE raw_id = ?",
                    (row[0],),
                ).fetchone()
                if raw_row:
                    return raw_row[0]
        return None

    # ── get_fact_ids / get_facts_by_ids (TASK-06) ──────────────────────────────

    def get_fact_ids(
        self, limit: int = 10_000, epistemic_state: str | None = None
    ) -> list[str]:
        """
        TASK-06: Лёгкий запрос — только fact_id без полного тела.
        SELECT fact_id вместо SELECT * — кратно дешевле на больших базах.
        limit=10_000 предохраняет от неограниченного роста RAM при работе
        без NGramIndex. Факты отсортированы по updated_at DESC (свежие важнее).
        """
        with self._db() as conn:
            if epistemic_state:
                rows = conn.execute(
                    "SELECT fact_id FROM facts WHERE epistemic_state = ? "                    "ORDER BY updated_at DESC LIMIT ?",
                    (epistemic_state, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT fact_id FROM facts ORDER BY updated_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [row["fact_id"] for row in rows]

    def get_facts_by_ids(self, fact_ids: list[str]) -> list[dict]:
        """
        TASK-06: Получить полные факты по списку ID.
        Используется после NGram-фильтрации — тянем только нужные N записей.
        Факты отсутствующие в БД — пропускаются без ошибки.
        """
        if not fact_ids:
            return []
        # Проверяем L0-кэш сначала — избегаем SQL для горячих фактов
        result = []
        miss_ids = []
        for fid in fact_ids:
            cached = self._l0_get(fid)
            if cached is not None:
                result.append(copy.deepcopy(cached))
            else:
                miss_ids.append(fid)
        if miss_ids:
            placeholders = ",".join("?" * len(miss_ids))
            with self._db() as conn:
                rows = conn.execute(
                    f"SELECT * FROM facts WHERE fact_id IN ({placeholders})",
                    miss_ids,
                ).fetchall()
                for row in rows:
                    r = dict(row)
                    r["metadata"] = json.loads(r["metadata"])
                    r["history"]  = json.loads(r.get("history") or "[]")
                    self._l0_put(r["fact_id"], r)
                    result.append(copy.deepcopy(r))
        # GDPR Art. 18: restricted facts are excluded from recall / answers.
        return [f for f in result if not (f.get("metadata") or {}).get("restricted")]

    # ── update_state (только из transition_esm) ─────────────────────────────

    def update_state(
        self,
        fact_id: str,
        new_state: str,
        history_entry: dict[str, Any],
        now: str,
    ) -> bool:
        """
        Атомарно обновить epistemic_state + history.
        При переходе в терминальное состояние (Collapsed, Contradicted)
        устанавливает t_ingestion_end = now (система перестала верить факту).
        """
        set_ingestion_end = new_state in _TERMINAL_BELIEF_STATES
        # FIX #19 (Claude audit): запоминаем текущее состояние до UPDATE для CAS-guard
        old_state: str = "Observed"

        # ── Шаг 1: подготовить L0/metadata ДО записи в L1.
        # Считаем новую integrity-metadata на КОПИИ (не мутируя живой L0-объект по
        # ссылке — это попутно закрывает aliasing-гонку). claim/source/confidence не
        # меняются переходом, поэтому читать факт можно из текущего (до-update) состояния.
        cached = self._l0_get(fact_id)
        if cached is None:
            cached = self.get_fact(fact_id)
        new_metadata_json = None
        if cached is not None:
            old_state = cached.get("epistemic_state", "Observed")  # FIX #19: сохраняем до мутации
            cached = copy.deepcopy(cached)
            cached["epistemic_state"] = new_state
            cached["updated_at"] = now
            cached.setdefault("history", []).append(history_entry)
            if set_ingestion_end and not cached.get("t_ingestion_end"):
                cached["t_ingestion_end"] = now
            from core.fact_integrity import attach_integrity_metadata

            cached["metadata"] = attach_integrity_metadata(
                cached.get("metadata") or {},
                claim=cached.get("claim", ""),
                source=cached.get("source", "unknown"),
                confidence=float(cached.get("confidence", 0.5)),
                epistemic_state=new_state,
            )
            new_metadata_json = json.dumps(cached["metadata"])

        # ── Шаг 2: state + history (+ t_ingestion_end) + metadata — В ОДНОЙ
        # транзакции. FIX #19 (Claude audit): CAS-guard — WHERE epistemic_state = ?
        # предотвращает check-then-act гонку при параллельных transition_esm вызовах.
        with self._db() as conn:
            bump = self._fact_version_bump_sql(conn)
            if self.use_json_insert:
                if set_ingestion_end:
                    conn.execute(f"""
                        UPDATE facts
                        SET epistemic_state = ?,
                            updated_at      = ?,
                            {bump}history         = json_insert(history, '$[#]', json(?)),
                            t_ingestion_end = COALESCE(t_ingestion_end, ?)
                        WHERE fact_id = ? AND epistemic_state = ?
                    """, (new_state, now, json.dumps(history_entry), now, fact_id, old_state))
                else:
                    conn.execute(f"""
                        UPDATE facts
                        SET epistemic_state = ?,
                            updated_at      = ?,    {bump}history         = json_insert(history, '$[#]', json(?))
                        WHERE fact_id = ? AND epistemic_state = ?
                    """, (new_state, now, json.dumps(history_entry), fact_id, old_state))
            else:
                row = conn.execute(
                    "SELECT history FROM facts WHERE fact_id = ?", (fact_id,)
                ).fetchone()
                if not row:
                    return False
                history_l1 = json.loads(row[0] or "[]")
                history_l1.append(history_entry)
                if set_ingestion_end:
                    conn.execute(f"""
                        UPDATE facts
                        SET epistemic_state = ?, updated_at = ?,
                            {bump}history = ?,
                            t_ingestion_end = COALESCE(t_ingestion_end, ?)
                        WHERE fact_id = ? AND epistemic_state = ?
                    """, (new_state, now, json.dumps(history_l1), now, fact_id, old_state))
                else:
                    conn.execute(f"""
                        UPDATE facts
                        SET epistemic_state = ?, updated_at = ?,
                            {bump}history = ?
                        WHERE fact_id = ? AND epistemic_state = ?
                    """, (new_state, now, json.dumps(history_l1), fact_id, old_state))

            # metadata/checksum — в ТОЙ ЖЕ транзакции (а не отдельной)
            if new_metadata_json is not None:
                conn.execute(
                    "UPDATE facts SET metadata = ? WHERE fact_id = ?",
                    (new_metadata_json, fact_id),
                )

        # ── Шаг 3: публикуем L0 ТОЛЬКО после успешного commit L1 (инвариант L1→L0)
        if cached is not None:
            self._l0_put(fact_id, cached)
        return True

    # ── transition_esm ──────────────────────────────────────────────────────

    def transition_esm(
        self, fact_id: str, new_state: str, by: str = "transition_esm"
    ) -> bool:
        if new_state not in ESM_STATES:
            raise ValueError(f"transition_esm: недопустимое состояние '{new_state}'")
        if fact_id in IMMUTABLE_FACT_IDS:
            raise ImmutableStateError(
                f"transition_esm: факт '{fact_id}' защищён Ring Zero"
            )
        if new_state == "ImmutableCore":
            raise ImmutableStateError(
                "transition_esm: переход в 'ImmutableCore' только для Ring Zero"
            )
        self._release_stray_locks()
        fact = self.get_fact(fact_id)
        if not fact:
            return False
        current_state = fact.get("epistemic_state", "Observed")
        allowed = ESM_TRANSITIONS.get(current_state)
        if allowed is not None and new_state not in allowed:
            raise ValueError(
                f"transition_esm: переход '{current_state}' → '{new_state}' недопустим"
            )
        now = _now()
        history_entry = {
            "state": new_state, "from": current_state, "at": now, "by": by
        }
        self._snapshot_before_change(
            fact_id,
            fact,
            caused_by=f"memory.transition_esm:{by}",
        )
        return self.update_state(fact_id, new_state, history_entry, now)

    _ESM_LADDER = ("Observed", "Hypothesized", "Supported", "Validated")

    def promote_esm_to(self, fact_id: str, target: str, by: str = "promote_esm") -> bool:
        """Пошагово повышает факт до target по канонической лестнице ESM."""
        if target not in ESM_STATES:
            raise ValueError(f"promote_esm_to: недопустимое состояние '{target}'")
        fact = self.get_fact(fact_id)
        if not fact:
            return False
        current = fact.get("epistemic_state", "Observed")
        if current == target:
            return True
        if target in self._ESM_LADDER and current in self._ESM_LADDER:
            cur_i = self._ESM_LADDER.index(current)
            tgt_i = self._ESM_LADDER.index(target)
            if cur_i >= tgt_i:
                return True
            for state in self._ESM_LADDER[cur_i + 1 : tgt_i + 1]:
                if not self.transition_esm(fact_id, state, by=by):
                    return False
            return True
        return self.transition_esm(fact_id, target, by=by)

    def promote_to_validated(self, fact_id: str, by: str = "promote_to_validated") -> bool:
        """Каноническая цепочка Observed → Hypothesized → Supported → Validated."""
        return self.promote_esm_to(fact_id, "Validated", by=by)

    def validate_and_promote(
        self,
        fact_id: str,
        by: str = "truth_gate",
        mode: "Any" = None,
    ) -> "Any":
        """
        SECURITY (I68): единственная канонical-функция для перевода факта в
        'Validated' по запросу внешнего/недоверенного вызывающего (например,
        PATCH /facts/{fact_id}/transition). В отличие от promote_to_validated()/
        promote_esm_to()/transition_esm() — которые используются внутренними
        путями (pipeline.run(), ConsolidationEngine, graduated promotion),
        уже применяющими СОБСТВЕННУЮ pre-vetting policy до вызова — эта функция
        сама прогоняет факт через TruthGate.evaluate() и мутирует состояние
        ТОЛЬКО если вердикт passed.

        Атомарность: если TruthGate отклоняет факт — get_fact()/history/
        snapshot/update_state() не вызываются вообще. Никакой мутации,
        никакой частичной записи в history, никакой audit-записи о
        несостоявшемся переходе.

        Returns:
            TruthGateVerdict. verdict.passed говорит, состоялся ли переход.
            reason == "not_found", если факт не существует (verdict.passed
            всегда False в этом случае — переход не выполняется).

        Не вызывает LLM. Не дублирует TruthGate policy — вся логика внутри
        core.truth_gate.TruthGate; эта функция только оркестрирует
        evaluate() → transition_esm() атомарно.
        """
        from core.truth_gate import CognitiveMode, TruthGate, TruthGateVerdict

        if mode is None:
            mode = CognitiveMode.BALANCED
        elif isinstance(mode, str):
            try:
                mode = CognitiveMode(mode.upper())
            except ValueError:
                mode = CognitiveMode.BALANCED

        # Ring Zero проверяется здесь так же строго, как в transition_esm():
        # по fact_id, до любого чтения/gate — не зависит от того, существует
        # ли факт в БД. Сохраняет 403 (не 404/422) для Ring Zero ID.
        if fact_id in IMMUTABLE_FACT_IDS:
            raise ImmutableStateError(
                f"validate_and_promote: факт '{fact_id}' защищён Ring Zero"
            )

        fact = self.get_fact(fact_id)
        if fact is None:
            return TruthGateVerdict(
                passed=False,
                fact_id=fact_id,
                reason="not_found",
                justification=f"Факт '{fact_id}' не найден.",
                by=by,
                mode=mode,
            )

        current_state = fact.get("epistemic_state", "Observed")
        if current_state == "Validated":
            # Идемпотентность: уже Validated — вердикт passed, без повторной мутации.
            return TruthGateVerdict(
                passed=True,
                fact_id=fact_id,
                reason="already_validated",
                justification="Факт уже в состоянии Validated.",
                by=by,
                mode=mode,
                confidence=float(fact.get("confidence", 0.0) or 0.0),
            )

        verdict = TruthGate(self).evaluate(fact, mode=mode, by=by)
        if verdict.passed:
            # Мутация ТОЛЬКО после успешного вердикта. transition_esm() сам
            # перепроверит ESM-легальность и Ring Zero/ImmutableCore.
            self.transition_esm(fact_id, "Validated", by=by)
        return verdict

    # ── Bi-temporal операции (I96) ──────────────────────────────────────────

    def get_fact_at(
        self,
        fact_id: str,
        known_at: str,
        world_at: str,
    ) -> dict | None:
        """
        Time-travel запрос (V9 §2.1):
        что система знала о fact_id в момент known_at
        для состояния мира world_at.

        Пример:
            fact = store.get_fact_at(
                "my_fact",
                known_at="2026-01-16T00:00:00+00:00",
                world_at="2026-01-15T00:00:00+00:00",
            )
        """
        with self._db() as conn:
            row = conn.execute("""
                SELECT * FROM facts
                WHERE fact_id = ?
                  AND t_ingestion_start  <= ?
                  AND (t_ingestion_end   IS NULL OR t_ingestion_end  > ?)
                  AND t_event_valid_start <= ?
                  AND (t_event_valid_end  IS NULL OR t_event_valid_end > ?)
            """, (fact_id, known_at, known_at, world_at, world_at)).fetchone()
            if row:
                result = dict(row)
                result["metadata"] = json.loads(result["metadata"])
                result["history"]  = json.loads(result.get("history") or "[]")
                return result
        return None

    def invalidate_edge(
        self,
        fact_id: str,
        t_event_valid_end: str | None = None,
        t_ingestion_end: str | None = None,
    ) -> bool:
        """
        Инвалидировать факт без DELETE (принцип V9 §2.1).
        Уже выставленные end-значения не перезаписываются (COALESCE).
        """
        now = _now()
        t_ev_end  = t_event_valid_end or now
        t_ing_end = t_ingestion_end   or now
        fact = self.get_fact(fact_id)
        if fact:
            self._snapshot_before_change(
                fact_id,
                fact,
                caused_by="memory.invalidate_edge",
            )
        with self._db() as conn:
            conn.execute("""
                UPDATE facts
                SET t_event_valid_end = COALESCE(t_event_valid_end, ?),
                    t_ingestion_end   = COALESCE(t_ingestion_end,   ?),
                    updated_at        = ?
                WHERE fact_id = ?
            """, (t_ev_end, t_ing_end, now, fact_id))
        # Синхронизировать L0-кэш
        cached = self._l0_get(fact_id)
        if cached is not None:
            if not cached.get("t_event_valid_end"):
                cached["t_event_valid_end"] = t_ev_end
            if not cached.get("t_ingestion_end"):
                cached["t_ingestion_end"] = t_ing_end
            cached["updated_at"] = now
            self._l0_put(fact_id, cached)
        return True

    def search(
        self,
        query: str,
        mode: str = "bm25",
        limit: int = 10,
        epistemic_state: str | None = None,
    ) -> list[dict]:
        """
        Поиск фактов по тексту.

        V8.8 FIX: FTS5 полнотекстовый поиск вместо O(N) LIKE-скана.
        При недоступности FTS5 — fallback на старый LIKE (legacy-БД без FTS5).
        """
        terms = query.lower().split()
        if not terms:
            return []

        # FTS5 быстрый путь
        try:
            return self._search_fts5(query, limit, epistemic_state)
        except Exception:
            pass

        # Legacy LIKE fallback (для БД без FTS5 виртуальной таблицы)
        return self._search_like(terms, limit, epistemic_state)

    def _search_fts5(
        self,
        query: str,
        limit: int = 10,
        epistemic_state: str | None = None,
    ) -> list[dict]:
        """FTS5 полнотекстовый поиск — O(log N)."""
        # Экранировать специальные символы FTS5
        safe = "".join(c for c in query if c.isalnum() or c.isspace() or c == '"')
        if not safe.strip():
            return []

        state_filter = ""
        params: list[Any] = []
        if epistemic_state:
            state_filter = "AND f.epistemic_state = ?"
            params.append(epistemic_state)

        results = []
        with self._db() as conn:
            rows = conn.execute(
                f"""SELECT f.*, rank
                    FROM facts f
                    JOIN facts_fts ft ON f.fact_id = ft.fact_id
                    WHERE facts_fts MATCH ? {state_filter}
                    ORDER BY rank
                    LIMIT ?""",
                (safe, *params, limit),
            ).fetchall()
            for row in rows:
                r = dict(row)
                rank_val = r.pop("rank", None)
                r["metadata"] = json.loads(r["metadata"])
                r["history"] = json.loads(r.get("history") or "[]")
                r["_search_score"] = 1.0 / (1.0 + (rank_val or 0) * 0.01)
                results.append(r)
        return results

    def _search_like(
        self,
        terms: list[str],
        limit: int = 10,
        epistemic_state: str | None = None,
    ) -> list[dict]:
        """Legacy LIKE-скан (fallback для БД без FTS5)."""
        state_filter = ""
        params: list[Any] = []
        if epistemic_state:
            state_filter = "AND epistemic_state = ?"
            params.append(epistemic_state)

        results = []
        with self._db() as conn:
            rows = conn.execute(
                f"SELECT * FROM facts WHERE 1=1 {state_filter}", params
            ).fetchall()
            for row in rows:
                r = dict(row)
                claim_lower = r.get("claim", "").lower()
                score = sum(1 for t in terms if t in claim_lower)
                if score > 0:
                    r["metadata"] = json.loads(r["metadata"])
                    r["history"] = json.loads(r.get("history") or "[]")
                    r["_search_score"] = score
                    results.append(r)

        results.sort(key=lambda x: x["_search_score"], reverse=True)
        return results[:limit]

    # ── store_facts_batch ───────────────────────────────────────────────────

    def store_facts_batch(self, facts: list[dict]) -> dict[str, int]:
        """
        Сохранить список фактов в одной SQLite транзакции.

        ЗАЧЕМ: store_fact() открывает отдельное соединение на каждый факт
        (per-op connection, LIMITATIONS P-4). При N=100 фактах это N коннектов.
        store_facts_batch() делает один коннект и N INSERT в одной транзакции.
        Прирост: ~80% по времени при batch ingestion.

        Семантика идентична store_fact(): новые факты только в Observed (I50),
        drift protection (TASK-02) применяется к каждому факту,
        BUG-FIX v8.3.1 split-brain применяется к каждому факту.

        Returns:
            {"stored": int, "updated": int, "drift": int, "errors": int}
        """
        if not facts:
            return {"stored": 0, "updated": 0, "drift": 0, "errors": 0}

        stats = {"stored": 0, "updated": 0, "drift": 0, "errors": 0}
        records: list[dict] = []
        drift_ids: list[tuple] = []  # (fact_id, epistemic_state, history_json)
        l0_pending: list[tuple] = []  # C2: (fact_id, l0_record) — в L0 ТОЛЬКО после commit L1

        now = _now()

        for fact in facts:
            try:
                fact_id = fact.get("fact_id")
                if not fact_id:
                    raise ValueError("store_facts_batch: fact_id обязателен")

                requested_state = fact.get("epistemic_state", "Observed")
                if requested_state not in ESM_STATES:
                    raise ValueError(f"Недопустимое ESM-состояние '{requested_state}'")

                if requested_state != "Observed":
                    is_ring_zero_seed = (fact_id in IMMUTABLE_FACT_IDS and
                                         requested_state == "Validated")
                    if not is_ring_zero_seed:
                        raise ValueError(
                            f"store_facts_batch: факт '{fact_id}' создаётся только в Observed"
                        )

                confidence = _validate_confidence(fact.get("confidence", 0.5))
                metadata_dict = dict(fact.get("metadata", {}) or {})
                new_claim = fact.get("claim", "")
                # D1 (audit M5): batch-факты обязаны нести claim_dedup_key
                # (store_fact делает это через attach_integrity_metadata), иначе
                # индексированный дедуп их не находит и падает в скан.
                if "claim_dedup_key" not in metadata_dict:
                    from core.fact_integrity import compute_claim_dedup_key as _cdk
                    metadata_dict["claim_dedup_key"] = _cdk(new_claim)

                # v8.7 P0: модальность
                from core.validators import normalize_claim_type, normalize_origin_type
                _raw_ct = fact.get("claim_type")
                _raw_ot = fact.get("origin_type")
                _ct = normalize_claim_type(_raw_ct)
                _ot = normalize_origin_type(_raw_ot)

                record = {
                    "fact_id":             fact_id,
                    "claim":               new_claim,
                    "source":              fact.get("source", "unknown"),
                    "confidence":          confidence,
                    "epistemic_state":     requested_state,
                    "created_at":          now,
                    "updated_at":          now,
                    "metadata":            json.dumps(metadata_dict),
                    "history":             json.dumps([]),
                    "t_event_valid_start": now,
                    "t_event_valid_end":   None,
                    "t_ingestion_start":   now,
                    "t_ingestion_end":     None,
                    "claim_type":          _ct,
                    "origin_type":         _ot,
                    "memory_type":         fact.get("memory_type", "semantic"),
                }

                # Drift protection: проверяем существующие факты через L0
                existing = self.get_fact(fact_id)
                if existing:
                    if (existing["claim"] != new_claim and
                            existing["epistemic_state"] in {"Validated", "Supported"}):
                        allowed = ESM_TRANSITIONS.get(existing["epistemic_state"], set())
                        if "Contradicted" in allowed:
                            record["epistemic_state"] = "Contradicted"
                            history = existing.get("history", [])
                            history.append({
                                "state": "Contradicted",
                                "from":  existing["epistemic_state"],
                                "at":    now,
                                "by":    "store_facts_batch_drift_protection",
                            })
                            record["history"] = json.dumps(history)
                            drift_ids.append((fact_id, "Contradicted", record["history"]))
                            stats["drift"] += 1
                    else:
                        record["epistemic_state"] = existing["epistemic_state"]
                        record["history"] = json.dumps(existing.get("history", []))

                    record["created_at"]         = existing["created_at"]
                    record["t_event_valid_start"] = existing.get("t_event_valid_start", now)
                    record["t_ingestion_start"]   = existing.get("t_ingestion_start", now)
                    record["t_event_valid_end"]   = existing.get("t_event_valid_end")
                    record["t_ingestion_end"]     = existing.get("t_ingestion_end")
                    stats["updated"] += 1
                else:
                    stats["stored"] += 1

                # C2 SPLIT-BRAIN FIX: L0 НЕ пишем здесь — только после commit L1 (ниже).
                l0_record = {**record,
                             "metadata": metadata_dict,
                             "history":  json.loads(record["history"])}
                l0_pending.append((fact_id, l0_record))
                records.append(record)

            except Exception as exc:
                logger.warning("store_facts_batch: пропущен факт '%s': %s",
                               fact.get("fact_id", "?"), exc)
                stats["errors"] += 1

        if not records:
            return stats

        # Один SQLite transaction на весь batch
        with self._db() as conn:
            conn.executemany("""
                INSERT INTO facts
                    (fact_id, claim, source, confidence, epistemic_state,
                     created_at, updated_at, metadata, history,
                     t_event_valid_start, t_event_valid_end,
                     t_ingestion_start,   t_ingestion_end,
                     claim_type, origin_type, memory_type)
                VALUES
                    (:fact_id, :claim, :source, :confidence, :epistemic_state,
                     :created_at, :updated_at, :metadata, :history,
                     :t_event_valid_start, :t_event_valid_end,
                     :t_ingestion_start,   :t_ingestion_end,
                     :claim_type, :origin_type, :memory_type)
                ON CONFLICT(fact_id) DO UPDATE SET
                    claim      = excluded.claim,
                    source     = excluded.source,
                    confidence = excluded.confidence,
                    updated_at = excluded.updated_at,
                    metadata   = excluded.metadata
            """, records)

            # BUG-FIX v8.3.1 для drift: синхронизируем epistemic_state в L1
            for fact_id, new_state, history_json in drift_ids:
                conn.execute(
                    "UPDATE facts SET epistemic_state = ?, history = ? WHERE fact_id = ?",
                    (new_state, history_json, fact_id),
                )

        # C2 SPLIT-BRAIN FIX (audit): L0 пишем ТОЛЬКО ПОСЛЕ успешного commit L1.
        # Раньше _l0_put шёл в цикле ДО executemany → при откате батча факты
        # оставались в L0, которых нет в L1 (нарушение инварианта D4, как в store_fact).
        for _fid, _l0_record in l0_pending:
            self._l0_put(_fid, _l0_record)

        logger.debug(
            "store_facts_batch: %d фактов | stored=%d updated=%d drift=%d errors=%d",
            len(facts), stats["stored"], stats["updated"], stats["drift"], stats["errors"],
        )
        return stats

    # ── close ───────────────────────────────────────────────────────────────

    def close(self) -> None:
        """Идемпотентное закрытие единственного SQLite-соединения."""
        if self._closed:
            return
        self._closed = True
        with self._db_lock:
            if self._sqlite_conn is not None:
                try:
                    self._sqlite_conn.close()
                except Exception:
                    pass
                self._sqlite_conn = None


# ─── Фабрика для тестовой изоляции ────────────────────────────────────────────
def make_store(db_path: str = SQLITE_PATH, l0_cap: int = L0_CAP) -> SQLiteGraphStore:
    """
    Создать свежий SQLiteGraphStore с заданным путём.
    Используй в тестах вместо _GLOBAL_STORE:

        store = make_store(str(tmp_path / "test.db"))
        monkeypatch.setattr(memory, "_GLOBAL_STORE", store)
        monkeypatch.setattr(memory, "_L0", store._l0)
        monkeypatch.setattr(memory, "_DDL_INITIALIZED", store._ddl_initialized_paths)
    """
    return SQLiteGraphStore(db_path, l0_cap)


# ─── Мост обратной совместимости (для тестов и MVP) ───────────────────────────
# TODO Sprint 2c: полностью перейти на DI, удалить этот блок.
_GLOBAL_STORE = SQLiteGraphStore(SQLITE_PATH)
_L0           = _GLOBAL_STORE._l0
_DDL_INITIALIZED = _GLOBAL_STORE._ddl_initialized_paths


def store_fact(fact: dict) -> bool:
    """Обёртка над SQLiteGraphStore.store_fact(). Возвращает True если новый INSERT."""
    return _GLOBAL_STORE.store_fact(fact)

def store_facts_batch(facts: list[dict]) -> dict[str, int]:
    """Batch insert: один SQLite transaction на N фактов. ~80% быстрее чем N×store_fact()."""
    return _GLOBAL_STORE.store_facts_batch(facts)

def get_fact(fact_id: str) -> dict | None:
    return _GLOBAL_STORE.get_fact(fact_id)


def find_fact_id_by_episode_hash(episode_hash: str) -> str | None:
    return _GLOBAL_STORE.find_fact_id_by_episode_hash(episode_hash)


def find_fact_id_by_claim_dedup(claim: str) -> str | None:
    return _GLOBAL_STORE.find_fact_id_by_claim_dedup(claim)

def transition_esm(fact_id: str, new_state: str, by: str = "transition_esm") -> bool:
    return _GLOBAL_STORE.transition_esm(fact_id, new_state, by)


def promote_to_validated(fact_id: str, by: str = "promote_to_validated") -> bool:
    return _GLOBAL_STORE.promote_to_validated(fact_id, by=by)


def promote_esm_to(fact_id: str, target: str, by: str = "promote_esm") -> bool:
    return _GLOBAL_STORE.promote_esm_to(fact_id, target, by=by)


def validate_and_promote(fact_id: str, by: str = "truth_gate", mode: Any = None) -> Any:
    """Обёртка над SQLiteGraphStore.validate_and_promote() — см. класс для деталей."""
    return _GLOBAL_STORE.validate_and_promote(fact_id, by=by, mode=mode)

def get_all_facts(
    epistemic_state: str | None = None,
    domain: str | None = None,
) -> list[dict]:
    from core.domain_tags import normalize_domain

    dom = normalize_domain(domain) if domain else None
    if dom == "general":
        dom = None
    return _GLOBAL_STORE.get_all_facts(epistemic_state, domain=dom)

def store_raw_text(text: str, source: str | None = None, source_type: str = "user_input") -> str:
    """TASK-09: Сохранить оригинальный текст в L0 Raw Memory. Возвращает raw_id."""
    return _GLOBAL_STORE.store_raw_text(text, source=source, source_type=source_type)

def link_raw_to_fact(raw_id: str, fact_id: str, derivation_type: str = "direct") -> None:
    """TASK-09: Связать derived факт с оригинальным raw_id в провенанс-таблице."""
    _GLOBAL_STORE.link_raw_to_fact(raw_id, fact_id, derivation_type)

def get_raw_text_for_fact(fact_id: str) -> str | None:
    """TASK-09: Оригинальный L0-текст для факта."""
    return _GLOBAL_STORE.get_raw_text_for_fact(fact_id)

def get_fact_ids(limit: int = 10_000, epistemic_state: str | None = None) -> list[str]:
    """TASK-06: Лёгкий запрос — только ID без полного тела фактов."""
    return _GLOBAL_STORE.get_fact_ids(limit=limit, epistemic_state=epistemic_state)

def get_facts_by_ids(fact_ids: list[str]) -> list[dict]:
    """TASK-06: Получить полные факты по списку ID."""
    return _GLOBAL_STORE.get_facts_by_ids(fact_ids)

def get_fact_at(fact_id: str, known_at: str, world_at: str) -> dict | None:
    return _GLOBAL_STORE.get_fact_at(fact_id, known_at, world_at)

def invalidate_edge(
    fact_id: str,
    t_event_valid_end: str | None = None,
    t_ingestion_end: str | None = None,
) -> bool:
    return _GLOBAL_STORE.invalidate_edge(fact_id, t_event_valid_end, t_ingestion_end)


# ─── GDPR Art. 17 erasure (module-level wrappers) ─────────────────────────────
def delete_fact_l1(fact_id: str) -> bool:
    """GDPR Art. 17: physically delete a fact from L0+L1 and dependent rows."""
    return _GLOBAL_STORE.delete_fact_l1(fact_id)


def write_tombstone(fact_id: str, *, reason: str, actor: str,
                    content_hash: str | None) -> None:
    _GLOBAL_STORE.write_tombstone(
        fact_id, reason=reason, actor=actor, content_hash=content_hash)


def get_tombstone(fact_id: str) -> dict | None:
    return _GLOBAL_STORE.get_tombstone(fact_id)


def get_tombstones() -> list[dict]:
    return _GLOBAL_STORE.get_tombstones()


def set_restricted(fact_id: str, restricted: bool) -> bool:
    """GDPR Art. 18: mark/unmark a fact's processing restriction."""
    return _GLOBAL_STORE.set_restricted(fact_id, restricted)
