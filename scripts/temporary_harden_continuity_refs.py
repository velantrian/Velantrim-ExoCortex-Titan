"""Temporary exact-string patcher for final Continuity review hardening."""
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one occurrence: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    Path("core/continuity/observations.py"),
    '''def _refs(values: Iterable[str], name: str) -> tuple[str, ...]:
    items = tuple(_text(value, name) for value in values)
    if len(items) != len(set(items)):
        raise ContinuitySignalObservationError(f"{name} cannot contain duplicates")
    return tuple(sorted(items))
''',
    '''def _refs(values: Iterable[str], name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ContinuitySignalObservationError(
            f"{name} must be an iterable of strings, not text"
        )
    try:
        items = tuple(_text(value, name) for value in values)
    except TypeError as exc:
        raise ContinuitySignalObservationError(
            f"{name} must be an iterable of strings"
        ) from exc
    if len(items) != len(set(items)):
        raise ContinuitySignalObservationError(f"{name} cannot contain duplicates")
    return tuple(sorted(items))
''',
)

replace_once(
    Path("core/continuity/signal_producer.py"),
    '''    by_scope: dict[str, tuple[ContinuitySignalObservation, ...]] = defaultdict(tuple)
    for observation in sorted(group, key=lambda item: item.observation_id):
        scope = _required_scope(observation.scope)
        by_scope[scope] = by_scope[scope] + (observation,)
''',
    '''    by_scope: dict[str, list[ContinuitySignalObservation]] = defaultdict(list)
    for observation in sorted(group, key=lambda item: item.observation_id):
        scope = _required_scope(observation.scope)
        by_scope[scope].append(observation)
''',
)

tests_path = Path("tests/test_continuity_observations.py")
tests = tests_path.read_text(encoding="utf-8")
anchor = '''def test_duplicate_reason_codes_are_rejected() -> None:
    with pytest.raises(ContinuitySignalObservationError, match="duplicates"):
        _make(reason_codes=("z", "z"))
'''
addition = anchor + '''

@pytest.mark.parametrize("field_name", ["evidence_refs", "reason_codes"])
@pytest.mark.parametrize("bad_value", ["ev:1", b"ev:1", None, 42])
def test_reference_collections_reject_text_and_non_iterables(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(ContinuitySignalObservationError, match="iterable of strings"):
        _make(**{field_name: bad_value})
'''
if tests.count(anchor) != 1:
    raise SystemExit("tests: expected one reference-test insertion anchor")
tests_path.write_text(tests.replace(anchor, addition, 1), encoding="utf-8")
