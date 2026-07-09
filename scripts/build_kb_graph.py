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
    from core.knowledge_linker import link_facts
    from core.memory import _GLOBAL_STORE, _now, store_facts_batch
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

    # 2) модальность (WORLD_FACT/EXTERNAL) — не меняет epistemic_state, ESM-триггеры молчат.
    # 3) валидация по СТРОГОЙ лестнице ESM. Прямой Observed→Validated запрещён DB-триггером
    #    truth_kernel (migrations/009): разрешены только ступени Observed→Hypothesized→
    #    Supported→Validated, и каждый UPDATE epistemic_state ОБЯЗАН поднять fact_version
    #    (триггер bump_fact_version). Делаем это 3-мя bulk-UPDATE по ступеням — быстро
    #    (не per-fact transition_esm, который на 19k = ~часы) и легально.
    #    Scoped к корпусу через temp-табличку _kb_ids: факты иных источников/состояний
    #    (Hypothesized из реального reasoning, ImmutableCore/Collapsed) НЕ трогаем.
    #    Идемпотентно: на ре-ране уже-Validated не матчатся ни одной ступенью (val=0).
    fact_ids = [f["fact_id"] for f in facts]
    now = _now()
    with _GLOBAL_STORE._db() as conn:
        # fact_version есть только на мигрированной БД (009 truth_kernel). Если есть —
        # поднимаем его на каждой ступени (триггер bump_fact_version этого требует);
        # если нет — UPDATE без него. Так скрипт работает на любой версии схемы.
        has_version = any(
            r[1] == "fact_version" for r in conn.execute("PRAGMA table_info(facts)")
        )
        bump = ", fact_version = fact_version + 1" if has_version else ""

        conn.execute("CREATE TEMP TABLE IF NOT EXISTS _kb_ids (fact_id TEXT PRIMARY KEY)")
        conn.execute("DELETE FROM _kb_ids")
        conn.executemany("INSERT OR IGNORE INTO _kb_ids VALUES (?)", [(i,) for i in fact_ids])
        conn.execute(
            "UPDATE facts SET claim_type='WORLD_FACT', origin_type='EXTERNAL' "
            "WHERE fact_id IN (SELECT fact_id FROM _kb_ids) "
            "  AND epistemic_state NOT IN ('ImmutableCore', 'Collapsed') "
            "  AND (claim_type IS NULL OR claim_type != 'WORLD_FACT')"
        )
        val = 0
        for frm, to in (
            ("Observed", "Hypothesized"),
            ("Hypothesized", "Supported"),
            ("Supported", "Validated"),
        ):
            cur = conn.execute(
                f"UPDATE facts SET epistemic_state=?, updated_at=?{bump} "
                "WHERE epistemic_state=? AND fact_id IN (SELECT fact_id FROM _kb_ids)",
                (to, now, frm),
            )
            val = cur.rowcount  # последняя ступень = число доведённых до Validated
        conn.execute("DROP TABLE IF EXISTS _kb_ids")
    print(f"  валидировано → Validated (строгая лестница ESM, 3 ступени): {val}")

    # 4) рёбра → causal_graph. link_facts = тег-матч (точные) ∪ namespace-структура
    #    (покрытие из иерархии id). Namespace-рёбра помечены inference_source='autolinker'.
    edges = link_facts(facts)
    cg = pipeline._get_causal_graph()
    added = skipped = 0
    if cg is not None:
        for e in edges:
            try:
                cg.add_relation(
                    e["source_id"], e["target_id"], e["relation_type"],
                    confidence=e["confidence"], knowledge_status=e["knowledge_status"],
                    inference_source=e.get("inference_source"),
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
