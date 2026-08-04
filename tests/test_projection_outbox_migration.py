from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPLY_MIGRATIONS = ROOT / "scripts" / "apply_migrations.py"


def _run_apply(db_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(APPLY_MIGRATIONS),
            "--db",
            str(db_path),
            "--no-backup",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_migration_020_is_registered_idempotent_and_content_minimized(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "projection-outbox-migration.db"

    first = _run_apply(db_path)
    assert first.returncode == 0, first.stderr

    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        # 21, not 20: migration 021 (projection_checkpoints, issue #194) is
        # the latest as of this test's own update — this assertion checks
        # the runner reached the current latest version, not specifically
        # that 020 is last forever.
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 21
        columns = {
            str(row[1])
            for row in conn.execute("PRAGMA table_info(projection_outbox)").fetchall()
        }
        assert columns == {
            "outbox_id",
            "aggregate_type",
            "aggregate_id",
            "scope_ref",
            "projection_kind",
            "operation",
            "canonical_version",
            "policy_version",
            "created_at",
        }
        indexes = {
            str(row[0])
            for row in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'index' AND tbl_name = 'projection_outbox'"
            ).fetchall()
        }
        assert "idx_projection_outbox_created" in indexes
        assert "idx_projection_outbox_aggregate" in indexes
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    second = _run_apply(db_path)
    assert second.returncode == 0, second.stderr
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 21
        assert conn.execute(
            "SELECT COUNT(*) FROM projection_outbox"
        ).fetchone()[0] == 0
