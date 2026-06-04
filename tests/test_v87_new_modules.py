"""
tests/test_v87_new_modules.py — Тесты для новых модулей V8.7 Titan

Покрытие:
    1. PAD-детектор — эмоциональный анализ
    2. GCR-фильтр — программный контракт Graph=Truth
    3. BranchManager — multi-perspective reasoning
    4. StimulusMap — двусторонняя трассируемость
    5. Identity Layer — классификация контента
    6. Reconsolidation — живая память
    7. Conversation Consolidation — блокнот диалога
    8. Lightweight Metrics — лёгкие метрики
    9. Meta-Cognition — рефлексия о процессе
"""

import pytest
import tempfile
import os


# ═══════════════════════════════════════════════════════════════════════════════
# 1. PAD-детектор
# ═══════════════════════════════════════════════════════════════════════════════

def test_pad_detects_high_arousal_negative():
    """PAD: 'TERRIBLE!!!' → низкий valence, высокий arousal."""
    from core.interoception import detect_pad_from_text
    pad = detect_pad_from_text("It's TERRIBLE! How could you suggest that?! FIX it NOW!!!")
    assert pad is not None
    assert pad.valence < 0.5, f"valence={pad.valence}, ожидалось <0.5 (негатив)"
    assert pad.arousal > 0.6, f"arousal={pad.arousal}, ожидалось >0.6 (возбуждение)"
    assert pad.distress > 0.4, f"distress={pad.distress}, ожидалось >0.4"


def test_pad_detects_calm_positive():
    """PAD: 'I am calm and happy' → высокий valence, низкий arousal."""
    from core.interoception import detect_pad_from_text
    pad = detect_pad_from_text("I am calm and happy today. Everything is great.")
    assert pad is not None
    assert pad.valence > 0.5, f"valence={pad.valence}, ожидалось >0.5 (позитив)"
    assert pad.arousal < 0.6, f"arousal={pad.arousal}, ожидалось <0.6 (спокойствие)"


def test_pad_none_for_empty_text():
    """PAD: пустой текст → None."""
    from core.interoception import detect_pad_from_text
    assert detect_pad_from_text("") is None
    assert detect_pad_from_text("   ") is None


def test_pad_crisis_detection():
    """PAD: кризис — valence<0.3 И arousal>0.7."""
    from core.interoception import PADState
    crisis = PADState(valence=0.2, arousal=0.8, dominance=0.3)
    assert crisis.is_crisis
    assert crisis.marker == "anxiety"

    normal = PADState(valence=0.6, arousal=0.4, dominance=0.6)
    assert not normal.is_crisis
    assert normal.marker in ("neutral", "curiosity", "relief")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. GCR-фильтр
# ═══════════════════════════════════════════════════════════════════════════════

def test_gcr_hypothesis_when_no_facts():
    """GCR: без фактов → весь ответ = HYPOTHESIS."""
    from core.output_faithfulness import apply_gcr_filter
    result = apply_gcr_filter("The Earth revolves around the Sun.", [])
    assert "[HYPOTHESIS" in result, f"Ожидался HYPOTHESIS в ответе: {result[:100]}"


def test_gcr_marks_unsupported_claim():
    """GCR: claim без опоры на факты → [UNSUPPORTED]."""
    from core.output_faithfulness import apply_gcr_filter
    facts = [{"claim": "Water boils at 100 degrees Celsius at sea level", "source": "physics"}]
    result = apply_gcr_filter("Water boils at 100C. Quantum computers will replace all classical computers by 2030.", facts)
    assert "UNSUPPORTED" in result or "HYPOTHESIS" in result, \
        f"Неподтверждённый claim должен быть маркирован: {result[:150]}"


def test_gcr_passes_supported_claim():
    """GCR: полностью supported claim → чистый вывод."""
    from core.output_faithfulness import apply_gcr_filter
    facts = [{"claim": "DNA carries genetic information in all living organisms", "source": "biology"}]
    result = apply_gcr_filter("DNA carries genetic information in all living organisms.", facts)
    assert "[HYPOTHESIS" not in result, f"Supported claim не должен маркироваться: {result[:100]}"
    assert "[UNSUPPORTED" not in result, f"Supported claim не должен маркироваться: {result[:100]}"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. BranchManager
# ═══════════════════════════════════════════════════════════════════════════════

def test_branch_manager_single_role():
    """BranchManager: 1 роль → 1 ветка, без синтеза, 0 ролей."""
    from core.perspectives import resolve_roles
    roles = resolve_roles("test query", requested_roles=["ENGINEER"])
    assert len(roles) == 1
    assert roles[0].role_id == "ENGINEER"


def test_branch_manager_auto_roles():
    """BranchManager: авто-определение ролей по запросу."""
    from core.perspectives import resolve_roles

    # "how to build" → ENGINEER + ADVISOR
    roles = resolve_roles("how to build an eco house?")
    role_ids = {r.role_id for r in roles}
    assert "ENGINEER" in role_ids

    # "why" → SCIENTIST + ANALYST
    roles = resolve_roles("why does water boil at 100 degrees?")
    role_ids = {r.role_id for r in roles}
    assert "SCIENTIST" in role_ids


def test_branch_manager_default_triad():
    """BranchManager: без явного запроса → default triad."""
    from core.perspectives import resolve_roles, DEFAULT_TRIAD
    roles = resolve_roles("tell me about quantum physics")
    role_ids = {r.role_id for r in roles}
    assert len(role_ids) >= 2, f"Ожидалось минимум 2 роли, получено {len(role_ids)}"


def test_branch_manager_creative_mode():
    """BranchManager: 'придумай метафору' → CREATIVE."""
    from core.perspectives import resolve_roles
    roles = resolve_roles("придумай метафору для искусственного интеллекта")
    role_ids = {r.role_id for r in roles}
    assert "CREATIVE" in role_ids, f"Ожидался CREATIVE в {role_ids}"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. StimulusMap
# ═══════════════════════════════════════════════════════════════════════════════

def test_stimulus_map_link_and_find():
    """StimulusMap: link → find_by_stimulus → правильный результат."""
    from core.stimulus_map import StimulusMap
    with tempfile.TemporaryDirectory() as tmp:
        sm = StimulusMap(os.path.join(tmp, "test_sm.db"))
        sm.link(stimulus_id="msg_001", memory_id="fact_001", stimulus_type="message")
        sm.link(stimulus_id="msg_001", memory_id="fact_002", stimulus_type="message")

        by_stimulus = sm.find_by_stimulus("msg_001")
        assert len(by_stimulus) == 2, f"Ожидалось 2 факта для msg_001, получено {len(by_stimulus)}"

        trace = sm.full_trace("fact_001")
        assert len(trace["stimuli"]) >= 1
        assert trace["memory_id"] == "fact_001"


def test_stimulus_map_attach_response():
    """StimulusMap: attach_response → find_by_memory содержит response_id."""
    from core.stimulus_map import StimulusMap
    with tempfile.TemporaryDirectory() as tmp:
        sm = StimulusMap(os.path.join(tmp, "test_sm2.db"))
        sm.link(stimulus_id="msg_002", memory_id="fact_003")
        sm.attach_response(memory_id="fact_003", response_id="resp_882")

        trace = sm.full_trace("fact_003")
        assert "resp_882" in trace["responses"], f"Ожидался response_id в trace: {trace['responses']}"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Identity Layer
# ═══════════════════════════════════════════════════════════════════════════════

def test_identity_classify_values():
    """Identity: 'I believe in honesty' → VALUES."""
    from core.identity_layer import classify_identity, IdentityCategory
    assert classify_identity("I believe in honesty above all") == IdentityCategory.VALUES


def test_identity_classify_biography():
    """Identity: 'I was born in Grozny' → BIOGRAPHY."""
    from core.identity_layer import classify_identity, IdentityCategory
    assert classify_identity("I was born in Grozny in 1990") == IdentityCategory.BIOGRAPHY


def test_identity_classify_worldview():
    """Identity: 'I think technology should serve people' → WORLDVIEW."""
    from core.identity_layer import classify_identity, IdentityCategory
    assert classify_identity("I think technology should serve people") == IdentityCategory.WORLDVIEW


def test_identity_classify_compass():
    """Identity: 'THIS INFURIATES ME!' → COMPASS."""
    from core.identity_layer import classify_identity, IdentityCategory
    assert classify_identity("THIS INFURIATES ME!") == IdentityCategory.COMPASS


def test_identity_neutral_content():
    """Identity: 'Water boils at 100C' → None (не про меня)."""
    from core.identity_layer import classify_identity
    assert classify_identity("Water boils at 100 degrees Celsius") is None


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Reconsolidation
# ═══════════════════════════════════════════════════════════════════════════════

def test_reconsolidation_signal_creation():
    """Reconsolidation: сигнал создаётся корректно."""
    from core.reconsolidation import ReconsolidationSignal
    signal = ReconsolidationSignal(
        fact_id="fact_test",
        query_context="architecture design",
        user_satisfaction=0.85,
    )
    assert signal.fact_id == "fact_test"
    assert signal.query_context == "architecture design"
    assert signal.user_satisfaction == 0.85


def test_reconsolidation_engine_instantiation():
    """Reconsolidation: движок создаётся без ошибок."""
    from core.reconsolidation import get_reconsolidation_engine
    engine = get_reconsolidation_engine()
    assert engine is not None
    stats = engine.stats()
    assert "processed_total" in stats


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Conversation Consolidation
# ═══════════════════════════════════════════════════════════════════════════════

def test_conversation_add_insight():
    """Conversation: add_insight создаёт запись."""
    from core.conversation_consolidation import ConversationConsolidator
    with tempfile.TemporaryDirectory() as tmp:
        cc = ConversationConsolidator(os.path.join(tmp, "test_cc.db"))
        ok = cc.add_insight(chat_id="chat_42", insight="Обсуждаем архитектуру памяти")
        assert ok

        nb = cc.get_notebook("chat_42")
        assert nb is not None
        assert len(nb.key_insights) >= 1
        assert "архитектуру" in nb.key_insights[0].lower()


def test_conversation_finalize():
    """Conversation: finalize создаёт финальный блокнот."""
    from core.conversation_consolidation import ConversationConsolidator
    with tempfile.TemporaryDirectory() as tmp:
        cc = ConversationConsolidator(os.path.join(tmp, "test_cc2.db"))
        cc.add_insight(chat_id="chat_43", insight="Обсуждаем RAG-системы")
        nb = cc.finalize(
            chat_id="chat_43",
            main_topic="RAG Architecture",
            user_goal="Улучшить retrieval",
            conclusion="Гибридный поиск с переранжированием даёт лучшие результаты",
        )
        assert nb is not None
        assert nb.main_topic == "RAG Architecture"
        assert nb.produced_gist is True


def test_conversation_search():
    """Conversation: search находит релевантные блокноты."""
    from core.conversation_consolidation import ConversationConsolidator
    with tempfile.TemporaryDirectory() as tmp:
        cc = ConversationConsolidator(os.path.join(tmp, "test_cc3.db"))
        cc.finalize(chat_id="chat_50", main_topic="Machine Learning Basics", user_goal="Learn ML", conclusion="ML is fun")
        cc.finalize(chat_id="chat_51", main_topic="Deep Learning Advanced", user_goal="Master DL", conclusion="DL is deep")
        results = cc.search("Machine Learning")
        assert len(results) >= 1
        assert any("Machine" in r.main_topic for r in results)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Lightweight Metrics
# ═══════════════════════════════════════════════════════════════════════════════

def test_metrics_record_and_summary():
    """Metrics: record → summary содержит счётчики."""
    from core.lightweight_metrics import LightweightMetrics, EvalReport
    with tempfile.TemporaryDirectory() as tmp:
        m = LightweightMetrics(os.path.join(tmp, "test_metrics.jsonl"))
        m.record(EvalReport(query="test", grounding_score=0.85, trace_completeness=0.9, unsupported_claim_count=2, total_claims=5))
        summary = m.summary()
        assert summary["total_queries"] >= 1
        assert summary["total_unsupported_claims"] >= 2


def test_metrics_aggregate():
    """Metrics: aggregate считает средние."""
    from core.lightweight_metrics import LightweightMetrics, EvalReport
    with tempfile.TemporaryDirectory() as tmp:
        m = LightweightMetrics(os.path.join(tmp, "test_metrics2.jsonl"))
        m.record(EvalReport(query="q1", grounding_score=0.8, trace_completeness=0.7))
        m.record(EvalReport(query="q2", grounding_score=1.0, trace_completeness=0.9))
        agg = m.aggregate()
        assert agg["count"] == 2
        assert 0.8 < agg["avg_grounding_score"] < 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Meta-Cognition
# ═══════════════════════════════════════════════════════════════════════════════

def test_meta_cognition_surface_warning():
    """MetaCognition: короткий ответ при многих фактах → surface warning."""
    from core.meta_cognition import MetaCognitiveLoop
    loop = MetaCognitiveLoop()
    report = loop.reflect(
        query="What is DNA?",
        facts=[{"claim": "DNA carries genetic info"}, {"claim": "DNA is a double helix"}, {"claim": "DNA replicates semi-conservatively"}],
        response="DNA is the blueprint of life.",
    )
    assert report.surface_level_warning, "Короткий ответ при 3 фактах должен вызвать surface warning"


def test_meta_cognition_overthinking():
    """MetaCognition: много фактов для короткого запроса → overthinking warning."""
    from core.meta_cognition import MetaCognitiveLoop
    loop = MetaCognitiveLoop()
    report = loop.reflect(
        query="Hi",
        facts=[{"claim": f"Fact {i}"} for i in range(12)],
        response="Hello! How can I help you today?",
    )
    assert report.overthinking_warning, "12 фактов для 'Hi' должны вызвать overthinking warning"


def test_meta_cognition_no_warnings_for_normal():
    """MetaCognition: нормальный запрос → без предупреждений."""
    from core.meta_cognition import MetaCognitiveLoop
    loop = MetaCognitiveLoop()
    report = loop.reflect(
        query="Explain quantum entanglement in detail",
        facts=[{"claim": "Entanglement is a quantum phenomenon"}, {"claim": "It links particles across distance"}],
        response="Quantum entanglement is a fascinating phenomenon where two particles become correlated in such a way that the state of one cannot be described independently of the other. This has profound implications for quantum computing and our understanding of reality.",
    )
    assert not report.surface_level_warning
    assert not report.overthinking_warning


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Ontological Axes
# ═══════════════════════════════════════════════════════════════════════════════

def test_axes_all_six_present():
    """OntologicalAxes: все 6 осей определены."""
    from core.ontological_axes import AXES, CognitiveAxis
    assert len(AXES) == 6
    assert CognitiveAxis.SPATIAL in AXES
    assert CognitiveAxis.BIOLOGICAL in AXES
    assert CognitiveAxis.ENGINEERING in AXES


def test_axes_properties():
    """OntologicalAxes: ось имеет свойства и аффордансы."""
    from core.ontological_axes import AXES, CognitiveAxis
    spatial = AXES[CognitiveAxis.SPATIAL]
    assert len(spatial.extractable_properties) >= 3
    assert len(spatial.affordance_categories) >= 2
    assert spatial.focus


# ═══════════════════════════════════════════════════════════════════════════════
# Сводка
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("V8.7 New Module Tests — запуск: pytest tests/test_v87_new_modules.py -v")
