"""Test-only builders for strict TruthGate EvidenceReference v1 fixtures."""
from __future__ import annotations

_SOURCE_DIGEST = "sha256:" + "a" * 64
_FRAGMENT_DIGEST = "sha256:" + "b" * 64


def typed_evidence_ref(index: int, *, prefix: str = "test") -> dict:
    return {
        "schema_version": 1,
        "reference_id": f"{prefix}-ref-{index}",
        "source_id": f"{prefix}-source-{index}",
        "source_digest": _SOURCE_DIGEST,
        "fragment_id": f"{prefix}-fragment-{index}",
        "fragment_digest": _FRAGMENT_DIGEST,
        "span": f"chars:{index * 10}-{index * 10 + 5}",
        "lineage_id": f"{prefix}-lineage-{index}",
        "captured_at": "2026-09-23T00:00:00Z",
    }


def typed_evidence_refs(count: int, *, prefix: str = "test") -> list[dict]:
    return [typed_evidence_ref(i + 1, prefix=prefix) for i in range(count)]
