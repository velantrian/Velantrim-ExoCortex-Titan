# RFC-0084 — Adaptive Update Safety Protocol

**Status:** Proposed  
**Date:** 2026-07-28  
**Profile:** Titan research / shadow evaluation  
**Runtime wiring:** None  
**Canon writes:** Forbidden  
**Operator approval:** Required before any future apply path

## 1. Summary

Titan needs a single safety protocol for evaluating adaptive changes before they
can affect retrieval policy, skills, derived projections, model parameters, or
canonical memory.

This RFC defines a bounded, replayable sequence:

```text
Candidate Update
→ Schema Validation
→ Rehearsal Corpus
→ New-Capability Tests
→ Regression Budget
→ Stability Window
→ Operator / Policy Approval
→ Versioned Apply
→ Immutable Update Receipt
→ Rollback Snapshot
```

The RFC does not implement online learning, model training, automatic policy
changes, or a canonical apply service. It defines the evidence required before a
later reviewed implementation may do so.

## 2. Motivation

A change can improve one target example while degrading previously correct
behaviour. This is especially likely for:

- adaptive retrieval thresholds;
- ranking and reranking policies;
- lexical or intent-routing rules;
- skill promotion;
- memory consolidation heuristics;
- ExperienceReplay-derived proposals;
- future local model fine-tuning;
- future LearningPatch application.

One successful evaluation is not evidence of stability. A safe adaptive system
must prove both:

1. the new capability works; and
2. previously accepted behaviour remains inside an explicit regression budget.

The source inspiration is a small transparent language-model experiment that
uses rehearsal examples and repeated successful checks to reduce catastrophic
forgetting. Titan adopts the safety pattern, not the toy model implementation.

Source:
https://habr.com/ru/articles/1063406/

## 3. Relationship to existing Titan boundaries

### 3.1 LearningPatch

RFC-0083 defines what a bounded learning proposal may contain.

```text
RFC-0083 LearningPatch
= what the system proposes to change

RFC-0084 Adaptive Update Safety Protocol
= how the proposal is evaluated, stabilized, approved, applied and rolled back
```

A schema-valid LearningPatch is not evidence that the patch is useful, true,
safe, or stable.

### 3.2 ExperienceReplay

`core/experience_replay.py` is analysis-only. It may produce a bounded proposal,
but it must not mutate Velum, Canon, epistemic state, relation strength, or any
other projection.

ExperienceReplay output may become an input to a future evaluator. It is never
an apply authorization.

### 3.3 Canonical memory boundary

The protocol preserves:

```text
proposal ≠ evidence ≠ admitted memory ≠ Canon
```

No evaluation stage may write to Canon. Any future apply operation requires a
separate canonical write service, policy check, version, audit receipt and
rollback path.

## 4. Scope

This RFC applies to candidate changes that may affect observable system
behaviour, including:

- retrieval configuration;
- query rewriting;
- lexical associations;
- intent patterns;
- skill activation;
- derived relation or attention policies;
- local model adapters or weights;
- prompt or template policy when it changes answer semantics;
- future replay-based consolidation;
- future adaptive domain modules.

## 5. Out of scope

- implementing model training;
- implementing an optimizer or autograd engine;
- changing Titan runtime defaults;
- wiring LearningPatch to stable `/query`;
- automatic Canon or ESM mutation;
- direct Velum mutation;
- remote-provider calls;
- Crystal runtime changes;
- grant deliverable expansion;
- replacing TruthGate, Guardian or the canonical write protocol.

## 6. Core invariants

1. **One pass is never sufficient.** A candidate cannot be promoted after a
   single successful run.
2. **New success cannot hide old regressions.** New-capability metrics and
   regression metrics are reported separately.
3. **Evaluation is read-only.** Production memory is read-only or replaced by an
   isolated snapshot.
4. **No truth promotion from repetition.** Rehearsal frequency, popularity,
   similarity, salience and repeated exposure cannot raise epistemic state or
   confidence.
5. **Every result is reproducible.** Inputs, dataset identities, code SHA,
   policy version, model/provider identity and outputs are recorded.
6. **No incomplete corpus is silently accepted.** Missing required rehearsal
   cases produce `NOT_READY`, not a partial pass.
7. **Restricted data remains restricted.** Erased, quarantined, credential,
   tenant-private and prohibited data cannot leak into fixtures or receipts.
8. **Promotion is explicit.** `STABLE` is not Operator approval.
9. **Apply is versioned and reversible.** Every applied update has a rollback
   target and immutable receipt.
10. **Fail closed on evaluator failure.** Timeout, parser failure, missing
    dependency or metric error cannot become PASS.

## 7. Protocol lifecycle

```text
PROPOSED
  ↓ schema and provenance valid
EVALUATABLE
  ↓ rehearsal corpus complete
EVALUATING
  ├─→ REJECTED
  ├─→ NOT_READY
  └─→ STABLE_CANDIDATE
          ↓ explicit Operator / Policy approval
       APPROVED
          ↓ canonical apply service
       APPLIED
          ├─→ VERIFIED_IN_OPERATION
          └─→ ROLLED_BACK
```

### 7.1 Status meanings

- `PROPOSED`: candidate exists; no quality claim.
- `EVALUATABLE`: required schema, provenance and fixtures are available.
- `EVALUATING`: one or more deterministic or bounded evaluations are running.
- `NOT_READY`: required evidence is missing or inconclusive.
- `REJECTED`: a hard invariant or regression budget was violated.
- `STABLE_CANDIDATE`: configured stability window passed; no apply permission.
- `APPROVED`: Operator or policy authority approved a specific candidate digest.
- `APPLIED`: a separate canonical service applied that exact version.
- `VERIFIED_IN_OPERATION`: post-apply observation remained inside limits.
- `ROLLED_BACK`: apply was reversed to a recorded snapshot/version.

## 8. Rehearsal corpus

The rehearsal corpus is a versioned set of previously accepted scenarios that a
candidate must preserve.

Each case should contain:

```text
case_id
scope
input
policy envelope
memory snapshot identity
expected invariant outcomes
allowed output variants
forbidden outcomes
risk class
source / provenance
fixture version
```

The corpus may include:

- retrieval golden queries;
- provenance and citation coverage cases;
- contradiction and restricted-data cases;
- safe-recall boundary tests;
- language-specific cases;
- latency and resource ceilings;
- failure and graceful-degradation cases;
- deterministic output contracts where appropriate.

### 8.1 Corpus rules

- Cases are immutable inside one dataset version.
- Dataset changes receive a new content identity.
- Training/adaptation data and evaluation data must be distinguishable.
- Hidden holdout cases are recommended for changes capable of overfitting.
- Tenant-private fixtures remain tenant-scoped and must support erasure.
- A candidate cannot remove a failing case from the corpus that judges it.

## 9. New-capability evaluation

A candidate must declare the capability it intends to improve and the metric
that proves the improvement.

Examples:

- relevant-fact recall;
- precision;
- evidence coverage;
- citation/source-span coverage;
- contradiction surfacing;
- intent precision;
- restricted-data leakage rate;
- answer faithfulness;
- latency;
- context size;
- bounded resource consumption.

The declared objective is stored before evaluation. Post-hoc metric selection is
not accepted as evidence.

## 10. Regression budget

A regression budget defines the maximum permitted degradation relative to a
specific baseline.

Example contract:

```yaml
baseline_id: retrieval-policy-v12
hard_zero_tolerance:
  - restricted_data_leakage
  - canonical_write_without_receipt
  - truthgate_bypass
maximum_regression:
  relevant_fact_recall: 0.01
  precision: 0.02
  p95_latency_ms: 25
minimum_improvement:
  target_domain_recall: 0.03
```

### 10.1 Hard failures

The following always reject the candidate regardless of aggregate score:

- unauthorized write;
- provenance loss;
- restricted-data disclosure;
- TruthGate or Guardian bypass;
- cross-tenant leakage;
- missing rollback material;
- non-reproducible candidate identity;
- evaluator failure reported as success.

## 11. Stability window

A candidate must pass the complete evaluation for `N` consecutive runs under
the same declared configuration.

The window records:

```text
required_passes
observed_passes
maximum_failures
maximum_variance
seed policy
environment identity
start time
completion time
```

Default policy is intentionally not fixed by this RFC. Each update class must
define its own `N` and variance limits through a reviewed profile.

A failed full run resets or invalidates the window according to that profile.
Partial tests cannot extend the window.

## 12. Evaluation receipt

Every run emits an immutable evaluation receipt.

Minimum fields:

```text
receipt_id
candidate_digest
candidate_type
base_version
repository_sha
policy_version
rehearsal_corpus_digest
holdout_digest, if applicable
runtime / dependency identity
model or provider identity, if any
network policy
input snapshot identity
new_capability_metrics
regression_metrics
hard_invariant_results
errors and timeouts
result: PASS | FAIL | NOT_READY
started_at
completed_at
```

The receipt must distinguish:

- absence of evidence;
- test failure;
- infrastructure failure;
- policy denial;
- successful evaluation.

## 13. Promotion receipt

A promotion receipt is separate from evaluation receipts.

It must bind approval to the exact candidate digest and include:

```text
approval_id
candidate_digest
accepted evaluation receipt ids
approver / policy authority
approval scope
expiry, if any
apply constraints
rollback target
reason
```

Re-evaluating or editing a candidate changes its digest and invalidates the old
approval.

## 14. Apply and rollback boundary

A future apply service must:

1. verify candidate digest;
2. verify unexpired approval;
3. acquire the correct canonical transaction boundary;
4. capture the pre-apply version/snapshot;
5. apply atomically;
6. emit an immutable update receipt;
7. verify postconditions;
8. roll back on failed postconditions.

This RFC does not authorize creation of that service.

## 15. Update receipt

Minimum fields for a future applied update:

```text
update_id
candidate_digest
approval_id
previous_version
new_version
changed scope
canonical transaction id
projection rebuild requirements
postcondition results
rollback target
operator / service identity
applied_at
final disposition
```

## 16. Threat model

### 16.1 Catastrophic forgetting

A candidate improves the target examples and damages old behaviour.

Mitigation: versioned rehearsal corpus, separate regression metrics, stability
window and rollback.

### 16.2 Evaluation overfitting

A candidate is tuned to visible fixtures without general improvement.

Mitigation: holdout cases, dataset versioning and explicit training/evaluation
separation.

### 16.3 Metric gaming

A candidate improves one aggregate score while violating a safety invariant.

Mitigation: hard zero-tolerance checks that cannot be averaged away.

### 16.4 Prompt-to-policy injection

Untrusted content attempts to alter thresholds, fixtures or approval.

Mitigation: evaluation configuration is policy-controlled, versioned and outside
candidate data.

### 16.5 Receipt forgery or ambiguity

A report claims success without binding to exact inputs and code.

Mitigation: content-addressed identities and complete immutable receipts.

### 16.6 Sensitive fixture retention

Evaluation stores erased or restricted content indefinitely.

Mitigation: data classification, tenant scope, erasure closure and minimal
fixture retention.

### 16.7 Automatic promotion by status confusion

`PASS`, `STABLE` or `SHADOW_VALID` is treated as apply permission.

Mitigation: explicit separate `APPROVED` status and promotion receipt.

## 17. Titan integration map

| Titan component | Permitted role | Forbidden role |
|---|---|---|
| LearningPatch | Candidate envelope | Direct apply |
| ExperienceReplay | Read-only proposal source | Velum/Canon mutation |
| Observer | Metrics and drift signals | Approval authority |
| PolicyKernel | Evaluation and promotion policy checks | Inventing evidence |
| TruthGate | Epistemic admission in a later canonical path | Judging retrieval utility alone |
| Guardian | Safety/values veto | Replacing evidence evaluation |
| AuditChain / receipts | Traceability | Truth by itself |
| VersionStore | Baseline and rollback identity | Automatic promotion |
| Operator | Explicit approval | Bypassing hard invariants |

## 18. Crystal applicability

Crystal may later use the protocol for deterministic regression testing of:

- retrieval changes;
- chunking changes;
- reranker changes;
- query-policy changes;
- citation and provenance presentation.

Current Crystal boundary:

```text
RESEARCH ONLY
NOT CRYSTAL RUNTIME
NOT GRANT DELIVERABLE
NO NEW COGNITIVE MODULE
```

No Crystal implementation is proposed before the current release/scope freeze is
complete.

## 19. Initial implementation plan

### Stage A — documentation and fixtures contract

- this RFC;
- research registry entry;
- no runtime code;
- no automatic learning.

### Stage B — shadow evaluator types

Separate reviewed PR:

```text
core/adaptive_update_protocol.py
tests/test_adaptive_update_protocol.py
tests/fixtures/adaptive_update_safety/
```

Allowed:

- stdlib-only typed contracts;
- deterministic validation;
- receipt serialization;
- in-memory evaluation state machine;
- no apply method.

### Stage C — objective evaluators

- retrieval replay evaluator;
- policy comparison;
- safety invariant suite;
- isolated snapshots;
- bounded resource accounting.

### Stage D — approval contract

- promotion receipt;
- Operator decision;
- expiry and scope;
- still no canonical apply.

### Stage E — canonical apply service

Requires a separate RFC, threat model, implementation PR and explicit Operator
GO.

## 20. Acceptance gates before any live apply path

- production hardening queue complete;
- executable network/egress boundary complete;
- canonical write protocol proven for every writer;
- versioned rehearsal corpus available;
- objective evaluator exists;
- zero-tolerance safety checks exist;
- stability profile reviewed;
- receipts are content-addressed and replayable;
- rollback tested;
- tenant scope and erasure closure verified;
- CI and security review green;
- explicit Operator GO recorded.

## 21. Decision

Adopt rehearsal, regression budgets, stability windows, immutable receipts and
rollback as the required safety boundary for future adaptive updates.

Do not adopt the source article's toy Transformer, scalar JavaScript autograd,
small word-level tokenizer, tiny dataset, or direct online fine-tuning as Titan
runtime components.
