"""Typed bridge from CSL continuity projections into the existing Synaptic Gate.

The adapter is deliberately policy-neutral.  It validates every semantic
``ContinuityContextItem`` against its immutable ``ConversationEpisode`` source,
projects the item as an exact-source ``KnowledgeCapsule``, and combines it with
caller-supplied Gate attributes.  It does not compute salience, decide privacy,
run ``WorkingMemoryGate``, build the final ``ContextPack``, write Canon, or alter
the answer path.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Iterable

from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.working_memory_gate import WorkingMemoryCandidate

from .context_pack import (
    ContinuityContextItem,
    ContinuityContextPack,
    ContinuityItemKind,
)
from .conversation_bridge import ConversationEpisode

ADAPTER_ID = "continuity-working-memory-adapter"
ADAPTER_VERSION = "continuity-working-memory-adapter.v1"


class ContinuityWorkingMemoryAdapterError(ValueError):
    """Raised when a continuity pack cannot be adapted without ambiguity."""


class ContinuityAdapterOmissionReason(str, Enum):
    """Stable reasons why an item is not converted into semantic content."""

    UNRESOLVED_REFERENCE_NOT_SEMANTIC_CONTENT = (
        "unresolved_reference_not_semantic_content"
    )


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContinuityWorkingMemoryAdapterError(
            f"{name} must be a non-empty string"
        )
    return value


def _score(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContinuityWorkingMemoryAdapterError(
            f"{name} must be a finite number in [0, 1]"
        )
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ContinuityWorkingMemoryAdapterError(
            f"{name} must be a finite number in [0, 1]"
        )
    return result


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ContinuityWorkingMemoryAdapterError(f"{name} must be a bool")
    return value


@dataclass(frozen=True, slots=True)
class ContinuityItemGatePolicy:
    """Explicit upstream policy facts for one semantic continuity item."""

    item_id: str
    attention_score: float
    recall_allowed: bool
    eligible: bool
    restricted: bool
    erased: bool
    protected: bool
    conflict: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "item_id", _text(self.item_id, "item_id"))
        object.__setattr__(
            self,
            "attention_score",
            _score(self.attention_score, "attention_score"),
        )
        for field_name in (
            "recall_allowed",
            "eligible",
            "restricted",
            "erased",
            "protected",
            "conflict",
        ):
            object.__setattr__(
                self,
                field_name,
                _strict_bool(getattr(self, field_name), field_name),
            )


@dataclass(frozen=True, slots=True)
class ContinuityCandidateBinding:
    """Trace one continuity item to its exact-source Synaptic capsule."""

    item_id: str
    capsule_id: str
    source_episode_id: str
    source_ref: str
    virtual_document_id: str
    source_span_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "item_id",
            "capsule_id",
            "source_episode_id",
            "source_ref",
            "virtual_document_id",
            "source_span_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(getattr(self, field_name), field_name),
            )


@dataclass(frozen=True, slots=True)
class ContinuityAdapterOmission:
    """One explicit non-semantic item omitted before the Gate."""

    item_id: str
    kind: ContinuityItemKind
    source_ref: str
    reason: ContinuityAdapterOmissionReason

    def __post_init__(self) -> None:
        object.__setattr__(self, "item_id", _text(self.item_id, "item_id"))
        object.__setattr__(
            self, "source_ref", _text(self.source_ref, "source_ref")
        )
        if not isinstance(self.kind, ContinuityItemKind):
            raise ContinuityWorkingMemoryAdapterError(
                "kind must be a ContinuityItemKind"
            )
        if not isinstance(self.reason, ContinuityAdapterOmissionReason):
            raise ContinuityWorkingMemoryAdapterError(
                "reason must be a ContinuityAdapterOmissionReason"
            )


@dataclass(frozen=True, slots=True)
class ContinuityWorkingMemoryBatch:
    """Deterministic adapter output ready for the existing WorkingMemoryGate."""

    source_pack_id: str
    candidates: tuple[WorkingMemoryCandidate, ...]
    bindings: tuple[ContinuityCandidateBinding, ...]
    omissions: tuple[ContinuityAdapterOmission, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source_pack_id", _text(self.source_pack_id, "source_pack_id")
        )
        if any(
            not isinstance(candidate, WorkingMemoryCandidate)
            for candidate in self.candidates
        ):
            raise ContinuityWorkingMemoryAdapterError(
                "candidates must contain WorkingMemoryCandidate values"
            )
        if any(
            not isinstance(binding, ContinuityCandidateBinding)
            for binding in self.bindings
        ):
            raise ContinuityWorkingMemoryAdapterError(
                "bindings must contain ContinuityCandidateBinding values"
            )
        if any(
            not isinstance(omission, ContinuityAdapterOmission)
            for omission in self.omissions
        ):
            raise ContinuityWorkingMemoryAdapterError(
                "omissions must contain ContinuityAdapterOmission values"
            )

        candidates = tuple(
            sorted(
                self.candidates,
                key=lambda candidate: str(
                    candidate.metadata["continuity_item_id"]
                ),
            )
        )
        bindings = tuple(sorted(self.bindings, key=lambda item: item.item_id))
        omissions = tuple(sorted(self.omissions, key=lambda item: item.item_id))
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "bindings", bindings)
        object.__setattr__(self, "omissions", omissions)

        candidate_item_ids = tuple(
            str(candidate.metadata["continuity_item_id"])
            for candidate in candidates
        )
        binding_item_ids = tuple(binding.item_id for binding in bindings)
        if len(candidate_item_ids) != len(set(candidate_item_ids)):
            raise ContinuityWorkingMemoryAdapterError(
                "candidate continuity item ids must be unique"
            )
        if candidate_item_ids != binding_item_ids:
            raise ContinuityWorkingMemoryAdapterError(
                "every candidate must have exactly one ordered binding"
            )
        capsule_ids = tuple(
            candidate.capsule.capsule_id for candidate in candidates
        )
        if len(capsule_ids) != len(set(capsule_ids)):
            raise ContinuityWorkingMemoryAdapterError(
                "adapted capsule ids must be unique"
            )
        if set(candidate_item_ids) & {item.item_id for item in omissions}:
            raise ContinuityWorkingMemoryAdapterError(
                "an item cannot be both adapted and omitted"
            )

    @property
    def capsules(self) -> tuple[KnowledgeCapsule, ...]:
        """Return capsules in the same deterministic order as candidates."""

        return tuple(candidate.capsule for candidate in self.candidates)


_MODALITY_BY_KIND: dict[ContinuityItemKind, ClaimModality] = {
    ContinuityItemKind.PRIOR_GOAL_TEXT: ClaimModality.GOAL,
    ContinuityItemKind.PRIOR_TOPIC_TEXT: ClaimModality.INTERPRETATION,
    ContinuityItemKind.PRIOR_INSIGHT_TEXT: ClaimModality.INTERPRETATION,
    ContinuityItemKind.PRIOR_CONCLUSION_TEXT: ClaimModality.INTERPRETATION,
}


def _effective_timestamp(episode: ConversationEpisode):
    return episode.finalized_at or episode.created_at


def _verify_item_source(
    item: ContinuityContextItem,
    episode: ConversationEpisode,
) -> None:
    if item.source_episode_id != episode.episode_id:
        raise ContinuityWorkingMemoryAdapterError(
            "continuity item source_episode_id does not match episode"
        )
    if item.source_ref != episode.source_ref:
        raise ContinuityWorkingMemoryAdapterError(
            "continuity item source_ref does not match episode"
        )

    matches_source = False
    if item.kind is ContinuityItemKind.PRIOR_GOAL_TEXT:
        matches_source = item.text == episode.user_goal
    elif item.kind is ContinuityItemKind.PRIOR_TOPIC_TEXT:
        matches_source = item.text == episode.main_topic
    elif item.kind is ContinuityItemKind.PRIOR_INSIGHT_TEXT:
        matches_source = item.text in episode.key_insights
    elif item.kind is ContinuityItemKind.PRIOR_CONCLUSION_TEXT:
        matches_source = item.text == episode.conclusion

    if not matches_source:
        raise ContinuityWorkingMemoryAdapterError(
            f"item {item.item_id} is not exact content from its source episode"
        )


def _virtual_document_id(item: ContinuityContextItem) -> str:
    return f"continuity_projection:{item.source_ref}:{item.item_id}"


def _capsule_for_item(
    item: ContinuityContextItem,
    episode: ConversationEpisode,
) -> tuple[KnowledgeCapsule, SourceSpan]:
    _verify_item_source(item, episode)
    modality = _MODALITY_BY_KIND.get(item.kind)
    if modality is None:
        raise ContinuityWorkingMemoryAdapterError(
            f"item kind {item.kind.value} is not semantic Gate content"
        )

    document_id = _virtual_document_id(item)
    span = SourceSpan.from_text(
        document_id=document_id,
        raw_text=item.text,
        start_offset=0,
        end_offset=len(item.text),
        source_revision=item.item_id,
    )
    claim = CapsuleClaim.create(
        text=item.text,
        modality=modality,
        source_spans=(span,),
        extraction_confidence=1.0,
        truth_confidence=None,
        uncertainties=tuple(code.value for code in item.uncertainty_codes),
    )
    capsule = KnowledgeCapsule.create(
        source_document_id=document_id,
        essence=item.text,
        claims=(claim,),
        reader_id=ADAPTER_ID,
        reader_version=ADAPTER_VERSION,
        coverage_score=1.0,
        compression_ratio=1.0,
        created_at=_effective_timestamp(episode),
    )
    return capsule, span


class ContinuityWorkingMemoryAdapter:
    """Pure continuity-to-Synaptic adapter with no policy authority."""

    def adapt(
        self,
        pack: ContinuityContextPack,
        episodes: Iterable[ConversationEpisode],
        policies: Iterable[ContinuityItemGatePolicy],
    ) -> ContinuityWorkingMemoryBatch:
        if not isinstance(pack, ContinuityContextPack):
            raise ContinuityWorkingMemoryAdapterError(
                "pack must be a ContinuityContextPack"
            )

        episode_by_id: dict[str, ConversationEpisode] = {}
        for episode in episodes:
            if not isinstance(episode, ConversationEpisode):
                raise ContinuityWorkingMemoryAdapterError(
                    "episodes must contain ConversationEpisode values"
                )
            if episode.episode_id in episode_by_id:
                raise ContinuityWorkingMemoryAdapterError(
                    f"duplicate episode_id: {episode.episode_id}"
                )
            episode_by_id[episode.episode_id] = episode

        policy_by_item_id: dict[str, ContinuityItemGatePolicy] = {}
        for policy in policies:
            if not isinstance(policy, ContinuityItemGatePolicy):
                raise ContinuityWorkingMemoryAdapterError(
                    "policies must contain ContinuityItemGatePolicy values"
                )
            if policy.item_id in policy_by_item_id:
                raise ContinuityWorkingMemoryAdapterError(
                    f"duplicate policy item_id: {policy.item_id}"
                )
            policy_by_item_id[policy.item_id] = policy

        semantic_items = tuple(
            item
            for item in pack.items
            if item.kind is not ContinuityItemKind.UNRESOLVED_CHAT_REFERENCE
        )
        expected_policy_ids = {item.item_id for item in semantic_items}
        supplied_policy_ids = set(policy_by_item_id)
        if expected_policy_ids != supplied_policy_ids:
            missing = sorted(expected_policy_ids - supplied_policy_ids)
            unexpected = sorted(supplied_policy_ids - expected_policy_ids)
            raise ContinuityWorkingMemoryAdapterError(
                f"policy/item mismatch: missing={missing}, unexpected={unexpected}"
            )

        candidates: list[WorkingMemoryCandidate] = []
        bindings: list[ContinuityCandidateBinding] = []
        omissions: list[ContinuityAdapterOmission] = []

        for item in pack.items:
            if item.kind is ContinuityItemKind.UNRESOLVED_CHAT_REFERENCE:
                omissions.append(
                    ContinuityAdapterOmission(
                        item_id=item.item_id,
                        kind=item.kind,
                        source_ref=item.source_ref,
                        reason=(
                            ContinuityAdapterOmissionReason.
                            UNRESOLVED_REFERENCE_NOT_SEMANTIC_CONTENT
                        ),
                    )
                )
                continue

            episode = episode_by_id.get(item.source_episode_id)
            if episode is None:
                raise ContinuityWorkingMemoryAdapterError(
                    f"missing source episode: {item.source_episode_id}"
                )
            policy = policy_by_item_id[item.item_id]
            capsule, span = _capsule_for_item(item, episode)
            candidate = WorkingMemoryCandidate(
                capsule=capsule,
                attention_score=policy.attention_score,
                recall_allowed=policy.recall_allowed,
                eligible=policy.eligible,
                restricted=policy.restricted,
                erased=policy.erased,
                protected=policy.protected,
                conflict=policy.conflict,
                metadata={
                    "continuity_pack_id": pack.pack_id,
                    "continuity_item_id": item.item_id,
                    "continuity_item_kind": item.kind.value,
                    "source_episode_id": item.source_episode_id,
                    "source_ref": item.source_ref,
                    "uncertainty_codes": tuple(
                        code.value for code in item.uncertainty_codes
                    ),
                },
            )
            candidates.append(candidate)
            bindings.append(
                ContinuityCandidateBinding(
                    item_id=item.item_id,
                    capsule_id=capsule.capsule_id,
                    source_episode_id=item.source_episode_id,
                    source_ref=item.source_ref,
                    virtual_document_id=capsule.source_document_id,
                    source_span_id=span.span_id,
                )
            )

        return ContinuityWorkingMemoryBatch(
            source_pack_id=pack.pack_id,
            candidates=tuple(candidates),
            bindings=tuple(bindings),
            omissions=tuple(omissions),
        )


__all__ = [
    "ADAPTER_ID",
    "ADAPTER_VERSION",
    "ContinuityAdapterOmission",
    "ContinuityAdapterOmissionReason",
    "ContinuityCandidateBinding",
    "ContinuityItemGatePolicy",
    "ContinuityWorkingMemoryAdapter",
    "ContinuityWorkingMemoryAdapterError",
    "ContinuityWorkingMemoryBatch",
]
