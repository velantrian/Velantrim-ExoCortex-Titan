# ADR — Smart-KB fact-build mutation authority

- Status: Proposed
- Date: 2026-08-12
- Tracking: #292
- Parent: #50

## Context

`scripts/build_kb_graph.py` historically had a performance-oriented `--fast-fresh` path that inserted rows directly into `facts`, then both fast and normal builds performed raw SQL classification and ESM ladder updates. The resulting `data/velantrim_kb.db` is not merely an export: `serve_smart_kb.ps1` can install it as `VELANTRIM_DB_PATH` for ordinary `server:app`.

The causal edge half was already converged by #286/#287 through `CausalGraph`; this ADR concerns fact mutation only.

## Decision

Smart-KB build orchestration owns no canonical fact DML.

1. Curated World Skills ingestion declares `WORLD_FACT / EXTERNAL` before admission.
2. Fact create/update goes through `SQLiteGraphStore.store_facts_batch()` and its existing WriteProtocolGate, VersionStore and same-transaction AuditChain evidence.
3. Batch classification changes are treated as versioned canonical changes, and UNKNOWN input preserves existing durable classification so L0 cannot diverge from L1.
4. Validation uses the existing `promote_to_validated()` ESM ladder, whose transitions are owned by canonical `update_state()` evidence semantics.
5. Historical `--fast-fresh` remains only an empty-database precondition. Empty storage is not an authority bypass.
6. Any incomplete ingest/validation causes the builder to fail, preventing the smart-KB launcher from treating a partially accepted database as a successful build.
7. Causal edges continue to delegate to `CausalGraph`; no second edge owner is introduced.

## Consequences

The build may be slower than the deleted raw bootstrap shortcut, but it preserves a single fact mutation authority and honest evidence semantics. This change does not grant runtime activation or production authority and does not change Continuity or project-state schema.
