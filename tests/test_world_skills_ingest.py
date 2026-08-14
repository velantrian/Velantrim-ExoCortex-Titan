"""Tests for World Skills parsing and the bounded C9 admission contract."""
from copy import deepcopy

from core.world_skills_ingest import (
    WorldSkillAdmissionStage,
    compute_world_skills_pack_id,
    evaluate_world_skill_candidate,
    ingest_facts,
    parse_batch_markdown,
)

_SAMPLE = """## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `agro.crop.wheat.grain` | MATERIAL_SOURCE | Пшеница даёт зерно для муки и хлеба | зависит от сорта | food.flour |
| `food.process.milling.gtf` | PROCESS | Помол превращает зерно в муку | степень помола важна | wheat |
| `x` | TYPE | tiny | — | — |
"""

_ENRICHED = """## 📦 Reviewed candidates

| ID | Тип | Суть | Условия / границы | Связи | truth_status | source_refs | confidence | risk_domain | limitations | review_status | reviewer | reviewed_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `science.water.boiling` | FACT | Вода кипит при определённой температуре в заданных условиях | зависит от давления | physics.phase | Supported | src:nist-water; src:textbook-thermo | 0.85 | general | значение зависит от давления | approved | reviewer.alice | 2026-08-14T12:00:00+00:00 |
"""


def test_parse_extracts_rows():
    facts = parse_batch_markdown(_SAMPLE)
    ids = {f["fact_id"] for f in facts}
    assert "agro.crop.wheat.grain" in ids
    assert "food.process.milling.gtf" in ids
    assert "x" not in ids


def test_legacy_parse_fields_are_explicit_draft_metadata():
    facts = parse_batch_markdown(_SAMPLE)
    wheat = next(f for f in facts if f["fact_id"] == "agro.crop.wheat.grain")
    assert wheat["type"] == "MATERIAL_SOURCE"
    assert "Пшеница" in wheat["claim"]
    assert wheat["links"] == "food.flour"
    assert wheat["source"] == "wsc:MATERIAL_SOURCE"
    assert wheat["truth_status"] == "Draft"
    assert wheat["source_refs"] == []
    assert wheat["risk_domain"] == ""
    assert wheat["limitations"] == ""
    assert wheat["review_status"] == "unreviewed"
    assert wheat["reviewer"] == ""
    assert wheat["reviewed_at"] == ""
    assert wheat["metadata"]["truth_status"] == "Draft"


def test_parse_skips_header_and_separator():
    facts = parse_batch_markdown(_SAMPLE)
    assert len(facts) == 2
    assert all(f["fact_id"].lower() != "id" for f in facts)
    assert all(not (set(f["fact_id"]) <= set("-: ")) for f in facts)


def test_legacy_rows_are_quarantined_and_never_auto_validate(tmp_path):
    from core.memory import SQLiteGraphStore

    store = SQLiteGraphStore(db_path=str(tmp_path / "kb.db"))
    facts = parse_batch_markdown(_SAMPLE)
    rep = ingest_facts(store, facts, validate=True)

    assert rep["ingested"] == 2
    assert rep["validated"] == 0
    assert rep["quarantined"] == 2
    assert rep["truth_gate_rejected"] == 0
    assert rep["errors"] == 0
    assert store.get_fact("agro.crop.wheat.grain")["epistemic_state"] == "Observed"


def test_reviewed_low_risk_candidate_reaches_validated_through_existing_gate(tmp_path):
    from core.memory import SQLiteGraphStore

    store = SQLiteGraphStore(db_path=str(tmp_path / "kb.db"))
    facts = parse_batch_markdown(_ENRICHED)
    candidate = facts[0]
    decision = evaluate_world_skill_candidate(candidate)
    assert decision.stage is WorldSkillAdmissionStage.TRUTH_GATE
    assert decision.passed is True

    rep = ingest_facts(store, facts, validate=True)

    assert rep["ingested"] == 1
    assert rep["validated"] == 1
    assert rep["quarantined"] == 0
    assert rep["truth_gate_rejected"] == 0
    assert rep["errors"] == 0
    stored = store.get_fact("science.water.boiling")
    assert stored["epistemic_state"] == "Validated"
    assert stored["metadata"]["source_refs"] == ["src:nist-water", "src:textbook-thermo"]
    assert stored["metadata"]["evidence_refs"] == ["src:nist-water", "src:textbook-thermo"]
    assert stored["metadata"]["world_skills_pack_id"] == rep["pack_id"]


def test_high_risk_candidate_with_two_sources_stays_observed(tmp_path):
    from core.memory import SQLiteGraphStore

    store = SQLiteGraphStore(db_path=str(tmp_path / "kb.db"))
    candidate = parse_batch_markdown(_ENRICHED)[0]
    candidate["risk_domain"] = "medical safety"
    candidate["confidence"] = 0.95
    candidate["metadata"]["risk_domain"] = "medical safety"
    candidate["metadata"]["confidence"] = 0.95

    rep = ingest_facts(store, [candidate], validate=True)

    assert rep["validated"] == 0
    assert rep["quarantined"] == 0
    assert rep["truth_gate_rejected"] == 1
    assert rep["errors"] == 0
    assert store.get_fact("science.water.boiling")["epistemic_state"] == "Observed"


def test_self_review_is_fail_closed():
    candidate = parse_batch_markdown(_ENRICHED)[0]
    candidate["reviewer"] = "world_skills_ingest"
    decision = evaluate_world_skill_candidate(candidate)
    assert decision.stage is WorldSkillAdmissionStage.DOMAIN_REVIEW
    assert decision.passed is False
    assert decision.reason_code == "self_review_forbidden"


def test_pack_identity_is_order_independent_and_content_bound():
    facts = parse_batch_markdown(_SAMPLE)
    pack_a = compute_world_skills_pack_id(facts)
    pack_b = compute_world_skills_pack_id(list(reversed(facts)))
    assert pack_a == pack_b

    mutated = deepcopy(facts)
    mutated[0]["claim"] += " уточнение"
    assert compute_world_skills_pack_id(mutated) != pack_a
