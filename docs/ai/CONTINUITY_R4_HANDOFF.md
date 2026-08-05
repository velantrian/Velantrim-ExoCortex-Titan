# ⚙️ Continuity R4 Recovery Hand-off

**Date:** 2026-08-05  
**PR:** #204  
**Base:** `main@a19d16656676ad5c98c92d4776e9709edbfb920c`  
**Initial code head:** `2af8eadc04ee7a1f22528ca4815e02ecc2639610`  
**Status:** `DRAFT / PRE-MERGE / SHADOW ONLY / NOT WIRED`

## Why historical #144 is not copied

Historical PR #144 changed the existing compute contract by:

- adding `DEFER_PATH`;
- changing `ComputeDecision.reasons` from `list` to `tuple`;
- adding fields to `ComputeDecision` and its serialized payload;
- refactoring the legacy `decide_compute_path()` implementation and signature surface.

Current `main` has an exhaustive `ComputePath` consumer in `core.rapid_orientation`. No accepted runtime/user-facing semantics exist for a new defer route. Direct recovery would therefore create an avoidable compatibility and exhaustiveness risk.

## R4 decision

Legacy compute routing remains unchanged:

```text
ComputePath = FAST | NORMAL | DEEP | VERIFY | CREATIVE
ComputeDecision = existing seven-field contract
decide_compute_path(query, *, goal, candidate_count, uncertainty)
```

Continuity uses a separate explicit shadow API:

```text
ContinuityComputeSignals
  → assess_compute_with_continuity(...)
  → ContinuityComputeAssessment
       base_decision
       decision
       context_rebuild_required
       reason_codes
       shadow_only = true
```

## Allowed effects

R4 may only:

- raise an important contradictory claim to VERIFY;
- raise missing/stale required state to VERIFY and request context rebuild;
- raise high-sensitivity low-evidence claims to VERIFY;
- cap a DEEP route to NORMAL when context is explicitly degraded.

R4 never downgrades VERIFY and never creates a new compute enum value.

## Compatibility proof

Focused tests lock:

- exact legacy function signature;
- exact five-value `ComputePath` set;
- positional `ComputeDecision` constructor;
- mutable legacy reasons-list behavior;
- exact legacy serialization keys;
- VERIFY/CREATIVE/DEEP/FAST/NORMAL decision matrix;
- exhaustive `RapidOrientation` cost mapping;
- neutral signals producing an identical legacy decision.

## Authority boundary

R4 has no:

- runtime/startup/worker/query integration;
- continuity-signal producer;
- retrieval, persistence or Canon/ESM/TruthGate mutation;
- answer, advice, tool or action authority;
- feature activation or user-visible behavior.

## Validation checklist

- [x] initial focused Continuity gate green
- [ ] final-head Continuity gate green
- [ ] final-head full Titan CI green
- [ ] final-head Docker hardening green
- [ ] independent final-head review complete
- [ ] Notion final-head checkpoint synchronized
- [ ] final merge SHA recorded
- [ ] historical #144 closed as superseded after merge

## Remaining limitations

- signal trust and policy ownership are separate designs;
- no live runtime evidence exists;
- critical low-evidence inputs VERIFY rather than DEFER;
- a future defer route requires its own ADR and exhaustive consumer handling;
- R5 replay evaluation, Advisory shadow and disabled runner remain separate.
