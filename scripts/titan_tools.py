from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable

DEFAULT_PORT = 8755


class ToolClientError(RuntimeError):
    """A user-actionable error from the existing Titan MCP surface."""


def project_root(script_file: str | Path = __file__) -> Path:
    return Path(script_file).resolve().parents[1]


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def mcp_request(
    *,
    base_url: str,
    api_key: str,
    capability: str,
    payload: dict,
    opener=urllib.request.urlopen,
) -> dict:
    if not api_key:
        raise ToolClientError("VELANTRIM_API_KEY is missing from .env.")
    request = urllib.request.Request(
        base_url.rstrip("/") + "/mcp",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": api_key,
            "X-MCP-Capability": capability,
        },
        method="POST",
    )
    try:
        with opener(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise ToolClientError(f"Titan MCP rejected the request (HTTP {exc.code}): {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ToolClientError(
            f"Titan is not reachable at {base_url}. Start scripts/bootstrap_titan.py first."
        ) from exc
    if "error" in body:
        error = body.get("error") or {}
        raise ToolClientError(str(error.get("message") or error))
    return body


def list_tools(*, base_url: str, api_key: str, capability: str, opener=urllib.request.urlopen) -> list[dict]:
    response = mcp_request(
        base_url=base_url,
        api_key=api_key,
        capability=capability,
        payload={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        opener=opener,
    )
    return list((response.get("result") or {}).get("tools") or [])


def call_tool(
    name: str,
    arguments: dict,
    *,
    base_url: str,
    api_key: str,
    capability: str,
    opener=urllib.request.urlopen,
) -> dict:
    return mcp_request(
        base_url=base_url,
        api_key=api_key,
        capability=capability,
        payload={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        opener=opener,
    )


def parse_arguments_json(raw: str) -> dict:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToolClientError("Tool arguments must be valid JSON.") from exc
    if not isinstance(value, dict):
        raise ToolClientError("Tool arguments must be a JSON object, for example: '{\"query\": \"memory\"}'.")
    return value


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List or call Titan's existing MCP tools without writing JSON-RPC by hand."
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--capability",
        default="reader",
        help="Requested MCP capability. The server still clamps this to VELANTRIM_MCP_MAX_CAPABILITY.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List tools visible under the effective server-side capability.")
    call = sub.add_parser("call", help="Call one visible MCP tool.")
    call.add_argument("name")
    call.add_argument("arguments", nargs="?", default="{}", help="JSON object with tool arguments.")
    return parser.parse_args(list(argv) if argv is not None else None)


def run(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    env = read_env(project_root() / ".env")
    api_key = env.get("VELANTRIM_API_KEY", "")
    base_url = f"http://127.0.0.1:{args.port}"

    if args.command == "list":
        tools = list_tools(
            base_url=base_url,
            api_key=api_key,
            capability=args.capability,
        )
        if not tools:
            print("No tools are visible under the current server capability.")
            return 0
        for tool in tools:
            print(f"- {tool.get('name', '?')}: {tool.get('description', '')}")
        return 0

    arguments = parse_arguments_json(args.arguments)
    response = call_tool(
        args.name,
        arguments,
        base_url=base_url,
        api_key=api_key,
        capability=args.capability,
    )
    result = response.get("result") or {}
    content = result.get("content") or []
    if content and isinstance(content[0], dict) and "text" in content[0]:
        print(content[0]["text"])
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    try:
        return run()
    except ToolClientError as exc:
        print(f"[Titan] Tool error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
