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
  machine (`core/memory.py`) and are only promoted to a trusted state after passing
  `core/truth_gate.py`, not just because an LLM said so.
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
2. **`core/memory.py`** — the epistemic-state machine and the single write path
   (`store_fact`, `transition_esm`). Almost every invariant in the project is enforced
   here or by callers of these functions.
3. **`core/truth_gate.py`** — the gate a fact must pass before it is trusted.
4. **`core/pipeline.py`** — the orchestration: how a query becomes retrieval → facts →
   gate → trace → answer.
5. **`tests/test_invariants.py`** — 18 executable invariants that must pass in CI; a
   failing invariant blocks deployment by design. Read this to see what the project
   itself considers non-negotiable.
6. **`docs/TRUTH_AND_RINGZERO_CANON.en.md`** — the canonical spec for the Truth Engine +
   Ring Zero (immutable core), verdicts (`allow`/`gap_notice`/`reject`), and invariants
   I0–I8.

## 4. Core modules map

| Area | Module(s) | Role |
|---|---|---|
| Memory / ESM | `core/memory.py` | Fact storage, 8-state epistemic state machine, bi-temporal fields, the single write path |
| Truth | `core/truth_gate.py`, `core/adaptive_truth.py`, `core/truth_maintenance.py` | Confidence/evidence thresholds by cognitive mode; reinforce/supersede/contradict over time |
| Provenance | `core/provenance_chain.py`, `core/evidence_pack.py`, `core/evidence_counter.py` | Append-only hash chain, evidence bundling and counting |
| Retrieval | `core/hybrid_retriever.py`, `core/ngram_index.py`, `core/query_router.py`, `core/query_expander.py` | BM25 + dense + graph retrieval, FTS5 candidate narrowing |
| Causal reasoning | `core/causal_graph.py`, `core/causal_retrieval.py`, `core/causal_persistence.py` | 15 relation types, contradiction/chain finding |
| Immune / integrity | `core/meta_supervisor.py`, `core/immutable_core_scheduler.py`, `core/contradiction_registry.py` | HEALTHY/DEGRADED/SAFE_MODE health states, periodic snapshot hashing, contradiction detection |
| Identity axis | `core/identity_layer.py`, `core/stimulus_map.py` | Traceability between stimulus, stored fact, and generated answer — not a claim of selfhood |
| Forgetting / privacy | `core/forgetting.py`, `core/crypto.py` | Erasure/redaction mechanism, optional field-level encryption at rest |
| Orchestration | `core/pipeline.py`, `core/app.py` | Query → retrieval → gate → trace → answer; DI container for the server |
| Storage backends | `core/storage.py`, `core/backends/ladybug_graph.py` | `GraphStore` ABC; SQLite (default), Kuzu, LadybugDB |
| LLM integration | `core/provider_catalog.py`, `llm_router` (via `api/llm_routes.py`) | Provider/model catalog, outbound calls gated behind API auth |

## 5. Tests map

- **91 test files** under `tests/`, covering unit, integration, and invariant levels.
- `tests/test_invariants.py` — the 18 CI-blocking invariants referenced in §3.
- `tests/test_truth_gate.py`, `tests/test_write_gate.py` — Truth Gate thresholds and
  the write-time admission gate (source/evidence requirements by claim type).
- `tests/test_server_integration.py` — end-to-end HTTP behavior, including
  `TestSecurityIntegration` (auth required, CORS not wildcard-with-credentials, etc.).
- `tests/test_console_security.py` — the console/LLM-proxy auth surface, including a
  regression test that a provider API key is never leaked in a response.
- `tests/test_smoke.py` — fast import/validator/relation-type sanity checks; a good
  first signal that a change hasn't broken basic wiring.

Run the narrow set relevant to a specific concern rather than the full suite when doing
a quick check — see §9 for exact commands.

## 6. Truth / memory / provenance map

This is the core trust chain and worth calling out on its own:

```text
1. store_fact() / store_facts_batch()   core/memory.py    — single write entry point
2. Epistemic State Machine (8 states)   core/memory.py    — Observed → ... → Validated/Collapsed
3. Truth Gate                           core/truth_gate.py — confidence + evidence thresholds
                                                              per CognitiveMode before Validated
4. Provenance chain                     core/provenance_chain.py — append-only hash chain,
                                                                    tamper-evidence via verify()
5. TRACE                                core/pipeline.py  — records retrieval → fact →
                                                              answer path for replay
6. Ring Zero (immutable core)           core/memory.py:IMMUTABLE_FACT_IDS — never transitions,
                                                                            never deleted
```

Verdicts returned by the Truth Gate are one of `allow`, `gap_notice`, or `reject` — a
`gap_notice` is the system's way of saying "I don't have enough evidence for this,"
rather than answering with unsupported confidence.

**API-level enforcement (tested):** `PATCH /facts/{fact_id}/transition` is the only
public HTTP endpoint that can move a fact into `Validated`. When the requested target
is `Validated`, `server.py` routes the request through
`core.memory.SQLiteGraphStore.validate_and_promote()` — the single canonical function
that runs `TruthGate.evaluate()` (mode `BALANCED`, `contradiction_detector="none"` — the
active-contradiction check is skipped until an NLI detector is wired in; only
source/confidence/evidence are enforced today) against the fact's stored source,
confidence, and evidence, and only mutates state on a passing verdict. A rejected
verdict returns `422` with the reason, leaves the fact's epistemic state and history
untouched, and never calls an LLM. ESM-transition legality (invariant I50) is checked
before TruthGate runs, so an illegal jump (e.g. a direct `Observed → Validated` request)
always returns `400`, regardless of how strong the fact's evidence is. All other ESM
targets on that endpoint (e.g. `Hypothesized`, `Supported`, `Contradicted`,
`Deprecated`) are unaffected. The function also closes a TOCTOU race: the fact snapshot
`TruthGate.evaluate()` scores is pinned via an optimistic `updated_at` compare-and-swap
at write time, so a concurrent `POST /facts` upsert that weakens the fact's
confidence/evidence between the check and the write aborts the promotion (`409
concurrent_modification`) instead of silently validating a now-weak fact. See
`tests/test_truthgate_api_transition.py` for the adversarial coverage this claim rests
on. Internal, non-API promotion paths (pipeline ingestion, `ConsolidationEngine`,
graduated promotion) apply their own pre-vetting policy before calling the lower-level
ESM primitives — this section describes the API boundary specifically, not a claim
that every code path uses byte-identical TruthGate policy or has the same CAS
protection.

## 7. Security map

See [`SECURITY.md`](../SECURITY.md) for the full write-up. Short version, with pointers:

| Control | Where |
|---|---|
| API key required at startup, `X-Api-Key` auth, constant-time compare | `server.py` (`require_api_key`, `API_KEY`) |
| CORS default-deny (empty allowlist, not `*`) | `server.py` (`CORS_ORIGINS`) |
| Swagger/OpenAPI hidden unless `ENABLE_API_DOCS=true` | `server.py` (`_API_DOCS`) |
| Per-IP token-bucket rate limiting (opt-in) | `core/rate_limit.py`, gated by `ENABLE_RATE_LIMIT` |
| Optional field-level encryption at rest | `core/crypto.py`, gated by `VELANTRIM_ENCRYPTION_KEY` |
| Erasure / PII redaction mechanism | `core/forgetting.py` |
| Production vs. dev Docker separation | `docker-compose.yml` (requires a key) vs. `docker-compose.dev.yml` (dev default) |

## 8. Stable vs. experimental areas

| Status | Areas |
|---|---|
| 🟢 Stable / product-leaning | Memory + ESM + bi-temporal fields, HTTP API + web console, Truth Gate + cognitive modes, provenance chain, hybrid retrieval (BM25 + dense + graph) |
| 🟡 Working, research-grade | Causal graph, forgetting/decay/reconsolidation, LLM orchestration (router/stream/multilingual), capability-based tool registry (contract defined, some handlers are stubs) |
| 🟡 Proof-of-concept, not hardened | Noetic/meta-cognition, Essence/Velum, Perspectives/poly-welt, concept emergence, goals/curiosity/volition, identity/welfare/interoception (L6) |
| 🔴 Known gap | Formal GDPR compliance program (mechanism exists, program doesn't), contract/concurrency stress testing, persisted long-term observability, MCP gateway transport (registry exists, no server) |

Most 🟡/🔴 layers above L1 are **off by default** and only activate via explicit
`ENABLE_*` flags (see `README.md` → ExoCortex optional flags) — the default startup
path only exercises the 🟢 row.

## 9. Known limitations

- No independent third-party security audit or penetration test has been performed.
- Concurrency has not been stress-tested (no automated 100+ concurrent writer test yet);
  the default storage path is synchronous SQLite with a per-operation connection.
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
docker compose config                              # fails without VELANTRIM_API_KEY
VELANTRIM_API_KEY=test-secret docker compose config  # succeeds
docker compose -f docker-compose.dev.yml config      # succeeds with a dev default
```
