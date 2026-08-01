from dataclasses import replace
from pathlib import Path

import pytest

from core.critical_exceptions import ExceptionCategory
from core.knowledge_capsule import ClaimModality, SourceSpan
from core.reader_benchmark_scoring import (
    DeterministicReaderGoldScorer,
    ReaderClaimPrediction,
    ReaderDocumentPrediction,
    ReaderExceptionPrediction,
    ReaderExecutionMeasurement,
    ReaderQualifierPrediction,
    ReaderRelationPrediction,
    ReaderScoringError,
    ReaderSynthesisPrediction,
)
from core.reader_core_contracts import RelationKind
from core.reader_corpus_adjudication import (
    CorpusDocumentDescriptor,
    CorpusPrivacyClass,
    CorpusUsageBasis,
    HumanClaimLabel,
    HumanExceptionLabel,
    HumanLabelSet,
    HumanQualifierLabel,
    HumanRelationLabel,
    LabelSetRole,
    QualifierKind,
)


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


def _gold_and_prediction():
    descriptor = _descriptor()
    text = (FIXTURE_ROOT / DOCUMENT_NAME).read_text(encoding="utf-8")
    first_text = "Policy Alpha applies to all standard requests."
    second_text = (
        "However, it does not apply to emergency requests unless manual approval is recorded."
    )
    trigger_text = "unless"
    approval_text = "manual approval"

    first_span = _span(descriptor, text, first_text)
    second_span = _span(descriptor, text, second_text)
    trigger_span = _span(descriptor, text, trigger_text)
    approval_span = _span(descriptor, text, approval_text)

    gold_first = HumanClaimLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=ClaimModality.WORLD_FACT,
        source_spans=(first_span,),
    )
    gold_second = HumanClaimLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=ClaimModality.WORLD_FACT,
        source_spans=(second_span,),
    )
    gold_exception = HumanExceptionLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        category=ExceptionCategory.CONDITION,
        trigger_span=trigger_span,
        statement_span=second_span,
        target_claim_label_ids=(gold_first.label_id,),
    )
    gold_relation = HumanRelationLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        relation_kind=RelationKind.LIMITS,
        source_claim_label_id=gold_second.label_id,
        target_claim_label_id=gold_first.label_id,
        evidence_spans=(second_span,),
    )
    gold_qualifier = HumanQualifierLabel.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        qualifier_kind=QualifierKind.APPROVAL,
        target_claim_label_id=gold_second.label_id,
        source_span=approval_span,
    )
    gold = HumanLabelSet(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        annotator_id="adjudicator-c",
        guideline_version="reader-label-guidelines-v1",
        label_version="rdr12-gold-v1",
        role=LabelSetRole.ADJUDICATED,
        claims=tuple(
            sorted((gold_first, gold_second), key=lambda item: item.label_id)
        ),
        exceptions=(gold_exception,),
        relations=(gold_relation,),
        qualifiers=(gold_qualifier,),
    )

    predicted_first = ReaderClaimPrediction.create(
        source_claim_id="predicted-claim-a",
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=ClaimModality.WORLD_FACT,
        source_spans=(first_span,),
    )
    predicted_second = ReaderClaimPrediction.create(
        source_claim_id="predicted-claim-b",
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=ClaimModality.WORLD_FACT,
        source_spans=(second_span,),
    )
    predicted_exception = ReaderExceptionPrediction.create(
        source_candidate_id="exception-candidate-a",
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        category=ExceptionCategory.CONDITION.value,
        trigger_span=trigger_span,
        statement_span=second_span,
        target_source_claim_ids=(predicted_first.source_claim_id,),
    )
    predicted_relation = ReaderRelationPrediction.create(
        source_relation_id="relation-candidate-a",
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        kind=RelationKind.LIMITS,
        source_claim_id=predicted_second.source_claim_id,
        target_claim_id=predicted_first.source_claim_id,
        evidence_spans=(second_span,),
    )
    predicted_qualifier = ReaderQualifierPrediction.create(
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        kind=QualifierKind.APPROVAL,
        target_claim_id=predicted_second.source_claim_id,
        source_span=approval_span,
    )
    synthesis = ReaderSynthesisPrediction(
        synthesis_claim_id="synthesis-claim-a",
        supporting_source_claim_ids=tuple(
            sorted(
                (
                    predicted_first.source_claim_id,
                    predicted_second.source_claim_id,
                )
            )
        ),
    )
    prediction = ReaderDocumentPrediction(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        claims=tuple(
            sorted(
                (predicted_first, predicted_second),
                key=lambda item: item.prediction_id,
            )
        ),
        exceptions=(predicted_exception,),
        relations=(predicted_relation,),
        qualifiers=(predicted_qualifier,),
        synthesis_claims=(synthesis,),
        artifact_ids=("artifact-a", "artifact-b"),
    )
    return descriptor, gold, prediction


def _measurement() -> ReaderExecutionMeasurement:
    return ReaderExecutionMeasurement(
        section_latencies_ms=(18, 22),
        session_wall_time_ms=80,
        model_tokens=420,
        projection_bytes=3072,
        rebuild_time_ms=18,
        query_path_latency_delta_ms=0,
        resume_reused_units=2,
        resume_eligible_units=2,
    )


def test_exact_source_linked_prediction_scores_all_gold_labels() -> None:
    _, gold, prediction = _gold_and_prediction()
    observation = DeterministicReaderGoldScorer().score(
        gold=gold,
        first=prediction,
        replay=prediction,
        measurement=_measurement(),
    )

    assert observation.predicted_claim_count == 2
    assert observation.matched_claim_count == 2
    assert observation.predicted_source_span_count == 2
    assert observation.correct_source_span_count == 2
    assert observation.predicted_exception_count == 1
    assert observation.matched_exception_count == 1
    assert observation.predicted_relation_count == 1
    assert observation.matched_relation_count == 1
    assert observation.false_relation_count == 0
    assert observation.connected_qualifier_count == 1
    assert observation.orphan_source_claim_count == 0
    assert observation.unsupported_synthesis_claim_count == 0
    assert observation.first_artifact_ids == observation.second_artifact_ids
    assert "scoring_policy:exact-source-linked-v1" in observation.warnings


def test_exact_matching_is_one_to_one_and_does_not_overcount_duplicates() -> None:
    descriptor, gold, prediction = _gold_and_prediction()
    duplicate = ReaderClaimPrediction.create(
        source_claim_id="predicted-claim-duplicate",
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=prediction.claims[0].modality,
        source_spans=prediction.claims[0].source_spans,
    )
    claims = tuple(
        sorted((*prediction.claims, duplicate), key=lambda item: item.prediction_id)
    )
    synthesis = ReaderSynthesisPrediction(
        synthesis_claim_id="synthesis-with-duplicate",
        supporting_source_claim_ids=tuple(
            sorted(item.source_claim_id for item in claims)
        ),
    )
    expanded = ReaderDocumentPrediction(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        claims=claims,
        synthesis_claims=(synthesis,),
        artifact_ids=("artifact-expanded",),
    )

    observation = DeterministicReaderGoldScorer().score(
        gold=gold,
        first=expanded,
        replay=expanded,
        measurement=_measurement(),
    )

    assert observation.predicted_claim_count == 3
    assert observation.matched_claim_count == 2
    assert observation.correct_source_span_count == 2


def test_wrong_relation_kind_is_counted_as_false_relation() -> None:
    descriptor, gold, prediction = _gold_and_prediction()
    original = prediction.relations[0]
    wrong = ReaderRelationPrediction.create(
        source_relation_id="relation-candidate-wrong",
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        kind=RelationKind.SUPPORTS,
        source_claim_id=original.source_claim_id,
        target_claim_id=original.target_claim_id,
        evidence_spans=original.evidence_spans,
    )
    changed = ReaderDocumentPrediction(
        document_descriptor_id=prediction.document_descriptor_id,
        document_id=prediction.document_id,
        source_revision=prediction.source_revision,
        claims=prediction.claims,
        exceptions=prediction.exceptions,
        relations=(wrong,),
        qualifiers=prediction.qualifiers,
        synthesis_claims=prediction.synthesis_claims,
        artifact_ids=("artifact-wrong-relation",),
    )

    observation = DeterministicReaderGoldScorer().score(
        gold=gold,
        first=changed,
        replay=changed,
        measurement=_measurement(),
    )

    assert observation.predicted_relation_count == 1
    assert observation.matched_relation_count == 0
    assert observation.false_relation_count == 1


def test_replay_change_is_visible_in_observation_artifact_sequences() -> None:
    _, gold, prediction = _gold_and_prediction()
    replay = replace(
        prediction,
        prediction_id="",
        artifact_ids=("artifact-a", "artifact-c"),
    )

    observation = DeterministicReaderGoldScorer().score(
        gold=gold,
        first=prediction,
        replay=replay,
        measurement=_measurement(),
    )

    assert observation.first_artifact_ids != observation.second_artifact_ids


def test_synthesis_without_matched_gold_support_is_explicitly_unsupported() -> None:
    descriptor, gold, prediction = _gold_and_prediction()
    unmatched_span = _span(
        descriptor,
        (FIXTURE_ROOT / DOCUMENT_NAME).read_text(encoding="utf-8"),
        "Version 2 supersedes Version 1.",
    )
    unmatched = ReaderClaimPrediction.create(
        source_claim_id="predicted-unmatched-claim",
        document_id=descriptor.document_id,
        source_revision=descriptor.source_revision,
        modality=ClaimModality.HYPOTHESIS,
        source_spans=(unmatched_span,),
    )
    changed = ReaderDocumentPrediction(
        document_descriptor_id=prediction.document_descriptor_id,
        document_id=prediction.document_id,
        source_revision=prediction.source_revision,
        claims=tuple(
            sorted((*prediction.claims, unmatched), key=lambda item: item.prediction_id)
        ),
        synthesis_claims=(
            ReaderSynthesisPrediction(
                synthesis_claim_id="unsupported-synthesis",
                supporting_source_claim_ids=(unmatched.source_claim_id,),
            ),
        ),
        artifact_ids=("artifact-unsupported",),
    )

    observation = DeterministicReaderGoldScorer().score(
        gold=gold,
        first=changed,
        replay=changed,
        measurement=_measurement(),
    )

    assert observation.synthesis_claim_count == 1
    assert observation.unsupported_synthesis_claim_count == 1
    assert observation.orphan_source_claim_count == 2


def test_stale_revision_and_non_adjudicated_gold_fail_closed() -> None:
    _, gold, prediction = _gold_and_prediction()
    stale = replace(
        prediction,
        prediction_id="",
        source_revision="0" * 64,
    )
    with pytest.raises(ReaderScoringError, match="source_revision"):
        DeterministicReaderGoldScorer().score(
            gold=gold,
            first=stale,
            replay=stale,
            measurement=_measurement(),
        )

    annotator_gold = replace(
        gold,
        label_set_id="",
        role=LabelSetRole.ANNOTATOR,
        annotator_id="annotator-not-gold",
    )
    with pytest.raises(ReaderScoringError, match="adjudicated"):
        DeterministicReaderGoldScorer().score(
            gold=annotator_gold,
            first=prediction,
            replay=prediction,
            measurement=_measurement(),
        )


def test_prediction_ids_are_self_verifying() -> None:
    _, _, prediction = _gold_and_prediction()
    with pytest.raises(ReaderScoringError, match="prediction_id"):
        replace(
            prediction.claims[0],
            prediction_id="forged",
        )
    with pytest.raises(ReaderScoringError, match="prediction_id"):
        replace(
            prediction,
            warnings=("forged",),
        )
