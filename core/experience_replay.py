"""
🔄 core/experience_replay.py — Experience Replay (V8.7 Titan)

Биологический механизм: ночная реактивация успешных цепочек retrieval.
Как мозг «переживает» важные события во сне.

⚠️  Статус: ANALYSIS-ONLY. Движок *анализирует* и *предлагает*, но ничего
не применяет.

Алгоритм:
    1. Найти факты, использованные успешно (usage_count > 0, confidence >= 0.6)
    2. Определить какие факты часто используются вместе
    3. Вернуть ограниченный proposal для co-occurrence-подкрепления
    4. Применение (Velum boost/decay) НЕ выполняется — см. ниже

Почему применение отложено (post-merge review PR #66):
    AGENTS.md §«Canonical memory boundary» запрещает background read-пути
    мутировать Canon, epistemic state, relations, activation history или
    projection state; безопасный путь — вернуть evidence/AnalysisProposal и
    требовать явный canonical write service.

    PR #66 включил прямую мутацию Velum отсюда, и это нарушало правило сразу
    по трём осям:
      • cross-loop: `run()` живёт в worker-потоке (`asyncio.to_thread`), а
        singleton Velum принадлежит серверному event loop. Новый loop через
        `asyncio.run` рядом с чужим `asyncio.Lock` — гонка либо вечный await.
      • keyspace: в Velum писались `fact_id`, тогда как ingest наполняет граф
        *именами сущностей*. Получался отдельный namespace UUID-рёбер, который
        обычный retrieval никогда не посещает.
      • flag: `ENABLE_VELUM=0` игнорировался, т.е. отключённая фича работала.

    До появления async-owning-loop apply-сервиса и маппинга fact_id → entity
    name применение остаётся deferred, и отчёт честно это сообщает
    (`velum_apply_status`), вместо того чтобы рапортовать несуществующее
    подкрепление.

Инварианты:
    I-ER1: Только Slow Path. Никогда не блокирует ответ.
    I-ER2: Не меняет truth_status.
    I-ER3: Не пишет новые факты в граф.
    I-ER4: Не мутирует projection state (Velum и прочее) — только proposal.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("velantrim.experience_replay")

# Границы разбора. Перечисление пар квадратично по числу успешных фактов, а
# один общий retrieval-контекст делает почти все факты взаимно co-occurring:
# n(n-1)/2 пар. Без явного потолка ночной цикл монополизировал бы CPU на
# большом сторе. Усечение никогда не молчит — см. proposal_truncated + WARNING.
_MAX_REPLAY_FACTS = 500
_MAX_PROPOSAL_PAIRS = 256

# Причины, по которым применение не выполнено. Отдельные коды, потому что
# «фича выключена» и «apply-путь ещё не реализован» — разные состояния.
_REASON_DEFERRED = "canonical_async_apply_not_implemented"
_REASON_DISABLED = "velum_disabled"


class ExperienceReplayEngine:
    """
    Движок ночной реактивации успешных цепочек.

    Используется в SleepTimeWorker один раз за цикл сна.
    """

    def __init__(self):
        self._run_count = 0
        self._proposal: List[Dict[str, Any]] = []

    def run(self) -> Dict[str, Any]:
        """
        Один полный цикл experience replay — read-only.

        Возвращает отчёт: сколько фактов реактивировано, какой proposal собран и
        почему применение отложено. `velum_edges_boosted` / `velum_edges_decayed`
        остаются нулями by design: ничего не применяется, и отчёт не должен
        заявлять подкрепление, которого не было.
        """
        self._run_count += 1
        report: Dict[str, Any] = {
            "run": self._run_count,
            "facts_reactivated": 0,
            # Всегда 0 в analysis-only режиме. Поля сохранены, чтобы не ломать
            # существующих читателей отчёта, но они больше ничего не утверждают.
            "velum_edges_boosted": 0,
            "velum_edges_decayed": 0,
            "velum_apply_status": "deferred",
            "velum_apply_reason": _REASON_DEFERRED,
            "candidate_pairs": 0,
            "proposal_pairs": 0,
            "proposal_truncated": False,
            "facts_truncated": False,
            "errors": 0,
        }

        # Флаг читается до любого анализа: при ENABLE_VELUM=0 singleton не
        # создаётся вообще (см. отсутствие get_velum() в этом модуле), и статус
        # отражает именно «выключено», а не «отложено».
        if not self._velum_enabled(report):
            report["velum_apply_status"] = "skipped"
            report["velum_apply_reason"] = _REASON_DISABLED

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

        # Потолок на входе в квадратичное перечисление пар. Берём самые
        # уверенные факты, а не произвольный префикс выборки.
        if len(successful) > _MAX_REPLAY_FACTS:
            successful.sort(key=lambda f: float(f.get("confidence", 0.0)), reverse=True)
            logger.warning(
                "ExperienceReplay: %d успешных фактов > потолка %d — "
                "анализируем top-%d по confidence",
                len(successful), _MAX_REPLAY_FACTS, _MAX_REPLAY_FACTS,
            )
            successful = successful[:_MAX_REPLAY_FACTS]
            report["facts_truncated"] = True

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

        # 3. Собрать ограниченный proposal. Мутации здесь нет и быть не должно:
        # apply-границу обязан пройти явный canonical write service
        # (AGENTS.md §«Canonical memory boundary»).
        report["candidate_pairs"] = len(cooccurring)
        self._proposal = self._build_proposal(cooccurring, report)
        report["proposal_pairs"] = len(self._proposal)

        logger.info(
            "ExperienceReplay #%d: %d фактов реактивировано, "
            "%d пар-кандидатов → proposal %d, применение %s (%s)",
            self._run_count,
            report["facts_reactivated"],
            report["candidate_pairs"],
            report["proposal_pairs"],
            report["velum_apply_status"],
            report["velum_apply_reason"],
        )
        return report

    # ── Внутреннее ─────────────────────────────────────────────────────────

    def _velum_enabled(self, report: Dict[str, Any]) -> bool:
        """ENABLE_VELUM без создания singleton.

        Читается только конфиг. `get_velum()` здесь не вызывается сознательно —
        именно безусловный lookup в PR #66 создавал Velum при выключённом флаге.
        """
        try:
            from core.velum_bridge import is_velum_enabled

            return is_velum_enabled()
        except Exception as exc:
            # Не знаем состояние флага → считаем выключенным (fail-closed) и
            # сообщаем: тихо «включить» отключённую фичу хуже, чем пропустить.
            logger.warning("ExperienceReplay: не удалось прочитать ENABLE_VELUM: %s", exc)
            report["errors"] += 1
            return False

    def _build_proposal(
        self,
        cooccurring: Dict[Tuple[str, str], int],
        report: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Ранжированный, усечённый proposal подкрепления.

        `fact_id` НЕ является Velum-идентификатором: ingest наполняет граф
        именами сущностей. Поэтому пары отдаются как `fact_a` / `fact_b` —
        маппинг fact_id → entity name принадлежит будущему apply-сервису, и
        сохранять эту разницу в имени поля важно, чтобы никто снова не отправил
        UUID-ы в keyspace имён.
        """
        if not cooccurring:
            return []

        ranked = sorted(cooccurring.items(), key=lambda kv: (-kv[1], kv[0]))
        if len(ranked) > _MAX_PROPOSAL_PAIRS:
            logger.warning(
                "ExperienceReplay: %d пар-кандидатов > потолка %d — "
                "proposal усечён до top-%d по overlap",
                len(ranked), _MAX_PROPOSAL_PAIRS, _MAX_PROPOSAL_PAIRS,
            )
            ranked = ranked[:_MAX_PROPOSAL_PAIRS]
            report["proposal_truncated"] = True

        return [
            {"fact_a": a, "fact_b": b, "cooccurrence": strength}
            for (a, b), strength in ranked
        ]

    def last_proposal(self) -> List[Dict[str, Any]]:
        """Proposal последнего прогона. Читатель сам решает, применять ли."""
        return list(self._proposal)

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
