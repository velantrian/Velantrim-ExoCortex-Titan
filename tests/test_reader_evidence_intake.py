from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from core.knowledge_capsule import ClaimModality, SourceSpan
from core.reader_corpus_adjudication import (
    CorpusDocumentDescriptor,
    CorpusDocumentVerification,
    CorpusPackageManifest,
    CorpusPackageVerificationReceipt,
    CorpusPrivacyClass,
    CorpusUsageBasis,
    HumanClaimLabel,
    HumanLabelAdjudication,
    HumanLabelKind,
    HumanLabelSet,
    HumanLabelSetVerificationReceipt,
    LabelSetRole,
)
from core.reader_evidence_intake import (
    EvidenceCaseStage,
    ReaderAnnotationGuidelineSpec,
    ReaderEvidenceIntakeError,
    ReaderEvidenceProgramPlanner,
    ReaderEvidenceReadinessEvaluator,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
GUIDELINE_PATH = (
    REPO_ROOT / "docs" / "research" / "READER_CORE_ANNOTATION_GUIDELINE_V1.md"
)
RAW_TEXT = "Policy Alpha applies to standard requests."


def _descriptor() -> CorpusDocumentDescriptor:
    digest = sha256(RAW_TEXT.encode("utf-8")).hexdigest()
    return CorpusDocumentDescriptor(
        document_id="evidence-policy-alpha",
        relative_path="documents/policy-alpha.txt",
        source_revision=digest,
        content_sha256=digest,
        byte_size=len(RAW_TEXT.encode("utf-8")),
        char_count=len(RAW_TEXT),
        media_type="text/plain; charset=utf-8",
        usage_basis=CorpusUsageBasis.SYNTHETIC,
        rights_reference="project-authored-evidence-fixture",
        privacy_class=CorpusPrivacyClass.PUBLIC,
        redistribution_allowed=True,
    )


def _package() -> CorpusPackageManifest:
    return CorpusPackageManifest(
        corpus_name="reader-evidence-fixture",
        corpus_version="1.0.0",
        documents=(_descriptor(),),
        tags=("evidence-intake", "reader-core"),
    )


def _guideline() -> ReaderAnnotationGuidelineSpec:
    digest = sha256(GUIDELINE_PATH.read_bytes()).hexdigest()
    return ReaderAnnotationGuidelineSpec(
        guideline_version="reader-core.annotation-guideline.v1",
        content_sha256=digest,
        required_label_kinds=tuple(
            sorted(tuple(HumanLabelKind), key=lambda item: item.value)
        ),
    )


def _plan(*, annotators: tuple[str, ...] = ("annotator-a", "annotator-b")):
    package = _package()
    plan = ReaderEvidenceProgramPlanner.create_plan(
        package=package,
        guideline=_guideline(),
        annotator_ids_by_document={
            package.documents[0].document_id: annotators,
        },
        adjudicator_ids_by_document={
            package.documents[0].document_id: "adjudicator-c",
        },
    )
    return package, plan


def _claim(descriptor: CorpusDocumentDescriptor) -> HumanClaimLabel:
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


def _label_set(
    descriptor: CorpusDocumentDescriptor,
    *,
    annotator_id: str,
    role: LabelSetRole,
    guideline_version: str = "reader-core.annotation-guideline.v1",
) -> HumanLabelSet:
    return HumanLabelSet(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        annotator_id=annotator_id,
        guideline_version=guideline_version,
        label_version="reader-evidence-labels-v1",
        role=role,
        claims=(_claim(descriptor),),
    )


def _evidence_sets():
    descriptor = _descriptor()
    set_a = _label_set(
        descriptor,
        annotator_id="annotator-a",
        role=LabelSetRole.ANNOTATOR,
    )
    set_b = _label_set(
        descriptor,
        annotator_id="annotator-b",
        role=LabelSetRole.ANNOTATOR,
    )
    final_set = _label_set(
        descriptor,
        annotator_id="adjudicator-c",
        role=LabelSetRole.ADJUDICATED,
    )
    adjudication = HumanLabelAdjudication(
        source_label_sets=tuple(
            sorted((set_a, set_b), key=lambda item: item.label_set_id)
        ),
        adjudicator_id="adjudicator-c",
        adjudicated_label_set=final_set,
        resolutions=(),
    )
    return set_a, set_b, final_set, adjudication


def _package_verification(
    package: CorpusPackageManifest,
) -> CorpusPackageVerificationReceipt:
    descriptor = package.documents[0]
    entry = CorpusDocumentVerification.create(
        descriptor_id=descriptor.descriptor_id,
        document_id=descriptor.document_id,
        content_sha256=descriptor.content_sha256,
        byte_size=descriptor.byte_size,
        char_count=descriptor.char_count,
    )
    return CorpusPackageVerificationReceipt.create(
        package_id=package.package_id,
        entries=(entry,),
    )


def _label_verification(
    label_set: HumanLabelSet,
) -> HumanLabelSetVerificationReceipt:
    span_ids = tuple(
        sorted(
            span.span_id
            for claim in label_set.claims
            for span in claim.source_spans
        )
    )
    return HumanLabelSetVerificationReceipt.create(
        label_set_id=label_set.label_set_id,
        descriptor_id=label_set.document_descriptor_id,
        verified_span_ids=span_ids,
    )


def test_annotation_packets_are_blind_and_deterministic() -> None:
    _, plan = _plan()

    packets = ReaderEvidenceProgramPlanner.build_annotation_packets(plan)
    repeated = ReaderEvidenceProgramPlanner.build_annotation_packets(plan)

    assert packets == repeated
    assert len(packets) == 2
    packet_a = next(item for item in packets if item.annotator_id == "annotator-a")
    payload = repr(packet_a.identity_payload())
    assert "annotator-b" not in payload
    assert "adjudicator-c" not in payload
    assert packet_a.guideline_id == plan.guideline.guideline_id


def test_readiness_progresses_fail_closed_to_benchmark_ready() -> None:
    package, plan = _plan()
    set_a, set_b, final_set, adjudication = _evidence_sets()
    evaluator = ReaderEvidenceReadinessEvaluator()

    unverified = evaluator.evaluate(plan=plan, package=package)
    assert (
        unverified.cases[0].stage
        is EvidenceCaseStage.AWAITING_PACKAGE_VERIFICATION
    )
    assert "missing_package_verification" in unverified.cases[0].blockers

    package_receipt = _package_verification(package)
    awaiting_annotation = evaluator.evaluate(
        plan=plan,
        package=package,
        package_verification=package_receipt,
    )
    assert (
        awaiting_annotation.cases[0].stage
        is EvidenceCaseStage.AWAITING_ANNOTATION
    )
    assert awaiting_annotation.cases[0].missing_annotator_ids == (
        "annotator-a",
        "annotator-b",
    )

    awaiting_adjudication = evaluator.evaluate(
        plan=plan,
        package=package,
        package_verification=package_receipt,
        annotation_sets=(set_a, set_b),
    )
    assert (
        awaiting_adjudication.cases[0].stage
        is EvidenceCaseStage.AWAITING_ADJUDICATION
    )
    assert "missing_adjudication" in awaiting_adjudication.cases[0].blockers

    awaiting_verification = evaluator.evaluate(
        plan=plan,
        package=package,
        package_verification=package_receipt,
        annotation_sets=(set_a, set_b),
        adjudications=(adjudication,),
    )
    assert (
        awaiting_verification.cases[0].stage
        is EvidenceCaseStage.AWAITING_LABEL_VERIFICATION
    )
    assert len(awaiting_verification.cases[0].blockers) == 3

    ready = evaluator.evaluate(
        plan=plan,
        package=package,
        package_verification=package_receipt,
        annotation_sets=(set_a, set_b),
        adjudications=(adjudication,),
        label_verifications=(
            _label_verification(set_a),
            _label_verification(set_b),
            _label_verification(final_set),
        ),
    )
    assert ready.is_ready_for_benchmark is True
    assert ready.cases[0].stage is EvidenceCaseStage.READY_FOR_BENCHMARK
    assert ready.cases[0].blockers == ()
    assert ready.ready_case_ids == (plan.assignments[0].case_id,)


def test_adjudication_packet_requires_every_assigned_annotation() -> None:
    _, plan = _plan()
    set_a, set_b, _, _ = _evidence_sets()
    case_id = plan.assignments[0].case_id

    with pytest.raises(
        ReaderEvidenceIntakeError,
        match="requires all assigned",
    ):
        ReaderEvidenceProgramPlanner.build_adjudication_packet(
            plan=plan,
            case_id=case_id,
            annotation_sets=(set_a,),
        )

    packet = ReaderEvidenceProgramPlanner.build_adjudication_packet(
        plan=plan,
        case_id=case_id,
        annotation_sets=(set_a, set_b),
    )
    assert packet.adjudicator_id == "adjudicator-c"
    assert packet.source_label_set_ids == tuple(
        sorted((set_a.label_set_id, set_b.label_set_id))
    )


def test_wrong_guideline_and_unassigned_annotator_are_rejected() -> None:
    package, plan = _plan()
    set_a, _, _, _ = _evidence_sets()
    evaluator = ReaderEvidenceReadinessEvaluator()
    package_receipt = _package_verification(package)

    wrong_guideline = replace(
        set_a,
        label_set_id="",
        guideline_version="reader-core.annotation-guideline.v2",
    )
    with pytest.raises(ReaderEvidenceIntakeError, match="guideline version"):
        evaluator.evaluate(
            plan=plan,
            package=package,
            package_verification=package_receipt,
            annotation_sets=(wrong_guideline,),
        )

    outsider = replace(
        set_a,
        label_set_id="",
        annotator_id="annotator-outsider",
    )
    with pytest.raises(ReaderEvidenceIntakeError, match="unassigned"):
        evaluator.evaluate(
            plan=plan,
            package=package,
            package_verification=package_receipt,
            annotation_sets=(outsider,),
        )


def test_adjudication_must_use_exact_assignment_roster() -> None:
    package, plan = _plan(
        annotators=("annotator-a", "annotator-b", "annotator-d")
    )
    _, _, _, adjudication = _evidence_sets()

    with pytest.raises(ReaderEvidenceIntakeError, match="exactly the assigned"):
        ReaderEvidenceReadinessEvaluator().evaluate(
            plan=plan,
            package=package,
            package_verification=_package_verification(package),
            adjudications=(adjudication,),
        )


def test_content_addressed_identities_reject_forgery() -> None:
    _, plan = _plan()

    with pytest.raises(ReaderEvidenceIntakeError, match="plan_id"):
        replace(plan, plan_id="forged-plan")

    packet = ReaderEvidenceProgramPlanner.build_annotation_packets(plan)[0]
    with pytest.raises(ReaderEvidenceIntakeError, match="packet_id"):
        replace(packet, packet_id="forged-packet")


def test_unknown_label_verification_is_rejected() -> None:
    package, plan = _plan()
    set_a, _, _, _ = _evidence_sets()
    forged_receipt = HumanLabelSetVerificationReceipt.create(
        label_set_id="unknown-label-set",
        descriptor_id=set_a.document_descriptor_id,
        verified_span_ids=(set_a.claims[0].source_spans[0].span_id,),
    )

    with pytest.raises(ReaderEvidenceIntakeError, match="unknown label set"):
        ReaderEvidenceReadinessEvaluator().evaluate(
            plan=plan,
            package=package,
            package_verification=_package_verification(package),
            annotation_sets=(set_a,),
            label_verifications=(forged_receipt,),
        )
