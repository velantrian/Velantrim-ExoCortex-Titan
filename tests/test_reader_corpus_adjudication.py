from dataclasses import replace
from pathlib import Path

import pytest

from core.critical_exceptions import ExceptionCategory
from core.knowledge_capsule import ClaimModality, SourceSpan
from core.reader_core_contracts import RelationKind
from core.reader_corpus_adjudication import (
    AdjudicationResolution,
    CorpusDocumentDescriptor,
    CorpusPackageManifest,
    CorpusPrivacyClass,
    CorpusUsageBasis,
    HumanClaimLabel,
    HumanExceptionLabel,
    HumanLabelAdjudication,
    HumanLabelEvaluationManifestBuilder,
    HumanLabelKind,
    HumanLabelSet,
    HumanQualifierLabel,
    HumanRelationLabel,
    LabelSetRole,
    QualifierKind,
    ReaderCorpusError,
)
from core.reader_evaluation import EvaluationCorpusKind


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "reader_core"
DOCUMENT_NAME = "rdr_11_synthetic_document.txt"


def _descriptor() -> CorpusDocumentDescriptor:
    return CorpusDocumentDescriptor.from_file(
        root=FIXTURE_ROOT,
        relative_path=DOCUMENT_NAME,
        document_id="rdr11-synthetic-policy",
        media_type="text/plain; charset=utf-8",
        usage_basis=CorpusUsageBasis.SYNTHETIC,
        rights_reference="project-authored-rdr11-fixture",
        privacy_class=CorpusPrivacyClass.PUBLIC,
        redistribution_allowed=True,
    )


def _span(
    descriptor: CorpusDocumentDescriptor,
    text: str,
    fragment: str,
) -> SourceSpan:
    start = text.index(fragment)
    return SourceSpan.from_text(
        document_id=descriptor.document_id,
        raw_text=text,
        start_offset=start,
        end_offset=start + len(fragment),
        source_revision=descriptor.source_revision,
    )


def _label_sets():
    descriptor = _descriptor()
    text = (FIXTURE_ROOT / DOCUMENT_NAME).read_text(encoding="utf-8")
    first_sentence = "Policy Alpha applies to all standard requests."
    second_without_lead = (
        "it does not apply to emergency requests unless manual approval is recorded."
    )
    second_full = (
        "However, it does not apply to emergency requests unless manual approval is recorded."
    )
    trigger = "unless"
    approval = "manual approval"

    claim_common = HumanClaimLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=ClaimModality.WORLD_FACT,
        source_spans=(_span(descriptor, text, first_sentence),),
    )
    claim_a = HumanClaimLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=ClaimModality.WORLD_FACT,
        source_spans=(_span(descriptor, text, second_without_lead),),
        qualifier_codes=("manual-approval",),
    )
    claim_b = HumanClaimLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=ClaimModality.WORLD_FACT,
        source_spans=(_span(descriptor, text, second_full),),
        qualifier_codes=("manual-approval",),
    )
    exception = HumanExceptionLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        category=ExceptionCategory.CONDITION,
        trigger_span=_span(descriptor, text, trigger),
        statement_span=_span(descriptor, text, second_full),
        target_claim_label_ids=(claim_common.label_id,),
    )
    relation_a = HumanRelationLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        relation_kind=RelationKind.LIMITS,
        source_claim_label_id=claim_a.label_id,
        target_claim_label_id=claim_common.label_id,
        evidence_spans=(_span(descriptor, text, second_without_lead),),
    )
    relation_b = HumanRelationLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        relation_kind=RelationKind.LIMITS,
        source_claim_label_id=claim_b.label_id,
        target_claim_label_id=claim_common.label_id,
        evidence_spans=(_span(descriptor, text, second_full),),
    )
    qualifier_a = HumanQualifierLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        qualifier_kind=QualifierKind.APPROVAL,
        target_claim_label_id=claim_a.label_id,
        source_span=_span(descriptor, text, approval),
    )
    qualifier_b = HumanQualifierLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        qualifier_kind=QualifierKind.APPROVAL,
        target_claim_label_id=claim_b.label_id,
        source_span=_span(descriptor, text, approval),
    )

    set_a = HumanLabelSet(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        annotator_id="annotator-a",
        guideline_version="reader-label-guidelines-v1",
        label_version="rdr11-labels-v1",
        role=LabelSetRole.ANNOTATOR,
        claims=tuple(sorted((claim_common, claim_a), key=lambda item: item.label_id)),
        exceptions=(exception,),
        relations=(relation_a,),
        qualifiers=(qualifier_a,),
    )
    set_b = HumanLabelSet(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        annotator_id="annotator-b",
        guideline_version="reader-label-guidelines-v1",
        label_version="rdr11-labels-v1",
        role=LabelSetRole.ANNOTATOR,
        claims=tuple(sorted((claim_common, claim_b), key=lambda item: item.label_id)),
        exceptions=(exception,),
        relations=(relation_b,),
        qualifiers=(qualifier_b,),
    )
    final_set = HumanLabelSet(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        annotator_id="adjudicator-c",
        guideline_version="reader-label-guidelines-v1",
        label_version="rdr11-labels-v1",
        role=LabelSetRole.ADJUDICATED,
        claims=tuple(sorted((claim_common, claim_b), key=lambda item: item.label_id)),
        exceptions=(exception,),
        relations=(relation_b,),
        qualifiers=(qualifier_b,),
    )
    resolutions = tuple(
        sorted(
            (
                AdjudicationResolution(
                    kind=HumanLabelKind.CLAIM,
                    candidate_label_ids=tuple(
                        sorted((claim_a.label_id, claim_b.label_id))
                    ),
                    resolved_label_ids=(claim_b.label_id,),
                    resolution_code="prefer-complete-discourse-span",
                    rationale_code="include-leading-contrast-marker",
                ),
                AdjudicationResolution(
                    kind=HumanLabelKind.RELATION,
                    candidate_label_ids=tuple(
                        sorted((relation_a.label_id, relation_b.label_id))
                    ),
                    resolved_label_ids=(relation_b.label_id,),
                    resolution_code="rebase-to-adjudicated-claim",
                    rationale_code="endpoint-must-reference-final-claim",
                ),
                AdjudicationResolution(
                    kind=HumanLabelKind.QUALIFIER,
                    candidate_label_ids=tuple(
                        sorted((qualifier_a.label_id, qualifier_b.label_id))
                    ),
                    resolved_label_ids=(qualifier_b.label_id,),
                    resolution_code="rebase-to-adjudicated-claim",
                    rationale_code="target-must-reference-final-claim",
                ),
            ),
            key=lambda item: item.resolution_id,
        )
    )
    return descriptor, set_a, set_b, final_set, resolutions


def _adjudication() -> HumanLabelAdjudication:
    _, set_a, set_b, final_set, resolutions = _label_sets()
    sources = tuple(sorted((set_a, set_b), key=lambda item: item.label_set_id))
    return HumanLabelAdjudication(
        source_label_sets=sources,
        adjudicator_id="adjudicator-c",
        adjudicated_label_set=final_set,
        resolutions=resolutions,
    )


def test_package_and_label_spans_are_content_verified() -> None:
    descriptor, set_a, set_b, final_set, _ = _label_sets()
    package = CorpusPackageManifest(
        corpus_name="rdr11-human-fixture",
        corpus_version="1.0.0",
        documents=(descriptor,),
        tags=("policy", "reader-core"),
    )

    package_receipt = package.verify(FIXTURE_ROOT)
    receipts = (
        set_a.verify_spans(root=FIXTURE_ROOT, descriptor=descriptor),
        set_b.verify_spans(root=FIXTURE_ROOT, descriptor=descriptor),
        final_set.verify_spans(root=FIXTURE_ROOT, descriptor=descriptor),
    )

    assert package_receipt.package_id == package.package_id
    assert package_receipt.entries[0].content_sha256 == descriptor.content_sha256
    assert all(receipt.verified_span_ids for receipt in receipts)
    assert descriptor.source_revision == descriptor.content_sha256


def test_adjudication_partitions_every_disagreement_and_builds_manifest() -> None:
    descriptor, _, _, final_set, _ = _label_sets()
    adjudication = _adjudication()
    package = CorpusPackageManifest(
        corpus_name="rdr11-human-fixture",
        corpus_version="1.0.0",
        documents=(descriptor,),
        tags=("policy", "reader-core"),
    )

    manifest = HumanLabelEvaluationManifestBuilder().build(
        package,
        (adjudication,),
    )
    case = manifest.cases[0]

    assert adjudication.adjudicated_label_set == final_set
    assert len(adjudication.resolutions) == 3
    assert case.corpus_kind is EvaluationCorpusKind.HUMAN_LABELLED
    assert case.expected_claim_count == 2
    assert case.expected_source_span_count == 2
    assert case.expected_exception_count == 1
    assert case.expected_relation_count == 1
    assert case.expected_contradiction_count == 0
    assert case.expected_qualifier_count == 1
    assert "human-adjudicated" in case.tags


def test_unresolved_disagreement_is_rejected_fail_closed() -> None:
    _, set_a, set_b, final_set, resolutions = _label_sets()
    sources = tuple(sorted((set_a, set_b), key=lambda item: item.label_set_id))

    with pytest.raises(ReaderCorpusError, match="every disputed label"):
        HumanLabelAdjudication(
            source_label_sets=sources,
            adjudicator_id="adjudicator-c",
            adjudicated_label_set=final_set,
            resolutions=resolutions[:-1],
        )


def test_adjudicator_must_be_independent() -> None:
    _, set_a, set_b, final_set, resolutions = _label_sets()
    forged_final = replace(
        final_set,
        label_set_id="",
        annotator_id="annotator-a",
    )
    sources = tuple(sorted((set_a, set_b), key=lambda item: item.label_set_id))

    with pytest.raises(ReaderCorpusError, match="independent"):
        HumanLabelAdjudication(
            source_label_sets=sources,
            adjudicator_id="annotator-a",
            adjudicated_label_set=forged_final,
            resolutions=resolutions,
        )


def test_path_traversal_and_private_redistribution_are_rejected() -> None:
    descriptor = _descriptor()
    with pytest.raises(ReaderCorpusError, match="unsafe"):
        CorpusDocumentDescriptor.from_file(
            root=FIXTURE_ROOT,
            relative_path="../outside.txt",
            document_id="unsafe",
            media_type="text/plain",
            usage_basis=CorpusUsageBasis.SYNTHETIC,
            rights_reference="fixture",
            privacy_class=CorpusPrivacyClass.PUBLIC,
            redistribution_allowed=True,
        )
    with pytest.raises(ReaderCorpusError, match="private"):
        replace(
            descriptor,
            descriptor_id="",
            usage_basis=CorpusUsageBasis.AUTHORIZED_PRIVATE,
            redistribution_allowed=True,
        )


def test_stale_span_hash_is_rejected_during_file_verification() -> None:
    descriptor, set_a, _, _, _ = _label_sets()
    original = set_a.claims[0]
    stale_span = SourceSpan(
        span_id="stale-span",
        document_id=descriptor.document_id,
        start_offset=original.source_spans[0].start_offset,
        end_offset=original.source_spans[0].end_offset,
        content_hash="0" * 64,
        source_revision=descriptor.source_revision,
    )
    stale_claim = HumanClaimLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=original.modality,
        source_spans=(stale_span,),
    )
    stale_set = HumanLabelSet(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        annotator_id="annotator-stale",
        guideline_version="reader-label-guidelines-v1",
        label_version="rdr11-labels-v1",
        role=LabelSetRole.ANNOTATOR,
        claims=(stale_claim,),
    )

    with pytest.raises(ReaderCorpusError, match="failed content verification"):
        stale_set.verify_spans(root=FIXTURE_ROOT, descriptor=descriptor)


def test_labels_and_receipts_do_not_embed_raw_document_text() -> None:
    descriptor, set_a, _, _, _ = _label_sets()
    raw_text = (FIXTURE_ROOT / DOCUMENT_NAME).read_text(encoding="utf-8")
    payload = repr(
        (
            descriptor.identity_payload(),
            set_a.identity_payload(),
            _adjudication().identity_payload(),
        )
    )

    assert raw_text not in payload
    assert "Policy Alpha applies" not in payload
    assert "manual approval is recorded" not in payload
