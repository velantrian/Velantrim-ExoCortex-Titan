#!/usr/bin/env python3
"""One-shot exact hardening patch for PR #155; removed before final review."""

from __future__ import annotations

from pathlib import Path


MODULE = Path("core/erasure_startup_recovery.py")
TESTS = Path("tests/test_erasure_startup_recovery.py")
DOCS = Path("docs/operations/erasure-startup-recovery-contract.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one target, found {count}")
    return text.replace(old, new)


def patch_module() -> None:
    text = MODULE.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "from enum import Enum\nfrom typing import Any, Iterable\n",
        "from enum import Enum\nimport re\nfrom typing import Any, Iterable\n",
        "import",
    )
    text = replace_once(
        text,
        'ERASURE_STARTUP_RECOVERY_SCHEMA_VERSION = "titan.erasure-startup-recovery.v1"\n',
        'ERASURE_STARTUP_RECOVERY_SCHEMA_VERSION = "titan.erasure-startup-recovery.v1"\n_SAFE_ERROR_CODE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")\n',
        "pattern",
    )
    text = replace_once(
        text,
        '''def _canonical_codes(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({_required_text(value, "error_code") for value in values}))
''',
        '''def _safe_error_code(value: str, name: str = "error_code") -> str:
    code = _required_text(value, name)
    if _SAFE_ERROR_CODE.fullmatch(code) is None:
        raise ErasureStartupRecoveryError(
            f"{name} must be lower_snake_case and at most 64 characters"
        )
    return code


def _canonical_codes(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({_safe_error_code(value) for value in values}))
''',
        "code validator",
    )
    text = replace_once(
        text,
        '''        object.__setattr__(
            self, "error_code", _required_text(self.error_code, "error_code")
        )
''',
        '''        object.__setattr__(
            self, "error_code", _safe_error_code(self.error_code)
        )
''',
        "failure code",
    )
    MODULE.write_text(text, encoding="utf-8")


def patch_tests() -> None:
    text = TESTS.read_text(encoding="utf-8")
    addition = '''


def test_error_codes_reject_untyped_or_sensitive_text() -> None:
    with pytest.raises(ErasureStartupRecoveryError, match="lower_snake_case"):
        _domain(
            RecoveryDomain.SINGLE_FACT,
            selected=1,
            attempted=1,
            failed=1,
            error_codes=("Database failed at /secret/path",),
        )

    with pytest.raises(ErasureStartupRecoveryError, match="lower_snake_case"):
        StartupRecoveryFailureReceipt(
            run_id="failed-sensitive",
            started_at_utc="2026-08-02T12:00:00Z",
            failed_at_utc="2026-08-02T12:00:00Z",
            budget=StartupRecoveryBudget(
                max_single_jobs=1,
                max_batches=0,
                time_budget_ms=1_000,
            ),
            error_code="sqlite3.ProgrammingError: /private/db.sqlite",
        )
'''
    if "def test_error_codes_reject_untyped_or_sensitive_text" in text:
        raise SystemExit("test already present")
    TESTS.write_text(text.rstrip() + addition + "\n", encoding="utf-8")


def patch_docs() -> None:
    text = DOCS.read_text(encoding="utf-8")
    old = "If recovery cannot produce measured domain outcomes because its observer, jobs schema or database fails first, callers must emit `StartupRecoveryFailureReceipt`. It derives `OBSERVER_FAILED`, carries only a typed safe error code and cannot pretend that zero violations were observed.\n"
    new = old + "\nAll recovery error codes are restricted to lower-case `snake_case` identifiers of at most 64 characters. Exception messages, paths, SQL text and payload fragments are invalid receipt data and belong only in protected server logs.\n"
    DOCS.write_text(replace_once(text, old, new, "docs"), encoding="utf-8")


def main() -> int:
    patch_module()
    patch_tests()
    patch_docs()
    print("Applied PR #155 safe error-code hardening")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
