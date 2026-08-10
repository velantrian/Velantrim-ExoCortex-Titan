"""Issue #282: canonical, privacy-safe PII claim redaction regression tests."""

from __future__ import annotations

import json
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

    db_path = str(tmp_path / "pii-redaction.db")
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


def _fact_row(store, fact_id: str):
    with store._db() as conn:
        return conn.execute(
            "SELECT claim, confidence, epistemic_state, metadata, fact_version, "
            "updated_at, audit_subject_id FROM facts WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()


def _version_rows(store, fact_id: str):
    with store._db() as conn:
        return conn.execute(
            "SELECT * FROM fact_versions WHERE fact_id = ? ORDER BY version_id",
            (fact_id,),
        ).fetchall()


def _audit_count(store, fact_id: str) -> int:
    row = _fact_row(store, fact_id)
    if row is None or not row[6]:
        return 0
    chain_id = f"fact-transition:{row[6]}"
    with store._db() as conn:
        return int(
            conn.execute(
                "SELECT COUNT(*) FROM memory_events WHERE chain_id = ?",
                (chain_id,),
            ).fetchone()[0]
        )


def _outbox_count(store, fact_id: str) -> int:
    with store._db() as conn:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='projection_outbox'"
        ).fetchone()
        if not exists:
            return 0
        return int(
            conn.execute(
                "SELECT COUNT(*) FROM projection_outbox WHERE aggregate_id = ?",
                (fact_id,),
            ).fetchone()[0]
        )


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
        return None if row is None else row[0]


def _seed_with_historical_pii(store, fact_id: str = "pii1") -> None:
    first = store.store_fact_result(
        {
            "fact_id": fact_id,
            "claim": "first contact alice@example.com",
            "source": "user",
            "confidence": 0.61,
        }
    )
    assert first.durable_write is True
    second = store.store_fact_result(
        {
            "fact_id": fact_id,
            "claim": "second contact bob@example.com",
            "source": "user",
            "confidence": 0.61,
        }
    )
    assert second.durable_write is True
    assert len(_version_rows(store, fact_id)) == 1


def test_single_redaction_sanitizes_canon_history_fts_and_emits_content_free_evidence(
    migrated_store,
):
    from core.fact_integrity import verify_stored_checksum
    from core.forgetting import ForgettingEngine
    from core.version_store import VersionStore

    store = migrated_store
    _seed_with_historical_pii(store)
    before = _fact_row(store, "pii1")
    assert before is not None
    before_version = int(before[4])
    before_audit = _audit_count(store, "pii1")
    before_outbox = _outbox_count(store, "pii1")

    verdict = ForgettingEngine(db_path=store.db_path).redact_pii_fact("pii1")

    assert verdict.allowed is True
    assert verdict.reason == "redacted"
    assert verdict.redacted_count == 1

    row = _fact_row(store, "pii1")
    assert row[0] == "second contact [EMAIL]"
    assert row[1] == before[1]  # I-F3: confidence unchanged
    assert row[2] == before[2]  # I-F3: ESM state unchanged
    assert int(row[4]) == before_version + 1

    current = store.get_fact_durable("pii1")
    assert current is not None
    assert verify_stored_checksum(current) is True

    versions = _version_rows(store, "pii1")
    assert len(versions) == 2
    assert all("@" not in (v["claim"] or "") for v in versions)
    assert [v["claim"] for v in versions] == [
        "first contact [EMAIL]",
        "second contact [EMAIL]",
    ]
    integrity = VersionStore(store.db_path).verify_versions_integrity("pii1")
    assert integrity["ok"] is True

    fts_claim = _fts_claim(store, "pii1")
    if fts_claim is not None:
        assert fts_claim == "second contact [EMAIL]"
        assert "@" not in fts_claim

    assert _audit_count(store, "pii1") == before_audit + 1
    assert _outbox_count(store, "pii1") == before_outbox + 1

    with store._db() as conn:
        chain_id = f"fact-transition:{row[6]}"
        event = conn.execute(
            "SELECT event_type, actor, reason, payload FROM memory_events "
            "WHERE chain_id = ? ORDER BY chain_sequence DESC LIMIT 1",
            (chain_id,),
        ).fetchone()
    assert event[0] == "fact_updated"
    assert event[2] == "cas_guarded_write"
    assert "alice@example.com" not in json.dumps(tuple(event))
    assert "bob@example.com" not in json.dumps(tuple(event))


def test_no_pii_is_true_noop_with_no_false_evidence(migrated_store):
    from core.forgetting import ForgettingEngine

    store = migrated_store
    store.store_fact_result(
        {
            "fact_id": "clean",
            "claim": "nothing sensitive here",
            "source": "user",
            "confidence": 0.5,
        }
    )
    before = _fact_row(store, "clean")
    before_versions = len(_version_rows(store, "clean"))
    before_audit = _audit_count(store, "clean")
    before_outbox = _outbox_count(store, "clean")

    verdict = ForgettingEngine(db_path=store.db_path).redact_pii_fact("clean")

    assert verdict.allowed is True
    assert verdict.reason == "no_pii_found"
    after = _fact_row(store, "clean")
    assert tuple(after) == tuple(before)
    assert len(_version_rows(store, "clean")) == before_versions
    assert _audit_count(store, "clean") == before_audit
    assert _outbox_count(store, "clean") == before_outbox


def test_version_evidence_failure_rolls_back_every_privacy_surface(
    migrated_store, monkeypatch,
):
    from core.forgetting import ForgettingEngine
    from core.version_store import VersionStore

    store = migrated_store
    _seed_with_historical_pii(store, "rollback-version")
    before = _fact_row(store, "rollback-version")
    before_versions = [tuple(row) for row in _version_rows(store, "rollback-version")]
    before_audit = _audit_count(store, "rollback-version")
    before_outbox = _outbox_count(store, "rollback-version")
    before_fts = _fts_claim(store, "rollback-version")

    def _fail_snapshot(cls, conn, fact_id, fact_data, caused_by="unknown", now_iso=None):
        raise RuntimeError("injected version evidence failure")

    monkeypatch.setattr(
        VersionStore,
        "snapshot_before_change_in_transaction",
        classmethod(_fail_snapshot),
    )

    verdict = ForgettingEngine(db_path=store.db_path).redact_pii_fact(
        "rollback-version"
    )
    assert verdict.allowed is False
    assert "store_error" in verdict.reason

    assert tuple(_fact_row(store, "rollback-version")) == tuple(before)
    assert [tuple(row) for row in _version_rows(store, "rollback-version")] == before_versions
    assert _audit_count(store, "rollback-version") == before_audit
    assert _outbox_count(store, "rollback-version") == before_outbox
    assert _fts_claim(store, "rollback-version") == before_fts


def test_audit_failure_rolls_back_canon_history_and_projection(migrated_store, monkeypatch):
    from core.audit_chain import AuditChain
    from core.forgetting import ForgettingEngine

    store = migrated_store
    _seed_with_historical_pii(store, "rollback-audit")
    before = _fact_row(store, "rollback-audit")
    before_versions = [tuple(row) for row in _version_rows(store, "rollback-audit")]
    before_audit = _audit_count(store, "rollback-audit")
    before_outbox = _outbox_count(store, "rollback-audit")
    before_fts = _fts_claim(store, "rollback-audit")

    def _fail_audit(self, *args, **kwargs):
        raise RuntimeError("injected audit failure")

    monkeypatch.setattr(AuditChain, "log_in_transaction", _fail_audit)
    verdict = ForgettingEngine(db_path=store.db_path).redact_pii_fact(
        "rollback-audit"
    )
    assert verdict.allowed is False
    assert "store_error" in verdict.reason

    assert tuple(_fact_row(store, "rollback-audit")) == tuple(before)
    assert [tuple(row) for row in _version_rows(store, "rollback-audit")] == before_versions
    assert _audit_count(store, "rollback-audit") == before_audit
    assert _outbox_count(store, "rollback-audit") == before_outbox
    assert _fts_claim(store, "rollback-audit") == before_fts


def test_single_redaction_fails_closed_on_stale_snapshot(migrated_store, monkeypatch):
    from core.forgetting import redact_pii
    from core.pii_redaction import (
        CanonicalPiiRedactor,
        PiiRedactionConcurrentModification,
    )

    store = migrated_store
    store.store_fact_result(
        {
            "fact_id": "race",
            "claim": "email race@example.com",
            "source": "user",
            "confidence": 0.5,
        }
    )
    before_versions = len(_version_rows(store, "race"))
    before_audit = _audit_count(store, "race")
    before_outbox = _outbox_count(store, "race")

    redactor = CanonicalPiiRedactor(store)
    original_prepare = redactor._prepare_evidence_schema

    def _prepare_then_change(candidates):
        original_prepare(candidates)
        with store._db() as conn:
            bump = store._fact_version_bump_sql(conn)
            conn.execute(
                f"UPDATE facts SET {bump}claim = ?, updated_at = ? WHERE fact_id = ?",
                ("concurrent replacement", "2099-01-01T00:00:00+00:00", "race"),
            )
        store._l0_del("race")

    monkeypatch.setattr(redactor, "_prepare_evidence_schema", _prepare_then_change)

    with pytest.raises(PiiRedactionConcurrentModification):
        redactor.redact_fact("race", redact_pii)

    row = _fact_row(store, "race")
    assert row[0] == "concurrent replacement"
    assert len(_version_rows(store, "race")) == before_versions
    assert _audit_count(store, "race") == before_audit
    assert _outbox_count(store, "race") == before_outbox


def test_batch_cas_failure_rolls_back_every_other_candidate(migrated_store, monkeypatch):
    from core.forgetting import redact_pii
    from core.pii_redaction import (
        CanonicalPiiRedactor,
        PiiRedactionConcurrentModification,
    )

    store = migrated_store
    for fid in ("batch-a", "batch-b"):
        store.store_fact_result(
            {
                "fact_id": fid,
                "claim": f"email {fid}@example.com",
                "source": "user",
                "confidence": 0.5,
            }
        )

    before_a = tuple(_fact_row(store, "batch-a"))
    before_a_versions = len(_version_rows(store, "batch-a"))
    before_a_audit = _audit_count(store, "batch-a")
    before_a_outbox = _outbox_count(store, "batch-a")

    redactor = CanonicalPiiRedactor(store)
    original_prepare = redactor._prepare_evidence_schema

    def _prepare_then_change_second(candidates):
        original_prepare(candidates)
        with store._db() as conn:
            bump = store._fact_version_bump_sql(conn)
            conn.execute(
                f"UPDATE facts SET {bump}claim = ?, updated_at = ? WHERE fact_id = ?",
                ("concurrent second", "2099-01-01T00:00:00+00:00", "batch-b"),
            )
        store._l0_del("batch-b")

    monkeypatch.setattr(
        redactor, "_prepare_evidence_schema", _prepare_then_change_second
    )

    with pytest.raises(PiiRedactionConcurrentModification):
        redactor.redact_batch(100, redact_pii)

    assert tuple(_fact_row(store, "batch-a")) == before_a
    assert len(_version_rows(store, "batch-a")) == before_a_versions
    assert _audit_count(store, "batch-a") == before_a_audit
    assert _outbox_count(store, "batch-a") == before_a_outbox
    assert _fact_row(store, "batch-b")[0] == "concurrent second"


def test_legacy_batch_adapter_is_atomic_and_preserves_state_confidence(migrated_store):
    from core.forgetting import ForgettingEngine

    store = migrated_store
    originals = {}
    for fid in ("legacy-a", "legacy-b"):
        store.store_fact_result(
            {
                "fact_id": fid,
                "claim": f"contact {fid}@example.com",
                "source": "user",
                "confidence": 0.73,
            }
        )
        originals[fid] = _fact_row(store, fid)

    verdict = ForgettingEngine(db_path=store.db_path).redact_pii_batch(limit=100)
    assert verdict.allowed is True
    assert verdict.reason == "batch_redacted"
    assert verdict.redacted_count == 2

    for fid in ("legacy-a", "legacy-b"):
        row = _fact_row(store, fid)
        assert "@" not in row[0]
        assert row[1] == originals[fid][1]
        assert row[2] == originals[fid][2]
        assert int(row[4]) == int(originals[fid][4]) + 1
