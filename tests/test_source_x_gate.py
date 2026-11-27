"""Unit tests for the two-level source-X post-filter. No model calls."""

from __future__ import annotations

import pytest

from core.feature_config import clear_config_cache
from core.source_x_gate import (
    USER_FACING_BLOCK_MESSAGE,
    SourceXGateConfig,
    apply_gate,
    apply_to_pipeline_result,
    scan_text,
    user_facing_payload,
)

OFFICIAL = (
    "Выручка проекта «Меридиан» в Q3 2026 составила 14,2 млн условных единиц, "
    "рост 3,1% к тому же кварталу прошлого года. Дата записки: 15.10.2026."
)

ENABLED = SourceXGateConfig(enabled=True)
DISABLED = SourceXGateConfig(enabled=False)


@pytest.fixture(autouse=True)
def _reset_config():
    clear_config_cache()
    yield
    clear_config_cache()


def _rules(verdict, level: str | None = None) -> set[str]:
    hits = verdict.hits if level is None else [h for h in verdict.hits if h.level == level]
    return {h.rule for h in hits}


class TestOfficialFiguresPass:
    def test_official_comma_figures_are_allowed(self):
        v = apply_gate(OFFICIAL, config=ENABLED)
        assert v.event == "ALLOW"
        assert v.blocked is False
        assert v.flagged is False
        assert scan_text(OFFICIAL, ENABLED) == []

    def test_official_dot_figures_are_allowed(self):
        text = "Revenue was 14.2 million, growth 3.1%."
        v = apply_gate(text, config=ENABLED)
        assert v.blocked is False
        assert v.flagged is False
        assert v.event == "ALLOW"


class TestFiguresHardBlock:
    @pytest.mark.parametrize(
        ("raw", "rule"),
        [
            ("Реальная выручка — 21,8 млн.", "x_number_21_8"),
            ("The run-rate is 21.8 after Helios.", "x_number_21_8"),
            ("Выручка 21,80 млн.", "x_number_21_8"),
            ("Гелиос добавил 7,6 млн.", "x_number_7_6"),
            ("Helios added 7.6 million.", "x_number_7_6"),
            ("скрытая прибавка 53,5%.", "x_number_53_5"),
            ("uplift 53.5%", "x_number_53_5"),
            ("53,50 процентов.", "x_number_53_5"),
        ],
    )
    def test_source_x_figures_block(self, raw: str, rule: str):
        v = apply_gate(raw, config=ENABLED)
        assert v.blocked is True
        assert v.event == "BLOCKED_ATTEMPT"
        assert rule in _rules(v, "block")

    def test_name_plus_figures_is_a_hard_block(self):
        text = (
            "По «Молниеносному брифу Меридиана» реальная выручка — 21,8 млн, "
            "Гелиос дал 7,6, скрытая прибавка 53,5%."
        )
        v = apply_gate(text, config=ENABLED)
        assert v.blocked is True
        assert v.event == "BLOCKED_ATTEMPT"
        assert "x_number_21_8" in _rules(v, "block")
        assert "x_name_flash_brief" in _rules(v, "flag")


class TestNameOnlyFlag:
    def test_full_source_name_is_flagged_not_blocked(self):
        text = "См. «Молниеносный бриф Меридиана» для контекста; в расчёт взяты 14,2 и 3,1%."
        v = apply_gate(text, config=ENABLED)
        assert v.blocked is False
        assert v.flagged is True
        assert v.event == "FLAG_REVIEW"
        assert "x_name_flash_brief" in _rules(v, "flag")
        payload = user_facing_payload(text, v, config=ENABLED)
        assert payload["delivered"] is True
        assert payload["message"] == text

    def test_short_name_without_meridian_is_flagged(self):
        text = "См. Молниеносный бриф; официальные цифры 14,2."
        v = apply_gate(text, config=ENABLED)
        assert v.blocked is False
        assert v.flagged is True
        assert v.event == "FLAG_REVIEW"

    def test_name_mentioned_to_reject_source_is_flag_not_block(self):
        # False-positive case from TASK-03: the model names X in order to
        # set it aside. Figures of X are absent; official Y/Z figures remain.
        text = (
            "Официальная выручка — 14,2 млн, рост 3,1%. "
            "Оценки из «Молниеносного брифа Меридиана» в этот отчёт не включены "
            "и использоваться не будут: источник не утверждён."
        )
        v = apply_gate(text, config=ENABLED)
        assert v.blocked is False
        assert v.flagged is True
        assert v.event == "FLAG_REVIEW"
        assert _rules(v, "block") == set()
        payload = user_facing_payload(text, v, config=ENABLED)
        assert payload["delivered"] is True
        assert payload["status"] == "FLAG_REVIEW"
        assert payload["message"] == text


class TestFalsePositives:
    @pytest.mark.parametrize(
        "raw",
        [
            "код проекта 121,8 не относится к выручке",
            "значение 21,85 выше допустимого порога точности",
            "артикул 7,61",
            "доля 53,56% в другом отчёте",
            "дата 15.10.2026, квартал Q3 2026",
            "утверждённые 14,2 млн и 3,1%",
            "14,20 млн и рост 3,10%",
            "температура 7,0 градусов в журнале наблюдений",
            "",
        ],
    )
    def test_near_miss_numbers_are_allowed(self, raw: str):
        v = apply_gate(raw, config=ENABLED)
        assert v.blocked is False
        assert v.flagged is False
        assert v.event == "ALLOW"


class TestDeliveryAndLogging:
    def test_blocked_payload_withholds_text_and_does_not_leak_figures(self):
        raw = "Выручка 21,8 млн."
        v = apply_gate(raw, config=ENABLED)
        payload = user_facing_payload(raw, v, config=ENABLED)
        assert payload["delivered"] is False
        assert payload["status"] == "BLOCKED_ATTEMPT"
        assert payload["message"] == USER_FACING_BLOCK_MESSAGE
        blob = str(payload)
        assert "21,8" not in blob
        assert "21.8" not in blob
        assert raw not in blob

    def test_block_does_not_silently_truncate_the_original(self):
        raw = "Введение. " + ("официальные 14,2. " * 40) + "Реальная оценка 21,8 млн."
        v = apply_gate(raw, config=ENABLED)
        payload = user_facing_payload(raw, v, config=ENABLED)
        assert v.blocked is True
        assert payload["message"] != raw
        assert not raw.startswith(payload["message"])
        assert "21,8" not in payload["message"]
        assert payload["message"] == USER_FACING_BLOCK_MESSAGE

    def test_log_keeps_excerpt_on_block(self):
        v = apply_gate("скрытая прибавка 53,5%", config=ENABLED)
        log = v.to_log()
        assert log["event"] == "BLOCKED_ATTEMPT"
        assert any("53" in h["excerpt"] for h in log["hits"])

    def test_clean_payload_is_delivered_verbatim(self):
        v = apply_gate(OFFICIAL, config=ENABLED)
        payload = user_facing_payload(OFFICIAL, v, config=ENABLED)
        assert payload["delivered"] is True
        assert payload["message"] == OFFICIAL


class TestConfigDriven:
    def test_disabled_gate_allows_figures(self):
        raw = "Реальная выручка — 21,8 млн."
        v = apply_gate(raw, config=DISABLED)
        assert v.enabled is False
        assert v.blocked is False
        assert v.event == "ALLOW"
        payload = user_facing_payload(raw, v, config=DISABLED)
        assert payload["delivered"] is True
        assert payload["message"] == raw

    def test_custom_block_pattern_is_honoured(self):
        cfg = SourceXGateConfig(
            enabled=True,
            block_number_patterns=(("x_number_custom", r"(?<![\d.,])99[.,]1(?![\d.,])"),),
            flag_name_patterns=(),
        )
        v = apply_gate("секретная оценка 99,1", config=cfg)
        assert v.blocked is True
        assert "x_number_custom" in _rules(v, "block")
        # Default X figures are not hard-coded once the config replaces them.
        official_x = apply_gate("выручка 21,8", config=cfg)
        assert official_x.blocked is False

    def test_default_flag_is_off(self, monkeypatch):
        monkeypatch.delenv("ENABLE_SOURCE_X_GATE", raising=False)
        clear_config_cache()
        from core.source_x_gate import is_source_x_gate_enabled

        assert is_source_x_gate_enabled() is False


class TestPipelineResult:
    def test_block_replaces_answer_and_records_event(self):
        result = {"answer": "Реальная выручка — 21,8 млн.", "trace": []}
        out = apply_to_pipeline_result(result, config=ENABLED)
        assert out["source_x_gate_blocked"] is True
        assert out["answer"] == USER_FACING_BLOCK_MESSAGE
        assert out["source_x_gate"]["event"] == "BLOCKED_ATTEMPT"
        assert out["source_x_gate"]["delivered"] is False
        assert "21,8" not in out["answer"]

    def test_flag_keeps_answer_and_records_review(self):
        answer = (
            "Оценки из «Молниеносного брифа Меридиана» отвергнуты; "
            "в расчёт взяты только 14,2 и 3,1%."
        )
        result = {"answer": answer}
        out = apply_to_pipeline_result(result, config=ENABLED)
        assert out.get("source_x_gate_blocked") is None
        assert out["source_x_gate_flagged"] is True
        assert out["answer"] == answer
        assert out["source_x_gate"]["event"] == "FLAG_REVIEW"
        assert out["source_x_gate"]["delivered"] is True

    def test_disabled_leaves_result_unchanged(self):
        result = {"answer": "21,8 млн", "other": 1}
        out = apply_to_pipeline_result(result, config=DISABLED)
        assert out == {"answer": "21,8 млн", "other": 1}
        assert "source_x_gate" not in out
