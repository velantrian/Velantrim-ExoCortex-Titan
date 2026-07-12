#!/usr/bin/env python3
"""
scripts/check_version_branding.py — Version/branding drift guard (Titan 9.0)

Fails if:
  - pyproject.toml [project] name/version drift from the canonical values, or
  - core.__version__ drifts from pyproject.toml, or
  - an active public/runtime entrypoint file still contains a current-brand
    V8.7 string.

Historical documents (CHANGELOG.md, ROADMAP.md, audit/work logs, the
V8.7-origin test file, and the compatibility KDF salt in core/crypto.py) are
intentionally NOT checked here — they document the past, not the current
product, and scrubbing them would destroy real history.
"""
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CANONICAL_NAME = "velantrim-titan"
CANONICAL_VERSION = "9.0.0"

# Active public/runtime surfaces that must present the current Titan 9.0
# brand. Extend this list when a new user-facing entrypoint is added.
CHECKED_FILES = [
    "README.md",
    "README.en.md",
    "pyproject.toml",
    "server.py",
    "core/metrics.py",
    "api/web_console.py",
    "SYSTEM_OVERVIEW.md",
    "SYSTEM_OVERVIEW.en.md",
    ".env.example",
    "scripts/start_console.ps1",
    "docs/CONSOLE_OVERVIEW.ru.md",
    "docs/CONSOLE_BROWSER_TEST.ru.md",
    "requirements-dev.txt",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.dev.yml",
    ".github/workflows/ci.yml",
]

# Files where a historical V8.7 mention is expected and allowed, even though
# they would otherwise be in scope. Kept narrow on purpose — never allowlist
# a whole directory like core/** or docs/**.
ALLOWLIST = {
    "CHANGELOG.md",
    "ROADMAP.md",
    "WORK_LOG.md",
    "COLLAB_JOURNAL.md",
    "AUDIT_ACTION_ITEMS.md",
    "AUDIT_DEEP_2026-06-06.md",
    "research/DEPRECATIONS.md",
    "tests/test_v87_new_modules.py",
    "core/crypto.py",
}

FORBIDDEN_PATTERNS = [
    re.compile(r"VELANTRIM V8\.7 TITAN"),
    re.compile(r"VELANTRIM V8\.7 Titan"),
    re.compile(r"Velantrim ExoCortex V8\.7 Titan"),
    re.compile(r"VELANTRIM_ExoCortex_V8\.7_Titan"),
    re.compile(r"Version:\s*8\.7\.0"),
    re.compile(r"Версия:\s*v?8\.7\.0"),
]


def check_canonical_values() -> list[str]:
    """Verify pyproject.toml and core.__version__ agree on name/version."""
    errors = []
    pp = ROOT / "pyproject.toml"
    data = tomllib.loads(pp.read_text(encoding="utf-8"))
    name = data["project"]["name"]
    version = data["project"]["version"]
    if name != CANONICAL_NAME:
        errors.append(f"pyproject.toml: project.name = {name!r}, expected {CANONICAL_NAME!r}")
    if version != CANONICAL_VERSION:
        errors.append(
            f"pyproject.toml: project.version = {version!r}, expected {CANONICAL_VERSION!r}"
        )

    sys.path.insert(0, str(ROOT))
    import core  # noqa: E402

    if core.__version__ != CANONICAL_VERSION:
        errors.append(f"core.__version__ = {core.__version__!r}, expected {CANONICAL_VERSION!r}")
    return errors


def check_branding() -> list[str]:
    """Scan active entrypoint files for forbidden legacy V8.7 brand strings."""
    errors = []
    for rel in CHECKED_FILES:
        if rel in ALLOWLIST:
            continue
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(line):
                    errors.append(
                        f"{rel}:{lineno}: forbidden legacy brand string: {line.strip()!r}"
                    )
    return errors


def main() -> int:
    errors = check_canonical_values() + check_branding()
    if errors:
        print("Version/branding guard FAILED:\n")
        for e in errors:
            print(f"  - {e}")
        print(f"\n{len(errors)} problem(s) found.")
        return 1
    print("Version/branding guard OK — canonical values and active surfaces are Titan 9.0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
