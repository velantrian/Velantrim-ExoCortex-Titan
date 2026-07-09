#!/usr/bin/env python
"""Исправление ошибочной замены ledger (бухгалтерия vs терраса)."""
from __future__ import annotations

import re
from pathlib import Path

RU = Path(__file__).resolve().parents[1] / "docs/knowledge/world_skills_core/ru"

# Падежи строительной «лагерной доски»
CASE_FIXES = [
    ("между лагерная доска", "между лагерной доской"),
    ("Гнилой лагерная доска", "Гнилая лагерная доска"),
    ("Приоритет лагерная доска", "Приоритет — лагерная доска"),
    ("Пропуск лагерная доска", "Пропуск лагерной доски"),
    ("у лагерная доска", "у лагерной доски"),
    ("Inspection лагерная доска", "Инспекция лагерной доски"),
    ("работе у лагерная доска", "работе у лагерной доски"),
    ("влаги у лагерная доска", "влаги у лагерной доски"),
    ("доска у лагерная доска", "доска у лагерной доски"),
    ("навешиваются на лагерная доска", "крепятся к лагерной доске"),
    ("Крепление лагерная доска", "Крепление лагерной доски"),
    ("над лагерной доскиом", "над лагерной доской"),
    ("поверх лагерной доскиа", "поверх лагерной доски"),
    ("за лагерная доска гноить", "за лагерной доской — гниение"),
    ("через лагерная доска", "к лагерной доске"),
]

FILE_FIXES: dict[str, list[tuple[str, str]]] = {
    "191_BATCH_179_PROPERTY_MANAGEMENT_LEASING_OPERATIONS.ru.md": [
        (
            "| propops.financial.лагерная доска | Книга арендаторов |",
            "| propops.financial.tenant_ledger | Книга арендаторов |",
        ),
    ],
    "421_BATCH_409_CRISIS_RENT_UTILITY_ASSISTANCE_INTAKE_OPERATIONS.ru.md": [
        (
            "| rentutilityintakeops.landlord.лагерная доска | книга аренды |",
            "| rentutilityintakeops.landlord.rent_ledger | Книга аренды |",
        ),
    ],
}


def main() -> None:
    changed = 0
    for path in RU.glob("*.ru.md"):
        text = path.read_text(encoding="utf-8")
        orig = text
        for old, new in CASE_FIXES:
            text = text.replace(old, new)
        for old, new in FILE_FIXES.get(path.name, []):
            text = text.replace(old, new)
        if text != orig:
            path.write_text(text, encoding="utf-8")
            changed += 1
    print(f"Исправлено файлов: {changed}")


if __name__ == "__main__":
    main()
