# Evaluation Replay Quickstart

**Status:** offline/CI prototype  
**Runtime authority:** none  
**Canon write authority:** none

This document describes the bounded PR-ERP-01 implementation of the research contract in [`research/EVALUATION_REPLAY_PROTOCOL.md`](../research/EVALUATION_REPLAY_PROTOCOL.md).

## What it does

`core/evaluation_replay.py` compares two already-recorded, local evaluation runs:

```text
fixed package
+ baseline receipts
+ candidate receipts
+ one declared fork
→ structural diff
→ critical safety gates
→ canonical JSON report
```

It compares:

- extracted claim references;
- evidence references;
- memory dispositions;
- temporal relations and conflicts;
- route and policy reason codes;
- latency and resource counters;
- critical write, TruthGate and external-call violations.

It does not execute the Titan query pipeline or reproduce hidden reasoning.

## Run the repository fixture

From the repository root:

```bash
python -m core.evaluation_replay \
  tests/fixtures/evaluation_replay/minimal.json
```

Write canonical JSON to a file:

```bash
python -m core.evaluation_replay \
  tests/fixtures/evaluation_replay/minimal.json \
  --output evaluation-report.json
```

Equivalent inputs produce deterministic semantic digests. Wall-clock timestamps, run labels and JSON key insertion order do not affect the result digest.

## Report classes

| Class | Meaning |
|---|---|
| `BIT_IDENTICAL` | recorded semantic outputs are identical |
| `STRUCTURALLY_EQUIVALENT` | only answer wording changed |
| `REVIEW_REQUIRED` | evidence, memory, route, policy or cost structure changed |
| `REGRESSION` | a critical gate failed |
| `INVALID_RUN` | reserved for callers that classify fixture/adapter failures |

A faster candidate is not automatically approved. `REVIEW_REQUIRED` remains the expected result when the retrieval route or other architecture changes.

## Critical gates

A candidate is classified as `REGRESSION` when any case records:

```text
truth_gate_bypass_count > 0
query_path_write_count > 0
unrecorded_external_call_count > 0
```

These gates are not weighted against latency improvements.

## Fixture boundary

Repository fixtures must be synthetic or explicitly approved. They must not contain:

- credentials or API keys;
- private conversations;
- production database snapshots;
- unredacted personal information;
- live provider calls;
- commands that create irreversible effects.

Missing fixtures fail explicitly. They never trigger network fallback.

## Current limits

PR-ERP-01 supplies schemas, canonical serialization, fixture loading and structural comparison. It does not yet provide:

- adapters from live `QueryPipeline` receipts;
- benchmark corpus generation;
- model-assisted semantic grading;
- trend storage across CI runs;
- automatic candidate promotion;
- production replay or external side-effect simulation.

Those capabilities require separate issues and operator approval.
