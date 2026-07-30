# 🔬 Velantrim Titan Research Mode

This directory contains proposed architecture, evaluation contracts and bounded experiments. A document in this directory does **not** imply runtime authority, production readiness or Canon write permission.

The root [`README.md`](../README.md) links to this research directory as the entry point for future ideas.

## Start here

| Document | Purpose | Status |
|---|---|---|
| [`FUTURE_COMPONENTS.md`](FUTURE_COMPONENTS.md) | current research registry and priorities | index |
| [`EXTERNAL_ARCHITECTURE_PATTERNS.md`](EXTERNAL_ARCHITECTURE_PATTERNS.md) | neutral Titan-native patterns derived from external prior art | research / prior art |
| [`EVALUATION_REPLAY_PROTOCOL.md`](EVALUATION_REPLAY_PROTOCOL.md) | fixed-corpus baseline, replay, fork and structural-diff protocol | research / proposed |
| [`RAPID_CALIBRATED_ORIENTATION.md`](RAPID_CALIBRATED_ORIENTATION.md) | read-only orientation research | research / proposed |
| [`D16_EXECUTIVE_CONTROL_CONTRACT.md`](D16_EXECUTIVE_CONTROL_CONTRACT.md) | proposal vocabulary; no active controller authority | research / proposed |
| [`FAILURE_LIFECYCLE_RELIABILITY_CONTRACT.md`](FAILURE_LIFECYCLE_RELIABILITY_CONTRACT.md) | failure, lifecycle and reliability boundaries | research / proposed |
| [`WORKING_DESK_RESEARCH_MODE.md`](WORKING_DESK_RESEARCH_MODE.md) | bounded task-aware research composition | research / proposed |

Adaptive retrieval and selective-memory architecture is tracked separately at [`../docs/research/ADAPTIVE_RETRIEVAL_MEMORY_ARCHITECTURE.md`](../docs/research/ADAPTIVE_RETRIEVAL_MEMORY_ARCHITECTURE.md).

## Promotion path

```text
research note
→ Titan-native contract
→ licence and threat review
→ offline prototype
→ deterministic replay evaluation
→ shadow receipts
→ explicit Operator GO
→ bounded implementation PR
```

## Research invariants

- no direct Canon or ESM mutation;
- no new policy, truth or audit authority;
- no hidden chain-of-thought requirement;
- no provider-first or mandatory remote dependency;
- external projects remain prior art;
- old ideas remain traceable in `research/archive/` or `docs/archive/legacy/`;
- reproducible evidence precedes active integration.

## Current priority

The first shared foundation is [`EVALUATION_REPLAY_PROTOCOL.md`](EVALUATION_REPLAY_PROTOCOL.md). It is intended to test retrieval, extraction, memory, temporal reasoning, conflict handling and answer support before additional architecture is promoted.
