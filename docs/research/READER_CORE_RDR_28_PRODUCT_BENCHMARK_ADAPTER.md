# PR-RDR-28 — Reader Product benchmark adapter

Status: **bounded production-evidence execution bridge / draft candidate**

Boundary:

```text
EXPLICIT_LOCAL_CORPUS_ONLY
EXACT_DESCRIPTOR_REVERIFICATION
CALLER_SUPPLIES_SEMANTIC_READER
EXISTING_READER_PRODUCT_PIPELINE_ONLY
EXISTING_RDR_12_NORMALIZATION_ONLY
NO_PROVIDER_SELECTION
NO_SECRET_LOADING
NO_QUERY_WIRING
NO_MEMORY_OR_CANON_WRITE
NO_GRAPH_WRITE
NO_TRUTHGATE_OR_WRITE_GATE
NO_SCHEDULER_OR_BACKGROUND_EXECUTION
NO_PROMOTION
NO_OPERATOR_GO
NO_LIVE_AUTHORIZATION
NO_CRYSTAL_CHANGES
```

## Purpose

RDR-14 intentionally left the concrete `ReaderLocalPipeline` implementation
outside its authority-free executor. RDR-28 supplies the smallest bridge needed
to execute the already-implemented Reader Product path against an adjudicated
RDR-11 benchmark case.

```text
ReaderLocalBenchmarkCase
  -> re-verify exact local corpus descriptor
  -> immutable UTF-8 RawSource
  -> existing ReaderProductPipeline
  -> existing ReaderDocumentPrediction.from_artifacts
  -> ReaderLocalPipelineResult
  -> existing RDR-14 executor/scorer
```

The adapter does not create gold labels, acquire documents, decide rights,
select a provider, read `.env`, or configure credentials. A `SemanticReader`
must be supplied explicitly by the caller. If that reader itself uses a remote
provider, that dependency belongs to the caller's separately reviewed benchmark
environment; this module grants no network capability of its own.

## Exact source binding

Every replay reconstructs the RDR-11 `CorpusDocumentDescriptor` from the local
file and declared metadata. Execution fails if the descriptor identity no longer
matches the benchmark case. The file bytes are then hashed again before decoding
as UTF-8, and the character count must still match.

The `RawSource` uses the descriptor's exact SHA-256 `source_revision`, so Reader
artifacts and human gold labels share one immutable revision identity.

## Existing product semantics only

RDR-28 does not reimplement reading or scoring. It invokes:

- `ReaderProductPipeline` for bounded foreground reading;
- its existing one-round selective reread behavior;
- its existing source-grounded SectionCards, exception scans, relation set and
  synthesis candidate;
- `ReaderDocumentPrediction.from_artifacts` for the already-defined RDR-12
  normalization contract.

No new semantic matching, LLM judge, threshold, authority, truth claim, relation
inference policy, or promotion rule is introduced.

## Measurement semantics

The adapter records total wall time and canonical projection byte size. Reader
Product v1 does not expose exact provider token usage or per-section latency, so
those fields remain zero/empty with explicit warnings rather than fabricated
measurements.

The following safety counters are always recorded as zero because this bridge
never invokes those paths:

- `truth_gate_bypass_count`;
- `query_path_write_count`;
- `direct_canon_write_count`;
- `untrusted_instruction_execution_count`.

Zero here is evidence about this adapter path only. It does not authorize live
use and must not be generalized to unrelated runtime surfaces.

## Replay behavior

RDR-14 calls the adapter twice with replay indexes 1 and 2. Each replay:

1. re-verifies the corpus bytes;
2. starts a fresh bounded Reader Product session;
3. produces an independently normalized prediction;
4. returns artifacts to the existing deterministic scorer.

The adapter does not average or conceal replay divergence.

## Relationship to Issue #120

This PR closes only the previously explicit technical gap between an adjudicated
human-labelled corpus and the existing local RDR-14 benchmark executor.

It does **not** satisfy Issue #120 by itself. Still external and mandatory:

1. rights-cleared representative real corpus;
2. at least two genuinely independent annotators per document;
3. independent adjudication and verified gold labels;
4. complete real benchmark batches and retained signed evidence;
5. measured threshold calibration;
6. real shadow burn-in;
7. explicit Operator decision before any canary/live proposal.
