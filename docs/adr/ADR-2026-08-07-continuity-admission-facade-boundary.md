# ADR-2026-08-07 — Internal Continuity admission-aware facade boundary

- **Status:** proposed — accepted only if PR #246 is reviewed and merged
- **Date:** 2026-08-07
- **Owner:** human maintainer/operator
- **Related architecture:** `docs/research/CONTINUITY_SOURCE_ADMISSION_ARCHITECTURE.md`
- **Related implementation:** PR #246

## Context

The accepted Continuity source-admission stack contains immutable principal,
authorization, source-binding, envelope, Draft, admission-receipt and authorized-batch
contracts; deterministic State/Goal/OpenLoop Draft adapters; and a pure deterministic
admission evaluator with content-addressed evaluator/rule definitions.

The evaluator intentionally accepts represented current-decision evidence. It does not:

- select which registry is trusted by a deployment;
- select which current-state resolver is trusted;
- obtain current principal, authorization, consent/lawful-basis, restriction, erasure or
  policy state;
- prevent a future caller from substituting a different internally valid registry;
- establish a controlled composition boundary before evaluation.

Direct runtime wiring of the evaluator would therefore create a false trust boundary.
The system needs one internal facade that pins represented registry and resolver
identities, verifies cross-contract scope, obtains current evidence through a typed
protocol and invokes only the existing pure evaluator.

The word `Policy` in `ContinuityAdmissionFacadePolicy` describes immutable configuration
evidence for this one facade. It is not a second `PolicyKernel`, a live authorization
owner or an activation mechanism.

## Decision

Introduce an **internal, explicitly invoked, evidence-only admission-aware facade** with
these surfaces:

1. `ContinuityAdmissionFacadePolicy`
   - content-addressed;
   - pins expected registry ID;
   - pins evaluator ID/version and rule ID/version;
   - pins current-decision resolver ID/version;
   - always carries `no_runtime_authority=True`.
2. `ContinuityCurrentDecisionResolver`
   - typed protocol only;
   - concrete implementations remain owned by accepted identity, authorization,
     consent, restriction, erasure and current-policy components;
   - does not make Continuity the owner of those decisions.
3. `evaluate_continuity_admission_facade(...)`
   - verifies registry and resolver identity;
   - verifies principal, authorization, tenant, source binding and complete subject
     scope;
   - rejects malformed Draft sets before calling an external resolver;
   - converts resolver identity or execution failures to controlled fail-closed errors;
   - invokes only `evaluate_continuity_admission(...)`;
   - returns content-addressed evidence and stops.
4. `ContinuityAdmissionFacadeResult`
   - binds facade policy, registry, resolver identity, current-decision evidence,
     evaluation receipt and explicit evaluation time;
   - remains evidence-only and non-authoritative.

The facade remains internal and is not exported from `core.continuity.__init__`.

## Why an existing owner is reused rather than replaced

- `PolicyKernel` remains the owner of hard capability, locality and data-mode policy.
- Existing principal/authorization/privacy components remain the future owners of
  current-decision evidence.
- The pure admission evaluator remains the only owner of deterministic Draft admission
  rules.
- Existing source adapters remain the only owners of source-result-to-Draft
  transformation.
- Existing signal producer remains a separate pure shadow component.

The facade owns only safe composition and anti-substitution checks. It does not duplicate
truth, identity, policy, erasure, action or compute authority.

## Authority boundary

- **Canon/ESM writes:** none.
- **TruthGate or PolicyKernel mutation:** none.
- **Background execution:** none.
- **Network/provider access:** none.
- **Persistence:** none.
- **Signal-producer invocation:** none.
- **Authorized-batch live consumption:** none.
- **External actions:** none.
- **User-visible influence:** none.
- **Reminder/notification/delivery authority:** none.
- **Tool/action authority:** none.
- **Compute-route authority:** none.
- **Runtime registration or activation:** none.

```text
facade policy object ≠ operator-approved deployment configuration
resolver protocol ≠ trusted concrete resolver implementation
facade result ≠ runtime permission
```

## Data, scope and privacy

The facade accepts only typed immutable evidence and requires:

- authorization principal ID to match the supplied principal context;
- source envelope to reference the supplied binding receipt and authorization context;
- tenant scope to match across envelope, binding and authorization;
- envelope subjects to equal binding subjects;
- source subjects to remain inside authorization scope;
- current-decision evidence to cover the exact principal, authorization, tenant and
  complete authorization subject set;
- every Draft to reference the supplied source envelope;
- duplicate Draft IDs to be rejected.

For multi-subject authorization, the resolver must represent the complete exact subject
set. A missing, blocked, erased or unknown subject may not be silently filtered.

The facade creates no durable retention obligation because it persists nothing. Any
future persistence or replay path requires a separate ADR covering retention,
subject/tenant indexing, erasure, cleanup and crash recovery.

## Failure semantics

The facade is fail-closed.

It raises controlled `ContinuitySourceAdmissionError` for:

- unexpected registry identity;
- unresolvable evaluator/rule identity;
- resolver identity mismatch or identity-access failure;
- principal/authorization/source/binding/tenant/subject mismatch;
- empty, malformed, duplicate or cross-envelope Draft sets;
- resolver exception;
- invalid resolver output;
- incomplete current-evidence coverage;
- any rejection or validation failure returned by the pure evaluator.

Malformed local evidence is rejected before the facade calls the external resolver.
Resolver exceptions never become empty success, permissive evidence or a partial result.

## Observability and receipts

The facade result is content-addressed evidence binding:

- facade policy ID;
- registry ID;
- resolver ID/version;
- current-decision evidence ID;
- evaluator receipt ID;
- explicit evaluation timestamp.

This result is not persisted by PR #246 and therefore is not operational telemetry or a
long-term audit store. Durable receipts, replay, metrics and operator visibility remain
separate work.

## Alternatives considered

### Call the evaluator directly from runtime

Rejected. It would permit arbitrary registry/current-evidence substitution and confuse
represented evidence with trusted configuration.

### Put current identity/privacy lookup logic inside the evaluator

Rejected. It would make a deterministic pure component depend on mutable runtime owners,
network/storage availability and potentially duplicate PolicyKernel or identity logic.

### Add concrete resolver implementations in the same PR

Deferred. Current resolver ownership and complete multi-subject aggregation require a
separate review against accepted identity, authorization, consent, restriction, erasure
and policy owners.

### Invoke the signal producer or build an authorized batch in the same PR

Rejected for this slice. Composition, admission evaluation, producer invocation,
persistence and activation must remain separately reviewable authority checkpoints.

### Treat this as Research Mode only

Rejected. The need for a facade follows directly from an accepted current architecture
and a verified implementation gap. This is active engineering hardening, not an
unproven future idea.

## Consequences

Positive:

- caller-controlled registry/resolver substitution is rejected;
- malformed Draft evidence is rejected before external resolver work;
- the pure evaluator remains deterministic and isolated;
- current-state ownership remains outside Continuity;
- the next resolver-integration slice has an explicit typed boundary;
- runtime activation remains impossible by default.

Costs:

- an additional evidence contract must be versioned and tested;
- deployment/operator configuration still needs a separate trusted owner;
- concrete resolver integration and anti-bypass runtime guards remain incomplete;
- canonical documentation must advance after merge.

## Rollback

The change is internal, unwired, unexported and has no persistence or migration.
Rollback is deletion/reversion of:

- `core/continuity/admission_facade.py`;
- its focused tests;
- this ADR and checkpoint documentation.

No stored data, Canon state, runtime configuration or user-visible behavior requires
migration or repair.

## Validation

PR #246 must provide, on one exact final head:

- repository architecture-freeze guard with this ADR;
- Ruff PASS;
- blocking mypy PASS;
- full Continuity tests PASS;
- full repository pytest PASS;
- blocking `core ≥74%` coverage PASS;
- Docker hardening PASS;
- aggregate merge evidence SUCCESS;
- zero unresolved review threads;
- GitHub and Notion synchronization.

Focused adversarial evidence must include:

- registry substitution rejected before resolver call;
- resolver ID/version mismatch rejected;
- resolver identity-property failure controlled;
- resolver execution failure controlled;
- incomplete multi-subject evidence rejected;
- duplicate and cross-envelope Drafts rejected before resolver call;
- cross-contract binding substitution rejected;
- blocked current erasure state remains rejection evidence;
- policy/result content-addressed tamper detection;
- package-level non-export.

## Follow-up decisions required

Separate future decisions are required for:

1. concrete current-decision resolver composition;
2. durable persistence/replay/retention/erasure lifecycle;
3. signal-producer integration and authorized-batch handling;
4. runtime wiring and lifecycle ownership;
5. feature enablement, SLO, monitoring, rollback and Operator GO;
6. any user-visible answer, reminder, notification, delivery, tool, action or compute
   effect.
