# 📍 Current System State

**Verified:** 2026-08-05  
**Reference main before PR #200:** `649d12953eb141aa783729555861e788cc03c150`  
**ARM-03 review surface:** PR #200

This is a compact orientation snapshot. Verify material claims against the exact checkout,
current PR head, tests, workflows, configuration and runtime evidence.

## Status vocabulary

| Status | Meaning |
|---|---|
| `MAIN` | present in the checked-out `main` tree |
| `TESTED` | focused or full tests passed at a recorded SHA |
| `WIRED` | called by an accepted runtime path |
| `ENABLED` | activated by the selected profile/configuration |
| `OBSERVED` | verified in a running instance with evidence |
| `OPEN PR` | proposed tree outside `main` |
| `RESEARCH` | design/proposal without runtime authority |
| `LEGACY/UNWIRED` | code exists without an accepted production role |

## Canon and promotion

- `PromotionGateway` and the shared promotion primitive are in `main`.
- Standard promotion callers are runtime-wired, but the gateway is not yet proven to be
  the sole owner of every mutation family.
- Projection intent creation is part of validated promotion on migrated databases.
- World Skills curated ingest remains an explicit exception.

**Do not claim:** every canonical mutation uses one typed envelope.

## Projection delivery

- Projection outbox, version-monotonic FTS application, checkpoints and bounded local
  dispatch are implemented and tested.
- `dispatch_once()` remains a plain callable without an accepted production scheduler,
  lifecycle owner, cadence, backlog SLO or reconciliation loop.

**Status:** `MAIN + TESTED`, but not `WIRED`, `ENABLED` or `OBSERVED` as a worker.

## Selective memory — ARM-03

The tree proposed by PR #200 contains a bounded, dependency-free selective-memory
candidate extractor.

Implemented contract:

- default-off flag `ENABLE_SELECTIVE_MEMORY_CANDIDATE_SHADOW`;
- exact source offsets and SHA-256 span hashes;
- typed candidate, temporal scope and `RetentionReason`;
- `extraction_confidence`, explicitly distinct from truth confidence;
- optional `subject_ref` and `context_id` bound into candidate identity;
- contact/credential redaction and explicit safe portable serialization;
- bounded English/Russian prompt-to-memory injection detection with default rejection;
- deterministic within-input `POSSIBLE_UPDATE_OF` hints;
- focused workflow, tests, benchmark and replay fixture.

Authority boundary:

- no `/query` wiring;
- no database or persistence access;
- no Canon, ESM, TruthGate, WriteGate or WorkingMemory authority;
- no model, embedding, graph or network dependency;
- no response, reminder, tool or action authority;
- no ARM-04 admission path.

When this tree is present in `main`, its status is `MAIN + TESTED + DEFAULT OFF`, but it
remains **not `WIRED`, not `ENABLED` by default and not `OBSERVED`**. A candidate is a
proposal, not admitted memory or truth.

## Runtime and deployment

- API access and remote-egress policy are fail-closed under the documented production
  settings.
- Docker runs non-root and has image/runtime hardening checks.
- `server.py` remains a broad composition module.
- `docker-compose.yml` and `docker-compose.prod.yml` still express materially different
  production-oriented postures.
- Authentication remains a shared API-key model, not per-user authorization or tenant
  isolation.

## CI and packaging

- Main CI runs branding, repository hygiene, architecture freeze, Ruff, blocking mypy
  and full pytest.
- Important runtime surfaces are not all covered by one static-analysis gate.
- The configured coverage target is not the same thing as a universally enforced full
  repository threshold.
- Dependency/build reproducibility and wheel/container parity remain incomplete.
- ARM-03 adds a path-scoped blocking workflow for its contracts, benchmark and replay.

## Continuity stack

PRs #131–#147 remain a historical stacked draft series outside `main`. Do not merge the
old chain directly.

Required recovery approach:

```text
current main
→ contracts and conformance
→ ledger / conversation bridge / deterministic threads
→ context / state / goals / open loops / working-memory adapters
→ compute signals / replay / advisory
→ disabled complete shadow runner
```

Known constraints:

- PR #147 contains a typing fix owned by the #146 layer;
- `DEFER_PATH` needs exhaustive downstream-consumer coverage, including Rapid
  Orientation cost mapping;
- legacy compatibility requires differential tests;
- a trusted live dialogue → candidate → attestation producer is absent;
- all stages remain shadow-only until separately reviewed and validated.

## Identity layer

`core/identity_layer.py` remains `LEGACY/UNWIRED`:

- direct mutable storage;
- no accepted assertion/admission/reconciliation lifecycle;
- no proven audit/version/consent/scope/erasure closure;
- no accepted production owner.

Do not activate it. A separate Identity Assertion/Admission/Reconciliation protocol is
required.

## Evidence required for status changes

Record:

- exact commit or PR head;
- changed files and callers;
- focused and full validation;
- wiring, enablement and observation state;
- privacy/safety boundaries;
- remaining exceptions and failure modes.
