"""Preserve specific schema-version rejection before canonical ID verification."""
from pathlib import Path

path = Path("core/continuity/signal_producer.py")
text = path.read_text(encoding="utf-8")
old = '''    try:
        expected_observation_id = _digest(observation.identity_payload())
    except (AttributeError, TypeError, ValueError):
        return "OBSERVATION_ID_MISMATCH"
    if observation.observation_id != expected_observation_id:
        return "OBSERVATION_ID_MISMATCH"
    if observation.schema_version != OBSERVATION_SCHEMA_VERSION:
        return "UNKNOWN_SCHEMA_VERSION"
'''
new = '''    if observation.schema_version != OBSERVATION_SCHEMA_VERSION:
        return "UNKNOWN_SCHEMA_VERSION"
    try:
        expected_observation_id = _digest(observation.identity_payload())
    except (AttributeError, TypeError, ValueError):
        return "OBSERVATION_ID_MISMATCH"
    if observation.observation_id != expected_observation_id:
        return "OBSERVATION_ID_MISMATCH"
'''
if text.count(old) != 1:
    raise SystemExit("expected one supported-schema trust block")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
