# Reviewer README — Velantrim Titan 9.0

This is a reviewer-oriented map, not runtime proof.

> **Audited base:** `main@70bc34fecdcf0bae15bc2264445e31b87b79bf08` on 2026-09-08.
> Re-query live GitHub for mutable state. Exact code/tests/CI/config/runtime evidence
> override this document on conflict.

[README](../README.md) · [Русский README](../README.ru.md) ·
[Project Status](PROJECT_STATUS.md) · [Security](../SECURITY.md)

---

## 1. What Titan is

Velantrim Titan is a local-first memory/orchestration runtime for AI agents with explicit
epistemic states, controlled canonical mutation, retrieval, provenance/audit, authenticated
tool/MCP surfaces, and replaceable model/provider execution.

```text
retrieval ≠ evidence
admission ≠ verification
model output ≠ Canon
TRACE membership ≠ semantic use ≠ answer support
capability ≠ permission
implemented ≠ wired ≠ enabled ≠ observed
```

## 2. Inspect these first

For AI coding/review work: [`../AGENTS.md`](../AGENTS.md) → [`ai/README.md`](ai/README.md).

For independent technical review:

1. `server.py` — network surface, auth, route registration, runtime composition;
2. `core/memory.py` — ESM/canonical storage;
3. `core/promotion_gateway.py` + `core/truth_gate.py` — standard Validated promotion boundary;
4. `core/pipeline.py` — read/query orchestration;
5. `api/mcp_gateway.py` + `core/mcp_transport.py` + `core/tool_registry.py` — MCP/tool boundary;
6. focused tests and current CI;
7. accepted ADR/current-state docs only after executable evidence.

## 3. Current read/query truth

`core/pipeline.py::run()` is read-only with respect to canonical fact storage, ESM
promotion, and causal-relation mutation. The older statement that `POST /query` itself
promotes retrieved facts is historical.

Legacy comments/docstrings in `server.py` can still describe the old sequence; they are
code-adjacent documentation debt and do not override the executable pipeline.

Standard `Validated` promotion callers route through `PromotionGateway` and the canonical
CAS-backed store path. Separate mutation families keep separate owners/contracts.

## 4. Retrieval truth

`HybridRetriever` supports lexical/BM25-style retrieval, optional dense embeddings,
optional graph signals, and ranking fusion. Do not infer that every installation executes
all signals on every request. Optional dependencies/configuration can narrow the path.
Ranking score is not evidence authority.

## 5. MCP truth

Current MCP is **implemented and server-wired**, not merely a dormant module:

```text
server.py
  → register_mcp_routes(app, auth_dependency=require_api_key)
  → api.mcp_gateway
  → McpHandler
  → ToolRegistry
```

The gateway provides authenticated StreamableHTTP/SSE-style handling, capability/session
resolution, and bounded idempotency behavior through the existing transport/registry.

Do not overclaim from this:

```text
server-wired + auth-gated
  ≠ enabled/exposed in every deployment
  ≠ observed in a concrete runtime
  ≠ unrestricted capability
  ≠ production authorization
```

## 6. Evidence-use / TRACE truth

The bounded evidence-use contract separates:

```text
R = retrieved / selected
S = serialized into answer prompt
T = survives provider-specific packing / transmission
U = demonstrably used by the model
A = demonstrably supports final answer
```

R/S/T do not establish U or A. Prompt presence, transmission, model self-report, or TRACE
membership are not automatically proof of internal causal use or answer support.

## 7. Security / production limits

- no independent third-party security audit is claimed;
- no certified GDPR/compliance program is claimed;
- SQLite/concurrency evidence is bounded, not unlimited production-scale proof;
- Issue #347's specific concurrent fresh-store bootstrap residual is closed through merged
  PR #349, while broader multiprocess/storage-environment proof remains open;
- remote provider calls remain behind PolicyKernel/remote-egress controls;
- server route registration is not runtime observation or production authorization.

## 8. Stable vs gated/research

| Status | Examples |
|---|---|
| 🟢 product-leaning foundation | memory/ESM, API, core truth/write boundaries, provenance, read orchestration |
| 🟡 dependency/config gated | dense/graph retrieval signals, causal/reasoning/adaptive layers |
| ✅ wired but deployment-dependent | authenticated MCP gateway/tool surface |
| 🔬 research/shadow | Synaptic answer integration, higher cognitive compositions |
| 🔴 production-hardening gaps | independent security review, compliance program, broad operational proof |

## 9. Verification baseline

```bash
python -m pip install -e ".[server,dev]"
python -c "import core; print(core.__version__)"
ruff check core/
mypy core/
pytest tests/test_smoke.py tests/test_invariants.py \
       tests/test_truth_gate.py tests/test_write_gate.py -v
```

For deployment/runtime claims, inspect the selected Compose/profile, live status endpoints,
and current GitHub Actions evidence. Green CI is evidence only.
