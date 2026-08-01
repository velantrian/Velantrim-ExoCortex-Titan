# PR-RDR-18 — Returned evidence import and readiness CLI

Status: **local human-evidence validation tooling**

Boundary:

```text
LOCAL_RETURN_FILES_ONLY
HUMANS_AUTHOR_LABELS
STRICT_CONTENT_IDS
LOCAL_SPAN_VERIFICATION
READINESS_ONLY
NO_LABEL_GENERATION
NO_MODEL_EXECUTION
NO_BENCHMARK_EXECUTION
NO_PROMOTION_OR_LIVE_AUTHORITY
NO_QUERY_MEMORY_CANON_OR_CRYSTAL_WIRING
```

## Purpose

RDR-17 creates a verified evidence pack and blind annotation packets. RDR-18
handles the return path after human annotators and an independent adjudicator
supply artifacts.

The command:

```text
scripts/import_reader_evidence.py
```

rebuilds the RDR-17 pack from the same local source spec and current immutable
file bytes, imports returned JSON artifacts, verifies every labelled source span
against the local corpus, and writes a canonical RDR-16 readiness bundle.

It never creates or completes labels on behalf of a human.

## Return directory

The return directory may contain only regular `.json` files. Unknown schemas,
non-JSON files, nested directories, and malformed JSON fail closed.

Two submission schemas are supported.

### Annotation submission

```json
{
  "schema_version": "reader-core.annotation-submission.v1",
  "packet_id": "...",
  "label_set": {
    "schema_version": "reader-core.human-labels.v1",
    "document_descriptor_id": "...",
    "document_id": "...",
    "source_revision": "...",
    "annotator_id": "annotator-001",
    "guideline_version": "reader-core.annotation-guideline.v1",
    "label_version": "labels-v1",
    "role": "annotator",
    "claims": [],
    "exceptions": [],
    "relations": [],
    "qualifiers": [],
    "label_set_id": "..."
  },
  "submission_id": "..."
}
```

The example omits actual label objects for brevity; a valid label set requires at
least one claim. Every label, span, label set, and optional submission ID is
self-verifying. The label set must match the exact packet recipient, document,
descriptor, revision, and guideline plan.

### Adjudication submission

```json
{
  "schema_version": "reader-core.adjudication-submission.v1",
  "case_id": "...",
  "adjudicator_id": "adjudicator-001",
  "source_label_set_ids": ["...", "..."],
  "adjudicated_label_set": {},
  "resolutions": [],
  "adjudication_id": "...",
  "submission_id": "..."
}
```

An adjudication submission is accepted only when every referenced source label
set has been imported from an assigned blind packet. Its source annotators must
exactly equal the case roster, and the adjudicator must equal the independently
assigned adjudicator.

The existing RDR-11 `HumanLabelAdjudication` contract reconstructs and validates
the complete disagreement partition. Common labels may not disappear, every
disputed candidate must be accounted for exactly once, and all resolved labels
must exist in the final adjudicated set.

## Local span verification

The importer does not trust a returned `content_hash` merely because its JSON ID
is internally consistent. For every imported source and final label set it:

1. resolves the matching corpus descriptor from the rebuilt evidence pack;
2. re-verifies the current document bytes and revision;
3. reads the local UTF-8 source;
4. checks each exact `SourceSpan` offset and content hash;
5. creates a fresh `HumanLabelSetVerificationReceipt`.

A changed document, forged span hash, stale revision, foreign descriptor, or
out-of-range offset prevents readiness.

## Readiness progression

With no returns, a verified pack remains:

```text
awaiting_annotation
```

After some but not all assigned annotation submissions:

```text
awaiting_annotation
```

After all independent annotations and before adjudication:

```text
awaiting_adjudication
```

After a valid adjudication and fresh local verification of every source and final
label set:

```text
ready_for_benchmark
```

The importer writes explicit blockers through the existing RDR-16 report. It does
not silently omit bad or missing submissions.

## CLI

```bash
python scripts/import_reader_evidence.py \
  --root /secure/titan-reader-evidence \
  --spec /secure/titan-reader-evidence/evidence-spec.json \
  --submission-dir /secure/titan-reader-evidence/returns \
  --output /secure/titan-reader-evidence/artifacts/readiness.json
```

`--require-ready` returns exit code `3` when any case is incomplete. The
readiness bundle is still written so automation can inspect exact stages and
blockers.

Exit code `2` means malformed, stale, foreign, unverifiable, or unreadable
input. Exit code `0` means the import itself succeeded; without
`--require-ready`, it does not imply complete evidence.

The summary always reports:

```text
benchmark_executed = false
live_integration_authorized = false
```

## Security properties

1. A packet cannot be answered by another annotator.
2. A submission from another evidence plan is rejected.
3. Duplicate packet and case submissions are rejected.
4. Adjudication cannot reference missing source label sets.
5. Annotator and adjudicator rosters must match exactly.
6. All content identities are reconstructed and checked.
7. All label spans are verified against local source bytes.
8. Non-JSON return-directory contents are not ignored.
9. No provider, network, scheduler, `/query`, memory, Canon, graph, tool,
   TruthGate, Write Gate, Crystal, or Native Kernel path is used.

## Next operational step

When the readiness report is fully green, the operator may build RDR-14 local
benchmark cases from the adjudicated gold label sets and run the explicit local
pipeline twice per case. That benchmark remains a separate action and produces
performance evidence, not automatic promotion.
