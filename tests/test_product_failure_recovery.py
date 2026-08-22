from __future__ import annotations

import importlib.util
import subprocess
import urllib.error
from pathlib import Path

import pytest


BOOTSTRAP_SCRIPT = Path(__file__).parents[1] / "scripts" / "bootstrap_titan.py"
spec = importlib.util.spec_from_file_location("bootstrap_titan_stage7", BOOTSTRAP_SCRIPT)
assert spec and spec.loader
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class _ExitedProcess:
    returncode = 23

    def poll(self):
        return self.returncode


class _RunningProcess:
    returncode = None

    def poll(self):
        return None


def test_startup_reports_early_server_exit() -> None:
    with pytest.raises(bootstrap.BootstrapError, match="exited during startup with code 23"):
        bootstrap.wait_until_ready(_ExitedProcess(), "http://127.0.0.1:8755", timeout_s=1)


def test_startup_timeout_reports_last_health_error(monkeypatch) -> None:
    def unavailable(*args, **kwargs):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(bootstrap.urllib.request, "urlopen", unavailable)
    monkeypatch.setattr(bootstrap.time, "sleep", lambda _seconds: None)

    with pytest.raises(bootstrap.BootstrapError) as exc:
        bootstrap.wait_until_ready(_RunningProcess(), "http://127.0.0.1:8755", timeout_s=0.01)

    message = str(exc.value)
    assert "did not become ready" in message
    assert "connection refused" in message


def test_dependency_install_failure_is_actionable(tmp_path: Path) -> None:
    class FailedRunner:
        def __call__(self, *args, **kwargs):
            raise subprocess.CalledProcessError(1, args[0])

    with pytest.raises(bootstrap.BootstrapError) as exc:
        bootstrap.install_server_dependencies(
            tmp_path,
            tmp_path / "python",
            runner=FailedRunner(),
        )

    message = str(exc.value)
    assert "could not be installed" in message
    assert "internet access" in message


def test_busy_port_has_recovery_instruction() -> None:
    message = (
        f"Port {bootstrap.DEFAULT_PORT} is already in use. "
        "Stop the existing process or pass --port <free-port>."
    )
    assert "Stop the existing process" in message
    assert "--port <free-port>" in message
