"""Static invariants for the TruthPolicy `/query` hot-path wiring."""

from __future__ import annotations

from pathlib import Path


SERVER = Path(__file__).resolve().parents[1] / "server.py"


def _query_block() -> str:
    source = SERVER.read_text(encoding="utf-8")
    start = source.index("    # TruthPolicy runtime boundary.")
    end = source.index("    # Шаг 5: LLM генерация", start)
    return source[start:end]


def test_query_uses_single_configured_fail_closed_adapter() -> None:
    block = _query_block()
    assert "evaluate_configured_truth_policy_runtime" in block
    assert block.count("evaluate_configured_truth_policy_runtime(") == 1
    assert "is_truth_policy_enabled" not in block
    assert "from core.truth_policy import decide" not in block
    assert "truth_policy verdict skipped" not in block


def test_adapter_result_controls_truth_block_and_llm_gate() -> None:
    block = _query_block()
    call = block.index("_truth_runtime = evaluate_configured_truth_policy_runtime(")
    truth_block = block.index("truth_block: dict[str, Any] | None = _truth_runtime.truth_block")
    llm_gate = block.index("truth_rejects_answer = _truth_runtime.blocks_llm")
    assert call < truth_block < llm_gate


def test_truth_policy_failure_cannot_be_caught_and_ignored_in_query_block() -> None:
    block = _query_block()
    assert "except Exception" not in block
    assert "logger.debug" not in block
    assert "never break answer" not in block


def test_llm_generation_still_respects_truth_rejects_answer() -> None:
    source = SERVER.read_text(encoding="utf-8")
    query_start = source.index('@app.post("/query"')
    llm_gate = source.index(
        "if eff_use_llm and not pipeline_error and not truth_rejects_answer:",
        query_start,
    )
    assert llm_gate > query_start


def test_disabled_policy_semantics_remain_in_runtime_adapter() -> None:
    runtime_source = (
        Path(__file__).resolve().parents[1] / "core" / "truth_policy_runtime.py"
    ).read_text(encoding="utf-8")
    assert 'reason_code="truth_policy_disabled"' in runtime_source
    assert "blocks_llm=False" in runtime_source
    assert "truth_block=None" in runtime_source
