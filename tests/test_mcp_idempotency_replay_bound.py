from __future__ import annotations

from core.mcp_transport import McpHandler
from core.tool_registry import ToolRegistry


def test_oversized_side_effect_result_is_not_retained_or_reexecuted(monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    calls = {"count": 0}

    def mutate() -> dict[str, str]:
        calls["count"] += 1
        return {"payload": "x" * 70000}

    registry = ToolRegistry()
    registry.register("mutate", mutate, capability="ingester", side_effecting=True)
    handler = McpHandler(registry=registry)

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "mutate", "arguments": {}},
    }
    first = handler.handle(
        payload,
        capability="ingester",
        credential_fingerprint="api:test",
        idempotency_key="big-result",
    )
    payload["id"] = 2
    replay = handler.handle(
        payload,
        capability="ingester",
        credential_fingerprint="api:test",
        idempotency_key="big-result",
    )

    assert calls["count"] == 1
    assert len(first["result"]["content"][0]["text"]) > 65536
    assert replay["id"] == 2
    assert replay["result"]["idempotencyReplayLimited"] is True
    assert "NOT re-executed" in replay["result"]["content"][0]["text"]
