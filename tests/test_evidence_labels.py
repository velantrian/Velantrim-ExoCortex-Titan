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
    # ("a", "dup") shows different content under the same fact_id: its own label, both ambiguous
    assert emap.to_dict() == {"ev_1": "a", "ev_2": "b", "ev_3": "a"}
    assert emap.ambiguous == frozenset({"ev_1", "ev_3"})
    assert emap.fact_id_for("ev_2") == "b" and emap.label_for("a") == "ev_1"
    assert emap.fact_id_for("ev_9") is None and emap.label_for("zzz") is None
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
    assert res == {"scope": "reference_existence_only", "valid": ["ev_2"], "unknown": ["ev_9"],
                   "ambiguous": [], "malformed": []}
    for bad in ("[ev_0]", "[ev_01]", "[ev_2a]", "[ev_99999]", "[ ev_1]", "[ev_ 1]", "ev_1", "［ev_1］"):
        assert el.check_references(bad, emap)["valid"] == [] and el.check_references(bad, emap)["unknown"] == []
    assert el.check_references("", emap)["valid"] == []


@pytest.mark.parametrize(
    ("answer", "malformed"),
    [
        ("Так [ev_1, ev_9].", ["ev_1", "ev_9"]),            # grouped citation: a common model habit
        ("Так [ev_9; ev_1]", ["ev_9", "ev_1"]),
        ("Так (ev_9)", ["ev_9"]),
        ("Так [EV_9]", ["EV_9"]),
        ("Так [ ev_9 ]", ["ev_9"]),
        ("см. ev_9 и ev_9", ["ev_9"]),                      # reported once
        ("[ev_01] [ev_0] [ev_2a] [ev_99999]", ["ev_01", "ev_0", "ev_2a", "ev_99999"]),
        ("［ev_1］", ["ev_1"]),                              # full-width brackets
    ],
)
def test_label_like_text_that_is_not_an_exact_label_is_reported_not_ignored(answer, malformed):
    el = _el()
    emap = el.build_evidence_map(_facts(("a", "x"), ("b", "y")))
    res = el.check_references(answer, emap)
    assert res["valid"] == [] and res["unknown"] == []       # never counted as a reference
    assert res["malformed"] == malformed


def test_exact_labels_are_not_reported_as_malformed_and_ordinary_words_are_ignored():
    el = _el()
    emap = el.build_evidence_map(_facts(("a", "x"), ("b", "y")))
    res = el.check_references("Так [ev_1][ev_9], dev_mode и prev_1 — обычные слова; ещё ev_3.", emap)
    assert res["valid"] == ["ev_1"] and res["unknown"] == ["ev_9"]
    assert res["malformed"] == ["ev_3"]
    many = " ".join(f"ev_{n}x" for n in range(1, 40)) + " ev_" + "9" * 80
    capped = el.check_references(many, emap)["malformed"]
    assert len(capped) == 20 and all(len(item) <= 24 for item in capped)


def test_opt_in_without_any_labelable_record_still_neutralizes_and_checks():
    # No record has a real fact_id: the map is empty, but the opt-in is still in force.
    srv = importlib.import_module("server")
    el = _el()
    facts = [{"fact_id": "", "claim": "в документе [ev_1]", "source": "import [ev_2]", "confidence": 0.9}]
    emap = el.build_evidence_map(facts)
    assert not emap and emap.to_dict() == {}
    prompt = srv._build_system_prompt(facts, evidence_map=emap)
    assert "- [import [ ev_2] | conf=0.90] в документе [ ev_1]" in prompt
    assert "[ev_" not in prompt.replace(el.PROMPT_EMPTY_INSTRUCTION, "")   # no label of any kind
    assert el.PROMPT_INSTRUCTION not in prompt                 # no label exists to point at
    assert el.PROMPT_EMPTY_INSTRUCTION in prompt               # the model is told not to invent any
    assert el.check_references("опираюсь на [ev_1]", emap)["unknown"] == ["ev_1"]
    # default (no map at all) is a different thing: the record text is passed as is
    assert "в документе [ev_1]" in srv._build_system_prompt(facts)


def test_the_instruction_points_at_the_records_above_and_asks_for_one_label_per_bracket():
    srv = importlib.import_module("server")
    el = _el()
    facts = _facts(("a", "x"))
    prompt = srv._build_system_prompt(facts, evidence_map=el.build_evidence_map(facts))
    assert prompt.index("- [ev_1] ") < prompt.index(el.PROMPT_INSTRUCTION)     # records come first
    assert "выше" in el.PROMPT_INSTRUCTION and "ниже" not in el.PROMPT_INSTRUCTION
    assert "[ev_N] [ev_M], а не [ev_N, ev_M]" in el.PROMPT_INSTRUCTION
    # the instruction's own examples are not labels: it adds no real-looking label to the prompt
    assert not el._LABEL_RE.search(el.PROMPT_INSTRUCTION)
    assert prompt.count("[ev_1]") == 1


# ── end to end: server.query ─────────────────────────────────────────────────

def _harness(monkeypatch, facts, *, answer, provider="openai", blocks_llm=False):
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
                        lambda *a, **k: SimpleNamespace(truth_block=None, blocks_llm=blocks_llm))
    traces = []
    monkeypatch.setattr(memory_ops.MemoryOpsStore, "save_trace", lambda self, **kw: traces.append(kw) or {"trace_id": "t-ev"})

    async def done(**kw):
        pass

    monkeypatch.setattr(events, "on_query_completed", done)
    cfg = LlmCallConfig(provider=provider, api_key="synthetic-valid-key", model="gpt-4o")
    monkeypatch.setattr(srv, "_resolve_llm_config_for_request", lambda req: cfg)
    prompts = []

    async def fake_chat(received_cfg, prompt, system="", **kw):
        prompts.append(system)
        if isinstance(answer, Exception):
            raise answer
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
    assert resp.reference_check == {"scope": "reference_existence_only", "valid": [valid_label],
                                    "unknown": ["ev_9"], "ambiguous": [], "malformed": []}
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


@pytest.mark.asyncio
async def test_query_builds_the_map_from_the_records_that_were_sent_and_renumbers_it(monkeypatch):
    # A per-message limit omits the oversized record. The published map and the prompt are built
    # from the records that were sent: no gap in the numbering, no label for the omitted record,
    # and the model is still told that records were left out (#516).
    facts = _facts(("small-1", "короткая запись один"), ("huge", "Ж" * 6000), ("small-2", "короткая запись два"))
    monkeypatch.setenv("DEEPSEEK_MESSAGE_CHAR_LIMIT", "4000")
    srv, prompts, traces = _harness(monkeypatch, facts, answer="[ev_1] [ev_2] [ev_3]", provider="deepseek")
    resp = await srv.query(srv.QueryRequest(query="q", use_llm=True, evidence_labels=True))

    prompt = prompts[0]
    assert "Ж" * 100 not in prompt                                       # retrieved, not sent
    assert set(resp.evidence_labels) == {"ev_1", "ev_2"}                 # no gap
    assert set(resp.evidence_labels.values()) == {"small-1", "small-2"}
    assert "- [ev_1] [src:t" in prompt and "- [ev_2] [src:t" in prompt and "[ev_3]" not in prompt
    assert resp.reference_check["valid"] == ["ev_1", "ev_2"] and resp.reference_check["unknown"] == ["ev_3"]
    assert "1 из 3 записей памяти не переданы" in prompt                 # the #516 notice survives
    report = resp.context_report
    assert report["memory_records_total"] == 3 and report["memory_records_sent"] == 2
    assert [o["fact_id"] for o in report["memory_records_omitted"]] == ["huge"]
    assert report["applied"] and report["applied"][0]["omitted"] == 1
    assert len(report["memory_records_omitted"]) == 1
    assert len([item for item in report["applied"] if item.get("affected") == "memory_records"]) == 1
    assert prompt.count("записей памяти не переданы") == 1
    assert len(prompt) <= 4000 + 400                                     # the sanitizer adds a short prefix
    assert traces[-1]["metadata"]["evidence_labels"] == resp.evidence_labels


@pytest.mark.asyncio
async def test_query_still_checks_references_when_every_labelled_record_was_omitted(monkeypatch):
    # The only record does not fit: nothing labelled reaches the model, the map is empty,
    # and a label in the answer is reported as unknown instead of not being checked at all.
    monkeypatch.setenv("DEEPSEEK_MESSAGE_CHAR_LIMIT", "4000")
    srv, prompts, _ = _harness(monkeypatch, _facts(("huge", "Ж" * 6000)), answer="Опираюсь на [ev_1].",
                               provider="deepseek")
    resp = await srv.query(srv.QueryRequest(query="q", use_llm=True, evidence_labels=True))

    assert "[ev_1]" not in prompts[0] and "Ж" * 100 not in prompts[0]
    assert resp.evidence_labels == {}                           # opt-in answered, nothing citable
    assert resp.reference_check["valid"] == [] and resp.reference_check["unknown"] == ["ev_1"]


# ── source field and conflicting records ─────────────────────────────────────

def test_an_exact_repeat_reuses_the_label_and_is_not_ambiguous():
    el = _el()
    emap = el.build_evidence_map(_facts(("a", "x"), ("a", "x"), ("b", "y")))
    assert emap.to_dict() == {"ev_1": "a", "ev_2": "b"} and not emap.ambiguous


def test_same_fact_id_with_different_content_gets_distinct_ambiguous_labels():
    el = _el()
    emap = el.build_evidence_map(_facts(("L", "ready"), ("L", "not ready")))
    assert emap.to_dict() == {"ev_1": "L", "ev_2": "L"}
    assert emap.ambiguous == frozenset({"ev_1", "ev_2"})
    res = el.check_references("см. [ev_1] и [ev_2]", emap)
    assert res["valid"] == ["ev_1", "ev_2"] and res["ambiguous"] == ["ev_1", "ev_2"]
    one = el.build_evidence_map(_facts(("L", "ready"), ("M", "other")))
    assert el.check_references("[ev_1]", one)["ambiguous"] == []


def test_a_different_source_with_the_same_claim_is_also_a_conflict():
    el = _el()
    a = {"fact_id": "L", "claim": "ready", "source": "kb:one"}
    b = {"fact_id": "L", "claim": "ready", "source": "kb:two"}
    assert el.build_evidence_map([a, b]).ambiguous == frozenset({"ev_1", "ev_2"})


def test_prompt_neutralizes_the_source_field_and_labels_conflicting_records_apart():
    # Built directly: the /query pipeline takes a record's content by fact_id, so two records
    # with one id and different content do not arise there; any other caller could pass them.
    srv = importlib.import_module("server")
    el = _el()
    facts = [
        {"fact_id": "A", "claim": "альфа", "source": "imported [ev_2]", "confidence": 0.8},
        {"fact_id": "L", "claim": "ready", "source": "src:t", "confidence": 0.9},
        {"fact_id": "L", "claim": "not ready", "source": "src:t", "confidence": 0.9},
    ]
    emap = el.build_evidence_map(facts)
    prompt = srv._build_system_prompt(facts, evidence_map=emap)

    assert "- [ev_1] [imported [ ev_2] | conf=0.80] альфа" in prompt             # source neutralized
    assert "- [ev_2] [src:t | conf=0.90] ready" in prompt
    assert "- [ev_3] [src:t | conf=0.90] not ready" in prompt                   # not the same label as the other L
    for lb in ("ev_1", "ev_2", "ev_3"):
        assert prompt.count(f"[{lb}]") == 1, lb
    res = el.check_references("[ev_1] [ev_2] [ev_3]", emap)
    assert res["valid"] == ["ev_1", "ev_2", "ev_3"] and res["ambiguous"] == ["ev_2", "ev_3"]


def test_a_source_that_starts_with_an_ev_label_and_a_bracket_does_not_become_a_code_made_label():
    # The line template wraps source in [...]: a source of "ev_2] ..." would become "[ev_2] ...".
    # Neutralizing "[ev_" inside the raw field is not enough, because the opening bracket is
    # added by the template, not present in the field.
    srv = importlib.import_module("server")
    el = _el()
    facts = [
        {"fact_id": "only", "claim": "обычный факт", "source": "ev_2] imported", "confidence": 0.8},
        {"fact_id": "other", "claim": "второй", "source": "src:t", "confidence": 0.9},
        {"fact_id": "forged", "claim": "в тексте [ev_9] и [ev_1]", "source": "doc [ev_3]", "confidence": 0.7},
    ]
    emap = el.build_evidence_map(facts)
    prompt = srv._build_system_prompt(facts, evidence_map=emap)

    assert emap.to_dict() == {"ev_1": "only", "ev_2": "other", "ev_3": "forged"}
    # The only [ev_2] in the prompt is the real label of the second record.
    assert prompt.count("[ev_2]") == 1
    assert "- [ev_2] [src:t | conf=0.90] второй" in prompt
    assert "- [ev_1] [ ev_2] imported | conf=0.80] обычный факт" in prompt
    # Forged labels inside claim/source are still neutralized; the map is unchanged.
    assert "[ ev_9]" in prompt and "[ ev_1]" in prompt and "[ ev_3]" in prompt
    assert prompt.count("[ev_1]") == 1 and prompt.count("[ev_3]") == 1
    assert "fact-only" not in prompt and "epistemic_state" not in prompt
    res = el.check_references("см. [ev_1] [ev_2] [ev_3] и [ev_9]", emap)
    assert res["valid"] == ["ev_1", "ev_2", "ev_3"] and res["unknown"] == ["ev_9"]


def test_prepared_prompt_and_map_describe_exactly_the_records_that_were_sent(monkeypatch):
    srv = importlib.import_module("server")
    el = _el()
    facts = _facts(("a", "x" * 50), ("b", "Ж" * 6000), ("c", "z" * 50))
    monkeypatch.setenv("DEEPSEEK_MESSAGE_CHAR_LIMIT", "4000")

    system, report, emap = srv._prepare_evidence_prompt(facts, provider="deepseek", lens_instructions=None)

    assert emap.to_dict() == {"ev_1": "a", "ev_2": "c"}
    assert report.sent_fact_positions == [0, 2] and report.memory_records_total == 3
    assert [o["fact_id"] for o in report.memory_records_omitted] == ["b"]
    assert "[ev_3]" not in system and "Ж" * 100 not in system
    assert "1 из 3 записей памяти не переданы" in system
    assert system.count(el.PROMPT_INSTRUCTION) == 1
    # nothing omitted: the same objects come back untouched
    monkeypatch.delenv("DEEPSEEK_MESSAGE_CHAR_LIMIT")
    system2, report2, emap2 = srv._prepare_evidence_prompt(facts, provider="deepseek", lens_instructions=None)
    assert emap2.to_dict() == {"ev_1": "a", "ev_2": "b", "ev_3": "c"} and not report2.applied


def test_the_label_instruction_appears_once_and_only_when_labelled():
    srv = importlib.import_module("server")
    el = _el()
    facts = _facts(("a", "x"), ("b", "y"))
    emap = el.build_evidence_map(facts)
    labelled = srv._build_system_prompt(facts, evidence_map=emap)
    plain = srv._build_system_prompt(facts)
    assert labelled.count(el.PROMPT_INSTRUCTION) == 1 and el.PROMPT_INSTRUCTION not in plain
    assert "- [ev_1] [src:t | conf=0.90] x" in labelled and "[ev_" not in plain


# ── lifecycle: the map is published only for an answer the model produced ────

def _assert_nothing_published(resp, lifecycle):
    assert resp.evidence_lifecycle == lifecycle
    assert resp.evidence_labels is None and resp.reference_check is None


@pytest.mark.asyncio
async def test_lifecycle_disabled_by_default(monkeypatch):
    srv, _, traces = _harness(monkeypatch, FACTS, answer="ответ")
    resp = await srv.query(srv.QueryRequest(query="q", use_llm=True))
    _assert_nothing_published(resp, "disabled")
    assert "evidence_lifecycle" not in traces[-1]["metadata"]            # the default trace is unchanged


@pytest.mark.asyncio
async def test_lifecycle_published_after_a_successful_answer(monkeypatch):
    srv, _, traces = _harness(monkeypatch, FACTS, answer="Так [ev_1].")
    resp = await srv.query(srv.QueryRequest(query="q", use_llm=True, evidence_labels=True))
    assert resp.evidence_lifecycle == "published"
    assert resp.evidence_labels and resp.reference_check["valid"] == ["ev_1"]
    meta = traces[-1]["metadata"]
    assert meta["evidence_lifecycle"] == "published"
    assert meta["evidence_labels"] == resp.evidence_labels and meta["reference_check"] == resp.reference_check


@pytest.mark.asyncio
@pytest.mark.parametrize("answer", ["", "   ", "(пустой ответ Gemini)"])
async def test_empty_or_gemini_stub_answer_does_not_publish_the_map(monkeypatch, answer):
    # published means the model produced answer text. An empty string, whitespace, or Titan's
    # Gemini-empty placeholder is not that: the map would look like a successful answer.
    # Reference checking is not run (it is existence-only and would just look like "no citations").
    srv, prompts, traces = _harness(monkeypatch, FACTS, answer=answer)
    resp = await srv.query(srv.QueryRequest(query="q", use_llm=True, evidence_labels=True))
    assert prompts  # the provider was called
    assert (resp.llm_answer or "") == answer
    _assert_nothing_published(resp, "no_answer")
    meta = traces[-1]["metadata"]
    assert meta["evidence_lifecycle"] == "no_answer"
    assert "evidence_labels" not in meta and "reference_check" not in meta


@pytest.mark.asyncio
async def test_no_map_when_the_model_is_not_called(monkeypatch):
    srv, prompts, traces = _harness(monkeypatch, FACTS, answer="не будет вызвана")
    resp = await srv.query(srv.QueryRequest(query="q", use_llm=False, evidence_labels=True))
    _assert_nothing_published(resp, "model_not_called")
    assert prompts == []
    assert "evidence_labels" not in traces[-1]["metadata"]
    assert traces[-1]["metadata"]["evidence_lifecycle"] == "model_not_called"


@pytest.mark.asyncio
async def test_no_map_when_the_truth_policy_blocks_the_model(monkeypatch):
    srv, prompts, traces = _harness(monkeypatch, FACTS, answer="не будет вызвана", blocks_llm=True)
    resp = await srv.query(srv.QueryRequest(query="q", use_llm=True, evidence_labels=True))
    _assert_nothing_published(resp, "model_not_called")
    assert prompts == [] and "evidence_labels" not in traces[-1]["metadata"]


@pytest.mark.asyncio
async def test_no_map_when_the_model_fails(monkeypatch):
    srv, prompts, traces = _harness(monkeypatch, FACTS, answer=RuntimeError("provider down"))
    resp = await srv.query(srv.QueryRequest(query="q", use_llm=True, evidence_labels=True))
    _assert_nothing_published(resp, "model_failed")
    assert prompts and "LLM error" in resp.llm_answer                    # the call was attempted
    meta = traces[-1]["metadata"]
    assert meta["evidence_lifecycle"] == "model_failed" and "evidence_labels" not in meta and "reference_check" not in meta


@pytest.mark.asyncio
async def test_no_map_when_the_prompt_is_rejected_before_sending(monkeypatch):
    # The mandatory instructions alone do not fit the configured limit: nothing is sent.
    monkeypatch.setenv("DEEPSEEK_MESSAGE_CHAR_LIMIT", "50")
    srv, prompts, traces = _harness(monkeypatch, FACTS, answer="не будет вызвана", provider="deepseek")
    resp = await srv.query(srv.QueryRequest(query="q", use_llm=True, evidence_labels=True))
    _assert_nothing_published(resp, "prompt_rejected")
    assert prompts == [] and "evidence_labels" not in traces[-1]["metadata"]


def _assert_report_without_secrets(report, *, limit=None, total=None):
    assert report is not None
    if limit is not None:
        assert report["message_char_limit"] == limit
        assert report["message_char_limit_setting"] == "DEEPSEEK_MESSAGE_CHAR_LIMIT"
    if total is not None:
        assert report["memory_records_total"] == total
    blob = str(report)
    assert "synthetic-valid-key" not in blob
    assert "sk-" not in blob


@pytest.mark.asyncio
@pytest.mark.parametrize("opt_in", [False, True])
async def test_context_report_survives_when_system_prompt_does_not_fit(monkeypatch, opt_in):
    # Mandatory instructions alone exceed the limit. The provider must not be called, the
    # citation map must not be published, and the report must still be returned (labels on
    # or off). The report is created before prompt assembly so a limit error cannot drop it.
    monkeypatch.setenv("DEEPSEEK_MESSAGE_CHAR_LIMIT", "50")
    srv, prompts, traces = _harness(monkeypatch, FACTS, answer="не будет вызвана", provider="deepseek")
    resp = await srv.query(srv.QueryRequest(query="q", use_llm=True, evidence_labels=opt_in))

    assert prompts == []
    assert resp.llm_answer.startswith("[LLM error: llm_context_limit")
    assert "mandatory system instructions" in resp.llm_answer
    assert "current question" not in resp.llm_answer
    assert "synthetic-valid-key" not in (resp.llm_answer or "")
    assert resp.llm_meta and "synthetic-valid-key" not in str(resp.llm_meta)
    _assert_report_without_secrets(resp.context_report, limit=50, total=len(FACTS))
    if opt_in:
        _assert_nothing_published(resp, "prompt_rejected")
        assert traces[-1]["metadata"]["evidence_lifecycle"] == "prompt_rejected"
        assert "evidence_labels" not in traces[-1]["metadata"]
    else:
        _assert_nothing_published(resp, "disabled")


@pytest.mark.asyncio
@pytest.mark.parametrize("opt_in", [False, True])
async def test_context_report_survives_when_the_question_itself_does_not_fit(monkeypatch, opt_in):
    # The limit is chosen so the system prompt (records + instructions) fits, and the
    # current question does not. Refusal reason must name the question, not the system
    # prompt; the report describes the records that would have been sent.
    # QueryRequest.query is capped at 2000 characters. 1800 leaves room for the
    # records, label/lens instructions and the remote sanitizer prefix, while
    # the 1950-character question is still over the limit.
    limit = 1800
    query = "Q" * 1950
    monkeypatch.setenv("DEEPSEEK_MESSAGE_CHAR_LIMIT", str(limit))
    srv, prompts, traces = _harness(monkeypatch, FACTS, answer="не будет вызвана", provider="deepseek")
    resp = await srv.query(srv.QueryRequest(query=query, use_llm=True, evidence_labels=opt_in))

    assert prompts == []
    assert resp.llm_answer.startswith("[LLM error: llm_context_limit")
    assert "current question" in resp.llm_answer
    assert "mandatory system instructions" not in resp.llm_answer
    assert "synthetic-valid-key" not in (resp.llm_answer or "")
    assert resp.llm_meta and "synthetic-valid-key" not in str(resp.llm_meta)
    report = resp.context_report
    _assert_report_without_secrets(report, limit=limit, total=len(FACTS))
    assert report["memory_records_sent"] == len(FACTS)
    assert report["memory_records_omitted"] == []
    if opt_in:
        _assert_nothing_published(resp, "prompt_rejected")
        assert traces[-1]["metadata"].get("evidence_lifecycle") == "prompt_rejected"
        assert "evidence_labels" not in traces[-1]["metadata"]
    else:
        _assert_nothing_published(resp, "disabled")


@pytest.mark.asyncio
async def test_context_report_survives_a_second_pass_build_error(monkeypatch):
    # Pass 2 (renumber labels for the records that fit) is coded to raise the same
    # limit error, but the production second prompt is not longer than the first:
    # labels only shrink or stay, and the empty-map instruction is shorter. This
    # test forces the second pass to fail to lock the report-preserving contract.
    from core.llm_context_budget import LlmContextLimitError

    facts = _facts(("small-1", "короткая запись один"), ("huge", "Ж" * 6000), ("small-2", "короткая запись два"))
    monkeypatch.setenv("DEEPSEEK_MESSAGE_CHAR_LIMIT", "4000")
    srv, prompts, traces = _harness(monkeypatch, facts, answer="не будет вызвана", provider="deepseek")
    real_build = srv._build_system_prompt

    def flaky(*args, **kwargs):
        if kwargs.get("selected_positions") is not None:
            raise LlmContextLimitError(
                setting="DEEPSEEK_MESSAGE_CHAR_LIMIT",
                limit=4000,
                role="system",
                length=4001,
                part="mandatory system instructions",
            )
        return real_build(*args, **kwargs)

    monkeypatch.setattr(srv, "_build_system_prompt", flaky)
    resp = await srv.query(srv.QueryRequest(query="q", use_llm=True, evidence_labels=True))

    assert prompts == []
    _assert_nothing_published(resp, "prompt_rejected")
    assert "evidence_labels" not in traces[-1]["metadata"]
    report = resp.context_report
    _assert_report_without_secrets(report, limit=4000, total=3)
    # Pass 1 already selected what would have been sent; that data must not be discarded.
    assert report["memory_records_sent"] == 2
    assert [item["fact_id"] for item in report["memory_records_omitted"]] == ["huge"]
    assert resp.llm_answer.startswith("[LLM error: llm_context_limit")
    assert "synthetic-valid-key" not in (resp.llm_answer or "")


@pytest.mark.asyncio
@pytest.mark.parametrize("opt_in", [False, True])
async def test_the_published_invariant_holds_in_every_scenario(monkeypatch, opt_in):
    # Whatever happened, a map in the response means: the model answered, and this is the map of
    # what it was sent.
    scenarios = [
        dict(kwargs={"use_llm": False}, answer="x"),
        dict(kwargs={"use_llm": True}, answer=RuntimeError("down")),
        dict(kwargs={"use_llm": True}, answer="ok [ev_1]"),
    ]
    for scenario in scenarios:
        srv, _, _ = _harness(monkeypatch, FACTS, answer=scenario["answer"])
        resp = await srv.query(srv.QueryRequest(query="q", evidence_labels=opt_in, **scenario["kwargs"]))
        if resp.evidence_lifecycle == "published":
            assert resp.evidence_labels is not None and resp.reference_check is not None
        else:
            assert resp.evidence_labels is None and resp.reference_check is None


# ── look-alike forms ─────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "text",
    ["［ev_1］", "[ｅｖ_１]", "[ev＿1]", "［ｅｖ＿１］", "[ 　ev_1]", "(ｅｖ_１)"],
)
def test_compatibility_forms_of_a_label_are_neutralized_in_the_prompt_and_reported_by_the_check(text):
    el = _el()
    emap = el.build_evidence_map(_facts(("a", "x")))
    res = el.check_references(text, emap)
    assert res["valid"] == [] and res["unknown"] == []                  # not a reference ...
    assert res["malformed"], text                                       # ... and not silent
    if "[" in text or "［" in text:
        cleaned = el.neutralize_label_like_text(text)
        assert not el._LABEL_RE.search(el._fold(cleaned)), cleaned         # not a label, even after folding
        assert el.neutralize_label_like_text(cleaned) == cleaned           # and neutralizing again changes nothing


def test_neutralization_keeps_surrounding_text_and_length_of_unrelated_parts():
    el = _el()
    assert el.neutralize_label_like_text("до ［ｅｖ＿１］ после [ev_2] конец") == "до [ ev_１］ после [ ev_2] конец"
    assert el.neutralize_label_like_text("обычный ｔｅｘｔ ｅｖ без скобок") == "обычный ｔｅｘｔ ｅｖ без скобок"


# ── what the prompt shows is what identifies the record ──────────────────────

def test_a_different_confidence_is_a_different_presented_record():
    el = _el()
    a = {"fact_id": "L", "claim": "ready", "source": "s", "confidence": 0.9}
    b = {"fact_id": "L", "claim": "ready", "source": "s", "confidence": 0.5}
    emap = el.build_evidence_map([a, b])
    assert emap.to_dict() == {"ev_1": "L", "ev_2": "L"} and emap.ambiguous == frozenset({"ev_1", "ev_2"})
    same = el.build_evidence_map([a, dict(a)])
    assert same.to_dict() == {"ev_1": "L"} and not same.ambiguous


def test_the_empty_instruction_is_not_longer_than_the_labelled_one():
    # The size-limit selection reserves room for the labelled instruction; the empty-map text may
    # replace it only if it is not longer.
    el = _el()
    assert len(el.PROMPT_EMPTY_INSTRUCTION) < len(el.PROMPT_INSTRUCTION)
    assert not el._LABEL_RE.search(el.PROMPT_EMPTY_INSTRUCTION)


def test_unit_separator_in_claim_or_source_does_not_alias_records():
    el = _el()
    facts = [
        {"fact_id": "same", "claim": "a\x1fb", "source": "c", "confidence": 0.9},
        {"fact_id": "same", "claim": "a", "source": "b\x1fc", "confidence": 0.9},
    ]

    emap = el.build_evidence_map(facts)

    assert el.record_fingerprint(facts[0]) != el.record_fingerprint(facts[1])
    assert emap.to_dict() == {"ev_1": "same", "ev_2": "same"}
    assert emap.ambiguous == frozenset({"ev_1", "ev_2"})
    assert [emap.label_for_fact(fact) for fact in facts] == ["ev_1", "ev_2"]
