"""
Header-aware parser tests for world_skills_ingest.parse_batch_markdown.

Regression: the new batch format puts «Суть» (claim) in column 3, the old format
in column 2. The previous parser hard-coded cells[2], so new-format claims were
parsed as the «Тип» value (e.g. "invariant"). The header-aware parser fixes this.
"""
import tempfile
from pathlib import Path

from core.world_skills_ingest import parse_batch_file, parse_batch_markdown
from scripts.verify_world_skills import _is_unit_file

OLD = """
| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `agro.crop.wheat.grain_use` | MATERIAL_SOURCE | Пшеница даёт зерно для муки и хлеба. | по сорту | food.flour |
"""

NEW = """
| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| physd.mech.newton1 | Первый закон Ньютона | invariant | Тело сохраняет покой без внешней силы. | основа динамики |
"""


def test_old_format_claim_in_col2():
    f = parse_batch_markdown(OLD)
    assert len(f) == 1
    assert f[0]["fact_id"] == "agro.crop.wheat.grain_use"
    assert "Пшеница" in f[0]["claim"]
    assert f[0]["conditions"] == "по сорту"
    assert f[0]["links"] == "food.flour"
    assert f[0]["practical"] == ""
    assert f[0]["metadata"]["domain"] == "agro"


def test_new_format_claim_in_col3_not_type():
    f = parse_batch_markdown(NEW)
    assert len(f) == 1
    assert f[0]["fact_id"] == "physd.mech.newton1"
    # the fix: claim is the «Суть» sentence, NOT the «Тип» token
    assert "Тело сохраняет покой" in f[0]["claim"]
    assert f[0]["claim"] != "invariant"
    assert f[0]["knowledge_unit"] == "Первый закон Ньютона"
    assert f[0]["practical"] == "основа динамики"
    assert f[0]["links"] == ""  # practical prose must never masquerade as tags
    assert f[0]["conditions"] == ""
    assert f[0]["metadata"]["domain"] == "physd"


def test_separator_and_header_rows_skipped():
    f = parse_batch_markdown(NEW)
    assert all(row["fact_id"] not in ("id", "ID", "") for row in f)
    assert len(f) == 1  # only the data row, not header/separator


def test_ops_source_file_marks_practical_domain():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "100_BATCH_900_SAMPLE_OPS.ru.md"
        path.write_text(NEW, encoding="utf-8")
        facts = parse_batch_file(str(path))
    assert facts[0]["metadata"]["practical_domain"] is True
    assert facts[0]["metadata"]["knowledge_file"] == path.name


def test_code_span_pipe_does_not_shift_claim_columns():
    table = """
| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| math.probability.bayes | THEOREM | `P(H | E)=P(E | H)P(H)/P(E)`. | P(E) != 0 | diagnosis |
"""
    facts = parse_batch_markdown(table)
    assert len(facts) == 1
    assert "P(H | E)" in facts[0]["claim"]
    assert facts[0]["conditions"] == "P(E) != 0"


def test_malformed_id_is_not_ingested():
    table = """
| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| bad.id.кириллица | METHOD | Запись должна быть пропущена. | | |
"""
    assert parse_batch_markdown(table) == []


def test_curated_relations_file_is_not_a_knowledge_unit_source():
    assert not _is_unit_file(Path("00_CURATED_CAUSAL_RELATIONS.ru.md"))
