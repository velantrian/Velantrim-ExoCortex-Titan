# PR-RDR-03 — Source-Linked SectionCards

**Status:** `IMPLEMENTED_IN_BRANCH / SHADOW_FOUNDATION / NO_RUNTIME_WIRING`  
**Depends on:** PR-RDR-00 contracts, PR-RDR-01 structure, PR-RDR-02 reading units  
**Authority:** `DERIVED / REBUILDABLE / NO_CANON_OR_MEMORY_AUTHORITY`

## Purpose

PR-RDR-03 turns an accepted `SemanticReader` result for one `ReadingUnit` into an immutable `SectionCard`.

A card is a local reading note, not evidence and not truth. It preserves:

- the exact unit that was read;
- the `KnowledgeCapsule` and origin claim identities used to build it;
- absolute document provenance for every accepted claim;
- local essence, entities, and omitted questions;
- explicit separation between extracted claims and inferred interpretations;
- observable build counts and structured Reader warnings.

```text
RawSource + ReadingUnit + accepted ReaderResult
        ↓ validate source, revision, unit, and capsule
validate or rebase every claim span
        ↓
absolute source-linked SectionCardClaims
        ↓
optional explicitly inferred interpretations
        ↓
self-verifying SectionCard + build receipt
```

## Coordinate space must be declared

A `SemanticReader` emits offsets relative to the `RawSource` it receives. A Reader run on a unit substring normally emits offsets beginning at zero. A Reader run against the full document may already emit absolute offsets.

Guessing between these cases would corrupt provenance. The builder therefore requires one explicit mode:

```text
UNIT_LOCAL        → verify against the unit substring, then rebase
DOCUMENT_ABSOLUTE → verify against the full source and unit boundaries
```

For `UNIT_LOCAL`:

```text
unit_text      = source.text[unit.start_offset:unit.end_offset]
absolute_start = unit.start_offset + local_start
absolute_end   = unit.start_offset + local_end
```

The original local span hash must verify against `unit_text`. The rebuilt absolute span hash must then derive from the full immutable source.

For `DOCUMENT_ABSOLUTE`, the span must already lie inside the unit and verify against the complete source.

No invalid, stale, ambiguous, or out-of-unit span is accepted.

## Explicit and derived source revisions

When `RawSource.source_revision` is present, it must equal the reading-unit revision. When it is absent, the builder derives the same deterministic revision used by PR-RDR-01 and PR-RDR-02:

```text
sha256:<SHA-256 of exact UTF-8 source text>
```

This allows the original immutable `RawSource` with `source_revision=None` to remain usable throughout the deterministic Reader Core pipeline.

## SectionCardClaim

A card claim contains:

- `origin_claim_id` — identity supplied by the input capsule;
- `source_capsule_id` — capsule that supplied it;
- `claim` — a rebuilt `CapsuleClaim` with absolute document spans.

The absolute claim receives a new deterministic identity based on its absolute provenance. Reusing a unit-local claim ID after changing its coordinate meaning would be unsafe.

Claim text, modality, extraction confidence, truth confidence, qualifiers, uncertainties, applicability conditions, and temporal scope are preserved without reinterpretation.

## Inferred interpretations remain separate

`SectionCardInterpretation` is a different type with:

- an explicit `InterpretationKind`;
- interpretation text;
- one or more exact supporting spans;
- a mandatory `inference_reason`;
- a deterministic content identity.

An interpretation is never inserted into `claims`. The initial kinds are definition, argument, example, condition, uncertainty, important quote, and other.

PR-RDR-03 does not automatically invent interpretations. It defines and validates the safe representation for future proposal-producing components.

## SectionCardBuildReceipt

The receipt records processing facts:

- original capsule identity;
- Reader status (`SUCCESS` or `PARTIAL`);
- declared coordinate space;
- ordered absolute claim IDs;
- claim and span counts;
- unique referenced source-character count;
- total unit-character count;
- omitted-question count;
- Reader-reported capsule coverage score;
- structured Reader warning codes.

The receipt ID is recomputed and verified from these fields. Direct construction cannot silently attach a stale receipt ID to altered counts.

The `SectionCard` then checks that receipt claim IDs, counts, source-span totals, referenced-character totals, unit length, omitted-question count, and capsule identity all match the actual card content.

## Coverage boundary

The existing `KnowledgeCapsule.coverage_score` is preserved only as:

```text
reader_reported_coverage_score
```

It is not structural, claim, exception, relation, table, or validation coverage. It is not truth confidence and not a promotion gate. The multi-axis `CoverageMap` remains PR-RDR-04.

`referenced_source_chars` is also only an observable count. Overlapping intervals are merged before counting:

```text
span A: 10..20
span B: 15..25
unique referenced characters = 15
```

This does not claim that the referenced text was understood correctly.

## Card identity

`card_id` includes the final normalized card meaning and absolute provenance:

- schema and builder versions;
- document, revision, structure-map, plan, section, and unit identities;
- exact unit span;
- local essence;
- absolute claim identity payloads;
- interpretation identities;
- entities and omitted questions.

It deliberately excludes:

- Reader identity and version;
- prompt version;
- timestamps and execution timing;
- warning text;
- input coordinate mode;
- original capsule ID.

The original capsule remains visible in each claim wrapper and in the build receipt. Excluding it from semantic card identity means `UNIT_LOCAL` and `DOCUMENT_ABSOLUTE` executions that resolve to identical absolute claims produce the same `card_id`, while their execution receipts remain distinct.

The card recomputes its own ID during validation. Changing card content while retaining an old ID fails closed.

## Fail-closed rules

A card is rejected when:

- the Reader result is not `SUCCESS` or `PARTIAL`;
- an accepted result lacks a capsule;
- source, unit, or capsule identities disagree;
- explicit or derived source revisions disagree;
- the unit source span does not verify;
- a local span falls outside the unit substring;
- an absolute span falls outside the unit;
- any span hash fails verification;
- an interpretation lacks support or an inference reason;
- interpretation, receipt, or card IDs do not match their content;
- receipt counts do not match actual card content.

Reader failure remains Reader failure. It never becomes an empty or misleading card.

## Safety and authority boundary

SectionCards:

- are derived and rebuildable;
- perform no model or network calls;
- execute no tools;
- persist nothing in this PR;
- are not wired into `/query`;
- cannot write Canon or admit memory;
- cannot call or bypass TruthGate or Write Gate;
- grant no graph, policy, or tool authority;
- treat source content and Reader output as untrusted data requiring validation.

## Executable checks

`tests/test_section_card.py` and `tests/test_section_card_hardening.py` verify:

- unit-local to absolute rebasing;
- absolute-span validation and source-hash checks;
- PARTIAL warning propagation;
- explicit source-supported interpretations;
- rejection of out-of-unit and invalid-hash spans;
- rejection of failed Reader results;
- provider-neutral card identity;
- derived source revisions;
- coordinate-space-neutral semantic identity;
- forged interpretation, receipt, and card ID rejection;
- immutability and absence of authority-bearing fields.

## Deferred

PR-RDR-03 intentionally does not implement:

- durable SectionCard persistence;
- Reader execution scheduling over plans;
- automatic definition, argument, example, or quotation classification;
- critical-exception extraction and multi-axis CoverageMap — PR-RDR-04;
- selective rereading — PR-RDR-05;
- cross-section relations — PR-RDR-06;
- durable ReadingSession orchestration — PR-RDR-07;
- global synthesis — PR-RDR-08;
- promotion thresholds — PR-RDR-09.
