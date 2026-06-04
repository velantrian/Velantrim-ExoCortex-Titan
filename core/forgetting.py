"""
🔒 core/forgetting.py — GDPR «Right to be Forgotten» + PII Redaction (V8.7 Titan)

Три режима:
    1. FORGET_ONE — удалить конкретный факт (с проверкой зависимостей)
    2. FORGET_ALL  — удалить всё для user_id (GDPR compliance)
    3. REDACT_PII  — удалить PII из факта без удаления самого факта

Инварианты:
    I-F1: ImmutableCore / Ring Zero факты НЕ удаляются (даже по GDPR-запросу)
    I-F2: Удаление факта → проверка зависимостей (causal relations, provenance)
    I-F3: REDACT_PII не меняет epistemic_state и confidence
    I-F4: FORGET_ALL создаёт audit-запись с timestamp и причиной (GDPR trail)

Архитектура:
    Не заменяет удаление в SQLite. Добавляет проверки ДО удаления.
    Все операции логируются в provenance_chain (если доступен).
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("velantrim.forgetting")

SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim.db")

# ─── Конфигурация ─────────────────────────────────────────────────────────────

# Базовые PII-паттерны (RU + EN)
_PII_PATTERNS = [
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL]'),
    (re.compile(r'\b(?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b'), '[PHONE]'),
    (re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), '[IP]'),
    (re.compile(r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\b'), '[FULL_NAME]'),
    (re.compile(r'\b(?:ул\.|улица|пр\.|проспект|д\.|дом)\s+\S+(?:\s+\d+)?\b'), '[ADDRESS]'),
]

# Immutable IDs — их нельзя удалить даже по GDPR
_IMMUTABLE_FACT_IDS = {"VALUES_CORE", "RING_ZERO"}


class ForgetMode(str, Enum):
    FORGET_ONE = "forget_one"
    FORGET_ALL = "forget_all"
    REDACT_PII = "redact_pii"


@dataclass
class ForgetVerdict:
    allowed: bool
    reason: str
    affected_facts: int = 0
    redacted_count: int = 0
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "affected_facts": self.affected_facts,
            "redacted_count": self.redacted_count,
            "details": self.details,
        }


# ─── PII Redaction ────────────────────────────────────────────────────────────

def redact_pii(text: str) -> str:
    """
    Удалить PII из текста. Заменяет на теги [EMAIL], [PHONE] и т.д.
    Не меняет смысл — только обезличивает.
    """
    result = text
    for pattern, replacement in _PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def detect_pii(text: str) -> List[str]:
    """Обнаружить PII в тексте (возвращает типы найденных PII)."""
    found: List[str] = []
    for pattern, tag in _PII_PATTERNS:
        if pattern.search(text):
            found.append(tag)
    return found


# ─── Forgetting Engine ────────────────────────────────────────────────────────

class ForgettingEngine:
    """
    Контролируемое удаление фактов с проверкой зависимостей.

    Использование:
        engine = ForgettingEngine()

        # Проверить можно ли удалить
        verdict = engine.check("fact_abc123")

        # Удалить один факт
        result = engine.forget_one("fact_abc123")

        # Удалить всё для пользователя (GDPR)
        result = engine.forget_all(user_id="user_42")

        # Обезличить факт (не удаляя)
        result = engine.redact_pii_fact("fact_abc123")
    """

    def __init__(self, db_path: str = SQLITE_PATH):
        self._db_path = db_path

    # ── Проверка ──────────────────────────────────────────────────────────

    def check(self, fact_id: str) -> ForgetVerdict:
        """
        Проверить можно ли удалить факт.
        НЕ удаляет — только возвращает вердикт.
        """
        if fact_id in _IMMUTABLE_FACT_IDS:
            return ForgetVerdict(
                allowed=False,
                reason="immutable_fact_protected",
                details=[f"Факт {fact_id} находится в Ring Zero — удаление запрещено архитектурно."],
            )

        # Проверить существование
        fact = self._get_fact(fact_id)
        if fact is None:
            return ForgetVerdict(
                allowed=False,
                reason="fact_not_found",
                details=[f"Факт {fact_id} не найден."],
            )

        # Проверить ESM-состояние
        state = fact.get("epistemic_state", "")
        if state in ("ImmutableCore",):
            return ForgetVerdict(
                allowed=False,
                reason="immutable_state",
                details=[f"Факт {fact_id} в состоянии {state} — удаление запрещено."],
            )

        # Проверить зависимости
        affected = self._find_dependents(fact_id)
        if affected:
            return ForgetVerdict(
                allowed=True,
                reason=f"has_dependents_{len(affected)}",
                affected_facts=len(affected),
                details=[
                    f"⚠️ Удаление {fact_id} затронет {len(affected)} связанных фактов.",
                    f"Зависимые факты: {affected[:5]}{'...' if len(affected) > 5 else ''}",
                ],
            )

        return ForgetVerdict(
            allowed=True,
            reason="ok",
            details=[f"Факт {fact_id} может быть безопасно удалён."],
        )

    # ── FORGET_ONE ────────────────────────────────────────────────────────

    def forget_one(
        self,
        fact_id: str,
        *,
        reason: str = "user_request",
        user_id: str = "default",
    ) -> ForgetVerdict:
        """Удалить один факт с проверками."""
        verdict = self.check(fact_id)
        if not verdict.allowed and "immutable" in verdict.reason:
            return verdict

        # Даже с зависимостями — удаляем (пользователь предупреждён)
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")

            # Удалить факт
            conn.execute("DELETE FROM facts WHERE fact_id = ?", (fact_id,))

            # Записать в provenance_chain
            self._log_forgetting(conn, fact_id, reason, user_id)

            conn.commit()
            conn.close()

            logger.info("Forgetting: удалён %s (reason=%s, user=%s)", fact_id, reason, user_id)
            return ForgetVerdict(
                allowed=True,
                reason="deleted",
                affected_facts=verdict.affected_facts + 1,
                details=[f"✅ Факт {fact_id} удалён."] + verdict.details,
            )
        except Exception as exc:
            logger.error("Forgetting.forget_one: %s", exc)
            return ForgetVerdict(
                allowed=False,
                reason=f"store_error: {exc}",
                details=[f"❌ Ошибка при удалении {fact_id}: {exc}"],
            )

    # ── FORGET_ALL (GDPR) ─────────────────────────────────────────────────

    def forget_all(
        self,
        *,
        user_id: str = "default",
        reason: str = "gdpr_request",
        dry_run: bool = False,
    ) -> ForgetVerdict:
        """
        Удалить ВСЕ факты для user_id.

        dry_run=True → только подсчёт (не удаляет).
        ImmutableCore факты НЕ трогает.
        """
        # Найти все факты пользователя (по source contains user_id)
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.row_factory = sqlite3.Row

            # Ищем по source, metadata, или user_id в поле
            rows = conn.execute(
                """SELECT fact_id, epistemic_state FROM facts
                   WHERE source LIKE ? OR metadata LIKE ?""",
                (f"%{user_id}%", f"%{user_id}%"),
            ).fetchall()

            # Фильтруем: ImmutableCore — пропускаем
            to_delete = [
                dict(r) for r in rows
                if r["epistemic_state"] not in ("ImmutableCore",)
                and r["fact_id"] not in _IMMUTABLE_FACT_IDS
            ]

            immutable_skipped = len(rows) - len(to_delete)

            if dry_run:
                conn.close()
                return ForgetVerdict(
                    allowed=True,
                    reason="dry_run",
                    affected_facts=len(to_delete),
                    details=[
                        f"🔍 Dry run: будет удалено {len(to_delete)} фактов.",
                        f"🛡️ Пропущено (ImmutableCore): {immutable_skipped}",
                        f"Пользователь: {user_id}",
                    ],
                )

            # Удалить
            for fact in to_delete:
                conn.execute(
                    "DELETE FROM facts WHERE fact_id = ?",
                    (fact["fact_id"],),
                )

            # Audit trail
            self._log_forgetting(
                conn,
                "FORGET_ALL",
                reason,
                user_id,
                extra={"count": len(to_delete), "immutable_skipped": immutable_skipped},
            )

            conn.commit()
            conn.close()

            msg = f"✅ GDPR: удалено {len(to_delete)} фактов для {user_id}"
            if immutable_skipped:
                msg += f" (пропущено {immutable_skipped} ImmutableCore)"
            logger.warning(msg)

            return ForgetVerdict(
                allowed=True,
                reason="gdpr_completed",
                affected_facts=len(to_delete),
                details=[msg],
            )

        except Exception as exc:
            logger.error("Forgetting.forget_all: %s", exc)
            return ForgetVerdict(
                allowed=False,
                reason=f"store_error: {exc}",
                details=[f"❌ Ошибка GDPR-удаления: {exc}"],
            )

    # ── REDACT_PII ────────────────────────────────────────────────────────

    def redact_pii_fact(self, fact_id: str) -> ForgetVerdict:
        """
        Обезличить факт — заменить PII на теги.
        Факт остаётся, но без персональных данных.
        """
        fact = self._get_fact(fact_id)
        if fact is None:
            return ForgetVerdict(allowed=False, reason="fact_not_found")

        claim = fact.get("claim", "")
        redacted = redact_pii(claim)

        if redacted == claim:
            return ForgetVerdict(
                allowed=True,
                reason="no_pii_found",
                details=[f"PII не обнаружено в факте {fact_id}."],
            )

        # Обновить claim
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "UPDATE facts SET claim = ?, updated_at = ? WHERE fact_id = ?",
                (redacted, datetime.now(timezone.utc).isoformat(), fact_id),
            )
            conn.commit()
            conn.close()

            logger.info("PII redacted: %s → %s", fact_id, redacted[:80])
            return ForgetVerdict(
                allowed=True,
                reason="redacted",
                redacted_count=1,
                details=[
                    f"✅ PII удалён из {fact_id}.",
                    f"Было: {claim[:80]}...",
                    f"Стало: {redacted[:80]}...",
                ],
            )
        except Exception as exc:
            logger.error("Forgetting.redact_pii: %s", exc)
            return ForgetVerdict(allowed=False, reason=f"store_error: {exc}")

    def redact_pii_batch(self, limit: int = 100) -> ForgetVerdict:
        """Пакетное обезличивание всех фактов с PII."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")

            rows = conn.execute(
                "SELECT fact_id, claim FROM facts LIMIT ?", (limit,)
            ).fetchall()

            redacted_count = 0
            for row in rows:
                claim = row["claim"]
                redacted = redact_pii(claim)
                if redacted != claim:
                    conn.execute(
                        "UPDATE facts SET claim = ?, updated_at = ? WHERE fact_id = ?",
                        (redacted, datetime.now(timezone.utc).isoformat(), row["fact_id"]),
                    )
                    redacted_count += 1

            conn.commit()
            conn.close()

            return ForgetVerdict(
                allowed=True,
                reason="batch_redacted",
                redacted_count=redacted_count,
                details=[f"✅ Обезличено {redacted_count} фактов из {len(rows)}."],
            )
        except Exception as exc:
            logger.error("Forgetting.redact_pii_batch: %s", exc)
            return ForgetVerdict(allowed=False, reason=f"store_error: {exc}")

    # ── Вспомогательные ──────────────────────────────────────────────────

    def _get_fact(self, fact_id: str) -> Optional[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception:
            return None

    def _find_dependents(self, fact_id: str) -> List[str]:
        """Найти факты, зависящие от этого (causal relations)."""
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            rows = conn.execute(
                "SELECT from_fact_id FROM relations WHERE to_fact_id = ?",
                (fact_id,),
            ).fetchall()
            conn.close()
            return [r[0] for r in rows if r[0]]
        except Exception:
            return []

    def _log_forgetting(
        self,
        conn: sqlite3.Connection,
        fact_id: str,
        reason: str,
        user_id: str,
        extra: Optional[Dict] = None,
    ) -> None:
        """Записать событие забывания в provenance_chain (если доступен)."""
        try:
            from core.provenance_chain import get_provenance_chain
            chain = get_provenance_chain()
            chain.append(
                fact_id,
                event_type="fact_forgotten",
                actor=user_id,
                reason=reason,
                payload=extra or {},
            )
        except Exception:
            pass  # provenance_chain может быть не инициализирован


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_engine: Optional[ForgettingEngine] = None


def get_forgetting_engine() -> ForgettingEngine:
    global _engine
    if _engine is None:
        _engine = ForgettingEngine()
    return _engine


__all__ = [
    "ForgettingEngine",
    "ForgetMode",
    "ForgetVerdict",
    "redact_pii",
    "detect_pii",
    "get_forgetting_engine",
]
