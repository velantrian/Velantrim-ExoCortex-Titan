# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-05  
**Current `main`:** `27b91a59f9e9291092b220ac1f53bfeae2daea28`

Code presence does not close a risk. Closure requires focused/full validation, wiring, activation and operational evidence.

## P0

- projection dispatcher is implemented and tested but not runtime-wired or observed;
- production compose contracts remain materially inconsistent;
- static-analysis and coverage scope do not uniformly cover every runtime surface;
- store-wide contention, crash/restart and disk-full evidence remains incomplete;
- build and artifact reproducibility remain incomplete.

## P1 — Continuity Milestone 1

R1–R5B are in `main`, tested and independently reviewed. The complete path exists only as a disabled deterministic in-memory shadow composition.

Residual risks:

- typed records can be wrong or forged without trusted/authenticated producers;
- caller-supplied Gate policy facts have no accepted single owner;
- Advisory intent exact resolution does not authenticate subject or tenant;
- replay equality proves deterministic artifacts, not semantic correctness;
- externally observed safety counters can under-report effects if their producer is incomplete;
- no accepted bounded input/resource policy exists for large episode/assertion sets;
- `ThreadWeaver` remains potentially O(n²) for large batches;
- process-local results and receipts have no durable retention/erasure lifecycle;
- proposed Advisory text has no localization, anti-spam, scheduling or cancellation contract;
- no live feature flag, monitoring, rollback, SLO or operator workflow exists;
- careless future startup/server wiring could convert evaluation into unintended authority.

Required before any live activation:

1. trusted and authenticated producers;
2. tenant/subject authorization and purpose-bound consent;
3. one policy owner for attention, recall, eligibility, privacy, protection and conflict inputs;
4. bounded input/resource policy;
5. durable evidence, retention and erasure design;
6. replay corpus, calibration and adversarial evaluation;
7. explicit runtime owner, feature flag, monitoring and rollback;
8. anti-spam, localization, scheduling and cancellation;
9. separate activation ADR and explicit operator approval.

## P1 — Identity

`core/identity_layer.py` remains a legacy mutable prototype. It lacks the accepted candidate/evidence/approval/version/receipt/rollback lifecycle and must not be activated or extended as a parallel governance path.

## P1 — Other

- ARM-03 remains heuristic and proposal-only;
- Canon mutation ownership is not proven unified across every family;
- `server.py` remains a composition monolith;
- shared API key is not per-user/tenant authorization;
- wheel and container require separate supported-artifact contracts.

## Update rule

Use exact states: proposed, implemented, tested, wired, enabled and observed.
