"""
MCP JSON-RPC transport over capability-based tool_registry (RFC 05).
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

from core.tool_registry import (
    CAPABILITY_CHAIN,
    PrincipalContext,
    ToolRegistry,
    get_tool_registry,
)

logger = logging.getLogger("velantrim.mcp")

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "velantrim-titan"
SERVER_VERSION = "9.0"

# SECURITY (confirmed issue: MCP capability must be authorized server-side):
# the ceiling every MCP caller is entitled to over this transport, regardless
# of what capability they request via a client-controlled header. Default is
# the safest level ("reader"); operators opt in to a higher deployment-wide
# ceiling explicitly via VELANTRIM_MCP_MAX_CAPABILITY, matching how
# VELANTRIM_API_KEY/ALLOW_NO_API_KEY are opt-in elsewhere in this codebase.
_DEFAULT_MAX_CAPABILITY = "reader"


def _server_max_capability() -> str:
    raw = (os.getenv("VELANTRIM_MCP_MAX_CAPABILITY", "") or "").strip().lower()
    return raw if raw in CAPABILITY_CHAIN else _DEFAULT_MAX_CAPABILITY


def _capability_rank(capability: str) -> int:
    try:
        return CAPABILITY_CHAIN.index(capability)
    except ValueError:
        return 0


def normalize_capability(raw: str | None) -> str:
    cap = (raw or "reader").strip().lower()
    if cap not in CAPABILITY_CHAIN:
        raise ValueError(f"unknown capability: {raw}")
    return cap


def resolve_authorized_capability(raw: str | None) -> str:
    """
    Единственная точка авторизации MCP capability (confirmed issue #1):
    клиентский заголовок X-MCP-Capability — это ЗАПРОС, не решение. Он может
    только ПОНИЗИТЬ эффективный capability относительно server-side потолка
    (VELANTRIM_MCP_MAX_CAPABILITY, по умолчанию "reader"), но никогда его не
    поднять. Запрос "admin" при потолке "reader" безопасно даёт "reader", а
    не "admin" — заголовок никогда не может САМ ПО СЕБЕ дать больше прав, чем
    сервер явно разрешил для этого деплоя.

    Все транспорты (HTTP gateway, любой будущий) обязаны вызывать эту
    функцию, а не bare normalize_capability(), чтобы авторизация не могла
    быть случайно обойдена новым entry point.
    """
    requested = normalize_capability(raw)
    ceiling = _server_max_capability()
    if _capability_rank(requested) > _capability_rank(ceiling):
        logger.warning(
            "MCP: запрошенный capability %r превышает server ceiling %r — понижаем",
            requested, ceiling,
        )
        return ceiling
    return requested


def make_error(id_: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def make_result(id_: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


class McpSessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, str] = {}

    def create(self, capability: str) -> str:
        sid = str(uuid.uuid4())
        self._sessions[sid] = capability
        return sid

    def bind(self, session_id: str, capability: str) -> None:
        self._sessions[session_id] = capability

    def get_capability(self, session_id: str) -> str | None:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


class McpHandler:
    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self.registry = registry or get_tool_registry()
        self.sessions = McpSessionManager()

    def handle(
        self,
        payload: dict[str, Any],
        *,
        capability: str,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any] | None:
        if payload.get("jsonrpc") != "2.0":
            return make_error(payload.get("id"), -32600, "Invalid Request")

        # SECURITY (confirmed issue #1): capability arriving here has already
        # been through resolve_authorized_capability() at the transport edge
        # (api/mcp_gateway.py); re-validating here (rather than trusting the
        # caller blindly) closes the gap for any future in-process caller of
        # this handler that might otherwise skip the gateway's clamp.
        capability = resolve_authorized_capability(capability)

        method = payload.get("method", "")
        params = payload.get("params") or {}
        msg_id = payload.get("id")

        if method == "initialize":
            sid = session_id or self.sessions.create(capability)
            self.sessions.bind(sid, capability)
            return make_result(
                msg_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                    "sessionId": sid,
                },
            )

        if method == "notifications/initialized":
            return None

        if method == "tools/list":
            return make_result(msg_id, {"tools": self._tools_for(capability)})

        if method == "tools/call":
            return self._tools_call(msg_id, capability, params, actor_id=actor_id)

        if msg_id is None:
            return None

        return make_error(msg_id, -32601, f"Method not found: {method}")

    def _tools_for(self, capability: str) -> list[dict[str, Any]]:
        tools = self.registry.for_capability(capability)
        return [t.to_manifest() for t in tools.values()]

    def _tools_call(
        self,
        msg_id: Any,
        capability: str,
        params: dict[str, Any],
        *,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        name = params.get("name", "")
        arguments = params.get("arguments") or {}

        available = self.registry.for_capability(capability)
        if name not in available:
            return make_error(
                msg_id,
                -32602,
                f"Tool not visible for capability {capability}: {name}",
            )

        tool = available[name]
        if tool.destructive and capability != "admin":
            return make_error(msg_id, -32603, "Destructive tool requires admin capability")

        call_kwargs = dict(arguments)
        if tool.needs_principal:
            # A real, server-verified PrincipalContext — `capability` is the
            # value resolve_authorized_capability() already computed for
            # THIS call (never a hardcoded literal a handler invents), and
            # actor_id is a pseudonymous, server-derived identity a client
            # cannot forge by naming themselves in the JSON body.
            call_kwargs["principal"] = PrincipalContext(
                capability=capability, actor_id=actor_id or "api:anon",
            )

        try:
            if tool.audit:
                logger.info("MCP tool call: %s capability=%s", name, capability)
            result = tool.fn(**call_kwargs)
            text = json.dumps(result, ensure_ascii=False, default=str)
            return make_result(
                msg_id,
                {
                    "content": [{"type": "text", "text": text}],
                    "isError": False,
                },
            )
        except TypeError as exc:
            return make_result(
                msg_id,
                {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                },
            )
        except Exception as exc:
            logger.exception("MCP tool %s failed", name)
            return make_result(
                msg_id,
                {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                },
            )
