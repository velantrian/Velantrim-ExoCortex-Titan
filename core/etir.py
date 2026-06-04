"""
L3.5a Etir — Spreading Activation (RFC0011 MVP).

Работает поверх GraphStoreBackend (sqlite/memory), без Neo4j.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from core.feature_config import get_config
from core.graph_store import ActivatedNode
from core.storage_facade import get_graph_store

logger = logging.getLogger(__name__)


def is_etir_enabled() -> bool:
    return get_config().app.enable_etir


@dataclass
class EtirActivationResult:
    seeds: list[str] = field(default_factory=list)
    activated: list[ActivatedNode] = field(default_factory=list)
    top_k: int = 0

    def to_dict(self) -> dict:
        return {
            "seeds": self.seeds,
            "activated": [
                {"node_id": a.node_id, "score": round(a.score, 4), "hops": a.hops}
                for a in self.activated
            ],
            "top_k": self.top_k,
        }


class EtirEngine:
    """Spreading activation по локальному графу."""

    def __init__(
        self,
        *,
        max_hops: int = 2,
        top_k: int = 10,
        decay: float = 0.65,
    ) -> None:
        get_config().app
        self.max_hops = max_hops
        self.top_k = top_k
        self.decay = decay
        self._store = get_graph_store()

    def observe_cooccurrence(
        self,
        entities: list[str],
        *,
        weight: float = 1.0,
    ) -> int:
        """Добавить рёбра co-occurrence между сущностями эпизода."""
        names = [e.strip() for e in entities if e and str(e).strip()]
        edges = 0
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                self._store.upsert_edge(a, b, relation="CO_OCCUR", weight=weight)
                edges += 1
        return edges

    def activate(self, seeds: list[str]) -> EtirActivationResult:
        clean = [s.strip() for s in seeds if s and str(s).strip()]
        if not clean:
            return EtirActivationResult(seeds=[], activated=[], top_k=0)

        activated = self._store.spreading_activation(
            clean,
            max_hops=self.max_hops,
            top_k=self.top_k,
            decay=self.decay,
        )
        return EtirActivationResult(
            seeds=clean,
            activated=activated,
            top_k=len(activated),
        )

    def format_context_section(self, result: EtirActivationResult) -> str:
        if not result.activated:
            return ""
        lines = ["## Etir (L3.5a spreading activation)"]
        for a in result.activated[: self.top_k]:
            lines.append(f"- {a.node_id} (score={a.score:.3f}, hops={a.hops})")
        return "\n".join(lines)


_etir: EtirEngine | None = None


def get_etir() -> EtirEngine:
    global _etir
    if _etir is None:
        _etir = EtirEngine()
    return _etir


def reset_etir() -> None:
    global _etir
    _etir = None


__all__ = [
    "EtirActivationResult",
    "EtirEngine",
    "get_etir",
    "is_etir_enabled",
    "reset_etir",
]
