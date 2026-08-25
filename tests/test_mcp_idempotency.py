from __future__ import annotations

import json

from api.mcp_gateway import _derive_batch_idempotency_key
from core.mcp_transport import McpHandler
from core.tool_registry import ToolRegistry


def _call(
    handler: McpHandler,
    *,
    msg_id: int,
    name: str,
    arguments: dict | None = None,
    capability: str = "reader",
    caller: str = "api:test",
    key: str | None = None,
):
    return handler.handle(
        {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        },
        capability=capability,
        credential_fingerprint=caller,
        idempotency_key=key,
    )


def _decoded(response: dict) -> dict:
    return json.loads(response["result"]["content"][0]["text"])


def test_same_side_effect_request_and_key_executes_once(monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    calls = {"count": 0}

    def mutate(value: int) -> dict[str, int]:
        calls["count"] += 1
        return {"value": value, "call": calls["count"]}

    registry = ToolRegistry()
    registry.register(
        "mutate",
        mutate,
        capability="ingester",
        side_effecting=True,
    )
    handler = McpHandler(registry=registry)

    first = _call(
        handler,
        msg_id=1,
        name="mutate",
        arguments={"value": 7},
        capability="ingester",
        key="retry-1",
    )
    second = _call(
        handler,
        msg_id=99,
        name="mutate",
        arguments={"value": 7},
        capability="ingester",
        key="retry-1",
    )

    assert calls["count"] == 1
    assert first["id"] == 1
    assert second["id"] == 99
    assert _decoded(first) == {"value": 7, "call": 1}
    assert _decoded(second) == {"value": 7, "call": 1}


def test_same_key_with_different_arguments_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    calls = {"count": 0}

    def mutate(value: int) -> dict[str, int]:
        calls["count"] += 1
        return {"value": value}

    registry = ToolRegistry()
    registry.register("mutate", mutate, capability="ingester", side_effecting=True)
    handler = McpHandler(registry=registry)

    allowed = _call(
        handler,
        msg_id=1,
        name="mutate",
        arguments={"value": 1},
        capability="ingester",
        key="same-key",
    )
    conflict = _call(
        handler,
        msg_id=2,
        name="mutate",
        arguments={"value": 2},
        capability="ingester",
        key="same-key",
    )

    assert allowed["result"]["isError"] is False
    assert conflict["error"]["code"] == -32602
    assert "different tool arguments" in conflict["error"]["message"]
    assert calls["count"] == 1


def test_same_key_is_scoped_by_server_derived_caller(monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    calls = {"count": 0}

    def mutate() -> dict[str, int]:
        calls["count"] += 1
        return {"call": calls["count"]}

    registry = ToolRegistry()
    registry.register("mutate", mutate, capability="ingester", side_effecting=True)
    handler = McpHandler(registry=registry)

    first = _call(
        handler,
        msg_id=1,
        name="mutate",
        capability="ingester",
        caller="api:a",
        key="shared-key",
    )
    second = _call(
        handler,
        msg_id=2,
        name="mutate",
        capability="ingester",
        caller="api:b",
        key="shared-key",
    )

    assert _decoded(first) == {"call": 1}
    assert _decoded(second) == {"call": 2}
    assert calls["count"] == 2


def test_read_only_tool_is_not_cached_even_when_key_is_present() -> None:
    calls = {"count": 0}

    def read() -> dict[str, int]:
        calls["count"] += 1
        return {"call": calls["count"]}

    registry = ToolRegistry()
    registry.register("read", read, capability="reader", side_effecting=False)
    handler = McpHandler(registry=registry)

    first = _call(handler, msg_id=1, name="read", key="irrelevant")
    second = _call(handler, msg_id=2, name="read", key="irrelevant")

    assert _decoded(first) == {"call": 1}
    assert _decoded(second) == {"call": 2}
    assert calls["count"] == 2


def test_side_effect_call_without_key_remains_backward_compatible(monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    calls = {"count": 0}

    def mutate() -> dict[str, int]:
        calls["count"] += 1
        return {"call": calls["count"]}

    registry = ToolRegistry()
    registry.register("mutate", mutate, capability="ingester", side_effecting=True)
    handler = McpHandler(registry=registry)

    _call(handler, msg_id=1, name="mutate", capability="ingester")
    _call(handler, msg_id=2, name="mutate", capability="ingester")

    assert calls["count"] == 2


def test_transport_key_reuses_operation_owned_idempotency_argument(monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    seen: list[str | None] = []

    def durable_operation(*, idempotency_key: str | None = None) -> dict[str, str | None]:
        seen.append(idempotency_key)
        return {"idempotency_key": idempotency_key}

    registry = ToolRegistry()
    registry.register(
        "durable",
        durable_operation,
        capability="admin",
        destructive=True,
        side_effecting=True,
        idempotency_arg="idempotency_key",
    )
    handler = McpHandler(registry=registry)

    first = _call(
        handler,
        msg_id=1,
        name="durable",
        capability="admin",
        key="durable-key",
    )
    second = _call(
        handler,
        msg_id=2,
        name="durable",
        capability="admin",
        key="durable-key",
    )

    assert seen == ["durable-key"]
    assert _decoded(first) == {"idempotency_key": "durable-key"}
    assert _decoded(second) == {"idempotency_key": "durable-key"}


def test_conflicting_transport_and_operation_keys_fail_closed(monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    calls = {"count": 0}

    def durable_operation(*, idempotency_key: str | None = None) -> dict[str, str | None]:
        calls["count"] += 1
        return {"idempotency_key": idempotency_key}

    registry = ToolRegistry()
    registry.register(
        "durable",
        durable_operation,
        capability="admin",
        destructive=True,
        side_effecting=True,
        idempotency_arg="idempotency_key",
    )
    handler = McpHandler(registry=registry)

    response = _call(
        handler,
        msg_id=1,
        name="durable",
        arguments={"idempotency_key": "body-key"},
        capability="admin",
        key="header-key",
    )

    assert response["error"]["code"] == -32602
    assert "conflicts" in response["error"]["message"]
    assert calls["count"] == 0


def test_idempotency_key_validation_is_bounded(monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    registry = ToolRegistry()
    registry.register("mutate", lambda: {}, capability="ingester", side_effecting=True)
    handler = McpHandler(registry=registry)

    too_long = _call(
        handler,
        msg_id=1,
        name="mutate",
        capability="ingester",
        key="x" * 129,
    )
    control_char = _call(
        handler,
        msg_id=2,
        name="mutate",
        capability="ingester",
        key="bad\nkey",
    )

    assert too_long["error"]["code"] == -32602
    assert control_char["error"]["code"] == -32602


def test_manifest_declares_side_effect_and_operation_idempotency_metadata() -> None:
    registry = ToolRegistry()
    registry.register(
        "write",
        lambda **kwargs: kwargs,
        capability="admin",
        side_effecting=True,
        idempotency_arg="idempotency_key",
    )

    manifest = registry.get_tool("write").to_manifest()
    assert manifest["sideEffecting"] is True
    assert manifest["idempotencyArg"] == "idempotency_key"


def test_batch_key_derivation_is_bounded_for_max_length_header() -> None:
    derived = _derive_batch_idempotency_key("x" * 128, 123)

    assert derived.startswith("batch-")
    assert len(derived) == 70
    assert derived.isascii()


def test_batch_key_derivation_accepts_unicode_and_whitespace_message_ids() -> None:
    first = _derive_batch_idempotency_key("retry", " сообщение 1 ")
    second = _derive_batch_idempotency_key("retry", " сообщение 1 ")
    different = _derive_batch_idempotency_key("retry", "сообщение 2")

    assert first == second
    assert first != different
    assert len(first) == 70


def test_batch_key_derivation_preserves_json_rpc_id_type() -> None:
    numeric = _derive_batch_idempotency_key("retry", 1)
    textual = _derive_batch_idempotency_key("retry", "1")

    assert numeric != textual
