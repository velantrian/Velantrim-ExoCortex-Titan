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
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from core.write_result import WriteResult

from core.storage import GraphStore
from core.recall_policy import (
    get_facts_for_recall as _get_facts_for_recall,
    list_facts_for_recall as _list_facts_for_recall,
    search_facts_for_recall as _search_facts_for_recall,
)

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
_SQLITE_BUSY_TIMEOUT_DEFAULT_MS = 30_000
_SQLITE_BUSY_TIMEOUT_MAX_MS = 120_000


def _sqlite_busy_timeout_ms() -> int:
    """Resolve one bounded SQLite lock-wait budget per store instance.

    Invalid/operator-hostile values retain the historical 30-second
    default. The returned integer is safe for both sqlite3.connect() and
    PRAGMA busy_timeout interpolation.
    """
    raw = os.getenv(
        "VELANTRIM_SQLITE_BUSY_TIMEOUT_MS",
        str(_SQLITE_BUSY_TIMEOUT_DEFAULT_MS),
    )
    try:
        value = int(raw.strip())
    except (AttributeError, ValueError):
        return _SQLITE_BUSY_TIMEOUT_DEFAULT_MS
    if not 1 <= value <= _SQLITE_BUSY_TIMEOUT_MAX_MS:
        return _SQLITE_BUSY_TIMEOUT_DEFAULT_MS
    return value


# GDPR Art. 17 batch erasure (core.erasure_batch_coordinator): the single
# source of truth for "which facts belong to user_id", shared by
# SQLiteGraphStore.list_fact_ids_by_user_durable() (used for dry-run
# previews) and BatchErasureCoordinator._create_batch_snapshot() (which runs
# this SAME text directly on its own connection, inside the same
# transaction as the batch/item INSERTs it snapshots for, so the read and
# the write are genuinely atomic — see there for why a separate connection
# for the SELECT would NOT be atomic).
FACTS_BY_USER_FILTER_SQL = (
    "SELECT fact_id, epistemic_state FROM facts "
    "WHERE source = ? OR json_extract(metadata, '$.user_id') = ? "
    "ORDER BY fact_id"
)

# Same-DB tables erase_fact_dependents_atomic() purges for a fact_id,
# shared with same_db_dependents_present() (a read-only residual check —
# see core/erasure_coordinator.py's _residual_data_present()) so the two
# can never drift apart: whatever this saga's l1_same_db step deletes is
# exactly what the residual check looks for. `where_sql`'s `?` count
# determines how many times fact_id is repeated in its params tuple (2 for
# `relations`, which matches on either direction of the edge; 1 for
# everything else).
#
# `projection_outbox` (migration 020, issue #183): `aggregate_type` is
# always the literal 'fact' (the only value the table's own CHECK
# constraint permits today), so it is written directly rather than as a
# second `?` — only `aggregate_id` is bound to fact_id. No Canon caller
# writes rows here yet; this entry exists so that WHEN one does, the
# already-atomic l1_same_db deletion and residual check cover it with no
# separate wiring. A pre-migration-020 database simply lacks this table
# (same "not applicable" handling as every other entry here) — see
# _table_exists()'s caller in same_db_dependents_present() for the one
# exception: a database whose PRAGMA user_version already claims
# migration 020 (>= 20) but is missing the table anyway is a corruption
# shape, not a legitimately older database, and fails closed instead.
#
# `projection_checkpoints` (migration 021, issue #194): same
# `aggregate_type = 'fact' AND aggregate_id = ?` shape as `projection_outbox`
# — a version-monotonic same-DB checkpoint of what canonical_version a
# local projection (policy v1: FTS only) has actually been derived from.
# Registering it here means erasure removes it atomically alongside every
# other same-DB dependent, and a surviving/reappeared checkpoint for an
# already-erased fact is detected as residual by the exact same
# `same_db_dependents_present()` check, with no separate wiring.
_SAME_DB_DEPENDENT_TABLES: tuple[tuple[str, str], ...] = (
    ("relations", "from_fact_id = ? OR to_fact_id = ?"),
    ("l0_fact_provenance", "fact_id = ?"),
    ("fact_living_context", "fact_id = ?"),
    ("fact_affordances", "fact_id = ?"),
    ("fact_affordance_tokens", "fact_id = ?"),
    ("fact_mentions", "fact_id = ?"),
    ("fact_versions", "fact_id = ?"),
    ("raw_derivation_chain", "derived_fact_id = ?"),
    ("facts_fts", "fact_id = ?"),
    ("projection_outbox", "aggregate_type = 'fact' AND aggregate_id = ?"),
    ("projection_checkpoints", "aggregate_type = 'fact' AND aggregate_id = ?"),
)

# Schema version at which scripts/apply_migrations.py records migration
# 020 (projection_outbox) as applied (PRAGMA user_version). Used by
# same_db_dependents_present()'s fail-closed check and by
# _promote_to_validated_cas()'s own activation gating (issue #191) — never
# by erase_fact_dependents_atomic()/_purge(), which reports table absence
# the same honest "not applicable" way for every entry regardless of why
# a table is missing.
_PROJECTION_OUTBOX_MIGRATION_VERSION: Final = 20


class ImmutableStateError(Exception):
    pass


class TriggerReconstructionError(RuntimeError):
    """Raised when the `prevent_fact_delete` safety guard is missing after a
    failed erasure transaction AND the emergency in-place reconstruction of
    the canonical trigger also failed. Distinct from the original DELETE
    error it is chained from (`raise ... from original_exc`) — the two must
    never be conflated, since this one means the anti-accidental-deletion
    guard is verifiably absent from the database, not just that one erasure
    attempt failed."""


class ProjectionOutboxActivationError(RuntimeError):
    """Raised by _promote_to_validated_cas() (issue #191) when a promotion
    cannot safely append its required projection-outbox intent on a
    database whose own migration bookkeeping (PRAGMA user_version >= 20)
    claims migration 020 is applied — `projection_outbox` or
    `facts.fact_version` unexpectedly missing is a schema-inconsistency,
    never a legitimately older/unmigrated database (see
    _PROJECTION_OUTBOX_MIGRATION_VERSION). Raising here, inside the same
    transaction as the Canon CAS UPDATE/VersionStore/AuditChain, rolls all
    of it back via _db()'s own exception handling — a promotion is never
    committed without the intent an activated outbox requires."""


@dataclass
class SupersedeCasResult:
    """Результат SQLiteGraphStore.supersede_fact_cas() — см. класс для деталей.

    committed=False всегда означает: ничего не изменилось в facts (ни новый
    факт, ни старый) — reason объясняет почему ("concurrent_modification"
    или "new_id_collision"). committed=True — оба факта закоммичены атомарно,
    new_record/old_record несут финальные (Validated/Deprecated) снимки.
    """
    committed:  bool
    reason:     str
    new_record: dict[str, Any] | None = None
    old_record: dict[str, Any] | None = None


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


def facts_table_has_fact_version(conn: sqlite3.Connection) -> bool:
    """PR-C1b (Issue #37): whether this connection's `facts` table has the
    `fact_version` column (migrations/009_truth_kernel.sql). Any UPDATE on
    `facts` that changes claim/confidence/epistemic_state must bump this
    column or the `bump_fact_version` trigger raises. Shared by
    SQLiteGraphStore._fact_version_bump_sql() and any other code path that
    writes to `facts` directly outside that class (core.forgetting PII
    redaction) — one PRAGMA check, not a duplicated ad-hoc one per caller."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(facts)").fetchall()}
    return "fact_version" in cols


# Round 5.3 Codex finding (P2): every reader of erasure_log must resolve
# the SAME correction-aware effective subject the erasure_audit VIEW
# resolves (migration 016) — a raw `SELECT ... FROM erasure_log` bypasses
# any correction recorded in erasure_log_subject_corrections and reports
# the original operator/credential fingerprint instead of the real data
# subject. This is the single shared query fragment behind
# SQLiteGraphStore.get_tombstone()/get_tombstone_for_job()/get_tombstones()
# — kept in one place so the COALESCE logic can never drift from the view's.
_EFFECTIVE_TOMBSTONE_SELECT_SQL = """
    SELECT el.erasure_id, el.fact_id,
           COALESCE(c.corrected_user_id, el.user_id) AS user_id,
           el.reason, el.claim_hash, el.erased_at, el.job_id
    FROM erasure_log el
    LEFT JOIN erasure_log_subject_corrections c ON c.erasure_id = el.erasure_id
"""


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


def _safe_add_column_if_missing(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    *,
    sql_type: str,
    not_null: bool,
    default_literal: str,
) -> None:
    """Cross-connection-safe lazy column upgrade (issue #184).

    The caller's own ``PRAGMA table_info(table)`` absence-check (taken
    before this call) is a snapshot that can be stale by the time this
    specific ``ALTER TABLE`` actually runs: a different, independent
    ``SQLiteGraphStore`` instance/connection can have added the exact same
    column in the gap, since the per-instance ``_ddl_initialized_paths``
    guard does not synchronize across connections. Rather than trusting
    that snapshot alone, this always attempts the real ``ALTER TABLE``
    and treats ONLY an exact ``duplicate column name: {column}`` failure
    for THIS column as a benign race — never any other
    ``sqlite3.OperationalError`` (malformed schema, I/O, capacity,
    permission, corruption, a duplicate reported for a different column,
    or any other failure), which all still propagate uncaught.

    A benign race is verified, never assumed: the authoritative current
    ``PRAGMA table_info(table)`` must show a column of this exact name
    with the exact declared type, ``NOT NULL`` contract and default this
    call itself would have created, or the bootstrap fails closed with a
    ``RuntimeError`` instead of silently accepting an incompatible
    pre-existing column.
    """
    clauses = [sql_type]
    if not_null:
        clauses.append("NOT NULL")
    clauses.append(f"DEFAULT {default_literal}")
    try:
        conn.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {' '.join(clauses)}"
        )
        return
    except sqlite3.OperationalError as exc:
        if str(exc) != f"duplicate column name: {column}":
            raise

    row = next(
        (
            r for r in conn.execute(f"PRAGMA table_info({table})").fetchall()
            if r[1] == column
        ),
        None,
    )
    if row is None:
        raise RuntimeError(
            f"{table}.{column}: ALTER TABLE reported a duplicate column "
            "name, but PRAGMA table_info no longer shows that column — "
            "the schema is inconsistent; refusing to proceed."
        )
    _cid, _name, decl_type, notnull, dflt_value, pk = row
    expected_notnull = 1 if not_null else 0
    if (
        decl_type != sql_type
        or notnull != expected_notnull
        or dflt_value != default_literal
        or pk != 0
    ):
        raise RuntimeError(
            f"{table}.{column}: benign-duplicate recovery rejected — a "
            f"pre-existing column has an incompatible definition. Expected "
            f"type={sql_type!r} not_null={not_null} default={default_literal!r}; "
            f"found type={decl_type!r} notnull={notnull} "
            f"default={dflt_value!r} pk={pk}."
        )


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
        self._busy_timeout_ms = _sqlite_busy_timeout_ms()
        # Одно WAL-соединение + RLock: исключает deadlock пула из 3 conn.
        self._sqlite_conn: sqlite3.Connection | None = None
        self._db_lock = threading.RLock()

    def ensure_schema(self) -> None:
        """Deterministically trigger the canonical DDL initialization for
        `self.db_path` (facts/l0_raw_memory/l0_fact_provenance/erasure_log/
        etc. — see `_db()`) without performing any read or write of actual
        data.

        `_db()` already does this lazily, guarded by
        `self._ddl_initialized_paths`, on first use by any real operation —
        this method exists for callers (e.g.
        core.forgetting.ForgettingEngine.forget_all()) that must guarantee
        the schema exists BEFORE handing this store's `db_path` to a
        DIFFERENT component that queries it via its own raw connection
        (core.erasure_batch_coordinator.BatchErasureCoordinator's
        `_create_batch_snapshot()`), where the lazy trigger would otherwise
        never fire. A genuinely corrupt/unreadable database file still
        raises its real sqlite3 error here — never silently swallowed or
        treated as "no data yet".
        """
        with self._db():
            pass

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
                    self.db_path,
                    timeout=self._busy_timeout_ms / 1000.0,
                    check_same_thread=False,
                )
                conn.row_factory = sqlite3.Row
                self._sqlite_conn = conn
            else:
                try:
                    conn.execute("SELECT 1")
                except sqlite3.ProgrammingError:
                    conn = sqlite3.connect(
                        self.db_path,
                    timeout=self._busy_timeout_ms / 1000.0,
                    check_same_thread=False,
                    )
                    conn.row_factory = sqlite3.Row
                    self._sqlite_conn = conn

            conn.execute(f"PRAGMA busy_timeout = {self._busy_timeout_ms}")
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
                            "t_ingestion_start", "t_ingestion_end",
                            "audit_subject_id"):
                    if col not in existing_cols:
                        _safe_add_column_if_missing(
                            conn, "facts", col,
                            sql_type="TEXT", not_null=False, default_literal="NULL",
                        )
                # v8.7 P0: modality fields — safe migration for existing databases
                if "claim_type" not in existing_cols:
                    _safe_add_column_if_missing(
                        conn, "facts", "claim_type",
                        sql_type="TEXT", not_null=True, default_literal="'UNKNOWN'",
                    )
                if "origin_type" not in existing_cols:
                    _safe_add_column_if_missing(
                        conn, "facts", "origin_type",
                        sql_type="TEXT", not_null=True, default_literal="'UNKNOWN'",
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
                        request_ref  TEXT DEFAULT NULL,
                        job_id       TEXT DEFAULT NULL
                    )
                """)
                _upgrade_erasure_log_schema(conn)
                # Post-review hotfix (migration 014): job_id scopes
                # write_tombstone()'s idempotency check to a specific
                # erasure_jobs generation instead of "any tombstone ever
                # recorded for this fact_id" — a fact_id that gets
                # recreated and durably re-erased needs its OWN new
                # tombstone row, not a silent no-op because an earlier
                # generation already has one. NULL for legacy rows written
                # before this column existed.
                erasure_log_cols = {
                    r[1] for r in conn.execute("PRAGMA table_info(erasure_log)").fetchall()
                }
                if "job_id" not in erasure_log_cols:
                    _safe_add_column_if_missing(
                        conn, "erasure_log", "job_id",
                        sql_type="TEXT", not_null=False, default_literal="NULL",
                    )
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_erasure_user
                    ON erasure_log(user_id, erased_at)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_erasure_fact
                    ON erasure_log(fact_id)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_erasure_job
                    ON erasure_log(job_id)
                """)
                # Post-review hotfix (round 2): the fact_id/job_id
                # check-then-insert in write_tombstone() below is a
                # necessary but not sufficient guard — two concurrent
                # callers finalizing the SAME job_id (e.g. a live
                # erase_fact_durable() racing resume_incomplete_jobs()'s
                # crash-recovery sweep for the same job) can both pass the
                # SELECT check before either commits its INSERT. A real
                # DB-level constraint is the actual source of truth: at
                # most one tombstone row may ever exist for a given
                # non-NULL job_id. NULL is excluded (SQLite treats NULL as
                # distinct from every other NULL in a UNIQUE index) so
                # legacy job_id=NULL rows are unaffected and can still
                # accumulate per the old fact_id-wide semantics.
                conn.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_job_unique
                    ON erasure_log(job_id)
                    WHERE job_id IS NOT NULL
                """)
                # Round 5.3 Codex finding (P2): a virgin/tenant DB initialized
                # ONLY through this runtime DDL path (no migrations/*.sql ever
                # applied) must expose the SAME durable-erasure audit surface
                # as a fully-migrated DB — append-only guards, the correction
                # table, and the correction-aware erasure_audit VIEW — not
                # just the bare erasure_log table. Mirrors migrations 012 and
                # 016 verbatim; kept idempotent (IF NOT EXISTS / DROP+CREATE)
                # for defense-in-depth even though _ddl_initialized_paths
                # already makes this whole block run once per db_path.
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS prevent_erasure_delete
                    BEFORE DELETE ON erasure_log
                    BEGIN
                        SELECT RAISE(ABORT, 'VELANTRIM: erasure_log is append-only. Cannot delete audit records.');
                    END
                """)
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS prevent_erasure_update
                    BEFORE UPDATE ON erasure_log
                    BEGIN
                        SELECT RAISE(ABORT, 'VELANTRIM: erasure_log is append-only. Cannot modify audit records.');
                    END
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS erasure_log_subject_corrections (
                        correction_id      TEXT PRIMARY KEY,
                        erasure_id         TEXT NOT NULL UNIQUE REFERENCES erasure_log(erasure_id),
                        job_id             TEXT,
                        batch_id           TEXT NOT NULL REFERENCES erasure_batches(batch_id),
                        corrected_user_id  TEXT NOT NULL,
                        original_user_id   TEXT NOT NULL,
                        created_at         TEXT NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_erasure_log_subject_corrections_erasure_id
                    ON erasure_log_subject_corrections(erasure_id)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_erasure_log_subject_corrections_user
                    ON erasure_log_subject_corrections(corrected_user_id)
                """)
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS prevent_erasure_log_subject_corrections_delete
                    BEFORE DELETE ON erasure_log_subject_corrections
                    BEGIN
                        SELECT RAISE(ABORT, 'VELANTRIM: erasure_log_subject_corrections is append-only. Cannot delete audit records.');
                    END
                """)
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS prevent_erasure_log_subject_corrections_update
                    BEFORE UPDATE ON erasure_log_subject_corrections
                    BEGIN
                        SELECT RAISE(ABORT, 'VELANTRIM: erasure_log_subject_corrections is append-only. Cannot modify audit records.');
                    END
                """)
                conn.execute("DROP VIEW IF EXISTS erasure_audit")
                conn.execute("""
                    CREATE VIEW IF NOT EXISTS erasure_audit AS
                    SELECT
                        el.erasure_id,
                        el.fact_id,
                        COALESCE(c.corrected_user_id, el.user_id) AS user_id,
                        el.reason,
                        el.claim_hash,
                        el.erased_at,
                        el.request_ref
                    FROM erasure_log el
                    LEFT JOIN erasure_log_subject_corrections c ON c.erasure_id = el.erasure_id
                    ORDER BY el.erased_at DESC
                """)
                # TASK-09: derived_from на facts (указывает на l0_raw_memory.raw_id)
                if "derived_from" not in existing_cols:
                    _safe_add_column_if_missing(
                        conn, "facts", "derived_from",
                        sql_type="TEXT", not_null=False, default_literal="NULL",
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
                        self.db_path,
                    timeout=self._busy_timeout_ms / 1000.0,
                    check_same_thread=False,
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
        """Best-effort lock release under the connection-owner lock.

        ``_db()`` owns ``_sqlite_conn`` under ``_db_lock`` and closes the
        shared handle in its ``finally`` block. Reading ``conn.in_transaction``
        outside that same lock left a check-vs-close race: another thread could
        close the handle after this method copied the reference but before the
        property access, raising ``ProgrammingError`` from cleanup itself.

        A cached handle confirmed closed is already released; clear only that
        exact stale reference. Other SQLite failures remain visible in logs
        rather than being silently converted into success.
        """
        with self._db_lock:
            conn = self._sqlite_conn
            if conn is None:
                return

            try:
                in_transaction = conn.in_transaction
            except sqlite3.ProgrammingError as exc:
                if "closed" in str(exc).lower() and self._sqlite_conn is conn:
                    self._sqlite_conn = None
                    logger.debug(
                        "SQLiteGraphStore: cleared stale closed connection during lock release"
                    )
                    return
                logger.warning(
                    "SQLiteGraphStore: cannot inspect transaction during lock release",
                    exc_info=True,
                )
                return

            if not in_transaction:
                return

            try:
                conn.commit()
            except sqlite3.ProgrammingError as exc:
                if "closed" in str(exc).lower() and self._sqlite_conn is conn:
                    self._sqlite_conn = None
                    logger.debug(
                        "SQLiteGraphStore: cleared connection closed during lock release"
                    )
                    return
                logger.warning(
                    "SQLiteGraphStore: programming error during lock-release commit",
                    exc_info=True,
                )
            except sqlite3.Error:
                logger.warning(
                    "SQLiteGraphStore: SQLite error during lock-release commit",
                    exc_info=True,
                )

    # Canonical text of migrations/009_truth_kernel.sql's `prevent_fact_delete`
    # guard — kept in sync so the erasure coordinator can prove it always
    # restores exactly the production guard, not an approximation of it.
    _PREVENT_FACT_DELETE_TRIGGER_SQL = """
        CREATE TRIGGER IF NOT EXISTS prevent_fact_delete
        BEFORE DELETE ON facts
        BEGIN
            SELECT CASE
                WHEN OLD.epistemic_state NOT IN ('Collapsed', 'Deprecated')
                THEN RAISE(ABORT, 'VELANTRIM: Cannot DELETE facts directly. Transition to Collapsed or Deprecated first.')
            END;
        END;
    """

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?",
            (table,),
        ).fetchone() is not None

    @staticmethod
    def _real_table_exists(conn: sqlite3.Connection, table: str) -> bool:
        """Stricter than _table_exists(): true only for an actual TABLE,
        never a same-named VIEW. _table_exists() intentionally treats
        table/view as interchangeable for its other callers (e.g. the
        erasure_audit VIEW is a legitimate target there); this one is used
        only by _promote_to_validated_cas()'s outbox activation gate
        (issue #191 review hardening), where a VIEW named
        `projection_outbox` would pass the general check yet cannot accept
        a plain INSERT — that must surface as a specific, caught schema
        inconsistency, not a raw 'cannot modify ... because it is a view'
        error from deep inside the append call."""
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone() is not None

    @staticmethod
    def _migration_020_activated(conn: sqlite3.Connection) -> bool:
        """True if `scripts/apply_migrations.py` has recorded migration 020
        (projection_outbox) as applied via `PRAGMA user_version` — used only
        by same_db_dependents_present()'s fail-closed check (see there) to
        distinguish a legitimately older/unmigrated database (user_version
        < 20, table absence expected) from one whose migration bookkeeping
        claims the table should exist. A version read that itself fails is
        treated as activated — fail CLOSED, never toward "not applicable".
        """
        try:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
        except sqlite3.Error:
            return True
        return bool(version >= _PROJECTION_OUTBOX_MIGRATION_VERSION)

    @staticmethod
    def _prevent_fact_delete_trigger_exists(conn: sqlite3.Connection) -> bool:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'trigger' "
            "AND name = 'prevent_fact_delete'",
        ).fetchone() is not None

    def _reconstruct_prevent_fact_delete_or_raise(
        self, conn: sqlite3.Connection, *, original_exc: Exception
    ) -> None:
        """Emergency path: `prevent_fact_delete` is missing after a rolled-back
        erasure transaction (should not happen once callers issue an explicit
        `BEGIN` before `DROP TRIGGER`, but this is the last line of defense
        against any SQLite/driver edge case that could still leave it absent).
        Recreates the canonical guard in its OWN, separate transaction — never
        inside the transaction that just failed. If this also fails, the
        surfaced error is a distinct `TriggerReconstructionError`, chained from
        (never replacing/hiding) the original DELETE failure, so callers can
        never mistake "the DELETE step you asked about failed" for "and also
        the DB-wide deletion guard is gone."
        """
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(self._PREVENT_FACT_DELETE_TRIGGER_SQL)
            conn.commit()
        except Exception as reconstruct_exc:
            try:
                conn.rollback()
            except Exception:  # noqa: BLE001 — best-effort, we're already raising
                pass
            raise TriggerReconstructionError(
                "CRITICAL: prevent_fact_delete guard is missing after a failed "
                "erasure transaction AND emergency reconstruction also failed "
                f"({reconstruct_exc!r}). The database has NO protection against "
                "direct DELETE of non-Collapsed/Deprecated facts until this is "
                f"manually repaired. Original erasure failure: {original_exc!r}."
            ) from original_exc
        if not self._prevent_fact_delete_trigger_exists(conn):
            raise TriggerReconstructionError(
                "CRITICAL: prevent_fact_delete guard is still missing after "
                "emergency reconstruction reported success — sqlite_master "
                "does not show it. Original erasure failure: "
                f"{original_exc!r}."
            ) from original_exc

    def erase_fact_dependents_atomic(self, fact_id: str) -> dict[str, Any]:
        """Physically delete `fact_id` and every dependent row in THIS SQLite
        file (relations both directions, living context, affordances, L0
        provenance links, mentions, bi-temporal fact_versions, FTS index),
        as ONE explicit, atomic transaction, with an honest per-table result.

        Unlike a bare try/except-pass sweep, table absence ("applicable":
        False — an older DB without that migration applied) and a real
        delete failure are never conflated: a missing table is fine, but a
        present table whose DELETE raises aborts the whole transaction —
        the erasure coordinator must never report a clean sweep it cannot
        prove.

        `prevent_fact_delete` (migration 009) lifecycle — the mechanism, not
        an assumption: Python's `sqlite3` module does NOT implicitly open a
        transaction before a DDL statement (`CREATE`/`DROP TRIGGER`), so a
        bare `conn.execute("DROP TRIGGER ...")` as the first statement would
        autocommit standalone, outside any transaction `conn.rollback()`
        could later undo — "SQLite DDL is transactional" is true at the
        engine level but does NOT protect a lone auto-committed statement
        from an earlier version of this method. This method therefore opens
        an EXPLICIT `BEGIN IMMEDIATE` before `DROP TRIGGER`, so the drop, every
        dependent-table delete, the `facts` delete, and the trigger's
        recreation are all genuinely one transaction:

          - On any exception: `conn.rollback()`, then verify via
            `sqlite_master` that `prevent_fact_delete` exists again. It
            should, since it was dropped inside the same now-rolled-back
            transaction — but if it is somehow still missing, an emergency
            reconstruction runs in its own separate transaction. If THAT also
            fails, a distinct `TriggerReconstructionError` is raised (chained
            from, never replacing, the original error) rather than letting
            the DELETE failure imply a false "and the guard is fine" — this
            method never returns or lets an exception escape while the
            trigger's presence is unproven.
          - On success: `conn.commit()`, then the same `sqlite_master` check
            runs again — this method does not return a result implying
            success unless `prevent_fact_delete`'s presence is verified,
            not merely assumed from having executed a `CREATE TRIGGER`
            statement.

        Returns {"fact_present_before": bool, "tables": {table: {"applicable":
        bool, "deleted": int}}}. Ring Zero / VALUES_CORE are protected (I6) →
        ImmutableStateError. The append-only L0 raw store (l0_raw_memory) is
        intentionally NOT touched (anti-drift trigger); see core/erasure.py
        for the GDPR note on raw originals.
        """
        if fact_id in IMMUTABLE_FACT_IDS:
            raise ImmutableStateError(
                f"erase_fact_dependents_atomic: '{fact_id}' is Ring Zero (I6) — deletion forbidden"
            )
        self._release_stray_locks()
        tables: dict[str, dict[str, Any]] = {}
        with self._db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute("DROP TRIGGER IF EXISTS prevent_fact_delete")

                present = conn.execute(
                    "SELECT 1 FROM facts WHERE fact_id = ?", (fact_id,)
                ).fetchone() is not None

                def _purge(table: str, where_sql: str, params: tuple) -> None:
                    if not self._table_exists(conn, table):
                        tables[table] = {"applicable": False, "deleted": 0}
                        return
                    cur = conn.execute(f"DELETE FROM {table} WHERE {where_sql}", params)  # noqa: S608
                    tables[table] = {"applicable": True, "deleted": cur.rowcount}

                # FK ON DELETE CASCADE is not relied upon — PRAGMA foreign_keys is
                # OFF on the runtime connection, so every dependent is removed
                # explicitly. Table list is shared with
                # same_db_dependents_present() — see _SAME_DB_DEPENDENT_TABLES.
                for _tbl, _where in _SAME_DB_DEPENDENT_TABLES:
                    _purge(_tbl, _where, (fact_id,) * _where.count("?"))

                cur = conn.execute("DELETE FROM facts WHERE fact_id = ?", (fact_id,))
                tables["facts"] = {"applicable": True, "deleted": cur.rowcount}

                conn.execute(self._PREVENT_FACT_DELETE_TRIGGER_SQL)
            except Exception as exc:  # noqa: BLE001 — must inspect, then re-raise
                conn.rollback()
                if not self._prevent_fact_delete_trigger_exists(conn):
                    self._reconstruct_prevent_fact_delete_or_raise(conn, original_exc=exc)
                raise
            else:
                conn.commit()
                if not self._prevent_fact_delete_trigger_exists(conn):
                    raise TriggerReconstructionError(
                        "CRITICAL: erase_fact_dependents_atomic committed "
                        f"successfully for '{fact_id}' but prevent_fact_delete "
                        "is not present in sqlite_master afterward — refusing "
                        "to report a result while the deletion guard's "
                        "presence is unproven."
                    )
        self._l0_del(fact_id)
        return {"fact_present_before": present, "tables": tables}

    def same_db_dependents_present(self, fact_id: str) -> bool:
        """Read-only residual check (Codex review finding, P1): True if any
        same-DB dependent table erase_fact_dependents_atomic() would purge
        still holds a row for `fact_id` — even if the `facts` row itself is
        already gone (e.g. a legacy/out-of-band deletion that never went
        through the atomic erasure path, exactly the P1-A tombstone shape).

        Used by core.erasure_coordinator._residual_data_present(): without
        this check, a fact_id whose `facts` row is gone but whose
        `relations`/`fact_mentions`/provenance/etc. rows survived, with no
        embeddings/ngram residual either, would make
        _residual_data_present() return False — causing erase_fact_durable()
        to report NOT_FOUND without ever creating a job, so l1_same_db never
        runs and the orphaned dependent rows are never cleaned.

        An optional table that doesn't exist in this DB (an older install
        missing a later migration) is simply not applicable — never treated
        as "residual present". Any DB-level error checking a table that DOES
        exist fails CLOSED (returns True, "residual might be present") —
        the same "can't verify absence is not verified absence" principle
        already applied throughout this saga's tri-state checks.

        `projection_outbox` (issue #183) gets one narrow exception to the
        plain "missing table = not applicable" rule above: if this
        database's own `PRAGMA user_version` already claims migration 020
        is applied (>= 20), the table is not merely from-an-older-install
        absent — its disappearance is a corruption/tampering shape, and a
        completion tombstone must never be trusted while that is unproven.
        That case also fails CLOSED (True), never silently treated as "no
        residual".
        """
        with self._db() as conn:
            for table, where_sql in _SAME_DB_DEPENDENT_TABLES:
                if not self._table_exists(conn, table):
                    if (
                        table == "projection_outbox"
                        and self._migration_020_activated(conn)
                    ):
                        return True
                    continue
                try:
                    params = (fact_id,) * where_sql.count("?")
                    row = conn.execute(
                        f"SELECT 1 FROM {table} WHERE {where_sql} LIMIT 1",  # noqa: S608
                        params,
                    ).fetchone()
                except sqlite3.Error:
                    return True
                if row is not None:
                    return True
        return False

    def list_fact_ids_by_user_durable(self, user_id: str) -> list[dict[str, Any]]:
        """Read-only, durable (bypasses L0/caches) selection of every fact
        currently matching a GDPR data-subject filter: `source = user_id`
        OR `metadata.user_id = user_id` — the same structural match
        core.forgetting.ForgettingEngine.forget_all() has always used, kept
        here as a real DB read rather than a substring LIKE (which would
        match far too broadly, e.g. user_id='default' matching every fact
        whose source merely CONTAINS the word).

        Used by core.erasure_batch_coordinator for `dry_run` previews only
        (a read with no follow-up write, so this connection is fine there).
        The durable batch SNAPSHOT itself does NOT use this method — it runs
        `FACTS_BY_USER_FILTER_SQL` directly on its OWN jobs-DB connection, in
        the SAME transaction as the batch/item INSERTs, so the read and the
        write are genuinely atomic (see
        BatchErasureCoordinator._create_batch_snapshot()). This module-level
        constant is the single source of truth for that filter clause so
        both call sites can never drift apart.

        Returns `[{"fact_id": ..., "epistemic_state": ...}, ...]`, ordered
        by fact_id for a deterministic snapshot ordering.
        """
        with self._db() as conn:
            rows = conn.execute(FACTS_BY_USER_FILTER_SQL, (user_id, user_id)).fetchall()
        return [{"fact_id": r[0], "epistemic_state": r[1]} for r in rows]

    def delete_fact_l1(self, fact_id: str) -> bool:
        """Legacy bool-returning wrapper.

        See erase_fact_dependents_atomic() for the erasure coordinator's
        honest, per-table, error-propagating result — this method exists
        only for callers that predate it and just need the old bool
        contract (True if a `facts` row was removed).
        """
        return self.erase_fact_dependents_atomic(fact_id)["fact_present_before"]

    def write_tombstone(
        self, fact_id: str, *, reason: str, actor: str,
        content_hash: str | None, job_id: str | None = None,
    ) -> None:
        """Record a content-free erasure tombstone (GDPR Art. 30).

        Idempotency is scoped to `job_id` when the caller provides one (the
        erasure coordinator always does, since migration 014 / post-review
        hotfix): only a tombstone already recorded for THIS specific
        durable job/generation is treated as "already written". A fact_id
        that was durably erased, later recreated, and durably re-erased
        under a NEW generation's job_id gets its OWN new tombstone row —
        the old idempotency check ("any tombstone ever for this fact_id")
        would have silently skipped it, leaving Art. 30's audit trail
        wrongly frozen on the first generation. `job_id=None` (legacy
        callers) preserves the original fact_id-wide idempotency.
        """
        import uuid
        self._release_stray_locks()
        claim_hash = content_hash or ""
        with self._db() as conn:
            if job_id is not None:
                exists = conn.execute(
                    "SELECT 1 FROM erasure_log WHERE fact_id = ? AND job_id = ? LIMIT 1",
                    (fact_id, job_id),
                ).fetchone()
            else:
                exists = conn.execute(
                    "SELECT 1 FROM erasure_log WHERE fact_id = ? LIMIT 1", (fact_id,)
                ).fetchone()
            if exists:
                return
            try:
                conn.execute(
                    "INSERT INTO erasure_log "
                    "(erasure_id, fact_id, user_id, reason, claim_hash, erased_at, job_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"era_{uuid.uuid4().hex[:12]}",
                        fact_id,
                        actor,
                        reason,
                        claim_hash,
                        _now(),
                        job_id,
                    ),
                )
            except sqlite3.IntegrityError:
                # Lost a race against a concurrent write_tombstone() call for
                # the SAME job_id (e.g. a live erase_fact_durable() and a
                # crash-recovery resume_incomplete_jobs() sweep finalizing
                # the same job at once): the SELECT-then-INSERT check above
                # is not atomic across connections, but
                # idx_erasure_job_unique (a real DB constraint) guarantees
                # at most one row for this job_id ever commits. The winner's
                # row IS the proven receipt — swallow this exception rather
                # than let it surface as an unhandled write_tombstone()
                # failure; callers read the result back via
                # get_tombstone_for_job(), so both racers converge on the
                # identical row regardless of which one's INSERT won.
                if job_id is None:
                    raise
                conn.rollback()

    def get_tombstone(self, fact_id: str) -> dict | None:
        """Latest tombstone for `fact_id`, regardless of which job/generation
        wrote it — for legacy/public history callers only (e.g. reporting
        "has this fact_id EVER been erased, in any generation"). Never use
        this to corroborate a SPECIFIC job's COMPLETE outcome: with
        generation-aware erasure_jobs (migration 014), a fact_id can have
        multiple jobs/tombstones over time, and this method has no way to
        tell you which one belongs to which job. Use get_tombstone_for_job()
        for that.

        Round 5.3 (Codex P2): `user_id` here is the EFFECTIVE, correction-
        aware subject — the same value erasure_audit/get_erasure_log()
        would report for this row — never the raw erasure_log.user_id,
        so every reader of a tombstone's subject agrees."""
        with self._db() as conn:
            row = conn.execute(
                _EFFECTIVE_TOMBSTONE_SELECT_SQL
                + "WHERE el.fact_id = ? ORDER BY el.erased_at DESC LIMIT 1",
                (fact_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_tombstone(row)

    def get_tombstone_for_job(self, fact_id: str, job_id: str | None) -> dict | None:
        """The tombstone written for THIS SPECIFIC job/generation, or None if
        no such tombstone exists — never another generation's tombstone for
        the same fact_id. `job_id=None` looks up a legacy tombstone (written
        with no job_id at all, e.g. by the deprecated core.erasure shim, or
        by a durable job that completed before migration 014 introduced
        job-scoped tombstones).

        Round 5.3 (Codex P2): `user_id` here is the EFFECTIVE, correction-
        aware subject (see get_tombstone()) — callers that need to know
        WHOSE data a specific job's tombstone actually corroborates (e.g.
        ErasureCoordinator._bind_subject_user_id()'s already-tombstoned-job
        check) get the corrected answer, not the raw operator fingerprint."""
        with self._db() as conn:
            if job_id is not None:
                row = conn.execute(
                    _EFFECTIVE_TOMBSTONE_SELECT_SQL
                    + "WHERE el.fact_id = ? AND el.job_id = ? "
                    "ORDER BY el.erased_at DESC LIMIT 1",
                    (fact_id, job_id),
                ).fetchone()
            else:
                row = conn.execute(
                    _EFFECTIVE_TOMBSTONE_SELECT_SQL
                    + "WHERE el.fact_id = ? AND el.job_id IS NULL "
                    "ORDER BY el.erased_at DESC LIMIT 1",
                    (fact_id,),
                ).fetchone()
        if row is None:
            return None
        return self._row_to_tombstone(row)

    def get_tombstones(self) -> list[dict]:
        """Every tombstone ever recorded, oldest first. Round 5.3 (Codex
        P2): `user_id` is the EFFECTIVE, correction-aware subject (see
        get_tombstone()) — this is the reader behind both
        ErasureCoordinator.erasure_log() and core.compliance.
        record_of_processing()'s Art. 30 report, so both must (and now do)
        agree with erasure_audit/get_erasure_log() on who each erasure
        actually belonged to."""
        with self._db() as conn:
            rows = conn.execute(
                _EFFECTIVE_TOMBSTONE_SELECT_SQL + "ORDER BY el.erased_at"
            ).fetchall()
        return [self._row_to_tombstone(r) for r in rows]

    def count_null_job_tombstones(self, fact_id: str) -> int:
        """Round 5.4 (Codex P2): how many legacy (job_id IS NULL) tombstones
        exist for `fact_id` — used by ErasureCoordinator to decide whether
        the narrow pre-014 NULL-job fallback lookup is safe to trust. Two
        or more is a genuine ambiguity (multiple historical erasures of the
        same fact_id, predating job-scoped tombstones) that must never be
        silently resolved by picking "the latest one" — the caller fails
        closed instead."""
        with self._db() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM erasure_log WHERE fact_id = ? AND job_id IS NULL",
                (fact_id,),
            ).fetchone()
        return row[0] if row else 0

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
            "job_id": row[6],
        }

    def set_restricted(self, fact_id: str, restricted: bool) -> bool:
        """Mark/unmark a fact's processing restriction (GDPR Art. 18).

        The flag lives in the fact's metadata (`restricted` = ISO timestamp).
        A restricted fact stays stored but is excluded from recall
        (get_facts_by_ids).

        Issue #50: restriction is a meaningful canonical mutation, not a
        metadata shortcut. The CAS-guarded facts UPDATE, VersionStore
        pre-image, and structured AuditChain event share one transaction.
        Repeating the already-applied state is an idempotent no-op and emits
        no false version/audit evidence.

        Returns True when the requested state exists after this call, False
        when the fact is absent or changed concurrently to a different state.
        """
        from core.write_gate import ensure_writes_allowed

        ensure_writes_allowed()
        self._release_stray_locks()

        durable = self._get_fact_durable(fact_id)
        if durable is None:
            self._l0_del(fact_id)
            return False

        old_meta = dict(durable.get("metadata") or {})
        currently_restricted = bool(old_meta.get("restricted"))
        if currently_restricted == restricted:
            self._l0_put(fact_id, durable)
            return True

        now = _now()
        new_meta = dict(old_meta)
        if restricted:
            new_meta["restricted"] = now
        else:
            new_meta.pop("restricted", None)

        import uuid as _uuid

        from core.audit_chain import (
            ACTOR_CODE_SET_RESTRICTED,
            REASON_CODE_CAS_GUARDED_WRITE,
            AuditChain,
            EventType,
        )

        audit_subject_id = durable.get("audit_subject_id") or _uuid.uuid4().hex
        chain_id = f"fact-transition:{audit_subject_id}"
        with self._db() as ready_conn:
            AuditChain.verify_schema_ready(ready_conn, chain_id=chain_id)

        cas_miss = False
        with self._db() as conn:
            cur = conn.execute(
                "UPDATE facts SET metadata = ?, updated_at = ?, "
                "audit_subject_id = COALESCE(audit_subject_id, ?) "
                "WHERE fact_id = ? AND updated_at = ?",
                (
                    json.dumps(new_meta),
                    now,
                    audit_subject_id,
                    fact_id,
                    durable["updated_at"],
                ),
            )
            if cur.rowcount == 0:
                cas_miss = True
            else:
                real_audit_subject_id = conn.execute(
                    "SELECT audit_subject_id FROM facts WHERE fact_id = ?",
                    (fact_id,),
                ).fetchone()[0]
                self._snapshot_before_change_in_transaction(
                    conn,
                    fact_id,
                    durable,
                    caused_by=(
                        "memory.set_restricted"
                        if restricted
                        else "memory.set_unrestricted"
                    ),
                    now_iso=now,
                )
                chain = AuditChain(
                    conn,
                    chain_id=f"fact-transition:{real_audit_subject_id}",
                    _skip_schema_check=True,
                )
                chain.log_in_transaction(
                    event_type=(
                        EventType.FACT_RESTRICTED
                        if restricted
                        else EventType.FACT_UNRESTRICTED
                    ),
                    actor=ACTOR_CODE_SET_RESTRICTED,
                    to_state=durable.get("epistemic_state"),
                    reason=REASON_CODE_CAS_GUARDED_WRITE,
                )

        self._l0_del(fact_id)  # force the next recall to read committed policy
        if cas_miss:
            latest = self._get_fact_durable(fact_id)
            if latest is None:
                return False
            return bool((latest.get("metadata") or {}).get("restricted")) == restricted
        return True

    def _fact_version_bump_sql(self, conn) -> str:
        """SET-фрагмент для bump fact_version (миграция 009 / Truth Kernel)."""
        if self._has_fact_version is None:
            self._has_fact_version = facts_table_has_fact_version(conn)
        if self._has_fact_version:
            return "fact_version = fact_version + 1, "
        return ""

    def _snapshot_before_change(
        self,
        fact_id: str,
        fact_data: dict[str, Any],
        caused_by: str,
        now_iso: str | None = None,
    ) -> None:
        """
        Legacy standalone snapshot helper.

        New canonical lifecycle writers MUST use
        _snapshot_before_change_in_transaction() instead: this helper opens a
        separate VersionStore connection, cannot share the canonical SQLite
        transaction, and intentionally remains only for backwards-compatible
        external/test instrumentation.

        PR-C1d: `now_iso`, when given, is forwarded as the snapshot's
        superseded_at — the SAME "now" the caller already used for its own
        canonical UPDATE/history entry, instead of a fresh, independently-read
        timestamp from VersionStore's own (separate) connection. Callers that
        omit it get the previous behavior unchanged.
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
                now_iso=now_iso,
            )
        except Exception:
            logger.exception("VersionStore snapshot failed for %s", fact_id)

    def _snapshot_before_change_in_transaction(
        self,
        conn: sqlite3.Connection,
        fact_id: str,
        fact_data: dict[str, Any],
        caused_by: str,
        now_iso: str,
    ) -> int | None:
        """Append VersionStore evidence inside a canonical write transaction.

        Issue #50 turns version history from a post-commit, best-effort side
        effect into part of the write protocol:

            facts mutation + fact_versions pre-image + AuditChain append
                                == one SQLite transaction

        The legacy ``VELANTRIM_VERSION_SNAPSHOTS=false`` switch is still
        honoured temporarily for backwards compatibility with historical
        recovery tests. In the default/production contract, however, errors
        are never swallowed here: a missing table, integrity failure, or
        injected storage error propagates through ``_db()`` and rolls the
        canonical mutation back with its audit append.
        """
        if (os.getenv("VELANTRIM_VERSION_SNAPSHOTS", "true") or "").lower() in {
            "0", "false", "no", "off",
        }:
            return None

        from core.version_store import VersionStore

        return VersionStore.snapshot_before_change_in_transaction(
            conn,
            fact_id,
            fact_data,
            caused_by=caused_by,
            now_iso=now_iso,
        )

    # ── store_fact ──────────────────────────────────────────────────────────

    def _store_fact_outcome(self, fact: dict) -> "WriteResult":
        """
        PR-C1: the detailed implementation behind store_fact()/store_fact_result().

        Returns a WriteResult distinguishing CREATED / UPDATED / NOOP_EXISTING /
        REJECTED_WRITE_GATE. Raises exactly the same exceptions store_fact()
        always has (ValueError, MemoryBudgetExceededError) — this method adds
        no new try/except; store_fact() and store_fact_result() each handle
        those differently (see below).

        TASK-04: the CREATED/UPDATED distinction is used by pipeline for
        conditional mark_retriever_dirty() — only on real database changes.
        TASK-05: no-op guard skips SQL entirely if claim/source/confidence
        are unchanged.
        """
        from core.write_gate import ensure_writes_allowed
        from core.write_result import WriteResult, WriteStatus

        # SAFE_MODE choke: MetaSupervisor.writes_blocked must stop all L3 writes.
        ensure_writes_allowed()

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
            # Auto-classify missing/placeholder values.  Passing the literal
            # string "UNKNOWN" as an explicit override would freeze both axes
            # at UNKNOWN and suppress deterministic source classification
            # (notably USER_REPORTED for CognitiveFactStore payloads).
            try:
                from core.claim_classifier import classify_claim as _classify
                _ct, _ot, _ = _classify(
                    new_claim, source_val,
                    explicit_claim_type=(
                        None if _raw_ct in (None, "", "UNKNOWN") else _raw_ct
                    ),
                    explicit_origin_type=(
                        None if _raw_ot in (None, "", "UNKNOWN") else _raw_ot
                    ),
                )
            except Exception:
                _ct = normalize_claim_type(_raw_ct)
                _ot = normalize_origin_type(_raw_ot)
        else:
            _ct = normalize_claim_type(_raw_ct)
            _ot = normalize_origin_type(_raw_ot) if not _raw_ot or _raw_ot == "UNKNOWN" else normalize_origin_type(_raw_ot)

        # P0 local-first policy: WriteProtocolGate is a mandatory canonical
        # boundary, not an optional feature flag. WORLD_FACT requires
        # provenance; LLM-derived world facts require evidence. Subjective
        # and UNKNOWN records may still enter as Observed.
        from core.write_gate import admit_fact

        _wg_refs = (metadata_dict or {}).get("evidence_refs") or []
        _wg_ok, _wg_reason = admit_fact(
            claim_type=_ct, origin_type=_ot,
            source=source_val, has_evidence=bool(_wg_refs),
        )
        if not _wg_ok:
            logger.warning("WriteProtocolGate отклонил факт %s: %s", fact_id, _wg_reason)
            return WriteResult(
                status=WriteStatus.REJECTED_WRITE_GATE,
                fact_id=fact_id,
                created=False,
                canonical_exists=not is_new,
                durable_write=False,
                safe_reason_code=_wg_reason,
                safe_message="Write rejected by write-protocol gate.",
            )
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
            # SECURITY (review finding on PR #6): metadata must be part of the
            # no-op check. claim/source/confidence/epistemic_state are all
            # deterministic inputs to attach_integrity_metadata() (checksum,
            # episode_hash, dedup_key) and are unchanged whenever the checks
            # above hold, so a genuine identical re-post still compares equal
            # here — but a caller supplying new metadata (e.g. fresh
            # evidence_refs) now correctly falls through to the real upsert
            # below instead of being silently dropped: this branch performs
            # no SQL write at all, so treating a metadata change as a no-op
            # meant it never reached the durable row (only L0), and
            # validate_and_promote() reads L1 directly (see
            # _get_fact_durable()) — it would never see that fresh evidence.
            _is_noop = (
                existing["claim"]  == new_claim
                and existing["source"] == fact.get("source", "unknown")
                and abs(existing["confidence"] - confidence) < 1e-9
                and existing.get("metadata") == record["metadata"]
                and record["epistemic_state"] != "Contradicted"
            )
            if _is_noop:
                # SECURITY (review finding on PR #6): the SQL row is untouched
                # below (no-op — nothing durable changed), so the cached copy
                # must not claim a fresher `updated_at` than L1 actually has —
                # that divergence is what let a stale L0 timestamp leak into
                # a CAS decision (see _get_fact_durable()). record["updated_at"]
                # was set to a new now() unconditionally above; restore the
                # durable value before publishing to L0.
                record["updated_at"] = existing["updated_at"]
                # PR-C3 hardening: `record` is assembled as a fresh dict and
                # does not carry durable audit_subject_id. Publishing it to
                # L0 as-is would clobber a previously assigned subject id —
                # later invalidate_edge()/transition_esm() would then mint a
                # NEW candidate, seed a phantom audit_chain_heads row via
                # verify_schema_ready(), and only recover the real chain via
                # COALESCE. Preserve the durable subject id on the no-op path.
                if existing.get("audit_subject_id"):
                    record["audit_subject_id"] = existing["audit_subject_id"]
                self._l0_put(fact_id, record)
                return WriteResult(
                    status=WriteStatus.NOOP_EXISTING,
                    fact_id=fact_id,
                    created=False,
                    canonical_exists=True,
                    durable_write=False,
                )  # TASK-04: не новый факт, retriever актуален

        # TASK-09: derived_from — провенанс из L0 Raw Memory
        derived_from = fact.get("derived_from")
        record["derived_from"] = derived_from

        l1_record = {
            **record,
            "metadata": json.dumps(metadata_dict),
            "history":  json.dumps(record["history"]),
        }

        # BUG-FIX v8.3.1: при срабатывании drift protection (TASK-02)
        # epistemic_state и history меняются в record. PR-C1b (Issue #37):
        # раньше это синхронизировалось ОТДЕЛЬНЫМ follow-up UPDATE — но это
        # значило два UPDATE-стейтмента на одну логическую запись, и второй
        # тоже подпадает под WHEN-условие триггера bump_fact_version
        # (migration 009), что дало бы двойной bump. Теперь оба обновления
        # слиты в один ON CONFLICT DO UPDATE — epistemic_state/history
        # входят в SET только когда реально меняются (drift), иначе не
        # трогаются вовсе, как и раньше.
        _drift_detected = (
            existing is not None
            and record["epistemic_state"] == "Contradicted"
            and existing["epistemic_state"] != "Contradicted"
        )

        # PR-C1b (Issue #37): триггер bump_fact_version требует, чтобы любой
        # UPDATE, меняющий claim/confidence/epistemic_state, сам увеличил
        # fact_version — store_fact()/store_fact_result() исторически этого
        # не делали (в отличие от update_state()/CAS-путей), отсюда падения
        # на существующих фактах. Бампим только когда одно из этих трёх
        # полей действительно меняется: metadata-only update не обязан
        # увеличивать fact_version, раз сам триггер этого не требует.
        #
        # PR-C1b review fix: confidence сравнивается EXACT (`!=`), не через
        # epsilon — сам триггер использует `OLD.confidence != NEW.confidence`
        # (миграция 009), точное сравнение. Epsilon здесь допускал случай,
        # когда только метаданные меняются (не no-op — см. _is_noop выше,
        # у него своя, отдельная и намеренно неточная эвристика), а
        # confidence отличается на величину меньше эпсилон, но не равен
        # ровно: SQL всё равно пишет `confidence = excluded.confidence`
        # (новое значение), OLD != NEW технически истинно для триггера, и
        # UPDATE без бампа падает. Exact-сравнение здесь всегда точно
        # отражает то, что реально попадёт в SQLite.
        _content_changed = existing is not None and (
            existing["claim"] != new_claim
            or existing["confidence"] != confidence
            or _drift_detected
        )

        # PR-C3: store_fact()/store_fact_result() get the same tamper-evident
        # AuditChain event as update_state()/_promote_to_validated_cas()
        # (PR-C2) — same C1 (atomic, same transaction) + S2 (per-fact
        # chain_id via audit_subject_id) design, no new architecture.
        # audit_subject_id is reused from the existing row if already
        # assigned (by ANY prior mutation path — store_fact, a later
        # transition_esm(), etc.), else minted lazily here.
        import uuid as _uuid

        from core.audit_chain import (
            ACTOR_CODE_STORE_FACT,
            REASON_CODE_DIRECT_WRITE,
            AuditChain,
            EventType,
        )

        audit_subject_id = (existing.get("audit_subject_id") if existing else None) or _uuid.uuid4().hex
        chain_id = f"fact-transition:{audit_subject_id}"
        l1_record["audit_subject_id"] = audit_subject_id
        with self._db() as ready_conn:
            AuditChain.verify_schema_ready(ready_conn, chain_id=chain_id)

        with self._db() as conn:
            _bump = self._fact_version_bump_sql(conn) if _content_changed else ""
            _esm_set = (
                ", epistemic_state = excluded.epistemic_state, history = excluded.history"
                if _drift_detected else ""
            )
            conn.execute(f"""
                INSERT INTO facts
                    (fact_id, claim, source, confidence, epistemic_state,
                     created_at, updated_at, metadata, history,
                     t_event_valid_start, t_event_valid_end,
                     t_ingestion_start,   t_ingestion_end,
                     derived_from,
                     claim_type, origin_type, memory_type,
                     audit_subject_id)
                VALUES
                    (:fact_id, :claim, :source, :confidence, :epistemic_state,
                     :created_at, :updated_at, :metadata, :history,
                     :t_event_valid_start, :t_event_valid_end,
                     :t_ingestion_start,   :t_ingestion_end,
                     :derived_from,
                     :claim_type, :origin_type, :memory_type,
                     :audit_subject_id)
                ON CONFLICT(fact_id) DO UPDATE SET
                    {_bump}claim       = excluded.claim,
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
                                  ELSE facts.memory_type END{_esm_set},
                    -- PR-C3: assigned once, then stable across every later
                    -- mutation of this row (same COALESCE convention as
                    -- update_state()/_promote_to_validated_cas()).
                    audit_subject_id = COALESCE(audit_subject_id, excluded.audit_subject_id)
                -- epistemic_state, history, t_*_start, derived_from по умолчанию
                -- исключены: управляются только через transition_esm() /
                -- invalidate_edge(). Единственное исключение — drift
                -- protection выше (_esm_set), легальность которой уже
                -- проверена через ESM_TRANSITIONS до этого момента.
            """, l1_record)

            # PR-C3 (same Codex P2 read-your-own-write lesson from PR-C2):
            # re-read the audit_subject_id that ACTUALLY won the COALESCE
            # above rather than trusting the locally-computed candidate —
            # a concurrent writer may have already assigned the real value
            # before this call's `existing` read.
            real_audit_subject_id = conn.execute(
                "SELECT audit_subject_id FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchone()[0]

            # Issue #50: the pre-image is no longer a post-commit,
            # best-effort side effect.  It shares this exact transaction
            # with the UPSERT above and AuditChain append below.  A version
            # failure therefore rolls the canonical write back instead of
            # leaving an unversioned current row.
            if existing:
                self._snapshot_before_change_in_transaction(
                    conn,
                    fact_id,
                    existing,
                    caused_by="memory.store_fact",
                    now_iso=now,
                )

            from_state: str | None = None
            if existing is None:
                event_type = EventType.FACT_CREATED
            elif _drift_detected:
                event_type = EventType.FACT_CONTRADICTED
                from_state = existing["epistemic_state"]
            else:
                event_type = EventType.FACT_UPDATED
            chain = AuditChain(conn, chain_id=f"fact-transition:{real_audit_subject_id}", _skip_schema_check=True)
            chain.log_in_transaction(
                event_type=event_type,
                actor=ACTOR_CODE_STORE_FACT,
                from_state=from_state,
                to_state=record["epistemic_state"],
                reason=REASON_CODE_DIRECT_WRITE,
            )

        record["audit_subject_id"] = real_audit_subject_id

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
                from core.projection_apply import upsert_fts_row
                upsert_fts_row(conn, fact_id, new_claim, source_val)
        except sqlite3.OperationalError:
            pass  # FTS5 недоступен

        # TASK-04: CREATED = реальный INSERT (новый факт) → retriever нужно обновить
        #          UPDATED = UPSERT существующего → retriever актуален
        if existing is None:
            return WriteResult(
                status=WriteStatus.CREATED,
                fact_id=fact_id,
                created=True,
                canonical_exists=True,
                durable_write=True,
            )
        return WriteResult(
            status=WriteStatus.UPDATED,
            fact_id=fact_id,
            created=False,
            canonical_exists=True,
            durable_write=True,
        )

    def store_fact(self, fact: dict) -> bool:
        """
        Сохранить факт. Возвращает True если был реальный INSERT (новый факт),
        False если факт уже существовал (UPSERT или no-op) — **или** был
        отклонён Write Protocol Gate. Raises ValueError / MemoryBudgetExceededError
        exactly as before (unchanged; see _store_fact_outcome()).

        Legacy bool contract — kept byte-for-byte identical for existing
        callers. Prefer store_fact_result() for new call sites that need to
        distinguish "rejected" from "already existed" from "updated" (PR-C1).
        """
        return self._store_fact_outcome(fact).created

    def _safe_canonical_exists(self, fact_id: str | None) -> bool:
        """
        PR-C1 hardening: read whether a canonical `facts` row exists for
        fact_id, WITHOUT ever raising — used only from store_fact_result()'s
        except-blocks, where a second exception (e.g. the same storage
        failure that triggered the except in the first place) must not
        escape and break the non-raising contract. Any read failure here is
        logged server-side and treated as "unknown, assume False" — never
        placed in a client-facing field.
        """
        if not fact_id:
            return False
        try:
            return bool(self.get_fact(fact_id))
        except Exception as exc:
            logger.warning(
                "store_fact_result: canonical-exists readback failed for %s: %s",
                fact_id, exc,
            )
            return False

    def store_fact_result(self, fact: dict) -> "WriteResult":
        """
        PR-C1: explicit, non-raising counterpart to store_fact().

        Never raises for the failure modes it knows about — converts them to
        a WriteResult with a safe_reason_code/safe_message instead, so a
        caller can branch on `result.status` without wrapping every call in
        its own try/except. Genuinely unexpected exceptions are still caught
        (FAILED_INTERNAL) rather than propagated, precisely so this is a
        *non-raising* structured API; the full exception is logged
        server-side only — never placed in a client-facing field.
        """
        from core.memory_budget import MemoryBudgetExceededError
        from core.write_gate import WritesBlockedError
        from core.write_result import WriteResult, WriteStatus

        fact_id = fact.get("fact_id")
        try:
            return self._store_fact_outcome(fact)
        except WritesBlockedError as exc:
            logger.warning(
                "store_fact_result: policy blocked write for fact %s (%s)",
                fact_id,
                exc.reason_code,
            )
            is_safe_mode = exc.reason_code == "safe_mode_writes_blocked"
            return WriteResult(
                status=(
                    WriteStatus.REJECTED_SAFE_MODE
                    if is_safe_mode
                    else WriteStatus.REJECTED_POLICY
                ),
                fact_id=fact_id,
                created=False,
                canonical_exists=self._safe_canonical_exists(fact_id),
                durable_write=False,
                safe_reason_code=exc.reason_code,
                safe_message=(
                    "System is in SAFE_MODE; writes are blocked."
                    if is_safe_mode
                    else "Canonical write policy is unavailable or denied."
                ),
            )
        except MemoryBudgetExceededError as exc:
            logger.warning(
                "store_fact_result: budget rejected fact %s: %s", fact_id, exc
            )
            return WriteResult(
                status=WriteStatus.REJECTED_BUDGET,
                fact_id=fact_id,
                created=False,
                canonical_exists=self._safe_canonical_exists(fact_id),
                durable_write=False,
                safe_reason_code="budget_exceeded",
                safe_message="Memory budget limit reached; fact was not stored.",
            )
        except ValueError as exc:
            logger.warning(
                "store_fact_result: validation rejected fact %s: %s", fact_id, exc
            )
            return WriteResult(
                status=WriteStatus.REJECTED_VALIDATION,
                fact_id=fact_id,
                created=False,
                canonical_exists=self._safe_canonical_exists(fact_id),
                durable_write=False,
                safe_reason_code="validation_failed",
                safe_message="Fact failed validation and was not stored.",
            )
        except sqlite3.Error as exc:
            logger.error(
                "store_fact_result: storage failure for fact %s: %s", fact_id, exc
            )
            return WriteResult(
                status=WriteStatus.FAILED_STORAGE,
                fact_id=fact_id,
                created=False,
                canonical_exists=self._safe_canonical_exists(fact_id),
                durable_write=False,
                safe_reason_code="storage_error",
                safe_message="A storage error occurred; fact was not stored.",
            )
        except Exception:
            logger.exception(
                "store_fact_result: unexpected failure for fact %s", fact_id
            )
            return WriteResult(
                status=WriteStatus.FAILED_INTERNAL,
                fact_id=fact_id,
                created=False,
                canonical_exists=self._safe_canonical_exists(fact_id),
                durable_write=False,
                safe_reason_code="internal_error",
                safe_message="An internal error occurred; fact was not stored.",
            )

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

    def _get_fact_durable(self, fact_id: str) -> dict | None:
        """
        Читает факт напрямую из L1 (SQLite), в обход L0-кэша.

        SECURITY (review finding on PR #6): store_fact()'s no-op upsert path
        publishes a fresh `updated_at` to L0 without touching the durable SQL
        row (see the no-op branch below) — an idempotent POST /facts can leave
        L0 pointing at a timestamp the DB row doesn't have. Any decision that
        has security consequences (validate_and_promote's TruthGate snapshot
        and CAS token) must read L1 directly, never L0, or it can act on a
        divergent value. Ordinary reads (get_fact) still prefer L0 for speed —
        only the validation boundary needs this stronger guarantee.

        Deliberately does NOT publish the result to L0 (review finding on
        PR #6): this snapshot is taken before the CAS-guarded write, so if
        that write later loses the race, caching here would leave L0
        holding a now-stale pre-race row for every other reader in this
        process until the next real write or eviction. The only caller
        (validate_and_promote) always re-reads durably on every call, so it
        gets no benefit from populating this cache and shouldn't poison it
        for everyone else.
        """
        with self._db() as conn:
            row = conn.execute(
                "SELECT * FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchone()
            if row is None:
                return None
            result = dict(row)
            result["metadata"] = json.loads(result["metadata"])
            result["history"]  = json.loads(result.get("history") or "[]")
        return result

    def get_fact_durable(self, fact_id: str) -> dict | None:
        """
        Публичная обёртка над _get_fact_durable() для других модулей core,
        которым нужно durable (в обход L0) чтение — например,
        core.truth_maintenance.supersede(), которому нужен снимок старого
        факта под тем же требованием, что и validate_and_promote(): решение
        с последствиями для безопасности не должно опираться на L0.
        """
        return self._get_fact_durable(fact_id)

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

    # ── count_facts_by_epistemic_state ─────────────────────────────────────

    def count_facts_by_epistemic_state(self) -> dict[str, int]:
        """Лёгкий COUNT(*) GROUP BY epistemic_state — для /health без full scan."""
        with self._db() as conn:
            rows = conn.execute(
                "SELECT epistemic_state, COUNT(*) AS n FROM facts "
                "GROUP BY epistemic_state"
            ).fetchall()
        return {
            (row["epistemic_state"] if row["epistemic_state"] is not None else "unknown"): int(row["n"])
            for row in rows
        }

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
    ) -> bool:
        """
        TASK-09: Связать derived факт с оригинальным raw_id в провенанс-таблице.
        Также устанавливает facts.derived_from = raw_id и инвалидирует L0-кэш.

        PR-C1: raw_id и fact_id проверяются на существование в ОДНОЙ
        транзакции перед записью — l0_fact_provenance.fact_id ссылается на
        facts(fact_id) как REFERENCES, но PRAGMA foreign_keys для этого
        соединения не включена, поэтому без явной проверки INSERT OR IGNORE
        молча создавал phantom-provenance на fact_id, которого нет в `facts`
        (см. PR-C1 evidence report). Возвращает False и ничего не пишет,
        если raw_id или fact_id отсутствуют — существующие вызывающие
        стороны, игнорирующие возврат, не ломаются (раньше метод возвращал
        None, тоже falsy).
        """
        prov_id = f"prov_{hashlib.sha256((raw_id+fact_id).encode()).hexdigest()[:16]}"
        now = datetime.now(UTC).isoformat()
        with self._db() as conn:
            raw_exists = conn.execute(
                "SELECT 1 FROM l0_raw_memory WHERE raw_id = ?", (raw_id,)
            ).fetchone()
            fact_exists = conn.execute(
                "SELECT 1 FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchone()
            if not raw_exists or not fact_exists:
                return False
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
        return True

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
        Атомарно обновить epistemic_state + history + metadata (+ fact_version,
        если колонка существует — миграция 009; на legacy-схеме без неё это
        no-op, как и раньше).
        При переходе в терминальное состояние (Collapsed, Contradicted)
        устанавливает t_ingestion_end = now (система перестала верить факту).

        PR-C1c (Issue #40): direct transition to 'ImmutableCore' is never
        permitted through this method. There is no production path anywhere
        that legitimately sets epistemic_state to 'ImmutableCore' today
        (Ring Zero seeding only ever creates facts directly in 'Observed'
        or, for a small allowlisted set, 'Validated' — see
        _store_fact_outcome()'s is_ring_zero_seed check). transition_esm()
        already blocks this target unconditionally before ever calling
        update_state() — this guard makes update_state() itself safe to
        call directly too, rather than relying on
        prevent_immutablecore_mutation's follow-up self-trip (removed
        below) as an accidental safety net.
        """
        from core.write_gate import ensure_writes_allowed
        ensure_writes_allowed()

        if new_state == "ImmutableCore":
            raise ImmutableStateError(
                "update_state: direct transition to 'ImmutableCore' is not "
                "permitted — requires Ring Zero / a special approval "
                "protocol outside this method."
            )

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
        if cached is None:
            # PR-C1c: fact doesn't exist — nothing to transition. The only
            # production caller (transition_esm()) already checks this
            # before calling update_state(), but a direct caller must not
            # get a false True back (see the CAS-miss fix below for the
            # matching concurrent-modification case).
            return False

        old_state = cached.get("epistemic_state", "Observed")  # FIX #19: сохраняем до мутации
        preimage = copy.deepcopy(cached)
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

        # ── Шаг 2: state + history (+ t_ingestion_end) + metadata + fact_version
        # — ОДНИМ UPDATE (PR-C1c/Issue #40). Раньше metadata обновлялась
        # ОТДЕЛЬНЫМ, вторым UPDATE-стейтментом после этого — но
        # prevent_collapsed_mutation/prevent_immutablecore_mutation (migration
        # 009) срабатывают на ЛЮБОЙ UPDATE, как только epistemic_state уже
        # Collapsed/ImmutableCore, так что второй стейтмент всегда падал на
        # переходе В эти состояния, спотыкаясь сам о себя. Слияние в один
        # стейтмент устраняет это: триггер видит ровно одно изменение строки,
        # соответствующее одному логическому переходу.
        #
        # FIX #19 (Claude audit) CAS-guard — WHERE epistemic_state = ? —
        # предотвращает check-then-act гонку при параллельных вызовах.
        # PR-C1c: rowcount теперь проверяется — раньше, если CAS-guard не
        # совпадал (конкурентная модификация между чтением old_state выше и
        # этой записью), первый UPDATE тихо не менял ни одной строки, но
        # ВТОРОЙ (metadata, без условия на epistemic_state) всё равно
        # выполнялся и "успешно" перезаписывал metadata под несостоявшийся
        # переход — false success с рассинхронизацией state/metadata. Слияние
        # в один стейтмент с проверкой rowcount закрывает и это.
        #
        # PR-C2: ESM/terminal-state transitions get a tamper-evident
        # AuditChain event, atomic with this same UPDATE (same connection,
        # same transaction — C1 design). audit_subject_id is an opaque,
        # lazily-generated per-fact token (never the real fact_id) used
        # only to build a per-fact chain_id; it is erased automatically
        # when the fact itself is erased (facts.audit_subject_id lives on
        # the same row). memory_events.fact_id is NEVER populated for
        # these events — confirmed empirically (PR-C2 design gate) that a
        # real fact_id there would deadlock GDPR erasure the moment
        # foreign_keys enforcement is ever enabled for this connection,
        # since memory_events' append-only triggers make the child row
        # undeletable. Readiness (schema self-heal, never DDL mid-
        # transaction) is checked on a SEPARATE connection/transaction
        # before this one opens.
        import uuid as _uuid

        from core.audit_chain import (
            AuditChain,
            EventType,
            REASON_CODE_CAS_TRANSITION,
            map_actor_code,
        )

        audit_subject_id = cached.get("audit_subject_id") or _uuid.uuid4().hex
        chain_id = f"fact-transition:{audit_subject_id}"
        with self._db() as ready_conn:
            AuditChain.verify_schema_ready(ready_conn, chain_id=chain_id)

        with self._db() as conn:
            bump = self._fact_version_bump_sql(conn)
            if self.use_json_insert:
                if set_ingestion_end:
                    cur = conn.execute(f"""
                        UPDATE facts
                        SET epistemic_state = ?,
                            updated_at      = ?,
                            {bump}history         = json_insert(history, '$[#]', json(?)),
                            t_ingestion_end = COALESCE(t_ingestion_end, ?),
                            metadata        = ?,
                            audit_subject_id = COALESCE(audit_subject_id, ?)
                        WHERE fact_id = ? AND epistemic_state = ?
                    """, (new_state, now, json.dumps(history_entry), now,
                          new_metadata_json, audit_subject_id, fact_id, old_state))
                else:
                    cur = conn.execute(f"""
                        UPDATE facts
                        SET epistemic_state = ?,
                            updated_at      = ?,    {bump}history         = json_insert(history, '$[#]', json(?)),
                            metadata        = ?,
                            audit_subject_id = COALESCE(audit_subject_id, ?)
                        WHERE fact_id = ? AND epistemic_state = ?
                    """, (new_state, now, json.dumps(history_entry),
                          new_metadata_json, audit_subject_id, fact_id, old_state))
            else:
                row = conn.execute(
                    "SELECT history FROM facts WHERE fact_id = ?", (fact_id,)
                ).fetchone()
                if not row:
                    # PR-C1c review fixup: symmetric to the CAS-miss path
                    # below — the row vanishing between our cached read and
                    # this fallback SELECT (concurrent deletion, or a stale
                    # L0 entry for an already-gone fact) proves any L0 entry
                    # for this fact_id is stale. Evict it so the next reader
                    # doesn't get the same staleness back.
                    self._l0_del(fact_id)
                    return False
                history_l1 = json.loads(row[0] or "[]")
                history_l1.append(history_entry)
                if set_ingestion_end:
                    cur = conn.execute(f"""
                        UPDATE facts
                        SET epistemic_state = ?, updated_at = ?,
                            {bump}history = ?,
                            t_ingestion_end = COALESCE(t_ingestion_end, ?),
                            metadata = ?,
                            audit_subject_id = COALESCE(audit_subject_id, ?)
                        WHERE fact_id = ? AND epistemic_state = ?
                    """, (new_state, now, json.dumps(history_l1), now,
                          new_metadata_json, audit_subject_id, fact_id, old_state))
                else:
                    cur = conn.execute(f"""
                        UPDATE facts
                        SET epistemic_state = ?, updated_at = ?,
                            {bump}history = ?,
                            metadata = ?,
                            audit_subject_id = COALESCE(audit_subject_id, ?)
                        WHERE fact_id = ? AND epistemic_state = ?
                    """, (new_state, now, json.dumps(history_l1),
                          new_metadata_json, audit_subject_id, fact_id, old_state))

            if cur.rowcount == 0:
                # CAS guard missed: epistemic_state changed concurrently
                # between the read above and this write. Nothing was
                # written by this statement (single merged UPDATE — no
                # partial effect to roll back); do not publish a stale L0
                # entry, do not report success. The miss itself proves the
                # L0 entry this caller read from (or the caller's own
                # in-hand copy) is stale — evict it so the next reader gets
                # a fresh row instead of the same staleness (review finding
                # on PR #41: an un-evicted stale L0 entry could otherwise
                # cause repeated CAS misses / illegal-transition decisions
                # downstream).
                #
                # PR-C2: a CAS miss produces NO AuditChain event — the log
                # call below is only reached after this check passes.
                self._l0_del(fact_id)
                return False

            # PR-C2 (Codex P2): re-read the audit_subject_id that ACTUALLY
            # won the COALESCE above, rather than trusting the candidate
            # this call computed from a possibly-stale `cached` read. If
            # another writer already assigned a real audit_subject_id
            # before this call's own (stale-L0) candidate was computed,
            # COALESCE correctly keeps the real one in the row — but the
            # local `audit_subject_id`/`chain_id` variables computed above
            # would still be the discarded candidate. Logging/caching
            # under that discarded value would fragment this fact's
            # ledger across two chains, only one of which is reachable
            # from facts.audit_subject_id. This SELECT sees the value
            # this same transaction just wrote (read-your-own-write),
            # never a value from any other, uncommitted transaction.
            real_audit_subject_id = conn.execute(
                "SELECT audit_subject_id FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchone()[0]
            real_chain_id = f"fact-transition:{real_audit_subject_id}"

            self._snapshot_before_change_in_transaction(
                conn,
                fact_id,
                preimage,
                caused_by=(
                    f"memory.transition_esm:"
                    f"{history_entry.get('by') or 'update_state'}"
                ),
                now_iso=now,
            )

            # PR-C2: log strictly after the CAS-guard success, still
            # inside this same transaction, using this same `conn` — any
            # exception here (including a stale chain-head race) aborts
            # the whole transaction via _db()'s own rollback, so the
            # canonical UPDATE above is undone too. No payload, no free
            # text: only structured, allowlisted actor_code/reason_code
            # and the plain ESM state names already validated above.
            if new_state == "Collapsed":
                event_type = EventType.FACT_COLLAPSED
            elif new_state == "Contradicted":
                event_type = EventType.FACT_CONTRADICTED
            elif new_state == "Deprecated":
                event_type = EventType.FACT_DEPRECATED
            else:
                event_type = EventType.ESM_TRANSITION
            chain = AuditChain(conn, chain_id=real_chain_id, _skip_schema_check=True)
            chain.log_in_transaction(
                event_type=event_type,
                actor=map_actor_code(history_entry.get("by")),
                from_state=old_state,
                to_state=new_state,
                reason=REASON_CODE_CAS_TRANSITION,
            )

        # ── Шаг 3: публикуем L0 ТОЛЬКО после успешной, CAS-подтверждённой записи
        cached["audit_subject_id"] = real_audit_subject_id
        self._l0_put(fact_id, cached)
        return True

    # ── refresh_fact_integrity_metadata ──────────────────────────────────────

    def refresh_fact_integrity_metadata(
        self, fact_id: str, *, max_attempts: int = 5
    ) -> str:
        """Atomically recompute and persist an EXISTING fact's integrity
        metadata (content_checksum, episode_hash, claim_dedup_key) from its
        OWN current claim/source/confidence/epistemic_state.

        Replaces the old ConsolidationEngine._refresh_checksum() ->
        store_fact() path (issue #26 / PR #27): store_fact() rejects any
        fact whose epistemic_state isn't 'Observed' (Ring Zero aside), so
        calling it right after a successful promotion always raised
        ValueError, which run()'s fallback handler misread as a failed
        promotion — incrementing report.errors on the happy path. It also
        replaces the narrower update_fact_metadata(fact_id, metadata) this
        PR originally added, and the Copilot review finding against it:
        that method took a CALLER-computed metadata dict (so the caller
        had to read some earlier snapshot to build it — exactly the
        "compute on one snapshot, write to a possibly different one"
        hazard) and used `cursor.rowcount > 0` to infer whether the row
        existed. A genuinely different fact_id correctly gives rowcount
        0 not-found; nothing here otherwise depends on that (see the CAS
        guard below, which is what actually decides success/failure —
        rowcount is only ever consulted on the guarded UPDATE, never as
        a stand-in existence probe on an unconditional one).

        This method computes the new metadata itself, from a read it took
        moments before, inside the SAME retry attempt — there is no
        caller-supplied snapshot to go stale.

        Never touches epistemic_state, claim, confidence, source, history,
        versions, or provenance — only `metadata`. Never creates a fact
        that doesn't exist.

        Atomicity / no lost update: mirrors _promote_to_validated_cas()'s
        convention — a guarded UPDATE whose WHERE clause pins fact_id AND
        the exact (epistemic_state, updated_at, metadata) this attempt
        read. If ANY of those changed (a concurrent ESM transition, a
        concurrent store_fact() upsert, or another concurrent metadata
        write) between the read and this write, the UPDATE matches zero
        rows — proving the snapshot this attempt computed FROM is no
        longer current — and the method re-reads a fresh snapshot and
        retries, up to `max_attempts` times, rather than either silently
        overwriting a newer value or reporting a false success. A fact
        that is deleted between the read and the write is caught the
        same way: the next attempt's read finds no row and returns
        "not_found" honestly, instead of reporting success for a write
        that never really landed.

        This CAS guard applies uniformly to a genuine no-op (the freshly
        recomputed metadata already equals what's stored) too — `_db()`
        opens no explicit transaction before the SELECT above, so a
        no-op branch that returned early right after that SELECT would
        have the same read-then-act race as the write path: another
        instance could mutate or delete the row in the gap, and the
        early return would report success against a snapshot that's
        already stale. Instead the no-op is written through the same
        guarded UPDATE (SQLite reports rowcount == 1 for a matching
        same-value UPDATE exactly as for a real change), so it is
        re-verified against the live row at write time and retried on a
        CAS miss exactly like any other attempt.

        Returns "success" if the fact exists — including a genuine no-op,
        proven live at write time, never a stale read alone — or
        "not_found" if no fact with this id currently exists. The L0
        cache is invalidated only after that outcome is durably proven:
        on a committed write (no-op or real change) or on a proven-absent
        read, never speculatively before either.
        """
        from core.fact_integrity import attach_integrity_metadata

        for _attempt in range(max_attempts):
            with self._db() as conn:
                row = conn.execute(
                    "SELECT claim, source, confidence, epistemic_state, "
                    "updated_at, metadata FROM facts WHERE fact_id = ?",
                    (fact_id,),
                ).fetchone()
                if row is None:
                    # This SELECT just proved the row absent from L1 — if
                    # another SQLiteGraphStore instance (or an erasure
                    # path) removed it after this instance's L0 cached an
                    # earlier read, that cached entry is now provably
                    # stale. Drop it so the next get_fact() doesn't keep
                    # serving a fact this call just proved gone.
                    with self._l0_lock:
                        if fact_id in self._l0:
                            del self._l0[fact_id]
                    return "not_found"
                claim, source, confidence, epistemic_state, updated_at, metadata_json = row
                current_metadata = json.loads(metadata_json or "{}")
                new_metadata = attach_integrity_metadata(
                    current_metadata,
                    claim=claim or "",
                    source=source or "unknown",
                    confidence=float(confidence if confidence is not None else 0.5),
                    epistemic_state=epistemic_state or "Observed",
                )

                # A genuine no-op (new_metadata == current_metadata) is
                # deliberately NOT special-cased with an early return
                # here. `_db()` doesn't open an explicit transaction
                # before this SELECT, so between this read and any
                # early-return, another SQLiteGraphStore instance can
                # freely mutate or delete this row — a "the SELECT
                # already proved it" no-op return would then report
                # stale-snapshot success. Instead, the no-op is routed
                # through the SAME CAS-guarded UPDATE as a real change,
                # writing new_metadata_json even when it's byte-identical
                # to what's already stored: the guard's WHERE clause
                # re-checks the row at write time, and SQLite reports
                # rowcount == 1 for a matching same-value UPDATE just as
                # for a genuine change, so a true no-op is proven exactly
                # as atomically as a write, and a concurrent mutation or
                # deletion between this read and the write below is
                # caught by the same rowcount == 0 retry path.
                new_metadata_json = json.dumps(new_metadata)
                cur = conn.execute(
                    "UPDATE facts SET metadata = ? "
                    "WHERE fact_id = ? AND epistemic_state = ? "
                    "AND updated_at = ? AND metadata = ?",
                    (
                        new_metadata_json,
                        fact_id,
                        epistemic_state,
                        updated_at,
                        metadata_json,
                    ),
                )
                committed = cur.rowcount == 1

            if committed:
                # Invalidate rather than patch: this attempt only proved
                # `metadata` (guarded by the CAS clause above); it does
                # NOT prove no OTHER field drifted between an earlier L0
                # read and this commit (e.g. a concurrent writer using a
                # different SQLiteGraphStore instance, whose own writes
                # this instance's L0 has no way to observe). Patching a
                # stale cached dict's metadata field in place would leave
                # every other field silently wrong; dropping the entry
                # forces the next get_fact() to re-read the durably
                # committed row instead.
                with self._l0_lock:
                    if fact_id in self._l0:
                        del self._l0[fact_id]
                return "success"
            # CAS miss: the row changed (or was deleted) between the read
            # above and this write — retry against a fresh snapshot.

        raise RuntimeError(
            f"refresh_fact_integrity_metadata: too much contention on "
            f"'{fact_id}' after {max_attempts} attempts"
        )

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
        # update_state() owns the full transaction: canonical UPDATE,
        # VersionStore pre-image, and AuditChain append. A CAS miss produces
        # none of them; any evidence-write failure rolls all of them back.
        return self.update_state(fact_id, new_state, history_entry, now)

    _ESM_LADDER = ("Observed", "Hypothesized", "Supported", "Validated")

    def promote_esm_to(self, fact_id: str, target: str, by: str = "promote_esm") -> bool:
        """Пошагово повышает факт до target по канонической лестнице ESM.

        P0-D scope note: this generic ladder-walker is used by call sites
        outside graduated-promotion/consolidation (world_skills_ingest,
        CognitiveStore.transition, test fixtures) purely as an ESM-legality
        helper, so it intentionally still ends its walk with a plain
        transition_esm() into 'Validated' — NOT validate_and_promote().
        Routing every one of those callers through TruthGate is out of
        scope here (that would be variant B's global lockdown); only
        core/promotion_policy.py and core/consolidation_engine.py were
        named for this fix and are handled at their own call sites instead.
        """
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

    def _promote_to_validated_cas(
        self,
        fact_id: str,
        expected_state: str,
        expected_updated_at: str,
        durable_snapshot: dict,
        by: str,
    ) -> bool:
        """
        Единственная мутация, которую делает validate_and_promote(): один
        атомарный conditional UPDATE прямо против снимка, на котором TruthGate
        вынес вердикт — WHERE fact_id = ? AND epistemic_state = ? AND
        updated_at = ?, оба значения приходят от вызывающего (durable-снимок),
        никакого нового чтения внутри.

        SAFE_MODE: ensure_writes_allowed() at entry (this path bypasses
        update_state()).

        Это НАРОЧНО не transition_esm(): тот делает свежий self.get_fact()
        и легальность проверяет по ЭТОМУ свежему состоянию — если факт успел
        измениться (например, конкурентный переход в другое состояние), это
        может кинуть ValueError (нелегальный переход) вместо честного
        concurrent_modification. Здесь легальность уже проверена в
        validate_and_promote() против исходного снимка; единственный
        оставшийся вопрос — совпадает ли ещё этот снимок с БД, и на него
        отвечает сам WHERE.

        Возвращает True только если UPDATE реально затронул строку (rowcount
        == 1) — т.е. факт был именно там, где его видел TruthGate. Возвращает
        False без какой-либо мутации, если WHERE не совпал (факт изменился
        ИЛИ был удалён конкурентно) — оба случая одинаково означают
        "снимок больше не действителен", и вызывающий обязан трактовать это
        как concurrent_modification, а не как success.

        VersionStore-снимок записывается только после подтверждённого CAS,
        но ДО commit — на том же ``conn`` и в той же транзакции, что facts
        UPDATE и AuditChain. Поэтому отклонённая попытка не создаёт фантом,
        а сбой version/audit evidence откатывает сам переход.
        """
        from core.write_gate import ensure_writes_allowed
        ensure_writes_allowed()

        now = _now()
        new_state = "Validated"
        history_entry = {
            "state": new_state, "from": expected_state, "at": now, "by": by,
        }

        from core.fact_integrity import attach_integrity_metadata

        new_record = copy.deepcopy(durable_snapshot)
        new_record["epistemic_state"] = new_state
        new_record["updated_at"] = now
        new_record.setdefault("history", []).append(history_entry)
        new_record["metadata"] = attach_integrity_metadata(
            new_record.get("metadata") or {},
            claim=new_record.get("claim", ""),
            source=new_record.get("source", "unknown"),
            confidence=float(new_record.get("confidence", 0.5)),
            epistemic_state=new_state,
        )
        new_metadata_json = json.dumps(new_record["metadata"])

        # PR-C2: Validated is a first-class ESM transition — the same
        # tamper-evident audit coverage wired into update_state() (C1:
        # atomic, same-transaction; S2: per-fact chain via
        # audit_subject_id/chain_id) applies here too. This method is
        # deliberately NOT routed through update_state() (see its own
        # docstring above), so it needs its own copy of the same wiring
        # rather than getting it "for free". audit_subject_id/chain_id
        # computation and the pre-transaction readiness check mirror
        # update_state()'s exactly.
        import uuid as _uuid

        from core.audit_chain import (
            AuditChain,
            EventType,
            REASON_CODE_CAS_TRANSITION,
            map_actor_code,
        )

        audit_subject_id = durable_snapshot.get("audit_subject_id") or _uuid.uuid4().hex
        chain_id = f"fact-transition:{audit_subject_id}"
        with self._db() as ready_conn:
            AuditChain.verify_schema_ready(ready_conn, chain_id=chain_id)

        with self._db() as conn:
            bump = self._fact_version_bump_sql(conn)
            if self.use_json_insert:
                cur = conn.execute(f"""
                    UPDATE facts
                    SET epistemic_state = ?,
                        updated_at      = ?,
                        {bump}history         = json_insert(history, '$[#]', json(?))
                    WHERE fact_id = ? AND epistemic_state = ? AND updated_at = ?
                """, (new_state, now, json.dumps(history_entry),
                      fact_id, expected_state, expected_updated_at))
                committed = cur.rowcount == 1
            else:
                # SECURITY (review finding on PR #6): "committed" must reflect
                # the guarded UPDATE's own rowcount, not this preceding SELECT
                # — another connection can change/delete the row in the gap
                # between them (the SELECT takes no write lock), and this
                # fallback path is otherwise the only one that would report
                # success based on a stale read instead of the actual write.
                row = conn.execute(
                    "SELECT history FROM facts "
                    "WHERE fact_id = ? AND epistemic_state = ? AND updated_at = ?",
                    (fact_id, expected_state, expected_updated_at),
                ).fetchone()
                committed = False
                if row is not None:
                    history_l1 = json.loads(row[0] or "[]")
                    history_l1.append(history_entry)
                    cur = conn.execute(f"""
                        UPDATE facts
                        SET epistemic_state = ?, updated_at = ?,
                            {bump}history = ?
                        WHERE fact_id = ? AND epistemic_state = ? AND updated_at = ?
                    """, (new_state, now, json.dumps(history_l1),
                          fact_id, expected_state, expected_updated_at))
                    committed = cur.rowcount == 1

            if not committed:
                # PR-C2: a CAS miss produces NO AuditChain event — nothing
                # below this point has run yet.
                return False

            conn.execute(
                "UPDATE facts SET metadata = ?, "
                "audit_subject_id = COALESCE(audit_subject_id, ?) WHERE fact_id = ?",
                (new_metadata_json, audit_subject_id, fact_id),
            )

            # PR-C2 (Codex P2): re-read the audit_subject_id that ACTUALLY
            # won the COALESCE above — see update_state()'s identical
            # comment for the full rationale (a stale durable_snapshot
            # could otherwise cause this call to log/cache under a
            # discarded candidate instead of the real, already-assigned
            # value, fragmenting the fact's ledger across two chains).
            real_audit_subject_id = conn.execute(
                "SELECT audit_subject_id FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchone()[0]
            real_chain_id = f"fact-transition:{real_audit_subject_id}"

            self._snapshot_before_change_in_transaction(
                conn,
                fact_id,
                durable_snapshot,
                caused_by=f"memory.validate_and_promote:{by}",
                now_iso=now,
            )

            # PR-C2: log strictly after the CAS-guard success, still
            # inside this same transaction, using this same `conn` — any
            # exception here (including a stale chain-head race) aborts
            # the whole transaction via _db()'s own rollback, so the
            # canonical UPDATEs above are undone too.
            chain = AuditChain(conn, chain_id=real_chain_id, _skip_schema_check=True)
            chain.log_in_transaction(
                event_type=EventType.ESM_TRANSITION,
                actor=map_actor_code(by),
                from_state=expected_state,
                to_state=new_state,
                reason=REASON_CODE_CAS_TRANSITION,
            )

            # issue #191: first Canon caller of the transactional projection
            # outbox. Appended strictly after the CAS UPDATE, VersionStore
            # pre-image and AuditChain event have all succeeded, still
            # inside this same transaction and connection, before commit —
            # any failure here (including the fail-closed raises below)
            # rolls back everything above via _db()'s own exception
            # handling. A pre-migration-020 database (user_version < 20)
            # has no outbox feature to be "backed" by, so this is a no-op
            # there, exactly as promotion has always behaved. An activated
            # database (user_version >= 20) missing either
            # projection_outbox or facts.fact_version is a schema
            # inconsistency, not a legacy shape — see
            # ProjectionOutboxActivationError.
            user_version = conn.execute("PRAGMA user_version").fetchone()[0]
            if user_version >= _PROJECTION_OUTBOX_MIGRATION_VERSION:
                if not self._real_table_exists(conn, "projection_outbox"):
                    raise ProjectionOutboxActivationError(
                        f"validate_and_promote('{fact_id}'): PRAGMA "
                        f"user_version={user_version} claims migration 020 "
                        "is applied, but projection_outbox does not exist "
                        "as a real table (missing entirely, or present as "
                        "a VIEW) — refusing to promote without the "
                        "required intent"
                    )
                if not self._has_fact_version:
                    raise ProjectionOutboxActivationError(
                        f"validate_and_promote('{fact_id}'): PRAGMA "
                        f"user_version={user_version} claims migration 020 "
                        "is applied, but facts.fact_version is missing — "
                        "refusing to promote without a durable "
                        "canonical_version"
                    )
                canonical_version = conn.execute(
                    "SELECT fact_version FROM facts WHERE fact_id = ?",
                    (fact_id,),
                ).fetchone()[0]

                from core.projection_outbox import (
                    LOCAL_PROJECTION_SCOPE_REF,
                    ProjectionIntent,
                    ProjectionKind,
                    ProjectionOperation,
                    append_projection_intent_in_transaction,
                )

                append_projection_intent_in_transaction(
                    conn,
                    ProjectionIntent(
                        aggregate_id=fact_id,
                        scope_ref=LOCAL_PROJECTION_SCOPE_REF,
                        canonical_version=canonical_version,
                        projection_kind=ProjectionKind.ALL,
                        operation=ProjectionOperation.REFRESH,
                    ),
                )

        # Canonical UPDATE + version pre-image + audit event + (if
        # activated) projection-outbox intent have committed. Only the
        # process-local cache publication remains.
        new_record["audit_subject_id"] = real_audit_subject_id
        self._l0_put(fact_id, new_record)
        return True

    def supersede_fact_cas(
        self,
        old_id: str,
        new_fact_id: str,
        new_record_seed: dict[str, Any],
        expected_old_state: str,
        expected_old_updated_at: str,
        old_durable_snapshot: dict[str, Any],
        by: str = "truth_maintenance.supersede",
    ) -> "SupersedeCasResult":
        """
        Единственная мутация, которую делает core.truth_maintenance.supersede():
        один атомарный facts-transaction, который либо целиком проводит новый
        факт Observed→Hypothesized→Supported→Validated и переводит старый в
        Deprecated, либо не меняет ничего вообще.

        SAFE_MODE: ensure_writes_allowed() at entry (bypasses store_fact /
        update_state choke points by design).

        НАРОЧНО не использует store_fact()/promote_to_validated()/
        transition_esm(): каждый из них открывает СВОЙ _db()-контекст (своя
        транзакция, свой commit) — последовательность таких вызовов оставляла
        бы окно, где новый факт уже закоммичен, а старый ещё нет (или
        наоборот). Здесь все SQL-мутации идут через один conn внутри одного
        `with self._db() as conn:` — либо все коммитятся вместе, либо (при
        любой ошибке/CAS-мисс) транзакция откатывается целиком.

        CAS: старый факт мутируется ТОЛЬКО guarded UPDATE-ом —
        WHERE fact_id = ? AND epistemic_state = ? AND updated_at = ?, оба
        значения взяты из durable-снимка, на котором TruthGate уже вынес
        вердикт (см. TruthGate.evaluate() в core.truth_maintenance.supersede,
        ДО вызова этого метода). Если WHERE не совпал — факт изменился или
        был удалён конкурентно между снимком и этой записью; уже сделанные в
        этой же транзакции insert/ladder нового факта откатываются вместе с
        ним (rollback), результат — committed=False, reason=
        "concurrent_modification". Коллизия по new_fact_id (PRIMARY KEY)
        детектируется тем же способом — попыткой INSERT без ON CONFLICT;
        sqlite3.IntegrityError → committed=False, reason="new_id_collision",
        без каких-либо иных мутаций в этой попытке.

        VersionStore pre-image старого факта и оба AuditChain события
        записываются после подтверждённого CAS, но до commit — внутри той
        же facts-транзакции. L0 публикуется только после commit. Внешние
        causal/provenance projections всё ещё остаются отдельной, явно
        ограниченной следующим P0-срезом областью.
        """
        from core.fact_integrity import attach_integrity_metadata
        from core.write_gate import ensure_writes_allowed
        ensure_writes_allowed()

        now = _now()
        claim      = new_record_seed.get("claim", "")
        source     = new_record_seed.get("source", "unknown")
        confidence = float(new_record_seed.get("confidence", 0.5))
        raw_metadata = dict(new_record_seed.get("metadata") or {})

        initial_metadata = attach_integrity_metadata(
            raw_metadata, claim=claim, source=source,
            confidence=confidence, epistemic_state="Observed",
        )
        insert_record = {
            "fact_id":             new_fact_id,
            "claim":               claim,
            "source":              source,
            "confidence":          confidence,
            "epistemic_state":     "Observed",
            "created_at":          now,
            "updated_at":          now,
            "metadata":            json.dumps(initial_metadata),
            "history":             json.dumps([]),
            "t_event_valid_start": now,
            "t_event_valid_end":   None,
            "t_ingestion_start":   now,
            "t_ingestion_end":     None,
            "derived_from":        new_record_seed.get("derived_from"),
            "claim_type":          new_record_seed.get("claim_type", "UNKNOWN"),
            "origin_type":         new_record_seed.get("origin_type", "UNKNOWN"),
            "memory_type":         new_record_seed.get("memory_type", "semantic"),
        }

        # PR-C3: supersede_fact_cas() gets the same tamper-evident
        # AuditChain wiring as the other lifecycle mutation paths — same
        # C1 (atomic, same transaction) + S2 (per-fact chain_id) design.
        # new_fact_id is guaranteed brand new here (the IntegrityError
        # collision check below is the authoritative guard), so its
        # audit_subject_id is always freshly minted, no COALESCE needed.
        # old_id may already have one from an earlier mutation.
        import uuid as _uuid

        from core.audit_chain import (
            AuditChain,
            EventType,
            REASON_CODE_CAS_TRANSITION,
            map_actor_code,
        )

        audit_subject_id_new = _uuid.uuid4().hex
        audit_subject_id_old_candidate = old_durable_snapshot.get("audit_subject_id") or _uuid.uuid4().hex
        insert_record["audit_subject_id"] = audit_subject_id_new
        with self._db() as ready_conn:
            AuditChain.verify_schema_ready(ready_conn, chain_id=f"fact-transition:{audit_subject_id_new}")
        with self._db() as ready_conn:
            AuditChain.verify_schema_ready(
                ready_conn, chain_id=f"fact-transition:{audit_subject_id_old_candidate}",
            )

        with self._db() as conn:
            # 1) Fail-fast recheck of the old fact's CAS snapshot — cheap,
            # avoids doing the insert+ladder work below when the snapshot is
            # already stale. Not itself the authoritative guard (see the
            # guarded UPDATE at the end); a plain SELECT takes no write lock.
            precheck = conn.execute(
                "SELECT 1 FROM facts WHERE fact_id = ? AND epistemic_state = ? "
                "AND updated_at = ?",
                (old_id, expected_old_state, expected_old_updated_at),
            ).fetchone()
            if precheck is None:
                return SupersedeCasResult(
                    committed=False, reason="concurrent_modification",
                )

            # 2) + 3) Insert the new fact as Observed. No ON CONFLICT clause:
            # a pre-existing row at new_fact_id raises IntegrityError (PK),
            # which is the authoritative, race-proof collision check — there
            # is no separate SELECT-then-INSERT window to lose.
            try:
                conn.execute("""
                    INSERT INTO facts
                        (fact_id, claim, source, confidence, epistemic_state,
                         created_at, updated_at, metadata, history,
                         t_event_valid_start, t_event_valid_end,
                         t_ingestion_start,   t_ingestion_end,
                         derived_from, claim_type, origin_type, memory_type,
                         audit_subject_id)
                    VALUES
                        (:fact_id, :claim, :source, :confidence, :epistemic_state,
                         :created_at, :updated_at, :metadata, :history,
                         :t_event_valid_start, :t_event_valid_end,
                         :t_ingestion_start,   :t_ingestion_end,
                         :derived_from, :claim_type, :origin_type, :memory_type,
                         :audit_subject_id)
                """, insert_record)
            except sqlite3.IntegrityError:
                return SupersedeCasResult(
                    committed=False, reason="new_id_collision",
                )

            bump = self._fact_version_bump_sql(conn)

            # 4) + 5) Ladder Observed → Hypothesized → Supported → Validated,
            # each step its own history entry. The row is invisible to any
            # other connection until this transaction commits, so no CAS
            # guard is needed here beyond the defensive epistemic_state match.
            new_history: list[dict[str, Any]] = []
            cur_state = "Observed"
            for target_state in ("Hypothesized", "Supported", "Validated"):
                entry_at = _now()
                entry = {
                    "state": target_state, "from": cur_state,
                    "at": entry_at, "by": by,
                }
                new_history.append(entry)
                if self.use_json_insert:
                    conn.execute(f"""
                        UPDATE facts
                        SET epistemic_state = ?, updated_at = ?,
                            {bump}history = json_insert(history, '$[#]', json(?))
                        WHERE fact_id = ? AND epistemic_state = ?
                    """, (target_state, entry_at, json.dumps(entry),
                          new_fact_id, cur_state))
                else:
                    row = conn.execute(
                        "SELECT history FROM facts WHERE fact_id = ?",
                        (new_fact_id,),
                    ).fetchone()
                    hist = json.loads((row[0] if row else None) or "[]")
                    hist.append(entry)
                    conn.execute(f"""
                        UPDATE facts
                        SET epistemic_state = ?, updated_at = ?, {bump}history = ?
                        WHERE fact_id = ? AND epistemic_state = ?
                    """, (target_state, entry_at, json.dumps(hist),
                          new_fact_id, cur_state))
                cur_state = target_state

            # 6) The authoritative CAS guard: old fact → Deprecated, WHERE
            # still matches the exact snapshot TruthGate scored. rowcount==0
            # means the fact changed or vanished concurrently — roll back
            # everything written above (new insert + ladder) and report
            # concurrent_modification, never a partial success.
            old_deprecated_at = _now()
            old_history_entry = {
                "state": "Deprecated", "from": expected_old_state,
                "at": old_deprecated_at, "by": by,
            }
            if self.use_json_insert:
                cur = conn.execute(f"""
                    UPDATE facts
                    SET epistemic_state = ?, updated_at = ?,
                        {bump}history = json_insert(history, '$[#]', json(?))
                    WHERE fact_id = ? AND epistemic_state = ? AND updated_at = ?
                """, ("Deprecated", old_deprecated_at, json.dumps(old_history_entry),
                      old_id, expected_old_state, expected_old_updated_at))
                old_committed = cur.rowcount == 1
            else:
                row = conn.execute(
                    "SELECT history FROM facts "
                    "WHERE fact_id = ? AND epistemic_state = ? AND updated_at = ?",
                    (old_id, expected_old_state, expected_old_updated_at),
                ).fetchone()
                old_committed = False
                if row is not None:
                    hist = json.loads(row[0] or "[]")
                    hist.append(old_history_entry)
                    cur = conn.execute(f"""
                        UPDATE facts
                        SET epistemic_state = ?, updated_at = ?, {bump}history = ?
                        WHERE fact_id = ? AND epistemic_state = ? AND updated_at = ?
                    """, ("Deprecated", old_deprecated_at, json.dumps(hist),
                          old_id, expected_old_state, expected_old_updated_at))
                    old_committed = cur.rowcount == 1

            if not old_committed:
                # 10) Roll back the whole transaction explicitly — the new
                # fact's insert+ladder above must not survive a CAS miss on
                # the old fact. conn.commit() below is then a no-op (nothing
                # left pending); no exception needed for this expected race.
                conn.rollback()
                return SupersedeCasResult(
                    committed=False, reason="concurrent_modification",
                )

            # 7) + 8) Final integrity metadata/checksums — new fact at
            # Validated, old fact at Deprecated. Checksums are a function of
            # (claim, source, confidence, epistemic_state), so each needs
            # its own recompute for its final state.
            new_final_metadata = attach_integrity_metadata(
                json.loads(insert_record["metadata"]),
                claim=claim, source=source, confidence=confidence,
                epistemic_state="Validated",
            )
            conn.execute(
                "UPDATE facts SET metadata = ? WHERE fact_id = ?",
                (json.dumps(new_final_metadata), new_fact_id),
            )

            old_final_metadata = attach_integrity_metadata(
                dict(old_durable_snapshot.get("metadata") or {}),
                claim=old_durable_snapshot.get("claim", ""),
                source=old_durable_snapshot.get("source", "unknown"),
                confidence=float(old_durable_snapshot.get("confidence", 0.5)),
                epistemic_state="Deprecated",
            )
            conn.execute(
                "UPDATE facts SET metadata = ?, "
                "audit_subject_id = COALESCE(audit_subject_id, ?) WHERE fact_id = ?",
                (json.dumps(old_final_metadata), audit_subject_id_old_candidate, old_id),
            )

            # 9) FTS index for the new fact — best-effort secondary index,
            # same convention as store_fact()'s own FTS sync.
            try:
                from core.projection_apply import upsert_fts_row
                upsert_fts_row(conn, new_fact_id, claim, source)
            except sqlite3.OperationalError:
                pass  # FTS5 not available in this SQLite build

            # PR-C3: log strictly after both facts' final state is durably
            # written, still inside this same transaction — any failure
            # here rolls back BOTH the new fact's ladder and the old
            # fact's Deprecation together (same C1 atomicity guarantee as
            # every other wired path). new_fact_id's audit_subject_id was
            # just freshly inserted by this same transaction (no other
            # writer could have touched it — read-your-own-write is not
            # needed there); old_id's candidate goes through the same
            # Codex P2 read-your-own-write re-read as every other reused
            # chain_id, since old_durable_snapshot may be a stale caller
            # snapshot.
            real_old_audit_subject_id = conn.execute(
                "SELECT audit_subject_id FROM facts WHERE fact_id = ?", (old_id,)
            ).fetchone()[0]

            self._snapshot_before_change_in_transaction(
                conn,
                old_id,
                old_durable_snapshot,
                caused_by=f"memory.supersede_fact_cas:{by}",
                now_iso=old_deprecated_at,
            )

            actor_code = map_actor_code(by)
            new_chain = AuditChain(
                conn, chain_id=f"fact-transition:{audit_subject_id_new}", _skip_schema_check=True,
            )
            new_chain.log_in_transaction(
                event_type=EventType.FACT_CREATED,
                actor=actor_code,
                to_state="Validated",
                reason=REASON_CODE_CAS_TRANSITION,
            )
            old_chain = AuditChain(
                conn, chain_id=f"fact-transition:{real_old_audit_subject_id}", _skip_schema_check=True,
            )
            old_chain.log_in_transaction(
                event_type=EventType.FACT_DEPRECATED,
                actor=actor_code,
                from_state=expected_old_state,
                to_state="Deprecated",
                reason=REASON_CODE_CAS_TRANSITION,
            )

            new_final_record = {
                **insert_record,
                "epistemic_state": "Validated",
                "updated_at":      new_history[-1]["at"],
                "metadata":        new_final_metadata,
                "history":         new_history,
                "audit_subject_id": audit_subject_id_new,
            }
            old_final_record = {
                **copy.deepcopy(old_durable_snapshot),
                "epistemic_state": "Deprecated",
                "updated_at":      old_deprecated_at,
                "metadata":        old_final_metadata,
                "history":         [*old_durable_snapshot.get("history", []), old_history_entry],
                "audit_subject_id": real_old_audit_subject_id,
            }

        # 10) The durable transaction has committed; only process-local L0
        # publication remains.
        self._l0_put(new_fact_id, new_final_record)
        self._l0_put(old_id, old_final_record)
        return SupersedeCasResult(
            committed=True, reason="ok",
            new_record=new_final_record, old_record=old_final_record,
        )

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
        ТОЛЬКО если вердикт passed И последующий CAS-write реально закоммитился.

        Атомарность: если TruthGate отклоняет факт — никакая запись не
        вызывается вообще. Никакой мутации, никакой частичной записи в
        history, никакой audit-записи о несостоявшемся переходе.

        SECURITY (durable read, review finding on PR #6): и снимок для
        TruthGate, и CAS-токен читаются через _get_fact_durable() — НАПРЯМУЮ
        из L1 SQLite, в обход L0-кэша. store_fact()'s no-op upsert path может
        опубликовать в L0 свежий updated_at, не трогая саму строку в БД
        (идемпотентный повторный POST /facts) — если бы CAS-токен брался
        оттуда, легитимный промоушен мог бы получать перманентный 409. Решение
        с реальными последствиями для безопасности обязано читать источник
        истины (L1), не кэш.

        SECURITY (TOCTOU): между этим durable-чтением (снимок, который видит
        TruthGate) и финальной записью факт может измениться конкурентно —
        другой запрос делает POST /facts upsert (меняя confidence/source/
        metadata/evidence_refs) или другой переход (меняя epistemic_state).
        Оба случая ловятся ОДНИМ conditional UPDATE в _promote_to_validated_cas()
        — WHERE fact_id = ? AND epistemic_state = ? AND updated_at = ?, оба
        значения из этого самого снимка, без какого-либо промежуточного
        свежего чтения. Если WHERE не совпал — 0 строк, никакой мутации,
        result False; validate_and_promote() трактует это как
        concurrent_modification, НЕ как success (raньше игнорировавшийся bool
        от transition_esm() позволял вернуть passed=True даже когда переход
        физически не состоялся — например, факт удалили между TruthGate и
        записью; это исправлено — CAS-write result проверяется явно).

        ESM-легальность (I50) проверяется ЗДЕСЬ, против ИСХОДНОГО durable-
        снимка, до TruthGate.evaluate() и до какой-либо повторной проверки —
        прямой Observed→Validated обязан вернуть ValueError/400 независимо от
        силы confidence/evidence, и независимо от того, что произошло с
        фактом ПОСЛЕ этого снимка (конкурентные гонки после легального
        снимка всегда concurrent_modification/409, никогда 400 — см.
        _promote_to_validated_cas()).

        Returns:
            TruthGateVerdict. verdict.passed говорит, состоялся ли переход.
            reason == "not_found", если факт не существует на момент
            исходного durable-чтения (verdict.passed всегда False).
            reason == "concurrent_modification", если факт изменился
            (включая удаление) между снимком для TruthGate и записью —
            независимо от того, существовал ли факт в момент снимка.

        Не вызывает LLM. Не дублирует TruthGate policy — вся логика внутри
        core.truth_gate.TruthGate; эта функция только оркестрирует
        evaluate() → guarded write атомарно.
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

        fact = self._get_fact_durable(fact_id)
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

        # ESM-легальность ПЕРЕД TruthGate (см. docstring): нелегальный прыжок
        # (например, прямой Observed→Validated) всегда ValueError/400,
        # независимо от confidence/evidence — TruthGate не может "простить"
        # нелегальный переход, и слабый факт не должен получать 422 там,
        # где сильный факт получил бы 400.
        allowed = ESM_TRANSITIONS.get(current_state)
        if allowed is not None and "Validated" not in allowed:
            raise ValueError(
                f"validate_and_promote: переход '{current_state}' → 'Validated' "
                "недопустим"
            )

        # Снимок, на котором основан вердикт — CAS-токен для финальной записи.
        # updated_at NOT NULL в схеме facts — индексируем, а не .get(), чтобы
        # тип был str, а не str | None (для _promote_to_validated_cas ниже).
        expected_updated_at: str = fact["updated_at"]

        verdict = TruthGate(self).evaluate(fact, mode=mode, by=by)
        if not verdict.passed:
            return verdict

        # Мутация ТОЛЬКО после успешного вердикта, и ТОЛЬКО если guarded write
        # реально закоммитился против исходного снимка — иначе (факт изменился
        # или был удалён конкурентно) это concurrent_modification, не success.
        committed = self._promote_to_validated_cas(
            fact_id,
            expected_state=current_state,
            expected_updated_at=expected_updated_at,
            durable_snapshot=fact,
            by=by,
        )
        if not committed:
            return TruthGateVerdict(
                passed=False,
                fact_id=fact_id,
                reason="concurrent_modification",
                justification=(
                    f"Факт '{fact_id}' изменился (или был удалён) между "
                    "проверкой TruthGate и записью перехода — промоушен "
                    "отменён, повторите запрос."
                ),
                by=by,
                mode=mode,
                confidence=verdict.confidence,
                evidence_count=verdict.evidence_count,
            )
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

        PR-C1d (Issue #39, part D): раньше здесь не было ни CAS-guard'а, ни
        проверки rowcount — UPDATE ничем не ограничивался кроме fact_id, и
        метод всегда возвращал True, даже если факта не существовало или
        строку успела изменить другая запись. Теперь: CAS минимум по
        durable updated_at (WHERE fact_id = ? AND updated_at = ?); при
        rowcount == 0 (несуществующий факт ИЛИ конкурентная модификация)
        возвращается False, stale L0 инвалидируется, ничего не
        перезаписывается. VersionStore-снимок создаётся после успешного CAS,
        но внутри той же транзакции до commit; L0 публикуется только после
        commit. Поэтому отклонённая попытка не оставляет фантомной версии,
        а сбой version/audit evidence откатывает сам UPDATE.
        """
        from core.write_gate import ensure_writes_allowed
        ensure_writes_allowed()

        now = _now()
        t_ev_end  = t_event_valid_end or now
        t_ing_end = t_ingestion_end   or now

        # Codex-style review finding (PR-C3): idempotency (both ends already
        # set) MUST be decided from durable L1, never L0 alone.
        # - L0 clearing already-set ends (same updated_at) used to fall
        #   through to UPDATE + a duplicate fact_invalidated.
        # - L0 faking both ends set while L1 is still open falsely returned
        #   True without writing L1.
        # The CAS token still prefers L0's updated_at when present — that
        # preserves stale-view / concurrent-modification detection that
        # PR-C1d installed (tests poison L0.updated_at to force a miss).
        l0_cached = self._l0_get(fact_id)
        durable = self._get_fact_durable(fact_id)
        if durable is None:
            self._l0_del(fact_id)
            return False

        if durable.get("t_event_valid_end") and durable.get("t_ingestion_end"):
            self._l0_put(fact_id, durable)
            return True

        # Review finding (PR #42, Copilot): facts.updated_at is TEXT NOT
        # NULL — index directly rather than .get().
        if l0_cached is not None:
            expected_updated_at: str = l0_cached["updated_at"]
        else:
            expected_updated_at = durable["updated_at"]
        # Logging / post-commit L0 publish use durable field values
        # (epistemic_state, audit_subject_id, prior ends).
        cached = durable

        # PR-C3: invalidate_edge() gets the same tamper-evident AuditChain
        # event as the other lifecycle mutation paths — same C1 (atomic,
        # same transaction) + S2 (per-fact chain_id) design. This is a
        # CAS-guarded write (WHERE ... AND updated_at = ?) but never
        # changes epistemic_state, so it uses its own reason_code rather
        # than REASON_CODE_CAS_TRANSITION (which is reserved for genuine
        # ESM-state transitions).
        import uuid as _uuid

        from core.audit_chain import (
            ACTOR_CODE_INVALIDATE_EDGE,
            REASON_CODE_CAS_GUARDED_WRITE,
            AuditChain,
            EventType,
        )

        audit_subject_id = cached.get("audit_subject_id") or _uuid.uuid4().hex
        chain_id = f"fact-transition:{audit_subject_id}"
        with self._db() as ready_conn:
            AuditChain.verify_schema_ready(ready_conn, chain_id=chain_id)

        cas_miss = False
        real_audit_subject_id: str | None = None
        with self._db() as conn:
            # Also require at least one end still NULL so a concurrent
            # invalidate that already closed both ends cannot bump
            # updated_at / append a second fact_invalidated under a
            # matching CAS token race.
            cur = conn.execute("""
                UPDATE facts
                SET t_event_valid_end = COALESCE(t_event_valid_end, ?),
                    t_ingestion_end   = COALESCE(t_ingestion_end,   ?),
                    updated_at        = ?,
                    audit_subject_id  = COALESCE(audit_subject_id, ?)
                WHERE fact_id = ? AND updated_at = ?
                  AND (t_event_valid_end IS NULL OR t_ingestion_end IS NULL)
            """, (t_ev_end, t_ing_end, now, audit_subject_id, fact_id, expected_updated_at))
            if cur.rowcount == 0:
                # Do NOT call _get_fact_durable() here — it opens nested
                # _db() on the same re-entrant lock, closes this conn in
                # its finally, and the outer commit then crashes with
                # "Cannot operate on a closed database". Re-check after
                # this context exits.
                cas_miss = True
            else:
                # PR-C3 (same Codex P2 read-your-own-write lesson from PR-C2):
                # re-read the audit_subject_id that ACTUALLY won the COALESCE.
                real_audit_subject_id = conn.execute(
                    "SELECT audit_subject_id FROM facts WHERE fact_id = ?", (fact_id,)
                ).fetchone()[0]
                self._snapshot_before_change_in_transaction(
                    conn,
                    fact_id,
                    cached,
                    caused_by="memory.invalidate_edge",
                    now_iso=now,
                )
                chain = AuditChain(
                    conn, chain_id=f"fact-transition:{real_audit_subject_id}", _skip_schema_check=True,
                )
                chain.log_in_transaction(
                    event_type=EventType.FACT_INVALIDATED,
                    actor=ACTOR_CODE_INVALIDATE_EDGE,
                    to_state=cached.get("epistemic_state"),
                    reason=REASON_CODE_CAS_GUARDED_WRITE,
                )

        if cas_miss:
            self._l0_del(fact_id)
            # Another writer may have completed invalidate between our
            # durable read and this UPDATE — treat that as idempotent
            # success (no new audit event from us).
            again = self._get_fact_durable(fact_id)
            if again and again.get("t_event_valid_end") and again.get("t_ingestion_end"):
                self._l0_put(fact_id, again)
                return True
            return False

        new_cached = copy.deepcopy(cached)
        if not new_cached.get("t_event_valid_end"):
            new_cached["t_event_valid_end"] = t_ev_end
        if not new_cached.get("t_ingestion_end"):
            new_cached["t_ingestion_end"] = t_ing_end
        new_cached["updated_at"] = now
        new_cached["audit_subject_id"] = real_audit_subject_id
        self._l0_put(fact_id, new_cached)
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
        from core.write_gate import ensure_writes_allowed
        ensure_writes_allowed()

        if not facts:
            return {"stored": 0, "updated": 0, "drift": 0, "errors": 0}

        stats = {"stored": 0, "updated": 0, "drift": 0, "errors": 0}
        records_bump: list[dict] = []    # existing facts with real claim/confidence/ESM change
        records_nobump: list[dict] = []  # new facts + metadata-only updates to existing facts
        l0_pending: list[tuple] = []  # C2: (fact_id, l0_record) — в L0 ТОЛЬКО после commit L1
        audit_pending: list[dict] = []  # PR-C3: one entry per record that reaches the transaction
        seen_fact_ids: set[str] = set()

        now = _now()

        # PR-C3: store_facts_batch() gets the same tamper-evident AuditChain
        # wiring as store_fact()/store_fact_result() — same C1+S2 design.
        import uuid as _uuid

        from core.audit_chain import (
            ACTOR_CODE_STORE_FACTS_BATCH,
            REASON_CODE_DIRECT_WRITE,
            AuditChain,
            EventType,
        )

        for fact in facts:
            try:
                fact_id = fact.get("fact_id")
                if not fact_id:
                    raise ValueError("store_facts_batch: fact_id обязателен")
                if fact_id in seen_fact_ids:
                    raise ValueError(
                        f"store_facts_batch: duplicate fact_id '{fact_id}' in one "
                        "transaction is ambiguous for version/audit evidence"
                    )
                seen_fact_ids.add(fact_id)

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
                if not _raw_ct or _raw_ct == "UNKNOWN":
                    try:
                        from core.claim_classifier import classify_claim as _classify

                        _ct, _ot, _ = _classify(
                            new_claim,
                            fact.get("source", "unknown"),
                            explicit_claim_type=(
                                None
                                if _raw_ct in (None, "", "UNKNOWN")
                                else _raw_ct
                            ),
                            explicit_origin_type=(
                                None
                                if _raw_ot in (None, "", "UNKNOWN")
                                else _raw_ot
                            ),
                        )
                    except Exception:
                        _ct = normalize_claim_type(_raw_ct)
                        _ot = normalize_origin_type(_raw_ot)
                else:
                    _ct = normalize_claim_type(_raw_ct)
                    _ot = normalize_origin_type(_raw_ot)

                # Batch ingestion is not a privileged side door. The exact
                # WriteProtocolGate used by store_fact() is applied per
                # record before anything enters the shared transaction.
                from core.write_gate import admit_fact

                _wg_refs = metadata_dict.get("evidence_refs") or []
                _wg_ok, _wg_reason = admit_fact(
                    claim_type=_ct,
                    origin_type=_ot,
                    source=fact.get("source", "unknown"),
                    has_evidence=bool(_wg_refs),
                )
                if not _wg_ok:
                    raise ValueError(
                        f"WriteProtocolGate rejected '{fact_id}': {_wg_reason}"
                    )

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
                _needs_bump = False
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

                    # PR-C1b (Issue #37): триггер bump_fact_version требует,
                    # чтобы UPDATE, меняющий claim/confidence/epistemic_state,
                    # сам увеличил fact_version. Бампим только записи, где
                    # что-то из этих трёх полей действительно меняется —
                    # metadata-only обновления в batch не должны искусственно
                    # увеличивать fact_version.
                    #
                    # PR-C1b review fix: confidence — EXACT сравнение (`!=`),
                    # не epsilon. Триггер сравнивает `OLD.confidence !=
                    # NEW.confidence` точно; epsilon здесь мог направить
                    # запись с суб-эпсилон, но реально ненулевым изменением
                    # confidence в records_nobump — SQL всё равно пишет
                    # confidence = excluded.confidence, OLD != NEW технически
                    # истинно для триггера, и необампленный UPDATE падает.
                    _needs_bump = (
                        existing["claim"] != new_claim
                        or existing["confidence"] != confidence
                        or (record["epistemic_state"] == "Contradicted"
                            and existing["epistemic_state"] != "Contradicted")
                    )
                else:
                    stats["stored"] += 1

                # PR-C3: audit_subject_id reused from the existing row if
                # already assigned (any prior mutation path), else minted
                # lazily. Set on `record` so it flows through the INSERT
                # below via the same COALESCE convention as store_fact().
                audit_subject_id = (
                    (existing.get("audit_subject_id") if existing else None)
                    or _uuid.uuid4().hex
                )
                record["audit_subject_id"] = audit_subject_id
                if existing is None:
                    _event_type = EventType.FACT_CREATED
                elif record["epistemic_state"] == "Contradicted" and existing["epistemic_state"] != "Contradicted":
                    _event_type = EventType.FACT_CONTRADICTED
                else:
                    _event_type = EventType.FACT_UPDATED
                audit_pending.append({
                    "fact_id": fact_id,
                    "chain_id_candidate": f"fact-transition:{audit_subject_id}",
                    "event_type": _event_type,
                    "from_state": existing["epistemic_state"] if (
                        existing is not None and _event_type == EventType.FACT_CONTRADICTED
                    ) else None,
                    "to_state": record["epistemic_state"],
                    # A batch may create and update different IDs together.
                    # Only an update has a pre-image to close in VersionStore.
                    "preimage": copy.deepcopy(existing) if existing else None,
                })

                # C2 SPLIT-BRAIN FIX: L0 НЕ пишем здесь — только после commit L1 (ниже).
                l0_record = {**record,
                             "metadata": metadata_dict,
                             "history":  json.loads(record["history"])}
                l0_pending.append((fact_id, l0_record))
                if _needs_bump:
                    records_bump.append(record)
                else:
                    records_nobump.append(record)

            except Exception as exc:
                logger.warning("store_facts_batch: пропущен факт '%s': %s",
                               fact.get("fact_id", "?"), exc)
                stats["errors"] += 1

        if not records_bump and not records_nobump:
            return stats

        # PR-C3: readiness check for every candidate chain_id, on a SEPARATE
        # connection/transaction, BEFORE the batch's own canonical
        # transaction opens below — same requirement as update_state()/
        # store_fact(). Idempotent and cheap to repeat per record.
        for _pending in audit_pending:
            with self._db() as ready_conn:
                AuditChain.verify_schema_ready(ready_conn, chain_id=_pending["chain_id_candidate"])

        # Один SQLite transaction на весь batch. PR-C1b (Issue #37): записи,
        # реально меняющие claim/confidence/epistemic_state, идут через SQL
        # с bump fact_version + слитым drift-sync (records_bump) — раньше
        # drift синхронизировался ОТДЕЛЬНЫМ UPDATE, что при наличии колонки
        # fact_version дало бы двойной bump на одну логическую запись, как и
        # в store_fact() (см. Issue #37). Новые факты и чисто metadata-only
        # обновления существующих идут через нетронутый SQL (records_nobump).
        with self._db() as conn:
            if records_nobump:
                conn.executemany("""
                    INSERT INTO facts
                        (fact_id, claim, source, confidence, epistemic_state,
                         created_at, updated_at, metadata, history,
                         t_event_valid_start, t_event_valid_end,
                         t_ingestion_start,   t_ingestion_end,
                         claim_type, origin_type, memory_type,
                         audit_subject_id)
                    VALUES
                        (:fact_id, :claim, :source, :confidence, :epistemic_state,
                         :created_at, :updated_at, :metadata, :history,
                         :t_event_valid_start, :t_event_valid_end,
                         :t_ingestion_start,   :t_ingestion_end,
                         :claim_type, :origin_type, :memory_type,
                         :audit_subject_id)
                    ON CONFLICT(fact_id) DO UPDATE SET
                        claim      = excluded.claim,
                        source     = excluded.source,
                        confidence = excluded.confidence,
                        updated_at = excluded.updated_at,
                        metadata   = excluded.metadata,
                        audit_subject_id = COALESCE(audit_subject_id, excluded.audit_subject_id)
                """, records_nobump)

            if records_bump:
                _bump = self._fact_version_bump_sql(conn)
                conn.executemany(f"""
                    INSERT INTO facts
                        (fact_id, claim, source, confidence, epistemic_state,
                         created_at, updated_at, metadata, history,
                         t_event_valid_start, t_event_valid_end,
                         t_ingestion_start,   t_ingestion_end,
                         claim_type, origin_type, memory_type,
                         audit_subject_id)
                    VALUES
                        (:fact_id, :claim, :source, :confidence, :epistemic_state,
                         :created_at, :updated_at, :metadata, :history,
                         :t_event_valid_start, :t_event_valid_end,
                         :t_ingestion_start,   :t_ingestion_end,
                         :claim_type, :origin_type, :memory_type,
                         :audit_subject_id)
                    ON CONFLICT(fact_id) DO UPDATE SET
                        {_bump}claim      = excluded.claim,
                        source           = excluded.source,
                        confidence       = excluded.confidence,
                        epistemic_state  = excluded.epistemic_state,
                        history          = excluded.history,
                        updated_at       = excluded.updated_at,
                        metadata         = excluded.metadata,
                        audit_subject_id = COALESCE(audit_subject_id, excluded.audit_subject_id)
                """, records_bump)

            # PR-C3: log one AuditChain event per record that reached this
            # transaction, strictly after both executemany() calls succeed,
            # still inside the same transaction/connection — any failure
            # here rolls back the WHOLE batch (all facts, not just this
            # one), same C1 atomicity guarantee as store_fact(). Re-read
            # each fact's real (COALESCE-resolved) audit_subject_id rather
            # than trusting the locally-computed candidate (same Codex P2
            # read-your-own-write lesson from PR-C2).
            real_subject_ids: dict[str, str] = {}
            for _pending in audit_pending:
                _fid = _pending["fact_id"]
                real_subject_id = conn.execute(
                    "SELECT audit_subject_id FROM facts WHERE fact_id = ?", (_fid,)
                ).fetchone()[0]
                real_subject_ids[_fid] = real_subject_id
                if _pending["preimage"] is not None:
                    self._snapshot_before_change_in_transaction(
                        conn,
                        _fid,
                        _pending["preimage"],
                        caused_by="memory.store_facts_batch",
                        now_iso=now,
                    )
                chain = AuditChain(
                    conn, chain_id=f"fact-transition:{real_subject_id}", _skip_schema_check=True,
                )
                chain.log_in_transaction(
                    event_type=_pending["event_type"],
                    actor=ACTOR_CODE_STORE_FACTS_BATCH,
                    from_state=_pending["from_state"],
                    to_state=_pending["to_state"],
                    reason=REASON_CODE_DIRECT_WRITE,
                )

        # C2 SPLIT-BRAIN FIX (audit): L0 пишем ТОЛЬКО ПОСЛЕ успешного commit L1.
        # Раньше _l0_put шёл в цикле ДО executemany → при откате батча факты
        # оставались в L0, которых нет в L1 (нарушение инварианта D4, как в store_fact).
        # Issue #50: every updated record's pre-image was appended inside
        # the same transaction above. New records correctly have no
        # predecessor snapshot.
        for _fid, _l0_record in l0_pending:
            _l0_record["audit_subject_id"] = real_subject_ids.get(_fid, _l0_record.get("audit_subject_id"))
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


def get_store() -> SQLiteGraphStore:
    """
    Предпочтительный accessor стора: core.app.get_app()'s VelantrimApp DI,
    с fallback на _GLOBAL_STORE.

    По умолчанию оба указывают на ОДИН и тот же файл: core.app.FeatureConfig.
    from_env() берёт sqlite_graph_path из этого же SQLITE_PATH (см. fix в
    core/feature_config.py), поэтому get_app()'s singleton app.store и
    _GLOBAL_STORE больше не могут молча разойтись на две разные БД. Явно
    сконструированный VelantrimApp (тесты, per-instance изоляция) может
    по-прежнему указывать на свой собственный путь — это не баг, это
    предназначение DI.
    """
    try:
        from core.app import get_app

        app = get_app()
        if "store" in app._lazy or "store" in app._components:
            return app.store
    except Exception:
        pass
    return _GLOBAL_STORE


def store_fact(fact: dict) -> bool:
    """Обёртка над SQLiteGraphStore.store_fact(). Возвращает True если новый INSERT."""
    return _GLOBAL_STORE.store_fact(fact)

def store_fact_result(fact: dict):
    """PR-C1: обёртка над SQLiteGraphStore.store_fact_result() — не бросает
    исключений, возвращает core.write_result.WriteResult."""
    return _GLOBAL_STORE.store_fact_result(fact)

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

def get_fact_durable(fact_id: str) -> dict | None:
    """Обёртка над SQLiteGraphStore.get_fact_durable() — durable read, в обход L0."""
    return _GLOBAL_STORE.get_fact_durable(fact_id)

def supersede_fact_cas(
    old_id: str,
    new_fact_id: str,
    new_record_seed: dict[str, Any],
    expected_old_state: str,
    expected_old_updated_at: str,
    old_durable_snapshot: dict[str, Any],
    by: str = "truth_maintenance.supersede",
) -> SupersedeCasResult:
    """Обёртка над SQLiteGraphStore.supersede_fact_cas() — см. класс для деталей."""
    return _GLOBAL_STORE.supersede_fact_cas(
        old_id, new_fact_id, new_record_seed,
        expected_old_state, expected_old_updated_at,
        old_durable_snapshot, by=by,
    )

def get_all_facts(
    epistemic_state: str | None = None,
    domain: str | None = None,
) -> list[dict]:
    from core.domain_tags import normalize_domain

    dom = normalize_domain(domain) if domain else None
    if dom == "general":
        dom = None
    return _GLOBAL_STORE.get_all_facts(epistemic_state, domain=dom)


def search(query: str, top_k: int = 5, domain: str | None = None) -> list[dict]:
    """Обёртка над SQLiteGraphStore.search() для search_facts_for_recall().

    Pre-existing bug fix (найден Ruff F821): раньше search_facts_for_recall()
    ссылался на неопределённое имя `search` и падал бы NameError при любом
    вызове. SQLiteGraphStore.search() не поддерживает domain-фильтрацию —
    параметр принимается для совместимости сигнатуры, но не применяется.
    """
    return _GLOBAL_STORE.search(query, limit=top_k)

def store_raw_text(text: str, source: str | None = None, source_type: str = "user_input") -> str:
    """TASK-09: Сохранить оригинальный текст в L0 Raw Memory. Возвращает raw_id."""
    return _GLOBAL_STORE.store_raw_text(text, source=source, source_type=source_type)

def link_raw_to_fact(raw_id: str, fact_id: str, derivation_type: str = "direct") -> bool:
    """TASK-09: Связать derived факт с оригинальным raw_id в провенанс-таблице.
    PR-C1: возвращает False (без записи) если raw_id или fact_id не существуют."""
    return _GLOBAL_STORE.link_raw_to_fact(raw_id, fact_id, derivation_type)

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


def erase_fact_dependents_atomic(fact_id: str) -> dict[str, Any]:
    """GDPR Art. 17: same-DB atomic erasure with an honest per-table result.

    See SQLiteGraphStore.erase_fact_dependents_atomic() — the primitive used
    by core.erasure_coordinator, the single enforced erasure entrypoint.
    """
    return _GLOBAL_STORE.erase_fact_dependents_atomic(fact_id)


def same_db_dependents_present(fact_id: str) -> bool:
    """Read-only residual check — see SQLiteGraphStore.same_db_dependents_present()."""
    return _GLOBAL_STORE.same_db_dependents_present(fact_id)


def list_fact_ids_by_user_durable(user_id: str) -> list[dict[str, Any]]:
    """GDPR Art. 17 batch erasure: durable snapshot selection — see
    SQLiteGraphStore.list_fact_ids_by_user_durable()."""
    return _GLOBAL_STORE.list_fact_ids_by_user_durable(user_id)


def write_tombstone(fact_id: str, *, reason: str, actor: str,
                    content_hash: str | None, job_id: str | None = None) -> None:
    _GLOBAL_STORE.write_tombstone(
        fact_id, reason=reason, actor=actor, content_hash=content_hash, job_id=job_id)


def get_tombstone(fact_id: str) -> dict | None:
    return _GLOBAL_STORE.get_tombstone(fact_id)


def get_tombstone_for_job(fact_id: str, job_id: str | None) -> dict | None:
    return _GLOBAL_STORE.get_tombstone_for_job(fact_id, job_id)


def get_tombstones() -> list[dict]:
    return _GLOBAL_STORE.get_tombstones()


def set_restricted(fact_id: str, restricted: bool) -> bool:
    """GDPR Art. 18: mark/unmark a fact's processing restriction."""
    return _GLOBAL_STORE.set_restricted(fact_id, restricted)




# ── Recall Policy функции (делегируем в recall_policy.py) ─────────


def get_facts_for_recall(
    epistemic_state: str | None = None,
    domain: str | None = None,
) -> list[dict]:
    """
    Получить факты для recall с применением политики фильтрации.
    
    Делегирует фильтрацию в core.recall_policy.
    """
    return _get_facts_for_recall(get_all_facts, epistemic_state=epistemic_state, domain=domain)


def list_facts_for_recall(
    epistemic_state: str | None = None,
    domain: str | None = None,
) -> list[dict]:
    """
    Алиас для get_facts_for_recall для совместимости.
    """
    return _list_facts_for_recall(get_all_facts, epistemic_state=epistemic_state, domain=domain)


def search_facts_for_recall(
    query: str,
    top_k: int = 5,
    domain: str | None = None,
) -> list[dict]:
    """
    Поиск фактов для recall с применением политики фильтрации.
    
    Делегирует фильтрацию в core.recall_policy.
    """
    return _search_facts_for_recall(search, query=query, top_k=top_k, domain=domain)
