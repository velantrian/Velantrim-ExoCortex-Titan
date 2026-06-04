"""
🌐 core/essence/situation.py — Situation Model (V8.7 Titan)

Расширяет living_context.py тремя полями:
    actors        — кто участвует в ситуации
    tension       — в чём проблема/напряжение
    missing_piece — чего не хватает для решения

Обёртка над living_context.py. Файл не перемещён.

Использование:
    from core.essence import build_situation
    model = build_situation(facts, query, user_id="default")
    print(model.actors)     # ["user", "Velantrim", "external_ai"]
    print(model.tension)    # "storage is not understanding"
    print(model.missing_piece)  # "gist-level compression"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SituationModel:
    """
    Модель текущей сцены мышления.
    Не факты о мире — а «картина происходящего».
    """

    # ── Из living_context (существующие 8 измерений) ─────────────────────
    where: List[str] = field(default_factory=list)     # WHERE — где используется
    who: List[str] = field(default_factory=list)       # WHO — кто использует
    how: List[str] = field(default_factory=list)       # HOW — affordances
    what: List[str] = field(default_factory=list)      # WHAT — что производит
    feel: Dict[str, float] = field(default_factory=dict)  # FEEL — качественные характеристики
    role: List[str] = field(default_factory=list)      # ROLE — роль в системе
    deep: Dict[str, Any] = field(default_factory=dict) # DEEP — научное знание

    # ── Новые поля (V8.7 Situation Model extension) ───────────────────────
    actors: List[str] = field(default_factory=list)
    tension: str = ""
    missing_piece: str = ""

    query: str = ""
    domain: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "where": self.where,
            "who": self.who,
            "how": self.how,
            "what": self.what,
            "feel": self.feel,
            "role": self.role,
            "actors": self.actors,
            "tension": self.tension,
            "missing_piece": self.missing_piece,
            "query": self.query,
            "domain": self.domain,
        }


def build_situation(
    facts: List[Dict[str, Any]],
    query: str = "",
    *,
    user_id: str = "default",
) -> SituationModel:
    """
    Построить Situation Model из фактов и запроса.

    Использует существующий living_context.py для 7 измерений
    и добавляет actors/tension/missing_piece.

    Args:
        facts: верифицированные факты.
        query: запрос пользователя.
        user_id: идентификатор пользователя.

    Returns:
        SituationModel.
    """
    model = SituationModel(query=query)

    # 1. LivingContext — существующие измерения
    try:
        fact_id = facts[0].get("fact_id", "") if facts else ""
        if fact_id:
            from core.living_context import LivingContextStore, get_living_store
            store = get_living_store()
            ctx = store.get(fact_id)
            if ctx:
                model.where = ctx.locations or []
                model.who = [a.entity for a in (ctx.agents or [])]
                model.how = ctx.affordances or []
                model.what = ctx.products or []
                model.feel = ctx.qualities or {}
                model.role = ctx.roles or []
                model.deep = ctx.to_dict().get("deep", {})
    except Exception:
        pass

    # 2. Actors — кто участвует
    model.actors = _detect_actors(query, facts)

    # 3. Tension — в чём проблема
    model.tension = _detect_tension(query, facts)

    # 4. Missing piece — чего не хватает
    model.missing_piece = _detect_missing_piece(facts)

    # 5. Domain
    try:
        for f in facts:
            meta = f.get("metadata", {})
            if isinstance(meta, dict) and meta.get("domain"):
                model.domain = str(meta["domain"])
                break
    except Exception:
        pass

    return model


def _detect_actors(query: str, facts: List[Dict[str, Any]]) -> List[str]:
    """Обнаружить участников ситуации."""
    actors: List[str] = ["user", "Velantrim"]

    sources = set(f.get("source", "") for f in facts if f.get("source"))
    if len(sources) > 3:
        actors.append("external_ai")
    if any("code" in (f.get("claim", "")).lower() for f in facts):
        actors.append("developer")
    if any("architecture" in (f.get("claim", "")).lower() for f in facts):
        actors.append("architect")

    return actors


def _detect_tension(query: str, facts: List[Dict[str, Any]]) -> str:
    """Обнаружить напряжение/проблему в ситуации."""
    # Ищем противоречивые факты
    states = set(f.get("epistemic_state", "") for f in facts)
    if "Contradicted" in states:
        return "противоречие в графе знаний"

    # Ищем запросы-проблемы
    if query:
        ql = query.lower()
        if any(w in ql for w in ["проблема", "не работает", "ошибка", "баг", "error", "bug"]):
            return "техническая проблема"
        if any(w in ql for w in ["не хватает", "missing", "недостаточно"]):
            return "нехватка данных/знаний"
        if any(w in ql for w in ["архитектура", "как построить", "architecture", "design"]):
            return "архитектурный выбор"

    return "поиск понимания"


def _detect_missing_piece(facts: List[Dict[str, Any]]) -> str:
    """Обнаружить чего не хватает."""
    # Если фактов мало — не хватает данных
    if len(facts) < 3:
        return "недостаточно верифицированных фактов"

    # Если все факты одного источника — не хватает независимых подтверждений
    sources = set(f.get("source", "") for f in facts)
    if len(sources) == 1:
        return f"только один источник ({list(sources)[0]}), нужны независимые"

    return ""


_situation_model: Optional[SituationModel] = None


def get_situation_model() -> SituationModel:
    global _situation_model
    if _situation_model is None:
        _situation_model = SituationModel()
    return _situation_model
