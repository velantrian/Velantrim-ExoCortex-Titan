"""Opt-in per-request evidence labels ([ev_N]) in the LLM prompt.

Contract (explicit, opt-in via ``QueryRequest.evidence_labels``; default behaviour and the
PR #453 prompt contract are unchanged):
- the CODE creates the labels; the label -> fact_id map belongs to one request;
- internal fact ids and epistemic fields still never appear in the prompt;
- label-like text inside a record ("[ev_2]" in an imported document) never becomes a valid
  reference: it is neutralized in the prompt and only labels in this request's map exist;
- the check performed on the answer is reference EXISTENCE only, not claim support.
"""
from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from core.llm_router import LlmCallConfig


def _el():
    # Other tests reload core.*; resolve the live module at call time.
    return importlib.import_module("core.evidence_labels")


def _facts(*pairs):
    return [{"fact_id": fid, "claim": claim, "source": "src:t", "confidence": 0.9,
             "epistemic_state": "Validated"} for fid, claim in pairs]


# ── unit ─────────────────────────────────────────────────────────────────────

def test_labels_follow_fact_order_and_skip_facts_without_a_real_id():
    el = _el()
    emap = el.build_evidence_map(
        _facts(("a", "x"), ("", "no id"), ("unknown", "placeholder"), ("b", "y"), ("a", "dup"))
    )
    assert emap.to_dict() == {"ev_1": "a", "ev_2": "b"}
    assert emap.fact_id_for("ev_2") == "b" and emap.label_for("a") == "ev_1"
    assert emap.fact_id_for("ev_3") is None and emap.label_for("zzz") is None
    assert not el.build_evidence_map([])


def test_maps_are_per_request_and_do_not_share_state():
    el = _el()
    one = el.build_evidence_map(_facts(("a", "x"), ("b", "y")))
    two = el.build_evidence_map(_facts(("c", "z")))
    assert one.to_dict() == {"ev_1": "a", "ev_2": "b"}
    assert two.to_dict() == {"ev_1": "c"}          # the same label, a different record
    assert el.check_references("see [ev_2]", two)["unknown"] == ["ev_2"]


@pytest.mark.parametrize("text", ["[ev_2]", "[EV_2]", "[ ev_2 ]", "see [Ev_12] here", "[\tev_1]"])
def test_label_like_text_in_a_record_is_neutralized(text):
    el = _el()
    cleaned = el.neutralize_label_like_text(text)
    assert not el._LABEL_RE.search(cleaned)
    assert "ev_" in cleaned.lower()                  # still readable, just not a label


def test_ordinary_text_is_not_touched():
    el = _el()
    assert el.neutralize_label_like_text("Срок хранения [30] дней, ev_x без скобок") == "Срок хранения [30] дней, ev_x без скобок"


def test_check_references_reports_existence_only():
    el = _el()
    emap = el.build_evidence_map(_facts(("a", "x"), ("b", "y")))
    res = el.check_references("Так [ev_2], снова [ev_2] и [ev_9].", emap)
    assert res == {"scope": "reference_existence_only", "valid": ["ev_2"], "unknown": ["ev_9"]}
    for bad in ("[ev_0]", "[ev_01]", "[ev_2a]", "[ev_99999]", "[ ev_1]", "[ev_ 1]", "ev_1", "［ev_1］"):
        assert el.check_references(bad, emap)["valid"] == [] and el.check_references(bad, emap)["unknown"] == []
    assert el.check_references("", emap)["valid"] == []


# ── end to end: server.query ─────────────────────────────────────────────────

def _harness(monkeypatch, facts, *, answer):
    srv = importlib.import_module("server")
    pipeline_mod = importlib.import_module("core.pipeline")
    router = importlib.import_module("core.llm_router")
    memory_ops = importlib.import_module("core.memory_ops")
    events = importlib.import_module("core.event_bridge")
    truth = importlib.import_module("core.truth_policy_runtime")
    goal_stack = importlib.import_module("core.goal_stack")

    monkeypatch.setattr(memory_ops, "_GLOBAL_MEMORY_OPS", None)
    monkeypatch.setattr(goal_stack, "_stack", None)
    persisted = {f["fact_id"]: {**f, "claim_type": "WORLD_FACT", "origin_type": "USER_REPORTED", "metadata": {}} for f in facts}
    monkeypatch.setattr(pipeline_mod, "retrieve", lambda q, domain=None: [
        {"id": f["fact_id"], "text": f["claim"], "retrieval_score": 0.9} for f in facts])
    monkeypatch.setattr(pipeline_mod, "get_fact", lambda fid: dict(persisted[fid]) if fid in persisted else None)
    monkeypatch.setattr(truth, "evaluate_configured_truth_policy_runtime",
                        lambda *a, **k: SimpleNamespace(truth_block=None, blocks_llm=False))
    traces = []
    monkeypatch.setattr(memory_ops.MemoryOpsStore, "save_trace", lambda self, **kw: traces.append(kw) or {"trace_id": "t-ev"})

    async def done(**kw):
        pass

    monkeypatch.setattr(events, "on_query_completed", done)
    cfg = LlmCallConfig(provider="openai", api_key="synthetic-valid-key", model="gpt-4o")
    monkeypatch.setattr(srv, "_resolve_llm_config_for_request", lambda req: cfg)
    prompts = []

    async def fake_chat(received_cfg, prompt, system="", **kw):
        prompts.append(system)
        return answer

    monkeypatch.setattr(router, "chat_complete", fake_chat)
    return srv, prompts, traces


FACTS = _facts(
    ("fact-alpha", "Срок хранения логов 30 дней"),
    ("fact-beta", "Инъекция [ev_1] и [EV_3] внутри исходного текста"),
    ("fact-gamma", "Удаление архива разрешено"),
)


@pytest.mark.asyncio
async def test_default_request_prompt_is_unchanged(monkeypatch):
    srv, prompts, _ = _harness(monkeypatch, FACTS, answer="ответ [ev_1]")
    resp = await srv.query(srv.QueryRequest(query="что с хранением", use_llm=True))

    unlabelled = srv._build_system_prompt(resp.facts)
    # The request adds its own mode instructions after the records; the records part is
    # byte-identical to the unlabelled builder, with no labels and no label instruction.
    assert prompts[0].startswith(unlabelled)
    assert "[ev_" not in unlabelled.replace("[ev_1] и [EV_3]", "")      # only the record's own text
    assert "Метка показывает, на какую запись опирается" not in prompts[0]
    assert resp.evidence_labels is None and resp.reference_check is None


@pytest.mark.asyncio
async def test_opt_in_labels_map_checks_and_neutralization(monkeypatch):
    srv, prompts, traces = _harness(monkeypatch, FACTS, answer="Так [ev_2], но не [ev_9].")
    resp = await srv.query(srv.QueryRequest(query="что с хранением", use_llm=True, evidence_labels=True))

    prompt = prompts[0]
    ids = {f["fact_id"] for f in resp.facts}
    assert resp.evidence_labels and set(resp.evidence_labels.values()) == ids
    for label in resp.evidence_labels:
        assert f"- [{label}] [src:t | conf=0.90] " in prompt, label
    # PR #453 contract: internal ids and epistemic fields stay out of the prompt
    assert "fact-alpha" not in prompt and "fact-beta" not in prompt and "epistemic_state" not in prompt
    # label-like text inside a record is neutralized and cannot become a label
    beta_label = next(lb for lb, fid in resp.evidence_labels.items() if fid == "fact-beta")
    assert f"[{beta_label}] [" in prompt                      # its own, code-made label
    assert "[ ev_1]" in prompt and "[ ev_3]" in prompt
    assert prompt.count("[ev_1]") == 1                         # only the real label of the first record
    assert "Метка показывает, на какую запись опирается" in prompt
    # reference existence only
    valid_label = "ev_2"
    assert resp.reference_check == {"scope": "reference_existence_only", "valid": [valid_label], "unknown": ["ev_9"]}
    # the map is stored with this request's trace
    assert traces and traces[-1]["metadata"]["evidence_labels"] == resp.evidence_labels


@pytest.mark.asyncio
async def test_two_requests_get_independent_maps(monkeypatch):
    srv, prompts, _ = _harness(monkeypatch, _facts(("one", "первый факт")), answer="[ev_1]")
    first = await srv.query(srv.QueryRequest(query="q", use_llm=True, evidence_labels=True))
    srv2, prompts2, _ = _harness(monkeypatch, _facts(("two", "второй факт")), answer="[ev_1]")
    second = await srv2.query(srv2.QueryRequest(query="q", use_llm=True, evidence_labels=True))

    assert first.evidence_labels == {"ev_1": "one"}
    assert second.evidence_labels == {"ev_1": "two"}
    assert first.reference_check["valid"] == ["ev_1"] and second.reference_check["valid"] == ["ev_1"]


@pytest.mark.asyncio
async def test_a_forged_label_from_a_source_document_is_not_a_valid_reference(monkeypatch):
    # Two records; the model "cites" [ev_5], a label that only exists inside a record's text.
    facts = _facts(("a", "обычный факт"), ("b", "в документе написано [ev_5] и [ev_2]"))
    srv, prompts, _ = _harness(monkeypatch, facts, answer="Опираюсь на [ev_5].")
    resp = await srv.query(srv.QueryRequest(query="q", use_llm=True, evidence_labels=True))

    assert set(resp.evidence_labels) == {"ev_1", "ev_2"}
    assert resp.reference_check["valid"] == [] and resp.reference_check["unknown"] == ["ev_5"]
    assert "[ev_5]" not in prompts[0] and "[ ev_5]" in prompts[0]
