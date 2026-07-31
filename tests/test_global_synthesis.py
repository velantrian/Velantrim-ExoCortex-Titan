from dataclasses import replace

import pytest

from core.critical_exceptions import (
    CriticalExceptionCandidate,
    DeterministicCriticalExceptionScanner,
)
from core.document_structure import (
    DeterministicDocumentStructureParser,
    DocumentStructureFormat,
)
from core.global_synthesis import (
    AlternativeInterpretationProposal,
    GlobalDocumentSynthesis,
    GlobalDocumentSynthesisBuilder,
    GlobalSynthesisError,
    SynthesisClaimKind,
    SynthesisClaimProposal,
    UnresolvedQuestionProposal,
)
from core.hierarchical_section_planner import (
    HierarchicalSectionPlan,
    HierarchicalSectionPlanner,
    SectionPlanningBudget,
)
from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.reader_core_contracts import (
    DocumentStructureMap,
    RelationKind,
    SessionState,
)
from core.reader_coverage import CoverageMap, CoverageMapBuilder
from core.reading_session import (
    ReadingSession,
    ReadingSessionManager,
    ReadingSessionUsage,
    SessionArtifactKind,
)
from core.section_card import SectionCard, SectionCardBuilder, SpanCoordinateSpace
from core.section_relation_builder import (
    DeterministicSectionRelationBuilder,
    RelationProposal,
)
from core.section_relations import CrossSectionRelationSet
from core.semantic_reader import RawSource, ReaderResult


class _Fixture:
    def __init__(
        self,
        *,
        source: RawSource,
        structure: DocumentStructureMap,
        plan: HierarchicalSectionPlan,
        cards: tuple[SectionCard, ...],
        exceptions: tuple[CriticalExceptionCandidate, ...],
        coverage: CoverageMap,
        relations: CrossSectionRelationSet,
        session: ReadingSession,
    ) -> None:
        self.source = source
        self.structure = structure
        self.plan = plan
        self.cards = cards
        self.exceptions = exceptions
        self.coverage = coverage
        self.relations = relations
        self.session = session

    @property
    def claim_ids(self) -> tuple[str, ...]:
        return tuple(card.claims[0].claim.claim_id for card in self.cards)


def _card_for_unit(
    source: RawSource,
    plan: HierarchicalSectionPlan,
    unit_index: int,
) -> SectionCard:
    unit = plan.units[unit_index]
    unit_text = source.text[unit.start_offset : unit.end_offset]
    claim_text = unit_text.strip()
    local_start = unit_text.index(claim_text)
    span = SourceSpan.from_text(
        document_id=unit.document_id,
        raw_text=unit_text,
        start_offset=local_start,
        end_offset=local_start + len(claim_text),
        source_revision=unit.source_revision,
    )
    claim = CapsuleClaim.create(
        text=claim_text,
        modality=ClaimModality.OBSERVATION,
        source_spans=(span,),
        extraction_confidence=1.0,
    )
    capsule = KnowledgeCapsule.create(
        source_document_id=unit.document_id,
        essence=claim_text,
        claims=(claim,),
        reader_id="synthesis-fixture-reader",
        reader_version="1",
        coverage_score=1.0,
    )
    return SectionCardBuilder().build(
        source,
        unit,
        ReaderResult.success(capsule),
        plan_id=plan.plan_id,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )


def _fixture() -> _Fixture:
    text = (
        "The system retains ordinary records by default.\n\n"
        "Unless approved, archived records are deleted.\n\n"
        "A later rule says archived records must always be retained.\n\n"
        "An appendix lists an implementation example without changing policy."
    )
    source = RawSource(
        document_id="synthesis-doc",
        text=text,
        source_revision="revision-1",
    )
    structure = DeterministicDocumentStructureParser().parse(
        source,
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )
    plan = HierarchicalSectionPlanner().plan(
        source,
        structure,
        budget=SectionPlanningBudget(
            max_unit_chars=75,
            min_unit_chars=20,
            boundary_search_chars=60,
        ),
    )
    assert len(plan.units) == 4
    cards = tuple(_card_for_unit(source, plan, index) for index in range(4))
    scans = tuple(
        DeterministicCriticalExceptionScanner().scan(source, card)
        for card in cards
    )
    exceptions = tuple(
        candidate
        for scan in scans
        for candidate in scan.candidates
    )
    assert len(exceptions) == 1
    assert exceptions[0].target_claim_refs == (
        cards[1].claims[0].claim.claim_id,
    )
    coverage = CoverageMapBuilder().build(
        source,
        structure,
        plan,
        cards=cards,
        exception_scans=scans,
    )

    claim_ids = tuple(card.claims[0].claim.claim_id for card in cards)
    relation_builder = DeterministicSectionRelationBuilder()
    relations = relation_builder.build(
        cards,
        evaluated_pairs=(
            (claim_ids[0], claim_ids[1]),
            (claim_ids[2], claim_ids[1]),
        ),
        proposals=(
            RelationProposal(
                kind=RelationKind.SUPPORTS,
                source_claim_id=claim_ids[0],
                target_claim_id=claim_ids[1],
                reason_code="default_rule_supports_scoped_rule",
            ),
            RelationProposal(
                kind=RelationKind.CONTRADICTS,
                source_claim_id=claim_ids[2],
                target_claim_id=claim_ids[1],
                reason_code="later_rule_conflicts_with_deletion_rule",
            ),
        ),
    )

    manager = ReadingSessionManager()
    session = manager.create(
        plan,
        session_key="synthesis-session-key",
        policy_snapshot_id="policy-snapshot-1",
        policy_version="policy-v1",
    )
    session = manager.claim(
        session,
        runner_id="synthesis-runner",
        expires_at_ms=100,
        now_ms=0,
    )
    lease = session.active_lease
    assert lease is not None
    session = manager.start(session, lease, now_ms=1)
    session = manager.record_cards(
        session,
        lease,
        cards,
        usage_delta=ReadingSessionUsage(
            processed_units=len(cards),
            source_chars=sum(unit.char_count for unit in plan.units),
        ),
        now_ms=2,
    )
    session = manager.attach_artifacts(
        session,
        lease,
        coverage_map_id=coverage.coverage_map_id,
        relation_set_id=relations.relation_set_id,
        now_ms=3,
    )
    session = manager.complete(session, lease, now_ms=4)
    assert session.state is SessionState.COMPLETED
    return _Fixture(
        source=source,
        structure=structure,
        plan=plan,
        cards=cards,
        exceptions=exceptions,
        coverage=coverage,
        relations=relations,
        session=session,
    )


def _proposals(
    fixture: _Fixture,
) -> tuple[
    tuple[SynthesisClaimProposal, ...],
    tuple[AlternativeInterpretationProposal, ...],
    tuple[UnresolvedQuestionProposal, ...],
]:
    claim_0, claim_1, claim_2, _ = fixture.claim_ids
    support_relation = next(
        item
        for item in fixture.relations.candidates
        if item.kind is RelationKind.SUPPORTS
    )
    contradiction = next(
        item
        for item in fixture.relations.candidates
        if item.kind is RelationKind.CONTRADICTS
    )
    exception = fixture.exceptions[0]
    claims = (
        SynthesisClaimProposal(
            proposal_key="central",
            kind=SynthesisClaimKind.CENTRAL_THEME,
            text=(
                "The document defines retention as a default rule constrained "
                "by explicit approval conditions."
            ),
            supporting_claim_ids=tuple(sorted((claim_0, claim_1))),
            exception_candidate_ids=(exception.candidate_id,),
            relation_ids=(support_relation.relation_id,),
            qualifiers=("archived records have a conditional exception",),
            inference_reason="combine_default_and_scoped_retention_rules",
        ),
        SynthesisClaimProposal(
            proposal_key="tension",
            kind=SynthesisClaimKind.CONTRADICTION,
            text=(
                "The later universal-retention rule conflicts with the earlier "
                "conditional deletion rule."
            ),
            supporting_claim_ids=(claim_2,),
            opposing_claim_ids=(claim_1,),
            relation_ids=(contradiction.relation_id,),
            inference_reason="preserve_explicit_cross_section_contradiction",
        ),
    )
    alternatives = (
        AlternativeInterpretationProposal(
            proposal_key="alternative-supersession",
            text=(
                "The later rule may supersede the earlier rule rather than "
                "coexist with it."
            ),
            supporting_synthesis_keys=("central", "tension"),
            source_claim_ids=tuple(sorted((claim_1, claim_2))),
            contrast_reason="ordering_may_indicate_supersession",
        ),
    )
    questions = (
        UnresolvedQuestionProposal(
            proposal_key="question-precedence",
            question="Which rule has precedence for archived records?",
            reason_code="contradiction_without_explicit_precedence",
            related_synthesis_keys=("tension",),
            related_source_claim_ids=tuple(sorted((claim_1, claim_2))),
            related_exception_candidate_ids=(exception.candidate_id,),
            related_relation_ids=(contradiction.relation_id,),
        ),
    )
    return claims, alternatives, questions


def _build(fixture: _Fixture) -> GlobalDocumentSynthesis:
    claims, alternatives, questions = _proposals(fixture)
    return GlobalDocumentSynthesisBuilder().build(
        fixture.session,
        fixture.coverage,
        fixture.relations,
        cards=fixture.cards,
        exception_candidates=fixture.exceptions,
        claim_proposals=claims,
        central_theme_proposal_key="central",
        alternative_proposals=alternatives,
        unresolved_question_proposals=questions,
    )


def test_builds_source_linked_navigable_global_synthesis() -> None:
    fixture = _fixture()
    synthesis = _build(fixture)

    assert synthesis.document_id == fixture.source.document_id
    assert synthesis.session_snapshot_id == fixture.session.snapshot_id
    assert len(synthesis.claims) == 2
    central = next(
        item
        for item in synthesis.claims
        if item.synthesis_claim_id == synthesis.central_theme_claim_id
    )
    assert central.kind is SynthesisClaimKind.CENTRAL_THEME
    assert central.exception_candidate_ids == (
        fixture.exceptions[0].candidate_id,
    )
    assert len(central.source_card_ids) == 2
    assert central.source_spans
    assert len(synthesis.alternative_interpretations) == 1
    assert len(synthesis.unresolved_questions) == 1
    assert synthesis.unsupported_source_claim_ids == (fixture.claim_ids[3],)
    assert "source_claims_not_represented_in_synthesis" in synthesis.warnings
    assert "alternative_interpretations_present" in synthesis.warnings
    assert "unresolved_synthesis_questions_present" in synthesis.warnings


def test_input_order_does_not_change_synthesis_identity() -> None:
    fixture = _fixture()
    claims, alternatives, questions = _proposals(fixture)
    builder = GlobalDocumentSynthesisBuilder()
    first = builder.build(
        fixture.session,
        fixture.coverage,
        fixture.relations,
        cards=fixture.cards,
        exception_candidates=fixture.exceptions,
        claim_proposals=claims,
        central_theme_proposal_key="central",
        alternative_proposals=alternatives,
        unresolved_question_proposals=questions,
    )
    second = builder.build(
        fixture.session,
        fixture.coverage,
        fixture.relations,
        cards=tuple(reversed(fixture.cards)),
        exception_candidates=tuple(reversed(fixture.exceptions)),
        claim_proposals=tuple(reversed(claims)),
        central_theme_proposal_key="central",
        alternative_proposals=tuple(reversed(alternatives)),
        unresolved_question_proposals=tuple(reversed(questions)),
    )
    assert first == second
    assert first.synthesis_id == second.synthesis_id


def test_unknown_source_claim_fails_closed() -> None:
    fixture = _fixture()
    proposal = SynthesisClaimProposal(
        proposal_key="central",
        kind=SynthesisClaimKind.CENTRAL_THEME,
        text="Unsupported claim.",
        supporting_claim_ids=("unknown-claim",),
    )
    with pytest.raises(GlobalSynthesisError, match="unknown source claim"):
        GlobalDocumentSynthesisBuilder().build(
            fixture.session,
            fixture.coverage,
            fixture.relations,
            cards=fixture.cards,
            exception_candidates=fixture.exceptions,
            claim_proposals=(proposal,),
            central_theme_proposal_key="central",
        )


def test_relation_endpoints_must_be_explicitly_represented() -> None:
    fixture = _fixture()
    claim_0, _, _, _ = fixture.claim_ids
    relation = fixture.relations.candidates[0]
    proposal = SynthesisClaimProposal(
        proposal_key="central",
        kind=SynthesisClaimKind.CENTRAL_THEME,
        text="A relation is mentioned without both endpoints.",
        supporting_claim_ids=(claim_0,),
        relation_ids=(relation.relation_id,),
    )
    with pytest.raises(GlobalSynthesisError, match="endpoints"):
        GlobalDocumentSynthesisBuilder().build(
            fixture.session,
            fixture.coverage,
            fixture.relations,
            cards=fixture.cards,
            exception_candidates=fixture.exceptions,
            claim_proposals=(proposal,),
            central_theme_proposal_key="central",
        )


def test_incomplete_session_cannot_create_global_synthesis() -> None:
    fixture = _fixture()
    incomplete = replace(
        fixture.session,
        snapshot_id="",
        state=SessionState.PAUSED,
        receipts=tuple(
            replace(
                receipt,
                receipt_id="",
                to_state=(
                    SessionState.PAUSED
                    if index == len(fixture.session.receipts) - 1
                    else receipt.to_state
                ),
            )
            for index, receipt in enumerate(fixture.session.receipts)
        ),
    )
    claims, alternatives, questions = _proposals(fixture)
    with pytest.raises(GlobalSynthesisError, match="COMPLETED"):
        GlobalDocumentSynthesisBuilder().build(
            incomplete,
            fixture.coverage,
            fixture.relations,
            cards=fixture.cards,
            exception_candidates=fixture.exceptions,
            claim_proposals=claims,
            central_theme_proposal_key="central",
            alternative_proposals=alternatives,
            unresolved_question_proposals=questions,
        )


def test_reused_card_artifacts_require_provenance_rebasing() -> None:
    fixture = _fixture()
    first = fixture.session.unit_artifacts[0]
    reused = replace(
        first,
        kind=SessionArtifactKind.REUSED_CARD,
        artifact_source_revision="revision-0",
    )
    artifacts = (reused, *fixture.session.unit_artifacts[1:])
    reused_session = replace(
        fixture.session,
        snapshot_id="",
        unit_artifacts=artifacts,
    )
    claims, _, _ = _proposals(fixture)
    with pytest.raises(GlobalSynthesisError, match="provenance rebasing"):
        GlobalDocumentSynthesisBuilder().build(
            reused_session,
            fixture.coverage,
            fixture.relations,
            cards=fixture.cards,
            exception_candidates=fixture.exceptions,
            claim_proposals=claims,
            central_theme_proposal_key="central",
        )


def test_synthesis_and_child_ids_are_self_verifying() -> None:
    synthesis = _build(_fixture())
    with pytest.raises(GlobalSynthesisError, match="synthesis_id"):
        replace(synthesis, warnings=(*synthesis.warnings, "forged"))
    with pytest.raises(GlobalSynthesisError, match="synthesis_claim_id"):
        replace(synthesis.claims[0], text="forged")
