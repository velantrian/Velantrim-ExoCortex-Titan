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
- `get_salience_detector()` remains an **explicit legacy singleton**. It retains
  process-wide history until `reset_salience_detector()` and must not be shared
  between independent callers or tenants.
- `analyze_episode_salience()` now uses a fresh detector for calls without an
  explicit `detector=` argument. Text signals still work, but temporal streak
  and return history cannot accumulate across those unscoped calls.
- Callers that require temporal continuity must retain and explicitly pass
  their own `SalienceDetector` instance (`detector=...`). This scopes history
  to that instance, not to an authenticated user or tenant.
- Caps, priority words, clarification, return-after-pause and the weight cap retain
  their existing behavior. Signal names, public constructor arguments and metadata
  format remain unchanged.

## Evidence

The original nine cases in `tests/test_salience.py` produce **2 failed / 7 passed**
against the unchanged baseline and **9 passed** at the initial #489 head. Additional
synthetic caller-A/caller-B controls reproduce contamination of both
`topic_streak_3d` and `topic_return_24h` through the unscoped singleton:
a first B observation on day 3 incorrectly receives weight 3.2 after
A's days 1–2, versus 1.0 with a fresh B history. The follow-up regressions
pin the safe unscoped default and explicitly retained per-caller histories.
These additions require exact-head hosted verification before claiming a new count.

The combined focused run with `tests/test_experience_replay_velum_bridge.py` and
`tests/test_decay_orchestrator_smoke.py` produces **31 passed** on Python 3.12.14 /
pytest 9.2.0. It uses local synthetic data, without model/provider or graph-server calls.
At the initial #489 head `a07d8e8941fc`, all five hosted workflows completed
successfully: CI, Docker, CodeQL, Stage 9 and Stage 10 (CI pytest:
4778 passed, 17 skipped, 1 xfailed). This is historical evidence for that
specific SHA, **not** evidence for any subsequent fix commit.

```bash
python -m pytest tests/test_salience.py \
  tests/test_experience_replay_velum_bridge.py \
  tests/test_decay_orchestrator_smoke.py -q
```

## Remaining boundaries

Detector isolation is not tenant authorization or isolation of every runtime caller.
The explicitly requested legacy singleton still has no user/scope key and is
unsafe for multiple independent owners. The existing ingest route in
`core/velum_bridge.py` does not provide a detector; it therefore keeps lexical
salience signals but **does not accumulate temporal signals across ingest calls**
until a properly owned detector is explicitly supplied in a separately reviewed change.
Velum itself also retains a process-wide singleton, so this is **not** end-to-end
tenant isolation or a privacy-leak demonstration. History remains in-memory and is
lost on restart; no persistence or migration is added. Salience is significance,
not evidence or truth; runtime feature flags and activation posture are unchanged.

This is an original local correction to Titan's existing implementation. No donor code,
coefficients or new memory subsystem are imported.
