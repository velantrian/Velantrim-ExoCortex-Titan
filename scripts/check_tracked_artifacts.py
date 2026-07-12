#!/usr/bin/env python3
"""Fail when generated runtime/cache artifacts are tracked by Git."""

from __future__ import annotations

import subprocess
from pathlib import PurePosixPath


def _tracked_files() -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in proc.stdout.split(b"\0") if item]


def _is_forbidden(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = PurePosixPath(normalized).parts

    if normalized == ".coverage" or normalized.startswith(".coverage."):
        return True
    if ".pytest_cache" in parts or ".ruff_cache" in parts:
        return True
    if normalized.startswith("data/backups/"):
        return True
    if normalized.startswith("data/") and normalized.endswith(".jsonl"):
        return True
    return False


def main() -> int:
    forbidden = sorted(path for path in _tracked_files() if _is_forbidden(path))
    if forbidden:
        print("Tracked runtime/cache artifacts are forbidden:")
        for path in forbidden:
            print(f"  - {path}")
        print(f"\n{len(forbidden)} tracked artifact(s) found.")
        return 1

    print("Repository hygiene OK — no tracked runtime/cache artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
