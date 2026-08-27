from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import unicodedata

from core.continuity.contracts import ActorKind, OriginType


TICC_FIXTURE_SCHEMA_VERSION = "ticc.fixtures.v0_1"
TICC_FIXTURE_STATUS = "TEST_ONLY_SHADOW_NO_RUNTIME_AUTHORITY"

SEMANTIC_MODALITIES = {
    "ASSERTION",
    "DIRECTIVE",
    "PROPOSAL",
    "RECOMMENDATION",
    "DECISION",
    "CORRECTION",
    "RETRACTION",
    "EXAMPLE",
    "HYPOTHESIS",
    "PREDICTION",
    "SIMULATION",
    "PSEUDOCODE",
    "QUESTION",
    "UNRESOLVED",
}


@dataclass(frozen=True, slots=True)
class SourceFixtureTurn:
    turn_ref: str
    sequence: int
    actor_kind: ActorKind
    origin_type: OriginType
    semantic_modality: str
    raw_text: str
    span_text: str
    qualifier_text: str | None = None
    temporal_status: str | None = None
    declared_loss: tuple[str, ...] = ()

    @property
    def normalized_text(self) -> str:
        return unicodedata.normalize("NFC", self.raw_text)

    @property
    def normalized_span(self) -> str:
        return unicodedata.normalize("NFC", self.span_text)

    @property
    def raw_text_sha256(self) -> str:
        return sha256(self.normalized_text.encode("utf-8")).hexdigest()

    @property
    def span_offsets(self) -> tuple[int, int]:
        start = self.normalized_text.index(self.normalized_span)
        return start, start + len(self.normalized_span)

    @property
    def slice_sha256(self) -> str:
        start, end = self.span_offsets
        return sha256(self.normalized_text[start:end].encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceBoundaryFixture:
    fixture_id: str
    title: str
    turns: tuple[SourceFixtureTurn, ...]
    expected: dict[str, object]


FIXTURES = (
    SourceBoundaryFixture(
        fixture_id="RB-01",
        title="Correction precedence",
        turns=(
            SourceFixtureTurn(
                "t1",
                1,
                ActorKind.HUMAN,
                OriginType.USER_STATED,
                "ASSERTION",
                "Store summaries in the graph.",
                "Store summaries in the graph.",
            ),
            SourceFixtureTurn(
                "t2",
                2,
                ActorKind.TITAN_COMPONENT,
                OriginType.MODEL_INFERRED,
                "PROPOSAL",
                "I suggest storing summaries in the graph.",
                "I suggest storing summaries in the graph.",
            ),
            SourceFixtureTurn(
                "t3",
                3,
                ActorKind.HUMAN,
                OriginType.USER_STATED,
                "CORRECTION",
                "Replace the earlier rule: keep only original records.",
                "keep only original records",
            ),
        ),
        expected={
            "governing_modality": "CORRECTION",
            "relation": "CORRECTS",
            "target_turn_ref": "t1",
            "must_not_promote": ("PROPOSAL",),
        },
    ),
    SourceBoundaryFixture(
        fixture_id="RB-02",
        title="Recommendation is not decision",
        turns=(
            SourceFixtureTurn(
                "t1",
                1,
                ActorKind.TITAN_COMPONENT,
                OriginType.MODEL_INFERRED,
                "RECOMMENDATION",
                "I recommend implementing Task Tracker first.",
                "I recommend implementing Task Tracker first.",
            ),
            SourceFixtureTurn(
                "t2",
                2,
                ActorKind.HUMAN,
                OriginType.USER_STATED,
                "DECISION",
                "We will start with the minimal vertical slice instead.",
                "We will start with the minimal vertical slice instead.",
            ),
        ),
        expected={
            "governing_modality": "DECISION",
            "must_not_promote": ("RECOMMENDATION",),
        },
    ),
    SourceBoundaryFixture(
        fixture_id="RB-03",
        title="Conditional constraint scope",
        turns=(
            SourceFixtureTurn(
                "t1",
                1,
                ActorKind.HUMAN,
                OriginType.USER_STATED,
                "DIRECTIVE",
                "Do not publish until I explicitly approve it.",
                "Do not publish until I explicitly approve it.",
                qualifier_text="until I explicitly approve it",
            ),
            SourceFixtureTurn(
                "t2",
                2,
                ActorKind.TITAN_COMPONENT,
                OriginType.MODEL_INFERRED,
                "PROPOSAL",
                "Let's publish it now.",
                "Let's publish it now.",
            ),
        ),
        expected={
            "governing_modality": "DIRECTIVE",
            "must_preserve_qualifier": "until I explicitly approve it",
            "must_not_promote": ("PROPOSAL",),
        },
    ),
    SourceBoundaryFixture(
        fixture_id="RB-05",
        title="Illustrative metric laundering",
        turns=(
            SourceFixtureTurn(
                "t1",
                1,
                ActorKind.HUMAN,
                OriginType.USER_STATED,
                "EXAMPLE",
                "For example, assume latency is 150 ms.",
                "assume latency is 150 ms",
            ),
        ),
        expected={"must_not_become": ("MEASUREMENT", "CURRENT_STATE")},
    ),
    SourceBoundaryFixture(
        fixture_id="RB-06",
        title="Simulation is not experience",
        turns=(
            SourceFixtureTurn(
                "t1",
                1,
                ActorKind.TITAN_COMPONENT,
                OriginType.MODEL_INFERRED,
                "SIMULATION",
                "Imagine that I researched this for two hours and found 12 sources.",
                "I researched this for two hours and found 12 sources",
            ),
        ),
        expected={"must_not_become": ("EXECUTED_EXPERIENCE", "MEASURED_RESULT")},
    ),
    SourceBoundaryFixture(
        fixture_id="RB-07",
        title="Pseudocode is not implementation",
        turns=(
            SourceFixtureTurn(
                "t1",
                1,
                ActorKind.TITAN_COMPONENT,
                OriginType.MODEL_INFERRED,
                "PSEUDOCODE",
                "Pseudocode: engine.start(); monitor.run();",
                "engine.start(); monitor.run();",
            ),
        ),
        expected={"must_not_become": ("IMPLEMENTED", "WIRED", "ENABLED")},
    ),
    SourceBoundaryFixture(
        fixture_id="RB-08",
        title="Provenance and endorsement",
        turns=(
            SourceFixtureTurn(
                "t1",
                1,
                ActorKind.EXTERNAL_AGENT,
                OriginType.EXTERNAL_STATED,
                "PROPOSAL",
                "Model A proposes replacing X with Y.",
                "Model A proposes replacing X with Y.",
            ),
            SourceFixtureTurn(
                "t2",
                2,
                ActorKind.EXTERNAL_AGENT,
                OriginType.EXTERNAL_STATED,
                "UNRESOLVED",
                "Model B critiques that proposal.",
                "Model B critiques that proposal.",
                declared_loss=("semantic_modality_not_frozen_for_critique",),
            ),
            SourceFixtureTurn(
                "t3",
                3,
                ActorKind.HUMAN,
                OriginType.USER_STATED,
                "UNRESOLVED",
                "I have not accepted either position.",
                "I have not accepted either position.",
            ),
        ),
        expected={
            "endorsement": "UNKNOWN",
            "must_not_become": ("USER_DECISION",),
            "must_preserve_distinct_sources": True,
        },
    ),
    SourceBoundaryFixture(
        fixture_id="RB-10",
        title="User-model contamination",
        turns=(
            SourceFixtureTurn(
                "t1",
                1,
                ActorKind.TITAN_COMPONENT,
                OriginType.MODEL_INFERRED,
                "HYPOTHESIS",
                "You may be avoiding a decision.",
                "You may be avoiding a decision.",
            ),
            SourceFixtureTurn(
                "t2",
                2,
                ActorKind.HUMAN,
                OriginType.USER_STATED,
                "UNRESOLVED",
                "I did not confirm that interpretation.",
                "I did not confirm that interpretation.",
            ),
        ),
        expected={"must_not_become": ("USER_TESTIMONY", "IDENTITY_FACT")},
    ),
    SourceBoundaryFixture(
        fixture_id="RB-11",
        title="Historical state is not current",
        turns=(
            SourceFixtureTurn(
                "t1",
                1,
                ActorKind.SERVICE,
                OriginType.DOCUMENT_STATED,
                "ASSERTION",
                "Historical note: PR #373 is OPEN.",
                "PR #373 is OPEN",
                temporal_status="HISTORICAL",
            ),
            SourceFixtureTurn(
                "t2",
                2,
                ActorKind.SYSTEM,
                OriginType.SYSTEM_OBSERVED,
                "ASSERTION",
                "Live owner reports PR #373 is MERGED.",
                "PR #373 is MERGED",
                temporal_status="CURRENT",
            ),
        ),
        expected={
            "governing_temporal_status": "CURRENT",
            "must_not_govern_temporal_status": "HISTORICAL",
        },
    ),
)


def test_fixture_wave_is_explicitly_shadow_only_and_non_authoritative() -> None:
    assert TICC_FIXTURE_SCHEMA_VERSION == "ticc.fixtures.v0_1"
    assert TICC_FIXTURE_STATUS == "TEST_ONLY_SHADOW_NO_RUNTIME_AUTHORITY"


def test_fixture_ids_turn_refs_and_sequences_are_deterministic() -> None:
    fixture_ids = [fixture.fixture_id for fixture in FIXTURES]
    assert len(fixture_ids) == len(set(fixture_ids))

    for fixture in FIXTURES:
        assert tuple(turn.sequence for turn in fixture.turns) == tuple(
            range(1, len(fixture.turns) + 1)
        )
        refs = tuple(turn.turn_ref for turn in fixture.turns)
        assert len(refs) == len(set(refs))


def test_source_spans_and_hashes_are_derived_from_literal_normalized_source() -> None:
    for fixture in FIXTURES:
        for turn in fixture.turns:
            assert turn.raw_text == turn.normalized_text
            start, end = turn.span_offsets
            assert 0 <= start < end <= len(turn.normalized_text)
            assert turn.normalized_text[start:end] == turn.normalized_span
            assert len(turn.raw_text_sha256) == 64
            assert len(turn.slice_sha256) == 64
            assert turn.raw_text_sha256 == sha256(
                turn.normalized_text.encode("utf-8")
            ).hexdigest()
            assert turn.slice_sha256 == sha256(
                turn.normalized_span.encode("utf-8")
            ).hexdigest()


def test_actor_origin_and_semantic_modality_are_orthogonal_axes() -> None:
    for fixture in FIXTURES:
        for turn in fixture.turns:
            assert isinstance(turn.actor_kind, ActorKind)
            assert isinstance(turn.origin_type, OriginType)
            assert turn.semantic_modality in SEMANTIC_MODALITIES
            assert not turn.semantic_modality.startswith(
                ("MODEL_", "SYSTEM_", "EXTERNAL_", "USER_")
            )


def test_status_axes_are_not_encoded_as_semantic_modality() -> None:
    rb11 = next(fixture for fixture in FIXTURES if fixture.fixture_id == "RB-11")
    assert tuple(turn.semantic_modality for turn in rb11.turns) == (
        "ASSERTION",
        "ASSERTION",
    )
    assert tuple(turn.temporal_status for turn in rb11.turns) == (
        "HISTORICAL",
        "CURRENT",
    )


def test_required_rosebud_failure_classes_are_covered_without_runtime_claims() -> None:
    by_id = {fixture.fixture_id: fixture for fixture in FIXTURES}
    assert {
        "RB-01",
        "RB-02",
        "RB-03",
        "RB-05",
        "RB-06",
        "RB-07",
        "RB-08",
        "RB-10",
        "RB-11",
    } <= set(by_id)

    assert by_id["RB-01"].expected["relation"] == "CORRECTS"
    assert by_id["RB-02"].expected["governing_modality"] == "DECISION"
    assert (
        by_id["RB-03"].expected["must_preserve_qualifier"]
        == "until I explicitly approve it"
    )
    assert "MEASUREMENT" in by_id["RB-05"].expected["must_not_become"]
    assert "EXECUTED_EXPERIENCE" in by_id["RB-06"].expected["must_not_become"]
    assert "IMPLEMENTED" in by_id["RB-07"].expected["must_not_become"]
    assert by_id["RB-08"].expected["endorsement"] == "UNKNOWN"
    assert "IDENTITY_FACT" in by_id["RB-10"].expected["must_not_become"]
    assert by_id["RB-11"].expected["governing_temporal_status"] == "CURRENT"


def test_unfrozen_semantics_declare_loss_instead_of_inventing_a_type() -> None:
    rb08 = next(fixture for fixture in FIXTURES if fixture.fixture_id == "RB-08")
    critique = rb08.turns[1]
    assert critique.semantic_modality == "UNRESOLVED"
    assert critique.declared_loss == (
        "semantic_modality_not_frozen_for_critique",
    )


def test_conditional_directive_keeps_qualifier_separate_from_modality() -> None:
    rb03 = next(fixture for fixture in FIXTURES if fixture.fixture_id == "RB-03")
    directive = rb03.turns[0]
    assert directive.semantic_modality == "DIRECTIVE"
    assert directive.qualifier_text == "until I explicitly approve it"
    assert directive.qualifier_text in directive.raw_text
