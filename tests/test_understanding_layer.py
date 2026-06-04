"""
tests/test_understanding_layer.py — Understanding Layer (Patch 13+14)
"""
import sqlite3

import pytest

from core.causal_graph import CausalGraph
from core.living_context import AgentRelation, LivingContext, LivingContextStore
from core.understanding_layer import UnderstandingLayer


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE facts (
            fact_id TEXT PRIMARY KEY,
            claim   TEXT NOT NULL,
            confidence REAL DEFAULT 0.8,
            epistemic_state TEXT DEFAULT 'Observed'
        );
        CREATE TABLE relations (
            relation_id       TEXT PRIMARY KEY,
            from_fact_id      TEXT NOT NULL,
            to_fact_id        TEXT NOT NULL,
            relation_type     TEXT NOT NULL,
            confidence        REAL NOT NULL DEFAULT 0.8,
            knowledge_status  TEXT NOT NULL DEFAULT 'known',
            inference_source  TEXT DEFAULT NULL,
            truth_status      TEXT DEFAULT 'validated',
            review_state      TEXT DEFAULT 'approved',
            evidence_ref      TEXT, created_at TEXT, valid_from TEXT,
            valid_to TEXT, metadata TEXT,
            CHECK (from_fact_id != to_fact_id),
            UNIQUE (from_fact_id, to_fact_id, relation_type, inference_source)
        );
        CREATE TABLE fact_living_context (
            fact_id    TEXT PRIMARY KEY,
            ctx_where  TEXT NOT NULL DEFAULT '[]',
            ctx_who    TEXT NOT NULL DEFAULT '[]',
            ctx_how    TEXT NOT NULL DEFAULT '[]',
            ctx_what   TEXT NOT NULL DEFAULT '[]',
            ctx_feel   TEXT NOT NULL DEFAULT '{}',
            ctx_role   TEXT NOT NULL DEFAULT '[]',
            ctx_time   TEXT DEFAULT NULL,
            ctx_deep   TEXT DEFAULT NULL,
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE fact_affordance_tokens (
            fact_id TEXT NOT NULL,
            token   TEXT NOT NULL,
            field   TEXT NOT NULL,
            PRIMARY KEY (fact_id, token, field)
        );
        CREATE TABLE fact_affordances (
            fact_id       TEXT NOT NULL,
            affordance_id TEXT NOT NULL,
            confidence    REAL NOT NULL DEFAULT 0.8,
            source        TEXT NOT NULL DEFAULT 'autolinker',
            PRIMARY KEY (fact_id, affordance_id)
        );
    """)
    conn.executemany(
        "INSERT INTO facts (fact_id, claim) VALUES (?, ?)",
        [
            ("f_tree",  "Дерево растёт в лесу"),
            ("f_wood",  "Дрова горят"),
            ("f_bird",  "Птицы вьют гнёзда в деревьях"),
            ("f_shade", "Тень прохладная"),
        ],
    )
    conn.commit()
    return conn


@pytest.fixture
def store(db):
    """Минимальный store-заглушка."""
    class MockStore:
        def __init__(self, conn):
            self._conn = conn
        def get_fact(self, fid):
            row = self._conn.execute(
                "SELECT fact_id, claim FROM facts WHERE fact_id = ?", (fid,)
            ).fetchone()
            return {"fact_id": row[0], "claim": row[1]} if row else None
    return MockStore(db)


@pytest.fixture
def causal_graph(db):
    return CausalGraph(db)


@pytest.fixture
def living_store(db):
    return LivingContextStore(db)


@pytest.fixture
def ul(store, causal_graph, living_store):
    return UnderstandingLayer(store, causal_graph, living_store)


class TestUnderstandingLayer:

    def test_understand_returns_both_layers(self, ul):
        result = ul.understand("f_tree")
        assert "causal" in result
        assert "living_context" in result
        assert "joint_implications" in result
        assert "knowledge_summary" in result

    def test_causal_summary_covers_all_types(self, ul, causal_graph):
        """FIX: _get_causal_summary проверяет все 12 типов, не только 5."""
        causal_graph.add_relation("f_tree", "f_shade",  "enables", 0.9)
        causal_graph.add_relation("f_tree", "f_bird",   "precedes", 0.8)
        result = ul.understand("f_tree")
        causal = result["causal"]
        assert "enables" in causal
        assert "precedes" in causal   # FIX: теперь включён

    def test_inferred_relations_are_pending(self, ul):
        """FIX: affordance_to_causal → PENDING, не canonical."""
        relations = ul.affordance_to_causal("срубить дерево", "f_tree")
        for r in relations:
            assert r["truth_status"] in ("hypothesis", "pending")
            assert r["review_state"] == "pending"
            assert r["source"] == "affordance_inference"

    def test_predict_intervention_is_pearl_level_2(self, ul, causal_graph):
        """FIX: метод predict_intervention(), Pearl Level 2."""
        causal_graph.add_relation("f_tree", "f_wood", "enables", 0.8)
        result = ul.predict_intervention("f_tree", "срубить все деревья")
        assert "causal_chain" in result
        assert result["pearl_level"] == 2
        assert "note" in result

    def test_for_agent_child(self, ul, living_store):
        """for_agent('child') возвращает can_do."""
        ctx = LivingContext(affordances=["укрыться от дождя", "сделать дрова"])
        living_store.set("f_tree", ctx)
        result = ul.for_agent("f_tree", "child")
        assert "can_do" in result

    def test_for_agent_scientist(self, ul):
        """for_agent('scientist') возвращает causes + knowledge_summary."""
        result = ul.for_agent("f_tree", "scientist")
        assert "knowledge_summary" in result

    def test_for_agent_engineer(self, ul, causal_graph):
        """for_agent('engineer') возвращает products + becomes."""
        causal_graph.add_relation("f_tree", "f_wood", "becomes", 0.9)
        result = ul.for_agent("f_tree", "engineer")
        assert "products" in result
        assert "becomes" in result

    def test_why_backward_reasoning(self, ul, causal_graph):
        """why() идёт по обратным рёбрам."""
        # FIX v8.5.2 (Claude audit): backward-типы (caused_by) теперь создаются
        # автоматически как inverse при добавлении forward-отношения. Чтобы
        # получить ребро f_shade -[caused_by]-> f_tree, добавляем forward-связь
        # f_tree -[causes]-> f_shade. Auto-inverse сохранит и обратное ребро.
        causal_graph.add_relation("f_tree", "f_shade", "causes", 0.9)
        result = ul.why("f_shade")
        assert "fact_id" in result

    def test_joint_reasoning_causal_plus_afford(self, ul, causal_graph, living_store):
        """Joint reasoning объединяет causal и living."""
        causal_graph.add_relation("f_tree", "f_wood", "becomes", 0.9)
        ctx = LivingContext(affordances=["срубить"])
        living_store.set("f_tree", ctx)
        result = ul.understand("f_tree")
        assert isinstance(result["joint_implications"], list)

    def test_unknown_fact_returns_error(self, ul):
        """Несуществующий факт → error в результате."""
        result = ul.understand("nonexistent_fact_xyz")
        assert "error" in result

    def test_existing_facts_unaffected(self, ul, store):
        """Работа UL не изменяет сами факты."""
        ul.understand("f_tree")
        fact = store.get_fact("f_tree")
        assert fact["claim"] == "Дерево растёт в лесу"


class TestLivingContext:

    def test_living_context_is_empty(self):
        ctx = LivingContext()
        assert ctx.is_empty() is True

    def test_living_context_not_empty_with_data(self):
        ctx = LivingContext(affordances=["сделать тень"])
        assert ctx.is_empty() is False

    def test_to_dict_from_dict_roundtrip(self):
        """Lossless serialization."""
        ctx = LivingContext(
            locations=["лес", "парк"],
            agents=[AgentRelation(entity="птица", role="гнездится", weight=0.9)],
            affordances=["сделать тень", "срубить"],
            products=["дрова", "зола"],
            qualities={"живое": 0.95, "сильное": 0.80},
            roles=["даёт кислород", "держит почву"],
        )
        d = ctx.to_dict()
        restored = LivingContext.from_dict(d)
        assert restored.locations == ctx.locations
        assert restored.affordances == ctx.affordances
        assert restored.products == ctx.products
        assert restored.qualities == ctx.qualities
        assert len(restored.agents) == len(ctx.agents)
        assert restored.agents[0].entity == "птица"

    def test_merge_combines_without_overwrite(self):
        ctx1 = LivingContext(
            affordances=["сделать тень"],
            qualities={"живое": 0.90},
        )
        ctx2 = LivingContext(
            affordances=["срубить"],
            qualities={"живое": 0.80, "сильное": 0.85},
        )
        merged = ctx1.merge(ctx2)
        assert "сделать тень" in merged.affordances
        assert "срубить" in merged.affordances
        # Берём максимальное качество
        assert merged.qualities["живое"] == pytest.approx(0.90)
        assert merged.qualities["сильное"] == pytest.approx(0.85)

    def test_living_context_store_set_get(self, living_store):
        ctx = LivingContext(
            locations=["лес"],
            affordances=["укрыться"],
        )
        living_store.set("f_tree", ctx)
        restored = living_store.get("f_tree")
        assert restored is not None
        assert "укрыться" in restored.affordances
        assert "лес" in restored.locations

    def test_living_context_store_update_merges(self, living_store):
        ctx1 = LivingContext(affordances=["тень"])
        ctx2 = LivingContext(affordances=["дрова"])
        living_store.set("f_tree", ctx1)
        living_store.update("f_tree", ctx2)
        merged = living_store.get("f_tree")
        assert "тень" in merged.affordances
        assert "дрова" in merged.affordances

    def test_living_context_delete(self, living_store):
        ctx = LivingContext(affordances=["тень"])
        living_store.set("f_tree", ctx)
        assert living_store.delete("f_tree") is True
        assert living_store.get("f_tree") is None
        assert living_store.delete("f_tree") is False
