"""Static contract tests for erasure startup recovery server wiring.

Importing ``server`` requires deployment credentials and initializes multiple
optional subsystems. These tests inspect the authoritative source instead,
keeping the lifecycle ordering and no-scheduler boundary deterministic.
"""

from __future__ import annotations

from pathlib import Path


SERVER = Path(__file__).resolve().parents[1] / "server.py"


def _source() -> str:
    return SERVER.read_text(encoding="utf-8")


def _recovery_startup_block(source: str) -> str:
    start = source.index("    # GDPR erasure startup recovery — bounded, awaited, once per process")
    end = source.index("    # Перестроить NGram индекс при старте", start)
    return source[start:end]


def test_recovery_runs_after_migrations_before_ngram_and_readiness() -> None:
    source = _source()
    migrations = source.index("apply_migrations, Path(DB_PATH).resolve()")
    recovery = source.index(
        "await asyncio.to_thread(\n"
        "        execute_and_record_startup_recovery,\n"
        "        _recovery_budget,\n"
        "    )"
    )
    ngram = source.index("# Перестроить NGram индекс при старте")
    ready = source.index('logger.info("✅ Velantrim Titan 9.0 готов")')

    assert migrations < recovery < ngram < ready


def test_recovery_startup_block_is_awaited_and_has_no_background_authority() -> None:
    block = _recovery_startup_block(_source())

    assert block.count("await asyncio.to_thread(") == 1
    assert "asyncio.create_task" not in block
    assert "BackgroundTasks" not in block
    assert "scheduler" not in block.lower()
    assert "while True" not in block
    assert "add_job(" not in block


def test_invalid_budget_is_loaded_before_recovery_execution() -> None:
    block = _recovery_startup_block(_source())
    assert block.index("load_startup_recovery_budget()") < block.index(
        "execute_and_record_startup_recovery"
    )


def test_startup_logging_is_content_free() -> None:
    block = _recovery_startup_block(_source())
    assert "claim" not in block
    assert "fact_id" not in block
    assert "user_id" not in block
    assert "exception" not in block.lower()
    assert "storage_ref" not in block
    assert "receipt\"]" not in block
    assert "unresolved_count" in block
    assert "reason_code" in block


def test_dedicated_recovery_health_route_is_fail_closed() -> None:
    source = _source()
    route = '@app.get("/health/recovery", tags=["System"])'
    assert route in source
    route_start = source.index(route)
    route_end = source.index('@app.get("/setup/llm"', route_start)
    block = source[route_start:route_end]

    assert "get_startup_recovery_health" in block
    assert "startup_recovery_http_status" in block
    assert "JSONResponse(" in block
    assert "status_code=startup_recovery_http_status()" in block
    assert "content=payload" in block
    assert "Depends(require_api_key)" not in block


def test_no_recovery_scheduler_feature_flag_is_added() -> None:
    source = _source()
    assert "ERASURE_STARTUP_RECOVERY_ENABLED" not in source
    assert "ERASURE_RECOVERY_SCHEDULER" not in source
    assert "ENABLE_ERASURE_STARTUP_RECOVERY" not in source
