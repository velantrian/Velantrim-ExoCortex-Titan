# PR-RDR-03 — Source-Linked SectionCards

**Status:** `IMPLEMENTED_IN_BRANCH / SHADOW_FOUNDATION / NO_RUNTIME_WIRING`  
**Depends on:** PR-RDR-00 contracts, PR-RDR-01 structure, PR-RDR-02 reading units  
**Authority:** `DERIVED / REBUILDABLE / NO_CANON_OR_MEMORY_AUTHORITY`

## Purpose

PR-RDR-03 turns an accepted `SemanticReader` result for one `ReadingUnit` into an immutable `SectionCard`.

A card is a local reading note, not evidence and not truth. Its purpose is to preserve:

- which unit was read;
- which `KnowledgeCapsule` supplied the extraction;
- exact absolute source provenance for every accepted claim;
- local essence, entities, and omitted questions;
- explicit separation between extracted claims and inferred interpretations;
- observable build counts and Reader warnings.

```text
RawSource + ReadingUnit + ReaderResult
        ↓ validate accepted status and source/unit identity
validate or rebase claim spans
        ↓
absolute source-linked SectionCardClaims
        ↓
optional explicitly inferred interpretations
        ↓
SectionCard + SectionCardBuildReceipt
```

## Why coordinate space is explicit

Existing `SemanticReader` implementations receive a `RawSource` and emit `SourceSpan` offsets relative to that supplied text. When a Reader is run on a bounded unit substring, its offsets begin at zero for that unit. When it is run against the full document with a targeted extraction policy, offsets may already be document-absolute.

Silently guessing between these cases would corrupt provenance. PR-RDR-03 therefore requires one explicit mode:

```text
UNIT_LOCAL        → validate against unit substring, then rebase
DOCUMENT_ABSOLUTE → validate against full source and unit boundaries
```

For `UNIT_LOCAL`, every source span is verified against:

```text
source.text[unit.start_offset:unit.end_offset]
```

It is then recreated against the full immutable source with:

```text
absolute_start = unit.start_offset + local_start
absolute_end   = unit.start_offset + local_end
```

For `DOCUMENT_ABSOLUTE`, every span must already fit inside the unit and its hash must verify against the full source.

No invalid, stale, ambiguous, or out-of-unit span is accepted.

## SectionCardClaim

A card claim wraps one rebased `CapsuleClaim` and retains:

- `origin_claim_id` — the claim identity supplied by the original capsule;
- `source_capsule_id` — the capsule from which it came;
- `claim` — a newly validated claim whose spans use absolute document offsets.

The absolute claim receives a deterministic identity derived from its absolute provenance. This is intentional: a unit-local identity must not be reused after its coordinate meaning changes.

Claim text, modality, extraction confidence, truth confidence, qualifiers, uncertainties, applicability conditions, and temporal scope are preserved without reinterpretation.

## Inferred interpretations remain separate

`SectionCardInterpretation` is a separate type with:

- explicit `InterpretationKind`;
- interpretation text;
- one or more exact supporting source spans;
- mandatory `inference_reason`;
- deterministic interpretation identity.

An interpretation is never inserted into `claims`. This prevents a derived conclusion from silently appearing as something directly extracted from the source.

The initial kinds are:

- definition;
- argument;
- example;
- condition;
- uncertainty;
- important quote;
- other.

PR-RDR-03 does not automatically generate interpretations. It only defines and validates the safe boundary for later proposal-producing components.

## SectionCardBuildReceipt

The receipt records observable processing facts:

- original capsule identity;
- Reader status (`SUCCESS` or `PARTIAL`);
- declared coordinate space;
- claim and span counts;
- unique referenced source character count;
- total unit character count;
- omitted-question count;
- Reader-reported capsule coverage score;
- structured Reader warning codes.

### Coverage warning

`KnowledgeCapsule.coverage_score` already exists in the Reader contract. PR-RDR-03 preserves it under the deliberately verbose name:

```text
reader_reported_coverage_score
```

It is not:

- structural coverage;
- claim coverage;
- exception coverage;
- relation coverage;
- validation coverage;
- truth confidence;
- a promotion gate.

The multi-axis `CoverageMap` remains PR-RDR-04. The receipt also records `referenced_source_chars`, but does not convert that count into a claim of understanding.

## Unique referenced-character accounting

Source spans may overlap or repeat. The receipt computes the union of their absolute intervals so characters are not double-counted.

```text
span A: 10..20
span B: 15..25
unique referenced characters = 15
```

This remains a processing count, not a correctness metric.

## Card identity

`card_id` includes:

- schema and builder versions;
- document, revision, structure-map, plan, section, and unit identities;
- exact unit provenance;
- original provider-neutral capsule identity;
- local essence;
- absolute claim identity payloads;
- interpretation identities;
- entities and omitted questions.

Replaceable Reader identity, Reader version, prompt version, timestamps, warning text, and execution timing are excluded. Equivalent accepted meaning and provenance can therefore deduplicate across replaceable Reader implementations, while execution metadata remains visible on the card and receipt.

## Fail-closed rules

A card is rejected when:

- the Reader result is not `SUCCESS` or `PARTIAL`;
- an accepted result lacks a capsule;
- source, unit, or capsule document identities disagree;
- source revision and unit revision disagree;
- the unit source hash does not verify;
- a unit-local span falls outside the unit substring;
- an absolute span falls outside the unit;
- any source-span hash fails verification;
- an interpretation lacks source support or an inference reason.

Reader failure remains Reader failure. It is never converted into an empty or misleading card.

## Safety and authority boundary

SectionCards:

- are derived and rebuildable;
- perform no model or network calls;
- execute no tools;
- persist nothing in this PR;
- are not wired into `/query`;
- cannot write Canon;
- cannot admit memory;
- cannot call or bypass TruthGate or Write Gate;
- do not grant graph, policy, or tool authority;
- treat all source content and Reader output as untrusted data requiring validation.

## Executable checks

`tests/test_section_card.py` verifies:

- unit-local to absolute offset rebasing;
- absolute-span validation;
- source-hash verification;
- preservation of original capsule and claim identities;
- PARTIAL warning-code propagation;
- explicit source-supported interpretations;
- rejection of out-of-unit and invalid-hash spans;
- rejection of failed Reader results;
- provider-neutral card identity;
- immutability and absence of authority-bearing fields.

## Deferred

PR-RDR-03 intentionally does not implement:

- durable SectionCard persistence;
- Reader execution scheduling over plans;
- automatic definition, argument, example, or quotation classification;
- critical-exception extraction — PR-RDR-04;
- multi-axis CoverageMap — PR-RDR-04;
- selective rereading — PR-RDR-05;
- cross-section relations — PR-RDR-06;
- durable ReadingSession orchestration — PR-RDR-07;
- global synthesis — PR-RDR-08;
- promotion thresholds — PR-RDR-09.
