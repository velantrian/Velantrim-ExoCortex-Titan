"""
Confirmed Codex finding: GET /mcp/sse's event generator used to yield the
endpoint event once and return, so Starlette closed the StreamingResponse
immediately despite advertising `Connection: keep-alive` — clients never got
a live channel. Fixed with a heartbeat-until-disconnect loop.

Drives api.mcp_gateway.sse_event_stream() directly against a fake Request
rather than through the full ASGI/middleware stack — server.py's
BaseHTTPMiddleware-based security/rate-limit middleware relays streaming
responses through an internal task, and cancelling mid-stream there hangs
regardless of this generator's own behavior. Testing the generator in
isolation is both faster and immune to that unrelated interaction.
"""
from __future__ import annotations

import asyncio

import api.mcp_gateway as mcp_gateway


class _FakeRequest:
    """is_disconnected() reports False for `alive_for` calls, then True —
    simulating a client that stays connected briefly then disconnects."""

    def __init__(self, alive_for: int) -> None:
        self._remaining = alive_for

    async def is_disconnected(self) -> bool:
        if self._remaining <= 0:
            return True
        self._remaining -= 1
        return False


def test_sse_stream_yields_heartbeats_before_the_client_disconnects(monkeypatch):
    monkeypatch.setattr(mcp_gateway, "SSE_HEARTBEAT_INTERVAL_SECONDS", 0)

    async def _run():
        request = _FakeRequest(alive_for=3)
        chunks = []
        async for chunk in mcp_gateway.sse_event_stream(request, "sid-123"):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(asyncio.wait_for(_run(), timeout=5.0))

    assert any("endpoint" in c for c in chunks)
    heartbeats = [c for c in chunks if c.startswith(":")]
    assert heartbeats, "stream produced no heartbeats before the fake client disconnected"


def test_sse_stream_terminates_once_client_disconnects_immediately(monkeypatch):
    monkeypatch.setattr(mcp_gateway, "SSE_HEARTBEAT_INTERVAL_SECONDS", 0)

    async def _run():
        request = _FakeRequest(alive_for=0)
        chunks = []
        async for chunk in mcp_gateway.sse_event_stream(request, "sid-456"):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(asyncio.wait_for(_run(), timeout=5.0))

    # Still gets the initial endpoint event, but no heartbeats once
    # is_disconnected() reports True right away.
    assert len(chunks) == 1
    assert "endpoint" in chunks[0]
