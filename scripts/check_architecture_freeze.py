#!/usr/bin/env python3
"""Require an ADR when a PR adds a likely runtime authority surface.

This is intentionally a conservative first-pass guard. It does not prove that a
change is safe; it prevents selected high-risk additions from being merged
without an explicit architecture decision record.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import PurePosixPath
import re
import subprocess
import sys
from typing import Iterable


ADR_PREFIX = "docs/adr/"
RUNTIME_PREFIXES = ("core/", "api/", "migrations/", ".github/workflows/")
RUNTIME_FILES = {"server.py"}
EXCLUDED_PREFIXES = ("tests/", "scripts/", "docs/", "research/")


@dataclass(frozen=True, slots=True)
class FreezeFinding:
    path: str
    line: str
    reason: str


AUTHORITY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("new feature flag", re.compile(r"\bENABLE_[A-Z0-9_]+\b")),
    (
        "canonical or epistemic write path",
        re.compile(
            r"\b(?:transition_esm|validate_and_promote|store_fact|upsert_fact|"
            r"supersede_fact_cas|write_tombstone)\s*\("
        ),
    ),
    (
        "background execution authority",
        re.compile(
            r"\b(?:asyncio\.create_task|create_task|add_job|BackgroundTasks)\s*\("
        ),
    ),
    (
        "remote transport construction",
        re.compile(
            r"\b(?:httpx\.(?:AsyncClient|Client)|"
            r"requests\.(?:get|post|put|patch|delete))\s*\("
        ),
    ),
    (
        "new authority-shaped class",
        re.compile(r"^\s*class\s+\w*(?:Worker|Scheduler|Controller|Policy|Gate)\b"),
    ),
)


def _runtime_path(path: str) -> bool:
    normalized = PurePosixPath(path).as_posix()
    if normalized in RUNTIME_FILES:
        return True
    if normalized.startswith(EXCLUDED_PREFIXES):
        return False
    return normalized.startswith(RUNTIME_PREFIXES)


def _has_decision_adr(changed_files: Iterable[str]) -> bool:
    for path in changed_files:
        normalized = PurePosixPath(path).as_posix()
        if not normalized.startswith(ADR_PREFIX) or not normalized.endswith(".md"):
            continue
        name = PurePosixPath(normalized).name.upper()
        if name not in {"README.MD", "ADR-TEMPLATE.MD"}:
            return True
    return False


def scan_diff(diff_text: str) -> tuple[FreezeFinding, ...]:
    current_path = ""
    findings: list[FreezeFinding] = []
    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git a/"):
            parts = raw_line.split(" b/", maxsplit=1)
            current_path = parts[1] if len(parts) == 2 else ""
            continue
        if not current_path or not _runtime_path(current_path):
            continue
        if not raw_line.startswith("+") or raw_line.startswith("+++"):
            continue
        added = raw_line[1:]
        for reason, pattern in AUTHORITY_PATTERNS:
            if pattern.search(added):
                findings.append(
                    FreezeFinding(path=current_path, line=added.strip(), reason=reason)
                )
    return tuple(findings)


def evaluate_freeze(
    diff_text: str, changed_files: Iterable[str]
) -> tuple[bool, tuple[FreezeFinding, ...]]:
    findings = scan_diff(diff_text)
    return (not findings or _has_decision_adr(changed_files)), findings


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _load_pr_diff(base_ref: str) -> tuple[str, tuple[str, ...]]:
    remote_ref = f"origin/{base_ref}"
    try:
        _run_git("rev-parse", "--verify", remote_ref)
    except subprocess.CalledProcessError:
        _run_git("fetch", "origin", base_ref, "--depth=1")
    diff_text = _run_git("diff", f"{remote_ref}...HEAD", "--")
    changed = tuple(
        line.strip()
        for line in _run_git("diff", "--name-only", f"{remote_ref}...HEAD", "--").splitlines()
        if line.strip()
    )
    return diff_text, changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="Base branch to compare with")
    parser.add_argument("--diff-file", help="Read a prepared unified diff")
    parser.add_argument("--changed-file", action="append", default=[])
    args = parser.parse_args()

    if args.diff_file:
        with open(args.diff_file, encoding="utf-8") as handle:
            diff_text = handle.read()
        changed_files = tuple(args.changed_file)
    else:
        base_ref = args.base or os.environ.get("GITHUB_BASE_REF", "").strip()
        if not base_ref:
            print("Architecture freeze guard: no PR base ref; skipped.")
            return 0
        diff_text, changed_files = _load_pr_diff(base_ref)

    allowed, findings = evaluate_freeze(diff_text, changed_files)
    if allowed:
        if findings:
            print("Architecture freeze guard: authority markers covered by an ADR.")
        else:
            print("Architecture freeze guard: no authority markers detected.")
        return 0

    print("Architecture freeze guard: ADR_REQUIRED", file=sys.stderr)
    print(
        "Add a concrete decision record under docs/adr/ (not README/template) "
        "or remove the new authority surface.",
        file=sys.stderr,
    )
    for finding in findings:
        print(
            f"  {finding.path}: {finding.reason}: {finding.line}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
