# 🧭 Rapid Calibrated Orientation — Research Program

**Status:** `RESEARCH / PROPOSED`  
**Runtime authority:** none  
**Canon write authority:** none  
**Default enabled:** false  
**Proposal target:** [`D16_EXECUTIVE_CONTROL_CONTRACT.md`](D16_EXECUTIVE_CONTROL_CONTRACT.md), currently `RESEARCH / PROPOSED` with no runtime authority  
**Date:** 2026-07-30  
**Scope:** read-only orientation research for Titan; not an implemented cognition claim

## Decision

Titan may research a capability called **Rapid Calibrated Orientation**: produce a
fast, goal-dependent, uncertainty-aware orientation over information already
available to the request.

This capability is **not**:

- a new `EssenceEngine`;
- a new C-level;
- a new `KnowledgeCapsule` or epistemic state;
- a replacement for D16 Executive Control;
- permission to bypass policy, Recall Policy, TruthGate or Canon admission;
- evidence that Titan has human-like wisdom, consciousness or an "effect of god";
- an active query-path feature.

The first permitted artifact is a read-only **`OrientationProjection`**. It may
propose a cognitive route to D16 and emit an auditable receipt. It may not execute
the route, suppress a user request, mutate memory or promote knowledge.

```text
available evidence + GoalFrame + policy-visible context
→ OrientationProjection
→ CognitiveRouteProposal
→ D16 research contract
→ receipt-only comparison; no route is executed by this experiment
```

## Why this belongs in Research Mode

Titan already has many of the mechanisms that an orientation layer would need:

- `GoalFrame` describes intent, risk and constraints;
- `KnowledgeCapsule` stores source-linked extracted meaning;
- `CausalGraph` exposes relations and knowledge status;
- `ontological_axes.py` provides analytic perspectives;
- `AttentionRouter` ranks candidate facts;
- `WorkingMemoryGate` assigns reversible context dispositions;
- `ContextPack` provides a bounded, provenance-preserving read model;
- `ComputeController` estimates computational budget;
- the D16 research contract defines proposal vocabulary and the legacy baseline; no D16 runtime controller is implemented yet.

What is not yet demonstrated is that a single goal-dependent projection over
those components improves routing quality enough to justify runtime authority.
Creating another engine before that evidence would duplicate existing
responsibilities and hide unresolved ownership questions.

Research Mode is therefore the correct home for:

- a precise contract;
- offline and shadow datasets;
- competing algorithms;
- receipts and evaluation metrics;
- falsification criteria;
- operator review.

## Operational vocabulary

### Rapid Calibrated Orientation

The research objective: identify the apparent structure of a situation quickly,
state critical uncertainty explicitly and recommend the minimum sufficient
cognitive route.

"Rapid" is measured by latency and cognitive cost. "Calibrated" is measured by
confidence calibration and error rates. "Orientation" is a proposal about how to
continue, not a claim that the task is already solved.

### `OrientationProjection`

A rebuildable, read-only representation computed from inputs already visible to
the request. It contains no hidden authority and is never the canonical owner of
facts, tasks, goals or policy.

### `CognitiveRouteProposal`

A versioned recommendation validated against the
[D16 research contract](D16_EXECUTIVE_CONTROL_CONTRACT.md). The contract
separates the two behaviours that exist today from proposal-only vocabulary:

```text
Observed baseline:
LEGACY_QUERY
SYNAPTIC_SHADOW_PREVIEW

Proposal-only:
FAST_LOCAL
DELIBERATE_LOCAL
REQUEST_EVIDENCE
CLARIFY
DEFER
```

`RETRIEVE`, `COMPUTE`, `RESEARCH` and `PARALLEL` remain research labels
until the D16 contract assigns explicit semantics, permitted capabilities and a
fallback. No proposal label may silently become a second executive state
machine or imply that an active controller already exists.

### `UnderstandingReceipt`

A structured explanation of the projection and proposal. The name refers to
auditability, not to a claim that the system possesses human understanding.

Every receipt must copy the projection's `policy_snapshot_id` and
`policy_version`. If an experiment invokes an optional capability, it must also
record the complete lease identity: capability, locality, data mode,
`snapshot_id`, `policy_version`, allow/deny result and reason code. A receipt
whose lease snapshot differs from its projection is invalid and cannot support
execution.

## Input boundary

An orientation experiment may read only information that the current request is
already authorised to access:

```text
GoalFrame
PolicySnapshot plus the full current CapabilityLease when a capability is proposed
Recall-policy-approved evidence
KnowledgeCapsule references
ContextPack preview
CausalGraph read views
knowledge_status
ontological axes
budget and latency constraints
operator-supplied preferences for this task
```

The experiment must fail closed when a mandatory policy or provenance dependency
is unavailable. Missing information is reported as a gap; it is never invented.

## Proposed read-model contract

The schema below is illustrative research notation, not a committed Python API:

```text
OrientationProjection
├── projection_version
├── request_id
├── policy_snapshot_id
├── policy_version
├── capability_lease_refs[]
├── goal_frame_digest
├── evidence_refs[]
├── evidence_snapshot_digest
├── apparent_subject
├── task_shape[]
├── knowledge_lenses[]
│   ├── invariant_candidate
│   ├── context_variant
│   ├── practical_procedure
│   └── hypothesis_or_unknown
├── critical_gaps[]
├── contradictions[]
├── risk_flags[]
├── expected_information_gain
├── estimated_cognitive_cost
├── confidence
└── generated_at
```

Required properties:

1. **Deterministic identity where possible.** The same versioned inputs should
   produce the same projection for deterministic implementations.
2. **Rebuildable.** Deleting the projection must not delete source knowledge.
3. **Source-linked.** Every evidence-dependent statement references admitted
   evidence or is labelled as a hypothesis/interpretation.
4. **Goal-relative.** Importance is always "important for goal X", never a
   universal importance score.
5. **Uncertainty-visible.** Critical gaps and conflicting evidence are first-class
   output, not prose hidden inside a summary.
6. **No mutation.** Computation does not alter Canon, ESM, graph relations,
   activation history, attention weights or task state.
7. **Snapshot-bound authority.** Projection identity includes
   `policy_snapshot_id` and `policy_version`. Any later optional action requires
   a current full `CapabilityLease` whose `snapshot_id` and `policy_version`
   exactly match the active projection; generic allow outcomes and stale leases
   are rejected.

## Knowledge lenses, not new knowledge types

The useful distinction "invariant / variant / practical" is retained as a
multi-label **projection lens**. It does not replace `knowledge_status`, ESM or
the existing ontology.

| Lens | Research question | Safety note |
|---|---|---|
| Invariant candidate | What appears stable across the stated scope? | Must still carry evidence and scope; "candidate" is not universal truth |
| Context variant | What changes with time, person, environment or assumptions? | Context must be explicit; absence of context lowers confidence |
| Practical procedure | What action or method is described? | A procedure is not automatically safe, permitted or effective |
| Hypothesis / unknown | What remains inferred, speculative or missing? | Must not be presented as fact or promoted without admission |

A single item may occupy several lenses. For example, a practical procedure may
depend on a context-variant assumption. The projection records that overlap
rather than forcing one permanent category.

## Research-mode reasoning cycle

When D16 or an operator selects a research route, the Working Desk may organise
a bounded investigation:

```text
goal and success criteria
→ known evidence and critical gaps
→ multiple competing hypotheses
→ contradiction map
→ selected research lenses
→ checks, calculations or experiments
→ falsification attempts
→ research receipt
→ optional explicit TruthGate / Canon admission request
```

### Competing hypotheses

Research must keep at least one plausible alternative when the evidence does not
uniquely identify an explanation. A hypothesis record should include:

- claim;
- supporting evidence;
- counter-evidence;
- assumptions;
- discriminating test;
- falsification condition;
- current status;
- remaining uncertainty.

Fast completion, persuasive wording or model confidence is not a valid reason to
select a hypothesis as true.

### Contradictions

Contradictions are research objects, not errors to erase immediately. The
experiment should distinguish:

- genuine logical conflict;
- different time scopes;
- different populations or environments;
- terminology mismatch;
- source disagreement;
- incomplete evidence;
- changed upstream premise.

Resolution produces a proposal. It does not mutate epistemic state by itself.

### Research lenses

Philosophy, literature, psychology, biology and cross-domain analogies may be
used to generate questions or decompositions. They may not become factual
evidence merely because a lens produced them.

Allowed result labels:

```text
FACT
HYPOTHESIS
INTERPRETATION
ANALOGY
METAPHOR
AUTHOR_VIEW
UNKNOWN
```

Examples:

- Aristotelian causes may suggest questions about material, form, cause and
  purpose;
- dialectical analysis may expose a possible conflict;
- an author's narrative may provide an `AUTHOR_VIEW`;
- a biological mechanism may suggest an `ANALOGY` for an algorithm.

Every such output remains labelled until independently supported.

## Reversible `DEFER`, never silent `IGNORE`

A user task must never disappear because a soft router considers it unimportant.
The orientation experiment may propose `DEFER` only with an auditable payload:

```text
DeferProposal
├── goal_reference
├── reason
├── residual_uncertainty
├── risk_of_deferral
├── evidence_that_would_change_the_decision
├── review_trigger
├── expiry_or_review_time
└── operator_override_available = true
```

Required rule:

```text
soft orientation proposal ≠ authority to discard
```

`WorkingMemoryGate.EXCLUDE` remains a separate item-level disposition for
forbidden, erased or unusable context. It must not be repurposed to discard an
entire user task silently.

## Authority boundaries

| Mechanism | Authority |
|---|---|
| Ring Zero / PolicyKernel / CapabilityLease | Permit or deny actions, tools, network and resources |
| Recall Policy | Permit or deny memory retrieval |
| OrientationProjection | Read-only description and route proposal |
| D16 Executive Control contract | Version proposal vocabulary and baseline semantics; currently research-only with no active route authority |
| Working Desk | Organise bounded research state in Research Mode |
| TruthGate / admission service | Evaluate explicit epistemic promotion |
| Canon write service | Perform authorised canonical mutation with required integrity controls |

Orientation must not be described as a gate because it has no blocking
authority. Terms such as `OrientationGate` or `UnderstandingGate` would blur
the distinction between a recommendation and a safety invariant.

## Shadow-first evaluation

The first experiment must be passive:

```text
existing request path ───────────────────────────→ actual outcome
          └→ OrientationProjection (read-only)
             └→ CognitiveRouteProposal
                └→ UnderstandingReceipt + metrics
```

The proposal does not alter the answer, tool selection, memory state, task
priority or Canon. Evaluation compares it with the current baseline and, where
available, an operator-labelled reference.

### Minimum metrics

| Metric | What it detects |
|---|---|
| Routing accuracy | Whether the proposed route matches a reviewed sufficient route |
| Critical-gap recall | Whether missing evidence that changes the answer is noticed |
| False-defer rate | How often useful or important work is wrongly deferred |
| Unsafe-fast rate | How often a risky task is incorrectly sent to a fast path |
| Confidence calibration | Whether confidence predicts correctness |
| Contradiction recall | Whether material conflicts are surfaced |
| Evidence attribution rate | Whether evidence-dependent fields remain source-linked |
| Latency | Wall-clock cost of projection |
| Cognitive cost | Tokens, model calls, retrievals and compute used |
| Stability | Whether equivalent inputs produce equivalent proposals |
| Policy non-interference | Whether shadow work attempts any forbidden access or mutation |

Metrics must be segmented by task class and risk. A good average cannot hide a
high false-defer or unsafe-fast rate in a critical class.

### Baselines

At minimum compare against:

1. the actual authoritative legacy `/query` path, with the passive `SYNAPTIC_SHADOW_PREVIEW` recorded separately;
2. a simple deterministic heuristic;
3. the candidate projection algorithm;
4. an operator-reviewed subset.

The complex candidate is justified only if it provides measurable benefit over
the simple heuristic at an acceptable cost.

## Relationship to PR-SYN-06

PR-SYN-06 is merged and supplies the passive
`SemanticReader → WorkingMemoryGate → ContextPack` preview. It remains the
baseline observation contour, not a D16 implementation. Rapid Calibrated
Orientation is a separate optional experiment and must not retroactively expand
PR-SYN-06 authority.

Current sequence:

1. harden the merged shadow contour and collect stable receipts;
2. define the D16 proposal contract and operator-labelled baseline dataset;
3. implement OrientationProjection as a separate optional experiment;
4. compare proposals without controlling runtime;
5. request explicit Operator GO for any bounded active slice.

## Candidate research phases

### RCO-0 — Contract and dataset

- freeze terminology and authority boundaries;
- define representative task classes and risk labels;
- create operator-labelled route examples;
- define receipt and metric schemas.

### RCO-1 — Deterministic baseline

- use existing goal, status, graph and budget signals;
- produce a read-only projection;
- avoid model calls;
- measure latency, stability and error rates.

### RCO-2 — Optional provider-neutral proposals

- compare local rules, graph algorithms and optional model adapters;
- bind every projection and receipt to `policy_snapshot_id` and
  `policy_version`;
- reject stale or mismatched capability leases before any optional invocation;
- treat all model output as untrusted proposals;
- require provenance for evidence-dependent fields;
- preserve a zero-model path.

### RCO-3 — Shadow comparison

- run beside the existing route;
- collect structured receipts;
- investigate false defers and unsafe-fast proposals;
- publish a reproducible comparison report.

### RCO-4 — Bounded implementation candidate

Only after explicit Operator GO, propose the smallest active use, with rollback,
feature flag, policy tests and no canonical write authority.

## Falsification and stop criteria

The research hypothesis should be rejected or redesigned when:

- it does not outperform a simple heuristic;
- false-defer or unsafe-fast rates exceed approved limits;
- confidence is poorly calibrated;
- provenance cannot be preserved;
- the projection creates material latency without measurable benefit;
- equivalent inputs produce unstable routes;
- the design requires a second task store, ESM or audit ledger;
- the mechanism cannot remain read-only in shadow mode;
- optional model adapters become mandatory for correct operation.

A failed experiment is a valid result. It prevents an attractive metaphor from
becoming unearned runtime complexity.

## Explicit non-goals

This research document does not authorise:

- a new `EssenceEngine`, `UnderstandingEngine` or `ComprehensionGate`;
- D23 or any new decision number;
- a new C-level or L-level;
- automatic task deletion or `IGNORE`;
- hidden chain-of-thought retention;
- self-modifying or learned policy weights;
- automatic truth-threshold weakening;
- direct Canon, ESM, graph or task-state writes;
- claims of consciousness, wisdom or complete understanding;
- mandatory LLMs, embeddings or remote providers.

## Exit criteria

Rapid Calibrated Orientation may become an
`IMPLEMENTATION_CANDIDATE` only when all are true:

1. PR-SYN-06 has produced stable passive receipts and a baseline dataset;
2. a versioned projection contract exists;
3. the zero-model deterministic baseline is measured;
4. operator-labelled evaluations cover simple, ambiguous, contradictory and
   high-risk tasks;
5. false-defer and unsafe-fast thresholds are explicitly approved;
6. policy non-interference and read-only behaviour are tested;
7. results outperform the accepted baseline;
8. rollback and feature-flag behaviour are specified;
9. no duplicate task, epistemic or audit authority is introduced;
10. an explicit Operator GO authorises a bounded active slice.

## Core rule

```text
The vision is rapid orientation.
The engineering artifact is a read-only projection.
The executive authority remains D16.
The truth authority remains explicit admission.
The first proof is shadow evaluation, not persuasive naming.
```
