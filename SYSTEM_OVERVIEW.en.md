# 🗺️ Velantrim Titan 9.0 — Living System Atlas

> **Role:** architecture/navigation map for users, engineers, operators, reviewers, and AI agents.
>
> **Product version:** <!-- SYNC:VERSION -->v9.0.0<!-- /SYNC:VERSION -->
> **Audited base:** `main@70bc34fecdcf0bae15bc2264445e31b87b79bf08` on 2026-09-08.
> This is a dated verification checkpoint, not an evergreen remote-head claim.
>
> Code at the exact SHA, tests/CI, selected configuration, and observed runtime evidence
> override this document on conflict.

**English** · [Русский](SYSTEM_OVERVIEW.md) · [README](README.md) ·
[Project status](docs/PROJECT_STATUS.md) · [Reviewer map](docs/REVIEWER_README.md)

---

<a id="plain"></a>

## 👋 Titan in 30 seconds

Titan is a local-first verifiable memory/orchestration runtime for AI agents. Its central
engineering idea is **authority separation**:

```text
source → memory → retrieval → policy/admission → answer/action
```

```text
retrieval ≠ evidence
admission ≠ verification
model output ≠ Canon
TRACE membership ≠ semantic use ≠ answer support
capability ≠ permission
wired ≠ enabled ≠ observed
```

The LLM/provider layer is replaceable. Canon mutation, policy, provenance, and tool
permission do not become model authority merely because an LLM generated the text.

---

<a id="evidence"></a>

## 🧾 Status / source-of-truth rules

```text
proposed ≠ implemented ≠ tested ≠ wired ≠ enabled ≠ observed
```

For implementation questions use this order:

1. executable code at the exact SHA;
2. tests and current CI;
3. selected configuration and runtime observation;
4. current-state docs / accepted ADRs;
5. PR/work-log history;
6. historical/archive material.

Green CI, a merged PR, a feature flag, or a registered route is evidence about a bounded
claim; none is automatically Operator GO or production authorization.

---

<a id="map"></a>

## 🗺️ L1 — system map

```text
HUMAN / AGENT / FILE
        │
        ▼
 API · auth · policy
        │
 ┌──────┼───────────────┐
 ▼      ▼               ▼
READ   WRITE          TOOLS/MCP
 │      │               │
 ▼      ▼               ▼
retrieval/ESM       capability + auth
context  + CAS          boundary
 │      │               │
 └──────┴───────┬───────┘
                ▼
       provenance / audit
                │
        ┌───────┴───────┐
        ▼               ▼
 derived projections   replaceable LLM/provider
```

| Area | Primary surface | Boundary |
|---|---|---|
| Memory/ESM | `core/memory.py` | canonical fact state |
| Standard promotion | `core/promotion_gateway.py` + canonical store primitive | reviewed `Validated` path |
| Read orchestration | `core/pipeline.py` | current `run()` is mutation-read-only |
| Retrieval | `core/hybrid_retriever.py`, `core/ngram_index.py` | lexical baseline + optional dense/graph signals |
| Policy/write | `core/truth_gate.py`, `core/write_gate.py`, `core/policy_kernel.py` | trust/permission boundaries |
| Provenance/audit | `core/provenance_chain.py`, `core/audit_chain.py` | evidence about system effects, not truth itself |
| MCP/tools | `api/mcp_gateway.py`, `core/mcp_transport.py`, `core/tool_registry.py` | authenticated server-wired capability surface |
| Remote LLM | `core/remote_egress.py`, `core/llm_router.py` | fail-closed egress lease + prompt guard |
| Synaptic | reader/capsule/context/shadow surfaces | no active answer-authority transfer |

---

<a id="flows"></a>

## 🔄 L2 — current flows

### Read/query

```text
query
  → API boundary
  → QueryPipeline
  → candidate narrowing / retrieval
  → FactsPackBuilder / Guardian / truth policy
  → structured result + TRACE
  → optional LLM rendering
```

**Current truth:** `core/pipeline.py::run()` is read-only with respect to canonical fact
storage, ESM promotion, and causal-relation mutation. The old statement that legacy
`POST /query` itself performs promotion is stale.

Note that some comments/docstrings in legacy server code may still describe the older
pipeline sequence; executable pipeline behavior and tests take precedence until those
comments are separately cleaned up.

### Write/admission

```text
candidate/source
  → provenance/metadata
  → applicable write/ESM/policy checks
  → owning mutation service
  → CAS / required durable evidence
  → canonical state
  → derived projections / audit artifacts
```

Standard `Validated` promotion converges on `PromotionGateway`; this does not imply that
all mutation families share one global owner.

### MCP/tools

```text
HTTP/SSE MCP request
  → FastAPI auth (`require_api_key`)
  → `api.mcp_gateway`
  → capability/session resolution
  → `McpHandler`
  → `ToolRegistry`
```

This is **implemented + server-wired + auth-gated** on the audited code base. Whether a
specific deployment is currently running/exposed and whether a concrete request has been
observed are separate runtime claims. Production authorization remains separate again.

---

## 🔍 Retrieval precision

`HybridRetriever` supports lexical/BM25-style retrieval, dense embeddings, optional graph
signals, and ranking fusion. Availability is dependency/configuration-sensitive:

```text
hybrid capability exists
  ≠ every optional dependency is installed
  ≠ every signal executes on every query
  ≠ ranking score is evidence/truth authority
```

---

## 🧠 Evidence-use precision

Current bounded measurement distinguishes:

```text
R = retrieved / selected
S = serialized into the prompt
T = survives provider-specific packing / transmission
U = demonstrably used by the model
A = demonstrably supports the final answer
```

R/S/T can be observed in bounded Titan fixtures. R/S/T do not establish U or A without
separate attribution evidence.

---

## 📄 Synaptic profile

```text
Raw evidence
  → SemanticReader
  → KnowledgeCapsule + SourceSpan
  → LLM Reader Adapter (main/tested; standalone caller)
  → Working Memory Gate (shadow-only)
  → ContextPack (shadow-only)
  → shadow evaluation (feature-gated; no answer authority)
```

Active Synaptic answer authority remains **not transferred**. Shadow wiring does not grant
Canon/ESM write authority or answer authority.

---

<a id="engineer"></a>

## 🧑‍💻 Engineering boundaries

- read/retrieval paths must not silently become canonical write paths;
- derived indexes/vectors/graphs do not outrank Canon;
- remote/model output does not self-admit into Canon;
- PolicyKernel denial cannot be weakened by routing or preference;
- tool capability names do not themselves grant permission;
- TRACE/audit show observable system artifacts, not hidden model cognition;
- `UNKNOWN` must not be silently rewritten as `FALSE` or `ABSENT`;
- research/shadow code does not gain runtime authority by being implemented.

---

<a id="assurance"></a>

## 🧪 Architecture Assurance

Architecture Assurance is an engineering loop, not another cognitive authority:

```text
model / invariant
  → bounded implementation
  → deterministic tests / fault injection / load
  → retained metrics/evidence
  → correction
```

Existing SQLite/concurrency evidence is bounded characterization, not unlimited
multiprocess, network-filesystem, SLA, or production-scale proof.

---

## 🚫 This Atlas does not claim

- zero hallucinations or absolute source truth;
- certified GDPR/compliance;
- an independent security audit that has not occurred;
- that every optional layer is enabled;
- that MCP server wiring means a deployment is observed or production-authorized;
- that TRACE proves semantic use or answer support;
- that bounded V1 closure means production-hardening P0/P1 are closed.

For production-hardening status use [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).
