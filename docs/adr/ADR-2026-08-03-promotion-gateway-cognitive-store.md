# ADR — Gate `CognitiveFactStore.transition(..., Validated)` through PromotionGateway

**Status:** accepted for one cognitive-store caller only  
**Date:** 2026-08-03  
**Issue:** #165  
**Dependency:** PromotionGateway foundation and the graduated, consolidation, API, and guardian-tool migrations

## Context

`CognitiveFactStore.transition()` delegates every target to the generic
`core.memory.promote_esm_to()` ladder. That helper intentionally performs ordinary ESM
transitions all the way through `Validated`; it does not run TruthGate. Consequently a
weak Observed fact can be walked through Hypothesized and Supported into Validated by the
cognitive facade without evidence or confidence enforcement.

`CognitiveRuntime.transition()` delegates to this method, so securing the store facade
also secures the runtime facade without a second authority implementation.

## Decision

Preserve the generic ladder for all targets except `Validated`. For `Validated`:

```text
CognitiveFactStore.transition
→ generic legal ladder only to Supported
→ PromotionRequest(requested_by=cognitive_store or caller actor)
→ PromotionGateway
→ current-memory adapter
→ existing validate_and_promote()
→ TruthGate + CAS
→ emit fact_esm_transition only when the final hop committed
→ return the current CognitiveFact snapshot
```

The current-memory adapter resolves the canonical `core.memory` module when the gateway
delegates, matching the repository's module-reload and isolated-store test model.

## Preserved behavior

- non-Validated transitions retain the existing generic ladder behavior;
- a strong Observed fact may still be advanced to Validated in one facade call;
- intermediate Observed → Hypothesized → Supported transitions remain legal and audited;
- an already Validated fact remains an idempotent successful call;
- return type remains `CognitiveFact | None`;
- caller actor is preserved;
- no threshold, mode, retry, outbox, response-model, or feature-default change.

## Corrected behavior

- a weak fact cannot reach Validated through CognitiveFactStore or CognitiveRuntime;
- after rejection it remains Supported and can be retried after evidence changes;
- a rejected or missing final promotion does not publish a false
  `fact_esm_transition` event claiming an authoritative transition;
- only a committed final gateway outcome publishes that event. An idempotent replay does
  not publish a duplicate transition event.

## Validation evidence

Focused validation proved:

- exactly one gateway call for a Validated attempt and no direct final ladder step into
  Validated;
- weak direct Observed → Validated attempt stops at Supported;
- strong direct Observed → Validated succeeds;
- sequential lower-state transitions remain unchanged;
- rejection publishes no transition event;
- successful final commit publishes one transition event;
- idempotent replay publishes no duplicate event;
- CognitiveRuntime delegation inherits the same gate;
- reload-safe gateway/store behavior remains green;
- the existing cognitive-store API regression remains green.

The first one-shot run produced 30 passing tests and one infrastructure error because its
install profile omitted the repository's `server` extra required by the existing FastAPI
test. No production assertion failed. The corrected run used the official server extra,
passed the complete focused suite, removed the temporary workflow and patch script, and
published the final clean four-file change-set.

Architecture-freeze, Ruff, blocking mypy, full repository pytest, and Docker must still
pass on the final maintainer-authored head before merge.

## Scope boundary

This PR does not change relation lifecycle, compound truth-maintenance supersede, Ring
Zero paths, or the generic `promote_esm_to()` helper itself. The helper remains available
for non-Validated transitions and legacy callers pending individual classification.
