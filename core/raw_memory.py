"""
core/raw_memory.py — L0 Immutable Raw Memory (v8.5.1)
======================================================
Защита от Semantic Drift.

ПРОБЛЕМА: без этого модуля факты могут медленно менять смысл
при суммаризации L1→L2→L3. Через несколько итераций оригинальное
"волки иногда избегают людей" становится "волки боятся людей".
Это происходит тихо, без ошибок в логах.

РЕШЕНИЕ: хранить оригинальный текст в l0_raw_memory.
Оттуда создаём derived факты со ссылкой. Оригинал можно всегда
восстановить и перепроверить.

Использование:
    from core.raw_memory import RawMemoryStore

    store = RawMemoryStore(db_conn)

    # Сохранить оригинальный текст
    raw_id = store.store("Дерево растёт в лесу. Птицы вьют гнёзда.",
                          source="document.pdf", source_type="file")

    # Создать derived fact со ссылкой
    fact = {
        "fact_id": "f_tree_001",
        "claim": "Дерево растёт в лесу",
        "derived_from": raw_id,   # ← ключевое поле
        ...
    }

    # Найти оригинал любого факта
    raw = store.get_raw_for_fact("f_tree_001")
    print(raw.original_text)  # "Дерево растёт в лесу. Птицы вьют гнёзда."
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class RawMemoryEntry:
    """Запись в L0 Raw Memory."""
    raw_id:        str
    original_text: str
    content_hash:  str
    source:        str | None = None
    source_url:    str | None = None
    source_type:   str = "unknown"
    language:      str = "unknown"
    char_count:    int = 0
    word_count:    int = 0
    created_at:    str = ""
    metadata:      dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "raw_id":        self.raw_id,
            "original_text": self.original_text,
            "content_hash":  self.content_hash,
            "source":        self.source,
            "source_type":   self.source_type,
            "char_count":    self.char_count,
            "word_count":    self.word_count,
            "created_at":    self.created_at,
        }


# ── RawMemoryStore ────────────────────────────────────────────────────────────

class RawMemoryStore:
    """
    API для работы с L0 Immutable Raw Memory.

    Гарантии:
    1. Оригинальный текст никогда не изменяется (DB-level trigger)
    2. Дубликаты автоматически дедуплицируются по SHA256
    3. Каждый derived факт может быть прослежен к оригиналу
    4. Цепочка суммаризации сохраняется для аудита
    """

    def __init__(self, db_conn) -> None:
        self._conn = db_conn

    # ── Запись ────────────────────────────────────────────────────────────────

    def store(
        self,
        text:        str,
        source:      str | None = None,
        source_url:  str | None = None,
        source_type: str = "unknown",
        language:    str = "unknown",
        metadata:    dict | None = None,
    ) -> str:
        """
        Сохранить оригинальный текст в L0.

        Если текст уже есть (по SHA256) — возвращает существующий raw_id.
        Дедупликация предотвращает дублирование одинакового контента.

        Returns: raw_id
        """
        if not text or not text.strip():
            raise ValueError("Нельзя сохранить пустой текст в L0 Raw Memory")

        content_hash = self._compute_hash(text)

        # Проверяем дедупликацию
        existing = self._conn.execute(
            "SELECT raw_id FROM l0_raw_memory WHERE content_hash = ?",
            (content_hash,),
        ).fetchone()
        if existing:
            return existing[0]

        # Новая запись
        raw_id = f"raw_{uuid.uuid4().hex[:16]}"
        now = datetime.now(UTC).isoformat()
        word_count = len(re.findall(r'\S+', text))

        self._conn.execute(
            """
            INSERT INTO l0_raw_memory (
                raw_id, original_text, content_hash,
                source, source_url, source_type, language,
                char_count, word_count,
                created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                raw_id, text, content_hash,
                source, source_url, source_type, language,
                len(text), word_count,
                now, json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )
        self._conn.commit()
        return raw_id

    def link_fact(
        self,
        raw_id:          str,
        fact_id:         str,
        derivation_type: str = "direct",
        step_index:      int = 0,
        transformation:  str | None = None,
    ) -> None:
        """
        Связать derived факт с оригинальным raw текстом.

        derivation_type:
            'direct'     — факт прямо из raw текста
            'chunked'    — факт из куска raw текста
            'summarized' — через суммаризацию (осторожно: drift risk)
            'inferred'   — выведен через reasoning
        """
        step_id = f"step_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC).isoformat()

        # Обновляем derived_from в facts
        self._conn.execute(
            "UPDATE facts SET derived_from = ? WHERE fact_id = ?",
            (raw_id, fact_id),
        )

        # Записываем шаг в цепочку
        self._conn.execute(
            """
            INSERT OR IGNORE INTO raw_derivation_chain (
                step_id, raw_id, derived_fact_id,
                derivation_type, step_index, transformation, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                step_id, raw_id, fact_id,
                derivation_type, step_index, transformation, now,
            ),
        )
        self._conn.commit()

    # ── Чтение ────────────────────────────────────────────────────────────────

    def get(self, raw_id: str) -> RawMemoryEntry | None:
        """Получить raw entry по ID."""
        row = self._conn.execute(
            """
            SELECT raw_id, original_text, content_hash, source, source_url,
                   source_type, language, char_count, word_count, created_at, metadata
            FROM l0_raw_memory WHERE raw_id = ?
            """,
            (raw_id,),
        ).fetchone()
        return self._row_to_entry(row) if row else None

    def get_raw_for_fact(self, fact_id: str) -> RawMemoryEntry | None:
        """
        Найти оригинал для любого derived факта.
        Это ключевой метод для защиты от semantic drift:
        всегда можно сравнить факт с оригинальным текстом.
        """
        row = self._conn.execute(
            """
            SELECT r.raw_id, r.original_text, r.content_hash, r.source, r.source_url,
                   r.source_type, r.language, r.char_count, r.word_count,
                   r.created_at, r.metadata
            FROM l0_raw_memory r
            JOIN facts f ON f.derived_from = r.raw_id
            WHERE f.fact_id = ?
            """,
            (fact_id,),
        ).fetchone()
        return self._row_to_entry(row) if row else None

    def get_facts_from_raw(self, raw_id: str) -> list[dict]:
        """Все derived факты из данного raw текста."""
        rows = self._conn.execute(
            """
            SELECT f.fact_id, f.claim, f.epistemic_state, f.confidence,
                   c.derivation_type, c.step_index
            FROM facts f
            JOIN raw_derivation_chain c ON c.derived_fact_id = f.fact_id
            WHERE c.raw_id = ?
            ORDER BY c.step_index, c.created_at
            """,
            (raw_id,),
        ).fetchall()
        return [
            {
                "fact_id":        r[0],
                "claim":          r[1],
                "epistemic_state": r[2],
                "confidence":     r[3],
                "derivation_type": r[4],
                "step_index":     r[5],
            }
            for r in rows
        ]

    def find_orphan_facts(self) -> list[str]:
        """
        Найти факты без ссылки на raw memory.
        Они — кандидаты на semantic drift (нет оригинала для проверки).
        """
        rows = self._conn.execute(
            """
            SELECT fact_id FROM facts
            WHERE derived_from IS NULL
              AND epistemic_state NOT IN ('ImmutableCore', 'Collapsed', 'Deprecated')
            """,
        ).fetchall()
        return [r[0] for r in rows]

    def verify_fact_drift(self, fact_id: str) -> dict:
        """
        Проверяет потенциальный semantic drift для факта.

        Сравнивает claim факта с оригинальным текстом.
        Возвращает: оценку drift (0.0 = нет, 1.0 = сильный drift).
        """
        raw = self.get_raw_for_fact(fact_id)
        if raw is None:
            return {
                "fact_id":     fact_id,
                "has_raw":     False,
                "drift_risk":  "unknown",
                "note":        "Нет оригинала — drift неизмерим",
            }

        fact_row = self._conn.execute(
            "SELECT claim FROM facts WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()
        if not fact_row:
            return {"fact_id": fact_id, "has_raw": True, "drift_risk": "fact_missing"}

        claim = fact_row[0] or ""
        original = raw.original_text

        # Простая эвристика: процент слов claim которые есть в original
        claim_words = set(claim.lower().split())
        original_words = set(original.lower().split())

        if not claim_words:
            overlap = 0.0
        else:
            overlap = len(claim_words & original_words) / len(claim_words)

        drift_risk = (
            "low"  if overlap >= 0.7 else
            "medium" if overlap >= 0.4 else
            "high"
        )

        return {
            "fact_id":    fact_id,
            "has_raw":    True,
            "raw_id":     raw.raw_id,
            "overlap":    round(overlap, 3),
            "drift_risk": drift_risk,
            "claim_preview":    claim[:100],
            "original_preview": original[:100],
        }

    def stats(self) -> dict:
        """Статистика L0 Raw Memory."""
        total = self._conn.execute(
            "SELECT COUNT(*) FROM l0_raw_memory"
        ).fetchone()[0]
        linked = self._conn.execute(
            "SELECT COUNT(DISTINCT derived_from) FROM facts WHERE derived_from IS NOT NULL"
        ).fetchone()[0]
        orphans = len(self.find_orphan_facts())
        return {
            "total_raw_entries": total,
            "linked_to_facts":   linked,
            "orphan_facts":      orphans,
            "coverage_pct":      round(linked / max(total, 1) * 100, 1),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _row_to_entry(row) -> RawMemoryEntry:
        meta = {}
        if row[10]:
            try:
                meta = json.loads(row[10])
            except Exception:
                pass
        return RawMemoryEntry(
            raw_id=row[0],
            original_text=row[1],
            content_hash=row[2],
            source=row[3],
            source_url=row[4],
            source_type=row[5] or "unknown",
            language=row[6] or "unknown",
            char_count=row[7] or 0,
            word_count=row[8] or 0,
            created_at=row[9] or "",
            metadata=meta,
        )
