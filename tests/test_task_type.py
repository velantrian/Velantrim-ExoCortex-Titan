"""Тесты Task Type Classifier (core/task_type.py) + роутинга в pipeline."""
from __future__ import annotations

import pytest


@pytest.mark.parametrize("query,expected", [
    ("почему железо ржавеет",               "WHY"),
    ("зачем нужна изоляция",                "WHY"),
    ("как работает двигатель внутреннего сгорания", "HOW"),
    ("каким образом передаётся тепло",      "HOW"),
    ("что такое фотосинтез",                "EXPLAIN"),
    ("объясни закон Ома",                   "EXPLAIN"),
    ("сравни медь и алюминий",              "COMPARE"),
    ("чем отличается кислота от щёлочи",     "COMPARE"),
    ("что лучше: сталь или титан",          "COMPARE"),
    ("реши уравнение для тока",             "SOLVE"),
    ("вычисли сопротивление цепи",          "SOLVE"),
    ("сколько планет в солнечной системе",  "FACT"),
    ("когда замерзает вода",                "FACT"),
    ("какой металл самый лёгкий",           "FACT"),
    ("кто открыл электрон",                 "FACT"),
    ("",                                     "UNKNOWN"),
    ("коррозия металла стальные трубы",      "UNKNOWN"),
])
def test_classify_task_type(query, expected):
    from core.task_type import classify_task_type
    assert classify_task_type(query) == expected, f"{query!r} → {classify_task_type(query)!r}"


def test_is_reasoning_query():
    from core.task_type import is_reasoning_query
    assert is_reasoning_query("почему металл ржавеет")       # WHY
    assert is_reasoning_query("как работает фотосинтез")     # HOW
    assert not is_reasoning_query("сколько весит протон")    # FACT
    assert not is_reasoning_query("просто слова")            # UNKNOWN


# ─── Роутинг в pipeline (ENABLE_TASK_ROUTING) ────────────────────────────────

@pytest.fixture()
def isolated_db(monkeypatch, tmp_path):
    """Изолированный store для pipeline-теста (как в test_pipeline.py)."""
    from core import memory
    fresh = memory.make_store(str(tmp_path / "tt.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE",    fresh)
    monkeypatch.setattr(memory, "_L0",              fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH",      str(tmp_path / "tt.db"))
    yield fresh
    fresh.close()


def test_pipeline_task_routing_sets_type(isolated_db, monkeypatch):
    """С ENABLE_TASK_ROUTING pipeline классифицирует запрос и кладёт task_type в ответ;
    WHY → reasoning (расширение разрешено), FACT → прямой (расширение запрещено)."""
    import core.essence as ess
    from core import pipeline
    from core.memory import store_fact, transition_esm, promote_to_validated
    monkeypatch.setattr(ess, "is_essence_enabled", lambda: True)
    monkeypatch.setattr(pipeline, "_task_routing_enabled", lambda: True)

    for fid, claim in [("ir1", "Железо ржавеет во влажном воздухе"),
                       ("ir2", "Ржавчина это оксид железа на поверхности")]:
        store_fact({"fact_id": fid, "claim": claim, "source": "chem", "confidence": 0.9,
                    "claim_type": "WORLD_FACT", "origin_type": "EXTERNAL",
                    "metadata": {"evidence_refs": [{"source_id": "c", "span": "1"}]}})
        promote_to_validated(fid)

    r_why = pipeline.run("почему железо ржавеет")
    r_fact = pipeline.run("сколько железа ржавеет")
    assert r_why.get("task_type") == "WHY"
    assert r_fact.get("task_type") == "FACT"
