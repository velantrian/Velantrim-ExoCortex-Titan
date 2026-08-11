from __future__ import annotations

import inspect
import sqlite3

import pytest


def _counts(store, fact_id: str) -> dict[str, int]:
    with store._db() as conn:
        def count(sql: str, params: tuple = ()) -> int:
            return int(conn.execute(sql, params).fetchone()[0])

        audit_table_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='memory_events'"
        ).fetchone()
        audit_count = (
            count(
                "SELECT COUNT(*) FROM memory_events WHERE actor = ?",
                ("memory_link_raw_to_fact",),
            )
            if audit_table_exists is not None
            else 0
        )

        return {
            "provenance": count(
                "SELECT COUNT(*) FROM l0_fact_provenance WHERE fact_id = ?",
                (fact_id,),
            ),
            "versions": count(
                "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?",
                (fact_id,),
            ),
            "audit": audit_count,
        }


@pytest.fixture
def store(tmp_path):
    from core.memory import make_store

    value = make_store(str(tmp_path / "provenance.db"))
    value.ensure_schema()
    yield value
    value.close()


def _seed(store, *, fact_id: str = "fact_prov_1", text: str = "raw source") -> tuple[str, str]:
    raw_id = store.store_raw_text(text, source="test", source_type="user_input")
    assert store.store_fact(
        {
            "fact_id": fact_id,
            "claim": "bounded provenance claim",
            "source": "test",
            "confidence": 0.8,
        }
    )
    return raw_id, fact_id


def test_first_binding_is_atomic_versioned_and_audited(store):
    raw_id, fact_id = _seed(store)
    before = _counts(store, fact_id)

    assert store.link_raw_to_fact(raw_id, fact_id) is True

    fact = store.get_fact_durable(fact_id)
    after = _counts(store, fact_id)
    assert fact is not None
    assert fact["derived_from"] == raw_id
    assert after["provenance"] == before["provenance"] + 1
    assert after["versions"] == before["versions"] + 1
    assert after["audit"] == before["audit"] + 1


def test_version_failure_rolls_back_canon_provenance_and_evidence(store, monkeypatch):
    raw_id, fact_id = _seed(store, fact_id="fact_prov_version_fail")
    before = _counts(store, fact_id)

    def fail_version(*_args, **_kwargs):
        raise RuntimeError("forced version failure")

    monkeypatch.setattr(store, "_snapshot_before_change_in_transaction", fail_version)
    with pytest.raises(RuntimeError, match="forced version failure"):
        store.link_raw_to_fact(raw_id, fact_id)

    assert store.get_fact_durable(fact_id)["derived_from"] is None
    assert _counts(store, fact_id) == before


def test_audit_failure_rolls_back_canon_provenance_and_version(store, monkeypatch):
    from core.audit_chain import AuditChain

    raw_id, fact_id = _seed(store, fact_id="fact_prov_audit_fail")
    before = _counts(store, fact_id)

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("forced audit failure")

    monkeypatch.setattr(AuditChain, "log_in_transaction", fail_audit)
    with pytest.raises(RuntimeError, match="forced audit failure"):
        store.link_raw_to_fact(raw_id, fact_id)

    assert store.get_fact_durable(fact_id)["derived_from"] is None
    assert _counts(store, fact_id) == before


def test_same_binding_retry_is_true_noop(store):
    raw_id, fact_id = _seed(store, fact_id="fact_prov_retry")
    assert store.link_raw_to_fact(raw_id, fact_id) is True
    after_first = _counts(store, fact_id)

    assert store.link_raw_to_fact(raw_id, fact_id) is True
    assert _counts(store, fact_id) == after_first


def test_conflicting_second_raw_fails_closed_without_false_evidence(store):
    raw_id, fact_id = _seed(store, fact_id="fact_prov_conflict", text="first raw")
    other_raw = store.store_raw_text("second raw", source="test", source_type="user_input")
    assert store.link_raw_to_fact(raw_id, fact_id) is True
    before = _counts(store, fact_id)

    assert store.link_raw_to_fact(other_raw, fact_id) is False

    assert store.get_fact_durable(fact_id)["derived_from"] == raw_id
    assert _counts(store, fact_id) == before
    with store._db() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM l0_fact_provenance WHERE raw_id = ? AND fact_id = ?",
            (other_raw, fact_id),
        ).fetchone()[0] == 0


def test_missing_raw_or_fact_is_true_noop(store):
    raw_id, fact_id = _seed(store, fact_id="fact_prov_missing")
    before = _counts(store, fact_id)

    assert store.link_raw_to_fact("raw_missing", fact_id) is False
    assert store.link_raw_to_fact(raw_id, "fact_missing") is False
    assert store.get_fact_durable(fact_id)["derived_from"] is None
    assert _counts(store, fact_id) == before


def test_legacy_raw_memory_has_no_independent_canonical_update():
    from core.raw_memory import RawMemoryStore

    src = inspect.getsource(RawMemoryStore.link_fact)
    assert "UPDATE facts SET derived_from" not in src
    assert ".link_raw_to_fact(" in src


def test_legacy_file_backed_adapter_uses_canonical_owner(store):
    from core.raw_memory import RawMemoryStore

    raw_id, fact_id = _seed(store, fact_id="fact_prov_legacy")
    conn = sqlite3.connect(store.db_path)
    try:
        legacy = RawMemoryStore(conn)
        legacy.link_fact(raw_id, fact_id)
    finally:
        conn.close()

    fact = store.get_fact_durable(fact_id)
    assert fact is not None
    assert fact["derived_from"] == raw_id
    counts = _counts(store, fact_id)
    assert counts["provenance"] == 1
    assert counts["versions"] == 1
    assert counts["audit"] >= 1
