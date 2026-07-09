"""
Тесты разрешения противоречий (core/contradiction_resolver.py).
Детекция — чистая; движок — на реальном SQLite-сторе (matrix-safe, no-DELETE).
"""
from core.contradiction_resolver import (
    _polarity,
    _subject_key,
    detect_contradictions,
    is_contradiction_resolver_enabled,
    resolve_contradictions,
)

# ── flag ──────────────────────────────────────────────────────────────────────

def test_flag_off_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_CONTRADICTION_RESOLVER", raising=False)
    assert is_contradiction_resolver_enabled() is False


# ── полярность и субъект ──────────────────────────────────────────────────────

def test_polarity_detection():
    assert _polarity("Дерево подходит") == 1
    assert _polarity("Дерево не подходит") == -1
    assert _polarity("This works") == 1
    assert _polarity("This doesn't fit") == -1
    assert _polarity("no longer valid") == -1


def test_subject_key_strips_negation():
    # «X» и «не X» дают ОДИН субъект-ключ
    assert _subject_key("Дерево подходит для дома") == _subject_key("Дерево не подходит для дома")


# ── детекция ────────────────────────────────────────────────────────────────────

def test_detects_negation_contradiction():
    facts = [
        {"fact_id": "a", "claim": "Дерево подходит для дома"},
        {"fact_id": "b", "claim": "Дерево не подходит для дома"},
    ]
    c = detect_contradictions(facts)
    assert len(c) == 1
    assert c[0].older_id == "a" and c[0].newer_id == "b"   # b новее (позже в списке)
    assert c[0].relation_type == "superseded_by"


def test_same_polarity_is_not_contradiction():
    facts = [
        {"fact_id": "a", "claim": "Бюджет ограничен"},
        {"fact_id": "b", "claim": "Бюджет ограничен"},   # тот же субъект, та же полярность → корроборация
    ]
    assert detect_contradictions(facts) == []


def test_different_subject_no_contradiction():
    facts = [
        {"fact_id": "a", "claim": "Дерево подходит"},
        {"fact_id": "b", "claim": "Кирпич не подходит"},   # разные субъекты
    ]
    assert detect_contradictions(facts) == []


def test_recency_uses_timestamp():
    # a — новее по времени (хоть и первый в списке), b — старее → новое убеждение = a
    facts = [
        {"fact_id": "a", "claim": "Дерево подходит для дома", "t_ingestion_start": "2026-06-02T00:00:00+00:00"},
        {"fact_id": "b", "claim": "Дерево не подходит для дома", "t_ingestion_start": "2026-06-01T00:00:00+00:00"},
    ]
    c = detect_contradictions(facts)
    assert len(c) == 1
    assert c[0].newer_id == "a" and c[0].older_id == "b"


# ── движок (реальный store) ────────────────────────────────────────────────────

def _store(tmp_path):
    from core.memory import SQLiteGraphStore, promote_to_validated
    return SQLiteGraphStore(db_path=str(tmp_path / "contra.db"))


def test_resolve_validated_not_demoted_by_newer_observed(tmp_path):
    # H2/M3 fix: новый low-trust Observed НЕ демотирует старый Validated (trust-aware).
    s = _store(tmp_path)
    s.store_fact({"fact_id": "a", "claim": "Дерево подходит для дома", "source": "s1", "confidence": 0.9})
    s.promote_to_validated("a", by="test")
    s.store_fact({"fact_id": "b", "claim": "Дерево не подходит для дома", "source": "s2", "confidence": 0.4})
    rep = resolve_contradictions(s)
    assert rep.detected == 1 and rep.demoted == 0
    assert s.get_fact("a")["epistemic_state"] == "Validated"      # проверенное знание сохранено
    assert rep.flagged_review == 1                                # новый Observed помечен, не побеждает


def test_resolve_demotes_weaker_validated_loser(tmp_path):
    # Демоушен по-прежнему работает: доверенный Validated-победитель демотирует
    # менее доверенный Validated-проигравший (выбор по доверию, а не по новизне).
    s = _store(tmp_path)
    s.store_fact({"fact_id": "a", "claim": "Дерево подходит для дома", "source": "u1", "confidence": 0.9})
    s.promote_to_validated("a", by="test")
    s.store_fact({"fact_id": "b", "claim": "Дерево не подходит для дома", "source": "domain_seed", "confidence": 0.9})
    s.promote_to_validated("b", by="test")
    rep = resolve_contradictions(s)
    assert rep.detected == 1 and rep.demoted == 1
    assert s.get_fact("a")["epistemic_state"] == "Contradicted"   # слабее (untrusted) → демотирован
    assert s.get_fact("b")["epistemic_state"] == "Validated"      # доверенный победитель цел


def test_resolve_flags_nonvalidated_older(tmp_path):
    s = _store(tmp_path)
    s.store_fact({"fact_id": "a", "claim": "Дерево подходит для дома", "source": "s1", "confidence": 0.9})
    s.store_fact({"fact_id": "b", "claim": "Дерево не подходит для дома", "source": "s2", "confidence": 0.9})
    rep = resolve_contradictions(s)
    assert rep.detected == 1 and rep.demoted == 0 and rep.flagged_review == 1
    assert s.get_fact("a")["epistemic_state"] == "Observed"       # матрица не пускает Observed→Contradicted; не форсим
