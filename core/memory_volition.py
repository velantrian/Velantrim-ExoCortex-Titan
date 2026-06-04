"""
Memory Volition + L6 gate (Velantrim V8.6 Complex).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from core.feature_config import get_config


def is_memory_volition_enabled() -> bool:
    return get_config().app.enable_memory_volition

logger = logging.getLogger(__name__)


@dataclass
class VolitionRequest:
    content: str
    user_id: str = "default"
    confidence: float = 0.85
    reason: str = "agent_volition"
    fact_id: str | None = None
    source: str = "volition"


async def voluntary_write(req: VolitionRequest) -> dict[str, Any]:
    if not is_memory_volition_enabled():
        return {"ok": False, "reason": "disabled"}

    from core.runtime_flags import is_l6_welfare_enabled
    from core.volition_gate import check_volition_allowed

    allowed, block_reason, welfare = check_volition_allowed(req.user_id)
    if not allowed:
        return {
            "ok": False,
            "reason": block_reason,
            "welfare": welfare,
            "volition_blocked": True,
        }

    # Повторная проверка: RED не должен писать в store даже при гонке EventBus
    from core.welfare_monitor import WelfareLevel, get_welfare_monitor

    snap = get_welfare_monitor(req.user_id).snapshot()

    if is_l6_welfare_enabled() and snap.level == WelfareLevel.RED.value:
        return {
            "ok": False,
            "reason": "welfare_red: volition_blocked",
            "welfare": snap.to_dict(),
            "volition_blocked": True,
        }

    fid = req.fact_id or f"vol_{uuid.uuid4().hex[:12]}"
    result: dict[str, Any] = {
        "ok": True,
        "fact_id": fid,
        "queued_at": datetime.now(UTC).isoformat(),
    }
    if welfare:
        result["welfare"] = welfare

    from core.event_bridge import publish_event

    await publish_event(
        "MEMORY_VOLITION",
        {
            "fact_id": fid,
            "user_id": req.user_id,
            "confidence": req.confidence,
            "reason": req.reason,
            "content_len": len(req.content),
        },
    )

    if req.content.strip():
        try:
            import asyncio

            from core.memory import store_fact

            fact = {
                "fact_id": fid,
                "claim": req.content.strip(),
                "source": req.source or f"volition:{req.reason}",
                "confidence": req.confidence,
                "metadata": {"volition": True, "reason": req.reason},
            }
            await asyncio.to_thread(store_fact, fact)
            result["stored"] = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("volition store_fact: %s", exc)
            result["stored"] = False
            result["store_error"] = str(exc)
            try:
                from core.l6_bridge import record_runtime_error

                record_runtime_error(req.user_id, str(exc))
            except Exception:  # noqa: BLE001
                pass

    return result


__all__ = ["VolitionRequest", "is_memory_volition_enabled", "voluntary_write"]
