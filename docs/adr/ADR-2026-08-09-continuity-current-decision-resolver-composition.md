# ADR — Continuity current-decision resolver composition

- **Date:** 2026-08-09
- **Status:** Accepted for internal implementation
- **Tracking:** issue #263
- **Scope:** Continuity source admission only
- **Authority:** evidence composition only; no runtime authority

## Context

The admission facade already defines a typed `ContinuityCurrentDecisionResolver` boundary
and the evaluator already consumes one immutable `ContinuityCurrentDecisionEvidence`.
What was missing was a concrete composition that obtains current decisions from the
accepted owner domains without allowing Continuity to invent identity, permission,
consent, restriction, erasure or policy state.

The aggregate evidence contract represents four decisions directly:

- authorization;
- lawful basis or consent;
- restriction;
- erasure.

Principal validity and PolicySnapshot compatibility are also mandatory, but the existing
aggregate contract has no separate status fields for them. They therefore act as hard
preconditions for composition.

## Decision

Introduce an internal `ContinuityCurrentDecisionResolverComposition` with six named,
injected, read-only owner ports:

1. principal;
2. authorization;
3. lawful basis or consent;
4. restriction;
5. erasure;
6. PolicySnapshot compatibility.

Each port returns exactly one immutable, content-addressed
`ContinuityCurrentDecisionOwnerSnapshot` for the exact invocation. Every snapshot binds:

- owner ID and version;
- principal context ID;
- authorization context ID;
- source envelope ID;
- source binding receipt ID;
- tenant;
- the complete authorization subject set;
- domain-specific scope references;
- status;
- observation and expiry times;
- evidence references.

The composition verifies the content digest again at use time, not only at object
construction. This detects post-construction substitution in hostile or incorrectly
implemented adapters.

## Status vocabulary

The implementation preserves the existing evaluator vocabulary exactly:

```text
ACTIVE · CLEAR · BLOCKED · INACTIVE · WITHDRAWN · UNKNOWN
```

It does not introduce parallel names such as `DENIED`, `INVALID`, `ERASED` or `STALE`.

Authorization and lawful-basis decisions may preserve `ACTIVE`, `BLOCKED`, `INACTIVE`,
`WITHDRAWN` or `UNKNOWN`. Restriction and erasure decisions may preserve `CLEAR`,
`BLOCKED` or `UNKNOWN`. The downstream evaluator remains responsible for converting
non-allowing represented states into rejection evidence.

Principal and PolicySnapshot owners must report `ACTIVE`. Any other state rejects the
complete composition because there is no safe field in the existing aggregate evidence
contract in which to preserve a non-active principal or policy decision.

## Fail-closed rules

The complete composition is rejected when any owner:

- is missing or has the wrong declared domain;
- returns zero, multiple or non-snapshot values;
- raises an exception;
- returns a malformed or tampered content digest;
- substitutes owner identity, principal, authorization, tenant, subjects, source envelope
  or binding receipt;
- returns a mismatched domain scope;
- returns an invalid state for its domain;
- returns evidence that is future-effective or expired at `evaluated_at`.

The resolver also rejects mismatched input contracts and evaluations outside the
authorization validity interval.

## Determinism and identity

The resolver ID is content-addressed from:

- resolver schema and version;
- all six owner domains;
- each owner ID and version;
- the explicit no-runtime-authority boundary.

Identical owner identities and identical current snapshots produce identical aggregate
evidence regardless of evidence-reference ordering.

## Explicit non-scope

This decision does not add:

- concrete database, network, configuration or operating-system owner adapters;
- process-global owner discovery;
- source-producer invocation;
- persistence, retention, replay, cleanup or migrations;
- `/query`, startup, worker or scheduler wiring;
- feature flags, SLOs, monitoring, rollback or Operator GO;
- answer, reminder, notification, delivery, tool or action behavior;
- Canon, ESM, TruthGate, GoalStack or compute-route writes;
- Phase II, ADAO or Research Copilot lifecycle work.

Concrete deployment adapters and their authenticity remain external trust decisions.
Content addressing proves integrity and scope consistency; it does not prove that an owner
is authentic or operator-approved.

## Consequences

### Positive

- the existing facade can be supplied with one strict concrete resolver composition;
- all six owner domains are explicit and independently replaceable;
- negative and unknown represented decisions cannot be silently softened;
- partial multi-subject coverage and cross-context substitution fail closed;
- the implementation remains testable without a database, network or clock read.

### Residual risks

- no concrete live owner adapters are selected or deployed;
- the operator-selected trust root remains absent;
- durable artifact lifecycle and runtime wiring remain separate work;
- owner authenticity, signatures and configuration lineage are not solved by hashes;
- this slice produces implementation evidence only, not live observed evidence.
