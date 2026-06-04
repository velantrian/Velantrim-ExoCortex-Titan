"""
HTTP helpers для ExoCortex-слоёв (V8.6).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EtirActivateRequest(BaseModel):
    seeds: list[str] = Field(default_factory=list)
    query: str = ""


class ImmutableSnapshotRequest(BaseModel):
    node_ids: list[str]
    reason: str = "api_snapshot"


def full_layers_status() -> dict[str, Any]:
    from core.layers_status import build_layers_status
    from core.storage_facade import storage_info

    base = build_layers_status()
    base["storage"] = storage_info()
    return base


def etir_activate(req: EtirActivateRequest) -> dict[str, Any]:
    from core.etir import get_etir, is_etir_enabled

    if not is_etir_enabled():
        return {"enabled": False, "error": "ENABLE_ETIR=0"}
    seeds = list(req.seeds)
    if req.query.strip():
        seeds = [req.query.strip()[:80]] + seeds
    return {"enabled": True, **get_etir().activate(seeds).to_dict()}


def focus_get(user_id: str) -> dict[str, Any]:
    from core.focus_engine import get_focus_engine, is_focus_engine_enabled

    if not is_focus_engine_enabled():
        return {"enabled": False}
    return {
        "enabled": True,
        "user_id": user_id,
        "vector": get_focus_engine(user_id).vector.to_dict(),
    }


def audit_list(limit: int = 20) -> dict[str, Any]:
    from core.response_audit import get_audit_store, is_response_audit_enabled

    if not is_response_audit_enabled():
        return {"enabled": False, "items": []}
    return {"enabled": True, "items": get_audit_store().list_recent(limit=limit)}


def immutable_list(limit: int = 20) -> dict[str, Any]:
    from core.immutable_core import get_immutable_core, is_immutable_core_enabled

    if not is_immutable_core_enabled():
        return {"enabled": False, "items": []}
    return {"enabled": True, "items": get_immutable_core().list_snapshots(limit=limit)}


def horizons_index() -> dict[str, Any]:
    """Индекс карточек Horizons для UI и агентов."""
    from core.horizons_catalog import experimental_entries, research_entries

    return {
        "docs_root": "docs/horizons/",
        "index_md": "docs/horizons/README.md",
        "horizons_md": "docs/HORIZONS.md",
        "layers_map": "docs/LAYERS_AND_HORIZONS.ru.md",
        "research": research_entries(),
        "experimental": experimental_entries(),
    }


async def immutable_create(req: ImmutableSnapshotRequest) -> dict[str, Any]:
    from core.immutable_core import get_immutable_core, is_immutable_core_enabled

    if not is_immutable_core_enabled():
        return {"enabled": False, "error": "ENABLE_IMMUTABLE_CORE=0"}
    snap = get_immutable_core().create_snapshot(req.node_ids, reason=req.reason)
    return {"enabled": True, "snapshot": snap.to_dict()}


def titan_status() -> dict[str, Any]:
    """Статус переноса Titan: бюджет памяти, circuit breakers, ACT-R."""
    from core.titan_status import build_titan_status

    return build_titan_status()
