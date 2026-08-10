"""Issue #284: archival claim rewrite converges on canonical evidence semantics."""

from __future__ import annotations

import inspect
import os
import subprocess
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
APPLY_MIGRATIONS = os.path.join(SCRIPTS_DIR, "apply_migrations.py")


def _run_apply(db_path: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, APPLY_MIGRATIONS, "--db", db_path, "--no-backup"],
        capture_output=True,
        text=True,
    )


@pytest.fixture
def migrated_store(tmp_path):
    from core.memory import SQLiteGraphStore, make_store

    db_path = str(tmp_path / "archive.db")
    bootstrap = SQLiteGraphStore(db_path)
    bootstrap.ensure_schema()
    bootstrap.close()
    result = _run_apply(db_path)
    assert result.returncode == 0, (
        f"apply_migrations failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    store = make_store(db_path)
    yield store
    store.close()


def _row(store, fact_id: str):
    with store._db() as conn:
        return conn.execute(
            "SELECT claim, confidence, epistemic_state, metadata, fact_version, "
            "updated_at, audit_subject_id FROM facts WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()


def _version_count(store, fact_id: str) -> int:
    with store._db() as conn:
        return int(conn.execute(
            "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?", (fact_id,)
        ).fetchone()[0])


def _archive_count(store, fact_id: str) -> int:
    with store._db() as conn:
        return int(conn.execute(
            "SELECT COUNT(*) FROM archived_facts WHERE fact_id = ?", (fact_id,)
        ).fetchone()[0])


def _audit_count(store, fact_id: str) -> int:
    row = _row(store, fact_id)
    if row is None or not row[6]:
        return 0
    with store._db() as conn:
        return int(conn.execute(
            "SELECT COUNT(*) FROM memory_events WHERE chain_id = ?",
            (f"fact-transition:{row[6]}",),
        ).fetchone()[0])


def _outbox_count(store, fact_id: str) -> int:
    with store._db() as conn:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='projection_outbox'"
        ).fetchone()
        if not exists:
            return 0
        return int(conn.execute(
            "SELECT COUNT(*) FROM projection_outbox WHERE aggregate_id = ?",
            (fact_id,),
        ).fetchone()[0])


def _fts_claim(store, fact_id: str) -> str | None:
    with store._db() as conn:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='facts_fts'"
        ).fetchone()
        if not exists:
            return None
        row = conn.execute(
            "SELECT claim FROM facts_fts WHERE fact_id = ?", (fact_id,)
        ).fetchone()
        return None if row is None else str(row[0])


def _seed(store, fact_id: str, claim: str = "old memory", confidence: float = 0.73):
    result = store.store_fact_result({
        "fact_id": fact_id,
        "claim": claim,
        "source": "user",
        "confidence": confidence,
    })
    assert result.durable_write is True


def _payload(tmp_path, fact_id: str):
    path = tmp_path / f"{fact_id}.json"
    path.write_text('{"facts": []}', encoding="utf-8")
    return path


def test_memory_archival_happy_path_preserves_state_confidence_and_updates_evidence(
    migrated_store, tmp_path,
):
    from core.fact_integrity import verify_stored_checksum
    from core.memory_archival import MemoryArchival

    store = migrated_store
    _seed(store, "archive-happy")
    before = _row(store, "archive-happy")
    before_versions = _version_count(store, "archive-happy")
    before_audit = _audit_count(store, "archive-happy")
    before_outbox = _outbox_count(store, "archive-happy")

    archival = MemoryArchival(
        db_path=store.db_path,
        archive_path=str(tmp_path / "payloads"),
        age_days=-1,
    )
    report = archival.archive_old_facts()
    archival.close()

    assert report.errors == 0
    assert report.archived == 1
    after = _row(store, "archive-happy")
    assert after[0].startswith("[ARCHIVED: archive://")
    assert after[1] == before[1]
    assert after[2] == before[2]
    assert int(after[4]) == int(before[4]) + 1
    assert _archive_count(store, "archive-happy") == 1
    assert _version_count(store, "archive-happy") == before_versions + 1
    assert _audit_count(store, "archive-happy") == before_audit + 1
    assert _outbox_count(store, "archive-happy") == before_outbox + 1
    current = store.get_fact_durable("archive-happy")
    assert current is not None and verify_stored_checksum(current) is True
    fts = _fts_claim(store, "archive-happy")
    if fts is not None:
        assert fts == after[0]
    assert len(list((tmp_path / "payloads").glob("archive_*.json"))) == 1


def test_dry_run_and_second_archive_are_true_noops(migrated_store, tmp_path):
    from core.memory_archival import MemoryArchival

    store = migrated_store
    _seed(store, "archive-noop")
    archival = MemoryArchival(
        db_path=store.db_path,
        archive_path=str(tmp_path / "payloads"),
        age_days=-1,
    )
    before = tuple(_row(store, "archive-noop"))
    dry = archival.archive_old_facts(dry_run=True)
    assert dry.scanned == 1 and dry.archived == 0 and dry.errors == 0
    assert tuple(_row(store, "archive-noop")) == before
    assert _archive_count(store, "archive-noop") == 0

    first = archival.archive_old_facts()
    versions = _version_count(store, "archive-noop")
    audits = _audit_count(store, "archive-noop")
    outbox = _outbox_count(store, "archive-noop")
    second = archival.archive_old_facts()
    archival.close()

    assert first.archived == 1 and first.errors == 0
    assert second.scanned == 0 and second.archived == 0 and second.errors == 0
    assert _version_count(store, "archive-noop") == versions
    assert _audit_count(store, "archive-noop") == audits
    assert _outbox_count(store, "archive-noop") == outbox


def test_missing_payload_fails_before_canonical_mutation(migrated_store, tmp_path):
    from core.archival_mutation import ArchivalCandidate, CanonicalArchivalRewriter

    store = migrated_store
    _seed(store, "missing-payload")
    snapshot = store.get_fact_durable("missing-payload")
    before = tuple(_row(store, "missing-payload"))
    candidate = ArchivalCandidate.from_snapshot(
        snapshot,
        archive_key="archive://missing.json#missing-payload",
        archive_file=str(tmp_path / "missing.json"),
    )
    rewriter = CanonicalArchivalRewriter(store)
    with pytest.raises(FileNotFoundError):
        rewriter.rewrite_batch([candidate])
    assert tuple(_row(store, "missing-payload")) == before
    assert _archive_count(store, "missing-payload") == 0


def test_stale_snapshot_cas_miss_has_no_false_archive_evidence(migrated_store, tmp_path):
    from core.archival_mutation import (
        ArchivalCandidate,
        ArchivalConcurrentModificationError,
        CanonicalArchivalRewriter,
    )

    store = migrated_store
    _seed(store, "archive-race")
    snapshot = store.get_fact_durable("archive-race")
    payload = _payload(tmp_path, "archive-race")
    candidate = ArchivalCandidate.from_snapshot(
        snapshot,
        archive_key=f"archive://{payload.name}#archive-race",
        archive_file=str(payload),
    )
    before_versions = _version_count(store, "archive-race")
    before_audit = _audit_count(store, "archive-race")
    before_outbox = _outbox_count(store, "archive-race")
    with store._db() as conn:
        bump = store._fact_version_bump_sql(conn)
        conn.execute(
            f"UPDATE facts SET {bump}claim = ?, updated_at = ? WHERE fact_id = ?",
            ("concurrent", "2099-01-01T00:00:00+00:00", "archive-race"),
        )
    store._l0_del("archive-race")

    with pytest.raises(ArchivalConcurrentModificationError):
        CanonicalArchivalRewriter(store).rewrite_batch([candidate])
    assert _row(store, "archive-race")[0] == "concurrent"
    assert _archive_count(store, "archive-race") == 0
    assert _version_count(store, "archive-race") == before_versions
    assert _audit_count(store, "archive-race") == before_audit
    assert _outbox_count(store, "archive-race") == before_outbox


def test_version_failure_rolls_back_db_and_coordinator_cleans_payload(
    migrated_store, tmp_path, monkeypatch,
):
    from core.memory_archival import MemoryArchival
    from core.version_store import VersionStore

    store = migrated_store
    _seed(store, "archive-version-fail")
    before = tuple(_row(store, "archive-version-fail"))

    def fail_snapshot(cls, conn, fact_id, fact_data, caused_by="unknown", now_iso=None):
        raise RuntimeError("injected version failure")

    monkeypatch.setattr(
        VersionStore,
        "snapshot_before_change_in_transaction",
        classmethod(fail_snapshot),
    )
    payload_dir = tmp_path / "payloads"
    archival = MemoryArchival(
        db_path=store.db_path, archive_path=str(payload_dir), age_days=-1
    )
    report = archival.archive_old_facts()
    archival.close()

    assert report.archived == 0 and report.errors == 1
    assert tuple(_row(store, "archive-version-fail")) == before
    assert _archive_count(store, "archive-version-fail") == 0
    assert list(payload_dir.glob("archive_*.json")) == []


def test_audit_failure_rolls_back_canon_marker_version_fts_and_outbox(
    migrated_store, tmp_path, monkeypatch,
):
    from core.archival_mutation import ArchivalCandidate, CanonicalArchivalRewriter
    from core.audit_chain import AuditChain

    store = migrated_store
    _seed(store, "archive-audit-fail")
    snapshot = store.get_fact_durable("archive-audit-fail")
    payload = _payload(tmp_path, "archive-audit-fail")
    candidate = ArchivalCandidate.from_snapshot(
        snapshot,
        archive_key=f"archive://{payload.name}#archive-audit-fail",
        archive_file=str(payload),
    )
    before = tuple(_row(store, "archive-audit-fail"))
    before_versions = _version_count(store, "archive-audit-fail")
    before_audit = _audit_count(store, "archive-audit-fail")
    before_outbox = _outbox_count(store, "archive-audit-fail")
    before_fts = _fts_claim(store, "archive-audit-fail")

    monkeypatch.setattr(
        AuditChain,
        "log_in_transaction",
        lambda self, *args, **kwargs: (_ for _ in ()).throw(RuntimeError("audit fail")),
    )
    with pytest.raises(RuntimeError, match="audit fail"):
        CanonicalArchivalRewriter(store).rewrite_batch([candidate])

    assert tuple(_row(store, "archive-audit-fail")) == before
    assert _archive_count(store, "archive-audit-fail") == 0
    assert _version_count(store, "archive-audit-fail") == before_versions
    assert _audit_count(store, "archive-audit-fail") == before_audit
    assert _outbox_count(store, "archive-audit-fail") == before_outbox
    assert _fts_claim(store, "archive-audit-fail") == before_fts


def test_one_stale_member_rolls_back_other_member_in_same_batch(
    migrated_store, tmp_path,
):
    from core.archival_mutation import (
        ArchivalCandidate,
        ArchivalConcurrentModificationError,
        CanonicalArchivalRewriter,
    )

    store = migrated_store
    for fid in ("batch-a", "batch-b"):
        _seed(store, fid)
    snapshots = {fid: store.get_fact_durable(fid) for fid in ("batch-a", "batch-b")}
    payload = _payload(tmp_path, "batch")
    candidates = [
        ArchivalCandidate.from_snapshot(
            snapshots[fid],
            archive_key=f"archive://{payload.name}#{fid}",
            archive_file=str(payload),
        )
        for fid in ("batch-a", "batch-b")
    ]
    before_a = tuple(_row(store, "batch-a"))
    before_a_versions = _version_count(store, "batch-a")
    before_a_audit = _audit_count(store, "batch-a")
    with store._db() as conn:
        bump = store._fact_version_bump_sql(conn)
        conn.execute(
            f"UPDATE facts SET {bump}claim = ?, updated_at = ? WHERE fact_id = ?",
            ("concurrent-b", "2099-01-01T00:00:00+00:00", "batch-b"),
        )
    store._l0_del("batch-b")

    with pytest.raises(ArchivalConcurrentModificationError):
        CanonicalArchivalRewriter(store).rewrite_batch(candidates)
    assert tuple(_row(store, "batch-a")) == before_a
    assert _archive_count(store, "batch-a") == 0
    assert _version_count(store, "batch-a") == before_a_versions
    assert _audit_count(store, "batch-a") == before_a_audit
    assert _row(store, "batch-b")[0] == "concurrent-b"
    assert _archive_count(store, "batch-b") == 0


def test_legacy_coordinator_no_longer_owns_direct_facts_update():
    from core.memory_archival import MemoryArchival

    source = inspect.getsource(MemoryArchival._archive_batch)
    assert "UPDATE facts" not in source
    assert "CanonicalArchivalRewriter" not in source  # delegated through self._rewriter
    assert "self._rewriter.rewrite_batch" in source
