# Titan Memory Evaluation Harness Profile v0

**Status:** DOCS-ONLY / RESEARCH / NON-RUNTIME  
**Authority:** none  
**Purpose:** define how Titan may implement a reproducible harness for memory and Reader evaluation without turning graders, retrieval scores, rewards, or generated lessons into truth or Canon.

## 1. Scope

This profile adapts the Velantrim Memory Evaluation Protocol research proposal to Titan's execution/orchestration role.

It does not:

- change TruthGate or Canon semantics;
- authorize new memory writes;
- authorize autonomous self-modification;
- replace existing Reader pipelines;
- add a second RAG pipeline;
- make an LLM grader authoritative.

## 2. Frozen Evaluation Manifest

Each comparable run should persist or emit a manifest containing:

- dataset/version/digest;
- task subset and exact order;
- random seed(s);
- agent model/provider/version;
- retriever configuration;
- Reader model and prompt digest;
- grader model and grader prompt digest;
- memory-construction prompt digest when online learning is tested;
- token/context budgets;
- environment capability profile;
- harness commit/version;
- memory initial-state digest;
- run id.

Material manifest drift creates a new evaluation condition.

## 3. Required comparison modes

Where the benchmark supports them, run:

1. `NO_MEMORY`
2. `FROZEN_MEMORY`
3. `ONLINE_MEMORY`

The same task set should be evaluated under each mode unless the benchmark contract explicitly prevents it.

## 4. Reader metrics

Report answer quality and retrieval quality separately.

Recommended metrics:

- task/answer accuracy;
- recall@k;
- MRR;
- hard-negative precision / forbidden-hit rate;
- abstention rate;
- retrieved tokens per question;
- Reader tokens per question;
- latency p50/p95/p99;
- cost per question when measured;
- accuracy delta per 1k Reader tokens.

A higher answer score with dramatically higher context consumption is not silently labeled strictly better.

## 5. Self-improvement stress matrix

For online-memory experiments, prefer at least:

```text
run1 / run2 / run3
x
default order / shuffle-1 / shuffle-2
```

Report mean, standard deviation, best-worst gap, and performance relative to `NO_MEMORY`.

Single-run gains are insufficient to establish robust self-improvement.

## 6. LessonCandidate boundary

A successful trajectory must not be promoted directly to a trusted reusable workflow.

Suggested flow:

```text
trajectory
-> LessonCandidate
-> environment/applicability check
-> evaluator provenance check
-> counterexample search
-> independent reuse evidence
-> VALIDATED_FOR_SCOPE or REJECTED/CONTESTED
```

Suggested LessonCandidate fields:

- source trajectory refs;
- environment assumptions;
- required capabilities;
- unavailable/forbidden capabilities;
- evaluator result and provenance;
- counterexamples;
- reuse observations;
- validation state.

## 7. Environment Binding

A lesson valid in one execution profile is not automatically valid in another.

```text
semantic similarity != operational applicability
```

For example, a browser-only environment must not learn an API-based workflow as an applicable strategy unless the environment profile actually exposes that capability.

## 8. Evaluator integrity

Evaluator output remains advisory evidence.

```text
grader PASS != causal proof
grader FAIL != proof the strategy failed
```

Prefer deterministic evaluators where possible. When semantic LLM grading is required, freeze grader identity and prompt and record both in the manifest.

## 9. Memory contagion test

Track whether a stochastic or accidental strategy becomes self-reinforcing:

```text
accidental success
-> lesson write
-> retrieval
-> repeated use
-> increasing prevalence
```

Useful observations:

- first introduction task;
- retrieval count over time;
- downstream usage count;
- score before/after introduction;
- effect of quarantine/removal.

## 10. External benchmark adapters

Potential research adapters may include:

- MemConflict-style conflict scenarios;
- LoCoMo / LongMemEval long-horizon memory;
- BEAM large-scale memory operations;
- correction/deletion governance profiles;
- self-improvement variance/task-order stress tests.

Adapters must remain benchmark-facing wrappers around the existing product/runtime boundaries. They do not become runtime authority.

## 11. Non-goals

This document does not authorize:

- replacing Titan Reader;
- GraphRAG expansion;
- new Canon-write paths;
- automatic promotion of learned workflows;
- autonomous M3/identity changes;
- production use of any external benchmark harness.

Any executable implementation requires a separate bounded PR with explicit tests and review.