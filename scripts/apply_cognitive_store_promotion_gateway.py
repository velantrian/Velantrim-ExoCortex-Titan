from __future__ import annotations

from pathlib import Path


STORE_PATH = Path("core/cognitive_store.py")
TEST_PATH = Path("tests/test_cognitive_store.py")


def _replace_once(source: str, old: str, new: str, *, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact match, found {count}")
    return source.replace(old, new, 1)


source = STORE_PATH.read_text(encoding="utf-8")
source = _replace_once(
    source,
    "from core.cognitive_fact import (\n"
    "    CognitiveFact,\n"
    "    cognitive_fact_from_store,\n"
    "    load_relations_for_fact,\n"
    ")\n\n"
    "logger = logging.getLogger(__name__)\n\n"
    "_store: CognitiveFactStore | None = None\n",
    "from core.cognitive_fact import (\n"
    "    CognitiveFact,\n"
    "    cognitive_fact_from_store,\n"
    "    load_relations_for_fact,\n"
    ")\n"
    "from core.promotion_gateway import PromotionGateway, PromotionRequest\n\n"
    "logger = logging.getLogger(__name__)\n\n\n"
    "class _CurrentMemoryPromotionStore:\n"
    "    \"\"\"Resolve the canonical memory module for each promotion call.\"\"\"\n\n"
    "    def validate_and_promote(\n"
    "        self,\n"
    "        fact_id: str,\n"
    "        by: str = \"truth_gate\",\n"
    "        mode: Any = None,\n"
    "    ) -> Any:\n"
    "        from core import memory as current_memory\n\n"
    "        return current_memory.validate_and_promote(fact_id, by=by, mode=mode)\n\n\n"
    "_cognitive_promotion_gateway = PromotionGateway(_CurrentMemoryPromotionStore())\n\n"
    "_store: CognitiveFactStore | None = None\n",
    label="imports and gateway adapter",
)

old_transition = '''    def transition(
        self,
        fact_id: str,
        new_state: str,
        *,
        by: str = "cognitive_store",
    ) -> CognitiveFact | None:
        from core.memory import promote_esm_to

        promote_esm_to(fact_id, new_state, by=by)
        _emit_fact_event(fact_id, is_new=False, event_type="fact_esm_transition")
        return self.get(fact_id)
'''

new_transition = '''    def transition(
        self,
        fact_id: str,
        new_state: str,
        *,
        by: str = "cognitive_store",
    ) -> CognitiveFact | None:
        from core.memory import promote_esm_to

        if new_state != "Validated":
            promote_esm_to(fact_id, new_state, by=by)
            _emit_fact_event(fact_id, is_new=False, event_type="fact_esm_transition")
            return self.get(fact_id)

        # Preserve the facade's existing auto-ladder behavior, but stop at
        # Supported. The final authoritative hop is owned by PromotionGateway
        # and the existing TruthGate + CAS transaction.
        if not promote_esm_to(fact_id, "Supported", by=by):
            return self.get(fact_id)

        outcome = _cognitive_promotion_gateway.promote(
            PromotionRequest(fact_id=fact_id, requested_by=by)
        )
        if outcome.receipt.committed:
            _emit_fact_event(
                fact_id,
                is_new=False,
                event_type="fact_esm_transition",
            )
        return self.get(fact_id)
'''
source = _replace_once(
    source,
    old_transition,
    new_transition,
    label="CognitiveFactStore.transition",
)
STORE_PATH.write_text(source, encoding="utf-8")


tests = TEST_PATH.read_text(encoding="utf-8")
tests = _replace_once(
    tests,
    '        cf = CognitiveFactStore.create_observed("x", "s")\n',
    '        cf = CognitiveFactStore.create_observed(\n'
    '            "x",\n'
    '            "s",\n'
    '            confidence=0.95,\n'
    '            metadata={"evidence_refs": ["source-a", "source-b"]},\n'
    '        )\n',
    label="existing positive cognitive transition fixture",
)
TEST_PATH.write_text(tests, encoding="utf-8")
