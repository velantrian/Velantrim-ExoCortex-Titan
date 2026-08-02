#!/usr/bin/env python3
"""Apply the exact graduated-promotion caller migration.

This script is temporary PR machinery.  The workflow deletes it before the
final branch head is published.
"""

from pathlib import Path


PATH = Path("core/promotion_policy.py")


def replace_once(source: str, old: str, new: str, *, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return source.replace(old, new, 1)


def main() -> None:
    source = PATH.read_text(encoding="utf-8")

    source = replace_once(
        source,
        "from typing import Any\n\n# Доверенные источники",
        "from typing import Any\n\n"
        "from core.promotion_gateway import PromotionGateway, PromotionRequest\n\n"
        "# Доверенные источники",
        label="gateway imports",
    )

    source = replace_once(
        source,
        "    report = PromotionReport()\n\n    try:\n",
        "    report = PromotionReport()\n"
        "    gateway = PromotionGateway(store)\n\n"
        "    try:\n",
        label="gateway construction",
    )

    source = replace_once(
        source,
        "                ok = store.validate_and_promote(fid, by=\"graduated_promotion\").passed\n"
        "                if not ok:\n",
        "                outcome = gateway.promote(\n"
        "                    PromotionRequest(\n"
        "                        fact_id=str(fid),\n"
        "                        requested_by=\"graduated_promotion\",\n"
        "                    )\n"
        "                )\n"
        "                ok = outcome.receipt.passed\n"
        "                if not ok:\n",
        label="validated promotion call",
    )

    PATH.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()
