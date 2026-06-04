"""
Тесты линковщика базы знаний (core/knowledge_linker.py).
Проверяют: парсинг тегов, направленные рёбра по совпадению тег↔сегмент-id,
складывание в цепочку, отсутствие self-edge и матча на корень-домен, статус/уверенность.
"""
from core.knowledge_linker import DEFAULT_RELATION, link_by_tags, parse_tags

# ── parse_tags ────────────────────────────────────────────────────────────────

def test_parse_tags_splits_and_filters():
    assert parse_tags("food, industry") == ["food", "industry"]
    assert parse_tags("textile.linen") == ["textile", "linen"]
    assert parse_tags("wheat") == ["wheat"]
    assert parse_tags(["food", "baking"]) == ["food", "baking"]
    assert parse_tags("a, of, in") == []          # короткие токены отброшены (<3)
    assert parse_tags("") == []


# ── link_by_tags: базовое ребро ────────────────────────────────────────────────

def test_tag_matching_id_segment_creates_edge():
    facts = [
        {"fact_id": "agro.crop.wheat.grain", "links": ""},
        {"fact_id": "food.process.milling", "links": "wheat"},
    ]
    edges = link_by_tags(facts)
    assert len(edges) == 1
    e = edges[0]
    assert e["source_id"] == "agro.crop.wheat.grain"   # A (домен совпал с тегом)
    assert e["target_id"] == "food.process.milling"    # B (тег «wheat»)
    assert e["relation_type"] == DEFAULT_RELATION       # enables
    assert e["knowledge_status"] == "inferred"
    assert e["confidence"] == 0.6


def test_edges_form_a_chain():
    facts = [
        {"fact_id": "d.wheat", "links": ""},
        {"fact_id": "d.milling", "links": "wheat"},     # wheat -> milling
        {"fact_id": "d.sieving", "links": "milling"},   # milling -> sieving
    ]
    edges = link_by_tags(facts)
    pairs = {(e["source_id"], e["target_id"]) for e in edges}
    assert ("d.wheat", "d.milling") in pairs
    assert ("d.milling", "d.sieving") in pairs


# ── защитные правила ────────────────────────────────────────────────────────────

def test_no_self_edge():
    facts = [{"fact_id": "d.wheat", "links": "wheat"}]   # тег совпадает со своим же сегментом
    assert link_by_tags(facts) == []


def test_domain_root_not_matched():
    # тег «food» = корень-домен → НЕ матчим (иначе всё связано со всем)
    facts = [
        {"fact_id": "food.flour", "links": ""},
        {"fact_id": "bakery.bread", "links": "food"},
    ]
    assert link_by_tags(facts) == []


def test_tag_matching_nothing_no_edge():
    facts = [
        {"fact_id": "agro.crop.flax.fiber", "links": "textile.linen"},  # нет факта 'textile'/'linen'
        {"fact_id": "agro.crop.cotton.fiber", "links": ""},
    ]
    assert link_by_tags(facts) == []


def test_broad_token_skipped():
    # токен 'hub' совпадает с 6 фактами (>MAX_SEGMENT_FANOUT) → категория, не связь → скип
    facts = [{"fact_id": f"d.hub.n{i}", "links": ""} for i in range(6)]
    facts.append({"fact_id": "d.consumer", "links": "hub"})
    assert link_by_tags(facts) == []


def test_specific_token_within_fanout_kept():
    # 'wheat' совпадает с 2 фактами (<= порога) → специфичная связь сохраняется
    facts = [
        {"fact_id": "agro.wheat.grain", "links": ""},
        {"fact_id": "agro.wheat.gluten", "links": ""},
        {"fact_id": "food.milling", "links": "wheat"},
    ]
    srcs = {e["source_id"] for e in link_by_tags(facts)}
    assert srcs == {"agro.wheat.grain", "agro.wheat.gluten"}


# ── ① ориентация по типу ────────────────────────────────────────────────────

def test_type_orientation_flips_reversed_edge():
    # структурно процесс сматчен тегом от материала → ребро должно стать материал→процесс
    facts = [
        {"fact_id": "textile.process.cotton.card", "type": "PROCESS",
         "claim": "Кардочесание распрямляет волокно", "links": ""},
        {"fact_id": "agro.crop.cotton.fiber", "type": "MATERIAL_SOURCE",
         "claim": "Хлопок даёт волокно", "links": "cotton"},
    ]
    edges = link_by_tags(facts)
    assert len(edges) == 1
    assert edges[0]["source_id"] == "agro.crop.cotton.fiber"        # материал — источник
    assert edges[0]["target_id"] == "textile.process.cotton.card"  # процесс — приёмник
    assert edges[0]["relation_type"] == "enables"


# ── ② типизация ребра по типам/cue ────────────────────────────────────────────

def test_same_process_tier_uses_precedes():
    # 4-сегментные id (как в реальных батчах: domain.cat.concept.qualifier)
    facts = [
        {"fact_id": "food.process.milling.grain", "type": "PROCESS",
         "claim": "Помол даёт муку", "links": ""},
        {"fact_id": "food.process.sieving.sort", "type": "PROCESS",
         "claim": "Просеивание сортирует муку", "links": "milling"},
    ]
    edges = link_by_tags(facts)
    assert len(edges) == 1
    assert (edges[0]["source_id"], edges[0]["target_id"]) == (
        "food.process.milling.grain", "food.process.sieving.sort")
    assert edges[0]["relation_type"] == "precedes"


def test_causal_cue_uses_causes():
    facts = [
        {"fact_id": "phys.water.freeze.expand", "type": "MECHANISM",
         "claim": "Замерзание расширяет воду", "links": ""},
        {"fact_id": "eng.road.damage.cracks", "type": "FAILURE_MODE",
         "claim": "Расширение льда вызывает трещины в дороге", "links": "freeze"},
    ]
    edges = link_by_tags(facts)
    assert len(edges) == 1
    assert edges[0]["relation_type"] == "causes"
