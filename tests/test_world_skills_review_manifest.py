from __future__ import annotations

import hashlib
import json
import shutil
import unicodedata
from pathlib import Path

import pytest

from core.evidence_reference import EvidenceReference
from core.world_skills_review_manifest import (
    CANDIDATE_SOURCE_PATH,
    OWNER_REVIEW_MANIFEST_RELATIVE_PATH,
    WorldSkillsEvidenceResolver,
    WorldSkillsManifestError,
    canonical_text_v1,
)

SOURCE_ID = "wsc:ru:p0-formal-logic-math"
LINEAGE_ID = "lineage:wsc:ru:p0-formal-logic-math"
FACT_ID = "logic.identity"
CLAIM_TEXT = "A = A"
REVIEW = {
    "status": "attested_unverified",
    "reviewer_id": "reviewer.example",
    "reviewed_at": "2026-10-09T12:00:00Z",
    "approval_ref": "LOCAL-ATTESTATION:test-record",
}


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _write_source(root: Path, raw: bytes = b"A = A\nB = B\n") -> tuple[Path, str, str, str]:
    path = root / CANDIDATE_SOURCE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    canonical = unicodedata.normalize(
        "NFC", raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    )
    source_digest = _digest(raw)
    canonical_digest = _digest(canonical.encode("utf-8"))
    fragment_digest = _digest(canonical[0:5].encode("utf-8"))
    return path, source_digest, canonical_digest, fragment_digest


def _manifest(
    *,
    status: str = "active",
    source_review: dict[str, str] | None = None,
    fragment_digest: str | None = None,
    source_digest: str | None = None,
    canonical_digest: str | None = None,
    claim_reviews: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    root = _current_root
    _, actual_source_digest, actual_canonical_digest, actual_fragment_digest = _write_source(root)
    source = {
        "source_id": SOURCE_ID,
        "relative_path": CANDIDATE_SOURCE_PATH,
        "lineage_id": LINEAGE_ID,
        "status": status,
        "source_digest": source_digest or actual_source_digest,
        "canonical_text_digest": canonical_digest or actual_canonical_digest,
        "source_review": source_review or REVIEW.copy(),
        "fragments": [
            {
                "fragment_id": "logic-identity-fragment",
                "span": "chars:0-5",
                "fragment_digest": fragment_digest or actual_fragment_digest,
            }
        ],
    }
    return {
        "schema_version": 1,
        "canonical_text_policy_version": "world-skills-canonical-text-v1",
        "candidates": [],
        "sources": [source],
        "claim_support_reviews": claim_reviews or [],
    }


_current_root: Path


def _write_manifest(root: Path, document: dict[str, object]) -> None:
    path = root / OWNER_REVIEW_MANIFEST_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _reference(
    *,
    source_digest: str,
    fragment_digest: str,
    reference_id: str = "ref-logic-identity",
    span: str = "chars:0-5",
) -> EvidenceReference:
    return EvidenceReference(
        schema_version=1,
        reference_id=reference_id,
        source_id=SOURCE_ID,
        source_digest=source_digest,
        fragment_id="logic-identity-fragment",
        fragment_digest=fragment_digest,
        span=span,
        lineage_id=LINEAGE_ID,
        captured_at="2026-10-09T12:00:00Z",
    )


def _support_attestation_record(reference: EvidenceReference) -> dict[str, object]:
    return {
        "fact_id": FACT_ID,
        "claim_digest": _digest(CLAIM_TEXT.encode("utf-8")),
        "reference_id": reference.reference_id,
        "reference_digest": reference.reference_digest,
        "assessment": "supports",
        "review": REVIEW.copy(),
    }


@pytest.fixture(autouse=True)
def _temporary_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    global _current_root
    _current_root = tmp_path
    monkeypatch.chdir(tmp_path)


def test_canonical_text_v1_is_versioned_and_preserves_non_normalized_content() -> None:
    raw = "e\u0301\r\n  x \r".encode("utf-8")
    assert canonical_text_v1(raw) == "é\n  x \n"
    assert canonical_text_v1(raw).encode("utf-8") != raw
    with pytest.raises(WorldSkillsManifestError, match="strict UTF-8"):
        canonical_text_v1(b"\xff")
    with pytest.raises(WorldSkillsManifestError, match="BOM"):
        canonical_text_v1(b"\xef\xbb\xbftext")


def test_checked_in_candidate_is_pending_and_cannot_resolve_as_source() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    resolver = WorldSkillsEvidenceResolver.load(repo_root)
    source = (repo_root / CANDIDATE_SOURCE_PATH).read_bytes()
    canonical = canonical_text_v1(source)
    reference = _reference(
        source_digest=_digest(source),
        fragment_digest=_digest(canonical[0:5].encode("utf-8")),
    )

    result = resolver.resolve(reference, fact_id=FACT_ID, claim_text=CLAIM_TEXT)

    assert result.reference_state == "REFERENCE_UNRESOLVED"
    assert result.validation_status == "unknown_source"
    assert result.source_provenance_state == "SOURCE_PROVENANCE_NOT_ATTESTED"
    assert result.claim_support_state == "CLAIM_SUPPORT_NOT_ESTABLISHED"


def test_pending_candidate_bytes_are_pinned_and_stale_digest_fails_closed(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    candidate_root = tmp_path / "candidate-repo"
    candidate_path = candidate_root / CANDIDATE_SOURCE_PATH
    candidate_path.parent.mkdir(parents=True)
    shutil.copyfile(repo_root / CANDIDATE_SOURCE_PATH, candidate_path)
    manifest_path = candidate_root / OWNER_REVIEW_MANIFEST_RELATIVE_PATH
    manifest_path.parent.mkdir(parents=True)
    shutil.copyfile(repo_root / OWNER_REVIEW_MANIFEST_RELATIVE_PATH, manifest_path)
    candidate_path.write_bytes(candidate_path.read_bytes() + b"\n# local drift\n")

    with pytest.raises(
        WorldSkillsManifestError, match="pending candidate raw-byte digest mismatch"
    ):
        WorldSkillsEvidenceResolver.load(candidate_root)


def test_digest_and_owner_source_review_do_not_establish_claim_support() -> None:
    _, source_digest, _, fragment_digest = _write_source(_current_root)
    _write_manifest(_current_root, _manifest())
    resolver = WorldSkillsEvidenceResolver.load(_current_root)
    reference = _reference(source_digest=source_digest, fragment_digest=fragment_digest)

    result = resolver.resolve(reference, fact_id=FACT_ID, claim_text=CLAIM_TEXT)

    assert result.reference_state == "REFERENCE_RESOLVED"
    assert result.source_provenance_state == "SOURCE_PROVENANCE_ATTESTED_UNVERIFIED"
    assert result.claim_support_state == "CLAIM_SUPPORT_NOT_ESTABLISHED"
    assert result.validation_status == "accepted"
    assert not hasattr(resolver, "validate_and_promote")
    assert not hasattr(resolver, "store_fact")


def test_claim_support_requires_a_distinct_review_bound_to_claim_and_reference() -> None:
    _, source_digest, _, fragment_digest = _write_source(_current_root)
    ref = _reference(source_digest=source_digest, fragment_digest=fragment_digest)
    document = _manifest(claim_reviews=[_support_attestation_record(ref)])
    _write_manifest(_current_root, document)
    resolver = WorldSkillsEvidenceResolver.load(_current_root)

    exact = resolver.resolve(ref, fact_id=FACT_ID, claim_text=CLAIM_TEXT)
    changed_claim = resolver.resolve(ref, fact_id=FACT_ID, claim_text="A = B")
    changed_reference = resolver.resolve(
        _reference(
            source_digest=source_digest,
            fragment_digest=fragment_digest,
            reference_id="different-reference",
        ),
        fact_id=FACT_ID,
        claim_text=CLAIM_TEXT,
    )

    assert exact.claim_support_state == "CLAIM_SUPPORT_ATTESTED_UNVERIFIED"
    assert changed_claim.reference_state == "REFERENCE_RESOLVED"
    assert changed_claim.source_provenance_state == "SOURCE_PROVENANCE_ATTESTED_UNVERIFIED"
    assert changed_claim.claim_support_state == "CLAIM_SUPPORT_NOT_ESTABLISHED"
    assert changed_reference.claim_support_state == "CLAIM_SUPPORT_NOT_ESTABLISHED"


def test_pending_or_missing_review_provenance_fails_closed() -> None:
    _, source_digest, _, fragment_digest = _write_source(_current_root)
    pending = REVIEW | {"status": "pending"}
    _write_manifest(_current_root, _manifest(source_review=pending))

    with pytest.raises(WorldSkillsManifestError, match="status must be attested_unverified"):
        WorldSkillsEvidenceResolver.load(_current_root)

    # The checked-in candidate file is not an active source record at all.
    repo_root = Path(__file__).resolve().parents[1]
    candidate_resolver = WorldSkillsEvidenceResolver.load(repo_root)
    ref = _reference(source_digest=source_digest, fragment_digest=fragment_digest)
    result = candidate_resolver.resolve(ref, fact_id=FACT_ID, claim_text=CLAIM_TEXT)
    assert result.source_provenance_state == "SOURCE_PROVENANCE_NOT_ATTESTED"
    assert result.claim_support_state == "CLAIM_SUPPORT_NOT_ESTABLISHED"


def test_raw_canonical_and_fragment_digest_mismatches_are_rejected(tmp_path: Path) -> None:
    _, source_digest, canonical_digest, fragment_digest = _write_source(_current_root)
    wrong = "sha256:" + "0" * 64
    cases = [
        _manifest(source_digest=wrong),
        _manifest(canonical_digest=wrong),
        _manifest(fragment_digest=wrong),
    ]
    for document in cases:
        _write_manifest(_current_root, document)
        with pytest.raises(WorldSkillsManifestError, match="digest"):
            WorldSkillsEvidenceResolver.load(_current_root)
    assert source_digest != wrong and canonical_digest != wrong and fragment_digest != wrong


def test_source_revocation_blocks_new_resolution_but_does_not_rewrite_old_snapshot() -> None:
    _, source_digest, _, fragment_digest = _write_source(_current_root)
    ref = _reference(source_digest=source_digest, fragment_digest=fragment_digest)
    active_doc = _manifest(claim_reviews=[_support_attestation_record(ref)])
    _write_manifest(_current_root, active_doc)
    old_resolver = WorldSkillsEvidenceResolver.load(_current_root)
    old_result = old_resolver.resolve(ref, fact_id=FACT_ID, claim_text=CLAIM_TEXT)
    assert old_result.reference_state == "REFERENCE_RESOLVED"
    assert old_result.claim_support_state == "CLAIM_SUPPORT_ATTESTED_UNVERIFIED"

    revoked_doc = _manifest(status="revoked", claim_reviews=[_support_attestation_record(ref)])
    _write_manifest(_current_root, revoked_doc)
    new_resolver = WorldSkillsEvidenceResolver.load(_current_root)
    new_result = new_resolver.resolve(ref, fact_id=FACT_ID, claim_text=CLAIM_TEXT)

    assert new_result.source_status == "revoked"
    assert new_result.validation_status == "revoked_source"
    assert new_result.reference_state == "REFERENCE_UNRESOLVED"
    assert new_result.source_provenance_state == "SOURCE_PROVENANCE_ATTESTED_UNVERIFIED"
    assert new_result.claim_support_state == "CLAIM_SUPPORT_NOT_ESTABLISHED"
    # Resolver instances are immutable snapshots: reload is required to observe revocation.
    assert old_resolver.resolve(ref, fact_id=FACT_ID, claim_text=CLAIM_TEXT) == old_result


def test_revoked_tombstone_loads_without_original_source_file() -> None:
    source_path, source_digest, _, fragment_digest = _write_source(_current_root)
    ref = _reference(source_digest=source_digest, fragment_digest=fragment_digest)
    _write_manifest(_current_root, _manifest(status="revoked"))
    source_path.unlink()

    resolver = WorldSkillsEvidenceResolver.load(_current_root)
    result = resolver.resolve(ref, fact_id=FACT_ID, claim_text=CLAIM_TEXT)

    assert result.source_status == "revoked"
    assert result.validation_status == "revoked_source"
    assert result.reference_state == "REFERENCE_UNRESOLVED"
    assert result.source_provenance_state == "SOURCE_PROVENANCE_ATTESTED_UNVERIFIED"
    assert result.claim_support_state == "CLAIM_SUPPORT_NOT_ESTABLISHED"
    assert result.validation_receipt_digest.startswith("sha256:")


def test_textual_reviewer_fields_are_only_unverified_attestations() -> None:
    _, source_digest, _, fragment_digest = _write_source(_current_root)
    ref = _reference(source_digest=source_digest, fragment_digest=fragment_digest)
    document = _manifest(claim_reviews=[_support_attestation_record(ref)])
    _write_manifest(_current_root, document)

    result = WorldSkillsEvidenceResolver.load(_current_root).resolve(
        ref, fact_id=FACT_ID, claim_text=CLAIM_TEXT
    )

    assert result.validation_status == "accepted"  # local pointer/digest resolution only
    assert result.source_provenance_state == "SOURCE_PROVENANCE_ATTESTED_UNVERIFIED"
    assert result.claim_support_state == "CLAIM_SUPPORT_ATTESTED_UNVERIFIED"
    assert result.source_provenance_state != "SOURCE_PROVENANCE_VERIFIED"
    assert result.claim_support_state != "CLAIM_SUPPORT_ESTABLISHED"

    falsely_approved = _manifest(source_review=REVIEW | {"status": "approved"})
    _write_manifest(_current_root, falsely_approved)
    with pytest.raises(WorldSkillsManifestError, match="owner identity is not authenticated"):
        WorldSkillsEvidenceResolver.load(_current_root)


def test_manifest_rejects_unknown_paths_and_noncanonical_spans() -> None:
    _, source_digest, _, fragment_digest = _write_source(_current_root)
    document = _manifest()
    source = document["sources"][0]  # type: ignore[index]
    source["relative_path"] = "docs/knowledge/attacker.md"  # type: ignore[index]
    _write_manifest(_current_root, document)
    with pytest.raises(WorldSkillsManifestError, match="bounded candidate allowlist"):
        WorldSkillsEvidenceResolver.load(_current_root)

    document = _manifest()
    source = document["sources"][0]  # type: ignore[index]
    source["fragments"][0]["span"] = "chars:00-5"  # type: ignore[index]
    _write_manifest(_current_root, document)
    with pytest.raises(WorldSkillsManifestError, match="canonical ASCII"):
        WorldSkillsEvidenceResolver.load(_current_root)

    ref = _reference(source_digest=source_digest, fragment_digest=fragment_digest, span="chars:0-5")
    assert ref.span == "chars:0-5"
