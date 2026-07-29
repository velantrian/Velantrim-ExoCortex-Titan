"""
🧪 tests/test_recall_policy_server.py — Real security tests for RecallPolicy
integration at the server/component layer (P0-1 Fix, PR #23).

Заменяет фиктивные "/health" тесты из tests/test_recall_policy_integration.py.
Каждый тест здесь создаёт controlled unrestricted + restricted facts с
уникальными маркерами и проверяет, что restricted marker не попадает в
конечный output реального пути: console fallback functions, /chat,
/chat/stream, BranchManager retrieval corpus.

Никакие тесты в этом файле не обращаются к внешним LLM API — llm_enabled=False
везде, где применимо.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ALLOW_MARKER = "ALLOW_MARKER_f3a9c2"
RESTRICTED_MARKER = "RESTRICTED_MARKER_b71de0"
COLLAPSED_MARKER = "COLLAPSED_MARKER_9c14aa"
DEPRECATED_MARKER = "DEPRECATED_MARKER_2d88e1"


def _fake_fact(fact_id: str, claim: str, **overrides) -> dict:
    fact = {
        "fact_id": fact_id,
        "claim": claim,
        "source": "test",
        "confidence": 0.9,
        "epistemic_state": "Validated",
        "metadata": {},
    }
    fact.update(overrides)
    return fact


@pytest.fixture
def imported_server(tmp_path, monkeypatch):
    """Import server.py with the env vars its module-level guard requires,
    without booting a full TestClient (used by the plain-function tests)."""
    monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
    monkeypatch.setenv("VELANTRIM_DB_PATH", str(tmp_path / "unit.db"))
    monkeypatch.setenv("VELANTRIM_NGRAM_DB", str(tmp_path / "unit_ngram.db"))
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")

    for mod in list(sys.modules.keys()):
        if mod.startswith(("server", "core.")):
            del sys.modules[mod]

    import server as srv

    return srv


# ─── _console_all_memory() ─────────────────────────────────────────────────────

class TestConsoleAllMemory:
    def test_excludes_restricted_collapsed_deprecated(self, imported_server, monkeypatch):
        server = imported_server

        facts = [
            _fake_fact("f_allow", ALLOW_MARKER),
            _fake_fact("f_restricted", RESTRICTED_MARKER, metadata={"restricted": "2026-07-12T10:00:00Z"}),
            _fake_fact("f_collapsed", COLLAPSED_MARKER, epistemic_state="Collapsed"),
            _fake_fact("f_deprecated", DEPRECATED_MARKER, epistemic_state="Deprecated"),
        ]

        monkeypatch.setattr("core.memory.get_all_facts", lambda: facts)

        result = server._console_all_memory()
        claims = [f["claim"] for f in result]

        assert ALLOW_MARKER in claims
        assert RESTRICTED_MARKER not in claims
        assert COLLAPSED_MARKER not in claims
        assert DEPRECATED_MARKER not in claims


# ─── _console_observed_memory_fallback() ───────────────────────────────────────

class TestConsoleObservedMemoryFallback:
    def test_excludes_restricted_and_malformed(self, imported_server, monkeypatch):
        server = imported_server

        facts = [
            _fake_fact("f_allow", ALLOW_MARKER),
            _fake_fact("f_restricted", RESTRICTED_MARKER, metadata={"restricted": True}),
            {"fact_id": "f_malformed", "claim": "malformed marker", "metadata": {}},  # missing epistemic_state
        ]

        call_count = {"n": 0}

        def fake_retrieve(message, k=5, domain=None):
            call_count["n"] += 1
            return list(facts)

        monkeypatch.setattr("core.pipeline.retrieve", fake_retrieve)

        result = server._console_observed_memory_fallback("query", domain=None, limit=10)
        claims = [f["claim"] for f in result]

        assert ALLOW_MARKER in claims
        assert RESTRICTED_MARKER not in claims
        assert "malformed marker" not in claims

        # Regression guard for the dead-code duplicate block: retrieve() must
        # not be called twice for the same successful domain pass.
        assert call_count["n"] == 1


# ─── _console_offline_reply() ──────────────────────────────────────────────────

class TestConsoleOfflineReply:
    def test_offline_reply_excludes_restricted_marker(self, imported_server, monkeypatch):
        server = imported_server

        allowed = _fake_fact("f_allow", ALLOW_MARKER, metadata={"memory_category": "personal"})
        restricted = _fake_fact(
            "f_restricted", RESTRICTED_MARKER,
            metadata={"memory_category": "personal", "restricted": "2026-07-12T10:00:00Z"},
        )

        # _console_offline_reply() also calls _console_all_memory() internally;
        # keep it empty here so the only facts in play are the ones passed in,
        # which is what actually proves the caller-supplied list is filtered.
        monkeypatch.setattr(server, "_console_all_memory", lambda limit=80: [])
        monkeypatch.setattr(server, "_console_recent_notes", lambda limit=50: [])

        reply = server._console_offline_reply(
            "what do you know about me?", [allowed, restricted], lang="en"
        )

        assert reply is not None
        assert ALLOW_MARKER in reply
        assert RESTRICTED_MARKER not in reply


# ─── /chat and /chat/stream (real FastAPI endpoints) ───────────────────────────

@pytest.fixture
def test_client(tmp_path, monkeypatch):
    """FastAPI TestClient with isolated DBs — same pattern as
    tests/test_server_integration.py's `test_client` fixture."""
    db_path = str(tmp_path / "recall_integration.db")
    ngram_db_path = str(tmp_path / "recall_integration_ngram.db")

    monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db_path)
    monkeypatch.setenv("VELANTRIM_NGRAM_DB", ngram_db_path)
    monkeypatch.setenv("CORE_BLOCKS_DB", str(tmp_path / "blocks.db"))
    monkeypatch.setenv("NOTEBOOK_DB", str(tmp_path / "notebook.db"))
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
    monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "false")
    monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "0")
    monkeypatch.setenv("ENABLE_VELUM", "0")

    for mod in list(sys.modules.keys()):
        if mod.startswith(("server", "core.")):
            del sys.modules[mod]

    try:
        from fastapi.testclient import TestClient

        import server as srv
        from core.feature_config import clear_config_cache
    except ImportError as exc:
        pytest.skip(f"Сервер недоступен ({exc})")

    clear_config_cache()

    with TestClient(srv.app) as client:
        client.headers.update({"X-Api-Key": "test-key"})
        yield client, srv


class TestChatEndpointExcludesRestricted:
    def test_chat_excludes_restricted_fact(self, test_client):
        client, srv = test_client

        r = client.post("/facts", json={
            "fact_id": "chat_allow_fact",
            "claim": ALLOW_MARKER,
            "source": "console_chat",
            "confidence": 0.88,
            "metadata": {"memory_category": "personal"},
        })
        assert r.status_code == 201, r.text

        r = client.post("/facts", json={
            "fact_id": "chat_restricted_fact",
            "claim": RESTRICTED_MARKER,
            "source": "console_chat",
            "confidence": 0.88,
            "metadata": {"memory_category": "personal"},
        })
        assert r.status_code == 201, r.text

        # Use the real set_restricted() contract — not a metadata shortcut.
        assert srv._store.set_restricted("chat_restricted_fact", True) is True

        # Sanity: raw storage still sees the restricted fact.
        raw = srv._store.get_all_facts()
        raw_claims = [f["claim"] for f in raw]
        assert RESTRICTED_MARKER in raw_claims

        r = client.post("/chat", json={
            "message": "what do you know about me in detail?",
            "profile": "citizen",
            "use_memory": True,
            "llm_enabled": False,
            "ui_lang": "en",
            "auto_save_memory": False,
            "block_memory": [],
            "chat_history": [],
        })
        assert r.status_code == 200, r.text
        reply = r.json()["reply"]

        assert ALLOW_MARKER in reply
        assert RESTRICTED_MARKER not in reply

    def test_chat_stream_excludes_restricted_fact(self, test_client):
        client, srv = test_client

        r = client.post("/facts", json={
            "fact_id": "stream_allow_fact",
            "claim": ALLOW_MARKER,
            "source": "console_chat",
            "confidence": 0.88,
            "metadata": {"memory_category": "personal"},
        })
        assert r.status_code == 201, r.text

        r = client.post("/facts", json={
            "fact_id": "stream_restricted_fact",
            "claim": RESTRICTED_MARKER,
            "source": "console_chat",
            "confidence": 0.88,
            "metadata": {"memory_category": "personal"},
        })
        assert r.status_code == 201, r.text

        assert srv._store.set_restricted("stream_restricted_fact", True) is True

        r = client.post("/chat/stream", json={
            "message": "what do you know about me in detail?",
            "profile": "citizen",
            "use_memory": True,
            "llm_enabled": False,
            "ui_lang": "en",
            "auto_save_memory": False,
            "block_memory": [],
            "chat_history": [],
        })
        assert r.status_code == 200, r.text
        body = r.text  # TestClient already assembles the full streamed body

        assert ALLOW_MARKER in body
        assert RESTRICTED_MARKER not in body


# ─── BranchManager retrieval corpus ────────────────────────────────────────────

class TestBranchManagerCorpusExcludesRestricted:
    def test_retrieve_with_hints_filters_corpus(self, monkeypatch):
        # FIX M15 (Claude audit 2026-07-28): _retrieve_with_hints() now goes
        # through core.pipeline._get_hybrid_retriever()'s cached singleton
        # instead of constructing core.hybrid_retriever.HybridRetriever
        # directly — patch the name pipeline.py actually calls, and force
        # its singleton to rebuild so this test doesn't get a stale hit from
        # whatever another test in this session already cached.
        import core.pipeline as pl
        from core.branch_manager import BranchManager

        facts = [
            _fake_fact("f_allow", ALLOW_MARKER),
            _fake_fact("f_restricted", RESTRICTED_MARKER, metadata={"restricted": True}),
        ]

        class _FakeStore:
            def get_all_facts(self):
                return facts

        captured_corpus: dict[str, list] = {}

        class _FakeHybridRetriever:
            def __init__(self, corpus, *args, **kwargs):
                captured_corpus["facts"] = corpus

            def retrieve(self, query, top_k=5):
                return []

            def retrieve_5stage(self, query, top_k=5, use_ego=False):
                return []

        saved_singleton = (pl._HYBRID_RETRIEVER, pl._HYBRID_DIRTY,
                            pl._HYBRID_FACTS_COUNT, pl._HYBRID_FACT_IDS)
        pl._HYBRID_RETRIEVER = None
        pl._HYBRID_DIRTY = True
        pl._HYBRID_FACTS_COUNT = 0
        pl._HYBRID_FACT_IDS = frozenset()
        try:
            monkeypatch.setattr("core.memory._GLOBAL_STORE", _FakeStore())
            monkeypatch.setattr(pl, "HybridRetriever", _FakeHybridRetriever)

            manager = BranchManager()
            manager._retrieve_with_hints("query", {"retrieval_k": "5"})
        finally:
            (pl._HYBRID_RETRIEVER, pl._HYBRID_DIRTY,
             pl._HYBRID_FACTS_COUNT, pl._HYBRID_FACT_IDS) = saved_singleton

        assert "facts" in captured_corpus, "HybridRetriever was never constructed"
        corpus_claims = [f["claim"] for f in captured_corpus["facts"]]

        assert ALLOW_MARKER in corpus_claims
        assert RESTRICTED_MARKER not in corpus_claims
