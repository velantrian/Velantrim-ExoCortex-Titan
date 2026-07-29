"""
Regression test for the M10 essence-fallback fix (Claude audit 2026-07-28).

BranchManager._generate_response()'s essence fallback called
compose_essence(query=query, facts=facts) — compose_essence(facts,
relations=None) has no `query` kwarg, so the call always raised a TypeError,
caught by the same bare `except Exception: pass` as any other failure. Every
branch response therefore always fell through to the generic
"[{emoji} {role}] Анализ N фактов по запросу: ..." template at confidence
0.3, regardless of how many real, verified facts were available.

This test proves that with real facts present, _generate_response() now
returns the essence's actual gist (a real fact's claim) at confidence 0.6,
not the generic template — LlmCallConfig(max_tokens=500) still raises
(no provider/api_key supplied anywhere in this call chain; see the
docstring left in branch_manager.py — untouched by this fix, tracked
separately), so the essence path is the first one that can actually
succeed.
"""
from __future__ import annotations

import pytest

from core.branch_manager import BranchManager
from core.perspectives import resolve_roles


@pytest.mark.asyncio
async def test_generate_response_uses_essence_gist_not_generic_fallback():
    manager = BranchManager()
    role = resolve_roles("test query", requested_roles=["ENGINEER"])[0]
    facts = [
        {
            "fact_id": "f1",
            "claim": "Solar panels convert sunlight directly into electricity",
            "source": "physics",
            "confidence": 0.9,
            "epistemic_state": "Validated",
        },
    ]

    response, confidence = await manager._generate_response("how do solar panels work?", facts, role)

    assert confidence == 0.6
    assert response == "Solar panels convert sunlight directly into electricity"
    assert "Анализ" not in response, "must not fall through to the generic template"


@pytest.mark.asyncio
async def test_generate_response_falls_back_to_generic_template_on_no_facts():
    """Sanity check: the essence path itself never raises on empty input
    (compose_essence's own contract) — it correctly yields an empty gist,
    which must still fall through to the absolute fallback."""
    manager = BranchManager()
    role = resolve_roles("test query", requested_roles=["ENGINEER"])[0]

    response, confidence = await manager._generate_response("empty query", [], role)

    assert confidence == 0.3
    assert "Анализ 0 фактов" in response
