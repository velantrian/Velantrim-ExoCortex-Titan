# 📍 Current System State

**Verified:** 2026-08-05  
**Current `main` before PR #201:** `bea535d8fd5f7d59d3f1cee02d060bd026ac05cb`  
**Continuity R1 review surface:** PR #201

This is an orientation snapshot. Verify material claims against the exact commit or PR
head, tests, workflows, configuration and runtime evidence.

## Status vocabulary

| Status | Meaning |
|---|---|
| `MAIN` | present in current `main` |
| `TESTED` | relevant tests passed at a recorded SHA |
| `WIRED` | called by an accepted runtime path |
| `ENABLED` | active in the selected configuration |
| `OBSERVED` | verified in a running instance |
| `OPEN PR` | proposed tree outside `main` |
| `RESEARCH` | design/prototype without runtime authority |
| `LEGACY/UNWIRED` | code exists without an accepted production role |

## Canon and promotion

- `PromotionGateway` and shared promotion primitives are in `main`.
- Standard promotion callers are wired, but the gateway is not proven to own every
  canonical mutation family.
- Projection intents are part of validated promotion on migrated databases.
- World Skills curated ingest remains an explicit exception.

## Projection delivery

Projection outbox, version-monotonic FTS apply, checkpoints and bounded dispatch are
implemented and tested. `dispatch_once()` still lacks an accepted runtime lifecycle,
cadence, backlog SLO and reconciliation loop.

**Status:** `MAIN + TESTED`, not a `WIRED/ENABLED/OBSERVED` worker.

## Selective memory — ARM-03

ARM-03 was merged through PR #200 as
`bea535d8fd5f7d59d3f1cee02d060bd026ac05cb`.

**Status:** `MAIN + TESTED + DEFAULT OFF`, but not runtime-wired or observed.

It provides bounded proposal-only extraction with source hashes, typed retention reason,
subject/context identity, privacy-safe portable serialization, bounded memory-injection
rejection, focused CI, benchmark and replay.

It has no persistence, Canon, ESM, TruthGate, WriteGate, WorkingMemory, answer or action
authority. ARM-04 remains a separate blocked admission decision.

## Continuity — R1 foundation

PR #201 rebuilds the first continuity layer on current `main`.

R1 contains only:

- `ActorRef` and `SubjectRef`;
- immutable `InteractionEvent`;
- immutable `AssertionRecord`;
- immutable `AssertionRelation`;
- explicit event, origin, relation, visibility and sensitivity enums;
- Unicode NFC and UTC canonicalization;
- deterministic canonical JSON and SHA-256 identities;
- golden vectors and focused conformance tests;
- an architecture ADR and path-scoped workflow.

R1 explicitly contains no:

- database, migration or event ledger;
- conversation bridge or thread linking;
- current-state, goal or open-loop projection;
- WorkingMemory or ContextPack adapter;
- compute or advisory path;
- `/query`, worker, response or action wiring;
- feature activation or personal-data collection authority.

Until PR #201 merges, R1 status is `OPEN PR / CONTRACTS ONLY`. After a green merge it may
be described as `MAIN + TESTED / NOT WIRED / NOT ENABLED / NOT OBSERVED`.

The historical PRs #131–#147 are source material, not a merge chain. Recovery order:

```text
R1 immutable contracts
→ R2 ledger + conversation bridge + deterministic threads
→ R3 state + goals/open loops + WorkingMemory adapters
→ R4 compute signals + replay + advisory shadow
→ R5 disabled complete shadow runner
```

Known later constraints remain:

- the Advisory typing fix belongs in its owning layer, not a child PR;
- `DEFER_PATH` needs exhaustive downstream coverage, including Rapid Orientation;
- compatibility must be proven with differential tests;
- a trusted dialogue → candidate → attestation producer is still absent;
- all later output remains shadow-only until separate review and evaluation.

## Runtime and deployment

- API and remote-egress policy are fail-closed under documented production settings.
- Docker runs non-root and has image/runtime hardening checks.
- `server.py` remains a broad composition module.
- production-oriented compose profiles remain materially inconsistent.
- authentication remains shared API-key, not per-user or tenant authorization.

## CI and packaging

- main CI runs branding, repository hygiene, architecture freeze, Ruff, blocking mypy and
  full pytest;
- ARM-03 has a focused benchmark/replay workflow;
- R1 adds a focused continuity contract workflow;
- static-analysis and coverage scope are still not uniform across all runtime surfaces;
- build reproducibility and wheel/container parity remain incomplete.

## Identity layer

`core/identity_layer.py` remains `LEGACY/UNWIRED` and must not be activated. A separate
Identity Assertion/Admission/Reconciliation protocol is required.

## Evidence required for status changes

Record exact SHA, changed files and consumers, focused/full validation, wiring,
enablement, observation state, privacy boundaries and remaining failure modes.
