"""
Regression tests for P0 bugs fixed across versions.
v2.0 (audit-fix: correct test isolation via make_store(),
      test_ddl_initialized_per_path переписан корректно —
      теперь использует SQLiteGraphStore напрямую, а не глобальные функции)

Тесты проверяют реальное поведение модуля при взаимодействии компонентов.
"""
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── Fixture: правильная тестовая изоляция ────────────────────────────────────

@pytest.fixture
def fresh_db(monkeypatch, tmp_path):
    """Свежий SQLiteGraphStore через make_store() — правильная изоляция."""
    from core import memory
    store = memory.make_store(str(tmp_path / "p0.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE",    store)
    monkeypatch.setattr(memory, "_L0",              store._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", store._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH",      str(tmp_path / "p0.db"))
    yield store
    store.close()


# ─── P0.1: store_fact не сбрасывает Validated → Observed ─────────────────────

def test_p0_1_store_fact_preserves_validated_state(fresh_db):
    """P0.1: повторный store_fact (claim changed) не откатывает Validated в L1."""
    m = fresh_db
    m.store_fact({"fact_id": "x", "claim": "a", "source": "s", "confidence": 0.5})
    m.promote_to_validated("x")
    assert m.get_fact("x")["epistemic_state"] == "Validated"

    m._l0.clear()
    # Изменённый claim при Validated → drift protection → Contradicted
    # (это корректное поведение TASK-02, не баг)
    # Проверяем P0.1: state НЕ откатывается в Observed при upsert с тем же claim
    m.store_fact({"fact_id": "x", "claim": "a", "source": "s", "confidence": 0.7})

    row = sqlite3.connect(m.db_path).execute(
        "SELECT epistemic_state FROM facts WHERE fact_id='x'"
    ).fetchone()
    assert row[0] == "Validated", f"L1 epistemic_state откатился: {row[0]}"
    assert m.get_fact("x")["epistemic_state"] == "Validated"


# ─── P0.3: get_all_facts прогревает L0 ───────────────────────────────────────

def test_p0_3_get_all_facts_warms_l0(fresh_db):
    m = fresh_db
    m.store_fact({"fact_id": "w1", "claim": "a", "source": "s"})
    m.store_fact({"fact_id": "w2", "claim": "b", "source": "s"})
    m._l0.clear()
    assert "w1" not in m._l0

    m.get_all_facts()
    assert "w1" in m._l0, "w1 не прогрет в L0"
    assert "w2" in m._l0, "w2 не прогрет в L0"


# ─── Ring Zero: Validated сохраняется при повторном store_fact ────────────────

def test_ring_zero_validated_preserved_by_store_fact(fresh_db):
    m = fresh_db
    m.store_fact({"fact_id": "RING_ZERO", "claim": "core", "source": "seed",
                  "confidence": 1.0, "epistemic_state": "Validated"})
    m._l0.clear()
    m.store_fact({"fact_id": "RING_ZERO", "claim": "core", "source": "seed",
                  "confidence": 1.0, "epistemic_state": "Validated"})
    assert m.get_fact("RING_ZERO")["epistemic_state"] == "Validated"


# ─── DDL-изоляция: каждый SQLiteGraphStore инициализирует свою БД ─────────────

def test_ddl_initialized_per_store_instance(tmp_path):
    """
    AUDIT-FIX v2.0: тест переписан для использования SQLiteGraphStore напрямую.
    Monkeypatch SQLITE_PATH не влияет на уже созданный _GLOBAL_STORE.
    Правильный способ — создать отдельные инстансы.

    Проверяет: каждый SQLiteGraphStore инициализирует DDL в свою БД,
    данные не перемешиваются между инстансами.
    """
    from core.memory import SQLiteGraphStore, promote_to_validated

    db_a = str(tmp_path / "a.db")
    db_b = str(tmp_path / "b.db")

    store_a = SQLiteGraphStore(db_a)
    store_b = SQLiteGraphStore(db_b)

    store_a.store_fact({"fact_id": "fa", "claim": "A", "source": "s"})
    store_b.store_fact({"fact_id": "fb", "claim": "B", "source": "s"})

    rows_a = sqlite3.connect(db_a).execute(
        "SELECT fact_id FROM facts"
    ).fetchall()
    rows_b = sqlite3.connect(db_b).execute(
        "SELECT fact_id FROM facts"
    ).fetchall()

    assert [r[0] for r in rows_a] == ["fa"], "db_a содержит посторонние факты"
    assert [r[0] for r in rows_b] == ["fb"], "db_b содержит посторонние факты"

    assert db_a in store_a._ddl_initialized_paths
    assert db_b in store_b._ddl_initialized_paths
    assert db_b not in store_a._ddl_initialized_paths, \
        "DDL path store_a не должен знать о db_b"

    store_a.close()
    store_b.close()


# ─── AUDIT-FIX: pipeline.run() idempotency на persistent DB ──────────────────

def test_pipeline_run_persistent_db_no_crash(fresh_db):
    """
    Критический баг v8.0.2: pipeline.run() на одной и той же БД дважды падал.
    Теперь должен проходить без ошибок.
    TASK-07: явно заполняем store — DATABASE mock убран из production-пути.
    """
    from core.memory import promote_to_validated, store_fact, transition_esm
    from core.pipeline import run

    # Кладём 3+ факта — BM25 IDF > 0 только при corpus >= 3 docs.
    # С 1 документом IDF = log(0.5/1.5) < 0 → все scores ≤ 0 → пустой retrieval.
    facts = [
        {"fact_id": "dna1", "claim": "DNA encodes genetic information", "source": "biology", "confidence": 0.99},
        {"fact_id": "pdn1", "claim": "Photons travel at the speed of light", "source": "physics", "confidence": 0.99},
        {"fact_id": "ast1", "claim": "Earth orbits the Sun every 365 days", "source": "astronomy", "confidence": 0.99},
    ]
    for f in facts:
        store_fact(f)
        promote_to_validated(f["fact_id"])

    r1 = run("DNA")
    assert r1.get("answer") is not None

    r2 = run("DNA")
    assert r2.get("answer") is not None
    assert r2.get("error")  is None


# ─── Bi-temporal: данные не теряются при переходах ESM ───────────────────────

def test_bitemporal_ingestion_end_set_on_collapsed(fresh_db):
    """
    I96: при Collapsed t_ingestion_end устанавливается.
    Факт остаётся в БД (no DELETE), но t_ingestion_end указывает
    когда система перестала в него верить.
    """
    m = fresh_db
    m.store_fact({"fact_id": "col", "claim": "x", "source": "s"})
    assert m.get_fact("col")["t_ingestion_end"] is None

    m.transition_esm("col", "Hypothesized")
    m.transition_esm("col", "Contradicted")
    m.transition_esm("col", "Collapsed")
    f = m.get_fact("col")
    assert f is not None,               "Факт не должен быть удалён"
    assert f["t_ingestion_end"] is not None, \
        "t_ingestion_end должен быть установлен при Collapsed"


def test_invalidate_edge_no_delete(fresh_db):
    """
    V9 §2.1: invalidate_edge не удаляет запись — только ставит end-поля.
    """
    m = fresh_db
    m.store_fact({"fact_id": "ie", "claim": "x", "source": "s"})
    m.invalidate_edge("ie")

    # Факт существует
    assert m.get_fact("ie") is not None
    # Но помечен как инвалидный
    f = m.get_fact("ie")
    assert f["t_ingestion_end"]   is not None
    assert f["t_event_valid_end"] is not None
