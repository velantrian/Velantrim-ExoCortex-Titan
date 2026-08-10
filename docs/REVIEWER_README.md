# Reviewer README — Velantrim Titan 9.0

A map for anyone auditing, reviewing, or evaluating this codebase for the first time —
a security reviewer, a grant/funding reviewer, or an engineer deciding whether to adopt
it. It is not a tutorial; it is a set of pointers to where the real answers live.

Related: [`SECURITY.md`](../SECURITY.md) (security model) and
[`docs/PROJECT_STATUS.md`](PROJECT_STATUS.md) (maturity, roadmap, current risks).

---

## 1. What Velantrim Titan 9.0 is

Velantrim Titan is a **local-first verifiable memory runtime for AI agents**. It sits
between an LLM and the outside world and enforces a separation that a bare LLM call
does not have:

```text
query -> memory -> retrieval -> facts -> Truth Gate -> TRACE -> LLM voice
```

Concretely, that means:

- **Evidence-gated AI memory** — facts move through an explicit epistemic-state
  machine (`core/memory.py`). Standard runtime promotion to `Validated` is routed
  through the reviewed TruthGate-backed promotion boundary; separately inventoried
  special mutation/admission families are not silently treated as that standard path.
- **Auditable provenance** — every accepted fact carries a source, and structural
  integrity is checkable after the fact via an append-only hash chain
  (`core/provenance_chain.py`).
- **Truth-bound generation** — the LLM is used as a "voice" over retrieved,
  gate-checked facts (`TRACE`), not as the source of truth itself.

It runs as a FastAPI HTTP server (`server.py`) over a local SQLite store by default, with
optional pluggable graph backends (Kuzu / LadybugDB / Neo4j-compatible via
`core/storage.py`'s `GraphStore` contract).

## 2. What it is not

Being explicit about this matters more than the marketing copy:

- It is **not** a hosted service or SaaS product — there is no multi-tenant control
  plane; you run and operate your own instance.
- It does **not** produce hallucination-free output. The Truth Gate raises the bar for
  what gets written into memory and cites what it retrieves — it does not verify the
  underlying LLM's free-text generation word-by-word, and gaps are reported
  (`gap_notice`) rather than silently hidden.
- It is **not** a certified, audited security or compliance product. See
  [`SECURITY.md`](../SECURITY.md) §9–11 for exactly what is and isn't covered (e.g. the
  erasure/redaction mechanism is not a certified GDPR compliance program).
- It is **not** a single monolithic "cognitive architecture" you must adopt wholesale.
  Most advanced layers (concept emergence, causal reasoning, identity axis, etc.) are
  off by default and opt-in via `ENABLE_*` environment flags — see §7.
- It does **not** claim any form of subjective experience, consciousness, or agency.
  Modules named things like "identity" or "welfare" are engineering constructs
  (traceability, self-consistency checks, resource-budget monitoring) — see §7 for what
  they actually do.

## 3. Where to inspect first

In priority order, for someone with limited review time:

1. **`server.py`** — the entire HTTP surface: auth (`require_api_key`), CORS, rate
   limiting, and every route. Read this before anything else; it tells you exactly what
   is network-reachable.
2. **`core/memory.py`** — the epistemic-state machine and the canonical fact storage
   primitives. Promotion ownership is described separately in
   `docs/operations/promotion-ownership-inventory.md`.
3. **`core/truth_gate.py`** — the gate a fact must pass before it is trusted.
4. **`core/pipeline.py`** — the read-side orchestration: query → retrieval → facts →
   gate → trace → answer. The query path is explicitly read-only with respect to facts,
   ESM state and causal relations.
5. **`tests/test_invariants.py`** — the executable invariant suite that must pass in
   CI; a failing invariant blocks deployment by design. Read this to see what the
   project itself considers non-negotiable.
6. **`docs/TRUTH_AND_RINGZERO_CANON.en.md`** — the normative Truth Engine + Ring Zero
   specification. Its inline `V8.6:` conformance annotations are a historical
   2026-05-31 snapshot, not current Titan 9.0 implementation status.

## 4. Core modules map

| Area | Module(s) | Role |
|---|---|---|
| Memory / ESM | `core/memory.py` | Fact storage, 8-state epistemic state machine, bi-temporal fields, canonical storage primitives |
| Promotion authority | `core/promotion_gateway.py`, `core/memory.py` | Typed standard promotion boundary + canonical CAS-backed single-fact promotion primitive |
| Truth | `core/truth_gate.py`, `core/adaptive_truth.py`, `core/truth_maintenance.py` | Confidence/evidence thresholds by cognitive mode; reinforce/supersede/contradict over time |
| Provenance | `core/provenance_chain.py`, `core/evidence_pack.py`, `core/evidence_counter.py` | Append-only hash chain, evidence bundling and counting |
| Retrieval | `core/hybrid_retriever.py`, `core/ngram_index.py`, `core/query_router.py`, `core/query_expander.py` | BM25 + dense + graph retrieval, FTS5 candidate narrowing |
| Causal reasoning | `core/causal_graph.py`, `core/causal_retrieval.py`, `core/causal_persistence.py` | 15 relation types, contradiction/chain finding |
| Immune / integrity | `core/meta_supervisor.py`, `core/immutable_core_scheduler.py`, `core/contradiction_registry.py` | HEALTHY/DEGRADED/SAFE_MODE health states, periodic snapshot hashing, contradiction detection |
| Identity axis | `core/identity_layer.py`, `core/stimulus_map.py` | Traceability between stimulus, stored fact, and generated answer — not a claim of selfhood |
| Forgetting / privacy | `core/forgetting.py`, `core/erasure_coordinator.py`, `core/erasure_batch_coordinator.py`, `core/crypto.py` | Legacy compatibility surface over durable erasure coordinators, PII redaction, optional field-level encryption |
| Orchestration | `core/pipeline.py`, `core/app.py` | Query → retrieval → gate → trace → answer; DI container for the server |
| Storage backends | `core/storage.py`, `core/backends/ladybug_graph.py` | `GraphStore` ABC; SQLite (default), Kuzu, LadybugDB |
| LLM integration | `core/provider_catalog.py`, `llm_router` (via `api/llm_routes.py`) | Provider/model catalog, outbound calls gated behind API auth |

## 5. Tests map

- **137 `test_*.py` files** under `tests/` on the documented repository snapshot,
  covering unit, integration, and invariant levels. Treat this as a snapshot count,
  not a live total; re-query or rerun before quoting it as current.
- `tests/test_invariants.py` — the CI-blocking invariant suite referenced in §3.
- `tests/test_truth_gate.py`, `tests/test_write_gate.py` — Truth Gate thresholds and
  the write-time admission gate (source/evidence requirements by claim type).
- `tests/test_promotion_ownership_guard.py` — AST-based lock over reviewed production
  promotion authority call sites.
- `tests/test_truthgate_api_transition.py` — adversarial API promotion and CAS races.
- `tests/test_server_integration.py` — end-to-end HTTP behavior, including
  `TestSecurityIntegration` (auth required, CORS not wildcard-with-credentials, etc.).
- `tests/test_console_security.py` — the console/LLM-proxy auth surface, including a
  regression test that a provider API key is never leaked in a response.
- `tests/test_smoke.py` — fast import/validator/relation-type sanity checks; a good
  first signal that a change hasn't broken basic wiring.

Run the narrow set relevant to a specific concern rather than the full suite when doing
a quick check — see §10 for exact commands.

## 6. Truth / memory / provenance map

This is the core trust chain and worth calling out on its own:

```text
1. store_fact() / store_facts_batch()   core/memory.py    — canonical fact admission/storage
2. Epistemic State Machine (8 states)   core/memory.py    — Observed → ... → Validated/Collapsed
3. PromotionGateway                     core/promotion_gateway.py — typed standard promotion boundary
4. Truth Gate                           core/truth_gate.py — confidence + evidence policy before Validated
5. Canonical promotion CAS              core/memory.py    — durable snapshot + guarded update
6. Version/Audit evidence               same transaction  — required pre-image + AuditChain event
7. TRACE                                core/pipeline.py  — read-side retrieval → fact → answer path
8. Ring Zero (immutable core)           core/memory.py:IMMUTABLE_FACT_IDS — never ordinary-mutable/deletable
```

Verdicts returned by the Truth Gate are one of `allow`, `gap_notice`, or `reject` — a
`gap_notice` is the system's way of saying "I don't have enough evidence for this,"
rather than answering with unsupported confidence.

### Current promotion ownership

A previous version of this reviewer map said `POST /query` could promote retrieved facts
through a legacy pipeline branch. **That is historical and no longer true.** Current
`core/pipeline.py::run()` is read-only with respect to fact storage, ESM promotion and
causal-relation mutation. Any future query-side write authority would require a new
architecture decision and must pass the architecture-freeze and ownership guards.

Five standard production promotion callers are currently routed through
`PromotionGateway`:

1. graduated promotion (`core/promotion_policy.py`);
2. `ConsolidationEngine`;
3. `PATCH /facts/{fact_id}/transition` when the target is `Validated`;
4. `core/tool_handlers.py::validate_fact`;
5. `core/cognitive_store.py::CognitiveFactStore.transition` (including its
   `CognitiveRuntime` delegation).

The gateway delegates to `SQLiteGraphStore.validate_and_promote()`. The canonical
single-fact path uses the durable L1 fact snapshot, ESM legality checks, TruthGate,
a CAS-guarded canonical update, `VersionStore` pre-image and `AuditChain` event in the
same SQLite transaction. When projection-outbox migration 020 is active, the required
content-minimized outbox intent joins that same transaction; an activated-but-invalid
outbox schema fails closed and rolls the promotion back. See
`docs/operations/promotion-ownership-inventory.md`.

An AST-based CI guard (`tests/test_promotion_ownership_guard.py`) inventories reviewed
calls to `validate_and_promote()`, `promote_to_validated()` and literal `Validated`
transitions. A new unreviewed production site is a blocking failure until both the ADR
and ownership inventory are deliberately updated.

### Boundaries that remain separate

This does **not** mean every mutation in Titan is owned by `PromotionGateway`:

- ordinary non-Validated ESM transitions remain ordinary ESM operations;
- `core/truth_maintenance.py::supersede()` is a compound mutation: it TruthGate-checks
  the replacement and atomically commits new-fact validation + old-fact deprecation in
  its own facts transaction; its causal `SUPERSEDED_BY` relation and provenance event
  are still best-effort post-commit artifacts on separate stores;
- `core/world_skills_ingest.py` remains one explicit, CI-locked curated-ingest exception
  pending a separate curated-pack admission contract;
- invalidation, relation lifecycle, archival/redaction and erasure have separate
  contracts and must be audited as separate mutation families rather than silently
  treated as promotion.

The correct review question is therefore not "does one global function own every
mutation?" but "does each mutation family have one explicit authority, required atomic
evidence, and a CI-visible bypass policy?"

## 7. Security map

See [`SECURITY.md`](../SECURITY.md) for the full write-up. Short version, with pointers:

| Control | Where |
|---|---|
| API key required at startup, `X-Api-Key` auth, constant-time compare | `server.py` (`require_api_key`, `API_KEY`) |
| CORS default-deny (empty allowlist, not `*`) | `server.py` (`CORS_ORIGINS`) |
| Swagger/OpenAPI hidden unless `ENABLE_API_DOCS=true` | `server.py` (`_API_DOCS`) |
| Per-IP token-bucket rate limiting (opt-in) | `core/rate_limit.py`, gated by `ENABLE_RATE_LIMIT` |
| Optional field-level encryption at rest | `core/crypto.py`, gated by `VELANTRIM_ENCRYPTION_KEY` |
| Erasure / PII redaction mechanism | `core/forgetting.py`, durable coordinators |
| Production vs. dev Docker separation | `docker-compose.yml` (requires a key) vs. `docker-compose.dev.yml` (dev default) |

## 8. Stable vs. experimental areas

| Status | Areas |
|---|---|
| 🟢 Stable / product-leaning | Memory + ESM + bi-temporal fields, HTTP API + web console, Truth Gate + cognitive modes, provenance chain, hybrid retrieval (BM25 + dense + graph) |
| 🟡 Working, research-grade | Causal graph, forgetting/decay/reconsolidation, LLM orchestration (router/stream/multilingual), capability-based tool registry (contract defined, some handlers are stubs) |
| 🟡 Proof-of-concept, not hardened | Noetic/meta-cognition, Essence/Velum, Perspectives/poly-welt, concept emergence, goals/curiosity/volition, identity/welfare/interoception (L6) |
| 🔴 Known gap | Formal GDPR compliance program (mechanism exists, program doesn't), production-scale operational characterization, persisted long-term observability, MCP gateway transport (registry exists, no server) |

Most 🟡/🔴 layers above L1 are **off by default** and only activate via explicit
`ENABLE_*` flags (see `README.md` → ExoCortex optional flags) — the default startup
path only exercises the 🟢 row.

## 9. Known limitations

- No independent third-party security audit or penetration test has been performed.
- SQLite concurrency and crash behavior have **bounded characterization**: PR #174
  covered one-store 100-thread writes, a `1/10/25/50/100` writer matrix, 25 independent
  store instances on one WAL database, mixed readers/writers, committed crash survival,
  uncommitted rollback and `integrity_check = ok`. This is not production-scale or
  unlimited-concurrency proof; issue #249 remains an uncharacterized CAS-contention
  failure and realistic multiprocess/storage-environment proof is still open.
- Observability is metrics + structured logs (`core/metrics.py`,
  `core/lightweight_metrics.py`); there is no persisted long-term trace store yet for
  answering "why did the system respond this way" after the fact at scale.
- The capability-based tool registry (`core/tool_registry.py`) defines a contract for
  role-scoped agent access, but some handlers are placeholder stubs pending the MCP
  gateway transport.
- Test coverage is broad but uneven across layers — treat the 🟢 row in §8 as the
  bar that's actually been exercised; treat 🟡/🔴 as "read the code, don't assume."

See [`docs/PROJECT_STATUS.md`](PROJECT_STATUS.md) for the prioritized roadmap addressing
these.

## 10. Minimal verification commands

Enough to confirm the repository is in the state it claims to be, without standing up a
full deployment:

```bash
# 1. Confirm the package installs cleanly and reports the expected version
python -m pip install -e ".[server,dev]"
python -c "import core; print(core.__version__)"   # expect 9.0.0

# 2. Static checks
ruff check core/
mypy core/

# 3. Narrow, fast test slice (invariants + truth/write gate + smoke)
pytest tests/test_smoke.py tests/test_invariants.py tests/test_truth_gate.py tests/test_write_gate.py -v

# 4. Confirm the server actually enforces auth (refuses to boot without a key)
python -c "import server"   # should raise RuntimeError unless VELANTRIM_API_KEY or
                             # VELANTRIM_ALLOW_OPEN=true is set

# 5. Docker config sanity (production requires a real key; dev does not)
docker compose config                                # fails without VELANTRIM_API_KEY
VELANTRIM_API_KEY=test-secret docker compose config  # succeeds
docker compose -f docker-compose.dev.yml config      # succeeds with a dev default
```
