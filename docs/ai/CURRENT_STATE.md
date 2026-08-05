# 📍 Current System State

**Verified:** 2026-08-05  
**Current `main`:** `06529700d70854504b88629eeecf737bdc6b81d5`  
**Continuity R2 review surface:** draft recovery branch / PR pending

Verify material claims against exact SHAs, tests, workflows, wiring, configuration and
runtime evidence.

## Status vocabulary

`MAIN`, `TESTED`, `WIRED`, `ENABLED`, `OBSERVED`, `OPEN PR`, `RESEARCH` and
`LEGACY/UNWIRED` are separate states.

## Canon and promotion

PromotionGateway and shared promotion primitives are in `main`, but every canonical
mutation family is not yet proven to use one typed owner. Projection intent creation is
part of validated promotion on migrated databases; World Skills curated ingest remains
an explicit exception.

## Projection delivery

Outbox, version-monotonic FTS apply, checkpoints and bounded dispatch are implemented and
tested. The dispatcher still lacks an accepted runtime lifecycle, cadence, backlog SLO
and reconciliation loop.

## Selective memory — ARM-03

Merged as `bea535d8fd5f7d59d3f1cee02d060bd026ac05cb`.

**Status:** `MAIN + TESTED + DEFAULT OFF / NOT WIRED / NO ADMISSION`.

It remains proposal-only with no persistence, Canon, gate, answer or action authority.

## Continuity — R1

Merged as `06529700d70854504b88629eeecf737bdc6b81d5`.

**Status:** `MAIN + TESTED / CONTRACTS ONLY / NOT WIRED`.

R1 provides immutable deterministic events, assertions and relations, canonical
serialization, golden vectors and authority regression tests. It adds no storage,
runtime or personal-data retention authority.

## Continuity — R2

The R2 recovery branch adds three shadow/read-side mechanisms:

1. `LocalShadowLedger`
   - in-memory, process-local and disposable;
   - append/read/paginated scan/head/integrity verification;
   - idempotency and conflict detection;
   - no delete/truncate/persist/Canon API.
2. `ConversationBridge`
   - consumes only existing notebook read methods;
   - emits immutable `ConversationEpisode` snapshots;
   - never calls notebook mutation methods;
   - preserves persisted timestamps and explicit related-chat refs.
3. `ThreadWeaver`
   - `REFERENCES` only from explicit related-chat refs;
   - `CONTINUES` only from exact normalized goal text;
   - topic/time alone do not create links;
   - missing explicit targets remain unresolved typed projections.

R2 also corrects a legacy read-reconstruction defect: `get_notebook`, `search` and
`list_recent` previously dropped `related_chats` and regenerated `created_at` instead of
preserving persisted source values.

Until merge, R2 is `OPEN PR / SHADOW-READ-SIDE ONLY`. Even after a green merge it is not a
durable ledger, not runtime-wired, not enabled and not observed.

## Remaining Continuity recovery

```text
R3 state reconciliation + qualified goals/open loops + WorkingMemory adapters
→ R4 compute signals + replay evaluation + Advisory shadow
→ R5 disabled complete shadow runner
```

Still required:

- move fixes to the lowest owning layer;
- close `DEFER_PATH` consumer gaps with exhaustive tests;
- prove legacy compatibility differentially;
- design trusted live event/assertion/attestation producers;
- keep all later output shadow-only until separately approved.

## Runtime and deployment

- API and egress policy are fail-closed under documented production settings;
- Docker is non-root and checked;
- `server.py` remains a broad composition module;
- production compose profiles remain inconsistent;
- authentication remains shared API-key rather than per-user/tenant authorization.

## CI and packaging

Main CI runs branding, hygiene, architecture freeze, Ruff, blocking mypy and full pytest.
Focused ARM-03 and Continuity workflows exist. Static-analysis/coverage scope and build
reproducibility remain incomplete across all surfaces.

## Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`; do not activate it.
