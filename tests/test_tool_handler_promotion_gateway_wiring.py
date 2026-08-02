from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest


HANDLERS = Path(__file__).resolve().parents[1] / "core" / "tool_handlers.py"


def _validate_fact_node() -> ast.FunctionDef:
    tree = ast.parse(HANDLERS.read_text(encoding="utf-8"), filename=str(HANDLERS))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "validate_fact":
            return node
    raise AssertionError("validate_fact handler was not found")


def test_validate_fact_uses_one_gateway_call_without_direct_authority_bypass() -> None:
    node = _validate_fact_node()
    gateway_calls = [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Attribute)
        and child.func.attr == "promote"
        and isinstance(child.func.value, ast.Name)
        and child.func.value.id == "_tool_promotion_gateway"
    ]
    direct_calls = [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and (
            isinstance(child.func, ast.Name)
            and child.func.id == "validate_and_promote"
            or isinstance(child.func, ast.Attribute)
            and child.func.attr == "validate_and_promote"
        )
    ]

    assert len(gateway_calls) == 1
    assert direct_calls == []


def test_validate_fact_maps_transient_verdict_and_preserves_request(monkeypatch) -> None:
    from core import tool_handlers as handlers

    calls = []

    class FakeGateway:
        def promote(self, request):
            calls.append(request)
            return SimpleNamespace(
                verdict=SimpleNamespace(
                    passed=False,
                    reason_code="insufficient_evidence",
                    justification="Needs more independent evidence.",
                )
            )

    monkeypatch.setattr(handlers, "_tool_promotion_gateway", FakeGateway())

    result = handlers.validate_fact("fact.tool.demo", by="tool:validate_fact")

    assert len(calls) == 1
    assert calls[0].fact_id == "fact.tool.demo"
    assert calls[0].requested_by == "tool:validate_fact"
    assert result == {
        "fact_id": "fact.tool.demo",
        "validated": False,
        "epistemic_state": None,
        "reason": "insufficient_evidence",
        "justification": "Needs more independent evidence.",
    }


def test_validate_fact_rejects_malformed_actor_before_gateway(monkeypatch) -> None:
    from core import tool_handlers as handlers

    class UnexpectedGateway:
        def promote(self, request):  # pragma: no cover - must never run
            raise AssertionError(f"unexpected gateway call: {request}")

    monkeypatch.setattr(handlers, "_tool_promotion_gateway", UnexpectedGateway())

    with pytest.raises(ValueError, match="requested_by"):
        handlers.validate_fact("fact.tool.demo", by="UNSAFE ACTOR")
