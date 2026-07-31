# PR-RDR-08 — GlobalDocumentSynthesis

**Boundary:** `SHADOW_FOUNDATION / STRUCTURED_INTERPRETATION_CANDIDATE / NO_CANON_AUTHORITY / NO_RUNTIME_WIRING`

## Purpose

`GlobalDocumentSynthesis` assembles a navigable, source-linked interpretation of
one completed reading session. It is deliberately not a single opaque summary.

```text
completed ReadingSession
├── SectionCards
├── CoverageMap
├── CriticalExceptionCandidates
└── CrossSectionRelationSet
        ↓
explicit structured proposals
        ↓
GlobalDocumentSynthesis candidate
```

The builder performs validation and provenance assembly only. It does not call
an LLM, invent prose, choose a truth, admit memory, write Canon, execute tools,
or change the user-facing answer path.

## Outputs

A synthesis contains:

- a central-theme claim;
- additional source-linked synthesis claims;
- supporting and opposing source claims;
- qualifiers and critical exceptions;
- relation references, including contradictions;
- alternative interpretations;
- unresolved questions;
- exact source spans and originating card/section references;
- source claims that were not represented in the synthesis;
- explicit warnings for unresolved coverage or unsupported assets.

## Proposal versus materialized candidate

Callers provide typed proposals:

- `SynthesisClaimProposal`;
- `AlternativeInterpretationProposal`;
- `UnresolvedQuestionProposal`.

The builder rejects a proposal when:

- a source claim does not exist in the supplied `SectionCards`;
- an exception is not present in the exact `CoverageMap` candidate set;
- a relation is not present in the exact relation set;
- a referenced relation's source and target claims are not both represented;
- an exception does not qualify a referenced claim;
- a central theme is missing or uses the wrong kind;
- an alternative lacks source evidence;
- an unresolved question lacks a source-linked reference.

The builder derives source spans, card IDs, and section IDs from accepted
artifacts. Callers cannot provide a free-floating provenance list.

## Structured synthesis claim

```text
SynthesisClaim
├── synthesis_claim_id
├── proposal_key
├── kind
├── text
├── supporting_claim_ids[]
├── opposing_claim_ids[]
├── exception_candidate_ids[]
├── relation_ids[]
├── source_card_ids[]
├── source_section_ids[]
├── source_spans[]
├── qualifiers[]
├── inference_reason
└── validation_state = UNVALIDATED
```

Every synthesis statement is an interpretation candidate even when all source
references are valid. Provenance validity does not prove that the interpretation
is correct.

## Alternative interpretations

Alternatives are first-class objects rather than prose hidden in a caveat. Each
alternative must point to:

1. one or more materialized synthesis claims;
2. one or more original source claims;
3. exact source spans;
4. a reason explaining the contrast.

The presence of an alternative adds a synthesis warning. It does not silently
lower or average a confidence score; PR-RDR-08 defines no global confidence
number.

## Unresolved questions

Questions preserve uncertainty without turning it into an unsupported answer.
A question may reference synthesis claims, source claims, exception candidates,
or relation candidates. Exact spans are assembled from those references.

```text
unresolved question != synthesis failure
unresolved question != answer
unresolved question = explicit remaining uncertainty
```

## Orphan source claims

After materialization, the builder computes source claims not represented by a
synthesis claim, alternative, or unresolved question. They are stored in
`unsupported_source_claim_ids` and produce the warning:

```text
source_claims_not_represented_in_synthesis
```

The name means “not represented by this synthesis,” not “false” or “unsupported
by the document.” This makes omission measurable and available to PR-RDR-09.

## Session boundary

Synthesis requires a `COMPLETED` `ReadingSession` whose exact references match:

- the supplied `CoverageMap`;
- the supplied `CrossSectionRelationSet`;
- the supplied current-revision `SectionCards`.

PR-RDR-07 can retain explicitly marked old-revision cards after exact-text
reuse. PR-RDR-08 fails closed on those `REUSED_CARD` artifacts until a future
provenance-rebasing contract maps their evidence to the current source revision.
Old provenance is never silently relabelled as current provenance.

## Determinism

- proposals are ordered by stable `proposal_key`;
- source claim, exception, relation, card, and section IDs use canonical order;
- exact source spans are deduplicated and canonically sorted;
- every child object has a content-derived ID;
- the complete synthesis has a content-derived `synthesis_id`;
- input iterable order does not change output identity.

## Invariants

- original sources remain evidence;
- SectionCards remain derived notes;
- relation graphs remain rebuildable projections;
- synthesis remains an interpretation candidate;
- no global understanding or truth score;
- no source claim silently disappears from accounting;
- no direct Canon write;
- no memory admission;
- no TruthGate bypass;
- no Write Gate call;
- no graph authority;
- no model, network, filesystem, scheduler, or tool execution;
- no `/query` or Native Kernel integration.

## Deferred

- provider-backed proposal generation;
- human or validator promotion from `UNVALIDATED`;
- current-revision provenance rebasing for reused cards;
- synthesis version supersession;
- persistence adapter;
- replay corpus and calibrated promotion gates;
- any live answer-path or admission integration.
