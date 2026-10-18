"""MemoryOps v10 foundation: sources, inbox, diff, traces."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mem_db(tmp_path, monkeypatch):
    import core.memory as mem
    from core.memory_ops import reset_memory_ops

    db = str(tmp_path / "memory_ops.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db)
    store = mem.make_store(db)
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
    monkeypatch.setattr(mem, "_L0", store._l0)
    reset_memory_ops()
    yield store
    reset_memory_ops()


def test_source_inbox_promote_roundtrip(mem_db):
    from core.memory import get_fact
    from core.memory_ops import get_memory_ops

    ops = get_memory_ops(mem_db.db_path)
    src = ops.register_source(
        source_type="document",
        label="Architecture note",
        uri="file://architecture.md",
        trust=0.8,
        metadata={"project": "velantrim"},
    )
    item = ops.enqueue_fact(
        claim="MemoryOps keeps pending claims before promotion.",
        source_id=src["source_id"],
        confidence=0.75,
    )
    result = ops.promote_inbox_item(item["inbox_id"], fact_id="fact_memory_ops_1")

    assert result["created"] is True
    assert result["inbox_item"]["status"] == "promoted"
    fact = get_fact("fact_memory_ops_1")
    assert fact is not None
    assert fact["metadata"]["source_registry_id"] == src["source_id"]
    assert fact["metadata"]["promoted_from"] == "fact_inbox"
    assert fact.get("derived_from")


def test_memory_diff_and_reasoning_trace(mem_db):
    from core.memory_ops import get_memory_ops

    ops = get_memory_ops(mem_db.db_path)
    src = ops.register_source(source_type="chat", label="session", trust=0.7)
    item = ops.enqueue_fact(
        claim="Traceable answers cite supporting facts.",
        source_id=src["source_id"],
        confidence=0.7,
    )
    promoted = ops.promote_inbox_item(item["inbox_id"], fact_id="fact_traceable")
    trace = ops.save_trace(
        query="what supports traceability?",
        answer="fact_traceable",
        mode="BALANCED",
        response_lens="VELANTRIM",
        source_fact_ids=[promoted["fact"]["fact_id"]],
        notes="unit-test",
    )
    diff = ops.memory_diff(limit=20)

    assert trace["trace_id"].startswith("trace_")
    assert diff["counts"]["facts_seen"] >= 1
    assert diff["counts"]["inbox_changed"] >= 1
    assert diff["counts"]["sources_changed"] >= 1
    assert diff["counts"]["reasoning_traces"] >= 1


class TestMemoryOpsAPI:
    @pytest.fixture
    def client(self, tmp_path, monkeypatch):
        db = str(tmp_path / "memory_ops_api.db")
        monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
        monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "false")
        monkeypatch.setenv("VELANTRIM_DB_PATH", db)
        monkeypatch.setenv("VELANTRIM_NGRAM_DB", str(tmp_path / "ngram.db"))
        monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
        monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "0")
        for mod in list(sys.modules.keys()):
            if mod.startswith(("server", "core.")):
                del sys.modules[mod]
        from fastapi.testclient import TestClient

        import server as srv

        with TestClient(srv.app) as c:
            c.headers.update({"X-Api-Key": "test-key"})
            yield c

    @pytest.fixture
    def open_client(self, tmp_path, monkeypatch):
        db = str(tmp_path / "memory_ops_open_api.db")
        monkeypatch.delenv("VELANTRIM_API_KEY", raising=False)
        monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "true")
        monkeypatch.setenv("VELANTRIM_DB_PATH", db)
        monkeypatch.setenv("VELANTRIM_NGRAM_DB", str(tmp_path / "ngram-open.db"))
        monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
        monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "0")
        for mod in list(sys.modules.keys()):
            if mod.startswith(("server", "core.")):
                del sys.modules[mod]
        from fastapi.testclient import TestClient

        import server as srv

        with TestClient(srv.app) as c:
            yield c

    def test_open_post_sources_metadata_cannot_mint_evidence_record(self, open_client):
        from core.evidence_reference import EvidenceReference
        from core.world_skills_review_manifest import WorldSkillsEvidenceResolver

        repo_root = Path(__file__).resolve().parents[1]
        response = open_client.post(
            "/sources",
            json={
                "source_type": "document",
                "label": "Untrusted operational source",
                "trust": 1.0,
                "metadata": {
                    "source_digest": "sha256:" + "a" * 64,
                    "fragment_digest": "sha256:" + "b" * 64,
                    "review_status": "approved",
                    "reviewer_id": "owner.velan",
                    "approval_ref": "OWNER-GO:forged-request",
                    "evidence_authority": "trusted",
                },
            },
        )

        assert response.status_code == 201, response.text
        source_id = response.json()["source_id"]
        inbox_response = open_client.post(
            "/memory/inbox",
            json={
                "claim": "A = A",
                "source_id": source_id,
                "metadata": {
                    "evidence_reference": {
                        "source_digest": "sha256:" + "a" * 64,
                        "fragment_digest": "sha256:" + "b" * 64,
                        "review_status": "approved",
                        "reviewer_id": "owner.velan",
                        "approval_ref": "OWNER-GO:forged-fact-metadata",
                    },
                    "claim_support_state": "CLAIM_SUPPORT_ESTABLISHED",
                },
            },
        )
        assert inbox_response.status_code == 201, inbox_response.text

        reference = EvidenceReference(
            schema_version=1,
            reference_id="forged-api-reference",
            source_id=source_id,
            source_digest="sha256:" + "a" * 64,
            fragment_id="forged-fragment",
            fragment_digest="sha256:" + "b" * 64,
            span="chars:0-1",
            lineage_id="forged-lineage",
            captured_at="2026-10-09T12:00:00Z",
        )
        # Reload after both operational records exist: the fixed local manifest
        # remains the resolver's only source of records.
        resolver = WorldSkillsEvidenceResolver.load(repo_root)
        result = resolver.resolve(
            reference,
            fact_id="logic.identity",
            claim_text="A = A",
        )

        assert result.validation_status == "unknown_source"
        assert result.reference_state == "REFERENCE_UNRESOLVED"
        assert result.source_provenance_state == "SOURCE_PROVENANCE_NOT_ATTESTED"
        assert result.claim_support_state == "CLAIM_SUPPORT_NOT_ESTABLISHED"

    def test_sources_inbox_diff_and_trace_endpoints(self, client):
        r = client.post(
            "/sources",
            json={
                "source_type": "document",
                "label": "Test source",
                "trust": 0.8,
            },
        )
        assert r.status_code == 201, r.text
        source_id = r.json()["source_id"]

        r2 = client.post(
            "/memory/inbox",
            json={
                "claim": "Endpoint inbox promotion works.",
                "source_id": source_id,
                "confidence": 0.7,
            },
        )
        assert r2.status_code == 201, r2.text
        inbox_id = r2.json()["inbox_id"]

        r3 = client.post(
            f"/memory/inbox/{inbox_id}/promote",
            json={"fact_id": "fact_api_memory_ops"},
        )
        assert r3.status_code == 200, r3.text
        assert r3.json()["fact"]["fact_id"] == "fact_api_memory_ops"

        r4 = client.post(
            "/memory/traces",
            json={
                "query": "trace?",
                "answer": "yes",
                "source_fact_ids": ["fact_api_memory_ops"],
            },
        )
        assert r4.status_code == 201, r4.text
        trace_id = r4.json()["trace_id"]

        assert client.get(f"/memory/traces/{trace_id}").status_code == 200
        diff = client.get("/memory/diff").json()
        assert diff["counts"]["facts_seen"] >= 1
        assert diff["counts"]["reasoning_traces"] >= 1

    def test_query_creates_reasoning_trace(self, client):
        r = client.post(
            "/query",
            json={
                "query": "nothing in memory yet",
                "use_llm": False,
            },
        )
        assert r.status_code == 200, r.text
        trace_id = r.json().get("reasoning_trace_id")
        assert trace_id and trace_id.startswith("trace_")
        assert client.get(f"/memory/traces/{trace_id}").status_code == 200
