# 🧵 Continuity Trusted Signal Producer — Final Merged Handoff

**Status:** `IMPLEMENTED IN MAIN · SHADOW ONLY · NOT WIRED · NOT ENABLED`  
**Implementation PR:** #214 → `5f1ce06199ebabd6a23f3656ddd91c5c968170fe`  
**Coverage isolation PR:** #218 → `3c73eab991c305d174f6c2c5805595c7998d4068`  
**Final hardening PR:** #220 → `e37a5d13332628bcdbd0d9441d7a61d5f8a8d523`  
**Final tested hardening head:** `289ce30433bf4660809f7ce194d901abadf7c7d2`  
**Post-merge documentation validation:** run `31077998734` → PASS *(temporary workflow, not retained)*

## Scope

Titan now has a deterministic typed producer for the existing
`ContinuityComputeSignals` contract from already-typed observations.

It does not extract observations from raw conversations and does not add:

- `/query`, startup, worker or scheduler wiring;
- answer, tool, action or policy authority;
- Canon, TruthGate, retrieval or ordinary memory writes;
- persistence, network or clock dependencies;
- tenant/subject authorization, consent, retention or erasure lifecycle.

## Final review corrections

The merged lineage includes all independent-review corrections:

1. policy `Iterable[str]` inputs accept ordinary and one-shot iterables while
   rejecting scalar text, bytes, empty and malformed collections;
2. trusted warning signals use OR semantics so one trusted warning is not
   suppressed by confirmation thresholds;
3. observation `evidence_refs` and `reason_codes` reject scalar text, bytes and
   non-iterables rather than iterating them character by character;
4. per-signal provenance retains trusted negative boolean observations,
   including false-only warning groups and fail-conservative unavailability;
5. supported-schema observations have their canonical content-addressed
   `observation_id` recomputed before trust;
6. an ID/content mismatch becomes reason-coded
   `OBSERVATION_ID_MISMATCH` rejection;
7. malformed categorical values fail through controlled
   `ContinuitySignalProducerError`, not raw `KeyError`;
8. contradiction counts remain unique-scope based while provenance retains
   every trusted contributing observation;
9. evidence-reference aggregation uses linear accumulation and the focused
   tests assert actual behavior rather than tautologies.

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

multiple contradiction observations for one scope
→ active_contradictions counts the scope once
→ provenance retains every trusted observation
```

## Compatibility boundary

The following public contracts remain unchanged:

- `ComputePath` five-value set;
- `ComputeDecision` constructor and serialization;
- `decide_compute_path()` signature and behavior;
- `ContinuityComputeSignals` shape;
- `assess_compute_with_continuity()` signature;
- R1–R5B disabled/shadow authority boundaries.

## Final validation evidence

### PR #214 implementation

```text
Full Titan CI         31076502756 → PASS
Continuity contracts  31076502806 → PASS
Docker hardening      31076502802 → PASS
```

### PR #218 coverage instrumentation isolation

```text
Full normal pytest       → PASS
Coverage ratchet ≥74%    → PASS
Trace-hook stress tests  → still blocking in normal pytest
```

### PR #220 defensive hardening

```text
Focused run          31077257141 → Ruff + mypy + 108 tests PASS
Full Titan CI        31077329680 → PASS
Continuity contracts 31077329650 → PASS
Docker hardening     31077329644 → PASS
Copilot review       4/4 files · 0 comments
Unresolved threads   0
```

## Remaining architecture work

Green tests and merged code do not authorize runtime wiring. Separate work is
still required for:

- trusted observation-source adapters;
- tenant and subject authorization;
- privacy, consent, retention and erasure lifecycle;
- persistence and replay strategy;
- feature flags and staged activation;
- calibration, monitoring and rollback;
- live-runtime evidence that the shadow assessment improves outcomes.
