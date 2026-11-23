"""Regression tests for the Source-X gate review findings T-1, T-2, T-3.

T-1: an error inside the gate must withhold the answer, not pass it through.
T-2: figures followed by sentence punctuation must still be detected.
T-3: a withheld result must not carry the withheld text or figures anywhere.
No model calls.
"""

from __future__ import annotations

import json

import pytest

import core.source_x_gate as gate
from core.feature_config import clear_config_cache
from core.source_x_gate import (
    USER_FACING_BLOCK_MESSAGE,
    SourceXGateConfig,
    apply_gate,
    apply_to_pipeline_result,
    fail_closed_result,
    has_official_figures,
    scan_text,
)

ENABLED = SourceXGateConfig(enabled=True)
DISABLED = SourceXGateConfig(enabled=False)
FIGURES = ("21,8", "21.8", "7,6", "7.6", "53,5", "53.5")


@pytest.fixture(autouse=True)
def _reset_config():
    clear_config_cache()
    yield
    clear_config_cache()


def _blocks(text: str) -> bool:
    return apply_gate(text, config=ENABLED).blocked


# ---------------------------------------------------------------- T-2

class TestPunctuationAfterFigure:
    @pytest.mark.parametrize(
        "text",
        [
            "Рост по брифу — 21,8.",
            "Рост 21,8, инфляция 7,6, доля 53,5%.",
            "Оценка: 7.6. Итого",
            "Рост 21,8; инфляция 7,6",
            "Доля 53,5%.",
            "Доля 53,5 %.",
            "Рост (21,8) за год",
            "Рост «21,8»!",
            "Выручка 21,80.",
            "Выручка 21.8?",
            "Рост,21,8",
            "Итог:\n21,8\nконец",
        ],
    )
    def test_figure_is_detected(self, text):
        assert _blocks(text), text

    @pytest.mark.parametrize(
        "text",
        [
            "Значение 21,85 млн.",
            "Значение 121,8 млн.",
            "Значение 21,8.5 млн.",
            "Значение 21,8,5 млн.",
            "Значение 7,61.",
            "Значение 17,6.",
            "Значение 53,56%.",
            "Версия 1.21,8",
            "Выручка 14,2 млн, рост 3,1%.",
        ],
    )
    def test_near_miss_is_not_detected(self, text):
        assert not [h for h in scan_text(text, ENABLED) if h.level == "block"], text

    def test_official_figures_with_trailing_punctuation(self):
        assert has_official_figures("Выручка 14,2.")["has_14_2"] is True
        assert has_official_figures("Рост 3,1%.")["has_3_1_pct"] is True
        assert has_official_figures("Выручка 114,2.")["has_14_2"] is False


# ---------------------------------------------------------------- T-3

NOTES = "Служебная заметка: цифры 21,8 и 7,6 не использованы."
ANSWER = "Реальная выручка — 21,8 млн."


def _dirty_result() -> dict:
    return {
        "answer": ANSWER,
        "query": "какая выручка",
        "retrieval_mode": "hybrid",
        "error": None,
        "notes": NOTES,
        "facts": [{"fact_id": "f1", "claim": "по брифу выручка 21,8"}],
        "conflicts": [{"claim": "рост 7,6"}],
        "trace": [{"id": "f1", "note": "53,5%"}],
        "faithfulness": {"quote": ANSWER},
        "exocortex_sections": [{"text": "…21,8…"}],
        "causal_hints": ["7,6"],
    }


def _all_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _all_strings(v)
    elif isinstance(obj, (list, tuple, set)):
        for v in obj:
            yield from _all_strings(v)


class TestWithheldResultIsClean:
    def test_no_figure_anywhere_in_result(self):
        out = apply_to_pipeline_result(_dirty_result(), config=ENABLED)
        assert out["source_x_gate_blocked"] is True
        blob = json.dumps(out, ensure_ascii=False)
        for fig in FIGURES:
            assert fig not in blob, fig
        for text in _all_strings(out):
            assert "Реальная выручка" not in text

    def test_only_allowlisted_keys_survive(self):
        out = apply_to_pipeline_result(_dirty_result(), config=ENABLED)
        allowed = set(gate.WITHHELD_KEEP_KEYS) | {
            "answer", "facts", "total_facts", "trace",
            "source_x_gate_blocked", "source_x_gate",
            "source_x_notes_review", "source_x_gate_notes_flagged",
        }
        assert set(out) <= allowed
        assert out["answer"] == USER_FACING_BLOCK_MESSAGE
        assert out["facts"] == [] and out["trace"] == []
        assert out["query"] == "какая выручка"

    def test_gate_record_has_rules_but_no_text(self):
        out = apply_to_pipeline_result(_dirty_result(), config=ENABLED)
        rec = out["source_x_gate"]
        assert rec["event"] == "BLOCKED_ATTEMPT"
        assert rec["delivered"] is False
        assert "x_number_21_8" in rec["rules"]
        assert "hits" not in rec and "soft_classification" not in rec
        assert out["source_x_notes_review"]["hard_fail"] is False
        assert out["source_x_notes_review"]["blocked"] is False
        assert "hits" not in out["source_x_notes_review"]

    def test_log_does_not_quote_withheld_text(self, caplog):
        with caplog.at_level("DEBUG", logger="core.source_x_gate"):
            apply_to_pipeline_result(_dirty_result(), config=ENABLED)
        text = "\n".join(r.getMessage() for r in caplog.records)
        assert "BLOCKED_ATTEMPT" in text
        for fig in FIGURES:
            assert fig not in text, fig
        assert "Реальная выручка" not in text

    def test_delivered_result_is_untouched_by_allowlist(self):
        result = {"answer": "Выручка 14,2 млн, рост 3,1%.", "facts": [{"x": 1}], "trace": [1]}
        out = apply_to_pipeline_result(result, config=ENABLED)
        assert out["facts"] == [{"x": 1}] and out["trace"] == [1]
        assert out["source_x_gate"]["delivered"] is True


# ---------------------------------------------------------------- T-1

class TestFailClosed:
    def test_exception_inside_gate_withholds(self, monkeypatch, caplog):
        def boom(*a, **k):
            raise RuntimeError("секрет 21,8")

        monkeypatch.setattr(gate, "apply_gate", boom)
        with caplog.at_level("DEBUG", logger="core.source_x_gate"):
            out = apply_to_pipeline_result(_dirty_result(), config=ENABLED)
        assert out["source_x_gate_blocked"] is True
        assert out["answer"] == USER_FACING_BLOCK_MESSAGE
        assert out["source_x_gate"]["event"] == "GATE_ERROR"
        assert out["source_x_gate"]["delivered"] is False
        blob = json.dumps(out, ensure_ascii=False) + "\n".join(
            r.getMessage() for r in caplog.records
        )
        for fig in FIGURES:
            assert fig not in blob, fig

    def test_exception_with_gate_disabled_passes_result_through(self, monkeypatch):
        monkeypatch.setattr(gate, "apply_gate", lambda *a, **k: 1 / 0)
        result = {"answer": "21,8 млн", "other": 1}
        out = apply_to_pipeline_result(result, config=DISABLED)
        assert out == {"answer": "21,8 млн", "other": 1}

    def test_unreadable_config_withholds(self, monkeypatch):
        def boom():
            raise RuntimeError("config broken")

        monkeypatch.setattr(SourceXGateConfig, "from_app", classmethod(lambda cls: boom()))
        out = apply_to_pipeline_result({"answer": "21,8 млн"})
        assert out["source_x_gate_blocked"] is True
        assert out["answer"] == USER_FACING_BLOCK_MESSAGE

    def test_fail_closed_result_respects_disabled(self):
        r = {"answer": "x"}
        assert fail_closed_result(r, config=DISABLED) is r
        assert fail_closed_result(r, config=ENABLED)["source_x_gate_blocked"] is True


class TestPipelineHook:
    """The hook in core.pipeline must also fail closed and run last."""

    def test_pipeline_hook_withholds_when_gate_raises(self, monkeypatch):
        from core import pipeline

        monkeypatch.setenv("ENABLE_SOURCE_X_GATE", "1")
        clear_config_cache()

        def boom(result, **k):
            raise RuntimeError("x")

        monkeypatch.setattr(gate, "apply_to_pipeline_result", boom)
        out = pipeline._source_x_gate_or_withhold(_dirty_result())
        assert out["source_x_gate_blocked"] is True
        assert out["answer"] == USER_FACING_BLOCK_MESSAGE
        assert "21,8" not in json.dumps(out, ensure_ascii=False)

    def test_pipeline_hook_passes_through_when_disabled(self, monkeypatch):
        from core import pipeline

        monkeypatch.delenv("ENABLE_SOURCE_X_GATE", raising=False)
        clear_config_cache()
        monkeypatch.setattr(gate, "apply_to_pipeline_result", lambda r, **k: 1 / 0)
        r = {"answer": "21,8"}
        assert pipeline._source_x_gate_or_withhold(r) == {"answer": "21,8"}

    def test_gate_is_the_last_step_of_run(self):
        import inspect

        from core import pipeline

        src = inspect.getsource(pipeline.run)
        assert src.rstrip().endswith("return _source_x_gate_or_withhold(result)")
        assert src.count("_source_x_gate_or_withhold(") == 1
