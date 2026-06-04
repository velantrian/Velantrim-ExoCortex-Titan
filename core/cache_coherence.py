"""
💾 core/cache_coherence.py — Cache Coherence L0/L1 (A4)
=========================================================
Защита от split-brain между RAM-кэшем (L0) и SQLite (L1).

Добавляет к каждому факту:
  fact_version:  монотонно растёт при каждом изменении
  content_hash:  SHA256(claim + confidence + epistemic_state)

L0 хранит не только факт, но и version/hash.
При чтении критичных фактов проверяем версию.
При rollback L1 — инвалидируем L0.

Sprint 1a — Этап A4
"""
from __future__ import annotations

import hashlib
import threading


def compute_content_hash(
    claim:           str,
    confidence:      float,
    epistemic_state: str,
) -> str:
    """
    Вычисляет content_hash факта.
    SHA256(claim + confidence + epistemic_state)
    """
    content = f"{claim}|{confidence:.6f}|{epistemic_state}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:32]


# ── CoherentCache (L0) ────────────────────────────────────────────────────────

class CoherentCache:
    """
    LRU-подобный кэш с version/hash проверкой.

    Заменяет простой dict-кэш в memory.py.
    Гарантирует что L0 не отдаёт устаревшие факты без предупреждения.
    """

    def __init__(self, max_size: int = 1000) -> None:
        self._store: dict[str, dict] = {}   # fact_id → {data, version, hash}
        self._lock = threading.RLock()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._stale_detected = 0

    def get(
        self,
        fact_id:         str,
        expected_version: int | None = None,
        expected_hash:   str | None = None,
    ) -> dict | None:
        """
        Получить факт из кэша.

        Если expected_version или expected_hash указаны —
        проверяем актуальность. При несоответствии возвращаем None
        (заставляем перечитать из L1).
        """
        with self._lock:
            entry = self._store.get(fact_id)
            if entry is None:
                self._misses += 1
                return None

            # Проверка версии
            if expected_version is not None:
                if entry.get("version", 0) < expected_version:
                    self._stale_detected += 1
                    del self._store[fact_id]
                    return None

            # Проверка хэша
            if expected_hash is not None:
                if entry.get("content_hash") != expected_hash:
                    self._stale_detected += 1
                    del self._store[fact_id]
                    return None

            self._hits += 1
            return entry["data"]

    def set(
        self,
        fact_id:      str,
        data:         dict,
        version:      int = 1,
        content_hash: str | None = None,
    ) -> None:
        """Записать факт в кэш с метаданными версии."""
        with self._lock:
            # Простой eviction при переполнении — удаляем первый ключ
            if len(self._store) >= self._max_size and fact_id not in self._store:
                oldest = next(iter(self._store))
                del self._store[oldest]

            # Вычисляем хэш если не передан
            if content_hash is None and data:
                content_hash = compute_content_hash(
                    claim=data.get("claim", ""),
                    confidence=float(data.get("confidence", 0.0)),
                    epistemic_state=data.get("epistemic_state", "Observed"),
                )

            self._store[fact_id] = {
                "data":         data,
                "version":      version,
                "content_hash": content_hash,
            }

    def invalidate(self, fact_id: str) -> bool:
        """Инвалидировать запись в кэше."""
        with self._lock:
            if fact_id in self._store:
                del self._store[fact_id]
                return True
            return False

    def invalidate_all(self) -> int:
        """Полная очистка кэша (например, при rollback)."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            return count

    def verify_coherence(self, db_conn) -> dict:
        """
        Проверяет согласованность L0 с L1.
        Читает все кэшированные факты из SQLite и сравнивает хэши.

        Returns:
            {"coherent": True/False, "stale_count": int, "checked": int}
        """
        with self._lock:
            fact_ids = list(self._store.keys())

        if not fact_ids:
            return {"coherent": True, "stale_count": 0, "checked": 0}

        placeholders = ",".join("?" * len(fact_ids))
        rows = db_conn.execute(
            f"""
            SELECT fact_id, claim, confidence, epistemic_state, fact_version
            FROM facts
            WHERE fact_id IN ({placeholders})
            """,
            fact_ids,
        ).fetchall()

        stale_count = 0
        for row in rows:
            fid, claim, confidence, state, db_version = row
            expected_hash = compute_content_hash(claim, confidence, state)

            entry = self._store.get(fid)
            if entry is None:
                continue

            cached_hash = entry.get("content_hash")
            cached_version = entry.get("version", 0)

            if cached_hash != expected_hash or (
                db_version is not None and cached_version < db_version
            ):
                stale_count += 1
                # Автоматически инвалидируем устаревшие
                with self._lock:
                    self._store.pop(fid, None)

        return {
            "coherent":   stale_count == 0,
            "stale_count": stale_count,
            "checked":    len(rows),
        }

    def stats(self) -> dict:
        """Статистика кэша."""
        with self._lock:
            total = self._hits + self._misses
            return {
                "size":            len(self._store),
                "max_size":        self._max_size,
                "hits":            self._hits,
                "misses":          self._misses,
                "hit_rate":        round(self._hits / max(total, 1), 3),
                "stale_detected":  self._stale_detected,
            }


# ── Rebuild content_hash в БД ─────────────────────────────────────────────────

def rebuild_content_hashes(db_conn) -> int:
    """
    Пересчитывает content_hash для всех фактов в БД.
    Запускать после применения миграции 009_truth_kernel.sql.

    Returns: количество обновлённых записей
    """
    rows = db_conn.execute(
        "SELECT fact_id, claim, confidence, epistemic_state FROM facts"
    ).fetchall()

    count = 0
    for fact_id, claim, confidence, state in rows:
        h = compute_content_hash(
            claim=claim or "",
            confidence=float(confidence or 0.0),
            epistemic_state=state or "Observed",
        )
        db_conn.execute(
            "UPDATE facts SET content_hash = ? WHERE fact_id = ?",
            (h, fact_id),
        )
        count += 1

    db_conn.commit()
    return count
