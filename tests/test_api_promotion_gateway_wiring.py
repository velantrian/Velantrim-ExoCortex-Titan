from __future__ import annotations

import ast
from pathlib import Path


SERVER = Path(__file__).resolve().parents[1] / "server.py"


def _transition_block() -> str:
    source = SERVER.read_text(encoding="utf-8")
    start = source.index('@app.patch("/facts/{fact_id}/transition"')
    end = source.index("\n\n@app.", start + 10)
    return source[start:end]


def _server_tree() -> ast.Module:
    return ast.parse(SERVER.read_text(encoding="utf-8"), filename=str(SERVER))


def _transition_node(tree: ast.Module) -> ast.AsyncFunctionDef:
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "transition_fact":
            return node
    raise AssertionError("transition_fact endpoint was not found")


def test_validated_api_transition_uses_single_gateway_boundary() -> None:
    source = SERVER.read_text(encoding="utf-8")
    block = _transition_block()
    tree = _server_tree()
    transition = _transition_node(tree)

    assert "from core.promotion_gateway import PromotionGateway, PromotionRequest" in source
    assert "_promotion_gateway = PromotionGateway(_store)" in source
    assert block.count("_promotion_gateway.promote") == 1
    assert "PromotionRequest(fact_id=fact_id, requested_by=actor_id)" in block

    # Ignore documentation/comments and inspect only executable syntax. The API
    # endpoint must not call the old authority directly, whether as an imported
    # name or as an attribute on another object.
    assert not any(
        isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name)
            and node.func.id == "validate_and_promote"
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == "validate_and_promote"
        )
        for node in ast.walk(transition)
    )

    memory_imports = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "core.memory"
        for alias in node.names
    }
    assert "validate_and_promote" not in memory_imports


def test_api_error_mapping_uses_transient_snapshot_not_receipt() -> None:
    block = _transition_block()

    assert "verdict = outcome.verdict" in block
    assert 'verdict.reason_code == "not_found"' in block
    assert 'verdict.reason_code == "concurrent_modification"' in block
    assert '"reason": verdict.reason_code' in block
    assert '"justification": verdict.justification' in block
    assert '"mode": verdict.mode.value' in block
    assert "outcome.receipt.justification" not in block


def test_non_validated_transition_path_remains_direct_esm() -> None:
    block = _transition_block()

    assert "transition_esm, fact_id, req.new_state, actor_id" in block
