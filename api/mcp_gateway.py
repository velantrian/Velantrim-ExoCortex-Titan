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
IDEMPOTENCY_HEADER = "Idempotency-Key"
SSE_HEARTBEAT_INTERVAL_SECONDS = 15


def get_mcp_handler() -> McpHandler:
    return _handler


def _resolve_capability(
    x_mcp_capability: str = Header(default="reader", alias=CAPABILITY_HEADER),
    mcp_session_id: str = Header(default="", alias=SESSION_HEADER),
) -> tuple[str, str | None]:
    try:
        cap = resolve_authorized_capability(x_mcp_capability)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    sid = mcp_session_id.strip() or None
    if sid:
        bound = _handler.sessions.get_capability(sid)
        if bound:
            cap = bound
    return cap, sid


def _derive_credential_fingerprint(x_api_key: str) -> str:
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
    credential_fingerprint: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any] | None:
    return _handler.handle(
        payload,
        capability=capability,
        session_id=session_id,
        credential_fingerprint=credential_fingerprint,
        idempotency_key=idempotency_key,
    )


async def sse_event_stream(request: Request, sid: str):
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
        idempotency_key: str = Header(default="", alias=IDEMPOTENCY_HEADER),
    ):
        capability, session_id = cap_sid
        credential_fingerprint = _derive_credential_fingerprint(x_api_key)
        transport_key = idempotency_key.strip() or None
        body = await _read_json_body(request)

        if isinstance(body, list):
            responses: list[dict[str, Any]] = []
            for item in body:
                if not isinstance(item, dict):
                    continue
                # One HTTP retry key may safely cover a JSON-RPC batch only by
                # deriving a stable per-message key from the JSON-RPC id.
                # Notifications have no response id and therefore do not get a
                # derived retry key from the shared HTTP header.
                item_key = None
                if transport_key is not None and item.get("id") is not None:
                    item_key = f"{transport_key}:{item['id']}"
                resp = _dispatch(
                    item,
                    capability=capability,
                    session_id=session_id,
                    credential_fingerprint=credential_fingerprint,
                    idempotency_key=item_key,
                )
                if resp is not None:
                    responses.append(resp)
            return JSONResponse(content=responses)

        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Expected JSON object or array")

        resp = _dispatch(
            body,
            capability=capability,
            session_id=session_id,
            credential_fingerprint=credential_fingerprint,
            idempotency_key=transport_key,
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
