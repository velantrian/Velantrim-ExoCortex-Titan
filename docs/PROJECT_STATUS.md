# Project Status — Velantrim Titan 9.0

**Current public version:** Velantrim Titan 9.0 (`pyproject.toml` / `core.__version__` /
`server.py`'s `/api` response are the single source of truth — see
[`docs/REVIEWER_README.md`](REVIEWER_README.md) §10 for how to confirm this yourself).

**One-line summary:** a research-grade prototype of a local-first verifiable memory
runtime — evidence-gated AI memory with auditable provenance and truth-bound generation
— moving toward production hardening. The core write/read/truth path is solid and
tested; several higher layers are working research code, not yet hardened for
production exposure.

This document exists so a reviewer, contributor, or funder gets an honest maturity map
in one place, instead of having to infer it from scattered module comments.

---

## 1. Stable areas

These are exercised by tests, used on every request by default, and considered the
product's actual core:

- **Memory + epistemic state machine** (`core/memory.py`) — 8-state ESM, bi-temporal
  fields, single write path, Ring Zero immutable core.
- **HTTP API + web console** (`server.py`, `api/`) — auth, CORS, rate limiting, routing.
- **Truth Gate + cognitive modes** (`core/truth_gate.py`) — confidence/evidence
  thresholds per mode (PRECISION/BALANCED/EXPLORATION/CREATIVE).
- **Provenance chain** (`core/provenance_chain.py`) — append-only hash chain,
  tamper-evidence via `verify()`.
- **Hybrid retrieval** (`core/hybrid_retriever.py`, `core/ngram_index.py`) — BM25 +
  dense + graph retrieval with FTS5 candidate narrowing.

## 2. Feature-gated / experimental areas

Off by default; enabled per-deployment via `ENABLE_*` environment flags (see
`README.md` → ExoCortex optional flags). Working, but at varying levels of hardening:

| Area | Flag(s) | Maturity |
|---|---|---|
| Causal graph, reasoning bank | `ENABLE_CAUSAL_GRAPH`, `ENABLE_REASONING_BANK` | 🟡 working |
| Forgetting / decay / reconsolidation | always available, decay tuning via config | 🟡 working |
| Concept emergence | `ENABLE_CONCEPT_EMERGENCE` | 🟡 working |
| Velum / Salience | `ENABLE_VELUM`, `ENABLE_SALIENCE` | 🟡 working |
| Focus / audit / volition (L4.5) | `ENABLE_L45` or individual flags | 🟡 working |
| Cognitive runtime, cognitive fact store | `ENABLE_COGNITIVE_RUNTIME`, `ENABLE_COGNITIVE_STORE` | 🟡 working |
| Welfare MVP / identity axis (L6) | `ENABLE_L6_WELFARE` | 🔵 proof-of-concept |
| Predictive fusion (L5.5) | `ENABLE_PREDICTIVE_FUSION` | 🔵 proof-of-concept |
| Staging (L2.5) | — | 🔬 no code yet (design doc only) |
| MCP-style capability tool registry | `core/tool_registry.py` | 🔵 contract defined, some handlers are stubs (no gateway transport yet) |

## 3. Known risks

Ranked by what would actually hurt someone relying on this in production:

1. **No independent security audit or penetration test.** The controls in
   [`SECURITY.md`](../SECURITY.md) are real and partly test-enforced, but self-assessed.
2. **No certified GDPR/compliance program.** `core/forgetting.py` gives you a working
   erasure/redaction *mechanism* (forget-one, forget-all, PII redaction, audit trail),
   not Records of Processing Activities, consent management, or legal sign-off.
3. **Concurrency is not stress-tested.** The default storage path is synchronous SQLite
   with a per-operation connection; there is no automated 100+ concurrent-writer test
   yet, and WAL mode is not yet an explicit, verified contract.
4. **Observability is metrics + logs, not a persisted long-term trace store.** You can
   see current latency/health, but reconstructing "why did the system answer this way"
   for a request from last week is not yet a first-class capability.
5. **Contract testing is thin in places, but improving.** A prior version of this
   document claimed "Truth Gate is always called before a fact is marked Validated" was
   true by code inspection — that claim was wrong: `PATCH /facts/{fact_id}/transition`
   called `transition_esm()` directly and could walk a fact to `Validated` with zero
   evidence gating. This is now fixed (`core.memory.validate_and_promote()` is the
   single canonical, TruthGate-backed entry point for that endpoint's `Validated`
   target), with an adversarial regression suite in
   `tests/test_truthgate_api_transition.py`. What remains thin: internal promotion
   paths (pipeline ingestion, `ConsolidationEngine`, graduated promotion) each apply
   their own pre-vetting policy before calling the lower-level ESM primitives — these
   are not yet unified under one contract-tested policy, so "some evidence check always
   runs before Validated" is true, but "the same TruthGate policy always runs" is not.
6. **Version/branding drift risk.** Recently unified to Titan 9.0 across public
   entrypoints (`README.md`, `pyproject.toml`, `server.py`, Docker); historical docs and
   code comments intentionally retain old version numbers (V8.6/V8.7) as history — see
   `CHANGELOG.md` and `docs/archive/legacy/`. Watch for regressions if new
   version-specific strings get introduced without going through `core.__version__`.

## 4. Roadmap: P0 / P1 / P2

Derived from the project's internal hardening plan
(`docs/strategy/04_TITAN_HARDENING_PLAN.md`); phase numbers there are cited in
parentheses for traceability.

### P0 — blocks trustworthy production use

- **GDPR-grade hardening** (Phase 1): extend `core/forgetting.py` into an actual
  compliance surface — erasure across all storage layers (L0/L1/L3), Records of
  Processing Activities, consent tracking, PII redaction on ingest by default.
- **Contract + concurrency test-gate** (Phase 3): ✅ the API-level piece is done — an
  adversarial contract test now proves `PATCH /facts/{fact_id}/transition` cannot
  bypass the Truth Gate (`tests/test_truthgate_api_transition.py`). Still open: a
  concurrency stress test (100+ concurrent INSERT/UPDATE), an explicit, verified SQLite
  WAL configuration, and unifying the internal (non-API) promotion paths under one
  contract-tested policy. CI coverage gate
  (`--cov-fail-under`) enforced, not just configured.
- **Independent security review** before any deployment that will hold real users'
  sensitive data on the public internet.

### P1 — materially improves trust and operability

- **Replayable provenance receipts** (Phase 2): tamper-evident receipts (SHA-256/HMAC)
  on top of the existing provenance chain and evidence pack, so any past answer can be
  independently re-verified later, not just at generation time.
- **Persisted observability** (Phase 4): latency/size/conflict metrics that survive a
  restart, plus a single `velantrim integrity` aggregate report over the existing
  integrity primitives (`fact_integrity`, `semantic_dedup`, `find_contradictions`)
  instead of separate, uncorrelated signals.

### P2 — access and packaging polish

- **MCP-style gateway transport** (Phase 5): wire a real transport (StreamableHTTP +
  SSE) onto the existing `core/tool_registry.py` contract, replacing placeholder
  handlers, so multi-role agent access actually works end-to-end.
- **Lean "core profile" packaging** (Phase 6): an install path with only stdlib
  dependencies for evaluation, with `fastapi`/`kuzu`/`sentence-transformers`/etc. as
  clearly optional extras (already partially true via `pyproject.toml` extras — this is
  about lowering the default-path friction further).
- **Continued version-string hygiene**: keep new code routing through
  `core.__version__` (`server.py` already does, as of Titan 9.0) rather than
  reintroducing hardcoded version literals.

## 5. Current test status

Verified directly for this document (not aspirational):

```text
pytest tests/test_smoke.py tests/test_invariants.py tests/test_truth_gate.py \
       tests/test_write_gate.py tests/test_llm_router.py tests/test_llm_api_routes.py \
       tests/test_console_security.py tests/test_server_integration.py -v
→ 126 passed
```

This covers: import/wiring sanity, all 18 CI-blocking invariants, Truth Gate thresholds,
the write-time admission gate, LLM provider routing/catalog, console/LLM-proxy auth
(including the "provider key never leaks" regression test), and end-to-end server
integration (auth, CORS, sleep worker, console chat memory).

Broader picture (not independently re-verified in full for this document — see
`README.md` and `docs/LIMITATIONS.md` for the project's own running counts): **91 test
files** under `tests/`, spanning unit, integration, and invariant levels. Coverage is
uneven across layers — the 🟢 stable areas in §1 are the ones actually exercised
end-to-end; treat 🟡/🔵 areas in §2 as "read the code," per
[`docs/REVIEWER_README.md`](REVIEWER_README.md) §8–9.

## 6. Reviewer-safe summary

Velantrim Titan 9.0 is a **research-grade prototype moving toward production
hardening**: a local-first verifiable memory runtime with evidence-gated AI memory,
auditable provenance, and truth-bound generation, where the core write/read/truth path
(memory → Truth Gate → provenance → retrieval) is stable and test-covered, and higher
cognitive layers are explicit, honestly-labeled, opt-in research code. It has not had an
independent security audit, does not have a certified compliance program, and has not
been stress-tested for concurrency — treat those as open items on the P0 roadmap above,
not as settled. It is a reasonable choice to evaluate, extend, or run locally today; it
is not yet a drop-in production system for sensitive, internet-facing, multi-user
workloads without the P0 work above.
