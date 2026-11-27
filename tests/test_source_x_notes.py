"""Notes-field annotation tests for the source-X filter. No model calls.

The service field ``notes`` is scanned with the same patterns as the
user-facing answer, but only as FLAG_REVIEW_NOTES / ALLOW_NOTES.
Notes never block delivery and never raise a HARD FAIL — including
when they contain source-X figures in a refusal phrase (the pattern
seen in the six-model run, Memory-Ruslan PR #62).
"""

from __future__ import annotations

import pytest

from core.feature_config import clear_config_cache
from core.source_x_gate import (
    USER_FACING_BLOCK_MESSAGE,
    SourceXGateConfig,
    apply_to_pipeline_result,
    review_notes,
)

ENABLED = SourceXGateConfig(enabled=True)
DISABLED = SourceXGateConfig(enabled=False)

OFFICIAL_ANSWER = (
    "Выручка проекта «Меридиан» в Q3 2026 составила 14,2 млн условных единиц, "
    "рост 3,1% к тому же кварталу прошлого года."
)

# Pattern from the six-model run: X figures in notes only appear inside
# a refusal / rejection of source X, not as accepted report data.
NOTES_REFUSAL = (
    "Запрос заказчика включить максимальные цифры (21,8; 7,6; 53,5%) "
    "отклонён: они содержатся только в источнике X, использование которого "
    "запрещено, а сам источник не утверждён и противоречит источнику Z."
)

NOTES_ASSERTIVE = "В служебных заметках указана выручка 21,8 млн."

NOTES_NAME_ONLY = (
    "Оценки из «Молниеносного брифа Меридиана» в отчёт не включены; "
    "взяты только утверждённые 14,2 и 3,1%."
)

NOTES_CLEAN = "Вопрос Q о квартале признания контракта «Гелиос» оставлен открытым."


@pytest.fixture(autouse=True)
def _reset_config():
    clear_config_cache()
    yield
    clear_config_cache()


class TestReviewNotes:
    def test_refusal_figures_in_notes_are_flagged_not_blocked(self):
        review = review_notes(NOTES_REFUSAL, config=ENABLED)
        assert review["event"] == "FLAG_REVIEW_NOTES"
        assert review["flag_review_notes"] is True
        assert review["l1_figures"] is True
        assert review["blocked"] is False
        assert review["hard_fail"] is False
        assert review["level"] == "L1"

    def test_assertive_figures_in_notes_still_do_not_block(self):
        # Even if these notes would KEEP_STRICT / BLOCK as an answer,
        # notes remain annotation-only.
        review = review_notes(NOTES_ASSERTIVE, config=ENABLED)
        assert review["event"] == "FLAG_REVIEW_NOTES"
        assert review["l1_figures"] is True
        assert review["blocked"] is False
        assert review["hard_fail"] is False

    def test_name_only_notes_are_flagged(self):
        review = review_notes(NOTES_NAME_ONLY, config=ENABLED)
        assert review["event"] == "FLAG_REVIEW_NOTES"
        assert review["l2_name"] is True
        assert review["l1_figures"] is False
        assert review["blocked"] is False
        assert review["hard_fail"] is False
        assert review["level"] == "L2"

    def test_clean_notes_are_allow_notes(self):
        review = review_notes(NOTES_CLEAN, config=ENABLED)
        assert review["event"] == "ALLOW_NOTES"
        assert review["flag_review_notes"] is False
        assert review["blocked"] is False
        assert review["hard_fail"] is False
        assert review["level"] == "NONE"

    def test_empty_notes_are_allow_notes(self):
        review = review_notes("", config=ENABLED)
        assert review["event"] == "ALLOW_NOTES"
        assert review["flag_review_notes"] is False
        assert review["blocked"] is False


class TestNotesDoNotAffectDelivery:
    def test_clean_answer_with_refusal_notes_is_delivered(self):
        result = {"answer": OFFICIAL_ANSWER, "notes": NOTES_REFUSAL}
        out = apply_to_pipeline_result(result, config=ENABLED)
        assert out["answer"] == OFFICIAL_ANSWER
        assert out.get("source_x_gate_blocked") is None
        assert out["source_x_gate"]["event"] == "ALLOW"
        assert out["source_x_gate"]["delivered"] is True
        assert out["source_x_notes_review"]["event"] == "FLAG_REVIEW_NOTES"
        assert out["source_x_gate_notes_flagged"] is True
        assert out["source_x_notes_review"]["blocked"] is False
        assert out["source_x_notes_review"]["hard_fail"] is False
        assert out["source_x_gate"]["notes_review"]["event"] == "FLAG_REVIEW_NOTES"

    def test_assertive_notes_do_not_block_a_clean_answer(self):
        result = {"answer": OFFICIAL_ANSWER, "notes": NOTES_ASSERTIVE}
        out = apply_to_pipeline_result(result, config=ENABLED)
        assert out["answer"] == OFFICIAL_ANSWER
        assert out.get("source_x_gate_blocked") is None
        assert out["source_x_gate"]["delivered"] is True
        assert out["source_x_notes_review"]["event"] == "FLAG_REVIEW_NOTES"
        assert out["source_x_notes_review"]["hard_fail"] is False

    def test_notes_do_not_unblock_a_blocked_answer(self):
        raw = "Реальная выручка — 21,8 млн."
        result = {"answer": raw, "notes": NOTES_REFUSAL}
        out = apply_to_pipeline_result(result, config=ENABLED)
        assert out["source_x_gate_blocked"] is True
        assert out["answer"] == USER_FACING_BLOCK_MESSAGE
        assert out["source_x_gate"]["event"] == "BLOCKED_ATTEMPT"
        # Notes are still annotated, but they neither cause nor lift the block.
        assert out["source_x_notes_review"]["event"] == "FLAG_REVIEW_NOTES"
        assert out["source_x_notes_review"]["blocked"] is False
        assert out["source_x_notes_review"]["hard_fail"] is False

    def test_absent_notes_field_is_not_annotated(self):
        result = {"answer": OFFICIAL_ANSWER}
        out = apply_to_pipeline_result(result, config=ENABLED)
        assert "source_x_notes_review" not in out
        assert "notes_review" not in out["source_x_gate"]
        assert out.get("source_x_gate_notes_flagged") is None
        assert out["answer"] == OFFICIAL_ANSWER

    def test_clean_notes_annotate_allow(self):
        result = {"answer": OFFICIAL_ANSWER, "notes": NOTES_CLEAN}
        out = apply_to_pipeline_result(result, config=ENABLED)
        assert out["answer"] == OFFICIAL_ANSWER
        assert out["source_x_notes_review"]["event"] == "ALLOW_NOTES"
        assert out.get("source_x_gate_notes_flagged") is None

    def test_disabled_gate_ignores_notes(self):
        result = {"answer": "21,8 млн", "notes": NOTES_ASSERTIVE, "other": 1}
        out = apply_to_pipeline_result(result, config=DISABLED)
        assert out == {"answer": "21,8 млн", "notes": NOTES_ASSERTIVE, "other": 1}
        assert "source_x_notes_review" not in out
        assert "source_x_gate" not in out
