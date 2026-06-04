"""
E2E: ingest → observe → query с ExoCortex-флагами (V8.6).
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def exocortex_client(tmp_path, monkeypatch):
    """TestClient с ENABLE_VELUM + ENABLE_CAUSAL_GRAPH."""
    monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
    monkeypatch.setenv("VELANTRIM_DB_PATH", str(tmp_path / "exo.db"))
    monkeypatch.setenv("VELANTRIM_NGRAM_DB", str(tmp_path / "exo_ngram.db"))
    monkeypatch.setenv("CORE_BLOCKS_DB", str(tmp_path / "blocks.db"))
    monkeypatch.setenv("NOTEBOOK_DB", str(tmp_path / "notebook.db"))
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
    monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "false")
    monkeypatch.setenv("ENABLE_VELUM", "1")
    monkeypatch.setenv("VELUM_HINT_MIN_WEIGHT", "0.05")
    monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "1")
    monkeypatch.setenv("ENABLE_ETIR", "0")

    from core.feature_config import clear_config_cache
    from core.velum_bridge import reset_velum

    clear_config_cache()
    reset_velum()

    for mod in list(sys.modules.keys()):
        if mod.startswith(("server", "core.", "api.")):
            del sys.modules[mod]

    try:
        from fastapi.testclient import TestClient

        import server as srv
    except ImportError as exc:
        pytest.skip(str(exc))

    with TestClient(srv.app) as client:
        client.headers.update({"X-Api-Key": "test-key"})
        yield client


class TestExocortexE2E:
    def test_ingest_fact_and_query_layers_status(self, exocortex_client):
        r = exocortex_client.post(
            "/facts",
            json={
                "claim": "Проект Velantrim требует память и каузальный граф",
                "source": "e2e_test",
                "confidence": 0.9,
            },
        )
        assert r.status_code in (200, 201)
        fact_id = r.json().get("fact_id")
        assert fact_id

        st = exocortex_client.get("/layers/status")
        assert st.status_code == 200
        body = st.json()
        assert body["layers"]["L1_5_velum"]["enabled"] is True
        assert "horizons" in body

    def test_query_pipeline_with_velum_enabled(self, exocortex_client):
        claim = "Velantrim использует Truth Gate для валидации фактов"
        exocortex_client.post(
            "/facts",
            json={"claim": claim, "source": "e2e_test", "confidence": 0.95},
        )
        q = exocortex_client.post(
            "/query",
            json={"query": "Velantrim Truth Gate", "mode": "BALANCED", "use_llm": False},
        )
        assert q.status_code == 200
        data = q.json()
        assert "facts" in data
        sections = data.get("exocortex_sections")
        assert sections is None or isinstance(sections, list)

    def test_enrich_query_context_velum_section(self, exocortex_client):
        import asyncio

        from core.async_utils import run_coroutine_sync
        from core.exocortex_hooks import enrich_query_context
        from core.velum_bridge import get_velum

        async def _seed_velum():
            v = get_velum()
            await v.observe_episode(
                "e2e_velum",
                ["Velantrim", "память", "граф", "каузальный"],
            )

        asyncio.run(_seed_velum())
        exo = run_coroutine_sync(
            enrich_query_context(
                "Velantrim память граф",
                [{"claim": "Velantrim связан с памятью и графом"}],
            )
        )
        kinds = {s.get("kind") for s in exo.get("sections", []) if isinstance(s, dict)}
        assert "velum" in kinds

    def test_observe_ingest_chunk_direct(self):
        import asyncio

        from core.feature_config import clear_config_cache

        os.environ["ENABLE_CAUSAL_GRAPH"] = "1"
        clear_config_cache()

        from core.exocortex_hooks import observe_ingest_chunk

        out = asyncio.run(
            observe_ingest_chunk(
                chunk="Система требует Velantrim память",
                episode_id="e2e_ep_1",
            )
        )
        assert isinstance(out, dict)
