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

DEPRECATED compatibility shims:
- ForgettingEngine.forget_all() delegates to the durable, resumable batch
  erasure saga in core.erasure_batch_coordinator.
- ForgettingEngine.forget_one() delegates to the durable single-fact erasure
  authority in core.erasure_coordinator. It no longer owns a second raw-SQL
  physical-delete path.
- ForgettingEngine.redact_pii_fact()/redact_pii_batch() delegate canonical
  claim mutation to core.pii_redaction.CanonicalPiiRedactor. They no longer
  own direct raw-SQL UPDATE paths.

These shims preserve the legacy ForgetVerdict surface while the durable
coordinators/canonical redaction service remain authoritative for mutation
completion and evidence. REDACT_PII is claim-surface redaction, not physical
Art. 17 erasure of every raw origin/projection; use the erasure coordinators
when complete data-subject deletion is required.
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.embedding_store import EmbeddingStore
    from core.ngram_index import NGramIndex

logger = logging.getLogger("velantrim.forgetting")

SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim.db")


def _normalize_tenant_path(path: str | None) -> str | None:
    """Round 5.4 seventh-order fix (Codex P2): a blank/whitespace-only
    tenant storage path must be treated exactly like a MISSING one — never
    silently accepted as "explicitly configured". `sqlite3.connect("")`
    happily opens a throwaway temporary database, so an unnormalized blank
    `embedding_db_path`/`ngram_db_path` (e.g. wired from an empty env/config
    value) would let a tenant's real storage go unchecked while a scratch
    file reports a clean, empty result."""
    if path is None:
        return None
    stripped = path.strip()
    return stripped or None


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


def _batch_report_to_allowed(report: Dict[str, Any]) -> bool:
    """Round 5.4 fix (Codex P2): the ONE place that converts a
    BatchErasureCoordinator report into the legacy ForgetVerdict.allowed
    field — replaces the old ad-hoc `operation_finished or outcome ==
    "PARTIAL"` mapping.

    `operation_finished` means only that the batch reached a terminal
    EXECUTION state — SUBJECT_CONFLICT (Round 5.3) is terminal too,
    precisely so it never auto-retries forever, but a terminal subject
    conflict is NOT an allowed/successfully-completed erasure. Mapping
    terminality straight to "allowed" silently claimed success for a
    batch where the conflicting fact was never actually erased.

    A critical-compliance finding (compliance_status, tracked
    independently of the execution outcome — see
    BatchErasureCoordinator._report()) must also never be reported as
    allowed, even though its execution outcome can itself be COMPLETE.

    COMPLETE_WITH_RESIDUAL keeps its pre-existing, deliberate "allowed"
    contract (the derived layer really is gone; the raw-original residual
    is a documented, known limitation, not a failure) — explicitly listed
    here, not incidentally caught by a "terminal" check.

    Every other outcome (PARTIAL/FAILED/RUNNING/anything still in
    progress) is not allowed — a caller must resubmit/resume to actually
    reach completion, exactly like every other still-in-progress state.
    """
    if report.get("critical_compliance_violation") or report.get("subject_conflict"):
        return False
    return report["outcome"] in ("COMPLETE", "COMPLETE_WITH_RESIDUAL")


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

    def __init__(
        self,
        db_path: str = SQLITE_PATH,
        *,
        embedding_db_path: str | None = None,
        embedding_store: EmbeddingStore | None = None,
        ngram_db_path: str | None = None,
        ngram_index: NGramIndex | None = None,
    ):
        """`embedding_db_path`/`embedding_store` (Round 5.4 sixth-order fix,
        Codex P2) and `ngram_db_path`/`ngram_index` (Round 5.4 seventh-order
        fix, Codex P2): a custom, non-global `db_path` used to leave the
        durable erasure coordinators with NO tenant-scoped embeddings/ngram
        backends at all — they would lazily default to process-global stores
        unrelated to this tenant's own storage. A tenant's derived index row
        could then survive erasure entirely undetected while the caller
        reports completion — a GDPR Art. 17 false-success condition.

        The defaults (all None) preserve the exact pre-existing global
        behavior for the default `db_path`. A blank/whitespace-only
        `embedding_db_path`/`ngram_db_path` is normalized to "not configured"
        (see `_normalize_tenant_path()`) — never silently treated as an
        explicit tenant path.
        """
        self._db_path = db_path
        self._embedding_db_path = embedding_db_path
        self._injected_embedding_store = embedding_store
        self._ngram_db_path = ngram_db_path
        self._injected_ngram_index = ngram_index

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
        """Compatibility adapter over the durable single-fact erasure authority.

        `ErasureCoordinator` owns physical deletion, dependency/projection
        cleanup, durable job receipts, residual semantics, and completion
        tombstones. This legacy method only preserves the preflight warning
        surface and maps the durable report into `ForgetVerdict`.
        """
        verdict = self.check(fact_id)
        if not verdict.allowed and "immutable" in verdict.reason:
            return verdict

        from core.erasure_coordinator import COMPLETE, NOT_FOUND, ErasureCoordinator
        from core.memory import SQLiteGraphStore

        store = None
        try:
            # Resolve every tenant backend before opening the facts store so a
            # misconfigured tenant fails closed before any destructive work.
            embedding_store, embedding_db_path = self._bind_tenant_embedding_store()
            ngram_index = self._bind_tenant_ngram_index()

            store = SQLiteGraphStore(self._db_path)
            store.ensure_schema()
            coordinator = ErasureCoordinator(
                store=store,
                embedding_store=embedding_store,
                embedding_db_path=embedding_db_path,
                ngram_index=ngram_index,
            )
            report = coordinator.erase_fact_durable(
                fact_id,
                reason=reason,
                actor=user_id,
                subject_user_id=user_id,
            )
        except Exception as exc:
            logger.error("Forgetting.forget_one: %s", exc)
            return ForgetVerdict(
                allowed=False,
                reason=f"store_error: {exc}",
                details=[f"❌ Ошибка при удалении {fact_id}: {exc}"],
            )
        finally:
            if store is not None:
                store.close()

        outcome = report["outcome"]
        if outcome == COMPLETE:
            erased_now = bool(report.get("erased_now"))
            if erased_now:
                self._log_forgetting(fact_id, reason, user_id)
            logger.info(
                "Forgetting: durable erasure %s for %s (reason=%s, user=%s, job=%s)",
                "completed" if erased_now else "already complete",
                fact_id,
                reason,
                user_id,
                report.get("job_id"),
            )
            return ForgetVerdict(
                allowed=True,
                reason="deleted" if erased_now else "already_deleted",
                affected_facts=verdict.affected_facts + 1 if erased_now else 0,
                details=[
                    (
                        f"✅ Факт {fact_id} удалён через durable ErasureCoordinator."
                        if erased_now
                        else f"ℹ️ Факт {fact_id} уже был durably удалён ранее."
                    ),
                    f"Erasure job: {report.get('job_id')}",
                ] + (verdict.details if erased_now else []),
            )

        if outcome == NOT_FOUND:
            return ForgetVerdict(
                allowed=False,
                reason="fact_not_found",
                details=verdict.details or [f"Факт {fact_id} не найден."],
            )

        # Any non-COMPLETE durable outcome must remain fail-closed here.
        # In particular RESIDUAL_IMMUTABLE_DATA means the derived layer may
        # be gone while immutable raw-origin data remains; that is not a
        # complete GDPR erasure and must never be translated into success.
        return ForgetVerdict(
            allowed=False,
            reason=str(outcome).lower(),
            affected_facts=0,
            details=[
                f"❌ Durable erasure не достиг полного COMPLETE для {fact_id}.",
                f"Outcome: {outcome}",
                f"Residual: {report.get('residual')}",
                f"Erasure job: {report.get('job_id')}",
            ],
        )

    # ── FORGET_ALL (GDPR) ─────────────────────────────────────────────────

    def _is_global_db_path(self) -> bool:
        return os.path.abspath(self._db_path) == os.path.abspath(SQLITE_PATH)

    def _bind_tenant_embedding_store(self) -> tuple[EmbeddingStore | None, str | None]:
        """Resolve what durable erasure must bind to the embeddings backend:
        either a real, externally-injected `EmbeddingStore` (returned as-is),
        or a bare tenant PATH string (never both — an injected object always
        wins when both are given).

        A custom, non-global `db_path` must never silently use the global
        embeddings store: that can leave tenant vectors unerased while a
        coordinator checks an unrelated file and reports success.

        The path-only case stays lazy so merely configuring a tenant path does
        not require importing the optional numpy-dependent embeddings module.
        Returns `(None, None)` only for the default/global `db_path`.
        """
        if self._injected_embedding_store is not None:
            return self._injected_embedding_store, None
        embedding_db_path = _normalize_tenant_path(self._embedding_db_path)
        if embedding_db_path is not None:
            return None, embedding_db_path
        if self._is_global_db_path():
            return None, None
        raise ValueError(
            f"ForgettingEngine(db_path={self._db_path!r}) is a custom tenant "
            "database, but no tenant embedding storage was configured "
            "(embedding_db_path=... or embedding_store=...). Refusing to "
            "silently fall back to the process-global embeddings store — "
            "that could let a tenant's real gs_vectors row survive erasure "
            "undetected. Pass embedding_db_path=... or embedding_store=... "
            "to ForgettingEngine()."
        )

    def _bind_tenant_ngram_index(self) -> NGramIndex | None:
        """Resolve the ngram backend for durable erasure.

        A custom tenant `db_path` must use an explicitly injected/path-bound
        NGramIndex. Only the default/global facts DB may use the global ngram
        fallback. Blank/whitespace paths are treated as missing.
        """
        if self._injected_ngram_index is not None:
            return self._injected_ngram_index
        ngram_db_path = _normalize_tenant_path(self._ngram_db_path)
        if ngram_db_path is not None:
            from core.ngram_index import NGramIndex

            return NGramIndex(ngram_db_path)
        if self._is_global_db_path():
            return None
        raise ValueError(
            f"ForgettingEngine(db_path={self._db_path!r}) is a custom tenant "
            "database, but no tenant ngram storage was configured "
            "(ngram_db_path=... or ngram_index=...). Refusing to silently "
            "fall back to the process-global ngram index — that could let "
            "tenant search data survive erasure undetected. Pass "
            "ngram_db_path=... or ngram_index=... to ForgettingEngine()."
        )

    def forget_all(
        self,
        *,
        user_id: str = "default",
        reason: str = "gdpr_request",
        dry_run: bool = False,
        force: bool = False,
        actor: str = "operator",
        actor_capability: str = "reader",
        scope: str | None = None,
        idempotency_key: str | None = None,
    ) -> ForgetVerdict:
        """DEPRECATED — delegates to
        core.erasure_batch_coordinator.forget_all_durable().

        This used to run its own single-pass, single-transaction delete
        with no durable record of which fact_ids it decided to erase
        before deleting them, and treated any fact whose epistemic_state
        was 'ImmutableCore' as an automatic, silent GDPR exemption. The
        enforced entrypoint is now the durable, resumable batch saga in
        core.erasure_batch_coordinator — see there for the full batch
        state machine, the durable snapshot/idempotency-key/resumability
        model, and why ImmutableCore is treated as a CRITICAL compliance
        finding (not an exemption) when it holds data matched by a
        user_id filter.

        Kept for backward compatibility only — new code (and the
        registered `forget_all` MCP tool, which keeps its own global
        application wiring via forget_all_durable()/get_batch_coordinator()
        unchanged) should call
        core.erasure_batch_coordinator.forget_all_durable() directly to
        get the full batch report (items/outcome/critical items); this
        shim narrows that down to the legacy ForgetVerdict shape.

        Round 5 fix (Codex P2): this shim used to delegate to the
        module-level forget_all_durable()/get_batch_coordinator() — those
        always operate on the process-global memory._GLOBAL_STORE,
        regardless of the `db_path` this ForgettingEngine was constructed
        with. A caller doing ForgettingEngine(db_path="tenant.db").
        forget_all(...) therefore ran the operation against the GLOBAL
        store, silently ignoring "tenant.db" — reporting success (or zero
        matching items) while the actually-configured database was never
        touched. This method now builds its own db_path-bound
        SQLiteGraphStore/ErasureCoordinator/BatchErasureCoordinator (mirrors
        core.erasure_batch_coordinator.BatchErasureCoordinator's own
        dependency-injection design) instead of touching the global
        singleton at all, so a custom db_path is honored for real, for both
        dry-run and actual erasure — and closes its own temporary store
        afterward (never the shared global one, since it's never assigned
        to memory._GLOBAL_STORE).

        Round 5.2 fix (Codex P2): SQLiteGraphStore's DDL (the `facts` table
        included) is initialized LAZILY, on first use via `_db()` — but
        BatchErasureCoordinator._create_batch_snapshot() queries `facts`
        through its OWN raw connection, never through this `store` object,
        so that lazy trigger never fired for a genuinely new/nonexistent
        `db_path`. A truly virgin tenant database raised
        `sqlite3.OperationalError: no such table: facts` instead of
        reporting zero matching facts. `store.ensure_schema()` — one
        explicit, deterministic call, no fake read/write of real data —
        forces that initialization up front, before either coordinator is
        even constructed. A genuinely corrupt/unreadable database file
        still raises its real sqlite3 error here, unmasked.
        """
        warnings.warn(
            "core.forgetting.ForgettingEngine.forget_all() is deprecated — "
            "use core.erasure_batch_coordinator.forget_all_durable() directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        from core.erasure_batch_coordinator import BatchErasureCoordinator
        from core.erasure_coordinator import ErasureCoordinator
        from core.memory import SQLiteGraphStore

        # Round 5.4 sixth/seventh-order fix (Codex P2): resolved/validated
        # BEFORE any facts store is even opened — a misconfigured tenant
        # db_path must fail closed before touching a single fact, never
        # partway through a destructive operation. Neither call here ever
        # imports core.embedding_store (numpy) for the path-only case — see
        # _bind_tenant_embedding_store()'s own docstring.
        embedding_store, embedding_db_path = self._bind_tenant_embedding_store()
        ngram_index = self._bind_tenant_ngram_index()

        store = SQLiteGraphStore(self._db_path)
        try:
            store.ensure_schema()
            coordinator = ErasureCoordinator(
                store=store,
                embedding_store=embedding_store,
                embedding_db_path=embedding_db_path,
                ngram_index=ngram_index,
            )
            batch_coordinator = BatchErasureCoordinator(
                store=store, coordinator=coordinator, jobs_db_path=self._db_path,
            )
            report = batch_coordinator.forget_all_durable(
                user_id,
                reason=reason,
                actor=actor,
                actor_capability=actor_capability,
                force=force,
                scope=scope,
                dry_run=dry_run,
                idempotency_key=idempotency_key,
            )
        finally:
            # Only the facts store's connection is ever explicitly closed
            # here — it's the only backend this method (or ErasureCoordinator)
            # ever holds a real persistent connection for. Embeddings/ngram
            # backends (injected, path-resolved, or lazily constructed deep
            # inside ErasureCoordinator) each open and close their own
            # connection per call and are never owned/closed here; an
            # externally injected embedding_store/ngram_index's lifecycle
            # always belongs to whoever created/injected it.
            store.close()

        if report["outcome"] in ("REFUSED", "IDEMPOTENCY_CONFLICT"):
            return ForgetVerdict(
                allowed=False,
                reason=report.get("reason") or report["outcome"].lower(),
                details=[f"❌ FORGET_ALL отклонён: {report.get('reason') or report['outcome']}"],
            )

        if report.get("dry_run"):
            return ForgetVerdict(
                allowed=True,
                reason="dry_run",
                affected_facts=report["would_erase"],
                details=[
                    f"🔍 Dry run: будет удалено {report['would_erase']} фактов.",
                    f"🛡️ Ring Zero пропущено: {len(report['ring_zero_skipped_items'])}",
                    f"⚠️ Потенциальные CRITICAL (ImmutableCore): "
                    f"{len(report['would_be_critical_items'])}",
                    f"Пользователь: {user_id}",
                ],
            )

        details = [
            f"Batch {report['batch_id']}: outcome={report['outcome']}, "
            f"items_total={report['items_total']}",
        ]
        if report["critical_compliance_violation"]:
            details.append(
                f"🚨 CRITICAL: {len(report['critical_items'])} персональных "
                f"фактов обнаружено в ImmutableCore — требуется ручная проверка. "
                f"fact_id: {report['critical_items']}"
            )

        return ForgetVerdict(
            # Round 5.4 fix (Codex P2): see _batch_report_to_allowed() —
            # `operation_finished` alone is never sufficient (SUBJECT_
            # CONFLICT is terminal too, but not a successful erasure).
            allowed=_batch_report_to_allowed(report),
            reason=report["outcome"].lower(),
            affected_facts=report["items_total"],
            details=details,
        )

    # ── REDACT_PII ────────────────────────────────────────────────────────

    def redact_pii_fact(self, fact_id: str) -> ForgetVerdict:
        """Redact PII from one fact through the canonical redaction authority.

        The compatibility result remains a ``ForgetVerdict``.  The mutation
        itself is owned by ``CanonicalPiiRedactor`` so current Canon,
        sanitized VersionStore evidence, AuditChain, FTS and active outbox
        intent share the required transaction semantics.
        """
        from core.memory import SQLiteGraphStore
        from core.pii_redaction import (
            CanonicalPiiRedactor,
            PiiRedactionConcurrentModification,
        )

        store = SQLiteGraphStore(self._db_path)
        try:
            result = CanonicalPiiRedactor(store).redact_fact(fact_id, redact_pii)
        except PiiRedactionConcurrentModification:
            return ForgetVerdict(
                allowed=False,
                reason="concurrent_modification",
                details=[f"Факт {fact_id} изменился конкурентно; redaction не применён."],
            )
        except Exception as exc:
            logger.error("Forgetting.redact_pii: %s", exc)
            return ForgetVerdict(allowed=False, reason=f"store_error: {exc}")
        finally:
            store.close()

        if result.status == "fact_not_found":
            return ForgetVerdict(allowed=False, reason="fact_not_found")
        if result.status == "no_pii_found":
            return ForgetVerdict(
                allowed=True,
                reason="no_pii_found",
                details=[f"PII не обнаружено в факте {fact_id}."],
            )
        logger.info("PII redacted canonically: %s", fact_id)
        return ForgetVerdict(
            allowed=True,
            reason="redacted",
            redacted_count=result.redacted_count,
            details=[f"✅ PII удалён из claim факта {fact_id}."],
        )

    def redact_pii_batch(self, limit: int = 100) -> ForgetVerdict:
        """Atomically redact PII claims in one bounded selected batch."""
        from core.memory import SQLiteGraphStore
        from core.pii_redaction import (
            CanonicalPiiRedactor,
            PiiRedactionConcurrentModification,
        )

        store = SQLiteGraphStore(self._db_path)
        try:
            result = CanonicalPiiRedactor(store).redact_batch(limit, redact_pii)
        except PiiRedactionConcurrentModification:
            return ForgetVerdict(
                allowed=False,
                reason="concurrent_modification",
                details=["Пакет redaction откатан: один из фактов изменился конкурентно."],
            )
        except Exception as exc:
            logger.error("Forgetting.redact_pii_batch: %s", exc)
            return ForgetVerdict(allowed=False, reason=f"store_error: {exc}")
        finally:
            store.close()

        return ForgetVerdict(
            allowed=True,
            reason="batch_redacted",
            redacted_count=result.redacted_count,
            details=[
                f"✅ Обезличено {result.redacted_count} фактов "
                f"из {result.scanned_count}."
            ],
        )

    # ── Вспомогательные ──────────────────────────────────────────────────

    def get_erasure_log(
        self, *, user_id: str = "", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        GDPR-аудит: получить записи об удалениях.

        Если user_id пустой — все записи (для административного аудита).
        Иначе — только для конкретного пользователя.
        """
        try:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row

            if user_id:
                rows = conn.execute(
                    """SELECT * FROM erasure_audit
                       WHERE user_id = ?
                       ORDER BY erased_at DESC
                       LIMIT ?""",
                    (user_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM erasure_audit ORDER BY erased_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as exc:
            logger.error("get_erasure_log: %s", exc)
            return []

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
        fact_id: str,
        reason: str,
        user_id: str,
        extra: Optional[Dict] = None,
    ) -> None:
        """Record legacy provenance evidence after durable completion.

        This is compatibility side evidence only. It never determines whether
        deletion completed; `ErasureCoordinator`'s durable job/tombstone is
        authoritative. Provenance failure is therefore logged but cannot turn
        an already-completed erasure into a false failure.
        """
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
        except ImportError:
            logger.debug("ProvenanceChain не инициализирован — событие забывания не записано")
        except Exception as exc:
            logger.warning("ProvenanceChain append failed for %s: %s", fact_id, exc)


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
