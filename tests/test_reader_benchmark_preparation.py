from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from core.knowledge_capsule import ClaimModality, SourceSpan
from core.reader_benchmark_preparation import (
    ReaderBenchmarkPreparationBuilder,
    ReaderBenchmarkPreparationError,
)
from core.reader_corpus_adjudication import (
    HumanClaimLabel,
    HumanLabelAdjudication,
    HumanLabelSet,
    LabelSetRole,
)
from core.reader_evidence_import import (
    ReaderAdjudicationSubmission,
    ReaderAnnotationSubmission,
    ReaderEvidenceImporter,
)
from core.reader_evidence_pack import (
    ReaderEvidencePackBuilder,
    load_evidence_source_spec,
    write_canonical_json,
)
from core.reader_evaluation import EvaluationCorpusKind


RAW_TEXT = "Policy Alpha applies to standard requests."
GUIDELINE_TEXT = "# Test guideline\nLabel exact claims and spans.\n"


def _source_payload() -> dict[str, object]:
    return {
        "schema_version": "reader-core.evidence-source-spec.v1",
        "corpus_name": "reader-benchmark-preparation-fixture",
        "corpus_version": "1.0.0",
        "tags": ["reader-core", "preparation"],
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
    pack = ReaderEvidencePackBuilder().build(
        root=root,
        spec=load_evidence_source_spec(spec_path),
    )
    return root, pack


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
        label_version="reader-preparation-labels-v1",
        role=role,
        claims=(_claim(pack),),
    )


def _submissions(pack):
    annotations = tuple(
        ReaderAnnotationSubmission(
            packet_id=packet.packet_id,
            label_set=_label_set(
                pack,
                actor_id=packet.annotator_id,
                role=LabelSetRole.ANNOTATOR,
            ),
        )
        for packet in pack.annotation_packets
    )
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
    typed_adjudication = HumanLabelAdjudication(
        source_label_sets=source_sets,
        adjudicator_id="adjudicator-c",
        adjudicated_label_set=final_set,
        resolutions=(),
    )
    adjudication = ReaderAdjudicationSubmission(
        case_id=pack.plan.assignments[0].case_id,
        adjudicator_id="adjudicator-c",
        source_label_set_ids=tuple(
            sorted(item.label_set_id for item in source_sets)
        ),
        adjudicated_label_set=final_set,
        resolutions=(),
        adjudication_id=typed_adjudication.adjudication_id,
    )
    return annotations, adjudication


def _ready_import(tmp_path: Path):
    root, pack = _source_tree(tmp_path)
    annotations, adjudication = _submissions(pack)
    returns = tmp_path / "returns"
    returns.mkdir()
    for index, value in enumerate((*annotations, adjudication)):
        write_canonical_json(returns / f"submission-{index}.json", value)
    imported = ReaderEvidenceImporter().import_directory(
        root=root,
        pack=pack,
        submission_directory=returns,
    )
    return root, pack, imported


def test_ready_evidence_builds_cases_manifest_batch_and_checkpoint(
    tmp_path: Path,
) -> None:
    _, pack, imported = _ready_import(tmp_path)

    prepared = ReaderBenchmarkPreparationBuilder().prepare(
        pack=pack,
        imported=imported,
        environment_id="environment-fixed-001",
        thresholds_id="thresholds-fixed-001",
        max_attempts_per_case=2,
        extra_tags=("pilot",),
    )

    assert len(prepared.prepared_cases) == 1
    case = prepared.prepared_cases[0]
    gold = case.benchmark_case.gold
    assert case.evidence_case_id == pack.plan.assignments[0].case_id
    assert case.benchmark_case.case_id == gold.document_id
    assert case.evaluation_manifest.case_id == gold.document_id
    assert (
        case.evaluation_manifest.corpus_kind
        is EvaluationCorpusKind.HUMAN_LABELLED
    )
    assert case.evaluation_manifest.expected_claim_count == 1
    assert case.evaluation_manifest.expected_source_span_count == 1
    assert case.evaluation_manifest.expected_exception_count == 0
    assert case.evaluation_manifest.expected_relation_count == 0
    assert case.evaluation_manifest.expected_contradiction_count == 0
    assert case.evaluation_manifest.expected_qualifier_count == 0
    assert case.evaluation_manifest.tags == (
        "human-adjudicated",
        "pilot",
        "preparation",
        "reader-core",
    )
    assert prepared.batch_plan.corpus_id == prepared.evaluation_manifest.corpus_id
    assert prepared.batch_plan.case_ids == (gold.document_id,)
    assert prepared.batch_plan.environment_id == "environment-fixed-001"
    assert prepared.batch_plan.threshold_policy_id == "thresholds-fixed-001"
    assert prepared.batch_plan.max_attempts_per_case == 2
    assert prepared.initial_checkpoint.plan == prepared.batch_plan
    assert prepared.initial_checkpoint.receipts == ()
    assert prepared.local_cases == (case.benchmark_case,)


def test_preparation_is_deterministic(tmp_path: Path) -> None:
    _, pack, imported = _ready_import(tmp_path)
    builder = ReaderBenchmarkPreparationBuilder()

    first = builder.prepare(
        pack=pack,
        imported=imported,
        environment_id="environment-fixed-001",
        thresholds_id="thresholds-fixed-001",
    )
    second = builder.prepare(
        pack=pack,
        imported=imported,
        environment_id="environment-fixed-001",
        thresholds_id="thresholds-fixed-001",
    )

    assert first == second
    assert first.preparation_id == second.preparation_id


def test_incomplete_evidence_is_rejected(tmp_path: Path) -> None:
    root, pack = _source_tree(tmp_path)
    returns = tmp_path / "returns"
    returns.mkdir()
    imported = ReaderEvidenceImporter().import_directory(
        root=root,
        pack=pack,
        submission_directory=returns,
    )

    with pytest.raises(
        ReaderBenchmarkPreparationError,
        match="must be ready",
    ):
        ReaderBenchmarkPreparationBuilder().prepare(
            pack=pack,
            imported=imported,
            environment_id="environment-fixed-001",
            thresholds_id="thresholds-fixed-001",
        )


def test_foreign_evidence_pack_is_rejected(tmp_path: Path) -> None:
    _, pack, imported = _ready_import(tmp_path)
    foreign_pack = replace(pack, pack_id="foreign-pack")

    with pytest.raises(
        ReaderBenchmarkPreparationError,
        match="different evidence pack",
    ):
        ReaderBenchmarkPreparationBuilder().prepare(
            pack=foreign_pack,
            imported=imported,
            environment_id="environment-fixed-001",
            thresholds_id="thresholds-fixed-001",
        )


def test_missing_adjudication_coverage_is_rejected(tmp_path: Path) -> None:
    _, pack, imported = _ready_import(tmp_path)
    forged_import = replace(
        imported,
        bundle_id="",
        adjudication_submissions=(),
    )

    with pytest.raises(
        ReaderBenchmarkPreparationError,
        match="exactly cover",
    ):
        ReaderBenchmarkPreparationBuilder().prepare(
            pack=pack,
            imported=forged_import,
            environment_id="environment-fixed-001",
            thresholds_id="thresholds-fixed-001",
        )


def test_forged_preparation_identity_is_rejected(tmp_path: Path) -> None:
    _, pack, imported = _ready_import(tmp_path)
    prepared = ReaderBenchmarkPreparationBuilder().prepare(
        pack=pack,
        imported=imported,
        environment_id="environment-fixed-001",
        thresholds_id="thresholds-fixed-001",
    )

    with pytest.raises(ReaderBenchmarkPreparationError, match="preparation_id"):
        replace(prepared, preparation_id="forged-preparation")


def test_duplicate_extra_tags_are_rejected(tmp_path: Path) -> None:
    _, pack, imported = _ready_import(tmp_path)

    with pytest.raises(ReaderBenchmarkPreparationError, match="tag values"):
        ReaderBenchmarkPreparationBuilder().prepare(
            pack=pack,
            imported=imported,
            environment_id="environment-fixed-001",
            thresholds_id="thresholds-fixed-001",
            extra_tags=("pilot", "pilot"),
        )
