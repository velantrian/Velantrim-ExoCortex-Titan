"""Dual-Process: Slow-only операции нельзя звать с Fast Path."""

from __future__ import annotations

import pytest

from core.dual_process import (
    DualProcessError,
    current_path,
    fast_path,
    is_fast_path,
    require_slow_path,
    slow_only,
    slow_path,
)


def test_default_is_fast():
    assert is_fast_path() is True
    assert current_path().value == "fast"


def test_slow_path_context():
    with slow_path():
        assert current_path().value == "slow"
        require_slow_path("demo")
    assert is_fast_path() is True


def test_require_slow_raises_on_fast():
    with pytest.raises(DualProcessError):
        require_slow_path("EdgeSuggester.scan")


def test_slow_only_decorator():
    @slow_only("heavy_job")
    def heavy_job() -> str:
        return "ok"

    with pytest.raises(DualProcessError):
        heavy_job()

    with slow_path():
        assert heavy_job() == "ok"


def test_nested_fast_inside_slow():
    with slow_path():
        with fast_path():
            with pytest.raises(DualProcessError):
                require_slow_path("nested")
        require_slow_path("after_nested")
