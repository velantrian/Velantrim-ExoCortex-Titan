"""Bounded operational capability manifest and diagnostics for Titan.

This module intentionally wraps the existing ToolRegistry instead of creating
another plugin/tool registry. It is read-only: it can snapshot registry
metadata, explain whether a capability can see/call a tool, and diagnose
registry invariants. It does not execute tools or grant authority.

Boundary:
    capability metadata != permission grant
    manifest visibility != epistemic authority
    diagnostics != runtime authorization
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from typing import Any

from core.tool_registry import CAPABILITY_CHAIN, ToolDef, ToolRegistry, get_tool_registry

MANIFEST_VERSION = "titan-capability-manifest-v0.1"


def _validate_capability(capability: str) -> str:
    normalized = capability.strip().lower()
    if normalized not in CAPABILITY_CHAIN:
        raise ValueError(
            f"unknown capability: {capability!r}; expected one of {CAPABILITY_CHAIN}"
        )
    return normalized


def _rank(capability: str) -> int:
    return CAPABILITY_CHAIN.index(_validate_capability(capability))


def _canonical_json(value: Any) -> str:
    """Serialize manifest material deterministically and fail closed."""
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("capability manifest contains non-canonical JSON data") from exc


@dataclass(frozen=True)
class CapabilityManifest:
    """Immutable metadata snapshot for one already-registered tool.

    ``input_schema_json`` is stored as canonical JSON text rather than a
    mutable dict so a snapshot cannot be changed through a retained reference
    to ToolDef.params after construction.
    """

    name: str
    description: str
    required_capability: str
    input_schema_json: str
    destructive: bool
    audit: bool
    needs_principal: bool

    @classmethod
    def from_tool(cls, tool: ToolDef) -> CapabilityManifest:
        return cls(
            name=tool.name,
            description=tool.description,
            required_capability=_validate_capability(tool.capability),
            input_schema_json=_canonical_json(tool.params),
            destructive=bool(tool.destructive),
            audit=bool(tool.audit),
            needs_principal=bool(tool.needs_principal),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "requiredCapability": self.required_capability,
            "inputSchema": json.loads(self.input_schema_json),
            "destructive": self.destructive,
            "audit": self.audit,
            "needsPrincipal": self.needs_principal,
        }


@dataclass(frozen=True)
class CapabilitySnapshot:
    """Deterministic visible-tool snapshot for one effective capability."""

    capability: str
    tools: tuple[CapabilityManifest, ...]
    sha256: str
    manifest_version: str = MANIFEST_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifestVersion": self.manifest_version,
            "capability": self.capability,
            "sha256": self.sha256,
            "tools": [tool.to_dict() for tool in self.tools],
        }


def snapshot_registry(registry: ToolRegistry, capability: str) -> CapabilitySnapshot:
    """Capture exactly what the existing registry exposes to ``capability``.

    The snapshot is metadata-only and does not retain callables or mutable
    parameter dicts. Sorting by tool name makes the digest independent of
    registration order.
    """
    cap = _validate_capability(capability)
    visible = registry.for_capability(cap)
    manifests = tuple(
        sorted(
            (CapabilityManifest.from_tool(tool) for tool in visible.values()),
            key=lambda item: item.name,
        )
    )
    payload = {
        "manifestVersion": MANIFEST_VERSION,
        "capability": cap,
        "tools": [tool.to_dict() for tool in manifests],
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return CapabilitySnapshot(capability=cap, tools=manifests, sha256=digest)


def explain_tool_access(
    registry: ToolRegistry,
    capability: str,
    tool_name: str,
) -> dict[str, Any]:
    """Explain effective registry visibility/callability without executing.

    This mirrors the existing ToolRegistry + MCP destructive-tool rule. It does
    not apply the transport's deployment ceiling; callers should pass the
    already-authorized/effective capability when using this at a transport
    boundary.
    """
    cap = _validate_capability(capability)
    tool = registry.get_tool(tool_name)
    if tool is None:
        return {
            "tool": tool_name,
            "capability": cap,
            "known": False,
            "visible": False,
            "callAllowed": False,
            "reasonCode": "unknown_tool",
        }

    required = _validate_capability(tool.capability)
    visible = tool_name in registry.for_capability(cap)

    if visible and _rank(cap) < _rank(required):
        allowed = False
        reason = "registry_invariant_violation"
    elif visible and tool.destructive and cap != "admin":
        allowed = False
        reason = "destructive_requires_admin"
    elif visible:
        allowed = True
        reason = "visible"
    else:
        allowed = False
        reason = "insufficient_capability"

    return {
        "tool": tool_name,
        "capability": cap,
        "known": True,
        "visible": visible,
        "callAllowed": allowed,
        "reasonCode": reason,
        "requiredCapability": required,
        "destructive": bool(tool.destructive),
        "audit": bool(tool.audit),
        "needsPrincipal": bool(tool.needs_principal),
    }


def diagnose_registry(registry: ToolRegistry, capability: str) -> dict[str, Any]:
    """Run bounded, read-only consistency checks over the existing registry."""
    cap = _validate_capability(capability)
    issues: list[str] = []

    # ToolRegistry keeps one canonical ToolDef per name plus derived visibility
    # indexes. Re-registration bugs can leave those indexes stale, so compare
    # each actual visible set against the set implied by canonical ToolDefs.
    canonical_tools = dict(registry._tools)
    for level in CAPABILITY_CHAIN:
        actual = set(registry.for_capability(level))
        expected = {
            name
            for name, tool in canonical_tools.items()
            if tool.capability in CAPABILITY_CHAIN and _rank(level) >= _rank(tool.capability)
        }
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            issues.append(
                f"visibility_index_mismatch:{level}:missing={missing}:extra={extra}"
            )

        for name in sorted(actual):
            tool = canonical_tools[name]
            if tool.capability not in CAPABILITY_CHAIN:
                issues.append(f"invalid_required_capability:{name}:{tool.capability}")
                continue
            if _rank(level) < _rank(tool.capability):
                issues.append(
                    f"capability_escalation:{level}:{name}:requires={tool.capability}"
                )
            if tool.destructive and level != "admin":
                issues.append(f"destructive_visible_below_admin:{level}:{name}")

    snapshot_sha256: str | None = None
    visible_tool_count = 0
    try:
        first = snapshot_registry(registry, cap)
        second = snapshot_registry(registry, cap)
        snapshot_sha256 = first.sha256
        visible_tool_count = len(first.tools)
        if first != second:
            issues.append("non_deterministic_snapshot")
    except ValueError as exc:
        issues.append(f"manifest_serialization_error:{exc}")

    return {
        "ok": not issues,
        "manifestVersion": MANIFEST_VERSION,
        "capability": cap,
        "visibleToolCount": visible_tool_count,
        "snapshotSha256": snapshot_sha256,
        "issues": issues,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m core.capability_plane",
        description="Read-only Titan capability manifest/explain/doctor surface.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest = subparsers.add_parser("manifest", help="print visible capability manifest")
    manifest.add_argument("--capability", default="reader", choices=CAPABILITY_CHAIN)

    explain = subparsers.add_parser("explain", help="explain access to one registered tool")
    explain.add_argument("tool")
    explain.add_argument("--capability", default="reader", choices=CAPABILITY_CHAIN)

    doctor = subparsers.add_parser("doctor", help="check registry visibility invariants")
    doctor.add_argument("--capability", default="reader", choices=CAPABILITY_CHAIN)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    registry = get_tool_registry()

    if args.command == "manifest":
        result = snapshot_registry(registry, args.capability).to_dict()
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.command == "explain":
        result = explain_tool_access(registry, args.capability, args.tool)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    result = diagnose_registry(registry, args.capability)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":  # pragma: no cover - exercised through main() tests
    raise SystemExit(main())
