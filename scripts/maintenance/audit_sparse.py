#!/usr/bin/env python
"""Read-only audit of sparse RU world-skills batch files."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RU = REPO_ROOT / "docs/knowledge/world_skills_core/ru"


def count_rows(text: str) -> int:
    return sum(
        1
        for line in text.splitlines()
        if line.startswith("|") and not line.startswith("|---") and "ID |" not in line
    )


def get_ns(text: str) -> str:
    match = re.search(r"\*\*Namespace:\*\*\s*`([^`]+)`", text)
    return match.group(1) if match else "?"


def main() -> None:
    cats: Counter[str] = Counter()
    sparse: list[tuple[int, str, str]] = []
    for file_path in sorted(RU.glob("*.ru.md")):
        text = file_path.read_text(encoding="utf-8")
        row_count = count_rows(text)
        if row_count < 40:
            namespace = get_ns(text)
            base = namespace.split(".")[0]
            cats[base] += 1
            sparse.append((row_count, file_path.name, namespace))
    print(f"sparse count: {len(sparse)}")
    print("by prefix:", cats.most_common(25))
    ops = sum(1 for _, _, namespace in sparse if "ops" in namespace)
    print(f"ops-like namespaces: {ops}")
    need = sum(max(0, 45 - row_count) for row_count, _, _ in sparse)
    print(f"facts needed to reach 45: {need}")
    if sparse:
        print("--- sparse files ---")
        for row_count, name, namespace in sparse:
            print(row_count, name, namespace)


if __name__ == "__main__":
    main()
