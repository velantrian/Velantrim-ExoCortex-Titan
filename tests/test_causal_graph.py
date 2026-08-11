"""
tests/test_causal_graph.py — Velantrim Causal Graph (Patch 13 v2)
==================================================================
45+ тестов. Целевое покрытие: ≥90% для core/causal_graph.py.

Запуск:
    pytest tests/test_causal_graph.py -v
    pytest tests/test_causal_graph.py -v -k "TestRelationCRUD"
"""
import sqlite3

import pytest

from core.causal_graph import (
    CausalGraph,
    Relation,
)

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    """In-memory SQLite с полной схемой."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")

    # Создаём facts таблицу (минимальная версия)
    conn.execute("""
        CREATE TABLE facts (
            fact_id  TEXT PRIMARY KEY,
            claim    TEXT NOT NULL,
            confidence REAL DEFAULT 0.8,
            epistemic_state TEXT DEFAULT 'Observed'
        )
    """)
    # Создаём relations таблицу
    conn.execute("""
        CREATE TABLE relations (
            relation_id       TEXT PRIMARY KEY,
            from_fact_id      TEXT NOT NULL REFERENCES facts(fact_id) ON DELETE CASCADE,
            to_fact_id        TEXT NOT NULL REFERENCES facts(fact_id) ON DELETE CASCADE,
            relation_type     TEXT NOT NULL,
            confidence        REAL NOT NULL DEFAULT 0.8,
            knowledge_status  TEXT NOT NULL DEFAULT 'known',
            inference_source  TEXT DEFAULT NULL,
            truth_status      TEXT DEFAULT 'validated',
            review_state      TEXT DEFAULT 'approved',
            evidence_ref      TEXT,
            created_at        TEXT,
            valid_from        TEXT,
            valid_to          TEXT,
            metadata          TEXT,
            CHECK (from_fact_id != to_fact_id),
            UNIQUE (from_fact_id, to_fact_id, relation_type, inference_source)
        )
    """)
    conn.execute("CREATE INDEX idx_rel_from ON relations(from_fact_id, relation_type)")
    conn.execute("CREATE INDEX idx_rel_to ON relations(to_fact_id, relation_type)")
    conn.commit()
    return conn


@pytest.fixture
def graph(db):
    """CausalGraph с тестовой БД."""
    return CausalGraph(db)


@pytest.fixture
def facts(db):
    """Набор тестовых фактов в БД."""
    test_facts = [
        ("f_water",   "Вода нужна для жизни",  0.99),
        ("f_life",    "Жизнь существует",       0.99),
        ("f_oxygen",  "Кислород нужен для дыхания", 0.95),
        ("f_fire",    "Огонь горит",            0.90),
        ("f_tree",    "Дерево растёт в лесу",   0.85),
        ("f_wood",    "Дрова можно сжечь",      0.80),
        ("f_heat",    "Тепло нужно людям",      0.85),
        ("f_bird",    "Птицы вьют гнёзда",     0.90),
    ]
    for fact_id, claim, confidence in test_facts:
        db.execute(
            "INSERT INTO facts (fact_id, claim, confidence) VALUES (?, ?, ?)",
            (fact_id, claim, confidence),
        )
    db.commit()
    return {fid: fid for fid, *_ in test_facts}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CRUD операции
# ═══════════════════════════════════════════════════════════════════════════════

class TestRelationCRUD:

    def test_add_simple_relation(self, graph, facts):
        """Добавить causes — успех, возвращает relation_id."""
        rid = graph.add_relation("f_water", "f_life", "causes", confidence=0.9)
        assert rid.startswith("rel_")
        rel = graph.get_relation(rid)
        assert rel is not None
        assert rel.from_fact_id == "f_water"
        assert rel.to_fact_id == "f_life"
        assert rel.relation_type == "causes"
        assert rel.confidence == pytest.approx(0.9)

    def test_invalid_type_rejected(self, graph, facts):
        """relation_type='invalid' → ValueError."""
        with pytest.raises(ValueError, match="relation_type"):
            graph.add_relation("f_water", "f_life", "invalid_type")

    def test_self_loop_rejected(self, graph, facts):
        """from_fact_id == to_fact_id → ValueError."""
        with pytest.raises(ValueError, match="Петли запрещены"):
            graph.add_relation("f_water", "f_water", "causes")

    def test_invalid_confidence(self, graph, facts):
        """confidence > 1.0 → ValueError."""
        with pytest.raises(ValueError, match="confidence"):
            graph.add_relation("f_water", "f_life", "causes", confidence=1.5)

    def test_duplicate_ignored(self, graph, facts):
        """Дубликат — true idempotent no-op с тем же durable relation_id."""
        rid1 = graph.add_relation("f_water", "f_life", "causes",
                                   inference_source="manual")
        rid2 = graph.add_relation("f_water", "f_life", "causes",
                                   inference_source="manual")
        assert rid1 == rid2
        rows = graph.get_relations_from("f_water", relation_type="causes")
        manual_rows = [r for r in rows if r.inference_source == "manual"]
        assert len(manual_rows) == 1

    def test_different_sources_coexist(self, graph, facts):
        """
        Одна пара + один тип, разные sources → оба хранятся.
        Автоматический source остаётся pending и поэтому читается здесь явно.
        """
        graph.add_relation("f_water", "f_life", "causes",
                            inference_source="manual")
        graph.add_relation("f_water", "f_life", "causes",
                            inference_source="autolinker")
        rows = graph.get_relations_from(
            "f_water", relation_type="causes", only_approved=False
        )
        sources = {r.inference_source for r in rows}
        assert "manual" in sources
        assert "autolinker" in sources

    def test_inverse_auto_created(self, graph, facts):
        """add_relation('causes') → автоматический 'caused_by'."""
        graph.add_relation("f_water", "f_life", "causes", confidence=0.9)
        inverse_rels = graph.get_relations_from("f_life")
        assert any(r.relation_type == "caused_by" for r in inverse_rels)
        to_rels = graph.get_relations_to("f_life", relation_type="causes")
        assert len(to_rels) >= 1

    def test_knowledge_status_stored(self, graph, facts):
        """knowledge_status='inferred' сохраняется и читается."""
        rid = graph.add_relation("f_water", "f_life", "enables",
                                  knowledge_status="inferred",
                                  inference_source="autolinker")
        rel = graph.get_relation(rid)
        assert rel.knowledge_status == "inferred"
        assert rel.inference_source == "autolinker"
        assert rel.truth_status == "hypothesis"
        assert rel.review_state == "pending"

    def test_inference_source_stored(self, graph, facts):
        """inference_source='atlas_sync' сохраняется."""
        rid = graph.add_relation("f_water", "f_life", "requires",
                                  knowledge_status="inferred",
                                  inference_source="atlas_sync")
        rel = graph.get_relation(rid)
        assert rel.inference_source == "atlas_sync"

    def test_invalid_knowledge_status_rejected(self, graph, facts):
        """knowledge_status='magic' → ValueError."""
        with pytest.raises(ValueError, match="knowledge_status"):
            graph.add_relation("f_water", "f_life", "causes",
                               knowledge_status="magic")

    def test_remove_relation(self, graph, facts):
        """Удаление работает."""
        rid = graph.add_relation("f_water", "f_life", "causes")
        assert graph.remove_relation(rid) is True
        assert graph.get_relation(rid) is None
        assert graph.remove_relation(rid) is False

    def test_get_relations_from_filter_type(self, graph, facts):
        """get_relations_from с фильтром relation_type."""
        graph.add_relation("f_water", "f_life", "causes")
        graph.add_relation("f_water", "f_oxygen", "requires")
        causes = graph.get_relations_from("f_water", relation_type="causes")
        assert all(r.relation_type == "causes" for r in causes)

    def test_get_relations_to(self, graph, facts):
        """get_relations_to возвращает входящие отношения."""
        graph.add_relation("f_water", "f_life", "causes")
        rels = graph.get_relations_to("f_life", relation_type="causes")
        assert any(r.from_fact_id == "f_water" for r in rels)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Графовый обход
# ═══════════════════════════════════════════════════════════════════════════════

class TestGraphTraversal:

    def test_causal_chain_depth_3(self, graph, facts):
        """A→B→C→D, depth=3 возвращает цепочку."""
        graph.add_relation("f_water",  "f_life",   "causes",  0.9)
        graph.add_relation("f_life",   "f_oxygen", "enables", 0.8)
        graph.add_relation("f_oxygen", "f_fire",   "enables", 0.7)

        chains = graph.causal_chain("f_water", max_depth=3, min_confidence=0.5)
        assert len(chains) > 0
        long_chains = [c for c in chains if len(c.chain) >= 2]
        assert len(long_chains) > 0

    def test_chain_respects_min_confidence(self, graph, facts):
        """Звено с confidence=0.3 не попадает при min_confidence=0.5."""
        graph.add_relation("f_water", "f_life", "causes", 0.9)
        graph.add_relation("f_life", "f_oxygen", "causes", 0.3)

        chains = graph.causal_chain("f_water", max_depth=3, min_confidence=0.5)
        for c in chains:
            for r in c.chain:
                assert r.confidence >= 0.5

    def test_implications_follows_implies_and_causes(self, graph, facts):
        """implies + causes объединяются в обход."""
        graph.add_relation("f_water", "f_life",   "implies", 0.8)
        graph.add_relation("f_water", "f_oxygen",  "causes",  0.9)

        implications = graph.implications("f_water", depth=2)
        implied_ids = {fid for fid, _ in implications}
        assert "f_life" in implied_ids
        assert "f_oxygen" in implied_ids

    def test_explain_traverses_backward(self, graph, facts):
        """explain() идёт по обратным рёбрам."""
        graph.add_relation("f_water", "f_life", "causes", 0.9)
        explanation = graph.explain("f_life")
        assert explanation["has_explanation"] is True
        caused_by_ids = [e["fact_id"] for e in explanation["caused_by"]]
        assert "f_water" in caused_by_ids

    def test_only_known_filter(self, graph, facts):
        """Pending inference хранится, но не попадает в approved traversal."""
        graph.add_relation("f_water", "f_life",   "causes", 0.9,
                            knowledge_status="known")
        graph.add_relation("f_water", "f_oxygen", "causes", 0.7,
                            knowledge_status="inferred",
                            inference_source="autolinker")

        chains_all = graph.causal_chain("f_water", only_known=False)
        chains_known = graph.causal_chain("f_water", only_known=True)

        all_targets = {r.to_fact_id for c in chains_all for r in c.chain}
        known_targets = {r.to_fact_id for c in chains_known for r in c.chain}

        assert "f_life" in all_targets
        assert "f_oxygen" not in all_targets
        assert "f_life" in known_targets
        assert "f_oxygen" not in known_targets

        pending = graph.get_relations_from(
            "f_water", relation_type="causes", only_approved=False
        )
        pending_targets = {r.to_fact_id for r in pending if r.review_state == "pending"}
        assert "f_oxygen" in pending_targets


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Confidence Propagation (v2)
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfidencePropagation:

    def test_chain_confidence_min(self, graph, facts):
        r1 = Relation("r1", "f_water",  "f_life",   "causes", 0.9)
        r2 = Relation("r2", "f_life",   "f_oxygen", "causes", 0.7)
        chain = CausalGraph._chain_confidence([r1, r2])
        assert chain.min_confidence == pytest.approx(0.7)

    def test_chain_confidence_product(self, graph, facts):
        r1 = Relation("r1", "f_water", "f_life",   "causes", 0.9)
        r2 = Relation("r2", "f_life",  "f_oxygen", "causes", 0.7)
        chain = CausalGraph._chain_confidence([r1, r2])
        assert chain.product_confidence == pytest.approx(0.63, rel=1e-3)

    def test_hypothetical_flagged(self, graph, facts):
        r1 = Relation("r1", "f_water", "f_life",   "causes", 0.9,
                       knowledge_status="known")
        r2 = Relation("r2", "f_life",  "f_oxygen", "causes", 0.7,
                       knowledge_status="hypothetical")
        chain = CausalGraph._chain_confidence([r1, r2])
        assert chain.has_hypothetical is True

    def test_chain_result_is_trustworthy(self, graph, facts):
        r1 = Relation("r1", "f_water", "f_life", "causes", 0.9)
        chain = CausalGraph._chain_confidence([r1])
        assert chain.is_trustworthy(min_confidence=0.5) is True
        assert chain.is_trustworthy(min_confidence=0.95) is False

    def test_unknown_count(self, graph, facts):
        r1 = Relation("r1", "f_water", "f_life",   "causes", 0.9,
                       knowledge_status="unknown")
        r2 = Relation("r2", "f_life",  "f_oxygen", "causes", 0.8,
                       knowledge_status="unknown")
        chain = CausalGraph._chain_confidence([r1, r2])
        assert chain.unknown_count == 2

    def test_empty_chain(self):
        chain = CausalGraph._chain_confidence([])
        assert chain.min_confidence == 1.0
        assert chain.product_confidence == 1.0
        assert chain.has_hypothetical is False
        assert chain.unknown_count == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Knowledge Boundary (v2)
# ═══════════════════════════════════════════════════════════════════════════════

class TestKnowledgeBoundary:

    def test_knowledge_summary_counts(self, graph, facts):
        graph.add_relation("f_water", "f_life",   "causes", 0.9,
                            knowledge_status="known")
        graph.add_relation(
            "f_water", "f_oxygen", "enables", 0.7,
            knowledge_status="inferred", inference_source="autolinker",
            truth_status="validated", review_state="approved",
        )
        summary = graph.knowledge_summary("f_water")
        assert summary["known_relations"] >= 1
        assert summary["inferred_relations"] >= 1
        assert summary["total_relations"] >= 2

    def test_summary_recommendation_reliable(self, graph, facts):
        graph.add_relation("f_water", "f_life", "causes", 0.95,
                            knowledge_status="known")
        summary = graph.knowledge_summary("f_water")
        assert summary["recommendation"] in ("reliable", "verify")

    def test_summary_recommendation_verify(self, graph, facts):
        graph.add_relation(
            "f_water", "f_life", "causes", 0.7,
            knowledge_status="inferred", inference_source="autolinker",
            truth_status="validated", review_state="approved",
        )
        summary = graph.knowledge_summary("f_water")
        assert summary["recommendation"] == "verify"

    def test_summary_recommendation_incomplete(self, graph, facts):
        graph.add_relation(
            "f_water", "f_life", "causes", 0.7,
            knowledge_status="unknown",
            truth_status="validated", review_state="approved",
        )
        summary = graph.knowledge_summary("f_water")
        assert summary["recommendation"] == "incomplete"

    def test_fact_not_in_graph_has_zero_relations(self, graph, facts):
        summary = graph.knowledge_summary("f_heat")
        assert summary["total_relations"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Abstraction Ladder
# ═══════════════════════════════════════════════════════════════════════════════

class TestAbstractionLadder:

    def test_ladder_returns_root_if_no_generalizes(self, graph, facts):
        ladder = graph.abstraction_ladder("f_water")
        assert any("f_water" in level for level in ladder)

    def test_ladder_returns_all_levels(self, graph, facts):
        db = graph._conn
        db.executemany("INSERT INTO facts VALUES (?,?,?,?)", [
            ("f_plant",    "Растение",   0.9, "Observed"),
            ("f_organism", "Организм",   0.9, "Observed"),
        ])
        db.commit()
        graph.add_relation("f_tree",   "f_plant",    "generalizes", 0.9)
        graph.add_relation("f_plant",  "f_organism", "generalizes", 0.9)
        ladder = graph.abstraction_ladder("f_tree", levels=3)
        assert len(ladder) >= 2

    def test_ladder_handles_branching(self, graph, facts):
        db = graph._conn
        db.executemany("INSERT INTO facts VALUES (?,?,?,?)", [
            ("f_plant",    "Растение",  0.9, "Observed"),
            ("f_fungus",   "Гриб",      0.9, "Observed"),
        ])
        db.commit()
        graph.add_relation("f_tree", "f_plant",  "generalizes", 0.9)
        graph.add_relation("f_tree", "f_fungus", "generalizes", 0.8)
        ladder = graph.abstraction_ladder("f_tree")
        all_ids = [fid for level in ladder for fid in level]
        assert "f_plant" in all_ids or "f_fungus" in all_ids


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Counterfactual (Pearl Level 2)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCounterfactual:

    def test_counterfactual_propagates_changes(self, graph, facts):
        graph.add_relation("f_water", "f_life",   "causes", 0.9)
        graph.add_relation("f_life",  "f_oxygen",  "requires", 0.8)
        result = graph.counterfactual("f_water", "испарилась вся вода")
        assert result["pearl_level"] == 2
        assert "causal_chain" in result
        assert result["affected_count"] >= 0

    def test_counterfactual_returns_note(self, graph, facts):
        result = graph.counterfactual("f_water", "изменилось")
        assert "note" in result
        assert "Level 2" in result["note"]

    def test_counterfactual_inferred_via_propagate(self, graph, facts):
        graph.add_relation("f_water", "f_life", "causes", 0.9)
        effects = graph.propagate_change("f_water", "удалить")
        assert isinstance(effects, list)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Contradiction detection
# ═══════════════════════════════════════════════════════════════════════════════

class TestContradictionDetection:

    def test_find_direct_contradictions(self, graph, facts):
        graph.add_relation("f_water", "f_fire", "contradicts", 0.8)
        contradictions = graph.find_contradictions("f_water")
        assert len(contradictions) >= 1
        ct_targets = {r.to_fact_id for r in contradictions}
        ct_targets |= {r.from_fact_id for r in contradictions}
        assert "f_fire" in ct_targets

    def test_no_contradictions_on_empty(self, graph, facts):
        contradictions = graph.find_contradictions("f_heat")
        assert contradictions == []


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Analogies
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnalogies:

    def test_direct_analogous_to_returned(self, graph, facts):
        graph.add_relation("f_water", "f_life", "analogous_to", 0.7)
        analogies = graph.find_analogies("f_water")
        analog_ids = {fid for fid, _ in analogies}
        assert "f_life" in analog_ids

    def test_no_self_in_analogies(self, graph, facts):
        graph.add_relation("f_water", "f_life", "causes")
        analogies = graph.find_analogies("f_water")
        analog_ids = {fid for fid, _ in analogies}
        assert "f_water" not in analog_ids


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Statistics
# ═══════════════════════════════════════════════════════════════════════════════

class TestStats:

    def test_stats_empty_graph(self, graph, facts):
        stats = graph.stats()
        assert stats["total_relations"] == 0
        assert stats["unique_source_facts"] == 0

    def test_stats_counts_by_type(self, graph, facts):
        graph.add_relation("f_water", "f_life",   "causes")
        graph.add_relation("f_water", "f_oxygen", "enables")
        stats = graph.stats()
        assert stats["total_relations"] >= 2


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Regression: существующие факты не затрагиваются
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegression:

    def test_existing_facts_unaffected_by_graph(self, graph, facts):
        graph.add_relation("f_water", "f_life", "causes")
        row = graph._conn.execute(
            "SELECT claim FROM facts WHERE fact_id = 'f_water'"
        ).fetchone()
        assert row[0] == "Вода нужна для жизни"

    def test_cascade_delete_on_fact_removal(self, graph, facts):
        graph.add_relation("f_bird", "f_tree", "requires")
        graph._conn.execute("DELETE FROM facts WHERE fact_id = 'f_bird'")
        graph._conn.commit()
        rels = graph.get_relations_from("f_bird")
        assert rels == []

    def test_relation_is_reliable_method(self, graph, facts):
        r = Relation("r1", "f_water", "f_life", "causes", 0.9,
                      knowledge_status="known")
        assert r.is_reliable(min_confidence=0.5) is True
        assert r.is_reliable(min_confidence=0.95) is False

        r_unknown = Relation("r2", "f_water", "f_life", "causes", 0.9,
                              knowledge_status="unknown")
        assert r_unknown.is_reliable() is False


# ─── TASK-10: cycle protection ────────────────────────────────────────────────

def test_find_contradictions_no_infinite_loop_on_cycle(db, graph):
    for fid, claim in [("fc1","A implies B"), ("fc2","B implies C"), ("fc3","C contradicts A")]:
        db.execute(
            "INSERT OR IGNORE INTO facts (fact_id, claim, confidence, epistemic_state)"
            " VALUES (?,?,?,?)",
            (fid, claim, 0.9, "Validated")
        )
    db.commit()

    graph.add_relation("fc1", "fc2", "implies", confidence=0.8, knowledge_status="known")
    graph.add_relation("fc2", "fc3", "implies", confidence=0.8, knowledge_status="known")
    graph.add_relation("fc3", "fc1", "implies", confidence=0.8, knowledge_status="known")
    graph.add_relation("fc1", "fc3", "contradicts", confidence=0.9, knowledge_status="known")

    import sys
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(100)
    try:
        result = graph.find_contradictions("fc1")
        assert isinstance(result, list)
    finally:
        sys.setrecursionlimit(old_limit)


# ─── TASK-11: BFS deque ───────────────────────────────────────────────────────

def test_causal_chain_uses_deque(db, graph):
    fact_ids = [f"chain_{i}" for i in range(6)]
    for fid in fact_ids:
        db.execute(
            "INSERT OR IGNORE INTO facts (fact_id, claim, confidence, epistemic_state)"
            " VALUES (?,?,?,?)",
            (fid, f"fact {fid}", 0.9, "Validated")
        )
    db.commit()

    for i in range(len(fact_ids) - 1):
        graph.add_relation(fact_ids[i], fact_ids[i+1], "causes",
                       confidence=0.8, knowledge_status="known")

    chains = graph.causal_chain(fact_ids[0], max_depth=5)
    assert len(chains) > 0
    assert all(len(c.chain) <= 5 for c in chains)


# ─── TASK-12: FactsPackBuilder ────────────────────────────────────────────────

def test_facts_pack_builder_import():
    from core.facts_pack import COGNITIVE_MODE_POLICIES, FactsPackBuilder
    assert "BALANCED" in COGNITIVE_MODE_POLICIES
    assert "PRECISION" in COGNITIVE_MODE_POLICIES
    builder = FactsPackBuilder("BALANCED")
    assert builder.mode == "BALANCED"
