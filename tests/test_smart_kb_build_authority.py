from __future__ import annotations

from pathlib import Path

import pytest


def _fact(fid: str) -> dict:
    """Explicitly reviewed World Skills candidate that is eligible for Canon admission."""
    return {
        "fact_id": fid,
        "type": "METHOD",
        "claim": f"Curated external world knowledge for {fid}",
        "source": "wsc:METHOD",
        "truth_status": "Supported",
        "source_refs": ["source:test:primary", "source:test:corroborating"],
        "confidence": 0.85,
        "risk_domain": "general",
        "limitations": "Synthetic fixture limited to the smart-KB authority contract.",
        "review_status": "approved",
        "reviewer": "reviewer:test-suite",
        "reviewed_at": "2026-08-14T18:00:00+00:00",
        "metadata": {"domain": "test", "knowledge_file": "TEST_BATCH.ru.md"},
    }


def _legacy_unreviewed_fact(fid: str) -> dict:
    """Historical curated row without the C9 provenance/review admission metadata."""
    return {
        "fact_id": fid,
        "type": "METHOD",
        "claim": f"Curated external world knowledge for {fid}",
        "source": "wsc:METHOD",
        "confidence": 0.85,
        "metadata": {"domain": "test", "knowledge_file": "TEST_BATCH.ru.md"},
    }


def test_builder_source_owns_no_raw_fact_dml():
    source = Path("scripts/build_kb_graph.py").read_text(encoding="utf-8")
    assert "INSERT INTO facts" not in source
    assert "UPDATE facts SET" not in source
    assert "ingest_kb_facts(" in source


def test_canonical_kb_build_creates_classifies_validates_and_versions(tmp_path):
    from core.memory import SQLiteGraphStore
    from scripts.build_kb_graph import ingest_kb_facts

    store = SQLiteGraphStore(db_path=str(tmp_path / "kb.db"))
    stats = ingest_kb_facts(store, [_fact("kb.authority.one")], batch_size=1, require_empty=True)

    assert stats == {"parsed": 1, "ingested": 1, "validated": 1, "errors": 0}
    durable = store.get_fact_durable("kb.authority.one")
    assert durable is not None
    assert durable["claim_type"] == "WORLD_FACT"
    assert durable["origin_type"] == "EXTERNAL"
    assert durable["epistemic_state"] == "Validated"
    with store._db() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?",
            ("kb.authority.one",),
        ).fetchone()[0] >= 3
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_events WHERE chain_id = ?",
            (f"fact-transition:{durable['audit_subject_id']}",),
        ).fetchone()[0] >= 4


def test_canonical_kb_build_rejects_legacy_unreviewed_curated_fact(tmp_path):
    from core.memory import SQLiteGraphStore
    from scripts.build_kb_graph import ingest_kb_facts

    store = SQLiteGraphStore(db_path=str(tmp_path / "kb.db"))
    with pytest.raises(RuntimeError, match="canonical smart-KB ingest incomplete"):
        ingest_kb_facts(
            store,
            [_legacy_unreviewed_fact("kb.authority.unreviewed")],
            batch_size=1,
            require_empty=True,
        )

    durable = store.get_fact_durable("kb.authority.unreviewed")
    assert durable is not None
    assert durable["epistemic_state"] == "Observed"
    assert durable["metadata"]["world_skills_admission_contract"] == "world-skills-admission-v1"


def test_normal_rebuild_reclassifies_existing_fact_through_batch_owner(tmp_path):
    from core.memory import SQLiteGraphStore
    from core.world_skills_ingest import ingest_facts

    store = SQLiteGraphStore(db_path=str(tmp_path / "kb.db"))
    seed = {
        "fact_id": "kb.authority.legacy",
        "claim": "Curated external world knowledge for kb.authority.legacy",
        "source": "user_message",
        "confidence": 0.85,
        "claim_type": "OPINION",
        "origin_type": "USER_REPORTED",
    }
    assert store.store_fact(seed)
    before = store.get_fact_durable("kb.authority.legacy")
    assert before is not None
    with store._db() as conn:
        before_version_count = int(conn.execute(
            "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?",
            ("kb.authority.legacy",),
        ).fetchone()[0])

    rep = ingest_facts(store, [_fact("kb.authority.legacy")], validate=False)
    assert {key: rep[key] for key in ("parsed", "ingested", "validated", "errors")} == {
        "parsed": 1,
        "ingested": 1,
        "validated": 0,
        "errors": 0,
    }
    assert rep["quarantined"] == 0
    assert rep["truth_gate_rejected"] == 0
    assert rep["admission_contract"] == "world-skills-admission-v1"
    assert rep["pack_id"].startswith("wsc_pack_")

    after = store.get_fact_durable("kb.authority.legacy")
    assert after is not None
    assert after["claim_type"] == "WORLD_FACT"
    assert after["origin_type"] == "EXTERNAL"
    with store._db() as conn:
        after_version_count = int(conn.execute(
            "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?",
            ("kb.authority.legacy",),
        ).fetchone()[0])
    assert after_version_count == before_version_count + 1
    assert store.get_fact("kb.authority.legacy")["claim_type"] == "WORLD_FACT"


def test_fast_fresh_rejects_nonempty_database_before_build(tmp_path):
    from core.memory import SQLiteGraphStore
    from scripts.build_kb_graph import ingest_kb_facts

    store = SQLiteGraphStore(db_path=str(tmp_path / "kb.db"))
    assert store.store_fact({
        "fact_id": "already.there",
        "claim": "Already present durable record",
        "source": "test",
        "confidence": 0.7,
    })

    with pytest.raises(RuntimeError, match="requires an empty KB database"):
        ingest_kb_facts(store, [_fact("kb.authority.new")], require_empty=True)
    assert store.get_fact_durable("kb.authority.new") is None


def test_evidence_failure_never_yields_accepted_smart_kb(tmp_path, monkeypatch):
    from core.audit_chain import AuditChain
    from core.memory import SQLiteGraphStore
    from scripts.build_kb_graph import ingest_kb_facts

    store = SQLiteGraphStore(db_path=str(tmp_path / "kb.db"))

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("forced audit failure")

    monkeypatch.setattr(AuditChain, "log_in_transaction", fail_audit)
    with pytest.raises(RuntimeError, match="canonical smart-KB ingest incomplete"):
        ingest_kb_facts(store, [_fact("kb.authority.rollback")], batch_size=1, require_empty=True)

    durable = store.get_fact_durable("kb.authority.rollback")
    assert durable is None or durable["epistemic_state"] != "Validated"
