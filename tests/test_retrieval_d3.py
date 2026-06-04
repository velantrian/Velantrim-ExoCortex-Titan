"""
Test for D3 (retrieval scale fix): when FTS5/NGram returns candidate fact_ids,
retrieval must use them DIRECTLY — not intersect with get_fact_ids(limit=1000).

Old bug: `all_ids = get_fact_ids(limit=1000)` (ORDER BY updated_at DESC) then
`[fid for fid in all_ids if fid in candidate_ids]` — a relevant candidate older
than the 1000 newest facts was silently dropped at scale.
"""
import core.memory as mem
import core.pipeline as pipeline
from core.memory import SQLiteGraphStore


class _StubNGram:
    """Fake FTS5 index that returns a fixed candidate set."""
    available = True

    def __init__(self, ids):
        self._ids = list(ids)

    def query(self, q, limit=50):
        return list(self._ids)


def test_d3_ngram_candidate_used_directly_beyond_cap(tmp_path, monkeypatch):
    store = SQLiteGraphStore(str(tmp_path / "t.db"))
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)

    # target stored FIRST → oldest by updated_at
    store.store_fact({"fact_id": "target", "claim": "редкий уникальный термин квазар",
                      "source": "s", "confidence": 0.9})
    # 1100 newer padding facts → target falls outside the newest-1000 window
    store.store_facts_batch([
        {"fact_id": f"pad{i}", "claim": f"наполнитель номер {i}",
         "source": "s", "confidence": 0.6} for i in range(1100)
    ])

    # FTS5 finds the target; retrieval must fetch it directly (not via capped all_ids)
    monkeypatch.setattr(pipeline, "_NGRAM_INDEX", _StubNGram(["target"]))

    res = pipeline._retrieve_from_store("редкий уникальный термин квазар", k=3)
    ids = [r.get("id") or r.get("fact_id") for r in res]
    assert "target" in ids, "D3: FTS5 candidate must be retrieved regardless of the 1000-cap"


def test_d3_empty_ngram_falls_back_bounded(tmp_path, monkeypatch):
    """No FTS5 candidates → bounded fallback (not a crash, not a full scan)."""
    store = SQLiteGraphStore(str(tmp_path / "t.db"))
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
    store.store_fact({"fact_id": "f1", "claim": "вода замерзает при ноль градусов",
                      "source": "s", "confidence": 0.9})
    monkeypatch.setattr(pipeline, "_NGRAM_INDEX", _StubNGram([]))  # FTS5 returns nothing

    res = pipeline._retrieve_from_store("вода замерзает", k=3)
    ids = [r.get("id") or r.get("fact_id") for r in res]
    assert "f1" in ids  # bounded fallback still finds it in a small store
