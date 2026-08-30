# Project Status — Velantrim Titan 9.0

> **Status:** CURRENT STATUS GUIDE  
> **Live-state rule:** mutable repository facts (current `main` SHA, PR/Issue state, workflow/review state) must be verified from GitHub when they matter. Dated evidence below remains snapshot evidence, not an evergreen remote-state claim.

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
  fields, canonical storage primitives, Ring Zero immutable core. Promotion ownership
  is separately inventoried in `docs/operations/promotion-ownership-inventory.md`.
- **HTTP API + web console** (`server.py`, `api/`) — auth, CORS, rate limiting, routing.
- **Truth Gate + cognitive modes** (`core/truth_gate.py`) — confidence/evidence
  thresholds per mode (PRECISION/BALANCED/EXPLORATION/CREATIVE).
- **Provenance chain** (`core/provenance_chain.py`) — append-only hash chain,
  tamper-evidence via `verify()`.
- **Hybrid retrieval** (`core/hybrid_retriever.py`, `core/ngram_index.py`) — BM25 +
  dense + graph retrieval with FTS5 candidate narrowing.

## 2. Feature-gated / experimental areas

These are opt-in at the code/configuration boundary and work at varying levels of
hardening. Do not infer the settings of a particular Compose profile from this table:
the compatibility `docker-compose.yml` intentionally enables several research layers,
while `docker-compose.prod.yml` pins them off for the hardened profile.

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
   `docs/evidence/sqlite-concurrency-baseline-2026-08-03.json`. Issue #249 was later
   characterized through merged PR #346 as a test-harness scope defect / historical
   runner sensitivity; a product CAS defect was not confirmed, and its one-winner /
   one-intent assertions remain intact. The distinct concurrent fresh-store bootstrap
   residual tracked as Issue #347 was subsequently resolved by the bounded bootstrap
   serialization fix merged through PR #349. Exact closure evidence records final PR,
   post-merge aggregate, and scheduled CodeQL success. This resolves the supported
   bounded concurrent fresh-store first-use scenario; it does **not** establish an SLA,
   unlimited scale, network-filesystem safety, or general multiprocess production proof.
4. **Observability is metrics + logs, not a persisted long-term trace store.** You can
   see current latency/health, but reconstructing "why did the system answer this way"
   for a request from last week is not yet a first-class capability.
5. **Promotion ownership is substantially hardened, but mutation ownership remains
   family-specific.** `core/pipeline.py::run()` is read-only with respect to fact/ESM
   mutation. Standard promotion callers route through `PromotionGateway`, which
   delegates to the canonical `SQLiteGraphStore.validate_and_promote()` path; an
   AST-based CI ownership guard rejects unreviewed new direct promotion sites. The
   hardened promotion primitive uses a durable L1 snapshot, TruthGate evaluation, a
   CAS-guarded canonical update, and transactionally coupled version/audit evidence.

   The old World Skills direct-promotion exception is **closed** as of Issue #52 C9 /
   PR #320. World Skills candidates now pass explicit provenance metadata, domain
   review and a read-only TruthGate precheck; a legal ESM transition reaches
   `Supported`; final `Validated` / local-Canon admission is owned by
   `PromotionGateway` + TruthGate recheck + CAS. Legacy/unreviewed World Skills rows are
   quarantined rather than auto-validated. See
   `docs/operations/world-skills-admission.md` and
   `docs/operations/promotion-ownership-inventory.md`.

   This is **not** a claim that all mutation families have one global owner.
   `truth_maintenance.supersede()` remains a compound mutation with its own atomic facts
   transaction; ordinary non-Validated ESM transitions, invalidation, relation
   lifecycle, archival/redaction and other mutation families retain their documented
   boundaries.
6. **Version/branding/public-release drift risk.** Public entrypoints use Titan 9.0,
   while historical docs and comments intentionally retain older version numbers as
   history. `CANONICAL.md` is now the current authority index; older V8.x material is
   historical unless explicitly re-adopted by a current contract. The historical
   GitHub Release classified in `docs/evidence/release-evidence-2026-08-14.md` is not
   current Titan release evidence.

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
  bounded SQLite concurrency/crash characterization exist. Standard Validated callers
  are CI-inventoried behind `PromotionGateway`; `/query` is read-only; the canonical
  promotion path is CAS guarded and transactionally couples its required Version/Audit
  evidence. World Skills uses its fail-closed admission contract rather than a
  direct-promotion exception. #249 has a bounded harness-scope classification and #347
  has a bounded fresh-store bootstrap fix. Still required for a broader production
  claim: prove the wider storage path under realistic multiprocess/production
  conditions and continue converging separate legacy mutation families only where
  evidence shows an authority or atomicity gap. CI coverage gate (`--cov-fail-under`)
  is enforced, not just configured.
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
  dependencies for evaluation, with `fastapi`/graph/embedding dependencies as clearly
  optional extras (already partially true via `pyproject.toml` extras — this is about
  lowering default-path friction further).
- **Continued version-string hygiene**: keep new code routing through
  `core.__version__` (`server.py` already does, as of Titan 9.0) rather than
  reintroducing hardcoded version literals.

## 5. Retained test / release evidence snapshot

A retained dated evidence snapshot is:

[`docs/evidence/release-evidence-2026-08-14.md`](evidence/release-evidence-2026-08-14.md)

Its signed baseline is `main@0b2c49d701b88d12c66042148c19199638130d03` after
C9 / PR #320. Repository-owned push evidence on that exact SHA records:

```text
Full CI #1181 / run 31839014136           SUCCESS (5/5 jobs)
Docker #779 / run 31839014137             SUCCESS
CodeQL #19 / run 31839014207              SUCCESS
Aggregate #1213 / run 31839014181         SUCCESS
full pytest path                          4160 passed
coverage ratchet                          76% >= 74%
```

Those values remain **historical snapshot evidence**, not the current repository HEAD
or evergreen CI state. Any newer candidate, merge, or decision must establish its own
fresh exact-head/post-merge evidence from GitHub.

The evidence report also records the explicit absence of a current 2026-08-14 GitHub
Release and classifies the repository's older mislabeled release/tag as historical, not
current Titan release evidence. No release is invented merely to make this status page
look complete.

## 6. Reviewer-safe summary

Velantrim Titan 9.0 is a **research-grade prototype moving toward production
hardening**: a local-first verifiable memory runtime with evidence-gated AI memory,
auditable provenance, and truth-bound generation, where the core write/read/truth path
(memory → Truth Gate → provenance → retrieval) is stable and test-covered, and higher
cognitive layers are explicit research code. It has not had an independent security
audit and does not have a certified compliance program. SQLite concurrency and crash
behavior have bounded characterization evidence, including closure of the #347 bounded
fresh-store first-use residual, but that does not imply unlimited or general
multiprocess production-scale proof. For deployment, `docker-compose.prod.yml` is the
repository's hardened deny-by-default profile; `docker-compose.yml` is retained for
compatibility/research behavior and is not the hardened production contract. It is a
reasonable choice to evaluate, extend, or run locally today; it is not yet a drop-in
production system for sensitive, internet-facing, multi-user workloads without the P0
work above.
