# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-05  
**Current `main` before PR #201:** `bea535d8fd5f7d59d3f1cee02d060bd026ac05cb`

Code or documentation alone does not close a risk. Closure requires the stated tests,
runtime evidence and governance decision.

## P0

### Projection delivery is not runtime-wired

Outbox, checkpoints and bounded dispatch exist, but there is no accepted lifecycle owner,
cadence, backlog/age SLO or reconciliation loop.

### Production deployment contract is ambiguous

`docker-compose.yml` and `docker-compose.prod.yml` express materially different
production-oriented defaults. Select one canonical contract and test it end to end.

### Verification scope is narrower than broad repository claims

Coverage, Ruff, mypy and pytest do not form one uniform gate over every runtime surface.
Expand in staged truthful baselines.

### Storage concurrency is not systemically proven

Selected CAS and recovery races are tested; store-wide WAL/contention, crash/restart,
disk-full and migration stress are not.

### Supply chain and builds are not fully reproducible

Broad dependency ranges, mutable references and wheel/container differences can produce
different artifacts from identical source.

## P1

### Continuity recovery is incomplete beyond R1

PR #201 establishes contracts only. Remaining layers:

1. R2 local shadow ledger, read-only conversation bridge and deterministic ThreadWeaver;
2. R3 state reconciliation, qualified goals/open loops and WorkingMemory adapters;
3. R4 compute signals, replay evaluation and Advisory shadow;
4. R5 disabled complete shadow runner;
5. later trusted dialogue → candidate → attestation producer and shadow evaluation.

Constraints:

- no direct merge of old #131–#147;
- every recovery PR independently green on current `main`;
- fixes move to the lowest owning layer;
- `DEFER_PATH` consumers require exhaustive coverage;
- legacy behavior requires differential tests;
- no user-facing continuity or Canon writes without separate promotion gates.

R1-specific residual risks:

- schema v1 is now an interoperability commitment;
- future field changes require versioning and new golden vectors;
- contract existence does not define privacy purpose, retention or erasure;
- neutral events and assertion candidates still need trusted producers;
- no durable ledger or replay store exists yet.

### Selective-memory extraction remains heuristic and proposal-only

ARM-03 is merged and tested, but classification/injection detection are bounded
heuristics; subject/context identity is caller-supplied; safe serialization does not
authorize raw evidence retention; precision/privacy evaluation is required before
ARM-04.

### Identity layer is a legacy mutable prototype

`core/identity_layer.py` lacks accepted assertion lifecycle, consent/scope,
contestation, audit/version and erasure closure.

### Canon mutation ownership remains fragmented

Standard promotion ownership improved, but every mutation family is not proven to use
one typed command/receipt/transaction boundary.

### `server.py` remains a composition monolith

Initialization, lifecycle, routes and providers have broad blast radius.

### Authentication is not multi-user authorization

A shared API key does not provide accounts, roles, scopes, tenants or sensitive
multi-user policy.

### Wheel and container are distinct packaging surfaces

Define supported artifacts and independent smoke tests.

## P2

- evaluate large generated knowledge assets for reproducible build/Release/LFS;
- mark historical audits as superseded or index them by verified SHA;
- verify CODEOWNERS, branch protection, automation, labels and templates;
- improve repository discovery metadata with verified capability language.

## Update rule

Use exact status words: proposed, implemented, tested, wired, enabled and observed.
