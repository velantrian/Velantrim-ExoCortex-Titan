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
    Новый факт замещает старый. Старый → Deprecated. Новый → Validated.

    Создаёт ребро old -SUPERSEDED_BY→ new в causal_graph (если доступен).
    Возвращает fact_id нового факта или None.
    """
    from core.memory import get_fact, store_fact, promote_to_validated, transition_esm

    old = get_fact(old_id)
    if old is None:
        logger.warning("TruthMaintenance.supersede: старый факт %s не найден", old_id)
        return None

    # Сохранить новый факт
    new_fact.setdefault("epistemic_state", "Observed")
    new_fact.setdefault("created_at", _now())
    new_fact.setdefault("updated_at", _now())

    store_fact(new_fact)
    new_id = new_fact.get("fact_id", "")

    # Промоут нового → Validated — FIX #14 (Claude audit):
    # прогоняем через TruthGate перед переходом. Без этого обходится I68
    # (требование верификации перед Validated).
    try:
        from core.truth_gate import TruthGate, CognitiveMode
        tg = TruthGate(mode=CognitiveMode.PRECISION)
        ok, msg = tg.evaluate(new_fact)
        if not ok:
            logger.warning("TruthMaintenance.supersede: TruthGate отклонил новый факт: %s", msg)
        else:
            promote_to_validated(new_id)
    except ImportError:
        # TruthGate недоступен — fallback без проверки (старое поведение)
        promote_to_validated(new_id)
    except Exception as exc:
        logger.warning("TruthMaintenance.supersede: ESM-переход нового: %s", exc)

    # Старый → Deprecated
    try:
        transition_esm(old_id, "Deprecated")
    except Exception as exc:
        logger.warning("TruthMaintenance.supersede: ESM-переход старого: %s", exc)

    # Ребро в causal graph
    try:
        from core.causal_graph import get_causal_graph, FORWARD_RELATION_TYPES
        cg = get_causal_graph()
        if cg is not None:
            cg.add_relation(
                from_fact_id=old_id,
                to_fact_id=new_id,
                relation_type=REL_SUPERSEDED_BY,
                confidence=0.95,
            )
    except Exception:
        logger.debug("supersede: causal edge not added")

    # Лог
    try:
        from core.provenance_chain import get_provenance_chain
        get_provenance_chain().append(
            old_id, event_type="fact_superseded",
            actor="truth_maintenance",
            reason=f"superseded_by={new_id}",
        )
    except Exception:
        pass

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
