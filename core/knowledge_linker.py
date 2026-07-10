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

import math
import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from typing import Any

DEFAULT_RELATION = "enables"          # валидный FORWARD-тип CausalGraph
DEFAULT_CONFIDENCE = 0.6
DEFAULT_STATUS = "inferred"           # валидный knowledge_status
MIN_TOKEN_LEN = 3
MAX_INCOMING_PER_FACT = 8             # защита от взрыва рёбер на широких тегах
MAX_SEGMENT_FANOUT = 4               # токен, совпадающий с >N фактами = категория (не связь) → скип

# Семантический practical-linker работает precision-first: общие редкие термины,
# не более одного соседа внутри practical-кластера и двух мостов к фундаментам.
MAX_SEMANTIC_TOKEN_FANOUT = 64
MAX_PRACTICAL_NEIGHBORS = 1
MAX_FOUNDATION_BRIDGES = 2
MIN_SEMANTIC_SHARED_TOKENS = 2
MIN_SEMANTIC_SCORE = 0.16
MIN_FOUNDATION_SCORE = 0.18
STRONG_FOUNDATION_SCORE = 0.26
MAX_NAMESPACE_NEIGHBORS = 1          # не более одного namespace-neighbor на узел

# Основы рёбер, допустимые для сильного causal reasoning в Essence.
CAUSAL_EDGE_BASES = frozenset({
    "curated_explicit",
    "explicit_tag",
    "practical_foundation",
})

# Структурные/семантические — не доказывают причинность.
STRUCTURAL_EDGE_BASES = frozenset({
    "namespace",
    "semantic_similarity",
})


def is_causal_edge_basis(edge_basis: str | None) -> bool:
    """Ребро может участвовать в causal chain (не structural-only)."""
    return str(edge_basis or "") in CAUSAL_EDGE_BASES


def is_causal_for_essence(edge: dict[str, Any]) -> bool:
    """Сильное причинное ребро для Essence: curated, tag, foundation с score."""
    basis = str(edge.get("edge_basis", ""))
    if basis == "curated_explicit":
        return True
    if basis == "explicit_tag":
        return True
    if basis == "practical_foundation":
        score = float(edge.get("semantic_score") or 0)
        return score >= MIN_FOUNDATION_SCORE
    return False


def relation_is_causal_for_essence(
    relation_type: str,
    metadata: dict[str, Any] | None,
) -> bool:
    """Runtime-проверка Relation из CausalGraph для Essence."""
    if not metadata:
        # Existing runtime/manual relations predate edge_basis metadata.  Keep
        # their explicitly causal types usable while filtering tagged KB edges.
        return relation_type in {"causes", "enables", "requires", "prevents", "precedes"}
    basis = str(metadata.get("edge_basis", ""))
    if basis == "namespace" or basis == "semantic_similarity":
        return False
    if basis == "analogous_to":
        return False
    if basis in CAUSAL_EDGE_BASES:
        return relation_type in {"causes", "enables", "requires", "prevents", "precedes"}
    if basis == "practical_foundation":
        score = float(metadata.get("semantic_score") or 0)
        return score >= MIN_FOUNDATION_SCORE and relation_type in {
            "enables", "requires", "prevents", "precedes",
        }
    return False


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
    "material": 0,
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

_TYPE_ALIASES = {
    "срок": "term",                 # историческая опечатка/перевод TERM в seed-паках
    "термин": "term",
    "закон": "law",
    "аксиома": "axiom",
    "теорема": "theorem",
    "формула": "formula",
    "принцип": "principle",
    "определение": "definition",
    "концепт": "concept",
    "факт": "fact",
    "модель": "model",
    "материал": "material",
    "свойство": "property",
    "ограничение": "constraint",
    "механизм": "mechanism",
    "процесс": "process",
    "метод": "method",
    "практический": "practical",
    "практика": "practical",
    "эвристика": "heuristic",
    "режим_отказа": "failure_mode",
    "отказ": "failure_mode",
    "безопасность_правило": "safety_rule",
    "правило_безопасности": "safety_rule",
    "проверка_качества": "quality_check",
    "контроль": "control",
    "измерение": "measurement",
    "компонент": "component",
    "система": "system",
    "состояние": "state",
    "вариант": "variant",
}

# Явные причинные cue в тексте claim (ru+en) → отношение "causes".
_CAUSE_RE = re.compile(r"(вызыва|приводит к|из-за|причин|causes|leads to|because)", re.I)


def normalize_type(fact_type: Any) -> str:
    """Нормализовать смешанную RU/EN и разнорегистровую типологию World Skills."""
    raw = str(fact_type or "").strip().lower().replace(" ", "_")
    return _TYPE_ALIASES.get(raw, raw)


def _tier(fact_type: Any) -> int:
    return _TYPE_TIER.get(normalize_type(fact_type), 1)


def _orient(aid: str, bid: str, by_id: dict[str, dict[str, Any]]) -> tuple:
    """Структурное ребро aid→bid ориентируем low-tier → high-tier (материал → процесс)."""
    ta = _tier(by_id.get(aid, {}).get("type"))
    tb = _tier(by_id.get(bid, {}).get("type"))
    return (bid, aid) if ta > tb else (aid, bid)


def _relation(src_fact: dict[str, Any], tgt_fact: dict[str, Any], default: str) -> str:
    """Тип ребра по типам (детерминированно, без LLM).

    Autolinker НЕ выводит causes из текста claim — только curated_explicit.
    """
    ts, tt = _tier(src_fact.get("type")), _tier(tgt_fact.get("type"))
    if ts == 2 and tt == 2:
        return "precedes"
    return default


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
                    "edge_basis": "explicit_tag",
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

NAMESPACE_CONFIDENCE = 0.35         # таксономическая близость, не причинность
NAMESPACE_BRIDGE_CONFIDENCE = 0.30  # ещё более слабый мост между подтемами домена
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
    neighbor_count: dict[str, int] = defaultdict(int)

    def _emit(src: str, tgt: str, conf: float) -> None:
        if src == tgt:
            return
        if neighbor_count[src] >= MAX_NAMESPACE_NEIGHBORS:
            return
        if neighbor_count[tgt] >= MAX_NAMESPACE_NEIGHBORS:
            return
        s, t = src, tgt
        if s == t or (s, t) in seen:
            return
        seen.add((s, t))
        neighbor_count[s] += 1
        neighbor_count[t] += 1
        edges.append({
            "source_id": s, "target_id": t, "relation_type": "analogous_to",
            "confidence": conf, "knowledge_status": knowledge_status,
            "inference_source": inference_source,
            "edge_basis": "namespace",
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


# ═══════════════════════════════════════════════════════════════════════════════
# Смысловые practical-связи: редкие общие термины + типовая ориентация
# ═══════════════════════════════════════════════════════════════════════════════

_TOKEN_RE = re.compile(r"[a-zа-яё][a-zа-яё0-9_\-]{2,}", re.I)
_STOPWORDS = frozenset({
    "более", "будет", "быть", "если", "когда", "который", "между", "может",
    "нужно", "после", "перед", "при", "также", "требует", "через", "чтобы",
    "этого", "этот", "этой", "использовать", "используется", "проверить",
    "для", "или", "без", "под", "над", "как", "это", "the", "and", "with",
    "from", "that", "this", "into", "after", "before", "using", "used",
})
_STOP_STEMS = frozenset({
    "данн", "компан", "метод", "операц", "практическ", "процесс", "работ",
    "результат", "систем", "способ", "технолог",
})
_RU_SUFFIXES = (
    "иями", "ями", "ами", "ого", "ему", "ому", "ыми", "ими", "ение", "ений",
    "ания", "аний", "остью", "остям", "овых", "евым", "ным", "ных", "ая", "яя",
    "ое", "ее", "ые", "ие", "ый", "ий", "ой", "ам", "ям", "ах", "ях", "ов",
    "ев", "ом", "ем", "ою", "ею", "у", "ю", "а", "я", "ы", "и", "е", "ь",
)


def _token_key(token: str) -> str:
    """Схлопнуть очевидные RU-окончания, не превращая линковщик в морфологический NLP."""
    if not re.search(r"[а-яё]", token) or len(token) < 7:
        return token
    for suffix in _RU_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[:-len(suffix)]
    return token


def _semantic_tokens(fact: dict[str, Any]) -> set[str]:
    text = " ".join(
        str(fact.get(field, "") or "")
        for field in ("fact_id", "knowledge_unit", "claim", "conditions", "practical")
    ).lower()
    out: set[str] = set()
    for token in _TOKEN_RE.findall(text):
        for part in re.split(r"[_\-]+", token):
            key = _token_key(part)
            if (
                len(key) >= 4
                and part not in _STOPWORDS
                and key not in _STOP_STEMS
                and not key.isdigit()
            ):
                out.add(key)
    return out


def _is_practical_fact(fact: dict[str, Any]) -> bool:
    fid = str(fact.get("fact_id", "")).lower()
    ftype = normalize_type(fact.get("type"))
    namespace_parts = [part for part in fid.split(".") if part]
    return (
        any(part == "ops" or part.endswith("ops") for part in namespace_parts)
        or fid.startswith("practical.")
        or ftype in {"practical", "process_step"}
        or bool((fact.get("metadata") or {}).get("practical_domain"))
    )


_FOUNDATION_TYPES = frozenset({
    "law", "axiom", "theorem", "formula", "principle", "definition", "concept",
    "fact", "model", "invariant", "term", "material", "material_source", "property",
    "constraint", "mechanism",
})


def _is_foundation_fact(fact: dict[str, Any]) -> bool:
    return not _is_practical_fact(fact) and normalize_type(fact.get("type")) in _FOUNDATION_TYPES


def _semantic_relation(
    aid: str,
    bid: str,
    by_id: dict[str, dict[str, Any]],
) -> tuple[str, str, str]:
    """Выбрать честную ориентацию для сильной лексико-типовой связи."""
    at = normalize_type(by_id[aid].get("type"))
    bt = normalize_type(by_id[bid].get("type"))
    safety = {"safety_rule", "control", "quality_check"}
    failures = {"failure_mode"}
    actions = {"method", "process", "practical", "process_step", "mechanism"}

    if at in safety and bt in failures:
        return aid, bid, "prevents"
    if bt in safety and at in failures:
        return bid, aid, "prevents"
    if at in actions and bt in safety:
        return aid, bid, "requires"
    if bt in actions and at in safety:
        return bid, aid, "requires"
    return aid, bid, "analogous_to"


def link_practical_semantics(
    facts: Sequence[dict[str, Any]],
    *,
    max_token_fanout: int = MAX_SEMANTIC_TOKEN_FANOUT,
) -> list[dict[str, Any]]:
    """Связать practical-узлы по смыслу и построить мосты к фундаментам.

    Алгоритм не использует сеть/LLM: TF-IDF-подобный score по редким общим терминам.
    Внутри practical-домена добавляется максимум один смысловой сосед, к непрактическим
    фундаментам — максимум два моста. Совпавшие термины сохраняются для аудита.
    """
    by_id = {str(f.get("fact_id", "")): f for f in facts if f.get("fact_id")}
    tokens = {fid: _semantic_tokens(f) for fid, f in by_id.items()}
    df = Counter(token for values in tokens.values() for token in values)
    informative = {
        token for token, count in df.items()
        if 2 <= count <= max_token_fanout
    }
    index: dict[str, list[str]] = defaultdict(list)
    for fid, values in tokens.items():
        for token in values & informative:
            index[token].append(fid)

    total = max(1, len(by_id))
    idf = {
        token: math.log((total + 1) / (df[token] + 1)) + 1.0
        for token in informative
    }
    norms = {
        fid: math.sqrt(sum(idf[t] ** 2 for t in values & informative))
        for fid, values in tokens.items()
    }

    practical_ids = sorted(fid for fid, fact in by_id.items() if _is_practical_fact(fact))
    practical_set = set(practical_ids)
    seen: set[frozenset[str]] = set()
    edges: list[dict[str, Any]] = []

    def ranked_candidates(pid: str) -> list[tuple[float, str, list[str]]]:
        shared_weight: dict[str, float] = defaultdict(float)
        shared_terms: dict[str, set[str]] = defaultdict(set)
        for token in tokens[pid] & informative:
            weight = idf[token] ** 2
            for cid in index[token]:
                if cid == pid:
                    continue
                shared_weight[cid] += weight
                shared_terms[cid].add(token)
        out: list[tuple[float, str, list[str]]] = []
        for cid, weight in shared_weight.items():
            terms = sorted(shared_terms[cid])
            denom = norms[pid] * norms[cid]
            if len(terms) < MIN_SEMANTIC_SHARED_TOKENS or denom <= 0:
                continue
            score = weight / denom
            if score >= MIN_SEMANTIC_SCORE:
                out.append((score, cid, terms))
        return sorted(out, key=lambda item: (-item[0], item[1]))

    def emit(
        src: str,
        tgt: str,
        relation: str,
        score: float,
        terms: list[str],
        basis: str,
    ) -> None:
        pair = frozenset((src, tgt))
        if src == tgt or pair in seen:
            return
        seen.add(pair)
        base = 0.52 if basis == "semantic_similarity" else 0.56
        confidence = round(min(0.72, base + score * 0.30), 3)
        edges.append({
            "source_id": src,
            "target_id": tgt,
            "relation_type": relation,
            "confidence": confidence,
            "knowledge_status": "inferred",
            "inference_source": "autolinker",
            "edge_basis": basis,
            "matched_terms": terms[:8],
            "semantic_score": round(score, 3),
        })

    for pid in practical_ids:
        ranked = ranked_candidates(pid)
        domain = pid.split(".", 1)[0]

        local = [
            item for item in ranked
            if item[1] in practical_set and item[1].split(".", 1)[0] == domain
        ][:MAX_PRACTICAL_NEIGHBORS]
        for score, cid, terms in local:
            src, tgt, relation = _semantic_relation(pid, cid, by_id)
            emit(src, tgt, relation, score, terms, "semantic_similarity")

        foundations = [
            item for item in ranked
            if (
                item[1] not in practical_set
                and _is_foundation_fact(by_id[item[1]])
                and (
                    item[0] >= STRONG_FOUNDATION_SCORE
                    or (item[0] >= MIN_FOUNDATION_SCORE and len(item[2]) >= 3)
                )
            )
        ][:MAX_FOUNDATION_BRIDGES]
        for score, cid, terms in foundations:
            emit(cid, pid, "enables", score, terms, "practical_foundation")

    return edges


def link_facts(
    facts: Sequence[dict[str, Any]],
    *,
    include_curated: bool = True,
) -> list[dict[str, Any]]:
    """Полный набор рёбер по убыванию качества.

    0. Курируемые causal relations (curated_explicit).
    1. Явные теги источника (explicit_tag).
    2. Редкие общие термины practical↔practical/theory (semantic_*).
    3. Namespace-каркас (analogous_to, ≤1 сосед/узел) только для покрытия.
    """
    curated_edges: list[dict[str, Any]] = []
    if include_curated:
        try:
            from core.curated_causal import link_curated_relations
            curated_edges = link_curated_relations(facts)
        except Exception:  # noqa: BLE001
            curated_edges = []
    tag_edges = link_by_tags(facts)
    semantic_edges = link_practical_semantics(facts)
    pairs: set[frozenset[str]] = set()
    out: list[dict[str, Any]] = []
    for e in [*curated_edges, *tag_edges, *semantic_edges]:
        pair = frozenset((e["source_id"], e["target_id"]))
        if pair in pairs:
            continue
        pairs.add(pair)
        out.append(e)
    for e in link_by_namespace(facts):
        pair = frozenset((e["source_id"], e["target_id"]))
        if pair in pairs:
            continue
        pairs.add(pair)
        out.append(e)
    return dedup_edges(out)


def graph_quality_report(
    facts: Sequence[dict[str, Any]],
    edges: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Компактные проверяемые метрики качества экспортируемого KB-графа."""
    by_id = {str(f.get("fact_id", "")): f for f in facts if f.get("fact_id")}
    node_ids = set(by_id)
    degrees: Counter[str] = Counter()
    valid_edges: list[dict[str, Any]] = []
    for edge in edges:
        src = str(edge.get("source_id", ""))
        tgt = str(edge.get("target_id", ""))
        if src not in node_ids or tgt not in node_ids or src == tgt:
            continue
        valid_edges.append(edge)
        degrees[src] += 1
        degrees[tgt] += 1

    practical_ids = {fid for fid, fact in by_id.items() if _is_practical_fact(fact)}
    practical_touch = 0
    practical_bridge = 0
    cross_domain = 0
    for edge in valid_edges:
        src, tgt = str(edge["source_id"]), str(edge["target_id"])
        src_practical, tgt_practical = src in practical_ids, tgt in practical_ids
        if src_practical or tgt_practical:
            practical_touch += 1
        if src_practical != tgt_practical:
            practical_bridge += 1
        if src.split(".", 1)[0] != tgt.split(".", 1)[0]:
            cross_domain += 1

    connected = sum(1 for fid in node_ids if degrees[fid] > 0)
    edge_count = len(valid_edges)
    curated = sum(1 for e in valid_edges if e.get("edge_basis") == "curated_explicit")
    inferred = sum(1 for e in valid_edges if e.get("knowledge_status") == "inferred")
    return {
        "nodes": len(node_ids),
        "edges": edge_count,
        "connected_nodes": connected,
        "isolated_nodes": len(node_ids) - connected,
        "coverage_pct": round(100.0 * connected / max(1, len(node_ids)), 2),
        "average_degree": round(2.0 * edge_count / max(1, len(node_ids)), 2),
        "by_relation_type": dict(Counter(str(e.get("relation_type", "")) for e in valid_edges)),
        "by_edge_basis": dict(Counter(str(e.get("edge_basis", "unknown")) for e in valid_edges)),
        "curated_edges": curated,
        "inferred_edges": inferred,
        "curated_ratio_pct": round(100.0 * curated / max(1, edge_count), 2),
        "cross_domain_edges": cross_domain,
        "cross_domain_pct": round(100.0 * cross_domain / max(1, edge_count), 2),
        "practical_nodes": len(practical_ids),
        "practical_touch_edges": practical_touch,
        "practical_bridge_edges": practical_bridge,
        "practical_bridge_pct": round(
            100.0 * practical_bridge / max(1, practical_touch), 2
        ),
    }


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
    "link_practical_semantics",
    "link_facts",
    "graph_quality_report",
    "dedup_edges",
    "normalize_type",
    "is_causal_edge_basis",
    "is_causal_for_essence",
    "relation_is_causal_for_essence",
    "CAUSAL_EDGE_BASES",
    "STRUCTURAL_EDGE_BASES",
    "DEFAULT_RELATION",
]
