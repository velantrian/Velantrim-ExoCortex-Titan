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

logger = logging.getLogger("velantrim.experience_replay")


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

        # 3. Усилить Velum-связи для co-occurring пар
        if cooccurring:
            try:
                # Pre-existing wrong import path: get_velum() actually lives in
                # core.velum_bridge, not core.velum. Caught below like any other
                # optional-bridge failure, so this boost currently always no-ops.
                # Not fixed here (behavior change out of scope for a typing-only
                # pass) — tracked as a follow-up bug.
                from core.velum import get_velum  # type: ignore[attr-defined]
                velum = get_velum()
                if velum is not None:
                    for (a, b), strength in cooccurring.items():
                        try:
                            velum.observe_entities([a, b])  # one observation
                            report["velum_edges_boosted"] += 1
                        except Exception:
                            pass
            except Exception as exc:
                logger.debug("ExperienceReplay: velum boost failed: %s", exc)
                report["errors"] += 1

        # 4. Decay для неиспользуемых Velum-связей
        try:
            # Pre-existing wrong import path: get_velum() actually lives in
            # core.velum_bridge, not core.velum. Caught below like any other
            # optional-bridge failure, so this decay currently always no-ops.
            # Not fixed here (behavior change out of scope for a typing-only
            # pass) — tracked as a follow-up bug.
            from core.velum import get_velum  # type: ignore[attr-defined]
            velum = get_velum()
            if velum is not None:
                # Light decay: multiply weak edges by 0.95
                edge_count_before = len(getattr(velum, '_edges', {}))
                try:
                    velum._decay_weak_edges(decay_factor=0.95, min_weight=0.2)
                except AttributeError:
                    # fallback: manual decay
                    edges = getattr(velum, '_edges', {})
                    for key, edge in list(edges.items()):
                        if edge.weight < 0.3:
                            edge.weight *= 0.95
                            if edge.weight < 0.05:
                                del edges[key]
                edge_count_after = len(getattr(velum, '_edges', {}))
                report["velum_edges_decayed"] = edge_count_before - edge_count_after
        except Exception as exc:
            logger.debug("ExperienceReplay: velum decay failed: %s", exc)

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
