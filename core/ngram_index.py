# core/ngram_index.py
# Velantrim ExoCortex — NGram L0 Pre-Filter
# v1.1.0
#
# Назначение: мгновенное сужение кандидатов ПЕРЕД дорогим BM25/vector поиском.
# Принцип Cursor: «Narrow candidates → Validate».
#
# AUDIT-FIX v8.4.0: NGRAM_DB_PATH читается из VELANTRIM_NGRAM_DB env-переменной,
# та же что использует server.py. До v8.4.0 module-level singleton и server
# использовали разные пути → pipeline индексировал в одну БД, server искал
# в другой → NGramIndex выглядел как "не работает".
#
# Проблема которую решает:
#   pipeline.py сейчас делает BM25 Okapi по всей DATABASE — O(N) retrieval.
#   На 5 фактах это нормально. На 10 000+ — катастрофа (LIMITATIONS.md P-1).
#   NGramIndex сужает кандидатов с N до limit=50 за константное время FTS5.
#
# Технология:
#   SQLite FTS5 с tokenize='trigram' — встроено в SQLite, никаких зависимостей.
#   Trigram: строка "hello" → {"hel", "ell", "llo"}.
#   MATCH по триграммам работает через FTS5 индекс → O(log N) вместо O(N).
#
# Интеграция в pipeline.py (Sprint 2a):
#   # Шаг 0 — перед retrieve():
#   candidates = ngram_index.query(query, limit=50)
#   results = retrieve(query, candidates=candidates)  # поиск только в кандидатах
#
# Источник идеи: HYPERIA Гиперия 5.0 §NGram Index Engine (Март 2026).
# Инвариант I99: NGramIndex не хранит содержимое фактов — только fact_id и text.
#               Запись в NGramIndex ≠ запись в граф. Graph = Truth сохраняется.

import logging
import os
import sqlite3

logger = logging.getLogger(__name__)

# AUDIT-FIX v8.4.0: читаем тот же env что и server.py
NGRAM_DB_PATH = os.getenv("VELANTRIM_NGRAM_DB", "./data/velantrim_ngram.db")


def _fts5_available(conn: sqlite3.Connection) -> bool:
    """Проверяет доступность FTS5 + trigram tokenizer в данной сборке SQLite."""
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE _fts5_check USING fts5(x, tokenize='trigram')"
        )
        conn.execute("DROP TABLE _fts5_check")
        return True
    except sqlite3.OperationalError:
        return False


class NGramIndex:
    """
    L0 Pre-Filter: SQLite FTS5 с trigram tokenizer.

    Мгновенно находит кандидатов по текстовому совпадению до BM25/vector.
    Если FTS5 недоступен — graceful degradation: query() возвращает [],
    pipeline делает fallback на полный поиск (поведение как раньше).

    Инвариант I99: хранит только (doc_id, content) — не ESM-состояние,
    не confidence, не history. Это вспомогательный индекс, не источник истины.
    """

    def __init__(self, db_path: str = NGRAM_DB_PATH) -> None:
        self.db_path = db_path
        self._available = False
        self._init_db()

    def _init_db(self) -> None:
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        try:
            # WAL для concurrent read/write
            conn.execute("PRAGMA journal_mode=WAL")

            if not _fts5_available(conn):
                logger.warning(
                    "NGramIndex: FTS5 trigram недоступен в данной сборке SQLite "
                    "(%s). query() будет возвращать [] → pipeline fallback на полный "
                    "поиск. Обновите SQLite >= 3.35.0 для использования NGram.",
                    sqlite3.sqlite_version,
                )
                return

            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS ngram_index
                USING fts5(
                    doc_id   UNINDEXED,
                    content,
                    tokenize = 'trigram'
                )
            """)
            conn.commit()
            self._available = True
            logger.debug(
                "NGramIndex: инициализирован (SQLite %s, FTS5 trigram)",
                sqlite3.sqlite_version,
            )
        finally:
            conn.close()

    # ── Запись ──────────────────────────────────────────────────────────────

    def index(self, doc_id: str, content: str) -> None:
        """
        Добавить или обновить факт в индексе.
        Вызывать после store_fact() — но только когда fact попадает в БД.
        Идемпотентен: повторный index() обновляет content.

        I99: не пишет в L3 граф. Graph = Truth не нарушается.
        """
        if not self._available:
            return
        if not doc_id or not content:
            return
        conn = sqlite3.connect(self.db_path)
        try:
            # FTS5 не поддерживает ON CONFLICT — сначала удаляем старую запись
            conn.execute(
                "DELETE FROM ngram_index WHERE doc_id = ?", (doc_id,)
            )
            conn.execute(
                "INSERT INTO ngram_index(doc_id, content) VALUES (?, ?)",
                (doc_id, content),
            )
            conn.commit()
        finally:
            conn.close()

    def remove(self, doc_id: str) -> None:
        """Удалить факт из индекса (при Collapsed/Deprecated)."""
        if not self._available:
            return
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "DELETE FROM ngram_index WHERE doc_id = ?", (doc_id,)
            )
            conn.commit()
        finally:
            conn.close()

    # ── Запрос ──────────────────────────────────────────────────────────────

    def query(self, text: str, limit: int = 50) -> list[str]:
        """
        Вернуть до limit кандидатов (fact_id) за константное время.

        Если FTS5 недоступен или текст пустой → возвращает [].
        Pipeline должен делать fallback на полный поиск при пустом списке.

        Принцип: «Narrow → Validate». Этот метод только сужает,
        финальный ранкинг — задача BM25/vector в retrieve().
        """
        if not self._available or not text or not text.strip():
            return []
        conn = sqlite3.connect(self.db_path)
        try:
            # FTS5 MATCH с trigram: ищет документы содержащие триграммы из text
            rows = conn.execute(
                "SELECT doc_id FROM ngram_index WHERE content MATCH ? LIMIT ?",
                (text.strip(), limit),
            ).fetchall()
            return [r[0] for r in rows]
        except sqlite3.OperationalError as e:
            # Graceful degradation — лучше вернуть пустой список чем упасть
            logger.warning("NGramIndex.query error: %s — fallback to full search", e)
            return []
        finally:
            conn.close()

    # ── Служебные ───────────────────────────────────────────────────────────

    def count(self) -> int:
        """Количество документов в индексе."""
        if not self._available:
            return 0
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT count(*) FROM ngram_index"
            ).fetchone()
            return row[0] if row else 0
        finally:
            conn.close()

    def rebuild(self, facts: list[dict]) -> int:
        """
        Полная перестройка индекса из списка фактов.
        Используется при первом запуске или после GC.

        facts: список dict с полями 'fact_id' и 'claim'.
        Возвращает количество проиндексированных фактов.
        """
        if not self._available:
            return 0
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("DELETE FROM ngram_index")
            indexed = 0
            for fact in facts:
                fid = fact.get("fact_id")
                claim = fact.get("claim", "")
                if fid and claim:
                    conn.execute(
                        "INSERT INTO ngram_index(doc_id, content) VALUES (?, ?)",
                        (fid, claim),
                    )
                    indexed += 1
            conn.commit()
            logger.info("NGramIndex.rebuild: %d фактов проиндексировано", indexed)
            return indexed
        finally:
            conn.close()

    @property
    def available(self) -> bool:
        """True если FTS5 trigram доступен в текущей сборке SQLite."""
        return self._available


# ── Глобальный синглтон (аналогично _GLOBAL_STORE в memory.py) ───────────────
# AUDIT-FIX v8.4.0: добавлен set_global_ngram() для DI из server.py.
# До v8.4.0 server.py создавал свой _ngram, а pipeline писал через
# ngram_index_fact() в этот module-level singleton → split на две БД.
# Теперь server при старте может вызвать set_global_ngram(server_ngram),
# и pipeline будет писать в ту же БД, что использует server для чтения.
# TODO Sprint 2c: DI через конструктор pipeline, удалить синглтон.
_GLOBAL_NGRAM = NGramIndex(NGRAM_DB_PATH)


def set_global_ngram(ngram: NGramIndex) -> None:
    """
    Заменить глобальный NGramIndex (для DI из server.py).
    Используй при старте сервера если хочешь специальный путь к БД.
    """
    global _GLOBAL_NGRAM
    _GLOBAL_NGRAM = ngram
    logger.info("NGramIndex global instance replaced (db=%s)", ngram.db_path)


def get_global_ngram() -> NGramIndex:
    """Получить текущий глобальный NGramIndex."""
    return _GLOBAL_NGRAM


def ngram_query(text: str, limit: int = 50) -> list[str]:
    """Быстрый поиск кандидатов через глобальный NGramIndex."""
    return _GLOBAL_NGRAM.query(text, limit)


def ngram_index_fact(fact_id: str, content: str) -> None:
    """Проиндексировать факт в глобальном NGramIndex."""
    _GLOBAL_NGRAM.index(fact_id, content)


def ngram_remove_fact(fact_id: str) -> None:
    """Удалить факт из глобального NGramIndex."""
    _GLOBAL_NGRAM.remove(fact_id)
