"""
Минимальный воспроизводящий тест для Titan Issue #510.

Сценарий: маленькая фикстура (2-3 записи), dense-модель недоступна,
BM25-скоринг с жёстким фильтром s > 0 отбрасывает релевантного кандидата.

Ожидание бага: релевантная запись не попадает в результаты поиска,
хотя по содержимому она явно подходит.

Запуск: pytest tests/test_issue_510_bm25_zero_score.py -q
"""
from __future__ import annotations

import math
from typing import Any


# ---------- минимальная имитация BM25 без dense-модели ----------

def _bm25_score(query_tokens: list[str], doc_tokens: list[str],
                avgdl: float, k1: float = 1.5, b: float = 0.75) -> float:
    """Упрощённый BM25. Возвращает 0.0, если ни один токен запроса
    не встречается в документе (типичная причина s > 0 фильтра)."""
    if not doc_tokens:
        return 0.0
    dl = len(doc_tokens)
    score = 0.0
    for qt in set(query_tokens):
        tf = doc_tokens.count(qt)
        if tf == 0:
            continue
        # IDF упрощённо: log((N - n + 0.5) / (n + 0.5))
        n_docs_with_term = sum(1 for d in [doc_tokens] if qt in d)  # 1 док
        idf = math.log((1 - n_docs_with_term + 0.5) / (n_docs_with_term + 0.5))
        score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / max(avgdl, 1e-9)))
    return score


def search_facts(query: str, facts: list[dict[str, Any]],
                 top_k: int = 5, min_score: float = 0.0) -> list[dict[str, Any]]:
    """Имитация retrieval Titan: BM25 + жёсткий порог s > 0."""
    q_tokens = query.lower().split()
    scored = []
    avgdl = sum(len(f["text"].lower().split()) for f in facts) / max(len(facts), 1)
    for f in facts:
        s = _bm25_score(q_tokens, f["text"].lower().split(), avgdl)
        if s > min_score:  # <-- жёсткий фильтр Issue #510
            scored.append({**f, "_score": s})
    scored.sort(key=lambda x: -x["_score"])
    return scored[:top_k]


# ---------- фикстура: 3 записи, dense-модель = None ----------

FACTS = [
    {"fact_id": "f1", "text": "Солнечные панели вырабатывают энергию днём",
     "epistemic_state": "observed", "source": "manual"},
    {"fact_id": "f2", "text": "Ветер дует с запада на восток",
     "epistemic_state": "observed", "source": "manual"},
    {"fact_id": "f3", "text": "Память хранит различающиеся факты без потерь",
     "epistemic_state": "hypothesis", "source": "test"},
]

QUERY = "солнечные панели энергия"  # релевантно f1


def test_issue_510_relevant_fact_dropped_by_bm25_zero_filter():
    """Релевантная запись f1 должна находиться, но жёсткий s > 0
    на маленькой фикстуре без dense-модели может её отбросить."""
    results = search_facts(QUERY, FACTS, top_k=5, min_score=0.0)
    found_ids = {r["fact_id"] for r in results}

    # --- что ожидаем при корректном поиске ---
    assert "f1" in found_ids, (
        f"Ожидали f1 в результатах для запроса {QUERY!r}, "
        f"нашли: {found_ids}"
    )

    # --- диагностика: показываем сырые скоры ---
    q_tokens = QUERY.lower().split()
    avgdl = sum(len(f["text"].lower().split()) for f in FACTS) / len(FACTS)
    for f in FACTS:
        s = _bm25_score(q_tokens, f["text"].lower().split(), avgdl)
        print(f"  {f['fact_id']}: score={s:.4f}  text={f['text'][:50]!r}")

    # --- маркер бага: если f1 отброшен ---
    if "f1" not in found_ids:
        print("БАГ #510 ВОСПРОИЗВЕДЁН: релевантная f1 отброшена фильтром s > 0")


def test_issue_510_small_fixture_without_dense_model():
    """Контроль: при наличии dense-модели (скор не нулевой)
    та же запись находится."""
    # Имитируем dense-скор: f1 получает ненулевой вклад
    results = search_facts(QUERY, FACTS, top_k=5, min_score=0.0)
    # Подменяем: добавляем dense-бонус, чтобы s > 0
    bonus = {"f1": 0.8, "f2": 0.1, "f3": 0.05}
    q_tokens = QUERY.lower().split()
    avgdl = sum(len(f["text"].lower().split()) for f in FACTS) / len(FACTS)
    rescued = []
    for f in FACTS:
        s = _bm25_score(q_tokens, f["text"].lower().split(), avgdl) + bonus[f["fact_id"]]
        if s > 0.0:
            rescued.append(f["fact_id"])
    assert "f1" in rescued, "С dense-моделью f1 должна находиться"
    print(f"  С dense-бонусом найдены: {rescued}")


if __name__ == "__main__":
    test_issue_510_relevant_fact_dropped_by_bm25_zero_filter()
    test_issue_510_small_fixture_without_dense_model()
    print("OK")
