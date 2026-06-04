"""
tests/test_claim_type.py — Acceptance tests for v8.7 P0: claim_type + origin_type modality.

10 criteria from the spec (adapted for Velantrim master + Russian-first):

1.  Emotion is stored as EMOTION, not WORLD_FACT.
2.  Opinion is stored as OPINION, not WORLD_FACT.
3.  User experience is stored as USER_EXPERIENCE.
4.  LLM output is not auto-promoted to WORLD_FACT.
5.  External-sourced claim may become WORLD_FACT candidate.
6.  significance_score (salience) does not affect truth promotion  [N/A in V8.7 — salience is separate, not stored; verified via absence of coupling].
7.  confidence does not act as importance (separate fields).
8.  TruthGate (modality_guard) allows subjective memory but blocks modality escalation.
9.  Migration preserves old records with UNKNOWN defaults.
10. Retrieval labels subjective memory correctly in generate_answer.

Plus: classifier smoke tests for Russian patterns.
"""
from __future__ import annotations

import pytest

# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture()
def store(tmp_path):
    from core.memory import SQLiteGraphStore
    return SQLiteGraphStore(str(tmp_path / "test_claim_type.db"))


# ─── Test 1: Emotion stored as EMOTION ───────────────────────────────────────

def test_emotion_classified_as_emotion(store):
    """Claim 'Мне было тревожно' → claim_type=EMOTION, not WORLD_FACT."""
    fact = {
        "fact_id": "emo_001",
        "claim":   "Мне было тревожно при разговоре с ним",
        "source":  "user_message",
        "confidence": 0.9,
    }
    store.store_fact(fact)
    saved = store.get_fact("emo_001")
    assert saved is not None
    assert saved["claim_type"] == "EMOTION", (
        f"Expected EMOTION, got {saved['claim_type']!r}. "
        "Emotional claims must not become WORLD_FACT."
    )
    assert saved["claim_type"] != "WORLD_FACT"


# ─── Test 2: Opinion stored as OPINION ───────────────────────────────────────

def test_opinion_classified_as_opinion(store):
    """'По моему мнению, он поступил неправильно' → OPINION."""
    fact = {
        "fact_id": "opin_001",
        "claim":   "По моему мнению, он поступил неправильно",
        "source":  "user_message",
        "confidence": 0.8,
    }
    store.store_fact(fact)
    saved = store.get_fact("opin_001")
    assert saved["claim_type"] == "OPINION"
    assert saved["claim_type"] != "WORLD_FACT"


# ─── Test 3: User experience stored as USER_EXPERIENCE ───────────────────────

def test_user_experience_classified(store):
    """'Я помню, как встретил его в парке' → USER_EXPERIENCE."""
    fact = {
        "fact_id": "exp_001",
        "claim":   "Я помню, как встретил его в парке год назад",
        "source":  "user_message",
        "confidence": 0.85,
    }
    store.store_fact(fact)
    saved = store.get_fact("exp_001")
    assert saved["claim_type"] == "USER_EXPERIENCE"


# ─── Test 4: LLM output not auto-promoted to WORLD_FACT ──────────────────────

def test_llm_output_origin_type(store):
    """Факт с source=llm/gpt → origin_type=LLM_OUTPUT, не является WORLD_FACT без доказательств."""
    fact = {
        "fact_id": "llm_001",
        "claim":   "Квантовая запутанность — это явление в физике",
        "source":  "llm_output",
        "confidence": 0.8,
    }
    store.store_fact(fact)
    saved = store.get_fact("llm_001")
    assert saved["origin_type"] == "LLM_OUTPUT", (
        f"Expected LLM_OUTPUT, got {saved['origin_type']!r}"
    )


def test_llm_world_fact_blocked_without_evidence():
    """modality_guard: WORLD_FACT + LLM_OUTPUT без evidence_refs → заблокировать."""
    from core.truth_policy import modality_guard
    fact = {
        "claim_type":  "WORLD_FACT",
        "origin_type": "LLM_OUTPUT",
        "confidence":  0.9,
        "source":      "gpt-4o",
        "metadata":    {},  # нет evidence_refs
    }
    ok, reason = modality_guard(fact, "Validated")
    assert not ok, "LLM_OUTPUT без evidence_refs не должен допускаться как WORLD_FACT Validated"
    assert "LLM_OUTPUT" in reason or "evidence" in reason.lower()


# ─── Test 5: External-sourced claim → WORLD_FACT candidate ───────────────────

def test_external_source_world_fact(store):
    """Факт из physics-источника → claim_type=WORLD_FACT, origin_type=EXTERNAL."""
    fact = {
        "fact_id": "wf_001",
        "claim":   "Скорость света в вакууме: 299 792 458 м/с",
        "source":  "physics.optics",
        "confidence": 0.99,
    }
    store.store_fact(fact)
    saved = store.get_fact("wf_001")
    assert saved["claim_type"] == "WORLD_FACT", (
        f"Физический факт должен быть WORLD_FACT, получено: {saved['claim_type']!r}"
    )
    assert saved["origin_type"] == "EXTERNAL"


# ─── Test 6: salience/confidence independence ────────────────────────────────

def test_confidence_not_importance(store):
    """confidence и salience — отдельные оси. Высокая salience не делает факт более верифицированным."""
    # Факт с высоким confidence, но субъективная модальность
    fact = {
        "fact_id": "conf_001",
        "claim":   "Мне очень страшно находиться рядом с ним",
        "source":  "user_message",
        "confidence": 0.95,  # высокая уверенность в эмоции
        "metadata": {"salience": 1.0},  # высокая значимость
    }
    store.store_fact(fact)
    saved = store.get_fact("conf_001")
    # Несмотря на высокий confidence и salience — остаётся EMOTION, не WORLD_FACT
    assert saved["claim_type"] == "EMOTION"
    assert saved["claim_type"] != "WORLD_FACT"


# ─── Test 7: confidence separate from modality in fact dict ──────────────────

def test_fields_are_separate(store):
    """claim_type, origin_type, confidence — все три поля присутствуют и независимы."""
    fact = {
        "fact_id": "sep_001",
        "claim":   "Я хочу выучить Python",
        "source":  "user",
        "confidence": 0.9,
    }
    store.store_fact(fact)
    saved = store.get_fact("sep_001")
    assert "claim_type" in saved, "claim_type должен быть в сохранённом факте"
    assert "origin_type" in saved, "origin_type должен быть в сохранённом факте"
    assert "confidence" in saved, "confidence должен быть в сохранённом факте"
    # Все три — разные значения
    assert saved["claim_type"] != saved["origin_type"]  # GOAL != USER_REPORTED


# ─── Test 8: TruthGate — subjective allowed, escalation blocked ──────────────

def test_modality_guard_emotion_validated_allowed():
    """EMOTION → VALIDATED (как эмоция) — разрешено."""
    from core.truth_policy import modality_guard
    fact = {
        "claim_type":  "EMOTION",
        "origin_type": "USER_REPORTED",
        "confidence":  0.9,
        "source":      "user",
        "metadata":    {},
    }
    ok, reason = modality_guard(fact, "Validated")
    assert ok, f"EMOTION→Validated должен быть разрешён, получено: {reason}"


def test_modality_guard_emotion_immutable_blocked():
    """EMOTION → ImmutableCore — запрещено. Эмоция не может стать неизменяемым ядром знания."""
    from core.truth_policy import modality_guard
    fact = {
        "claim_type":  "EMOTION",
        "origin_type": "USER_REPORTED",
        "confidence":  1.0,
        "source":      "user",
        "metadata":    {},
    }
    ok, reason = modality_guard(fact, "ImmutableCore")
    assert not ok, "EMOTION не должна становиться ImmutableCore"
    assert "ImmutableCore" in reason or "субъективн" in reason.lower()


def test_modality_guard_opinion_immutable_blocked():
    """OPINION → ImmutableCore — запрещено."""
    from core.truth_policy import modality_guard
    fact = {"claim_type": "OPINION", "origin_type": "USER_REPORTED",
            "confidence": 0.95, "source": "user", "metadata": {}}
    ok, _ = modality_guard(fact, "ImmutableCore")
    assert not ok


def test_modality_guard_world_fact_validated_allowed():
    """WORLD_FACT с evidence_refs → Validated — разрешено."""
    from core.truth_policy import modality_guard
    fact = {
        "claim_type":  "WORLD_FACT",
        "origin_type": "EXTERNAL",
        "confidence":  0.99,
        "source":      "physics.textbook",
        "metadata":    {"evidence_refs": [{"source_id": "ref_001"}]},
    }
    ok, reason = modality_guard(fact, "Validated")
    assert ok, f"WORLD_FACT с evidence должен быть разрешён: {reason}"


# ─── Test 9: Migration — old records get UNKNOWN defaults ────────────────────

def test_migration_old_records_get_unknown_defaults(tmp_path):
    """Старые БД без claim_type/origin_type получают DEFAULT='UNKNOWN' при открытии."""
    import sqlite3

    db_path = str(tmp_path / "legacy.db")
    # Создаём старую БД без новых колонок
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE facts (
            fact_id TEXT PRIMARY KEY,
            claim TEXT NOT NULL,
            source TEXT NOT NULL,
            confidence REAL DEFAULT 0.5,
            epistemic_state TEXT DEFAULT 'Observed',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            history TEXT DEFAULT '[]'
        )
    """)
    now = "2026-01-01T00:00:00+00:00"
    conn.execute(
        "INSERT INTO facts (fact_id, claim, source, confidence, epistemic_state, "
        "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("legacy_001", "Старый факт без типа", "old_source", 0.8, "Validated", now, now),
    )
    conn.commit()
    conn.close()

    # Открываем через новый SQLiteGraphStore — должна произойти inline-migration
    from core.memory import SQLiteGraphStore
    store = SQLiteGraphStore(db_path)
    fact = store.get_fact("legacy_001")

    assert fact is not None, "Старый факт должен быть доступен после миграции"
    assert fact.get("claim_type", "UNKNOWN") == "UNKNOWN", (
        f"Старые записи должны получить claim_type='UNKNOWN', получено: {fact.get('claim_type')!r}"
    )
    assert fact.get("origin_type", "UNKNOWN") == "UNKNOWN"


# ─── Test 10: Retrieval labeling — subjective memory correctly labeled ────────

def test_retrieval_labeling_emotion():
    """generate_answer маркирует EMOTION-факты с честным префиксом."""
    from core.pipeline import _label_claim_for_answer
    fact = {
        "claim":      "Мне было тревожно",
        "claim_type": "EMOTION",
        "source":     "user",
        "confidence": 0.9,
        "epistemic_state": "Validated",
    }
    labeled = _label_claim_for_answer(fact)
    assert "тревожно" in labeled, "Исходный текст должен быть сохранён"
    assert "чувств" in labeled.lower() or "EMOTION" in labeled or "сообщали" in labeled.lower(), (
        f"EMOTION-факт должен быть помечен. Получено: {labeled!r}"
    )


def test_retrieval_labeling_world_fact_no_prefix():
    """WORLD_FACT не маркируется — факты мира отдаются без префикса."""
    from core.pipeline import _label_claim_for_answer
    fact = {
        "claim":      "Скорость света: 299792458 м/с",
        "claim_type": "WORLD_FACT",
        "source":     "physics",
        "confidence": 0.99,
        "epistemic_state": "Validated",
    }
    labeled = _label_claim_for_answer(fact)
    assert labeled == "Скорость света: 299792458 м/с", (
        f"WORLD_FACT не должен получать prefix. Получено: {labeled!r}"
    )


def test_retrieval_labeling_opinion():
    """OPINION маркируется как «Ваше мнение»."""
    from core.pipeline import _label_claim_for_answer
    labeled = _label_claim_for_answer({
        "claim": "он поступил плохо",
        "claim_type": "OPINION",
    })
    assert "мнени" in labeled.lower() or "OPINION" in labeled


# ─── Bonus: Classifier smoke tests (Russian) ─────────────────────────────────

@pytest.mark.parametrize("text,expected_ct", [
    ("Мне было тревожно при разговоре",          "EMOTION"),
    ("Я чувствую радость",                        "EMOTION"),
    ("По моему мнению, это неправильно",          "OPINION"),
    ("Мне кажется, он меня не уважает",           "INTERPRETATION"),
    ("Я хочу выучить программирование",           "GOAL"),
    ("Я предпочитаю работать по утрам",           "PREFERENCE"),
    ("Я помню, как мы встретились в парке",       "USER_EXPERIENCE"),
    ("Согласно данным ВОЗ, заболеваемость растёт","WORLD_FACT"),
    ("Вода кипит при 100°C на уровне моря",       "WORLD_FACT"),
])
def test_classifier_ru(text, expected_ct):
    from core.claim_classifier import classify_claim
    ct, _, _ = classify_claim(text)
    assert ct == expected_ct, (
        f"Текст {text!r}: ожидался {expected_ct!r}, получен {ct!r}"
    )


@pytest.mark.parametrize("source,expected_ot", [
    ("user_message",    "USER_REPORTED"),
    ("telegram",        "USER_REPORTED"),
    ("llm_output",      "LLM_OUTPUT"),
    ("gpt-4o",          "LLM_OUTPUT"),
    ("physics.optics",  "EXTERNAL"),
    ("wsc:TERM",        "EXTERNAL"),
    ("domain_seed",     "EXTERNAL"),
    ("causal_bridge",   "DERIVED"),
])
def test_origin_from_source(source, expected_ot):
    from core.claim_classifier import classify_claim
    _, ot, _ = classify_claim("Некое утверждение", source=source)
    assert ot == expected_ot, (
        f"source={source!r}: ожидался origin_type={expected_ot!r}, получен {ot!r}"
    )


# ─── Validation matrix (Qwen Уточнение А): recommend_target_state ────────────

@pytest.mark.parametrize("ct,ot,evidence,expected_state", [
    # WORLD_FACT depends on origin
    ("WORLD_FACT",     "EXTERNAL",      True,  "Validated"),    # external + evidence
    ("WORLD_FACT",     "EXTERNAL",      False, "Supported"),    # external, no structural cite
    ("WORLD_FACT",     "USER_REPORTED", False, "Hypothesized"), # hearsay needs confirmation
    ("WORLD_FACT",     "LLM_OUTPUT",    False, "Observed"),     # LLM can't self-verify
    ("WORLD_FACT",     "DERIVED",       False, "Hypothesized"), # inferred needs review
    # Subjective types — valid as their modality when human-reported
    ("EMOTION",        "USER_REPORTED", False, "Validated"),
    ("OPINION",        "USER_REPORTED", False, "Validated"),
    ("INTERPRETATION", "USER_REPORTED", False, "Validated"),
    ("GOAL",           "USER_REPORTED", False, "Validated"),
    ("PREFERENCE",     "USER_REPORTED", False, "Validated"),
    ("USER_EXPERIENCE","USER_REPORTED", False, "Validated"),
    # Subjective + LLM → weaker
    ("EMOTION",        "LLM_OUTPUT",    False, "Hypothesized"),
    # System note / unknown
    ("SYSTEM_NOTE",    "SYSTEM_GENERATED", False, "Supported"),
    ("UNKNOWN",        "UNKNOWN",       False, "Observed"),
])
def test_recommend_target_state_matrix(ct, ot, evidence, expected_state):
    from core.truth_policy import recommend_target_state
    fact = {
        "claim_type":  ct,
        "origin_type": ot,
        "confidence":  0.9,
        "source":      "test",
        "metadata":    {"evidence_refs": [{"source_id": "e1"}]} if evidence else {},
    }
    state, reason = recommend_target_state(fact)
    assert state == expected_state, (
        f"({ct} × {ot}, evidence={evidence}): "
        f"ожидалось {expected_state!r}, получено {state!r} (reason={reason})"
    )


def test_unknown_cannot_become_world_fact_grade():
    """ChatGPT v1.1 #1: UNKNOWN-модальность без evidence не может стать
    Validated/ImmutableCore (не трактуется как факт о мире)."""
    from core.truth_policy import modality_guard
    fact = {
        "claim_type": "UNKNOWN", "origin_type": "UNKNOWN",
        "confidence": 0.95, "source": "legacy", "metadata": {},
    }
    ok_v, reason_v = modality_guard(fact, "Validated")
    ok_i, _ = modality_guard(fact, "ImmutableCore")
    assert not ok_v, f"UNKNOWN→Validated должен блокироваться, reason={reason_v}"
    assert not ok_i, "UNKNOWN→ImmutableCore должен блокироваться"
    # но cautious-состояния разрешены
    ok_s, _ = modality_guard(fact, "Supported")
    ok_o, _ = modality_guard(fact, "Observed")
    assert ok_s and ok_o, "UNKNOWN → Supported/Observed должно быть разрешено"


def test_unknown_with_evidence_may_be_validated():
    """UNKNOWN с реальными evidence_refs (реклассификация/доказательство) → Validated ок."""
    from core.truth_policy import modality_guard
    fact = {
        "claim_type": "UNKNOWN", "origin_type": "EXTERNAL",
        "confidence": 0.95, "source": "doc:x",
        "metadata": {"evidence_refs": [{"source_id": "e1", "span": "1-9"}]},
    }
    ok, reason = modality_guard(fact, "Validated")
    assert ok, f"UNKNOWN+evidence → Validated должно быть разрешено, reason={reason}"


def test_matrix_consistent_with_modality_guard():
    """Матрица не должна рекомендовать состояние, которое modality_guard блокирует."""
    from core.truth_policy import modality_guard, recommend_target_state
    # EMOTION рекомендуется в Validated — guard это разрешает
    emo = {"claim_type": "EMOTION", "origin_type": "USER_REPORTED",
           "confidence": 0.9, "source": "user", "metadata": {}}
    state, _ = recommend_target_state(emo)
    ok, _ = modality_guard(emo, state)
    assert ok, "Матрица и guard должны быть согласованы для EMOTION"
    # И guard всё ещё блокирует ImmutableCore для EMOTION (матрица его и не рекомендует)
    ok_immut, _ = modality_guard(emo, "ImmutableCore")
    assert not ok_immut
