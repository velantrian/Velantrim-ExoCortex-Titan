# 🛡️ Execution Observation & Evaluation — Boundary Hardening

**Status:** `R1 NORMATIVE CLARIFICATION · RESEARCH / PROPOSED`  
**Runtime authority:** none  
**Canon / ESM write authority:** none  
**Production authority:** none  
**Default enabled:** false  
**Documentation impact:** `GITHUB_AND_NOTION`  
**Date:** 2026-09-04  
**Baseline:** `main@84a25712cbd1c2a7e42e7aebb9aace7e7b1d0168`  
**Parent contract:** [`EXECUTION_OBSERVATION_EVALUATION_CONTRACT.md`](EXECUTION_OBSERVATION_EVALUATION_CONTRACT.md)  
**Parent intake:** merged PR `#442`

## 0. Purpose and precedence

This document is a bounded corrective clarification of the R1 execution-observation
contract introduced by PR #442 after independent review. It does **not** create a new
research track, runtime subsystem, storage owner, evaluator owner, TRACE owner or
production capability.

Where wording in the parent contract is ambiguous, this clarification governs future
implementation and review.

```text
PR #442 historical intake remains historical truth
+
this clarification tightens interpretation
≠
retroactive runtime authority
```

The goal is to close six risks before any implementation is considered:

1. duplicate TRACE / observability ownership;
2. hidden authority transfer;
3. observation → evidence / causal-use conflation;
4. accidental Opik topology import;
5. overlap with replay / RT-REFTRACE / operational observability;
6. privacy / retention / erasure ambiguity.

## 1. Source-of-record and duplicate-ownership firewall

`ExecutionTraceView` and `ExecutionSpanView` are **derived, rebuildable, non-owning
projections**.

They must never become the source of truth for execution, evidence, permission,
continuity, cognition, identity, Canon or policy state.

### Normative rules

- every projected item must retain an explicit `owner_domain` and an opaque reference to
  the owning artifact;
- the owning artifact's lifecycle, access policy, revocation, restriction and erasure
  status govern the projection;
- a projection may be recomputed from owner-local artifacts but may not silently create
  an independent semantic lifecycle;
- no future `ExecutionTraceView` store may become a second TRACE source of record;
- no cross-project fallback is implicit: `Crystal` and a Titan-local owner are not
  interchangeable evidence authorities merely because both can expose references;
- cross-project references require an explicit receiving boundary and preserve the
  source owner's authority.

```text
projection != owner
projection persistence != authority
shared vocabulary != shared ownership
Crystal reference != Titan Canon
Titan reference != Crystal Canon
```

If a future design cannot name the owning artifact and owner domain for a projected
field, that field is not admissible to the projection contract.

## 2. Evidence-reference and causal-use semantics

The parent R1 schema used the label `evidence_refs[]` inside `ExecutionSpanView`. Any
future implementation should prefer the less ambiguous name:

```text
evidence_artifact_refs[]
```

If compatibility requires retaining `evidence_refs[]`, its meaning is strictly:

> opaque references to artifacts whose evidence status is determined elsewhere by the
> owning domain.

Presence in a span does **not** create, strengthen or transfer evidence status.

### Required invariants

```text
SPAN != EVIDENCE
EVIDENCE_REF_PRESENT != EVIDENCE_ADMITTED
TRACE != PROOF OF USE
TRACE TREE != CAUSAL PROOF
PARENT_SPAN != AUTHORITY PARENT
R != S != T != U != A
OBSERVED_TRANSMISSION != U
U != A
EVALUATION SCORE != TRUTH
OBSERVATION != CANON
FIXTURE_APPROVAL != EVIDENCE_ADMISSION
FIXTURE_APPROVAL != CANON_ADMISSION
```

The preferred term for accepting a regression fixture is **fixture approval**, not
unqualified `admission`. If historical text says `fixture admission`, it must be read as
approval into an evaluation package only.

A trace may establish that an artifact was retrieved, serialized or transmitted when
those stages are directly observed. It may not infer semantic use, causal contribution
or answer support without a separately accepted attribution contract.

## 3. Operational observability boundary

Titan already has an operational-observability engineering lane. The R1 research track
must not duplicate it.

### Operational observability engineering owns

- runtime collection and instrumentation;
- operational metrics and logs;
- persisted incident/debug history;
- production trace-store selection, if ever accepted;
- storage lifecycle, retention, backup, recovery and incident evidence;
- production access control and operational SLOs.

### `RT-OBS-EVAL-01` research owns only

- a Titan-native **read-only semantic projection** for evaluation;
- offline/synthetic execution-tree fixtures;
- `R/S/T` discrimination experiments;
- non-authoritative evaluation observations;
- fixture-local selective evaluator reopen;
- comparison of richer observation against the simpler existing TRACE/logging baseline.

```text
RT-OBS-EVAL-01 != production observability program
R1 contract != authorization to add instrumentation
R1 contract != authorization to persist production traces
```

The already-documented historical-trace reconstruction gap is a relevant problem
statement, but **is not by itself sufficient promotion evidence**. Before implementation,
a concrete Titan workload must show that the existing ReasoningTrace / receipts / logs /
evaluation-replay surfaces cannot represent the required evaluation or debugging question
cleanly.

## 4. Replay and `RT-REFTRACE-01` deduplication

The existing [`EVALUATION_REPLAY_PROTOCOL.md`](EVALUATION_REPLAY_PROTOCOL.md) remains the
single evaluation-package, baseline/fork, deterministic replay and structural-diff owner.

`RT-OBS-EVAL-01` may provide richer read-only inputs to that protocol; it does not create
another replay framework.

`RT-REFTRACE-01` remains specifically the lane for **reference decision-trace fixtures**.
Therefore:

```text
decision-trace-shaped regression
→ may extend RT-REFTRACE-01

generic failure / timeout / privacy / transport / resource regression
→ ordinary EvaluationCase / EvaluationPackage
```

A generic failure must not be forced into `RT-REFTRACE-01` merely because a trace exists.
There is no second failure-fixture program.

## 5. Privacy, retention and erasure semantics

This section is normative for any future trace/span/fixture persistence.

### 5.1 Retention inheritance

A derived observation, preview, digest or reference may not obtain a stronger retention
entitlement than its source.

```text
derived retention <= source-authorized retention
replay convenience != retention authority
evaluation value != lawful retention basis
```

Where multiple source artifacts apply, the derived object must respect the most
restrictive applicable visibility/retention/erasure condition unless an explicit owner
policy says otherwise.

### 5.2 Digests and opaque references

Digests, IDs and opaque references are not automatically non-sensitive. If they remain
linkable to restricted or erased source material, they inherit the relevant restriction.

A digest may support integrity/reproducibility, but must not be used as an erasure bypass
or as a hidden durable identifier for removed content.

### 5.3 Erasure / revocation propagation

When an owning source becomes erased, revoked or newly restricted:

- selective reopen of that source must fail closed;
- cached previews must no longer expose the removed payload;
- derived artifacts must be re-evaluated for continued lawful/authorized retention;
- a fixture that can no longer be safely retained must not remain usable merely because
  its evaluation package was previously immutable;
- source references may be replaced with a non-reversible tombstone where audit policy
  permits retaining the fact that an invalidation occurred.

### 5.4 Immutable package does not mean erasure-immune

In the evaluation protocol, **immutable** means that a historical valid package version is
not silently rewritten into a different semantic package.

It does **not** mean that privacy, erasure, legal restriction or secret-removal obligations
can be ignored.

Permitted lifecycle labels for a package or fixture include:

```text
VALID
QUARANTINED_PRIVACY
INVALIDATED_ERASURE
SUPERSEDED_REDACTED
```

If material must be removed, create a new safe/redacted package version when possible and
mark the affected historical version unusable for evaluation. Do not manufacture a false
claim that the erased payload remains available.

### 5.5 Failure-derived fixture requirements

A future `FailureDerivedFixture` must record enough policy metadata to prove safe handling,
for example:

```text
fixture_id
owner_domain
source_class
sanitization_manifest
fixture_approved_by
fixture_approved_at
retention_class
visibility_scope
source_restriction_state
expected_invariants[]
acceptable_outcomes[]
forbidden_outcomes[]
limitation_notes[]
fixture_digest
```

Raw production prompts, personal data, secrets or hidden chain-of-thought remain forbidden
as automatic repository fixtures.

## 6. Selective reopen authority

Selective evaluator reopen is a read pattern, not a permission source.

A future implementation must:

- use the existing applicable access decision / lease / authorization boundary;
- remain within the original evaluation visibility scope;
- fail closed when the source has been erased, revoked, expired or restricted;
- record exactly what bounded item was reopened and under which evaluation scope;
- obey count/bytes/tokens/time/cost ceilings;
- make deterministic offline claims only when all reopened data is fixture-bound and
  versioned;
- never widen access because an evaluator requested more context;
- never call an unleased provider or external tool as a fallback.

```text
evaluator need != permission
evaluator reopen != new capability lease
read access != evidence admission
```

## 7. External prior-art / Opik topology containment

The Opik intake remains prior art only. This clarification reaffirms that no external
service topology becomes Titan architecture by analogy.

The following remain explicitly non-authoritative:

- Opik class/service names;
- ClickHouse / MySQL / Redis / MinIO deployment topology;
- a mandatory SaaS control plane;
- Opik guardrails as Titan permission authority;
- Opik evaluator scores as truth;
- OpenTelemetry / OTLP as semantic authority.

OpenTelemetry/OTLP may only be considered as a separately reviewed transport profile.
Transport compatibility does not select storage, retention, ownership or semantic status.

## 8. Hardened promotion gate

No runtime implementation follows from PR #442 or this clarification.

Before any implementation PR, reviewers must have all of the following:

1. one concrete Titan workload that the current ReasoningTrace / receipts / logging /
   replay baseline cannot represent cleanly;
2. an explicit field-by-field source-of-record and owner map;
3. proof that the candidate projection is rebuildable and non-owning;
4. deterministic `R/S/T` fixtures leaving `U/A` unestablished unless separately proven;
5. a replay deduplication check against `EVALUATION_REPLAY_PROTOCOL.md`;
6. a fixture-classification check showing when `RT-REFTRACE-01` applies and when it does not;
7. a privacy matrix covering retention, restriction, erasure, tombstoning and digest
   linkability;
8. fail-closed selective-reopen tests for erased/revoked/out-of-scope refs;
9. explicit resource ceilings;
10. proof of zero Canon / ESM / policy / permission / runtime-decision mutation;
11. comparison against the simpler existing operational observability baseline;
12. a separate bounded implementation PR;
13. a separate activation / Operator GO if runtime or production posture would change.

Passing offline evaluation remains evidence for a decision; it is not the decision itself.

## 9. Cheapest additional discriminating experiments

### EO-H1 — projection source-of-record test

Build a synthetic trace projection from owner-local fixture artifacts. Remove or revoke one
source artifact and prove the projection cannot continue presenting it as independently
owned durable state.

### EO-H2 — erasure-aware immutable package test

Create an evaluation package containing one sanitized failure-derived fixture. Simulate a
later erasure/restriction event and prove:

- the old semantic package is not silently rewritten;
- the affected fixture becomes unusable (`INVALIDATED_ERASURE` or
  `QUARANTINED_PRIVACY`);
- selective reopen fails closed;
- a safe redacted successor package can be created without claiming the erased material
  still exists.

### EO-H3 — operational-observability dedup test

For one concrete debugging/evaluation workload, compare:

```text
existing ReasoningTrace + receipts + logs + replay
vs
candidate read-only ExecutionTraceView
```

Promote the candidate only if the richer projection answers a declared question the
baseline cannot answer cleanly, without adding a second operational storage owner.

## 10. Documentation synchronization rule

GitHub owns mutable PR/main/check/review lifecycle facts. Notion may mirror research
rationale and current research status, but any `DRAFT`, `MERGED`, SHA, review or CI claim
must be refreshed when the GitHub lifecycle changes.

PR #442 is historical evidence of the original intake. This corrective follow-up must be
represented as its own bounded draft until independently reviewed; it must not rewrite the
history of #442 to make the earlier lifecycle appear different.

## 11. Review verdict encoded by this clarification

```text
authority transfer:                 NOT FOUND
observation/evidence conflation:    BOUNDED BY CLARIFICATION
Opik topology transfer:             NOT FOUND
second replay owner:                FORBIDDEN
second operational TRACE owner:     FORBIDDEN
privacy/retention ambiguity:        HARDENED HERE
runtime implementation:             NOT AUTHORIZED
production authority:               NOT AUTHORIZED
```

## Core rule

```text
Project observations; do not own them twice.
Reference evidence; do not manufacture its status.
Use replay; do not fork its authority.
Evaluate failures; do not turn them into automatic truth.
Respect erasure even when evaluation history is immutable.
Borrow patterns; never borrow sovereignty.
```
