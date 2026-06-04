"""Horizons в GET /layers/status (V8.6)."""

from __future__ import annotations

from core.layers_status import build_layers_status


def test_l2_5_staging_is_research():
    st = build_layers_status()
    assert st["layers"]["L2_5_staging"]["status"] == "research"
    assert st["layers"]["L2_5_staging"]["enabled"] is False


def test_horizons_research_includes_l2_5():
    st = build_layers_status()
    research = {e["id"] for e in st["horizons"]["research"]}
    assert "L2_5_staging" in research


def test_horizons_docs_index():
    st = build_layers_status()
    assert "docs/HORIZONS.md" in st["horizons"]["docs_index"]


def test_horizons_api_index():
    from api.exocortex_api import horizons_index

    idx = horizons_index()
    assert idx["docs_root"] == "docs/horizons/"
    ids = {e["id"] for e in idx["research"]}
    assert "kde" in ids
    assert "R2_category_truth_gate" in ids


def test_horizons_r3_evo_memory_card():
    st = build_layers_status()
    by_id = {e["id"]: e for e in st["horizons"]["research"]}
    assert by_id["R3_evo_memory"]["docs"] == "docs/horizons/R3_EVO_MEMORY.md"
    assert by_id["R3_evo_memory"]["status"] == "research"


def test_horizons_e6_shadow_state_card():
    st = build_layers_status()
    by_id = {e["id"]: e for e in st["horizons"]["experimental"]}
    assert by_id["E6_shadow_state"]["docs"] == "docs/horizons/E6_SHADOW_STATE.md"
    assert by_id["E6_shadow_state"]["status"] == "experimental"


def test_horizons_r4_global_workspace_card():
    st = build_layers_status()
    by_id = {e["id"]: e for e in st["horizons"]["research"]}
    assert by_id["R4_global_workspace"]["docs"] == "docs/horizons/R4_GLOBAL_WORKSPACE.md"


def test_horizons_e1_neurocore_card():
    st = build_layers_status()
    by_id = {e["id"]: e for e in st["horizons"]["experimental"]}
    assert by_id["E1_neurocore"]["docs"] == "docs/horizons/E1_NEUROCORE.md"


def test_horizons_e7_lens_engine_card():
    st = build_layers_status()
    by_id = {e["id"]: e for e in st["horizons"]["experimental"]}
    assert by_id["E7_lens_engine_bae"]["docs"] == "docs/horizons/E7_LENS_ENGINE_BAE.md"


def test_horizons_r2_r5_research_cards():
    st = build_layers_status()
    by_id = {e["id"]: e for e in st["horizons"]["research"]}
    assert by_id["R2_category_truth_gate"]["docs"] == "docs/horizons/R2_CATEGORY_TRUTH_GATE.md"
    assert by_id["R5_k_lines"]["docs"] == "docs/horizons/R5_K_LINES.md"


def test_horizons_e3_e4_e5_experimental_cards():
    st = build_layers_status()
    by_id = {e["id"]: e for e in st["horizons"]["experimental"]}
    assert by_id["E3_hebbian_stdp"]["docs"] == "docs/horizons/E3_HEBBIAN_STDP.md"
    assert by_id["E4_virf_pattern"]["docs"] == "docs/horizons/E4_VIRF_PATTERN.md"
    assert by_id["E5_scallop_dpp"]["docs"] == "docs/horizons/E5_SCALLOP_DPP.md"
