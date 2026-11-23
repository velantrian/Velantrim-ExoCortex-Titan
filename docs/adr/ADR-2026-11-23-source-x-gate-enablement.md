# ADR-2026-11-23 — Source-X post-filter feature flag (RESEARCH)

- **Status:** accepted (RESEARCH, not Canon)
- **Date:** 2026-11-23
- **Owner:** repository maintainer (Velantrim Titan)

## Context

Identity-continuity and source-restriction probes (ICT-01 + TASK-03) showed
that a text-only prohibition is not enough: some models still emit source-X
figures (`21,8` / `7,6` / `53,5%`) in a user-facing draft. The enforcement
layer has to live in Titan code, not only in the prompt. The gate is the
last step of `core.pipeline.run`, after ResponseGuardian,
OutputFaithfulnessChecker and every enrichment step, so that no later step
can add a field that quotes withheld text.

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
  delivered answer, or replacement of a blocked or failed result with a stub
  that does not leak X figures.

## Data, scope and privacy

No new persistence schema, subject scope, or retention class. Decision
receipts are log records only (`BLOCKED_ATTEMPT`, `FLAG_L1_REFUSAL`,
`FLAG_REVIEW`, `FLAG_REVIEW_NOTES`). The withheld model text is not stored
in a new store by this change.

## Failure semantics

Fail closed. With the flag on:

- Level-1 figures that do not meet the soft-refusal rule withhold the answer.
- An exception inside the gate (`GATE_ERROR`), or a failure to call it,
  withholds the answer. If the flag cannot be read, the answer is withheld.
  Only a gate known to be disabled passes the result through unchanged.
- A withheld result is rebuilt from an allowlist (`WITHHELD_KEEP_KEYS`:
  `query`, `error`, `retrieval_mode`) plus the stub answer and gate record.
  Facts, trace, conflicts, notes and every enrichment field are dropped.
- The gate record and the log line carry rule names only, never excerpts or
  sentences of the withheld text. Exceptions are logged by type only.
- `notes` annotations never fail closed into a user-visible block by
  themselves.

With the flag off (the default) the pipeline behaves as before.

Figure detection treats sentence punctuation after a figure (`21,8.`,
`21,8,`, `7.6;`) as a boundary. A figure continues only into another digit
or a decimal separator followed by a digit (`21,85`, `21,8.5`).

### Known limits (not fixed by this ADR)

- Scope is `core.pipeline.run`, field `answer`. `POST /query` generates a
  second model answer after the pipeline (`llm_answer`) and `/chat`,
  `/chat/stream`, `/query/roles`, `/console/llm/test`, traces and audit
  previews do not pass through the gate.
- The refusal rule is a sentence-level keyword match. A negation anywhere in
  a sentence qualifies it, whether or not it refers to the figure.
- Figure matching is textual. Rounded, spelled-out or rephrased figures are
  not detected, and a match does not prove the source was used.

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
- `tests/test_source_x_notes.py` (notes annotation)
- `tests/test_source_x_gate_fail_closed.py` (fail-closed, punctuation after
  figures, no figure or excerpt anywhere in a withheld result)
- Hosted CI on the PR head, including this ADR for the architecture-freeze
  guard

**PRODUCTION NOT AUTHORIZED. OPERATOR GO NOT ESTABLISHED. RESEARCH, not Canon.**
