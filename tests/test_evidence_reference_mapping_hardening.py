from collections.abc import Iterator, Mapping

import pytest

from core.evidence_reference import EvidenceReference, EvidenceReferenceError


class VanishingFieldMapping(Mapping[str, object]):
    """Mapping whose advertised key becomes unreadable during value access."""

    def __init__(self) -> None:
        self._payload = {
            "schema_version": 1,
            "reference_id": "ref-1",
            "source_id": "source-a",
            "source_digest": "sha256:" + "a" * 64,
            "fragment_id": "fragment-a",
            "fragment_digest": "sha256:" + "b" * 64,
            "span": "chars:0-10",
            "lineage_id": "lineage-a",
            "captured_at": "2026-08-19T00:00:00Z",
        }

    def __iter__(self) -> Iterator[str]:
        return iter(self._payload)

    def __len__(self) -> int:
        return len(self._payload)

    def __getitem__(self, key: str) -> object:
        if key == "fragment_id":
            raise KeyError(key)
        return self._payload[key]


def test_stateful_mapping_access_failure_is_normalized() -> None:
    with pytest.raises(
        EvidenceReferenceError,
        match="payload could not be read consistently",
    ):
        EvidenceReference.from_mapping(VanishingFieldMapping())
