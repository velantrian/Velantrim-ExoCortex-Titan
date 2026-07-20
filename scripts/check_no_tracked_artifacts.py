#!/usr/bin/env python3
"""CI guard (PR-0): fail if runtime/test-cache artifacts are tracked in git.

These paths were removed from tracking in PR-0 (repo containment). This
guard stops them from being silently re-added in a future commit.

Explicitly NOT covered here (intentionally kept tracked, do not add):
kb_graph.json, data/kb_translation_cache.json — these are knowledge assets,
not runtime/test cache, and must never be untracked by this guard.
"""
import re
import subprocess
import sys

FORBIDDEN_PATTERNS = [
    r"^\.coverage$",
    r"^\.pytest_cache/",
    r"^\.ruff_cache/",
    r"^\.mypy_cache/",
    r"^data/metrics\.jsonl$",
    r"^data/backups/",
]


def main() -> int:
    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout.splitlines()

    violations = [
        path
        for path in tracked
        if any(re.match(pattern, path) for pattern in FORBIDDEN_PATTERNS)
    ]

    if violations:
        print("Tracked runtime/test-cache artifacts found (forbidden by PR-0 hygiene policy):")
        for v in violations:
            print(f"  {v}")
        print(
            "\nThese paths must never be committed. Remove with `git rm --cached <path>` "
            "and confirm .gitignore covers them."
        )
        return 1

    print("OK: no forbidden tracked artifacts found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
