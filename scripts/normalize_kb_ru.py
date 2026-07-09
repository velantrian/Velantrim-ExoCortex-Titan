#!/usr/bin/env python
"""
Нормализация KB: архив EN → en/, исправление заголовков/номеров батчей, перевод ru на русский.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RU_DIR = ROOT / "docs/knowledge/world_skills_core/ru"
EN_DIR = ROOT / "docs/knowledge/world_skills_core/en"
CACHE_PATH = ROOT / "data/kb_translation_cache.json"
NON_FACT = frozenset({
    "00_WORLD_SKILLS_CORE_MAP.ru.md",
    "10_PRACTICAL_FULL_SCOPE_MAP.ru.md",
    "11_AGRO_TEXTILE_INDUSTRY_ECONOMY_SCOPE.ru.md",
    "12_50K_COLLECTION_PROTOCOL.ru.md",
    "99_SOURCE_RULES_AND_COLLECTION_PLAN.ru.md",
})


def cyr_ratio(s: str) -> float:
    if not s:
        return 0.0
    cyr = sum(1 for ch in s if "\u0400" <= ch <= "\u04FF")
    lat = sum(1 for ch in s if ch.isascii() and ch.isalpha())
    total = cyr + lat
    return cyr / total if total else 0.0


def needs_translation(s: str, threshold: float = 0.45) -> bool:
    if not s or len(s.strip()) < 2:
        return False
    return cyr_ratio(s) < threshold


def load_cache() -> dict[str, str]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")


def get_translator():
    from deep_translator import GoogleTranslator
    return GoogleTranslator(source="en", target="ru")


def translate_text(text: str, cache: dict[str, str], translator, delay: float = 0.02) -> str:
    key = text.strip()
    if not key:
        return text
    if key in cache:
        return cache[key]
    if not needs_translation(key, 0.45):
        cache[key] = key
        return key
    try:
        if len(key) > 4500:
            parts = []
            for i in range(0, len(key), 4500):
                time.sleep(delay)
                parts.append(translator.translate(key[i : i + 4500]))
            result = "".join(parts)
        else:
            time.sleep(delay)
            result = translator.translate(key)
        cache[key] = result
        return result
    except Exception as exc:
        print(f"  ⚠ перевод пропущен ({exc}): {key[:60]}...")
        cache[key] = key
        return key


def count_data_rows(text: str) -> int:
    n = 0
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        low = [c.lower().strip("` ") for c in cells]
        if "id" in low and "суть" in low:
            continue
        if all(set(c) <= set("-: ") for c in cells if c):
            continue
        fid = cells[0].strip("` ")
        if fid and fid.lower() != "id":
            n += 1
    return n


def archive_to_en() -> int:
    EN_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for path in sorted(RU_DIR.glob("*.ru.md")):
        if path.name in NON_FACT:
            continue
        dest = EN_DIR / path.name.replace(".ru.md", ".en.md")
        if not dest.exists():
            shutil.copy2(path, dest)
            n += 1
    print(f"📦 Архив EN: скопировано {n} новых файлов → {EN_DIR}")
    return n


def fix_headers() -> int:
    fixed = 0
    for path in sorted(RU_DIR.glob("*.ru.md")):
        if path.name in NON_FACT:
            continue
        text = path.read_text(encoding="utf-8")
        actual = count_data_rows(text)
        if actual == 0:
            continue
        new_text, n = re.subn(
            r"(\*\*KnowledgeUnits:\*\*\s*)\d+",
            rf"\g<1>{actual}",
            text,
            count=1,
        )
        if n and new_text != text:
            path.write_text(new_text, encoding="utf-8")
            fixed += 1
    print(f"📋 Заголовки KnowledgeUnits исправлены: {fixed} файлов")
    return fixed


def fix_duplicate_batch_numbers() -> int:
    batch_map: dict[int, list[Path]] = {}
    for path in RU_DIR.glob("*BATCH_*.ru.md"):
        m = re.search(r"BATCH_(\d+)", path.name)
        if m:
            batch_map.setdefault(int(m.group(1)), []).append(path)

    max_bn = max(batch_map.keys(), default=891)
    next_bn = max_bn + 1
    renamed = 0

    for bn, paths in sorted(batch_map.items()):
        if len(paths) < 2:
            continue
        paths_sorted = sorted(paths, key=lambda p: p.name)
        for p in paths_sorted[1:]:
            new_bn = next_bn
            next_bn += 1
            new_name = re.sub(r"BATCH_\d+", f"BATCH_{new_bn}", p.name, count=1)
            new_path = p.parent / new_name
            text = p.read_text(encoding="utf-8")
            text = re.sub(r"# BATCH \d+:", f"# BATCH {new_bn}:", text, count=1)
            new_path.write_text(text, encoding="utf-8")
            p.unlink()
            en_old = EN_DIR / p.name.replace(".ru.md", ".en.md")
            if en_old.exists():
                en_new = EN_DIR / new_name.replace(".ru.md", ".en.md")
                en_old.rename(en_new)
            renamed += 1
    print(f"🔢 Дубли BATCH_N переименованы: {renamed} файлов")
    return renamed


def collect_unique_strings() -> set[str]:
    """Собрать уникальные строки для перевода из всех ru-файлов."""
    unique: set[str] = set()
    for path in sorted(RU_DIR.glob("*.ru.md")):
        if path.name in NON_FACT:
            continue
        claim_idx = ku_idx = practical_idx = None
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                continue
            low = [c.lower().strip("` ") for c in cells]
            if "id" in low and "суть" in low:
                claim_idx = low.index("суть")
                ku_idx = low.index("knowledgeunit") if "knowledgeunit" in low else 1
                practical_idx = low.index("практический смысл") if "практический смысл" in low else None
                continue
            if all(set(c) <= set("-: ") for c in cells if c):
                continue
            fid = cells[0].strip("` ")
            if not fid or fid.lower() == "id":
                continue
            for idx, thr in [(ku_idx, 0.35), (claim_idx, 0.45), (practical_idx, 0.45)]:
                if idx is None or idx >= len(cells):
                    continue
                val = cells[idx]
                if needs_translation(val, thr):
                    unique.add(val)
    return unique


def build_translation_cache(delay: float = 0.02, limit: int = 0) -> int:
    """Перевести уникальные строки → кэш (один раз)."""
    cache = load_cache()
    translator = get_translator()
    todo = [s for s in sorted(collect_unique_strings()) if s not in cache]
    if limit:
        todo = todo[:limit]
    print(f"🌐 Уникальных строк к переводу: {len(todo)} (кэш: {len(cache)})")
    for i, s in enumerate(todo, 1):
        translate_text(s, cache, translator, delay)
        if i % 100 == 0:
            save_cache(cache)
            print(f"  … {i}/{len(todo)}")
    save_cache(cache)
    print(f"✅ Кэш перевода: {len(cache)} записей → {CACHE_PATH}")
    return len(todo)


def apply_cache_to_files() -> dict[str, int]:
    """Применить кэш ко всем ru-файлам (без API)."""
    cache = load_cache()
    stats = {"files": 0, "cells": 0}
    for path in sorted(RU_DIR.glob("*.ru.md")):
        if path.name in NON_FACT:
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        out: list[str] = []
        claim_idx = ku_idx = practical_idx = None
        changed = False

        for line in lines:
            if not line.lstrip().startswith("|"):
                out.append(line)
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                out.append(line)
                continue
            low = [c.lower().strip("` ") for c in cells]
            if "id" in low and "суть" in low:
                claim_idx = low.index("суть")
                ku_idx = low.index("knowledgeunit") if "knowledgeunit" in low else 1
                practical_idx = low.index("практический смысл") if "практический смысл" in low else None
                out.append(line)
                continue
            if all(set(c) <= set("-: ") for c in cells if c):
                out.append(line)
                continue
            fid = cells[0].strip("` ")
            if not fid or fid.lower() == "id":
                out.append(line)
                continue

            new_cells = list(cells)
            for idx, thr in [(ku_idx, 0.35), (claim_idx, 0.45), (practical_idx, 0.45)]:
                if idx is None or idx >= len(new_cells):
                    continue
                val = new_cells[idx]
                if needs_translation(val, thr) and val in cache:
                    new_cells[idx] = cache[val]
                    stats["cells"] += 1
                    changed = True
                elif needs_translation(val, thr) and val.strip() in cache:
                    new_cells[idx] = cache[val.strip()]
                    stats["cells"] += 1
                    changed = True

            out.append("| " + " | ".join(new_cells) + " |")

        if changed:
            path.write_text("\n".join(out) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
            stats["files"] += 1

    print(f"📝 Применён кэш: файлов={stats['files']}, ячеек={stats['cells']}")
    return stats


def translate_ru_files(limit_unique: int = 0, delay: float = 0.02) -> None:
    build_translation_cache(delay=delay, limit=limit_unique)
    apply_cache_to_files()


def main() -> int:
    ap = argparse.ArgumentParser(description="Нормализация и русификация World Skills Core KB")
    ap.add_argument("--archive", action="store_true")
    ap.add_argument("--fix-headers", action="store_true")
    ap.add_argument("--fix-batch-dupes", action="store_true")
    ap.add_argument("--translate", action="store_true", help="Перевести (кэш + применение)")
    ap.add_argument("--translate-cache-only", action="store_true", help="Только наполнить кэш")
    ap.add_argument("--apply-cache", action="store_true", help="Только применить кэш")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--limit-unique", type=int, default=0)
    ap.add_argument("--delay", type=float, default=0.02)
    args = ap.parse_args()

    if not any([args.archive, args.fix_headers, args.fix_batch_dupes, args.translate,
                args.translate_cache_only, args.apply_cache, args.all, args.full]):
        ap.print_help()
        return 1

    if args.archive or args.all or args.full:
        archive_to_en()
    if args.fix_headers or args.all or args.full:
        fix_headers()
    if args.fix_batch_dupes or args.all or args.full:
        fix_duplicate_batch_numbers()
    if args.translate_cache_only:
        build_translation_cache(delay=args.delay, limit=args.limit_unique)
    elif args.apply_cache:
        apply_cache_to_files()
    elif args.translate or args.full:
        translate_ru_files(limit_unique=args.limit_unique, delay=args.delay)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
