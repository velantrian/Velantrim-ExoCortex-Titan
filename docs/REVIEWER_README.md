# 🔍 Reviewer README — Velantrim Titan 9.0

A bounded map for security reviewers, engineers, funders, and independent auditors.

**Audited base:** `main@70bc34fecdcf0bae15bc2264445e31b87b79bf08` on 2026-09-08.  
**Freshness rule:** re-query GitHub for current branch/PR/check/runtime state; this is a dated implementation checkpoint.

Related: [`README.md`](../README.md), [`SYSTEM_OVERVIEW.en.md`](../SYSTEM_OVERVIEW.en.md),
[`PROJECT_STATUS.md`](PROJECT_STATUS.md), [`SECURITY.md`](../SECURITY.md).

---

## 1. What Titan is

Velantrim Titan is a **local-first verifiable memory runtime for AI agents** with explicit
separation between memory state, retrieval, evidence/admission, policy, audit/provenance,
and language generation.

```text
query → memory → retrieval → admitted context → policy/TruthGate → TRACE → optional LLM voice
```

This does not mean every arrow is one monolithic synchronous path, nor that TRACE proves
internal model use. Review status and wiring separately.

Core invariants:

```text
retrieval ≠ evidence
admission ≠ verification
confidence ≠ authority
model output ≠ Canon
TRACE membership ≠ semantic use U ≠ answer support A
CI green ≠ production authorization
```

---

## 2. What to inspect first

1. `server.py` — network surface, auth, CORS, runtime wiring, LLM path.
2. `core/memory.py` — ESM and canonical fact primitives.
3. `core/promotion_gateway.py` + `core/truth_gate.py` — standard Validated promotion boundary.
4. `core/pipeline.py` — current read-side query orchestration.
5. `core/remote_egress.py` + `core/llm_router.py` — remote policy and prompt/provider boundary.
6. `tests/test_invariants.py`, `tests/test_promotion_ownership_guard.py`, focused component tests.
7. `docs/ai/CURRENT_STATE.md`, `docs/ai/KNOWN_RISKS.md`, then live GitHub.

Do not infer current behavior from historical V8.x comments or archived audits when exact
current code contradicts them.

---

## 3. Current read/write truth

### Query path

`core/pipeline.py::run()` is **read-only** with respect to canonical fact storage, ESM
promotion, and causal-relation mutation. The old documentation claim that legacy
`POST /query` may promote retrieved facts is historical and no longer current.

### Standard promotion

Standard production callers targeting `Validated` route through `PromotionGateway`,
which delegates to the canonical `SQLiteGraphStore.validate_and_promote()` path and its
reviewed TruthGate/CAS/audit contract.

This is not one global owner for every mutation family. Ordinary non-Validated ESM
transitions, invalidation, erasure, archival/redaction, relation lifecycle, and compound
supersession retain separate explicit contracts and must be reviewed separately.

---

## 4. Retrieval truth

`core/hybrid_retriever.py` supports lexical/BM25-style retrieval, dense embeddings,
optional graph signals, and ranking fusion. Availability is dependency/configuration
sensitive.

Do **not** translate “hybrid retriever exists” into “every request executes BM25 + dense +
graph.” The base package has no mandatory third-party dependencies; enhanced retrieval
features require optional extras and can degrade to narrower paths.

Ranking/relevance is not evidence or truth authority.

---

## 5. Prompt / evidence-use truth

The current server answer path serializes selected facts through
`server._build_system_prompt()` and sends remote calls through the mandatory remote-egress
boundary. `core.remote_egress.sanitize_remote_system_prompt()` prevents legacy prompt
labels from silently elevating mixed-status memory to verified evidence before remote
provider transmission.

The bounded evidence-use tests explicitly separate:

```text
R = retrieved / selected
S = serialized into system prompt
T = survives provider-specific message packing
U = demonstrably used by the model          NOT established by R/S/T alone
A = demonstrably supports the final answer  NOT established by R/S/T alone
```

Do not claim U or A from TRACE membership, prompt presence, provider transmission,
model self-report, or answer change alone.

---

## 6. MCP status

`core/tool_registry.py` and `core/mcp_transport.py` contain a bounded capability-based
JSON-RPC transport implementation with capability ceilings, session handling, tool
visibility checks, and bounded process-local idempotency behavior.

Reality status:

```text
IMPLEMENTED_BOUNDED: yes
server-wired by default: no
enabled merely by module presence: no
runtime authority: no
production authorization: no
```

Therefore both of these claims are wrong:

- “only a registry exists; there is no transport” — stale;
- “transport exists, therefore MCP is deployed/active” — overclaim.

---

## 7. Concurrency / storage status

Issue #249 was characterized as a harness-scope / historical runner-sensitivity problem;
a product CAS defect was not confirmed by the retained one-winner/one-intent evidence.

The distinct fresh-store bootstrap residual tracked in Issue #347 was **closed** through
the bounded serialization fix merged in PR #349. That closes the supported bounded
first-use scenario only. It does not establish an SLA, unlimited concurrency,
network-filesystem safety, or general production multiprocess proof.

---

## 8. Stable vs bounded / experimental

| Area | Current reviewer-safe statement |
|---|---|
| Memory + ESM | implemented/tested core primitives |
| Standard Validated promotion | converged through reviewed gateway/CAS path |
| Query pipeline | read-only for canonical fact/ESM/causal mutation |
| Retrieval | hybrid-capable; actual signals depend on dependency/config/runtime |
| Provenance/audit | implemented surfaces; do not overclaim full replayability of every past answer |
| Remote LLM egress | policy-gated; prompt sanitizer preserves epistemic boundary |
| Synaptic | implemented/tested foundation + shadow-only pieces; no active answer authority |
| MCP transport | bounded implementation present; not default server-wired |
| Identity/welfare/noetic layers | research/proof-of-concept; no consciousness claim |
| Production readiness | not established; see `PROJECT_STATUS.md` P0/P1 |

---

## 9. V1 vs production-hardening scope

The bounded V1 productization ledger may report **V1 P0 = 0 / V1 P1 = 0** and
`TITAN_V1_DONE`. That means the frozen V1 productization program closed its admitted
scope.

It does **not** mean production-hardening P0/P1 is empty, production authorization exists,
or sensitive internet-facing multi-user deployment is approved. Keep these scopes
explicitly separate.

---

## 10. Minimal verification commands

```bash
python -m pip install -e ".[server,dev]"
python -c "import core; print(core.__version__)"
ruff check core/ --output-format=github
mypy core/ --show-error-codes
pytest tests/test_smoke.py tests/test_invariants.py tests/test_truth_gate.py tests/test_write_gate.py -v
```

For the evidence-use boundary, also inspect/run `tests/test_evidence_use_contract.py`.
For promotion ownership, inspect/run `tests/test_promotion_ownership_guard.py` and
`tests/test_truthgate_api_transition.py`.

---

## 11. Reviewer-safe conclusion

Titan 9.0 is a **research-grade local-first verifiable-memory prototype moving toward
production hardening**. The core memory/truth/promotion/read boundaries are materially
more mature than the research layers, but implementation presence, test coverage, wiring,
enablement, observation, and production authorization remain separate claims.

A correct review should prefer exact code/tests/CI over narrative docs, preserve authority
boundaries, and downgrade any statement that turns retrieval, ranking, TRACE, model output,
or bounded CI evidence into stronger truth/production claims than the evidence supports.
