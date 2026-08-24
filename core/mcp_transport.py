"""MCP JSON-RPC transport over capability-based tool_registry (RFC 05)."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import uuid
from collections import OrderedDict
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
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
_DEFAULT_MAX_CAPABILITY = "reader"
_MAX_IDEMPOTENCY_KEY_LENGTH = 128
_DEFAULT_IDEMPOTENCY_CACHE_SIZE = 1024


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
    requested = normalize_capability(raw)
    ceiling = _server_max_capability()
    if _capability_rank(requested) > _capability_rank(ceiling):
        logger.warning(
            "MCP: запрошенный capability %r превышает server ceiling %r — понижаем",
            requested,
            ceiling,
        )
        return ceiling
    return requested


def make_error(id_: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def make_result(id_: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _normalize_idempotency_key(raw: str | None) -> str | None:
    if raw is None:
        return None
    key = raw.strip()
    if not key:
        return None
    if len(key) > _MAX_IDEMPOTENCY_KEY_LENGTH:
        raise ValueError(
            f"idempotency key exceeds {_MAX_IDEMPOTENCY_KEY_LENGTH} characters"
        )
    if any(ord(ch) < 33 or ord(ch) > 126 for ch in key):
        raise ValueError("idempotency key must contain visible ASCII characters only")
    return key


def _canonical_request_fingerprint(
    *,
    tool_name: str,
    capability: str,
    arguments: Mapping[str, Any],
) -> str:
    try:
        encoded = json.dumps(
            {
                "tool": tool_name,
                "capability": capability,
                "arguments": dict(arguments),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("tool arguments are not canonical JSON for idempotency") from exc
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class _IdempotencyEntry:
    request_fingerprint: str
    result_payload: dict[str, Any]


class _IdempotencyCache:
    """Bounded process-local MCP retry cache.

    This deliberately does not claim cross-process or post-restart exactly-once
    semantics. Durable operation-owned idempotency remains authoritative where
    it already exists (for example forget_all).
    """

    def __init__(self, max_entries: int = _DEFAULT_IDEMPOTENCY_CACHE_SIZE) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be >= 1")
        self._max_entries = max_entries
        self._entries: OrderedDict[tuple[str, str, str], _IdempotencyEntry] = OrderedDict()
        self._lock = threading.Lock()

    def get(
        self,
        scope: tuple[str, str, str],
        request_fingerprint: str,
    ) -> tuple[str, dict[str, Any] | None]:
        with self._lock:
            entry = self._entries.get(scope)
            if entry is None:
                return "MISS", None
            self._entries.move_to_end(scope)
            if entry.request_fingerprint != request_fingerprint:
                return "CONFLICT", None
            return "HIT", deepcopy(entry.result_payload)

    def put(
        self,
        scope: tuple[str, str, str],
        request_fingerprint: str,
        result_payload: dict[str, Any],
    ) -> None:
        with self._lock:
            self._entries[scope] = _IdempotencyEntry(
                request_fingerprint=request_fingerprint,
                result_payload=deepcopy(result_payload),
            )
            self._entries.move_to_end(scope)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)


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
    def __init__(
        self,
        registry: ToolRegistry | None = None,
        *,
        idempotency_cache_size: int = _DEFAULT_IDEMPOTENCY_CACHE_SIZE,
    ) -> None:
        self.registry = registry or get_tool_registry()
        self.sessions = McpSessionManager()
        self._idempotency = _IdempotencyCache(idempotency_cache_size)

    def handle(
        self,
        payload: dict[str, Any],
        *,
        capability: str,
        session_id: str | None = None,
        credential_fingerprint: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any] | None:
        if payload.get("jsonrpc") != "2.0":
            return make_error(payload.get("id"), -32600, "Invalid Request")

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
            return self._tools_call(
                msg_id,
                capability,
                params,
                credential_fingerprint=credential_fingerprint,
                idempotency_key=idempotency_key,
            )
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
        credential_fingerprint: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        name = params.get("name", "")
        arguments = params.get("arguments")
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

        if arguments is None:
            call_kwargs: dict[str, Any] = {}
        elif isinstance(arguments, Mapping):
            call_kwargs = dict(arguments)
        else:
            return make_error(msg_id, -32602, "Tool arguments must be a JSON object")

        normalized_key: str | None = None
        request_fingerprint: str | None = None
        cache_scope: tuple[str, str, str] | None = None
        if tool.side_effecting:
            try:
                normalized_key = _normalize_idempotency_key(idempotency_key)
            except ValueError as exc:
                return make_error(msg_id, -32602, str(exc))

            if normalized_key is not None:
                if tool.idempotency_arg:
                    supplied = call_kwargs.get(tool.idempotency_arg)
                    if supplied not in (None, "", normalized_key):
                        return make_error(
                            msg_id,
                            -32602,
                            "transport idempotency key conflicts with operation idempotency key",
                        )
                    call_kwargs[tool.idempotency_arg] = normalized_key

                try:
                    request_fingerprint = _canonical_request_fingerprint(
                        tool_name=name,
                        capability=capability,
                        arguments=call_kwargs,
                    )
                except ValueError as exc:
                    return make_error(msg_id, -32602, str(exc))

                caller = credential_fingerprint or "api:anon"
                cache_scope = (caller, name, normalized_key)
                state, cached = self._idempotency.get(cache_scope, request_fingerprint)
                if state == "CONFLICT":
                    return make_error(
                        msg_id,
                        -32602,
                        "idempotency key was already used with different tool arguments",
                    )
                if state == "HIT" and cached is not None:
                    return make_result(msg_id, cached)

        if tool.needs_principal:
            call_kwargs["principal"] = PrincipalContext(
                capability=capability,
                credential_fingerprint=credential_fingerprint or "api:anon",
            )

        try:
            if tool.audit:
                logger.info("MCP tool call: %s capability=%s", name, capability)
            result = tool.fn(**call_kwargs)
            result_payload = {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, default=str),
                    }
                ],
                "isError": False,
            }
        except TypeError as exc:
            result_payload = {
                "content": [{"type": "text", "text": str(exc)}],
                "isError": True,
            }
        except Exception as exc:
            logger.exception("MCP tool %s failed", name)
            result_payload = {
                "content": [{"type": "text", "text": str(exc)}],
                "isError": True,
            }

        if (
            tool.side_effecting
            and normalized_key is not None
            and cache_scope is not None
            and request_fingerprint is not None
        ):
            self._idempotency.put(cache_scope, request_fingerprint, result_payload)

        return make_result(msg_id, result_payload)
