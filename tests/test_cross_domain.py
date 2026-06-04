"""CrossDomainLayer + DomainOrchestrator (V3 MVP)."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_list_bridges():
    from core.cross_domain import DOMAIN_BRIDGES, list_bridges

    assert len(DOMAIN_BRIDGES) >= 4
    assert any(b["from_domain"] == "science" for b in list_bridges())


def test_orchestrator_plan_science():
    from core.cross_domain import DomainOrchestrator

    plan = DomainOrchestrator().plan(
        "эксперимент с нагрузкой на материал дерева",
        "science",
    )
    assert plan.primary_domain == "science"
    assert plan.cross_domain is True
    assert "engineering" in plan.secondary_domains


@pytest.fixture
def cd_db(tmp_path, monkeypatch):
    import core.memory as mem

    db = str(tmp_path / "cd.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db)
    monkeypatch.setenv("ENABLE_CROSS_DOMAIN", "1")
    monkeypatch.setenv("ENABLE_DOMAIN_TAGS", "1")
    from core.feature_config import clear_config_cache

    clear_config_cache()
    store = mem.make_store(db)
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
    from core.domain_tags import apply_domain_to_metadata
    from core.memory import store_fact

    store_fact(
        {
            "fact_id": "sci_1",
            "claim": "Фотосинтез у деревьев в лесу",
            "source": "experiment",
            "metadata": apply_domain_to_metadata({}, claim="наука", explicit_domain="science"),
        }
    )
    store_fact(
        {
            "fact_id": "eng_1",
            "claim": "Несущая нагрузка балки из древесины",
            "source": "calc",
            "metadata": apply_domain_to_metadata(
                {}, claim="инженерный расчёт", explicit_domain="engineering"
            ),
        }
    )
    yield store
    clear_config_cache()


def test_retrieve_cross_domain_merges(cd_db, monkeypatch):
    from core.cross_domain import get_cross_domain_layer, is_cross_domain_enabled

    assert is_cross_domain_enabled()

  # без hybrid — fallback bm25 / store
    items, plan = get_cross_domain_layer().retrieve(
        "дерево материал нагрузка",
        k=5,
        domain="science",
    )
    assert plan.primary_domain == "science"
    assert isinstance(items, list)
