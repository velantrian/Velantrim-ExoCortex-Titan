from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import unicodedata

from core.continuity.contracts import ActorKind, OriginType


@dataclass(frozen=True, slots=True)
class Wave2Turn:
    turn_ref: str
    sequence: int
    actor_kind: ActorKind
    origin_type: OriginType
    semantic_modality: str
    raw_text: str
    span_text: str
    lineage_ref: str | None = None
    constraint_scope: str | None = None
    model_backend: str | None = None

    @property
    def normalized_text(self) -> str:
        return unicodedata.normalize("NFC", self.raw_text)

    @property
    def normalized_span(self) -> str:
        return unicodedata.normalize("NFC", self.span_text)

    @property
    def span_offsets(self) -> tuple[int, int]:
        start = self.normalized_text.index(self.normalized_span)
        return start, start + len(self.normalized_span)

    @property
    def source_digest(self) -> str:
        return sha256(self.normalized_text.encode("utf-8")).hexdigest()

    @property
    def span_digest(self) -> str:
        start, end = self.span_offsets
        return sha256(self.normalized_text[start:end].encode("utf-8")).hexdigest()


RB04 = (
    Wave2Turn(
        turn_ref="t1",
        sequence=1,
        actor_kind=ActorKind.HUMAN,
        origin_type=OriginType.USER_STATED,
        semantic_modality="DIRECTIVE",
        raw_text="Do not publish until I explicitly approve it.",
        span_text="Do not publish until I explicitly approve it.",
        constraint_scope="until I explicitly approve it",
    ),
    Wave2Turn(
        turn_ref="t2",
        sequence=2,
        actor_kind=ActorKind.TITAN_COMPONENT,
        origin_type=OriginType.MODEL_INFERRED,
        semantic_modality="PROPOSAL",
        raw_text="Let's publish it now.",
        span_text="Let's publish it now.",
    ),
)

RB09 = (
    Wave2Turn(
        turn_ref="t1",
        sequence=1,
        actor_kind=ActorKind.EXTERNAL_AGENT,
        origin_type=OriginType.EXTERNAL_STATED,
        semantic_modality="PROPOSAL",
        raw_text="Model A proposes X.",
        span_text="Model A proposes X.",
        lineage_ref="lineage-a",
    ),
    Wave2Turn(
        turn_ref="t2",
        sequence=2,
        actor_kind=ActorKind.EXTERNAL_AGENT,
        origin_type=OriginType.EXTERNAL_STATED,
        semantic_modality="PROPOSAL",
        raw_text="Model B repeats X after reading Model A.",
        span_text="Model B repeats X after reading Model A.",
        lineage_ref="lineage-a",
    ),
    Wave2Turn(
        turn_ref="t3",
        sequence=3,
        actor_kind=ActorKind.EXTERNAL_AGENT,
        origin_type=OriginType.EXTERNAL_STATED,
        semantic_modality="PROPOSAL",
        raw_text="Model C agrees after reading both earlier outputs.",
        span_text="Model C agrees after reading both earlier outputs.",
        lineage_ref="lineage-a",
    ),
)

RB12 = (
    Wave2Turn(
        turn_ref="t1",
        sequence=1,
        actor_kind=ActorKind.SYSTEM,
        origin_type=OriginType.SYSTEM_OBSERVED,
        semantic_modality="ASSERTION",
        raw_text="Frozen context: Y corrects X; publishing remains forbidden until approval.",
        span_text="Y corrects X; publishing remains forbidden until approval",
        model_backend="provider-a",
    ),
    Wave2Turn(
        turn_ref="t2",
        sequence=2,
        actor_kind=ActorKind.SYSTEM,
        origin_type=OriginType.SYSTEM_OBSERVED,
        semantic_modality="ASSERTION",
        raw_text="Frozen context: Y corrects X; publishing remains forbidden until approval.",
        span_text="Y corrects X; publishing remains forbidden until approval",
        model_backend="provider-b",
    ),
)


def test_rb04_constraint_application_fixture_keeps_retention_separate_from_enforcement() -> None:
    directive, proposal = RB04
    assert directive.semantic_modality == "DIRECTIVE"
    assert directive.constraint_scope == "until I explicitly approve it"
    assert proposal.semantic_modality == "PROPOSAL"
    assert proposal.origin_type is OriginType.MODEL_INFERRED
    # Fixture expectation only: later planning evaluation must detect this conflict.
    # This test does not claim or create an action gate.
    assert directive.constraint_scope in directive.raw_text


def test_rb09_multi_model_echo_shares_lineage_and_is_not_three_independent_sources() -> None:
    assert len(RB09) == 3
    assert {turn.lineage_ref for turn in RB09} == {"lineage-a"}
    assert all(turn.actor_kind is ActorKind.EXTERNAL_AGENT for turn in RB09)
    assert all(turn.origin_type is OriginType.EXTERNAL_STATED for turn in RB09)
    assert len({turn.turn_ref for turn in RB09}) == 3
    # Distinct actors/turns do not imply independent evidence when lineage is shared.
    assert len({turn.lineage_ref for turn in RB09}) == 1


def test_rb12_model_replacement_uses_identical_source_semantics_across_backends() -> None:
    left, right = RB12
    assert left.model_backend != right.model_backend
    assert left.normalized_text == right.normalized_text
    assert left.normalized_span == right.normalized_span
    assert left.semantic_modality == right.semantic_modality == "ASSERTION"
    assert left.source_digest == right.source_digest
    assert left.span_digest == right.span_digest
    # Backend identity is experimental condition metadata, not semantic authority.


def test_wave2_source_spans_are_self_validating() -> None:
    for turn in (*RB04, *RB09, *RB12):
        start, end = turn.span_offsets
        assert 0 <= start < end <= len(turn.normalized_text)
        assert turn.normalized_text[start:end] == turn.normalized_span
        assert len(turn.source_digest) == 64
        assert len(turn.span_digest) == 64


def test_wave2_preserves_orthogonal_axes() -> None:
    for turn in (*RB04, *RB09, *RB12):
        assert isinstance(turn.actor_kind, ActorKind)
        assert isinstance(turn.origin_type, OriginType)
        assert turn.semantic_modality in {"ASSERTION", "DIRECTIVE", "PROPOSAL"}
        assert not turn.semantic_modality.startswith(("MODEL_", "SYSTEM_", "EXTERNAL_", "USER_"))


def test_wave2_does_not_claim_runtime_authority() -> None:
    prohibited_claims = {
        "CANON_WRITE",
        "TRUTH_AUTHORITY",
        "ACTION_AUTHORITY",
        "RUNTIME_ENABLED",
        "PRODUCTION_AUTHORIZED",
    }
    fixture_vocabulary = {
        turn.semantic_modality
        for turn in (*RB04, *RB09, *RB12)
    }
    assert fixture_vocabulary.isdisjoint(prohibited_claims)
