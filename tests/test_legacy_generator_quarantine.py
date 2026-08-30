from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_legacy_869_878_generator_fails_closed() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "_gen_batches_869_878.py"

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
    assert "docs/history/generators/_gen_batches_869_878.py.txt" in combined
