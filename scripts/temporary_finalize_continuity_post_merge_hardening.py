"""Temporary exact-string patcher for Continuity post-merge hardening."""
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one occurrence: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


producer_path = Path("core/continuity/signal_producer.py")
replace_once(
    producer_path,
    '''    "MISSING_REQUIRED_SCOPE": "this signal_type requires a non-empty scope",
}''',
    '''    "MISSING_REQUIRED_SCOPE": "this signal_type requires a non-empty scope",
    "OBSERVATION_ID_MISMATCH": (
        "observation_id does not match canonical observation content"
    ),
}''',
)
replace_once(
    producer_path,
    '''def _trust_reason(
    observation: ContinuitySignalObservation, policy: ContinuitySignalPolicy
) -> str | None:
    if observation.schema_version != OBSERVATION_SCHEMA_VERSION:
''',
    '''def _trust_reason(
    observation: ContinuitySignalObservation, policy: ContinuitySignalPolicy
) -> str | None:
    try:
        expected_observation_id = _digest(observation.identity_payload())
    except (AttributeError, TypeError, ValueError):
        return "OBSERVATION_ID_MISMATCH"
    if observation.observation_id != expected_observation_id:
        return "OBSERVATION_ID_MISMATCH"
    if observation.schema_version != OBSERVATION_SCHEMA_VERSION:
''',
)
replace_once(
    producer_path,
    '''    top_priority = max(
        priority_table[_string_value(observation.value)] for observation in group
    )
    contributing = tuple(
        observation
        for observation in group
        if priority_table[_string_value(observation.value)] == top_priority
    )
    value = _string_value(contributing[0].value)
''',
    '''    ranked: list[tuple[ContinuitySignalObservation, str, int]] = []
    for observation in group:
        raw_value = _string_value(observation.value)
        priority = priority_table.get(raw_value)
        if priority is None:
            raise ContinuitySignalProducerError(
                f"unsupported {signal_type.value} observation value: {raw_value!r}"
            )
        ranked.append((observation, raw_value, priority))
    top_priority = max(priority for _, _, priority in ranked)
    contributing = tuple(
        observation
        for observation, _, priority in ranked
        if priority == top_priority
    )
    value = next(
        raw_value
        for _, raw_value, priority in ranked
        if priority == top_priority
    )
''',
)
replace_once(
    producer_path,
    '''    by_scope: dict[str, ContinuitySignalObservation] = {}
    for observation in sorted(group, key=lambda item: item.observation_id):
        by_scope.setdefault(_required_scope(observation.scope), observation)
    unique = tuple(by_scope[key] for key in sorted(by_scope))
    raw_count = len(unique)
    capped = raw_count > policy.max_contradiction_count
    count = min(raw_count, policy.max_contradiction_count)
    rule = f"unique_scopes_deduped_from_{len(group)}_observations"
    if capped:
        rule += "_capped_by_policy"
    return count, ContinuitySignalProvenance(
        signal_type=ContinuitySignalType.ACTIVE_CONTRADICTION,
        observation_ids=tuple(observation.observation_id for observation in unique),
        evidence_refs=_refs_union(unique),
        producers=_producers(unique),
        confidence=_min_confidence(unique),
        rule=rule,
        value=count,
    ), capped
''',
    '''    ordered = tuple(sorted(group, key=lambda item: item.observation_id))
    unique_scopes = {
        _required_scope(observation.scope) for observation in ordered
    }
    raw_count = len(unique_scopes)
    capped = raw_count > policy.max_contradiction_count
    count = min(raw_count, policy.max_contradiction_count)
    rule = f"unique_scopes_deduped_from_{len(group)}_observations"
    if capped:
        rule += "_capped_by_policy"
    return count, ContinuitySignalProvenance(
        signal_type=ContinuitySignalType.ACTIVE_CONTRADICTION,
        observation_ids=tuple(
            observation.observation_id for observation in ordered
        ),
        evidence_refs=_refs_union(ordered),
        producers=_producers(ordered),
        confidence=_min_confidence(ordered),
        rule=rule,
        value=count,
    ), capped
''',
)

work_log_path = Path("docs/ai/WORK_LOG.md")
replace_once(
    work_log_path,
    "Base:      main @ adfccb02f88b290aac8411e94aac69417defbafe",
    "Merge base: main @ 3c73eab991c305d174f6c2c5805595c7998d4068",
)

tests_path = Path("tests/test_continuity_signal_producer_review_regressions.py")
replace_once(
    tests_path,
    '''import pytest

from core.continuity import (
''',
    '''import pytest

import core.continuity.signal_producer as signal_producer_module
from core.continuity import (
''',
)
replace_once(
    tests_path,
    '''    ContinuitySignalPolicy,
    ContinuitySignalType,
''',
    '''    ContinuitySignalPolicy,
    ContinuitySignalProducerError,
    ContinuitySignalType,
''',
)
replace_once(
    tests_path,
    '''    evidence_ref: str = "evidence-1",
    confidence: float = 0.9,
) -> ContinuitySignalObservation:
''',
    '''    evidence_ref: str = "evidence-1",
    confidence: float = 0.9,
    scope: str | None = None,
) -> ContinuitySignalObservation:
''',
)
replace_once(
    tests_path,
    '''        evidence_refs=(evidence_ref,),
        reason_codes=("review-regression",),
    )
''',
    '''        evidence_refs=(evidence_ref,),
        reason_codes=("review-regression",),
        scope=scope,
    )
''',
)

tests = tests_path.read_text(encoding="utf-8")
marker = "def test_tampered_observation_id_is_reason_coded_rejection"
if marker not in tests:
    tests += '''


def test_tampered_observation_id_is_reason_coded_rejection() -> None:
    observation = _observation(
        ContinuitySignalType.CONTEXT_DEGRADED,
        True,
    )
    object.__setattr__(observation, "observation_id", "0" * 64)

    result = produce_continuity_compute_signals(
        [observation], policy=_policy()
    )

    assert result.observation_ids == ()
    assert result.ignored_or_rejected_ids == ("0" * 64,)
    assert len(result.rejected_observations) == 1
    rejected = result.rejected_observations[0]
    assert rejected.reason_code == "OBSERVATION_ID_MISMATCH"
    assert "canonical observation content" in rejected.message


def test_tampered_categorical_value_fails_with_controlled_error() -> None:
    observation = _observation(
        ContinuitySignalType.CONTEXT_FRESHNESS,
        "fresh",
    )
    object.__setattr__(observation, "value", "impossible")
    object.__setattr__(
        observation,
        "observation_id",
        signal_producer_module._digest(observation.identity_payload()),
    )

    with pytest.raises(
        ContinuitySignalProducerError,
        match="unsupported context_freshness observation value",
    ):
        produce_continuity_compute_signals(
            [observation], policy=_policy()
        )


def test_duplicate_contradiction_scope_keeps_complete_provenance() -> None:
    first = _observation(
        ContinuitySignalType.ACTIVE_CONTRADICTION,
        True,
        producer="trusted-a",
        source_id="contradiction-a",
        evidence_ref="evidence-a",
        confidence=0.9,
        scope="claim:1",
    )
    second = _observation(
        ContinuitySignalType.ACTIVE_CONTRADICTION,
        True,
        producer="trusted-b",
        source_id="contradiction-b",
        evidence_ref="evidence-b",
        confidence=0.7,
        scope="claim:1",
    )

    result = produce_continuity_compute_signals(
        [first, second], policy=_policy()
    )
    item = _provenance(
        result, ContinuitySignalType.ACTIVE_CONTRADICTION
    )

    assert result.signals.active_contradictions == 1
    assert item.observation_ids == tuple(
        sorted((first.observation_id, second.observation_id))
    )
    assert item.producers == ("trusted-a", "trusted-b")
    assert item.evidence_refs == ("evidence-a", "evidence-b")
    assert item.confidence == 0.7
    assert item.rule == "unique_scopes_deduped_from_2_observations"
'''
    tests_path.write_text(tests, encoding="utf-8")
