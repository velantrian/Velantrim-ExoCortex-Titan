from __future__ import annotations

import json

import pytest

from core.capability_plane import (
    CapabilityManifest,
    diagnose_registry,
    explain_tool_access,
    main,
    snapshot_registry,
)
from core.tool_registry import ToolRegistry


def _noop(**kwargs):
    return kwargs


def _registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        "read_tool",
        _noop,
        capability="reader",
        description="read",
        params={"type": "object", "properties": {"q": {"type": "string"}}},
    )
    registry.register(
        "research_tool",
        _noop,
        capability="researcher",
        description="research",
    )
    registry.register(
        "danger_tool",
        _noop,
        capability="admin",
        description="danger",
        destructive=True,
        needs_principal=True,
    )
    return registry


def test_snapshot_is_deterministic_and_sorted() -> None:
    registry = _registry()

    first = snapshot_registry(registry, "admin")
    second = snapshot_registry(registry, "admin")

    assert first == second
    assert first.sha256 == second.sha256
    assert [tool.name for tool in first.tools] == [
        "danger_tool",
        "read_tool",
        "research_tool",
    ]


def test_snapshot_does_not_retain_mutable_param_reference() -> None:
    registry = _registry()
    snapshot = snapshot_registry(registry, "reader")

    registry.get_tool("read_tool").params["properties"]["q"]["type"] = "integer"

    manifest = snapshot.tools[0].to_dict()
    assert manifest["inputSchema"]["properties"]["q"]["type"] == "string"


def test_manifest_fails_closed_on_non_json_schema() -> None:
    registry = ToolRegistry()
    registry.register("bad", _noop, params={"bad": object()})

    with pytest.raises(ValueError, match="non-canonical JSON"):
        snapshot_registry(registry, "reader")


def test_explain_unknown_tool() -> None:
    result = explain_tool_access(_registry(), "reader", "missing")
    assert result["known"] is False
    assert result["callAllowed"] is False
    assert result["reasonCode"] == "unknown_tool"


def test_explain_insufficient_capability() -> None:
    result = explain_tool_access(_registry(), "reader", "research_tool")
    assert result["known"] is True
    assert result["visible"] is False
    assert result["callAllowed"] is False
    assert result["reasonCode"] == "insufficient_capability"
    assert result["requiredCapability"] == "researcher"


def test_explain_admin_destructive_tool() -> None:
    result = explain_tool_access(_registry(), "admin", "danger_tool")
    assert result["visible"] is True
    assert result["callAllowed"] is True
    assert result["reasonCode"] == "visible"
    assert result["destructive"] is True
    assert result["needsPrincipal"] is True


def test_doctor_passes_for_consistent_registry() -> None:
    result = diagnose_registry(_registry(), "reader")
    assert result["ok"] is True
    assert result["issues"] == []
    assert result["visibleToolCount"] == 1
    assert len(result["snapshotSha256"]) == 64


def test_doctor_detects_stale_visibility_index_after_reregistration() -> None:
    registry = ToolRegistry()
    registry.register("same", _noop, capability="reader")
    registry.register("same", _noop, capability="admin", destructive=True)

    result = diagnose_registry(registry, "admin")

    assert result["ok"] is False
    assert any(issue.startswith("visibility_index_mismatch:reader") for issue in result["issues"])


def test_doctor_detects_destructive_tool_visible_below_admin() -> None:
    registry = ToolRegistry()
    registry.register("danger", _noop, capability="reader", destructive=True)

    result = diagnose_registry(registry, "reader")

    assert result["ok"] is False
    assert "destructive_visible_below_admin:reader:danger" in result["issues"]


def test_manifest_dataclass_is_frozen() -> None:
    manifest = CapabilityManifest(
        name="x",
        description="",
        required_capability="reader",
        input_schema_json="{}",
        destructive=False,
        audit=True,
        needs_principal=False,
    )
    with pytest.raises(Exception):
        manifest.name = "y"  # type: ignore[misc]


def test_cli_explain_outputs_json(monkeypatch, capsys) -> None:
    registry = _registry()
    monkeypatch.setattr("core.capability_plane.get_tool_registry", lambda: registry)

    code = main(["explain", "read_tool", "--capability", "reader"])
    output = json.loads(capsys.readouterr().out)

    assert code == 0
    assert output["callAllowed"] is True
    assert output["reasonCode"] == "visible"


def test_cli_doctor_returns_nonzero_on_issue(monkeypatch, capsys) -> None:
    registry = ToolRegistry()
    registry.register("danger", _noop, capability="reader", destructive=True)
    monkeypatch.setattr("core.capability_plane.get_tool_registry", lambda: registry)

    code = main(["doctor", "--capability", "reader"])
    output = json.loads(capsys.readouterr().out)

    assert code == 2
    assert output["ok"] is False
