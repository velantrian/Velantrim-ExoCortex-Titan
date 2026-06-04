#!/usr/bin/env python3
"""
Демонстрация ESM на живом примере (без HTTP-сервера).

Запуск из корня проекта:
    python scripts/demo_esm_flow.py

Показывает по шагам:
  1) любой текст → ingest → Observed
  2) /query BALANCED → почему часто пусто
  3) ручной переход → Validated
  4) /query BALANCED с evidence → успех
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Текст может быть ЛЮБЫМ — это просто знание, которое система режет на факты
DEMO_TEXT = (
    "Дельфины — млекопитающие, они дышат лёгкими, а не жабрами. "
    "Скорость дельфина может достигать 55 км/ч."
)
DEMO_SOURCE = "demo_lesson_biology"


def sep(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def show_fact(label: str, fact: dict | None) -> None:
    if not fact:
        print(f"  {label}: (нет)")
        return
    print(f"  {label}:")
    print(f"    fact_id:          {fact.get('fact_id')}")
    print(f"    epistemic_state:  {fact.get('epistemic_state')}")
    print(f"    confidence:       {fact.get('confidence')}")
    print(f"    source:           {fact.get('source')}")
    claim = (fact.get("claim") or "")[:80]
    print(f"    claim:            {claim}{'...' if len(fact.get('claim','')) > 80 else ''}")
    hist = fact.get("history") or []
    if hist:
        last = hist[-1]
        print(f"    history[-1]:      {last.get('from')} → {last.get('state')} by={last.get('by')}")


def main() -> int:
    sep("0. Подготовка: изолированная БД во временной папке")
    tmp = tempfile.mkdtemp(prefix="velantrim_esm_demo_")
    db_path = os.path.join(tmp, "demo.db")
    os.environ["VELANTRIM_DB_PATH"] = db_path
    print(f"  БД: {db_path}")

    # Перезагрузить memory с новым путём
    for mod in list(sys.modules.keys()):
        if mod == "core.memory" or mod.startswith("core."):
            del sys.modules[mod]

    from core import memory
    from core.memory import (
        get_fact,
        make_store,
        store_facts_batch,
        transition_esm,
    )
    from core.pipeline import run as pipeline_run

    store = make_store(db_path)
    memory._GLOBAL_STORE = store
    memory._L0 = store._l0
    memory._DDL_INITIALIZED = store._ddl_initialized_paths

    sep("1. Загрузка текста (как POST /ingest/text)")
    print(f"  Текст:\n    «{DEMO_TEXT}»\n")
    batch = [{
        "fact_id": "demo_dolphins_001",
        "claim": DEMO_TEXT,
        "source": DEMO_SOURCE,
        "confidence": 0.85,
        "metadata": {"demo": True},  # без evidence_refs — как обычный ingest
    }]
    store.store_facts_batch(batch)
    fact = get_fact("demo_dolphins_001")
    show_fact("После ingest", fact)
    print("\n  👉 Состояние всегда Observed — система «увидела», но ещё не «подтвердила».")

    sep("2. Запрос как POST /query mode=BALANCED (дефолт сервера)")
    r1 = pipeline_run("Как дышат дельфины?", cognitive_mode="BALANCED")
    print(f"  error:  {r1.get('error')}")
    print(f"  answer: {r1.get('answer')}")
    print(f"  facts:  {len(r1.get('facts') or [])} шт.")
    if r1.get("error"):
        print("\n  👉 Частая «проблема»: не ESM сломан, а Observed отфильтрован FactsPack")
        print("     (BALANCED не включает Observed) или TruthGate требует evidence.")

    sep("3. Запрос mode=CREATIVE (мягче по состояниям)")
    r2 = pipeline_run("Как дышат дельфины?", cognitive_mode="CREATIVE")
    print(f"  error:  {r2.get('error')}")
    print(f"  answer: {r2.get('answer')}")
    print(f"  facts:  {len(r2.get('facts') or [])} шт.")
    fact = get_fact("demo_dolphins_001")
    show_fact("Факт после CREATIVE query", fact)

    sep("4. Ручной ESM-переход (как PATCH /facts/.../transition)")
    transition_esm("demo_dolphins_001", "Hypothesized", by="demo_user")
    transition_esm("demo_dolphins_001", "Supported", by="demo_user")
    transition_esm("demo_dolphins_001", "Validated", by="demo_user")
    fact = get_fact("demo_dolphins_001")
    show_fact("После Observed→Validated", fact)
    print("\n  История переходов:")
    for i, h in enumerate(fact.get("history") or [], 1):
        print(f"    {i}. {h.get('from')} → {h.get('state')}  ({h.get('by')})")

    sep("5. Добавляем evidence и снова BALANCED (ожидаемый успех)")
    # Важно: enrich уже существующий demo_dolphins_001 через batch-upsert.
    # store_fact() имеет no-op guard по claim/source/confidence и может не обновить metadata.
    store_facts_batch([
        {
            "fact_id": "demo_dolphins_001",
            "claim": DEMO_TEXT,
            "source": DEMO_SOURCE,
            "confidence": 0.85,
            "metadata": {
                "demo": True,
                "evidence_refs": ["biology_guide_2024", "zoology_handbook_ch7"],
            },
        },
        {
            "fact_id": "demo_dolphins_002",
            "claim": "Дельфины относятся к отряду китообразных.",
            "source": DEMO_SOURCE,
            "confidence": 0.9,
            "metadata": {"evidence_refs": ["textbook_ch12", "marine_biology_2024"]},
        },
    ])
    transition_esm("demo_dolphins_002", "Hypothesized", by="demo_user")
    transition_esm("demo_dolphins_002", "Supported", by="demo_user")
    transition_esm("demo_dolphins_002", "Validated", by="demo_user")
    r3 = pipeline_run("Кто такие дельфины?", cognitive_mode="BALANCED")
    print(f"  error:  {r3.get('error')}")
    print(f"  answer: {(r3.get('answer') or '')[:120]}...")
    print(f"  facts:  {len(r3.get('facts') or [])} шт.")
    for f in r3.get("facts") or []:
        refs = (f.get("metadata") or {}).get("evidence_refs", [])
        print(
            f"    - {f.get('fact_id')}: state={f.get('epistemic_state')} "
            f"evidence_refs={len(refs)}"
        )

    sep("6. Итог")
    print("  • Текст может быть любым — важны source, confidence, mode, evidence.")
    print("  • ESM работает: переходы пишутся в history.")
    print("  • После ingest без Validated + BALANCED ответ часто пустой — это ожидаемо.")
    print(f"\n  Временная БД: {db_path}")
    print("  (удали папку вручную, если не нужна)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
