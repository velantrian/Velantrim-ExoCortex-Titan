# ADR-CONT-SYN-01: Continuity / Synaptic Contract Reconciliation

- **Status:** PROPOSED
- **Scope:** Milestone 1 contract ownership
- **Date:** 2026-08-02
- **Repository:** `velantrian/Velantrim-ExoCortex-Titan`
- **Decision owner:** human operator / maintainer

## 1. Context

Titan already contains an executable Synaptic Exo-Cortex slice:

- `SourceSpan`, `CapsuleClaim`, and `KnowledgeCapsule` in `core/knowledge_capsule.py`;
- `WorkingMemoryGate` and `WorkingMemoryPlan` in `core/working_memory_gate.py`;
- a deterministic, budget-checked `ContextPack` in `core/context_pack.py`;
- source-linked Reader implementations and shadow integration support.

The Continuity milestone adds:

- neutral `InteractionEvent` history;
- immutable `AssertionRecord` and `AssertionRelation` records;
- conversation episodes and continuity threads;
- a continuity-specific context projection and receipt.

Without an explicit reconciliation decision, Titan could acquire two competing claim contracts, two context selectors, or two final prompt payloads.

## 2. Decision

Synaptic and Continuity are complementary stages of one pipeline, not parallel implementations.

```text
raw source / interaction
        |
        +--> InteractionEvent
        |      neutral historical occurrence
        |
        `--> Semantic Reader
               |
               v
          SourceSpan + CapsuleClaim
               extraction proposal
               |
               v
          AssertionCandidate
               explicit admission boundary
               |
               v
          AssertionRecord + AssertionRelation
               normalized durable assertion history
```

Context assembly uses one existing budget path:

```text
KnowledgeCapsule candidates ----+
                                |
ContinuityContextPack ----------+--> WorkingMemoryGate
                                      |
                                      v
                                WorkingMemoryPlan
                                      |
                                      v
                              existing ContextPack
                                      |
                                      v
                               answer / shadow path
```

## 3. Canonical ownership matrix

| Responsibility | Canonical owner | Notes |
|---|---|---|
| Exact document offsets and source hash verification | `SourceSpan` | Do not introduce a second span contract. |
| Reader extraction proposal | `CapsuleClaim` | Rebuildable and provider-derived; not Canon. |
| Reader extraction bundle | `KnowledgeCapsule` | Proposal/projection; not neutral history and not Canon. |
| Neutral occurrence history | `InteractionEvent` | Records that an interaction/action/document event occurred. |
| Normalized durable assertion | `AssertionRecord` | Immutable subject/predicate/value record with actor, origin, time, privacy and provenance. |
| Assertion support/contradiction/correction | `AssertionRelation` | Separate immutable relation record. |
| Conversation continuity source | `ConversationEpisode` | Rebuildable read projection over the existing consolidator. |
| Cross-conversation relation | `ThreadLink` / `ContinuityThread` | Rebuildable continuity projection. |
| Continuity-specific retrieval result | `ContinuityContextPack` | Source of continuity candidates; not the final prompt payload. |
| Continuity explanation | `ContinuityReceipt` | Explains inclusion, exclusion, uncertainty and policy version. |
| Working-memory selection and budget disposition | existing `WorkingMemoryGate` | Extended through typed candidate adapters; no second ACM selector. |
| Working-memory decision record | existing `WorkingMemoryPlan` | Continues to own ACTIVE/COMPRESS/DEFER/QUARANTINE/EXCLUDE. |
| Final provider-neutral prompt payload | existing `ContextPack` | Extended if continuity content requires new typed sections. |
| Processing depth | existing `ComputeController` | Not owned by ContextPack, WorkingMemoryGate or CSL. |

## 4. Contract distinctions

### 4.1 `CapsuleClaim` is not `AssertionRecord`

`CapsuleClaim` represents what a Reader extracted from a source. It carries Reader-stage concerns:

- free-form extracted text;
- modality;
- exact source spans;
- extraction confidence;
- optional truth estimate;
- qualifiers, uncertainties and applicability conditions;
- temporal scope expressed by the extraction layer.

`AssertionRecord` represents a normalized immutable assertion record. It carries durable-record concerns:

- typed subject;
- predicate;
- scalar value;
- origin;
- asserting actor;
- valid-time interval and recorded time;
- visibility and sensitivity;
- source references;
- deterministic record identity.

They must not be aliases and must not share one mutable lifecycle.

### 4.2 `KnowledgeCapsule` is not `InteractionEvent`

`InteractionEvent` records that something occurred.

`KnowledgeCapsule` records a rebuildable semantic extraction from a source.

One interaction or document event may produce zero, one, or several capsules. A capsule may later produce zero, one, or several assertion candidates.

### 4.3 `ContinuityContextPack` is not the final `ContextPack`

`ContinuityContextPack` contains continuity evidence and projections relevant to one request:

- episode and thread references;
- prior decision references;
- explicit goal and open-loop references;
- contradiction, freshness and uncertainty markers;
- exclusion reasons and policy version.

The existing `ContextPack` remains the final bounded prompt payload. Continuity data reaches it only after privacy, eligibility, ranking and budget decisions.

## 5. Admission boundary

There is no automatic `CapsuleClaim -> AssertionRecord` conversion.

The required sequence is:

```text
CapsuleClaim
  -> explicit AssertionCandidate mapping
  -> provenance and span verification
  -> origin assignment
  -> subject/predicate/value normalization
  -> epistemic/admission decision
  -> AssertionRecord or rejection/quarantine
```

The mapping must preserve:

- source span identifiers;
- qualifiers and uncertainty, either as typed candidate metadata or separate records;
- temporal conditions;
- Reader and schema versions;
- the distinction between extraction fidelity and external truth support.

A Reader confidence value cannot directly promote an assertion or assign a canonical epistemic state.

## 6. Context integration boundary

A second `AdaptiveContextManager`, selector, or final prompt pack is forbidden.

Milestone 1 will extend the existing Synaptic path with adapters:

```text
ContinuityContextPack
  -> ContinuityWorkingMemoryCandidate adapter
  -> WorkingMemoryGate
  -> WorkingMemoryPlan
  -> ContextPack builder extension
```

The adapter may provide:

- deterministic attention input supplied upstream;
- privacy and recall eligibility;
- conflict/protection flags;
- full and compact representations;
- source and receipt references.

The adapter may not:

- change assertion truth or ESM status;
- perform hidden retrieval;
- rescore after `WorkingMemoryGate`;
- bypass budget accounting;
- write Canon;
- modify the main answer in shadow mode.

## 7. Serialization and identity

Synaptic and Continuity schemas may retain separate schema names because they represent different stages.

They must share compatible primitives:

- NFC Unicode normalization;
- timezone-aware UTC timestamps where time is part of the contract;
- deterministic JSON encoding;
- lowercase SHA-256 identifiers;
- immutable nested values;
- explicit schema versions;
- stable source references.

Cross-stage identity is reference-based, not hash-equality-based. A `CapsuleClaim.claim_id` and an `AssertionRecord.assertion_id` are not expected to match.

## 8. Forbidden duplication

The following additions are prohibited without a superseding ADR:

- `ContinuitySourceSpan` duplicating `SourceSpan`;
- a second document claim extraction type equivalent to `CapsuleClaim`;
- a second knowledge capsule envelope;
- a second ACTIVE/COMPRESS/DEFER selector;
- a second final prompt `ContextPack`;
- a second token or character budget authority operating after `WorkingMemoryGate`;
- direct `CapsuleClaim -> Canon` or `CapsuleClaim -> AssertionRecord` promotion;
- embedding continuity records directly inside neutral Kernel event contracts.

## 9. Required implementation follow-ups

### PR-CONT-05

Implement only:

- `ContinuityContextPack`;
- `ContinuityReceipt`;
- deterministic assembly from existing episodes and thread links;
- no prompt integration and no response authority.

### PR-CTX-01

Extend the existing context path:

- define a typed adapter from continuity items to `WorkingMemoryCandidate`-compatible inputs;
- preserve existing gate dispositions and reason codes;
- extend the existing `ContextPack` with a bounded continuity section or pointers;
- keep flags-off and legacy behavior unchanged.

### Future admission adapter

A separate ADR and PR must define `CapsuleClaim -> AssertionCandidate`. It is not part of PR-CONT-05.

## 10. Research mode

The following remain research-only:

- learned salience replacing deterministic gate inputs;
- LLM-proposed continuity links;
- alternative semantic-pack taxonomies;
- a unified generic claim superclass;
- cross-language shared contract extraction;
- graph-database migration;
- live hardware-aware budgets.

Research prototypes may compare models but cannot introduce production authority or parallel canonical contracts.

## 11. Acceptance criteria

This ADR is accepted when reviewers confirm:

- [ ] `CapsuleClaim` and `AssertionRecord` are documented as different stages;
- [ ] `SourceSpan` remains the only exact document-span contract;
- [ ] `WorkingMemoryGate` remains the sole working-memory disposition owner;
- [ ] existing `ContextPack` remains the sole final prompt payload contract;
- [ ] `ContinuityContextPack` is defined as an input projection, not a competing prompt pack;
- [ ] automatic Reader-to-Canon promotion is explicitly forbidden;
- [ ] PR-CONT-05 and PR-CTX-01 have non-overlapping responsibilities;
- [ ] no current draft PR must be reverted because of this reconciliation.

## 12. Consequences

### Positive

- preserves the already implemented Synaptic path;
- prevents a second ACM and second ContextPack;
- keeps extraction confidence separate from truth admission;
- allows continuity to add value without replacing Reader provenance contracts;
- gives future Native Kernel integration neutral records rather than cognitive payloads.

### Costs

- requires explicit adapters between stages;
- prevents convenient but unsafe direct conversion between claim models;
- may require extending existing ContextPack schemas rather than creating a new one;
- creates an additional review gate before active context integration.

These costs are intentional.