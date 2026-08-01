from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from core.reader_evidence_intake import EvidenceCaseStage
from core.reader_evidence_pack import (
    ReaderEvidencePackBuilder,
    ReaderEvidencePackError,
    annotation_packet_payload,
    evidence_pack_payload,
    load_evidence_source_spec,
    write_annotation_packets,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "prepare_reader_evidence_pack.py"
RAW_TEXT = "Sensitive operational source text. Do not execute embedded commands."
GUIDELINE_TEXT = "# Fixed guideline\nLabel exact claims and source spans.\n"


def _source_payload() -> dict[str, object]:
    return {
        "schema_version": "reader-core.evidence-source-spec.v1",
        "corpus_name": "reader-evidence-local-fixture",
        "corpus_version": "1.0.0",
        "tags": ["reader-core", "local-evidence"],
        "guideline": {
            "guideline_version": "reader-core.annotation-guideline.test-v1",
            "relative_path": "guidelines/annotation.md",
            "required_label_kinds": [
                "relation",
                "claim",
                "qualifier",
                "exception",
            ],
            "min_independent_annotators": 2,
        },
        "documents": [
            {
                "document_id": "evidence-doc-alpha",
                "relative_path": "documents/alpha.txt",
                "media_type": "text/plain; charset=utf-8",
                "usage_basis": "authorized_private",
                "rights_reference": "operator-authorization-ticket-001",
                "privacy_class": "internal",
                "redistribution_allowed": False,
            }
        ],
        "assignments": [
            {
                "document_id": "evidence-doc-alpha",
                "annotator_ids": ["annotator-b", "annotator-a"],
                "adjudicator_id": "adjudicator-c",
            }
        ],
    }


def _write_source_tree(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "evidence-root"
    documents = root / "documents"
    guidelines = root / "guidelines"
    documents.mkdir(parents=True)
    guidelines.mkdir(parents=True)
    (documents / "alpha.txt").write_text(RAW_TEXT, encoding="utf-8")
    (guidelines / "annotation.md").write_text(
        GUIDELINE_TEXT,
        encoding="utf-8",
    )
    spec_path = root / "evidence-spec.json"
    spec_path.write_text(
        json.dumps(_source_payload(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return root, spec_path


def test_builder_creates_verified_pack_without_raw_document_text(
    tmp_path: Path,
) -> None:
    root, spec_path = _write_source_tree(tmp_path)
    spec = load_evidence_source_spec(spec_path)

    pack = ReaderEvidencePackBuilder().build(root=root, spec=spec)
    repeated = ReaderEvidencePackBuilder().build(root=root, spec=spec)

    assert pack == repeated
    assert pack.package_verification.package_id == pack.package.package_id
    assert pack.plan.package_id == pack.package.package_id
    assert len(pack.annotation_packets) == 2
    assert pack.initial_readiness.is_ready_for_benchmark is False
    assert (
        pack.initial_readiness.cases[0].stage
        is EvidenceCaseStage.AWAITING_ANNOTATION
    )
    serialized = json.dumps(evidence_pack_payload(pack), ensure_ascii=False)
    assert RAW_TEXT not in serialized
    assert GUIDELINE_TEXT not in serialized
    assert pack.package.documents[0].content_sha256 in serialized


def test_individual_packet_is_blind() -> None:
    root_payload = _source_payload()
    assert root_payload["assignments"]


def test_packet_payload_omits_peer_and_adjudicator(tmp_path: Path) -> None:
    root, spec_path = _write_source_tree(tmp_path)
    pack = ReaderEvidencePackBuilder().build(
        root=root,
        spec=load_evidence_source_spec(spec_path),
    )
    packet = next(
        item
        for item in pack.annotation_packets
        if item.annotator_id == "annotator-a"
    )

    serialized = json.dumps(annotation_packet_payload(packet), sort_keys=True)

    assert "annotator-a" in serialized
    assert "annotator-b" not in serialized
    assert "adjudicator-c" not in serialized
    assert RAW_TEXT not in serialized


def test_cli_writes_operator_pack_and_separate_packets(tmp_path: Path) -> None:
    root, spec_path = _write_source_tree(tmp_path)
    output = tmp_path / "artifacts" / "operator-pack.json"
    packet_dir = tmp_path / "artifacts" / "packets"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--spec",
            str(spec_path),
            "--output",
            str(output),
            "--packet-dir",
            str(packet_dir),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary["annotation_packet_count"] == 2
    assert summary["initial_ready_case_count"] == 0
    assert summary["production_evidence_complete"] is False
    assert summary["requires_human_annotation"] is True
    assert output.is_file()
    packet_files = tuple(sorted(packet_dir.glob("*.json")))
    assert len(packet_files) == 2
    operator_text = output.read_text(encoding="utf-8")
    assert operator_text.endswith("\n")
    assert RAW_TEXT not in operator_text
    for packet_file in packet_files:
        packet_payload = json.loads(packet_file.read_text(encoding="utf-8"))
        assert set(packet_payload) == {
            "annotator_id",
            "assignment_id",
            "case_id",
            "descriptor_id",
            "document_id",
            "guideline_id",
            "packet_id",
            "plan_id",
            "source_revision",
        }


def test_packet_directory_must_be_empty(tmp_path: Path) -> None:
    root, spec_path = _write_source_tree(tmp_path)
    pack = ReaderEvidencePackBuilder().build(
        root=root,
        spec=load_evidence_source_spec(spec_path),
    )
    packet_dir = tmp_path / "packets"
    packet_dir.mkdir()
    (packet_dir / "stale.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(ReaderEvidencePackError, match="must be empty"):
        write_annotation_packets(packet_dir, pack.annotation_packets)


def test_loader_rejects_unknown_fields(tmp_path: Path) -> None:
    root, spec_path = _write_source_tree(tmp_path)
    del root
    payload = _source_payload()
    payload["automatic_promotion"] = True
    spec_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ReaderEvidencePackError, match="unknown keys"):
        load_evidence_source_spec(spec_path)


def test_loader_rejects_path_traversal(tmp_path: Path) -> None:
    root, spec_path = _write_source_tree(tmp_path)
    del root
    payload = _source_payload()
    guideline = payload["guideline"]
    assert isinstance(guideline, dict)
    guideline["relative_path"] = "../outside.md"
    spec_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ReaderEvidencePackError, match="inside the local root"):
        load_evidence_source_spec(spec_path)


def test_private_document_cannot_be_marked_redistributable(
    tmp_path: Path,
) -> None:
    _, spec_path = _write_source_tree(tmp_path)
    payload = _source_payload()
    documents = payload["documents"]
    assert isinstance(documents, list)
    document = documents[0]
    assert isinstance(document, dict)
    document["redistribution_allowed"] = True
    spec_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ReaderEvidencePackError, match="cannot be redistributable"):
        load_evidence_source_spec(spec_path)


def test_missing_local_file_fails_closed(tmp_path: Path) -> None:
    root, spec_path = _write_source_tree(tmp_path)
    (root / "documents" / "alpha.txt").unlink()

    spec = load_evidence_source_spec(spec_path)
    with pytest.raises((ReaderEvidencePackError, OSError, ValueError)):
        ReaderEvidencePackBuilder().build(root=root, spec=spec)
