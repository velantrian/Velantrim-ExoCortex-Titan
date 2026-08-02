from __future__ import annotations

from pathlib import Path


PATH = Path("core/tool_handlers.py")


def _replace_once(source: str, old: str, new: str, *, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact match, found {count}")
    return source.replace(old, new, 1)


source = PATH.read_text(encoding="utf-8")

source = _replace_once(
    source,
    "from core import memory as memory_api\n"
    "from core.pipeline import retrieve\n"
    "from core.tool_registry import PrincipalContext\n\n\n",
    "from core import memory as memory_api\n"
    "from core.pipeline import retrieve\n"
    "from core.promotion_gateway import PromotionGateway, PromotionRequest\n"
    "from core.tool_registry import PrincipalContext\n\n\n"
    "class _CurrentMemoryPromotionStore:\n"
    "    \"\"\"Reload-safe adapter over the currently canonical memory module.\"\"\"\n\n"
    "    def validate_and_promote(\n"
    "        self,\n"
    "        fact_id: str,\n"
    "        by: str = \"truth_gate\",\n"
    "        mode: Any = None,\n"
    "    ) -> Any:\n"
    "        from core import memory as current_memory_api\n\n"
    "        return current_memory_api.validate_and_promote(\n"
    "            fact_id, by=by, mode=mode\n"
    "        )\n\n\n"
    "_tool_promotion_gateway = PromotionGateway(_CurrentMemoryPromotionStore())\n\n\n",
    label="imports and adapter",
)

old_handler = '''def validate_fact(fact_id: str, *, by: str = "tool:validate_fact") -> dict[str, Any]:
    """
    SECURITY (confirmed Codex finding): promote_to_validated() is an internal
    path with no TruthGate/I68 check — server.py's PATCH /facts/{fact_id}/transition
    deliberately routes external Validated transitions through
    validate_and_promote() instead so a weak fact (missing evidence, low
    confidence) can't reach Validated. An MCP guardian/admin caller is exactly
    such an external/untrusted caller, so this handler must use the same path.
    """
    verdict = memory_api.validate_and_promote(fact_id, by=by)
    return {
        "fact_id": fact_id,
        "validated": verdict.passed,
        "epistemic_state": "Validated" if verdict.passed else None,
        "reason": verdict.reason,
        "justification": verdict.justification,
    }
'''

new_handler = '''def validate_fact(fact_id: str, *, by: str = "tool:validate_fact") -> dict[str, Any]:
    """Validate one guardian-tool fact through PromotionGateway.

    The gateway delegates to the existing TruthGate + CAS authority. The
    reload-safe adapter resolves the currently canonical memory module when
    the call executes, so test/runtime store reconstruction cannot leave this
    handler pinned to an obsolete SQLiteGraphStore instance.
    """
    outcome = _tool_promotion_gateway.promote(
        PromotionRequest(fact_id=fact_id, requested_by=by)
    )
    verdict = outcome.verdict
    return {
        "fact_id": fact_id,
        "validated": verdict.passed,
        "epistemic_state": "Validated" if verdict.passed else None,
        "reason": verdict.reason_code,
        "justification": verdict.justification,
    }
'''

source = _replace_once(
    source,
    old_handler,
    new_handler,
    label="validate_fact handler",
)

PATH.write_text(source, encoding="utf-8")
