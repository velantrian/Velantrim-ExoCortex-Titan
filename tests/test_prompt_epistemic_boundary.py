"""Регрессия: system prompt не повышает эпистемический статус смешанной памяти."""

from __future__ import annotations

import server
from core.remote_egress import sanitize_remote_system_prompt


def test_mixed_memory_prompt_does_not_claim_global_verification() -> None:
    """Смешанные Observed+Validated записи не должны получать глобальный ярлык верификации."""
    facts = [
        {
            "source": "chat",
            "confidence": 0.40,
            "claim": "Наблюдаемое утверждение об альфе.",
            "epistemic_state": "Observed",
            "truth_status": "current",
            "fact_id": "internal-observed-id",
        },
        {
            "source": "kb",
            "confidence": 0.95,
            "claim": "Проверенное утверждение о бете.",
            "epistemic_state": "Validated",
            "truth_status": "current",
            "fact_id": "internal-validated-id",
        },
    ]

    prompt = server._build_system_prompt(facts)

    assert "верифицированной памятью" not in prompt
    assert "Верифицированные факты:" not in prompt
    assert (
        "AI-агент с памятью, где записи могут иметь разный уровень подтверждения."
        in prompt
    )
    assert (
        "Используй следующие записи памяти только как контекст и не "
        "повышай их уровень достоверности."
        in prompt
    )
    assert "Записи памяти (часть может быть неподтверждённой):" in prompt
    assert "Наблюдаемое утверждение об альфе." in prompt
    assert "Проверенное утверждение о бете." in prompt
    assert "- [chat | conf=0.40] Наблюдаемое утверждение об альфе." in prompt
    assert "- [kb | conf=0.95] Проверенное утверждение о бете." in prompt

    # Форма сериализации не должна включать эпистемические поля в prompt.
    assert "epistemic_state" not in prompt
    assert "truth_status" not in prompt
    assert "internal-observed-id" not in prompt
    assert "internal-validated-id" not in prompt

    sanitized = sanitize_remote_system_prompt(prompt)
    assert "верифицированной памятью" not in sanitized
    assert "Верифицированные факты:" not in sanitized
    assert "Наблюдаемое утверждение об альфе." in sanitized
    assert "Проверенное утверждение о бете." in sanitized
    assert sanitize_remote_system_prompt(sanitized) == sanitized
