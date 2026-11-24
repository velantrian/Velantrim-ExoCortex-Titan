"""Source-X Gate, hardening round 2 (independent audit of PR #537 @ 149f477).

The first ten tests are the audit's reproducing tests, moved from the
local scratch file. They fail on 149f477 and pass on the round-2 head.
Adaptation: the evidence-policy fields (``facts``, ``memory_*``,
``dialogue_essence``, essence snapshots) are deliberately left unchanged in
this round (see ``docs/adr/ADR-2026-11-24-source-x-evidence-surfaces-PROPOSED.md``);
those tests therefore assert that every OTHER field / event is clean and that
the exempt fields are exactly the documented ones.

The remaining tests cover the round-2 requirements (log safety, SSE
allowlist, verdict integrity, bounded stream, deadline, keep-alive,
parallel requests, cancel, client disconnect). No model calls; the flag is
enabled only inside these tests.
"""

from __future__ import annotations

import asyncio
import contextlib
import importlib
import json
import logging
import time
from types import SimpleNamespace
from typing import Any

import pytest

from tests.test_llm_context_no_silent_truncation import (
    _ALL_SETTINGS,
    _chat_req,
    _install_fake,
    _query_harness,
)

X = ("21,8", "21.8", "7,6", "53,5")
X_TEXT = "По брифу выручка составила 21,8 млн у. е., маржа 7,6."
OFFICIAL = "Официальная выручка 14,2 млн, рост 3,1%."
EVIDENCE_QUERY = {"facts"}
EVIDENCE_CHAT = {"memory_highlights", "memory_saved", "memory_suggestions", "dialogue_essence"}
EVIDENCE_SSE = {("essence", "snapshot")} | {("final", k) for k in EVIDENCE_CHAT}


def sxg():
    return importlib.import_module("core.source_x_gate")


def has_x(obj: Any) -> bool:
    s = json.dumps(obj, ensure_ascii=False, default=str)
    return any(f in s for f in X)


@pytest.fixture(autouse=True)
def _clean_flag(monkeypatch):
    monkeypatch.delenv("ENABLE_SOURCE_X_GATE", raising=False)
    importlib.import_module("core.feature_config").clear_config_cache()
    yield
    importlib.import_module("core.feature_config").clear_config_cache()


@pytest.fixture
def fake(monkeypatch):
    for n in _ALL_SETTINGS:
        monkeypatch.delenv(n, raising=False)
    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "allow")
    monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", "allowed")
    return _install_fake(monkeypatch)


@pytest.fixture
def gate_on(monkeypatch):
    monkeypatch.setenv("ENABLE_SOURCE_X_GATE", "1")
    importlib.import_module("core.feature_config").clear_config_cache()
    assert sxg().SourceXGateConfig.from_app().enabled
    yield


def _log_dump(caplog) -> list[str]:
    out = []
    for r in caplog.records:
        line = f"{r.levelname} {r.name}: {r.getMessage()}"
        if r.exc_info:
            line += "\n" + logging.Formatter().formatException(r.exc_info)
        out.append(line)
    return out


X_FACTS = [
    {"fact_id": "fx1", "claim": "Молниеносный бриф: выручка 21,8 млн, маржа 7,6.", "source": "brief",
     "confidence": 0.9},
    {"fact_id": "fx2", "claim": OFFICIAL, "source": "memo", "confidence": 0.9},
]


def _leaky_fields(model) -> set[str]:
    d = model.model_dump() if hasattr(model, "model_dump") else dict(model)
    return {k for k, v in d.items() if has_x(v)}


def _patch_pipeline_x(monkeypatch):
    srv = importlib.import_module("server")
    monkeypatch.setattr(srv, "pipeline_run", lambda q, mode, domain: {"facts": X_FACTS, "error": None})


def _sse_frames(response) -> list[str]:
    async def collect():
        frames = []
        async for chunk in response.body_iterator:
            frames.append(chunk.decode() if isinstance(chunk, bytes) else chunk)
        return frames
    return asyncio.run(collect())


def _events(frames: list[str]) -> list[dict]:
    evs = []
    for t in frames:
        for line in t.splitlines():
            if line.startswith("data: "):
                evs.append(json.loads(line[6:]))
    return evs


# ════════════════ audit reproductions (RED on 149f477) ════════════════════════


def test_p0_logs_blocked_text(caplog):
    caplog.set_level(logging.DEBUG, logger="core.source_x_gate")
    out = sxg().gate_final_text(X_TEXT, surface="audit", config=sxg().SourceXGateConfig(enabled=True))
    assert out.blocked
    dump = _log_dump(caplog)
    assert dump, "a decision must still be logged"
    assert not any(has_x(d) for d in dump), "X figures written to logs"


def test_p0_logs_gate_exception_with_x_in_message(caplog, monkeypatch):
    def boom(*a, **k):
        raise ValueError("cannot parse 21,8 near 'выручка составила 21,8 млн'")
    monkeypatch.setattr(sxg(), "apply_gate", boom)
    caplog.set_level(logging.DEBUG, logger="core.source_x_gate")
    out = sxg().gate_final_text(X_TEXT, surface="audit", config=sxg().SourceXGateConfig(enabled=True))
    assert out.status == "GATE_ERROR"
    dump = _log_dump(caplog)
    assert any("ValueError" in d for d in dump)
    assert not any(has_x(d) for d in dump), "exception text with X figures logged"
    assert all(r.exc_info is None for r in caplog.records), "traceback logged"


def test_p0_query_fields(fake, gate_on, monkeypatch):
    srv = _query_harness(monkeypatch, X_FACTS)

    async def gen(q, system=None, override=None):
        return OFFICIAL
    monkeypatch.setattr(srv, "_llm_generate", gen)
    resp = asyncio.run(srv.query(srv.QueryRequest(query="Какая выручка?", use_llm=True)))
    assert _leaky_fields(resp) <= EVIDENCE_QUERY


def test_p0_query_llm_meta_error(fake, gate_on, monkeypatch):
    srv = _query_harness(monkeypatch, X_FACTS[1:])

    async def gen(q, system=None, override=None):
        raise RuntimeError("provider echoed: выручка 21,8 млн")
    monkeypatch.setattr(srv, "_llm_generate", gen)
    resp = asyncio.run(srv.query(srv.QueryRequest(query="Какая выручка?", use_llm=True)))
    assert not has_x(resp.llm_meta)
    assert not has_x(resp.llm_answer)


def _roles_call(monkeypatch, response: str, branch_response: str, key_claims: list[str]):
    import core.branch_manager as bm_mod
    srv = importlib.import_module("server")
    branch = bm_mod.BranchResult(
        role=SimpleNamespace(role_id="ANALYST", emoji="🔬"), facts=[X_FACTS[0]],
        response=branch_response, key_claims=key_claims, used_llm=True,
    )
    synth = SimpleNamespace(response=response, branches=[branch], all_branches_used_llm=True,
                            confidence=0.5, dominant_role="ANALYST")

    class BM:
        async def reason(self, **kw):
            return synth
    monkeypatch.setattr(bm_mod, "get_branch_manager", lambda: BM())
    monkeypatch.setattr(srv, "_env_llm_config", lambda: None)
    return asyncio.run(srv.query_with_roles(srv._QueryRolesRequest(query="q")))


def test_p0_query_roles_branches(gate_on, monkeypatch):
    resp = _roles_call(monkeypatch, X_TEXT, X_TEXT, ["выручка 21,8"])
    assert _leaky_fields(resp) <= EVIDENCE_QUERY
    assert not has_x(resp.lens_context)


def test_p0_chat_fields(fake, gate_on, monkeypatch):
    import core.llm_stream as ls
    srv = importlib.import_module("server")
    _patch_pipeline_x(monkeypatch)

    async def comp(cfg, system, message, history, report=None):
        return OFFICIAL, {}
    monkeypatch.setattr(ls, "chat_complete_messages", comp)
    resp = asyncio.run(srv.chat_endpoint(_chat_req(message="Запомни: выручка 21,8 млн")))
    assert _leaky_fields(resp) <= EVIDENCE_CHAT


def test_p0_chat_stream_events(fake, gate_on, monkeypatch):
    import core.llm_stream as ls
    srv = importlib.import_module("server")
    _patch_pipeline_x(monkeypatch)

    async def stream(cfg, system, message, history, report=None):
        yield {"type": "context", "report": {"note": "omitted record: выручка 21,8"}}
        yield {"type": "token", "text": OFFICIAL}
        yield {"type": "done", "reply": OFFICIAL, "usage": {"x": "7,6"}}
    monkeypatch.setattr(ls, "stream_chat_events", stream)
    evs = _events(_sse_frames(asyncio.run(
        srv.chat_stream_endpoint(_chat_req(message="Запомни: выручка 21,8 млн")))))
    for e in evs:
        for k, v in e.items():
            if has_x(v):
                assert (e.get("type"), k) in EVIDENCE_SSE, (e.get("type"), k)


def test_p1_lost_verdict_query(fake, gate_on, monkeypatch):
    srv = _query_harness(monkeypatch, X_FACTS[:1])
    mo = importlib.import_module("core.memory_ops")
    ev = importlib.import_module("core.event_bridge")
    traces, events = [], []
    monkeypatch.setattr(mo.MemoryOpsStore, "save_trace",
                        lambda self, **kw: traces.append(kw) or {"trace_id": "t"})

    async def on_done(**kw):
        events.append(kw)
    monkeypatch.setattr(ev, "on_query_completed", on_done)
    pl = importlib.import_module("core.pipeline")
    seen: dict[str, Any] = {}
    orig = pl.run

    def spy(*a, **k):
        r = orig(*a, **k)
        seen["blocked"] = r.get("source_x_gate_blocked")
        return r
    monkeypatch.setattr(srv, "pipeline_run", spy)
    resp = asyncio.run(srv.query(srv.QueryRequest(query="Какая выручка?", use_llm=False)))
    assert seen.get("blocked") is True, "precondition: pipeline must block"
    assert resp.source_x_gate["answer"]["status"] == "BLOCKED_ATTEMPT", "original verdict lost"
    assert resp.source_x_gate["answer"]["origin"] == "pipeline"
    assert resp.source_x_gate["llm_answer"]["status"] == "NO_ANSWER"
    meta = traces[0]["metadata"]
    assert meta["source_x_gate"]["answer"]["status"] == "BLOCKED_ATTEMPT"
    assert meta["source_x_gate"]["answer"]["reason"]
    assert events[0]["source_x_gate"]["answer"]["status"] == "BLOCKED_ATTEMPT"
    assert not has_x(meta) and not has_x(events[0])


def test_p1_buffer_growth_bounded_run():
    buf = sxg().SourceXStreamBuffer(surface="audit", config=sxg().SourceXGateConfig(enabled=True))
    chunk = "x" * 1024
    for _ in range(20_000):  # 20 MiB offered
        assert buf.feed(chunk) is None
    held = len(buf.held_text)
    out = buf.finalize()
    assert held < 1024 * 1024, "no cap: buffer grew past 1 MiB"
    assert out.status == "GATE_ERROR" and out.blocked
    assert "x" * 64 not in (out.text or "")


def test_p1_never_ending_stream_no_output_no_cap(fake, gate_on, monkeypatch):
    import core.llm_stream as ls
    srv = importlib.import_module("server")
    _patch_pipeline_x(monkeypatch)
    produced = {"n": 0}

    async def endless(cfg, system, message, history, report=None):
        yield {"type": "context", "report": {}}
        while True:
            produced["n"] += 1
            yield {"type": "token", "text": "y" * 512}
            await asyncio.sleep(0)

    monkeypatch.setattr(ls, "stream_chat_events", endless)
    resp = asyncio.run(srv.chat_stream_endpoint(_chat_req()))
    got: list[str] = []

    async def consume():
        async for chunk in resp.body_iterator:
            got.append(chunk if isinstance(chunk, str) else chunk.decode())

    async def run():
        try:
            await asyncio.wait_for(consume(), timeout=2.0)
            return "finished"
        except TimeoutError:
            return "timeout"
    res = asyncio.run(run())
    assert res == "finished", "endless provider stream: endpoint never ends, no cap/timeout in code"
    assert not any("y" * 64 in g for g in got), "held text released"


# ════════════════ round-2 requirements ════════════════════════════════════════


def test_r2_pipeline_exception_and_notes_logs_are_safe(caplog, monkeypatch):
    s = sxg()
    cfg = s.SourceXGateConfig(enabled=True)
    caplog.set_level(logging.DEBUG, logger="core.source_x_gate")
    s.apply_to_pipeline_result({"answer": X_TEXT, "notes": "бриф: 53,5% и 21,8"}, config=cfg)

    def boom(*a, **k):
        raise RuntimeError("bad 21,8")
    monkeypatch.setattr(s, "apply_gate", boom)
    s.apply_to_pipeline_result({"answer": X_TEXT}, config=cfg)
    dump = _log_dump(caplog)
    assert any("BLOCKED_ATTEMPT" in d for d in dump)
    assert any("FLAG_REVIEW_NOTES" in d for d in dump)
    assert any("GATE_ERROR" in d and "RuntimeError" in d for d in dump)
    assert not any(has_x(d) for d in dump)
    assert not any("'excerpt'" in d or "'sentence'" in d for d in dump)
    assert all(r.exc_info is None for r in caplog.records)


def test_r2_safe_log_record_has_only_rule_level_positions():
    s = sxg()
    v = s.apply_gate(X_TEXT, config=s.SourceXGateConfig(enabled=True))
    rec = s.safe_log_record(v, surface="t")
    assert set(rec["hits"][0]) == {"rule", "level", "start", "end"}
    assert not has_x(rec)


def test_r2_sse_unknown_event_and_key_dropped(fake, gate_on, monkeypatch):
    import core.llm_stream as ls
    srv = importlib.import_module("server")
    monkeypatch.setattr(srv, "pipeline_run", lambda q, mode, domain: {"facts": [], "error": None})

    async def stream(cfg, system, message, history, report=None):
        yield {"type": "context", "report": {"memory_records_sent": 1, "debug": "21,8"}}
        yield {"type": "token", "text": "Ок.", "raw": "7,6"}
        yield {"type": "done", "reply": "Ок.", "usage": {"prompt_tokens": 5, "note": "53,5%"}}
    monkeypatch.setattr(ls, "stream_chat_events", stream)
    evs = _events(_sse_frames(asyncio.run(srv.chat_stream_endpoint(_chat_req()))))
    ctx = next(e for e in evs if e["type"] == "context")
    assert ctx["report"] == {"memory_records_sent": 1}
    done = next(e for e in evs if e["type"] == "done")
    assert done["usage"] == {"prompt_tokens": 5}
    assert not has_x(evs)


def test_r2_query_full_response_scan_withholds_unlisted_field(fake, gate_on, monkeypatch):
    srv = _query_harness(monkeypatch, X_FACTS[1:])

    async def gen(q, system=None, override=None):
        return OFFICIAL
    monkeypatch.setattr(srv, "_llm_generate", gen)
    pl = importlib.import_module("core.pipeline")
    orig = pl.run

    def run_with_x(*a, **k):
        r = orig(*a, **k)
        r["cross_domain"] = {"summary": "бриф говорит 21,8"}
        return r
    monkeypatch.setattr(srv, "pipeline_run", run_with_x)
    resp = asyncio.run(srv.query(srv.QueryRequest(query="Какая выручка?", use_llm=True)))
    assert resp.cross_domain == {"summary": sxg().WITHHELD_PLACEHOLDER}
    assert "cross_domain/summary" in resp.source_x_gate["outbound"]["withheld_paths"]


def test_r2_flag_off_responses_unchanged(fake, monkeypatch):
    srv = _query_harness(monkeypatch, X_FACTS[1:])

    async def gen(q, system=None, override=None):
        raise RuntimeError("provider echoed: выручка 21,8 млн")
    monkeypatch.setattr(srv, "_llm_generate", gen)
    resp = asyncio.run(srv.query(srv.QueryRequest(query="Какая выручка?", use_llm=True)))
    # PR #537 secfix (Manus 2026-11-24): the flag-off contract no longer
    # echoes the provider message; llm_meta is a stable code for every flag
    # state. Gate-specific output stays absent while the flag is off.
    assert resp.llm_meta == {
        "error": "llm_provider_error", "error_type": "RuntimeError", "error_redacted": True,
    }
    assert "21,8" not in (resp.llm_answer or "")
    assert resp.source_x_gate is None


def test_r2_no_answer_allow_blocked_are_distinct():
    s = sxg()
    cfg = s.SourceXGateConfig(enabled=True)
    assert s.gate_final_text(None, surface="t", config=cfg).status == "NO_ANSWER"
    assert s.gate_final_text(OFFICIAL, surface="t", config=cfg).status == "ALLOW"
    assert s.gate_final_text(X_TEXT, surface="t", config=cfg).status == "BLOCKED_ATTEMPT"
    stub = s.gate_final_text(s.USER_FACING_BLOCK_MESSAGE, surface="t", config=cfg)
    merged = s.merge_with_prior_verdict(stub, {"status": "BLOCKED_ATTEMPT", "blocked": True,
                                               "hits": [{"rule": "x_number_21_8", "level": "block"}]})
    assert merged.status == "BLOCKED_ATTEMPT" and merged.origin == "pipeline"
    assert merged.rules == ("x_number_21_8",)


def _endless_with_marker(monkeypatch, closed: dict, *, delay: float = 0.0, chunk: str = "z" * 256):
    import core.llm_stream as ls

    async def endless(cfg, system, message, history, report=None):
        try:
            while True:
                closed["chunks"] = closed.get("chunks", 0) + 1
                yield {"type": "token", "text": chunk}
                await asyncio.sleep(delay)
        finally:
            closed["closed"] = True

    monkeypatch.setattr(ls, "stream_chat_events", endless)


def test_r2_overflow_fail_closed_no_offline_fallback(fake, gate_on, monkeypatch):
    srv = importlib.import_module("server")
    _patch_pipeline_x(monkeypatch)
    monkeypatch.setattr(srv, "_console_offline_reply", lambda *a, **k: "OFFLINE 21,8")
    closed: dict = {}
    _endless_with_marker(monkeypatch, closed)
    evs = _events(_sse_frames(asyncio.run(srv.chat_stream_endpoint(_chat_req()))))
    final = evs[-1]
    assert final["type"] == "final"
    assert final["source_x_gate"]["status"] == "GATE_ERROR"
    assert final["source_x_gate"]["reason"] == "stream_buffer_limit"
    assert final["from_llm"] is False
    assert "OFFLINE" not in json.dumps(evs, ensure_ascii=False)
    assert "z" * 64 not in json.dumps(evs)
    assert closed.get("closed") is True, "provider stream must be closed on overflow"
    assert closed["chunks"] <= 262_144 // 256 + 2


def test_r2_deadline_fail_closed_and_keepalive_is_content_free(fake, gate_on, monkeypatch):
    srv = importlib.import_module("server")
    _patch_pipeline_x(monkeypatch)
    monkeypatch.setenv("SOURCE_X_GATE_STREAM_DEADLINE_S", "0.6")
    monkeypatch.setenv("SOURCE_X_GATE_STREAM_KEEPALIVE_S", "0.1")
    import core.llm_stream as ls
    closed: dict = {}

    async def stalls(cfg, system, message, history, report=None):
        try:
            yield {"type": "token", "text": "Выручка 21,8 "}
            await asyncio.sleep(3600)  # provider stalls
            yield {"type": "done", "reply": "never"}
        finally:
            closed["closed"] = True
    monkeypatch.setattr(ls, "stream_chat_events", stalls)
    t0 = time.monotonic()
    frames = _sse_frames(asyncio.run(srv.chat_stream_endpoint(_chat_req())))
    elapsed = time.monotonic() - t0
    assert elapsed < 3.0
    keepalives = [f for f in frames if f.startswith(": hold")]
    assert keepalives and all(f == ": hold\n\n" for f in keepalives)
    evs = _events(frames)
    assert evs[-1]["source_x_gate"]["reason"] == "stream_deadline"
    assert not has_x([e for e in evs if e["type"] != "essence" and e["type"] != "final"])
    assert closed.get("closed") is True


@pytest.mark.parametrize("spec_version", ["2.3", "2.4"])
def test_r2_client_disconnect_closes_provider(fake, gate_on, monkeypatch, spec_version):
    """ASGI 2.3: Starlette listens for http.disconnect and cancels the stream.
    ASGI 2.4: disconnect surfaces when a send fails; while the gate holds,
    the next send is the content-free keep-alive, so detection is bounded by
    the keep-alive interval (shortened here)."""
    srv = importlib.import_module("server")
    _patch_pipeline_x(monkeypatch)
    monkeypatch.setenv("SOURCE_X_GATE_STREAM_KEEPALIVE_S", "0.1")
    closed: dict = {}
    _endless_with_marker(monkeypatch, closed, delay=0.01, chunk="a")
    resp = asyncio.run(srv.chat_stream_endpoint(_chat_req()))
    sent: list[dict] = []

    async def run():
        loop = asyncio.get_running_loop()
        gone_at = loop.time() + 0.3

        async def receive():
            await asyncio.sleep(max(0.0, gone_at - loop.time()))
            return {"type": "http.disconnect"}

        async def send(msg):
            if loop.time() >= gone_at:
                raise OSError("client gone")
            sent.append(msg)

        scope = {"type": "http", "asgi": {"version": "3.0", "spec_version": spec_version},
                 "method": "POST", "path": "/chat/stream", "headers": []}
        with contextlib.suppress(Exception):
            await asyncio.wait_for(resp(scope, receive, send), timeout=5)

    t0 = time.monotonic()
    asyncio.run(run())
    assert time.monotonic() - t0 < 5
    body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    assert b'"type": "token"' not in body
    assert closed.get("closed") is True, "provider stream not closed after client disconnect"


def test_r2_generation_cancel_closes_provider(fake, gate_on, monkeypatch):
    srv = importlib.import_module("server")
    _patch_pipeline_x(monkeypatch)
    closed: dict = {}
    _endless_with_marker(monkeypatch, closed, delay=0.01, chunk="a")
    resp = asyncio.run(srv.chat_stream_endpoint(_chat_req()))

    async def run():
        async def consume():
            async for _ in resp.body_iterator:
                pass
        task = asyncio.ensure_future(consume())
        await asyncio.sleep(0.2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await resp.body_iterator.aclose()

    asyncio.run(run())
    assert closed.get("closed") is True


def test_r2_parallel_requests_are_isolated(fake, gate_on, monkeypatch):
    import core.llm_stream as ls
    srv = importlib.import_module("server")
    monkeypatch.setattr(srv, "pipeline_run", lambda q, mode, domain: {"facts": [], "error": None})

    async def stream(cfg, system, message, history, report=None):
        text = "Выручка 21,8 млн." if "blocked" in message else f"Чистый ответ {message}."
        for ch in (text[:5], text[5:]):
            yield {"type": "token", "text": ch}
            await asyncio.sleep(0.01)
        yield {"type": "done", "reply": text, "usage": {}}
    monkeypatch.setattr(ls, "stream_chat_events", stream)
    msgs = [f"req{i}" if i % 2 else f"blocked{i}" for i in range(8)]

    async def one(m):
        resp = await srv.chat_stream_endpoint(_chat_req(message=m))
        frames = []
        async for chunk in resp.body_iterator:
            frames.append(chunk if isinstance(chunk, str) else chunk.decode())
        return _events(frames)

    async def run():
        return await asyncio.gather(*(one(m) for m in msgs))

    results = asyncio.run(run())
    for m, evs in zip(msgs, results, strict=True):
        final = evs[-1]
        if m.startswith("blocked"):
            assert final["source_x_gate"]["status"] == "BLOCKED_ATTEMPT"
            assert not has_x([e for e in evs if e["type"] != "essence"])
        else:
            assert final["reply"] == f"Чистый ответ {m}."
            assert final["source_x_gate"]["status"] == "ALLOW"
