# ADR-2026-08-12: Initial raw provenance parent-transaction convergence

Status: Proposed on tracking issue #290 until protected merge.

## Context

After PR #289 converged post-create raw binding on `SQLiteGraphStore.link_raw_to_fact()`, a fresh parent #50 audit found an initial-create gap. `store_fact()` could insert a non-null `facts.derived_from` before the canonical linker, while `store_facts_batch()` accepted the field from callers but did not persist or link it. The same column also carries historical fact-to-fact lineage such as MeaningParser GIST → VERBATIM, so globally stripping it would destroy a different semantic.

## Decision

The `raw_` namespace is the existing L0 raw-memory identity namespace. When a new fact is created with a `raw_*` `derived_from`, the owning fact-create transaction verifies that the raw row exists and appends the deterministic `l0_fact_provenance` row before commit. The existing FACT_CREATED AuditChain event remains the mutation audit; no artificial VersionStore pre-image or second FACT_UPDATED event is created for a row that had no predecessor.

This is `ACCEPTED_PARENT_TRANSACTION`, not a second post-create mutation owner. `SQLiteGraphStore.link_raw_to_fact()` remains the canonical owner for binding an already-existing unbound fact.

Non-`raw_` values remain fact-to-fact lineage and do not create L0 provenance evidence. Existing facts retain their durable `derived_from` during generic upsert/batch calls; rebinding must use the canonical linker and its #289 CAS contract. `supersede_fact_cas()` follows the same parent-create rule because it directly inserts a replacement fact inside a larger canonical transaction.

## Failure semantics

A missing `raw_*` parent fails closed. Provenance or AuditChain failure rolls the parent creation transaction back. Batch creation keeps raw provenance inside the same all-or-nothing transaction as the fact rows and AuditChain events.

## Non-scope

No schema v8, new store, second TruthGate/write protocol, runtime enablement, Operator GO, remote Canon, scheduler, Phase II, ADAO or ARM-04 is introduced. Continuity remains 12/12 and #249 remains separate.
