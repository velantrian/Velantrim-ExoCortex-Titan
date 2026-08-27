import json

from core.mcp_transport import McpHandler
from core.tool_registry import ToolRegistry


def _call(handler: McpHandler, name: str, arguments=None):
    params = {"name": name}
    if arguments is not None:
        params["arguments"] = arguments
    return handler.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params},
        capability="reader",
    )


def test_tool_exception_details_are_not_reflected_to_client():
    diagnostic = "path=/srv/titan/private.db target=https://provider.invalid/v1"

    def _explode():
        raise RuntimeError(diagnostic)

    registry = ToolRegistry()
    registry.register("explode", _explode, capability="reader")
    response = _call(McpHandler(registry=registry), "explode")

    payload = response["result"]
    serialized = json.dumps(payload)
    assert payload["isError"] is True
    assert payload["errorCode"] == "TOOL_EXECUTION_FAILED"
    assert payload["correlationId"]
    assert diagnostic not in serialized
    assert "/srv/titan/private.db" not in serialized
    assert "provider.invalid" not in serialized


def test_tool_type_error_uses_same_safe_public_contract():
    def _requires_argument(value):
        return value

    registry = ToolRegistry()
    registry.register("requires_argument", _requires_argument, capability="reader")
    response = _call(McpHandler(registry=registry), "requires_argument")

    payload = response["result"]
    text = payload["content"][0]["text"]
    assert payload["isError"] is True
    assert payload["errorCode"] == "TOOL_EXECUTION_FAILED"
    assert payload["correlationId"]
    assert text == "Tool execution failed. See correlationId in server logs."
    assert "required positional argument" not in text
