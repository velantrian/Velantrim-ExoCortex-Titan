# PR-RDR-16 — Evidence intake, blind assignment, and readiness

Status: **production-evidence operations foundation**

Boundary:

```text
LOCAL_EVIDENCE_COORDINATION_ONLY
HUMANS_CREATE_LABELS
BLIND_INDEPENDENT_ANNOTATION
INDEPENDENT_ADJUDICATOR
VERIFICATION_REQUIRED
NO_MODEL_EXECUTION
NO_QUERY_WIRING
NO_MEMORY_OR_CANON_WRITE
NO_PROMOTION_AUTHORITY
NO_CRYSTAL_CHANGES
```

## Purpose

PR-RDR-11 defines corpus, label, span-verification, and adjudication contracts.
PR-RDR-16 defines the missing operational layer that answers:

- which immutable documents belong to the evidence program;
- which independent annotators are assigned to each document;
- which independent adjudicator is assigned;
- which exact guideline version and digest apply;
- what information an annotator packet may contain;
- whether a case is waiting for annotation, adjudication, verification, or is
  ready to enter the benchmark executor.

It does not create labels or claim that any real evidence already exists.

## Workflow

```text
CorpusPackageManifest
  -> ReaderEvidenceProgramPlan
  -> blind ReaderAnnotationPacket per annotator
  -> independent HumanLabelSet submissions
  -> ReaderAdjudicationPacket
  -> HumanLabelAdjudication
  -> package and label verification receipts
  -> ReaderEvidenceReadinessReport
  -> READY_FOR_BENCHMARK
```

`READY_FOR_BENCHMARK` only means the evidence inputs are complete enough to run
RDR-14. It is not a quality result, promotion decision, Operator GO, or live
authorization.

## Guideline binding

`ReaderAnnotationGuidelineSpec` binds:

- the public guideline version identifier;
- exact SHA-256 bytes of the guideline document;
- label kinds that annotators must review;
- the minimum independent annotator count.

The initial authored guideline is:

```text
docs/research/READER_CORE_ANNOTATION_GUIDELINE_V1.md
```

Changing any byte produces a different guideline digest and therefore a
different evidence plan ID. Existing label sets remain bound to their recorded
version and cannot silently migrate to a changed protocol.

## Assignment plan

`ReaderEvidenceProgramPlanner.create_plan` requires mappings that exactly cover
every corpus document. Each case has:

- content-addressed corpus descriptor identity;
- deterministic evidence case ID;
- at least two distinct annotator IDs;
- one adjudicator ID distinct from every annotator;
- exact source revision.

Missing documents, surplus mapping entries, duplicate annotators, or an
annotator acting as adjudicator fail closed.

Annotator IDs are pseudonymous workflow identifiers, not proof of real-world
identity. Identity verification, conflicts of interest, compensation, access
control, and workforce governance remain operator responsibilities.

## Blind annotation packets

One `ReaderAnnotationPacket` is generated per assigned annotator. The packet
contains only:

- the recipient annotator ID;
- case, descriptor, document, and revision identity;
- evidence plan and assignment identity;
- guideline identity.

It deliberately omits:

- peer annotator IDs;
- adjudicator identity;
- peer labels;
- model predictions;
- scores and thresholds;
- promotion state.

The contract therefore supports blind distribution without treating a shared
assignment plan as the packet shown to each annotator.

## Adjudication packets

A `ReaderAdjudicationPacket` can be built only after exactly one source label set
exists for every assigned annotator. All source sets must:

- have annotator role;
- match descriptor, document, and source revision;
- use the assigned guideline version;
- use one common label version;
- come from the assigned annotator roster.

The adjudication packet contains source label-set IDs, not raw source text. The
existing RDR-11 `HumanLabelAdjudication` remains responsible for accounting for
every disagreement and producing the final adjudicated set.

## Readiness stages

Each case receives exactly one stage:

1. `awaiting_package_verification`
2. `awaiting_annotation`
3. `awaiting_adjudication`
4. `awaiting_label_verification`
5. `ready_for_benchmark`

The report includes explicit blocker codes such as:

```text
missing_package_verification
missing_annotation:<annotator-id>
missing_adjudication
missing_label_verification:<label-set-id>
```

Unknown label sets, foreign descriptors, unassigned annotators, inconsistent
label versions, wrong guidelines, duplicate adjudications, conflicting
verification receipts, and stale identities are rejected rather than converted
into soft warnings.

## Verification requirements

A case cannot become ready until:

- the corpus package verification receipt exactly covers every descriptor;
- every source annotator label set has a span-verification receipt;
- the final adjudicated label set has a span-verification receipt;
- the adjudication uses exactly the assigned annotators and adjudicator.

Verification receipts remain local evidence artifacts. They do not authorize
execution or promotion.

## Security properties

1. Annotation packets do not disclose peer identities or labels.
2. The adjudicator is distinct from source annotators by contract.
3. Corpus and guideline bytes are content-addressed.
4. Source revision changes invalidate assignments and labels.
5. Partial evidence remains visibly blocked.
6. Failed or missing verification cannot be treated as benchmark-ready.
7. No raw document text is copied into packets or readiness reports.
8. No component invokes a model, provider, network, scheduler, `/query`, memory,
   Canon, graph, TruthGate, Write Gate, Crystal, or Native Kernel.

## Operational next action

After merge, the operator can begin issue #120 with a real rights-cleared corpus:

1. approve document rights and privacy metadata;
2. create and locally verify `CorpusDocumentDescriptor` values;
3. freeze the guideline digest;
4. assign independent annotators and adjudicators;
5. distribute blind packets;
6. collect immutable label sets and verification receipts;
7. adjudicate all disagreements;
8. produce a readiness report;
9. run RDR-14 only for cases marked `ready_for_benchmark`.

Human labour and rights approval cannot be synthesized by this repository. This
PR makes their outputs explicit, auditable, and fail-closed once supplied.
