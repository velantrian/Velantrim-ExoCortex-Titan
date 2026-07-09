#!/usr/bin/env python
"""Удаление domain-шаблонов fill_domain_quality (по умолчанию только если остаётся ≥40 фактов)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RU = ROOT / "docs/knowledge/world_skills_core/ru"
sys.path.insert(0, str(ROOT))

from scripts.fill_domain_quality import TRADE, CLINICAL, MUNICIPAL, SCIENCE

MIN_KEEP = 40

SUFFIXES: set[str] = set()
for block in (TRADE, CLINICAL, MUNICIPAL, SCIENCE):
    for item in block:
        SUFFIXES.add(item[0])

SUFFIX_RE = re.compile(
    r"^\|\s*([a-z0-9_.]+)\.\s*("
    + "|".join(re.escape(s) for s in sorted(SUFFIXES, key=len, reverse=True))
    + r")(?:_[a-f0-9]+(?:_\d+)?)?\s*\|",
    re.I,
)


def count_rows(text: str) -> int:
    return sum(
        1
        for l in text.splitlines()
        if l.startswith("|") and not l.startswith("|---") and "ID |" not in l
    )


def is_template_row(line: str) -> bool:
    return bool(SUFFIX_RE.match(line))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--force",
        action="store_true",
        help="Удалить шаблоны даже если файл станет <40 фактов",
    )
    args = ap.parse_args()

    removed = 0
    files = 0
    skipped = 0
    sparse_after: list[tuple[str, int]] = []
    for path in sorted(RU.glob("*.ru.md")):
        if "BATCH" not in path.name:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        data_rows = [
            l
            for l in lines
            if l.startswith("|") and not l.startswith("|---") and "ID |" not in l
        ]
        template_rows = [l for l in data_rows if is_template_row(l)]
        if not template_rows:
            continue
        kept = len(data_rows) - len(template_rows)
        if kept < MIN_KEEP and not args.force:
            skipped += 1
            continue
        if kept < MIN_KEEP:
            sparse_after.append((path.name, kept))
        new_lines = [l for l in lines if not is_template_row(l)]
        text = "\n".join(new_lines)
        if "**KnowledgeUnits:**" in text:
            text = re.sub(
                r"(\*\*KnowledgeUnits:\*\*\s*)\d+",
                rf"\g<1>{count_rows(text)}",
                text,
                count=1,
            )
        if not text.endswith("\n"):
            text += "\n"
        path.write_text(text, encoding="utf-8")
        removed += len(template_rows)
        files += 1
    print(f"Файлов очищено: {files}, пропущено (<{MIN_KEEP}): {skipped}, строк: {removed}")
    if sparse_after:
        print(f"Стало <{MIN_KEEP} фактов: {len(sparse_after)} файлов")
    from core.world_skills_ingest import parse_knowledge_dir

    print(f"Парсер: {len(parse_knowledge_dir())} фактов")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
