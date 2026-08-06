# 🧠 Titan Cognitive Runtime Reconciliation

**Status:** `PROPOSED · DOCS-ONLY · NO RUNTIME AUTHORITY`  
**Source reviewed:** historical draft PR #33 (`7ea833c1fb39a8c2b11a6963f82325eaa1218765`)  
**Reconciled against:** `main@adfccb02f88b290aac8411e94aac69417defbafe`  
**Disposition for old PR #33:** `REVISE_AND_REPLACE`  
**Runtime activation:** forbidden by this document

## 1. Decision

The historical Epistemic and Cognitive Runtime specification contains useful concepts, but it predates accepted owners for compute routing, working-memory admission, context construction, policy snapshots, capability leases, Continuity, Project Cognition, ARM-03 hardening and RFC-0084.

The old branch must not be conflict-resolved and merged wholesale.

```text
old PR #33
    ↓ research source only
current-owner reconciliation
    ↓
small docs-only replacement
    ↓
separate contracts / implementation PRs when approved
```

This document preserves useful ideas while assigning every future responsibility to an existing accepted owner or to an explicitly proposal-only gap.

## 2. Non-authority boundary

This document adds no:

- `/query` change;
- startup registration;
- worker, scheduler or daemon;
- Canon or TruthGate write;
- durable persistence;
- tool execution or network call;
- user-visible answer modification;
- policy authority;
- automatic goal, intention or memory admission;
- automatic learning or adaptation;
- new root of trust.

`PROPOSED ≠ IMPLEMENTED ≠ TESTED ≠ WIRED ≠ ENABLED ≠ OBSERVED`.

## 3. Accepted owner map

| Concern | Accepted current owner | Reconciliation rule |
|---|---|---|
| Canon admission and truth promotion | TruthGate, TruthPolicy, WriteGate, PromotionGateway | Cognitive components may emit candidates only; no direct admission |
| Epistemic state and claim metadata | existing ESM / claim type / origin type / confidence / salience axes | Do not create a second universal epistemic enum |
| Hard policy and capability decisions | PolicyKernel, PolicySnapshot, CapabilityLease, mutation gates | No controller may infer or expand permission |
| Legacy compute routing | `decide_compute_path()` / `ComputeController` | Existing five `ComputePath` values remain authoritative |
| Continuity-aware compute analysis | R4 `assess_compute_with_continuity()` | Shadow-only assessment; not an execution route |
| Executive route vocabulary | D16 Executive Control research contract | Proposal-only; `LEGACY_QUERY` remains fallback |
| Working-memory disposition | WorkingMemoryGate | No parallel eviction/admission owner |
| Final prompt/context payload | ContextPackBuilder | No hidden retrieval, rescore or write |
| Durable user goals | GoalStack under mutation gate | Model inference does not create or cancel user goals |
| Conversation continuity | Continuity GoalAttestation, OpenLoop and projections | Recurrence/open loop does not imply executable intention |
| Adaptation lifecycle | RFC-0084 | One governance lifecycle only |
| Project/repository context | Project Cognition | Code/project context remains separate from user/world Canon |
| Recovery/root-of-trust research | current SAFE_MODE, policy/mutation boundaries; PR #17 remains research | Do not assume Ring Zero is accepted or implemented |
| Event substrate | neutral Claim → Event → Reduction → State → Projection → Receipt model | Do not create a second monolithic audit ledger |

## 4. Epistemic object model

The following are useful **domain concepts**, not a replacement for existing storage axes:

```text
Observation
Claim
Assumption
Hypothesis
Inference
Prediction
Evidence
Candidate Fact
Model
```

Required separation:

```text
object kind
    ≠ processing state
    ≠ truth/admission state
    ≠ source/origin
    ≠ confidence
    ≠ salience
```

A hypothesis never mutates into a fact:

```text
Observation
  → Hypothesis proposal
  → diagnostic predictions
  → supporting / contradicting evidence
  → evaluation result
  → optional Candidate Fact
  → existing TruthGate / promotion path
  → receipt
```

The hypothesis remains a historical reasoning object even when a distinct fact candidate is later admitted.

### Required future contract

Any implementation proposal must define a neutral envelope containing at minimum:

- stable content identity;
- object kind;
- subject and tenant binding where applicable;
- source/origin;
- evidence references;
- confidence and calibration identity;
- created-at supplied by the caller;
- policy snapshot reference;
- purpose and retention class;
- explicit `proposal_only` authority;
- no answer, action, tool, Canon-write or runtime-override field.

## 5. Hypothesis and evidence dynamics

Preserved requirements from PR #33:

- generate more than one plausible hypothesis when evidence is incomplete;
- derive diagnostic predictions capable of distinguishing hypotheses;
- search for contradicting as well as supporting evidence;
- retain counterexamples and unresolved states;
- prevent evidence double-counting through explicit independence groups;
- use deterministic stopping rules and hard budgets;
- preserve structured reasons and evidence references rather than hidden chain-of-thought.

Rejected mechanisms:

- learned source reputation as an automatic TruthGate multiplier;
- model confidence as admission authority;
- majority vote without correlated-error handling;
- automatic promotion of a successful explanation into Canon.

## 6. Cognitive control

PR #33 must not create a new `Cognitive Executive` god-object.

The accepted D16 research contract already separates:

```text
executive route proposal
    ≠ compute path
    ≠ policy permission
    ≠ action execution
```

Future control proposals may use D16 vocabulary and must retain:

- `LEGACY_QUERY` as authoritative fallback until a separate activation decision;
- immutable policy snapshot identity;
- fresh CapabilityLease validation before every optional action;
- bounded budget and stop conditions;
- deterministic reason codes;
- fail-isolated behavior;
- no Canon or task-state mutation unless a separate authorised service is invoked.

The old PR #33 labels `ROUTE_FAST`, `ROUTE_DELIBERATE`, `CONTINUE`, `STOP`, `PAUSE`, `PREEMPT`, `CHECKPOINT`, `REQUEST_EVIDENCE`, `ESCALATE`, `ACTIVATE_INTENTION` and `DEFER` must therefore be treated as candidate control actions and mapped explicitly to D16 or another existing owner. They are not accepted runtime routes by themselves.

## 7. Compute routing

The legacy five-value contract remains unchanged:

```text
FAST_PATH
NORMAL_PATH
DEEP_PATH
VERIFY_PATH
CREATIVE_PATH
```

“Fast epistemic analysis” and “deliberative epistemic analysis” are analysis profiles or evaluation metadata. They must not become a parallel route enum and must not bypass `ComputeController`.

Continuity may provide typed evidence to the R4 shadow assessment, but the result remains non-authoritative until a separate reviewed activation design exists.

## 8. Goals, open loops and intentions

The historical `Intention Registry` idea overlaps with GoalStack and Continuity. The replacement model must distinguish:

| Object | Meaning | Authority |
|---|---|---|
| User Goal | durable user-attested objective | mutation-gated user state |
| Goal Candidate | model-extracted proposal | proposal only |
| GoalAttestation | typed attestation accepted by its contract | no independent action authority |
| Open Loop | unresolved conversational/project continuity signal | descriptive only |
| Intention Proposal | suggestion to revisit or act | proposal only |
| Scheduled Commitment | explicit user/operator-approved future obligation | requires separate scheduler/consent contract |
| Execution Plan | bounded plan for a current action | requires current policy and capability leases |

Core invariant:

```text
recurrence
  ≠ identity
  ≠ user goal
  ≠ consent
  ≠ scheduling permission
  ≠ execution authority
```

Before any future intention implementation, define:

- creator and subject identity;
- tenant binding;
- user statement versus model inference;
- trigger semantics;
- cancellation and supersession;
- expiry;
- consent and purpose;
- retention and erasure;
- anti-spam and localization;
- policy owner;
- receipt and rollback behavior.

## 9. Working-set compaction

The useful “Working Set Eviction” requirements are retained as constraints on existing owners, not as a new manager.

```text
WorkingMemoryGate
    → ACTIVE / COMPRESS / DEFER / REJECT disposition
    → source-linked compact representation
ContextPackBuilder
    → bounded immutable prompt payload
```

Mandatory invariants:

- never remove the only source pointer;
- never merge fact and hypothesis into one untyped summary;
- never collapse conflicting claims into one apparent consensus;
- preserve provenance references and object modality;
- preserve unresolved commitments through an explicit open-loop/checkpoint representation;
- make reconstruction deterministic and bounded;
- do not convert compaction into durable memory admission.

## 10. Information-gathering actions

Useful categories:

```text
TASK_ACTION
INFORMATION_ACTION
MIXED_ACTION
RECOVERY_ACTION
```

These are action-purpose labels only. `read-only` does not mean safe.

Every future information action must pass:

- active PolicySnapshot validation;
- capability and locality checks;
- privacy and remote-data checks;
- subject/tenant authorization;
- resource/rate limits;
- evidence-gap binding;
- provenance and receipt creation;
- cancellation/timeout behavior.

Value-of-information may rank already permitted candidates, but it cannot create permission or override hard policy.

## 11. Failure modes and budgets

The following failure-mode vocabulary is retained for evaluation:

- confirmation-search bias;
- single-source dependency;
- anchor lock;
- base-rate neglect;
- availability dominance;
- overconfidence;
- premature closure;
- hypothesis proliferation;
- analysis loop;
- evidence double-counting;
- feedback contamination;
- self-confirming action.

Each detector must specify:

```text
detection input
false-positive / false-negative cost
severity
required mitigation
receipt event
owner
```

Hard budgets may include:

- maximum active hypotheses;
- retrieval queries;
- external requests;
- scenario depth;
- runtime;
- cost;
- context-pack size.

Adaptive allocation may operate only inside immutable hard limits and only after evaluation under RFC-0084 when it changes learned policy.

## 12. Learning and adaptation

There must be exactly one adaptation governance lifecycle:

```text
Observation
  → Learning Proposal
  → Shadow Evaluation
  → RFC-0084 Candidate
  → Schema Validation
  → Rehearsal
  → Regression Budget
  → Stability Check
  → Operator Approval
  → Versioned Apply
  → Receipt
  → Rollback
```

No cognitive-runtime component may add its own `apply()`, approval path, persistence or Canon write.

This rule also constrains PR #43: LearningPatch may be a proposal envelope, not a parallel governance system.

## 13. Event and receipt model

The old PR #33 proposed a single Titan Audit Ledger. A new monolithic ledger is not accepted.

Future cognitive events must map to the neutral substrate:

```text
Claim / Proposal
    → immutable Event
    → deterministic Reduction
    → rebuildable State
    → bounded Projection
    → Receipt
```

Candidate event names such as `HYPOTHESIS_PROPOSED`, `EVIDENCE_ATTACHED`, `INTENTION_TRIGGERED` or `CONTROL_DECISION_RECORDED` are domain event types only. They do not define a new database, root of trust or authority boundary.

Required properties:

- append-only event identity;
- schema and policy version;
- subject/tenant/purpose binding;
- provenance;
- deterministic reduction;
- replay and corruption detection;
- retention/erasure policy;
- projection checkpoints;
- receipt linking;
- no hidden authority gain during reduction.

## 14. Implementation sequence

### Stage A — documentation and ownership

1. approve this owner map;
2. close old PR #33 as superseded only after the replacement is merged;
3. reference D16, Continuity, WorkingMemoryGate, ContextPackBuilder, GoalStack, PolicyKernel and RFC-0084 rather than redefining them;
4. record GitHub ↔ Notion synchronization.

### Stage B — neutral proposal contracts

Separate Draft PRs may define:

1. hypothesis/prediction/evidence proposal envelope;
2. failure-mode evaluation schema;
3. bounded reasoning-budget schema;
4. goal/open-loop/intention distinction;
5. neutral cognitive event mapping.

All remain unwired and default-off.

### Stage C — shadow evaluation

Only after Stage B review:

- deterministic replay corpus;
- counterevidence and double-counting tests;
- calibration and stopping-rule evaluation;
- unsafe-fast and analysis-loop metrics;
- policy non-interference tests;
- no-user-visible-effect proof.

### Stage D — activation decision

A separate ADR and explicit operator approval are required. Activation must not be bundled with architecture or contract creation.

## 15. Stop conditions

Stop and keep Draft if any change introduces:

- direct Canon write or TruthGate bypass;
- `/query` behavior change;
- startup/worker/scheduler registration;
- a second policy, goal, memory, learning or audit owner;
- a new compute-route enum that conflicts with `ComputeController`;
- automatic user-goal or intention creation from model inference;
- action/tool authority in a proposal object;
- unbounded reasoning or background expansion;
- missing subject/tenant/consent/retention design;
- runtime activation mixed with architecture work.

## 16. Progress by state

```text
Architecture reconciliation:  1/1  = 100%
Implementation:                0/5  =   0%
Tests/evaluation:              0/5  =   0%
Runtime wiring:                0/1  =   0%
Runtime readiness:             0/1  =   0%
```

The architecture decision is intentionally complete while implementation and runtime readiness remain zero.

## 17. Final disposition

```text
PR #33 = REVISE_AND_REPLACE
```

Preserve its useful research concepts, reject its stale ownership assumptions, and never merge the old conflicted branch directly.