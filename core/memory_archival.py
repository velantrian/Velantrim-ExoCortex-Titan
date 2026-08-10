"""📦 Memory archival coordinator.

Issue #284 / parent #50 convergence: this module owns archival eligibility,
filesystem payload preparation, restore and reporting.  It no longer owns raw SQL
updates of canonical ``facts.claim``.  Canonical claim mutation is delegated to
``CanonicalArchivalRewriter`` over the existing ``SQLiteGraphStore`` transaction.

Filesystem and SQLite cannot share a literal transaction.  The bounded ordering is:
prepare a durable archive payload first, then atomically commit Canon + archive marker
+ VersionStore + AuditChain + projections.  If the DB/evidence transaction fails, a
newly-created payload is removed best-effort; an unremovable orphan never counts as a
successful canonical archive.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.archival_mutation import ArchivalCandidate, CanonicalArchivalRewriter
from core.memory import SQLiteGraphStore
from core.write_gate import ensure_writes_allowed

logger = logging.getLogger("velantrim.memory_archival")

SQLITE_PATH = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim.db")
ARCHIVE_PATH = os.getenv("VELANTRIM_ARCHIVE_PATH", "./data/archive")
ARCHIVE_AGE_DAYS = int(os.getenv("VELANTRIM_ARCHIVE_AGE", "90"))

_IMMUTABLE_STATES = {"ImmutableCore"}


@dataclass
class ArchiveReport:
    scanned: int = 0
    archived: int = 0
    skipped_immutable: int = 0
    skipped_recent: int = 0
    errors: int = 0
    archive_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scanned": self.scanned,
            "archived": self.archived,
            "skipped_immutable": self.skipped_immutable,
            "skipped_recent": self.skipped_recent,
            "errors": self.errors,
            "archive_path": self.archive_path,
        }


class MemoryArchival:
    """Archive coordinator; not an independent canonical-write owner."""

    def __init__(
        self,
        *,
        db_path: str = SQLITE_PATH,
        archive_path: str = ARCHIVE_PATH,
        age_days: int = ARCHIVE_AGE_DAYS,
    ):
        self._db_path = db_path
        self._archive_path = Path(archive_path)
        self._age_days = age_days
        self._archive_path.mkdir(parents=True, exist_ok=True)
        self._store = SQLiteGraphStore(db_path)
        self._rewriter = CanonicalArchivalRewriter(self._store)
        self._rewriter.ensure_schema()

    def close(self) -> None:
        self._store.close()

    def _eligible_snapshots(self, cutoff: str) -> list[dict[str, Any]]:
        with self._store._db() as conn:
            rows = conn.execute(
                """SELECT fact_id
                   FROM facts
                   WHERE created_at < ?
                     AND epistemic_state != 'ImmutableCore'
                     AND fact_id NOT IN (SELECT fact_id FROM archived_facts)
                   ORDER BY created_at ASC""",
                (cutoff,),
            ).fetchall()
        snapshots: list[dict[str, Any]] = []
        for row in rows:
            snapshot = self._store.get_fact_durable(str(row["fact_id"]))
            if snapshot is not None:
                snapshots.append(snapshot)
        return snapshots

    def archive_old_facts(self, *, dry_run: bool = False) -> ArchiveReport:
        """Archive eligible facts older than the configured age.

        Each generated payload batch (max 100 records) is one SQLite atomic mutation
        unit.  A later batch failure does not lie about earlier committed batches.
        """
        report = ArchiveReport(archive_path=str(self._archive_path))
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self._age_days)).isoformat()

        try:
            snapshots = self._eligible_snapshots(cutoff)
            report.scanned = len(snapshots)
            if dry_run:
                return report

            batch: List[Dict[str, Any]] = []
            batch_count = 0
            for snapshot in snapshots:
                if snapshot.get("epistemic_state") in _IMMUTABLE_STATES:
                    report.skipped_immutable += 1
                    continue
                batch.append(snapshot)
                if len(batch) >= 100:
                    report.archived += self._archive_batch(batch, batch_count)
                    batch_count += 1
                    batch = []
            if batch:
                report.archived += self._archive_batch(batch, batch_count)
            return report
        except Exception as exc:  # fail closed; committed prior batches stay truthful
            logger.error("MemoryArchival.archive_old_facts: %s", exc)
            report.errors += 1
            return report

    def _archive_batch(
        self,
        batch: List[Dict[str, Any]],
        batch_num: int,
    ) -> int:
        """Prepare one immutable payload, then atomically rewrite its Canon rows."""
        if not batch:
            return 0
        ensure_writes_allowed()

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        archive_file = self._archive_path / (
            f"archive_{timestamp}_b{batch_num:03d}_{uuid.uuid4().hex[:8]}.json"
        )
        archived_at = datetime.now(timezone.utc).isoformat()

        # Exclusive create avoids silently replacing an existing archive artifact.
        with open(archive_file, "x", encoding="utf-8") as f:
            json.dump(
                {
                    "archived_at": archived_at,
                    "archived_count": len(batch),
                    "facts": batch,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
            f.flush()
            os.fsync(f.fileno())

        candidates = [
            ArchivalCandidate.from_snapshot(
                snapshot,
                archive_key=f"archive://{archive_file.name}#{snapshot['fact_id']}",
                archive_file=str(archive_file),
            )
            for snapshot in batch
        ]

        try:
            return self._rewriter.rewrite_batch(candidates)
        except Exception:
            try:
                archive_file.unlink(missing_ok=True)
            except OSError as cleanup_exc:
                logger.error(
                    "Archival DB rollback left non-canonical orphan payload %s: %s",
                    archive_file,
                    cleanup_exc,
                )
            raise

    def restore_fact(self, fact_id: str) -> Optional[Dict[str, Any]]:
        """Read the original archived payload; this is not a Canon mutation."""
        try:
            with self._store._db() as conn:
                row = conn.execute(
                    "SELECT * FROM archived_facts WHERE fact_id = ?", (fact_id,)
                ).fetchone()
            if not row:
                return None

            archive_path = self._archive_path / Path(row["archive_file"]).name
            if archive_path.exists():
                with open(archive_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for fact in data.get("facts", []):
                    if fact.get("fact_id") == fact_id:
                        return fact
            return {
                "fact_id": fact_id,
                "claim": row["original_claim"],
                "archived": True,
            }
        except Exception as exc:
            logger.error("MemoryArchival.restore_fact: %s", exc)
            return None

    def stats(self) -> Dict[str, Any]:
        try:
            with self._store._db() as conn:
                archived = conn.execute(
                    "SELECT COUNT(*) FROM archived_facts"
                ).fetchone()[0]
            archive_files = list(self._archive_path.glob("archive_*.json"))
            return {
                "archived_facts": archived,
                "archive_files_count": len(archive_files),
                "archive_path": str(self._archive_path),
                "archive_age_days": self._age_days,
                "total_archive_size_bytes": sum(f.stat().st_size for f in archive_files),
            }
        except Exception:
            return {"archived_facts": 0, "archive_path": str(self._archive_path)}


_archival: Optional[MemoryArchival] = None


def get_memory_archival() -> MemoryArchival:
    """Legacy process-level access surface; not a new mutation authority."""
    global _archival
    if _archival is None:
        _archival = MemoryArchival()
    return _archival


__all__ = ["MemoryArchival", "ArchiveReport", "get_memory_archival"]
