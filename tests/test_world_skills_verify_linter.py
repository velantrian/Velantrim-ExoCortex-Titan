"""
Tests for the claim linter in scripts/verify_world_skills.py:
- header-aware claim extraction (both table formats);
- duplicate-claim detection (one normalized «Суть» under ≥2 different IDs);
- generic/short claim detection.
"""
import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "verify_world_skills",
    Path(__file__).resolve().parents[1] / "scripts" / "verify_world_skills.py",
)
vws = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(vws)


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_extract_units_new_format(tmp_path):
    p = _write(tmp_path, "10_BATCH_X.ru.md", """
| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| phys.mech.inertia | Инерция | invariant | Тело сохраняет состояние без внешней силы | основа |
""")
    units = vws.extract_units(p)
    assert units == [("phys.mech.inertia", "Тело сохраняет состояние без внешней силы", 4)]


def test_extract_units_old_format(tmp_path):
    p = _write(tmp_path, "13_BATCH_Y.ru.md", """
| ID | Тип | Суть | Условия | Связи |
|---|---|---|---|---|
| agro.wheat | MATERIAL | Пшеница даёт зерно для муки | по сорту | food |
""")
    units = vws.extract_units(p)
    assert units[0][0] == "agro.wheat"
    assert "Пшеница" in units[0][1]


def test_norm_claim_dedup_key():
    # case/punctuation/space-insensitive normalization
    assert vws._norm_claim("Вода кипит, при 100°C!") == vws._norm_claim("вода   кипит при 100 c")


def test_duplicate_and_generic_claims_detected(tmp_path, monkeypatch):
    # point the scanner at a temp KB dir with a generic/duplicate claim
    monkeypatch.setattr(vws, "RU_DIR", tmp_path)
    monkeypatch.setattr(vws, "KB_DIR", tmp_path)
    _write(tmp_path, "20_BATCH_GENERIC.ru.md", """
| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| geo.fr.cap | Франция — Париж | invariant | столица, евро (EUR) | справка |
| geo.it.cap | Италия — Рим | invariant | столица, евро (EUR) | справка |
| geo.de.cap | Германия — Берлин | invariant | Столица Германии — Берлин; евро (EUR) | справка |
""")
    r = vws.scan()
    # the two identical generic claims (fr+it) → one duplicate-claim group of ≥2 ids
    assert any(len(ids) >= 2 for ids in r["duplicate_claims"].values())
    # "столица, евро (EUR)" begins with a generic column-label prefix
    assert len(r["generic_claims"]) >= 1
    assert r["unique_ids"] == 3 and not r["duplicates"]  # IDs themselves are fine
