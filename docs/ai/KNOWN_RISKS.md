# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-05  
**Current `main`:** `58e29bba26299ce7003b62e73fd3b25e028956de`

## P0

- projection dispatcher remains implemented/tested but unwired and unobserved;
- production compose contracts remain inconsistent;
- static-analysis/coverage scope is not uniform across every runtime surface;
- store-wide contention/crash/restart/disk-full evidence remains incomplete;
- build and artifact reproducibility remain incomplete.

## P1 — Continuity R1–R5A

All accepted layers are in main and tested but remain unwired. They do not provide trusted producers, durable lifecycle, consent, tenant authorization, calibration, monitoring or live user behavior.

## P1 — R5B complete shadow composition

Draft PR #206 composes the full path in memory. Residual risks:

- `enabled=True` could be mistaken for production activation despite being local-call permission only;
- every typed record can be wrong or forged if upstream producer trust is weak;
- caller-supplied Gate policy facts have no accepted single owner;
- Advisory intent exact resolution prevents inference but does not authenticate the target subject;
- replay equality proves deterministic artifacts, not semantic correctness;
- explicit safety counters can under-report external effects if their producer is incomplete;
- process-local results and receipts have no durable retention/erasure lifecycle;
- no bounded input-count/resource policy is accepted for large episode/assertion sets;
- ThreadWeaver remains potentially O(n²) on large batches;
- proposed Advisory text has no localization, anti-spam, scheduling or cancellation contract;
- no runtime feature flag, rollback, SLO, monitoring or operator workflow exists;
- adding a future server/startup caller could accidentally convert evaluation into authority.

Required before any live use:

1. trusted and authenticated producers;
2. tenant/subject authorization and purpose-bound consent;
3. bounded input/resource policy;
4. durable evidence, retention and erasure design;
5. replay corpus, calibration and adversarial evaluation;
6. explicit runtime owner, feature flag, monitoring and rollback;
7. delivery anti-spam/localization/scheduling/cancellation;
8. separate activation ADR and operator approval.

## P1 — other

- ARM-03 remains heuristic proposal-only;
- identity remains a legacy mutable prototype without accepted lifecycle;
- Canon mutation ownership is not proven unified across every family;
- `server.py` remains a composition monolith;
- shared API key is not per-user/tenant authorization.

## Update rule

Use exact states: proposed, implemented, tested, wired, enabled and observed.
