"""Bounded F3 research probe: same outward stop, distinct default-pipeline bases.

``tests/test_f3_same_stop_different_reason_model_free.py`` already proves this
invariant for the ``ModelFreeCore`` read-side facade. This probe asks the same
bounded question about the actual default production path
(``core.pipeline.run`` / ``core.pipeline.generate_answer``), which that fixture
does not exercise.

The bounded question: can several materially different evidence/policy/gate
failures inside the default pipeline collapse into the identical outward
``insufficient_evidence`` answer while their existing ``reason_code`` still
preserves the distinct material basis?

This test adds no ``StopReason`` type, reopen policy, scheduler, or authority.
It only observes existing ``core.pipeline`` behavior through its public
``run``/``generate_answer`` entry points.
"""

from __future__ import annotations

import pytest

_STOP_ANSWER = "Недостаточно подтверждённых локальных данных."


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    """Fresh SQLiteGraphStore per test, mirroring tests/test_pipeline.py."""

    from core import memory

    fresh = memory.make_store(str(tmp_path / "test.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE", fresh)
    monkeypatch.setattr(memory, "_L0", fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH", str(tmp_path / "test.db"))
    yield fresh
    import sys

    pipeline = sys.modules.get("core.pipeline")
    if pipeline is not None:
        graph = getattr(pipeline, "_CAUSAL_GRAPH", None)
        if graph is not None:
            try:
                graph._conn.close()
            except Exception:
                pass
        pipeline._CAUSAL_GRAPH = None
        pipeline._CAUSAL_GRAPH_DB_PATH = ""
    fresh.close()


def test_f3_default_pipeline_preserves_distinct_bases_under_one_stop_answer():
    from core.memory import promote_to_validated, store_fact
    from core.pipeline import generate_answer, run

    # Case 1: retrieval finds no matching local fact at all.
    no_retrieval = run("zxqvbnmqwerty-f3-default-pipeline-probe")

    # Case 2: retrieval finds a fact, but it is Observed-only, so the BALANCED
    # policy excludes it before it ever reaches TruthGate.
    store_fact({
        "fact_id": "f3-default-observed-only",
        "claim": "f3 default pipeline probe unconfirmed observed claim",
        "source": "field_note",
        "confidence": 0.9,
    })
    not_policy_eligible = run("f3 default pipeline probe unconfirmed observed claim")

    # Case 3: retrieval and policy both pass on a Validated fact, but the
    # explicit cognitive mode itself is malformed, so TruthGate rejects.
    store_fact({
        "fact_id": "f3-default-validated",
        "claim": "f3 default pipeline probe validated claim",
        "source": "physics",
        "confidence": 0.99,
    })
    promote_to_validated("f3-default-validated")
    truth_gate_rejected = run(
        "f3 default pipeline probe validated claim",
        cognitive_mode="NOT_A_REAL_COGNITIVE_MODE",
    )

    # Case 4: generate_answer() is handed a fact that self-asserts a
    # non-canonical "Validated" projection; it is never real Canon evidence.
    spoofed_validated = generate_answer(
        {
            "facts": [
                {
                    "fact_id": "f3-default-spoofed",
                    "claim": "f3 default pipeline probe spoofed claim",
                    "source": "external-index",
                    "confidence": 1.0,
                    "epistemic_state": "Validated",
                    "canonical_record": False,
                },
            ],
        },
        [],
    )

    results = (no_retrieval, not_policy_eligible, truth_gate_rejected, spoofed_validated)

    # Same outward STOP-like result for all four conditions.
    assert {result["insufficient_evidence"] for result in results} == {True}
    assert {result["answer"] for result in results} == {_STOP_ANSWER}

    # The existing reason_code still preserves each distinct material basis.
    assert tuple(result["reason_code"] for result in results) == (
        "no_local_retrieval_results",
        "no_policy_eligible_local_evidence",
        "truth_gate_rejected",
        "insufficient_validated_local_evidence",
    )
    assert len({result["reason_code"] for result in results}) == len(results)

    # F3 ceiling: this probe establishes no reopen semantics, no new StopReason
    # taxonomy, and no action/decision authority over which basis is retried.
    assert all(result["facts"] == [] for result in results)
