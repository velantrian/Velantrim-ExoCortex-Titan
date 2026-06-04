#!/usr/bin/env python3
"""
scripts/sync_docs.py — Velantrim ExoCortex documentation sync
==============================================================

Автоматически обновляет цифры в README.md, INVARIANTS.md, LIMITATIONS.md
из живых источников:
  - Версия       → pyproject.toml [project].version
  - Число тестов → pytest --collect-only -q
  - Coverage     → coverage report --format=total
  - Дата релиза  → текущая дата (UTC)

Закрывает класс багов «документация расходится с кодом», который привёл
к нескольким раундам аудита (README v8.5.0 при pyproject 8.3.0).

Использование:
    python scripts/sync_docs.py             # обновить in-place
    python scripts/sync_docs.py --check     # CI: упасть если расхождение
    python scripts/sync_docs.py --dry-run   # показать diff без записи

Placeholder'ы в документах (комментарии HTML — не показываются при рендере):
    <!-- SYNC:VERSION -->v8.4.0<!-- /SYNC:VERSION -->
    <!-- SYNC:TESTS -->256<!-- /SYNC:TESTS -->
    <!-- SYNC:COVERAGE -->86%<!-- /SYNC:COVERAGE -->
    <!-- SYNC:DATE -->May 2026<!-- /SYNC:DATE -->

Скрипт работает идемпотентно: повторный запуск без изменений → no-op.

CI integration (.github/workflows/sync-docs.yml):
    - run: python scripts/sync_docs.py --check
    Если расхождение — workflow упадёт с понятным сообщением.

Author: Velantrim audit team
Since: v8.4.0
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# ─── Конфигурация ──────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent

# Файлы которые синхронизируем. Можно расширить.
TARGETS = [
    ROOT / "README.md",
    ROOT / "docs" / "INVARIANTS.md",
    ROOT / "docs" / "LIMITATIONS.md",
]

# Регекспы для placeholder'ов. Используем HTML-комментарии чтобы не портить
# markdown-рендеринг — они невидимы в браузере и на GitHub.
PLACEHOLDERS = {
    "VERSION":  re.compile(r"<!--\s*SYNC:VERSION\s*-->(.*?)<!--\s*/SYNC:VERSION\s*-->"),
    "TESTS":    re.compile(r"<!--\s*SYNC:TESTS\s*-->(.*?)<!--\s*/SYNC:TESTS\s*-->"),
    "COVERAGE": re.compile(r"<!--\s*SYNC:COVERAGE\s*-->(.*?)<!--\s*/SYNC:COVERAGE\s*-->"),
    "DATE":     re.compile(r"<!--\s*SYNC:DATE\s*-->(.*?)<!--\s*/SYNC:DATE\s*-->"),
}


# ─── Источники данных ──────────────────────────────────────────────────────

def get_version_from_pyproject() -> str:
    """Читает [project].version из pyproject.toml без зависимостей."""
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.exists():
        raise FileNotFoundError(f"pyproject.toml не найден в {ROOT}")

    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^\s*version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise ValueError("Не нашёл version = \"...\" в pyproject.toml")
    return match.group(1)


def get_tests_count() -> int:
    """Считает реальное число тестов через `pytest --collect-only -q`."""
    try:
        result = subprocess.run(
            ["pytest", "--collect-only", "-q", "tests/"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        print(f"⚠️  pytest недоступен ({exc}). Считаю руками через grep.", file=sys.stderr)
        return _count_tests_via_grep()

    # pytest 9 в --collect-only -q выводит "N tests collected" в конце
    match = re.search(r"(\d+)\s+tests?\s+collected", result.stdout + result.stderr)
    if match:
        return int(match.group(1))

    # Fallback: считаем строки вида "tests/test_*.py::test_*"
    lines = [
        line for line in result.stdout.splitlines()
        if "::" in line and "test_" in line
    ]
    return len(lines) if lines else _count_tests_via_grep()


def _count_tests_via_grep() -> int:
    """Fallback: считаем `def test_` во всех test_*.py."""
    tests_dir = ROOT / "tests"
    if not tests_dir.exists():
        return 0
    count = 0
    for test_file in tests_dir.glob("test_*.py"):
        text = test_file.read_text(encoding="utf-8", errors="ignore")
        count += len(re.findall(r"^\s*(?:async\s+)?def\s+test_", text, re.MULTILINE))
    return count


def get_coverage_percent() -> str:
    """Читает coverage через `coverage report`."""
    try:
        result = subprocess.run(
            ["coverage", "report", "--format=total"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return f"{result.stdout.strip()}%"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback — пишем "N/A" честно, не выдумываем
    return "N/A"


def get_release_date() -> str:
    """Текущая дата формата 'May 2026'."""
    return datetime.now(UTC).strftime("%B %Y")


# ─── Логика синхронизации ──────────────────────────────────────────────────

def collect_truths() -> dict[str, str]:
    """Собирает живые значения из источников."""
    return {
        "VERSION":  f"v{get_version_from_pyproject()}",
        "TESTS":    str(get_tests_count()),
        "COVERAGE": get_coverage_percent(),
        "DATE":     get_release_date(),
    }


def apply_to_text(text: str, truths: dict[str, str]) -> tuple[str, list[str]]:
    """
    Заменяет placeholder'ы. Возвращает (new_text, changes_log).
    Если placeholder'а нет — пропускаем (молча).
    """
    changes: list[str] = []
    for key, pattern in PLACEHOLDERS.items():
        new_value = truths[key]

        def replacer(match: re.Match) -> str:
            old = match.group(1).strip()
            if old != new_value:
                changes.append(f"  {key}: {old!r} → {new_value!r}")
            return f"<!-- SYNC:{key} -->{new_value}<!-- /SYNC:{key} -->"

        text = pattern.sub(replacer, text)
    return text, changes


def process_file(path: Path, truths: dict[str, str], dry_run: bool, check: bool) -> bool:
    """Обрабатывает один файл. Возвращает True если были изменения."""
    if not path.exists():
        print(f"⚠️  {path.relative_to(ROOT)} не найден — пропуск.")
        return False

    original = path.read_text(encoding="utf-8")
    updated, changes = apply_to_text(original, truths)

    if not changes:
        return False

    rel = path.relative_to(ROOT)
    if check:
        print(f"❌ {rel} — расхождение:")
        for ch in changes:
            print(ch)
        return True

    if dry_run:
        print(f"🔍 {rel} — изменения (dry-run):")
    else:
        path.write_text(updated, encoding="utf-8")
        print(f"✅ {rel} — обновлён:")
    for ch in changes:
        print(ch)
    return True


# ─── CLI ───────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Синхронизация документации Velantrim с живыми источниками."
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Только проверка: упасть если есть расхождения (для CI)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Показать diff без записи в файлы."
    )
    args = parser.parse_args()

    print("🔄 Velantrim sync_docs — собираю живые цифры...")
    truths = collect_truths()
    print("📊 Истина из источников:")
    for k, v in truths.items():
        print(f"   {k:10s} = {v}")
    print()

    any_changes = False
    for path in TARGETS:
        if process_file(path, truths, args.dry_run, args.check):
            any_changes = True

    if args.check and any_changes:
        print("\n❌ FAIL: документация расходится с кодом. "
              "Запусти `python scripts/sync_docs.py` локально.")
        return 1

    if not any_changes:
        print("✨ Документация уже синхронизирована.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
