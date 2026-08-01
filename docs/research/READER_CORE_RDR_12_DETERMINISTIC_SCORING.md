# PR-RDR-12 — Deterministic prediction-to-gold scoring

Status: **isolated evaluation adapter**

Boundary:

```text
EXACT_SOURCE_LINKED_MATCHING
NO_FUZZY_TEXT_MATCHING
NO_EMBEDDINGS
NO_LLM_AS_JUDGE
NO_MODEL_EXECUTION
NO_QUERY_WIRING
NO_MEMORY_OR_CANON_WRITE
NO_PROMOTION_AUTHORITY
NO_LIVE_AUTHORIZATION
```

## Purpose

PR-RDR-11 creates verified, adjudicated human labels. PR-RDR-10 consumes
measured benchmark observations. PR-RDR-12 connects those layers by converting
Reader Core artifacts into normalized predictions and scoring them against one
adjudicated document label set.

```text
Reader Core artifacts
    -> normalized source-linked predictions
    -> exact one-to-one gold matching
    -> transparent integer counts
    -> ReaderBenchmarkObservation
    -> PR-RDR-10 report/review
```

This PR does not execute Reader Core. It scores artifacts produced by an
isolated caller. An execution harness remains a separate stage.

## Normalized prediction types

- `ReaderClaimPrediction`
- `ReaderExceptionPrediction`
- `ReaderRelationPrediction`
- `ReaderQualifierPrediction`
- `ReaderSynthesisPrediction`
- `ReaderDocumentPrediction`
- `ReaderExecutionMeasurement`

Prediction envelopes intentionally omit claim prose. Identity and scoring use:

- exact document and revision;
- enum category or modality;
- exact `SourceSpan` coordinates and content hash;
- explicit qualifier/applicability codes;
- directed claim endpoints;
- explicit synthesis support IDs.

`ReaderDocumentPrediction.from_artifacts()` adapts existing `SectionCard`,
`CriticalExceptionCandidate`, `CrossSectionRelationSet`, and
`GlobalDocumentSynthesis` values. Rejected exception/relation candidates are not
counted as predictions. Unvalidated and supported candidates remain observable.

## Claim matching

A predicted claim and gold claim share a matching key only when all of the
following are equal:

```text
modality
ordered exact source spans
sorted qualifier codes
sorted applicability codes
```

Claim text, extraction confidence and truth confidence are not used as hidden
matching variables. Exact source evidence is the primary contract.

Matching is one-to-one. When several predictions share one key, they cannot all
claim credit for one gold label. Deterministic sorted pairing caps matches at
the smaller multiplicity.

## Source-span scoring

Claim source spans are compared as a multiset of:

```text
document_id
source_revision
start_offset
end_offset
content_hash
```

This separately measures span precision/recall even when a full claim key does
not match.

## Exception matching

An exception matches only when these values are exact:

- exception category;
- trigger span;
- statement span;
- target gold claim IDs.

Predicted target claim IDs are first translated through the exact claim match
map. An exception referencing an unmatched claim receives no match.

## Relation matching

A relation matches only when these values are exact:

- directed relation kind;
- mapped source gold claim ID;
- mapped target gold claim ID;
- evidence spans.

Direction is significant. A wrong kind, reversed edge, unmatched endpoint or
changed evidence span is a false relation.

`matched_contradiction_count` is derived only from exactly matched
`CONTRADICTS` relations.

## Qualifier matching

A qualifier matches only when these values are exact:

- qualifier kind;
- mapped target gold claim ID;
- source span.

Current Reader Core claim strings do not provide typed qualifier provenance.
Therefore qualifier predictions are an explicit evaluation adapter input rather
than an inferred conversion from arbitrary strings.

## Synthesis observability

For scoring purposes:

- `source_claim_count` is the number of normalized predicted source claims;
- an orphan source claim is not referenced by any synthesis claim;
- a synthesis claim is unsupported when none of its supporting source claims
  exactly matches a gold claim.

This does not claim that gold labels are external truth. It measures whether the
synthesis remains connected to the adjudicated evaluation evidence.

## Replay

A document prediction has a content-addressed prediction ID and a canonical
artifact-ID list. The observation sends:

```text
first.replay_artifact_ids
replay.replay_artifact_ids
```

into the existing PR-RDR-10 replay comparator. Any normalized prediction or
artifact change is visible as replay mismatch.

## Measurements and safety counters

`ReaderExecutionMeasurement` carries only explicit observations:

- section latencies;
- wall time;
- model tokens;
- projection bytes;
- rebuild time;
- query-path latency delta;
- resume reused/eligible units;
- TruthGate bypass count;
- query write count;
- direct Canon write count;
- untrusted instruction execution count.

The scorer never invents these values. PR-RDR-09 still applies zero-tolerance
safety gates.

## Why exact matching

Exact matching has lower recall than a semantic judge, especially when two
correct annotations choose slightly different spans. That is deliberate for the
first promotion boundary:

- results are reproducible;
- no evaluator model can quietly change;
- no embedding threshold needs calibration;
- evidence can be inspected directly;
- duplicate credit is impossible;
- mismatch reasons remain mechanically explainable.

Later work may add separately reported overlap or adjudicated semantic metrics.
Such metrics must not replace the exact score silently.

## Remaining work

PR-RDR-12 still does not provide:

- an isolated process that executes the full Reader Core pipeline;
- model/provider pinning and resource isolation;
- corpus-package JSON loaders;
- batch scoring across a complete package;
- automatic RDR-10 benchmark input emission;
- real or independently labelled corpus acquisition;
- calibration distributions;
- public-key report signing;
- Operator GO;
- shadow, canary, or live integration.
