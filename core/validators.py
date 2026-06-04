"""
core/validators.py — Единый модуль валидации (v8.7.0)
======================================================
FIX: раньше валидация была разбросана по pipeline.py, truth_gate.py,
memory.py с разными правилами. Теперь один источник истины.

Правила:
  - confidence: float в [0.0, 1.0], не NaN, не Inf
  - source: непустая строка, не whitespace-only
  - claim: непустая строка, минимум 3 символа
  - fact_id: непустая строка, только безопасные символы
  - claim_type: модальность утверждения (v8.7, P0)
  - origin_type: откуда пришёл факт (v8.7, P0)
"""
from __future__ import annotations

import math
import re
from typing import Any

# ── ClaimType — модальность утверждения ──────────────────────────────────────

class ClaimType:
    """
    Модальность памяти — ЧТО это за утверждение по природе.

    Ключевое правило: claim_type НЕ является truth_status.
    EMOTION может быть VALIDATED как эмоция.
    Только WORLD_FACT требует внешних доказательств/источника для продвижения.

    Примеры:
        «Земля вращается вокруг Солнца»   → WORLD_FACT
        «Мне было тревожно при разговоре» → EMOTION
        «Кажется, он меня не уважает»     → INTERPRETATION
        «Хочу выучить Python»              → GOAL
    """
    WORLD_FACT    = "WORLD_FACT"      # Утверждение о внешнем мире. Требует доказательств.
    USER_EXPERIENCE = "USER_EXPERIENCE"  # Пользователь описывает пережитое. Реально как опыт.
    EMOTION       = "EMOTION"         # Внутреннее эмоциональное состояние.
    INTERPRETATION = "INTERPRETATION" # Объяснение/интерпретация события.
    OPINION       = "OPINION"         # Суждение, взгляд, оценка.
    GOAL          = "GOAL"            # Желаемое будущее состояние / намерение.
    PREFERENCE    = "PREFERENCE"      # Стабильное или временное предпочтение.
    SYSTEM_NOTE   = "SYSTEM_NOTE"     # Внутренняя служебная заметка системы.
    UNKNOWN       = "UNKNOWN"         # Fallback для старых записей или неясной классификации.

    ALL: frozenset = frozenset({
        WORLD_FACT, USER_EXPERIENCE, EMOTION, INTERPRETATION,
        OPINION, GOAL, PREFERENCE, SYSTEM_NOTE, UNKNOWN,
    })

    # Типы, которые НИКОГДА не могут стать WORLD_FACT автоматически
    # (только через независимые внешние доказательства)
    SUBJECTIVE_TYPES: frozenset = frozenset({
        EMOTION, OPINION, INTERPRETATION, PREFERENCE,
    })

    # Типы, которые могут быть VALIDATED «как есть» (без evidence_refs)
    SELF_VALIDATING: frozenset = frozenset({
        EMOTION, OPINION, INTERPRETATION, GOAL, PREFERENCE, SYSTEM_NOTE, USER_EXPERIENCE,
    })


# ── OriginType — происхождение факта ─────────────────────────────────────────

class OriginType:
    """
    Откуда пришёл факт — источник происхождения.

    ВАЖНО: не конфликтует с ESM-состоянием «Observed» (это первый шаг проверки).
    OriginType = откуда пришёл; epistemic_state = насколько проверен.

    Примеры:
        Пользователь написал «Я чувствую тревогу»      → USER_REPORTED
        Система наблюдала ошибку в логах                → SYSTEM_OBSERVED
        Вывод из двух других фактов                     → DERIVED
        Загружено из PDF/API/веба                       → EXTERNAL
        Сгенерировано LLM (само по себе не есть факт)  → LLM_OUTPUT
        Внутренний детерминированный процесс            → SYSTEM_GENERATED
    """
    USER_REPORTED     = "USER_REPORTED"     # Пользователь прямо сообщил.
    SYSTEM_OBSERVED   = "SYSTEM_OBSERVED"   # Система наблюдала из взаимодействия/логов.
    DERIVED           = "DERIVED"           # Выведено из других сохранённых фактов.
    EXTERNAL          = "EXTERNAL"          # Из документа, веба, файла, API, датасета.
    LLM_OUTPUT        = "LLM_OUTPUT"        # Сгенерировано LLM. Само по себе — не факт.
    SYSTEM_GENERATED  = "SYSTEM_GENERATED"  # Внутренний детерминированный процесс.
    UNKNOWN           = "UNKNOWN"           # Fallback при миграции или неизвестном источнике.

    ALL: frozenset = frozenset({
        USER_REPORTED, SYSTEM_OBSERVED, DERIVED, EXTERNAL,
        LLM_OUTPUT, SYSTEM_GENERATED, UNKNOWN,
    })

    # LLM_OUTPUT сам по себе НИКОГДА не является доказательством
    NEVER_EVIDENCE: frozenset = frozenset({LLM_OUTPUT})


# ── Confidence ────────────────────────────────────────────────────────────────

def validate_confidence(value: Any) -> tuple[bool, str | None]:
    """
    Проверяет confidence.
    Returns: (is_valid, error_message)

    Примеры:
        validate_confidence(0.85)           → (True, None)
        validate_confidence(float("nan"))   → (False, "NaN не допускается")
        validate_confidence(float("inf"))   → (False, "Inf не допускается")
        validate_confidence("0.8")          → (False, "Должен быть числом")
        validate_confidence(1.5)            → (False, "Должен быть в [0.0, 1.0]")
    """
    if value is None:
        return False, "confidence не может быть None"
    if not isinstance(value, (int, float)):
        return False, f"confidence должен быть числом, получено: {type(value).__name__}"
    if math.isnan(value):
        return False, "confidence NaN не допускается — используй явное число"
    if math.isinf(value):
        return False, "confidence Inf не допускается — используй явное число"
    if not (0.0 <= float(value) <= 1.0):
        return False, f"confidence должен быть в [0.0, 1.0], получено: {value}"
    return True, None


def assert_confidence(value: Any, context: str = "") -> float:
    """Проверяет confidence и бросает ValueError при ошибке."""
    ok, err = validate_confidence(value)
    if not ok:
        prefix = f"[{context}] " if context else ""
        raise ValueError(f"{prefix}{err}")
    return float(value)


# ── Source ────────────────────────────────────────────────────────────────────

def validate_source(value: Any) -> tuple[bool, str | None]:
    """
    Проверяет source.

    Примеры:
        validate_source("physics")      → (True, None)
        validate_source("")             → (False, "пустой source")
        validate_source("   ")          → (False, "whitespace-only source")
        validate_source(None)           → (False, "source не может быть None")
    """
    if value is None:
        return False, "source не может быть None"
    if not isinstance(value, str):
        return False, f"source должен быть строкой, получено: {type(value).__name__}"
    if not value:
        return False, "source не может быть пустым"
    if not value.strip():
        return False, "source не может быть whitespace-only"
    return True, None


# ── Claim ─────────────────────────────────────────────────────────────────────

def validate_claim(value: Any, min_length: int = 3) -> tuple[bool, str | None]:
    """
    Проверяет claim.

    Примеры:
        validate_claim("Вода кипит при 100°C")  → (True, None)
        validate_claim("")                       → (False, "пустой claim")
        validate_claim("AB")                     → (False, "слишком короткий")
    """
    if value is None:
        return False, "claim не может быть None"
    if not isinstance(value, str):
        return False, f"claim должен быть строкой, получено: {type(value).__name__}"
    if not value.strip():
        return False, "claim не может быть пустым или whitespace-only"
    if len(value.strip()) < min_length:
        return False, f"claim слишком короткий: {len(value.strip())} < {min_length} символов"
    return True, None


# ── Fact ID ───────────────────────────────────────────────────────────────────

_FACT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+$')

def validate_fact_id(value: Any) -> tuple[bool, str | None]:
    """
    Проверяет fact_id.

    Допустимы: буквы, цифры, _, -, .
    Запрещены: пробелы, спецсимволы, path traversal.
    """
    if value is None:
        return False, "fact_id не может быть None"
    if not isinstance(value, str):
        return False, f"fact_id должен быть строкой, получено: {type(value).__name__}"
    if not value:
        return False, "fact_id не может быть пустым"
    if not _FACT_ID_PATTERN.match(value):
        return False, (
            f"fact_id содержит недопустимые символы: {value!r}. "
            "Допустимы: буквы, цифры, _, -, ."
        )
    if len(value) > 200:
        return False, f"fact_id слишком длинный: {len(value)} > 200 символов"
    return True, None


# ── Fact dict ─────────────────────────────────────────────────────────────────

def validate_fact_dict(fact: dict) -> list[str]:
    """
    Проверяет полный dict факта.
    Returns: список ошибок (пустой = валидный).

    Использование:
        errors = validate_fact_dict(fact)
        if errors:
            raise ValidationError(errors)
    """
    errors: list[str] = []

    fid = fact.get("fact_id", "")
    ok, err = validate_fact_id(fid)
    if not ok:
        errors.append(f"fact_id: {err}")

    ok, err = validate_claim(fact.get("claim", ""))
    if not ok:
        errors.append(f"claim: {err}")

    ok, err = validate_confidence(fact.get("confidence"))
    if not ok:
        errors.append(f"confidence: {err}")

    ok, err = validate_source(fact.get("source"))
    if not ok:
        errors.append(f"source: {err}")

    return errors


# ── ClaimType / OriginType validators ────────────────────────────────────────

def validate_claim_type(value: Any) -> tuple[bool, str | None]:
    """
    Проверяет claim_type. Неизвестное значение → рекомендует UNKNOWN (не ошибка).

    Примеры:
        validate_claim_type("WORLD_FACT")    → (True, None)
        validate_claim_type("EMOTION")       → (True, None)
        validate_claim_type("nonsense")      → (False, "недопустимый claim_type: 'nonsense'")
        validate_claim_type(None)            → (True, None)  # None → UNKNOWN при сохранении
    """
    if value is None:
        return True, None   # None нормализуется в UNKNOWN при хранении
    if not isinstance(value, str):
        return False, f"claim_type должен быть строкой, получено: {type(value).__name__}"
    if value not in ClaimType.ALL:
        return False, (
            f"недопустимый claim_type: {value!r}. "
            f"Допустимые: {sorted(ClaimType.ALL)}"
        )
    return True, None


def validate_origin_type(value: Any) -> tuple[bool, str | None]:
    """
    Проверяет origin_type.

    Примеры:
        validate_origin_type("EXTERNAL")      → (True, None)
        validate_origin_type("USER_REPORTED") → (True, None)
        validate_origin_type("bad")           → (False, "недопустимый origin_type: 'bad'")
        validate_origin_type(None)            → (True, None)  # None → UNKNOWN при сохранении
    """
    if value is None:
        return True, None
    if not isinstance(value, str):
        return False, f"origin_type должен быть строкой, получено: {type(value).__name__}"
    if value not in OriginType.ALL:
        return False, (
            f"недопустимый origin_type: {value!r}. "
            f"Допустимые: {sorted(OriginType.ALL)}"
        )
    return True, None


def normalize_claim_type(value: Any) -> str:
    """Вернуть валидный claim_type; неизвестное/None → UNKNOWN."""
    if value and isinstance(value, str) and value in ClaimType.ALL:
        return value
    return ClaimType.UNKNOWN


def normalize_origin_type(value: Any) -> str:
    """Вернуть валидный origin_type; неизвестное/None → UNKNOWN."""
    if value and isinstance(value, str) and value in OriginType.ALL:
        return value
    return OriginType.UNKNOWN
