# 🌱 External Model Cognitive Proposals — Speculative Future Ideas

**Status:** `RESEARCH / UNVERIFIED SOURCE — R0`
**Runtime authority:** none
**Canon write authority:** none
**Default enabled:** false
**Date:** 2026-08-03
**Scope:** raw architecture proposals surfaced by external AI assistants (GitHub Copilot,
DeepSeek, Qwen, Gemini, Perplexity, Grok) reacting to a *description* of Titan from
outside this repository — not from reading `core/`, `api/`, or the test suite. Filtered,
fact-checked where checkable, and reframed against actual Titan ownership before being
recorded here.

## Why this document exists

On 2026-08-03 six external AI assistants were asked, independently, what would
strengthen this project. Some of their proposals are genuinely useful raw material;
several others were stated as confident fact about *this repository's current state*
and turned out to be **false** when checked against the actual code. This document
keeps the useful ideas, discards the noise, and — per this project's own standing rule
that a document must never assert a runtime claim it hasn't checked — records exactly
what was verified and what wasn't, so a future reader doesn't have to redo that check
or mistake a proposal for a status claim.

## ⚠️ Provenance & reliability check — read this before anything else

Three specific factual claims from the external-model output were checked against the
current `main` tree during the same audit session that produced this document. All
three were stated with confident, file-specific language and all three were **wrong**:

| Claim made | Reality (checked against code) |
|---|---|
| "`core/fact_decayer.py` has 0 production callers" | False — called from `core/sleep_time_worker.py:375` via `experience_replay`, gated by `SLEEP_WORKER_ENABLED` |
| "`core/experience_replay.py` is orphaned / dead" | False — same call site as above; feature-gated, not disconnected |
| "`core/working_memory.py` is orphaned" | False — referenced from `core/query_router.py`, `core/context_pack.py`, `core/synaptic_shadow.py`; `use_working_memory=True` is set for the personal-memory routing mode |

Nothing else in this document should be read as a status claim about Titan. Every
proposal below is speculative raw material, not a finding. Where a proposal overlaps
with something that already exists in this codebase, that overlap is called out
explicitly — several of the ideas below were pitched as novel and are, in fact,
partial re-inventions of existing Titan components.

## Decision

Titan may record external-model brainstorming as prior art, exactly as it already does
for external open-source systems (see
[`EXTERNAL_ARCHITECTURE_PATTERNS.md`](EXTERNAL_ARCHITECTURE_PATTERNS.md)). An idea
proposed by an external model — including one asked to review this very project — does
not gain runtime, policy, truth, memory or Canon authority merely by being written down
confidently.

```text
external model brainstorming
→ fact-check any status claims against actual code
→ discard duplicates of existing Titan components
→ reframe survivors as a Titan-native research question
→ record here as R0 (no offline prototype yet)
→ same promotion path as any other research item
```

## Non-negotiable boundaries

These are the same standing invariants as every other document in this directory —
repeated here, not weakened:

- Canon, ESM, TruthGate, PolicyKernel, Recall Policy, Write Gate, AuditChain and
  ErasureCoordinator retain their existing ownership.
- Query and retrieval paths remain read-only with respect to Canon and epistemic state.
- External (human or AI) proposal output is a proposal and cannot write directly to
  durable memory.
- No item below implies Titan has, or should simulate having, subjective experience,
  autonomous will or a "self" beyond the explicitly-scoped, proof-of-concept L6
  Welfare/identity-axis code that already exists and is off by default.
- Reproducible evidence on a Titan workload precedes active integration, exactly as
  for every other research track.

## Research portfolio

Numbered `Q` (not `P`) to keep this batch visibly separate from the already-triaged
`P0`–`P4` track in [`FUTURE_COMPONENTS.md`](FUTURE_COMPONENTS.md) until any of these
earns promotion into that list.

### Q1 — Human-readable decision receipt

**Source:** Perplexity ("Truth Receipt").

**Overlap check:** Titan already has machine-verifiable provenance
(`core/provenance_chain.py`) and an append-only audit trail (`core/audit_chain.py`).
What's proposed here is not a new authority — it's a **rendering** of an existing
TruthGate verdict into a short, fixed-template, human-readable summary (which
thresholds fired, what evidence was present, what was missing) alongside the existing
machine record.

**Research question:** can a TruthGate verdict already produced by
`validate_and_promote()` be rendered into a fixed, non-generative (no LLM in the loop)
template without adding a second source of truth that can drift from the real
decision?

**Initial boundary:** template-only, derived deterministically from the existing
verdict object; no free-text LLM summarization (that would reintroduce exactly the
"explanation that isn't the real trace" problem `core/xai_explain.py`'s own rule
already forbids).

### Q2 — Adversarial refutation pass before promotion

**Source:** Gemini ("adversarial falsification loop"), echoed loosely by Copilot's
"activation receipts" framing.

**Overlap check:** partial. `core/truth_gate.py` already gates on evidence/confidence;
`contradiction_detector="none"` is explicitly disabled today (see
`docs/PROJECT_STATUS.md` §5) because no NLI detector exists. This proposal is really
"turn contradiction detection back on, but make it adversarial (try to refute) rather
than passive pattern-matching."

**Research question:** does a bounded, deterministic-fixture "attempt to refute this
candidate against existing Supported/Validated facts" stage measurably reduce false
promotions on a fixed evaluation corpus, without becoming a second, uncorrelated
promotion policy the way the pre-`PromotionGateway` code paths were?

**Initial boundary:** must run *inside* `PromotionGateway`, not as a parallel path;
must be evaluated via `EvaluationReplay` (P0 track) before any Operator GO; no
autonomous multi-step agent loop — a single bounded check, fixture-driven in tests.

### Q3 — Confidence propagation across causal edges

**Source:** Perplexity.

**Overlap check:** `core/causal_graph.py` stores edges; it does not currently
recompute a `derived_confidence` on downstream nodes when an upstream fact's
confidence changes.

**Research question:** should a confidence change on fact A cause a bounded-depth,
read-only recomputation of a *derived* (non-canonical) confidence signal on nodes
reachable from A, and if so, how does that avoid becoming a second, unauthoritative
epistemic state that competes with ESM?

**Initial boundary:** the output must be a clearly-separate `derived_confidence`
projection field, rebuildable from source data, never conflated with the fact's own
ESM-governed `confidence`; bounded hop count (as `research/ARCHITECTURE_AXES.md`-style
projections already require elsewhere in this codebase).

### Q4 — Structured uncertainty in LLM claim candidates

**Source:** Perplexity.

**Overlap check:** the Synaptic Exo-Cortex profile already separates
`extraction_confidence` from `truth_confidence` on `KnowledgeCapsule`
(`docs/SYNAPTIC_EXO_CORTEX_IMPLEMENTATION_PLAN.md`). This proposal asks whether that
same discipline should extend to *why* a model is uncertain (ambiguous reference,
temporal ambiguity, conflicting source), not just *how much*.

**Research question:** does adding a small closed vocabulary of `uncertainty_source`
tags to a claim candidate change TruthGate outcomes on a fixed corpus, or is scalar
confidence already sufficient signal?

**Initial boundary:** closed enum, not free text (free text reintroduces
unverifiable LLM narrative into a truth-adjacent field); additive to the existing
candidate schema, not a new object.

### Q5 — Human-in-the-loop queue for ambiguous contradictions

**Source:** Perplexity ("ContradictionQueue").

**Overlap check:** this is **not new** — it is the same gap already tracked in
[`docs/LIMITATIONS.md`](../docs/LIMITATIONS.md) as `TS-2`: *"TrustedSources 'замораживают'
ошибочные факты... Нужен `emergency_invalidate_trusted()` с 2-approval flow."* File this
proposal as corroborating evidence for TS-2's priority, not as a new track.

**Research question:** unchanged from TS-2 — what does a 2-approval, human-adjudicated
override path look like for a trusted-source fact that later turns out to be wrong,
without giving any single human or model unilateral Canon-rewrite power?

### Q6 — Explicit model-selection reasoning in provenance

**Source:** Perplexity ("TaskComplexityEstimator" / `ModelSelectionReason`).

**Overlap check:** `core/llm_router.py` already routes by provider/task; it does not
currently record *why* a given model was chosen alongside the resulting claim's
provenance.

**Research question:** does recording a short, closed-vocabulary routing reason
(e.g. `latency_sensitive`, `reasoning_required`, `provider_unavailable_fallback`)
in provenance improve auditability enough to justify the extra field, given the
project's existing "LLM is replaceable and provider-neutral" invariant?

**Initial boundary:** observability only — must not become a hidden policy input that
the visible routing config doesn't already expose.

### Q7 — Static authority-surface scanning ("FreezeGuard v2")

**Source:** Copilot.

**Overlap check:** this one is **substantially already built**, not a green-field
idea. `scripts/check_architecture_freeze.py` already regex-scans PR diffs for new
`ENABLE_*` flags and new canonical/ESM write-call patterns
(`transition_esm`, `validate_and_promote`, `store_fact`, `upsert_fact`,
`supersede_fact_cas`, `write_tombstone`) and requires an ADR under `docs/adr/` before
allowing them to merge — see [`ARCHITECTURE_FREEZE.md`](../docs/ARCHITECTURE_FREEZE.md).
What Copilot actually proposed on top of that is narrower than it sounded: replace the
regex matcher with an AST-based one, so a renamed import or an indirect call
(`getattr(store, "store_fact")(...)`) can't quietly slip past a pattern match.

**Research question:** does an AST-based successor meaningfully reduce false negatives
over the current regex guard on Titan's actual PR history, enough to justify the added
complexity of a Python-AST-aware CI step?

**Initial boundary:** stays a diff-time CI gate, exactly like today's guard — no new
runtime authority, no new blocking behavior beyond what `check_architecture_freeze.py`
already enforces.

### Q8 — Identity/self-description drift measurement — high caution

**Source:** Copilot ("Identity Drift Monitor").

**Overlap check:** Titan has an explicit, proof-of-concept, off-by-default L6
Welfare/identity-axis layer (`ENABLE_L6_WELFARE`), and the project's own README states
outright that Titan does not claim "consciousness, subjective experience, or
autonomous will." Any "identity drift" framing must not be read as tracking drift in
some emergent self — that would contradict the project's own stated non-goals.

**Research question, reframed to stay inside existing boundaries:** if `docs/PHILOSOPHY.md`,
`docs/PHILOSOPHY_SPEC.md`, or any other declared values/policy *document* changes
between versions, would a plain text/semantic diff between those documents over time
be useful evidence for reviewers — as a **documentation-consistency check**, not a
runtime self-monitoring capability?

**Initial boundary:** operates only on committed text documents via version-control
history; produces no runtime signal, no behavioral inference, no claim about an
internal state; if this is not wanted even in this narrow form, it should be dropped
rather than reframed further — it is the most speculative item in this document and
the one most likely to invite anthropomorphic misreadings if implemented carelessly.

## Explicitly considered and not recorded as a research item

For transparency about what was filtered out and why, rather than silently dropping
proposals: `Tension Heatmap` (Gemini), `Lexical Anchoring` (Gemini),
`EpisodicStore` (Perplexity), `CausalReasoner` forward/backward chaining (Perplexity),
and dashboard-style UIs (`Memory Inspector`, `Canon Admission Dashboard`, `Replay
Divergence Dashboard` — Copilot) were not added as separate `Q` items. Each is a
plausible idea in isolation, but all of them (a) had no overlap check performed by
their source model against existing Titan components, (b) would require a new
persistent data structure or authority surface to even prototype, and (c) have no
return trigger under this directory's existing rule — no measured limitation, no
reproducible benchmark case, and no operator-labelled dataset motivating them yet. They
remain available to reconsider individually if a concrete trigger appears; recording
eight vague dashboards as eight research tracks would violate this directory's own
"feature count is not a sufficient trigger" rule.

The **process/governance suggestions** from this same round (time-boxed sprints, a
named owner per workstream, a rollback protocol, an emergency kill switch,
characterization tests before refactoring `core/memory.py`, a dogfooding protocol, a
per-PR status-doc update rule, CI time budgets, an explicit project exit-criteria list —
DeepSeek, Qwen, Grok) are deliberately **not** in this file. They are not architecture
research; they are engineering-process proposals that don't need an offline prototype
or a promotion pipeline, and belong with the project's contribution/process
documentation, not `research/`.

## Return triggers

Same rule as [`FUTURE_COMPONENTS.md`](FUTURE_COMPONENTS.md): a measured limitation in
the current baseline, a reproducible benchmark case, a concrete workload existing
components cannot satisfy, an approved security/policy/compliance requirement, or an
operator-labelled evaluation dataset. External-model novelty or confident phrasing is
not a trigger — see the provenance check above for exactly why not.
