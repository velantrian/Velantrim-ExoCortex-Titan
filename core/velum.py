"""
Velum L1.5 — Synaptic Pre-Graph (RFC0016).

Sprint 2 / T2. In-memory трекер co-occurrence между сущностями эпизода.
Phase 0: только рёбра и веса, без ProtoConcept (RFC0066 — Sprint 3).

Назначение:
  - Живёт между L1 (эпизоды) и L2 (кластеры).
  - НЕ хранит содержимое — только undirected synapse (entity_a, entity_b) + weight.
  - Backend-agnostic: dict[frozenset[str], VelumEdge] в RAM.

Инварианты (RFC0016):
  Velum.I1: только рёбра, не факты — Graph=Truth не нарушается.
  Velum.I2: сильные рёбра при смене сессии → VelumSignal для L2.
  Velum.I3: слабые рёбра → decay, не промоут.
  Velum.I4: не персистентен по умолчанию.
  I77: мутации весов только под asyncio.Lock.

Связь:
  - core/fsrs.py — decay_edge_weight() при session decay и FSRS-пути.
"""

from __future__ import annotations

import asyncio
import math
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from itertools import combinations
from typing import Any

from core.fsrs import FSRSParams, decay_edge_weight

# ─── Конфигурация ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class VelumParams:
    """Параметры Velum L1.5 (RFC0016, Phase 0)."""

    window_episodes: int = 5
    co_occur_threshold: int = 3
    signal_weight_threshold: float = 0.6
    promote_weight: float = 0.6
    decay_per_session: float = 0.9
    max_edges: int = 1000
    gc_fraction: float = 0.25
    strengthen_factor: float = 1.1
    co_occur_weight_delta: float = 0.12
    max_weight: float = 1.0
    lateral_inhibition_factor: float = 0.95
    lateral_protection_threshold: float = 0.4
    protect_window_episodes: int = 5
    min_weight_floor: float = 1e-6
    # Graduated RAM guard (доля удаляемых рёбер при GC)
    ram_guard_soft: int = 1000
    ram_guard_medium: int = 1500
    ram_guard_critical: int = 2000
    gc_soft: float = 0.25
    gc_medium: float = 0.35
    gc_critical: float = 0.50
    fsrs: FSRSParams = field(default_factory=FSRSParams)
    default_edge_stability_days: float = 7.0


_DEFAULT_PARAMS = VelumParams()


# ─── Модели ───────────────────────────────────────────────────────────────────


def _normalize_entity(entity: object) -> str | None:
    if not isinstance(entity, str):
        return None
    cleaned = entity.strip()
    return cleaned if cleaned else None


def _edge_key(a: str, b: str) -> frozenset[str]:
    return frozenset((a, b))


def _ordered_pair(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a <= b else (b, a)


@dataclass
class VelumEdge:
    """Синапс между двумя сущностями (undirected)."""

    entity_a: str
    entity_b: str
    weight: float = 0.0
    co_occur_count: int = 0
    episode_window: deque[str] = field(default_factory=lambda: deque(maxlen=5))
    last_episode_id: str | None = None
    stability_days: float = 7.0
    last_touch: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    retrieval_hits: int = 0
    last_retrieval_episode: str | None = None
    salience_weight: float = 1.0

    @property
    def key(self) -> frozenset[str]:
        return frozenset((self.entity_a, self.entity_b))

    def window_distinct_episodes(self) -> int:
        return len(set(self.episode_window))

    def touch(
        self,
        episode_id: str,
        now: datetime,
        params: VelumParams,
        *,
        salience_weight: float = 1.0,
    ) -> None:
        self.co_occur_count += 1
        self.last_episode_id = episode_id
        self.last_touch = now
        sw = max(1.0, float(salience_weight)) if salience_weight else 1.0
        self.salience_weight = max(self.salience_weight, sw)
        if self.episode_window.maxlen != params.window_episodes:
            self.episode_window = deque(
                self.episode_window, maxlen=params.window_episodes
            )
        self.episode_window.append(episode_id)

    def other_entity(self, entity: str) -> str | None:
        if entity == self.entity_a:
            return self.entity_b
        if entity == self.entity_b:
            return self.entity_a
        return None


class VelumSignalKind(str):
    CO_OCCURRENCE = "CO_OCCURRENCE"
    SESSION_END_PROMOTE = "SESSION_END_PROMOTE"


@dataclass(frozen=True)
class VelumSignal:
    """Сигнал для ReactivationEngine / L2 (без ProtoConcept в Phase 0)."""

    kind: str
    entity_a: str
    entity_b: str
    weight: float
    co_occur_count: int
    episode_id: str | None = None


@dataclass
class ObserveResult:
    episode_id: str
    entities_seen: int
    edges_touched: int
    signals: list[VelumSignal] = field(default_factory=list)


@dataclass
class SessionEndResult:
    promoted: list[VelumSignal]
    decayed_edges: int
    gc_removed: int
    gc_fraction_applied: float


@dataclass
class VelumStats:
    edge_count: int
    episode_count: int
    avg_weight: float
    max_weight: float


@dataclass
class VelumDecayBatchResult:
    """Результат пакетного FSRS decay (Sprint 2 / T5)."""

    edges_processed: int
    edges_decayed: int
    edges_unchanged: int
    edges_pruned: int
    gc_removed: int
    avg_weight_before: float
    avg_weight_after: float


# ─── Velum ────────────────────────────────────────────────────────────────────


class Velum:
    """
    In-memory synaptic pre-graph.

    Async API: все мутации под self._lock (P0.5 / I77).
    """

    def __init__(self, params: VelumParams = _DEFAULT_PARAMS) -> None:
        self._params = params
        self._edges: dict[frozenset[str], VelumEdge] = {}
        self._degree_cache: dict[str, int] = {}
        self._episode_ids: set[str] = set()
        self._lock = asyncio.Lock()

    @property
    def params(self) -> VelumParams:
        return self._params

    async def observe_episode(
        self,
        episode_id: str,
        entities: Iterable[str],
        *,
        now: datetime | None = None,
        salience_weight: float = 1.0,
    ) -> ObserveResult:
        """
        Зафиксировать co-occurrence сущностей в эпизоде.

        Для каждой уникальной пары сущностей:
          - усилить ребро (Hebbian + fan-effect dampening);
          - lateral inhibition для слабых соседей;
          - при weight ≥ порога и count в окне ≥ порога — VelumSignal.
        """
        if now is None:
            now = datetime.now(UTC)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        normalized = self._normalize_entities(entities)
        signals: list[VelumSignal] = []
        edges_touched = 0

        async with self._lock:
            self._episode_ids.add(episode_id)
            if len(normalized) < 2:
                return ObserveResult(
                    episode_id=episode_id,
                    entities_seen=len(normalized),
                    edges_touched=0,
                    signals=signals,
                )

            salience = max(1.0, float(salience_weight)) if salience_weight else 1.0
            for a, b in combinations(sorted(normalized), 2):
                edge = await self._observe_pair(
                    a, b, episode_id, now, salience_weight=salience
                )
                edges_touched += 1
                if self._should_emit_co_occur_signal(edge):
                    signals.append(
                        VelumSignal(
                            kind=VelumSignalKind.CO_OCCURRENCE,
                            entity_a=edge.entity_a,
                            entity_b=edge.entity_b,
                            weight=edge.weight,
                            co_occur_count=edge.co_occur_count,
                            episode_id=episode_id,
                        )
                    )

            await self._maybe_gc_locked()

        return ObserveResult(
            episode_id=episode_id,
            entities_seen=len(normalized),
            edges_touched=edges_touched,
            signals=signals,
        )

    async def get_neighbors(
        self,
        entity: str,
        min_weight: float = 0.0,
        *,
        limit: int | None = None,
        episode_id: str | None = None,
    ) -> list[tuple[str, float]]:
        """
        Соседи сущности по synapse weight (для F1.5 context hint / retriever).

        Учитывает retrieval hit — защищает ребро от GC (protect window).
        """
        ent = _normalize_entity(entity)
        if ent is None:
            return []

        async with self._lock:
            if episode_id:
                for edge in self._edges.values():
                    if ent in edge.key:
                        edge.retrieval_hits += 1
                        edge.last_retrieval_episode = episode_id

            neighbors: list[tuple[str, float]] = []
            for edge in self._edges.values():
                if ent not in edge.key or edge.weight < min_weight:
                    continue
                other = edge.other_entity(ent)
                if other is not None:
                    neighbors.append((other, edge.weight))

        neighbors.sort(key=lambda x: x[1], reverse=True)
        if limit is not None and limit > 0:
            return neighbors[:limit]
        return neighbors

    async def on_session_end(
        self,
        *,
        now: datetime | None = None,
        use_fsrs_decay: bool = False,
    ) -> SessionEndResult:
        """
        Конец сессии: промоут сильных рёбер, decay слабых (Velum.I2/I3).

        use_fsrs_decay=True — weight *= retention(1 день, stability) вместо
        фиксированного decay_per_session.
        """
        if now is None:
            now = datetime.now(UTC)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        promoted: list[VelumSignal] = []
        decayed = 0

        async with self._lock:
            for edge in list(self._edges.values()):
                if edge.weight >= self._params.promote_weight:
                    promoted.append(
                        VelumSignal(
                            kind=VelumSignalKind.SESSION_END_PROMOTE,
                            entity_a=edge.entity_a,
                            entity_b=edge.entity_b,
                            weight=edge.weight,
                            co_occur_count=edge.co_occur_count,
                        )
                    )
                else:
                    if use_fsrs_decay:
                        edge.weight = decay_edge_weight(
                            edge.weight,
                            t_days=1.0,
                            stability=edge.stability_days,
                            params=self._params.fsrs,
                        )
                    else:
                        edge.weight *= self._params.decay_per_session
                    edge.weight = max(
                        self._params.min_weight_floor,
                        min(self._params.max_weight, edge.weight),
                    )
                    decayed += 1

            gc_removed, gc_frac = await self._gc_locked(force=False)

        return SessionEndResult(
            promoted=promoted,
            decayed_edges=decayed,
            gc_removed=gc_removed,
            gc_fraction_applied=gc_frac,
        )

    async def stats(self) -> VelumStats:
        async with self._lock:
            if not self._edges:
                return VelumStats(
                    edge_count=0,
                    episode_count=len(self._episode_ids),
                    avg_weight=0.0,
                    max_weight=0.0,
                )
            weights = [e.weight for e in self._edges.values()]
            return VelumStats(
                edge_count=len(self._edges),
                episode_count=len(self._episode_ids),
                avg_weight=sum(weights) / len(weights),
                max_weight=max(weights),
            )

    async def edge_count(self) -> int:
        async with self._lock:
            return len(self._edges)

    async def strengthen_cluster(
        self,
        entities: Iterable[str],
        *,
        factor: float = 1.3,
    ) -> int:
        """Усилить synapse между всеми парами кластера (RFC0066 LTP hint)."""
        normalized = self._normalize_entities(entities)
        if len(normalized) < 2:
            return 0
        count = 0
        async with self._lock:
            for a, b in combinations(sorted(normalized), 2):
                key = _edge_key(a, b)
                edge = self._edges.get(key)
                if edge:
                    edge.weight = min(
                        self._params.max_weight,
                        edge.weight * factor,
                    )
                    count += 1
        return count

    async def get_edge(self, a: str, b: str) -> VelumEdge | None:
        na, nb = self._normalize_pair(a, b)
        if na is None or nb is None:
            return None
        key = _edge_key(na, nb)
        async with self._lock:
            return self._edges.get(key)

    async def apply_fsrs_decay_all(
        self,
        *,
        now: datetime | None = None,
        prune_below: float | None = None,
        run_gc: bool = True,
    ) -> VelumDecayBatchResult:
        """
        Пакетный FSRS decay всех synapse по времени с last_touch (RFC0017 / T5).

        Не сдвигает last_touch — decay отражает «забывание» с момента
        последнего co-occurrence / retrieval.
        """
        if now is None:
            now = datetime.now(UTC)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        if prune_below is None:
            prune_below = self._params.min_weight_floor

        async with self._lock:
            edges = list(self._edges.values())
            if not edges:
                return VelumDecayBatchResult(
                    edges_processed=0,
                    edges_decayed=0,
                    edges_unchanged=0,
                    edges_pruned=0,
                    gc_removed=0,
                    avg_weight_before=0.0,
                    avg_weight_after=0.0,
                )

            weights_before = [e.weight for e in edges]
            decayed = 0
            unchanged = 0

            from core.decay_orchestrator import (
                DecayTarget,
                is_decay_orchestrator_enabled,
            )
            from core.salience_fsrs import should_protect_from_decay

            orchestrator = None
            if is_decay_orchestrator_enabled():
                from core.decay_orchestrator import get_decay_orchestrator

                orchestrator = get_decay_orchestrator()

            for edge in edges:
                touch = edge.last_touch
                if touch.tzinfo is None:
                    touch = touch.replace(tzinfo=UTC)
                t_days = max(0.0, (now - touch).total_seconds() / 86_400.0)

                old_w = edge.weight

                if orchestrator is not None:
                    outcome = orchestrator.compute(
                        DecayTarget(
                            weight=old_w,
                            t_days=t_days,
                            stability_days=edge.stability_days,
                            salience_weight=edge.salience_weight,
                            min_weight=self._params.min_weight_floor,
                            max_weight=self._params.max_weight,
                        ),
                        prune_below=prune_below,
                    )
                    if outcome.skipped:
                        unchanged += 1
                        continue
                    new_w = outcome.new_weight
                else:
                    if should_protect_from_decay(edge.salience_weight):
                        unchanged += 1
                        continue
                    if t_days <= 0.0:
                        unchanged += 1
                        continue
                    new_w = decay_edge_weight(
                        old_w,
                        t_days=t_days,
                        stability=edge.stability_days,
                        params=self._params.fsrs,
                    )
                    new_w = max(
                        self._params.min_weight_floor,
                        min(self._params.max_weight, new_w),
                    )

                if abs(new_w - old_w) > 1e-12:
                    edge.weight = new_w
                    decayed += 1
                else:
                    unchanged += 1

            pruned = self._prune_edges_below_locked(prune_below)

            gc_removed = 0
            if run_gc:
                gc_removed, _ = await self._gc_locked(force=False)

            weights_after = [e.weight for e in self._edges.values()]
            avg_before = sum(weights_before) / len(weights_before)
            avg_after = (
                sum(weights_after) / len(weights_after) if weights_after else 0.0
            )

        return VelumDecayBatchResult(
            edges_processed=len(edges),
            edges_decayed=decayed,
            edges_unchanged=unchanged,
            edges_pruned=pruned,
            gc_removed=gc_removed,
            avg_weight_before=avg_before,
            avg_weight_after=avg_after,
        )

    async def export_snapshots(self) -> list[dict[str, Any]]:
        """Сериализация рёбер для Neo4j / batch job."""
        async with self._lock:
            return self._export_snapshots_locked()

    def _export_snapshots_locked(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for edge in self._edges.values():
            touch = edge.last_touch
            if touch.tzinfo is None:
                touch = touch.replace(tzinfo=UTC)
            rows.append(
                {
                    "edge_key": "|".join(sorted((edge.entity_a, edge.entity_b))),
                    "entity_a": edge.entity_a,
                    "entity_b": edge.entity_b,
                    "weight": edge.weight,
                    "stability_days": edge.stability_days,
                    "co_occur_count": edge.co_occur_count,
                    "last_touch": touch.isoformat(),
                    "last_episode_id": edge.last_episode_id,
                    "retrieval_hits": edge.retrieval_hits,
                    "salience_weight": edge.salience_weight,
                }
            )
        return rows

    async def import_snapshots(
        self,
        rows: Iterable[dict[str, Any]],
        *,
        merge: bool = True,
    ) -> int:
        """
        Загрузить рёбра из Neo4j/JSON в in-memory Velum.

        merge=True: более высокий weight побеждает при конфликте.
        """
        imported = 0
        async with self._lock:
            for row in rows:
                ea = _normalize_entity(row.get("entity_a"))
                eb = _normalize_entity(row.get("entity_b"))
                if ea is None or eb is None:
                    continue
                ea, eb = _ordered_pair(ea, eb)
                key = _edge_key(ea, eb)
                weight = float(row.get("weight") or 0.0)
                stability = float(
                    row.get("stability_days")
                    or self._params.default_edge_stability_days
                )
                touch_raw = row.get("last_touch")
                if isinstance(touch_raw, datetime):
                    touch = touch_raw
                elif isinstance(touch_raw, str) and touch_raw:
                    touch = datetime.fromisoformat(
                        touch_raw.replace("Z", "+00:00")
                    )
                else:
                    touch = datetime.now(UTC)
                if touch.tzinfo is None:
                    touch = touch.replace(tzinfo=UTC)

                existing = self._edges.get(key)
                if existing and merge and existing.weight >= weight:
                    continue

                self._edges[key] = VelumEdge(
                    entity_a=ea,
                    entity_b=eb,
                    weight=min(self._params.max_weight, max(0.0, weight)),
                    co_occur_count=int(row.get("co_occur_count") or 0),
                    episode_window=deque(maxlen=self._params.window_episodes),
                    last_episode_id=row.get("last_episode_id"),
                    stability_days=stability,
                    last_touch=touch,
                    retrieval_hits=int(row.get("retrieval_hits") or 0),
                    salience_weight=float(row.get("salience_weight") or 1.0),
                )
                imported += 1

            self._degree_cache.clear()
            for edge in self._edges.values():
                self._increment_degree(edge.entity_a)
                self._increment_degree(edge.entity_b)

        return imported

    def _prune_edges_below_locked(self, threshold: float) -> int:
        """Удалить рёбра ниже порога (только под lock)."""
        to_remove = [
            k for k, e in self._edges.items() if e.weight < threshold
        ]
        for key in to_remove:
            edge = self._edges.pop(key, None)
            if edge:
                self._decrement_degree(edge.entity_a)
                self._decrement_degree(edge.entity_b)
        return len(to_remove)

    # ─── Внутренние методы (под lock) ─────────────────────────────────────────

    def _normalize_entities(self, entities: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for raw in entities:
            ent = _normalize_entity(raw)
            if ent is None or ent in seen:
                continue
            seen.add(ent)
            result.append(ent)
        return result

    def _normalize_pair(
        self, a: str, b: str
    ) -> tuple[str | None, str | None]:
        na = _normalize_entity(a)
        nb = _normalize_entity(b)
        if na is None or nb is None or na == nb:
            return None, None
        return _ordered_pair(na, nb)

    async def _observe_pair(
        self,
        a: str,
        b: str,
        episode_id: str,
        now: datetime,
        *,
        salience_weight: float = 1.0,
    ) -> VelumEdge:
        """Вызывается только под self._lock."""
        key = _edge_key(a, b)
        edge = self._edges.get(key)
        if edge is None:
            ea, eb = _ordered_pair(a, b)
            edge = VelumEdge(
                entity_a=ea,
                entity_b=eb,
                weight=0.0,
                episode_window=deque(maxlen=self._params.window_episodes),
                stability_days=self._params.default_edge_stability_days,
                last_touch=now,
            )
            self._edges[key] = edge
            self._increment_degree(a)
            self._increment_degree(b)

        edge.touch(episode_id, now, self._params, salience_weight=salience_weight)
        self._strengthen_edge_locked(a, b, salience_weight=salience_weight)
        return edge

    def _strengthen_edge_locked(
        self, a: str, b: str, *, salience_weight: float = 1.0
    ) -> None:
        """Усиление ребра + LateralInhibition (I77 — только под lock)."""
        key = _edge_key(a, b)
        edge = self._edges.get(key)
        if edge is None:
            return

        # ACT-R fan-effect: чем больше связей у узла, тем слабее усиление (O(1) cache).
        deg_a = max(1, self._degree_cache.get(a, 1))
        deg_b = max(1, self._degree_cache.get(b, 1))
        fan = (1.0 / math.log(deg_a + 1) + 1.0 / math.log(deg_b + 1)) / 2.0
        fan_effect = fan

        salience = max(1.0, salience_weight) if salience_weight else 1.0
        delta = self._params.co_occur_weight_delta * salience
        edge.weight = min(
            self._params.max_weight,
            edge.weight * self._params.strengthen_factor * fan_effect + delta,
        )

        self._lateral_inhibition_locked(a, key)
        self._lateral_inhibition_locked(b, key)

    def _lateral_inhibition_locked(
        self,
        hub: str,
        strengthened_key: frozenset[str],
    ) -> None:
        """Ослабить слабые соседние рёбра hub (SYNAPSE-style, RFC0016)."""
        prot = self._params.lateral_protection_threshold
        inhib = self._params.lateral_inhibition_factor
        for other_key, other_edge in self._edges.items():
            if hub not in other_key or other_key == strengthened_key:
                continue
            if other_edge.weight < prot:
                other_edge.weight = max(
                    self._params.min_weight_floor,
                    other_edge.weight * inhib,
                )

    def _increment_degree(self, entity: str) -> None:
        self._degree_cache[entity] = self._degree_cache.get(entity, 0) + 1

    def _should_emit_co_occur_signal(self, edge: VelumEdge) -> bool:
        p = self._params
        return (
            edge.weight >= p.signal_weight_threshold
            and edge.window_distinct_episodes() >= p.co_occur_threshold
        )

    async def _maybe_gc_locked(self) -> None:
        if len(self._edges) > self._params.max_edges:
            await self._gc_locked(force=True)

    async def _gc_locked(self, *, force: bool) -> tuple[int, float]:
        """
        Graduated GC: удалить долю слабейших рёбер.

        Защищённые: retrieval за protect_window или weight ≥ lateral_protection.
        """
        n_edges = len(self._edges)
        if not force and n_edges <= self._params.max_edges:
            return 0, 0.0

        n_episodes = len(self._episode_ids)
        frac = self._gc_fraction_for_load(n_episodes)
        if frac <= 0.0:
            return 0, 0.0

        protected_keys = self._protected_edge_keys_locked()
        candidates = [
            (k, e)
            for k, e in self._edges.items()
            if k not in protected_keys
        ]
        if not candidates:
            return 0, frac

        remove_count = max(1, int(math.ceil(len(candidates) * frac)))
        candidates.sort(key=lambda kv: self._health_score(kv[1]))
        to_remove = {k for k, _ in candidates[:remove_count]}

        for key in to_remove:
            edge = self._edges.pop(key, None)
            if edge:
                self._decrement_degree(edge.entity_a)
                self._decrement_degree(edge.entity_b)

        self._degree_cache.clear()
        for edge in self._edges.values():
            self._increment_degree(edge.entity_a)
            self._increment_degree(edge.entity_b)

        return len(to_remove), frac

    def _gc_fraction_for_load(self, episode_count: int) -> float:
        p = self._params
        if episode_count > p.ram_guard_critical:
            return p.gc_critical
        if episode_count > p.ram_guard_medium:
            return p.gc_medium
        if episode_count > p.ram_guard_soft or len(self._edges) > p.max_edges:
            return p.gc_soft
        if len(self._edges) > p.max_edges:
            return p.gc_fraction
        return 0.0

    def _protected_edge_keys_locked(self) -> set[frozenset[str]]:
        protected: set[frozenset[str]] = set()
        for key, edge in self._edges.items():
            if edge.last_retrieval_episode is not None:
                protected.add(key)
            if edge.weight >= self._params.lateral_protection_threshold:
                protected.add(key)
        return protected

    def _health_score(self, edge: VelumEdge) -> float:
        """Чем выше — тем «полезнее» ребро (меньше шанс удаления)."""
        retrieval_bonus = min(1.0, edge.retrieval_hits * 0.1) * 0.4
        signal_bonus = min(1.0, edge.co_occur_count / 10.0) * 0.3
        recency_bonus = 0.1 if edge.last_episode_id else 0.0
        return edge.weight + retrieval_bonus + signal_bonus + recency_bonus

    def _decrement_degree(self, entity: str) -> None:
        if entity in self._degree_cache:
            self._degree_cache[entity] = max(0, self._degree_cache[entity] - 1)
            if self._degree_cache[entity] == 0:
                del self._degree_cache[entity]


__all__ = [
    "Velum",
    "VelumEdge",
    "VelumParams",
    "VelumSignal",
    "VelumSignalKind",
    "ObserveResult",
    "SessionEndResult",
    "VelumStats",
    "VelumDecayBatchResult",
]
