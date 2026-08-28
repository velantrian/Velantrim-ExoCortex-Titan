from core.semantic_dedup import plan_dedup


def _embed_same(claims):
    return [[1.0, 0.0] for _ in claims]


def _facts(order):
    rows = {
        "a-fact": {
            "fact_id": "a-fact",
            "claim": "same meaning alpha",
            "source": "s1",
            "epistemic_state": "Supported",
            "confidence": 0.8,
        },
        "z-fact": {
            "fact_id": "z-fact",
            "claim": "same meaning beta",
            "source": "s2",
            "epistemic_state": "Supported",
            "confidence": 0.8,
        },
    }
    return [rows[fact_id] for fact_id in order]


def test_plan_dedup_tie_break_is_input_order_independent():
    first = plan_dedup(
        _facts(["z-fact", "a-fact"]), threshold=0.5, embed_fn=_embed_same
    )
    second = plan_dedup(
        _facts(["a-fact", "z-fact"]), threshold=0.5, embed_fn=_embed_same
    )

    assert len(first) == len(second) == 1
    assert first[0].canonical_id == second[0].canonical_id == "a-fact"
    assert first[0].absorbed_ids == second[0].absorbed_ids == ["z-fact"]
