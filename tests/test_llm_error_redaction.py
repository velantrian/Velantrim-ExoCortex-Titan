"""LLM failures must not leak exception text, and unsafe keys must not reach the wire.

Provider exceptions can carry request headers, URLs with credentials, a key echoed back
by the provider, or part of the prompt. This file plants a SYNTHETIC marker (never a real
credential) in the exception text, in its chained cause and in the provider detail, and
asserts the marker is absent from every surface an operator, a client or a downstream
consumer can see: the HTTP/API response, ``llm_meta``, every log record (message and
formatted traceback), the persisted reasoning trace and the emitted completion event.

Keys with characters that cannot go into an HTTP header are rejected before any request
is built; the HTTP layer would otherwise raise an error containing the whole header value.
"""
from __future__ import annotations

import importlib
import json
import logging
from types import SimpleNamespace

import httpx
import pytest

MARKER = "SYNTHETIC-SECRET-MARKER-9c41e7"


def _llm_router():
    # Earlier tests reload core.*. Exception classes and functions are resolved from the
    # live modules at call time: a class captured at import or collection time would no
    # longer match the class the (reloaded) code under test raises or checks.
    return importlib.import_module("core.llm_router")


def _errors():
    return importlib.import_module("core.llm_errors")


def _failures():
    """(factory, expected code) pairs. Exceptions are built inside the test, not at collection."""

    def provider_error(status):
        def make():
            return _llm_router().LlmProviderRequestError(
                provider="openai", status_code=status, detail=f"Incorrect API key {MARKER}",
                message=f"openai: HTTP {status} — Incorrect API key {MARKER}",
            )
        return make

    def chained():
        try:
            raise RuntimeError(f"inner {MARKER}")
        except RuntimeError as inner:
            err = ValueError(f"outer {MARKER}")
            err.__cause__ = inner
            return err

    return [
        pytest.param(lambda: RuntimeError(f"boom Authorization: Bearer {MARKER}"), "llm_internal_error", id="runtime"),
        pytest.param(chained, "llm_request_invalid", id="chained"),
        pytest.param(lambda: TimeoutError(MARKER), "llm_timeout", id="timeout"),
        pytest.param(lambda: httpx.ConnectError(f"connect {MARKER}"), "llm_unreachable", id="connect"),
        pytest.param(provider_error(401), "llm_auth_failed", id="provider-401"),
        pytest.param(provider_error(429), "llm_rate_limited", id="provider-429"),
    ]


# ── unit: key validation and classification ──────────────────────────────────

@pytest.mark.parametrize("key", ["sk-abc_DEF.123", "AIzaSyA-b_c123", "x" * 200])
def test_header_safe_keys_are_accepted(key):
    _errors().validate_llm_api_key(key)


@pytest.mark.parametrize(
    "key",
    [f"{MARKER}\n", f"{MARKER}\r\nX: y", f"{MARKER} tail", f"{MARKER}\x00", f"{MARKER}\t", f"{MARKER}é", f"{MARKER}\x7f"],
)
def test_unsafe_keys_are_rejected_without_echoing_them(key):
    with pytest.raises(_errors().LlmKeyInvalidError) as excinfo:
        _errors().validate_llm_api_key(key)
    assert MARKER not in str(excinfo.value)
    assert MARKER not in repr(excinfo.value)


def test_empty_key_is_left_to_the_not_configured_check():
    _errors().validate_llm_api_key("")
    _errors().validate_llm_api_key(None)


def test_classification_uses_the_type_not_the_text():
    e = _errors()
    for p in _failures():
        make, code = p.values[0], p.values[1]
        assert e.classify_llm_error(make()) == code
    assert e.classify_llm_error(e.LlmNotConfiguredError("x")) == "llm_not_configured"
    assert e.classify_llm_error(e.LlmKeyInvalidError()) == "llm_key_invalid"


def test_event_ids_are_unique_and_text_is_static():
    e = _errors()
    a = e.describe_llm_failure(RuntimeError(MARKER))
    b = e.describe_llm_failure(RuntimeError(MARKER))
    assert a.event_id != b.event_id
    text = e.safe_llm_error_text(a)
    assert a.code in text and a.event_id in text and MARKER not in text


# ── end to end: /query ───────────────────────────────────────────────────────

class _Surfaces:
    def __init__(self):
        self.traces: list[dict] = []
        self.events: list[dict] = []


def _install_query_harness(monkeypatch, *, cfg):
    """Real server.query path; only retrieval, persistence sinks and the provider are replaced."""
    srv = importlib.import_module("server")
    pipeline_mod = importlib.import_module("core.pipeline")
    memory_ops_mod = importlib.import_module("core.memory_ops")
    event_bridge_mod = importlib.import_module("core.event_bridge")
    truth_mod = importlib.import_module("core.truth_policy_runtime")
    goal_stack_mod = importlib.import_module("core.goal_stack")

    monkeypatch.setattr(memory_ops_mod, "_GLOBAL_MEMORY_OPS", None)
    monkeypatch.setattr(goal_stack_mod, "_stack", None)
    fact = {
        "fact_id": "llm-err-1", "claim": "SQLite serializes writes.", "source": "src:t",
        "confidence": 0.9, "epistemic_state": "Validated", "claim_type": "WORLD_FACT",
        "origin_type": "USER_REPORTED", "metadata": {},
    }
    monkeypatch.setattr(pipeline_mod, "retrieve", lambda q, domain=None: [{"id": "llm-err-1", "text": fact["claim"], "retrieval_score": 0.9}])
    monkeypatch.setattr(pipeline_mod, "get_fact", lambda fid: dict(fact) if fid == "llm-err-1" else None)
    monkeypatch.setattr(
        truth_mod, "evaluate_configured_truth_policy_runtime",
        lambda *a, **k: SimpleNamespace(truth_block=None, blocks_llm=False),
    )
    sinks = _Surfaces()
    monkeypatch.setattr(
        memory_ops_mod.MemoryOpsStore, "save_trace",
        lambda self, **kw: sinks.traces.append(kw) or {"trace_id": "t-llm-err"},
    )

    async def on_completed(**kw):
        sinks.events.append(kw)

    monkeypatch.setattr(event_bridge_mod, "on_query_completed", on_completed)
    monkeypatch.setattr(srv, "_resolve_llm_config_for_request", lambda req: cfg)
    return srv, sinks


def _log_blob(caplog) -> str:
    fmt = logging.Formatter("%(name)s %(levelname)s %(message)s")
    return "\n".join(fmt.format(r) + "\n" + (r.exc_text or "") for r in caplog.records)


def _assert_no_marker(**surfaces):
    for name, value in surfaces.items():
        assert MARKER not in value, f"marker leaked into {name}"


@pytest.mark.asyncio
@pytest.mark.parametrize(("exc", "code"), _failures())
async def test_query_failure_surfaces_only_a_code_and_event_id(monkeypatch, caplog, exc, code):
    make = exc
    r = _llm_router()
    cfg = r.LlmCallConfig(provider="openai", api_key="synthetic-valid-key", model="gpt-4o")
    srv, sinks = _install_query_harness(monkeypatch, cfg=cfg)

    async def failing(*args, **kwargs):
        raise make()

    monkeypatch.setattr(r, "chat_complete", failing)
    caplog.set_level(logging.DEBUG)

    resp = await srv.query(srv.QueryRequest(query="how are writes serialized", use_llm=True))

    assert resp.llm_meta["error_code"] == code
    assert resp.llm_meta["error"] == code
    assert resp.llm_meta["event_id"].startswith("llm_evt_")
    assert code in resp.llm_answer and resp.llm_meta["event_id"] in resp.llm_answer
    _assert_no_marker(
        response=resp.model_dump_json(),
        logs=_log_blob(caplog),
        traces=repr(sinks.traces),
        events=repr(sinks.events),
    )
    assert sinks.traces, "trace sink was not reached: the test would be vacuous"
    assert sinks.events, "event sink was not reached: the test would be vacuous"
    assert any(resp.llm_meta["event_id"] in rec.getMessage() for rec in caplog.records)


@pytest.mark.asyncio
@pytest.mark.parametrize("key", [f"{MARKER}\nX", f"{MARKER}\r\n", f"{MARKER} y", f"{MARKER}é"])
async def test_query_rejects_an_unsafe_key_before_any_request(monkeypatch, caplog, key):
    r = _llm_router()
    cfg = r.LlmCallConfig(provider="openai", api_key=key, model="gpt-4o")
    srv, sinks = _install_query_harness(monkeypatch, cfg=cfg)
    sent: list[str] = []

    async def must_not_dispatch(*args, **kwargs):
        sent.append("dispatch")
        raise AssertionError("a request was built for an unsafe key")

    monkeypatch.setattr(r, "_chat_complete_dispatch", must_not_dispatch)
    caplog.set_level(logging.DEBUG)

    resp = await srv.query(srv.QueryRequest(query="how are writes serialized", use_llm=True))

    assert sent == []
    assert resp.llm_meta["error_code"] == "llm_key_invalid"
    _assert_no_marker(
        response=resp.model_dump_json(), logs=_log_blob(caplog),
        traces=repr(sinks.traces), events=repr(sinks.events),
    )


@pytest.mark.asyncio
async def test_router_rejects_unsafe_key_before_building_a_request(monkeypatch):
    r = _llm_router()

    class _NoNetwork:
        def __init__(self, *a, **k):
            raise AssertionError("an HTTP client was created for an unsafe key")

    monkeypatch.setattr(httpx, "AsyncClient", _NoNetwork)
    cfg = r.LlmCallConfig(provider="openai", api_key=f"{MARKER}\n", model="gpt-4o")
    with pytest.raises(_errors().LlmKeyInvalidError):
        await r.chat_complete(cfg, "hello")
    with pytest.raises(_errors().LlmKeyInvalidError):
        await r.test_connection(cfg)


# ── end to end: streaming and the other routes ───────────────────────────────

@pytest.mark.asyncio
async def test_stream_chat_events_rejects_unsafe_key_and_emits_a_safe_event(monkeypatch):
    stream = importlib.import_module("core.llm_stream")
    r = _llm_router()

    class _NoNetwork:
        def __init__(self, *a, **k):
            raise AssertionError("an HTTP client was created for an unsafe key")

    monkeypatch.setattr(httpx, "AsyncClient", _NoNetwork)
    cfg = r.LlmCallConfig(provider="openai", api_key=f"{MARKER}\n", model="gpt-4o")
    events = [e async for e in stream.stream_chat_events(cfg, "system", "hello", None)]

    assert [e["type"] for e in events] == ["error"]
    assert events[0]["error_code"] == "llm_key_invalid"
    _assert_no_marker(events=json.dumps(events))


@pytest.mark.asyncio
async def test_stream_chat_events_hides_provider_exception_text(monkeypatch, caplog):
    stream = importlib.import_module("core.llm_stream")
    r = _llm_router()

    async def boom(*a, **k):
        raise RuntimeError(f"stream {MARKER}")
        yield  # pragma: no cover

    monkeypatch.setattr(stream, "_stream_openai_compatible", boom)
    # The egress lease/policy is not the subject of this test; the provider stream is.
    monkeypatch.setattr(stream, "ensure_remote_egress_allowed", lambda *a, **k: None)
    monkeypatch.setattr(stream, "assert_model_allowed", lambda cfg: None)
    caplog.set_level(logging.DEBUG)
    cfg = r.LlmCallConfig(provider="openai", api_key="synthetic-valid-key", model="gpt-4o")
    events = [e async for e in stream.stream_chat_events(cfg, "system", "hello", None)]

    assert events and events[-1]["type"] == "error"
    assert events[-1]["error_code"] == "llm_internal_error"
    _assert_no_marker(events=json.dumps(events), logs=_log_blob(caplog))


@pytest.mark.asyncio
async def test_chat_endpoint_http_error_carries_no_exception_text(monkeypatch, caplog):
    from fastapi import HTTPException

    srv = importlib.import_module("server")
    stream = importlib.import_module("core.llm_stream")
    r = _llm_router()
    cfg = r.LlmCallConfig(provider="openai", api_key="synthetic-valid-key", model="gpt-4o")
    monkeypatch.setattr(srv, "_resolve_llm_config_for_request", lambda req: cfg)
    monkeypatch.setattr(srv, "pipeline_run", lambda q, m, d: {"facts": [], "answer": "", "error": None})
    monkeypatch.setattr(srv, "_console_offline_reply", lambda *a, **k: None)

    async def failing(*a, **k):
        raise RuntimeError(f"chat {MARKER}")

    monkeypatch.setattr(stream, "chat_complete_messages", failing)
    caplog.set_level(logging.DEBUG)

    with pytest.raises(HTTPException) as excinfo:
        await srv.chat_endpoint(srv.ChatRequest(message="hello", llm_provider="openai", llm_api_key="synthetic-valid-key"))

    assert excinfo.value.status_code == 400
    assert "llm_internal_error" in str(excinfo.value.detail)
    _assert_no_marker(detail=str(excinfo.value.detail), logs=_log_blob(caplog), cause=repr(excinfo.value.__cause__))


@pytest.mark.asyncio
async def test_llm_test_route_maps_codes_to_statuses_without_text(monkeypatch, caplog):
    from fastapi import HTTPException

    routes = importlib.import_module("api.llm_routes")
    r = _llm_router()
    caplog.set_level(logging.DEBUG)

    async def rejected(cfg):
        raise r.LlmProviderRequestError(
            provider="openai", status_code=401, detail=MARKER, message=f"openai: HTTP 401 {MARKER}",
        )

    monkeypatch.setattr(r, "test_connection", rejected)
    body = routes.LlmTestBody(provider="openai", api_key="synthetic-valid-key")

    with pytest.raises(HTTPException) as excinfo:
        await routes._run_llm_test(body)

    assert excinfo.value.status_code == 401
    assert "llm_auth_failed" in str(excinfo.value.detail)
    _assert_no_marker(detail=str(excinfo.value.detail), logs=_log_blob(caplog), cause=repr(excinfo.value.__cause__))


def test_egress_denial_keeps_the_policy_reason_code_and_nothing_else():
    egress = importlib.import_module("core.remote_egress")
    e = _errors()

    denied = egress.RemoteEgressDeniedError(
        "network_denied", capability="remote_llm", provider="openai",
        snapshot_id="snap-private-1", policy_version="v1",
    )
    info = e.describe_llm_failure(denied)
    text = e.safe_llm_error_text(info)
    assert info.code == "llm_egress_denied" and "network_denied" in text
    assert "snap-private-1" not in text and "openai" not in text
    assert e.safe_llm_error_meta(info)["detail_code"] == "network_denied"

    odd = egress.RemoteEgressDeniedError(
        f"bad reason {MARKER}", capability="remote_llm", provider="openai",
        snapshot_id="s", policy_version="v1",
    )
    info = e.describe_llm_failure(odd)
    assert info.code == "llm_egress_denied" and info.detail == ""
    assert MARKER not in e.safe_llm_error_text(info)
    assert "detail_code" not in e.safe_llm_error_meta(info)


# ── remaining surfaces found by the leak audit ──────────────────────────────

def _mock_httpx(monkeypatch, handler):
    real = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient",
        lambda *a, **k: real(*a, **{**k, "transport": httpx.MockTransport(handler)}),
    )


def _unauthorized(request):
    # A provider that echoes the credential back in its error body.
    return httpx.Response(401, json={"error": {"message": f"Incorrect API key provided: {MARKER}"}})


def _no_network(monkeypatch):
    class _NoNetwork:
        def __init__(self, *a, **k):
            raise AssertionError("an HTTP client was created for an unsafe key")

    monkeypatch.setattr(httpx, "AsyncClient", _NoNetwork)


def _allow_egress(monkeypatch):
    for modname in ("core.llm_router", "core.llm_stream", "core.tts_router", "core.remote_egress"):
        mod = importlib.import_module(modname)
        if hasattr(mod, "ensure_remote_egress_allowed"):
            monkeypatch.setattr(mod, "ensure_remote_egress_allowed", lambda *a, **k: None)
    for modname in ("core.llm_router", "core.llm_stream"):
        mod = importlib.import_module(modname)
        if hasattr(mod, "assert_model_allowed"):
            monkeypatch.setattr(mod, "assert_model_allowed", lambda *a, **k: None)


def _b64(n=32):
    import base64
    return base64.b64encode(b"x" * n).decode("ascii")


@pytest.mark.asyncio
async def test_stt_transcribe_route_returns_a_code_not_the_provider_text(monkeypatch, caplog):
    from fastapi import HTTPException

    routes = importlib.import_module("api.llm_routes")
    _allow_egress(monkeypatch)
    _mock_httpx(monkeypatch, _unauthorized)
    caplog.set_level(logging.DEBUG)
    body = routes.SttTranscribeBody(provider="openai", api_key="synthetic-valid-key", audio_base64=_b64())

    with pytest.raises(HTTPException) as excinfo:
        await routes.stt_transcribe(body)

    assert excinfo.value.status_code == 401
    assert "llm_auth_failed" in str(excinfo.value.detail)
    _assert_no_marker(detail=str(excinfo.value.detail), logs=_log_blob(caplog), cause=repr(excinfo.value.__cause__))


@pytest.mark.asyncio
async def test_gemini_stt_keeps_the_typed_error_and_logs_no_provider_text(monkeypatch, caplog):
    r = _llm_router()
    _allow_egress(monkeypatch)
    _mock_httpx(monkeypatch, _unauthorized)
    caplog.set_level(logging.DEBUG)
    cfg = r.LlmCallConfig(provider="gemini", api_key="synthetic-valid-key")

    with pytest.raises(r.LlmProviderRequestError) as excinfo:
        await r.transcribe_audio_gemini(cfg, _b64())

    assert _errors().classify_llm_error(excinfo.value) == "llm_auth_failed"
    _assert_no_marker(logs=_log_blob(caplog))


@pytest.mark.asyncio
async def test_tts_speak_route_hides_provider_text_and_rejects_unsafe_keys(monkeypatch, caplog):
    from fastapi import HTTPException

    routes = importlib.import_module("api.llm_routes")
    _allow_egress(monkeypatch)
    caplog.set_level(logging.DEBUG)

    _mock_httpx(monkeypatch, _unauthorized)
    with pytest.raises(HTTPException) as excinfo:
        await routes.tts_speak_chunk(routes.TtsSpeakBody(provider="openai", api_key="synthetic-valid-key", text="hello"))
    assert excinfo.value.status_code == 401 and "llm_auth_failed" in str(excinfo.value.detail)
    _assert_no_marker(detail=str(excinfo.value.detail), logs=_log_blob(caplog))

    _no_network(monkeypatch)
    for provider in ("openai", "gemini"):
        with pytest.raises(HTTPException) as excinfo:
            await routes.tts_speak_chunk(routes.TtsSpeakBody(provider=provider, api_key=f"{MARKER}\nX", text="hello"))
        assert "llm_key_invalid" in str(excinfo.value.detail)
        _assert_no_marker(detail=str(excinfo.value.detail), logs=_log_blob(caplog))


@pytest.mark.asyncio
async def test_tts_stream_route_rejects_unsafe_keys_before_the_response_starts(monkeypatch):
    from fastapi import HTTPException

    routes = importlib.import_module("api.llm_routes")
    _allow_egress(monkeypatch)
    _no_network(monkeypatch)
    with pytest.raises(HTTPException) as excinfo:
        await routes.tts_stream_route(routes.TtsSpeakBody(provider="openai", api_key=f"{MARKER}\nX", text="hello"))
    assert "llm_key_invalid" in str(excinfo.value.detail)
    _assert_no_marker(detail=str(excinfo.value.detail))


@pytest.mark.asyncio
async def test_tts_stream_failure_ends_with_a_safe_line_and_a_clean_log(monkeypatch, caplog):
    routes = importlib.import_module("api.llm_routes")
    _allow_egress(monkeypatch)
    _mock_httpx(monkeypatch, _unauthorized)
    caplog.set_level(logging.DEBUG)

    tts = importlib.import_module("core.tts_router")
    # Model and voice are explicit on purpose: the route passes model=None through, and
    # gemini_tts_bytes rejects an empty Gemini model id (pre-existing, separate from this change).
    resp = await routes.tts_stream_route(routes.TtsSpeakBody(
        provider="gemini", api_key="synthetic-valid-key", text="hello",
        model=tts.DEFAULT_GEMINI_TTS_MODEL, voice=tts.DEFAULT_GEMINI_TTS_VOICE,
    ))
    chunks = [c async for c in resp.body_iterator]

    last = json.loads(chunks[-1].decode("utf-8"))
    assert last["error_code"] == "llm_auth_failed" and last["event_id"].startswith("llm_evt_")
    _assert_no_marker(body=b"".join(chunks).decode("utf-8"), logs=_log_blob(caplog))


@pytest.mark.asyncio
async def test_gemini_model_discovery_validates_the_key_and_hides_exception_text(monkeypatch, caplog):
    models = importlib.import_module("core.gemini_models")
    _allow_egress(monkeypatch)
    caplog.set_level(logging.DEBUG)

    _no_network(monkeypatch)
    ids, warnings = await models.fetch_gemini_models_from_api(f"{MARKER}\nX")
    assert ids == [] and any("llm_key_invalid" in w for w in warnings)
    _assert_no_marker(warnings=" ".join(warnings), logs=_log_blob(caplog))

    def boom(request):
        raise httpx.ConnectError(f"connect {MARKER}")

    _mock_httpx(monkeypatch, boom)
    ids, warnings = await models.fetch_gemini_models_from_api("synthetic-valid-key")
    assert warnings and all("llm_" in w for w in warnings)
    _assert_no_marker(warnings=" ".join(warnings), logs=_log_blob(caplog))


@pytest.mark.asyncio
async def test_streaming_provider_http_error_keeps_its_status_and_leaks_nothing(monkeypatch, caplog):
    stream = importlib.import_module("core.llm_stream")
    r = _llm_router()
    _allow_egress(monkeypatch)
    _mock_httpx(monkeypatch, _unauthorized)
    caplog.set_level(logging.DEBUG)
    cfg = r.LlmCallConfig(provider="openai", api_key="synthetic-valid-key", model="gpt-4o")

    events = [e async for e in stream.stream_chat_events(cfg, "system", "hello", None)]

    assert events[-1]["type"] == "error" and events[-1]["error_code"] == "llm_auth_failed"
    _assert_no_marker(events=json.dumps(events), logs=_log_blob(caplog))


@pytest.mark.asyncio
async def test_chat_stream_forwards_the_stream_error_code_and_event_id(monkeypatch, caplog):
    srv = importlib.import_module("server")
    r = _llm_router()
    cfg = r.LlmCallConfig(provider="openai", api_key=f"{MARKER}\nX", model="gpt-4o")

    async def prepare(req):
        return [], None, cfg, "system", "ru", "openai", "gpt-4o"

    monkeypatch.setattr(srv, "_chat_prepare", prepare)
    monkeypatch.setattr(srv, "_console_offline_reply", lambda *a, **k: None)
    _no_network(monkeypatch)
    caplog.set_level(logging.DEBUG)

    resp = await srv.chat_stream_endpoint(srv.ChatRequest(message="hello", llm_provider="openai", llm_api_key="synthetic-valid-key"))
    text = "".join([c if isinstance(c, str) else c.decode("utf-8") async for c in resp.body_iterator])

    errors = [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ") and '"type": "error"' in line]
    assert errors, "no error event was streamed"
    assert errors[-1]["error_code"] == "llm_key_invalid"
    assert sum(errors[-1]["event_id"] in rec.getMessage() for rec in caplog.records) >= 1
    _assert_no_marker(sse=text, logs=_log_blob(caplog))


@pytest.mark.asyncio
async def test_sleep_worker_logs_a_code_not_the_exception_text(monkeypatch, caplog):
    sleep = importlib.import_module("core.sleep_time_worker")
    caplog.set_level(logging.DEBUG)
    worker = object.__new__(sleep.SleepTimeWorker)

    async def failing(prompt):
        raise RuntimeError(f"provider said Bearer {MARKER}")

    worker._llm_fn = failing
    await worker._llm_complete("prompt")

    _assert_no_marker(logs=_log_blob(caplog))
    assert any("sleep_worker" in rec.getMessage() for rec in caplog.records)


def test_reader_adapter_treats_key_and_config_errors_as_permanent():
    adapter = importlib.import_module("core.readers.llm_adapter")
    e = _errors()
    assert adapter._provider_failure_code(e.LlmKeyInvalidError()) == "PROVIDER_REQUEST_REJECTED"
    assert adapter._provider_failure_code(e.LlmNotConfiguredError("x")) == "PROVIDER_REQUEST_REJECTED"


def test_call_config_repr_does_not_contain_the_key():
    cfg = _llm_router().LlmCallConfig(provider="openai", api_key=MARKER)
    _assert_no_marker(repr=repr(cfg), str_=str(cfg), fmt=f"{cfg}", fmt_r=f"{cfg!r}")
    assert cfg.api_key == MARKER


def test_http_403_has_its_own_code_and_keeps_the_historical_status():
    r = _llm_router()
    exc = r.LlmProviderRequestError(provider="gemini", status_code=403, detail=MARKER, message=MARKER)
    info = _errors().describe_llm_failure(exc)
    assert info.code == "llm_access_denied" and info.http_status == 400
    assert "403" in info.hint and MARKER not in _errors().safe_llm_error_text(info)
