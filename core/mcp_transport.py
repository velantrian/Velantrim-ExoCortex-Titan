"""
MCP JSON-RPC transport over capability-based tool_registry (RFC 05).
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from core.tool_registry import CAPABILITY_CHAIN, ToolRegistry, get_tool_registry

logger = logging.getLogger("velantrim.mcp")

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "velantrim-titan"
SERVER_VERSION = "8.7"


def normalize_capability(raw: str | None) -> str:
    cap = (raw or "reader").strip().lower()
    if cap not in CAPABILITY_CHAIN:
        raise ValueError(f"unknown capability: {raw}")
    return cap


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
    ) -> dict[str, Any] | None:
        if payload.get("jsonrpc") != "2.0":
            return make_error(payload.get("id"), -32600, "Invalid Request")

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
            return self._tools_call(msg_id, capability, params)

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

        try:
            if tool.audit:
                logger.info("MCP tool call: %s capability=%s", name, capability)
            result = tool.fn(**arguments) if arguments else tool.fn()
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