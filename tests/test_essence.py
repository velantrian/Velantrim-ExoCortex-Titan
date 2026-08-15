"""
Тесты Essence Layer P0 (core/essence.py).
Проверяют правила канона: честность Truth Gate, сохранение uncertainty,
смысловые роли, цепочка смысла, WhyTrace, устойчивость к кривому входу.
"""


from core.essence import (
    Essence,
    MeaningRole,
    WhyTrace,
    compose_essence,
    is_essence_enabled,
)


def _fact(fid, claim, state="Validated", conf=0.9, source="test"):
    return {
        "fact_id": fid,
        "claim": claim,
        "epistemic_state": state,
        "confidence": conf,
        "source": source,
    }


# ── flag ──────────────────────────────────────────────────────────────────────

def test_flag_off_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_ESSENCE", raising=False)
    assert is_essence_enabled() is False


def test_flag_on_when_set(monkeypatch):
    for val in ("1", "true", "TRUE", "yes", "on"):
        monkeypatch.setenv("ENABLE_ESSENCE", val)
        assert is_essence_enabled() is True


# ── empty / defensive ───────────────────────────────────────────────────────

def test_empty_input_is_honest():
    e = compose_essence([])
    assert isinstance(e, Essence)
    assert e.gist == ""
    assert "Нет проверенных фактов" in e.short_answer
    assert e.why.reason == "empty_input"
    assert e.why.gist_fact_id is None


def test_missing_keys_do_not_crash():
    # факты с отсутствующими полями не должны ронять модуль
    e = compose_essence([{"claim": "только claim"}, {}, {"claim": "   "}])
    assert isinstance(e, Essence)
    assert e.gist == "только claim"  # пустые/пробельные claim отброшены


def test_to_dict_structure():
    e = compose_essence([_fact("f1", "Земля вращается вокруг Солнца")])
    d = e.to_dict()
    assert set(d) == {"gist", "short_answer", "roles", "chain",
                      "uncertainty_note", "why", "version"}
    assert d["why"]["gist_fact_id"] == "f1"


# ── выбор сути (gist) ──────────────────────────────────────────────────────────

def test_gist_picks_highest_confidence():
    facts = [
        _fact("f1", "слабый факт", conf=0.55),
        _fact("f2", "сильный факт", conf=0.95),
    ]
    e = compose_essence(facts)
    assert e.gist == "сильный факт"
    assert e.why.gist_fact_id == "f2"


def test_gist_prefers_validated_over_supported_even_if_lower_conf():
    facts = [
        _fact("f1", "supported но уверенный", state="Supported", conf=0.99),
        _fact("f2", "validated но скромный", state="Validated", conf=0.60),
    ]
    e = compose_essence(facts)
    # Validated должен победить Supported несмотря на меньшую уверенность
    assert e.gist == "validated но скромный"


def test_gist_boosted_by_causal_degree():
    facts = [
        _fact("f1", "узел без связей", conf=0.80),
        _fact("f2", "узел-хаб", conf=0.80),
    ]
    relations = [
        {"source_id": "f2", "target_id": "f1", "relation_type": "causes"},
        {"source_id": "f2", "target_id": "f3", "relation_type": "enables"},
    ]
    e = compose_essence(facts, relations)
    assert e.gist == "узел-хаб"  # больше причинных связей → выше score


# ── неопределённость (канон: не скрывать) ──────────────────────────────────────

def test_uncertainty_note_when_only_supported():
    e = compose_essence([_fact("f1", "лишь подкреплён", state="Supported", conf=0.9)])
    assert e.uncertainty_note is not None
    assert "не Validated" in e.uncertainty_note
    assert "⚠️" in e.short_answer


def test_uncertainty_note_when_low_confidence():
    e = compose_essence([_fact("f1", "неуверенно", state="Validated", conf=0.4)])
    assert e.uncertainty_note is not None
    assert "ниже" in e.uncertainty_note


def test_no_uncertainty_for_strong_validated_fact():
    e = compose_essence([_fact("f1", "крепкий факт", state="Validated", conf=0.95)])
    assert e.uncertainty_note is None
    assert "⚠️" not in e.short_answer


def test_contradicted_fact_flags_uncertainty():
    facts = [
        _fact("f1", "основной", state="Validated", conf=0.95),
        _fact("f2", "конфликт", state="Contradicted", conf=0.9),
    ]
    e = compose_essence(facts)
    assert e.uncertainty_note is not None
    assert "Contradicted" in e.uncertainty_note


def test_gist_only_from_eligible_states():
    # если есть только Observed — eligible пуст, но вывод честно помечен
    e = compose_essence([_fact("f1", "лишь наблюдаем", state="Observed", conf=0.9)])
    assert e.gist == "лишь наблюдаем"  # fallback на всё
    assert "Validated/Supported" in (e.uncertainty_note or "")


# ── смысловые роли ─────────────────────────────────────────────────────────────

def test_role_from_causal_relation():
    facts = [_fact("f1", "пожар"), _fact("f2", "дым")]
    relations = [{"source_id": "f1", "target_id": "f2", "relation_type": "causes"}]
    e = compose_essence(facts, relations)
    roles = {r.fact_id: r.role for r in e.roles}
    assert roles["f1"] == MeaningRole.CAUSE.value


def test_role_from_keyword_cue_without_relations():
    e = compose_essence([_fact("f1", "Это приводит к перегреву")])
    assert e.roles[0].role == MeaningRole.EFFECT.value


def test_role_defaults_to_claim():
    e = compose_essence([_fact("f1", "нейтральное утверждение без подсказок")])
    assert e.roles[0].role == MeaningRole.CLAIM.value


# ── смысловая цепочка ──────────────────────────────────────────────────────────

def test_chain_built_from_relations():
    facts = [_fact("f1", "A", conf=0.99), _fact("f2", "B"), _fact("f3", "C")]
    relations = [
        {"source_id": "f1", "target_id": "f2", "relation_type": "causes"},
        {"source_id": "f2", "target_id": "f3", "relation_type": "enables"},
    ]
    e = compose_essence(facts, relations)
    assert e.chain[0] == "A"
    assert "—causes→ B" in e.chain[1]
    assert "—enables→ C" in e.chain[2]
    assert "Цепочка:" in e.short_answer


def test_chain_single_node_without_relations():
    e = compose_essence([_fact("f1", "одинокий факт")])
    assert e.chain == ["одинокий факт"]
    assert "Цепочка:" not in e.short_answer  # одиночный узел не показываем как цепь


def test_chain_no_infinite_loop_on_cycle():
    facts = [_fact("f1", "A", conf=0.99), _fact("f2", "B")]
    relations = [
        {"source_id": "f1", "target_id": "f2", "relation_type": "causes"},
        {"source_id": "f2", "target_id": "f1", "relation_type": "causes"},
    ]
    e = compose_essence(facts, relations)
    assert len(e.chain) <= 4  # цикл не зацикливает построение


# ── WhyTrace ───────────────────────────────────────────────────────────────────

def test_whytrace_records_sources_and_reason():
    facts = [_fact("f1", "главный", conf=0.95), _fact("f2", "второй", conf=0.8)]
    e = compose_essence(facts)
    assert isinstance(e.why, WhyTrace)
    assert e.why.gist_fact_id == "f1"
    assert set(e.why.source_fact_ids) == {"f1", "f2"}
    assert "уверенность" in e.why.reason


def test_whytrace_relation_types_touching_gist():
    facts = [_fact("f1", "hub", conf=0.9), _fact("f2", "leaf")]
    relations = [{"source_id": "f1", "target_id": "f2", "relation_type": "causes"}]
    e = compose_essence(facts, relations)
    assert "causes" in e.why.relation_types


# ── wiring: pipeline.generate_answer за флагом ENABLE_ESSENCE ───────────────────

def _pack(*claims):
    return {"facts": [
        {"fact_id": f"p{i}", "claim": c, "source": "s",
         "epistemic_state": "Validated", "confidence": 0.9}
        for i, c in enumerate(claims)
    ]}


def test_generate_answer_default_is_join(monkeypatch):
    """Флаг ВЫКЛ → прежнее поведение `" | ".join` бит-в-бит, без ключа essence."""
    monkeypatch.delenv("ENABLE_ESSENCE", raising=False)
    from core.pipeline import generate_answer
    res = generate_answer(_pack("Alpha claim", "Beta claim"), [])
    assert res["answer"] == "Alpha claim | Beta claim"
    assert "essence" not in res


def test_generate_answer_essence_when_enabled(monkeypatch):
    """Флаг ВКЛ → ответ «по сути» + структура essence в результате."""
    monkeypatch.setenv("ENABLE_ESSENCE", "true")
    from core.pipeline import generate_answer
    res = generate_answer(_pack("Вода кипит при ста градусах на уровне моря"), [])
    assert res["answer"].startswith("Суть:")
    assert "essence" in res and res["essence"]["gist"]
    # Truth Gate не тронут: трасса и факты по-прежнему в ответе
    assert "facts" in res and "trace" in res


# ── подача causal-связей в Essence (цепочка) ──────────────────────────────────

def _stub_cg(relations_by_from):
    class _CG:
        def get_relations_from(self, fid, **kw):
            return relations_by_from.get(fid, [])
    return _CG()


def _rel(frm, to, rtype="causes", conf=0.9, status="known"):
    from core.causal_graph import Relation
    return Relation(relation_id=f"{frm}->{to}", from_fact_id=frm, to_fact_id=to,
                    relation_type=rtype, confidence=conf, knowledge_status=status)


def test_relations_helper_keeps_only_in_set_and_reliable():
    from core.pipeline import _essence_relations_for
    facts = [{"fact_id": "f0"}, {"fact_id": "f1"}, {"fact_id": "f2"}]
    cg = _stub_cg({
        "f0": [_rel("f0", "f1", "causes")],
        "f1": [_rel("f1", "f2", "enables"),
               _rel("f1", "OUTSIDE", "causes")],                    # конец вне набора
        "f2": [_rel("f2", "f0", "causes", conf=0.35, status="hypothetical")],  # ненадёжно
    })
    pairs = {(r["source_id"], r["target_id"], r["relation_type"])
             for r in _essence_relations_for(facts, cg=cg)}
    assert ("f0", "f1", "causes") in pairs
    assert ("f1", "f2", "enables") in pairs
    assert not any(t == "OUTSIDE" for _, t, _ in pairs)   # ушло наружу → выкинуто
    assert not any(s == "f2" for s, _, _ in pairs)         # гипотетическое → выкинуто


def test_relations_helper_needs_two_facts():
    from core.pipeline import _essence_relations_for
    assert _essence_relations_for([{"fact_id": "only"}], cg=_stub_cg({})) == []


def test_generate_answer_builds_chain_from_causal(monkeypatch):
    monkeypatch.setenv("ENABLE_ESSENCE", "true")
    import core.pipeline as pl
    cg = _stub_cg({"p0": [_rel("p0", "p1", "causes")],
                   "p1": [_rel("p1", "p2", "enables")]})
    monkeypatch.setattr(pl, "_peek_causal_graph", lambda: cg)
    pack = {"facts": [
        {"fact_id": "p0", "claim": "Сухая древесина легко загорается",
         "source": "s", "epistemic_state": "Validated", "confidence": 0.95},
        {"fact_id": "p1", "claim": "Горение выделяет тепло",
         "source": "s", "epistemic_state": "Validated", "confidence": 0.92},
        {"fact_id": "p2", "claim": "Тепло обогревает дом",
         "source": "s", "epistemic_state": "Validated", "confidence": 0.90},
    ]}
    res = pl.generate_answer(pack, [])
    assert "Цепочка:" in res["answer"]
    assert "—causes→" in res["answer"] and "—enables→" in res["answer"]
    assert len(res["essence"]["chain"]) >= 3
