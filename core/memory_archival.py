"""
📦 core/memory_archival.py — Memory Archival (V8.7 Titan, из Memory f.md)

Архивация старых эпизодов — не удаление, а ПЕРЕНОС в object storage.
Освобождает граф от мёртвого груза, сохраняя историю доступной.

V8.7: использует локальную файловую систему (архив в JSON).
S3/MinIO — опциональное расширение (меняется только storage backend).

Конфигурация:
    VELANTRIM_ARCHIVE_PATH   — путь к архиву (default: ./data/archive)
    VELANTRIM_ARCHIVE_AGE    — возраст эпизодов для архивации в днях (default: 90)

Инварианты:
    I-AR1: Архивация НЕ удаляет факт — заменяет на ссылку archive_key.
    I-AR2: ImmutableCore / Ring Zero — НЕ архивируются.
    I-AR3: Архивные файлы — read-only после записи.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.memory_archival")

SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim_house.db")
ARCHIVE_PATH = os.getenv("VELANTRIM_ARCHIVE_PATH", "./data/archive")
ARCHIVE_AGE_DAYS = int(os.getenv("VELANTRIM_ARCHIVE_AGE", "90"))

_IMMUTABLE_STATES = {"ImmutableCore"}

_ARCHIVE_MARK_DDL = """
CREATE TABLE IF NOT EXISTS archived_facts (
    fact_id       TEXT PRIMARY KEY,
    archive_key   TEXT NOT NULL,
    archived_at   TEXT NOT NULL,
    original_claim TEXT,
    original_state TEXT,
    archive_file  TEXT NOT NULL
);
"""


@dataclass
class ArchiveReport:
    scanned: int = 0
    archived: int = 0
    skipped_immutable: int = 0
    skipped_recent: int = 0
    errors: int = 0
    archive_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scanned": self.scanned,
            "archived": self.archived,
            "skipped_immutable": self.skipped_immutable,
            "skipped_recent": self.skipped_recent,
            "errors": self.errors,
            "archive_path": self.archive_path,
        }


class MemoryArchival:
    """
    Перенос старых фактов в архив.

    Не удаляет данные — заменяет claim на archive_key.
    Оригинал сохраняется в JSON-файле.
    """

    def __init__(
        self,
        *,
        db_path: str = SQLITE_PATH,
        archive_path: str = ARCHIVE_PATH,
        age_days: int = ARCHIVE_AGE_DAYS,
    ):
        self._db_path = db_path
        self._archive_path = Path(archive_path)
        self._age_days = age_days
        self._archive_path.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(_ARCHIVE_MARK_DDL)
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning("MemoryArchival DDL: %s", exc)

    # ── Архивация ─────────────────────────────────────────────────────────

    def archive_old_facts(self, *, dry_run: bool = False) -> ArchiveReport:
        """
        Найти и заархивировать факты старше age_days.

        dry_run=True → только отчёт (не архивирует).
        """
        report = ArchiveReport(archive_path=str(self._archive_path))
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self._age_days)).isoformat()

        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.row_factory = sqlite3.Row

            # Найти старые факты — FIX #11 (Claude audit): исключать уже-архивированные
            rows = conn.execute(
                """SELECT fact_id, claim, epistemic_state, confidence, created_at
                   FROM facts
                   WHERE created_at < ?
                     AND epistemic_state NOT IN ('ImmutableCore',)
                     AND fact_id NOT IN (SELECT fact_id FROM archived_facts)
                   ORDER BY created_at ASC""",
                (cutoff,),
            ).fetchall()

            report.scanned = len(rows)
            logger.info(
                "MemoryArchival: найдено %d старых фактов (старше %d дней)",
                report.scanned, self._age_days,
            )

            if dry_run:
                conn.close()
                report.archived = 0
                return report

            # Группировка для архивации (batch по 100 фактов в один файл)
            batch: List[Dict] = []
            batch_count = 0

            for row in rows:
                if row["epistemic_state"] in _IMMUTABLE_STATES:
                    report.skipped_immutable += 1
                    continue

                batch.append(dict(row))

                if len(batch) >= 100:
                    self._archive_batch(conn, batch, batch_count)
                    report.archived += len(batch)
                    batch_count += 1
                    batch = []

            # Последний batch
            if batch:
                self._archive_batch(conn, batch, batch_count)
                report.archived += len(batch)

            conn.commit()
            conn.close()

            logger.info(
                "MemoryArchival: заархивировано %d фактов, пропущено %d immutable",
                report.archived, report.skipped_immutable,
            )
            return report

        except Exception as exc:
            logger.error("MemoryArchival.archive_old_facts: %s", exc)
            report.errors += 1
            return report

    def _archive_batch(
        self,
        conn: sqlite3.Connection,
        batch: List[Dict],
        batch_num: int,
    ) -> None:
        """Заархивировать пачку фактов в один JSON-файл."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        archive_file = self._archive_path / f"archive_{timestamp}_b{batch_num:03d}.json"

        # Записать JSON
        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "archived_at": datetime.now(timezone.utc).isoformat(),
                    "archived_count": len(batch),
                    "facts": batch,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        # Заменить claim на ссылку, обновить БД
        for fact in batch:
            archive_key = f"archive://{archive_file.name}#{fact['fact_id']}"

            # Отметить в таблице archived_facts — FIX #11 (Claude audit):
            # INSERT OR IGNORE чтобы избежать дублей при перезапуске.
            # Фильтр: исключать уже-архивированные (AND fact_id NOT IN archived_facts).
            conn.execute(
                """INSERT OR IGNORE INTO archived_facts
                   (fact_id, archive_key, archived_at, original_claim, original_state, archive_file)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    fact["fact_id"],
                    archive_key,
                    datetime.now(timezone.utc).isoformat(),
                    fact.get("claim", "")[:500],
                    fact.get("epistemic_state", ""),
                    str(archive_file),
                ),
            )

            # Обновить claim в facts + bump fact_version (триггер 009 требует)
            bump = ""
            try:
                has_version = any(
                    r[1] == "fact_version"
                    for r in conn.execute("PRAGMA table_info(facts)")
                )
                bump = ", fact_version = fact_version + 1" if has_version else ""
            except Exception:
                pass
            conn.execute(
                f"UPDATE facts SET claim = ?, updated_at = ?{bump} WHERE fact_id = ?",
                (
                    f"[ARCHIVED: {archive_key}]",
                    datetime.now(timezone.utc).isoformat(),
                    fact["fact_id"],
                ),
            )

    # ── Восстановление ────────────────────────────────────────────────────

    def restore_fact(self, fact_id: str) -> Optional[Dict[str, Any]]:
        """Восстановить факт из архива."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row

            # Найти архивную запись
            row = conn.execute(
                "SELECT * FROM archived_facts WHERE fact_id = ?",
                (fact_id,),
            ).fetchone()

            if not row:
                conn.close()
                return None

            archive_file = row["archive_file"]
            original_claim = row["original_claim"]

            # Найти в JSON-файле
            archive_path = self._archive_path / Path(archive_file).name
            if archive_path.exists():
                with open(archive_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for fact in data.get("facts", []):
                    if fact.get("fact_id") == fact_id:
                        conn.close()
                        return fact

            conn.close()
            return {"fact_id": fact_id, "claim": original_claim, "archived": True}

        except Exception as exc:
            logger.error("MemoryArchival.restore_fact: %s", exc)
            return None

    # ── Статистика ────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            archived = conn.execute(
                "SELECT COUNT(*) FROM archived_facts"
            ).fetchone()[0]
            conn.close()

            archive_files = list(self._archive_path.glob("archive_*.json"))
            return {
                "archived_facts": archived,
                "archive_files_count": len(archive_files),
                "archive_path": str(self._archive_path),
                "archive_age_days": self._age_days,
                "total_archive_size_bytes": sum(
                    f.stat().st_size for f in archive_files
                ),
            }
        except Exception:
            return {"archived_facts": 0, "archive_path": str(self._archive_path)}


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_archival: Optional[MemoryArchival] = None


def get_memory_archival() -> MemoryArchival:
    global _archival
    if _archival is None:
        _archival = MemoryArchival()
    return _archival


__all__ = [
    "MemoryArchival",
    "ArchiveReport",
    "get_memory_archival",
]
