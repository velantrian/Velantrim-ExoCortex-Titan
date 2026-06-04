"""
Smoke-тест встроенного L3-графа на LadybugDB (форк Kuzu).

Пропускается, если пакет `ladybug` не установлен (опциональная зависимость).
Проверяет реальный движок: upsert узлов/рёбер, идемпотентность ребра (MERGE,
не CREATE — аудит-фикс против дублей), ненаправленный обход и spreading activation.
"""

from __future__ import annotations

import pytest

ladybug = pytest.importorskip("ladybug")

from core.backends.factory import backend_capabilities  # noqa: E402
from core.backends.ladybug_graph import LadybugGraphStore  # noqa: E402


@pytest.fixture(autouse=True)
def _small_buffer(monkeypatch):
    # Маленький буфер-пул: много экземпляров LadybugDB в одном процессе (полный suite)
    # не должны давить память — иначе construction падает в sqlite-fallback.
    monkeypatch.setenv("LADYBUG_BUFFER_POOL_MB", "64")


@pytest.fixture()
def store(tmp_path):
    s = LadybugGraphStore(str(tmp_path / "t.lbug"))
    yield s
    s.close()


def test_capabilities_report_ladybug():
    caps = backend_capabilities()
    assert caps["ladybug"] is True
    # kuzu — устаревший псевдоним, возможности совпадают с ladybug
    assert caps["kuzu"] == caps["ladybug"]


def test_upsert_and_neighbors(store):
    store.upsert_node("a", label="Concept")
    store.upsert_node("b", label="Concept")
    store.upsert_edge("a", "b", relation="RELATED", weight=1.0)
    nbrs = store.get_neighbors("a")
    assert "b" in nbrs
    # Ненаправленный обход: ребро видно и со стороны b
    assert "a" in store.get_neighbors("b")


def test_edge_merge_is_idempotent(store):
    """Повторный upsert одного ребра НЕ должен плодить дубликаты (MERGE)."""
    for w in (1.0, 1.0, 0.5, 2.0):
        store.upsert_edge("x", "y", relation="LINK", weight=w)
    rows = store._query(
        "MATCH (:GsNode {node_id:$id})-[e:GsEdge]->(:GsNode) "
        "RETURN count(e) AS n, max(e.weight) AS mx",
        {"id": "x"},
    )
    assert rows and rows[0]["n"] == 1      # ровно одно ребро, не четыре
    assert rows[0]["mx"] == pytest.approx(2.0)  # вес поднят до максимума


def test_spreading_activation(store):
    store.upsert_edge("seed", "n1", relation="R", weight=1.0)
    store.upsert_edge("n1", "n2", relation="R", weight=1.0)
    activated = store.spreading_activation(["seed"], max_hops=2, top_k=10)
    ids = {a.node_id for a in activated}
    assert "seed" in ids and "n1" in ids and "n2" in ids
    # Активация затухает с расстоянием
    by_id = {a.node_id: a.score for a in activated}
    assert by_id["seed"] >= by_id["n1"] >= by_id["n2"]


def test_snapshot_roundtrip(store):
    store.upsert_node("s1")
    store.create_snapshot("snap-1", reason="test", node_ids=["s1"])
    snaps = store.list_snapshots(limit=5)
    assert any(s["snapshot_id"] == "snap-1" and s["node_ids"] == ["s1"] for s in snaps)


def test_kuzu_kind_routes_to_ladybug(monkeypatch):
    """Устаревший STORAGE_BACKEND=kuzu должен маршрутизироваться на LadybugDB,
    а НЕ на sqlite. Проверяем решение роутинга детерминированно — без реальной
    конструкции БД: она покрыта остальными тестами и зависит от ресурсов процесса
    (под нагрузкой фабрика штатно делает graceful fallback в sqlite, и это норма)."""
    import core.backends.factory as fac

    captured = {}

    def fake_create_ladybug(path_env, fallback_db):
        captured["path_env"] = path_env
        return "LADYBUG_SENTINEL"

    monkeypatch.setattr(fac, "_create_ladybug", fake_create_ladybug)
    result = fac.create_graph_store("kuzu")
    assert result == "LADYBUG_SENTINEL"  # kuzu → ladybug-ветка, не sqlite-fallback
    assert captured["path_env"] in ("LADYBUG_DB_PATH", "KUZU_DB_PATH")
