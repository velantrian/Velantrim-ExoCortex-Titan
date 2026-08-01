# PR-RDR-17 — Local evidence-pack CLI

Status: **operator tooling for production-evidence intake**

Boundary:

```text
LOCAL_FILES_ONLY
EXPLICIT_OPERATOR_SPEC
CONTENT_ADDRESSED_OUTPUTS
BLIND_PACKET_EXPORT
NO_RAW_TEXT_IN_OUTPUTS
NO_UPLOAD
NO_MODEL_EXECUTION
NO_BENCHMARK_EXECUTION
NO_PROMOTION
NO_QUERY_MEMORY_CANON_OR_CRYSTAL_WIRING
```

## Purpose

PR-RDR-16 defines the evidence-program contracts. PR-RDR-17 makes the first
real operational step executable without requiring an operator to write Python.

The command:

```text
scripts/prepare_reader_evidence_pack.py
```

accepts a local root and an explicit JSON source spec. It then:

1. reads each declared corpus file locally;
2. creates content-addressed `CorpusDocumentDescriptor` values;
3. verifies the complete corpus package;
4. hashes the exact annotation guideline bytes;
5. binds annotator and independent adjudicator assignments;
6. creates the RDR-16 evidence plan;
7. creates one blind annotation packet per annotator;
8. writes a canonical operator pack and separate packet JSON files.

The command does not upload documents, inspect email, choose annotators, create
labels, execute Reader Core, run a benchmark, or authorize promotion.

## Source specification

Example:

```json
{
  "schema_version": "reader-core.evidence-source-spec.v1",
  "corpus_name": "titan-reader-evidence-2026q3",
  "corpus_version": "1.0.0",
  "tags": ["long-form", "rights-cleared"],
  "guideline": {
    "guideline_version": "reader-core.annotation-guideline.v1",
    "relative_path": "guidelines/reader-core-v1.md",
    "required_label_kinds": [
      "claim",
      "exception",
      "qualifier",
      "relation"
    ],
    "min_independent_annotators": 2
  },
  "documents": [
    {
      "document_id": "policy-alpha",
      "relative_path": "documents/policy-alpha.txt",
      "media_type": "text/plain; charset=utf-8",
      "usage_basis": "authorized_private",
      "rights_reference": "approval-ticket-1234",
      "privacy_class": "internal",
      "redistribution_allowed": false
    }
  ],
  "assignments": [
    {
      "document_id": "policy-alpha",
      "annotator_ids": ["annotator-001", "annotator-002"],
      "adjudicator_id": "adjudicator-001"
    }
  ]
}
```

Unknown keys are rejected. Assignment document IDs must exactly match document
IDs. Every case requires at least two unique annotators and an adjudicator who is
not one of them.

Paths use POSIX separators, must be relative, and may not contain `..`. Guideline
resolution also rejects symlink or resolved-path escape from the declared root.
Existing RDR-11 document loading verifies UTF-8 decoding and content identity.

## Rights and privacy metadata

Every document requires:

- `usage_basis`;
- `rights_reference`;
- `privacy_class`;
- `redistribution_allowed`.

The CLI does not decide whether a rights reference is legally sufficient. That
approval belongs to the operator. It does enforce mechanical contradictions:

- `authorized_private` cannot be redistributable;
- `sensitive` cannot be redistributable.

Documents are never copied into the generated JSON artifacts. Outputs contain
relative paths, hashes, sizes, identifiers, rights metadata, assignments, and
readiness blockers only.

## Command

```bash
python scripts/prepare_reader_evidence_pack.py \
  --root /secure/titan-reader-evidence \
  --spec /secure/titan-reader-evidence/evidence-spec.json \
  --output /secure/titan-reader-evidence/artifacts/operator-pack.json \
  --packet-dir /secure/titan-reader-evidence/artifacts/annotation-packets
```

The packet directory must not exist or must be empty. This prevents a new
assignment generation from being mixed with stale packets from another plan.
Packet filenames use content-addressed packet IDs rather than annotator names.

The command prints a machine-readable summary containing pack, package, and plan
IDs. It always reports:

```text
production_evidence_complete = false
requires_human_annotation = true
```

Creating packets is not evidence completion.

## Operator pack versus blind packets

The operator pack contains the complete plan, including the full roster. It must
remain access-controlled.

Each annotation packet contains only:

- its recipient annotator ID;
- plan, assignment, case, descriptor, document, and revision IDs;
- guideline ID.

It does not contain peer annotator IDs, adjudicator ID, peer labels, model output,
scores, thresholds, or raw document text.

The corpus document itself and approved annotation tooling must be delivered
through a separate access-controlled process. The packet is identity metadata,
not a transport container for private documents.

## Determinism

With unchanged spec, document bytes, guideline bytes, and assignments, repeated
runs produce identical:

- descriptor IDs;
- package and verification IDs;
- guideline ID;
- evidence plan ID;
- packet IDs;
- readiness report ID;
- pack ID;
- canonical JSON bytes.

Changing a document, guideline, rights declaration, roster, or adjudicator changes
the corresponding content-addressed identities.

## Next operational step

After the pack is created:

1. review rights and privacy metadata;
2. distribute each packet and its permitted document to the named annotator;
3. collect independently frozen `HumanLabelSet` artifacts;
4. verify every source span locally;
5. build the adjudication packet only after all assigned labels arrive;
6. perform independent adjudication;
7. obtain a RDR-16 `READY_FOR_BENCHMARK` report;
8. pass only ready cases to the RDR-14 local benchmark executor.

Neither RDR-16 nor RDR-17 turns readiness into promotion. Signed real benchmark
evidence, shadow burn-in, and explicit Operator GO remain mandatory.
