"""Bound HTTP input before any dispatch, including streams without length."""
import httpx
import pytest
from fastapi import FastAPI

from api import mcp_gateway as gateway


@pytest.fixture
def app_calls(monkeypatch):
    app = FastAPI()
    calls = []
    def dispatch(payload, **kwargs):
        calls.append(payload)
        return {"jsonrpc": "2.0", "id": payload.get("id"), "result": {}}
    monkeypatch.setattr(gateway, "_dispatch", dispatch)
    monkeypatch.setattr(gateway, "MAX_MCP_BODY_BYTES", 4096)
    monkeypatch.setattr(gateway, "MAX_MCP_BATCH_ITEMS", 3)
    monkeypatch.setattr(gateway, "MAX_MCP_JSON_DEPTH", 8)
    gateway.register_mcp_routes(app)
    return app, calls


@pytest.mark.parametrize("body,headers,status", [
    (b" " * 4097, {}, 413), (b"\xff", {}, 400),
    (b"[" * 10 + b"]" * 10, {}, 400),
    (b"{}", {"Content-Length": "9" * 5000}, 413),
    (b"{}", {"Content-Length": "-1"}, 400),
    (b"{}", {"Content-Length": "+2"}, 400),
])
async def test_invalid_input_does_not_dispatch(app_calls, body, headers, status):
    app, calls = app_calls
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/mcp", content=body, headers=headers)
    assert response.status_code == status
    assert calls == []


async def test_stream_without_content_length_is_bounded(app_calls):
    app, calls = app_calls
    async def chunks():
        yield b'{"params":"'
        yield b"x" * 4096
        yield b'"}'
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/mcp", content=chunks())
    assert "content-length" not in response.request.headers
    assert response.status_code == 413
    assert calls == []


@pytest.mark.parametrize("count,status", [(3, 200), (4, 413)])
async def test_batch_checked_before_first_dispatch(app_calls, count, status):
    app, calls = app_calls
    batch = [{"jsonrpc": "2.0", "id": i, "method": "ping"} for i in range(count)]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/mcp", json=batch)
    assert response.status_code == status
    assert len(calls) == (count if status == 200 else 0)


async def test_exact_byte_budget_allows_valid_request(app_calls):
    app, calls = app_calls
    body = b'{"jsonrpc":"2.0","id":1,"method":"ping"}'
    body += b" " * (4096 - len(body))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/mcp", content=body)
    assert response.status_code == 200
    assert len(calls) == 1


@pytest.mark.parametrize("body", [b'{"id":NaN}', b'{"id":Infinity}', b'{"id":' + b'1' * 5000 + b'}'])
async def test_invalid_json_numbers_return_400_instead_of_500(app_calls, monkeypatch, body):
    monkeypatch.setattr(gateway, "MAX_MCP_BODY_BYTES", 8192)
    app, calls = app_calls
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/mcp", content=body)
    assert response.status_code == 400
    assert calls == []


async def test_sync_tool_cannot_block_other_http_requests(app_calls, monkeypatch):
    import asyncio
    import threading
    app, _ = app_calls
    entered, release = threading.Event(), threading.Event()
    def blocked_dispatch(payload, **kwargs):
        entered.set()
        assert release.wait(2), "tool was never released"
        return {"jsonrpc": "2.0", "id": 1, "result": {}}
    monkeypatch.setattr(gateway, "_dispatch", blocked_dispatch)
    @app.get("/probe")
    async def probe():
        return {"ready": True}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        task = asyncio.create_task(client.post("/mcp", json={"id": 1}))
        try:
            for _ in range(100):
                if entered.is_set():
                    break
                await asyncio.sleep(.005)
            assert entered.is_set()
            response = await asyncio.wait_for(client.get("/probe"), .5)
            assert response.json() == {"ready": True}
        finally:
            release.set()
            await task


@pytest.mark.parametrize("oversized", [False, True])
async def test_real_uvicorn_chunked_transport(app_calls, oversized):
    import asyncio
    import socket
    import uvicorn
    app, calls = app_calls
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(16)
    sock.setblocking(False)
    server = uvicorn.Server(uvicorn.Config(app, lifespan="off", log_level="error"))
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        for _ in range(200):
            if server.started:
                break
            if task.done():
                await task
                pytest.fail("server stopped before startup")
            await asyncio.sleep(.01)
        assert server.started
        async def chunks():
            yield b'{"jsonrpc":"2.0","id":7,"method":"ping"}'
            if oversized:
                yield b" " * 4096
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{sock.getsockname()[1]}", trust_env=False) as client:
            response = await client.post("/mcp", content=chunks())
        assert "content-length" not in response.request.headers
        assert response.request.headers["transfer-encoding"] == "chunked"
        assert response.status_code == (413 if oversized else 200)
        assert len(calls) == (0 if oversized else 1)
    finally:
        server.should_exit = True
        try:
            await asyncio.wait_for(task, 5)
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            sock.close()


def test_sessions_expire_and_evict_without_retaining_idle_locks(monkeypatch):
    from core import mcp_transport as transport
    now = [0.0]
    monkeypatch.setattr(transport.time, "monotonic", lambda: now[0])
    sessions = transport.McpSessionManager(max_sessions=2, ttl_seconds=10)
    a, b = sessions.create("reader"), sessions.create("reader")
    sessions.create("reader")
    assert sessions.get_capability(a) is None
    assert len(sessions._sessions) == 2
    with sessions.side_effect_lock(session_id=b, credential_fingerprint=None, capability="reader"):
        assert len(sessions._side_effect_locks._locks) == 1
    assert sessions._side_effect_locks._locks == {}
    now[0] = 11
    assert sessions.get_capability(b) is None
    assert not sessions._sessions
