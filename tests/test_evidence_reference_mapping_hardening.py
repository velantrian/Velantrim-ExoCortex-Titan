from collections.abc import Iterator, Mapping
from types import MappingProxyType

import pytest

from core.evidence_reference import EvidenceReference, EvidenceReferenceError

_VALID_PAYLOAD: dict[str, object] = {
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


class MappingReadFailure(Exception):
    """Project-local stand-in for unforeseen ordinary Mapping read failures."""


class ValueFailureMapping(Mapping[str, object]):
    """Mapping that fails while dict(payload) retrieves one advertised value."""

    def __init__(self, failure: BaseException) -> None:
        self._failure = failure

    def __iter__(self) -> Iterator[str]:
        return iter(_VALID_PAYLOAD)

    def __len__(self) -> int:
        return len(_VALID_PAYLOAD)

    def __getitem__(self, key: str) -> object:
        if key == "fragment_id":
            raise self._failure
        return _VALID_PAYLOAD[key]


class KeysFailureMapping(Mapping[str, object]):
    """Mapping that fails when dict(payload) asks for its keys surface."""

    def __init__(self, failure: BaseException) -> None:
        self._failure = failure

    def __iter__(self) -> Iterator[str]:
        return iter(_VALID_PAYLOAD)

    def __len__(self) -> int:
        return len(_VALID_PAYLOAD)

    def __getitem__(self, key: str) -> object:
        return _VALID_PAYLOAD[key]

    def keys(self):  # type: ignore[override]
        raise self._failure


class IterationFailureMapping(Mapping[str, object]):
    """Mapping that fails when inherited keys traversal reaches iteration."""

    def __init__(self, failure: BaseException) -> None:
        self._failure = failure

    def __iter__(self) -> Iterator[str]:
        raise self._failure

    def __len__(self) -> int:
        return len(_VALID_PAYLOAD)

    def __getitem__(self, key: str) -> object:
        return _VALID_PAYLOAD[key]


class StableMapping(Mapping[str, object]):
    """Ordinary custom Mapping used to prove supported-input compatibility."""

    def __iter__(self) -> Iterator[str]:
        return iter(_VALID_PAYLOAD)

    def __len__(self) -> int:
        return len(_VALID_PAYLOAD)

    def __getitem__(self, key: str) -> object:
        return _VALID_PAYLOAD[key]


@pytest.mark.parametrize(
    "failure",
    [
        KeyError("fragment_id"),
        TypeError("read failed"),
        ValueError("read failed"),
        RuntimeError("read failed"),
        AttributeError("read failed"),
        OSError("read failed"),
        IndexError("read failed"),
        MappingReadFailure("read failed"),
        ExceptionGroup("read failed", [AttributeError("x"), OSError("y")]),
    ],
)
def test_mapping_value_read_failures_are_normalized(failure: Exception) -> None:
    with pytest.raises(
        EvidenceReferenceError,
        match="payload could not be read consistently",
    ):
        EvidenceReference.from_mapping(ValueFailureMapping(failure))


@pytest.mark.parametrize(
    "payload",
    [
        KeysFailureMapping(AttributeError("read failed")),
        IterationFailureMapping(AttributeError("read failed")),
    ],
)
def test_mapping_snapshot_surface_failures_are_normalized(
    payload: Mapping[str, object],
) -> None:
    with pytest.raises(
        EvidenceReferenceError,
        match="payload could not be read consistently",
    ):
        EvidenceReference.from_mapping(payload)


@pytest.mark.parametrize(
    "failure_type",
    [KeyboardInterrupt, SystemExit, GeneratorExit, MemoryError],
)
def test_process_control_and_memory_failures_are_not_normalized(
    failure_type: type[BaseException],
) -> None:
    with pytest.raises(failure_type):
        EvidenceReference.from_mapping(ValueFailureMapping(failure_type()))


def test_valid_mapping_variants_preserve_reference_semantics() -> None:
    expected = EvidenceReference.from_mapping(_VALID_PAYLOAD)
    for payload in (StableMapping(), MappingProxyType(_VALID_PAYLOAD)):
        parsed = EvidenceReference.from_mapping(payload)
        assert parsed == expected
        assert parsed.reference_digest == expected.reference_digest


def test_non_mapping_iterable_is_still_rejected() -> None:
    with pytest.raises(EvidenceReferenceError, match="payload must be a mapping"):
        EvidenceReference.from_mapping(list(_VALID_PAYLOAD.items()))  # type: ignore[arg-type]
