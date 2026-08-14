import tomllib
from pathlib import Path

import pytest

from scripts.export_locked_runtime_requirements import build_export_command, parse_extras


PYPROJECT = Path("pyproject.toml")
LOCKFILE = Path("uv.lock")


def test_runtime_extra_parser_accepts_declared_extras() -> None:
    assert parse_extras("server, parsers", PYPROJECT) == ("server", "parsers")


def test_runtime_extra_parser_fails_closed_on_unknown_or_duplicate() -> None:
    with pytest.raises(ValueError, match="unknown runtime extra"):
        parse_extras("server,not-a-real-extra", PYPROJECT)
    with pytest.raises(ValueError, match="duplicate runtime extra"):
        parse_extras("server,server", PYPROJECT)


def test_uv_export_command_is_frozen_and_keeps_hashes() -> None:
    command = build_export_command(("server", "parsers"), Path("/tmp/runtime.txt"))
    assert command[:2] == ["uv", "export"]
    assert "--frozen" in command
    assert "--no-dev" in command
    assert "--no-emit-project" in command
    assert "--no-hashes" not in command
    assert command.count("--extra") == 2
    assert command[-4:] == ["--extra", "server", "--extra", "parsers"]


def test_docker_declared_dependency_install_is_lock_bound() -> None:
    text = Path("Dockerfile").read_text(encoding="utf-8")
    copy_lines = [line.split() for line in text.splitlines() if line.startswith("COPY ")]
    assert any("uv.lock" in tokens[1:-1] for tokens in copy_lines)
    assert "export_locked_runtime_requirements.py" in text
    assert "--require-hashes" in text
    assert 'pip install --no-deps "${WHEEL}"' in text
    assert 'pip install "${WHEEL}[${RUNTIME_EXTRAS}]"' not in text


def test_docker_workflow_runs_when_lock_contract_changes() -> None:
    workflow = Path(".github/workflows/docker.yml").read_text(encoding="utf-8")
    # Both push and pull_request path filters must watch these inputs.
    assert workflow.count('- "uv.lock"') == 2
    assert workflow.count('- "scripts/export_locked_runtime_requirements.py"') == 2


def test_docker_uv_version_matches_ci_sync_owner() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    action = Path(".github/actions/sync-python-deps/action.yml").read_text(encoding="utf-8")
    assert "ARG UV_VERSION=0.12.3" in dockerfile
    assert "version: 0.12.3" in action


def test_pymorphy3_is_owned_by_server_lock_graph() -> None:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    server_deps = project["project"]["optional-dependencies"]["server"]
    assert any(dep.startswith("pymorphy3>=2.0.6") for dep in server_deps)

    lock = tomllib.loads(LOCKFILE.read_text(encoding="utf-8"))
    packages = {
        (package["name"], package["version"])
        for package in lock["package"]
    }
    assert ("pymorphy3", "2.0.6") in packages
    assert any(name == "pymorphy3-dicts-ru" for name, _ in packages)
    assert any(name == "dawg2-python" for name, _ in packages)


def test_docker_has_no_runtime_python_dependency_bypass() -> None:
    text = Path("Dockerfile").read_text(encoding="utf-8")
    assert "pip install pymorphy3" not in text
    assert "Docker-only residual" not in text
    assert "pip check" in text
    assert "import pymorphy3; pymorphy3.MorphAnalyzer(lang='ru')" in text


def test_primary_multilingual_morphology_is_available() -> None:
    from core.multilingual_router import lemmatize_ru_text

    assert lemmatize_ru_text("кошке") == "кошка"
