# 🧩 Continuity R3 Recovery Hand-off

**Date:** 2026-08-05  
**PR:** #203  
**Base:** `main@320d5ae9f89780efc553ffbfc3a17c1ebc83b47e`  
**Initial recovery head:** `f178feadf698ef5ca51d14a37a7beb7863cf2999`  
**Status:** `DRAFT / PRE-MERGE / NOT WIRED / NO USER-FACING AUTHORITY`

## Scope

R3 recovers the projection and WorkingMemory-adapter material from historical stacked PRs #138–#143 onto current `main`. The old stacked branches are source material only and are not merged or rebased.

Recovered components:

- `ContinuityContextPack`, `ContinuityReceipt`, deterministic assembly;
- exact-source continuity-to-`KnowledgeCapsule` adapter;
- deterministic current-state reconciliation;
- read-only GoalStack snapshots;
- explicit typed `GoalAttestation` admission;
- typed open-loop signals and resolution projections;
- state/goal/open-loop adapter into the existing `WorkingMemoryGate`;
- Synaptic/Continuity ownership ADR;
- focused tests for replay stability, fail-closed validation and authority absence.

## Authority boundary

R3 is a typed projection layer. It does not own:

- durable storage or migrations;
- raw-text extraction or trusted producer admission;
- truth, epistemic state or Canon mutation;
- salience, privacy or eligibility policy;
- the WorkingMemory disposition decision;
- the final prompt budget or final ContextPack ownership;
- compute routing, advisory, answers, tools or actions;
- startup, worker, `/query` or live runtime wiring.

```text
R1 immutable records + R2 episodes/threads
  → R3 rebuildable projections
  → caller-supplied typed policy facts
  → existing WorkingMemoryGate
  → existing ContextPack
```

## Critical invariants

1. Model inference cannot silently replace an active user statement.
2. Conflicting user statements remain contested and reviewable.
3. Goals are excluded without an explicit typed attestation.
4. Open loops are not inferred from raw text.
5. Projection adapters preserve `truth_confidence=None`.
6. Exact policy coverage is required; missing or extra policy input fails closed.
7. Existing Gate dispositions and budgets remain authoritative.
8. No second selector, prompt pack or Canon path is introduced.

## Validation checklist

- [ ] Continuity contracts green on final head
- [ ] full Titan CI green on final head
- [ ] Docker hardening green on final head
- [ ] independent authority review complete
- [ ] compatibility with current `KnowledgeCapsule`, `WorkingMemoryGate`, `ContextPack` and `GoalStack` confirmed
- [ ] Notion checkpoint synchronized
- [ ] final merge SHA recorded
- [ ] historical #138–#143 closed as superseded only after merge

## Known limitations

- trusted producers for assertions, attestations and open-loop signals are not designed here;
- projections are not persisted and are not live-runtime inputs;
- caller-supplied attention/privacy/eligibility facts need a separately governed owner;
- consent, retention, erasure and access control remain mandatory before durable personal continuity;
- R4 compute integration and R5 evaluation/advisory/runner remain separate reviews.
