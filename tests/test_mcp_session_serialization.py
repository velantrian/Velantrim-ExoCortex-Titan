"""Process-local MCP side-effect session serialization."""

from __future__ import annotations

import threading
import time

from core.mcp_transport import McpHandler, _side_effect_scope
from core.tool_registry import ToolRegistry


def _call(
    handler: McpHandler,
    *,
    msg_id: int,
    name: str,
    arguments: dict | None = None,
    capability: str = "ingester",
    caller: str = "api:test",
    session_id: str | None = None,
):
    return handler.handle(
        {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        },
        capability=capability,
        session_id=session_id,
        credential_fingerprint=caller,
    )


def test_side_effect_scope_prefers_explicit_session() -> None:
    assert (
        _side_effect_scope(
            "sess-1",
            credential_fingerprint="api:a",
            capability="ingester",
        )
        == "session:sess-1"
    )
    assert (
        _side_effect_scope(
            None,
            credential_fingerprint="api:a",
            capability="ingester",
        )
        == "anon:api:a:ingester"
    )


def test_same_session_side_effects_do_not_interleave(monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    hold = threading.Event()
    a_inside = threading.Event()
    order: list[str] = []
    active = {"count": 0}
    max_active = {"count": 0}
    lock = threading.Lock()

    def mutate(label: str) -> dict[str, str]:
        with lock:
            active["count"] += 1
            max_active["count"] = max(max_active["count"], active["count"])
            order.append(f"start:{label}")
        if label == "a":
            a_inside.set()
            hold.wait(timeout=2)
        with lock:
            order.append(f"end:{label}")
            active["count"] -= 1
        return {"label": label}

    registry = ToolRegistry()
    registry.register("mutate", mutate, capability="ingester", side_effecting=True)
    handler = McpHandler(registry=registry)
    session_id = "shared-session"
    results: dict[str, dict] = {}

    def run(label: str, msg_id: int) -> None:
        results[label] = _call(
            handler,
            msg_id=msg_id,
            name="mutate",
            arguments={"label": label},
            session_id=session_id,
        )

    t1 = threading.Thread(target=run, args=("a", 1))
    t1.start()
    assert a_inside.wait(timeout=2)
    t2 = threading.Thread(target=run, args=("b", 2))
    t2.start()
    # While A still holds the session lock, B must not have entered the tool.
    time.sleep(0.1)
    with lock:
        assert "start:b" not in order
        assert max_active["count"] == 1
    hold.set()
    t1.join(timeout=5)
    t2.join(timeout=5)

    assert not t1.is_alive() and not t2.is_alive()
    assert max_active["count"] == 1
    assert results["a"]["result"]["isError"] is False
    assert results["b"]["result"]["isError"] is False
    assert order.index("end:a") < order.index("start:b")


def test_different_sessions_may_overlap(monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    both_inside = threading.Barrier(2)
    release = threading.Event()
    max_active = {"count": 0}
    active = {"count": 0}
    lock = threading.Lock()

    def mutate(label: str) -> dict[str, str]:
        with lock:
            active["count"] += 1
            max_active["count"] = max(max_active["count"], active["count"])
        both_inside.wait(timeout=2)
        release.wait(timeout=2)
        with lock:
            active["count"] -= 1
        return {"label": label}

    registry = ToolRegistry()
    registry.register("mutate", mutate, capability="ingester", side_effecting=True)
    handler = McpHandler(registry=registry)

    def run(label: str, session_id: str, msg_id: int) -> None:
        _call(
            handler,
            msg_id=msg_id,
            name="mutate",
            arguments={"label": label},
            session_id=session_id,
        )

    t1 = threading.Thread(target=run, args=("a", "sess-a", 1))
    t2 = threading.Thread(target=run, args=("b", "sess-b", 2))
    t1.start()
    t2.start()
    # Wait until both critical sections are entered concurrently.
    deadline = time.time() + 2
    while time.time() < deadline and max_active["count"] < 2:
        time.sleep(0.01)
    release.set()
    t1.join(timeout=5)
    t2.join(timeout=5)

    assert not t1.is_alive() and not t2.is_alive()
    assert max_active["count"] == 2


def test_read_only_tools_are_not_serialized_against_side_effects(monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    hold = threading.Event()
    reader_saw_hold = threading.Event()
    calls = {"mutate": 0, "peek": 0}

    def mutate() -> dict[str, str]:
        calls["mutate"] += 1
        hold.wait(timeout=2)
        return {"ok": True}

    def peek() -> dict[str, int]:
        calls["peek"] += 1
        reader_saw_hold.set()
        return {"peek": calls["peek"]}

    registry = ToolRegistry()
    registry.register("mutate", mutate, capability="ingester", side_effecting=True)
    registry.register("peek", peek, capability="reader", side_effecting=False)
    handler = McpHandler(registry=registry)
    session_id = "shared-session"
    mutate_result: dict = {}

    def run_mutate() -> None:
        nonlocal mutate_result
        mutate_result = _call(
            handler,
            msg_id=1,
            name="mutate",
            session_id=session_id,
            capability="ingester",
        )

    t = threading.Thread(target=run_mutate)
    t.start()
    # Give mutate a moment to acquire the session side-effect lock.
    time.sleep(0.05)
    peek_result = _call(
        handler,
        msg_id=2,
        name="peek",
        session_id=session_id,
        capability="reader",
    )
    assert reader_saw_hold.is_set()
    hold.set()
    t.join(timeout=5)

    assert not t.is_alive()
    assert peek_result["result"]["isError"] is False
    assert mutate_result["result"]["isError"] is False
    assert calls["mutate"] == 1
    assert calls["peek"] == 1


def test_session_delete_discards_side_effect_lock(monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    registry = ToolRegistry()
    registry.register(
        "mutate",
        lambda: {"ok": True},
        capability="ingester",
        side_effecting=True,
    )
    handler = McpHandler(registry=registry)
    sid = "to-delete"
    first = handler.sessions.side_effect_lock(
        session_id=sid,
        credential_fingerprint="api:test",
        capability="ingester",
    )
    handler.sessions.delete(sid)
    second = handler.sessions.side_effect_lock(
        session_id=sid,
        credential_fingerprint="api:test",
        capability="ingester",
    )
    assert first is not second
