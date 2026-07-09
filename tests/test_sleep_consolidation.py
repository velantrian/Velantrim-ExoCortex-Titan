"""
Тесты Sleep Consolidation Loop (core/sleep_consolidation.py, RFC-0082 P0.3).
Проверяют связку corroboration→promotion→contradiction→decay и диспетчер run_consolidation.
"""
from core.sleep_consolidation import is_sleep_consolidation_enabled, run_sleep_consolidation


def _store(tmp_path):
    from core.memory import SQLiteGraphStore, promote_to_validated
    return SQLiteGraphStore(db_path=str(tmp_path / "sleep.db"))


# ── flag ──────────────────────────────────────────────────────────────────────

def test_flag_off_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_SLEEP_CONSOLIDATION", raising=False)
    assert is_sleep_consolidation_enabled() is False


# ── end-to-end ────────────────────────────────────────────────────────────────

def test_sleep_loop_promotes_and_resolves(tmp_path):
    s = _store(tmp_path)
    # доверенный факт → должен промоутнуться (Observed→Supported)
    s.store_fact({"fact_id": "t1", "claim": "A trusted seed axiom about the domain",
                  "source": "domain_seed", "confidence": 0.9})
    # D5/trust-aware: противоречие двух Validated — побеждает БОЛЕЕ ДОВЕРЕННЫЙ источник,
    # проигравший Validated демотируется (демоушен по-прежнему работает, но по доверию, не по новизне).
    s.store_fact({"fact_id": "a", "claim": "Дерево подходит для дома", "source": "u1", "confidence": 0.9})
    s.promote_to_validated("a", by="test")
    s.store_fact({"fact_id": "b", "claim": "Дерево не подходит для дома", "source": "domain_seed", "confidence": 0.9})
    s.promote_to_validated("b", by="test")

    rep = run_sleep_consolidation(s)

    assert rep.facts_examined == 3
    assert rep.corroboration_mode == "lexical"           # embedder не передан
    assert s.get_fact("t1")["epistemic_state"] in ("Hypothesized", "Supported", "Validated")   # промоушен
    assert s.get_fact("a")["epistemic_state"] == "Contradicted"                # проигравший (менее доверенный)
    assert s.get_fact("b")["epistemic_state"] == "Validated"                   # победитель (domain_seed) цел
    assert rep.contradictions["demoted"] == 1
    assert rep.decay["status"] == "skipped_p0"           # честно: decay фактов — P1
    assert rep.errors == 0


def test_sleep_loop_validated_not_demoted_by_newer_observed(tmp_path):
    # H2/M3 fix: новый Observed low-trust НЕ демотирует старый Validated trusted.
    s = _store(tmp_path)
    s.store_fact({"fact_id": "a", "claim": "Дерево подходит для дома", "source": "u1", "confidence": 0.9})
    s.promote_to_validated("a", by="test")
    s.store_fact({"fact_id": "b", "claim": "Дерево не подходит для дома", "source": "u2", "confidence": 0.4})
    first = run_sleep_consolidation(s)
    second = run_sleep_consolidation(s)
    assert first.contradictions["detected"] == 1
    assert first.contradictions["demoted"] == 0           # Validated 'a' НЕ демотируется новым Observed 'b'
    assert second.contradictions["demoted"] == 0          # идемпотентно
    assert s.get_fact("a")["epistemic_state"] == "Validated"   # проверенное знание сохранено


def test_semantic_mode_when_embedder_passed(tmp_path):
    s = _store(tmp_path)
    s.store_fact({"fact_id": "x", "claim": "Some fact here long enough", "source": "s", "confidence": 0.9})
    rep = run_sleep_consolidation(s, embed_fn=lambda claims: [[1.0, 0.0] for _ in claims])
    assert rep.corroboration_mode == "semantic"


# ── dispatch via run_consolidation ──────────────────────────────────────────────

def test_dispatch_routes_to_sleep_when_flag_on(tmp_path, monkeypatch):
    monkeypatch.setenv("ENABLE_SLEEP_CONSOLIDATION", "true")
    from core.consolidation_engine import run_consolidation
    s = _store(tmp_path)
    s.store_fact({"fact_id": "x", "claim": "Some fact here long enough", "source": "s", "confidence": 0.9})
    d = run_consolidation(s).to_dict()
    # форма SleepReport (а не наивного ConsolidationReport)
    assert "facts_examined" in d and "promotion" in d and "contradictions" in d


def test_dispatch_naive_when_all_flags_off(tmp_path, monkeypatch):
    for f in ("ENABLE_SLEEP_CONSOLIDATION", "ENABLE_GRADUATED_PROMOTION"):
        monkeypatch.delenv(f, raising=False)
    from core.consolidation_engine import run_consolidation
    s = _store(tmp_path)
    s.store_fact({"fact_id": "x", "claim": "Достаточно длинный факт", "source": "s", "confidence": 0.9})
    d = run_consolidation(s).to_dict()
    assert "promoted_validated" in d            # наивный ConsolidationReport
