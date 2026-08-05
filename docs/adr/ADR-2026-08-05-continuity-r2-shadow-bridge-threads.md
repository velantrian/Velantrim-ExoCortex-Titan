# ADR — Continuity R2 Shadow Ledger, Read Bridge and Deterministic Threads

- **Status:** Accepted for PR review
- **Date:** 2026-08-05
- **Scope:** R2 only
- **Base:** `main@06529700d70854504b88629eeecf737bdc6b81d5`
- **Decision owner:** human maintainer / repository architecture policy

## Context

R1 established immutable neutral events, assertions and relations. R2 needs enough
read-side structure to test continuity without creating a second durable memory, changing
legacy conversation behavior or inferring semantic relations with an LLM.

Historical PRs #133, #135 and #136 contained this material as a stacked chain. R2
rebuilds it on current `main` as one independently green shadow layer.

## Decision

R2 contains exactly three mechanisms:

```text
1. LocalShadowLedger
   process-local append-only adapter for immutable InteractionEvent values

2. ConversationBridge
   read-only projection of existing ConversationNotebook rows into immutable episodes

3. ThreadWeaver
   conservative rebuildable links and connected components over episodes
```

## Authority boundaries

### LocalShadowLedger

- records neutral events only;
- is process-local, in-memory and disposable;
- provides append, read, bounded page scan, head and integrity verification;
- provides idempotency and conflict detection;
- has no delete, truncate, flush, subscribe, Canon promotion or durable-storage API;
- is a transition adapter, not a production event store or Native Kernel implementation.

### ConversationBridge

- consumes only `get_notebook`, `search` and `list_recent`;
- never calls `add_insight` or `finalize`;
- projects mutable legacy rows into frozen deterministic `ConversationEpisode` values;
- preserves source timestamps and explicit related-chat references;
- assigns no truth, confirmation, salience, retention or action status.

### ThreadWeaver

Version 1 emits only:

- `REFERENCES` from an explicit `related_chat_refs` source field;
- `CONTINUES` from an exact normalized notebook goal match.

Topic equality is supplemental evidence only and never creates a link by itself.
Recency/time proximity never creates a link. Reserved relation types are not inferred
without future typed evidence.

## Legacy read-fidelity correction

The existing notebook read methods reconstructed rows without the persisted
`created_at` and `related_chats` fields, silently replacing or dropping source evidence.
R2 corrects `get_notebook`, `search` and `list_recent` so read projections preserve those
stored values.

This changes read reconstruction only. It does not change notebook writes, table schema,
finalization semantics or Canon.

## R2 non-scope

R2 adds no:

- durable ledger database or migration;
- event ingestion from `/query`;
- background worker or scheduler;
- semantic/embedding/LLM thread linking;
- assertion extraction from raw conversation text;
- current-state, goal or open-loop projection;
- WorkingMemory or ContextPack adapter;
- compute signal, advice or action;
- Canon, ESM, TruthGate, WriteGate or promotion call;
- feature activation or user-visible behavior.

## Determinism and failure rules

1. Equal logical inputs produce equal IDs and canonical bytes.
2. Duplicate identical snapshots are idempotent/deduplicated.
3. Conflicting duplicate snapshots fail closed.
4. Missing explicit thread targets remain typed unresolved references.
5. Self-references fail closed.
6. Input ordering does not change link/thread/reference identities.
7. Integrity verification recomputes event hashes.
8. The legacy source remains authoritative for notebook storage; episodes and threads are
   rebuildable projections.

## Privacy boundary

R2 does not authorize new data collection or retention. A future durable event adapter
must separately define purpose, consent/scope, retention, erasure, access control,
encryption, audit and multi-tenant isolation.

Conversation-derived text remains source projection and must not be treated as confirmed
fact merely because it appears in a notebook or thread.

## Alternatives rejected

### New continuity SQLite store

Rejected in R2. It would create storage and migration authority before the neutral port
and privacy lifecycle are proven.

### Automatic semantic linking

Rejected. Embedding similarity, topic proximity or LLM judgment can create false merges
and cannot become continuity evidence without typed validation.

### Modify ConversationConsolidator writes

Rejected. R2 adapts the existing read surface and corrects read reconstruction only.

### Merge old #133/#135/#136 directly

Rejected. The current-main recovery keeps the layer independently reviewable and lets CI
validate compatibility with the merged R1 foundation.

## Consequences

Positive:

- a real end-to-end read-only continuity substrate can be tested;
- unresolved references and false-link avoidance are explicit;
- legacy source fidelity improves;
- no migration or runtime rollback burden.

Costs and limitations:

- the ledger is not durable and is lost on process exit;
- no trusted event producer is wired;
- notebook text remains non-epistemic source material;
- exact-goal matching can miss genuine continuations and must not be marketed as semantic
  understanding;
- large-batch operational bounds need a future runtime caller contract before wiring.

## Rollback

Remove the R2 modules/exports/tests and revert the read-reconstruction fields. No data
migration is required because R2 adds no persistent schema or writes.
