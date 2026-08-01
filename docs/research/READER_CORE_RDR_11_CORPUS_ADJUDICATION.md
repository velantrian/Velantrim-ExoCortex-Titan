# PR-RDR-11 — Verifiable corpus packages and human-label adjudication

Status: **evaluation-data foundation**

Boundary:

```text
LOCAL_FILES_ONLY
NO_RAW_TEXT_IN_LABELS_OR_RECEIPTS
RIGHTS_AND_PRIVACY_METADATA_REQUIRED
INDEPENDENT_ANNOTATORS_REQUIRED
ALL_DISAGREEMENTS_EXPLICITLY_RESOLVED
NO_MODEL_EXECUTION
NO_QUERY_WIRING
NO_MEMORY_OR_CANON_WRITE
NO_LIVE_AUTHORIZATION
```

## Purpose

PR-RDR-09 defines evaluation metrics. PR-RDR-10 executes those metrics over
explicit observations. PR-RDR-11 defines how real and human-labelled corpus
evidence can be prepared without quietly treating one annotator, an unchecked
file, or a copyrighted text dump as a trustworthy gold standard.

```text
local document
  -> content-addressed descriptor
  -> file/hash/path verification
  -> independent label set A
  -> independent label set B
  -> explicit disagreement partition
  -> independent adjudicator
  -> adjudicated label set
  -> human-labelled EvaluationCorpusManifest
```

## Corpus document descriptors

`CorpusDocumentDescriptor` stores only metadata:

- stable document ID;
- normalized relative POSIX path;
- exact SHA-256 source revision;
- byte and Unicode character counts;
- media type;
- usage basis;
- rights reference;
- privacy class;
- redistribution permission.

Raw document text is not embedded in the descriptor.

Supported usage bases:

- `synthetic`;
- `owned`;
- `public_domain`;
- `permissive_license`;
- `authorized_private`.

Authorized-private and sensitive documents cannot be marked redistributable.
The contract records the asserted legal/operational basis; it does not make a
legal determination on behalf of the operator.

## Path and content verification

Corpus paths must:

- be normalized relative POSIX paths;
- contain no `..`, absolute path, backslash, or empty component;
- remain under the selected corpus root after resolution;
- traverse no symbolic link;
- resolve to a regular file.

Documents must be valid UTF-8. Verification recomputes:

- SHA-256;
- byte size;
- Unicode code-point count.

The descriptor uses the SHA-256 digest itself as `source_revision`, preventing
a friendly revision name from hiding changed bytes.

## Span-only human labels

Labels contain IDs, enum categories, cross-references and `SourceSpan` values.
They do not copy claim sentences or exception text into labels, receipts, logs,
or content identities.

Four label types are defined:

- `HumanClaimLabel`;
- `HumanExceptionLabel`;
- `HumanRelationLabel`;
- `HumanQualifierLabel`.

Every span must match the document ID and exact source revision. Executable
verification checks each span hash against the local document before the label
set is accepted as verified evidence.

## Independent label sets

A `HumanLabelSet` identifies:

- pseudonymous annotator ID;
- guideline version;
- label version;
- exact document descriptor;
- role: `annotator` or `adjudicated`;
- canonical claims, exceptions, relations and qualifiers.

Relations, qualifiers and exceptions must reference claims from the same label
set. Cross-document or stale-revision references fail closed.

Annotator IDs are identifiers, not identity proof. Workforce controls,
conflict-of-interest checks and access management remain operational duties.

## Adjudication

`HumanLabelAdjudication` requires at least two source label sets with:

- distinct annotator IDs;
- identical document and revision;
- identical guideline and label versions;
- annotator role.

The adjudicator must have a different ID from every source annotator. The final
label set must have the adjudicated role and use the adjudicator ID.

Agreement is exact content-addressed label-ID agreement. For each label kind:

```text
common labels   = intersection(all source label sets)
disputed labels = union(all source label sets) - common labels
```

Common labels must remain in the final set. Every disputed label must appear in
exactly one `AdjudicationResolution`. Every non-common final label must be the
output of exactly one resolution. A resolution may:

- retain one candidate;
- retain several candidates;
- replace candidates with a newly merged final label;
- reject all candidates by producing no resolved label.

There is no implicit majority vote, automatic confidence averaging, or silent
dropping of disagreements.

## Evaluation manifest bridge

`HumanLabelEvaluationManifestBuilder` converts only fully adjudicated packages
into the existing PR-RDR-09 `EvaluationCorpusManifest`.

For each document it derives:

- claim count;
- claim source-span count;
- exception count;
- relation count;
- contradiction count;
- qualifier count;
- `human_labelled` corpus kind.

Every corpus document must have exactly one adjudication. Partial package
coverage is rejected.

## Security and privacy properties

1. Labels and receipts do not embed raw document text.
2. Source changes invalidate descriptor and span verification.
3. Path traversal and symlink traversal are rejected.
4. Private/sensitive redistribution contradictions are rejected.
5. Cross-revision labels are rejected.
6. Independent annotators and an independent adjudicator are required by ID.
7. Every disagreement is accounted for exactly once.
8. Gold labels remain evaluation evidence, not Canon or memory facts.

## Authored fixture

The committed test document is project-authored synthetic text:

- `tests/fixtures/reader_core/rdr_11_synthetic_document.txt`

No third-party book, article, policy, manual, or private document is added by
this PR.

## Still outside PR-RDR-11

- acquiring and approving real documents;
- legal review of actual licenses or permissions;
- secure storage for private corpora;
- annotator user interface;
- blind assignment and workforce identity proof;
- inter-annotator agreement statistics;
- an isolated adapter that executes Reader Core and scores predictions;
- benchmark runs on real/human-labelled packages;
- public-key signatures or transparency logs;
- Operator promotion decision;
- shadow, canary, or live integration.
