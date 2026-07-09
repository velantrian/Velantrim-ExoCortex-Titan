#!/usr/bin/env python
"""Удаление ошибочно добавленных строк unknown.ops.*"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RU = ROOT / "docs/knowledge/world_skills_core/ru"
sys.path.insert(0, str(ROOT))

NON_FACT = {
    "00_WORLD_SKILLS_CORE_MAP.ru.md",
    "10_PRACTICAL_FULL_SCOPE_MAP.ru.md",
    "11_AGRO_TEXTILE_INDUSTRY_ECONOMY_SCOPE.ru.md",
    "12_50K_COLLECTION_PROTOCOL.ru.md",
    "99_SOURCE_RULES_AND_COLLECTION_PLAN.ru.md",
}


def count_rows(text: str) -> int:
    return sum(
        1
        for l in text.splitlines()
        if l.startswith("|") and not l.startswith("|---") and "ID |" not in l and "unknown.ops." not in l
    )


def main() -> int:
    removed = 0
    files = 0
    for path in sorted(RU.glob("*.ru.md")):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        new_lines = [l for l in lines if "unknown.ops." not in l]
        n = len(lines) - len(new_lines)
        if not n:
            continue
        removed += n
        files += 1
        new_text = "\n".join(new_lines)
        if "**KnowledgeUnits:**" in new_text:
            new_text = re.sub(
                r"(\*\*KnowledgeUnits:\*\*\s*)\d+",
                rf"\g<1>{count_rows(new_text)}",
                new_text,
                count=1,
            )
        if not new_text.endswith("\n"):
            new_text += "\n"
        path.write_text(new_text, encoding="utf-8")
    print(f"Файлов очищено: {files}, строк удалено: {removed}")
    from core.world_skills_ingest import parse_knowledge_dir

    print(f"Парсер: {len(parse_knowledge_dir())} фактов")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
