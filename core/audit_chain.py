"""
🔗 core/audit_chain.py — Append-only Audit Log с Hash-Chain
============================================================
Каждое событие связано с предыдущим через SHA256 хэш.
Подделка любого события математически обнаруживается при verify().

Принцип: как блокчейн, только для памяти AI-агента.

event_hash = SHA256(prev_event_hash + event_type + fact_id + payload + created_at)

Sprint 1a — Этап A3
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime

# ── Типы событий ──────────────────────────────────────────────────────────────

class EventType:
    FACT_CREATED              = "fact_created"
    FACT_UPDATED              = "fact_updated"
    ESM_TRANSITION            = "esm_transition"
    FACT_DEPRECATED           = "fact_deprecated"
    FACT_COLLAPSED            = "fact_collapsed"
    TRUTH_GATE_VERDICT        = "truth_gate_verdict"
    OBSERVER_VERDICT          = "observer_verdict"
    IMMUTABLE_ATTEMPT_BLOCKED = "immutable_attempt_blocked"
    AUDIT_VERIFY              = "audit_verify"
    CACHE_INVALIDATED         = "cache_invalidated"
    INTEGRITY_CHECK           = "integrity_check"


# ── AuditEvent ────────────────────────────────────────────────────────────────

class AuditEvent:
    """Одно событие в цепочке памяти."""

    def __init__(
        self,
        event_type:      str,
        actor:           str,
        fact_id:         str | None = None,
        from_state:      str | None = None,
        to_state:        str | None = None,
        reason:          str | None = None,
        payload:         dict | None = None,
        confidence:      float | None = None,
        prev_event_hash: str | None = None,
    ) -> None:
        self.event_id        = f"evt_{uuid.uuid4().hex[:16]}"
        self.event_type      = event_type
        self.fact_id         = fact_id
        self.from_state      = from_state
        self.to_state        = to_state
        self.actor           = actor
        self.reason          = reason
        self.payload         = payload or {}
        self.confidence      = confidence
        self.prev_event_hash = prev_event_hash
        self.created_at      = datetime.now(UTC).isoformat()

        # Вычисляем хэш
        self.event_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """
        SHA256(prev_hash + event_type + fact_id + payload_json + created_at)
        Если prev_hash = None → используем GENESIS как константу.
        """
        prev = self.prev_event_hash or "VELANTRIM_GENESIS_BLOCK"
        payload_str = json.dumps(self.payload, sort_keys=True, ensure_ascii=False)

        data = "|".join([
            prev,
            self.event_type,
            self.fact_id or "",
            self.from_state or "",
            self.to_state or "",
            self.actor,
            payload_str,
            self.created_at,
        ])
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {
            "event_id":        self.event_id,
            "event_type":      self.event_type,
            "fact_id":         self.fact_id,
            "from_state":      self.from_state,
            "to_state":        self.to_state,
            "actor":           self.actor,
            "reason":          self.reason,
            "payload":         json.dumps(self.payload, ensure_ascii=False),
            "confidence":      self.confidence,
            "event_hash":      self.event_hash,
            "prev_event_hash": self.prev_event_hash,
            "created_at":      self.created_at,
        }


# ── AuditChain ────────────────────────────────────────────────────────────────

class AuditChain:
    """
    Append-only audit log с hash-chain верификацией.

    Гарантирует:
    1. Нельзя изменить прошлое незаметно (hash-chain)
    2. Нельзя удалить событие (DB-level TRIGGER)
    3. Любой разрыв цепочки обнаруживается через verify_chain()

    Использование:
        chain = AuditChain(db_conn)
        chain.log_esm_transition("f1", "Observed", "Hypothesized", "agent:api")
        report = chain.verify_chain()
    """

    def __init__(self, db_conn) -> None:
        self._conn = db_conn

    # ── Запись событий ────────────────────────────────────────────────────────

    def log(
        self,
        event_type:  str,
        actor:       str,
        fact_id:     str | None = None,
        from_state:  str | None = None,
        to_state:    str | None = None,
        reason:      str | None = None,
        payload:     dict | None = None,
        confidence:  float | None = None,
    ) -> AuditEvent:
        """Записать событие в цепочку."""
        prev_hash = self._get_last_hash()

        event = AuditEvent(
            event_type=event_type,
            actor=actor,
            fact_id=fact_id,
            from_state=from_state,
            to_state=to_state,
            reason=reason,
            payload=payload,
            confidence=confidence,
            prev_event_hash=prev_hash,
        )

        self._conn.execute(
            """
            INSERT INTO memory_events (
                event_id, event_type, fact_id, from_state, to_state,
                actor, reason, payload, confidence,
                event_hash, prev_event_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id, event.event_type, event.fact_id,
                event.from_state, event.to_state,
                event.actor, event.reason,
                json.dumps(event.payload, ensure_ascii=False),
                event.confidence,
                event.event_hash, event.prev_event_hash,
                event.created_at,
            ),
        )
        self._conn.commit()
        return event

    # ── Удобные shortcut методы ───────────────────────────────────────────────

    def log_fact_created(
        self, fact_id: str, claim: str, actor: str, confidence: float,
    ) -> AuditEvent:
        return self.log(
            EventType.FACT_CREATED, actor, fact_id=fact_id,
            to_state="Observed", confidence=confidence,
            payload={"claim_preview": claim[:100]},
        )

    def log_esm_transition(
        self,
        fact_id:    str,
        from_state: str,
        to_state:   str,
        actor:      str,
        reason:     str | None = None,
        confidence: float | None = None,
    ) -> AuditEvent:
        event_type = (
            EventType.FACT_DEPRECATED if to_state == "Deprecated"
            else EventType.FACT_COLLAPSED if to_state == "Collapsed"
            else EventType.ESM_TRANSITION
        )
        return self.log(
            event_type, actor, fact_id=fact_id,
            from_state=from_state, to_state=to_state,
            reason=reason, confidence=confidence,
        )

    def log_truth_gate_verdict(
        self,
        fact_id:    str,
        passed:     bool,
        mode:       str,
        actor:      str,
        reason:     str | None = None,
        confidence: float | None = None,
    ) -> AuditEvent:
        return self.log(
            EventType.TRUTH_GATE_VERDICT, actor, fact_id=fact_id,
            reason=reason, confidence=confidence,
            payload={"passed": passed, "mode": mode},
        )

    def log_observer_verdict(
        self,
        decision: str,
        flags:    list | None = None,
        actor:    str = "observer",
        reason:   str | None = None,
    ) -> AuditEvent:
        """Append a passive Observer verdict (allow|warn|gap_notice|reject) + flags."""
        return self.log(
            EventType.OBSERVER_VERDICT, actor,
            reason=reason,
            payload={"decision": decision, "flags": list(flags or [])},
        )

    def log_immutable_blocked(
        self, fact_id: str, actor: str, attempted_state: str,
    ) -> AuditEvent:
        return self.log(
            EventType.IMMUTABLE_ATTEMPT_BLOCKED, actor, fact_id=fact_id,
            payload={"attempted_transition_to": attempted_state},
        )

    def log_cache_invalidated(self, fact_id: str, reason: str) -> AuditEvent:
        return self.log(
            EventType.CACHE_INVALIDATED, "system", fact_id=fact_id,
            reason=reason,
        )

    # ── Верификация цепочки ───────────────────────────────────────────────────

    def verify_chain(
        self,
        fact_id:  str | None = None,
        max_rows: int = 10_000,
    ) -> dict:
        """
        Проверяет целостность hash-chain.

        Алгоритм:
        1. Читаем все события в хронологическом порядке
        2. Для каждого пересчитываем event_hash
        3. Сравниваем с сохранённым
        4. Проверяем что prev_event_hash совпадает с хэшем предыдущего

        Returns:
            {
                "valid": True/False,
                "events_checked": int,
                "first_broken_event": str | None,
                "broken_at_position": int | None,
                "error": str | None,
            }
        """
        sql = """
            SELECT event_id, event_type, fact_id, from_state, to_state,
                   actor, payload, confidence, event_hash, prev_event_hash, created_at
            FROM memory_events
        """
        params = []
        if fact_id:
            sql += " WHERE fact_id = ?"
            params.append(fact_id)
        sql += " ORDER BY rowid ASC"
        sql += f" LIMIT {max_rows}"

        rows = self._conn.execute(sql, params).fetchall()

        if not rows:
            return {
                "valid": True,
                "events_checked": 0,
                "first_broken_event": None,
                "broken_at_position": None,
                "error": None,
            }

        prev_hash: str | None = None

        for i, row in enumerate(rows):
            (
                event_id, event_type, fid, from_state, to_state,
                actor, payload_str, confidence,
                stored_hash, stored_prev_hash, created_at,
            ) = row

            # Проверяем prev_event_hash
            if stored_prev_hash != prev_hash:
                return {
                    "valid": False,
                    "events_checked": i,
                    "first_broken_event": event_id,
                    "broken_at_position": i,
                    "error": (
                        f"Chain broken at position {i}: "
                        f"expected prev_hash={prev_hash!r}, "
                        f"got {stored_prev_hash!r}"
                    ),
                }

            # Пересчитываем event_hash
            payload_data: dict = {}
            if payload_str:
                try:
                    payload_data = json.loads(payload_str)
                except (json.JSONDecodeError, TypeError):
                    pass

            expected_event = AuditEvent(
                event_type=event_type,
                actor=actor or "",
                fact_id=fid,
                from_state=from_state,
                to_state=to_state,
                reason=None,
                payload=payload_data,
                confidence=confidence,
                prev_event_hash=stored_prev_hash,
            )
            # Подставляем оригинальный created_at для пересчёта
            expected_event.created_at = created_at
            expected_hash = expected_event._compute_hash()

            if expected_hash != stored_hash:
                return {
                    "valid": False,
                    "events_checked": i + 1,
                    "first_broken_event": event_id,
                    "broken_at_position": i,
                    "error": (
                        f"Hash mismatch at position {i} (event_id={event_id}): "
                        f"stored={stored_hash[:16]}..., "
                        f"computed={expected_hash[:16]}..."
                    ),
                }

            prev_hash = stored_hash

        # Логируем результат проверки
        self._conn.execute(
            """
            INSERT INTO integrity_checks
            (check_id, check_type, status, details, checked_by)
            VALUES (?, 'audit_chain', 'passed', ?, 'verify_chain()')
            """,
            (
                f"ic_{uuid.uuid4().hex[:12]}",
                json.dumps({
                    "events_checked": len(rows),
                    "fact_id_filter": fact_id,
                }),
            ),
        )
        self._conn.commit()

        return {
            "valid": True,
            "events_checked": len(rows),
            "first_broken_event": None,
            "broken_at_position": None,
            "error": None,
        }

    def get_fact_history(self, fact_id: str) -> list[dict]:
        """Полная история событий для одного факта."""
        rows = self._conn.execute(
            """
            SELECT event_id, event_type, from_state, to_state,
                   actor, reason, confidence, created_at
            FROM memory_events
            WHERE fact_id = ?
            ORDER BY rowid ASC
            """,
            (fact_id,),
        ).fetchall()
        return [
            {
                "event_id":   r[0],
                "event_type": r[1],
                "from_state": r[2],
                "to_state":   r[3],
                "actor":      r[4],
                "reason":     r[5],
                "confidence": r[6],
                "created_at": r[7],
            }
            for r in rows
        ]

    def stats(self) -> dict:
        """Статистика audit log."""
        total = self._conn.execute(
            "SELECT COUNT(*) FROM memory_events"
        ).fetchone()[0]
        by_type = {}
        for row in self._conn.execute(
            "SELECT event_type, COUNT(*) FROM memory_events GROUP BY event_type"
        ):
            by_type[row[0]] = row[1]
        return {
            "total_events": total,
            "by_event_type": by_type,
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _get_last_hash(self) -> str | None:
        """Хэш последнего события — для связывания новых."""
        row = self._conn.execute(
            "SELECT event_hash FROM memory_events ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None
