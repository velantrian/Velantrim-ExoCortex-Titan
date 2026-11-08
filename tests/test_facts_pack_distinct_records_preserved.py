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
