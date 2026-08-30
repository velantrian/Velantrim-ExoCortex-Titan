from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/maintenance/audit_sparse.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("audit_sparse_maintenance", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sparse_audit_uses_repo_root_and_remains_read_only() -> None:
    module = _load_module()

    assert module.REPO_ROOT == REPO_ROOT
    assert module.RU == REPO_ROOT / "docs/knowledge/world_skills_core/ru"

    source = SCRIPT.read_text(encoding="utf-8")
    assert ".write_text(" not in source
    assert ".write_bytes(" not in source
    assert "open(" not in source
    assert "unlink(" not in source
    assert "rename(" not in source
    assert "replace(" not in source
