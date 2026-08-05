# ADR-2026-08-05: Compatibility-preserving Continuity compute assessment

- **Status:** ACCEPTED FOR SHADOW-ONLY RECOVERY
- **Scope:** Continuity R4 compute integration
- **Date:** 2026-08-05
- **Decision owner:** repository maintainer
- **Runtime activation:** forbidden by this ADR

## Context

Historical PR #144 attempted to add continuity-aware compute signals by changing the existing `ComputeController` public contract. It introduced a new `DEFER_PATH`, changed `ComputeDecision.reasons` from `list[str]` to `tuple[str, ...]`, added fields to `ComputeDecision`, changed serialization, and refactored the legacy decision function.

That shape is unsafe to recover directly on current `main`:

- `core.rapid_orientation._cost_for_path()` exhaustively maps every current `ComputePath` value;
- external or future callers may construct `ComputeDecision` positionally;
- callers may depend on the current seven-field `to_dict()` payload;
- a frozen dataclass still exposes a mutable legacy reasons list, and changing it would be a compatibility break;
- no accepted downstream contract exists for a new defer route;
- continuity signals remain shadow inputs supplied by a separately trusted caller.

## Decision

R4 preserves the legacy compute API unchanged:

```text
ComputePath
ComputeDecision
decide_compute_path(query, *, goal, candidate_count, uncertainty)
```

The following remain stable:

- exactly five compute paths: FAST, NORMAL, DEEP, VERIFY and CREATIVE;
- the seven existing `ComputeDecision` fields;
- positional constructor compatibility;
- mutable `reasons: list[str]` behaviour;
- the existing `to_dict()` key set;
- the existing function signature and legacy decision matrix.

Continuity uses a separate explicit API:

```text
ContinuityComputeSignals
        ↓
assess_compute_with_continuity(...)
        ↓
ContinuityComputeAssessment
  ├─ base_decision: unchanged legacy output
  ├─ decision: equal, raised to VERIFY, or DEEP capped to NORMAL
  ├─ context_rebuild_required
  ├─ typed reason_codes
  └─ shadow_only = true
```

## Allowed R4 effects

When a caller explicitly invokes the new shadow API, R4 may:

- raise an important contradictory claim to `VERIFY_PATH`;
- raise missing/stale required current state to `VERIFY_PATH` and request context rebuild;
- raise a high-sensitivity, low-evidence claim to `VERIFY_PATH`;
- cap a `DEEP_PATH` decision to `NORMAL_PATH` when context is explicitly degraded.

R4 never downgrades `VERIFY_PATH`.

## Rejected alternatives

### Add `DEFER_PATH` now

Rejected. A new enum member would make existing exhaustive consumers incomplete and no accepted end-to-end defer semantics exist. Critical low-evidence inputs conservatively use `VERIFY_PATH` in R4.

### Modify `ComputeDecision`

Rejected. New fields or a changed reasons type would alter constructor and serialization compatibility.

### Add an optional `continuity=` argument to `decide_compute_path()`

Rejected. The legacy function signature is itself a compatibility contract. Continuity assessment is explicit and separate.

### Wire the assessment into `/query`

Rejected. R4 is shadow-only and has no trusted producer, policy owner, runtime flag, answer-path authority or operational evidence.

## Invariants

1. Legacy calls produce the same decisions and serialization.
2. Existing `ComputePath` consumers remain exhaustive.
3. Continuity assessment requires typed signals and fails closed on invalid values.
4. Continuity cannot silently lower verification.
5. Critical uncertainty cannot become answer or action authority.
6. Assessment contains no retrieval, persistence, Canon, TruthGate, answer, tool or action API.
7. `shadow_only=False` is rejected by contract.
8. No runtime caller is introduced in this recovery.

## Validation

R4 requires:

- a legacy signature test;
- a five-route legacy decision matrix;
- direct-constructor and serialization compatibility tests;
- an exhaustive `RapidOrientation` mapping test;
- signal validation and deterministic replay tests;
- focused Continuity workflow, full repository CI and Docker hardening;
- independent final-head review;
- GitHub and Notion synchronization before merge.

## Consequences

R4 is intentionally less ambitious than historical #144 but safer to merge. A future defer route requires its own ADR, complete downstream mapping, explicit runtime semantics, cancellation/timeout behaviour, user-visible handling and operator approval.
