# Salience topic-history contract

Status: proposed correction on a Draft PR; resolve the live PR before treating it as main.
Baseline: `f44216656673b2a49e64f8cc7c8bca6d32e44d3f` (2026-10-29).

## Behavior

- `topic_streak_3d` requires consecutive calendar dates ending on the current observation.
  Observations on October 1, 2, 3 and 10 do not qualify on October 10. Observations on
  October 10, 11 and 12 qualify on October 12. Repeated observations on one date count
  as one date. The existing 14-day history window remains unchanged.
- Each explicitly constructed `SalienceDetector` owns its topic history. Creating a
  second detector starts with empty history, without affecting the first detector.
- `get_salience_detector()` and `analyze_episode_salience()` retain the existing
  process-wide singleton lifecycle. Its observations accumulate until
  `reset_salience_detector()` replaces the default instance.
- Caps, priority words, clarification, return-after-pause and the weight cap retain
  their existing behavior. Signal names, public constructor arguments and metadata
  format remain unchanged.

## Evidence

The nine cases in `tests/test_salience.py` produce **2 failed / 7 passed** against the
unchanged baseline and **9 passed** with the correction. They include paired controls:
an actual three-day sequence still earns the bonus, and the original detector retains
its history while a separately constructed detector starts empty.

The combined focused run with `tests/test_experience_replay_velum_bridge.py` and
`tests/test_decay_orchestrator_smoke.py` produces **31 passed** on Python 3.12.14 /
pytest 9.2.0. It uses local synthetic data, without model/provider or graph-server calls.
Hosted CI and merge readiness must be resolved on the exact proposed head.

```bash
python -m pytest tests/test_salience.py \
  tests/test_experience_replay_velum_bridge.py \
  tests/test_decay_orchestrator_smoke.py -q
```

## Remaining boundaries

Detector isolation is not tenant authorization or isolation of every runtime caller.
The convenience singleton remains process-wide and has no user/scope key. These tests
do not establish isolation between real tenants. History is in-memory and is lost on
restart; this change adds no persistence or migration. Salience signals do not provide
new evidence or promote a fact to a verified epistemic state. Runtime feature flags and
activation posture are unchanged.

This is an original local correction to Titan's existing implementation. No donor code,
coefficients or new memory subsystem are imported.
