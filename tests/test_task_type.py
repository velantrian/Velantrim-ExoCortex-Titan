"""Тесты Task Type Classifier (core/task_type.py) + роутинга в pipeline."""
from __future__ import annotations

import pytest



def _r1_promote_to_validated(fact_id, by="test", store=None):
    """TEST-ONLY: enrich to BALANCED TruthGate bar, then protected admission."""
    from core import memory as memory_mod
    api = store or memory_mod
    get = api.get_fact if hasattr(api, "get_fact") else memory_mod.get_fact
    put = api.store_fact if hasattr(api, "store_fact") else memory_mod.store_fact
    promote = api.promote_to_validated if hasattr(api, "promote_to_validated") else memory_mod.promote_to_validated
    fact = get(fact_id)
    if fact is not None:
        meta = dict(fact.get("metadata") or {})
        # TruthGate._count_evidence only counts STRING refs (dicts are ignored).
        refs = [r for r in (meta.get("evidence_refs") or []) if isinstance(r, str)]
        while len(refs) < 2:
            refs.append(f"test_ev_{len(refs)+1}")
        meta["evidence_refs"] = refs
        payload = {
            "fact_id": fact_id,
            "claim": fact.get("claim", ""),
            "source": fact.get("source") or "test",
            "confidence": max(float(fact.get("confidence") or 0.0), 0.8),
            "metadata": meta,
        }
        for extra in ("claim_type", "origin_type", "raw_input", "derived_from"):
            if fact.get(extra) is not None:
                payload[extra] = fact.get(extra)
        put(payload)
    try:
        ok = promote(fact_id, by=by)
    except TypeError:
        ok = promote(fact_id)
    assert ok is True, (
        f"expected TruthGate Validated for {fact_id}; "
        f"fact={get(fact_id)!r}"
    )
    return True

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
        _r1_promote_to_validated(fid)

    r_why = pipeline.run("почему железо ржавеет")
    r_fact = pipeline.run("сколько железа ржавеет")
    assert r_why.get("task_type") == "WHY"
    assert r_fact.get("task_type") == "FACT"
