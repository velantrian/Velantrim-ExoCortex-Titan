# 📍 Current System State

**Verified:** 2026-08-07  
**Repository `main` head at verification:** `97fe27a37184c6c7277f54e96acd04d98d583ab3`  
**Latest implementation-bearing Continuity baseline:** `97fe27a37184c6c7277f54e96acd04d98d583ab3`  
**Documentation checkpoint branch:** `docs/continuity-admission-evaluator-checkpoint`  
**Reality boundary:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`

Material claims must be verified against exact SHAs, tests, workflows, wiring, configuration and runtime evidence.

```text
PROPOSED ≠ IMPLEMENTED
IMPLEMENTED ≠ TESTED
TESTED ≠ WIRED
WIRED ≠ ENABLED
ENABLED ≠ OBSERVED

Integrity ≠ authorization
Content-addressed registry ≠ trusted runtime root
Current-decision evidence object ≠ trusted external resolver
Admission receipt ≠ runtime permission
Authorized batch ≠ runtime permission
Continuity ≠ truth, action, reminder or compute authority
```

## Current canonical summary

Titan is a research-grade local-first verifiable-memory runtime moving toward production hardening. The core memory, ESM, provenance, TruthGate, retrieval and controlled write boundaries are real and tested. Higher cognitive layers remain explicitly staged.

Continuity source admission now contains:

- accepted architecture and ownership boundary;
- seven primary immutable evidence contracts;
- State, Goal and OpenLoop deterministic Draft adapters;
- explicit Goal and OpenLoop subject identity;
- pure deterministic admission evaluator;
- immutable content-addressed evaluator/rule registry;
- explicit content-addressed current-decision evidence;
- complete deterministic admitted/rejected Draft partition;
- existing immutable admission receipt.

It still has no live-capable facade, trusted current-state resolver integration, durable lifecycle, runtime wiring, enablement or observed operation.

## Continuity readiness

```text
Completed: 6/12 = 50.0%
Remaining: 6/12 = 50.0%
```

### Completed capability categories

1. accepted source-admission architecture and authority placement;
2. seven primary immutable evidence contracts;
3. State reconciliation → bounded Draft adapter;
4. Goal projection → bounded Draft adapter;
5. OpenLoop projection → bounded Draft adapter;
6. deterministic admission evaluator + content-addressed allowlist registry.

### Remaining capability categories

1. accepted current principal/authorization/consent/restriction/erasure/policy resolver boundary;
2. internal admission-aware facade and anti-bypass guards;
3. durable retention, replay, cleanup and erasure lifecycle for admission artifacts;
4. runtime wiring with a single lifecycle owner;
5. controlled enablement, SLO, monitoring, rollback and Operator GO;
6. live observed evidence.

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

## PR #244 exact evidence

```text
Exact tested head:          52fdc9b0ef0ff7833c091a64c35d0754874cedb8
Merge SHA:                  97fe27a37184c6c7277f54e96acd04d98d583ab3
Full Titan CI + coverage:   31215957409 PASS
Continuity contracts:       31215957406 PASS · 502 passed
Docker hardening:           31215957402 PASS
Aggregate merge evidence:   31216560826 SUCCESS
Unresolved review threads:  0
```

The initial evaluator test head produced `503 passed, 1 failed`. The failure was an invalid test chronology: a Draft was created earlier than its SourceEnvelope. The existing payload contract correctly rejected it. The fixture was corrected without weakening production validation, and the final exact head passed every required gate.

## Evaluator guarantees

`core/continuity/admission_evaluator.py` provides:

- content-addressed `ContinuityAdmissionRuleDefinition`;
- content-addressed `ContinuityAdmissionEvaluatorDefinition`;
- immutable `ContinuityAdmissionRegistry`;
- content-addressed `ContinuityCurrentDecisionEvidence`;
- stable fail-closed reason codes;
- pure `evaluate_continuity_admission(...)`;
- evidence-only `ContinuityAdmissionEvaluationResult` with `no_runtime_authority=True`.

The evaluator:

- reads no database, environment, network, mutable global state or implicit clock;
- accepts an explicit `evaluated_at`;
- resolves only exact evaluator/rule ID+version pairs included in the supplied registry;
- validates exact current principal, authorization, tenant, complete subject set, purpose, policy, lawful basis, authorization receipt and erasure-domain evidence;
- rejects stale/mismatched/withdrawn/blocked current evidence fail-closed;
- rejects unsupported source, adapter, derivation rule, signal, purpose, handling mode or retention class;
- rejects low-confidence or stale Drafts;
- produces a complete deterministic admitted/rejected partition;
- creates no runtime permission.

## Trust boundary that remains open

A content-addressed registry proves the identity of its represented contents. It does not prove that the registry is the operator-approved live trust root.

A current-decision evidence object proves the identity of its represented status. It does not prove that the external resolver was authentic or authoritative.

A future facade must therefore:

1. use an operator-selected registry configuration;
2. resolve current identity, authorization, consent/lawful basis, restriction, erasure and policy through accepted owners;
3. preserve the complete exact subject set;
4. reject missing, stale, ambiguous or conflicting state;
5. invoke the pure evaluator;
6. stop before producer invocation or any user-visible effect in its first bounded slice.

## Explicit limitations

Not implemented or not accepted for live use:

- end-user or tenant authentication provider integration;
- trusted registry selection owner;
- trusted current-state resolver aggregation;
- admission-aware facade;
- anti-bypass guards around bare Draft/observation/producer calls;
- durable persistence, replay, retention, cleanup or erasure lifecycle;
- public package export;
- `/query`, startup, worker or scheduler wiring;
- feature flag, runtime enablement, SLO, monitoring, alert, rollback or Operator GO;
- answer, reminder, notification, delivery, tool, action, Canon, ESM, TruthGate, GoalStack or compute-route authority.

## Global project boundaries

- `main` still lacks an administrator-enforced branch ruleset; issue #234 tracks this.
- the aggregate merge-evidence workflow is implemented and observed but is not yet protected by repository settings;
- the normal query path is not yet proven read-only across all legacy promotion paths;
- Canon writer ownership is not yet unified across every promotion/supersession family;
- projection dispatcher lifecycle and long-horizon operational metrics remain unwired;
- independent security audit and certified privacy/compliance program remain absent;
- SQLite remains the accepted local profile; PostgreSQL/ANN/distributed profiles remain research candidates with explicit return triggers.

## Research boundary

Research intake is governed by `research/IDEA_INTAKE_PROTOCOL.md` and `research/FUTURE_COMPONENTS.md` from PR #243 (`2655ecabab400dda4b350ed90142510cf5a4f49c`). Recording an idea does not accept architecture or grant authority.

## Next safe implementation slice

The next bounded implementation PR may add an **internal admission-aware facade and resolver boundary only**.

It must:

- accept complete source envelope, binding, authorization, Draft and registry evidence;
- require exact operator-selected registry identity rather than trusting arbitrary caller registry contents;
- obtain current-decision evidence through explicit typed resolver protocols;
- aggregate multi-subject state fail-closed;
- invoke the pure evaluator;
- optionally construct evidence-only authorized-batch output;
- remain internal and explicitly invoked;
- add no producer invocation, persistence, public export, server/startup/worker/scheduler caller, feature flag or user-visible effect.

Current resolver implementations, durable lifecycle, runtime wiring and activation remain separate later decisions.
