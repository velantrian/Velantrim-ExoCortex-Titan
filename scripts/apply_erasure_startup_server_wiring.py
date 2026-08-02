#!/usr/bin/env python3
"""Apply the exact erasure startup recovery wiring patch to server.py.

This script is branch-only patch machinery. The workflow removes it before the
final implementation commit, so it never appears in the pull-request diff.
"""

from pathlib import Path


path = Path("server.py")
source = path.read_text(encoding="utf-8")

startup_marker = """        raise

    # Перестроить NGram индекс при старте — только Validated факты
"""
startup_replacement = """        raise

    # GDPR erasure startup recovery — bounded, awaited, once per process.
    # Invalid explicit budgets fail startup. Measured backlog/observer failure
    # keeps the process inspectable but makes /health/recovery fail readiness.
    from core.erasure_startup_runtime import (
        execute_and_record_startup_recovery,
        get_startup_recovery_health,
        load_startup_recovery_budget,
    )

    _recovery_budget = load_startup_recovery_budget()
    await asyncio.to_thread(
        execute_and_record_startup_recovery,
        _recovery_budget,
    )
    _recovery_health = get_startup_recovery_health()
    _recovery_status = str(_recovery_health.get("status") or "observer_failed")
    _recovery_receipt = _recovery_health.get("receipt") or {}
    _recovery_unresolved = int(_recovery_receipt.get("unresolved_count") or 0)
    _recovery_reason = str(_recovery_health.get("reason_code") or "none")
    if _recovery_status == "clean":
        logger.info(
            "   GDPR startup recovery: ✅ status=%s unresolved=%d",
            _recovery_status,
            _recovery_unresolved,
        )
    elif _recovery_status == "degraded":
        logger.warning(
            "   GDPR startup recovery: ⚠️ status=%s unresolved=%d reason=%s",
            _recovery_status,
            _recovery_unresolved,
            _recovery_reason,
        )
    else:
        logger.error(
            "   GDPR startup recovery: ❌ status=%s unresolved=%d reason=%s",
            _recovery_status,
            _recovery_unresolved,
            _recovery_reason,
        )

    # Перестроить NGram индекс при старте — только Validated факты
"""

route_marker = """@app.get("/setup/llm", tags=["System"])
async def setup_llm():
"""
route_replacement = """@app.get("/health/recovery", tags=["System"])
async def erasure_startup_recovery_health():
    \"\"\"Content-free GDPR startup recovery readiness evidence.\"\"\"
    from core.erasure_startup_runtime import (
        get_startup_recovery_health,
        startup_recovery_http_status,
    )

    payload = get_startup_recovery_health()
    return JSONResponse(
        status_code=startup_recovery_http_status(),
        content=payload,
    )


@app.get("/setup/llm", tags=["System"])
async def setup_llm():
"""

for marker, label in (
    (startup_marker, "startup marker"),
    (route_marker, "route marker"),
):
    count = source.count(marker)
    if count != 1:
        raise SystemExit(f"{label} expected exactly once, found {count}")

if "/health/recovery" in source:
    raise SystemExit("server.py already contains /health/recovery")
if "execute_and_record_startup_recovery" in source:
    raise SystemExit("server.py already contains startup recovery wiring")

source = source.replace(startup_marker, startup_replacement, 1)
source = source.replace(route_marker, route_replacement, 1)
path.write_text(source, encoding="utf-8")
