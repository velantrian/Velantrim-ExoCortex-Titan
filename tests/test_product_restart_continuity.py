from __future__ import annotations

import importlib.util
from pathlib import Path

from core.console_notes import ConsoleNotesStore
from core.memory import make_store


BOOTSTRAP_SCRIPT = Path(__file__).parents[1] / "scripts" / "bootstrap_titan.py"
spec = importlib.util.spec_from_file_location("bootstrap_titan_stage6", BOOTSTRAP_SCRIPT)
assert spec and spec.loader
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


def _env_map(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def _make_bootstrap_project(tmp_path: Path) -> Path:
    for relative in bootstrap.REQUIRED_PROJECT_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text(
        "VELANTRIM_API_KEY=\nLLM_PROVIDER=none\n",
        encoding="utf-8",
    )
    return tmp_path


def test_fact_survives_store_close_and_reopen(tmp_path: Path) -> None:
    db_path = str(tmp_path / "velantrim.db")
    first = make_store(db_path)
    result = first.store_fact_result(
        {
            "fact_id": "restart_fact",
            "claim": "restart continuity survives",
            "source": "stage6-test",
            "confidence": 0.8,
        }
    )
    assert result.durable_write is True
    first.close()

    second = make_store(db_path)
    try:
        fact = second.get_fact("restart_fact")
        assert fact is not None
        assert fact["claim"] == "restart continuity survives"
        assert fact["source"] == "stage6-test"
    finally:
        second.close()


def test_console_note_survives_new_store_instance(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VELANTRIM_SAFE_MODE", raising=False)
    db_path = str(tmp_path / "velantrim_notes.db")
    first = ConsoleNotesStore(db_path)
    created = first.create_note(
        title="Restart note",
        content="This note must survive a new store instance.",
        tags=["stage6"],
    )

    second = ConsoleNotesStore(db_path)
    restored = second.get_note(created["note_id"])
    assert restored is not None
    assert restored["title"] == "Restart note"
    assert restored["content"] == "This note must survive a new store instance."
    assert restored["tags"] == ["stage6"]


def test_repeat_bootstrap_preserves_user_configuration(tmp_path: Path) -> None:
    root = _make_bootstrap_project(tmp_path)
    env_path, created = bootstrap.ensure_env(root)
    assert created is True

    initial = _env_map(env_path)
    env_path.write_text(
        env_path.read_text(encoding="utf-8")
        + "OPENAI_API_KEY=user-provider-secret\n"
        + "OPENAI_MODEL=user-model\n",
        encoding="utf-8",
    )

    returned, created_again = bootstrap.ensure_env(root)
    assert returned == env_path
    assert created_again is False

    after_restart = _env_map(env_path)
    assert after_restart["VELANTRIM_API_KEY"] == initial["VELANTRIM_API_KEY"]
    assert after_restart["VELANTRIM_NETWORK_MODE"] == initial["VELANTRIM_NETWORK_MODE"]
    assert after_restart["VELANTRIM_REMOTE_DATA_MODE"] == initial["VELANTRIM_REMOTE_DATA_MODE"]
    assert after_restart["OPENAI_API_KEY"] == "user-provider-secret"
    assert after_restart["OPENAI_MODEL"] == "user-model"
