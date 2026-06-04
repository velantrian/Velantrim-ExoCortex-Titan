"""
🌍 core/living_context.py — Velantrim Living Context (Patch 14)
===============================================================
"Что с этим можно делать?" — практические связи вокруг факта.

8 измерений понимания:
  WHERE  — где это используется/встречается
  WHO    — кто использует / кто зависит
  HOW    — как можно взаимодействовать (affordances)
  WHAT   — что производит / что из него получается
  FEEL   — качественные характеристики (с числовой оценкой)
  ROLE   — какую роль играет в системе
  TIME   — временные характеристики
  DEEP   — глубокое / научное знание

Спек: VARIANT_A_FULL_LIVING_CONTEXT-1.md + VARIANT_B_CAUSAL_PLUS_LIVING-1.md
Version: Patch 14 v2
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime

# ═══════════════════════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AgentRelation:
    """Описание агента и его отношения к факту."""
    entity: str
    role:   str = ""     # "гнездится", "питается", "использует"
    weight: float = 1.0  # важность этой связи

    def to_dict(self) -> dict:
        return {"entity": self.entity, "role": self.role, "weight": self.weight}

    @classmethod
    def from_dict(cls, d: dict) -> AgentRelation:
        return cls(
            entity=d.get("entity", ""),
            role=d.get("role", ""),
            weight=float(d.get("weight", 1.0)),
        )


@dataclass
class TimeContext:
    """Временной контекст факта."""
    duration:   str | None = None   # "сотни лет", "мгновения"
    frequency:  str | None = None   # "ежегодно", "постоянно"
    lifecycle:  str | None = None   # "прорастает → растёт → плодоносит → умирает"
    season:     str | None = None   # "летом", "весной"

    def is_empty(self) -> bool:
        return not any([self.duration, self.frequency, self.lifecycle, self.season])

    def to_dict(self) -> dict:
        return {
            "duration":  self.duration,
            "frequency": self.frequency,
            "lifecycle": self.lifecycle,
            "season":    self.season,
        }

    @classmethod
    def from_dict(cls, d: dict) -> TimeContext:
        if not d:
            return cls()
        return cls(
            duration=d.get("duration"),
            frequency=d.get("frequency"),
            lifecycle=d.get("lifecycle"),
            season=d.get("season"),
        )


@dataclass
class LivingContext:
    """
    Живой контекст факта — 8 измерений понимания.
    Хранится в таблице fact_living_context (Patch 14).

    FIX (ChatGPT/DeepSeek): контекст вынесен в отдельную таблицу,
    не раздувает основную таблицу facts.
    """
    # 1. WHERE — где встречается/используется
    locations:   list[str] = field(default_factory=list)

    # 2. WHO — кто использует / кто зависит
    agents:      list[AgentRelation] = field(default_factory=list)

    # 3. HOW — affordances (что можно с этим сделать)
    affordances: list[str] = field(default_factory=list)

    # 4. WHAT — что производит / что из этого получается
    products:    list[str] = field(default_factory=list)

    # 5. FEEL — качественные характеристики с числовой оценкой [0.0, 1.0]
    qualities:   dict[str, float] = field(default_factory=dict)

    # 6. ROLE — какую роль играет в системе / экосистеме
    roles:       list[str] = field(default_factory=list)

    # 7. TIME — временные характеристики
    time:        TimeContext | None = None

    # 8. DEEP — глубокое / научное знание (формулы, механизмы)
    deep:        str | None = None

    def is_empty(self) -> bool:
        """FIX: полная проверка всех 8 измерений."""
        return (
            not self.locations
            and not self.agents
            and not self.affordances
            and not self.products
            and not self.qualities
            and not self.roles
            and (self.time is None or self.time.is_empty())
            and not self.deep
        )

    def to_dict(self) -> dict:
        """Lossless сериализация — FIX: была lossy в v1."""
        return {
            "where":  self.locations,
            "who":    [a.to_dict() for a in self.agents],
            "how":    self.affordances,
            "what":   self.products,
            "feel":   self.qualities,
            "role":   self.roles,
            "time":   self.time.to_dict() if self.time else None,
            "deep":   self.deep,
        }

    @classmethod
    def from_dict(cls, d: dict) -> LivingContext:
        """Десериализация из dict."""
        if not d:
            return cls()

        agents_raw = d.get("who", [])
        agents = []
        for a in agents_raw:
            if isinstance(a, dict):
                agents.append(AgentRelation.from_dict(a))
            elif isinstance(a, str):
                agents.append(AgentRelation(entity=a))

        time_raw = d.get("time")
        time_ctx = TimeContext.from_dict(time_raw) if time_raw else None

        return cls(
            locations=d.get("where", []),
            agents=agents,
            affordances=d.get("how", []),
            products=d.get("what", []),
            qualities=d.get("feel", {}),
            roles=d.get("role", []),
            time=time_ctx,
            deep=d.get("deep"),
        )

    def merge(self, other: LivingContext) -> LivingContext:
        """Слияние двух контекстов. Не перезаписывает — объединяет."""
        merged_agents = list(self.agents)
        existing_entities = {a.entity for a in self.agents}
        for a in other.agents:
            if a.entity not in existing_entities:
                merged_agents.append(a)

        merged_qualities = dict(self.qualities)
        for k, v in other.qualities.items():
            # Берём максимальное значение (более уверенное)
            merged_qualities[k] = max(merged_qualities.get(k, 0.0), v)

        return LivingContext(
            locations=list(set(self.locations + other.locations)),
            agents=merged_agents,
            affordances=list(set(self.affordances + other.affordances)),
            products=list(set(self.products + other.products)),
            qualities=merged_qualities,
            roles=list(set(self.roles + other.roles)),
            time=self.time or other.time,
            deep=self.deep or other.deep,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SQLite-backed store operations
# ═══════════════════════════════════════════════════════════════════════════════

class LivingContextStore:
    """
    Операции с fact_living_context таблицей.
    Инжектится в SQLiteGraphStore (или используется standalone).
    """

    def __init__(self, db_conn) -> None:
        self._conn = db_conn

    def get(self, fact_id: str) -> LivingContext | None:
        """Получить Living Context для факта."""
        row = self._conn.execute(
            """
            SELECT ctx_where, ctx_who, ctx_how, ctx_what,
                   ctx_feel, ctx_role, ctx_time, ctx_deep
            FROM fact_living_context
            WHERE fact_id = ?
            """,
            (fact_id,),
        ).fetchone()

        if not row:
            return None

        def _load(val, default):
            if not val:
                return default
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return default

        agents_raw = _load(row[1], [])
        agents = []
        for a in agents_raw:
            if isinstance(a, dict):
                agents.append(AgentRelation.from_dict(a))
            elif isinstance(a, str):
                agents.append(AgentRelation(entity=a))

        time_raw = _load(row[6], None)
        time_ctx = TimeContext.from_dict(time_raw) if time_raw else None

        return LivingContext(
            locations=_load(row[0], []),
            agents=agents,
            affordances=_load(row[2], []),
            products=_load(row[3], []),
            qualities=_load(row[4], {}),
            roles=_load(row[5], []),
            time=time_ctx,
            deep=row[7],
        )

    def set(self, fact_id: str, ctx: LivingContext) -> None:
        """Сохранить или обновить Living Context."""
        now = datetime.now(UTC).isoformat()

        self._conn.execute(
            """
            INSERT INTO fact_living_context
                (fact_id, ctx_where, ctx_who, ctx_how, ctx_what,
                 ctx_feel, ctx_role, ctx_time, ctx_deep, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fact_id) DO UPDATE SET
                ctx_where  = excluded.ctx_where,
                ctx_who    = excluded.ctx_who,
                ctx_how    = excluded.ctx_how,
                ctx_what   = excluded.ctx_what,
                ctx_feel   = excluded.ctx_feel,
                ctx_role   = excluded.ctx_role,
                ctx_time   = excluded.ctx_time,
                ctx_deep   = excluded.ctx_deep,
                updated_at = excluded.updated_at
            """,
            (
                fact_id,
                json.dumps(ctx.locations, ensure_ascii=False),
                json.dumps([a.to_dict() for a in ctx.agents], ensure_ascii=False),
                json.dumps(ctx.affordances, ensure_ascii=False),
                json.dumps(ctx.products, ensure_ascii=False),
                json.dumps(ctx.qualities, ensure_ascii=False),
                json.dumps(ctx.roles, ensure_ascii=False),
                json.dumps(ctx.time.to_dict(), ensure_ascii=False) if ctx.time else None,
                ctx.deep,
                now,
            ),
        )
        self._conn.commit()

    def update(self, fact_id: str, ctx: LivingContext) -> None:
        """Merge с существующим контекстом (не перезаписывает)."""
        existing = self.get(fact_id)
        if existing:
            merged = existing.merge(ctx)
        else:
            merged = ctx
        self.set(fact_id, merged)

    def delete(self, fact_id: str) -> bool:
        cur = self._conn.execute(
            "DELETE FROM fact_living_context WHERE fact_id = ?",
            (fact_id,),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def search_by_affordance(
        self,
        affordance: str,
        min_confidence: float = 0.0,
    ) -> list[str]:
        """
        Найти факты с данным affordance.
        FIX (Perplexity/DeepSeek): использует fact_affordance_tokens
        вместо LIKE по JSON (быстро, по индексу).
        """
        normalized = affordance.lower().strip()
        rows = self._conn.execute(
            """
            SELECT DISTINCT fat.fact_id
            FROM fact_affordance_tokens fat
            JOIN fact_affordances fa ON fa.fact_id = fat.fact_id
            WHERE fat.token = ?
              AND fat.field = 'affordance'
              AND fa.confidence >= ?
            """,
            (normalized, min_confidence),
        ).fetchall()
        return [row[0] for row in rows]

    def index_affordance_tokens(self, fact_id: str, ctx: LivingContext) -> None:
        """
        Обновить индекс токенов для быстрого поиска.
        Вызывать после каждого set/update.
        """
        self._conn.execute(
            "DELETE FROM fact_affordance_tokens WHERE fact_id = ?",
            (fact_id,),
        )
        for affordance in ctx.affordances:
            for token in self._tokenize(affordance):
                try:
                    self._conn.execute(
                        """
                        INSERT OR IGNORE INTO fact_affordance_tokens
                        (fact_id, token, field) VALUES (?, ?, 'affordance')
                        """,
                        (fact_id, token),
                    )
                except Exception:
                    pass
        for product in ctx.products:
            for token in self._tokenize(product):
                try:
                    self._conn.execute(
                        """
                        INSERT OR IGNORE INTO fact_affordance_tokens
                        (fact_id, token, field) VALUES (?, ?, 'product')
                        """,
                        (fact_id, token),
                    )
                except Exception:
                    pass
        for agent in ctx.agents:
            for token in self._tokenize(agent.entity):
                try:
                    self._conn.execute(
                        """
                        INSERT OR IGNORE INTO fact_affordance_tokens
                        (fact_id, token, field) VALUES (?, ?, 'agent')
                        """,
                        (fact_id, token),
                    )
                except Exception:
                    pass
        self._conn.commit()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """
        Простая токенизация. FIX: использует pymorphy2 если установлен
        для лемматизации русских слов.
        """
        tokens = [t.lower().strip() for t in text.split() if len(t) > 2]
        try:
            import pymorphy2
            morph = pymorphy2.MorphAnalyzer()
            tokens = [morph.parse(t)[0].normal_form for t in tokens]
        except ImportError:
            pass
        return tokens
