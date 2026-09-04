# 🔬 Velantrim Titan Research Mode

This directory contains proposed architecture, evaluation contracts and bounded experiments. A document in this directory does **not** imply runtime authority, production readiness or Canon write permission.

The root [`README.md`](../README.md) links to this research directory as the entry point for future ideas.

## Start here

| Document | Purpose | Status |
|---|---|---|
| [`IDEA_INTAKE_PROTOCOL.md`](IDEA_INTAKE_PROTOCOL.md) | capture, classify and preserve ideas from audits, conversations and external analysis without confusing them with current engineering | research governance contract |
| [`FUTURE_COMPONENTS.md`](FUTURE_COMPONENTS.md) | current research registry, candidate tracks and return triggers | index |
| [`SMART_CONTEXT_HANDOFF_V0_1.md`](SMART_CONTEXT_HANDOFF_V0_1.md) | bounded Smart Context / Context Observer / state-delta / successor-handoff research contract | research design · shadow candidate · not runtime authority |
| [`EXTERNAL_ARCHITECTURE_PATTERNS.md`](EXTERNAL_ARCHITECTURE_PATTERNS.md) | neutral Titan-native patterns derived from external prior art | research / prior art |
| [`EVALUATION_REPLAY_PROTOCOL.md`](EVALUATION_REPLAY_PROTOCOL.md) | fixed-corpus baseline, replay, fork and structural-diff protocol | partial offline prototype |
| [`EXECUTION_OBSERVATION_EVALUATION_CONTRACT.md`](EXECUTION_OBSERVATION_EVALUATION_CONTRACT.md) | hierarchical execution observation, non-authoritative evaluation, failure-derived fixture admission and bounded selective drill-down | R1 contract · research / proposed · no runtime authority |
| [`../docs/EVALUATION_REPLAY_QUICKSTART.md`](../docs/EVALUATION_REPLAY_QUICKSTART.md) | command, report classes, critical gates and fixture boundary | PR-ERP-01 implementation guide |
| [`../docs/research/READER_CORE_LONG_DOCUMENT_ARCHITECTURE.md`](../docs/research/READER_CORE_LONG_DOCUMENT_ARCHITECTURE.md) | progressive book and long-document reading, SectionCards, coverage and selective reread | research / proposed |
| [`RAPID_CALIBRATED_ORIENTATION.md`](RAPID_CALIBRATED_ORIENTATION.md) | read-only orientation research | research / proposed |
| [`D16_EXECUTIVE_CONTROL_CONTRACT.md`](D16_EXECUTIVE_CONTROL_CONTRACT.md) | proposal vocabulary; no active controller authority | research / proposed |
| [`FAILURE_LIFECYCLE_RELIABILITY_CONTRACT.md`](FAILURE_LIFECYCLE_RELIABILITY_CONTRACT.md) | failure, lifecycle and reliability boundaries | research / proposed |
| [`HYPERIA_LINEAGE_REASSESSMENT_2026-08-24.md`](HYPERIA_LINEAGE_REASSESSMENT_2026-08-24.md) | current-code reassessment of residual Hyperia/v7.5/v8 ideas; separates one bounded engineering slice from parked research | triaged research + offline prototype |
| [`WORKING_DESK_RESEARCH_MODE.md`](WORKING_DESK_RESEARCH_MODE.md) | bounded task-aware research composition | research / proposed |

Adaptive retrieval and selective-memory architecture is tracked separately at [`../docs/research/ADAPTIVE_RETRIEVAL_MEMORY_ARCHITECTURE.md`](../docs/research/ADAPTIVE_RETRIEVAL_MEMORY_ARCHITECTURE.md).

## Where an idea belongs

```text
verified defect / accepted missing proof / current blocker
→ active engineering docs, issue or bounded implementation PR

unproven architecture / future workload / uncertain ownership or value
→ IDEA_INTAKE_PROTOCOL.md
→ FUTURE_COMPONENTS.md
```

Do not move branch protection, current Continuity admission work, privacy/erasure closure,
query-path read-only enforcement, Canon-writer unification, projection lifecycle or
security hardening into Research Mode. Those are current engineering obligations.

Research Mode is for preserving future ideas whose design, trigger, evidence or authority
boundary is not yet accepted.

## Promotion path

```text
captured idea
→ triage against current architecture
→ Titan-native contract
→ licence and threat review
→ offline prototype
→ deterministic replay evaluation
→ shadow receipts
→ explicit architecture decision
→ bounded implementation PR
→ separate Operator GO when authority changes
```

## Research invariants

- no direct Canon or ESM mutation;
- no new policy, truth or audit authority;
- no hidden chain-of-thought requirement;
- no provider-first or mandatory remote dependency;
- external projects remain prior art;
- old ideas remain traceable in `research/archive/` or `docs/archive/legacy/`;
- every parked idea has an explicit return trigger;
- current engineering debt is not hidden in the future-ideas registry;
- reproducible evidence precedes active integration.

## Current priority

The first shared foundation is [`EVALUATION_REPLAY_PROTOCOL.md`](EVALUATION_REPLAY_PROTOCOL.md). PR-ERP-01 implements only its offline schemas, canonical digests, local fixture loader and structural diff in [`core/evaluation_replay.py`](../core/evaluation_replay.py). It is not connected to production startup, query routing or Canon writes.

The execution-observation contract is deliberately downstream of that foundation: it may propose richer read-only observations and evaluation fixtures, but it does not create a second replay system, TRACE owner or runtime path.

New ideas from audits or conversations must first pass the classification and mandatory-card requirements in [`IDEA_INTAKE_PROTOCOL.md`](IDEA_INTAKE_PROTOCOL.md).
