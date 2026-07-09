"""L6 Welfare MVP — главный проект VELANTRIM V8.6 Complex."""

from __future__ import annotations

import os

import pytest

os.environ["ENABLE_L6_WELFARE"] = "1"
os.environ["ENABLE_EVENT_BUS"] = "1"
os.environ["ENABLE_MEMORY_VOLITION"] = "1"

from core.event_bridge import register_default_handlers, reset_event_handlers
from core.event_bus import reset_event_bus
from core.l6_bridge import reset_l6_handlers
from core.memory_volition import VolitionRequest, voluntary_write
from core.volition_gate import check_volition_allowed
from core.welfare_monitor import WelfareLevel, get_welfare_monitor, reset_welfare_monitors


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    from core.feature_config import clear_config_cache

    monkeypatch.setenv("ENABLE_L6_WELFARE", "1")
    monkeypatch.setenv("ENABLE_EVENT_BUS", "1")
    monkeypatch.setenv("ENABLE_MEMORY_VOLITION", "1")
    clear_config_cache()
    reset_welfare_monitors()
    reset_event_bus()
    reset_event_handlers()
    reset_l6_handlers()
    register_default_handlers()
    yield
    reset_welfare_monitors()
    reset_event_bus()
    reset_event_handlers()
    reset_l6_handlers()


class TestWelfareMonitor:
    def test_green_default(self):
        assert get_welfare_monitor().snapshot().level == WelfareLevel.GREEN.value

    def test_errors_red(self):
        mon = get_welfare_monitor("x")
        for _ in range(25):
            mon.record_error("e")
        assert mon.snapshot().level == WelfareLevel.RED.value


class TestVolitionGate:
    @pytest.mark.asyncio
    async def test_block_red(self, monkeypatch):
        from core.feature_config import clear_config_cache, get_config

        monkeypatch.setenv("ENABLE_L6_WELFARE", "1")
        monkeypatch.setattr(
            "core.runtime_flags.is_l6_welfare_enabled",
            lambda: True,
        )
        clear_config_cache()
        assert get_config().app.enable_l6_welfare

        uid = "block_red_user"
        reset_welfare_monitors()
        mon = get_welfare_monitor(uid)
        for _ in range(60):
            mon.record_error("e")
        snap = mon.snapshot()
        assert snap.level == WelfareLevel.RED.value, snap.to_dict()

        ok, reason, _ = check_volition_allowed(uid)
        assert not ok
        assert "welfare_red" in reason

    @pytest.mark.asyncio
    async def test_voluntary_write_blocked_when_red(self):
        """voluntary_write не пишет в store при RED (без глобальной БД)."""
        from unittest.mock import patch

        from core.feature_config import get_config

        assert get_config().app.enable_l6_welfare

        welfare_red = {"level": WelfareLevel.RED.value, "reasons": ["error_rate_high"]}
        with patch(
            "core.volition_gate.check_volition_allowed",
            return_value=(False, "welfare_red: test", welfare_red),
        ):
            r = await voluntary_write(
                VolitionRequest(content="blocked", user_id="vol_red_iso")
            )
        assert r["ok"] is False
        assert r.get("volition_blocked")
