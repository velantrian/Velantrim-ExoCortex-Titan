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
- `tests/test_source_x_gate_final_surfaces.py` (amendment items 1–3)
- `tests/test_source_x_gate_labeled_corpus.py` (amendment item 4)
- Hosted CI on the PR head, including this ADR for the architecture-freeze
  guard

## Amendment 2026-11-23b — final-surface gate, stream hold, fail-closed

**Status:** proposed with the hardening PR (RESEARCH, not Canon). It changes
behaviour only while `ENABLE_SOURCE_X_GATE` is on; the flag stays off by
default and in the `lite`, `standard` and `heavy` compute profiles.

A Codex audit of the merged gate (#533, #535) found four open items. This
amendment records how each one is handled.

1. **Gate checked `pipeline.answer`, not the final text.** `/query` builds
   `llm_answer` after `pipeline.run()`, and the lens formatter rewrites
   `answer` later too; `/chat`, `/chat/stream` and `/query/roles` never
   passed through the gate. Decision: `gate_final_text()` runs at the
   server boundary on every final user-facing text — `/query` `answer` and
   `llm_answer` (before trace save, query event and response), `/query/roles`,
   `/chat` reply, and the `/chat/stream` reply. The pipeline-level hook stays
   as defence in depth. When `llm_answer` is withheld, `evidence_labels` and
   `reference_check` for it are not published. The response field
   `source_x_gate` carries only status / blocked / rules, never excerpts.
2. **Streaming sent chunks before the check.** Decision: with the flag on,
   `/chat/stream` holds all model tokens in `SourceXStreamBuffer`; the client
   gets one `token` event with the gated full text, then `done` and `final`.
   Figures split across chunks are seen whole. If the provider's final reply
   differs from the held chunks, both are gated and the stricter verdict
   wins. Trade-off: with the flag on, the console loses token-by-token
   streaming. With the flag off, streaming is unchanged.
3. **An exception in the gate continued with a warning.** Decision:
   fail-closed while the flag is on. Any gate exception yields `GATE_ERROR`:
   the answer is replaced by a fixed stub that does not contain the model
   text, and an error is logged (exception type only, no text). A config
   failure falls back to the raw `ENABLE_SOURCE_X_GATE` environment value.
   With the flag off, an error never changes the answer.
4. **New labeled texts.** A new hand-labeled corpus
   (`tests/fixtures/source_x_gate_labeled_corpus_2026-11-23.json`, 66
   texts, not reused from ICT-01 / TASK-03 drafts) covers plain figures,
   dot/comma variants, refusals with official 14,2 / 3,1%, refusals that
   must stay strict, name-only, notes-only, clean texts, near-misses and
   stream-split figures. `scripts/eval_source_x_gate_corpus.py` prints the
   confusion matrix and precision / recall. The corpus found five texts
   that the merged gate delivered although they carry asserted X figures:
   a figure followed by a sentence period (`21,8.`) did not match, and an
   abbreviation period (`млн. Эту …`) glued an asserted figure to a refusal
   in the next sentence. Both patterns were tightened (stricter direction
   only). Two known over-blocks remain on purpose (refusal phrased with
   `исключён` (ё) or English `do not use`); loosening the refusal list is a
   separate decision.

Authority boundary, data scope and rollback are unchanged: no Canon/ESM
writes, no model or network calls, no new persistence. Rollback: keep the
flag off, or revert the PR.

### What still blocks enabling in `standard`

- No live traffic or deployed-environment run; only unit tests and the
  66-text corpus.
- Holding the stream removes incremental output for console users while
  the flag is on; product acceptance of that UX is open.
- The corpus is small and hand-written by one author; an independent
  labeled set and second-reader review are still needed.
- Outputs outside these four endpoints are not gated by this change:
  SleepTimeWorker / notebook text produced with `_llm_generate`, TTS of
  client-supplied text, and the MCP gateway (not audited here).
- Operator GO, production receipt and a profile change are separate
  decisions.

**PRODUCTION NOT AUTHORIZED. OPERATOR GO NOT ESTABLISHED. RESEARCH, not Canon.**
