from dataclasses import FrozenInstanceError, replace

import pytest

from core.evidence_reference import EvidenceReference, EvidenceReferenceError
from core.evidence_registry import (
    EvidenceFragmentRecord,
    EvidenceReferenceValidator,
    EvidenceRegistrySnapshot,
    EvidenceSourceRecord,
    EvidenceValidationReceipt,
    InMemoryEvidenceRegistry,
)

_SOURCE_A_DIGEST = "sha256:" + "a" * 64
_SOURCE_B_DIGEST = "sha256:" + "b" * 64
_SOURCE_C_DIGEST = "sha256:" + "f" * 64
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


def test_reference_rejects_producer_claimed_independence() -> None:
    payload = {**_reference().to_mapping(), "independence_class": "independent"}
    with pytest.raises(EvidenceReferenceError, match="unexpected=independence_class"):
        EvidenceReference.from_mapping(payload)


@pytest.mark.parametrize(
    "payload, message",
    [
        ({}, "missing="),
        ({"schema_version": 1}, "missing="),
        ({**_reference().to_mapping(), "unknown": "value"}, "unexpected=unknown"),
        ({**_reference().to_mapping(), "span": "chars:10-10"}, "span end"),
        (
            {**_reference().to_mapping(), "captured_at": "2026-08-19"},
            "explicit timezone",
        ),
        (
            {**_reference().to_mapping(), "source_digest": "sha256:UPPER"},
            "lower-case",
        ),
    ],
)
def test_reference_parser_rejects_invalid_payloads(
    payload: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(EvidenceReferenceError, match=message):
        EvidenceReference.from_mapping(payload)


def test_validator_accepts_reference_without_self_granting_independence() -> None:
    receipt = EvidenceReferenceValidator(_registry()).validate(
        fact_id="fact-1",
        references=[_reference()],
    )
    assert receipt.raw_reference_count == 1
    assert receipt.unique_reference_count == 1
    assert receipt.validated_reference_count == 1
    assert receipt.distinct_independent_lineage_count == 0
    assert receipt.outcomes[0].status == "accepted"
    assert receipt.registry_snapshot_digest.startswith("sha256:")
    assert receipt.fact_ref.startswith("fact_")
    assert "fact-1" not in receipt.fact_ref


def test_validator_deduplicates_reference_ids_without_inflating_counts() -> None:
    reference = _reference()
    receipt = EvidenceReferenceValidator(_registry()).validate(
        fact_id="fact-1",
        references=[reference, reference],
    )
    assert receipt.raw_reference_count == 2
    assert receipt.unique_reference_count == 1
    assert receipt.validated_reference_count == 1
    assert receipt.distinct_independent_lineage_count == 0
    assert [outcome.status for outcome in receipt.outcomes] == [
        "accepted",
        "duplicate_reference_id",
    ]


def test_validator_fails_closed_for_conflicting_reference_id_in_any_order() -> None:
    valid = _reference(reference_id="ref-conflict")
    conflicting = _reference(
        reference_id="ref-conflict",
        source_digest=_SOURCE_B_DIGEST,
    )
    validator = EvidenceReferenceValidator(_registry())
    forward = validator.validate(
        fact_id="fact-1",
        references=[valid, conflicting],
    )
    backward = validator.validate(
        fact_id="fact-1",
        references=[conflicting, valid],
    )
    assert forward.to_mapping() == backward.to_mapping()
    assert forward.raw_reference_count == 2
    assert forward.unique_reference_count == 1
    assert forward.validated_reference_count == 0
    assert forward.distinct_independent_lineage_count == 0
    assert {outcome.status for outcome in forward.outcomes} == {
        "conflicting_reference_id"
    }


def test_registry_copies_fragment_mapping_into_immutable_record() -> None:
    fragments = {
        "fragment-a": EvidenceFragmentRecord(
            fragment_id="fragment-a",
            fragment_digest=_FRAGMENT_A_DIGEST,
            allowed_spans={"chars:0-10"},  # type: ignore[arg-type]
        )
    }
    source = EvidenceSourceRecord(
        source_id="source-a",
        source_digest=_SOURCE_A_DIGEST,
        lineage_id="lineage-a",
        status="active",
        fragments=fragments,
    )
    fragments["fragment-b"] = EvidenceFragmentRecord(
        fragment_id="fragment-b",
        fragment_digest=_FRAGMENT_B_DIGEST,
        allowed_spans=frozenset({"chars:10-20"}),
    )
    assert set(source.fragments) == {"fragment-a"}
    with pytest.raises(TypeError):
        source.fragments["fragment-b"] = fragments["fragment-b"]  # type: ignore[index]


def test_registry_rejects_invalid_or_inconsistent_fragment_metadata() -> None:
    fragment = EvidenceFragmentRecord(
        fragment_id="fragment-a",
        fragment_digest=_FRAGMENT_A_DIGEST,
        allowed_spans=frozenset({"chars:0-10"}),
    )
    with pytest.raises(ValueError, match="mapping key"):
        EvidenceSourceRecord(
            source_id="source-a",
            source_digest=_SOURCE_A_DIGEST,
            lineage_id="lineage-a",
            status="active",
            fragments={"fragment-b": fragment},
        )
    with pytest.raises(ValueError, match="technical identifier"):
        EvidenceFragmentRecord(
            fragment_id="bad space",
            fragment_digest=_FRAGMENT_A_DIGEST,
            allowed_spans=frozenset({"chars:0-10"}),
        )
    with pytest.raises(ValueError, match="lower-case sha256"):
        EvidenceFragmentRecord(
            fragment_id="fragment-a",
            fragment_digest="sha256:short",
            allowed_spans=frozenset({"chars:0-10"}),
        )
    with pytest.raises(ValueError, match="greater than start"):
        EvidenceFragmentRecord(
            fragment_id="fragment-a",
            fragment_digest=_FRAGMENT_A_DIGEST,
            allowed_spans=frozenset({"chars:10-10"}),
        )


@pytest.mark.parametrize(
    "reference, expected_status",
    [
        (_reference(source_id="unknown"), "unknown_source"),
        (_reference(source_digest=_SOURCE_B_DIGEST), "source_digest_mismatch"),
        (_reference(lineage_id="lineage-b"), "lineage_mismatch"),
        (_reference(fragment_id="unknown"), "unknown_fragment"),
        (
            _reference(fragment_digest=_FRAGMENT_B_DIGEST),
            "fragment_digest_mismatch",
        ),
        (_reference(span="chars:20-30"), "invalid_span"),
    ],
)
def test_validator_fails_closed_for_unresolvable_or_tampered_reference(
    reference: EvidenceReference,
    expected_status: str,
) -> None:
    receipt = EvidenceReferenceValidator(_registry()).validate(
        fact_id="fact-1",
        references=[reference],
    )
    assert receipt.validated_reference_count == 0
    assert receipt.distinct_independent_lineage_count == 0
    assert receipt.outcomes[0].status == expected_status


def test_validator_rejects_revoked_source() -> None:
    source = _registry().resolve("source-a")
    assert source is not None
    registry = InMemoryEvidenceRegistry([replace(source, status="revoked")])
    receipt = EvidenceReferenceValidator(registry).validate(
        fact_id="fact-1",
        references=[_reference()],
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
    forward = validator.validate(
        fact_id="fact-1",
        references=[first, second],
    )
    backward = validator.validate(
        fact_id="fact-1",
        references=[second, first],
    )
    assert forward.to_mapping() == backward.to_mapping()
    assert forward.receipt_digest == backward.receipt_digest
    assert forward.distinct_independent_lineage_count == 0


def test_registry_snapshot_digest_is_deterministic_and_metadata_bound() -> None:
    first = _registry().snapshot()
    second = _registry().snapshot()
    assert first.snapshot_digest == second.snapshot_digest
    source = _registry().resolve("source-a")
    assert source is not None
    changed = EvidenceRegistrySnapshot(
        {source.source_id: replace(source, status="revoked")}
    )
    assert changed.snapshot_digest != first.snapshot_digest


def test_registry_snapshot_is_defensive_and_immutable() -> None:
    registry = _registry()
    snapshot = registry.snapshot()
    digest_before = snapshot.snapshot_digest
    source_c = EvidenceSourceRecord(
        source_id="source-c",
        source_digest=_SOURCE_C_DIGEST,
        lineage_id="lineage-c",
        status="active",
        fragments={
            "fragment-c": EvidenceFragmentRecord(
                fragment_id="fragment-c",
                fragment_digest=_FRAGMENT_C_DIGEST,
                allowed_spans=frozenset({"chars:0-15"}),
            )
        },
    )
    registry.register(source_c)
    assert snapshot.resolve("source-c") is None
    assert snapshot.snapshot_digest == digest_before
    with pytest.raises(TypeError):
        snapshot.records["source-c"] = source_c  # type: ignore[index]


def test_snapshot_rejects_source_mapping_key_mismatch() -> None:
    source = _registry().resolve("source-a")
    assert source is not None
    with pytest.raises(ValueError, match="source mapping key"):
        EvidenceRegistrySnapshot({"wrong-source": source})


def test_validator_captures_exactly_one_snapshot_and_avoids_live_lookups() -> None:
    initial_snapshot = _registry().snapshot()

    class SnapshotOnlyRegistry:
        def __init__(self) -> None:
            self.snapshot_calls = 0

        def snapshot(self) -> EvidenceRegistrySnapshot:
            self.snapshot_calls += 1
            return initial_snapshot

        def resolve(self, source_id: str) -> EvidenceSourceRecord | None:
            raise AssertionError(f"live lookup forbidden: {source_id}")

        @property
        def snapshot_digest(self) -> str:
            raise AssertionError("live digest lookup forbidden")

    registry = SnapshotOnlyRegistry()
    second = _reference(
        reference_id="ref-2",
        source_id="source-b",
        source_digest=_SOURCE_B_DIGEST,
        fragment_id="fragment-c",
        fragment_digest=_FRAGMENT_C_DIGEST,
        span="chars:0-15",
        lineage_id="lineage-b",
    )
    receipt = EvidenceReferenceValidator(registry).validate(
        fact_id="fact-1",
        references=[_reference(), second],
    )
    assert registry.snapshot_calls == 1
    assert receipt.validated_reference_count == 2
    assert receipt.registry_snapshot_digest == initial_snapshot.snapshot_digest


def test_validator_rejects_non_snapshot_registry_view() -> None:
    class BadRegistry:
        def snapshot(self) -> object:
            return object()

    with pytest.raises(ValueError, match="EvidenceRegistrySnapshot"):
        EvidenceReferenceValidator(BadRegistry()).validate(  # type: ignore[arg-type]
            fact_id="fact-1",
            references=[_reference()],
        )


def test_receipt_cannot_assert_independence_without_authorized_policy() -> None:
    receipt = EvidenceReferenceValidator(_registry()).validate(
        fact_id="fact-1",
        references=[_reference()],
    )
    with pytest.raises(ValueError, match="authorized independence policy"):
        EvidenceValidationReceipt(
            fact_ref=receipt.fact_ref,
            policy_version=receipt.policy_version,
            reference_policy_version=receipt.reference_policy_version,
            registry_snapshot_digest=receipt.registry_snapshot_digest,
            raw_reference_count=1,
            unique_reference_count=1,
            validated_reference_count=1,
            distinct_independent_lineage_count=1,
            outcomes=receipt.outcomes,
        )


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
