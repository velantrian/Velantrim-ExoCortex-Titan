#!/usr/bin/env python
"""Исправление структурных ошибок KB и калек автоперевода."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RU = ROOT / "docs/knowledge/world_skills_core/ru"
sys.path.insert(0, str(ROOT))

# Точечные замены калек (EN-термин → корректный русский в контексте)
GLOSSARY: list[tuple[str, str]] = [
    ("Доска бухгалтерской книги", "Лагерная доска"),
    ("крепление и каркас бухгалтерской доски", "крепление лагерной доски и каркас"),
    ("Палуба — крепление", "Терраса — крепление"),
    ("бухгалтерской доски", "лагерной доски"),
    ("Ledger Board", "Лагерная доска"),
    ("ledger board", "лагерная доска"),
    ("Deck — Ledger", "Терраса — лагерная доска"),
    ("Deck building", "Строительство террасы"),
    ("Negative air machine", "Машина отрицательного давления"),
    ("negative air", "отрицательное давление"),
    ("Click & Collect", "Самовывоз онлайн-заказа"),
    ("Mystery shopper", "Тайный покупатель"),
    ("BOPIS", "Самовывоз интернет-заказа"),
    ("Loaner", "Подменное устройство"),
    ("loaner", "подменное устройство"),
    ("Shrink ", "Потери (shrink) "),
    ("shrink ", "потери (shrink) "),
    ("Fill rate", "Процент выполнения поставки"),
    ("Soft wash", "Мягкая мойка"),
    ("soft wash", "мягкая мойка"),
    ("Downstream injector", "Инжектор поститания"),
    ("Surface cleaner", "Дисковый очиститель поверхности"),
    ("Turbo nozzle", "Турбо-сопло"),
    ("Unloader valve", "Разгрузочный клапан"),
    ("Bucket test", "Тест с ведром"),
    ("Dwell time", "Время выдержки химии"),
    ("Post Construction", "После строительных работ"),
    ("Bird mess cleanup", "Уборка загрязнений от птиц"),
    ("Epoxy Grout", "Эпоксидная затирка"),
    ("Soot — Interior Cleanup", "Сажа — уборка внутри помещения"),
    ("Waterhouse-Friderichsen", "Уотерхауса-Фридериксена"),
    ("Jarisch-Herxheimer", "Яриша-Герксгеймера"),
    ("Kaposi Sarcoma", "Саркома Капоши"),
    ("Toxic Shock Syndrome", "Синдром токсического шока"),
    ("Thrombotic Thrombocytopenic Purpura", "Тромботическая тромбоцитопеническая пурпура"),
    ("Grey Turner sign", "Симптом Грея Тернера"),
    ("Cullen's sign", "Симптом Каллена"),
    ("pallor", "бледность"),
    ("koilonychia", "койлонихия"),
    ("atrophic glossitis", "атрофический глоссит"),
    ("petechiae", "петехии"),
    ("perifollicular hemorrhage", "перифолликулярные кровоизлияния"),
    ("акродерматит", "акродерматит"),
    ("GCS", "шкала комы Глазго"),
    ("IMR (Уровень детской смертности)", "Младенческая смертность (IMR)"),
    ("MMR (коэффициент материнской смертности)", "Материнская смертность (MMR)"),
    ("DALY", "DALY (потерянные годы здоровой жизни)"),
    ("QALY", "QALY (годы жизни с поправкой на качество)"),
    ("GBD study", "Исследование GBD"),
    ("Antibiotics + microbiome", "Антибиотики и микробиом"),
    ("Probióticos", "Пробиотики"),
    ("Пробиотики: спорная", "Пробиотики: спорная"),
    ("Thomas Hicks (marathon", "Томас Хикс (марафон"),
    ("Mars mission", "Миссия на Марс"),
    ("VIIP", "синдром VIIP"),
    ("ARED", "тренажёр ARED"),
    ("FMT", "трансплантация фекальной микробиоты (FMT)"),
    ("CDI", "инфекция C. difficile"),
    ("HMP", "проект микробиома человека (HMP)"),
    ("TUE (освобождение", "TUE (терапевтическое использование"),
    ("ВАДА (Всемирное", "ВАДА (Всемирное"),
    ("АДАМС (Система", "АДАМС (система"),
    ("COVID-19: отклонение", "COVID-19: откат"),
    ("Это reversible?", "Восстановимо ли это?"),
    ("разреженных графиков", "разреженных графов"),
    ("плотного (O", "плотных графов (O"),
    ("Флойд-Уоршалл", "Флойда-Уоршелла"),
    ("Дейкстра:", "Дейкстры:"),
    ("Ledger Board — Bolt Inspection", "Лагерная доска — проверка крепежа"),
    ("Deck — Ledger Board Attachment", "Терраса — крепление лагерной доски"),
]


def fix_double_pipes(text: str) -> tuple[str, int]:
    lines = text.splitlines()
    fixed = 0
    out: list[str] = []
    for line in lines:
        if line.startswith("||"):
            out.append("|" + line[2:])
            fixed += 1
        else:
            out.append(line)
    return "\n".join(out), fixed


def apply_glossary(text: str) -> tuple[str, int]:
    count = 0
    for old, new in GLOSSARY:
        if old in text:
            text = text.replace(old, new)
            count += 1
    return text, count


def fix_headers(text: str) -> str:
    rows = sum(
        1
        for l in text.splitlines()
        if l.startswith("|") and not l.startswith("|---") and "ID |" not in l
    )
    return re.sub(r"(\*\*KnowledgeUnits:\*\*\s*)\d+", rf"\g<1>{rows}", text, count=1)


def main() -> int:
    pipe_fixes = 0
    gloss_hits = 0
    files_changed = 0
    for path in sorted(RU.glob("*.ru.md")):
        text = path.read_text(encoding="utf-8")
        orig = text
        text, n = fix_double_pipes(text)
        pipe_fixes += n
        text, g = apply_glossary(text)
        gloss_hits += g
        text = fix_headers(text)
        if text != orig:
            if not text.endswith("\n"):
                text += "\n"
            path.write_text(text, encoding="utf-8")
            files_changed += 1
    print(f"Файлов изменено: {files_changed}")
    print(f"Исправлено строк ||: {pipe_fixes}")
    print(f"Применено замен глоссария (вхождений): {gloss_hits}")
    from core.world_skills_ingest import parse_knowledge_dir

    print(f"Парсер после правок: {len(parse_knowledge_dir())} фактов")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
