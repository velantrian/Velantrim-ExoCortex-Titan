# ADR — PromotionGateway foundation

**Status:** accepted for foundation only  
**Date:** 2026-08-02  
**Issue:** #165

## Context

Titan currently has a hardened `SQLiteGraphStore.validate_and_promote()` path that
combines a durable snapshot, TruthGate evaluation and a CAS-guarded transition to
`Validated`.  Several callers invoke that path directly, while other internal paths
still use separate pre-vetting and ESM helpers.  The result is good local safety but
fragmented ownership: there is no single typed request/receipt contract that every
future promotion caller can share.

A large replacement of all promotion paths in one change would be unsafe.  It would
mix API behavior, consolidation accounting, pipeline ingestion, truth maintenance,
legacy tool handlers and cognitive stores without enough characterization evidence.

## Decision

Introduce `core.promotion_gateway` as a narrow adapter over the existing authority.

The first increment:

- accepts only an explicit `PromotionRequest` targeting `Validated`;
- delegates exactly once to the store's existing `validate_and_promote()` method;
- owns no confidence, evidence or contradiction thresholds;
- performs no raw ESM transition and exposes no `transition_esm` shortcut;
- validates the returned `TruthGateVerdict` contract fail-closed;
- distinguishes committed, idempotent and rejected outcomes;
- produces deterministic, content-minimized receipts using a hashed fact reference;
- propagates store failures instead of fabricating success evidence;
- remains unwired to runtime callers in this PR.

`SQLiteGraphStore.validate_and_promote()` remains the mutation authority until caller
migration is completed and proven individually.  Merely merging the gateway class does
not make it the sole runtime owner.

## Receipt boundary

A `PromotionReceipt` may contain:

- deterministic request ID;
- hashed fact reference;
- safe actor code;
- requested target and cognitive mode;
- policy version;
- passed/committed/idempotent booleans;
- machine-readable reason code.

It must not contain claim text, justification text, evidence payloads, source content,
user text, SQL, filesystem paths or exception messages.

The internal `PromotionOutcome` may retain the technical `fact_id` for the immediate
caller.  The replayable receipt does not.

## Ordered migration

Caller migration is incremental and must not be combined with outbox persistence:

1. graduated promotion;
2. `ConsolidationEngine`;
3. direct API transition;
4. tool handlers and pipeline/internal promotion paths;
5. truth maintenance, CognitiveStore and world-skills paths after separate
   characterization.

Each migration requires focused behavior tests and final repository CI.  A caller is
not considered migrated until its direct promotion invocation is absent and the gateway
path is exercised by tests.

## Consequences

### Positive

- one stable request/outcome vocabulary for future callers;
- deterministic evidence suitable for a later transactional outbox;
- no duplicated TruthGate policy;
- no semantic change to existing runtime in the foundation PR;
- malformed or future-ambiguous passed verdicts fail closed.

### Costs

- two layers temporarily coexist;
- the gateway is not yet runtime-authoritative;
- each caller needs a separate migration and accounting review;
- transactional persistence remains future work.

## Rejected alternatives

### Replace `validate_and_promote()` inside `memory.py` immediately

Rejected because the existing path already contains mature CAS, audit and cache
semantics.  Moving it before characterization would create unnecessary regression risk.

### Route every ESM transition through the gateway

Rejected.  The gateway governs promotion to `Validated`, not contradiction,
deprecation, collapse, invalidation or ordinary legal ladder movement.

### Add automatic retries

Rejected.  `concurrent_modification` is evidence that the evaluated snapshot is stale.
A transparent retry could evaluate different data under the same caller action and hide
contention.  Retry policy belongs to an explicit caller or operator decision.

### Persist receipts in this increment

Rejected.  Persistence must be introduced with a same-transaction outbox contract and
crash/restart tests, not a best-effort side write.

## Non-claims

This decision does not prove that all current promotion paths are unified.  It does not
activate Continuity, change TruthGate thresholds, make SQLite generally concurrent, or
make Titan production-ready.
