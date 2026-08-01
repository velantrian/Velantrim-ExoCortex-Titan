# PR-RDR-19 — Benchmark preparation from ready human evidence

Status: **non-executing bridge from evidence to benchmark inputs**

Boundary:

```text
READY_HUMAN_EVIDENCE_ONLY
DETERMINISTIC_MANIFESTS
EMPTY_BATCH_CHECKPOINT
NO_PIPELINE_EXECUTION
NO_PROVIDER_SELECTION
NO_SCHEDULER
NO_PROMOTION_OR_LIVE_AUTHORITY
NO_QUERY_MEMORY_CANON_OR_CRYSTAL_WIRING
```

## Purpose

RDR-18 imports returned human evidence and produces an RDR-16 readiness report.
RDR-19 converts a completely ready evidence set into the existing benchmark
contracts:

```text
ReaderEvidencePack
+ ReaderEvidenceImportBundle (all cases ready)
  -> ReaderLocalBenchmarkCase per document
  -> ReaderEvaluationCaseManifest per document
  -> EvaluationCorpusManifest
  -> ReaderBenchmarkBatchPlan
  -> empty ReaderBenchmarkBatchCheckpoint
```

The bridge prepares work. It does not execute the local Reader pipeline, produce
predictions, score observations, sign a report, or authorize promotion.

## Case identity

The evidence workflow uses a content-addressed `evidence_case_id` derived from
package and descriptor identity. The deterministic scorer emits observations
whose `case_id` is the gold label set's `document_id`.

RDR-19 therefore keeps both identities:

- `evidence_case_id` for evidence-program traceability;
- `benchmark_case.case_id == document_id` for scorer, evaluation manifest, batch
  receipt, and report compatibility.

This avoids a late mismatch between a batch receipt keyed by one ID and an
observation keyed by another.

## Gold-derived denominators

Every evaluation case manifest is derived only from the adjudicated gold set:

- expected claim count: number of gold claims;
- expected source-span count: claim source spans, matching the RDR-12 scorer's
  source-span denominator;
- expected exception count: number of gold exceptions;
- expected relation count: number of directed gold relations;
- expected contradiction count: gold relations with kind `contradicts`;
- expected qualifier count: number of gold qualifiers;
- label version: the adjudicated label-set version;
- corpus kind: `human_labelled`.

The bridge does not infer missing labels or change denominators based on model
predictions.

## Readiness gate

Preparation fails unless:

- the import bundle belongs to the supplied evidence pack;
- its readiness report belongs to the same plan;
- every evidence case is `ready_for_benchmark`;
- adjudication submissions exactly cover all evidence assignments;
- every adjudicated gold set matches its corpus descriptor and revision.

Partial evidence cannot produce a smaller, deceptively clean benchmark corpus.

## Evaluation corpus and batch plan

The `EvaluationCorpusManifest` inherits corpus name and version from the verified
corpus package. Case IDs are sorted and unique.

The operator supplies explicit:

- `environment_id`;
- `thresholds_id`;
- maximum attempts per case.

RDR-19 copies these identities into the RDR-13 batch plan. It does not validate
the runtime environment bytes or threshold policy contents; those content-
addressed objects must be created and reviewed separately before execution.

The initial checkpoint is guaranteed to contain zero receipts. Consequently,
preparation cannot masquerade as completed work.

## Tags

Case tags combine:

- source-controlled corpus tags;
- optional explicit preparation tags;
- the fixed tag `human-adjudicated`.

Duplicate tags fail closed rather than being silently collapsed, so accidental
configuration overlap remains visible.

## Output contract

`ReaderBenchmarkPreparationBundle` binds:

- evidence pack ID;
- evidence import bundle ID;
- evaluation corpus ID;
- prepared case IDs;
- batch plan ID;
- empty initial checkpoint ID.

All IDs are content-addressed and self-verifying.

## Security properties

1. No non-ready case enters the benchmark plan.
2. No failed or missing evidence case is silently dropped.
3. Gold labels remain adjudicated human artifacts.
4. Expected counts cannot depend on model predictions.
5. Batch IDs align with scorer observation IDs.
6. The initial checkpoint proves that no case has run.
7. No model, provider, network, scheduler, `/query`, memory, Canon, graph, tool,
   TruthGate, Write Gate, Crystal, or Native Kernel path is invoked.

## Next operational step

A separate explicit runner may consume the preparation bundle, a reviewed local
`ReaderLocalPipeline`, the matching environment object, and the matching
threshold policy. It must execute every planned case twice, append typed receipts
to the checkpoint, retain failures and skips, and only then build the signed
evaluation report.

A prepared batch is not a benchmark result. A successful benchmark is not live
authorization. Shadow burn-in and explicit Operator GO remain mandatory.
