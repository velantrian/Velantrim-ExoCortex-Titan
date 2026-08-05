# 📍 Current System State

**Verified:** 2026-08-05  
**Baseline branch:** `main`  
**Baseline commit:** `024454e5ee17a52f6de321e6917bf29eb5cc88ca`

This is a compact orientation snapshot. It must be re-verified after relevant merges.
It does not replace code, tests, current GitHub checks, or runtime observation.

## Status vocabulary

| Status | Meaning |
|---|---|
| `MAIN` | present in the baseline `main` commit |
| `TESTED` | focused tests exist; this is not a production guarantee |
| `WIRED` | called by a production/runtime path |
| `ENABLED` | enabled by the selected runtime profile |
| `OBSERVED` | verified in a running instance with evidence |
| `OPEN PR` | not part of `main` |
| `RESEARCH` | design/proposal without runtime authority |
| `LEGACY/UNWIRED` | code exists but has no accepted production role |

## Main baseline

### Canon and promotion

- `PromotionGateway` and the shared promotion primitive are in `main`.
- Five standard promotion callers are documented as runtime-wired.
- The gateway is not yet proven to be the sole owner of every mutation family.
- World Skills curated ingest remains an explicit exception.
- Projection intent creation is part of the validated-promotion transaction on migrated
  databases.

**Do not claim:** every canonical mutation in the repository is governed by one typed
mutation envelope.

### Projection outbox and dispatcher

- Projection outbox, version-monotonic FTS apply, checkpoints, and the bounded local
  dispatcher are in `main`.
- Lease/CAS/retry/park/ack and apply-before-ack crash recovery are tested.
- `dispatch_once()` is a plain callable.
- There is no server startup registration, scheduler, background worker, invocation
  cadence, backlog SLO, or reconciliation loop in `main`.

**Status:** `MAIN + TESTED`, but **not `WIRED`, not `ENABLED`, and not `OBSERVED`**.

### Runtime and deployment

- The server is fail-closed for API access unless explicitly configured open.
- Remote egress policy is validated at boot.
- Docker runtime is non-root and has strong image-content checks.
- `server.py` remains a large composition module containing configuration, lifecycle,
  stores, routes, and provider wiring.
- The repository currently presents both `docker-compose.yml` and
  `docker-compose.prod.yml` as production-oriented profiles with materially different
  defaults. This production contract is not reconciled.
- Authentication is a shared API-key model, not per-user accounts, roles, scopes, or
  tenant isolation.

### CI and packaging

- Main CI runs branding, hygiene, architecture-freeze, Ruff, mypy, and pytest.
- Ruff and mypy are focused on `core/`; important runtime surfaces such as `server.py`,
  `api/`, and `utils/` are not all covered by the same static gate.
- Coverage has a configured threshold but the primary CI command does not enforce it.
- CI currently targets Python 3.11 only.
- Dependency ranges are broad and the lockfile is not the authoritative CI/install path.
- The wheel package set and the Docker runtime asset set are not identical products.

## Continuity stack — open PRs

The Continuity work is a stacked draft series rooted at PR #131 and continuing through
PR #147. It is **not part of `main`**.

Architectural intent:

```text
neutral event ledger
→ deterministic thread linking
→ current-state reconciliation
→ typed goal/open-loop projections
→ WorkingMemory adapters
→ continuity-aware compute signals
→ replay evaluation
→ advisory shadow
→ disabled complete shadow runner
```

Current conclusions:

- the stack is deliberately separate from Canon truth and canonical writes;
- model inference is not allowed to silently override a user statement;
- conflicts are represented rather than silently resolved;
- advisory behavior is shadow-only and disabled by default;
- no formal independent review has been recorded for the stack;
- the producer path from a live conversation to trusted `GoalAttestation` or
  `OpenLoopSignal` is not implemented;
- PR #146 is `mergeable: true` but `mergeable_state: unstable` because the
  `Continuity contracts` workflow fails at mypy;
- the concrete failure is an optional-type assignment in
  `core/continuity/advisory_shadow.py`;
- PR #147 contains a behavior-neutral typing fix that should be moved down so PR #146
  is independently green;
- PR #144 changes the public compute contract beyond adding an optional input:
  `DEFER_PATH`, immutable/slotted contracts, tuple reasons, strict validation, policy
  version, rebuild state, and defer reason;
- on the #144 branch, `core/rapid_orientation.py` does not map `DEFER_PATH` in
  `_cost_for_path()`. The path is currently unreachable there because the caller does
  not pass continuity signals, but future wiring would raise `KeyError`.

**Required before merge:** focused review gates, a green #146, exhaustive enum-consumer
tests, differential legacy compatibility tests for #144, and a clean rebase of the
upper stack.

## Identity layer

`core/identity_layer.py` exists in `main`, but it is not an accepted production identity
protocol.

Observed characteristics:

- direct `INSERT OR REPLACE` storage;
- no automatic version increment;
- no AuditChain or VersionStore integration;
- no accepted assertion lifecycle (`CURRENT`, `CONTESTED`, `SUPERSEDED`, `RETRACTED`);
- no user/tenant scope or proven erasure closure;
- no focused tests or established runtime callers found in the audit;
- module comments promise stronger invariants than the implementation proves.

**Status:** `LEGACY/UNWIRED`. Do not activate it or patch it into a parallel governance
system. A separate Identity Assertion/Admission/Reconciliation design is required.
RFC-0084 may govern changes to the identity mechanism, but it is not itself the content
model for identity assertions.

## Evidence needed to refresh this document

Before changing a status, record:

- exact commit or PR head SHA;
- changed files and runtime callers;
- focused tests and static checks;
- whether the component is wired and enabled;
- relevant runtime evidence or an explicit statement that none exists;
- remaining exceptions and failure modes.
