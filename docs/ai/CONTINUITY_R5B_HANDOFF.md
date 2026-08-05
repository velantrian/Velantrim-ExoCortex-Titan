# 🧩 Continuity R5B Recovery Hand-off

**Date:** 2026-08-05  
**PR:** #206  
**Base:** `main@58e29bba26299ce7003b62e73fd3b25e028956de`  
**Initial runner head:** `0e0679feb234455f6a5768c7f9e783f00abb5889`  
**Focused-tested head:** `a4a6e08462fc948fb1e5620968ecdaa93d28703f`  
**Status:** `DRAFT / PRE-MERGE / DISABLED BY DEFAULT / NOT WIRED`

## Scope

R5B is the final recovery layer of Continuity Milestone 1. It composes the accepted R1–R5A components in one deterministic in-memory baseline/replay evaluation.

```text
ConversationEpisode
→ ThreadWeaver
→ Continuity context
→ State / Goal / OpenLoop projections
→ WorkingMemory adapters
→ existing WorkingMemoryGate
→ existing ContextPackBuilder
→ R4 compute assessment
→ R5A baseline/replay snapshots
→ ReplayEvaluationReport
→ R5A Advisory Shadow
→ immutable result + receipt
```

## Disabled boundary

The default runner exits before pipeline input validation or component execution. Disabled and completed receipts require:

- `MAIN_ANSWER_UNTOUCHED`;
- `CANON_UNCHANGED`;
- `ADVISORY_SHADOW_ONLY`;
- `NO_RUNTIME_AUTHORITY`.

`enabled=True` is local object-evaluation permission only. It is not a runtime feature flag, startup hook, service registration or production mode.

## Current API adaptation

Historical #147 is not copied unchanged:

- R4 uses `assess_compute_with_continuity()` and preserves the five legacy paths;
- R5B stores the final R4 assessment decision in the replay snapshot but never executes it;
- R5A Advisory Shadow v2 requires passed replay, private audience, explicit typed relevance and exact actionable projection;
- Advisory `DEFER` remains distinct from compute routing.

## Input and policy boundary

R5B accepts only typed episodes, assertions, relations, goals, attestations, open-loop records, Gate policy facts, compute signals and safety observations. It never extracts these from raw request text.

`AdvisoryIntent` resolves an explicit semantic ref to exactly one generated projection. Zero or multiple matches fail closed. The runner does not infer relevance.

Gate policy values remain caller-owned facts. The runner copies them into typed records but does not become their policy owner.

## Authority boundary

R5B has no:

- server/startup registration, worker, scheduler or daemon;
- API route or `/query` integration;
- persistence, migration or durable queue;
- retrieval, network or provider calls;
- Canon, ESM, TruthGate, memory or policy mutation;
- answer generation or answer-path modification;
- reminder delivery, notification scheduling, tools or actions;
- user-visible output or feature activation.

## Validation checklist

- [x] disabled short-circuit before component execution
- [x] complete current R1–R5A pipeline focused test
- [x] reversed-order replay equality
- [x] R4 VERIFY escalation recorded without execution
- [x] R5A hard-gate DEFER and shared-audience SILENCE
- [x] exact Advisory target resolution
- [x] deterministic/immutable results and no-runtime receipt invariant
- [x] focused Continuity workflow green on `a4a6e084...`
- [ ] final-head Continuity workflow green
- [ ] final-head full Titan CI green
- [ ] final-head Docker hardening green
- [ ] independent final-head review complete
- [ ] final merge SHA recorded
- [ ] historical #147 closed after merge

## Initial test correction

The first runner test modelled two conflicting assertions from the same author. `StateReconciler` correctly treated the newer record as superseding the older one, not as a contested state. The end-to-end Advisory test was corrected to use an explicitly attested active goal; contested-priority behavior remains fully covered by R5A tests. Production runner code did not change.

## Remaining limitations

- all typed records and policy values still require trusted producers/owners;
- no consent, tenant authorization, retention, erasure or durable evidence lifecycle;
- no runtime corpus, calibration, monitoring, rollback or operational SLO;
- Advisory text cannot be shown or delivered;
- any live activation requires a separate ADR and explicit operator approval.
