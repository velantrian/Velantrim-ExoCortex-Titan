from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "bootstrap_titan.py"
spec = importlib.util.spec_from_file_location("bootstrap_titan", SCRIPT)
assert spec and spec.loader
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


def make_project(tmp_path: Path) -> Path:
    for relative in bootstrap.REQUIRED_PROJECT_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text(
        "VELANTRIM_API_KEY=\nLLM_PROVIDER=none\nSLEEP_WORKER_ENABLED=true\n",
        encoding="utf-8",
    )
    return tmp_path


def env_map(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def test_python_version_guard_rejects_old_runtime():
    with pytest.raises(bootstrap.BootstrapError, match="Python 3.11"):
        bootstrap.require_supported_python((3, 10, 9))


def test_validate_project_lists_missing_files(tmp_path):
    with pytest.raises(bootstrap.BootstrapError) as exc:
        bootstrap.validate_project(tmp_path)
    message = str(exc.value)
    assert "pyproject.toml" in message
    assert "server.py" in message
    assert "static/console/index.html" in message


def test_first_env_is_safe_and_has_generated_key(tmp_path):
    root = make_project(tmp_path)
    env_path, created = bootstrap.ensure_env(root)
    assert created is True
    values = env_map(env_path)
    assert values["VELANTRIM_API_KEY"]
    assert values["VELANTRIM_API_KEY"] != "dev-console-key"
    assert values["VELANTRIM_ALLOW_OPEN"] == "false"
    assert values["VELANTRIM_NETWORK_MODE"] == "deny"
    assert values["VELANTRIM_REMOTE_DATA_MODE"] == "never"
    assert values["LLM_PROVIDER"] == "none"


def test_existing_env_is_preserved(tmp_path):
    root = make_project(tmp_path)
    env_path = root / ".env"
    env_path.write_text(
        "VELANTRIM_API_KEY=user-owned-key\n"
        "VELANTRIM_NETWORK_MODE=allow\n"
        "VELANTRIM_REMOTE_DATA_MODE=redacted\n"
        "LLM_PROVIDER=openai\n",
        encoding="utf-8",
    )
    returned, created = bootstrap.ensure_env(root)
    assert returned == env_path
    assert created is False
    values = env_map(env_path)
    assert values["VELANTRIM_API_KEY"] == "user-owned-key"
    assert values["VELANTRIM_NETWORK_MODE"] == "allow"
    assert values["VELANTRIM_REMOTE_DATA_MODE"] == "redacted"
    assert values["LLM_PROVIDER"] == "openai"


def test_blank_existing_key_is_filled_without_rewriting_other_settings(tmp_path):
    root = make_project(tmp_path)
    env_path = root / ".env"
    env_path.write_text(
        "VELANTRIM_API_KEY=\nVELANTRIM_NETWORK_MODE=allow\n",
        encoding="utf-8",
    )
    bootstrap.ensure_env(root)
    values = env_map(env_path)
    assert values["VELANTRIM_API_KEY"]
    assert values["VELANTRIM_NETWORK_MODE"] == "allow"


def test_venv_python_path_is_cross_platform(tmp_path):
    assert bootstrap.venv_python(tmp_path, platform="nt") == tmp_path / ".venv" / "Scripts" / "python.exe"
    assert bootstrap.venv_python(tmp_path, platform="posix") == tmp_path / ".venv" / "bin" / "python"


def test_server_command_is_loopback_only(tmp_path):
    py = tmp_path / "python"
    command = bootstrap.build_server_command(py, 8755)
    assert command == [
        str(py), "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8755"
    ]
