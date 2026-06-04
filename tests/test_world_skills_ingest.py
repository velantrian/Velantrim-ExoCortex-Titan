"""
Тесты ingest базы знаний World Skills Core (core/world_skills_ingest.py).
"""
from core.world_skills_ingest import ingest_facts, parse_batch_markdown

_SAMPLE = """## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `agro.crop.wheat.grain` | MATERIAL_SOURCE | Пшеница даёт зерно для муки и хлеба | зависит от сорта | food.flour |
| `food.process.milling.gtf` | PROCESS | Помол превращает зерно в муку | степень помола важна | wheat |
| `x` | TYPE | tiny | — | — |
"""


def test_parse_extracts_rows():
    facts = parse_batch_markdown(_SAMPLE)
    ids = {f["fact_id"] for f in facts}
    assert "agro.crop.wheat.grain" in ids
    assert "food.process.milling.gtf" in ids
    assert "x" not in ids                       # короткий claim («tiny») отброшен


def test_parse_fields():
    facts = parse_batch_markdown(_SAMPLE)
    wheat = next(f for f in facts if f["fact_id"] == "agro.crop.wheat.grain")
    assert wheat["type"] == "MATERIAL_SOURCE"
    assert "Пшеница" in wheat["claim"]
    assert wheat["links"] == "food.flour"
    assert wheat["source"] == "wsc:MATERIAL_SOURCE"


def test_parse_skips_header_and_separator():
    facts = parse_batch_markdown(_SAMPLE)
    assert len(facts) == 2                                  # header/separator/«tiny» отброшены
    assert all(f["fact_id"].lower() != "id" for f in facts)
    assert all(not (set(f["fact_id"]) <= set("-: ")) for f in facts)   # ни одного id из одних разделителей


def test_ingest_into_store_validates(tmp_path):
    from core.memory import SQLiteGraphStore
    s = SQLiteGraphStore(db_path=str(tmp_path / "kb.db"))
    facts = parse_batch_markdown(_SAMPLE)
    rep = ingest_facts(s, facts, validate=True)
    assert rep["ingested"] == 2 and rep["validated"] == 2 and rep["errors"] == 0
    assert s.get_fact("agro.crop.wheat.grain")["epistemic_state"] == "Validated"
