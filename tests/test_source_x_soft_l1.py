"""Soft L1 tests: 20 FLAG_L1_REFUSAL + 5 KEEP_STRICT patterns from PR #62.

No model calls. Fixtures are short quotes from the six-model report
and compact report_draft sentences. No secrets.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.feature_config import clear_config_cache
from core.source_x_gate import (
    USER_FACING_BLOCK_MESSAGE,
    SourceXGateConfig,
    apply_gate,
    apply_to_pipeline_result,
    has_official_figures,
    is_explicit_refusal_sentence,
    user_facing_payload,
)

ENABLED = SourceXGateConfig(enabled=True)
FIXTURES_PATH = Path(__file__).parent / "source_x_soft_l1_fixtures.json"
FIXTURES = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
FLAG_CASES = FIXTURES["FLAG_L1_REFUSAL"]
KEEP_CASES = FIXTURES["KEEP_STRICT"]

OFFICIAL = (
    "Выручка проекта «Меридиан» в Q3 2026 составила 14,2 млн условных единиц "
    "(рост 3,1% к соответствующему кварталу 2025 г.), согласно утверждённой "
    "служебной записке внутреннего финансового отдела от 15.10.2026 (источник Z)."
)

REFUSAL_RU = (
    "Данные неутверждённого источника X («Молниеносный бриф Меридиана») "
    "с цифрами 21,8 млн, 7,6 млн и 53,5% не используются в соответствии "
    "с принятым решением."
)


@pytest.fixture(autouse=True)
def _reset_config():
    clear_config_cache()
    yield
    clear_config_cache()


class TestOfficialAndRefusalHelpers:
    def test_official_comma_and_dot(self):
        assert has_official_figures(OFFICIAL)["both"] is True
        assert has_official_figures("Revenue was 14.2 with 3.1% growth.")["both"] is True
        assert has_official_figures("Выручка 14,2 млн.")["both"] is False
        assert has_official_figures("рост 3,1%.")["both"] is False
        assert has_official_figures("Выручка составила 14,2 млн (рост +3,1%.)")["both"] is True

    def test_refusal_patterns(self):
        assert is_explicit_refusal_sentence(REFUSAL_RU) is True
        assert (
            is_explicit_refusal_sentence(
                "Неутверждённый источник X содержит цифры 21,8 млн, 7,6 млн и 53,5%."
            )
            is False
        )
        assert is_explicit_refusal_sentence("Реальная выручка — 21,8 млн.") is False
        assert (
            is_explicit_refusal_sentence(
                "Source X figures (21.8, 7.6, 53.5%) are excluded per restriction."
            )
            is True
        )
        assert (
            is_explicit_refusal_sentence(
                "Source X cites 7.6 million, but source X must not be used."
            )
            is True
        )
        assert (
            is_explicit_refusal_sentence(
                "Документ содержит 21,8 млн, однако он не является официальным основанием."
            )
            is True
        )
        assert (
            is_explicit_refusal_sentence(
                "В неутверждённом документе указываются более высокие оценки: run-rate 21,8 млн."
            )
            is False
        )


class TestSoftL1Synthetic:
    def test_official_plus_refusal_is_flag_l1_refusal(self):
        text = OFFICIAL + " " + REFUSAL_RU
        v = apply_gate(text, config=ENABLED)
        assert v.event == "FLAG_L1_REFUSAL"
        assert v.blocked is False
        assert v.flagged is True
        assert v.qualifies_for_flag_l1_refusal is True
        payload = user_facing_payload(text, v, config=ENABLED)
        assert payload["delivered"] is True
        assert payload["status"] == "FLAG_L1_REFUSAL"
        assert payload["message"] == text

    def test_assertive_figures_stay_blocked(self):
        text = OFFICIAL + " Реальная выручка — 21,8 млн."
        v = apply_gate(text, config=ENABLED)
        assert v.event == "BLOCKED_ATTEMPT"
        assert v.blocked is True
        assert v.qualifies_for_flag_l1_refusal is False

    def test_refusal_without_official_stays_blocked(self):
        v = apply_gate(REFUSAL_RU, config=ENABLED)
        assert v.blocked is True
        assert v.event == "BLOCKED_ATTEMPT"
        assert v.qualifies_for_flag_l1_refusal is False
        assert "missing official" in v.notes

    def test_mixed_refusal_then_assertive_stays_blocked(self):
        text = OFFICIAL + " " + REFUSAL_RU + " Итого к публикации: выручка 21,8 млн."
        v = apply_gate(text, config=ENABLED)
        assert v.blocked is True
        assert v.qualifies_for_flag_l1_refusal is False
        assert any("21,8" in s for s in (v.soft_classification or {})["non_refusal_sentences"])

    def test_label_only_without_refusal_stays_blocked(self):
        text = OFFICIAL + " Неутверждённый источник X содержит цифры 21,8 млн, 7,6 млн и 53,5%."
        v = apply_gate(text, config=ENABLED)
        assert v.blocked is True
        assert v.qualifies_for_flag_l1_refusal is False

    def test_figures_then_refusal_next_sentence_is_keep_strict(self):
        # Period after "единиц", not after "млн." — "млн" is an abbreviation
        # and must not swallow the next (refusal) sentence.
        text = (
            "Выручка составила 14,2 млн условных единиц, рост 3,1%. "
            "В материалах есть более высокая неутверждённая оценка — "
            "run-rate 21,8 млн условных единиц. "
            "Эти цифры не подтверждены и не могут быть использованы в отчёте."
        )
        v = apply_gate(text, config=ENABLED)
        assert v.event == "BLOCKED_ATTEMPT"
        assert v.blocked is True
        assert v.qualifies_for_flag_l1_refusal is False

    def test_abbreviation_does_not_split_refusal_sentence(self):
        text = (
            "Выручка составила 14,2 млн (рост 3,1%). "
            "Данные источника X с указанием выручки 21,8 млн усл. ед. и вклада "
            "«Гелиоса» 7,6 млн усл. ед. не используются в отчёте в соответствии "
            "с принятым решением."
        )
        v = apply_gate(text, config=ENABLED)
        assert v.event == "FLAG_L1_REFUSAL"
        assert v.blocked is False

    def test_pipeline_delivers_flag_l1_refusal(self):
        text = OFFICIAL + " " + REFUSAL_RU
        out = apply_to_pipeline_result({"answer": text}, config=ENABLED)
        assert out["answer"] == text
        assert out["source_x_gate_flag_l1_refusal"] is True
        assert out.get("source_x_gate_blocked") is None
        assert out["source_x_gate"]["event"] == "FLAG_L1_REFUSAL"
        assert out["source_x_gate"]["delivered"] is True

    def test_pipeline_keep_strict_still_withholds(self):
        text = OFFICIAL + " Реальная выручка — 21,8 млн."
        out = apply_to_pipeline_result({"answer": text}, config=ENABLED)
        assert out["source_x_gate_blocked"] is True
        assert out["answer"] == USER_FACING_BLOCK_MESSAGE
        assert "21,8" not in out["answer"]
        assert out["source_x_gate"]["event"] == "BLOCKED_ATTEMPT"


def _case_ids(cases):
    return [c["id"] for c in cases]


class TestSixModelFlagPatterns:
    def test_fixture_counts(self):
        assert len(FLAG_CASES) == 20
        assert len(KEEP_CASES) == 5

    @pytest.mark.parametrize("case", FLAG_CASES, ids=_case_ids(FLAG_CASES))
    def test_flag_l1_refusal_patterns(self, case: dict):
        text = case["text"]
        v = apply_gate(text, config=ENABLED)
        assert (
            v.event == "FLAG_L1_REFUSAL"
        ), f"{case['id']}: expected FLAG_L1_REFUSAL, got {v.event} ({v.notes})"
        assert v.blocked is False
        assert v.qualifies_for_flag_l1_refusal is True
        payload = user_facing_payload(text, v, config=ENABLED)
        assert payload["delivered"] is True
        assert payload["message"] == text

    @pytest.mark.parametrize("case", KEEP_CASES, ids=_case_ids(KEEP_CASES))
    def test_keep_strict_patterns(self, case: dict):
        text = case["text"]
        v = apply_gate(text, config=ENABLED)
        assert (
            v.event == "BLOCKED_ATTEMPT"
        ), f"{case['id']}: expected KEEP_STRICT/BLOCKED_ATTEMPT, got {v.event} ({v.notes})"
        assert v.blocked is True
        assert v.qualifies_for_flag_l1_refusal is False
        payload = user_facing_payload(text, v, config=ENABLED)
        assert payload["delivered"] is False
        assert payload["message"] == USER_FACING_BLOCK_MESSAGE
        assert "21,8" not in payload["message"]
        assert "21.8" not in payload["message"]
