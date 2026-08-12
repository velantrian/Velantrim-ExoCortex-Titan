from __future__ import annotations

import pytest


@pytest.fixture
def store(tmp_path):
    from core.memory import make_store

    value = make_store(str(tmp_path / "initial-provenance.db"))
    value.ensure_schema()
    yield value
    value.close()


def _current_write_status(name: str):
    # Resolve lazily because the full suite exercises core import isolation and may
    # replace module objects after collection. Identity remains strict against the
    # WriteStatus class that the store is currently using.
    from core.write_result import WriteStatus

    return getattr(WriteStatus, name)


def _provenance_count(store, fact_id: str) -> int:
    with store._db() as conn:
        return int(
            conn.execute(
                "SELECT COUNT(*) FROM l0_fact_provenance WHERE fact_id = ?",
                (fact_id,),
            ).fetchone()[0]
        )


def _fact_version_count(store, fact_id: str) -> int:
    with store._db() as conn:
        return int(
            conn.execute(
                "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?",
                (fact_id,),
            ).fetchone()[0]
        )


def _fact_payload(fact_id: str, **extra):
    payload = {
        "fact_id": fact_id,
        "claim": f"claim for {fact_id}",
        "source": "test",
        "confidence": 0.8,
    }
    payload.update(extra)
    return payload


def test_direct_create_raw_binding_is_parent_transaction_evidence(store):
    raw_id = store.store_raw_text("direct raw", source="test")
    result = store.store_fact_result(
        _fact_payload("fact_initial_raw", derived_from=raw_id)
    )

    assert result.status is _current_write_status("CREATED")
    assert store.get_fact_durable("fact_initial_raw")["derived_from"] == raw_id
    assert _provenance_count(store, "fact_initial_raw") == 1
    # Brand-new Canon has no predecessor, therefore no VersionStore pre-image.
    assert _fact_version_count(store, "fact_initial_raw") == 0


def test_direct_create_audit_failure_rolls_back_fact_and_provenance(store, monkeypatch):
    from core.audit_chain import AuditChain

    raw_id = store.store_raw_text("rollback raw", source="test")

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("forced create audit failure")

    monkeypatch.setattr(AuditChain, "log_in_transaction", fail_audit)
    result = store.store_fact_result(
        _fact_payload("fact_initial_rollback", derived_from=raw_id)
    )

    assert result.status is _current_write_status("FAILED_INTERNAL")
    assert store.get_fact_durable("fact_initial_rollback") is None
    assert _provenance_count(store, "fact_initial_rollback") == 0


def test_missing_raw_namespace_pointer_fails_closed(store):
    result = store.store_fact_result(
        _fact_payload("fact_missing_raw", derived_from="raw_missing_parent")
    )

    assert result.status is _current_write_status("REJECTED_VALIDATION")
    assert store.get_fact_durable("fact_missing_raw") is None
    assert _provenance_count(store, "fact_missing_raw") == 0


def test_fact_to_fact_lineage_is_preserved_without_l0_provenance(store):
    result = store.store_fact_result(
        _fact_payload("gist_1", derived_from="verb_1")
    )

    assert result.status is _current_write_status("CREATED")
    assert store.get_fact_durable("gist_1")["derived_from"] == "verb_1"
    assert _provenance_count(store, "gist_1") == 0


def test_existing_fact_cannot_rebind_through_generic_upsert_or_poison_l0(store):
    raw_1 = store.store_raw_text("first raw", source="test")
    raw_2 = store.store_raw_text("second raw", source="test")
    assert store.store_fact(
        _fact_payload("fact_no_rebind", derived_from=raw_1)
    )

    result = store.store_fact_result(
        _fact_payload(
            "fact_no_rebind",
            confidence=0.81,
            derived_from=raw_2,
        )
    )

    assert result.status is _current_write_status("UPDATED")
    assert store.get_fact_durable("fact_no_rebind")["derived_from"] == raw_1
    assert store.get_fact("fact_no_rebind")["derived_from"] == raw_1
    assert _provenance_count(store, "fact_no_rebind") == 1


def test_supersede_create_raw_binding_is_parent_transaction_evidence(store):
    assert store.store_fact(_fact_payload("fact_supersede_old"))
    old = store.get_fact_durable("fact_supersede_old")
    assert old is not None
    raw_id = store.store_raw_text("supersede raw", source="test")

    result = store.supersede_fact_cas(
        "fact_supersede_old",
        "fact_supersede_new",
        _fact_payload("fact_supersede_new", derived_from=raw_id),
        expected_old_state=old["epistemic_state"],
        expected_old_updated_at=old["updated_at"],
        old_durable_snapshot=old,
    )

    assert result.committed is True
    assert store.get_fact_durable("fact_supersede_new")["derived_from"] == raw_id
    assert _provenance_count(store, "fact_supersede_new") == 1


def test_batch_create_raw_binding_is_parent_transaction_evidence(store):
    raw_id = store.store_raw_text("batch raw", source="test")
    stats = store.store_facts_batch(
        [
            _fact_payload("fact_batch_raw_1", derived_from=raw_id),
            _fact_payload("fact_batch_raw_2", derived_from=raw_id),
        ]
    )

    assert stats["stored"] == 2
    for fact_id in ("fact_batch_raw_1", "fact_batch_raw_2"):
        assert store.get_fact_durable(fact_id)["derived_from"] == raw_id
        assert _provenance_count(store, fact_id) == 1
        assert _fact_version_count(store, fact_id) == 0


def test_batch_fact_lineage_survives_without_l0_provenance(store):
    stats = store.store_facts_batch(
        [_fact_payload("gist_batch", derived_from="verb_batch")]
    )

    assert stats["stored"] == 1
    assert store.get_fact_durable("gist_batch")["derived_from"] == "verb_batch"
    assert _provenance_count(store, "gist_batch") == 0


def test_batch_audit_failure_rolls_back_fact_and_raw_provenance(store, monkeypatch):
    from core.audit_chain import AuditChain

    raw_id = store.store_raw_text("batch rollback raw", source="test")

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("forced batch audit failure")

    monkeypatch.setattr(AuditChain, "log_in_transaction", fail_audit)
    with pytest.raises(RuntimeError, match="forced batch audit failure"):
        store.store_facts_batch(
            [_fact_payload("fact_batch_rollback", derived_from=raw_id)]
        )

    assert store.get_fact_durable("fact_batch_rollback") is None
    assert _provenance_count(store, "fact_batch_rollback") == 0
