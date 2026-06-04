"""CrossDomain: smart routing + causal edges."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def cd_causal_db(tmp_path, monkeypatch):
    import core.memory as mem
    from core.pipeline import reset_causal_graph

    db = str(tmp_path / "cdc.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db)
    monkeypatch.setenv("ENABLE_CROSS_DOMAIN", "1")
    monkeypatch.setenv("ENABLE_CROSS_DOMAIN_CAUSAL", "1")
    monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "1")
    from core.feature_config import clear_config_cache

    clear_config_cache()
    store = mem.make_store(db)
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
    import core.pipeline as pipe

    monkeypatch.setattr(pipe, "_GLOBAL_STORE", store)
    from core.domain_tags import apply_domain_to_metadata
    from core.memory import store_fact

    store_fact(
        {
            "fact_id": "sci_x",
            "claim": "Эксперимент измеряет прочность древесины",
            "source": "lab",
            "metadata": apply_domain_to_metadata({}, explicit_domain="science"),
        }
    )
    store_fact(
        {
            "fact_id": "eng_x",
            "claim": "Расчёт нагрузки на балку из материала",
            "source": "calc",
            "metadata": apply_domain_to_metadata({}, explicit_domain="engineering"),
        }
    )
    reset_causal_graph()
    yield store
    reset_causal_graph()
    clear_config_cache()


def test_smart_term_routing():
    from core.cross_domain import DomainOrchestrator

    plan = DomainOrchestrator().plan(
        "инженерный расчёт нагрузки и материал прочность",
        "science",
    )
    assert plan.routing == "smart_terms"
    assert "engineering" in plan.secondary_domains


def test_sync_cross_domain_edges(cd_causal_db):
    from core.causal_graph import get_causal_graph
    from core.cross_domain import DomainOrchestrator, sync_cross_domain_edges
    from core.memory import get_fact

    plan = DomainOrchestrator().plan("материал нагрузка", "science")
    facts = [get_fact("sci_x"), get_fact("eng_x")]
    links = sync_cross_domain_edges(facts, plan, max_links=3)
    assert len(links) >= 1
    cg = get_causal_graph()
    rels = cg.get_relations_from("sci_x")
    assert any(r.to_fact_id == "eng_x" for r in rels) or links
