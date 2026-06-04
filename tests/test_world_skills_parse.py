"""
Header-aware parser tests for world_skills_ingest.parse_batch_markdown.

Regression: the new batch format puts «Суть» (claim) in column 3, the old format
in column 2. The previous parser hard-coded cells[2], so new-format claims were
parsed as the «Тип» value (e.g. "invariant"). The header-aware parser fixes this.
"""
from core.world_skills_ingest import parse_batch_markdown

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
    assert f[0]["metadata"]["domain"] == "agro"


def test_new_format_claim_in_col3_not_type():
    f = parse_batch_markdown(NEW)
    assert len(f) == 1
    assert f[0]["fact_id"] == "physd.mech.newton1"
    # the fix: claim is the «Суть» sentence, NOT the «Тип» token
    assert "Тело сохраняет покой" in f[0]["claim"]
    assert f[0]["claim"] != "invariant"
    assert f[0]["metadata"]["domain"] == "physd"


def test_separator_and_header_rows_skipped():
    f = parse_batch_markdown(NEW)
    assert all(row["fact_id"] not in ("id", "ID", "") for row in f)
    assert len(f) == 1  # only the data row, not header/separator
