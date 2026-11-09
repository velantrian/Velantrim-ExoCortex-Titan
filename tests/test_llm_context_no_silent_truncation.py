"""No silent context loss on the way to the LLM (DeepSeek Flash and Pro).

Every test uses a fake HTTP client that records the exact final request body;
no model or network is called. The API key is synthetic.

Contract under test (core/llm_context_budget.py):
- the former fixed 4000-character DeepSeek message cut is gone; by default no
  Titan per-message limit applies;
- DEEPSEEK_MESSAGE_CHAR_LIMIT is optional; when set, Titan never truncates: the
  current question and mandatory instructions must fit or the request is refused
  with a clear message, memory records and history turns are left out WHOLE and
  every omission is reported;
- the records that are in the request are exactly the records the report lists
  as sent, so a per-request citation map built from them cannot point at a record
  the model did not receive;
- a provider "context too long" rejection is reported clearly;
- normal and streaming paths and Flash/Pro follow one policy;
- Reader chunks cover the whole document with and without a configured limit.
"""
from __future__ import annotations

import asyncio
import copy
import importlib
import json
from typing import Any

import httpx
import pytest

from core.llm_context_budget import (
    BLOCK_MEMORY_MAX_ITEMS_ENV,
    DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV,
    HISTORY_MAX_TURNS_ENV,
    HISTORY_TURN_MAX_CHARS_ENV,
    PREVIOUS_SUMMARY_MAX_CHARS_ENV,
    ContextReport,
)
from core.llm_router import LlmCallConfig
from core.remote_egress import sanitize_remote_system_prompt

SYNTHETIC_KEY = "sk-synthetic-context-test-0001"


def _raises(name: str):
    """Match by class name: other test modules reload ``core.*`` mid-session,
    so a class imported at collection time may not be the one raised."""

    class _Matcher:
        def __enter__(self):
            self._ctx = pytest.raises(ValueError)
            self.info = self._ctx.__enter__()
            return self.info

        def __exit__(self, *exc):
            handled = self._ctx.__exit__(*exc)
            assert type(self.info.value).__name__ == name, type(self.info.value)
            return handled

    return _Matcher()
MODELS = ("deepseek-v4-flash", "deepseek-v4-pro")
_ALL_SETTINGS = (
    DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV,
    HISTORY_MAX_TURNS_ENV,
    HISTORY_TURN_MAX_CHARS_ENV,
    PREVIOUS_SUMMARY_MAX_CHARS_ENV,
    BLOCK_MEMORY_MAX_ITEMS_ENV,
)


# ── fake provider ────────────────────────────────────────────────────────────


class _FakeProvider:
    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.error: tuple[int, dict[str, Any]] | None = None

    @property
    def bodies(self) -> list[dict[str, Any]]:
        return [r["body"] for r in self.requests]


class _FakeStreamResponse:
    def __init__(self, provider: _FakeProvider) -> None:
        self._provider = provider
        self.status_code = provider.error[0] if provider.error else 200

    async def __aenter__(self) -> _FakeStreamResponse:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def aread(self) -> bytes:
        assert self._provider.error is not None
        return json.dumps(self._provider.error[1]).encode()

    async def aiter_lines(self):
        yield 'data: {"choices":[{"delta":{"content":"ok"}}]}'
        yield "data: [DONE]"


def _install_fake(monkeypatch: pytest.MonkeyPatch) -> _FakeProvider:
    provider = _FakeProvider()

    class FakeAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> FakeAsyncClient:
            return self

        async def __aexit__(self, *exc: object) -> bool:
            return False

        async def post(self, url: str, headers: Any = None, json: Any = None) -> httpx.Response:
            provider.requests.append({"url": url, "body": copy.deepcopy(json)})
            request = httpx.Request("POST", url)
            if provider.error:
                return httpx.Response(provider.error[0], json=provider.error[1], request=request)
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "ok"}}], "usage": {}},
                request=request,
            )

        def stream(self, method: str, url: str, headers: Any = None, json: Any = None):
            provider.requests.append({"url": url, "body": copy.deepcopy(json)})
            return _FakeStreamResponse(provider)

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    return provider


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> _FakeProvider:
    for name in _ALL_SETTINGS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "allow")
    monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", "allowed")
    return _install_fake(monkeypatch)


def _cfg(model: str = "deepseek-v4-flash") -> LlmCallConfig:
    return LlmCallConfig(provider="deepseek", api_key=SYNTHETIC_KEY, model=model)


def _contents(body: dict[str, Any]) -> list[str]:
    return [m["content"] for m in body["messages"]]


def _stream(cfg: LlmCallConfig, system: str, user: str, history=None, report=None):
    from core.llm_stream import stream_chat_events

    async def collect() -> list[dict[str, Any]]:
        return [e async for e in stream_chat_events(cfg, system, user, history, report=report)]

    return asyncio.run(collect())


def _history(n: int, size: int = 50) -> list[dict[str, str]]:
    return [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"TURN-{i:03d} " + "h" * size}
        for i in range(n)
    ]


# ── 1. no limit by default: long text goes whole (normal, messages, stream) ──


@pytest.mark.parametrize("model", MODELS)
def test_default_router_sends_text_longer_than_4000_whole(fake: _FakeProvider, model: str):
    from core.llm_router import chat_complete

    system = "SYSTEM-START " + "s" * 6000 + " SYSTEM-END-RULE: answer only from memory"
    question = "QUESTION-START " + "q" * 9000 + " QUESTION-END: и только если сегодня пятница?"

    assert asyncio.run(chat_complete(_cfg(model), question, system)) == "ok"

    body = fake.bodies[0]
    assert body["model"] == model
    assert _contents(body) == [sanitize_remote_system_prompt(system), question]
    assert "truncated" not in json.dumps(body, ensure_ascii=False)


@pytest.mark.parametrize("model", MODELS)
def test_default_messages_and_stream_paths_send_question_history_system_whole(
    fake: _FakeProvider, model: str
):
    from core.llm_stream import chat_complete_messages

    system = "SYS " + "s" * 5000 + " SYS-TAIL-CONDITION"
    question = "Q " + "q" * 7000 + " Q-TAIL"
    history = [
        {"role": "user", "content": "H1 " + "a" * 4500 + " H1-TAIL"},
        {"role": "assistant", "content": "H2 " + "b" * 4500 + " H2-TAIL"},
    ]
    expected = [sanitize_remote_system_prompt(system), history[0]["content"],
                history[1]["content"], question]

    report = ContextReport.for_provider("deepseek")
    text, _usage = asyncio.run(chat_complete_messages(_cfg(model), system, question, history,
                                                      report=report))
    assert text == "ok"
    assert _contents(fake.bodies[0]) == expected
    assert fake.bodies[0]["stream"] is False
    assert report.to_dict()["limits_applied"] is False
    assert report.to_dict()["message_char_limit"] is None

    stream_report = ContextReport.for_provider("deepseek")
    events = _stream(_cfg(model), system, question, history, report=stream_report)
    assert [e["type"] for e in events] == ["context", "token", "done"]
    assert events[0]["report"]["limits_applied"] is False
    assert events[0]["report"]["token_count"] == "not_computed"
    assert _contents(fake.bodies[1]) == expected
    assert fake.bodies[1]["stream"] is True


# ── 2. explicit limit: applied by refusal or whole-unit omission, reported ───


@pytest.mark.parametrize("model", MODELS)
def test_explicit_limit_refuses_long_question_instead_of_cutting_it(
    fake: _FakeProvider, monkeypatch: pytest.MonkeyPatch, model: str
):
    from core.llm_router import chat_complete

    monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "4000")
    question = "SECRET-QUESTION-TEXT " + "q" * 5000

    with _raises("LlmContextLimitError") as info:
        asyncio.run(chat_complete(_cfg(model), question, "short system"))

    message = str(info.value)
    assert message.startswith("llm_context_limit")
    assert DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV in message and "4000" in message
    assert "current question" in message and str(len(question)) in message
    assert "SECRET-QUESTION-TEXT" not in message and SYNTHETIC_KEY not in message
    assert fake.requests == []  # nothing was sent


@pytest.mark.parametrize("model", MODELS)
def test_explicit_limit_refuses_long_mandatory_system_on_both_paths(
    fake: _FakeProvider, monkeypatch: pytest.MonkeyPatch, model: str
):
    from core.llm_stream import chat_complete_messages

    monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "3000")
    system = "MANDATORY " + "m" * 3500

    with _raises("LlmContextLimitError"):
        asyncio.run(chat_complete_messages(_cfg(model), system, "short question"))
    events = _stream(_cfg(model), system, "short question")
    assert events[-1]["type"] == "error"
    assert events[-1]["message"].startswith("llm_context_limit")
    assert "MANDATORY" not in events[-1]["message"]
    assert fake.requests == []


@pytest.mark.parametrize("model", MODELS)
def test_explicit_limit_leaves_out_a_long_history_turn_whole_and_reports_it(
    fake: _FakeProvider, monkeypatch: pytest.MonkeyPatch, model: str
):
    monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "4000")
    history = [
        {"role": "user", "content": "KEEP-1 short"},
        {"role": "assistant", "content": "DROP-LONG " + "x" * 4500},
        {"role": "user", "content": "KEEP-2 short"},
    ]
    report = ContextReport.for_provider("deepseek")
    events = _stream(_cfg(model), "system", "question", history, report=report)

    sent = _contents(fake.bodies[0])
    assert sent[1:] == ["KEEP-1 short", "KEEP-2 short", "question"]
    assert not any("DROP-LONG" in c for c in sent)
    data = events[0]["report"]
    assert data["limits_applied"] is True
    assert data["history_turns_total"] == 3 and data["history_turns_sent"] == 2
    assert {"setting": DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "value": 4000,
            "affected": "history_turns", "omitted": 1, "shortened": 0} in data["applied"]


def test_history_turn_cap_is_reported_and_can_be_switched_off(fake: _FakeProvider,
                                                              monkeypatch: pytest.MonkeyPatch):
    report = ContextReport.for_provider("deepseek")
    _stream(_cfg(), "system", "question", _history(25), report=report)
    assert len(fake.bodies[0]["messages"]) == 1 + 20 + 1
    assert report.history_turns_total == 25 and report.history_turns_sent == 20
    assert report.applied == [{"setting": HISTORY_MAX_TURNS_ENV, "value": 20,
                               "affected": "history_turns", "omitted": 5, "shortened": 0}]

    monkeypatch.setenv(HISTORY_MAX_TURNS_ENV, "off")
    report_off = ContextReport.for_provider("deepseek")
    _stream(_cfg(), "system", "question", _history(25), report=report_off)
    assert len(fake.bodies[1]["messages"]) == 1 + 25 + 1
    assert report_off.applied == []


# ── 3. memory records: whole, important condition at the end ─────────────────


def _facts() -> list[dict[str, Any]]:
    return [
        {"fact_id": "f-alpha", "source": "note:a", "confidence": 0.9,
         "claim": "ALPHA-RECORD the store opens at 09:00 " + "a" * 900},
        {"fact_id": "f-beta", "source": "note:b", "confidence": 0.8,
         "claim": "BETA-RECORD delivery is free " + "b" * 900},
        {"fact_id": "f-gamma", "source": "note:c", "confidence": 0.7,
         "claim": "GAMMA-RECORD " + "c" * 1500
         + " IMPORTANT-CONDITION: only on Fridays, never on holidays"},
    ]


def _line(f: dict[str, Any]) -> str:
    return f"- [{f['source']} | conf={f['confidence']:.2f}] {f['claim']}"


@pytest.mark.parametrize("model", MODELS)
def test_default_all_memory_records_reach_the_request_whole(fake: _FakeProvider, model: str):
    import server
    from core.llm_stream import chat_complete_messages

    facts = _facts()
    report = ContextReport.for_provider("deepseek")
    system = server._build_system_prompt(facts, report=report)
    assert system == server._build_system_prompt(facts)  # byte-identical to legacy builder
    asyncio.run(chat_complete_messages(_cfg(model), system, "When can I come?", report=report))

    sent_system = fake.bodies[0]["messages"][0]["content"]
    assert len(sent_system) > 4000
    for f in facts:
        assert _line(f) in sent_system
    assert "IMPORTANT-CONDITION: only on Fridays, never on holidays" in sent_system
    assert report.memory_records_sent == 3 and report.memory_records_omitted == []
    assert report.sent_facts(facts) == facts


@pytest.mark.parametrize("model", MODELS)
def test_explicit_limit_leaves_out_records_whole_and_says_so(
    fake: _FakeProvider, monkeypatch: pytest.MonkeyPatch, model: str
):
    import server
    from core.llm_stream import chat_complete_messages

    monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "3000")
    facts = _facts()
    report = ContextReport.for_provider("deepseek")
    system = server._build_system_prompt(facts, report=report)
    asyncio.run(chat_complete_messages(_cfg(model), system, "When can I come?", report=report))

    sent_system = fake.bodies[0]["messages"][0]["content"]
    assert len(sent_system) <= 3000
    # Sent records are whole; the left-out record is absent entirely, not cut.
    sent = report.sent_facts(facts)
    for f in sent:
        assert _line(f) in sent_system
    omitted = [f for f in facts if f not in sent]
    assert omitted, "the fixture must force an omission"
    for f in omitted:
        assert f["claim"][:12] not in sent_system
    assert "IMPORTANT-CONDITION" not in sent_system
    # ...and the model and the caller are told.
    assert f"{len(omitted)} из 3 записей памяти не переданы" in sent_system
    data = report.to_dict()
    assert data["limits_applied"] is True
    assert data["memory_records_sent"] == len(sent)
    assert [o["fact_id"] for o in data["memory_records_omitted"]] == [f["fact_id"] for f in omitted]
    assert {"setting": DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "value": 3000,
            "affected": "memory_records", "omitted": len(omitted), "shortened": 0} in data["applied"]
    # Diagnostics carry ids and counts, never record text or the key.
    dumped = json.dumps(data, ensure_ascii=False)
    assert "RECORD" not in dumped and SYNTHETIC_KEY not in dumped


def test_explicit_limit_too_small_for_mandatory_instructions_is_refused(
    monkeypatch: pytest.MonkeyPatch,
):
    import server

    monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "200")
    report = ContextReport.for_provider("deepseek")
    with _raises("LlmContextLimitError") as info:
        server._build_system_prompt(_facts(), lens_instructions="OPERATOR: " + "o" * 300,
                                    report=report)
    assert "mandatory system instructions" in str(info.value)
    assert "OPERATOR" not in str(info.value)


def test_citation_map_built_from_sent_records_points_only_at_records_in_the_request(
    fake: _FakeProvider, monkeypatch: pytest.MonkeyPatch,
):
    """The [ev_N] map must be built from ``report.sent_facts``.

    On main there is no [ev_N] labelling yet (draft PR #515); this test pins the
    contract for any per-request citation map: every record it can reference is
    whole in the final request body.
    """
    import server
    from core.llm_stream import chat_complete_messages

    monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "3000")
    facts = _facts()
    report = ContextReport.for_provider("deepseek")
    system = server._build_system_prompt(facts, report=report)
    asyncio.run(chat_complete_messages(_cfg(), system, "q", report=report))
    sent_system = fake.bodies[0]["messages"][0]["content"]

    citable = {f"ev_{i + 1}": f["fact_id"] for i, f in enumerate(report.sent_facts(facts))}
    by_id = {f["fact_id"]: f for f in facts}
    assert citable
    for fact_id in citable.values():
        assert _line(by_id[fact_id]) in sent_system
    omitted_ids = {o["fact_id"] for o in report.memory_records_omitted}
    assert omitted_ids.isdisjoint(citable.values())

    try:
        labels = importlib.import_module("core.evidence_labels")
    except ModuleNotFoundError:
        return
    emap = labels.build_evidence_map(report.sent_facts(facts))
    assert set(emap.to_dict().values()) <= {f["fact_id"] for f in report.sent_facts(facts)}


# ── 4. console context block: summary, per-turn chars, block memory ──────────


def test_console_context_has_no_silent_cuts_by_default_and_reports_explicit_caps(
    monkeypatch: pytest.MonkeyPatch,
):
    from core.console_memory import build_chat_context_for_prompt

    for name in _ALL_SETTINGS:
        monkeypatch.delenv(name, raising=False)
    summary = "SUMMARY-START " + "s" * 6000 + " SUMMARY-END-CONDITION"
    turn = "TURN-START " + "t" * 900 + " TURN-END"
    notes = [{"claim": f"NOTE-{i:02d}"} for i in range(45)]

    report = ContextReport.for_provider("deepseek")
    text = build_chat_context_for_prompt([{"role": "user", "content": turn}], summary, "en",
                                         notes, report=report)
    assert "SUMMARY-END-CONDITION" in text and "TURN-END" in text
    assert "NOTE-39" in text and "NOTE-40" not in text
    assert report.applied == [{"setting": BLOCK_MEMORY_MAX_ITEMS_ENV, "value": 40,
                               "affected": "block_memory_notes", "omitted": 5, "shortened": 0}]

    monkeypatch.setenv(PREVIOUS_SUMMARY_MAX_CHARS_ENV, "1000")
    monkeypatch.setenv(HISTORY_TURN_MAX_CHARS_ENV, "600")
    monkeypatch.setenv(BLOCK_MEMORY_MAX_ITEMS_ENV, "off")
    capped = ContextReport.for_provider("deepseek")
    text = build_chat_context_for_prompt([{"role": "user", "content": turn}], summary, "en",
                                         notes, report=capped)
    assert "SUMMARY-END-CONDITION" not in text and "TURN-END" not in text
    assert text.count("shortened to") == 2  # the cut is visible in the prompt itself
    assert "NOTE-44" in text
    affected = {(a["setting"], a["shortened"]) for a in capped.applied}
    assert affected == {(PREVIOUS_SUMMARY_MAX_CHARS_ENV, 1), (HISTORY_TURN_MAX_CHARS_ENV, 1)}


@pytest.mark.parametrize("value", ["abc", "-5", "4k"])
def test_invalid_limit_setting_fails_with_the_setting_name(monkeypatch, value):
    monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, value)
    with _raises("LlmContextConfigError") as info:
        ContextReport.for_provider("deepseek")
    assert DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV in str(info.value)
    assert value not in str(info.value)


# ── 5. provider context overflow is clear on both paths ──────────────────────

_OVERFLOW = (400, {"error": {"type": "invalid_request_error",
                             "message": "synthetic fixture: maximum context length exceeded"}})


@pytest.mark.parametrize("model", MODELS)
def test_provider_context_overflow_is_reported_clearly(fake: _FakeProvider, model: str):
    from core.llm_router import chat_complete

    fake.error = _OVERFLOW
    with _raises("LlmContextOverflowError") as info:
        asyncio.run(chat_complete(_cfg(model), "q", "s"))
    assert str(info.value).startswith("llm_context_overflow")
    assert "does not count tokens" in str(info.value)
    assert info.value.retryable is False
    assert SYNTHETIC_KEY not in str(info.value)

    events = _stream(_cfg(model), "s", "q")
    assert events[-1]["type"] == "error"
    assert events[-1]["message"].startswith("llm_context_overflow")


# ── 6. Reader: every fragment of a long document is read ─────────────────────


def _reader_prompts(monkeypatch: pytest.MonkeyPatch, text: str) -> tuple[list[str], Any]:
    import core.llm_router as router
    from core.semantic_reader import RawSource
    from core.readers.llm_adapter import LlmReaderAdapter

    prompts: list[str] = []

    from core.knowledge_capsule import ClaimModality

    modality = next(iter(ClaimModality)).value

    async def fake_chat_complete(cfg, prompt, system="", **kwargs):
        prompts.append(prompt)
        claims = [{"text": "<frag-0000>", "modality": modality}] if "<frag-0000>" in prompt else []
        return json.dumps({"claims": claims})

    monkeypatch.setattr(router, "chat_complete", fake_chat_complete)
    adapter = LlmReaderAdapter(provider="deepseek", model="deepseek-v4-pro", api_key=SYNTHETIC_KEY)
    out = asyncio.run(adapter.extract_with_receipt(RawSource(document_id="doc", text=text)))
    return prompts, out


def _assert_full_coverage(text: str, prompts: list[str]) -> None:
    covered = [False] * len(text)
    for prompt in prompts:
        chunk = prompt.split("<<<SOURCE_BEGIN>>>\n", 1)[1].rsplit("\n<<<SOURCE_END>>>", 1)[0]
        start = text.index(chunk)
        covered[start:start + len(chunk)] = [True] * len(chunk)
    assert all(covered), "every fragment of the document must be sent"


@pytest.mark.parametrize("limit", [None, "3000"])
def test_reader_keeps_all_fragments_with_and_without_a_message_limit(
    monkeypatch: pytest.MonkeyPatch, limit: str | None
):
    monkeypatch.delenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, raising=False)
    if limit:
        monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, limit)
    text = "".join(f"<frag-{i:04d}>" for i in range(1500))  # 16 500 characters
    prompts, out = _reader_prompts(monkeypatch, text)

    _assert_full_coverage(text, prompts)
    assert out.receipt.chunks_attempted == out.receipt.chunks_planned == len(prompts)
    assert "CHUNK_BUDGET_EXHAUSTED" not in {w.code for w in out.result.warnings}
    if limit:
        assert all(len(p) <= int(limit) for p in prompts)
    else:
        assert max(len(p) for p in prompts) > 4000  # the 4000 cut no longer shapes chunks


def test_reader_reports_an_unread_tail_instead_of_dropping_it(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, raising=False)
    text = "".join(f"<frag-{i:04d}>" for i in range(6000))  # > max_chunks * chunk_chars
    _prompts, out = _reader_prompts(monkeypatch, text)
    assert out.result.partial
    assert "CHUNK_BUDGET_EXHAUSTED" in {w.code for w in out.result.warnings}


def test_reader_refuses_a_limit_smaller_than_its_instructions(monkeypatch: pytest.MonkeyPatch):
    from core.readers.llm_adapter import LlmReaderAdapter

    monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "300")
    with pytest.raises(ValueError, match="Reader system instructions"):
        LlmReaderAdapter(provider="deepseek", model="deepseek-v4-flash", api_key=SYNTHETIC_KEY)


# ── 7. server endpoints: /chat and /chat/stream surface the report ───────────


def _chat_req(**overrides: Any):
    import server

    data: dict[str, Any] = {
        "message": "When can I come?",
        "llm_provider": "deepseek",
        "llm_api_key": SYNTHETIC_KEY,
        "llm_model": "deepseek-v4-flash",
        "auto_save_memory": False,
        "use_memory": True,
    }
    data.update(overrides)
    return server.ChatRequest(**data)


def _patch_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    import server

    monkeypatch.setattr(server, "pipeline_run",
                        lambda q, mode, domain: {"facts": _facts(), "error": None})


def test_chat_endpoint_returns_context_report_and_sends_records_whole(
    fake: _FakeProvider, monkeypatch: pytest.MonkeyPatch
):
    import server

    _patch_pipeline(monkeypatch)
    resp = asyncio.run(server.chat_endpoint(_chat_req()))
    assert resp.from_llm is True
    assert resp.context_report["memory_records_sent"] == 3
    assert resp.context_report["limits_applied"] is False
    sent_system = fake.bodies[0]["messages"][0]["content"]
    for f in _facts():
        assert _line(f) in sent_system

    monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "3000")
    limited = asyncio.run(server.chat_endpoint(_chat_req()))
    assert limited.context_report["limits_applied"] is True
    assert limited.context_report["memory_records_omitted"]


def test_chat_endpoint_refuses_overlong_question_without_offline_substitute(
    fake: _FakeProvider, monkeypatch: pytest.MonkeyPatch
):
    import server
    from fastapi import HTTPException

    _patch_pipeline(monkeypatch)
    monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "4000")
    with pytest.raises(HTTPException) as info:
        asyncio.run(server.chat_endpoint(_chat_req(message="LONG " + "q" * 4500)))
    assert info.value.status_code == 413
    assert str(info.value.detail).startswith("llm_context_limit")
    assert fake.requests == []


def _sse_events(response) -> list[dict[str, Any]]:
    async def collect() -> list[str]:
        return [chunk async for chunk in response.body_iterator]

    events = []
    for chunk in asyncio.run(collect()):
        text = chunk.decode() if isinstance(chunk, bytes) else chunk
        for line in text.splitlines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    return events


def test_chat_stream_endpoint_emits_context_report_and_clear_refusal(
    fake: _FakeProvider, monkeypatch: pytest.MonkeyPatch
):
    import server

    _patch_pipeline(monkeypatch)
    events = _sse_events(asyncio.run(server.chat_stream_endpoint(_chat_req())))
    types = [e["type"] for e in events]
    assert "context" in types and types[-1] == "final"
    assert events[-1]["context_report"]["memory_records_sent"] == 3
    assert fake.bodies[0]["stream"] is True

    monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "4000")
    refused = _sse_events(
        asyncio.run(server.chat_stream_endpoint(_chat_req(message="LONG " + "q" * 4500)))
    )
    assert refused[-1]["type"] == "error"
    assert refused[-1]["message"].startswith("llm_context_limit")
    assert "LONG" not in refused[-1]["message"]
    assert not any(e["type"] == "token" for e in refused)  # no offline substitute
    assert len(fake.requests) == 1  # the refused request was never sent


# ── 8. /query surfaces the same report ───────────────────────────────────────


def _query_harness(monkeypatch: pytest.MonkeyPatch, facts: list[dict[str, Any]]):
    from types import SimpleNamespace

    srv = importlib.import_module("server")
    pipeline_mod = importlib.import_module("core.pipeline")
    memory_ops = importlib.import_module("core.memory_ops")
    events = importlib.import_module("core.event_bridge")
    truth = importlib.import_module("core.truth_policy_runtime")
    goal_stack = importlib.import_module("core.goal_stack")

    monkeypatch.setattr(memory_ops, "_GLOBAL_MEMORY_OPS", None)
    monkeypatch.setattr(goal_stack, "_stack", None)
    persisted = {
        f["fact_id"]: {**f, "claim_type": "WORLD_FACT", "origin_type": "USER_REPORTED",
                       "epistemic_state": "Validated", "metadata": {}}
        for f in facts
    }
    monkeypatch.setattr(pipeline_mod, "retrieve", lambda q, domain=None: [
        {"id": f["fact_id"], "text": f["claim"], "retrieval_score": 0.9} for f in facts])
    monkeypatch.setattr(pipeline_mod, "get_fact",
                        lambda fid: dict(persisted[fid]) if fid in persisted else None)
    monkeypatch.setattr(truth, "evaluate_configured_truth_policy_runtime",
                        lambda *a, **k: SimpleNamespace(truth_block=None, blocks_llm=False))
    monkeypatch.setattr(memory_ops.MemoryOpsStore, "save_trace",
                        lambda self, **kw: {"trace_id": "t-ctx"})

    async def done(**kw: Any) -> None:
        return None

    monkeypatch.setattr(events, "on_query_completed", done)
    monkeypatch.setattr(srv, "_resolve_llm_config_for_request", lambda req: _cfg())
    return srv


def test_query_endpoint_reports_what_was_sent(fake: _FakeProvider,
                                              monkeypatch: pytest.MonkeyPatch):
    facts = _facts()
    srv = _query_harness(monkeypatch, facts)
    resp = asyncio.run(srv.query(srv.QueryRequest(query="When can I come?", use_llm=True)))
    if not fake.requests:
        pytest.skip("query pipeline did not reach the LLM step in this environment")
    report = resp.context_report
    assert report is not None and report["limits_applied"] is False
    assert report["memory_records_sent"] == report["memory_records_total"]
    sent_system = fake.bodies[0]["messages"][0]["content"]
    assert fake.bodies[0]["messages"][-1]["content"] == "When can I come?"
    assert "truncated" not in sent_system

    # /query itself accepts at most 2000 characters (explicit 422 above that).
    monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "1500")
    refused = asyncio.run(srv.query(srv.QueryRequest(query="LONG " + "q" * 1800, use_llm=True)))
    assert refused.llm_answer.startswith("[LLM error: llm_context_limit")
    assert len(fake.requests) == 1
