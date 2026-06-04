"""
Регресс-тест split-brain L0/L1 (audit C-2):
L0-кэш должен заполняться ТОЛЬКО ПОСЛЕ durable-записи в L1, чтобы факт не оставался
в L0 без L1. Проверяем durability: свежий стор (пустой L0) читает факт из L1.
"""


def test_fact_durable_in_l1(tmp_path):
    from core.memory import SQLiteGraphStore
    db = str(tmp_path / "m.db")
    s1 = SQLiteGraphStore(db_path=db)
    s1.store_fact({"fact_id": "x", "claim": "durable fact here", "source": "s", "confidence": 0.9})

    # Вторая копия стора = пустой L0-кэш → чтение идёт ИЗ L1.
    s2 = SQLiteGraphStore(db_path=db)
    got = s2.get_fact("x")
    assert got is not None                      # факт реально в L1 (durable), не только в L0-кэше
    assert got["claim"] == "durable fact here"


def test_l0_and_l1_agree_after_store(tmp_path):
    from core.memory import SQLiteGraphStore
    db = str(tmp_path / "m2.db")
    s = SQLiteGraphStore(db_path=db)
    s.store_fact({"fact_id": "y", "claim": "another durable fact", "source": "s", "confidence": 0.8})
    # из L0-кэша (тот же инстанс) и из L1 (свежий инстанс) — одно и то же состояние
    from_l0 = s.get_fact("y")
    from_l1 = SQLiteGraphStore(db_path=db).get_fact("y")
    assert from_l0["epistemic_state"] == from_l1["epistemic_state"] == "Observed"
    assert from_l0["claim"] == from_l1["claim"]
