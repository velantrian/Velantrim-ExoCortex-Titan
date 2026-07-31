# PR-RDR-09 — Evaluation, Replay, and Promotion Review

**Boundary:** `SHADOW_EVALUATION / OBSERVATION_ONLY / OPERATOR_GO_REQUIRED / NO_LIVE_AUTHORIZATION`

## Purpose

PR-RDR-09 makes Reader Core quality measurable before any live-path decision.
It separates raw observations, deterministic metrics, threshold policy, and the
final operator decision.

```text
labelled cases
    ↓
case observations
    ↓
deterministic aggregate metrics
    ↓
explicit threshold review
    ↓
eligible | no-go | insufficient evidence
    ↓
separate Operator GO still required
```

The framework does not execute Reader Core itself, choose a model, create human
labels, or authorize integration. It records and evaluates results produced by
an external benchmark harness.

## Corpus classes

Every case belongs to exactly one corpus class:

- `SYNTHETIC` — constructed edge cases and invariants;
- `REAL` — representative books, manuals, papers, policies, and long-form
  documents;
- `HUMAN_LABELLED` — cases with independently reviewed expected claims,
  exceptions, relations, contradictions, qualifiers, and source spans.

A synthetic corpus is included in source control for:

- distant contradictions;
- hidden critical exceptions;
- ambiguous revision reuse;
- untrusted document instructions.

Synthetic success is necessary but not sufficient. Promotion thresholds may
require non-zero real and human-labelled corpus counts. Until those counts are
met, the result is `INSUFFICIENT_EVIDENCE` rather than an optimistic zero-error
score.

## Case manifest

`ReaderEvaluationCaseManifest` records expected denominators:

- claims;
- source spans;
- critical exceptions;
- relations;
- contradictions;
- connected qualifiers;
- corpus and label versions;
- stable tags.

A manifest contains labels and counts, not model output.

## Case observation

`ReaderEvaluationCaseResult` records observable counts and resources:

- predicted and matched claims;
- predicted and correct source spans;
- predicted and matched exceptions;
- predicted, matched, and false relations;
- matched contradiction clusters;
- connected qualifiers;
- orphan source claims;
- unsupported synthesis claims;
- replay comparison;
- section latency samples;
- session wall time;
- model tokens;
- projection bytes;
- rebuild time;
- query-path latency delta;
- resume reuse counts;
- safety counters.

The contract rejects impossible observations, such as more matched claims than
expected or more reused units than eligible units.

## Metrics

The aggregator computes transparent ratios only from counts:

```text
claim fidelity                 = matched claims / expected claims
source-span precision          = correct spans / predicted spans
source-span recall             = correct spans / expected spans
critical-exception recall      = matched exceptions / expected exceptions
relation recall                = matched relations / expected relations
false-relation rate            = false relations / predicted relations
contradiction recall           = matched contradictions / expected contradictions
orphan-claim rate              = orphan claims / source claims
qualifier connectivity         = connected qualifiers / expected qualifiers
unsupported-synthesis rate     = unsupported synthesis claims / synthesis claims
replay match rate              = matching replays / cases
resume reuse ratio             = reused units / eligible units
```

When a denominator is unknown or zero, the metric is `None`. It is never
silently converted to `0.0` or `1.0`. A required but unmeasured metric produces
`INSUFFICIENT_EVIDENCE`.

Performance accounting includes nearest-rank p50/p95 section latency, p95
rebuild time, model tokens per case, total projection bytes, and maximum
query-path latency delta.

## Replay

`ReaderReplayComparator` compares two ordered artifact-ID sequences by stable
content-derived digest. Ordering differences count as a mismatch because order
is part of Reader Core's deterministic contract.

```text
same ordered artifacts → matched replay
same artifacts reordered → replay mismatch
```

The comparator does not execute the replay. A harness supplies the two observed
artifact sequences.

## Hard safety gates

The following counters must remain exactly zero:

- TruthGate bypasses;
- query-path writes;
- direct Canon writes;
- execution of untrusted document instructions.

Any non-zero hard safety counter produces `NO_GO`, even when all quality metrics
are perfect and corpus evidence is incomplete.

## Threshold policy

`ReaderPromotionThresholds` is explicit and content-addressed. PR-RDR-09 does
not ship a universal production threshold profile because thresholds must be
chosen against reproducible corpora and deployment constraints.

Thresholds can require:

- minimum total, synthetic, real, and human-labelled case counts;
- minimum fidelity, precision, recall, connectivity, replay, and reuse ratios;
- maximum false-relation, orphan, and unsupported-synthesis rates;
- maximum query-path latency delta;
- optional p95 section latency and model-token envelopes.

## Promotion decisions

`ReaderCorePromotionReviewer` emits one of:

- `ELIGIBLE_FOR_OPERATOR_REVIEW` — evidence exists and configured gates pass;
- `NO_GO` — a hard safety or measured threshold gate fails;
- `INSUFFICIENT_EVIDENCE` — corpus counts or required denominators are missing.

Even an eligible review always contains:

```text
operator_go_required = true
live_integration_authorized = false
```

The review object cannot be constructed with live authorization. Promotion to
`/query`, persistence, memory, Canon, graph authority, or Native Kernel remains
a separate change requiring its own review and explicit operator approval.

## Reproducibility

Reports include a content-derived `EvaluationEnvironment`:

- commit SHA;
- runner ID;
- Python version;
- hardware profile;
- configuration digest;
- optional model ID and version.

Case results are canonically ordered by case ID. Metrics are recomputed from
case results inside `EvaluationSuiteReport`; callers cannot substitute a forged
aggregate. Environment, manifests, replay comparisons, case results, metrics,
thresholds, reports, and promotion reviews all have self-verifying IDs.

## What this PR completes

PR-RDR-09 completes the executable Reader Core evaluation and promotion-review
foundation plus an initial synthetic manifest.

It does **not** claim that Reader Core has passed production evaluation. The
remaining operational work is to:

1. build and version representative real and human-labelled corpora;
2. run the external benchmark harness on pinned environments;
3. inspect failures and calibrate thresholds;
4. publish signed evaluation reports;
5. obtain a separate Operator GO before any live integration.

## Invariants

- observations are not metrics;
- metrics are not authority;
- synthetic success is not production proof;
- missing denominators remain unknown;
- safety violations always block promotion;
- replay order is observable;
- reports cannot forge aggregates;
- promotion review cannot authorize live integration;
- no model, network, database, scheduler, tool, Canon, memory, TruthGate, Write
  Gate, `/query`, graph-authority, or Native Kernel integration.
