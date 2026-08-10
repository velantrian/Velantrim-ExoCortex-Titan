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
3. **Concurrency has bounded characterization, not production-scale proof.** PR #174
   added repeatable SQLite evidence for one-store 100-thread writes, a writer matrix of
   `1/10/25/50/100`, 25 independent store instances against one WAL database, mixed
   readers/writers, committed-write crash survival, uncommitted rollback, and
   `PRAGMA integrity_check = ok`. The retained evidence is
   `docs/evidence/sqlite-concurrency-baseline-2026-08-03.json`. This materially closes
   the old claim that no automated 100-writer characterization existed, but it is not an
   SLA or proof of unlimited scale, network filesystems, production multiprocess load,
   or every contention edge. Issue #249 remains a separate uncharacterized
   CAS-contention flake and must not be weakened or reclassified without evidence.
4. **Observability is metrics + logs, not a persisted long-term trace store.** You can
   see current latency/health, but reconstructing "why did the system answer this way"
   for a request from last week is not yet a first-class capability.
5. **Promotion ownership is substantially hardened, but not globally singular.** A
   previous version of this document described `POST /query` as a second public path
   that could promote retrieved facts. That is stale: `core/pipeline.py::run()` is now
   read-only with respect to fact/ESM mutation. Five standard promotion callers route
   through `PromotionGateway`, which delegates to the canonical
   `SQLiteGraphStore.validate_and_promote()` path; an AST-based CI ownership guard
   rejects unreviewed new direct promotion sites. The hardened promotion primitive uses
   a durable L1 snapshot, TruthGate evaluation, a CAS-guarded canonical update, and
   `VersionStore` pre-image + `AuditChain` event in the same SQLite transaction; when
   migration 020 is active, the projection-outbox intent is committed in that same
   transaction too. See `docs/operations/promotion-ownership-inventory.md` and
   `docs/adr/ADR-2026-08-03-promotion-ownership-lock.md`.

   This is **not** a claim that all mutation families have one global owner. The curated
   World Skills ingest remains one explicit, CI-locked promotion exception pending a
   separate admission contract; `truth_maintenance.supersede()` remains a compound
   mutation with its own atomic facts transaction; ordinary non-Validated ESM
   transitions, invalidation, relation lifecycle, archival/redaction and other mutation
   families have their own boundaries. The remaining engineering task is to keep those
   families explicit and converge legacy bypasses without creating a second authority.
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

- **GDPR-grade hardening** (Phase 1): extend the current erasure/redaction mechanisms
  into an actual compliance surface — Records of Processing Activities, consent
  tracking, lawful-basis handling, PII redaction policy, and legal/operational proof.
  The durable erasure coordinators are engineering mechanisms, not a certified program.
- **Contract + concurrency test-gate** (Phase 3): ✅ core promotion ownership and the
  bounded SQLite concurrency/crash characterization now exist. Standard Validated
  callers are CI-inventoried behind `PromotionGateway`; `/query` is read-only; the
  canonical promotion path is CAS guarded and transactionally couples its required
  Version/Audit evidence. Still open: characterize issue #249 without weakening its
  one-winner/one-intent assertions; prove the wider storage path under realistic
  multiprocess/production conditions; and continue converging separate legacy mutation
  families only where evidence shows an authority or atomicity gap. CI coverage gate
  (`--cov-fail-under`) is enforced, not just configured.
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

This covers: import/wiring sanity, all current CI-blocking tests in
`tests/test_invariants.py`, Truth Gate thresholds,
the write-time admission gate, LLM provider routing/catalog, console/LLM-proxy auth
(including the "provider key never leaks" regression test), and end-to-end server
integration (auth, CORS, sleep worker, console chat memory).

Broader picture (not independently re-verified in full for this document — see
`README.md` and `docs/LIMITATIONS.md` for the project's own running counts): **137
`test_*.py` files** under `tests/` on the documented repository snapshot, spanning
unit, integration, and invariant levels. Coverage is
uneven across layers — the 🟢 stable areas in §1 are the ones actually exercised
end-to-end; treat 🟡/🔵 areas in §2 as "read the code," per
[`docs/REVIEWER_README.md`](REVIEWER_README.md) §8–9.

These counts are snapshot evidence for the documented run, not a live repository total;
re-run the relevant commands before quoting them as current.

## 6. Reviewer-safe summary

Velantrim Titan 9.0 is a **research-grade prototype moving toward production
hardening**: a local-first verifiable memory runtime with evidence-gated AI memory,
auditable provenance, and truth-bound generation, where the core write/read/truth path
(memory → Truth Gate → provenance → retrieval) is stable and test-covered, and higher
cognitive layers are explicit, honestly-labeled, opt-in research code. It has not had an
independent security audit and does not have a certified compliance program. SQLite
concurrency and crash behavior have bounded characterization evidence, but production-
scale multiprocess/storage behavior and issue #249 remain unresolved. It is a reasonable
choice to evaluate, extend, or run locally today; it is not yet a drop-in production
system for sensitive, internet-facing, multi-user workloads without the P0 work above.
