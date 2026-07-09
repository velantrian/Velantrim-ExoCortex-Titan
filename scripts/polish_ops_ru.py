#!/usr/bin/env python
"""Полировка ops: глоссарий EN→RU для заголовков и смешанного текста."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RU = ROOT / "docs/knowledge/world_skills_core/ru"
sys.path.insert(0, str(ROOT))

# Заголовки KnowledgeUnit (часто EN из генераторов)
TITLE_GLOSSARY: list[tuple[str, str]] = [
    ("Soft Wash — Wood PSI Limit", "Мягкая мойка — лимит PSI для дерева"),
    ("Stain Prep — Moisture Content", "Подготовка к морилке — влажность древесины"),
    ("Ledger Board — Bolt Inspection", "Лагерная доска — проверка крепежа"),
    ("Joist Rot — Sister Repair", "Гниль балки — сестринский ремонт"),
    ("Board Gap — Drainage Spacing", "Зазор досок — дренаж"),
    ("Composite Deck — Cleaning Protocol", "Композитная терраса — протокол очистки"),
    ("Railing Post — Tension Check", "Стойка перил — проверка крепления"),
    ("Stain — Solid vs Semi-Transparent", "Морилка — плотная vs полупрозрачная"),
    ("Footing — Frost Line Depth", "Опора — глубина промерзания"),
    ("Hidden Fastener — Install Gap", "Скрытый крепёж — зазор установки"),
    ("Sanding — Grit Sequence", "Шлифовка — последовательность зерна"),
    ("Mold — Sodium Percarbonate Treatment", "Плесень — перкарбонат натрия"),
    ("Stair Tread — Nosing Code", "Ступень — свес по норме"),
    ("Baluster Spacing — Child Safety", "Балясины — безопасность детей"),
    ("Penetrating Oil — Application", "Проникающее масло — нанесение"),
    ("Pressure Treated — Drying Time", "Древесина под давлением — сушка"),
    ("Cable Railing — Tension Setup", "Тросовые перила — натяжение"),
    ("Deck Drainage — Slope to Edge", "Дренаж настила — уклон к краю"),
    ("Board Replacement — Color Match", "Замена доски — подбор цвета"),
    ("Handrail Height — ADA Standard", "Высота поручня — норма доступности"),
    ("Annual Inspection — Checklist", "Ежегодный осмотр — чек-лист"),
    ("Strip Old Finish — Chemical", "Снятие старого покрытия — химия"),
    ("Winter Prep — Snow Load", "Подготовка к зиме — снеговая нагрузка"),
    ("Cantilever — Joist Limit", "Консоль — предел вылета балки"),
    ("Low Voltage — Deck Lighting", "Низковольтное освещение террасы"),
    ("Gutter Slope — Quarter Inch Per Foot", "Уклон желоба — 6 мм на метр"),
    ("Hanger Spacing — Max Six Feet", "Крепления — шаг до 1,8 м"),
    ("Seamless — On-Site Machine", "Бесшовный желоб — катка на объекте"),
    ("Downspout — Sizing Rule", "Водосток — правило размера"),
    ("Gutter Guard — Mesh Selection", "Защита желоба — выбор сетки"),
    ("End Cap — Sealant Application", "Заглушка — герметик"),
    ("Fascia Rot — Repair Before Install", "Гниль обшивки — ремонт до монтажа"),
    ("Ice Dam — Heat Cable Option", "Ледяная дамба — греющий кабель"),
    ("Copper Gutter — Patina & Solder", "Медный желоб — патина и пайка"),
    ("Splash Block — Placement", "Отбойник — установка"),
    ("Pitch Adjustment — Low Spot Fix", "Уклон — исправление провисания"),
    ("Leaf Blower — Gutter Cleaning", "Воздуходувка — очистка желоба"),
    ("Box Gutter — Liner Replacement", "Встроенный желоб — замена подкладки"),
    ("Rain Chain — Downspout Alternative", "Дождевая цепь — альтернатива водостоку"),
    ("Color — Coil Stock Match", "Цвет — подбор катушки"),
    ("Expansion — Long Run Joint", "Дилатационный шов — длинный прогон"),
    ("Underground Drain — Connection", "Подземный дренаж — подключение"),
    ("Warranty — Workmanship Terms", "Гарантия — условия работ"),
    ("Ladder — Gutter Work Safety", "Лестница — безопасность на желобах"),
    ("Scupper — Flat Roof Drain", "Воронка — плоская кровля"),
    ("Size — 5 vs 6 Inch K-Style", "Размер — 5 vs 6 дюймов K-style"),
    ("Mitre Corner — Cut & Seal", "Угол — резка и герметизация"),
    ("Fascia Wrap — Before Gutter", "Обшивка фасада — до желоба"),
    ("Cleaning — Frequency Guide", "Чистка — частота"),
    ("Follow-up — обратная связь", "Follow-up — обратная связь"),
    ("Triage — красные флаги", "Триаж — красные флаги"),
]

# Внутритекстовые замены (длинные первыми)
INLINE_GLOSSARY: list[tuple[str, str]] = [
    ("pressure washing", "мойка под давлением"),
    ("soft wash", "мягкая мойка"),
    ("downstream injector", "инжектор поститания"),
    ("upstream injection", "инжектор до насоса"),
    ("surface cleaner", "дисковый очиститель"),
    ("turbo nozzle", "турбо-сопло"),
    ("unloader valve", "разгрузочный клапан"),
    ("bucket test", "тест с ведром"),
    ("dwell time", "время выдержки"),
    ("spot test", "пробный участок"),
    ("water reclaim", "сбор и рециркуляция воды"),
    ("GFCI", "УЗО (GFCI)"),
    ("beltdrive", "ременной привод"),
    ("triplex pump", "триплексный насос"),
    ("axial cam", "аксиальный насос"),
    ("joist hangers", "кронштейны для балок"),
    ("kiln-dried", "камерной сушки"),
    ("face screw", "наружный саморез"),
    ("tack cloth", "липкая ткань для пыли"),
    ("oxalic acid", "щавелевая кислота"),
    ("sodium percarbonate", "перкарбонат натрия"),
    ("sodium hypochlorite", "гипохлорит натрия"),
    ("degreaser", "обезжириватель"),
    ("makeup air", "приточный воздух"),
    ("backdraft", "обратная тяга"),
    ("fall protection", "страховка от падения"),
    ("toolbox talk", "инструктаж на 5 минут"),
    ("change order", "дополнительное соглашение"),
    ("scope creep", "раздувание объёма работ"),
    ("chargeback", "возврат платежа"),
    ("follow-up", "контрольный звонок"),
    ("walkthrough", "обход с заказчиком"),
    ("time-out", "пауза безопасности"),
    ("shared decision-making", "совместное принятие решения"),
    ("door-to-balloon", "время до баллона"),
    ("readmission", "повторная госпитализация"),
    ("teach-back", "метод обратного обучения"),
]


def polish_text(text: str) -> str:
    for old, new in TITLE_GLOSSARY:
        text = text.replace(old, new)
    for old, new in INLINE_GLOSSARY:
        text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)
    return text


def main() -> int:
    changed = 0
    cells = 0
    for path in sorted(RU.glob("*.ru.md")):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        out: list[str] = []
        file_changed = False
        ku_idx = claim_idx = practical_idx = None

        for line in lines:
            if not line.lstrip().startswith("|"):
                out.append(line)
                continue
            parts = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(parts) < 3:
                out.append(line)
                continue
            low = [c.lower().strip("` ") for c in parts]
            if "id" in low and "суть" in low:
                ku_idx = low.index("knowledgeunit") if "knowledgeunit" in low else 1
                claim_idx = low.index("суть")
                practical_idx = low.index("практический смысл") if "практический смысл" in low else None
                out.append(line)
                continue
            if all(set(c) <= set("-: ") for c in parts if c):
                out.append(line)
                continue
            fid = parts[0].strip("` ")
            if not fid or fid.lower() == "id":
                out.append(line)
                continue

            new_parts = list(parts)
            for idx in (ku_idx, claim_idx, practical_idx):
                if idx is None or idx >= len(new_parts):
                    continue
                polished = polish_text(new_parts[idx])
                if polished != new_parts[idx]:
                    new_parts[idx] = polished
                    cells += 1
                    file_changed = True
            out.append("| " + " | ".join(new_parts) + " |")

        if file_changed:
            new_text = "\n".join(out)
            if not new_text.endswith("\n"):
                new_text += "\n"
            path.write_text(new_text, encoding="utf-8")
            changed += 1
    print(f"Файлов изменено: {changed}, ячеек: {cells}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
