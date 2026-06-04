"""Тесты Write Protocol Gate (core/write_gate.py) + интеграции в store_fact."""
from __future__ import annotations

import pytest

# ─── admit_fact (чистая функция) ─────────────────────────────────────────────

@pytest.mark.parametrize("ct,ot,source,ev,ok", [
    ("EMOTION",    "USER_REPORTED", "user",    False, True),   # субъективное — допускается
    ("OPINION",    "USER_REPORTED", "unknown", False, True),
    ("USER_EXPERIENCE", "USER_REPORTED", "user", False, True),
    ("UNKNOWN",    "UNKNOWN",       "unknown", False, True),   # UNKNOWN хранится (Observed)
    ("WORLD_FACT", "EXTERNAL",      "physics", False, True),   # факт мира + источник — ок
    ("WORLD_FACT", "EXTERNAL",      "",        False, False),  # факт мира без источника
    ("WORLD_FACT", "EXTERNAL",      "unknown", False, False),  # source=unknown = нет провенанса
    ("WORLD_FACT", "LLM_OUTPUT",    "gpt-4",   False, False),  # LLM-факт без evidence
    ("WORLD_FACT", "LLM_OUTPUT",    "gpt-4",   True,  True),   # LLM-факт + evidence — ок
])
def test_admit_fact(ct, ot, source, ev, ok):
    from core.write_gate import admit_fact
    res, reason = admit_fact(claim_type=ct, origin_type=ot, source=source, has_evidence=ev)
    assert res is ok, f"({ct},{ot},{source!r},ev={ev}) → {res} ({reason})"


# ─── интеграция в store_fact (флаг ENABLE_WRITE_GATE) ─────────────────────────

@pytest.fixture()
def isolated_db(monkeypatch, tmp_path):
    from core import memory
    fresh = memory.make_store(str(tmp_path / "wg.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE", fresh)
    monkeypatch.setattr(memory, "_L0", fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH", str(tmp_path / "wg.db"))
    yield fresh
    fresh.close()


def test_gate_off_legacy_stores_world_fact_without_source(isolated_db, monkeypatch):
    """Флаг OFF (дефолт): WORLD_FACT без источника пишется — поведение прежнее."""
    import core.write_gate as wg
    from core.memory import get_fact, store_fact
    monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: False)
    store_fact({"fact_id": "w1", "claim": "Некое утверждение о мире", "source": "unknown",
                "claim_type": "WORLD_FACT", "origin_type": "EXTERNAL"})
    assert get_fact("w1") is not None


def test_gate_on_rejects_world_fact_without_source(isolated_db, monkeypatch):
    """Флаг ON: WORLD_FACT без провенанса отклоняется (не пишется)."""
    import core.write_gate as wg
    from core.memory import get_fact, store_fact
    monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: True)
    ok = store_fact({"fact_id": "w2", "claim": "Некое утверждение о мире", "source": "unknown",
                     "claim_type": "WORLD_FACT", "origin_type": "EXTERNAL"})
    assert ok is False
    assert get_fact("w2") is None


def test_gate_on_allows_world_fact_with_source(isolated_db, monkeypatch):
    """Флаг ON: WORLD_FACT с источником и evidence — пишется."""
    import core.write_gate as wg
    from core.memory import get_fact, store_fact
    monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: True)
    store_fact({"fact_id": "w3", "claim": "Вода кипит при 100 °C", "source": "physics",
                "claim_type": "WORLD_FACT", "origin_type": "EXTERNAL",
                "metadata": {"evidence_refs": [{"source_id": "p", "span": "1"}]}})
    assert get_fact("w3") is not None


def test_gate_on_allows_subjective(isolated_db, monkeypatch):
    """Флаг ON: EMOTION без источника — пишется (субъективное допускается)."""
    import core.write_gate as wg
    from core.memory import get_fact, store_fact
    monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: True)
    store_fact({"fact_id": "e1", "claim": "Мне тревожно перед встречей", "source": "user_message",
                "claim_type": "EMOTION", "origin_type": "USER_REPORTED"})
    assert get_fact("e1") is not None
