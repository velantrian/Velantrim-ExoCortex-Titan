# 🤝 Multi-AI Role Evaluation Track — Titan Research

**Status:** `R0/R1 RESEARCH · BENCHMARK/REPLAY TRACK · NO RUNTIME AUTHORITY · NO CANON WRITES`  
**Date:** 2026-08-26  
**Primary semantic owner:** `velantrian/Velantrim-Version-LLM-AI-Cognitive-OS`  
**Titan role:** evaluation, replay, shadow comparison, routing evidence and procedural-skill experimentation

## Purpose

Titan should not own permanent claims such as “model X is the critic” or “model Y understands the user best”. Cognitive OS owns the model-profile and routing semantics.

Titan’s bounded role is to answer a narrower engineering question:

> **Can role-specific model hypotheses be measured reproducibly on fixed Velantrim workloads, with preserved inputs, outputs, failures, configuration and independent checks?**

## Source research hypotheses

The current qualitative role observations are maintained in Cognitive OS as `docs/MULTI_AI_ROLE_OBSERVATIONS.md`.

Current candidate task roles include:

```text
Meaning Keeper
Research Translator
Adversarial Reviewer
Experimental Methodologist
Big-Picture Integrator
Engineering Translator
Divergent Explorer
Execution Structurer
Boundary Integrator
```

These labels are test targets, not runtime authority.

## Titan invariants

```text
role hypothesis != routing authority
model agreement != independent evidence
cross-family review != guaranteed independence
model-generated validation status != validation
benchmark winner != Canon truth
replay result != production authorization
skill draft != executable skill
```

Titan must preserve the existing authority boundaries around Canon, TruthGate, PolicyKernel, WriteGate, AuditChain and erasure/privacy controls.

## Cheapest useful experiment

Start with a fixed replayable corpus of existing Velantrim research cases.

Target: 8–12 cases per role family where enough historical examples exist.

Each case should store:

```yaml
case:
  case_id: ...
  task_family: ...
  original_prompt: ...
  context_snapshot_ref: ...
  hard_constraints: [...]
  expected_failure_traps: [...]
  evidence_refs: [...]
  scoring_contract: ...
```

Each model run should store:

```yaml
run:
  provider: ...
  model: ...
  product_or_api: ...
  model_version_if_known: ...
  date: ...
  reasoning_mode: ...
  tools_enabled: [...]
  context_policy: ...
  system_harness_known: true|false
  raw_output_ref: ...
  latency: ...
  token_or_cost_notes: ...
  tool_failures: [...]
  evaluator_refs: [...]
```

## Initial evaluation families

### 1. Meaning Drift

Measure whether the model preserves the user’s original intent after long technical expansion.

Failure examples:
- replaces the goal with a prettier architecture;
- turns a cautious hypothesis into a strong claim;
- loses the user’s non-goals;
- agrees instead of preserving the distinction.

Required companion metric: anti-sycophancy.

### 2. Falsification Precision

Seed known overclaims and subtle vocabulary-regression cases.

Measure:
- true error detection;
- invented-error rate;
- ability to distinguish source evidence from interpretation;
- self-revision after contrary evidence.

### 3. Research Translation

Input: broad intuition.

Expected output:
- falsifiable research question;
- known vs unknown;
- source classes;
- cheapest measurement;
- contradiction/negative-test plan.

Failure: fluent synthesis presented as maturity/evidence.

### 4. Experimentalization

Measure whether the model defines:
- correct object of measurement;
- denominator;
- sample/unit;
- stop rule;
- blocked state;
- resume condition;
- reviewer independence.

Special test: wrong-repository / wrong-live-path trap.

### 5. Divergent Search

Measure useful non-duplicate alternatives while requiring explicit speculation labels.

Failure metrics:
- unsupported analogy rate;
- metaphor-as-mechanism rate;
- stereotype/persona leakage;
- duplicate-idea rate.

### 6. Engineering Translation

Input: accepted bounded research hypothesis.

Measure:
- contract fidelity;
- ownership preservation;
- new-authority creation;
- premature architecture;
- deterministic testability.

### 7. Execution Discipline

Measure exact compliance with a bounded code/workflow task.

Critical negative test:
- model must not invent `validated/supported/PASS` without actual evidence.

### 8. Boundary Integration

Input: conflicting analyses from multiple AIs.

Measure whether the integrator preserves:
- disagreements;
- evidence classes;
- ownership;
- uncertainty;
- separate next tests.

Failure: consensus collapse or umbrella synthesis that erases contradictions.

## Multi-curator / independence experiment

Reuse the existing Research Mode principle:

```text
multi-agent agreement != independent evidence
```

Compare at least:

```text
A: same model, different role prompts
B: same family, different checkpoints/configurations
C: cross-family models
D: model + deterministic verifier
E: model + independent human reviewer
```

Measure correlated misses and correlated false positives, not only agreement rate.

Candidate output:

```yaml
independence_report:
  pair: ...
  shared_errors: ...
  unique_errors: ...
  disagreement_precision: ...
  agreement_correctness: ...
  correlation_notes: ...
```

## Relationship to EvaluationReplay

This track should prefer existing `EvaluationReplay`, `ExperimentFork` and `StructuralDiff` research contracts rather than create a second replay system.

Useful structural diff fields:

```text
answer_diff
claim_diff
evidence_diff
route_diff
policy_diff
cost_diff
failure_diff
```

Provider calls should use recorded outputs/fixtures for deterministic replay where possible. Live re-runs are separate observations because hosted models may change.

## Relationship to Evaluated Procedural Skills

Role observations may suggest skills, but they do not become skills automatically.

Candidate skills for later evaluation:

```text
Meaning Drift Check
Adversarial Architecture Review
Evidence-Status Audit
Experiment Denominator Check
Validation-Status Provenance Check
Boundary-Preserving Synthesis
```

Lifecycle remains:

```text
SkillDraft
→ Experimental Skill
→ fixed evaluation cases
→ failure analysis
→ operator review
→ versioned skill artifact
→ optional bounded use through existing policy/tool boundaries
```

## Routing evidence output

Titan may emit a **role evaluation receipt**, not a routing decision authority.

Candidate shape:

```yaml
role_evaluation_receipt:
  profile_ref: ...
  role: ...
  dataset_id: ...
  dataset_digest: ...
  configuration_ref: ...
  metrics: {...}
  failure_cases: [...]
  independence_notes: ...
  limitations: [...]
  result: supported_candidate|mixed|not_supported|insufficient_data
```

Cognitive OS may later consume measured receipts when designing routing policy. Titan does not promote a model globally.

## Stop rules

Stop or redesign the track if:

- role labels cannot achieve acceptable inter-rater agreement;
- behavior changes too quickly across product updates for the profile granularity used;
- same-role variance exceeds between-role signal;
- reviewers cannot separate preference from correctness;
- role routing does not beat a simpler generic strong-model baseline;
- added multi-model cost/latency does not improve verified task outcomes;
- the experiment begins creating a second truth, policy or identity owner.

## Promotion path

```text
qualitative Cognitive OS hypothesis
→ fixed Titan corpus
→ deterministic/replayable protocol
→ multi-model runs
→ blind/human/deterministic scoring
→ correlation and failure analysis
→ role evaluation receipts
→ Cognitive OS Model Genome update
→ optional shadow routing experiment
→ measured baseline comparison
→ explicit architecture decision
```

## Final rule

> **Titan measures whether model-role specialization is useful. Cognitive OS owns what those measured profiles mean for model selection. Neither AI consensus nor a benchmark score becomes truth or authority.**
