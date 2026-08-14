from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_FILES = [ROOT / "server.py", *sorted((ROOT / "core").rglob("*.py"))]


@dataclass(frozen=True, order=True)
class CallSite:
    path: str
    scope: str
    callee: str


class _AuthorityCallVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path.relative_to(ROOT).as_posix()
        self.scope: list[str] = []
        self.sites: set[CallSite] = set()
        self.literal_validated_steps: set[CallSite] = set()

    def _scope_name(self) -> str:
        return ".".join(self.scope) or "<module>"

    @staticmethod
    def _callee_name(node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None

    @staticmethod
    def _literal_target(node: ast.Call) -> str | None:
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            value = node.args[1].value
            return value if isinstance(value, str) else None
        for keyword in node.keywords:
            if keyword.arg in {"target", "new_state"} and isinstance(
                keyword.value, ast.Constant
            ):
                value = keyword.value.value
                return value if isinstance(value, str) else None
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_Call(self, node: ast.Call) -> None:
        callee = self._callee_name(node.func)
        if callee in {"validate_and_promote", "promote_to_validated"}:
            self.sites.add(CallSite(self.path, self._scope_name(), callee))
        if callee in {"transition_esm", "promote_esm_to"}:
            if self._literal_target(node) == "Validated":
                self.literal_validated_steps.add(
                    CallSite(self.path, self._scope_name(), callee)
                )
        self.generic_visit(node)


def _scan() -> tuple[set[CallSite], set[CallSite]]:
    authority_sites: set[CallSite] = set()
    literal_validated_steps: set[CallSite] = set()
    for path in PRODUCTION_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = _AuthorityCallVisitor(path)
        visitor.visit(tree)
        authority_sites.update(visitor.sites)
        literal_validated_steps.update(visitor.literal_validated_steps)
    return authority_sites, literal_validated_steps


def test_direct_single_fact_authority_callers_match_reviewed_inventory() -> None:
    authority_sites, _ = _scan()

    # Exact reviewed boundary. New entries require an ADR and an intentional
    # update to docs/operations/promotion-ownership-inventory.md. World Skills
    # is no longer an exception: C9 routes final Canon admission through
    # PromotionGateway instead of calling the low-level promotion primitive.
    expected = {
        CallSite(
            "core/promotion_gateway.py",
            "PromotionGateway.promote",
            "validate_and_promote",
        ),
        CallSite(
            "core/tool_handlers.py",
            "_CurrentMemoryPromotionStore.validate_and_promote",
            "validate_and_promote",
        ),
        CallSite(
            "core/cognitive_store.py",
            "_CurrentMemoryPromotionStore.validate_and_promote",
            "validate_and_promote",
        ),
        CallSite(
            "core/memory.py",
            "validate_and_promote",
            "validate_and_promote",
        ),
        CallSite(
            "core/memory.py",
            "promote_to_validated",
            "promote_to_validated",
        ),
    }

    assert authority_sites == expected


def test_literal_plain_validated_steps_match_reviewed_primitives() -> None:
    _, literal_validated_steps = _scan()

    # One reviewed low-level compatibility primitive implements its operation
    # through the generic ladder. No business/runtime caller may add another
    # literal Validated step without an ADR and inventory update.
    expected = {
        CallSite(
            "core/memory.py",
            "SQLiteGraphStore.promote_to_validated",
            "promote_esm_to",
        )
    }

    assert literal_validated_steps == expected
