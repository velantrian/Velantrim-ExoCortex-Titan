#!/usr/bin/env python
"""Аудит неполных batch-файлов."""
from __future__ import annotations
import re
from collections import Counter
from pathlib import Path

RU = Path(__file__).resolve().parents[1] / "docs/knowledge/world_skills_core/ru"


def count_rows(text: str) -> int:
    return sum(
        1
        for l in text.splitlines()
        if l.startswith("|") and not l.startswith("|---") and "ID |" not in l
    )


def get_ns(text: str) -> str:
    m = re.search(r"\*\*Namespace:\*\*\s*`([^`]+)`", text)
    return m.group(1) if m else "?"


def main() -> None:
    cats: Counter[str] = Counter()
    sparse: list[tuple[int, str, str]] = []
    for f in sorted(RU.glob("*.ru.md")):
        t = f.read_text(encoding="utf-8")
        n = count_rows(t)
        if n < 40:
            ns = get_ns(t)
            base = ns.split(".")[0]
            cats[base] += 1
            sparse.append((n, f.name, ns))
    print(f"sparse count: {len(sparse)}")
    print("by prefix:", cats.most_common(25))
    ops = sum(1 for _, _, n in sparse if "ops" in n)
    print(f"ops-like namespaces: {ops}")
    need = sum(max(0, 45 - n) for n, _, _ in sparse)
    print(f"facts needed to reach 45: {need}")
    if sparse:
        print("--- sparse files ---")
        for n, name, ns in sparse:
            print(n, name, ns)


if __name__ == "__main__":
    main()
