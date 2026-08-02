#!/usr/bin/env python3
"""Apply the exact ConsolidationEngine PromotionGateway migration.

Temporary PR machinery. The one-shot workflow deletes this script before the
final branch head is published.
"""

from pathlib import Path


PATH = Path("core/consolidation_engine.py")


def replace_once(source: str, old: str, new: str, *, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return source.replace(old, new, 1)


def main() -> None:
    source = PATH.read_text(encoding="utf-8")

    source = replace_once(
        source,
        "from typing import TYPE_CHECKING, Any\n\nif TYPE_CHECKING:",
        "from typing import TYPE_CHECKING, Any\n\n"
        "from core.promotion_gateway import PromotionGateway, PromotionRequest\n\n"
        "if TYPE_CHECKING:",
        label="gateway import",
    )

    source = replace_once(
        source,
        "        self._store = store\n        self.min_confidence = (",
        "        self._store = store\n"
        "        self._promotion_gateway = PromotionGateway(store)\n"
        "        self.min_confidence = (",
        label="gateway construction",
    )

    source = replace_once(
        source,
        "        return self._store.validate_and_promote(fact_id, by=\"consolidation_engine\").passed\n",
        "        outcome = self._promotion_gateway.promote(\n"
        "            PromotionRequest(\n"
        "                fact_id=fact_id,\n"
        "                requested_by=\"consolidation_engine\",\n"
        "            )\n"
        "        )\n"
        "        return outcome.receipt.passed\n",
        label="final validation call",
    )

    PATH.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()
