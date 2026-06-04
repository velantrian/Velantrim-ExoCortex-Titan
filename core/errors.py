"""
core/errors.py — Доменные исключения Velantrim (v8.5.1)
========================================================
FIX (ChatGPT): раньше система бросала голые SQLite/Python исключения
(IntegrityError, OperationalError, ValueError) через API.

Теперь:
  - Внутри системы: ловим низкоуровневые ошибки
  - Наружу: бросаем доменные исключения с понятными сообщениями
  - FastAPI endpoint'ы перехватывают VelantrimError → 4xx/5xx с JSON

Иерархия:
    VelantrimError
    ├── MemoryError          — ошибки работы с памятью
    │   ├── FactNotFoundError
    │   ├── DuplicateFactError
    │   └── ImmutableCoreError
    ├── ValidationError      — невалидные входные данные
    ├── ESMViolationError    — нарушение ESM инварианта
    ├── RetrievalError       — ошибки поиска
    ├── TruthGateError       — ошибки верификации
    └── AuditError           — нарушение audit trail
"""
from __future__ import annotations


class VelantrimError(Exception):
    """Базовый класс всех доменных ошибок Velantrim."""
    http_status: int = 500
    error_code: str = "VELANTRIM_ERROR"

    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail

    def to_dict(self) -> dict:
        return {
            "error": self.error_code,
            "message": self.message,
            "detail": self.detail,
        }


# ── Memory errors ─────────────────────────────────────────────────────────────

class MemoryError(VelantrimError):
    """Ошибка работы с памятью."""
    error_code = "MEMORY_ERROR"


class FactNotFoundError(MemoryError):
    """Факт не найден."""
    http_status = 404
    error_code = "FACT_NOT_FOUND"

    def __init__(self, fact_id: str) -> None:
        super().__init__(
            message=f"Факт не найден: {fact_id!r}",
            detail=f"fact_id={fact_id}",
        )
        self.fact_id = fact_id


class DuplicateFactError(MemoryError):
    """Дубликат факта."""
    http_status = 409
    error_code = "DUPLICATE_FACT"

    def __init__(self, fact_id: str) -> None:
        super().__init__(
            message=f"Факт уже существует: {fact_id!r}",
            detail="Используй update() для обновления существующих фактов",
        )
        self.fact_id = fact_id


class ImmutableCoreError(MemoryError):
    """Попытка изменить ImmutableCore факт."""
    http_status = 403
    error_code = "IMMUTABLE_CORE_VIOLATION"

    def __init__(self, fact_id: str, attempted: str = "update") -> None:
        super().__init__(
            message=f"ImmutableCore факт {fact_id!r} нельзя {attempted}",
            detail="ImmutableCore факты неизменны. Для изменения нужны 2+ approvers.",
        )


# ── Validation errors ─────────────────────────────────────────────────────────

class ValidationError(VelantrimError):
    """Невалидные входные данные."""
    http_status = 422
    error_code = "VALIDATION_ERROR"

    def __init__(self, message: str, fields: list[str] | None = None) -> None:
        super().__init__(message=message, detail=str(fields) if fields else None)
        self.fields = fields or []


# ── ESM violations ────────────────────────────────────────────────────────────

class ESMViolationError(VelantrimError):
    """Нарушение инварианта ESM."""
    http_status = 422
    error_code = "ESM_VIOLATION"

    def __init__(self, from_state: str, to_state: str, fact_id: str = "") -> None:
        super().__init__(
            message=f"ESM переход {from_state!r} → {to_state!r} запрещён",
            detail=(
                f"fact_id={fact_id}. "
                "Используй transition_esm() с корректным путём."
            ),
        )
        self.from_state = from_state
        self.to_state = to_state


# ── Retrieval errors ──────────────────────────────────────────────────────────

class RetrievalError(VelantrimError):
    """Ошибка поиска."""
    http_status = 500
    error_code = "RETRIEVAL_ERROR"


# ── TruthGate errors ──────────────────────────────────────────────────────────

class TruthGateError(VelantrimError):
    """Ошибка верификации."""
    http_status = 422
    error_code = "TRUTH_GATE_ERROR"


# ── Audit errors ──────────────────────────────────────────────────────────────

class AuditError(VelantrimError):
    """Нарушение целостности audit trail."""
    http_status = 500
    error_code = "AUDIT_INTEGRITY_ERROR"


# ── Helper: нормализация SQLite ошибок ───────────────────────────────────────

def normalize_sqlite_error(exc: Exception, fact_id: str = "") -> VelantrimError:
    """
    Конвертирует SQLite исключения в доменные.

    Использование:
        try:
            conn.execute(...)
        except Exception as e:
            raise normalize_sqlite_error(e, fact_id) from e
    """
    import sqlite3
    msg = str(exc).lower()

    if isinstance(exc, sqlite3.IntegrityError):
        if "unique" in msg or "duplicate" in msg:
            return DuplicateFactError(fact_id)
        if "immutablecore" in msg or "immutable" in msg:
            return ImmutableCoreError(fact_id)
        if "esm violation" in msg or "esm" in msg:
            return ESMViolationError("unknown", "unknown", fact_id)

    if isinstance(exc, sqlite3.OperationalError):
        if "no such table" in msg:
            return MemoryError(
                "Таблица БД не найдена. Запусти миграции.",
                detail=str(exc),
            )

    return MemoryError(f"Ошибка базы данных: {exc}", detail=str(exc))
