"""
MCP Gateway — StreamableHTTP + SSE transport (RFC 05, Phase 5).
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from typing import Any, Callable

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from core.mcp_transport import McpHandler, resolve_authorized_capability

logger = logging.getLogger("velantrim.mcp.gateway")

_handler = McpHandler()
CAPABILITY_HEADER = "X-MCP-Capability"
SESSION_HEADER = "Mcp-Session-Id"
SSE_HEARTBEAT_INTERVAL_SECONDS = 15


def get_mcp_handler() -> McpHandler:
    return _handler


def _resolve_capability(
    x_mcp_capability: str = Header(default="reader", alias=CAPABILITY_HEADER),
    mcp_session_id: str = Header(default="", alias=SESSION_HEADER),
) -> tuple[str, str | None]:
    # SECURITY (confirmed issue #1): resolve_authorized_capability() clamps
    # the client-supplied header to the server-side ceiling — it can only
    # downgrade, never elevate a caller to "admin". This is the ONLY place
    # a fresh (session-less) request's capability is derived from client
    # input; every branch below is either this clamped value or a
    # previously-clamped value re-read from a bound session.
    try:
        cap = resolve_authorized_capability(x_mcp_capability)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    sid = mcp_session_id.strip() or None
    if sid:
        bound = _handler.sessions.get_capability(sid)
        if bound:
            # A resumed session always uses the capability it was bound with
            # at creation time (itself already clamped) — never re-elevated
            # by a later, differently-valued header on the same session.
            cap = bound
    return cap, sid


def _derive_actor_id(x_api_key: str) -> str:
    """Pseudonymous, server-derived caller identity — mirrors server.py's
    existing PATCH /facts/{fact_id}/transition precedent
    ("api:" + sha256(api_key)[:8]) instead of trusting any client-supplied
    identity field. Only ever fed to tools registered with
    needs_principal=True (see core.tool_registry.PrincipalContext)."""
    if not x_api_key:
        return "api:anon"
    digest = hashlib.sha256(x_api_key.encode("utf-8")).hexdigest()[:8]
    return f"api:{digest}"


async def _read_json_body(request: Request) -> Any:
    raw = await request.body()
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc


def _dispatch(
    payload: dict[str, Any],
    *,
    capability: str,
    session_id: str | None,
    actor_id: str | None = None,
) -> dict[str, Any] | None:
    return _handler.handle(
        payload, capability=capability, session_id=session_id, actor_id=actor_id,
    )


async def sse_event_stream(request: Request, sid: str):
    """
    CONFIRMED (Codex review): yielding once then returning let Starlette
    close the response immediately after connect, despite advertising
    Connection: keep-alive — clients using this transport never got a live
    channel. Keep it open with periodic heartbeat comments until the client
    disconnects. A module-level function (not a closure) so it's directly
    unit-testable against a fake Request without needing a full ASGI/
    middleware round-trip.
    """
    endpoint = json.dumps({"uri": "/mcp", "sessionId": sid})
    yield f"event: endpoint\ndata: {endpoint}\n\n"
    while not await request.is_disconnected():
        await asyncio.sleep(SSE_HEARTBEAT_INTERVAL_SECONDS)
        if await request.is_disconnected():
            break
        yield ": heartbeat\n\n"


def register_mcp_routes(
    app,
    *,
    auth_dependency: Callable | None = None,
) -> None:
    router = APIRouter(tags=["MCP"])
    deps = [Depends(auth_dependency)] if auth_dependency else []

    @router.post("/mcp", dependencies=deps)
    async def mcp_post(
        request: Request,
        cap_sid: tuple[str, str | None] = Depends(_resolve_capability),
        x_api_key: str = Header(default=""),
    ):
        capability, session_id = cap_sid
        actor_id = _derive_actor_id(x_api_key)
        body = await _read_json_body(request)

        if isinstance(body, list):
            responses: list[dict[str, Any]] = []
            for item in body:
                if not isinstance(item, dict):
                    continue
                resp = _dispatch(
                    item, capability=capability, session_id=session_id, actor_id=actor_id,
                )
                if resp is not None:
                    responses.append(resp)
            return JSONResponse(content=responses)

        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Expected JSON object or array")

        resp = _dispatch(
            body, capability=capability, session_id=session_id, actor_id=actor_id,
        )
        if resp is None:
            return JSONResponse(content={}, status_code=202)

        if (
            "result" in resp
            and isinstance(resp["result"], dict)
            and "sessionId" in resp["result"]
        ):
            session_id = resp["result"]["sessionId"]
            return JSONResponse(content=resp, headers={SESSION_HEADER: session_id})

        return JSONResponse(content=resp)

    @router.get("/mcp", dependencies=deps)
    async def mcp_get(
        cap_sid: tuple[str, str | None] = Depends(_resolve_capability),
    ):
        capability, _ = cap_sid
        tools = _handler._tools_for(capability)
        return {
            "protocol": "streamable-http",
            "capability": capability,
            "tools_count": len(tools),
        }

    @router.delete("/mcp", dependencies=deps)
    async def mcp_delete_session(
        mcp_session_id: str = Header(default="", alias=SESSION_HEADER),
    ):
        if not mcp_session_id.strip():
            raise HTTPException(status_code=400, detail="Mcp-Session-Id required")
        _handler.sessions.delete(mcp_session_id.strip())
        return {"status": "deleted", "session_id": mcp_session_id.strip()}

    @router.get("/mcp/sse", dependencies=deps)
    async def mcp_sse(
        request: Request,
        cap_sid: tuple[str, str | None] = Depends(_resolve_capability),
    ):
        capability, session_id = cap_sid
        sid = session_id or _handler.sessions.create(capability)
        _handler.sessions.bind(sid, capability)

        return StreamingResponse(
            sse_event_stream(request, sid),
            media_type="text/event-stream",
            headers={
                SESSION_HEADER: sid,
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    app.include_router(router)
    logger.info("MCP gateway: POST/GET/DELETE /mcp, GET /mcp/sse")
