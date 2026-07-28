"""
🔄 core/experience_replay.py — Experience Replay (V8.7 Titan)

Биологический механизм: ночная реактивация успешных цепочек retrieval
для консолидации памяти. Как мозг «переживает» важные события во сне.

Алгоритм:
    1. Найти факты, confidence которых вырос после использования
    2. Определить какие факты часто используются вместе
    3. Усилить Velum-связи между такими фактами (co-occurrence boost)
    4. Ослабить неиспользуемые связи (decay)

Инварианты:
    I-ER1: Только Slow Path. Никогда не блокирует ответ.
    I-ER2: Не меняет truth_status. Только attention_weight и confidence.
    I-ER3: Не пишет новые факты в граф.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from core.async_utils import run_coroutine_sync

logger = logging.getLogger("velantrim.experience_replay")


def _get_velum() -> Any:
    """Вернуть process-wide Velum singleton.

    Единственная точка импорта моста: `get_velum()` живёт в
    `core.velum_bridge`, НЕ в `core.velum`. Раньше неверный путь был продублирован
    в двух блоках ниже, и оба тихо no-op'или. Один helper — чтобы такой дрейф не мог
    разойтись по копиям.

    Импорт ленивый: `core.velum_bridge` тянет `core.feature_config`, и держать это
    на уровне модуля означало бы тащить конфиг в любой импорт replay-движка.
    Исключения не глушатся — вызывающий сам решает, что делать с отказом моста.
    """
    from core.velum_bridge import get_velum

    return get_velum()


async def _boost_pairs(
    velum: Any,
    cooccurring: Dict[Tuple[str, str], int],
    episode_id: str,
) -> int:
    """Усилить рёбра для co-occurring пар. Возвращает число затронутых рёбер.

    Публичный API Velum — `observe_episode()`, async и под внутренним локом
    (Velum.I77). Раньше здесь вызывался несуществующий `observe_entities()`:
    AttributeError глушился per-pair `except: pass`, поэтому счётчик
    `velum_edges_boosted` инкрементировался за *попытку*, а не за реальное ребро.

    Число совпавших контекстов передаётся как `salience_weight`: чем чаще пара
    использовалась вместе, тем сильнее хеббовское усиление.
    """
    boosted = 0
    for (a, b), strength in cooccurring.items():
        result = await velum.observe_episode(
            episode_id, [a, b], salience_weight=float(strength)
        )
        boosted += result.edges_touched
    return boosted


class ExperienceReplayEngine:
    """
    Движок ночной реактивации успешных цепочек.

    Используется в SleepTimeWorker один раз за цикл сна.
    """

    def __init__(self):
        self._run_count = 0

    def run(self) -> Dict[str, Any]:
        """
        Один полный цикл experience replay.

        Возвращает отчёт: сколько связей усилено, сколько ослаблено.
        """
        self._run_count += 1
        report = {
            "run": self._run_count,
            "facts_reactivated": 0,
            "velum_edges_boosted": 0,
            "velum_edges_decayed": 0,
            "errors": 0,
        }

        # 1. Найти «успешные» факты — те что использовались и confidence вырос
        try:
            from core.memory import get_all_facts
            facts = get_all_facts() or []
        except Exception as exc:
            logger.debug("ExperienceReplay: get_all_facts failed: %s", exc)
            report["errors"] += 1
            return report

        if not facts:
            return report

        # Фильтр: факты с usage_count > 0 и confidence >= 0.6
        successful: List[Dict[str, Any]] = []
        for f in facts:
            meta = f.get("metadata", {})
            if isinstance(meta, str):
                import json
                try:
                    meta = json.loads(meta)
                except json.JSONDecodeError:
                    meta = {}
            usage_count = int(meta.get("usage_count", 0))
            confidence = float(f.get("confidence", 0.5))
            if usage_count > 0 and confidence >= 0.6:
                successful.append(f)

        if not successful:
            return report

        report["facts_reactivated"] = len(successful)

        # 2. Найти пары фактов, часто используемых вместе (из контекстов)
        cooccurring: Dict[Tuple[str, str], int] = {}
        for f in successful:
            fact_id = f.get("fact_id", "")
            contexts: List[str] = []
            meta = f.get("metadata", {})
            if isinstance(meta, str):
                import json
                try:
                    meta = json.loads(meta)
                except json.JSONDecodeError:
                    meta = {}
            contexts = meta.get("usage_contexts", [])
            if isinstance(contexts, str):
                contexts = [contexts]

            # Найти другие факты с такими же контекстами
            for other in successful:
                other_id = other.get("fact_id", "")
                if other_id <= fact_id:  # избегать дублей (a,b) = (b,a)
                    continue
                other_meta = other.get("metadata", {})
                if isinstance(other_meta, str):
                    import json
                    try:
                        other_meta = json.loads(other_meta)
                    except json.JSONDecodeError:
                        other_meta = {}
                other_contexts = other_meta.get("usage_contexts", [])
                if isinstance(other_contexts, str):
                    other_contexts = [other_contexts]

                overlap = len(set(contexts) & set(other_contexts))
                if overlap > 0:
                    cooccurring[(fact_id, other_id)] = cooccurring.get((fact_id, other_id), 0) + overlap

        # 3. Усилить Velum-связи для co-occurring пар.
        #
        # Один replay-прогон = одна граница эпизода для Velum, поэтому все пары
        # усиливаются под общим episode_id: `_episode_ids` растёт на 1 за прогон,
        # а не на одну запись за пару.
        if cooccurring:
            try:
                velum = _get_velum()
                episode_id = f"experience-replay:{self._run_count}"
                report["velum_edges_boosted"] = run_coroutine_sync(
                    _boost_pairs(velum, cooccurring, episode_id)
                )
            except Exception as exc:
                # Не фатально (Slow Path, best-effort), но видимо: молчаливый
                # debug-лог и был причиной, по которой мёртвый мост не замечали.
                logger.warning("ExperienceReplay: velum boost failed: %s", exc)
                report["errors"] += 1

        # 4. Decay слабых связей + промоут сильных: конец replay-прогона —
        # такая же граница «сессии», как конец ingest-документа.
        #
        # `use_fsrs_decay` намеренно оставлен по умолчанию (фиксированный
        # decay_per_session): выбор FSRS-режима принадлежит ingest-пути
        # (`velum_bridge.finalize_ingest_session`), и тянуть его сюда означало бы
        # расширять поведение за рамки починки мёртвого сигнала.
        try:
            velum = _get_velum()
            session = run_coroutine_sync(velum.on_session_end())
            report["velum_edges_decayed"] = session.decayed_edges
        except Exception as exc:
            # Тот же контракт, что у boost-ветки выше: не фатально, но видимо и
            # учтено в report["errors"] — раньше decay-ветка ошибку не считала.
            logger.warning("ExperienceReplay: velum decay failed: %s", exc)
            report["errors"] += 1

        logger.info(
            "ExperienceReplay #%d: %d facts reactivated, %d edges boosted, %d decayed",
            self._run_count, report["facts_reactivated"], report["velum_edges_boosted"], report["velum_edges_decayed"],
        )
        return report

    def stats(self) -> Dict[str, Any]:
        return {"runs": self._run_count}


# Глобальный
_engine: Optional[ExperienceReplayEngine] = None


def get_experience_replay_engine() -> ExperienceReplayEngine:
    global _engine
    if _engine is None:
        _engine = ExperienceReplayEngine()
    return _engine


__all__ = ["ExperienceReplayEngine", "get_experience_replay_engine"]
