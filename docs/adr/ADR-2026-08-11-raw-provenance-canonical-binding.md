# ADR-2026-08-11: Raw provenance canonical binding convergence

Status: Proposed on tracking issue #288 until protected merge.

## Context

Fresh residual audit of parent Truth Foundation issue #50 on `main@615201ec1073dafb047028e88ce94463f4ef9b77` found one meaningful mutation family that still lacked the established evidence contract.

`SQLiteGraphStore.link_raw_to_fact()` changed canonical `facts.derived_from` and inserted `l0_fact_provenance`, but did not record a VersionStore pre-image or same-transaction AuditChain event. The legacy `RawMemoryStore.link_fact()` additionally owned a second direct `UPDATE facts SET derived_from` path.

The old canonical function could also insert a provenance row before discovering that `facts.derived_from` was already bound to a different raw source. Because it did not inspect the guarded UPDATE rowcount, conflicting provenance could be recorded even though Canon did not accept the new binding.

## Decision

`SQLiteGraphStore.link_raw_to_fact()` remains the single bounded canonical owner for `facts.derived_from` mutation. No second write protocol or store is introduced.

A first binding must:

1. pass the existing WriteGate;
2. verify the immutable raw row and fact exist;
3. accept only a fact whose durable `derived_from` is NULL;
4. treat an already-identical binding as an idempotent no-op;
5. reject an already-different binding without new provenance/evidence;
6. use a guarded facts UPDATE tied to the durable `updated_at` snapshot;
7. record the existing VersionStore pre-image in the same SQLite transaction;
8. insert the `l0_fact_provenance` row in that transaction;
9. append one structured AuditChain `FACT_UPDATED` event on the fact's existing transition chain in that transaction;
10. invalidate process-local L0 only after successful commit.

Any VersionStore, provenance or AuditChain failure rolls the canonical binding back. A CAS loser creates no false evidence and may return idempotent success only if durable read-back proves the same raw binding won.

`RawMemoryStore.link_fact()` becomes a compatibility adapter. It may retain `raw_derivation_chain` as a derived/read-side trace after canonical acceptance, but it no longer owns direct canonical SQL.

## Authority boundary

This ADR does not make raw input authoritative truth. Raw material is provenance/evidence for a fact; `derived_from` records source lineage and does not validate the fact's proposition or advance its ESM state.

No schema v8, new TruthGate, second Canon, scheduler, runtime activation, Operator GO, runtime authority or production authority is introduced. Continuity remains exactly 12/12 and project-state schema remains v7. Issue #249 remains separate.

## Consequences

- provenance binding gains the same atomic evidence guarantees as the other meaningful fact mutation families;
- conflicting second-source binding fails closed;
- legacy raw-memory code can no longer bypass the canonical owner;
- post-merge parent #50 may be closed only after a fresh current-main residual inventory proves no other meaningful mutation gap remains.
