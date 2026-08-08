# 📍 Current System State

**Verified:** 2026-08-08  
**Repository `main` head at verification:** `c14916214a920802c9ce6187be79ebe74ddfadfc`  
**Latest implementation-bearing Continuity baseline:** `9f07db6de8d32683d00bfe4f1673e84493607553` (PR #246)  
**Documentation checkpoint SHA:** `c14916214a920802c9ce6187be79ebe74ddfadfc` (PR #248 FINAL of PR #247 checkpoint)  
**Reality boundary:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`

> Exact, dated, historical snapshot. Re-query GitHub before treating any SHA here as the
> current head. `docs/state/project_state.json` records the three SHA roles explicitly.

Material claims must be verified against exact SHAs, tests, workflows, wiring, configuration and runtime evidence.

```text
PROPOSED ≠ IMPLEMENTED
IMPLEMENTED ≠ TESTED
TESTED ≠ WIRED
WIRED ≠ ENABLED
ENABLED ≠ OBSERVED

Integrity ≠ authenticity
Content-addressed policy ≠ operator-approved configuration
Resolver protocol ≠ trusted resolver implementation
Facade result ≠ runtime permission
Continuity ≠ truth, action, reminder or compute authority
```

## Current canonical summary

Titan is a research-grade local-first verifiable-memory runtime moving toward production hardening. Core memory, ESM, provenance, TruthGate, retrieval and controlled write boundaries are real and tested. Higher cognitive layers remain explicitly staged.

Continuity source admission now contains:

- accepted architecture and ownership boundary;
- seven primary immutable evidence contracts;
- State, Goal and OpenLoop deterministic Draft adapters;
- explicit Goal and OpenLoop subject identity;
- pure deterministic admission evaluator;
- immutable content-addressed evaluator/rule registry;
- explicit content-addressed current-decision evidence;
- an internal admission-aware facade with pinned registry, evaluator/rule and resolver identity;
- deterministic anti-substitution, exact-scope and malformed-Draft rejection;
- content-addressed evidence-only facade result.

It still has no concrete trusted current-state resolver composition, durable lifecycle, runtime wiring, enablement or observed operation.

## Continuity readiness

```text
Completed: 7/12 = 58.3%
Remaining: 5/12 = 41.7%
```

This is implementation readiness, not production or live readiness.

### Completed capability categories

1. accepted source-admission architecture and authority placement;
2. seven primary immutable evidence contracts;
3. State reconciliation → bounded Draft adapter;
4. Goal projection → bounded Draft adapter;
5. OpenLoop projection → bounded Draft adapter;
6. deterministic admission evaluator + content-addressed allowlist registry;
7. internal admission-aware facade + typed resolver boundary + anti-substitution guards.

### Remaining capability categories

1. concrete current principal/authorization/consent/restriction/erasure/policy resolver composition through accepted owners;
2. durable retention, replay, cleanup and erasure lifecycle for admission artifacts;
3. runtime wiring with a single lifecycle owner;
4. controlled enablement, SLO, monitoring, rollback and Operator GO;
5. live observed evidence.

## Accepted source-admission lineage

| Capability | Accepted change | State |
|---|---|---|
| Architecture and owner map | PR #223 → `fa7a15726ff14c6fe5c8611b58db7229fa4b6c2b` | docs-only architecture |
| Principal / authorization / binding evidence | PR #225 → `f5725d54b5230f5fbfd6f0550eb08c80ce579237` | tested, internal, unwired |
| Source envelope / Draft | PR #226 → `695f22b7ff7cf6f3af4b4a8d326534a601c09178` | tested, internal, unwired |
| Admission receipt / authorized batch | PR #227 → `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | tested evidence only |
| State Draft adapter | PR #229 → `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | tested, internal, unwired |
| Goal subject identity v2 | PR #230 → `81836b4f715470c50a4c6c7768a2cde7478568c8` | tested contract correction |
| OpenLoop subject identity v2 | PR #232 → `659c30e0e8023c48fdf68be8583401fc042a1ab8` | tested contract correction |
| Goal Draft adapter | PR #236 → `2f9eadd2c16a77835fb58c0d1e481abfc57d8a2d` | tested, internal, unwired |
| OpenLoop Draft adapter | PR #240 → `42aa79338c57e9b9a67c3e3c08dd948b60c5541f` | tested, internal, unwired |
| Pure admission evaluator | PR #244 → `97fe27a37184c6c7277f54e96acd04d98d583ab3` | tested, internal, unwired |
| Internal admission facade | PR #246 → `9f07db6de8d32683d00bfe4f1673e84493607553` | tested, internal, unwired |

## PR #246 exact evidence

```text
Exact tested head:          ec2966ed336ba619e987dfc1e99d45fdf87907b5
Merge SHA:                  9f07db6de8d32683d00bfe4f1673e84493607553
Full Titan CI + coverage:   31219904698 PASS on attempt 2, unchanged SHA
Continuity contracts:       31219904684 PASS · 514 passed
Docker hardening:           31219904770 PASS
Aggregate merge evidence:   31221208768 SUCCESS
Unresolved review threads:  0
```

Attempt 1 of the Full Titan run retained one existing SQLite recovery timeout in `test_drop_legacy_embeddings_lock_owner_process_is_bounded`; coverage passed. The unchanged exact head passed the complete second attempt. The timeout remains risk evidence and is not represented as a facade defect.

Architecture freeze initially rejected the authority-shaped `ContinuityAdmissionFacadePolicy` because no concrete ADR existed. The gate was not bypassed. PR #246 added `docs/adr/ADR-2026-08-07-continuity-admission-facade-boundary.md`, after which the exact head passed the freeze guard.

## PR #247 post-merge docs checkpoint

```text
Merge SHA:                  294bdfa6a77097e48310872a2e3fae811e8c2c9e
Full Titan CI + coverage:   31222680496
  Attempt 1:                FAILED · test_cas_contention_yields_exactly_one_winner_and_one_intent[25]
                            threading.BrokenBarrierError at barrier.wait(timeout=15)
  Attempt 2:                PASS · 3746 passed, 17 skipped, 1 xfailed
Aggregate push evidence:    31222680550 SUCCESS
Unresolved review threads:  0
Documentation impact:       GITHUB_AND_NOTION
Checkpoint document:        docs/ai/PR247_ADMISSION_FACADE_POSTMERGE_CHECKPOINT.md (FINAL)
```

This post-merge failure is an **uncharacterized CAS-contention test failure**
(`BrokenBarrierError`). It is not yet classified as harness-only flake or production CAS
defect. It is not the historical SQLite fresh-bootstrap ADD COLUMN race family and not
the legacy embeddings-lock recovery timeout family tracked from PR #246 run
`31219904698`. Characterization is tracked by issue #249 / draft PR #250.

## Facade guarantees

`core/continuity/admission_facade.py` provides:

- content-addressed `ContinuityAdmissionFacadePolicy`;
- typed `ContinuityCurrentDecisionResolver` protocol;
- internal `evaluate_continuity_admission_facade(...)`;
- content-addressed `ContinuityAdmissionFacadeResult`;
- exact registry, evaluator/rule and resolver identity pinning;
- exact principal, authorization, tenant, binding receipt and complete-subject checks;
- duplicate and cross-envelope Draft rejection before resolver access;
- controlled fail-closed resolver identity and execution failures;
- invocation of only the pure admission evaluator.

The facade does not select or activate itself. Its policy object is represented evidence, not trusted deployment configuration. The resolver protocol is an interface, not a concrete identity, authorization, consent, restriction, erasure or policy owner.

## Trust boundary that remains open

The next accepted composition must:

1. select the expected facade/registry configuration through an explicit operator/deployment owner;
2. obtain principal and authorization evidence from accepted owners;
3. obtain consent or lawful-basis, restriction, erasure-domain and current `PolicySnapshot` evidence from accepted owners;
4. aggregate the complete exact subject set fail-closed;
5. reject missing, stale, unknown, ambiguous or conflicting evidence;
6. call the merged internal facade;
7. stop before signal-producer invocation, persistence or any user-visible effect.

## Explicit limitations

Not implemented or not accepted for live use:

- concrete end-user or tenant authentication integration;
- trusted deployment selection of facade policy and registry identity;
- concrete current-state resolver composition;
- durable persistence, replay, retention, cleanup or erasure lifecycle;
- public package export;
- `/query`, startup, worker or scheduler wiring;
- feature flag, runtime enablement, SLO, monitoring, alert, rollback or Operator GO;
- answer, reminder, notification, delivery, tool, action, Canon, ESM, TruthGate, GoalStack or compute-route authority.

## Global project boundaries

- `main` still lacks an administrator-enforced branch ruleset; issue #234 tracks this;
- aggregate merge evidence exists but is not protected by repository settings;
- normal query-path read-only behavior is not yet proven across every legacy promotion path;
- Canon writer ownership is not unified across every promotion/supersession family;
- projection dispatcher lifecycle and long-horizon operational metrics remain unwired;
- independent security audit and certified privacy/compliance program remain absent;
- SQLite remains the accepted local profile; PostgreSQL, ANN and distributed profiles remain research candidates with explicit return triggers.

## Research boundary

Research intake is governed by `research/IDEA_INTAKE_PROTOCOL.md` and `research/FUTURE_COMPONENTS.md` from PR #243 (`2655ecabab400dda4b350ed90142510cf5a4f49c`). Recording an idea does not accept architecture or grant authority.

Current Continuity resolvers, privacy closure, durable lifecycle, runtime wiring and activation are active engineering, not Research Mode.

## Next safe implementation slice

The next bounded implementation PR may add **concrete current-decision resolver composition through accepted owners only**.

It must remain internal and explicitly invoked, preserve the complete subject set, fail closed on missing or conflicting evidence, and add no producer invocation, persistence, public export, server/startup/worker/scheduler caller, feature flag or user-visible effect.
