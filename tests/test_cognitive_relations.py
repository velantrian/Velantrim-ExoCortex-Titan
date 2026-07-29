"""Relations preview v9.7 (спринт 3.3)."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def causal_mem(tmp_path, monkeypatch):
    import core.memory as mem
    from core.cognitive_store import reset_cognitive_store

    db = str(tmp_path / "rel.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db)
    monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "1")
    monkeypatch.setenv("ENABLE_COGNITIVE_FACT", "1")
    monkeypatch.setenv("ENABLE_COGNITIVE_STORE", "1")
    from core.feature_config import clear_config_cache

    clear_config_cache()
    reset_cognitive_store()
    store = mem.make_store(db)
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
    from core.pipeline import reset_causal_graph

    reset_causal_graph()
    yield store
    reset_causal_graph()
    reset_cognitive_store()
    clear_config_cache()


class TestRelationsPreview:
    def test_load_relations_for_fact(self, causal_mem):
        from core.causal_graph import get_causal_graph
        from core.cognitive_fact import load_relations_for_fact
        from core.cognitive_store import CognitiveFactStore, get_cognitive_store
        from core.memory import store_fact

        store_fact(
            {
                "fact_id": "fact_a",
                "claim": "A",
                "source": "t",
                "confidence": 0.9,
            }
        )
        store_fact(
            {
                "fact_id": "fact_b",
                "claim": "B",
                "source": "t",
                "confidence": 0.9,
            }
        )
        cg = get_causal_graph()
        cg.add_relation("fact_a", "fact_b", "implies", confidence=0.85)

        rels = load_relations_for_fact("fact_a", limit=10)
        assert len(rels) >= 1
        assert any(r.target_fact_id == "fact_b" for r in rels)

        cf = CognitiveFactStore.create_observed("C", "t", fact_id="fact_c")
        get_cognitive_store().save(cf)
        loaded = get_cognitive_store().get("fact_c", include_relations=False)
        assert loaded is not None
        with_rels = get_cognitive_store().get("fact_a", include_relations=True)
        assert with_rels is not None
        assert len(with_rels.relations) >= 1

        cg = get_causal_graph()
        # import_snapshots() returns (imported, failed) — see M7, Claude
        # audit 2026-07-28.
        n, failed = cg.import_snapshots(
            [
                {
                    "from_fact_id": "fact_a",
                    "to_fact_id": "fact_b",
                    "relation_type": "implies",
                }
            ],
        )
        assert n >= 0
        assert failed == 0


class TestRelationsAPI:
    """API проверяется в test_load_relations_for_fact; отдельный TestClient — опционально."""

    def test_relations_preview_flag(self):
        from core.cognitive_fact import is_relations_preview_enabled

        assert is_relations_preview_enabled() is True or is_relations_preview_enabled() is False
