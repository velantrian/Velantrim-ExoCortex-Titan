# ADR — 2026-08-22 — Bounded Reader Product Pipeline

## Status

`PROPOSED IN PR #374 · POST-V1 · GITHUB_AND_NOTION · NO RUNTIME AUTHORITY`

## Context

Titan already contains the major Reader Core primitives for progressive long-document reading: deterministic structure parsing, hierarchy-aware reading units, provider-neutral `SemanticReader`, source-linked `SectionCard`, multi-axis `CoverageMap`, selective reread planning, resumable `ReadingSession` contracts, relation sets and source-linked `GlobalDocumentSynthesis` candidates.

Separately, Titan V1 already exposes an ordinary-user file ingest helper. That helper intentionally feeds extracted file text into the governed `/ingest/text` memory/write path. Reusing it for Reader Core would conflate document reading with memory admission.

The missing product seam is therefore orchestration, not a new Reader architecture.

## Decision

Add one explicit foreground `ReaderProductPipeline` and one CLI, `scripts/read_document.py`, that compose the existing Reader Core directly from `FileIngester` output.

The product path is:

```text
local file
→ FileIngester
→ RawSource
→ existing Reader Core primitives
→ source-grounded read-side result
```

It does **not** pass through `/ingest/text` and does not perform any memory/Canon write.

### Bounded execution

One invocation performs:

1. deterministic structure extraction;
2. bounded reading-unit planning;
3. initial SemanticReader pass per unit;
4. SectionCard materialization only for accepted source-linked results;
5. deterministic exception scan and CoverageMap;
6. one SelectiveReReadPlanner pass;
7. at most one explicit reread attempt for each queued task that already carries a planner-assigned `ReaderMode` within the existing reread budget;
8. non-reader tasks with `reader_mode=None` remain explicit open work and are never coerced into a hidden `DEEP` or other model call;
9. final coverage reconstruction;
10. ReadingSession completion only when every reading unit has a valid card;
11. source-linked synthesis only for a completed reading session.

If any reading unit remains unresolved, the session becomes `DEGRADED`; global synthesis is skipped and remaining work stays explicit.

The product-facing CLI further distinguishes `COMPLETE`, `COMPLETE_WITH_OPEN_WORK`, and `DEGRADED`. `COMPLETE_WITH_OPEN_WORK` means all reading units were processed but explicit reread/deferred follow-up remains. This does not redefine the RDR-07 session state; it prevents a completed reading-unit state from being presented as proof that every exception or follow-up action is resolved.

## Synthesis policy

PR #374 does not add a second free-form LLM synthesis surface.

The product-facing digest is deterministically assembled from accepted `SectionCard.local_essence` values, whose upstream LLM adapter admits only exact source-linked claims. `GlobalDocumentSynthesis` remains an `UNVALIDATED` interpretation candidate backed by those claims.

This is intentionally conservative. Fluent semantic abstraction can be proposed later only with an explicit provenance/admission contract rather than silently widening model authority.

## Relation policy

The existing relation-set contract is reused, but v1 does not invent cross-section relations automatically. A valid empty evaluated relation projection is attached so the synthesis contract remains coherent without introducing an unreviewed detector.

## Authority and safety boundary

This decision adds no:

- Canon or memory write;
- TruthGate / Write Gate call;
- ESM transition;
- graph authority;
- provider bypass;
- scheduler, worker or background loop;
- durable ReadingSession persistence;
- automatic retry beyond the single bounded selective-reread round;
- canary/live/production authorization;
- Crystal or Native Kernel integration.

`Reader result != truth`, `synthesis != fact`, and `successful pipeline execution != production evidence` remain invariant.

## Alternatives rejected

### Route files through `/ingest/text` first

Rejected because it would make the memory/write path a prerequisite for reading and blur extraction vs epistemic admission.

### Build a second book-reader subsystem

Rejected because existing Reader Core already owns the required primitives. The missing layer is orchestration.

### Add an autonomous background reader

Rejected for this stage. It introduces lifecycle, scheduling, persistence and operational authority that are unnecessary for the explicit user command.

### Let an LLM produce unconstrained final prose

Deferred. Existing `LlmReaderAdapter` deliberately restricts trusted model contribution to exact source quotes + modality. PR #374 preserves that boundary.

## Evidence and completion

PR #374 remains Draft until:

- focused tests and repository CI are green on the exact head;
- documentation accurately reflects candidate status and limitations;
- existing `Velantrim Titan 9.0` Notion record is synchronized/read back;
- review finds no authority expansion, hidden write path, or hidden provider call for non-reader work.

This ADR does not close Issue #120. Production Reader evidence remains externally blocked on real corpora, independent adjudicated labels, benchmark/calibration, shadow burn-in and explicit operator decision.
