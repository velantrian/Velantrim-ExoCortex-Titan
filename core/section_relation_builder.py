"""Deterministic builder for PR-RDR-06 cross-section relation sets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.reader_core_contracts import RelationKind, stable_reader_core_id
from core.section_card import SectionCard
from core.section_relations import (
    ClaimEndpoint,
    CrossSectionRelationCandidate,
    CrossSectionRelationSet,
    SECTION_RELATION_SCHEMA_VERSION,
    SectionRelationError,
    relation_pair_key,
)


@dataclass(frozen=True, slots=True)
class RelationProposal:
    """Explicit detector output; still only a non-authoritative proposal."""

    kind: RelationKind
    source_claim_id: str
    target_claim_id: str
    reason_code: str


class DeterministicSectionRelationBuilder:
    """Build a canonical relation projection from explicit evaluated pairs."""

    detector_id = "deterministic-explicit-relation-builder"
    detector_version = "1.0.0"

    def build(
        self,
        cards: Iterable[SectionCard],
        *,
        evaluated_pairs: Iterable[tuple[str, str]],
        proposals: Iterable[RelationProposal] = (),
    ) -> CrossSectionRelationSet:
        card_tuple = tuple(cards)
        if not card_tuple:
            raise SectionRelationError("cards must not be empty")
        first = card_tuple[0]
        endpoints: dict[str, ClaimEndpoint] = {}
        for card in card_tuple:
            if (
                card.document_id != first.document_id
                or card.source_revision != first.source_revision
                or card.structure_map_id != first.structure_map_id
                or card.plan_id != first.plan_id
            ):
                raise SectionRelationError("all cards must share one reading identity")
            for card_claim in card.claims:
                endpoint = ClaimEndpoint.from_card_claim(card, card_claim)
                if endpoint.claim_id in endpoints:
                    raise SectionRelationError("claim IDs must be unique across cards")
                endpoints[endpoint.claim_id] = endpoint

        known_claim_ids = tuple(sorted(endpoints))
        pair_keys: list[str] = []
        evaluated_set: set[tuple[str, str]] = set()
        for source_id, target_id in evaluated_pairs:
            if source_id not in endpoints or target_id not in endpoints:
                raise SectionRelationError("evaluated pair must reference known claims")
            pair = (source_id, target_id)
            if pair in evaluated_set:
                raise SectionRelationError("evaluated pairs must be unique")
            evaluated_set.add(pair)
            pair_keys.append(relation_pair_key(source_id, target_id))
        evaluated_pair_keys = tuple(sorted(pair_keys))

        candidates: list[CrossSectionRelationCandidate] = []
        seen_keys: set[tuple[str, str, str]] = set()
        for proposal in proposals:
            if not isinstance(proposal, RelationProposal):
                raise SectionRelationError("proposals require RelationProposal values")
            pair = (proposal.source_claim_id, proposal.target_claim_id)
            if pair not in evaluated_set:
                raise SectionRelationError("proposal pair must be explicitly evaluated")
            source = endpoints[proposal.source_claim_id]
            target = endpoints[proposal.target_claim_id]
            candidate = CrossSectionRelationCandidate.create(
                detector_id=self.detector_id,
                detector_version=self.detector_version,
                kind=proposal.kind,
                source=source,
                target=target,
                reason_code=proposal.reason_code,
                evidence_spans=(*source.source_spans, *target.source_spans),
            )
            if candidate.canonical_key in seen_keys:
                raise SectionRelationError("duplicate directed relation proposal")
            seen_keys.add(candidate.canonical_key)
            candidates.append(candidate)
        candidate_tuple = tuple(sorted(candidates, key=lambda item: item.canonical_key))

        relation_set_id = stable_reader_core_id(
            "cross-section-relation-set",
            {
                "schema_version": SECTION_RELATION_SCHEMA_VERSION,
                "document_id": first.document_id,
                "source_revision": first.source_revision,
                "structure_map_id": first.structure_map_id,
                "plan_id": first.plan_id,
                "known_claim_ids": list(known_claim_ids),
                "evaluated_pair_keys": list(evaluated_pair_keys),
                "relation_ids": [item.relation_id for item in candidate_tuple],
            },
        )
        return CrossSectionRelationSet(
            relation_set_id=relation_set_id,
            schema_version=SECTION_RELATION_SCHEMA_VERSION,
            document_id=first.document_id,
            source_revision=first.source_revision,
            structure_map_id=first.structure_map_id,
            plan_id=first.plan_id,
            known_claim_ids=known_claim_ids,
            evaluated_pair_keys=evaluated_pair_keys,
            candidates=candidate_tuple,
        )


__all__ = ["DeterministicSectionRelationBuilder", "RelationProposal"]
