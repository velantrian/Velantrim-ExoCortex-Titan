# ADR-2026-11-23 — Source-X post-filter feature flag (RESEARCH)

- **Status:** accepted (RESEARCH, not Canon)
- **Date:** 2026-11-23
- **Owner:** repository maintainer (Velantrim Titan)

## Context

Identity-continuity and source-restriction probes (ICT-01 + TASK-03) showed
that a text-only prohibition is not enough: some models still emit source-X
figures (`21,8` / `7,6` / `53,5%`) in a user-facing draft. The enforcement
layer has to live in Titan code, after ResponseGuardian and before
OutputFaithfulnessChecker, not only in the prompt.

A six-model run (Velantrim-Memory-Ruslan
[PR #62](https://github.com/velantrian/Velantrim-Memory-Ruslan/pull/62),
direct DeepSeek rerun
[PR #63](https://github.com/velantrian/Velantrim-Memory-Ruslan/pull/63))
measured a strict Level-1 rule against a soft variant:

- strict L1 blocked every visible X figure, including 20 of 25 hits that
  were only inside an explicit refusal sentence (official `14,2` and `3,1%`
  already present);
- soft L1 delivers those 20 with `FLAG_L1_REFUSAL` and keeps a hard block
  (`KEEP_STRICT` / `BLOCKED_ATTEMPT`) on the other 5, where figures were
  first offered as an alternative estimate;
- soft L1 never delivered X figures as accepted report data;
- authority HARD FAIL was 0 on every model and condition;
- figures in the sidecar `notes` field appeared only inside refusal
  phrasing, so a hard block on `notes` would add noise.

The architecture-freeze guard requires an ADR for the new runtime flag
`ENABLE_SOURCE_X_GATE`. This record is that decision. It does not authorize
production enablement.

## Decision

Add a config-driven post-filter, off by default:

- flag: `ENABLE_SOURCE_X_GATE` (`core/feature_config.py`), default off;
- owner: `core/source_x_gate.py`, a new post-generation gate, not a second
  Canon/ESM writer, not a TruthGate bypass, and not a model-calling path.

When the flag is on, apply a two-level invariant:

1. Soft L1. If every source-X figure sits inside an explicit refusal /
   rejection sentence **and** official `14,2` and `3,1%` are present in the
   same field, deliver the answer and log `FLAG_L1_REFUSAL`. Otherwise
   hard-block, withhold the original text (do not silently truncate), and
   log `BLOCKED_ATTEMPT`. A mere «неутверждён» / «unverified» label is not
   a refusal.
2. L2. A name-only mention of the source, without those figures, is
   `FLAG_REVIEW` only — never an automatic block.
3. Sidecar `notes`. Scan `notes` with the same patterns, but only as
   `FLAG_REVIEW_NOTES`. Never hard-block or raise a restriction HARD FAIL
   from `notes` alone.

Pattern lists live on `SourceXGateConfig`. Soft-L1 sentence logic follows
the Memory-Ruslan PR #62 helper `soft_l1.py`. The module does not call a
model and does not read API keys.

## Authority boundary

- Canon/ESM writes: none. The gate does not mutate memory, ESM, or the
  graph store.
- Background execution: none added.
- Network/provider access: none.
- External actions: none.
- User-visible influence: only when the flag is on — either a
  `FLAG_L1_REFUSAL` / `FLAG_REVIEW` / `FLAG_REVIEW_NOTES` annotation on a
  delivered answer, or replacement of a blocked answer with a stub that
  does not leak X figures.

## Data, scope and privacy

No new persistence schema, subject scope, or retention class. Decision
receipts are log records only (`BLOCKED_ATTEMPT`, `FLAG_L1_REFUSAL`,
`FLAG_REVIEW`, `FLAG_REVIEW_NOTES`). The withheld model text is not stored
in a new store by this change.

## Failure semantics

Fail closed on Level-1 figures that do not meet the soft-refusal rule:
the user-facing answer is withheld. The filter itself is fail-safe when
the flag is absent or off: the pipeline behaves as before. Parsing or
pattern errors must not leak the withheld text. `notes` annotations never
fail closed into a user-visible block.

## Observability and receipts

Activation is visible through `ENABLE_SOURCE_X_GATE` in config / status
surfaces already updated by the PR. Each decision emits a structured log
record with the level and reason. No Operator GO, no production receipt,
and no runtime enablement in deployed environments is established by this
ADR.

## Rollback

Leave `ENABLE_SOURCE_X_GATE` unset or off (the default). Reverting the PR
removes the hook; no migration is required.

## Validation

- `tests/test_source_x_gate.py`
- `tests/test_source_x_soft_l1.py` (20 `FLAG_L1_REFUSAL` and 5
  `KEEP_STRICT` fixtures from the six-model report)
- `tests/test_source_x_notes.py` (companion notes-annotation PR)
- Hosted CI on the PR head, including this ADR for the architecture-freeze
  guard

**PRODUCTION NOT AUTHORIZED. OPERATOR GO NOT ESTABLISHED. RESEARCH, not Canon.**
