"""
Tests for core/ngram_index.py — NGram L0 Pre-Filter.

Covers:
  - FTS5 trigram доступность (graceful degradation если нет)
  - index / query / remove / count / rebuild
  - Изоляция через tmp_path
  - Пустые входные данные
  - Идемпотентность index()
  - query() limit соблюдается
  - Синглтон ngram_query / ngram_index_fact / ngram_remove_fact
  - I99: NGramIndex не хранит ESM-состояние
"""
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Fixture: изолированный NGramIndex ─────────────────────────────────────────

@pytest.fixture
def ngram(tmp_path):
    """Каждый тест получает свой NGramIndex в tmp_path."""
    from core.ngram_index import NGramIndex
    idx = NGramIndex(str(tmp_path / "ngram.db"))
    yield idx


@pytest.fixture
def ngram_with_facts(ngram):
    """NGramIndex с пятью проиндексированными фактами из pipeline.py DATABASE."""
    facts = [
        {"fact_id": "f1", "claim": "Water boils at 100 degrees Celsius at sea level"},
        {"fact_id": "f2", "claim": "Quantum entanglement links particles"},
        {"fact_id": "f3", "claim": "Earth revolves around the Sun"},
        {"fact_id": "f4", "claim": "The human brain has 86 billion neurons"},
        {"fact_id": "f5", "claim": "DNA encodes genetic information"},
    ]
    ngram.rebuild(facts)
    yield ngram


# ── FTS5 доступность ──────────────────────────────────────────────────────────

def test_ngram_available_or_graceful_degradation(ngram):
    """NGramIndex либо доступен либо graceful — никогда не падает."""
    # available — True или False, но не исключение
    assert isinstance(ngram.available, bool)


def test_ngram_query_returns_list_even_if_unavailable(ngram):
    """query() всегда возвращает list, даже если FTS5 недоступен."""
    result = ngram.query("anything")
    assert isinstance(result, list)


# ── index / query / count ─────────────────────────────────────────────────────

def test_index_and_query_basic(ngram):
    """Проиндексированный факт находится через query()."""
    if not ngram.available:
        pytest.skip("FTS5 trigram недоступен в этой сборке SQLite")

    ngram.index("f1", "Water boils at 100 degrees Celsius")
    result = ngram.query("water boils")
    assert "f1" in result


def test_query_returns_empty_for_no_match(ngram_with_facts):
    """Запрос без совпадений → пустой список."""
    if not ngram_with_facts.available:
        pytest.skip("FTS5 trigram недоступен")

    result = ngram_with_facts.query("zxqvbnm nonexistent")
    assert result == []


def test_count_reflects_indexed_facts(ngram_with_facts):
    """count() возвращает правильное число проиндексированных документов."""
    if not ngram_with_facts.available:
        pytest.skip("FTS5 trigram недоступен")

    assert ngram_with_facts.count() == 5


def test_query_limit_respected(ngram_with_facts):
    """query() возвращает не больше limit результатов."""
    if not ngram_with_facts.available:
        pytest.skip("FTS5 trigram недоступен")

    # Все факты содержат английские слова — широкий запрос даст много hits
    result = ngram_with_facts.query("the", limit=2)
    assert len(result) <= 2


def test_query_empty_text_returns_empty(ngram_with_facts):
    """Пустой или whitespace-запрос → пустой список."""
    assert ngram_with_facts.query("") == []
    assert ngram_with_facts.query("   ") == []


# ── Идемпотентность ───────────────────────────────────────────────────────────

def test_index_idempotent(ngram):
    """Повторный index() того же fact_id обновляет content, не дублирует."""
    if not ngram.available:
        pytest.skip("FTS5 trigram недоступен")

    ngram.index("f1", "original content")
    ngram.index("f1", "updated content")

    # Должен находиться по новому содержимому
    result = ngram.query("updated content")
    assert "f1" in result

    # count должен быть 1, не 2
    assert ngram.count() == 1


# ── remove ────────────────────────────────────────────────────────────────────

def test_remove_deletes_fact_from_index(ngram_with_facts):
    """remove() убирает факт — он больше не находится через query()."""
    if not ngram_with_facts.available:
        pytest.skip("FTS5 trigram недоступен")

    # f3 — Earth revolves around the Sun
    result_before = ngram_with_facts.query("revolves Sun")
    assert "f3" in result_before

    ngram_with_facts.remove("f3")

    result_after = ngram_with_facts.query("revolves Sun")
    assert "f3" not in result_after
    assert ngram_with_facts.count() == 4


def test_remove_nonexistent_is_safe(ngram):
    """remove() для несуществующего ID не падает."""
    ngram.remove("nonexistent_fact_id")  # не должно бросать исключение


# ── rebuild ───────────────────────────────────────────────────────────────────

def test_rebuild_replaces_existing_index(ngram):
    """rebuild() полностью заменяет старый индекс."""
    if not ngram.available:
        pytest.skip("FTS5 trigram недоступен")

    ngram.index("old1", "old content about apples")
    assert ngram.count() == 1

    new_facts = [
        {"fact_id": "new1", "claim": "quantum mechanics is fascinating"},
        {"fact_id": "new2", "claim": "neural networks learn from data"},
    ]
    count = ngram.rebuild(new_facts)
    assert count == 2
    assert ngram.count() == 2

    # Старый факт не должен находиться
    assert ngram.query("apples") == []
    assert "new1" in ngram.query("quantum")


def test_rebuild_skips_facts_without_claim(ngram):
    """rebuild() пропускает факты без claim или fact_id."""
    if not ngram.available:
        pytest.skip("FTS5 trigram недоступен")

    facts = [
        {"fact_id": "f1", "claim": "valid fact"},
        {"fact_id": "f2"},              # нет claim
        {"claim": "no id"},             # нет fact_id
        {"fact_id": "f3", "claim": ""},  # пустой claim
    ]
    count = ngram.rebuild(facts)
    assert count == 1  # только f1


# ── I99: не хранит ESM-состояние ─────────────────────────────────────────────

def test_ngram_schema_has_no_esm_columns(tmp_path):
    """I99: схема NGramIndex не содержит ESM-полей."""
    from core.ngram_index import NGramIndex
    idx = NGramIndex(str(tmp_path / "schema_check.db"))
    if not idx.available:
        pytest.skip("FTS5 trigram недоступен")

    conn = sqlite3.connect(str(tmp_path / "schema_check.db"))
    # FTS5 таблицы — через fts_config
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    conn.close()

    # Не должно быть полей epistemic_state, history, confidence в индексе
    assert "facts" not in tables, \
        "NGramIndex не должен создавать таблицу 'facts' — это зона memory.py"


# ── Синглтон API ──────────────────────────────────────────────────────────────

def test_singleton_functions_do_not_crash(tmp_path, monkeypatch):
    """ngram_query / ngram_index_fact / ngram_remove_fact работают без исключений."""
    import core.ngram_index as mod
    fresh = mod.NGramIndex(str(tmp_path / "singleton.db"))
    monkeypatch.setattr(mod, "_GLOBAL_NGRAM", fresh)

    mod.ngram_index_fact("s1", "some content about quantum")
    result = mod.ngram_query("quantum")
    assert isinstance(result, list)

    mod.ngram_remove_fact("s1")
    result_after = mod.ngram_query("quantum")
    # После удаления не должен находиться (если FTS5 доступен)
    if fresh.available:
        assert "s1" not in result_after
