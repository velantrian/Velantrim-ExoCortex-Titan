#!/usr/bin/env python
"""Удаление municipal-шаблонов из trade/clinical batch-файлов."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RU = ROOT / "docs/knowledge/world_skills_core/ru"
sys.path.insert(0, str(ROOT))

MUNICIPAL_SUFFIXES = {
    "citizen_intake_triage", "records_privacy_redaction",
    "field_inspection_checklist", "equity_language_access",
    "emergency_activation_plan",
}

MUNICIPAL_NS = (
    "municipal", "public_", "disaster", "election", "envcompliance",
    "longtermrecovery", "evacuation", "emergmgmt", "pubhealth", "crisismh",
    "msw", "sanitation",
)

SUFFIX_RE = re.compile(
    r"^\|\s*([a-z0-9_.]+)\.\s*("
    + "|".join(re.escape(s) for s in MUNICIPAL_SUFFIXES)
    + r")(?:_[a-f0-9]+(?:_\d+)?)?\s*\|",
    re.I,
)


def count_rows(text: str) -> int:
    return sum(
        1
        for l in text.splitlines()
        if l.startswith("|") and not l.startswith("|---") and "ID |" not in l
    )


def is_municipal_file(ns: str, name: str) -> bool:
    blob = f"{ns} {name}".lower()
    return any(k in blob for k in MUNICIPAL_NS)


def main() -> int:
    removed = 0
    files = 0
    for path in sorted(RU.glob("*.ru.md")):
        if "BATCH" not in path.name:
            continue
        text = path.read_text(encoding="utf-8")
        m = re.search(r"\*\*Namespace:\*\*\s*`([^`]+)`", text)
        ns = m.group(1) if m else ""
        if is_municipal_file(ns, path.name):
            continue
        lines = text.splitlines()
        kept = [l for l in lines if not SUFFIX_RE.match(l)]
        n = len(lines) - len(kept)
        if not n:
            continue
        removed += n
        files += 1
        new_text = "\n".join(kept)
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
    print(f"Файлов: {files}, удалено строк: {removed}")
    from core.world_skills_ingest import parse_knowledge_dir

    print(f"Парсер: {len(parse_knowledge_dir())} фактов")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
