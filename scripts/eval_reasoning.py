#!/usr/bin/env python
"""
📊 scripts/eval_reasoning.py — измерить, насколько система РАССУЖДАЕТ, а не просто
ищет. Гоняет набор научных запросов по построенному графу знаний (build_kb_graph.py)
в двух режимах и считает объективные метрики цепочек.

    LEGACY  — флаги OFF: дамп фактов («ответ» = склейка), без цепочек.
    SMART   — graph-expansion + essence + truth_policy ON: multi-hop цепочки.

Метрики (SMART):
    chain_len      — длина смысловой цепочки (звеньев)
    causal_links   — число причинных связей, найденных вокруг сути
    reasoned       — доля запросов, где построена цепочка ≥2 звеньев

Запуск (из корня, после build_kb_graph.py):
    python scripts/eval_reasoning.py
"""
from __future__ import annotations

import os
import re
import sys

os.environ.setdefault("VELANTRIM_DB_PATH", "data/velantrim_kb.db")
os.environ.setdefault("ENABLE_CAUSAL_GRAPH", "true")
os.environ.setdefault("VELANTRIM_SQLITE_SYNCHRONOUS", "NORMAL")
sys.path.insert(0, os.getcwd())

QUERIES = [
    "коррозия металла и её предотвращение",
    "тепловое расширение материалов в конструкциях",
    "фотосинтез и преобразование энергии в растении",
    "давление и температура газа",
    "электрический заряд и взаимодействие",
    "трение и износ деталей",
    "кислота и основание реакция нейтрализации",
    "теплопередача и охлаждение",
    "вода замерзание и расширение",
    "окисление и горение",
]

_LINKS_RE = re.compile(r"связ[еи][й]?:\s*(\d+)")


def _set_mode(on: bool):
    import core.essence as ess
    from core import pipeline
    pipeline._graph_expansion_enabled = lambda: on        # noqa: E731
    pipeline._truth_policy_enabled = lambda: on            # noqa: E731
    ess.is_essence_enabled = lambda: on                    # noqa: E731


def main() -> int:
    from core import pipeline

    print("=" * 70)
    print("EVAL — РАССУЖДЕНИЕ ПО ГРАФУ ЗНАНИЙ (LEGACY vs SMART)")
    print("=" * 70)
    rows = []
    for q in QUERIES:
        _set_mode(True)
        r = pipeline.run(q)
        ess = r.get("essence") or {}
        chain = ess.get("chain") or []
        why = (ess.get("why") or {}).get("reason", "")
        m = _LINKS_RE.search(why)
        links = int(m.group(1)) if m else 0
        rows.append((q, len(chain), links))
        gist = (ess.get("short_answer") or r.get("answer") or "")[:64]
        flag = "🧠" if len(chain) >= 2 else "  "
        print(f"  {flag} chain={len(chain)} links={links:<2} | {q[:34]:34} → {gist}")

    n = len(rows)
    reasoned = sum(1 for _, c, _ in rows if c >= 2)
    avg_chain = sum(c for _, c, _ in rows) / max(1, n)
    avg_links = sum(l for _, _, l in rows) / max(1, n)
    reason_pct = 100 * reasoned // n

    # Связность KB (доля фактов хотя бы с одним ребром) — второй ключевой показатель.
    conn_pct = -1
    try:
        from core.knowledge_linker import link_by_tags
        from core.world_skills_ingest import parse_knowledge_dir
        kb = parse_knowledge_dir()
        edges = link_by_tags(kb)
        connected: set = set()
        for e in edges:
            connected.add(e["source_id"]); connected.add(e["target_id"])
        conn_pct = 100 * len(connected) // max(1, len(kb))
    except Exception as exc:  # noqa: BLE001
        print(f"  (связность не посчитана: {exc})")

    print("\n" + "-" * 70)
    print(f"  запросов:              {n}")
    print(f"  доля рассуждений:      {reason_pct}%   (цепочка ≥2 звена)")
    print(f"  средняя длина цепочки: {avg_chain:.1f}")
    print(f"  среднее число связей:  {avg_links:.1f}")
    if conn_pct >= 0:
        print(f"  связность KB:          {conn_pct}%   (фактов хотя бы с 1 ребром)")
    print("-" * 70)

    # Самодиагностика: где узкое место — ДАННЫЕ или КОД.
    print("  📍 ВЕРДИКТ:")
    if conn_pct < 0:
        print("     связность не измерена — запусти из корня репозитория.")
    elif conn_pct < 35:
        print(f"     УЗКОЕ МЕСТО = ДАННЫЕ (связность {conn_pct}% низкая).")
        print("     Рычаг ТВОЙ: ID-связи в батчах Codex + рост KB к 50k. Код пока не нужен.")
    elif reason_pct < conn_pct - 15:
        print(f"     УЗКОЕ МЕСТО = КОД (связность {conn_pct}% есть, но рассуждение {reason_pct}% отстаёт).")
        print("     Рычаг КОД: depth-2 (VELANTRIM_GRAPH_EXPANSION_DEPTH=2) / глубже Essence. Возвращайся ко мне.")
    else:
        print(f"     Сбалансировано (связность {conn_pct}%, рассуждение {reason_pct}%).")
        print("     Продолжай растить KB и связность; код подключим, когда упрётся.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
