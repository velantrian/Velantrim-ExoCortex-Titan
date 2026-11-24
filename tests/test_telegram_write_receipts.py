"""Telegram acknowledgements require an accepted durable canonical result."""
from concurrent.futures import ThreadPoolExecutor

import pytest



@pytest.fixture(params=[False, True])
def store(tmp_path, monkeypatch, request):
    from core import memory
    from core.feature_config import clear_config_cache
    from core.memory import SQLiteGraphStore
    instance = SQLiteGraphStore(str(tmp_path / "telegram.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE", instance)
    monkeypatch.setattr(memory, "_L0", instance._l0)
    monkeypatch.setenv("ENABLE_COGNITIVE_STORE", "1" if request.param else "0")
    clear_config_cache()
    yield instance
    clear_config_cache()
    instance.close()


def test_rejected_write_is_not_acknowledged(store, monkeypatch):
    from app.telegram_ingest import ingest_telegram_message
    monkeypatch.setattr("core.write_gate.admit_fact", lambda **kwargs: (False, "synthetic_gate_denial"))
    result = ingest_telegram_message("A normal Telegram message", chat_id=17, message_id=0)
    assert result["ok"] is False
    assert result["write_status"] == "rejected_write_gate"
    assert not result["durable_write"]
    assert store.get_fact(result["fact_id"]) is None


def test_repeat_returns_first_fact_and_conflicting_edit_cannot_overwrite(store):
    from app.telegram_ingest import ingest_telegram_message
    first = ingest_telegram_message("First delivered message", chat_id=17, message_id=0)
    repeat = ingest_telegram_message("First delivered message", chat_id=17, message_id=0)
    assert first["ok"] and repeat["ok"] and repeat["deduplicated_delivery"]
    assert first["fact_id"] == repeat["fact_id"] == "tg_17_0"
    before = store._get_fact_durable(first["fact_id"])
    conflict = ingest_telegram_message("Edited payload under the same delivery", chat_id=17, message_id=0)
    assert not conflict["ok"] and conflict["reason_code"] == "telegram_delivery_conflict"
    assert store._get_fact_durable(first["fact_id"]) == before
    assert len(store.get_all_facts()) == 1


def test_parallel_retries_cannot_create_duplicate_facts_or_raw(store):
    from app.telegram_ingest import ingest_telegram_message
    def deliver(index):
        return ingest_telegram_message("Concurrent same Telegram delivery", chat_id=42, message_id=3)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(deliver, range(8)))
    assert all(result["ok"] for result in results)
    assert len({result["fact_id"] for result in results}) == 1
    with store._db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM l0_raw_memory").fetchone()[0] == 1


def test_atomic_create_only_preserves_first_writer_even_for_conflicting_payloads(tmp_path):
    from core.memory import SQLiteGraphStore
    from core.write_result import WriteStatus
    stores = [SQLiteGraphStore(str(tmp_path / "first-writer.db")) for _ in range(2)]
    try:
        def write(index):
            return stores[index].store_fact_result({"fact_id": "delivery", "claim": f"payload {index}", "source": "manual"}, create_only=True)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(write, [0, 1]))
        assert sorted(result.status.value for result in results) == ["created", "noop_existing"]
        winner = next(i for i, result in enumerate(results) if result.status is WriteStatus.CREATED)
        fact = stores[0]._get_fact_durable("delivery")
        assert fact["claim"] == f"payload {winner}"
        assert sum(result.durable_write for result in results) == 1
    finally:
        for store in stores:
            store.close()


def test_retry_does_not_emit_a_second_fact_event(store, monkeypatch):
    from app.telegram_ingest import ingest_telegram_message
    from core import cognitive_store
    events = []
    monkeypatch.setattr(cognitive_store, "_emit_fact_event", lambda *a, **k: events.append((a, k)))
    first = ingest_telegram_message("One delivery creates one event", chat_id=54, message_id=9)
    repeat = ingest_telegram_message("One delivery creates one event", chat_id=54, message_id=9)
    assert first["ok"] and repeat["deduplicated_delivery"]
    assert len(events) == (1 if cognitive_store.is_cognitive_store_enabled() else 0)
    assert first["deduplicated_raw"] is repeat["deduplicated_raw"] is None
