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
    # Реальные типы батчей world_skills_core (в источнике UPPERCASE; здесь — нормализованный
    # lower). Без них всё уходило в дефолтный тир 1 и ориентация рёбер была случайной.
    "invariant": 0, "term": 0, "system": 0,                              # основания/сущности
    "variant": 1, "record": 1, "state": 1, "measurement": 1, "component": 1,  # описания/свойства
    "practical": 2, "process_step": 2,                                   # действия
    "quality_check": 3, "control": 3,                                    # проверки/митигация
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
                    "inference_source": "autolinker",  # FIX #12 (Claude audit)
                })
    return edges


# ═══════════════════════════════════════════════════════════════════════════════
# Структурная связность из namespace-иерархии id (P0-fix, 2026-06-03)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Проблема: контракт генерации батчей (WORLD_SKILLS_CORE_STATE.ru.json) сменил формат
# на `ID | KnowledgeUnit | Тип | Суть | Практический смысл` — колонку «Связи» УБРАЛИ.
# Парсер читает 5-ю колонку как `links`, поэтому link_by_tags теперь питается прозой
# «Практический смысл» и связывает лишь ~16% фактов (остальные 79% — изолированные узлы).
#
# Этот линковщик НЕ зависит от тегов. Он строит рёбра из САМОЙ ИЕРАРХИИ id
# (`domain.subdomain.term`), которую задал куратор и которая всегда присутствует:
#   • внутри подтемы (`domain.subdomain.*`) — звезда от «фундамента» (низший тип-тир)
#     к остальным единицам подтемы (anchor --enables/precedes--> member);
#   • между подтемами одного домена — звезда от доменного «фундамента» к якорям подтем.
# Так каждый домен становится ОДНОЙ компонентой связности (а не россыпью одиночек).
#
# Честность: рёбра помечаются knowledge_status='inferred' + inference_source='autolinker'
# (выведены из таксономии id, НЕ доказаны) с умеренной уверенностью (структура < тег-матч).
# Кросс-доменные связи здесь НЕ создаются — домены остаются отдельными компонентами,
# пока их не свяжет тег-матч или (следующий тиер) семантика по эмбеддингам.

NAMESPACE_CONFIDENCE = 0.5          # структурная связь внутри подтемы — слабее тег-матча (0.6)
# FIX #17 (Claude audit): bridge_confidence был 0.4 — multi-hop reasoning не пересекал
# подразделы на дефолтном пороге (0.5). Поднято до 0.5.
NAMESPACE_BRIDGE_CONFIDENCE = 0.5   # связь-мост между подтемами домена — равно внутри-подтеме
NAMESPACE_INFERENCE_SOURCE = "autolinker"
STAR_MAX = 24                       # группа крупнее → цепочка вместо звезды (ограничить степень)


def _subdomain_key(fact_id: str) -> tuple[str, str]:
    """(domain, subdomain-prefix). domain = первый сегмент id; subdomain-prefix = id без
    последнего сегмента (группа сиблингов одной подтемы). Для id из ≤2 сегментов подтема = домен.
    Пример: `vitalfeeops.intake.request_source` → ('vitalfeeops', 'vitalfeeops.intake')."""
    segs = [s for s in str(fact_id).lower().split(".") if s]
    if not segs:
        return str(fact_id), str(fact_id)
    domain = segs[0]
    sub = ".".join(segs[:-1]) if len(segs) >= 2 else domain
    return domain, sub


def _anchor(fids: Sequence[str], by_id: dict[str, dict[str, Any]]) -> str:
    """«Фундамент» группы: факт низшего тип-тира (источник/основание), при равенстве —
    лексикографически первый. Детерминированно (одинаков на каждом ре-ране)."""
    return min(fids, key=lambda f: (_tier(by_id.get(f, {}).get("type")), f))


def link_by_namespace(
    facts: Sequence[dict[str, Any]],
    confidence: float = NAMESPACE_CONFIDENCE,
    bridge_confidence: float = NAMESPACE_BRIDGE_CONFIDENCE,
    knowledge_status: str = DEFAULT_STATUS,
    inference_source: str = NAMESPACE_INFERENCE_SOURCE,
) -> list[dict[str, Any]]:
    """Вывести структурные рёбра из иерархии id (без тегов). См. блок выше.

    Возвращает список dict-рёбер {source_id, target_id, relation_type, confidence,
    knowledge_status, inference_source} — совместим с link_by_tags и CausalGraph.add_relation.
    """
    by_id = {str(f.get("fact_id", "")): f for f in facts if f.get("fact_id")}
    # группировка: domain -> subdomain -> [fact_id...]
    domains: dict[str, dict[str, list[str]]] = {}
    for fid in by_id:
        domain, sub = _subdomain_key(fid)
        domains.setdefault(domain, {}).setdefault(sub, []).append(fid)

    edges: list[dict[str, Any]] = []
    seen: set = set()

    def _emit(src: str, tgt: str, conf: float) -> None:
        if src == tgt:
            return
        s, t = _orient(src, tgt, by_id)           # low-tier → high-tier (фундамент → следствие)
        if s == t or (s, t) in seen:
            return
        seen.add((s, t))
        rel = _relation(by_id.get(s, {}), by_id.get(t, {}), DEFAULT_RELATION)
        edges.append({
            "source_id": s, "target_id": t, "relation_type": rel,
            "confidence": conf, "knowledge_status": knowledge_status,
            "inference_source": inference_source,
        })

    def _connect_group(members: list[str], conf: float) -> str:
        """Связать группу и вернуть её якорь. Звезда от якоря; на крупных группах —
        цепочка (anchor→m1→m2→…), чтобы не раздувать степень якоря."""
        anchor = _anchor(members, by_id)
        rest = [m for m in sorted(members) if m != anchor]
        if len(members) <= STAR_MAX:
            for m in rest:                         # звезда: диаметр 2 внутри подтемы
                _emit(anchor, m, conf)
        else:
            prev = anchor                          # цепочка: ограниченная степень
            for m in rest:
                _emit(prev, m, conf)
                prev = m
        return anchor

    for domain in sorted(domains):
        subs = domains[domain]
        sub_anchors = [_connect_group(subs[sub], confidence) for sub in sorted(subs)]
        # мост между подтемами: доменный якорь → якорь каждой подтемы → домен = 1 компонента
        if len(sub_anchors) >= 2:
            dom_anchor = _anchor(sub_anchors, by_id)
            for a in sub_anchors:
                _emit(dom_anchor, a, bridge_confidence)
    return edges


def link_facts(facts: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Полный набор рёбер: тег-матч (точные, conf 0.6) ∪ namespace-структура (покрытие,
    conf 0.4–0.5). Namespace-ребро добавляется, только если такой ПАРЫ ещё нет среди
    тег-рёбер (в любом направлении) — точные тег-связи приоритетны и не дублируются."""
    tag_edges = link_by_tags(facts)
    pairs: set = {frozenset((e["source_id"], e["target_id"])) for e in tag_edges}
    out: list[dict[str, Any]] = list(tag_edges)
    for e in link_by_namespace(facts):
        pair = frozenset((e["source_id"], e["target_id"]))
        if pair in pairs:
            continue
        pairs.add(pair)
        out.append(e)
    return dedup_edges(out)


# ═══════════════════════════════════════════════════════════════════════════════
# Дедупликация рёбер (из Wiki-MCP-Server, апрель 2026)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Проблема: одна пара фактов может получить несколько рёбер разных типов
# (например, тег-матч → enables, namespace → precedes). Нужно выбрать
# лучшее — с максимальным весом типа.
#
# Алгоритм (из статьи): для каждой пары (source, target) — оставить ребро
# с максимальным весом RELATION_TYPE_WEIGHTS. При равенстве — большее confidence.


def dedup_edges(
    edges: list[dict[str, Any]],
    *,
    weight_map: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """
    Удалить дублирующиеся рёбра для одной пары фактов.

    Если пара (source, target) имеет несколько рёбер (разные relation_type),
    оставляется ТОЛЬКО одно — с максимальным весом типа × confidence.

    Args:
        edges: список dict-рёбер {source_id, target_id, relation_type, confidence, ...}
        weight_map: словарь весов типов (по умолчанию RELATION_TYPE_WEIGHTS из causal_graph)

    Returns:
        Дедуплицированный список рёбер.
    """
    if weight_map is None:
        try:
            from core.causal_graph import RELATION_TYPE_WEIGHTS
            weight_map = RELATION_TYPE_WEIGHTS
        except ImportError:
            weight_map = {}

    best: dict[tuple[str, str], tuple[dict[str, Any], float]] = {}

    for e in edges:
        src = str(e.get("source_id", ""))
        tgt = str(e.get("target_id", ""))
        if not src or not tgt or src == tgt:
            continue

        rtype = str(e.get("relation_type", ""))
        conf = float(e.get("confidence", 0.5))
        type_weight = weight_map.get(rtype, 0.5)
        score = conf * type_weight

        key = (src, tgt)
        if key not in best or score > best[key][1]:
            best[key] = (e, score)

    return [v[0] for v in best.values()]


__all__ = [
    "parse_tags",
    "link_by_tags",
    "link_by_namespace",
    "link_facts",
    "dedup_edges",
    "DEFAULT_RELATION",
]
