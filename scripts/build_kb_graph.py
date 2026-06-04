#!/usr/bin/env python
"""
🔗 scripts/build_kb_graph.py — собрать СВЯЗНЫЙ граф знаний из World Skills Core KB.

Берёт ВСЮ KB (`docs/knowledge/world_skills_core/ru`), грузит факты в store как
WORLD_FACT / Validated и строит причинные рёбра (knowledge_linker по тегам) в
CausalGraph. Идемпотентно (UPSERT фактов; дубли рёбер пропускаются) — можно
перезапускать после новых батчей Codex; рёбра ВЫЧИСЛЯЮТСЯ из тегов, не пишутся
руками (перестраиваются, не переписываются).

Запуск из корня репозитория:
    python scripts/build_kb_graph.py
    python scripts/build_kb_graph.py --limit 500     # быстрый тест на срезе

Затем запусти сервер на этой БД, чтобы pipeline отвечал из связной науки:
    VELANTRIM_DB_PATH=data/velantrim_kb.db ENABLE_ESSENCE=1 ENABLE_GRAPH_EXPANSION=1 \
        uvicorn server:app --port 8000

ENV:
    VELANTRIM_DB_PATH          куда писать (default data/velantrim_kb.db) — отдельная
                               KB-БД, основную velantrim.db НЕ трогает.
    VELANTRIM_SQLITE_SYNCHRONOUS=NORMAL  массовый ingest быстрее (выставляется сам).
"""
from __future__ import annotations

import argparse
import os
import sys
import time

# Отдельная KB-БД по умолчанию + быстрый sync для массового ingest.
os.environ.setdefault("VELANTRIM_DB_PATH", "data/velantrim_kb.db")
os.environ.setdefault("VELANTRIM_SQLITE_SYNCHRONOUS", "NORMAL")
os.environ.setdefault("ENABLE_CAUSAL_GRAPH", "true")

# repo root на sys.path (скрипт запускается из корня)
sys.path.insert(0, os.getcwd())


def main() -> int:
    ap = argparse.ArgumentParser(description="Build connected KB graph (facts + edges).")
    ap.add_argument("--limit", type=int, default=0, help="ограничить число фактов (0 = все)")
    args = ap.parse_args()

    from core import pipeline
    from core.knowledge_linker import link_by_tags
    from core.memory import _GLOBAL_STORE, store_facts_batch
    from core.world_skills_ingest import parse_knowledge_dir

    db = os.environ["VELANTRIM_DB_PATH"]
    print(f"🔗 KB → {db}  (synchronous={os.environ['VELANTRIM_SQLITE_SYNCHRONOUS']})")
    t0 = time.time()

    facts = parse_knowledge_dir()
    if args.limit:
        facts = facts[: args.limit]
    print(f"  распарсено фактов: {len(facts)}")

    # 1) факты → store (одна транзакция). claim_type выставляем массовым UPDATE ниже,
    #    т.к. store_facts_batch модальность пока не несёт (известный пробел batch-пути).
    payload = [{
        "fact_id":   f["fact_id"],
        "claim":     f["claim"],
        "source":    f["source"],
        "confidence": 0.85,
        "metadata":  {"domain": f["metadata"]["domain"], "kb_type": f.get("type", "")},
    } for f in facts]
    st = store_facts_batch(payload)
    print(f"  факты в store: stored={st.get('stored')} updated={st.get('updated')} errors={st.get('errors')}")

    # 2+3) модальность (WORLD_FACT/EXTERNAL) + массовая валидация → Validated, ОДНИМ
    #      bulk UPDATE. Почему не per-fact transition_esm: на 19k это ~часы (per-call
    #      conn + checksum). Для bulk-load КУРИРУЕМОЙ KB прямой UPDATE приемлем — нет
    #      дрейфа/конкуренции; per-fact ESM-история тут не ведётся (admin-загрузка).
    #      WHERE epistemic_state='Observed' → идемпотентно: на ре-ране трогает только новые.
    with _GLOBAL_STORE._db() as conn:
        cur = conn.execute(
            "UPDATE facts "
            "SET claim_type='WORLD_FACT', origin_type='EXTERNAL', epistemic_state='Validated' "
            "WHERE epistemic_state='Observed'"
        )
        val = cur.rowcount
    print(f"  валидировано → Validated (bulk): {val}")

    # 4) рёбра (вычисляются из тегов) → causal_graph
    edges = link_by_tags(facts)
    cg = pipeline._get_causal_graph()
    added = skipped = 0
    if cg is not None:
        for e in edges:
            try:
                cg.add_relation(
                    e["source_id"], e["target_id"], e["relation_type"],
                    confidence=e["confidence"], knowledge_status=e["knowledge_status"],
                )
                added += 1
            except Exception:  # noqa: BLE001 — дубль ребра / отсутствующий факт → пропуск
                skipped += 1
    conn_ids: set = set()
    for e in edges:
        conn_ids.add(e["source_id"]); conn_ids.add(e["target_id"])
    pct = 100 * len(conn_ids) // max(1, len(facts))
    print(f"  рёбер вычислено: {len(edges)}  загружено: {added}  пропущено(дубли): {skipped}")
    print(f"  связано фактов: {len(conn_ids)} ({pct}%)")
    print(f"  ⏱ {time.time() - t0:.1f} c")
    print(f"\n✅ Готово. Связный граф знаний в {db}.")
    print(f"   Запуск: VELANTRIM_DB_PATH={db} ENABLE_ESSENCE=1 ENABLE_GRAPH_EXPANSION=1 uvicorn server:app")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
