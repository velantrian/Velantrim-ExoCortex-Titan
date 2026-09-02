"""Bounded F3 research probe: same outward stop, different existing bases.

This test observes the existing ModelFreeCore read path only. It does not add a
StopReason type, reopen policy, scheduler, authority, or runtime behavior.

The bounded question is whether several materially different failure conditions
can produce the same outward insufficient-evidence answer while preserving their
existing reason/gate distinctions. Reopen semantics are intentionally outside
this probe and remain NOT_OBSERVABLE here.
"""

from __future__ import annotations


def _pipeline():
    import core.pipeline as module

    return module


def _model_free():
    import core.model_free_core as module

    return module


def _packed_fact() -> dict[str, object]:
    return {
        "fact_id": "f3-fixture-fact",
        "claim": "bounded F3 fixture evidence",
        "source": "fixture://f3",
        "epistemic_state": "Observed",
        "confidence": 0.95,
        "retrieval_score": 1.0,
        "claim_type": "WORLD_FACT",
        "origin_type": "fixture",
        "truth_status": "VALIDATED",
    }


def _prime_evidence_path(monkeypatch) -> None:
    pipeline = _pipeline()
    packed_fact = _packed_fact()
    monkeypatch.setattr(
        pipeline,
        "_retrieve_from_store",
        lambda *_args, **_kwargs: [
            {"id": packed_fact["fact_id"], "retrieval_score": 1.0, "metadata": {}}
        ],
    )
    monkeypatch.setattr(
        pipeline,
        "build_facts_pack",
        lambda *_args, **_kwargs: {"facts": [dict(packed_fact)]},
    )


def test_f3_same_outward_stop_preserves_distinct_existing_bases(monkeypatch) -> None:
    pipeline = _pipeline()
    model_free = _model_free()
    core = model_free.ModelFreeCore()
    request = model_free.L2Query("bounded f3 probe", include_graph=True)

    # Case 1: no local evidence was retrieved.
    monkeypatch.setattr(
        pipeline,
        "_retrieve_from_store",
        lambda *_args, **_kwargs: [],
    )
    no_retrieval = core.query(request)

    # Case 2: evidence exists, but Guardian rejects the bounded pack.
    _prime_evidence_path(monkeypatch)
    monkeypatch.setattr(pipeline, "guardian", lambda *_args, **_kwargs: (False, "f3"))
    guardian_rejected = core.query(request)

    # Case 3: Guardian passes, but TruthGate rejects.
    monkeypatch.setattr(pipeline, "guardian", lambda *_args, **_kwargs: (True, "f3"))
    monkeypatch.setattr(pipeline, "truth_gate", lambda *_args, **_kwargs: (False, "f3"))
    truth_gate_rejected = core.query(request)

    # Case 4: evidence and both gates pass, but the optional graph read fails.
    monkeypatch.setattr(pipeline, "truth_gate", lambda *_args, **_kwargs: (True, "f3"))

    def fail_graph_lookup():
        raise RuntimeError("bounded F3 graph read failure")

    monkeypatch.setattr(pipeline, "_peek_causal_graph", fail_graph_lookup)
    graph_read_failed = core.query(request)

    results = (
        no_retrieval,
        guardian_rejected,
        truth_gate_rejected,
        graph_read_failed,
    )

    # Same outward STOP-like result for all four conditions.
    assert {result.insufficient_evidence for result in results} == {True}
    assert {result.answer for result in results} == {
        "Недостаточно подтверждённых локальных данных."
    }

    # But the existing path does not collapse the material basis to one label.
    assert tuple(result.reason_code for result in results) == (
        "no_local_lexical_retrieval_results",
        "guardian_rejected",
        "truth_gate_rejected",
        "causal_graph_read_failed",
    )
    assert len({result.reason_code for result in results}) == len(results)

    # Existing downstream gate-state consequences are also not identical.
    assert {
        (result.guardian_passed, result.truth_gate_passed) for result in results
    } == {
        (False, False),
        (True, False),
        (True, True),
    }

    # F3 ceiling: this probe establishes no reopen semantics or action authority.
    assert all(result.evidence == () for result in results)
