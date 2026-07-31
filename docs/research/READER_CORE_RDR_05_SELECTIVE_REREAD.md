# Reader Core PR-RDR-05 — Selective ReRead

Status: `RESEARCH / SHADOW_FOUNDATION / DETERMINISTIC_ONLY / NO_RUNTIME_AUTHORITY`

## Purpose

PR-RDR-05 turns exact gaps already recorded by `CoverageMap` into a bounded,
deduplicated proposal queue for additional reading work.

It does **not** execute a Reader, schedule background work, call a model, write to
memory, invoke TruthGate, call Write Gate, or grant authority to any candidate.

```text
CoverageMap gaps
      +
critical-exception candidates
      +
explicit reread budget
      ↓
SelectiveReReadPlanner
      ↓
queued ReReadTask[] + explicit DeferredReReadItem[]
```

## Core invariants

1. **Selective, not fixed-pass** — there is no mandatory second or fifth pass.
2. **One unit, one proposal** — multiple triggers for one reading unit are merged.
3. **Source linked** — every task points to the exact original source span.
4. **Bounded** — task count, task size, total characters, and tasks per section are hard limits.
5. **No silent loss** — every triggered unit is either queued or explicitly deferred.
6. **Fail closed** — unknown coverage reasons, stale revisions, foreign plans, or mismatched candidate sets are rejected.
7. **Proposal only** — the plan has no scheduling, execution, memory, Canon, policy, tool, or kernel authority.
8. **Deterministic identity** — task, deferred-item, and plan IDs are derived from canonical content.

## Trigger model

The deterministic planner currently recognizes:

| Trigger | Proposed action | Default priority |
|---|---|---|
| missing section card | read unit | high |
| missing claim provenance | read unit | high |
| missing exception scan | rescan exceptions | normal |
| partial Reader result | deepen unit | high |
| unresolved exception target | resolve target relation | critical |
| atomic asset exceeds normal budget | inspect atomic asset | high |

A trigger is evidence that more work may be useful. It is not proof that the
source is wrong, incomplete, or misunderstood.

## Deduplication

Triggers are grouped by `unit_id`. The resulting task contains:

- the strongest priority;
- the union of actions in canonical enum order;
- the union of trigger codes in canonical enum order;
- all exact evidence references;
- one source span matching the original reading unit.

This prevents three gaps on one unit from becoming three redundant rereads.

## Budget and deferral

`SelectiveReReadBudget` limits:

- maximum queued tasks;
- maximum total queued source characters;
- maximum characters in one task;
- maximum tasks from one section.

When a proposal cannot be admitted, it becomes a `DeferredReReadItem` with an
explicit reason:

- task character limit;
- total character limit;
- task count limit;
- section task limit.

Deferral is visible state, not dropped work.

## Reader mode

Tasks that require reading carry an explicit Reader mode:

- ordinary missing-card or missing-provenance work uses the normal bounded mode;
- a `PARTIAL` Reader result requests a deeper mode;
- pure exception-target resolution or asset inspection may not require a Reader mode.

The plan only records this request. A future `ReadingSession` owns execution and
must still enforce its own budgets and policies.

## Input integrity

The planner requires exact agreement across:

- `RawSource.document_id` and derived or declared source revision;
- `HierarchicalSectionPlan.document_id`, revision, structure map ID, and plan ID;
- `CoverageMap.document_id`, revision, structure map ID, and plan ID;
- every unresolved region and unsupported asset;
- every supplied critical-exception candidate.

Candidate IDs supplied to the planner must equal the candidate IDs recorded by
the `CoverageMap`; partial or foreign candidate sets are rejected.

## Output integrity

`SelectiveReReadPlan` verifies that:

- queue indices are consecutive from zero;
- task IDs and deferred IDs are unique;
- at most one task exists per unit;
- no unit is both queued and deferred;
- every triggered unit is represented;
- all task and deferred identities match the same document, revision, structure map, reading plan, and coverage map;
- queued character accounting exactly matches source spans;
- all budget limits hold;
- the plan ID matches canonical plan content.

## Non-goals

PR-RDR-05 intentionally does not provide:

- an execution loop;
- retry scheduling;
- a background queue;
- persistence;
- global synthesis;
- cross-section relation discovery;
- model selection;
- confidence or truth scoring;
- automatic memory admission;
- `/query` integration;
- Native Kernel integration.

Those boundaries keep the deterministic planning layer small and auditable.

## Tests

Executable tests cover:

- merging several triggers into one unit task;
- deeper reread mode for `PARTIAL` Reader output;
- unresolved exception target priority;
- explicit oversized-asset deferral;
- section-level and global budgets;
- empty plans without fabricated full-document rereads;
- stale source and foreign-plan rejection;
- candidate-set mismatch rejection;
- self-verifying task, deferred-item, and plan identities.

## Next stage

PR-RDR-06 should add cross-section relation candidates and a measurable relation
denominator. Selective reread can then consume unresolved relation regions
without changing the authority boundary described here.
