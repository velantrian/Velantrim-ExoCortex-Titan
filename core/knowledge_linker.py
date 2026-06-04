"""
🔗 core/knowledge_linker.py — линковщик базы знаний (P0, детерминированный)
==========================================================================

Проблема (выявлена в First Light, 2026-05-31): батч-таблицы `world_skills_core`
дают в колонке «Связи» только теги-темы (`wheat`, `baking`, `textile.linen`),
а НЕ типизированные рёбра факт→факт. Поэтому Essence-цепочка молчит — нет
направленных причинных связей, по которым строить «причина → механизм → вывод».

Этот линковщик выводит ДЕТЕРМИНИРОВАННЫЕ направленные рёбра из тегов:

    Правило: если факт B перечисляет тег T, и T совпадает с СЕГМЕНТОМ id
    факта A (кроме корня-домена), то A --enables--> B.
    Смысл: домен A питает / обеспечивает B (B «о» A или использует A).
    Пример: `food.process.milling…` с тегом «wheat» → `agro.crop.wheat…` --enables--> milling.
            milling с тегом… ← следующий факт с тегом «milling» → milling --enables--> sieving.
    Так складывается цепочка wheat → milling → sieving.

Честность:
  • Рёбра помечаются knowledge_status='inferred' (выведены из тегов куратора,
    НЕ проверены вручную) с умеренной уверенностью (0.6). is_reliable()=True →
    Essence их использует, но это явно «выведено», а не «доказано».
  • Корень-домен (`agro`, `food`, …) НЕ матчится — иначе тег «food» связал бы всё
    со всем. Матчим только конкретные сегменты (len ≥ 3, не первый).
  • Истинная причинность из ТЕКСТА claim («X превращается в Y» → becomes/causes) —
    следующий тиер (LLM/NLP extraction). Здесь только структурные связи из тегов.

Аддитивно, без LLM, stdlib-only. Не трогает рантайм/БД — отдаёт список рёбер,
которые можно подать в `compose_essence(relations=...)` или в CausalGraph.add_relation.
"""
from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

DEFAULT_RELATION = "enables"          # валидный FORWARD-тип CausalGraph
DEFAULT_CONFIDENCE = 0.6
DEFAULT_STATUS = "inferred"           # валидный knowledge_status
MIN_TOKEN_LEN = 3
MAX_INCOMING_PER_FACT = 8             # защита от взрыва рёбер на широких тегах
MAX_SEGMENT_FANOUT = 4               # токен, совпадающий с >N фактами = категория (не связь) → скип


def parse_tags(value: Any) -> list[str]:
    """«food, industry» / «textile.linen» / [..] → ['food','industry'] / ['textile','linen']."""
    if isinstance(value, (list, tuple, set)):
        value = ",".join(str(v) for v in value)
    tokens = re.split(r"[,\s.;/|]+", str(value).lower())
    return [t for t in (tok.strip() for tok in tokens) if len(t) >= MIN_TOKEN_LEN]


# Тиры типов знаний: upstream (причина/материал) → downstream (процесс/следствие).
# Ребро всегда ориентируется от меньшего тира к большему (материал → процесс).
_TYPE_TIER = {
    # 0 — источники/основания (причина)
    "material_source": 0, "dye_source": 0, "law": 0, "axiom": 0, "theorem": 0,
    "formula": 0, "principle": 0, "definition": 0, "concept": 0, "fact": 0, "model": 0,
    # 1 — свойства/ограничения
    "property": 1, "constraint": 1,
    # 2 — процессы/механизмы/методы
    "mechanism": 2, "process": 2, "method": 2,
    # 3 — следствия/риски
    "failure_mode": 3, "safety_rule": 3, "heuristic": 3,
}

# Явные причинные cue в тексте claim (ru+en) → отношение "causes".
_CAUSE_RE = re.compile(r"(вызыва|приводит к|из-за|причин|causes|leads to|because)", re.I)


def _tier(fact_type: Any) -> int:
    return _TYPE_TIER.get(str(fact_type or "").strip().lower(), 1)


def _orient(aid: str, bid: str, by_id: dict[str, dict[str, Any]]) -> tuple:
    """Структурное ребро aid→bid ориентируем low-tier → high-tier (материал → процесс)."""
    ta = _tier(by_id.get(aid, {}).get("type"))
    tb = _tier(by_id.get(bid, {}).get("type"))
    return (bid, aid) if ta > tb else (aid, bid)


def _relation(src_fact: dict[str, Any], tgt_fact: dict[str, Any], default: str) -> str:
    """Тип ребра по типам и текстовым cue (детерминированно, без LLM)."""
    ts, tt = _tier(src_fact.get("type")), _tier(tgt_fact.get("type"))
    if ts == 2 and tt == 2:
        return "precedes"                                   # процесс → процесс = последовательность
    if _CAUSE_RE.search(str(tgt_fact.get("claim", "") or "")):
        return "causes"                                     # явная причинность в downstream-факте
    return default                                          # по умолчанию enables (материал питает процесс)


def _concept_segments(fact_id: str) -> list[str]:
    """
    Концепт-сегменты id: КРОМЕ корня-домена (первого) И листа-квалификатора (последнего).
    Лист обычно — действие/уточнение (`grain_use`, `oil_fiber`, `food`), а не сам концепт;
    его матчинг порождает шум (тег «food» → лист `…lentil.food`). Берём середину.
    Фолбэк для коротких id (≤2 сегментов): оставляем всё после корня.
    """
    segs = [s for s in str(fact_id).lower().split(".") if s]
    core = segs[1:-1] if len(segs) >= 3 else segs[1:]
    return [s for s in core if len(s) >= MIN_TOKEN_LEN]


def link_by_tags(
    facts: Sequence[dict[str, Any]],
    relation_type: str = DEFAULT_RELATION,
    confidence: float = DEFAULT_CONFIDENCE,
    knowledge_status: str = DEFAULT_STATUS,
) -> list[dict[str, Any]]:
    """
    Вывести направленные рёбра из тегов «Связи».

    Каждый факт должен иметь `fact_id` и теги в `links` (или `tags`).
    Возвращает список dict-рёбер: {source_id, target_id, relation_type,
    confidence, knowledge_status}. Совместим и с `compose_essence(relations=...)`,
    и с `CausalGraph.add_relation`.
    """
    # индекс: сегмент-концепт → множество fact_id, у которых он есть в id
    seg_index: dict[str, set] = {}
    for f in facts:
        fid = str(f.get("fact_id", ""))
        if not fid:
            continue
        for seg in _concept_segments(fid):
            seg_index.setdefault(seg, set()).add(fid)

    by_id = {str(f.get("fact_id", "")): f for f in facts if f.get("fact_id")}
    edges: list[dict[str, Any]] = []
    seen: set = set()
    incoming: dict[str, int] = {}

    for f in facts:
        bid = str(f.get("fact_id", ""))
        if not bid:
            continue
        tags = parse_tags(f.get("links", f.get("tags", "")))
        for tag in tags:
            sources = seg_index.get(tag, ())
            # слишком широкий токен (категория вроде «food»/«oil») → не специфичная связь
            if len(sources) > MAX_SEGMENT_FANOUT:
                continue
            for aid in sorted(sources):  # sorted → детерминированный порядок
                if aid == bid:
                    continue
                # ① ориентация по типу: материал/источник → процесс/следствие
                src, tgt = _orient(aid, bid, by_id)
                if src == tgt:
                    continue
                key = (src, tgt)
                if key in seen:
                    continue
                if incoming.get(tgt, 0) >= MAX_INCOMING_PER_FACT:
                    continue
                seen.add(key)
                incoming[tgt] = incoming.get(tgt, 0) + 1
                # ② тип ребра по типам + текстовым cue (precedes/causes/enables)
                rel = _relation(by_id.get(src, {}), by_id.get(tgt, {}), relation_type)
                edges.append({
                    "source_id": src,
                    "target_id": tgt,
                    "relation_type": rel,
                    "confidence": confidence,
                    "knowledge_status": knowledge_status,
                })
    return edges


__all__ = ["parse_tags", "link_by_tags", "DEFAULT_RELATION"]
