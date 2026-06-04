"""
Tests for core/memory.py ESM (Epistemic State Machine).
v2.0 (audit-fix: correct test isolation via make_store(),
      added drift protection test TASK-02,
      added bi-temporal tests I96)

Covers:
  - I1:   8 ESM states
  - I6:   Ring Zero immutability
  - I50:  store_fact does not bypass transition_esm
  - I96:  bi-temporal fields set on store_fact
  - TASK-02: drift protection (Validated claim change → Contradicted)
  - LRU L0 cache behavior
  - history (audit trail) populated by transition_esm
  - confidence validation
  - get_fact returns deepcopy (no mutable aliasing)
  - invalidate_edge: sets t_*_end without DELETE
  - get_fact_at: time-travel query
"""
import json
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── Fixture: правильная тестовая изоляция ────────────────────────────────────
# AUDIT-FIX v2.0: monkeypatch.setattr(memory, "SQLITE_PATH", ...) не работает
# потому что _GLOBAL_STORE уже создан с оригинальным путём при импорте.
# Правильный способ: заменить _GLOBAL_STORE целиком через make_store().

@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    """
    Каждый тест получает свежий SQLiteGraphStore с изолированной БД в tmp_path.
    Заменяем _GLOBAL_STORE, _L0 и _DDL_INITIALIZED через monkeypatch.
    """
    from core import memory
    fresh = memory.make_store(str(tmp_path / "test.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE",     fresh)
    monkeypatch.setattr(memory, "_L0",               fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED",  fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH",       str(tmp_path / "test.db"))
    yield fresh
    fresh.close()


# ─── I1: ESM matrix structure ─────────────────────────────────────────────────

def test_esm_has_eight_states():
    """I1: ровно 8 ESM-состояний."""
    from core.memory import ESM_STATES
    assert len(ESM_STATES) == 8
    assert {"Observed", "Hypothesized", "Supported", "Validated",
            "Contradicted", "Deprecated", "Collapsed", "ImmutableCore"} == ESM_STATES


def test_validated_can_reach_contradicted():
    """Validated → Contradicted разрешён (для конфликтов)."""
    from core.memory import ESM_TRANSITIONS
    assert "Contradicted" in ESM_TRANSITIONS["Validated"]


def test_terminal_states_have_no_exits():
    """Collapsed и ImmutableCore — терминальные."""
    from core.memory import ESM_TRANSITIONS
    assert ESM_TRANSITIONS["Collapsed"]     == set()
    assert ESM_TRANSITIONS["ImmutableCore"] == set()


# ─── store_fact / get_fact basic ─────────────────────────────────────────────

def test_store_and_get_fact_roundtrip():
    from core.memory import get_fact, store_fact
    store_fact({"fact_id": "t1", "claim": "hello", "source": "test", "confidence": 0.9})
    f = get_fact("t1")
    assert f is not None
    assert f["claim"] == "hello"
    assert f["epistemic_state"] == "Observed"


def test_transition_esm_valid():
    from core.memory import get_fact, store_fact, transition_esm
    store_fact({"fact_id": "t2", "claim": "x", "source": "s", "confidence": 0.5})
    assert transition_esm("t2", "Validated") is True
    assert get_fact("t2")["epistemic_state"] == "Validated"


def test_transition_esm_invalid_transition_raises():
    from core.memory import store_fact, transition_esm
    store_fact({"fact_id": "t3", "claim": "x", "source": "s", "confidence": 0.5})
    transition_esm("t3", "Collapsed")
    with pytest.raises(ValueError, match="недопустим"):
        transition_esm("t3", "Validated")


def test_store_fact_rejects_invalid_state():
    from core.memory import store_fact
    with pytest.raises(ValueError, match="недопустимое ESM"):
        store_fact({"fact_id": "bad", "claim": "x", "source": "s",
                    "epistemic_state": "NotAState"})


# ─── I6: Ring Zero immutability ──────────────────────────────────────────────

def test_ring_zero_is_immutable():
    """I6: VALUES_CORE и RING_ZERO не могут быть переведены через transition_esm."""
    from core.memory import IMMUTABLE_FACT_IDS, ImmutableStateError, store_fact, transition_esm
    assert "VALUES_CORE" in IMMUTABLE_FACT_IDS
    assert "RING_ZERO"   in IMMUTABLE_FACT_IDS
    store_fact({"fact_id": "VALUES_CORE", "claim": "honesty", "source": "ring_zero",
                "confidence": 1.0, "epistemic_state": "Validated"})
    with pytest.raises(ImmutableStateError):
        transition_esm("VALUES_CORE", "Contradicted")


def test_ring_zero_seed_allowed_in_store_fact():
    """Ring Zero seed (Validated) — единственный легальный non-Observed initial."""
    from core.memory import get_fact, store_fact
    store_fact({"fact_id": "RING_ZERO", "claim": "core", "source": "seed",
                "confidence": 1.0, "epistemic_state": "Validated"})
    assert get_fact("RING_ZERO")["epistemic_state"] == "Validated"


# ─── I50: store_fact не обходит transition_esm ───────────────────────────────

def test_store_fact_rejects_non_observed_initial_state():
    """I50: новые факты создаются только в 'Observed'."""
    from core.memory import store_fact
    with pytest.raises(ValueError, match="только в 'Observed'"):
        store_fact({"fact_id": "sneaky", "claim": "x", "source": "s",
                    "confidence": 0.5, "epistemic_state": "Validated"})


def test_store_fact_rejects_immutable_core_for_regular_fact():
    """I50: ImmutableCore нельзя выставить для обычного факта."""
    from core.memory import store_fact
    with pytest.raises(ValueError, match="только в 'Observed'"):
        store_fact({"fact_id": "fake_core", "claim": "x", "source": "s",
                    "confidence": 1.0, "epistemic_state": "ImmutableCore"})


def test_transition_to_immutable_core_blocked_for_regular_fact():
    """Только Ring Zero может перейти в ImmutableCore."""
    from core.memory import ImmutableStateError, store_fact, transition_esm
    store_fact({"fact_id": "regular", "claim": "x", "source": "s", "confidence": 0.5})
    transition_esm("regular", "Validated")
    with pytest.raises(ImmutableStateError, match="ImmutableCore"):
        transition_esm("regular", "ImmutableCore")


# ─── TASK-02: drift protection ───────────────────────────────────────────────

def test_store_fact_drift_protection_auto_contradicted():
    """
    TASK-02: claim изменился у Validated факта → авто-переход в Contradicted
    с записью в history (store_fact_upsert_drift_protection).
    """
    from core.memory import get_fact, store_fact, transition_esm
    store_fact({"fact_id": "drift1", "claim": "original", "source": "s", "confidence": 0.8})
    transition_esm("drift1", "Validated")

    store_fact({"fact_id": "drift1", "claim": "CHANGED claim", "source": "s",
                "confidence": 0.8})
    fact = get_fact("drift1")
    assert fact["epistemic_state"] == "Contradicted"
    assert any(
        h.get("by") == "store_fact_upsert_drift_protection"
        for h in fact["history"]
    ), "history должен содержать запись drift protection"


def test_store_fact_drift_protection_same_claim_no_transition():
    """TASK-02: одинаковый claim не триггерит Contradicted."""
    from core.memory import get_fact, store_fact, transition_esm
    store_fact({"fact_id": "nodrift", "claim": "same", "source": "s", "confidence": 0.8})
    transition_esm("nodrift", "Validated")
    store_fact({"fact_id": "nodrift", "claim": "same", "source": "s", "confidence": 0.9})
    assert get_fact("nodrift")["epistemic_state"] == "Validated"


# ─── I96: bi-temporal fields ─────────────────────────────────────────────────

def test_store_fact_populates_bitemporal_fields():
    """I96: store_fact устанавливает все 4 bi-temporal поля."""
    from core.memory import get_fact, store_fact
    store_fact({"fact_id": "bt1", "claim": "x", "source": "s", "confidence": 0.5})
    f = get_fact("bt1")
    assert f["t_event_valid_start"] is not None, "t_event_valid_start не заполнен"
    assert f["t_ingestion_start"]   is not None, "t_ingestion_start не заполнен"
    assert f["t_event_valid_end"]   is None,     "t_event_valid_end должен быть NULL"
    assert f["t_ingestion_end"]     is None,     "t_ingestion_end должен быть NULL"


def test_bitemporal_start_preserved_on_upsert():
    """I96: повторный store_fact не обновляет t_*_start поля."""
    from core.memory import get_fact, store_fact
    store_fact({"fact_id": "bt2", "claim": "x", "source": "s", "confidence": 0.5})
    original = get_fact("bt2")
    original_start = original["t_event_valid_start"]

    store_fact({"fact_id": "bt2", "claim": "x updated", "source": "s", "confidence": 0.7})
    updated = get_fact("bt2")
    assert updated["t_event_valid_start"] == original_start, \
        "t_event_valid_start не должен меняться при upsert"


def test_invalidate_edge_sets_end_fields():
    """invalidate_edge: устанавливает t_*_end без DELETE."""
    from core.memory import get_fact, invalidate_edge, store_fact
    store_fact({"fact_id": "inv1", "claim": "x", "source": "s", "confidence": 0.5})
    assert get_fact("inv1")["t_ingestion_end"] is None

    invalidate_edge("inv1")
    f = get_fact("inv1")
    assert f["t_event_valid_end"] is not None, "t_event_valid_end должен быть установлен"
    assert f["t_ingestion_end"]   is not None, "t_ingestion_end должен быть установлен"
    # Факт всё ещё существует — не удалён
    assert get_fact("inv1") is not None


def test_invalidate_edge_idempotent():
    """invalidate_edge: повторный вызов не перезаписывает уже установленные end-поля."""
    from core.memory import get_fact, invalidate_edge, store_fact
    store_fact({"fact_id": "inv2", "claim": "x", "source": "s", "confidence": 0.5})
    invalidate_edge("inv2", t_event_valid_end="2026-01-01T00:00:00+00:00")
    first_end = get_fact("inv2")["t_event_valid_end"]

    invalidate_edge("inv2", t_event_valid_end="2099-01-01T00:00:00+00:00")
    second_end = get_fact("inv2")["t_event_valid_end"]
    assert first_end == second_end, "COALESCE должен сохранить первое значение"


def test_get_fact_at_returns_fact_in_valid_window():
    """get_fact_at: возвращает факт если оба timestamp в окне."""
    from core.memory import get_fact, get_fact_at, store_fact
    store_fact({"fact_id": "ta1", "claim": "x", "source": "s", "confidence": 0.5})
    f = get_fact("ta1")
    start = f["t_ingestion_start"]

    # Спросить "что я знал сразу после создания"
    result = get_fact_at("ta1", known_at=start, world_at=start)
    assert result is not None, "Факт должен быть найден в момент создания"
    assert result["fact_id"] == "ta1"


def test_get_fact_at_returns_none_before_ingestion():
    """get_fact_at: возвращает None если known_at раньше t_ingestion_start."""
    from core.memory import get_fact_at, store_fact
    store_fact({"fact_id": "ta2", "claim": "x", "source": "s", "confidence": 0.5})
    result = get_fact_at("ta2", known_at="2000-01-01T00:00:00+00:00",
                         world_at="2000-01-01T00:00:00+00:00")
    assert result is None, "Факт не должен быть виден до момента ingestion"


def test_collapsed_sets_ingestion_end():
    """При переходе в Collapsed: t_ingestion_end устанавливается автоматически."""
    from core.memory import get_fact, store_fact, transition_esm
    store_fact({"fact_id": "col1", "claim": "x", "source": "s", "confidence": 0.5})
    transition_esm("col1", "Collapsed")
    f = get_fact("col1")
    assert f["t_ingestion_end"] is not None, \
        "Collapsed должен установить t_ingestion_end"


# ─── confidence validation ────────────────────────────────────────────────────

def test_confidence_negative_rejected():
    from core.memory import store_fact
    # FIX v8.5.2 (Claude audit): regex привязан к интенту, не к конкретному
    # тексту сообщения. После делегирования валидации в core.validators
    # формулировка сообщения изменилась ("должен быть в [0.0, 1.0]" вместо
    # "out of [0, 1]"), но смысл тот же — отвергнуть отрицательное значение.
    with pytest.raises(ValueError, match="confidence"):
        store_fact({"fact_id": "neg", "claim": "x", "source": "s", "confidence": -0.5})


def test_confidence_above_one_rejected():
    from core.memory import store_fact
    # FIX v8.5.2 (Claude audit): см. test_confidence_negative_rejected.
    with pytest.raises(ValueError, match="confidence"):
        store_fact({"fact_id": "huge", "claim": "x", "source": "s", "confidence": 99.0})


def test_confidence_boundary_values_accepted():
    from core.memory import get_fact, store_fact
    store_fact({"fact_id": "zero", "claim": "x", "source": "s", "confidence": 0.0})
    store_fact({"fact_id": "one",  "claim": "x", "source": "s", "confidence": 1.0})
    assert get_fact("zero")["confidence"] == 0.0
    assert get_fact("one")["confidence"]  == 1.0


# ─── get_fact deepcopy (no aliasing) ─────────────────────────────────────────

def test_get_fact_returns_deepcopy_not_reference():
    """Внешняя мутация не должна корруптить L0."""
    from core.memory import get_fact, store_fact
    store_fact({"fact_id": "share", "claim": "original", "source": "s", "confidence": 0.5})

    f1 = get_fact("share")
    f1["claim"] = "MUTATED EXTERNALLY"
    f1["history"].append({"injected": "from outside"})

    f2 = get_fact("share")
    assert f2["claim"]   == "original", "L0 коррумпирован внешней мутацией"
    assert len(f2["history"]) == 0,     "history L0 коррумпирован"


# ─── LRU L0 cache ────────────────────────────────────────────────────────────

def test_lru_cap_respected():
    from core.memory import _L0, L0_CAP, store_fact
    for i in range(L0_CAP + 3):
        store_fact({"fact_id": f"lru_{i}", "claim": f"c{i}", "source": "t",
                    "confidence": 0.5})
    assert len(_L0) <= L0_CAP


def test_lru_evicts_oldest():
    from core.memory import _L0, L0_CAP, store_fact
    for i in range(L0_CAP):
        store_fact({"fact_id": f"ev_{i}", "claim": f"c{i}", "source": "t",
                    "confidence": 0.5})
    assert "ev_0" in _L0
    store_fact({"fact_id": "ev_overflow", "claim": "x", "source": "t",
                "confidence": 0.5})
    assert "ev_0"        not in _L0
    assert "ev_overflow" in _L0


def test_lru_read_refreshes_recency():
    from core.memory import _L0, L0_CAP, get_fact, store_fact
    for i in range(L0_CAP):
        store_fact({"fact_id": f"rec_{i}", "claim": f"c{i}", "source": "t",
                    "confidence": 0.5})
    get_fact("rec_0")
    store_fact({"fact_id": "rec_new", "claim": "x", "source": "t", "confidence": 0.5})
    assert "rec_0"   in _L0
    assert "rec_1" not in _L0


# ─── P0.1: UPSERT не сбрасывает state ────────────────────────────────────────

def test_store_fact_preserves_validated_after_upsert(isolated_db):
    """P0.1: повторный store_fact с ТЕМ ЖЕ claim не откатывает Validated → Observed (L1).

    v8.3.1: тест обновлён — раньше использовал 'a updated' (другой claim),
    что триггерило drift protection (TASK-02). Это маскировало split-brain
    L0/L1. Сейчас drift protection синхронно обновляет L1, а этот тест
    проверяет именно случай "одинаковый claim" (P0.1).
    """
    from core import memory
    memory.store_fact({"fact_id": "x", "claim": "a", "source": "s", "confidence": 0.5})
    memory.transition_esm("x", "Validated")
    assert memory.get_fact("x")["epistemic_state"] == "Validated"

    memory._L0.clear()
    # ВАЖНО: тот же claim — иначе triggers drift protection (см. test ниже).
    memory.store_fact({"fact_id": "x", "claim": "a", "source": "s",
                       "confidence": 0.5})

    with sqlite3.connect(isolated_db.db_path) as conn:
        row = conn.execute(
            "SELECT epistemic_state FROM facts WHERE fact_id='x'"
        ).fetchone()
    assert row[0] == "Validated"
    assert memory.get_fact("x")["epistemic_state"] == "Validated"


def test_store_fact_drift_protection_keeps_l0_l1_in_sync(isolated_db):
    """v8.3.1: проверяет что drift protection (TASK-02) синхронно обновляет L1.

    До v8.3.1 был split-brain bug: при detect drift L0 переходил
    в Contradicted, но SQL ON CONFLICT не обновлял epistemic_state
    в L1 → расхождение L0 (Contradicted) vs L1 (Validated).

    После v8.3.1 fix: оба слоя синхронны.
    """
    from core import memory
    memory.store_fact({"fact_id": "y", "claim": "original", "source": "s",
                       "confidence": 0.5})
    memory.transition_esm("y", "Validated")
    assert memory.get_fact("y")["epistemic_state"] == "Validated"

    memory._L0.clear()
    # ИЗМЕНЁННЫЙ claim → drift protection срабатывает
    memory.store_fact({"fact_id": "y", "claim": "changed claim", "source": "s",
                       "confidence": 0.5})

    # L0 должен быть Contradicted
    assert memory.get_fact("y")["epistemic_state"] == "Contradicted"

    # L1 ТОЖЕ должен быть Contradicted (split-brain исправлен)
    with sqlite3.connect(isolated_db.db_path) as conn:
        row = conn.execute(
            "SELECT epistemic_state FROM facts WHERE fact_id='y'"
        ).fetchone()
    assert row[0] == "Contradicted", (
        f"split-brain: L0={memory.get_fact('y')['epistemic_state']} vs L1={row[0]}"
    )


# ─── history (audit trail) ───────────────────────────────────────────────────

def test_new_fact_has_empty_history():
    from core.memory import get_fact, store_fact
    store_fact({"fact_id": "h1", "claim": "x", "source": "s"})
    f = get_fact("h1")
    assert isinstance(f["history"], list)
    assert len(f["history"]) == 0


def test_transition_appends_history_entry():
    from core.memory import get_fact, store_fact, transition_esm
    store_fact({"fact_id": "h2", "claim": "x", "source": "s"})
    transition_esm("h2", "Validated")
    f = get_fact("h2")
    assert len(f["history"]) == 1
    entry = f["history"][0]
    assert entry["state"] == "Validated"
    assert entry["from"]  == "Observed"
    assert "at"           in entry
    assert entry["by"]    == "transition_esm"


def test_history_persists_across_l0_clear(isolated_db):
    from core import memory
    memory.store_fact({"fact_id": "h5", "claim": "x", "source": "s"})
    memory.transition_esm("h5", "Supported")
    memory.transition_esm("h5", "Validated")

    memory._L0.clear()
    f = memory.get_fact("h5")
    assert f["epistemic_state"] == "Validated"
    assert len(f["history"])    == 2

    with sqlite3.connect(isolated_db.db_path) as conn:
        row = conn.execute(
            "SELECT history FROM facts WHERE fact_id='h5'"
        ).fetchone()
    h = json.loads(row[0])
    assert len(h)         == 2
    assert h[0]["state"]  == "Supported"
    assert h[1]["state"]  == "Validated"


def test_transition_esm_by_param_recorded():
    from core.memory import get_fact, store_fact, transition_esm
    store_fact({"fact_id": "h_by", "claim": "x", "source": "s"})
    transition_esm("h_by", "Validated", by="custom_caller")
    entry = get_fact("h_by")["history"][0]
    assert entry["by"] == "custom_caller"


# ─── get_all_facts фильтр ────────────────────────────────────────────────────

def test_get_all_facts_filter_by_state():
    from core.memory import get_all_facts, store_fact, transition_esm
    store_fact({"fact_id": "a1", "claim": "x", "source": "s"})
    store_fact({"fact_id": "a2", "claim": "x", "source": "s"})
    store_fact({"fact_id": "a3", "claim": "x", "source": "s"})
    transition_esm("a1", "Validated")
    transition_esm("a2", "Validated")

    validated = get_all_facts(epistemic_state="Validated")
    assert len(validated) == 2
    assert {f["fact_id"] for f in validated} == {"a1", "a2"}

    observed = get_all_facts(epistemic_state="Observed")
    assert len(observed) == 1
    assert observed[0]["fact_id"] == "a3"


def test_get_all_facts_no_filter_returns_all():
    from core.memory import get_all_facts, store_fact, transition_esm
    store_fact({"fact_id": "all1", "claim": "x", "source": "s"})
    store_fact({"fact_id": "all2", "claim": "x", "source": "s"})
    transition_esm("all1", "Validated")
    all_facts = get_all_facts()
    ids = {f["fact_id"] for f in all_facts}
    assert {"all1", "all2"} <= ids


# ─── TASK-09: L0 Raw Memory integration ──────────────────────────────────────

def test_store_raw_text_returns_raw_id():
    """TASK-09: store_raw_text возвращает raw_id и дедуплицирует по контенту."""
    from core.memory import store_raw_text
    raw_id1 = store_raw_text("Original text for testing", source="test")
    raw_id2 = store_raw_text("Original text for testing", source="test")
    assert raw_id1.startswith("raw_")
    assert raw_id1 == raw_id2  # дедупликация


def test_store_raw_text_different_content():
    """TASK-09: разный текст → разные raw_id."""
    from core.memory import store_raw_text
    r1 = store_raw_text("Content alpha", source="s")
    r2 = store_raw_text("Content beta",  source="s")
    assert r1 != r2


def test_store_fact_with_derived_from():
    """TASK-09: store_fact принимает derived_from и сохраняет его в БД."""
    from core.memory import get_fact, store_fact, store_raw_text
    raw_id = store_raw_text("Water is H2O", source="chemistry")
    store_fact({
        "fact_id":      "h2o_test",
        "claim":        "Water consists of hydrogen and oxygen",
        "source":       "chemistry",
        "confidence":   0.99,
        "derived_from": raw_id,
    })
    fact = get_fact("h2o_test")
    assert fact is not None
    assert fact.get("derived_from") == raw_id


def test_link_raw_to_fact():
    """TASK-09: link_raw_to_fact связывает факт с оригиналом в провенанс-таблице."""
    from core.memory import get_fact, link_raw_to_fact, store_fact, store_raw_text
    raw_id = store_raw_text("DNA has double helix structure", source="biology")
    store_fact({"fact_id": "dna_helix", "claim": "DNA double helix",
                "source": "biology", "confidence": 0.99})
    link_raw_to_fact(raw_id, "dna_helix")
    fact = get_fact("dna_helix")
    assert fact is not None
    # derived_from установлен через link_raw_to_fact
    assert fact.get("derived_from") == raw_id
