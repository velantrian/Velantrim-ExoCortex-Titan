"""
🌿 core/essence.py — Essence Layer P0 (deterministic core)
==========================================================
Канон: docs/ESSENCE_LAYER_CANON.ru.md (v1.0)

Назначение
----------
Превратить НАБОР уже проверенных (Truth-Gated) фактов в:

    суть (gist) + смысловые роли + смысловую цепочку + короткий ответ + WhyTrace

…как делает хороший инженер: понять главное, отбросить шум, связать сложное,
ответить коротко — но НЕ скрывая неопределённость.

Жёсткие правила канона, которые этот модуль соблюдает
-----------------------------------------------------
1. НЕ трогает stable `/query`, БД и Truth Gate. Это чистый, аддитивный модуль.
2. НЕ подменяет Truth Gate: в `gist` берутся только Validated/Supported факты.
3. НЕ скрывает uncertainty: если факты лишь Supported или уверенность низкая —
   к ответу добавляется честная пометка.
4. НЕ выкидывает источники/TRACE: каждый вывод сопровождается WhyTrace.
5. БЕЗ LLM и без эмоций/«личности» — только детерминированная ясность.

Это P0: детерминированный фундамент. Креативный LLM-синтез — отдельный слой
поверх этого, подключается позже за флагом и с отдельными тестами.
"""
from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

ESSENCE_VERSION = "0.1.0"

# Состояния, которым разрешено формировать «суть» (зеркалит Truth Gate honesty).
_GIST_ELIGIBLE_STATES = {"Validated", "Supported"}
# Порог уверенности, ниже которого вывод считается предварительным.
_UNCERTAINTY_CONFIDENCE = 0.7


def is_essence_enabled() -> bool:
    """Флаг готовности к будущей интеграции (по умолчанию ВЫКЛ). Модуль аддитивен."""
    return os.getenv("ENABLE_ESSENCE", "false").strip().lower() in {"1", "true", "yes", "on"}


class MeaningRole(str, Enum):
    """Смысловая роль факта в цепочке рассуждения (канон P0)."""
    CAUSE = "cause"
    MECHANISM = "mechanism"
    EFFECT = "effect"
    RISK = "risk"
    EXAMPLE = "example"
    SOURCE = "source"
    DECISION = "decision"
    CLAIM = "claim"  # нейтральная роль по умолчанию


# Тип причинной связи (causal_graph) → смысловая роль источника связи.
_RELATION_TO_ROLE: dict[str, MeaningRole] = {
    "causes": MeaningRole.CAUSE,
    "precedes": MeaningRole.CAUSE,
    "enables": MeaningRole.MECHANISM,
    "requires": MeaningRole.MECHANISM,
    "composes": MeaningRole.MECHANISM,
    "implies": MeaningRole.EFFECT,
    "follows": MeaningRole.EFFECT,
    "prevents": MeaningRole.RISK,
    "contradicts": MeaningRole.RISK,
}

# Лексические подсказки (ru+en) для разметки ролей, когда нет причинных связей.
_ROLE_CUES: dict[MeaningRole, Sequence[str]] = {
    MeaningRole.CAUSE: ("потому что", "из-за", "вызывает", "because", "due to", "causes"),
    MeaningRole.EFFECT: ("приводит к", "поэтому", "в результате", "следствие",
                         "therefore", "leads to", "results in"),
    MeaningRole.MECHANISM: ("через", "за счёт", "механизм", "требует",
                            "via", "mechanism", "requires", "by means of"),
    MeaningRole.RISK: ("риск", "опасн", "противореч", "ошибк", "сбой",
                       "risk", "danger", "fails", "contradict"),
    MeaningRole.EXAMPLE: ("например", "к примеру", "пример", "for example", "e.g.", "such as"),
    MeaningRole.DECISION: ("решено", "выбираем", "следует", "decision", "we choose", "should"),
}


@dataclass
class RoledFact:
    """Факт с присвоенной смысловой ролью."""
    fact_id: str
    claim: str
    role: str
    source: str
    epistemic_state: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "claim": self.claim,
            "role": self.role,
            "source": self.source,
            "epistemic_state": self.epistemic_state,
            "confidence": self.confidence,
        }


@dataclass
class WhyTrace:
    """Почему выбрана именно эта суть — проверяемость канона."""
    gist_fact_id: str | None
    reason: str
    source_fact_ids: list[str] = field(default_factory=list)
    relation_types: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gist_fact_id": self.gist_fact_id,
            "reason": self.reason,
            "source_fact_ids": list(self.source_fact_ids),
            "relation_types": list(self.relation_types),
        }


@dataclass
class Essence:
    """Результат Essence Layer P0."""
    gist: str
    short_answer: str
    roles: list[RoledFact]
    chain: list[str]
    uncertainty_note: str | None
    why: WhyTrace
    version: str = ESSENCE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "gist": self.gist,
            "short_answer": self.short_answer,
            "roles": [r.to_dict() for r in self.roles],
            "chain": list(self.chain),
            "uncertainty_note": self.uncertainty_note,
            "why": self.why.to_dict(),
            "version": self.version,
        }


# ── helpers ────────────────────────────────────────────────────────────────


def _norm_fact(f: dict[str, Any]) -> dict[str, Any]:
    """Защитная нормализация факта — устойчива к вариациям схемы."""
    conf = f.get("confidence", f.get("source_confidence", 0.0))
    try:
        conf = float(conf)
    except (TypeError, ValueError):
        conf = 0.0
    return {
        "fact_id": str(f.get("fact_id", f.get("id", ""))),
        "claim": str(f.get("claim", "")).strip(),
        "source": str(f.get("source", "")),
        "epistemic_state": str(f.get("epistemic_state", "")),
        "confidence": conf,
    }


def _rel_endpoints(rel: dict[str, Any]) -> tuple[str, str, str]:
    """Достаёт (source_id, target_id, relation_type) из связи, терпя разные ключи."""
    src = str(rel.get("source_id", rel.get("from", rel.get("source", ""))))
    tgt = str(rel.get("target_id", rel.get("to", rel.get("target", ""))))
    rtype = str(rel.get("relation_type", rel.get("type", rel.get("rel", ""))))
    return src, tgt, rtype


def _tag_role_by_cues(claim: str) -> MeaningRole:
    low = claim.lower()
    for role, cues in _ROLE_CUES.items():
        if any(cue in low for cue in cues):
            return role
    return MeaningRole.CLAIM


def _causal_degree(fact_id: str, relations: Sequence[dict[str, Any]]) -> int:
    deg = 0
    for rel in relations:
        src, tgt, _ = _rel_endpoints(rel)
        if fact_id and (fact_id == src or fact_id == tgt):
            deg += 1
    return deg


# ── public API ───────────────────────────────────────────────────────────────


def compose_essence(
    facts: Sequence[dict[str, Any]],
    relations: Sequence[dict[str, Any]] | None = None,
) -> Essence:
    """
    Собрать суть из набора фактов (+ опционально причинных связей causal_graph).

    Args:
        facts: список фактов (как в facts_pack["facts"]); ожидаются ключи
               claim / fact_id / source / epistemic_state / confidence
               (все читаются защитно через .get).
        relations: список причинных связей с ключами source_id/target_id/relation_type
                   (терпит также from/to/type). Опционально.

    Returns:
        Essence: gist + roles + chain + short_answer + uncertainty_note + WhyTrace.
        Никогда не бросает на «пустом»/кривом входе — возвращает честный «нет данных».
    """
    relations = list(relations or [])
    norm = [_norm_fact(f) for f in (facts or []) if str(f.get("claim", "")).strip()]

    if not norm:
        return Essence(
            gist="",
            short_answer="Нет проверенных фактов — вывод невозможен.",
            roles=[],
            chain=[],
            uncertainty_note="Пустой вход: ни одного факта с непустым claim.",
            why=WhyTrace(gist_fact_id=None, reason="empty_input"),
        )

    # ── роли ────────────────────────────────────────────────────────────────
    # Сначала роли из причинных связей (источник связи → роль по типу).
    role_by_id: dict[str, MeaningRole] = {}
    for rel in relations:
        src, _tgt, rtype = _rel_endpoints(rel)
        role = _RELATION_TO_ROLE.get(rtype)
        if src and role and src not in role_by_id:
            role_by_id[src] = role

    roled: list[RoledFact] = []
    for f in norm:
        role = role_by_id.get(f["fact_id"]) or _tag_role_by_cues(f["claim"])
        roled.append(RoledFact(
            fact_id=f["fact_id"], claim=f["claim"], role=role.value,
            source=f["source"], epistemic_state=f["epistemic_state"],
            confidence=f["confidence"],
        ))

    # ── выбор сути (gist) ─────────────────────────────────────────────────────
    # Кандидаты — только Validated/Supported (честность Truth Gate).
    eligible = [f for f in norm if f["epistemic_state"] in _GIST_ELIGIBLE_STATES]
    pool = eligible or norm  # если ничего не прошло — берём всё, но пометим uncertainty

    def _score(f: dict[str, Any]) -> tuple:
        validated = 1 if f["epistemic_state"] == "Validated" else 0
        degree = _causal_degree(f["fact_id"], relations)
        return (validated, f["confidence"] + 0.1 * degree, degree)

    # max по score; при равенстве сохраняется порядок поступления (стабильно).
    gist_fact = max(pool, key=_score)
    gist = gist_fact["claim"]

    # ── смысловая цепочка ─────────────────────────────────────────────────────
    chain = _build_chain(norm, relations, gist_fact["fact_id"])

    # ── неопределённость (канон: не скрывать) ─────────────────────────────────
    uncertainty = _uncertainty_note(gist_fact, eligible_exists=bool(eligible), facts=norm)

    # ── короткий ответ ────────────────────────────────────────────────────────
    parts = [f"Суть: {gist}"]
    if len(chain) > 1:
        # элементы цепочки (кроме первого) уже несут свою стрелку «—rel→ »
        parts.append("Цепочка: " + " ".join(chain))
    if uncertainty:
        parts.append(uncertainty)
    short_answer = "\n".join(parts)

    # ── WhyTrace ──────────────────────────────────────────────────────────────
    rel_types_touching = sorted({
        rtype for rel in relations
        for s, t, rtype in [_rel_endpoints(rel)]
        if rtype and gist_fact["fact_id"] in (s, t)
    })
    why = WhyTrace(
        gist_fact_id=gist_fact["fact_id"] or None,
        reason=(
            f"Выбран факт со статусом {gist_fact['epistemic_state']}, "
            f"уверенность {gist_fact['confidence']:.2f}, "
            f"причинных связей: {_causal_degree(gist_fact['fact_id'], relations)}."
        ),
        source_fact_ids=[f["fact_id"] for f in norm if f["fact_id"]],
        relation_types=rel_types_touching,
    )

    return Essence(
        gist=gist, short_answer=short_answer, roles=roled,
        chain=chain, uncertainty_note=uncertainty, why=why,
    )


def _build_chain(
    norm: Sequence[dict[str, Any]],
    relations: Sequence[dict[str, Any]],
    start_id: str,
) -> list[str]:
    """
    Построить человекочитаемую цепочку смысла «причина → механизм → вывод».
    Идёт ВПЕРЁД от корневой причины (источник ребра, не являющийся ничьим
    следствием), без циклов, максимум 4 шага. Если явного корня нет (цикл) —
    стартует от `start_id` (факт-суть). Если связей нет — возвращает
    [claim факта-сути] (одиночный узел).
    """
    claim_by_id = {f["fact_id"]: f["claim"] for f in norm if f["fact_id"]}
    # forward-рёбра: source_id -> (target_id, relation_type); targets — у кого есть вход
    forward: dict[str, tuple] = {}
    targets: set = set()
    for rel in relations:
        src, tgt, rtype = _rel_endpoints(rel)
        if src in claim_by_id and tgt in claim_by_id:
            if src not in forward:
                forward[src] = (tgt, rtype)
            targets.add(tgt)

    # корень = источник ребра, который сам не является ничьим следствием
    roots = [f["fact_id"] for f in norm
             if f["fact_id"] in forward and f["fact_id"] not in targets]
    origin = roots[0] if roots else start_id

    origin_claim = claim_by_id.get(origin, "")
    if not origin_claim:
        return []
    if origin not in forward:
        return [origin_claim]

    chain: list[str] = [origin_claim]
    seen = {origin}
    cur = origin
    for _ in range(4):
        nxt = forward.get(cur)
        if not nxt:
            break
        tgt_id, rtype = nxt
        if tgt_id in seen:
            break
        arrow = f"—{rtype}→ " if rtype else "→ "
        chain.append(arrow + claim_by_id[tgt_id])
        seen.add(tgt_id)
        cur = tgt_id
    return chain


def _uncertainty_note(
    gist_fact: dict[str, Any],
    eligible_exists: bool,
    facts: Sequence[dict[str, Any]],
) -> str | None:
    """Честная пометка о неопределённости (канон: не скрывать ради краткости)."""
    notes: list[str] = []
    if not eligible_exists:
        notes.append("ни один факт не прошёл в Validated/Supported")
    elif gist_fact["epistemic_state"] != "Validated":
        notes.append(f"опора на факт в состоянии {gist_fact['epistemic_state']}, не Validated")
    if gist_fact["confidence"] < _UNCERTAINTY_CONFIDENCE:
        notes.append(f"уверенность {gist_fact['confidence']:.2f} ниже {_UNCERTAINTY_CONFIDENCE}")
    # противоречие среди фактов
    if any(f["epistemic_state"] == "Contradicted" for f in facts):
        notes.append("среди фактов есть Contradicted")
    if not notes:
        return None
    return "⚠️ Предварительно: " + "; ".join(notes) + "."
