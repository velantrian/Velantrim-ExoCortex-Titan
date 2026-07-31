# 📚 Reader Core — Long-Document Understanding Architecture

**Status:** `RESEARCH / PROPOSED / DOCS_ONLY / NO_RUNTIME_AUTHORITY`  
**Date:** 2026-07-31  
**Repository:** `velantrian/Velantrim-ExoCortex-Titan`  
**Implementation rule:** only merged code and executable checks count as implementation.

## Purpose

Titan already has a source-grounded Semantic Reader foundation, but it does not yet provide a complete book-level reading loop. This document defines the next architecture track for reading books, articles, reports and large document sets progressively instead of relying on one oversized context window or one final summary.

The target behavior is deliberately similar to careful human reading:

```text
source
→ orient to structure
→ read bounded sections
→ make local notes
→ preserve important details and quotations
→ connect distant sections
→ identify omissions and uncertainty
→ selectively reread weak areas
→ produce a source-linked global synthesis
```

Reader Core is not a truth authority, memory authority or replacement for the existing retrieval and admission boundaries. It is an orchestrator that produces source-linked interpretation candidates.

## Architectural position

```text
📚 Original document
        ↓
🗺️ DocumentStructureMap
        ↓
✂️ HierarchicalSectionPlanner
        ↓
🧠 existing SemanticReader implementations
        ↓
📝 SectionCards
        ↓
📊 CoverageMap
        ↓
🚨 Exception and relation candidates
        ↓
🔁 SelectiveReReadPlanner
        ↓
🧠 GlobalDocumentSynthesis candidate
        ↓
🌑 replay / shadow evaluation
        ↓
🛡️ WorkingMemoryGate / TruthGate
        ↓
🔐 explicit Write Gate
```

Reader Core remains outside Canon authority. Original source revisions and exact provenance remain the evidence base. Every other view is derived and rebuildable.

## Current implementation reality

### ✅ Already present in merged Titan code

- provider-neutral `SemanticReader` contract;
- immutable `RawSource` with document identity and revision;
- bounded `ReaderBudget`;
- `FAST`, `STANDARD` and `DEEP` reader modes;
- structured success, partial and failure results;
- deterministic `ExtractiveReader` with exact source offsets;
- hardened `LlmReaderAdapter` with bounded chunk planning and strict output parsing;
- exact-quote localization and fail-closed ambiguous-quote rejection;
- source-linked `KnowledgeCapsule` and `CapsuleClaim` structures;
- separate extraction confidence and truth confidence concepts in the Reader layer;
- `WorkingMemoryGate`, provenance-preserving `ContextPack`, Guardian and TruthGate boundaries;
- bounded shadow dispatch and replay-oriented evaluation infrastructure;
- adaptive retrieval modes and rebuildable embedding projection contracts;
- default-off feature gating and local-first fallbacks.

### 🟡 Active but not merged

PR #102 (`PR-ARM-03`) contains a shadow-only selective-memory candidate extractor. Its CI and Docker workflows are green, but the PR remains draft and requires later hardening before any memory admission work:

- subject and context identity;
- retention reason;
- prompt-to-memory injection classification;
- safe source-span serialization without raw PII leakage;
- deterministic supersession handling;
- consistent `extraction_confidence` naming.

Reader Core work must remain in separate PRs and must not be mixed into PR #102.

### ❌ Not implemented yet

- book-level `DocumentStructureMap`;
- hierarchy-aware section planning across chapters, appendices, tables and footnotes;
- persistent `SectionCard` notes;
- multi-axis `CoverageMap`;
- explicit critical-exception candidate model;
- cross-section relation candidates;
- selective reread planning;
- resumable `ReadingSession`;
- revision-aware incremental rereading;
- global document synthesis linked back to local cards and source spans;
- long-document evaluation corpus and calibrated performance gates.

## Design principles

### 1. Progressive reading, not one-shot context stuffing

A large context window is an execution resource, not a guarantee of understanding. Reader Core must work section by section, preserve intermediate state and revisit weak areas.

### 2. Original source is evidence

```text
Original source       = evidence
SectionCard           = derived note
CoverageMap           = processing account
Relation graph        = rebuildable projection
Global synthesis      = interpretation candidate
Canon                 = separate admission result
```

### 3. Coverage is not confidence or truth

Coverage answers what was processed and represented. It does not prove correctness, understanding or truth.

```text
Coverage ≠ correctness
Coverage ≠ confidence
Coverage ≠ truth
```

### 4. Adaptive depth

The architecture exposes multiple reading passes, but does not require every pass for every document.

```text
cheap structure scan
→ fast local extraction
→ stop when sufficient
→ targeted semantic reading when needed
→ relation/conflict analysis when triggered
→ selective reread of weak areas
→ global synthesis only when useful
```

### 5. Cheap-first and off the answer critical path

Deep reading must run as a bounded `ReadingSession`. Ordinary user answers must not wait for a full book analysis.

### 6. Untrusted content remains data

Instructions found inside a book, PDF, webpage or attachment never gain instruction authority. They may be described or classified, but cannot control Titan, tools, memory admission or policy.

## Proposed contracts

## 🗺️ `DocumentStructureMap`

Purpose: preserve stable navigation and source boundaries before semantic interpretation.

Suggested fields:

```text
DocumentStructureMap
├── document_id
├── source_revision
├── title
├── authors
├── parser_id / parser_version
├── sections[]
├── non_text_assets[]
├── warnings[]
└── content_hash
```

Each section should include:

```text
DocumentSection
├── section_id
├── parent_section_id
├── order_index
├── heading
├── level
├── start_offset
├── end_offset
├── page_range
├── content_kind
├── previous_section_id
├── next_section_id
└── parser_warnings
```

Structure extraction should be deterministic where the source format permits it. Model-generated structure may only be a proposal and must retain parser/source provenance.

## ✂️ `HierarchicalSectionPlanner`

Purpose: create bounded reading units without discarding document hierarchy.

Required behavior:

- prefer chapter, subsection, paragraph and sentence boundaries;
- retain absolute offsets into the original source;
- identify continuation across budget boundaries;
- keep tables, captions, footnotes and appendices visible as first-class units;
- support overlap only when explicitly versioned and measured;
- report every truncation or unsupported asset;
- produce deterministic unit identity for unchanged source revisions.

## 📝 `SectionCard`

Purpose: act as a source-linked reading note for one section.

```text
SectionCard
├── card_id
├── document_id / source_revision
├── section_id
├── local_essence
├── claims[]
├── definitions[]
├── arguments[]
├── examples[]
├── conditions[]
├── exception_candidates[]
├── uncertainties[]
├── important_quotes[]
├── omitted_questions[]
├── relation_candidates[]
├── source_spans[]
├── reader_identity
├── coverage_receipt
└── warnings[]
```

A card is never evidence by itself. Claims, quotations, conditions and exceptions must link to exact source spans or be marked as inferred interpretations with explicit provenance.

## 🚨 `CriticalExceptionCandidate`

Purpose: prevent rare but decisive limitations from disappearing inside summaries.

Candidate triggers include language equivalent to:

- except;
- only if;
- however;
- unless;
- does not apply to;
- subject to;
- superseded by;
- invalid for version;
- requires manual approval.

Suggested contract:

```text
CriticalExceptionCandidate
├── candidate_id
├── source_span
├── target_claim_refs[]
├── condition
├── candidate_severity
├── extraction_confidence
├── origin_trust
├── instruction_taint
└── validation_status
```

`candidate_severity` is not Canon truth and must not be accepted solely from an LLM.

## 📊 `CoverageMap`

Purpose: expose what Reader Core processed, omitted, linked and validated.

Required independent axes:

```text
CoverageMap
├── structural_coverage
├── claim_coverage
├── exception_coverage
├── relation_coverage
├── table_figure_coverage
├── validation_coverage
├── unresolved_regions[]
├── unsupported_assets[]
└── reread_recommendations[]
```

A single global percentage must not be used as a substitute for these axes.

## 🕸️ `SectionRelationCandidate`

Purpose: represent possible long-range dependencies without granting graph authority.

Initial relation vocabulary:

- supports;
- refines;
- limits;
- exemplifies;
- depends on;
- contradicts;
- supersedes;
- is exception to;
- defines term used by.

Every relation requires source-linked endpoints and a reason code. The relation graph is a disposable projection and can be rebuilt from cards and receipts.

## 🔁 `SelectiveReReadPlanner`

Purpose: allocate deeper reading only where evidence shows a need.

Trigger examples:

- low or uncalibrated coverage;
- unresolved reference or pronoun;
- possible critical exception;
- contradiction candidate;
- unsupported table, figure or footnote;
- synthesis claim without adequate source links;
- question targeting an unread or weakly processed region;
- changed document revision.

The planner proposes reread tasks. It does not control policy, write authority or the user-facing answer path.

## 💾 `ReadingSession`

Purpose: support pause, resume, progress tracking and incremental rereading.

```text
ReadingSession
├── session_id
├── document_id / revision
├── structure_map_id
├── completed_section_ids[]
├── pending_section_ids[]
├── section_card_ids[]
├── bookmarks[]
├── coverage_map_id
├── unresolved_questions[]
├── reread_queue[]
├── synthesis_version
├── resource_budget
├── policy_snapshot_id
├── policy_version
├── capability_lease
└── receipts[]
```

Sessions must be restartable from durable receipts without treating cached projections as authoritative history.

## 🧠 `GlobalDocumentSynthesis`

Purpose: assemble a navigable model of the whole document after local evidence exists.

Suggested outputs:

- central theme;
- author position or narrative arc;
- important concepts and definitions;
- argument or episode sequence;
- decisive examples and quotations;
- exceptions and applicability limits;
- contradictions and unresolved tensions;
- alternative interpretations;
- open questions;
- references to supporting SectionCards and exact source spans.

The synthesis remains an interpretation candidate and cannot directly enter Canon.

## Adaptive reading flow

```text
PASS 0 — deterministic structure and source inventory
        ↓
PASS 1 — fast local extraction
        ↓
quality sufficient? ── yes → checkpoint
        │
        no
        ↓
PASS 2 — targeted semantic reading
        ↓
relations or conflicts detected? ── no → optional synthesis
        │
        yes
        ↓
PASS 3 — relation and contradiction analysis
        ↓
coverage weak or assets unsupported?
        ↓
PASS 4 — selective reread
        ↓
PASS 5 — global synthesis only when requested or justified
```

These are available pass types, not a mandatory five-pass tax on every document.

## Speed and resource contract

### Critical-path rule

```text
user query
→ existing retrieval / policy / TruthGate
→ answer

separate bounded path:
ReadingSession
→ section workers
→ cards / receipts
→ no direct answer or write authority
```

### Required behavior

- default-off integration until evaluated;
- deep reading never blocks an already-computed legacy answer;
- queue saturation delays optional reading work instead of failing the query;
- local deterministic structure and extractive reading are preferred first;
- model calls are reserved for ambiguous or high-value sections;
- independent sections may be processed concurrently within fixed budgets;
- completed unchanged sections are reused;
- revision changes invalidate only affected derived artifacts;
- global synthesis is lazy and versioned;
- CPU, RAM, disk, model tokens and wall time are accounted per session;
- all benchmark claims include environment and model metadata.

### Resource states

Reader projections should support explicit states:

```text
hot   → active session artifacts
warm  → reusable cards and maps
cold  → rebuildable archived projections
stale → source or policy revision changed
```

Metrics should include projection bytes, duplicate payload ratio, rebuild cost, cold-start latency, invalidation lag and canon-to-projection storage ratio.

## Safety and trust contract

Every source-derived object should carry or inherit:

```text
origin_trust
instruction_taint
authority_class
allowed_use
may_influence_answer
may_propose_memory
may_request_tool
may_affect_policy
```

Core invariant:

> Untrusted content may describe instructions but never gains instruction authority.

Additional invariants:

- Reader failure does not become query failure;
- Reader output is not truth;
- model confidence is not truth confidence;
- raw PII is not copied into portable receipts when offsets, hashes or redacted previews are sufficient;
- original sources are immutable by Reader Core;
- every derived projection can be deleted and rebuilt;
- no direct Canon write;
- no direct memory admission;
- no TruthGate bypass;
- no hidden tool execution;
- no automatic graph authority;
- no required remote provider.

## Evaluation strategy

### Corpora

```text
Synthetic corpus
├── hidden exceptions
├── distant contradictions
├── superseded claims
├── ambiguous quotations
├── prompt-injection instructions
├── footnotes and appendices
└── tables with critical conditions

Real corpus
├── articles
├── books
├── technical manuals
├── legal documents
├── scientific papers
├── philosophical works
└── narrative literature

Human-labelled corpus
├── important claims
├── critical exceptions
├── cross-section relations
├── acceptable interpretations
└── important omissions
```

### Metrics

- claim fidelity;
- source-span precision and recall;
- critical-exception recall;
- critical omission rate;
- relation recall;
- false relation rate;
- contradiction-cluster recall;
- orphan claim rate;
- qualifier connectivity;
- unsupported synthesis rate;
- structural, claim, exception, relation and validation coverage calibration;
- p50 and p95 section latency;
- total session wall time;
- CPU, memory, disk and model-token use;
- resume reuse ratio;
- projection rebuild cost;
- query-path latency delta;
- `truth_gate_bypass_count == 0`;
- `query_path_write_count == 0`.

No fixed accuracy, cost-per-book or ROI claim is accepted before reproducible evaluation.

## Ordered implementation plan

### PR-RDR-00 — contracts and fixtures

- freeze names and boundaries;
- define minimal synthetic long-document fixtures;
- add no runtime wiring;
- define performance and safety gates.

### PR-RDR-01 — `DocumentStructureMap`

- deterministic structure contract;
- plain-text and Markdown fixture support first;
- stable section identity and source offsets;
- no model dependency.

### PR-RDR-02 — `HierarchicalSectionPlanner`

- hierarchy-aware bounded sections;
- truncation and continuation receipts;
- deterministic unchanged-input output.

### PR-RDR-03 — `SectionCard`

- build cards from existing `KnowledgeCapsule` outputs;
- preserve exact provenance;
- keep inferred interpretations explicit.

### PR-RDR-04 — exceptions and coverage

- `CriticalExceptionCandidate`;
- multi-axis `CoverageMap`;
- no global confidence number.

### PR-RDR-05 — selective reread

- deterministic trigger rules first;
- bounded reread queue;
- no mandatory repeated full-document passes.

### PR-RDR-06 — relation candidates

- source-linked relation vocabulary;
- contradiction and qualifier preservation;
- rebuildable graph projection only.

### PR-RDR-07 — `ReadingSession`

- pause and resume;
- revision-aware invalidation;
- resource accounting and checkpoints.

### PR-RDR-08 — global synthesis

- source-linked synthesis candidate;
- alternative interpretations and unresolved questions;
- no Canon authority.

### PR-RDR-09 — replay, benchmarks and promotion review

- synthetic, real and human-labelled evaluation;
- compare against existing extractive and retrieval baselines;
- shadow only;
- separate Operator GO for any admission or live-path integration.

## Promotion gates

A Reader Core slice cannot move beyond shadow evaluation unless:

- critical safety counters remain zero;
- source provenance is preserved;
- default-off behavior is compatible;
- query latency does not regress outside approved bounds;
- resource use is measured and bounded;
- erasure and revision invalidation are complete;
- failure is isolated;
- labelled evaluation shows benefit over the simpler baseline;
- rollback is immediate and tested;
- Operator approval is explicit and scoped.

## Explicit non-goals

This track does not claim:

- human-equivalent understanding;
- guaranteed elimination of Lost in the Middle;
- guaranteed discovery of every exception;
- universal five-pass processing;
- a new Action Arbiter;
- a second TruthGate or Write Gate;
- blockchain provenance;
- mandatory GPT or any named provider;
- direct LLM memory writes;
- autonomous Canon mutation;
- production readiness before evidence;
- active Native Kernel integration.

Native Kernel may later serve as a portable event and receipt substrate after its runnable checkpoint is present in its own `main` and a separate integration contract is approved. It is not a current Titan runtime dependency.

## Relationship to PR #102

PR #102 remains an independent selective-memory shadow track. Its green CI proves its current tests and speed-contract checks pass, but does not complete its hardening or grant memory admission authority.

Reader Core documentation may advance now. Runtime implementation should begin only in separate branches and PRs, starting with PR-RDR-00/01, after the selective-memory hardening work can be reviewed without mixing concerns.

## Core rule

```text
Read progressively.
Preserve the original.
Link every important conclusion back to evidence.
Admit nothing automatically.
Measure depth, cost and omissions before promotion.
```
