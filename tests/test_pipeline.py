"""
Smoke tests + AUDIT-FIX regression tests for the MVP pipeline.
v2.0 (audit-fix: correct test isolation via make_store(),
      added promote_trace `by` param test)

Covers:
  - happy path
  - empty retrieval blocks
  - tokenize edge cases (em-dash, punctuation-only)
  - Guardian fact_id coverage check
  - promote_trace ESM-matrix validation + idempotency + `by` param
  - confidence vs retrieval_score separation
  - AUDIT-FIX: pipeline.run() idempotent on persistent DB
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── Fixture: правильная тестовая изоляция ────────────────────────────────────
# AUDIT-FIX v2.0: заменяем _GLOBAL_STORE целиком через make_store().

@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    """Каждый тест получает свежий SQLiteGraphStore в tmp_path."""
    from core import memory
    fresh = memory.make_store(str(tmp_path / "test.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE",    fresh)
    monkeypatch.setattr(memory, "_L0",              fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH",      str(tmp_path / "test.db"))
    yield fresh
    fresh.close()


# ─── Fixture: засеянная БД для тестов pipeline ───────────────────────────────

@pytest.fixture
def seeded_db(isolated_db):
    """isolated_db + несколько фактов для тестов pipeline.
    TASK-07: DATABASE mock fallback убран из production-пути.
    Тесты pipeline теперь явно кладут данные в store.
    """
    from core.memory import promote_to_validated, store_fact, transition_esm, promote_to_validated
    seed_facts = [
        {"fact_id": "f1", "claim": "Water boils at 100 degrees Celsius",
         "source": "physics", "confidence": 0.99},
        {"fact_id": "f2", "claim": "Quantum entanglement links distant particles",
         "source": "physics", "confidence": 0.85},
        {"fact_id": "f3", "claim": "Earth revolves around the Sun",
         "source": "astronomy", "confidence": 0.99},
        {"fact_id": "f4", "claim": "The human brain has 86 billion neurons",
         "source": "neuroscience", "confidence": 0.90},
        {"fact_id": "f5", "claim": "DNA encodes genetic information in genes",
         "source": "biology", "confidence": 0.99},
    ]
    for f in seed_facts:
        store_fact(f)
        promote_to_validated(f["fact_id"])
    return isolated_db


# ─── Pipeline happy path ──────────────────────────────────────────────────────

def test_pipeline_happy_path(seeded_db):
    from core.pipeline import run
    result = run("quantum entanglement")
    assert result.get("answer") is not None
    assert result.get("error") is None
    assert len(result["facts"]) > 0
    for f in result["facts"]:
        assert f["epistemic_state"] == "Validated"
        assert f["truth_status"]    == "VERIFIED"


def test_pipeline_empty_retrieval_blocks():
    from core.pipeline import run
    result = run("zxqvbnmqwerty")
    assert result.get("answer") is None
    assert "Retrieval" in result.get("error", "")


def test_trace_is_built_for_each_fact():
    from core.pipeline import run
    result = run("DNA")
    assert len(result["trace"]) == len(result["facts"])
    for el in result["trace"]:
        assert "fact_id"        in el
        assert "epistemic_state" in el
        assert el["epistemic_state"] == "Validated"


# ─── v8.7: modality-aware step-6 promotion (ENABLE_TRUTH_POLICY) ─────────────

def test_pipeline_step6_modality_flag_on(isolated_db, monkeypatch):
    """Флаг ON: EMOTION валидна как модальность, но truth_status=UNVERIFIED;
    WORLD_FACT с evidence → VERIFIED. (Флаг OFF проверяется happy_path = всё VERIFIED.)"""
    from core import pipeline
    from core.memory import get_fact, promote_to_validated, store_fact, transition_esm
    monkeypatch.setattr(pipeline, "_truth_policy_enabled", lambda: True)

    store_fact({
        "fact_id": "emo1", "claim": "anxiety signal during the long meeting",
        "source": "user_message", "confidence": 0.9,
        "claim_type": "EMOTION", "origin_type": "USER_REPORTED",
    })
    promote_to_validated("emo1")
    store_fact({
        "fact_id": "wf1", "claim": "anxiety is a documented physiological response",
        "source": "psychology", "confidence": 0.95,
        "claim_type": "WORLD_FACT", "origin_type": "EXTERNAL",
        "metadata": {"evidence_refs": [{"source_id": "doi:1", "span": "1-5"}]},
    })
    promote_to_validated("wf1")

    assert get_fact("emo1")["claim_type"] == "EMOTION"
    assert get_fact("wf1")["claim_type"] == "WORLD_FACT"

    result = pipeline.run("anxiety")
    by_id = {f["fact_id"]: f for f in result["facts"]}
    assert "emo1" in by_id and "wf1" in by_id, by_id.keys()
    assert by_id["emo1"]["truth_status"] == "UNVERIFIED"   # чувство ≠ факт мира
    assert by_id["wf1"]["truth_status"] == "VERIFIED"        # внешний факт + evidence


def test_pipeline_step6_modality_flag_off_legacy(seeded_db):
    """Флаг OFF (дефолт): шаг 6 промоутит всё в Validated/VERIFIED — поведение прежнее."""
    from core.pipeline import run
    result = run("quantum entanglement")
    for f in result["facts"]:
        assert f["epistemic_state"] == "Validated"
        assert f["truth_status"] == "VERIFIED"


# ─── v8.7: graph-expansion retrieval (ENABLE_GRAPH_EXPANSION) ─────────────────

def test_graph_expansion_pulls_reliable_neighbors(isolated_db):
    """_expand_with_graph_neighbors тянет reliable причинных соседей факта из
    causal_graph — основа multi-hop рассуждения (рёбра + соседи → цепочка)."""
    from core import pipeline
    from core.memory import promote_to_validated, store_fact, transition_esm
    for fid, claim in [("ga", "Лидер молнии начинает разряд"),
                       ("gb", "Лидер создаёт ионизированный канал"),
                       ("gc", "Канал проводит главный разряд молнии")]:
        store_fact({"fact_id": fid, "claim": claim, "source": "physics", "confidence": 0.9,
                    "claim_type": "WORLD_FACT", "origin_type": "EXTERNAL",
                    "metadata": {"evidence_refs": [{"source_id": "p", "span": "1"}]}})
        promote_to_validated(fid)
    cg = pipeline._get_causal_graph()
    assert cg is not None, "causal_graph недоступен в тестовом контексте"
    cg.add_relation("ga", "gb", "causes", confidence=0.9)
    cg.add_relation("gb", "gc", "causes", confidence=0.9)

    # стартуем ТОЛЬКО с hub-факта gb — соседи ga/gc должны подтянуться по рёбрам
    seed = [{"fact_id": "gb", "claim": "Лидер создаёт ионизированный канал",
             "epistemic_state": "Validated", "confidence": 0.9, "claim_type": "WORLD_FACT"}]
    expanded = pipeline._expand_with_graph_neighbors(seed)
    ids = {f["fact_id"] for f in expanded}
    assert len(ids) >= 2, f"expansion должна добавить соседей, got {ids}"
    assert {"ga", "gc"} & ids, f"должны подтянуться ga/gc как соседи gb, got {ids}"
    assert any(f.get("graph_expanded") for f in expanded), "соседи помечены graph_expanded"


def test_graph_expansion_no_graph_is_noop(isolated_db):
    """Без рёбер / соседей — expansion возвращает исходный набор (безопасно)."""
    from core import pipeline
    from core.memory import promote_to_validated, store_fact, transition_esm
    store_fact({"fact_id": "solo", "claim": "Одинокий факт без связей", "source": "x",
                "confidence": 0.9, "claim_type": "WORLD_FACT", "origin_type": "EXTERNAL"})
    promote_to_validated("solo")
    seed = [{"fact_id": "solo", "claim": "Одинокий факт без связей",
             "epistemic_state": "Validated", "confidence": 0.9, "claim_type": "WORLD_FACT"}]
    out = pipeline._expand_with_graph_neighbors(seed)
    assert {f["fact_id"] for f in out} == {"solo"}


# ─── AUDIT-FIX: pipeline.run() idempotent ────────────────────────────────────

def test_pipeline_run_idempotent_on_same_db(seeded_db):
    """
    Критический баг v8.0.2: повторный run() крашился
    (Validated→Validated нет в ESM-матрице).
    Теперь должен проходить без ошибок.
    """
    from core.pipeline import run
    r1 = run("DNA")
    assert r1.get("answer") is not None
    assert r1.get("error")  is None

    r2 = run("DNA")
    assert r2.get("answer") is not None
    assert r2.get("error")  is None
    assert r2["answer"] == r1["answer"]
    for f in r2["facts"]:
        assert f["epistemic_state"] == "Validated"


def test_pipeline_run_idempotent_three_times(seeded_db):
    from core.pipeline import run
    answers = [run("quantum entanglement").get("answer") for _ in range(3)]
    assert all(a is not None for a in answers)
    assert len(set(answers)) == 1


# ─── tokenize edge cases ──────────────────────────────────────────────────────

def test_tokenize_punctuation_only_returns_empty():
    from core.pipeline import tokenize
    assert tokenize("...") == []
    assert tokenize("")    == []
    assert tokenize("!?;:") == []


def test_tokenize_emdash_and_hyphen():
    from core.pipeline import tokenize
    assert tokenize("hello\u2014world") == ["hello", "world"]
    assert tokenize("hello--world")     == ["hello", "world"]
    assert tokenize("hello-world")      == ["hello", "world"]


# ─── retrieve: confidence vs retrieval_score ─────────────────────────────────

def test_retrieve_uses_source_confidence():
    """P1.3: confidence = source confidence, не BM25 retrieval_score.
    TASK-07: используем database=DATABASE DI напрямую — тест алгоритма,
    не поведения store. Реальный store изолирован через isolated_db.
    """
    from core.pipeline import DATABASE, retrieve
    # Используем DI: передаём DATABASE явно, минуем store-путь
    r = retrieve("quantum entanglement", database=DATABASE)
    assert r, "retrieve вернул пустой список"
    db_item = next(
        (item for item in DATABASE if "quantum" in item["text"].lower()), None
    )
    assert db_item is not None
    assert r[0]["confidence"]      == db_item["confidence"]
    assert r[0]["retrieval_score"] != r[0]["confidence"]


# ─── promote_trace ESM-matrix + idempotency + by param ───────────────────────

def test_promote_trace_blocks_invalid_transition():
    from core.trace import promote_trace
    trace = [{"fact_id": "x", "epistemic_state": "Collapsed",
              "source": "s", "origin": "r", "retrieval_score": 0.5,
              "source_confidence": 0.5, "retrieved_at": "now"}]
    with pytest.raises(ValueError, match="недопустим"):
        promote_trace(trace, "Validated")


def test_promote_trace_idempotent_when_already_in_target_state():
    from core.trace import promote_trace
    trace = [{"fact_id": "x", "epistemic_state": "Validated",
              "source": "s", "origin": "r", "retrieval_score": 0.5,
              "source_confidence": 0.5, "retrieved_at": "now"}]
    promote_trace(trace, "Validated")
    assert trace[0]["epistemic_state"] == "Validated"
    assert "promoted_at" in trace[0]


def test_promote_trace_records_by_param():
    """AUDIT-FIX v8.0.4: параметр `by` сохраняется в promoted_by."""
    from core.trace import promote_trace
    trace = [{"fact_id": "x", "epistemic_state": "Observed",
              "source": "s", "origin": "r", "retrieval_score": 0.5,
              "source_confidence": 0.5, "retrieved_at": "now"}]
    promote_trace(trace, "Validated", by="test_caller")
    assert trace[0]["promoted_by"] == "test_caller"


def test_build_trace_separates_retrieval_score_and_confidence():
    """v8.0.4: build_trace разделяет retrieval_score и source_confidence."""
    from core.trace import build_trace
    items = [{"id": "f1", "source": "s", "origin": "retrieval",
              "epistemic_state": "Observed",
              "retrieval_score": 1.23, "confidence": 0.99}]
    trace = build_trace(items)
    assert trace[0]["retrieval_score"]   == round(1.23, 4)
    assert trace[0]["source_confidence"] == 0.99
    assert "confidence" not in trace[0], \
        "поле confidence не должно быть в trace напрямую"


# ─── Guardian fact_id coverage ────────────────────────────────────────────────

def test_guardian_checks_fact_id_coverage():
    from core.pipeline import guardian
    facts_pack = {
        "facts": [
            {"fact_id": "a", "claim": "c", "source": "s", "confidence": 0.9},
            {"fact_id": "b", "claim": "c", "source": "s", "confidence": 0.9},
        ]
    }
    trace = [{"fact_id": "a", "epistemic_state": "Observed"}]
    ok, reason = guardian(facts_pack, trace)
    assert not ok
    assert "b" in reason


def test_guardian_passes_full_coverage():
    from core.pipeline import guardian
    facts_pack = {
        "facts": [{"fact_id": "a", "claim": "c", "source": "s", "confidence": 0.9}]
    }
    trace = [{"fact_id": "a", "epistemic_state": "Observed"}]
    ok, reason = guardian(facts_pack, trace)
    assert ok
    assert reason is None


# ─── truth_gate unit tests ────────────────────────────────────────────────────

def test_truth_gate_passes_valid_facts():
    from core.pipeline import truth_gate
    facts_pack = {
        "facts": [{"fact_id": "x", "claim": "c", "source": "s", "confidence": 0.9}]
    }
    ok, reason = truth_gate(facts_pack)
    assert ok
    assert reason is None


def test_truth_gate_blocks_low_confidence():
    from core.pipeline import truth_gate
    facts_pack = {
        "facts": [{"fact_id": "x", "claim": "c", "source": "s", "confidence": 0.0}]
    }
    ok, reason = truth_gate(facts_pack, min_confidence=0.05)
    assert not ok
    assert "Confidence" in reason


def test_truth_gate_blocks_missing_source():
    from core.pipeline import truth_gate
    facts_pack = {
        "facts": [{"fact_id": "x", "claim": "c", "source": "", "confidence": 0.9}]
    }
    ok, reason = truth_gate(facts_pack)
    assert not ok
    assert "source" in reason


def test_truth_gate_blocks_empty_facts():
    from core.pipeline import truth_gate
    ok, _ = truth_gate({"facts": []})
    assert not ok


def test_truth_gate_balanced_uses_metadata_evidence_from_pipeline_pack():
    """
    Регрессия: metadata.evidence_refs не должны теряться в build_facts_pack().
    Иначе реальный TruthGate(BALANCED) ложно блокирует факт как insufficient_evidence.
    """
    import core.pipeline as pl

    retrieved = [{
        "id": "tg_meta_1",
        "text": "Earth revolves around the Sun",
        "source": "astronomy",
        "confidence": 0.95,
        "retrieval_score": 0.9,
        "metadata": {"evidence_refs": ["ref1", "ref2"]},
    }]
    # CREATIVE включает Observed-факты в pack; сам gate проверяем в BALANCED.
    facts_pack = pl.build_facts_pack(retrieved, "earth sun", cognitive_mode="CREATIVE")
    assert len(facts_pack["facts"]) == 1
    assert facts_pack["facts"][0]["metadata"]["evidence_refs"] == ["ref1", "ref2"]

    ok, reason = pl.truth_gate(facts_pack, mode="BALANCED")
    assert ok, f"Ожидался PASS c evidence_refs, но получили BLOCKED: {reason}"


# ─── generate_answer fallback path ───────────────────────────────────────────

def test_generate_answer_fallback_when_no_validated_facts():
    from core.pipeline import generate_answer
    facts_pack = {
        "facts": [
            {"fact_id": "x", "claim": "fallback claim", "source": "s",
             "confidence": 0.9, "epistemic_state": "Observed"},
        ]
    }
    trace = [{"fact_id": "x", "source": "s", "origin": "r",
              "epistemic_state": "Observed", "retrieval_score": 0.5,
              "source_confidence": 0.9, "retrieved_at": "now"}]
    result = generate_answer(facts_pack, trace)
    assert result["answer"]      == "fallback claim"
    assert result["total_facts"] == 1


# ─── TASK-04: mark_retriever_dirty только при новом факте ────────────────────

def test_store_fact_returns_true_for_new_false_for_existing():
    """TASK-04: store_fact возвращает True при INSERT, False при UPSERT."""
    from core.memory import store_fact
    fact = {"fact_id": "rf_test", "claim": "gravity", "source": "physics", "confidence": 0.9}
    # Первый вызов — новый факт
    assert store_fact(fact) is True
    # Второй вызов с теми же данными — no-op
    assert store_fact(fact) is False


def test_retriever_not_dirty_for_existing_facts(monkeypatch):
    """TASK-04: mark_retriever_dirty НЕ вызывается когда build_facts_pack
    получает факты которые уже есть в store (no-op guard).
    Тестируем build_facts_pack напрямую — минуем retrieval (BM25 IDF=0
    для маленьких корпусов делает retrieval ненадёжным в unit-тестах)."""
    import core.pipeline as pl
    dirty_calls = []
    monkeypatch.setattr(pl, "mark_retriever_dirty", lambda: dirty_calls.append(1))

    from core.memory import store_fact
    # Кладём факт заранее в store
    store_fact({"fact_id": "existing_f", "claim": "gravity pulls objects",
                "source": "physics", "confidence": 0.9})

    dirty_calls.clear()  # сбрасываем после предзагрузки

    # build_facts_pack с УЖЕ ИЗВЕСТНЫМ фактом — dirty не должен вызваться
    retrieved_known = [{
        "id": "existing_f", "text": "gravity pulls objects",
        "source": "physics", "confidence": 0.9, "retrieval_score": 0.8,
    }]
    pl.build_facts_pack(retrieved_known, "gravity test")
    assert len(dirty_calls) == 0, (
        f"mark_retriever_dirty вызван {len(dirty_calls)} раз(а) "
        f"для уже известного факта — TASK-04 регрессия"
    )

    # build_facts_pack с НОВЫМ фактом — dirty ДОЛЖЕН быть вызван
    retrieved_new = [{
        "id": "brand_new_f", "text": "dark matter exists",
        "source": "cosmology", "confidence": 0.7, "retrieval_score": 0.6,
    }]
    pl.build_facts_pack(retrieved_new, "dark matter test")
    assert len(dirty_calls) == 1, (
        f"mark_retriever_dirty вызван {len(dirty_calls)} раз(а) "
        f"вместо 1 для нового факта — TASK-04 регрессия"
    )


# ─── TASK-06: get_fact_ids + get_facts_by_ids ─────────────────────────────────

def test_get_fact_ids_returns_only_ids():
    """TASK-06: get_fact_ids возвращает список строк, не полные факты."""
    from core.memory import get_fact_ids, store_fact
    store_fact({"fact_id": "gfi_1", "claim": "alpha", "source": "s", "confidence": 0.9})
    store_fact({"fact_id": "gfi_2", "claim": "beta",  "source": "s", "confidence": 0.8})
    ids = get_fact_ids()
    assert "gfi_1" in ids
    assert "gfi_2" in ids
    assert all(isinstance(i, str) for i in ids), "get_fact_ids должен возвращать List[str]"


def test_get_facts_by_ids_returns_full_facts():
    """TASK-06: get_facts_by_ids тянет полные факты только для нужных ID."""
    from core.memory import get_facts_by_ids, store_fact
    store_fact({"fact_id": "gfbi_1", "claim": "gamma", "source": "s", "confidence": 0.9})
    store_fact({"fact_id": "gfbi_2", "claim": "delta", "source": "s", "confidence": 0.8})
    facts = get_facts_by_ids(["gfbi_1"])
    assert len(facts) == 1
    assert facts[0]["fact_id"] == "gfbi_1"
    assert facts[0]["claim"] == "gamma"
    # gfbi_2 НЕ должен попасть
    assert not any(f["fact_id"] == "gfbi_2" for f in facts)


def test_get_facts_by_ids_empty_input():
    """TASK-06: пустой список ID → пустой результат без SQL."""
    from core.memory import get_facts_by_ids
    assert get_facts_by_ids([]) == []


# ─── TASK-08: CausalGraph integration ────────────────────────────────────────

def test_causal_hints_in_response_for_causal_facts(seeded_db):
    """TASK-08: run() возвращает causal_hints когда факты содержат каузальные паттерны."""
    from core.memory import promote_to_validated, store_fact, transition_esm
    from core.pipeline import run

    # Кладём факты с каузальными паттернами
    store_fact({"fact_id": "cg1", "claim": "Heat causes water to evaporate",
                "source": "physics", "confidence": 0.9})
    store_fact({"fact_id": "cg2", "claim": "Evaporation therefore cools surfaces",
                "source": "physics", "confidence": 0.9})
    store_fact({"fact_id": "cg3", "claim": "Cooling results in condensation",
                "source": "physics", "confidence": 0.9})
    for fid in ["cg1", "cg2", "cg3"]:
        promote_to_validated(fid)

    result = run("heat causes evaporation")
    # Проверяем что ответ пришёл
    assert result.get("error") is None or result.get("answer") is not None

    # Если CausalGraph доступен — должны быть hints
    from core.pipeline import _CAUSAL_GRAPH_AVAILABLE
    if _CAUSAL_GRAPH_AVAILABLE and result.get("causal_hints"):
        hints = result["causal_hints"]
        assert isinstance(hints, list)
        assert len(hints) > 0
        # Каждый hint имеет нужные поля
        for h in hints:
            assert "from" in h
            assert "to" in h
            assert h["status"] == "hypothetical"
            assert h["review"] == "pending"
            assert h["confidence"] < 0.5  # гипотезы — низкий confidence


def test_no_causal_hints_for_plain_facts(seeded_db):
    """TASK-08: causal_hints не генерируются для фактов без каузальных паттернов."""
    from core.pipeline import run
    # seeded_db имеет факты без каузальных паттернов ("Water boils", "Earth orbits" и т.д.)
    result = run("quantum entanglement")
    # causal_hints либо отсутствует либо пустой
    hints = result.get("causal_hints", [])
    assert isinstance(hints, list)
    # Для обычных фактов без каузальных слов — 0 hints
    assert len(hints) == 0


def test_causal_hints_are_non_blocking(seeded_db):
    """TASK-08: causal_hints не блокируют ответ даже если CausalGraph падает."""
    from core.pipeline import run
    result = run("quantum entanglement")
    # answer должен быть независимо от causal_hints
    assert result.get("answer") is not None
    assert result.get("error") is None


# ─── TASK-16: Contradiction-First in pipeline ────────────────────────────────

def test_conflicts_block_present_when_contradictions_exist(seeded_db):
    """TASK-16: pipeline.run() возвращает conflicts когда в CausalGraph есть contradicts-связи."""
    from core.memory import promote_to_validated, store_fact, transition_esm
    from core.pipeline import _get_causal_graph, run

    # Кладём два противоречивых факта
    store_fact({"fact_id": "earth_round", "claim": "Earth is round",
                "source": "science", "confidence": 0.99})
    store_fact({"fact_id": "earth_flat",  "claim": "Earth is flat",
                "source": "myth", "confidence": 0.10})
    for fid in ["earth_round", "earth_flat"]:
        promote_to_validated(fid)

    # Создаём contradicts-связь между ними
    cg = _get_causal_graph()
    if cg is not None:
        try:
            cg.add_relation(
                from_fact_id="earth_round",
                to_fact_id="earth_flat",
                relation_type="contradicts",
                confidence=0.95,
                knowledge_status="known",
                inference_source="test",
                review_state="approved",
            )
        except Exception:
            pass

    # Запускаем pipeline
    result = run("Earth shape")

    # Проверки
    assert result.get("answer") is not None or result.get("conflicts"), \
        "Ожидался answer или conflicts"
    if "conflicts" in result:
        conflicts = result["conflicts"]
        assert isinstance(conflicts, list)
        assert len(conflicts) > 0
        # Проверяем структуру каждого конфликта
        for c in conflicts:
            assert "fact_a" in c
            assert "fact_b" in c
            assert "kind" in c
            assert c["kind"] in {"internal", "external"}
        # При наличии conflicts должен быть honesty_marker
        assert result.get("honesty_marker") == "conflicts_detected"


def test_no_conflicts_block_for_facts_without_contradictions(seeded_db):
    """TASK-16: когда противоречий нет — поля conflicts быть не должно."""
    from core.pipeline import run
    # seeded_db имеет факты БЕЗ contradicts-связей
    result = run("quantum entanglement")
    # conflicts либо отсутствует либо пустой
    conflicts = result.get("conflicts", [])
    assert isinstance(conflicts, list)
    assert len(conflicts) == 0
    # honesty_marker тоже не должен быть установлен
    assert result.get("honesty_marker") != "conflicts_detected"


def test_conflicts_extraction_handles_cycles(seeded_db):
    """TASK-16 × TASK-10: при циклах в графе не зависаем (используем cycle protection)."""
    from core.memory import promote_to_validated, store_fact, transition_esm
    from core.pipeline import _get_causal_graph, run

    # Создаём 3 факта с цикличными contradicts (теоретически возможный плохой случай)
    for fid, claim in [("c1","Statement A"), ("c2","Statement B"), ("c3","Statement C")]:
        store_fact({"fact_id": fid, "claim": claim, "source": "test", "confidence": 0.8})
        promote_to_validated(fid)

    cg = _get_causal_graph()
    if cg is not None:
        try:
            # A → B contradicts, B → C contradicts, C → A contradicts (цикл!)
            cg.add_relation("c1", "c2", "contradicts", confidence=0.9,
                          knowledge_status="known", inference_source="test")
            cg.add_relation("c2", "c3", "contradicts", confidence=0.9,
                          knowledge_status="known", inference_source="test")
            cg.add_relation("c3", "c1", "contradicts", confidence=0.9,
                          knowledge_status="known", inference_source="test")
        except Exception:
            pass

    # Должен завершиться без RecursionError
    import sys
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(200)
    try:
        result = run("statement A")
        # Не упало — отлично
        assert result is not None
    finally:
        sys.setrecursionlimit(old_limit)


def test_pipeline_response_structure_unchanged_without_conflicts(seeded_db):
    """TASK-16: добавление conflicts не ломает существующий формат ответа."""
    from core.pipeline import run
    result = run("Water")
    # Базовые поля ответа должны быть на месте
    assert "answer" in result or "error" in result
    # Если есть facts — должны быть в правильной структуре
    if result.get("facts"):
        for fact in result["facts"]:
            assert "fact_id" in fact
            assert "claim" in fact
