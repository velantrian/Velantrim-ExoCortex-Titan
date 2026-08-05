# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-05  
**Current verified implementation head:** `c7ad5a171ccc6da5015b67b8cefd6d60649d6792`

Code presence and test coverage do not close a risk. Closure requires focused/full validation, correct wiring, activation controls and operational evidence.

## Closed or materially reduced in this cycle

- CI now executes a blocking full-core coverage ratchet at `74%`, based on a measured approximately `74.12%` baseline;
- production database bundles now have a versioned manifest, path/size/SHA-256 verifier and external archive checksum;
- emergency `prevent_fact_delete` reconstruction paths now have committed regression evidence;
- obsolete cleanup PRs were closed only after useful deltas were recovered or proven superseded;
- unsafe generated KB PR #10 was closed without merge.

## P0

- projection dispatcher is implemented and tested but not runtime-wired or operationally observed;
- production compose contracts remain materially inconsistent;
- store-wide contention, crash/restart and disk-full evidence remains incomplete on some storage paths;
- build and artifact reproducibility is improved but not complete across every supported artifact;
- shared API-key authentication is not per-user/tenant authorization.

## P1 — Coverage and CI

The `74%` floor is now real and blocking, but it is only a regression ratchet:

- high aggregate coverage can hide low-coverage critical modules;
- coverage does not prove semantic correctness, security or realistic production behavior;
- one trace-hook concurrency stress test cannot run simultaneously with `coverage.py`, but remains blocking in the normal full-pytest job;
- optional dependency installation is heavy and may consume excessive CI time/bandwidth;
- the floor should rise only with executable tests and must not be lowered silently.

## P1 — Continuity Milestone 1

R1–R5B are in `main`, tested and independently reviewed. The complete path exists only as a disabled deterministic in-memory shadow composition.

Residual risks:

- typed records can be wrong or forged without trusted/authenticated producers;
- caller-supplied Gate policy facts have no accepted single owner;
- Advisory intent exact resolution does not authenticate subject or tenant;
- replay equality proves deterministic artifacts, not semantic correctness;
- externally supplied safety counters can under-report effects;
- no accepted bounded input/resource policy exists for large batches;
- `ThreadWeaver` remains potentially O(n²);
- process-local results and receipts have no durable retention/erasure lifecycle;
- no live feature flag, monitoring, rollback, SLO or operator workflow exists;
- careless future wiring could convert evaluation into unintended authority.

## P1 — Identity

`core/identity_layer.py` is formally quarantined as `LEGACY/UNWIRED`. It lacks the accepted candidate/evidence/approval/version/receipt/rollback lifecycle. Do not add production callers, persistence authority or a parallel identity-admission path.

## P1 — Adaptive updates and projections

- RFC-0084 remains `Proposed`, has no implementation module or runtime wiring, forbids Canon writes and requires operator approval;
- projection dispatcher startup/runtime wiring remains deliberately absent;
- outbox growth, retry/dead-letter operations and long-horizon operational metrics require explicit ownership before activation.

## P1 — Open architecture drafts

Exactly four PRs remain open: #17, #30, #33 and #43. Their risk is not abandonment but ambiguous adoption:

- stale branches must not be merged wholesale;
- terminology, ownership and placement require human decisions;
- #33 must reconcile with newer Project Cognition and Continuity documents;
- #43 must reconcile with RFC-0084, current Canon ownership, tenant/erasure closure and architecture-freeze rules.

## P1 — Other

- ARM-03 remains heuristic, proposal-only, default-off and unwired;
- Canon mutation ownership is not proven unified across every family;
- `server.py` remains a composition monolith;
- wheel and container require separately supported artifact contracts;
- the new release-bundle verifier validates local artifacts but does not publish or authorize a GitHub Release.

## Update rule

Use exact states: `PROPOSED`, `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED`.
