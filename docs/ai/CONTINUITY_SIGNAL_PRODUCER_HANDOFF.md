# 🧵 Continuity Trusted Signal Producer — Final Review Handoff

**Status:** `DRAFT · SHADOW-ONLY · UNWIRED · NO RUNTIME AUTHORITY`  
**Pull request:** #214  
**Current validation base:** `main@3c73eab991c305d174f6c2c5805595c7998d4068`  
**Implementation lineage reviewed through:** `c78d6d02ba361ec72bee63f0fdf9ebe1c64dadd5`

## Scope

This change adds a deterministic producer for the existing
`ContinuityComputeSignals` contract from already-typed observations.

It does not extract observations from raw conversations and does not add:

- `/query`, startup, worker or scheduler wiring;
- answer, tool, action or policy authority;
- Canon, TruthGate, retrieval or ordinary memory writes;
- persistence, network or clock dependencies;
- tenant/subject authorization, consent, retention or erasure lifecycle.

## Independent-review corrections

The final implementation lineage includes corrections for all four review
findings:

1. policy `Iterable[str]` inputs accept ordinary and one-shot iterables while
   rejecting scalar text, bytes, empty and malformed collections;
2. trusted warning signals use OR semantics so one trusted warning is not
   suppressed by confirmation thresholds;
3. observation `evidence_refs` and `reason_codes` reject scalar text, bytes and
   non-iterables rather than iterating them character by character;
4. per-signal provenance retains trusted negative boolean observations,
   including false-only warning groups and fail-conservative unavailability.

Additional review cleanup:

- the composition test asserts a real Continuity reason code;
- evidence-coverage test naming matches behavior;
- evidence reference aggregation avoids repeated tuple concatenation;
- temporary patch workflows and scripts are absent from the final diff.

## Provenance semantics

```text
warning group with trusted True
→ value = True
→ provenance includes all trusted positive and negative observations

warning group with trusted False only
→ value = False
→ rule = trusted_false_observations_only
→ provenance retains observation IDs, producers, evidence and confidence

availability with trusted False
→ value = False
→ rule = trusted_negative_observations_fail_conservative

availability with trusted True and False
→ value = False
→ conflict provenance retains both sides
```

## Compatibility boundary

The following public contracts remain unchanged:

- `ComputePath` five-value set;
- `ComputeDecision` constructor and serialization;
- `decide_compute_path()` signature and behavior;
- `ContinuityComputeSignals` shape;
- `assess_compute_with_continuity()` signature;
- R1–R5B disabled/shadow authority boundaries.

## Required final gates

Before merge, verify the exact final head against the current validation base rather than any earlier green head:

- repository hygiene: no temporary workflow or patch script in the diff;
- Ruff;
- blocking mypy;
- focused Continuity tests including review regressions;
- full pytest;
- coverage floor ≥74% with the accepted trace-hook instrumentation isolation;
- Docker hardening;
- unresolved review threads = 0;
- final diff review for authority leakage, mutable state and nondeterminism;
- merge by expected exact head SHA.

Green tests do not authorize runtime wiring. A separate producer-source,
privacy, consent and activation architecture remains required.