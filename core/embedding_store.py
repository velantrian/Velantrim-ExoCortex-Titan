"""
🔢 core/embedding_store.py — Persistent Embedding Store (из Crystal в V8.7)
===========================================================================

Хранит эмбеддинги фактов на диске → не пересчитывать при каждом рестарте.
Актуально при >5 000 фактов (холодный старт retrieval = 30-60 сек без кэша).

Использование:
    store = EmbeddingStore(db_path="./data/velantrim_house.db")
    store.ensure_table()                     # один раз при старте

    # При ingest факта:
    store.store(fact_id, embedding_numpy, model_name="paraphrase-multilingual-MiniLM-L12-v2")

    # При retrieval:
    emb = store.load(fact_id)                # numpy array или None

    # Массовая загрузка:
    all_embs = store.load_all(model_name)    # dict[fact_id, ndarray]

    # Инвалидация при смене модели:
    store.invalidate_model("старая-модель")

Архитектура:
    BLOB-хранение: numpy.ndarray.tobytes() → BLOB (быстрее JSON в 10x).
    Одна таблица на все модели (model_name — часть PK).
    Нет внешних зависимостей кроме numpy (уже есть в проекте).
"""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import numpy as np

logger = logging.getLogger("velantrim.embedding_store")

EXOCORTEX_DB = os.getenv("SQLITE_GRAPH_PATH", "./data/exocortex_graph.db")


class EmbeddingStore:
    """
    Персистентное хранилище эмбеддингов в exocortex_graph.db.

    Таблица: gs_vectors (node_id, model_name, embedding_blob, dims, computed_at).
    """

    def __init__(self, db_path: str = EXOCORTEX_DB):
        self._db_path = db_path

    def ensure_table(self) -> None:
        """Создать таблицу gs_vectors если её нет (идемпотентно)."""
        try:
            db_dir = os.path.dirname(self._db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gs_vectors (
                    node_id      TEXT NOT NULL,
                    model_name   TEXT NOT NULL,
                    embedding_blob BLOB NOT NULL,
                    dims         INTEGER NOT NULL,
                    computed_at  REAL NOT NULL,
                    content_hash TEXT,
                    PRIMARY KEY (node_id, model_name)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_gs_vectors_model
                ON gs_vectors(model_name, computed_at)
            """)
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning("EmbeddingStore.ensure_table: %s", exc)

    # ── Запись ──────────────────────────────────────────────────────────────

    def store(
        self,
        node_id: str,
        embedding: np.ndarray,
        *,
        model_name: str = "default",
        content_hash: str | None = None,
    ) -> bool:
        """
        Сохранить эмбеддинг.

        Args:
            node_id: fact_id или entity_id
            embedding: numpy-вектор (1D, float32)
            model_name: идентификатор модели (для инвалидации при смене)
            content_hash: опциональный хеш контента (для детекта изменений)

        Returns:
            True если успешно, False при ошибке
        """
        try:
            blob = embedding.astype(np.float32).tobytes()
            dims = embedding.shape[0]
            now = datetime.now(timezone.utc).timestamp()

            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                """INSERT OR REPLACE INTO gs_vectors
                   (node_id, model_name, embedding_blob, dims, computed_at, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (node_id, model_name, blob, dims, now, content_hash),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as exc:
            logger.error("EmbeddingStore.store(%s): %s", node_id, exc)
            return False

    def store_batch(
        self,
        items: list[tuple[str, np.ndarray]],
        *,
        model_name: str = "default",
    ) -> int:
        """
        Пакетное сохранение эмбеддингов. Возвращает число сохранённых.

        Args:
            items: список (node_id, embedding_ndarray)
            model_name: модель
        """
        if not items:
            return 0

        count = 0
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            now = datetime.now(timezone.utc).timestamp()

            for node_id, emb in items:
                blob = emb.astype(np.float32).tobytes()
                dims = emb.shape[0]
                try:
                    conn.execute(
                        """INSERT OR REPLACE INTO gs_vectors
                           (node_id, model_name, embedding_blob, dims, computed_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (node_id, model_name, blob, dims, now),
                    )
                    count += 1
                except Exception:
                    continue

            conn.commit()
            conn.close()
        except Exception as exc:
            logger.error("EmbeddingStore.store_batch: %s", exc)
        return count

    # ── Чтение ──────────────────────────────────────────────────────────────

    def load(self, node_id: str, model_name: str = "default") -> Optional[np.ndarray]:
        """
        Загрузить эмбеддинг одного факта.
        Возвращает numpy-вектор или None.
        """
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            row = conn.execute(
                "SELECT embedding_blob, dims FROM gs_vectors WHERE node_id = ? AND model_name = ?",
                (node_id, model_name),
            ).fetchone()
            conn.close()
            if row is None:
                return None
            blob, dims = row
            return np.frombuffer(blob, dtype=np.float32).reshape(dims)
        except Exception as exc:
            logger.debug("EmbeddingStore.load(%s): %s", node_id, exc)
            return None

    def load_all(self, model_name: str = "default") -> Dict[str, np.ndarray]:
        """
        Загрузить ВСЕ эмбеддинги для модели.
        Возвращает dict[fact_id, ndarray].
        """
        result: Dict[str, np.ndarray] = {}
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            rows = conn.execute(
                "SELECT node_id, embedding_blob, dims FROM gs_vectors WHERE model_name = ?",
                (model_name,),
            ).fetchall()
            conn.close()
            for node_id, blob, dims in rows:
                try:
                    result[node_id] = np.frombuffer(blob, dtype=np.float32).reshape(dims)
                except Exception:
                    continue
        except Exception as exc:
            logger.error("EmbeddingStore.load_all: %s", exc)
        return result

    def load_batch(
        self, node_ids: list[str], model_name: str = "default"
    ) -> Dict[str, np.ndarray]:
        """Загрузить эмбеддинги для списка фактов."""
        if not node_ids:
            return {}

        result: Dict[str, np.ndarray] = {}
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            placeholders = ", ".join("?" for _ in node_ids)
            rows = conn.execute(
                f"SELECT node_id, embedding_blob, dims FROM gs_vectors "
                f"WHERE node_id IN ({placeholders}) AND model_name = ?",
                (*node_ids, model_name),
            ).fetchall()
            conn.close()
            for node_id, blob, dims in rows:
                try:
                    result[node_id] = np.frombuffer(blob, dtype=np.float32).reshape(dims)
                except Exception:
                    continue
        except Exception as exc:
            logger.error("EmbeddingStore.load_batch: %s", exc)
        return result

    # ── Управление ──────────────────────────────────────────────────────────

    def invalidate_model(self, model_name: str) -> int:
        """
        Удалить все эмбеддинги для модели (при смене embedding-модели).
        Возвращает число удалённых записей.
        """
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            cur = conn.execute(
                "DELETE FROM gs_vectors WHERE model_name = ?",
                (model_name,),
            )
            conn.commit()
            conn.close()
            logger.info("Invalidated %d embeddings for model %s", cur.rowcount, model_name)
            return cur.rowcount
        except Exception as exc:
            logger.error("EmbeddingStore.invalidate_model: %s", exc)
            return 0

    def invalidate_node(self, node_id: str) -> bool:
        """Удалить эмбеддинг конкретного факта (при изменении claim)."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("DELETE FROM gs_vectors WHERE node_id = ?", (node_id,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def is_cached(self, node_id: str, model_name: str = "default") -> bool:
        """Проверить, есть ли эмбеддинг в кэше."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            row = conn.execute(
                "SELECT 1 FROM gs_vectors WHERE node_id = ? AND model_name = ?",
                (node_id, model_name),
            ).fetchone()
            conn.close()
            return row is not None
        except Exception:
            return False

    def stats(self) -> Dict[str, Any]:
        """Статистика хранилища эмбеддингов."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            total = conn.execute("SELECT COUNT(*) FROM gs_vectors").fetchone()[0]
            by_model = {}
            for row in conn.execute(
                "SELECT model_name, COUNT(*), AVG(dims) FROM gs_vectors GROUP BY model_name"
            ):
                by_model[row[0]] = {"count": row[1], "avg_dims": round(row[2], 1) if row[2] else 0}
            conn.close()
            return {"total_embeddings": total, "by_model": by_model}
        except Exception:
            return {"total_embeddings": 0, "by_model": {}}


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_store: Optional[EmbeddingStore] = None


def get_embedding_store() -> EmbeddingStore:
    global _store
    if _store is None:
        _store = EmbeddingStore()
        _store.ensure_table()
    return _store


__all__ = [
    "EmbeddingStore",
    "get_embedding_store",
]
