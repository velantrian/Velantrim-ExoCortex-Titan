"""Issue #50 — executable invariants for the canonical write boundary.

These tests intentionally inspect all three durable artifacts:

    facts mutation + fact_versions pre-image + memory_events audit append

The first P0 slice is correct only when those artifacts commit together or
roll back together. A false audit/version row for a rejected write is just as
incorrect as an unlogged canonical mutation.
"""

from __future__ import annotations

import sqlite3

import pytest


@pytest.fixture
def store(tmp_path):
    from core.memory import SQLiteGraphStore

    instance = SQLiteGraphStore(str(tmp_path / "canonical-write.db"))
    instance.ensure_schema()
    yield instance
    instance.close()


def _counts(store, fact_id: str) -> tuple[int, int]:
    with store._db() as conn:
        versions = conn.execute(
            "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()[0]
        subject = conn.execute(
            "SELECT audit_subject_id FROM facts WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()
        if subject is None or subject[0] is None:
            events = 0
        else:
            events = conn.execute(
                "SELECT COUNT(*) FROM memory_events WHERE chain_id = ?",
                (f"fact-transition:{subject[0]}",),
            ).fetchone()[0]
    return int(versions), int(events)


def _install_abort_trigger(store, *, table: str, name: str) -> None:
    allowed = {"fact_versions", "memory_events"}
    if table not in allowed:
        raise AssertionError(f"unsafe test table: {table}")
    with store._db() as conn:
        conn.execute(
            f"""
            CREATE TRIGGER {name}
            BEFORE INSERT ON {table}
            BEGIN
                SELECT RAISE(ABORT, 'forced evidence failure');
            END
            """
        )


def test_transactional_snapshot_rejects_standalone_use(tmp_path):
    from core.version_store import VersionStore

    db_path = str(tmp_path / "version-only.db")
    VersionStore(db_path)
    conn = sqlite3.connect(db_path)
    try:
        with pytest.raises(RuntimeError, match="active caller-owned"):
            VersionStore.snapshot_before_change_in_transaction(
                conn,
                "f1",
                {"fact_id": "f1", "claim": "before"},
                caused_by="test",
            )
    finally:
        conn.close()


def test_version_failure_rolls_back_store_fact_update_and_audit(store):
    from core.write_result import WriteStatus

    fact_id = "version_rollback"
    assert store.store_fact({
        "fact_id": fact_id,
        "claim": "before",
        "source": "test",
        "confidence": 0.5,
    }) is True
    assert _counts(store, fact_id) == (0, 1)

    _install_abort_trigger(
        store,
        table="fact_versions",
        name="test_abort_fact_versions_insert",
    )
    result = store.store_fact_result({
        "fact_id": fact_id,
        "claim": "after",
        "source": "test",
        "confidence": 0.5,
    })

    assert result.status is WriteStatus.FAILED_STORAGE
    assert store.get_fact_durable(fact_id)["claim"] == "before"
    assert _counts(store, fact_id) == (0, 1)


def test_audit_failure_rolls_back_canonical_update_and_version(store):
    from core.write_result import WriteStatus

    fact_id = "audit_rollback"
    store.store_fact({
        "fact_id": fact_id,
        "claim": "before",
        "source": "test",
        "confidence": 0.5,
    })
    assert _counts(store, fact_id) == (0, 1)

    _install_abort_trigger(
        store,
        table="memory_events",
        name="test_abort_memory_events_insert",
    )
    result = store.store_fact_result({
        "fact_id": fact_id,
        "claim": "after",
        "source": "test",
        "confidence": 0.5,
    })

    assert result.status is WriteStatus.FAILED_STORAGE
    assert store.get_fact_durable(fact_id)["claim"] == "before"
    assert _counts(store, fact_id) == (0, 1)


def test_transition_version_failure_rolls_back_state_history_and_audit(store):
    fact_id = "transition_rollback"
    store.store_fact({
        "fact_id": fact_id,
        "claim": "claim",
        "source": "test",
        "confidence": 0.5,
    })
    assert _counts(store, fact_id) == (0, 1)

    _install_abort_trigger(
        store,
        table="fact_versions",
        name="test_abort_transition_version",
    )
    with pytest.raises(sqlite3.IntegrityError, match="forced evidence failure"):
        store.transition_esm(fact_id, "Hypothesized", by="test")

    fact = store.get_fact_durable(fact_id)
    assert fact["epistemic_state"] == "Observed"
    assert fact["history"] == []
    assert _counts(store, fact_id) == (0, 1)


def test_batch_updates_append_one_preimage_per_fact_in_same_transaction(store):
    for fact_id in ("batch_a", "batch_b"):
        store.store_fact({
            "fact_id": fact_id,
            "claim": "before",
            "source": "test",
            "confidence": 0.5,
        })

    stats = store.store_facts_batch([
        {
            "fact_id": "batch_a",
            "claim": "after A",
            "source": "test",
            "confidence": 0.5,
        },
        {
            "fact_id": "batch_b",
            "claim": "after B",
            "source": "test",
            "confidence": 0.5,
        },
    ])

    assert stats == {"stored": 0, "updated": 2, "drift": 0, "errors": 0}
    assert store.get_fact_durable("batch_a")["claim"] == "after A"
    assert store.get_fact_durable("batch_b")["claim"] == "after B"
    assert _counts(store, "batch_a") == (1, 2)
    assert _counts(store, "batch_b") == (1, 2)


def test_batch_version_failure_rolls_back_every_record_and_audit(store):
    for fact_id in ("batch_fail_a", "batch_fail_b"):
        store.store_fact({
            "fact_id": fact_id,
            "claim": "before",
            "source": "test",
            "confidence": 0.5,
        })

    _install_abort_trigger(
        store,
        table="fact_versions",
        name="test_abort_batch_version",
    )
    with pytest.raises(sqlite3.IntegrityError, match="forced evidence failure"):
        store.store_facts_batch([
            {
                "fact_id": "batch_fail_a",
                "claim": "after A",
                "source": "test",
                "confidence": 0.5,
            },
            {
                "fact_id": "batch_fail_b",
                "claim": "after B",
                "source": "test",
                "confidence": 0.5,
            },
        ])

    for fact_id in ("batch_fail_a", "batch_fail_b"):
        assert store.get_fact_durable(fact_id)["claim"] == "before"
        assert _counts(store, fact_id) == (0, 1)


def test_batch_cannot_bypass_write_protocol_gate(store, monkeypatch):
    import core.write_gate as write_gate

    monkeypatch.setattr(write_gate, "is_write_gate_enabled", lambda: True)
    stats = store.store_facts_batch([
        {
            "fact_id": "unproven_world_fact",
            "claim": "An unproven external assertion",
            "source": "unknown",
            "claim_type": "WORLD_FACT",
            "origin_type": "EXTERNAL",
        }
    ])

    assert stats == {"stored": 0, "updated": 0, "drift": 0, "errors": 1}
    assert store.get_fact_durable("unproven_world_fact") is None


def test_restriction_is_versioned_audited_and_idempotent(store):
    fact_id = "restricted_fact"
    store.store_fact({
        "fact_id": fact_id,
        "claim": "personal data",
        "source": "user",
        "confidence": 0.9,
    })

    assert store.set_restricted(fact_id, True) is True
    assert bool(store.get_fact_durable(fact_id)["metadata"]["restricted"]) is True
    assert _counts(store, fact_id) == (1, 2)

    # Repeating the policy state is a proven no-op: no false evidence.
    assert store.set_restricted(fact_id, True) is True
    assert _counts(store, fact_id) == (1, 2)

    assert store.set_restricted(fact_id, False) is True
    assert "restricted" not in store.get_fact_durable(fact_id)["metadata"]
    assert _counts(store, fact_id) == (2, 3)
