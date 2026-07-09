"""
🏷️ core/entity_resolver.py — Entity Resolver (из Crystal в V8.7 Titan)
======================================================================

Нормализует имена сущностей, находит канонические формы, управляет
таблицами entities / fact_mentions.

Задача: превратить «Ньютон», «Newton», «Исаак Ньютон» → одна сущность.

Использование:
    resolver = EntityResolver(db_path="./data/velantrim.db")
    resolver.ensure_entity("Исаак Ньютон", entity_type="person",
                           aliases=["Ньютон", "Newton", "Isaac Newton"])

    # При ingest факта:
    resolver.link_entity("fact_abc", "Исаак Ньютон", mention_type="subject")

    # Запрос:
    facts = resolver.get_facts_for_entity("и.ньютон")  # alias-матчинг

Архитектура:
    Rule-based нормализация (без LLM/NER — это следующий тиер).
    MVP: lower + trim + alias lookup.
    v2: embedding-based canonical resolution (при >1000 сущностей).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger("velantrim.entity_resolver")

SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim.db")

# ─── Нормализация имён ──────────────────────────────────────────────────────

def normalize_name(name: str) -> str:
    """
    Привести имя к каноническому виду для поиска.
    - lower + trim
    - замена ё → е
    - удаление лишних пробелов
    """
    if not name:
        return ""
    norm = name.lower().strip()
    norm = norm.replace("ё", "е")
    # collapse whitespace
    while "  " in norm:
        norm = norm.replace("  ", " ")
    return norm


def name_to_entity_id(name: str) -> str:
    """Детерминированный entity_id из канонического имени."""
    return "ent_" + hashlib.sha256(
        normalize_name(name).encode("utf-8")
    ).hexdigest()[:16]


# ─── Entity Types ───────────────────────────────────────────────────────────

VALID_ENTITY_TYPES = frozenset({
    "person", "concept", "location", "organization",
    "event", "artifact", "method", "other",
})


# ═══════════════════════════════════════════════════════════════════════════════
# EntityResolver
# ═══════════════════════════════════════════════════════════════════════════════

class EntityResolver:
    """
    Управление каталогом сущностей и связями факт→сущность.

    Работает с таблицами entities, fact_mentions, erasure_log
    (созданы миграцией 012_crystal_memory.sql).
    """

    def __init__(self, db_path: str = SQLITE_PATH):
        self._db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Применить миграцию 012 если таблиц ещё нет."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys = ON")

            # Проверить что таблицы существуют
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='entities'"
            ).fetchone()
            if row is None:
                # Применить DDL из миграции
                mig_path = os.path.join(
                    os.path.dirname(__file__), "..", "migrations", "012_crystal_memory.sql"
                )
                mig_path = os.path.normpath(mig_path)
                try:
                    with open(mig_path, encoding="utf-8") as f:
                        ddl = f.read()
                    conn.executescript(ddl)
                    conn.commit()
                    logger.info("Миграция 012 применена (entities/mentions/erasure_log)")
                except FileNotFoundError:
                    logger.warning("012_crystal_memory.sql не найден по пути %s", mig_path)
                except Exception as exc:
                    logger.warning("Ошибка применения 012: %s", exc)
            conn.close()
        except Exception as exc:
            logger.warning("EntityResolver._ensure_schema: %s", exc)

    # ── CRUD сущностей ──────────────────────────────────────────────────────

    def ensure_entity(
        self,
        name: str,
        *,
        entity_type: str = "concept",
        aliases: Sequence[str] = (),
        description: str = "",
        external_ids: Dict[str, str] | None = None,
    ) -> str:
        """
        Создать или найти сущность. Возвращает entity_id.

        Если сущность с таким каноническим именем уже есть — обновляет
        алиасы и last_seen. Если нет — создаёт новую.
        """
        norm = normalize_name(name)
        if not norm:
            raise ValueError("Имя сущности не может быть пустым")

        eid = name_to_entity_id(norm)
        now = datetime.now(timezone.utc).isoformat()
        if entity_type not in VALID_ENTITY_TYPES:
            entity_type = "concept"

        # Собрать все алиасы (каноническое имя + переданные + нормализованные варианты)
        all_aliases = {norm}
        for a in aliases:
            an = normalize_name(a)
            if an:
                all_aliases.add(an)

        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys = ON")

            existing = conn.execute(
                "SELECT entity_id, aliases_json FROM entities WHERE entity_id = ?",
                (eid,),
            ).fetchone()

            if existing:
                # Обновить существующую
                cur_aliases = set(json.loads(existing[1] or "[]"))
                merged = sorted(cur_aliases | all_aliases)
                conn.execute(
                    """UPDATE entities SET
                        aliases_json = ?, description = COALESCE(NULLIF(?, ''), description),
                        external_ids_json = COALESCE(?, external_ids_json),
                        last_seen = ?
                       WHERE entity_id = ?""",
                    (
                        json.dumps(merged, ensure_ascii=False),
                        description,
                        json.dumps(external_ids or {}, ensure_ascii=False) if external_ids else None,
                        now,
                        eid,
                    ),
                )
            else:
                # Создать новую
                conn.execute(
                    """INSERT INTO entities
                       (entity_id, canonical_name, entity_type, aliases_json,
                        description, external_ids_json, first_seen, last_seen)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        eid, name.strip(), entity_type,
                        json.dumps(sorted(all_aliases), ensure_ascii=False),
                        description,
                        json.dumps(external_ids or {}, ensure_ascii=False),
                        now, now,
                    ),
                )

            conn.commit()
            conn.close()
            return eid
        except Exception as exc:
            logger.error("ensure_entity(%s): %s", name, exc)
            raise

    def resolve(self, name: str) -> Optional[str]:
        """
        Найти entity_id по имени (alias-матчинг).
        Возвращает None если сущность не найдена.
        """
        norm = normalize_name(name)
        if not norm:
            return None

        eid = name_to_entity_id(norm)
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            # Быстрый путь: точное совпадение entity_id
            row = conn.execute(
                "SELECT entity_id FROM entities WHERE entity_id = ?",
                (eid,),
            ).fetchone()
            if row:
                conn.close()
                return row[0]

            # Медленный путь: поиск по алиасам (LIKE в JSON)
            row = conn.execute(
                """SELECT entity_id FROM entities
                   WHERE canonical_name = ?
                      OR aliases_json LIKE ?
                   LIMIT 1""",
                (name.strip(), f'%"{norm}"%'),
            ).fetchone()
            conn.close()
            return row[0] if row else None
        except Exception:
            return None

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Получить полную информацию о сущности."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM entities WHERE entity_id = ?",
                (entity_id,),
            ).fetchone()
            conn.close()
            if row is None:
                return None
            d = dict(row)
            d["aliases"] = json.loads(d.get("aliases_json", "[]"))
            d["external_ids"] = json.loads(d.get("external_ids_json", "{}"))
            return d
        except Exception:
            return None

    # ── Связи факт↔сущность ─────────────────────────────────────────────────

    def link_entity(
        self,
        fact_id: str,
        entity_name: str,
        *,
        mention_type: str = "context",
        entity_type: str = "concept",
        confidence: float = 0.7,
    ) -> str:
        """
        Связать факт с сущностью. Создаёт сущность если её ещё нет.
        Возвращает mention_id.

        Args:
            fact_id: идентификатор факта
            entity_name: имя сущности (будет разрешено/нормализовано)
            mention_type: subject / object / context
            entity_type: тип сущности (если создаётся новая)
            confidence: уверенность экстрактора (0.0-1.0)
        """
        entity_id = self.ensure_entity(entity_name, entity_type=entity_type)
        mention_id = f"men_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys = ON")

            conn.execute(
                """INSERT OR IGNORE INTO fact_mentions
                   (mention_id, fact_id, entity_id, mention_type, confidence, extracted_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (mention_id, fact_id, entity_id, mention_type, confidence, now),
            )
            conn.commit()
            conn.close()
            return mention_id
        except Exception as exc:
            logger.error("link_entity(%s, %s): %s", fact_id, entity_name, exc)
            return ""

    def link_entities_batch(
        self,
        fact_id: str,
        entities: Sequence[tuple[str, str, float]],  # (name, mention_type, confidence)
    ) -> int:
        """Пакетная привязка сущностей к факту. Возвращает число связей."""
        count = 0
        for name, mtype, conf in entities:
            mid = self.link_entity(fact_id, name, mention_type=mtype, confidence=conf)
            if mid:
                count += 1
        return count

    def get_facts_for_entity(self, entity_name: str, limit: int = 50) -> List[str]:
        """
        Найти все факты, упоминающие сущность (по имени или алиасам).
        Возвращает список fact_id.
        """
        entity_id = self.resolve(entity_name)
        if not entity_id:
            return []

        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            rows = conn.execute(
                """SELECT DISTINCT fm.fact_id
                   FROM fact_mentions fm
                   WHERE fm.entity_id = ?
                   ORDER BY fm.extracted_at DESC
                   LIMIT ?""",
                (entity_id, limit),
            ).fetchall()
            conn.close()
            return [r[0] for r in rows]
        except Exception as exc:
            logger.error("get_facts_for_entity(%s): %s", entity_name, exc)
            return []

    def get_entities_for_fact(self, fact_id: str) -> List[Dict[str, Any]]:
        """Все сущности, связанные с фактом."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT e.entity_id, e.canonical_name, e.entity_type,
                          fm.mention_type, fm.confidence
                   FROM entities e
                   JOIN fact_mentions fm ON fm.entity_id = e.entity_id
                   WHERE fm.fact_id = ?
                   ORDER BY fm.confidence DESC""",
                (fact_id,),
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    # ── Удаление (каскад для GDPR) ──────────────────────────────────────────

    def delete_mentions_for_fact(self, fact_id: str) -> int:
        """Удалить все упоминания сущностей для факта (при forget_one)."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            cur = conn.execute(
                "DELETE FROM fact_mentions WHERE fact_id = ?",
                (fact_id,),
            )
            conn.commit()
            conn.close()
            return cur.rowcount
        except Exception as exc:
            logger.error("delete_mentions_for_fact(%s): %s", fact_id, exc)
            return 0

    # ── Статистика ──────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """Статистика каталога сущностей."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            total = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            mentions = conn.execute("SELECT COUNT(*) FROM fact_mentions").fetchone()[0]
            by_type = {}
            for row in conn.execute(
                "SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type"
            ):
                by_type[row[0]] = row[1]
            conn.close()
            return {
                "total_entities": total,
                "total_mentions": mentions,
                "by_type": by_type,
            }
        except Exception:
            return {"total_entities": 0, "total_mentions": 0, "by_type": {}}


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_resolver: Optional[EntityResolver] = None


def get_entity_resolver() -> EntityResolver:
    global _resolver
    if _resolver is None:
        _resolver = EntityResolver()
    return _resolver


__all__ = [
    "EntityResolver",
    "normalize_name",
    "name_to_entity_id",
    "get_entity_resolver",
]
