from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_legacy_sparse_patcher_fails_closed() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "_fill_sparse_batches_pt1.py"

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    combined = f"{result.stdout}\n{result.stderr}".lower()
    assert "disabled" in combined
    assert "provenance-only" in combined
    assert "docs/history/generators/_fill_sparse_batches_pt1.py.txt" in combined
