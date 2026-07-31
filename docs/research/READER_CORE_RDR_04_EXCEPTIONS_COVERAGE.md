# PR-RDR-04 — Critical Exception Signals and Multi-Axis CoverageMap

**Status:** `IMPLEMENTED_IN_BRANCH / SHADOW_FOUNDATION / NO_RUNTIME_WIRING`  
**Depends on:** PR-RDR-00 through PR-RDR-03  
**Authority:** `DERIVED / REBUILDABLE / NO_CANON_OR_MEMORY_AUTHORITY`

## Purpose

PR-RDR-04 introduces two related but deliberately separate capabilities:

1. deterministic source-linked signals that may represent critical exceptions, limitations, conditions, or supersession;
2. independent coverage axes that report observable processing state without claiming correctness or understanding.

```text
RawSource + validated SectionCard
        ↓
DeterministicCriticalExceptionScanner
        ↓
CriticalExceptionCandidates + ExceptionScanReceipt

RawSource + DocumentStructureMap + HierarchicalSectionPlan
          + SectionCards + ExceptionScanResults
        ↓
CoverageMapBuilder
        ↓
6 independent CoverageAxisReceipts
+ unresolved source regions
+ unsupported atomic assets
```

Neither path writes memory, Canon, policy, a graph, or the live answer path.

---

# Part I — Critical exception signals

## Candidate, not conclusion

A lexical match such as `unless` is evidence that a region deserves attention. It is not proof that the sentence legally, scientifically, or logically overrides another claim.

Every scanner output therefore has:

```text
validation_status = UNVALIDATED
```

The scanner never emits `CONFIRMED`. Confirmation and rejection are reserved for later deterministic validators, replay evaluation, or explicit human review.

## Initial signal vocabulary

The deterministic scanner recognizes bounded, case-insensitive forms corresponding to:

- `unless`;
- `only if`;
- `provided that`;
- `except` / `except for`;
- `does not apply to`;
- `but not`;
- `however`;
- `subject to`;
- `superseded by`;
- `is/are/was/were invalid for version(s)`;
- `require(s) manual approval`.

The categories are:

```text
CONDITION
EXCLUSION
CONTRAST
SCOPE_LIMITATION
SUPERSESSION
VERSION_LIMITATION
APPROVAL_REQUIREMENT
```

This vocabulary is intentionally small and versioned. Adding a phrase changes scanner behavior and therefore requires a scanner-version change, fixtures, and evaluation.

## Exact provenance

Each `CriticalExceptionCandidate` carries two different spans:

- `trigger_span` — exact bytes-as-Unicode-code-points corresponding to the matched signal phrase;
- `statement_span` — the bounded sentence or line containing the signal.

Both spans:

- use absolute document coordinates;
- carry document identity and source revision;
- carry exact SHA-256 content hashes;
- must fit inside the scanned SectionCard unit;
- must verify against the immutable source before CoverageMap admission.

The candidate also stores the exact `trigger_phrase` and `statement_text`. CoverageMap validation checks that these strings equal the current source slices; a valid span hash cannot be paired with altered display text.

## Target claim linking

The scanner attempts conservative claim linkage in this order:

1. card claims whose source spans overlap the candidate statement;
2. otherwise, the nearest preceding card claim inside the configured character window;
3. otherwise, no target claim and warning `unresolved_target_claim`.

Target references point to the **absolute claim identities inside the SectionCard**, not to local pre-rebase capsule IDs.

This is still only candidate linkage. A nearby claim may not be the true semantic target.

## Scan receipt

A complete scan produces an `ExceptionScanReceipt` even when it finds zero signals. This distinction is essential:

```text
zero candidates + receipt  = scanned, no configured signal found
zero candidates + no receipt = not scanned / unknown
```

The receipt identifies:

- scanner version;
- card and unit;
- full scanned unit span;
- exact candidate IDs;
- trigger count;
- warnings.

Receipt and candidate identities are self-verifying.

## Known limitations

The scanner does not yet understand:

- implicit exceptions without trigger phrases;
- negation scope across several sentences;
- legal cross-references;
- mathematical domains and quantifiers;
- exceptions encoded only in tables or figures;
- sarcasm, narrative reversal, or rhetorical contrast;
- whether `however` is actually decisive;
- exception-to-exception chains.

Therefore candidate count must never be reported as exception recall.

---

# Part II — CoverageMap

## No global score

`CoverageMap` has exactly six independent axes and intentionally has no `global_score`, `overall_coverage`, or `understanding_percentage`.

```text
Coverage ≠ correctness
Coverage ≠ confidence
Coverage ≠ understanding
Coverage ≠ truth
Coverage ≠ Canon admission
```

Every axis contains:

- `measure_kind`;
- `processed_count`;
- `denominator_count` or `None`;
- `basis_code`;
- unresolved IDs;
- warnings;
- an independently self-verifying receipt ID.

`ratio` is returned only when a non-empty denominator is known. A denominator of `None` or zero produces `ratio=None`.

## Structural axis

```text
measure: reading units
numerator: plan units with one validated SectionCard
denominator: all plan units
```

Missing cards produce exact `missing_section_card` unresolved regions.

A structural ratio of `1.0` means every planned unit has a card. It does not mean every idea was extracted correctly.

## Claim axis

```text
measure: non-whitespace source characters
numerator: unique characters linked by absolute card-claim spans
denominator: non-whitespace characters in the source
```

Overlapping claim spans are merged before counting.

This axis is a **provenance footprint**, not claim recall. A short but decisive statement may yield a low ratio and still be important. A verbose extraction may yield a larger ratio without being more correct.

The receipt always carries warning:

```text
claim_axis_is_provenance_footprint_not_claim_recall
```

## Exception axis

```text
measure: reading units
numerator: units with an ExceptionScanReceipt
denominator: all plan units
```

This distinguishes a completed zero-match scan from an unscanned region.

It measures scan execution coverage, not semantic exception recall. Missing scans produce exact `exception_scan_missing` regions.

## Relation axis

PR-RDR-04 does not implement cross-section relation analysis. Therefore:

```text
processed_count = 0
denominator_count = None
ratio = None
basis = relation_analysis_not_implemented
```

Returning zero percent here would be misleading because the relation population is unknown. The axis remains unknown until PR-RDR-06.

## Table/figure axis

```text
measure: table, figure, or caption reading units
numerator: those units with SectionCards
denominator: all such units identified by DocumentStructureMap
```

When no table/figure/caption units exist, the denominator is zero and ratio remains `None`, accompanied by `no_table_figure_assets_in_structure`.

## Validation axis

```text
measure: emitted card-claim SourceSpans
numerator: spans whose content hashes verify against the source
denominator: all emitted card-claim spans
```

This axis covers emitted provenance only. It cannot detect a claim that should have been extracted but was omitted. Missing cards are represented by structural and claim axes instead.

A card produced from a `PARTIAL` ReaderResult creates a `partial_reader_result` unresolved validation region even when its emitted spans verify correctly.

## Unresolved regions

Coverage gaps are represented as exact `UnresolvedCoverageRegion` objects linked to reading-unit source spans. Initial reason codes include:

- `missing_section_card`;
- `unread_unit_has_no_claim_provenance`;
- `exception_scan_missing`;
- `partial_reader_result`.

These regions provide deterministic inputs for PR-RDR-05 selective rereading.

## Unsupported atomic assets

PR-RDR-02 preserves atomic tables, figures, captions, footnotes, and code instead of silently cutting them. When such a unit exceeds the normal budget, PR-RDR-04 exposes an `UnsupportedAssetRegion` with:

```text
reason_code = atomic_section_exceeds_budget
```

The asset remains source-linked and intact. Coverage reports the resource limitation rather than pretending the budget was satisfied.

## Canonical order and deterministic identity

Input iterables may arrive in arbitrary order. `CoverageMapBuilder` canonicalizes cards and exception scans by plan-unit order before producing IDs.

Equivalent sets of cards and scans therefore produce the same:

- card ID sequence;
- scan receipt sequence;
- candidate sequence;
- CoverageMap identity.

The map identity includes axis receipt IDs, ordered artifact IDs, unresolved-region IDs, unsupported-asset IDs, and warnings. Directly changing content while retaining a stale ID fails closed.

## Input validation

Coverage construction rejects:

- source, structure, or plan revision/hash disagreement;
- duplicate cards or multiple cards for one unit;
- cards outside the plan;
- scans without a matching card and plan unit;
- duplicate scans or candidate IDs;
- candidates outside their unit;
- trigger or statement spans whose hashes fail;
- trigger phrases or statement text that differ from source slices;
- target claim references not present in the candidate's card.

## Safety boundary

PR-RDR-04:

- uses deterministic standard-library operations only;
- performs no model or network calls;
- executes no tools;
- persists nothing;
- is not wired into `/query`;
- cannot write Canon or memory;
- cannot call or bypass TruthGate or Write Gate;
- does not promote candidates into facts;
- does not grant graph, policy, or tool authority.

## Executable checks

Tests verify:

- exact exception trigger and statement spans;
- candidate categories and target-claim linkage;
- unresolved target handling;
- zero-match scan receipts;
- deterministic and self-verifying IDs;
- stale-source rejection;
- independent coverage denominators and ratios;
- unknown relation coverage;
- missing-unit unresolved regions;
- claim provenance-footprint accounting;
- partial ReaderResult reporting;
- input-order-independent CoverageMap identity;
- atomic oversized asset reporting;
- rejection of scans without cards;
- stale CoverageMap identity rejection.

## Deferred

PR-RDR-04 intentionally does not implement:

- semantic or human confirmation of exception candidates;
- calibrated exception recall thresholds;
- automatic severity assignment;
- exception-to-exception graphs;
- selective reread prioritization — PR-RDR-05;
- cross-section relations — PR-RDR-06;
- durable sessions — PR-RDR-07;
- global synthesis — PR-RDR-08;
- real-corpus promotion gates — PR-RDR-09.
