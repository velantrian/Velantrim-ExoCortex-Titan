"""
Тесты линковщика базы знаний (core/knowledge_linker.py).
Проверяют: парсинг тегов, направленные рёбра по совпадению тег↔сегмент-id,
складывание в цепочку, отсутствие self-edge и матча на корень-домен, статус/уверенность.
"""
from core.knowledge_linker import (
    DEFAULT_RELATION,
    graph_quality_report,
    is_causal_for_essence,
    link_by_causal_claims,
    link_by_fact_references,
    link_by_namespace,
    link_by_tags,
    link_facts,
    link_practical_semantics,
    normalize_type,
    parse_tags,
    relation_is_causal_for_essence,
)

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


def test_autolinker_does_not_infer_causes_from_claim_text():
    """Autolinker не выводит causes из текста claim — только curated_explicit."""
    facts = [
        {"fact_id": "phys.water.freeze.expand", "type": "MECHANISM",
         "claim": "Замерзание расширяет воду", "links": ""},
        {"fact_id": "eng.road.damage.cracks", "type": "FAILURE_MODE",
         "claim": "Расширение льда вызывает трещины в дороге", "links": "freeze"},
    ]
    edges = link_by_tags(facts)
    assert edges
    assert all(e["relation_type"] != "causes" for e in edges)


# ── ③ namespace-линковщик: связность (F-01 регрессия-гард) ──────────────────────

def test_namespace_linker_provides_minimal_structure_not_full_mesh():
    """Namespace: ≤1 сосед на узел — структурная подсказка, не полная связность."""
    facts = [
        {"fact_id": f"{domain}.{sub}.{term}", "links": ""}
        for domain in ("agro", "phys", "food")
        for sub in ("alpha", "beta", "gamma")
        for term in ("one", "two", "three")
    ]
    assert link_by_tags(facts) == []
    ns_only = link_by_namespace(facts)
    assert ns_only
    assert all(e["relation_type"] == "analogous_to" for e in ns_only)
    touched = {e["source_id"] for e in ns_only} | {e["target_id"] for e in ns_only}
    assert len(touched) < len(facts)  # namespace без fallback — не 100% coverage
    full = link_facts(facts)
    full_touched = {e["source_id"] for e in full} | {e["target_id"] for e in full}
    assert len(full_touched) == len(facts)  # fallback подключает изолированные узлы


def test_link_facts_no_duplicate_pairs():
    """link_facts: namespace-ребро не дублирует уже существующую тег-пару (в любом
    направлении) — точные тег-связи приоритетны."""
    facts = [
        {"fact_id": "agro.wheat.grain", "links": ""},
        {"fact_id": "agro.wheat.gluten", "links": ""},
        {"fact_id": "food.milling.flour", "links": "wheat"},  # тег-ребро agro.wheat.* → food
    ]
    edges = link_facts(facts)
    pairs = [frozenset((e["source_id"], e["target_id"])) for e in edges]
    assert len(pairs) == len(set(pairs)), "дублирующиеся пары source/target в link_facts"
    # namespace добавил рёбра сверх тег-рёбер (agro.wheat.grain↔gluten не связаны тегом)
    assert len(edges) > len(link_by_tags(facts))


def test_russian_types_are_normalized_for_orientation():
    assert normalize_type("МЕТОД") == "method"
    assert normalize_type("БЕЗОПАСНОСТЬ_ПРАВИЛО") == "safety_rule"
    assert normalize_type("СРОК") == "term"


def test_practical_semantics_builds_foundation_bridge_with_audit_terms():
    facts = [
        {
            "fact_id": "chemistry.surfactant.action",
            "type": "PRINCIPLE",
            "knowledge_unit": "Поверхностно-активные вещества",
            "claim": "Моющее средство с ПАВ отделяет жир и грязь от поверхности.",
            "practical": "Подбор средства зависит от поверхности.",
        },
        {
            "fact_id": "pressurewash.ops.detergent_dwell",
            "type": "METHOD",
            "knowledge_unit": "Выдержка моющего средства",
            "claim": "Моющее средство отделяет жир и грязь от поверхности после выдержки.",
            "practical": "Подбирать средство по типу поверхности.",
        },
    ]
    edges = link_practical_semantics(facts)
    bridge = next(e for e in edges if e["edge_basis"] == "practical_foundation")
    assert bridge["source_id"] == "chemistry.surfactant.action"
    assert bridge["target_id"] == "pressurewash.ops.detergent_dwell"
    assert bridge["relation_type"] == "enables"
    assert len(bridge["matched_terms"]) >= 2
    assert bridge["confidence"] > 0.56


def test_practical_semantics_types_method_to_quality_as_requires():
    facts = [
        {
            "fact_id": "pressurewash.ops.concrete_cleaning",
            "type": "METHOD",
            "claim": "Очистка бетонной поверхности удаляет масло и грязь.",
            "practical": "Проверить бетонную поверхность после очистки.",
        },
        {
            "fact_id": "pressurewash.ops.concrete_quality_check",
            "type": "QUALITY_CHECK",
            "claim": "Проверка бетонной поверхности выявляет остатки масла и грязи.",
            "practical": "Контроль поверхности выполняют после очистки.",
        },
    ]
    edges = link_practical_semantics(facts)
    edge = next(e for e in edges if e["edge_basis"] == "semantic_similarity")
    assert edge["source_id"] == "pressurewash.ops.concrete_cleaning"
    assert edge["target_id"] == "pressurewash.ops.concrete_quality_check"
    assert edge["relation_type"] == "requires"


def test_namespace_edges_are_structural_not_fake_causality():
    facts = [
        {"fact_id": "domain.topic.alpha", "type": "METHOD", "claim": "Alpha unique"},
        {"fact_id": "domain.topic.beta", "type": "METHOD", "claim": "Beta unique"},
    ]
    edges = link_facts(facts)
    assert len(edges) == 1
    assert edges[0]["edge_basis"] == "namespace"
    assert edges[0]["relation_type"] == "analogous_to"
    assert edges[0]["confidence"] == 0.35


def test_graph_quality_report_separates_structure_and_semantics():
    facts = [
        {"fact_id": "theory.surface.cleaning", "type": "PRINCIPLE"},
        {"fact_id": "cleaning.ops.surface_method", "type": "METHOD"},
        {"fact_id": "cleaning.ops.surface_check", "type": "QUALITY_CHECK"},
    ]
    edges = [
        {
            "source_id": "theory.surface.cleaning",
            "target_id": "cleaning.ops.surface_method",
            "relation_type": "enables",
            "edge_basis": "practical_foundation",
        },
        {
            "source_id": "cleaning.ops.surface_method",
            "target_id": "cleaning.ops.surface_check",
            "relation_type": "requires",
            "edge_basis": "semantic_similarity",
        },
    ]
    report = graph_quality_report(facts, edges)
    assert report["coverage_pct"] == 100.0
    assert report["practical_nodes"] == 2
    assert report["practical_bridge_edges"] == 1
    assert report["by_edge_basis"]["practical_foundation"] == 1


def test_namespace_edge_not_causal_for_essence():
    edge = {
        "source_id": "a.x.one",
        "target_id": "a.x.two",
        "relation_type": "analogous_to",
        "edge_basis": "namespace",
    }
    assert not is_causal_for_essence(edge)
    assert not relation_is_causal_for_essence("analogous_to", {"edge_basis": "namespace"})


def test_curated_edge_is_causal_for_essence():
    edge = {
        "source_id": "electric.ops.gfci_afci_operation_test",
        "target_id": "electric.ops.residential_wiring_basics",
        "relation_type": "requires",
        "edge_basis": "curated_explicit",
    }
    assert is_causal_for_essence(edge)
    assert relation_is_causal_for_essence("requires", {"edge_basis": "curated_explicit"})


def test_link_facts_marks_generated_ops_sequence_as_inferred():
    facts = [
        {"fact_id": "electric.ops.step_one", "type": "METHOD",
         "metadata": {"knowledge_file": "651_BATCH_901_ELECTRICAL_INSTALLATION_OPERATIONS.ru.md",
                      "practical_domain": True}},
        {"fact_id": "electric.ops.step_two", "type": "METHOD",
         "metadata": {"knowledge_file": "651_BATCH_901_ELECTRICAL_INSTALLATION_OPERATIONS.ru.md",
                      "practical_domain": True}},
    ]
    edges = link_facts(facts)
    heuristic = [e for e in edges if e.get("edge_basis") == "heuristic_ops_sequence"]
    assert heuristic
    assert all(e["knowledge_status"] == "inferred" for e in heuristic)
    assert all(is_causal_for_essence(e) for e in heuristic)


def test_link_by_causal_claims_from_claim_text():
    facts = [
        {
            "fact_id": "streetlightops.electrical.photocell_fault",
            "type": "INVARIANT",
            "claim": "Fault causes dayburner, night outage, cycling or wrong switching time.",
            "metadata": {"knowledge_file": "289_BATCH_277_STREETLIGHT_MAINTENANCE_OPERATIONS.en.md"},
        },
        {
            "fact_id": "streetlightops.outage.dayburner",
            "type": "INVARIANT",
            "claim": "Dayburner remains on during daylight because of photocell fault.",
            "metadata": {"knowledge_file": "289_BATCH_277_STREETLIGHT_MAINTENANCE_OPERATIONS.en.md"},
        },
    ]
    edges = link_by_causal_claims(facts)
    assert len(edges) == 1
    e = edges[0]
    assert e["source_id"] == "streetlightops.electrical.photocell_fault"
    assert e["target_id"] == "streetlightops.outage.dayburner"
    assert e["relation_type"] == "causes"
    assert e["edge_basis"] == "heuristic_causal_claim"
    assert is_causal_for_essence(e)


def test_link_by_fact_references_from_claim_text():
    facts = [
        {
            "fact_id": "plumb.system.shutoff_main",
            "type": "SYSTEM",
            "claim": "Главный запорный клапан.",
        },
        {
            "fact_id": "emergplumb.ops.water_main_shutoff",
            "type": "METHOD",
            "claim": "Перед работой закройте plumb.system.shutoff_main.",
            "practical": "",
        },
    ]
    edges = link_by_fact_references(facts)
    assert len(edges) == 1
    e = edges[0]
    assert e["source_id"] == "plumb.system.shutoff_main"
    assert e["target_id"] == "emergplumb.ops.water_main_shutoff"
    assert e["edge_basis"] == "claim_reference"
    assert is_causal_for_essence(e)


def test_practical_column_feeds_tag_linker():
    facts = [
        {"fact_id": "agro.crop.wheat.grain", "links": "", "practical": ""},
        {
            "fact_id": "food.process.milling",
            "links": "",
            "practical": "использует wheat при помоле",
        },
    ]
    edges = link_by_tags(facts)
    assert len(edges) == 1
    assert edges[0]["edge_basis"] == "explicit_tag"


def test_namespace_limited_to_one_neighbor_per_node():
    facts = [
        {"fact_id": f"domain.topic.node{i}", "type": "METHOD", "claim": f"Claim {i}"}
        for i in range(6)
    ]
    ns = link_by_namespace(facts)
    degree: dict[str, int] = {}
    for e in ns:
        degree[e["source_id"]] = degree.get(e["source_id"], 0) + 1
        degree[e["target_id"]] = degree.get(e["target_id"], 0) + 1
    assert all(v <= 1 for v in degree.values())
