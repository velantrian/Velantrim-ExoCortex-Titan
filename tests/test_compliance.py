"""GDPR Art. 18 restriction of processing + Art. 30 record-of-processing."""
import json

import pytest

from core import memory
from core.memory import make_store, store_fact, get_facts_by_ids
from core import compliance, erasure


@pytest.fixture
def store(tmp_path, monkeypatch):
    """erasure.erase_fact() delegates to core.erasure_coordinator.get_coordinator(),
    which builds a fresh ErasureCoordinator from `memory._GLOBAL_STORE` on
    every call (see erasure_coordinator.py) — patching it here is enough for
    facts-layer isolation. embeddings/ngram default paths are redirected away
    from ./data/*.db for the whole session by tests/conftest.py.
    """
    st = make_store(str(tmp_path / "comp.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE", st)
    monkeypatch.setattr(memory, "_L0", st._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", st._ddl_initialized_paths)
    return st


def _fact(fid, claim="some neutral claim"):
    return {"fact_id": fid, "claim": claim, "source": "test", "confidence": 0.9}


def test_restrict_excludes_from_recall_but_keeps_fact(store):
    store_fact(_fact("r1"))
    assert any(f["fact_id"] == "r1" for f in get_facts_by_ids(["r1"]))  # recalled

    res = compliance.restrict_processing("r1", reason="dsr")
    assert res["found"] is True and res["restricted"] is True
    assert compliance.is_restricted("r1") is True

    # Art. 18: excluded from recall, but still stored (not deleted).
    assert get_facts_by_ids(["r1"]) == []
    assert memory.get_fact("r1") is not None


def test_unrestrict_restores_recall(store):
    store_fact(_fact("r2"))
    compliance.restrict_processing("r2")
    assert get_facts_by_ids(["r2"]) == []

    compliance.unrestrict_processing("r2")
    assert compliance.is_restricted("r2") is False
    assert any(f["fact_id"] == "r2" for f in get_facts_by_ids(["r2"]))


def test_restrict_missing_fact_reports_not_found(store):
    assert compliance.restrict_processing("nope")["found"] is False


def test_restricted_facts_list(store):
    for fid in ("a", "b", "c"):
        store_fact(_fact(fid))
    compliance.restrict_processing("b")
    assert compliance.restricted_facts() == ["b"]


def test_record_of_processing_is_content_free(store):
    store_fact(_fact("x", claim="secret personal data here"))
    store_fact(_fact("e1"))
    compliance.restrict_processing("x")
    erasure.erase_fact("e1")  # produces a tombstone (Art. 30 erasure record)

    ropa = compliance.record_of_processing(controller="Acme EU")

    assert ropa["regulation"].startswith("GDPR")
    assert ropa["controller"] == "Acme EU"
    assert ropa["restricted_count"] == 1 and "x" in ropa["restricted_fact_ids"]
    assert ropa["erasure_count"] >= 1
    # No personal data (claim text) leaks into the RoPA.
    assert "secret personal data here" not in json.dumps(ropa)


# ── Round 5.3 Codex finding (P2): unified correction-aware audit readers ───
# record_of_processing() calls core.memory.get_tombstones() directly — the
# same reader ErasureCoordinator.erasure_log() uses. Before this fix, that
# raw read bypassed erasure_log_subject_corrections entirely, so a
# corrected batch-erasure subject (see migrations/016) was invisible to the
# Art. 30 record even though get_erasure_log()/erasure_audit reported it
# correctly — the two "same audit" surfaces disagreed.

def test_record_of_processing_reports_corrected_subject(store):
    import sqlite3

    store_fact(_fact("e2"))
    erasure.erase_fact("e2", actor="api:deadbeef")

    with sqlite3.connect(store.db_path) as conn:
        erasure_id = conn.execute(
            "SELECT erasure_id FROM erasure_log WHERE fact_id = 'e2'"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO erasure_log_subject_corrections "
            "(correction_id, erasure_id, job_id, batch_id, corrected_user_id, "
            "original_user_id, created_at) "
            "VALUES ('c_ropa', ?, NULL, 'b_ropa', 'realUserA', 'api:deadbeef', "
            "datetime('now'))",
            (erasure_id,),
        )
        conn.commit()

    ropa = compliance.record_of_processing()
    subjects = {row["user_id"] for row in ropa["erasure_log"]}
    assert "realUserA" in subjects
    assert "api:deadbeef" not in subjects
