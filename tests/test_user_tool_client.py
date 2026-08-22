from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "titan_tools.py"
spec = importlib.util.spec_from_file_location("titan_tools", SCRIPT)
assert spec and spec.loader
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_list_tools_uses_existing_mcp_tools_list_and_server_key():
    captured = []

    def opener(request, timeout):
        captured.append((request, timeout))
        return FakeResponse(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"tools": [{"name": "search_facts", "description": "Search memory"}]},
            }
        )

    visible = tools.list_tools(
        base_url="http://127.0.0.1:8755",
        api_key="server-key",
        capability="reader",
        opener=opener,
    )
    assert [item["name"] for item in visible] == ["search_facts"]
    request, timeout = captured[0]
    assert request.full_url == "http://127.0.0.1:8755/mcp"
    assert request.get_header("X-api-key") == "server-key"
    assert request.get_header("X-mcp-capability") == "reader"
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["method"] == "tools/list"
    assert timeout == 30


def test_call_tool_uses_tools_call_without_changing_capability_semantics():
    captured = []

    def opener(request, timeout):
        captured.append(request)
        return FakeResponse(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "result": {"content": [{"type": "text", "text": "{\"ok\": true}"}], "isError": False},
            }
        )

    response = tools.call_tool(
        "search_facts",
        {"query": "memory"},
        base_url="http://127.0.0.1:8755",
        api_key="server-key",
        capability="admin",
        opener=opener,
    )
    assert response["result"]["isError"] is False
    request = captured[0]
    assert request.get_header("X-mcp-capability") == "admin"
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["method"] == "tools/call"
    assert payload["params"] == {
        "name": "search_facts",
        "arguments": {"query": "memory"},
    }


def test_tool_arguments_must_be_object():
    with pytest.raises(tools.ToolClientError, match="JSON object"):
        tools.parse_arguments_json("[1, 2]")


def test_invalid_json_is_actionable():
    with pytest.raises(tools.ToolClientError, match="valid JSON"):
        tools.parse_arguments_json("{bad")


def test_missing_server_key_fails_before_request():
    with pytest.raises(tools.ToolClientError, match="VELANTRIM_API_KEY"):
        tools.list_tools(
            base_url="http://127.0.0.1:8755",
            api_key="",
            capability="reader",
        )
