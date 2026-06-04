"""
L3.5b ImmutableCore — снепшоты + связка с Ring Zero (I6).

Ring Zero на Entity (Neo4j) — graph_ring_zero.py.
Снепшоты неизменяемых наборов узлов — локальный GraphStore.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from core.feature_config import get_config
from core.storage_facade import get_graph_store

logger = logging.getLogger(__name__)


def is_immutable_core_enabled() -> bool:
    return get_config().app.enable_immutable_core


@dataclass
class ImmutableSnapshot:
    snapshot_id: str
    reason: str
    node_ids: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    ring_zero_linked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "reason": self.reason,
            "node_ids": self.node_ids,
            "created_at": self.created_at,
            "ring_zero_linked": self.ring_zero_linked,
        }


class ImmutableCore:
    """Снепшоты «вечной» основы памяти (локальный store)."""

    def __init__(self) -> None:
        self._store = get_graph_store()

    def create_snapshot(
        self,
        node_ids: list[str],
        *,
        reason: str = "immutable_core",
        snapshot_id: str | None = None,
    ) -> ImmutableSnapshot:
        sid = snapshot_id or f"imm_{uuid.uuid4().hex[:12]}"
        clean = [n for n in node_ids if n]
        for nid in clean:
            self._store.upsert_node(
                nid,
                label="Immutable",
                immutable=True,
                snapshot_id=sid,
            )
        self._store.create_snapshot(sid, reason=reason, node_ids=clean)
        return ImmutableSnapshot(
            snapshot_id=sid,
            reason=reason,
            node_ids=clean,
        )

    async def mark_ring_zero_on_graph(
        self,
        graphiti,
        entity_uuids: list[str],
        *,
        reason: str = "immutable_core",
    ) -> int:
        """Связать снепшот с Ring Zero на Neo4j Entity (если graphiti доступен)."""
        from core.graph_ring_zero import mark_ring_zero

        n = 0
        for uid in entity_uuids:
            if not uid:
                continue
            try:
                if await mark_ring_zero(graphiti, uid, reason=reason, by="immutable_core"):
                    n += 1
            except Exception as exc:  # noqa: BLE001
                logger.debug("immutable ring_zero %s: %s", uid, exc)
        return n

    def list_snapshots(self, *, limit: int = 20) -> list[dict[str, Any]]:
        return self._store.list_snapshots(limit=limit)


_core: ImmutableCore | None = None


def get_immutable_core() -> ImmutableCore:
    global _core
    if _core is None:
        _core = ImmutableCore()
    return _core


def reset_immutable_core() -> None:
    global _core
    _core = None


__all__ = [
    "ImmutableCore",
    "ImmutableSnapshot",
    "get_immutable_core",
    "is_immutable_core_enabled",
    "reset_immutable_core",
]
