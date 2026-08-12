# Smart-KB fact build authority — operator note

Tracking: #292 · parent #50

## Canonical build rule

`build_kb_graph.py` may parse, batch, checkpoint and orchestrate, but it must not execute `INSERT INTO facts` or `UPDATE facts SET` as a fact mutation owner. Curated facts enter through `world_skills_ingest.ingest_facts()` → `SQLiteGraphStore.store_facts_batch()`, then use `promote_to_validated()` for the legal ESM ladder.

`--fast-fresh` means **require an empty KB database**, not **bypass canonical evidence because the DB is empty**.

A successful fact stage requires every chunk to report all rows ingested, all requested rows validated, and zero errors. Otherwise the build exits non-successfully and `serve_smart_kb.ps1` must not proceed to ordinary server startup for that build invocation.

## Verification

Focused tests must prove:

- the builder source contains no raw canonical fact DML;
- fresh build produces `WORLD_FACT / EXTERNAL / Validated` durable state with version and AuditChain evidence;
- an older misclassified fact is corrected through the canonical batch owner with a version bump and coherent L0/L1 state;
- `--fast-fresh` rejects a non-empty database before build mutation;
- forced audit failure cannot produce an accepted `Validated` smart-KB result.

The existing `CausalGraph` owner remains unchanged for relation creation/removal/reset.

## Authority boundary

Continuity remains 12/12; schema remains v7; runtime enabled=false; Operator GO=false; runtime authority=false; production authority=false. No Phase II, ADAO, ARM-04, scheduler/control plane, remote Canon or new generalized TruthGate is introduced.
