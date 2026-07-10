"""
🧬 core/truth_maintenance.py — Truth Maintenance (V8.7 Titan, из Crystal fork)

Атомарные операции над фактами когда новый встречает канон:
    reinforce()  — повторное свидетельство → confidence растёт (Laplace-затухание)
    supersede()  — переформулировка: старый → Deprecated + ребро SUPERSEDED_BY
    contradict() — старый факт → Contradicted + ребро CONTRADICTS

Всё детерминировано. Авто-детекция семантических противоречий (NLI)
намеренно вынесена в contradiction_registry.py.

Инварианты:
    I-TM1: reinforce НЕ продвигает факт в ESM. Только confidence.
    I-TM2: supersede всегда через ESM-переходы. Прямой SET — запрещён.
    I-TM3: contradict пишет provenance через provenance_chain.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("velantrim.truth_maintenance")

REL_SUPERSEDED_BY = "SUPERSEDED_BY"
REL_CONTRADICTS = "CONTRADICTS"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def reinforce(fact_id: str, agreement: bool = True) -> Optional[float]:
    """
    Подкрепить факт независимым свидетельством.

    agreement=True  → confidence += (1-conf) / (obs+1)  — затухающий рост
    agreement=False → confidence *= obs / (obs+1)        — затухающее падение

    Счётчик наблюдений: metadata['observations'].
    Подкрепление сбрасывает часы спада (last_consolidated).
    """
    from core.memory import get_fact, store_fact
    # FIX #10 (Claude audit): update_fact не существует → используем store_fact

    fact = get_fact(fact_id)
    if fact is None:
        logger.warning("TruthMaintenance.reinforce: факт %s не найден", fact_id)
        return None

    meta = dict(fact.get("metadata") or {})
    if isinstance(meta, str):
        import json
        try:
            meta = json.loads(meta)
        except json.JSONDecodeError:
            meta = {}
    obs = int(meta.get("observations", 1))
    conf = float(fact.get("confidence", 0.5))

    if agreement:
        new_conf = round(conf + (1.0 - conf) / (obs + 1), 4)
    else:
        new_conf = round(conf * obs / (obs + 1), 4)

    meta["observations"] = obs + 1
    meta["last_consolidated"] = _now()
    fact["confidence"] = new_conf
    fact["metadata"] = meta
    store_fact(fact)
    # FIX #10 (Claude audit): update_fact → store_fact

    # Лог в provenance
    try:
        from core.provenance_chain import get_provenance_chain
        get_provenance_chain().append(
            fact_id,
            event_type="fact_reinforced",
            actor="truth_maintenance",
            reason=f"agreement={agreement}, obs={obs+1}, conf={conf:.3f}→{new_conf:.3f}",
        )
    except Exception:
        pass

    logger.info("TruthMaintenance.reinforce: %s conf=%.3f→%.3f", fact_id, conf, new_conf)
    return new_conf


def supersede(old_id: str, new_fact: Dict[str, Any]) -> Optional[str]:
    """
    Новый факт замещает старый: атомарно Observed→Hypothesized→Supported→
    Validated для нового и →Deprecated для старого, в ОДНОЙ facts-транзакции
    (core.memory.SQLiteGraphStore.supersede_fact_cas()) — либо оба факта
    меняются вместе, либо не меняется ничего.

    Успех репортится ТОЛЬКО когда:
    - старый durable-снимок всё ещё актуален (CAS на fact_id+epistemic_state+
      updated_at, взятый ДО TruthGate.evaluate());
    - новый кандидат проходит TruthGate (mode=PRECISION, без LLM, без
      дублирования пороговой логики — вся она внутри core.truth_gate);
    - guarded facts-transaction реально закоммитилась.

    Rejected/raced/failed → None, без частичного состояния: ни новый факт,
    ни ложное ребро SUPERSEDED_BY, ни ложная provenance-запись, ни мутация
    старого факта. reinforce()/contradict() не тронуты этим фиксом.

    Не мутирует переданный new_fact — работает на defensive copy.

    Invalid programmer input (пустой old_id/new_fact_id, new_fact_id ==
    old_id, явно заданный initial epistemic_state отличный от Observed,
    нелегальный ESM-переход старого состояния в Deprecated) → ValueError.
    Ordinary operational failures (старый факт не найден, TruthGate
    отклонил, коллизия по new_fact_id, конкурентная гонка, любая иная
    неожиданная ошибка внутри атомарной транзакции) → None, fail-closed.

    Ограничение согласованности (см. docs/PROJECT_STATUS.md): facts-
    транзакция (evidence gate + CAS) атомарна; causal_graph/
    provenance_chain/VersionStore — отдельные соединения/файлы, пишутся
    ПОСЛЕ успешного commit, best-effort. Падение процесса между commit'ом
    facts и этими вторичными записями оставит успешный supersede без
    соответствующих audit/relation-артефактов — это не решается здесь.
    """
    import copy as _copy

    import core.memory as _mem

    if not old_id:
        raise ValueError("supersede: old_id обязателен")

    new_fact = _copy.deepcopy(new_fact)  # никогда не мутируем аргумент вызывающего
    new_id = new_fact.get("fact_id")
    if not new_id:
        raise ValueError("supersede: new_fact['fact_id'] обязателен")
    if new_id == old_id:
        raise ValueError("supersede: new_fact['fact_id'] должен отличаться от old_id")

    requested_state = new_fact.get("epistemic_state")
    if requested_state not in (None, "Observed"):
        raise ValueError(
            "supersede: новый факт может создаваться только в 'Observed' "
            f"(получено epistemic_state={requested_state!r})"
        )

    old = _mem.get_fact_durable(old_id)
    if old is None:
        logger.warning("TruthMaintenance.supersede: старый факт %s не найден", old_id)
        return None

    current_state = old.get("epistemic_state", "Observed")
    allowed = _mem.ESM_TRANSITIONS.get(current_state, set())
    if "Deprecated" not in allowed:
        raise ValueError(
            f"supersede: переход '{current_state}' → 'Deprecated' недопустим "
            f"для '{old_id}' — матрица ESM_TRANSITIONS этого не разрешает"
        )

    metadata = new_fact.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    candidate = {
        "fact_id":    new_id,
        "claim":      new_fact.get("claim", ""),
        "source":     new_fact.get("source", "unknown"),
        "confidence": new_fact.get("confidence", 0.0),
        "metadata":   metadata,
    }

    # SECURITY (I68 — narrow re-fix of this function): реальный TruthGate,
    # не (ok, msg)-заглушка. Никогда не промоутим без прохождения гейта —
    # ImportError/любое неожиданное исключение здесь означает fail-closed
    # (return None), а не старое поведение "гейт недоступен → промоутим
    # всё равно".
    try:
        from core.truth_gate import CognitiveMode, TruthGate

        verdict = TruthGate(_mem._GLOBAL_STORE, contradiction_detector="none").evaluate(
            candidate, mode=CognitiveMode.PRECISION, by="truth_maintenance.supersede",
        )
    except Exception:
        logger.exception(
            "TruthMaintenance.supersede: TruthGate недоступен или упал — "
            "отклоняем без промоушена (fail-closed)"
        )
        return None

    if not verdict.passed:
        logger.info(
            "TruthMaintenance.supersede: TruthGate отклонил новый факт %s: %s",
            new_id, verdict.justification,
        )
        return None

    seed_record = {
        "claim":       candidate["claim"],
        "source":      candidate["source"],
        "confidence":  float(candidate["confidence"]),
        "metadata":    metadata,
        "claim_type":  new_fact.get("claim_type", "UNKNOWN"),
        "origin_type": new_fact.get("origin_type", "UNKNOWN"),
        "memory_type": new_fact.get("memory_type", "semantic"),
        "derived_from": new_fact.get("derived_from"),
    }

    try:
        result = _mem.supersede_fact_cas(
            old_id=old_id,
            new_fact_id=new_id,
            new_record_seed=seed_record,
            expected_old_state=current_state,
            expected_old_updated_at=old["updated_at"],
            old_durable_snapshot=old,
            by="truth_maintenance.supersede",
        )
    except Exception:
        logger.exception(
            "TruthMaintenance.supersede: атомарная facts-транзакция упала "
            "неожиданно для %s → %s — fail-closed", old_id, new_id,
        )
        return None

    if not result.committed:
        logger.warning(
            "TruthMaintenance.supersede: %s → %s отклонено (%s)",
            old_id, new_id, result.reason,
        )
        return None

    # Пост-commit best-effort: ребро в causal graph + provenance. Отдельные
    # соединения/файлы от facts-транзакции выше — сбой здесь НЕ откатывает
    # уже успешный supersede, но и не должен маскироваться под полную
    # кросс-хранилищную атомарность (см. docstring и docs/PROJECT_STATUS.md).
    try:
        from core.causal_graph import get_causal_graph
        cg = get_causal_graph()
        if cg is not None:
            cg.add_relation(
                from_fact_id=old_id,
                to_fact_id=new_id,
                relation_type=REL_SUPERSEDED_BY,
                confidence=0.95,
            )
    except Exception:
        logger.warning(
            "TruthMaintenance.supersede: causal edge %s -SUPERSEDED_BY→ %s "
            "not added", old_id, new_id, exc_info=True,
        )

    try:
        from core.provenance_chain import get_provenance_chain
        get_provenance_chain().append(
            old_id, event_type="fact_superseded",
            actor="truth_maintenance.supersede",
            reason=f"superseded_by={new_id}",
        )
    except Exception:
        logger.warning(
            "TruthMaintenance.supersede: provenance event not recorded for %s",
            old_id, exc_info=True,
        )

    logger.info("TruthMaintenance.supersede: %s → %s", old_id, new_id)
    return new_id


def contradict(fact_id: str, source_id: str, reason: str = "") -> bool:
    """
    Объявить противоречие между фактами. Оба → Contradicted.
    Создаёт ребро fact -CONTRADICTS→ source.

    Возвращает True если операция выполнена (хотя бы один факт изменён).
    """
    from core.memory import get_fact, transition_esm

    fact_a = get_fact(fact_id)
    fact_b = get_fact(source_id)
    if fact_a is None and fact_b is None:
        return False

    changed = False
    for fid in (fact_id, source_id):
        try:
            transition_esm(fid, "Contradicted")
            changed = True
        except Exception:
            logger.debug("contradict: ESM skip for %s", fid)

    # Ребро
    if changed:
        try:
            from core.causal_graph import get_causal_graph
            cg = get_causal_graph()
            if cg is not None:
                cg.add_relation(
                    from_fact_id=fact_id,
                    to_fact_id=source_id,
                    relation_type=REL_CONTRADICTS,
                    confidence=0.95,
                )
        except Exception:
            pass

        # Регистрация в CRISPR-спейсеры
        try:
            from core.contradiction_registry import get_contradiction_registry
            reg = get_contradiction_registry()
            claim_a = fact_a.get("claim", "") if fact_a else ""
            claim_b = fact_b.get("claim", "") if fact_b else ""
            reg.record(fact_id, claim_a, source_id, claim_b, method="manual")
        except Exception:
            pass

    logger.info("TruthMaintenance.contradict: %s ↔ %s", fact_id, source_id)
    return changed


def confidence_decay(
    fact_id: str,
    *,
    half_life_days: float = 30.0,
    floor: float = 0.02,
    now: Optional[datetime] = None,
) -> Optional[float]:
    """
    Временной спад confidence. Значимое (significance > 0) забывается медленнее.
    half_life_eff = half_life × (1 + significance).

    Не разрушает факт. Только снижает confidence.
    Идемпотентен: elapsed считает от last_consolidated.
    """
    from core.memory import get_fact, store_fact
    # FIX #10 (Claude audit): update_fact не существует → используем store_fact

    fact = get_fact(fact_id)
    if fact is None:
        return None
    state = fact.get("epistemic_state", "")
    if state not in ("Validated", "Supported"):
        return float(fact.get("confidence", 0.5))

    meta = dict(fact.get("metadata") or {})
    if isinstance(meta, str):
        import json
        try:
            meta = json.loads(meta)
        except json.JSONDecodeError:
            meta = {}
    baseline_str = meta.get("last_consolidated") or fact.get("created_at") or fact.get("updated_at")
    if not baseline_str:
        return float(fact.get("confidence", 0.5))

    now = now or datetime.now(timezone.utc)
    try:
        baseline = datetime.fromisoformat(baseline_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return float(fact.get("confidence", 0.5))

    elapsed = (now - baseline).total_seconds() / 86400.0  # дни
    if elapsed < 1:
        return float(fact.get("confidence", 0.5))

    sig = float(meta.get("significance", 0))
    effective_hl = half_life_days * (1.0 + sig * 2)
    conf = float(fact.get("confidence", 0.5))
    new_conf = round(max(floor, conf * (0.5 ** (elapsed / effective_hl))), 4)

    if abs(new_conf - conf) < 0.001:
        return conf

    meta["last_consolidated"] = now.isoformat()
    fact["confidence"] = new_conf
    fact["metadata"] = meta
    store_fact(fact)
    # FIX #10 (Claude audit): update_fact → store_fact
    return new_conf


__all__ = [
    "REL_CONTRADICTS",
    "REL_SUPERSEDED_BY",
    "confidence_decay",
    "contradict",
    "reinforce",
    "supersede",
]
