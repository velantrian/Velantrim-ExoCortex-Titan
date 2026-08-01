from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import pytest

from core.knowledge_capsule import ClaimModality, SourceSpan
from core.reader_corpus_adjudication import (
    HumanClaimLabel,
    HumanLabelAdjudication,
    HumanLabelKind,
    HumanLabelSet,
    LabelSetRole,
)
from core.reader_evidence_import import (
    ReaderAdjudicationSubmission,
    ReaderAnnotationSubmission,
    ReaderEvidenceImportError,
    ReaderEvidenceImporter,
)
from core.reader_evidence_intake import EvidenceCaseStage
from core.reader_evidence_pack import (
    ReaderEvidencePackBuilder,
    load_evidence_source_spec,
    write_canonical_json,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "import_reader_evidence.py"
RAW_TEXT = "Policy Alpha applies to standard requests."
GUIDELINE_TEXT = "# Test guideline\nLabel exact claims and spans.\n"


def _source_payload() -> dict[str, object]:
    return {
        "schema_version": "reader-core.evidence-source-spec.v1",
        "corpus_name": "reader-evidence-import-fixture",
        "corpus_version": "1.0.0",
        "tags": ["evidence-import", "reader-core"],
        "guideline": {
            "guideline_version": "reader-core.annotation-guideline.test-v1",
            "relative_path": "guidelines/annotation.md",
            "required_label_kinds": [
                "claim",
                "exception",
                "qualifier",
                "relation",
            ],
            "min_independent_annotators": 2,
        },
        "documents": [
            {
                "document_id": "evidence-policy-alpha",
                "relative_path": "documents/policy-alpha.txt",
                "media_type": "text/plain; charset=utf-8",
                "usage_basis": "synthetic",
                "rights_reference": "project-authored-test-fixture",
                "privacy_class": "public",
                "redistribution_allowed": True,
            }
        ],
        "assignments": [
            {
                "document_id": "evidence-policy-alpha",
                "annotator_ids": ["annotator-a", "annotator-b"],
                "adjudicator_id": "adjudicator-c",
            }
        ],
    }


def _source_tree(tmp_path: Path):
    root = tmp_path / "evidence-root"
    (root / "documents").mkdir(parents=True)
    (root / "guidelines").mkdir(parents=True)
    (root / "documents" / "policy-alpha.txt").write_text(
        RAW_TEXT,
        encoding="utf-8",
    )
    (root / "guidelines" / "annotation.md").write_text(
        GUIDELINE_TEXT,
        encoding="utf-8",
    )
    spec_path = root / "evidence-spec.json"
    spec_path.write_text(
        json.dumps(_source_payload(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    spec = load_evidence_source_spec(spec_path)
    pack = ReaderEvidencePackBuilder().build(root=root, spec=spec)
    return root, spec_path, pack


def _claim(pack) -> HumanClaimLabel:
    descriptor = pack.package.documents[0]
    span = SourceSpan.from_text(
        document_id=descriptor.document_id,
        raw_text=RAW_TEXT,
        start_offset=0,
        end_offset=len(RAW_TEXT),
        source_revision=descriptor.source_revision,
    )
    return HumanClaimLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=ClaimModality.WORLD_FACT,
        source_spans=(span,),
    )


def _label_set(pack, *, actor_id: str, role: LabelSetRole) -> HumanLabelSet:
    descriptor = pack.package.documents[0]
    return HumanLabelSet(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        annotator_id=actor_id,
        guideline_version=pack.guideline.guideline_version,
        label_version="reader-evidence-import-labels-v1",
        role=role,
        claims=(_claim(pack),),
    )


def _annotation_submissions(pack):
    result = []
    for packet in pack.annotation_packets:
        label_set = _label_set(
            pack,
            actor_id=packet.annotator_id,
            role=LabelSetRole.ANNOTATOR,
        )
        result.append(
            ReaderAnnotationSubmission(
                packet_id=packet.packet_id,
                label_set=label_set,
            )
        )
    return tuple(sorted(result, key=lambda item: item.packet_id))


def _adjudication_submission(pack, annotations):
    source_sets = tuple(
        sorted(
            (item.label_set for item in annotations),
            key=lambda item: item.label_set_id,
        )
    )
    final_set = _label_set(
        pack,
        actor_id="adjudicator-c",
        role=LabelSetRole.ADJUDICATED,
    )
    adjudication = HumanLabelAdjudication(
        source_label_sets=source_sets,
        adjudicator_id="adjudicator-c",
        adjudicated_label_set=final_set,
        resolutions=(),
    )
    return ReaderAdjudicationSubmission(
        case_id=pack.plan.assignments[0].case_id,
        adjudicator_id="adjudicator-c",
        source_label_set_ids=tuple(
            sorted(item.label_set_id for item in source_sets)
        ),
        adjudicated_label_set=final_set,
        resolutions=(),
        adjudication_id=adjudication.adjudication_id,
    )


def _write_submissions(directory: Path, values) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for index, value in enumerate(values):
        write_canonical_json(directory / f"submission-{index:02d}.json", value)


def test_empty_return_directory_remains_awaiting_annotation(
    tmp_path: Path,
) -> None:
    root, _, pack = _source_tree(tmp_path)
    returns = tmp_path / "returns"
    returns.mkdir()

    bundle = ReaderEvidenceImporter().import_directory(
        root=root,
        pack=pack,
        submission_directory=returns,
    )

    assert bundle.annotation_submissions == ()
    assert bundle.adjudication_submissions == ()
    assert bundle.label_verifications == ()
    assert bundle.readiness.is_ready_for_benchmark is False
    assert (
        bundle.readiness.cases[0].stage
        is EvidenceCaseStage.AWAITING_ANNOTATION
    )


def test_import_progresses_to_adjudication_then_ready(tmp_path: Path) -> None:
    root, _, pack = _source_tree(tmp_path)
    annotations = _annotation_submissions(pack)
    returns = tmp_path / "returns"

    _write_submissions(returns, annotations[:1])
    partial = ReaderEvidenceImporter().import_directory(
        root=root,
        pack=pack,
        submission_directory=returns,
    )
    assert partial.readiness.cases[0].stage is EvidenceCaseStage.AWAITING_ANNOTATION
    assert len(partial.label_verifications) == 1

    for item in returns.iterdir():
        item.unlink()
    _write_submissions(returns, annotations)
    annotated = ReaderEvidenceImporter().import_directory(
        root=root,
        pack=pack,
        submission_directory=returns,
    )
    assert (
        annotated.readiness.cases[0].stage
        is EvidenceCaseStage.AWAITING_ADJUDICATION
    )
    assert len(annotated.label_verifications) == 2

    adjudication = _adjudication_submission(pack, annotations)
    for item in returns.iterdir():
        item.unlink()
    _write_submissions(returns, (*annotations, adjudication))
    ready = ReaderEvidenceImporter().import_directory(
        root=root,
        pack=pack,
        submission_directory=returns,
    )

    assert ready.readiness.is_ready_for_benchmark is True
    assert ready.readiness.cases[0].stage is EvidenceCaseStage.READY_FOR_BENCHMARK
    assert len(ready.annotation_submissions) == 2
    assert len(ready.adjudication_submissions) == 1
    assert len(ready.label_verifications) == 3


def test_import_is_deterministic(tmp_path: Path) -> None:
    root, _, pack = _source_tree(tmp_path)
    annotations = _annotation_submissions(pack)
    adjudication = _adjudication_submission(pack, annotations)
    returns = tmp_path / "returns"
    _write_submissions(returns, (*annotations, adjudication))

    first = ReaderEvidenceImporter().import_directory(
        root=root,
        pack=pack,
        submission_directory=returns,
    )
    second = ReaderEvidenceImporter().import_directory(
        root=root,
        pack=pack,
        submission_directory=returns,
    )

    assert first == second
    assert first.bundle_id == second.bundle_id


def test_forged_packet_is_rejected(tmp_path: Path) -> None:
    root, _, pack = _source_tree(tmp_path)
    submission = _annotation_submissions(pack)[0]
    forged = replace(submission, packet_id="foreign-packet", submission_id="")
    returns = tmp_path / "returns"
    _write_submissions(returns, (forged,))

    with pytest.raises(ReaderEvidenceImportError, match="foreign packet"):
        ReaderEvidenceImporter().import_directory(
            root=root,
            pack=pack,
            submission_directory=returns,
        )


def test_tampered_span_fails_local_verification(tmp_path: Path) -> None:
    root, _, pack = _source_tree(tmp_path)
    submission = _annotation_submissions(pack)[0]
    claim = submission.label_set.claims[0]
    span = claim.source_spans[0]
    tampered_span = replace(span, content_hash="0" * 64)
    tampered_claim = replace(
        claim,
        label_id="",
        source_spans=(tampered_span,),
    )
    tampered_set = replace(
        submission.label_set,
        label_set_id="",
        claims=(tampered_claim,),
    )
    tampered_submission = ReaderAnnotationSubmission(
        packet_id=submission.packet_id,
        label_set=tampered_set,
    )
    returns = tmp_path / "returns"
    _write_submissions(returns, (tampered_submission,))

    with pytest.raises(ReaderEvidenceImportError, match="span verification failed"):
        ReaderEvidenceImporter().import_directory(
            root=root,
            pack=pack,
            submission_directory=returns,
        )


def test_adjudication_requires_imported_source_sets(tmp_path: Path) -> None:
    root, _, pack = _source_tree(tmp_path)
    annotations = _annotation_submissions(pack)
    adjudication = _adjudication_submission(pack, annotations)
    returns = tmp_path / "returns"
    _write_submissions(returns, (adjudication,))

    with pytest.raises(
        ReaderEvidenceImportError,
        match="has not been imported",
    ):
        ReaderEvidenceImporter().import_directory(
            root=root,
            pack=pack,
            submission_directory=returns,
        )


def test_cli_reports_incomplete_and_require_ready_exit(tmp_path: Path) -> None:
    root, spec_path, _ = _source_tree(tmp_path)
    returns = tmp_path / "returns"
    returns.mkdir()
    output = tmp_path / "readiness.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--spec",
            str(spec_path),
            "--submission-dir",
            str(returns),
            "--output",
            str(output),
            "--require-ready",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 3, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary["is_ready_for_benchmark"] is False
    assert summary["benchmark_executed"] is False
    assert summary["live_integration_authorized"] is False
    assert summary["stage_counts"] == {"awaiting_annotation": 1}
    assert output.is_file()


def test_cli_reports_ready_without_executing_benchmark(tmp_path: Path) -> None:
    root, spec_path, pack = _source_tree(tmp_path)
    annotations = _annotation_submissions(pack)
    adjudication = _adjudication_submission(pack, annotations)
    returns = tmp_path / "returns"
    _write_submissions(returns, (*annotations, adjudication))
    output = tmp_path / "readiness.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--spec",
            str(spec_path),
            "--submission-dir",
            str(returns),
            "--output",
            str(output),
            "--require-ready",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary["is_ready_for_benchmark"] is True
    assert summary["annotation_submission_count"] == 2
    assert summary["adjudication_submission_count"] == 1
    assert summary["label_verification_count"] == 3
    assert summary["benchmark_executed"] is False
    assert output.read_text(encoding="utf-8").endswith("\n")


def test_non_json_return_file_is_rejected(tmp_path: Path) -> None:
    root, _, pack = _source_tree(tmp_path)
    returns = tmp_path / "returns"
    returns.mkdir()
    (returns / "notes.txt").write_text("ignored? no.", encoding="utf-8")

    with pytest.raises(ReaderEvidenceImportError, match="only JSON files"):
        ReaderEvidenceImporter().import_directory(
            root=root,
            pack=pack,
            submission_directory=returns,
        )
