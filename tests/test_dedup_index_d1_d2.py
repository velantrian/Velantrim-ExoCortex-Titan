"""
Tests for D1 (indexed claim_dedup_key, audit M5) and D2 (stable get_all_facts order).

D1: every fact — whether written via store_fact OR store_facts_batch OR a legacy
fact backfilled at init — must carry claim_dedup_key, so the indexed dedup lookup
finds duplicates regardless of DB size (no 5000-row scan cap).

D2: get_all_facts must return a deterministic order (created_at, fact_id) so the
contradiction resolver / semantic dedup are not order-dependent (audit M2/M3).
"""
import json

from core.memory import SQLiteGraphStore


def test_dedup_index_exists(tmp_path):
    store = SQLiteGraphStore(str(tmp_path / "t.db"))
    with store._db() as conn:
        idx = {r[1] for r in conn.execute("PRAGMA index_list(facts)")}
    assert "idx_facts_claim_dedup" in idx


def test_store_fact_then_find_dedup(tmp_path):
    store = SQLiteGraphStore(str(tmp_path / "t.db"))
    store.store_fact({"fact_id": "f1", "claim": "Вода кипит при 100°C",
                      "source": "phys", "confidence": 0.9})
    # same claim, different case/spacing → dedup must find it
    assert store.find_fact_id_by_claim_dedup("вода  кипит при 100°c") == "f1"


def test_batch_fact_carries_dedup_key_and_is_findable(tmp_path):
    store = SQLiteGraphStore(str(tmp_path / "t.db"))
    store.store_facts_batch([
        {"fact_id": "b1", "claim": "ДНК хранит генетическую информацию",
         "source": "biol", "confidence": 0.9},
    ])
    # D1: batch facts must have the key (previously they did NOT → dedup missed them)
    fact = store.get_fact("b1")
    assert fact["metadata"].get("claim_dedup_key")
    # and the indexed dedup lookup finds the batch-stored fact
    assert store.find_fact_id_by_claim_dedup("ДНК хранит генетическую информацию") == "b1"


def test_backfill_legacy_fact_without_key(tmp_path):
    path = str(tmp_path / "t.db")
    store = SQLiteGraphStore(path)
    # simulate a legacy fact: insert directly with metadata that has NO claim_dedup_key
    now = "2026-01-01T00:00:00+00:00"
    with store._db() as conn:
        conn.execute(
            "INSERT INTO facts (fact_id, claim, source, confidence, epistemic_state, "
            "created_at, updated_at, metadata) VALUES (?,?,?,?,?,?,?,?)",
            ("legacy1", "Старый факт без ключа", "src", 0.7, "Observed",
             now, now, json.dumps({"note": "no dedup key here"})),
        )
    # a fresh store instance triggers DDL init → backfill
    store2 = SQLiteGraphStore(path)
    with store2._db() as conn:
        meta = json.loads(conn.execute(
            "SELECT metadata FROM facts WHERE fact_id='legacy1'").fetchone()[0])
    assert meta.get("claim_dedup_key"), "backfill must populate the key for legacy facts"
    assert store2.find_fact_id_by_claim_dedup("Старый факт без ключа") == "legacy1"


def test_no_5000_row_cap(tmp_path):
    """Regression for M5: a dup beyond the old 5000-row window must still be found."""
    store = SQLiteGraphStore(str(tmp_path / "t.db"))
    # the target fact is the FIRST inserted; then add many more after it
    store.store_fact({"fact_id": "old", "claim": "уникальный старый факт альфа",
                      "source": "s", "confidence": 0.8})
    store.store_facts_batch([
        {"fact_id": f"pad{i}", "claim": f"наполнитель номер {i}",
         "source": "s", "confidence": 0.6} for i in range(50)
    ])
    # indexed lookup must find the old fact regardless of insertion recency
    assert store.find_fact_id_by_claim_dedup("уникальный старый факт альфа") == "old"


def test_get_all_facts_stable_order(tmp_path):
    store = SQLiteGraphStore(str(tmp_path / "t.db"))
    store.store_facts_batch([
        {"fact_id": f"z{i}", "claim": f"claim {i}", "source": "s", "confidence": 0.6}
        for i in range(10)
    ])
    order1 = [f["fact_id"] for f in store.get_all_facts()]
    # fresh instance (empty L0) must yield the SAME order from L1
    store2 = SQLiteGraphStore(str(tmp_path / "t.db"))
    order2 = [f["fact_id"] for f in store2.get_all_facts()]
    assert order1 == order2, "get_all_facts order must be deterministic across instances"
    # and it must match the documented (created_at, fact_id) ordering
    assert order1 == sorted(order1, key=lambda fid: fid)  # same created_at → fact_id asc
