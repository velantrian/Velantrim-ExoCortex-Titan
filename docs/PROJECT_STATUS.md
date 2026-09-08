# Project Status — Velantrim Titan 9.0

> **Status:** CURRENT STATUS GUIDE
>
> **Live-state rule:** mutable repository facts (current main SHA, PR/Issue/check state,
> deployment state) must be verified live when they matter. Dated evidence is snapshot
> evidence, not an evergreen remote-state claim.
>
> **Scope rule:** P0/P1/P2 in this document are **production-hardening priorities**.
> They are distinct from the closed bounded **V1 productization** counters in
> `docs/project_status/FOR_AI.json`. `V1 P0/P1 = 0` does not mean production-hardening
> P0/P1 = 0 and does not authorize production.

**Public version:** Titan 9.0 (`pyproject.toml` / `core.__version__`).

**Summary:** research-grade local-first memory/orchestration runtime moving toward
production hardening. Core memory/ESM, controlled mutation, API, retrieval orchestration,
provenance/audit, and authenticated MCP/tool surfaces are implemented; optional research,
provider, retrieval, and cognitive layers have separate wiring/enablement states.

---

## 1. Current engineering foundation

- **Memory + ESM** — `core/memory.py`; canonical fact state and temporal/epistemic primitives.
- **Standard Validated promotion** — `core/promotion_gateway.py` → canonical CAS-backed store path.
- **Read/query path** — current `core/pipeline.py::run()` is read-only with respect to
  canonical fact storage, ESM promotion, and causal-relation mutation.
- **Truth/write policy** — `core/truth_gate.py`, `core/write_gate.py`, `core/policy_kernel.py`.
- **Provenance/audit** — `core/provenance_chain.py`, `core/audit_chain.py`.
- **Retrieval** — lexical/BM25-style baseline plus optional dense/graph signals and ranking
  fusion; availability depends on optional dependencies/configuration.
- **MCP/tools** — `server.py` registers authenticated routes from `api/mcp_gateway.py`,
  which delegates to `core/mcp_transport.py` / `core/tool_registry.py`.

```text
implemented ≠ tested ≠ wired ≠ enabled ≠ observed
```

MCP is therefore **implemented + server-wired/auth-gated** in the code base, while concrete
deployment exposure and runtime observation remain instance-specific claims.

---

## 2. Feature-gated / research areas

Examples include causal/reasoning layers, dense/graph retrieval signals, adaptive memory,
concept emergence, welfare/identity experiments, Synaptic shadow evaluation, and other
higher cognitive compositions.

A file, flag, or registration point does not prove a selected deployment enables or has
observed that capability.

Synaptic components/shadow evaluation are present, but active Synaptic answer authority is
not transferred. Research/shadow ≠ runtime authority.

---

## 3. Known production-hardening risks

1. **Independent security assurance:** no independent third-party security audit or
   penetration test is claimed.
2. **Compliance:** existing erasure/redaction mechanisms are not a certified GDPR or legal
   compliance program.
3. **Storage/concurrency:** substantial bounded SQLite evidence exists. The specific
   concurrent fresh-store bootstrap residual from Issue #347 is closed through merged PR
   #349; general realistic multiprocess/network-filesystem/SLA-scale proof remains open.
4. **Persisted observability:** metrics/logs/traces exist, but there is no universal durable
   causal record that proves why every historical answer was produced.
5. **Mutation families:** standard Validated promotion is converged, but other mutation
   families intentionally retain separate owners/contracts.
6. **Evidence-use attribution:** retrieval/selection (R), prompt serialization (S), and
   provider packing/transmission (T) do not establish model semantic use (U) or final-answer
   support (A).
7. **Deployment truth:** server wiring, CI, a feature flag, or a successful bounded pilot
   does not itself establish current deployment/observation or production authorization.

---

## 4. Production-hardening P0 / P1 / P2

### P0 — blocks trustworthy production use

- independent security review before sensitive public internet deployment;
- GDPR/compliance program beyond existing engineering erasure/redaction mechanisms;
- broader realistic storage/concurrency/recovery proof beyond the bounded evidence already
  retained.

### P1 — materially improves trust/operability

- durable replayable provenance/answer receipts without treating receipts as truth;
- persisted operational observability suitable for retrospective diagnosis;
- bounded attribution work that preserves `R/S/T ≠ U/A` unless separately proven.

### P2 — access / packaging / hygiene

- further production deployment evidence around the already server-wired MCP surface;
- lean dependency/profile packaging;
- continued documentation/version/language hygiene.

---

## 5. MCP status, precisely

```text
core/tool_registry.py        implemented
core/mcp_transport.py        implemented bounded JSON-RPC transport
api/mcp_gateway.py           implemented HTTP/SSE gateway
server.py registration       wired with require_api_key
selected deployment enabled  verify configuration/runtime
observed traffic             verify runtime evidence
production authorized        false unless separately granted
```

Capability ceilings, auth, idempotency, or route presence are controls/evidence; they are
not production authorization.

---

## 6. Retrieval status, precisely

`HybridRetriever` supports multiple signals, but optional dependencies matter. Do not write
“BM25 + dense + graph on every request” as a universal runtime statement.

```text
hybrid capability ≠ all signals active
ranking ≠ evidence
not retrieved ≠ absent
```

---

## 7. Reviewer-safe conclusion

Titan V1 productization is closed within its bounded scope, but production hardening remains
a separate program. The current code has a read-only canonical query pipeline, controlled
standard promotion, authenticated server-wired MCP/tool routes, optional hybrid retrieval
signals, and explicit evidence/authority boundaries. No independent security audit,
certified compliance program, general production-scale storage proof, or universal U/A
attribution is claimed. Merge, CI, wiring, V1 closure, and bounded pilots do not by
themselves grant production authority.
