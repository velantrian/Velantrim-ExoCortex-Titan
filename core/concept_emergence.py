"""
Concept Emergence — ProtoConcept (RFC0066).

Sprint 3 / T1. Органическое рождение безымянных концептов из co-occurrence
сущностей в эпизодах (Hebbian-style, 0 LLM-токенов на фазе рождения).

Инварианты:
  I50:   не создаёт :Fact и не пишет в L3 напрямую.
  I50-c: emergence_matrix — только счётчики, не содержимое.
  I66:   ProtoConcept только in-memory.
  I70:   активных proto ≤ max_active_protos (eviction по min confidence).
  I-K3:  GC не удаляет наблюдения моложе matrix_ttl_days без proto.

Фазы (MVP):
  1. observe(entities, session_id) — матрица co-occurrence комбинаций 3–7 сущностей.
  2. При порогах → ProtoConcept (name=None, confidence>0).
  3. lazy_name() — общие токены имён сущностей (0 токенов LLM).
  4. promote_proto_to_l3() — L3 через TruthGate (core/concept_promote.py).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from itertools import combinations
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmergenceParams:
    """Пороги RFC0066 (конфигурируемые)."""

    min_entities: int = 3
    max_entities: int = 7
    co_occur_min: int = 5
    cross_session_min: int = 3
    max_active_protos: int = 500
    proto_ttl_days: int = 30
    matrix_ttl_days: int = 30
    hebbian_decay_factor: float = 0.98
    velum_strengthen_factor: float = 1.3


_DEFAULT_PARAMS = EmergenceParams()


def _normalize_entities(entities: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in entities:
        if not isinstance(raw, str):
            continue
        name = raw.strip()
        if not name or name.lower() == "unknown" or name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


@dataclass
class ProtoConcept:
    """Безымянный концепт (in-memory, I66)."""

    proto_id: str
    entities: frozenset[str]
    co_occur_count: int = 0
    cross_sessions: int = 0
    salience_boost: float = 0.0
    first_seen: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    last_active: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    last_decay: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    name: str | None = None
    confidence: float = 0.0
    expired: bool = False
    promoted: bool = False
    l3_entity_uuid: str | None = None

    def update_confidence(self) -> None:
        base = (
            min(1.0, self.co_occur_count / 20.0) * 0.6
            + min(1.0, self.cross_sessions / 10.0) * 0.4
        )
        self.confidence = min(1.0, base * (1.0 + self.salience_boost))

    def to_dict(self) -> dict[str, object]:
        return {
            "proto_id": self.proto_id,
            "entities": sorted(self.entities),
            "co_occur_count": self.co_occur_count,
            "cross_sessions": self.cross_sessions,
            "confidence": round(self.confidence, 4),
            "name": self.name,
            "expired": self.expired,
        }


@dataclass
class EmergenceObserveResult:
    session_id: str
    entities_seen: int
    combos_updated: int
    protos_born: list[str] = field(default_factory=list)
    protos_updated: list[str] = field(default_factory=list)


class ConceptEmergenceDetector:
    """
    Детектор органического рождения ProtoConcept (RFC0066).
    """

    def __init__(self, params: EmergenceParams = _DEFAULT_PARAMS) -> None:
        self._params = params
        self._matrix: dict[frozenset[str], int] = {}
        self._sessions: dict[frozenset[str], set[str]] = {}
        self._matrix_last_seen: dict[frozenset[str], datetime] = {}
        self._protos: dict[str, ProtoConcept] = {}
        self._entity_to_protos: dict[str, list[str]] = {}
        self._lock = asyncio.Lock()

    @property
    def params(self) -> EmergenceParams:
        return self._params

    async def observe(
        self,
        entities: Iterable[str],
        session_id: str,
        *,
        salience_weight: float = 1.0,
        now: datetime | None = None,
    ) -> EmergenceObserveResult:
        """
        Фаза 1–2: обновить матрицу и при порогах создать ProtoConcept.
        """
        if now is None:
            now = datetime.now(UTC)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        normalized = _normalize_entities(entities)[: self._params.max_entities]
        p = self._params

        if len(normalized) < p.min_entities:
            return EmergenceObserveResult(
                session_id=session_id,
                entities_seen=len(normalized),
                combos_updated=0,
            )

        born: list[str] = []
        updated: list[str] = []
        combos = 0

        async with self._lock:
            for size in range(p.min_entities, len(normalized) + 1):
                for combo in combinations(sorted(normalized), size):
                    key = frozenset(combo)
                    self._matrix[key] = self._matrix.get(key, 0) + 1
                    self._matrix_last_seen[key] = now
                    self._sessions.setdefault(key, set()).add(session_id)
                    combos += 1

                    for proto in self._protos.values():
                        if proto.entities == key and not proto.expired:
                            proto.co_occur_count = self._matrix[key]
                            proto.cross_sessions = len(self._sessions[key])
                            proto.last_active = now
                            proto.salience_boost = max(
                                proto.salience_boost, max(0.0, salience_weight - 1.0)
                            )
                            proto.update_confidence()
                            updated.append(proto.proto_id)
                            break
                    else:
                        if (
                            self._matrix[key] >= p.co_occur_min
                            and len(self._sessions[key]) >= p.cross_session_min
                        ):
                            new_id = self._maybe_create_proto_locked(key, now)
                            if new_id:
                                born.append(new_id)

        if born:
            logger.info(
                "concept_emergence: born %d protos session=%s",
                len(born),
                session_id,
            )
            try:
                from core.velum_bridge import get_velum

                await get_velum().strengthen_cluster(
                    normalized, factor=p.velum_strengthen_factor
                )
            except Exception as exc:  # noqa: BLE001
                logger.debug("velum strengthen cluster skipped: %s", exc)

        return EmergenceObserveResult(
            session_id=session_id,
            entities_seen=len(normalized),
            combos_updated=combos,
            protos_born=born,
            protos_updated=updated,
        )

    def _maybe_create_proto_locked(
        self, key: frozenset[str], now: datetime
    ) -> str | None:
        """Только под self._lock."""
        for proto in self._protos.values():
            if proto.entities == key and not proto.expired:
                proto.co_occur_count = self._matrix[key]
                proto.cross_sessions = len(self._sessions[key])
                proto.last_active = now
                proto.update_confidence()
                return None

        active = [p for p in self._protos.values() if not p.expired]
        if len(active) >= self._params.max_active_protos:
            victim = min(active, key=lambda p: p.confidence)
            del self._protos[victim.proto_id]
            for entity in victim.entities:
                if entity in self._entity_to_protos:
                    self._entity_to_protos[entity] = [
                        pid
                        for pid in self._entity_to_protos[entity]
                        if pid != victim.proto_id
                    ]
            logger.debug(
                "ProtoConcept evicted (cap=%d): %s",
                self._params.max_active_protos,
                victim.proto_id,
            )

        proto_id = f"proto:{uuid4().hex[:8]}"
        proto = ProtoConcept(
            proto_id=proto_id,
            entities=key,
            co_occur_count=self._matrix[key],
            cross_sessions=len(self._sessions[key]),
        )
        proto.update_confidence()
        self._protos[proto_id] = proto
        for entity in key:
            self._entity_to_protos.setdefault(entity, []).append(proto_id)
        return proto_id

    def get_protos_for_entity(self, entity: str) -> list[ProtoConcept]:
        name = (entity or "").strip()
        if not name:
            return []
        return [
            self._protos[pid]
            for pid in self._entity_to_protos.get(name, [])
            if pid in self._protos and not self._protos[pid].expired
        ]

    def list_active_protos(self) -> list[ProtoConcept]:
        return [p for p in self._protos.values() if not p.expired]

    def get_proto(self, proto_id: str) -> ProtoConcept | None:
        proto = self._protos.get(proto_id)
        if proto and not proto.expired:
            return proto
        return None

    def lazy_name(self, proto_id: str) -> str | None:
        """
        Фаза 3 (MVP): имя из пересечения токенов сущностей — 0 LLM.
        """
        proto = self.get_proto(proto_id)
        if proto is None:
            return None
        if proto.name:
            return proto.name
        name = _common_token_name(proto.entities)
        proto.name = name
        return name

    async def daily_maintenance(self, *, now: datetime | None = None) -> dict[str, int]:
        """Hebbian decay + GC (для cron / scripts)."""
        if now is None:
            now = datetime.now(UTC)
        async with self._lock:
            decayed = 0
            for proto in self._protos.values():
                if proto.expired:
                    continue
                days = (now - proto.last_decay).days
                if days > 0:
                    proto.confidence *= self._params.hebbian_decay_factor ** days
                    proto.last_decay = now
                    decayed += 1
            gc_matrix, gc_expired = self._gc_impl_locked(now)
        return {
            "decayed_protos": decayed,
            "matrix_keys_removed": gc_matrix,
            "protos_expired": gc_expired,
        }

    async def gc_expired(self, *, now: datetime | None = None) -> dict[str, int]:
        if now is None:
            now = datetime.now(UTC)
        async with self._lock:
            gc_matrix, gc_expired = self._gc_impl_locked(now)
        return {"matrix_keys_removed": gc_matrix, "protos_expired": gc_expired}

    def _gc_impl_locked(self, now: datetime) -> tuple[int, int]:
        """Только под lock."""
        p = self._params
        matrix_removed = 0
        cutoff_matrix = now - timedelta(days=p.matrix_ttl_days)
        cutoff_proto = now - timedelta(days=p.proto_ttl_days)

        keys_to_drop: list[frozenset[str]] = []
        for key, last_seen in list(self._matrix_last_seen.items()):
            has_live_proto = any(
                pr.entities == key and not pr.expired for pr in self._protos.values()
            )
            if has_live_proto:
                continue
            if last_seen < cutoff_matrix:
                keys_to_drop.append(key)

        for key in keys_to_drop:
            self._matrix.pop(key, None)
            self._sessions.pop(key, None)
            self._matrix_last_seen.pop(key, None)
            matrix_removed += 1

        protos_expired = 0
        for proto in self._protos.values():
            if proto.expired:
                continue
            if proto.last_active < cutoff_proto:
                proto.expired = True
                protos_expired += 1

        return matrix_removed, protos_expired

    def stats(self) -> dict[str, int]:
        active = len(self.list_active_protos())
        return {
            "active_protos": active,
            "total_protos": len(self._protos),
            "matrix_keys": len(self._matrix),
        }


def _common_token_name(entities: frozenset[str]) -> str:
    entity_words = [
        e.lower().replace("_", " ").split() for e in sorted(entities) if e
    ]
    if not entity_words:
        return "unnamed_concept"
    common = set(entity_words[0])
    for words in entity_words[1:]:
        common &= set(words)
    if common:
        return "_".join(sorted(common)[:3])
    first = [w[0] for w in entity_words[:3] if w]
    return "_".join(first) if first else "unnamed_concept"


# ─── Singleton ────────────────────────────────────────────────────────────────

_detector_singleton: ConceptEmergenceDetector | None = None


def get_concept_detector() -> ConceptEmergenceDetector:
    global _detector_singleton
    if _detector_singleton is None:
        from core.feature_config import get_config

        cfg = get_config().app
        params = EmergenceParams(
            co_occur_min=getattr(cfg, "emergence_co_occur_min", 5),
            cross_session_min=getattr(cfg, "emergence_cross_session_min", 3),
            max_active_protos=getattr(cfg, "emergence_max_active_protos", 500),
            proto_ttl_days=getattr(cfg, "emergence_proto_ttl_days", 30),
        )
        _detector_singleton = ConceptEmergenceDetector(params)
    return _detector_singleton


def reset_concept_detector() -> None:
    global _detector_singleton
    _detector_singleton = None


def is_concept_emergence_enabled() -> bool:
    from core.feature_config import get_config

    return bool(get_config().app.enable_concept_emergence)


async def observe_concept_emergence(
    entity_names: list[str],
    session_id: str,
    *,
    salience_weight: float = 1.0,
) -> EmergenceObserveResult:
    """Обёртка для ingest: observe + логирование рождения."""
    result = await get_concept_detector().observe(
        entity_names, session_id, salience_weight=salience_weight
    )
    if result.protos_born:
        logger.info(
            "concept_emergence: session=%s born=%s",
            session_id,
            result.protos_born,
        )
        try:
            from core.event_bridge import on_concept_born
            from core.fusion_bridge import notify_proto_candidate

            await on_concept_born(result.protos_born, session_id)
            detector = get_concept_detector()
            for pid in result.protos_born:
                proto = detector.get_proto(pid)
                if proto:
                    await notify_proto_candidate(
                        pid,
                        list(proto.entities),
                        proto.confidence,
                    )
        except Exception as exc:  # noqa: BLE001
            logger.debug("proto notify skipped: %s", exc)
    return result


def format_proto_context_section(
    protos: list[ProtoConcept],
) -> str:
    """Секция контекста для F1.5 / build_context."""
    if not protos:
        return ""
    lines = ["## Возникающие концепты (ProtoConcept, RFC0066):"]
    for proto in protos[:5]:
        label = proto.name or proto.proto_id
        ents = ", ".join(sorted(proto.entities)[:6])
        promoted = " ✅L3" if getattr(proto, "promoted", False) else ""
        lines.append(
            f"- {label} (conf={proto.confidence:.2f}){promoted}: {ents}"
        )
    return "\n".join(lines)


__all__ = [
    "ConceptEmergenceDetector",
    "EmergenceParams",
    "EmergenceObserveResult",
    "ProtoConcept",
    "get_concept_detector",
    "is_concept_emergence_enabled",
    "reset_concept_detector",
    "observe_concept_emergence",
    "format_proto_context_section",
]
