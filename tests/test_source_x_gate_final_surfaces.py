"""Source-X gate on the final user-facing surfaces (Codex audit 2026-11-23).

Items covered, no model calls:

1. the FINAL text is gated: ``/query`` ``llm_answer`` and lens-formatted
   ``answer``, ``/query/roles``, ``/chat`` reply;
2. ``/chat/stream`` holds model tokens until the gate verdict; a blocked
   reply never reaches the client, including figures split across chunks;
3. an exception inside the gate is fail-closed when the flag is on.

The flag stays off by default; with it off every surface is unchanged.
"""

from __future__ import annotations

import asyncio
import importlib
import json
from types import SimpleNamespace
from typing import Any

import pytest

from core.source_x_gate import (
    USER_FACING_BLOCK_MESSAGE,
    USER_FACING_GATE_ERROR_MESSAGE,
)
from tests.test_llm_context_no_silent_truncation import (
    _ALL_SETTINGS,
    _chat_req,
    _install_fake,
    _patch_pipeline,
    _query_harness,
)

def _sxg():
    """The gate module currently in sys.modules.

    Other suites (test_server_integration) drop ``core.*`` from sys.modules
    and re-import ``server``; resolve at call time so the test patches and
    configures the same module objects the server code will import.
    """
    return importlib.import_module("core.source_x_gate")


def _clear_config() -> None:
    importlib.import_module("core.feature_config").clear_config_cache()


def _cfg(enabled: bool):
    return _sxg().SourceXGateConfig(enabled=enabled)


def gate_final_text(*a, **k):
    return _sxg().gate_final_text(*a, **k)


def apply_to_pipeline_result(*a, **k):
    return _sxg().apply_to_pipeline_result(*a, **k)


def SourceXStreamBuffer(*a, **k):  # noqa: N802 - mirrors the class name
    return _sxg().SourceXStreamBuffer(*a, **k)


OFFICIAL = "Официальная выручка — 14,2 млн у. е., рост 3,1%."
X_ANSWER = "По брифу выручка составила 21,8 млн у. е."
X_FIGURES = ("21,8", "21.8", "7,6", "53,5")


@pytest.fixture(autouse=True)
def _reset_config(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ENABLE_SOURCE_X_GATE", raising=False)
    _clear_config()
    yield
    _clear_config()


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch):
    """Offline provider fake (no network); same setup as the context tests."""
    for name in _ALL_SETTINGS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "allow")
    monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", "allowed")
    return _install_fake(monkeypatch)


@pytest.fixture
def gate_on(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_SOURCE_X_GATE", "1")
    _clear_config()
    assert _sxg().SourceXGateConfig.from_app().enabled is True
    yield
    _clear_config()


def _no_x(text: str | None) -> bool:
    return not any(f in (text or "") for f in X_FIGURES)


# ── default: flag stays off ─────────────────────────────────────────────────


def test_flag_is_off_by_default_and_in_every_compute_profile(monkeypatch):
    from core.compute_profile import resolve_flag

    assert _sxg().SourceXGateConfig.from_app().enabled is False
    for profile in ("lite", "standard", "heavy"):
        monkeypatch.setenv("COMPUTE_PROFILE", profile)
        _clear_config()
        assert resolve_flag("ENABLE_SOURCE_X_GATE", default="0", profile=profile) is False
        assert _sxg().SourceXGateConfig.from_app().enabled is False


def test_gate_final_text_disabled_passes_through():
    out = gate_final_text(X_ANSWER, surface="t", config=_cfg(False))
    assert out.text == X_ANSWER and out.status == "DISABLED" and not out.blocked


# ── item 1: final text ──────────────────────────────────────────────────────


def test_gate_final_text_blocks_and_public_record_has_no_figures():
    out = gate_final_text(X_ANSWER, surface="query_llm_answer", config=_cfg(True))
    assert out.blocked and out.status == "BLOCKED_ATTEMPT"
    assert out.text == USER_FACING_BLOCK_MESSAGE
    assert _no_x(json.dumps(out.public(), ensure_ascii=False))


def test_gate_final_text_keeps_none_and_clean_text():
    assert gate_final_text(None, surface="t", config=_cfg(True)).text is None
    clean = gate_final_text(OFFICIAL, surface="t", config=_cfg(True))
    assert clean.text == OFFICIAL and clean.status == "ALLOW"


def _query_with_llm_text(monkeypatch, llm_text: str, lens_suffix: str | None = None):
    from tests.test_llm_context_no_silent_truncation import _facts

    srv = _query_harness(monkeypatch, _facts())
    calls: list[str] = []

    async def fake_generate(query: str, system: str | None = None, override=None) -> str:
        calls.append(query)
        return llm_text

    monkeypatch.setattr(srv, "_llm_generate", fake_generate)
    if lens_suffix is not None:
        import core.mode_router as mode_router

        monkeypatch.setattr(
            mode_router, "format_lens_answer", lambda ans, routed: f"{ans} {lens_suffix}"
        )
    resp = asyncio.run(srv.query(srv.QueryRequest(query="Какая выручка?", use_llm=True)))
    return resp, calls


def test_query_llm_answer_is_gated_after_llm_step(fake, gate_on, monkeypatch):
    resp, calls = _query_with_llm_text(monkeypatch, X_ANSWER)
    if not calls:
        pytest.skip("query pipeline did not reach the LLM step in this environment")
    assert resp.llm_answer == USER_FACING_BLOCK_MESSAGE
    assert _no_x(resp.llm_answer) and _no_x(resp.answer)
    assert resp.source_x_gate["llm_answer"]["status"] == "BLOCKED_ATTEMPT"
    assert _no_x(json.dumps(resp.source_x_gate, ensure_ascii=False))


def test_query_llm_answer_unchanged_when_flag_off(fake, monkeypatch):
    resp, calls = _query_with_llm_text(monkeypatch, X_ANSWER)
    if not calls:
        pytest.skip("query pipeline did not reach the LLM step in this environment")
    assert resp.llm_answer == X_ANSWER
    assert resp.source_x_gate is None


def test_query_soft_l1_refusal_is_delivered(fake, gate_on, monkeypatch):
    text = "Цифра 21,8 из брифа не используется. " + OFFICIAL
    resp, calls = _query_with_llm_text(monkeypatch, text)
    if not calls:
        pytest.skip("query pipeline did not reach the LLM step in this environment")
    assert resp.llm_answer == text
    assert resp.source_x_gate["llm_answer"]["status"] == "FLAG_L1_REFUSAL"


def test_chat_reply_is_gated(fake, gate_on, monkeypatch):
    import core.llm_stream as llm_stream
    import server

    _patch_pipeline(monkeypatch)

    async def fake_complete(cfg, system, message, history, report=None):
        return X_ANSWER, {}

    monkeypatch.setattr(llm_stream, "chat_complete_messages", fake_complete)
    resp = asyncio.run(server.chat_endpoint(_chat_req()))
    assert resp.reply == USER_FACING_BLOCK_MESSAGE
    assert resp.source_x_gate["status"] == "BLOCKED_ATTEMPT"


def test_chat_reply_unchanged_when_flag_off(fake, monkeypatch):
    import core.llm_stream as llm_stream
    import server

    _patch_pipeline(monkeypatch)

    async def fake_complete(cfg, system, message, history, report=None):
        return X_ANSWER, {}

    monkeypatch.setattr(llm_stream, "chat_complete_messages", fake_complete)
    resp = asyncio.run(server.chat_endpoint(_chat_req()))
    assert resp.reply == X_ANSWER
    assert resp.source_x_gate is None


def test_query_roles_answer_is_gated(gate_on, monkeypatch):
    import core.branch_manager as bm_mod
    import server

    synthesis = SimpleNamespace(
        response=X_ANSWER, branches=[], all_branches_used_llm=True,
        confidence=0.5, dominant_role=None,
    )

    class FakeBM:
        async def reason(self, **kw):
            return synthesis

    monkeypatch.setattr(bm_mod, "get_branch_manager", lambda: FakeBM())
    monkeypatch.setattr(server, "_env_llm_config", lambda: None)
    req = server._QueryRolesRequest(query="q")
    resp = asyncio.run(server.query_with_roles(req)) if hasattr(server, "query_with_roles") else None
    if resp is None:
        handler = next(
            r.endpoint for r in server.app.routes if getattr(r, "path", None) == "/query/roles"
        )
        resp = asyncio.run(handler(req))
    assert resp.answer == USER_FACING_BLOCK_MESSAGE
    assert resp.llm_answer == USER_FACING_BLOCK_MESSAGE
    assert resp.source_x_gate["status"] == "BLOCKED_ATTEMPT"


# ── item 2: streaming holds output until the verdict ───────────────────────


def _install_stream(monkeypatch, chunks: list[str], log: list[str], *, done: bool = True):
    import core.llm_stream as llm_stream

    async def fake_stream(cfg, system, message, history, report=None):
        yield {"type": "context", "report": {}}
        for c in chunks:
            log.append(f"provider:{c}")
            yield {"type": "token", "text": c}
        if done:
            log.append("provider:done")
            yield {"type": "done", "reply": "".join(chunks), "usage": {}}

    monkeypatch.setattr(llm_stream, "stream_chat_events", fake_stream)


def _stream_events(monkeypatch, log: list[str]) -> list[dict[str, Any]]:
    import server

    _patch_pipeline(monkeypatch)
    response = asyncio.run(server.chat_stream_endpoint(_chat_req()))

    async def collect() -> list[dict[str, Any]]:
        out = []
        async for chunk in response.body_iterator:
            text = chunk.decode() if isinstance(chunk, bytes) else chunk
            for line in text.splitlines():
                if line.startswith("data: "):
                    ev = json.loads(line[6:])
                    if ev.get("type") == "token":
                        log.append(f"client:{ev['text']}")
                    out.append(ev)
        return out

    return asyncio.run(collect())


@pytest.mark.parametrize(
    "chunks",
    [
        ["По брифу выручка ", "21,8 млн."],
        ["Выручка за год — 2", "1,8 млн у. е."],
        ["Маржа: 7", ",", "6 пункта."],
        ["Доля 53", ".5", "% по брифу."],
    ],
)
def test_stream_blocked_reply_never_reaches_client(fake, gate_on, monkeypatch, chunks):
    log: list[str] = []
    _install_stream(monkeypatch, chunks, log)
    events = _stream_events(monkeypatch, log)
    client_text = json.dumps(events, ensure_ascii=False)
    for c in chunks:
        if len(c) > 2:
            assert c not in client_text, f"raw chunk leaked: {c!r}"
    assert _no_x(client_text)
    tokens = [e for e in events if e["type"] == "token"]
    assert len(tokens) == 1 and tokens[0]["text"] == USER_FACING_BLOCK_MESSAGE
    # every provider chunk was produced before the client saw any token
    first_client = next(i for i, x in enumerate(log) if x.startswith("client:"))
    assert all(x.startswith("provider:") for x in log[:first_client])
    assert "provider:done" in log[:first_client]
    done = next(e for e in events if e["type"] == "done")
    assert done["reply"] == USER_FACING_BLOCK_MESSAGE
    assert done["source_x_gate"]["status"] == "BLOCKED_ATTEMPT"
    final = events[-1]
    assert final["type"] == "final" and final["reply"] == USER_FACING_BLOCK_MESSAGE
    assert final["source_x_gate"]["blocked"] is True


def test_stream_clean_reply_released_after_verdict(fake, gate_on, monkeypatch):
    log: list[str] = []
    chunks = ["Официальная выручка — ", "14,2 млн у. е., ", "рост 3,1%."]
    _install_stream(monkeypatch, chunks, log)
    events = _stream_events(monkeypatch, log)
    tokens = [e for e in events if e["type"] == "token"]
    assert [t["text"] for t in tokens] == ["".join(chunks)]
    assert events[-1]["reply"] == "".join(chunks)
    assert events[-1]["source_x_gate"]["status"] == "ALLOW"


def test_stream_without_done_event_still_gates_held_chunks(fake, gate_on, monkeypatch):
    log: list[str] = []
    _install_stream(monkeypatch, ["Выручка 2", "1,8."], log, done=False)
    events = _stream_events(monkeypatch, log)
    assert _no_x(json.dumps(events, ensure_ascii=False))
    assert events[-1]["reply"] == USER_FACING_BLOCK_MESSAGE


def test_stream_unchanged_when_flag_off(fake, monkeypatch):
    log: list[str] = []
    chunks = ["По брифу выручка ", "21,8 млн."]
    _install_stream(monkeypatch, chunks, log)
    events = _stream_events(monkeypatch, log)
    tokens = [e["text"] for e in events if e["type"] == "token"]
    assert tokens == chunks  # streamed chunk by chunk as before
    assert "source_x_gate" not in events[-1]
    # with the gate off the client sees chunk 1 before the provider sends chunk 2
    assert log.index("client:" + chunks[0]) < log.index("provider:" + chunks[1])


def test_stream_buffer_prefers_stricter_of_final_and_held():
    buf = SourceXStreamBuffer(surface="t", config=_cfg(True))
    assert buf.feed("Выручка 2") is None and buf.feed("1,8 млн.") is None
    out = buf.finalize(OFFICIAL)  # provider claims a clean final reply
    assert out.blocked and out.text == USER_FACING_BLOCK_MESSAGE


def test_stream_buffer_off_is_passthrough():
    buf = SourceXStreamBuffer(surface="t", config=_cfg(False))
    assert buf.feed("21,8") == "21,8"
    assert buf.finalize("21,8").status == "DISABLED"


# ── item 3: fail-closed on gate errors ──────────────────────────────────────


def _boom(*a, **k):
    raise RuntimeError("synthetic gate failure")


def test_gate_final_text_fail_closed_on_exception(monkeypatch, caplog):
    monkeypatch.setattr(_sxg(), "apply_gate", _boom)
    with caplog.at_level("ERROR", logger="core.source_x_gate"):
        out = gate_final_text(OFFICIAL, surface="t", config=_cfg(True))
    assert out.blocked and out.status == "GATE_ERROR"
    assert out.text == USER_FACING_GATE_ERROR_MESSAGE
    assert any("GATE_ERROR" in r.getMessage() for r in caplog.records)


def test_gate_final_text_error_ignored_when_off(monkeypatch):
    monkeypatch.setattr(_sxg(), "apply_gate", _boom)
    out = gate_final_text(X_ANSWER, surface="t", config=_cfg(False))
    assert out.text == X_ANSWER and out.status == "DISABLED"


def test_apply_to_pipeline_result_fail_closed(monkeypatch, caplog):
    monkeypatch.setattr(_sxg(), "apply_gate", _boom)
    with caplog.at_level("ERROR", logger="core.source_x_gate"):
        res = apply_to_pipeline_result({"answer": X_ANSWER}, config=_cfg(True))
    assert res["answer"] == USER_FACING_GATE_ERROR_MESSAGE
    assert res["source_x_gate_blocked"] is True and res["source_x_gate_error"] is True
    assert res["source_x_gate"]["status"] == "GATE_ERROR"
    assert any("GATE_ERROR" in r.getMessage() for r in caplog.records)


def test_config_failure_falls_back_to_env_flag(monkeypatch):
    def broken():
        raise RuntimeError("config down")

    monkeypatch.setattr(_sxg(), "get_config", broken)
    monkeypatch.setenv("ENABLE_SOURCE_X_GATE", "1")
    out = gate_final_text(X_ANSWER, surface="t")
    assert out.blocked and _no_x(out.text)
    monkeypatch.setenv("ENABLE_SOURCE_X_GATE", "0")
    assert gate_final_text(X_ANSWER, surface="t").text == X_ANSWER


def test_pipeline_wiring_failure_fail_closed(gate_on, monkeypatch):
    import core.pipeline as pipeline

    res = pipeline._source_x_gate_fail_closed({"answer": X_ANSWER}, RuntimeError("x"))
    assert res["answer"] == USER_FACING_GATE_ERROR_MESSAGE
    assert res["source_x_gate_blocked"] is True


def test_pipeline_wiring_failure_passes_through_when_off(monkeypatch):
    import core.pipeline as pipeline

    res = pipeline._source_x_gate_fail_closed({"answer": OFFICIAL}, RuntimeError("x"))
    assert res["answer"] == OFFICIAL and "source_x_gate_blocked" not in res


def test_stream_gate_error_fail_closed(fake, gate_on, monkeypatch):
    monkeypatch.setattr(_sxg(), "apply_gate", _boom)
    log: list[str] = []
    _install_stream(monkeypatch, ["Официальная выручка ", "14,2 млн."], log)
    events = _stream_events(monkeypatch, log)
    tokens = [e for e in events if e["type"] == "token"]
    assert [t["text"] for t in tokens] == [USER_FACING_GATE_ERROR_MESSAGE]
    assert events[-1]["source_x_gate"]["status"] == "GATE_ERROR"
    assert "14,2 млн" not in json.dumps(events, ensure_ascii=False)


def test_chat_gate_error_fail_closed(fake, gate_on, monkeypatch):
    import core.llm_stream as llm_stream
    import server

    _patch_pipeline(monkeypatch)
    monkeypatch.setattr(_sxg(), "apply_gate", _boom)

    async def fake_complete(cfg, system, message, history, report=None):
        return OFFICIAL, {}

    monkeypatch.setattr(llm_stream, "chat_complete_messages", fake_complete)
    resp = asyncio.run(server.chat_endpoint(_chat_req()))
    assert resp.reply == USER_FACING_GATE_ERROR_MESSAGE
    assert resp.source_x_gate["status"] == "GATE_ERROR"
