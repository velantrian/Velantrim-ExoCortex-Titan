from dataclasses import FrozenInstanceError, replace

import pytest

from core.evidence_reference import EvidenceReference, EvidenceReferenceError
from core.evidence_registry import (
    EvidenceFragmentRecord,
    EvidenceReferenceValidator,
    EvidenceSourceRecord,
    InMemoryEvidenceRegistry,
)

_SOURCE_A_DIGEST = "sha256:" + "a" * 64
_SOURCE_B_DIGEST = "sha256:" + "b" * 64
_FRAGMENT_A_DIGEST = "sha256:" + "c" * 64
_FRAGMENT_B_DIGEST = "sha256:" + "d" * 64
_FRAGMENT_C_DIGEST = "sha256:" + "e" * 64
_CAPTURED_AT = "2026-08-19T00:00:00+00:00"


def _reference(
    *,
    reference_id: str = "ref-1",
    source_id: str = "source-a",
    source_digest: str = _SOURCE_A_DIGEST,
    fragment_id: str = "fragment-a",
    fragment_digest: str = _FRAGMENT_A_DIGEST,
    span: str = "chars:0-10",
    lineage_id: str = "lineage-a",
    independence_class: str = "independent",
) -> EvidenceReference:
    return EvidenceReference(
        schema_version=1,
        reference_id=reference_id,
        source_id=source_id,
        source_digest=source_digest,
        fragment_id=fragment_id,
        fragment_digest=fragment_digest,
        span=span,
        lineage_id=lineage_id,
        independence_class=independence_class,  # type: ignore[arg-type]
        captured_at=_CAPTURED_AT,
    )


def _registry() -> InMemoryEvidenceRegistry:
    return InMemoryEvidenceRegistry(
        [
            EvidenceSourceRecord(
                source_id="source-a",
                source_digest=_SOURCE_A_DIGEST,
                lineage_id="lineage-a",
                status="active",
                fragments={
                    "fragment-a": EvidenceFragmentRecord(
                        fragment_id="fragment-a",
                        fragment_digest=_FRAGMENT_A_DIGEST,
                        allowed_spans=frozenset({"chars:0-10"}),
                    ),
                    "fragment-b": EvidenceFragmentRecord(
                        fragment_id="fragment-b",
                        fragment_digest=_FRAGMENT_B_DIGEST,
                        allowed_spans=frozenset({"chars:10-20"}),
                    ),
                },
            ),
            EvidenceSourceRecord(
                source_id="source-b",
                source_digest=_SOURCE_B_DIGEST,
                lineage_id="lineage-b",
                status="active",
                fragments={
                    "fragment-c": EvidenceFragmentRecord(
                        fragment_id="fragment-c",
                        fragment_digest=_FRAGMENT_C_DIGEST,
                        allowed_spans=frozenset({"chars:0-15"}),
                    )
                },
            ),
        ]
    )


def test_reference_mapping_and_digest_are_canonical_and_content_minimized() -> None:
    reference = _reference()
    parsed = EvidenceReference.from_mapping(reference.to_mapping())

    assert parsed == reference
    assert parsed.reference_digest == reference.reference_digest
    assert parsed.reference_digest.startswith("sha256:")
    assert "quote" not in reference.to_mapping()
    assert "https://" not in reference.canonical_json_bytes().decode("utf-8")


def test_reference_is_frozen() -> None:
    reference = _reference()

    with pytest.raises(FrozenInstanceError):
        reference.reference_id = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    "payload, message",
    [
        ({}, "missing="),
        ({"schema_version": 1}, "missing="),
        ({**_reference().to_mapping(), "unknown": "value"}, "unexpected=unknown"),
        ({**_reference().to_mapping(), "span": "chars:10-10"}, "span end"),
        ({**_reference().to_mapping(), "captured_at": "2026-08-19"}, "explicit timezone"),
        ({**_reference().to_mapping(), "source_digest": "sha256:UPPER"}, "lower-case"),
    ],
)
def test_reference_parser_rejects_invalid_payloads(
    payload: dict[str, object], message: str
) -> None:
    with pytest.raises(EvidenceReferenceError, match=message):
        EvidenceReference.from_mapping(payload)


def test_validator_accepts_one_registered_reference() -> None:
    receipt = EvidenceReferenceValidator(_registry()).validate(
        fact_id="fact-1", references=[_reference()]
    )

    assert receipt.raw_reference_count == 1
    assert receipt.unique_reference_count == 1
    assert receipt.validated_reference_count == 1
    assert receipt.distinct_independent_lineage_count == 1
    assert receipt.outcomes[0].status == "accepted"
    assert receipt.fact_ref.startswith("fact_")
    assert "fact-1" not in receipt.fact_ref


def test_validator_deduplicates_reference_ids_without_inflating_counts() -> None:
    reference = _reference()
    receipt = EvidenceReferenceValidator(_registry()).validate(
        fact_id="fact-1", references=[reference, reference]
    )

    assert receipt.raw_reference_count == 2
    assert receipt.unique_reference_count == 1
    assert receipt.validated_reference_count == 1
    assert receipt.distinct_independent_lineage_count == 1
    assert [outcome.status for outcome in receipt.outcomes] == [
        "accepted",
        "duplicate_reference_id",
    ]


def test_validator_counts_same_lineage_only_once() -> None:
    first = _reference()
    second = _reference(
        reference_id="ref-2",
        fragment_id="fragment-b",
        fragment_digest=_FRAGMENT_B_DIGEST,
        span="chars:10-20",
    )

    receipt = EvidenceReferenceValidator(_registry()).validate(
        fact_id="fact-1", references=[first, second]
    )

    assert receipt.validated_reference_count == 2
    assert receipt.distinct_independent_lineage_count == 1
    assert [outcome.status for outcome in receipt.outcomes] == [
        "accepted",
        "same_lineage_not_counted",
    ]


def test_validator_does_not_count_derived_reference_as_independent() -> None:
    independent = _reference()
    derived = _reference(
        reference_id="ref-2",
        source_id="source-b",
        source_digest=_SOURCE_B_DIGEST,
        fragment_id="fragment-c",
        fragment_digest=_FRAGMENT_C_DIGEST,
        span="chars:0-15",
        lineage_id="lineage-b",
        independence_class="derived",
    )

    receipt = EvidenceReferenceValidator(_registry()).validate(
        fact_id="fact-1", references=[independent, derived]
    )

    assert receipt.validated_reference_count == 2
    assert receipt.distinct_independent_lineage_count == 1
    assert [outcome.status for outcome in receipt.outcomes] == [
        "accepted",
        "derived_not_counted",
    ]


@pytest.mark.parametrize(
    "reference, expected_status",
    [
        (_reference(source_id="unknown"), "unknown_source"),
        (_reference(source_digest=_SOURCE_B_DIGEST), "source_digest_mismatch"),
        (_reference(lineage_id="lineage-b"), "lineage_mismatch"),
        (_reference(fragment_id="unknown"), "unknown_fragment"),
        (_reference(fragment_digest=_FRAGMENT_B_DIGEST), "fragment_digest_mismatch"),
        (_reference(span="chars:20-30"), "invalid_span"),
    ],
)
def test_validator_fails_closed_for_unresolvable_or_tampered_reference(
    reference: EvidenceReference, expected_status: str
) -> None:
    receipt = EvidenceReferenceValidator(_registry()).validate(
        fact_id="fact-1", references=[reference]
    )

    assert receipt.validated_reference_count == 0
    assert receipt.distinct_independent_lineage_count == 0
    assert receipt.outcomes[0].status == expected_status


def test_validator_rejects_revoked_source() -> None:
    source = _registry().resolve("source-a")
    assert source is not None
    registry = InMemoryEvidenceRegistry([replace(source, status="revoked")])

    receipt = EvidenceReferenceValidator(registry).validate(
        fact_id="fact-1", references=[_reference()]
    )

    assert receipt.validated_reference_count == 0
    assert receipt.outcomes[0].status == "revoked_source"


def test_receipt_is_deterministic_across_input_order() -> None:
    first = _reference()
    second = _reference(
        reference_id="ref-2",
        source_id="source-b",
        source_digest=_SOURCE_B_DIGEST,
        fragment_id="fragment-c",
        fragment_digest=_FRAGMENT_C_DIGEST,
        span="chars:0-15",
        lineage_id="lineage-b",
    )
    validator = EvidenceReferenceValidator(_registry())

    forward = validator.validate(fact_id="fact-1", references=[first, second])
    backward = validator.validate(fact_id="fact-1", references=[second, first])

    assert forward.to_mapping() == backward.to_mapping()
    assert forward.receipt_digest == backward.receipt_digest


def test_registry_rejects_conflicting_source_replacement() -> None:
    registry = _registry()
    source = registry.resolve("source-a")
    assert source is not None

    with pytest.raises(ValueError, match="different metadata"):
        registry.register(replace(source, lineage_id="different"))


def test_validator_exposes_no_write_or_promotion_shortcut() -> None:
    validator = EvidenceReferenceValidator(_registry())

    assert not hasattr(validator, "validate_and_promote")
    assert not hasattr(validator, "store_fact")
    assert not hasattr(validator, "transition_esm")
