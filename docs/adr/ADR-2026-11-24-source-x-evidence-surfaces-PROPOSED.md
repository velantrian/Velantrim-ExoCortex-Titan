# ADR-2026-11-24 — Source-X Gate and evidence surfaces (PROPOSED)

- **Status:** PROPOSED — not accepted, not implemented. No behaviour in this
  repository depends on this record.
- **Date:** 2026-11-24
- **Owner:** repository maintainer (Velantrim Titan)
- **Related:** `ADR-2026-11-23-source-x-gate-enablement.md` (amendment
  2026-11-24), Draft PR #537

## Context

The source-X Gate (`ENABLE_SOURCE_X_GATE`, off by default) withholds
model-authored text that asserts source-X figures. PR #537 round 2 scans
the full HTTP response and every SSE event while the flag is on. Several
fields carry **evidence** — stored memory, retrieval results, the user's
own input — rather than model output. If source X was ever stored in
memory, those fields return its figures verbatim even with the Gate on.

Changing what evidence a client can see is an evidence-access policy
decision, not a Gate bug fix. Round 2 therefore leaves these fields
unchanged and records hits in them only as paths
(`source_x_gate.outbound.evidence_exempt_paths_with_hits`).

## Data-flow map (PR #537 round 2, flag ON)

Legend: **soft** = `gate_final_text` (two-level rule, soft L1 may deliver
an explicit refusal); **strict** = `sanitize_outbound` string-leaf scan,
Level-1 hit → `[withheld: source-X gate]`; **allow** = key allowlist;
**exempt** = returned unchanged (this ADR).

| Endpoint | Field / event | Origin | Treatment |
|---|---|---|---|
| `/query` | `answer` | pipeline answer + lens formatter | soft, pipeline verdict kept |
| `/query` | `llm_answer` | model | soft |
| `/query` | `llm_meta.error` | provider exception | type + code only |
| `/query` | `facts` | memory retrieval | **exempt** |
| `/query` | `query` | user input | **exempt** |
| `/query` | `causal_hints`, `exocortex_sections`, `cross_domain`, `lens_context`, `observer`, `truth`, `gaps`, `innenwelt`, `context_report`, `evidence_labels`, `reference_check`, `effective_params`, `profile_landmark`, `error`, … | derived / server | strict |
| `/query/roles` | `answer`, `llm_answer` | model synthesis | soft |
| `/query/roles` | `lens_context.branches[].response` | model (per branch) | soft |
| `/query/roles` | `lens_context.branches[].key_claims`, other fields | model-derived / server | strict |
| `/query/roles` | `facts` | memory | **exempt** |
| `/chat` | `reply` | model / offline memory reply | soft |
| `/chat` | `memory_highlights`, `memory_saved`, `memory_suggestions`, `dialogue_essence` | memory + user message | **exempt** |
| `/chat` | other fields | server | strict |
| `/chat/stream` | `token.text`, `done.reply`, `final.reply` | model (held, bounded) | soft |
| `/chat/stream` | `context.report` | server | allow (ContextReport keys) + strict |
| `/chat/stream` | `done.usage`, `final.llm_usage` | provider | allow (numeric only) |
| `/chat/stream` | `essence.snapshot` | memory + user message | **exempt** |
| `/chat/stream` | `final.memory_*`, `final.dialogue_essence` | memory + user message | **exempt** |
| `/chat/stream` | `error.message`, other `final` keys | server / provider | allow + strict |
| `/chat/stream` | any other event type (e.g. `thinking`) | provider | dropped |

## Proposal (for decision, not implemented)

Option A — **status quo**: evidence stays visible; the Gate only governs
model-authored text. Lowest risk of hiding legitimate memory.

Option B — **strict evidence redaction when the flag is on**: apply
`sanitize_outbound` to the exempt fields too. Prevents verbatim echo of
source X from memory, but changes evidence access and may hide records a
user is entitled to inspect.

Option C — **source-level quarantine**: mark records that originate from
source X at ingest and exclude them from retrieval / highlights while the
flag is on. Addresses the cause, needs a provenance field and migration
review.

Recommendation for discussion: C long-term, A until C is designed; B only
as a temporary measure with explicit owner approval.

## Not decided here

User-input echo (`query`, essence of the user message), Canon / ESM
policy, retention, Notion synchronisation.

**PROPOSED. Not accepted. PRODUCTION NOT AUTHORIZED. RESEARCH, not Canon.**
