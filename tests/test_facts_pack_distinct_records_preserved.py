"""FactsPack must not drop distinct memory records because their wording overlaps.

Regression for the former ``FactsPackBuilder._dedup_semantic`` (token overlap
> 0.7, winner by confidence). It silently removed a correction that differed
only by a negation, a condition, an identifier, a status, a number or argument
order, before the LLM ever saw the facts. Dropped records were not reported in
``excluded_facts``.

Only a provable repeat of the same record (same real ``fact_id`` and identical
packed payload) may be collapsed. Same text under different ``fact_id`` values
keeps separate provenance.
"""
from __future__ import annotations

import pytest

from core.facts_pack import FactsPackBuilder

QUERY = "правила хранения и миграции"

# (kept_by_old_dedup, removed_by_old_dedup): the second record is the lower
# confidence one, so the former token-overlap dedup kept only the first.
DISTINCT_PAIRS = [
    pytest.param(
        ("neg-a", "Руслан одобрил миграцию на PostgreSQL", 0.90),
        ("neg-b", "Руслан не одобрил миграцию на PostgreSQL", 0.80),
        id="negation",
    ),
    pytest.param(
        ("cond-a", "Удаление архива разрешено", 0.90),
        ("cond-b", "Удаление архива разрешено только после подтверждения владельца", 0.70),
        id="condition",
    ),
    pytest.param(
        ("id-a", "Правило хранения действует на уровне L1", 0.90),
        ("id-b", "Правило хранения действует на уровне L2", 0.85),
        id="identifier",
    ),
    pytest.param(
        ("status-a", "Статус решения ADR-12: принято", 0.90),
        ("status-b", "Статус решения ADR-12: отменено", 0.80),
        id="status",
    ),
    pytest.param(
        ("num-a", "Срок хранения логов 30 дней", 0.90),
        ("num-b", "Срок хранения логов 7 дней", 0.80),
        id="number",
    ),
    pytest.param(
        ("role-a", "Alice paid Bob", 0.90),
        ("role-b", "Bob paid Alice", 0.80),
        id="argument-order",
    ),
]


def _raw(fact_id, claim, confidence, *, source="src:test", state="Validated", score=0.9):
    return {
        "fact_id": fact_id,
        "claim": claim,
        "confidence": confidence,
        "source": source,
        "epistemic_state": state,
        "retrieval_score": score,
    }


def _build(raw_facts):
    return FactsPackBuilder("BALANCED").add_facts(raw_facts).build(QUERY)


@pytest.mark.parametrize(("first", "second"), DISTINCT_PAIRS)
def test_overlapping_but_distinct_records_both_reach_the_pack(first, second):
    pack = _build([_raw(*first), _raw(*second)])

    assert {f.fact_id for f in pack.facts} == {first[0], second[0]}
    assert {f.claim for f in pack.facts} == {first[1], second[1]}
    # Nothing was silently discarded either.
    assert pack.excluded_facts == []


def test_same_text_from_different_records_keeps_both_provenances():
    claim = "Срок хранения логов 30 дней"
    pack = _build([
        _raw("rec-1", claim, 0.90, source="kb:policy"),
        _raw("rec-2", claim, 0.60, source="chat:2026-11-01"),
    ])

    assert sorted((f.fact_id, f.source) for f in pack.facts) == [
        ("rec-1", "kb:policy"),
        ("rec-2", "chat:2026-11-01"),
    ]


def test_provable_repeat_of_the_same_record_is_collapsed():
    record = _raw("rec-1", "Срок хранения логов 30 дней", 0.90, score=0.4)
    repeat = dict(record, retrieval_score=0.8)

    pack = _build([record, repeat])

    assert [f.fact_id for f in pack.facts] == ["rec-1"]
    # The surviving copy keeps the strongest retrieval signal for that record.
    assert pack.facts[0].retrieval_score == pytest.approx(0.8)
    assert pack.excluded_facts == []


def test_same_fact_id_with_different_payload_is_not_treated_as_a_repeat():
    pack = _build([
        _raw("rec-1", "Срок хранения логов 30 дней", 0.90),
        _raw("rec-1", "Срок хранения логов 7 дней", 0.90),
    ])

    assert sorted(f.claim for f in pack.facts) == [
        "Срок хранения логов 30 дней",
        "Срок хранения логов 7 дней",
    ]


def test_records_without_a_real_fact_id_are_never_collapsed():
    claim = "Срок хранения логов 30 дней"
    no_id = {k: v for k, v in _raw("x", claim, 0.90).items() if k != "fact_id"}

    pack = _build([dict(no_id), dict(no_id)])

    assert len(pack.facts) == 2


@pytest.mark.parametrize(
    ("field", "other"),
    [
        ("fact_id", "rec-2"),
        ("source", "src:other"),
        ("confidence", 0.60),
        ("epistemic_state", "Supported"),
        ("claim", "Срок хранения логов 31 день"),
    ],
)
def test_record_is_not_a_repeat_when_any_key_field_differs(field, other):
    base = _raw("rec-1", "Срок хранения логов 30 дней", 0.90)

    pack = _build([base, {**base, field: other}])

    assert len(pack.facts) == 2


def test_empty_string_fact_id_is_never_collapsed():
    record = _raw("", "Срок хранения логов 30 дней", 0.90)

    pack = _build([dict(record), dict(record)])

    assert len(pack.facts) == 2


@pytest.mark.parametrize("scores", [(0.4, 0.8), (0.8, 0.4)])
def test_repeat_keeps_the_strongest_retrieval_score_in_either_order(scores):
    claim = "Срок хранения логов 30 дней"

    pack = _build([
        _raw("rec-1", claim, 0.90, score=scores[0]),
        _raw("rec-1", claim, 0.90, score=scores[1]),
    ])

    assert [f.fact_id for f in pack.facts] == ["rec-1"]
    assert pack.facts[0].retrieval_score == pytest.approx(0.8)


# ── enrichment fields are part of the record ────────────────────────────────

ENRICHMENT_DIFFERENCES = [
    pytest.param("causal_summary", {"path": ["a", "b"]}, {"path": ["a", "c"]}, id="causal_summary"),
    pytest.param("living_context", {"where": "lab"}, {"where": "field"}, id="living_context"),
    pytest.param("context_applicability", 0.9, 0.4, id="context_applicability"),
]


@pytest.mark.parametrize(("field", "first", "second"), ENRICHMENT_DIFFERENCES)
def test_same_record_with_different_enrichment_is_not_collapsed(field, first, second):
    # Collapsing would keep the first copy and silently lose the other one's enrichment.
    base = _raw("rec-1", "Срок хранения логов 30 дней", 0.90)

    pack = _build([{**base, field: first}, {**base, field: second}])

    assert len(pack.facts) == 2
    assert sorted(repr(getattr(f, field)) for f in pack.facts) == sorted([repr(first), repr(second)])


@pytest.mark.parametrize(("field", "first", "second"), ENRICHMENT_DIFFERENCES)
def test_enrichment_present_on_one_copy_only_is_a_difference(field, first, second):
    base = _raw("rec-1", "Срок хранения логов 30 дней", 0.90)

    pack = _build([dict(base), {**base, field: first}])

    assert len(pack.facts) == 2


def test_identical_enrichment_still_collapses_and_key_order_does_not_matter():
    base = _raw("rec-1", "Срок хранения логов 30 дней", 0.90)
    one = {**base, "retrieval_score": 0.4, "causal_summary": {"a": 1, "b": [1, 2]}, "living_context": {"x": {"y": 1, "z": 2}}}
    two = {**base, "retrieval_score": 0.8, "causal_summary": {"b": [1, 2], "a": 1}, "living_context": {"x": {"z": 2, "y": 1}}}

    pack = _build([one, two])

    assert [f.fact_id for f in pack.facts] == ["rec-1"]
    assert pack.facts[0].retrieval_score == pytest.approx(0.8)


def test_an_unserializable_enrichment_value_never_raises_in_the_key():
    base = _raw("rec-1", "Срок хранения логов 30 дней", 0.90)

    pack = _build([{**base, "living_context": {"k": object()}}, {**base, "living_context": {"k": object()}}])

    assert len(pack.facts) == 2          # two different objects: not provably the same record


def test_every_field_of_a_packed_fact_except_the_retrieval_score_is_part_of_the_record():
    # Guards the key against a field added to PackedFact later: each field, changed alone,
    # must stop two otherwise identical copies from collapsing.
    from dataclasses import fields, replace

    from core.facts_pack import PackedFact

    base = PackedFact(
        fact_id="rec-1", claim="c", epistemic_state="Validated", confidence=0.9, source="s",
        retrieval_score=0.5, context_applicability=1.0, causal_summary={"a": 1}, living_context={"b": 2},
    )
    changed = {
        "fact_id": "rec-2", "claim": "c2", "epistemic_state": "Supported", "confidence": 0.8, "source": "s2",
        "context_applicability": 0.5, "causal_summary": {"a": 2}, "living_context": {"b": 3},
    }
    for field in fields(PackedFact):
        if field.name == "retrieval_score":
            continue
        assert field.name in changed, f"new PackedFact field {field.name!r}: add it to this test"
        out = FactsPackBuilder._dedup_exact_record_repeats([base, replace(base, **{field.name: changed[field.name]})])
        assert len(out) == 2, field.name
    assert len(FactsPackBuilder._dedup_exact_record_repeats([base, replace(base, retrieval_score=0.9)])) == 1
