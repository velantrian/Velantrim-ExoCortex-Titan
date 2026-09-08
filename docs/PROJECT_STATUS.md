# Project Status — Velantrim Titan 9.0

> **Status:** CURRENT STATUS GUIDE  
> **Live-state rule:** mutable repository facts (current `main` SHA, PR/Issue state,
> workflow/review state) must be verified from GitHub when they matter. Dated evidence
> below remains snapshot evidence, not an evergreen remote-state claim.
>
> **Scope rule:** the `P0/P1/P2` in this document are **production-hardening priorities**.
> They are not the same counters as the already-closed bounded **V1 productization** scope
> in `docs/project_status/FOR_AI.json`. `V1 P0/P1 = 0` therefore does **not** mean
> production-hardening P0/P1 = 0 or production authorization.

**Current public version:** Velantrim Titan 9.0 (`pyproject.toml` / `core.__version__` /
`server.py`'s `/api` response are the version source of truth; see
[`docs/REVIEWER_README.md`](REVIEWER_README.md) for verification guidance).

**One-line summary:** a research-grade prototype of a local-first verifiable memory
runtime — evidence-gated AI memory with auditable provenance, explicit epistemic states,
controlled write boundaries, and replaceable language generation — moving toward
production hardening.

This document exists so a reviewer, contributor, or funder gets an honest maturity map
without inferring current truth from scattered comments or historical audits.

---

## 1. Stable / product-leaning areas

These are part of the current engineering foundation. “Stable” here does not mean every
optional dependency/signal is enabled in every installation.

- **Memory + epistemic state machine** (`core/memory.py`) — 8-state ESM, bi-temporal
  fields, canonical storage primitives, Ring Zero immutable core. Promotion ownership is
  separately inventoried in `docs/operations/promotion-ownership-inventory.md`.
- **HTTP API + web console** (`server.py`, `api/`) — auth, CORS, routing and current
  server composition.
- **Truth/write boundaries** (`core/truth_gate.py`, `core/write_gate.py`,
  `core/promotion_gateway.py`, `core/policy_kernel.py`) — controlled standard promotion
  and permission/write policy.
- **Provenance / audit** (`core/provenance_chain.py`, `core/audit_chain.py`) — source
  lineage and tamper-evident/audit artifacts.
- **Retrieval orchestration** (`core/hybrid_retriever.py`, `core/ngram_index.py`) —
  lexical/BM25-style retrieval with optional dense/graph signals and candidate narrowing.
  This is **not** a claim that every installation executes BM25 + dense + graph on every
  request; enhanced signals depend on optional dependencies/configuration and may degrade
  to narrower retrieval paths.
- **Read-path mutation boundary** — current `core/pipeline.py::run()` is read-only with
  respect to canonical fact storage, ESM promotion, and causal-relation mutation.

## 2. Feature-gated / bounded / experimental areas

These exist at varying levels of hardening. Do not infer settings of a particular Compose
profile from this table: compatibility/research profiles may enable layers that the
hardened profile pins off.

| Area | Flag / surface | Maturity |
|---|---|---|
| Causal graph, reasoning bank | `ENABLE_CAUSAL_GRAPH`, `ENABLE_REASONING_BANK` | 🟡 working / gated |
| Forgetting / decay / reconsolidation | config-dependent | 🟡 working |
| Concept emergence | `ENABLE_CONCEPT_EMERGENCE` | 🟡 working |
| Velum / Salience | `ENABLE_VELUM`, `ENABLE_SALIENCE` | 🟡 working |
| Focus / audit / volition | `ENABLE_L45` or individual flags | 🟡 working |
| Cognitive runtime/store | `ENABLE_COGNITIVE_RUNTIME`, `ENABLE_COGNITIVE_STORE` | 🟡 working |
| Welfare / identity axis | `ENABLE_L6_WELFARE` | 🔵 proof-of-concept |
| Predictive fusion | `ENABLE_PREDICTIVE_FUSION` | 🔵 proof-of-concept |
| Staging (L2.5) | design docs | 🔬 no code yet |
| MCP capability registry + JSON-RPC transport | `core/tool_registry.py`, `core/mcp_transport.py` | 🔵 bounded implementation present; not server-wired by default; no runtime/production authority |
| Synaptic answer integration | shadow/reader surfaces | ✅ components/shadow evidence exist; active answer authority not transferred |

## 3. Known production-hardening risks

Ranked by what would materially affect trustworthy production use:

1. **No independent security audit or penetration test.** Existing controls are real and
   partly test-enforced, but self-assessed.
2. **No certified GDPR/compliance program.** Erasure/redaction mechanisms are engineering
   mechanisms, not Records of Processing Activities, consent/lawful-basis management, or
   legal sign-off.
3. **Concurrency/storage proof is bounded, not production-scale.** Existing SQLite
   evidence covers significant thread/concurrency/crash scenarios. Issue #249 was
   characterized as a harness-scope/historical runner problem rather than a confirmed
   product CAS defect. The separate concurrent fresh-store bootstrap residual tracked as
   Issue #347 was closed through merged PR #349. This still does **not** establish an SLA,
   unlimited scale, network-filesystem safety, or general multiprocess production proof.
4. **Observability is not a universal persisted long-term causal trace store.** Metrics,
   logs, TRACE and bounded receipts exist, but “why did the system answer this way last
   week?” is not universally reconstructable as first-class durable evidence.
5. **Mutation ownership remains family-specific.** Standard `Validated` promotion callers
   converge on `PromotionGateway`/canonical CAS, while ordinary non-Validated transitions,
   invalidation, relation lifecycle, compound supersession, archival/redaction, erasure,
   and other mutation families retain their own explicit contracts.
6. **Version/branding/public-release drift remains a hygiene risk.** Public entrypoints use
   Titan 9.0; historical V8.x material remains history unless explicitly re-adopted by a
   current contract. Historical GitHub Release evidence is not current release evidence.
7. **Evidence-use attribution remains bounded.** Retrieval/selection (R), serialization
   (S), and provider transmission/packing (T) do not establish model semantic use (U) or
   answer support (A). TRACE membership must not be promoted into U/A without separate
   attribution evidence.

## 4. Production-hardening roadmap: P0 / P1 / P2

These priorities are distinct from the completed bounded V1 productization ledger.

### P0 — blocks trustworthy production use

- **GDPR-grade hardening:** extend existing erasure/redaction mechanisms into an actual
  compliance surface with legal/operational proof.
- **Broader storage/concurrency proof:** current promotion ownership and bounded SQLite
  characterization are strong, and #347's bounded bootstrap residual is closed, but
  realistic multiprocess/production storage conditions still require proof.
- **Independent security review** before exposing sensitive real-user data on the public
  internet.

### P1 — materially improves trust and operability

- **Replayable provenance/answer receipts:** durable, independently re-verifiable evidence
  over past answer paths without pretending receipts are truth.
- **Persisted observability:** metrics/trace evidence that survives restart and supports
  reliable retrospective diagnosis.
- **Evidence-use attribution research:** preserve R/S/T/U/A separation and only promote U/A
  when a bounded measurement contract justifies it.

### P2 — access and packaging polish

- **MCP deployment/product evidence:** bounded JSON-RPC transport exists in
  `core/mcp_transport.py`; remaining work is concrete server/deployment admission and
  hardening evidence. Transport presence does not establish enablement or unrestricted
  multi-role access.
- **Lean core packaging:** reduce default-path dependency friction while keeping optional
  server/graph/retrieval features explicit.
- **Version/language-entry hygiene:** keep `README.md` as the English landing page,
  `README.ru.md` as the Russian companion, and preserve compatibility pointers where old
  links exist.

## 5. Retained test / release evidence snapshot

A retained dated evidence snapshot is:

[`docs/evidence/release-evidence-2026-08-14.md`](evidence/release-evidence-2026-08-14.md)

Its historical baseline and CI counts remain **snapshot evidence**, not the current
repository head or evergreen CI state. Any newer candidate, merge, or operator decision
must establish fresh exact-head/post-merge evidence from GitHub.

The historical repository release/tag classified there remains historical rather than
current Titan release evidence. No release is invented merely to make status appear
complete.

## 6. Reviewer-safe summary

Velantrim Titan 9.0 is a **research-grade prototype moving toward production hardening**:
a local-first verifiable memory runtime with explicit epistemic states, controlled
promotion/write boundaries, auditable provenance, hybrid retrieval capability, and a
replaceable language layer. Current `core/pipeline.py::run()` is read-only with respect to
canonical fact/ESM/causal mutation. Hybrid retrieval capability does not imply all dense /
graph dependencies are active in every installation. MCP transport exists as a bounded
module but is not server-wired by default. TRACE and prompt/transmission evidence do not
prove internal model use or final-answer support. The project has meaningful bounded
engineering evidence but no independent security audit, certified compliance program, or
general production-scale storage proof. Green CI, V1 closure, merge, or bounded pilot do
not themselves authorize production deployment.
