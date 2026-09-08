# 🗺️ Velantrim Titan 9.0 — Living System Atlas

> **Purpose:** architecture tour for users, engineers, operators, reviewers, and AI agents.
>
> **Product version:** <!-- SYNC:VERSION -->v9.0.0<!-- /SYNC:VERSION -->
> **Audited base:** `main@70bc34fecdcf0bae15bc2264445e31b87b79bf08` on 2026-09-08.
> This is a dated verification checkpoint, not an evergreen claim about the latest remote head.
>
> **Document role:** navigation and explanation only. Code at the exact SHA, tests/CI,
> selected configuration, and observed runtime evidence override this document on conflict.

**English** · [Русский](SYSTEM_OVERVIEW.md) ·
[🏠 README](README.md) ·
[📊 Project status](docs/PROJECT_STATUS.md) ·
[🔍 Reviewer map](docs/REVIEWER_README.md) ·
[🏛️ Truth canon](docs/TRUTH_AND_RINGZERO_CANON.en.md)

---

## 🧭 Choose a route

| Goal | Route | Typical depth |
|---|---|---:|
| 👋 Understand the idea | [30-second explanation](#plain) | L0 |
| 🗺️ See the system | [component map](#map) | L1 |
| 🔄 Follow query/write flows | [two main flows](#flows) | L2 |
| 🧑‍💻 Audit contracts | [engineering boundaries](#engineer) | L3 |
| 🧾 Verify claims | [evidence/status rules](#evidence) | L1–L3 |
| 🧪 Test viability | [Architecture Assurance](#assurance) | L2–L3 |
| 🤖 Explain Titan to someone else | [self-explanation protocol](#self-explain) | adaptive |

---

<a id="plain"></a>

## 👋 L0 — Titan in 30 seconds

Velantrim Titan is a **local-first verifiable memory runtime for AI agents**. It separates
things a normal chat often collapses together:

```text
source → memory → retrieval → policy → answer
```

A useful analogy:

```text
librarian   finds records
lab worker  preserves source and uncertainty
border gate limits trusted state changes
auditor     records what the system can observe
translator  turns admitted context into human language
```

Titan is not an oracle. It improves traceability and authority separation; it does not
make arbitrary text true.

Engineering shorthand:

```text
Memory stores state.
Retrieval proposes context.
Policy limits authority.
TruthGate evaluates admission where that contract applies.
TRACE records observable path artifacts.
LLM renders language.
```

Critical invariants:

```text
retrieval ≠ evidence
admission ≠ verification
confidence ≠ evidence
model output ≠ Canon
TRACE membership ≠ semantic use ≠ answer support
CI green ≠ runtime or production authorization
```

---

<a id="evidence"></a>

## 🧾 How to read status claims

| Label | Meaning |
|---|---|
| 🟢 **default path** | belongs to the baseline path |
| ✅ **main / tested** | code and relevant tests are present in `main` |
| 🟡 **available / gated** | implementation exists; profile/ENV/dependency decides use |
| 🚧 **open PR** | not part of `main` yet |
| 🔬 **research / proposed** | design/research only; no runtime authority |
| ⚠️ **known limitation** | bounded claim, gap, or debt |
| 📡 **runtime observed** | concrete running-instance evidence exists |

Never compress these into one word:

```text
implemented ≠ tested ≠ wired ≠ enabled ≠ observed
```

Source-of-truth order for implementation questions:

1. executable code at the exact SHA;
2. tests and current CI evidence;
3. selected runtime configuration and observed telemetry;
4. current-state docs and accepted ADRs;
5. PR/work-log history;
6. historical audits/archive.

For live activation, inspect configuration plus `/health`, `/layers/status`, and
`/titan/status`.

---

<a id="map"></a>

## 🗺️ L1 — Component map

```text
┌──────────────────── HUMAN / AGENT / FILE ─────────────────────┐
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
                    API · auth · policy · egress
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
            READ PATH                     WRITE PATH
        query / retrieval              source / candidate
                │                             │
                ▼                             ▼
      admitted context + TRACE          ESM + evidence
                │                             │
                ▼                             ▼
        Guardian / policy              TruthGate / CAS
                │                             │
                └──────────────┬──────────────┘
                               ▼
                     provenance · audit
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
          derived projections          replaceable LLM
```

| Area | Primary role | Main surfaces |
|---|---|---|
| API | network boundary, auth, routes | `server.py`, `api/` |
| Orchestration | read-side flow | `core/pipeline.py`, `core/app.py` |
| Memory | fact + ESM + temporal state | `core/memory.py` |
| Retrieval | lexical baseline, optional dense/graph signals, narrowing | `core/hybrid_retriever.py`, `core/ngram_index.py` |
| Trust/write | policy, write admission, standard promotion | `core/truth_gate.py`, `core/write_gate.py`, `core/promotion_gateway.py`, `core/policy_kernel.py` |
| Provenance/audit | source lineage and auditable effects | `core/provenance_chain.py`, `core/audit_chain.py` |
| Remote egress | fail-closed remote capability boundary | `core/remote_egress.py` |
| Synaptic | source-linked document reading/shadow evaluation | `core/semantic_reader.py`, `core/knowledge_capsule.py` |
| Research | proposed/feature-gated compositions | `research/`, shadow paths, feature flags |

Derived indexes/graphs accelerate retrieval and analysis. They do not become a hidden
second Canon merely because they are faster or semantically richer.

---

<a id="flows"></a>

## 🔄 L2 — Two main flows

### 🔎 Flow A: query / answer

```text
query
  → API boundary
  → QueryPipeline
  → candidate narrowing / hybrid retrieval
       lexical baseline
       optional dense / graph signals when available
  → FactsPackBuilder / Guardian / truth policy
  → structured TRACE / result
  → optional LLM rendering
```

**Current implementation boundary:** `core/pipeline.py::run()` is read-only with respect
to canonical fact storage, ESM promotion, and causal-relation mutation. The old statement
that legacy `POST /query` performs promotion is historical and no longer current.

The current server answer path still uses the legacy query answer authority. Synaptic
shadow evaluation is separate and does not acquire answer authority merely by being wired
as shadow processing.

### ✍️ Flow B: admitted mutation

```text
source / candidate
  → provenance / metadata
  → legal ESM transition and applicable write checks
  → reviewed mutation owner
  → CAS / transactional evidence where required
  → Canon/local durable state
  → projections / audit updates
```

Standard `Validated` promotion callers converge on `PromotionGateway` and the canonical
`SQLiteGraphStore.validate_and_promote()` path. This does **not** mean every mutation in
Titan has one global owner: ordinary non-Validated transitions, invalidation, relation
lifecycle, erasure, archival/redaction, and compound supersession keep their own explicit
contracts.

---

## 🔍 Retrieval: what “hybrid” currently means

`HybridRetriever` supports lexical/BM25-style retrieval, dense embeddings, optional graph
signals, and ranking fusion. Availability is dependency/configuration sensitive.

```text
hybrid capability exists
  ≠ every dependency is installed
  ≠ every signal runs on every query
  ≠ ranking score is truth/evidence authority
```

The base Python package has no mandatory third-party dependencies. Dense retrieval and
some enhanced paths require optional extras and degrade to narrower retrieval when those
components are unavailable.

---

## 📄 Synaptic Exo-Cortex

Current bounded status at the audited base:

```text
Raw evidence
  → ✅ SemanticReader
  → ✅ KnowledgeCapsule + exact SourceSpan
  → ✅ LLM Reader Adapter
       main/tested; no server /query answer-path caller;
       standalone CLI uses scripts/read_document.py
  → ✅ Working Memory Gate
       main/tested; shadow-chain only
  → ✅ ContextPack
       main/tested; shadow-chain only
  → ✅ shadow evaluation
       main/tested; feature-gated; qualifying POST /query responses only;
       no answer authority
  → active answer authority
       NOT transferred to Synaptic; LEGACY_QUERY remains authoritative
```

Shadow processing does not write Canon/ESM and does not become active answer authority
without a separate decision. `KnowledgeCapsule` remains a proposal/evidence structure,
not Canon.

---

## 🔌 MCP transport

`core/tool_registry.py` and `core/mcp_transport.py` contain a bounded capability-based
JSON-RPC transport implementation, including capability ceilings and bounded process-local
idempotency behavior.

Reality status:

```text
implemented: yes (bounded)
module tests/evidence: present
server-wired by default: no
enabled merely by file presence: no
runtime authority: no
production authorization: no
```

“Registry exists, no transport” is stale. “Transport exists, therefore MCP is deployed”
is also false.

---

<a id="engineer"></a>

## 🧑‍💻 L3 — Engineering boundaries

### 1. Read and write are different authorities

```text
READ
  returns facts / context / evidence / proposals
  must not silently mutate Canon

WRITE
  uses an explicit owning service
  checks the required policy / ESM / provenance contract
  records the required durable/audit effect
```

### 2. Canon and projections are different authority levels

```text
canonical state
  > rebuildable indexes / vectors / graph views / caches
  > model/provider output
```

A projection failure should cause rebuild/degradation, not a hidden truth change.

### 3. LLM is a replaceable executor

An LLM may extract, summarize, rank, compress with qualifiers, or render a response. It
cannot by itself grant Canon admission, bypass PolicyKernel/TruthGate/write boundaries,
or turn model self-report into runtime evidence.

### 4. TRACE is accountability, not proof of internal cognition

Titan can observe retrieval/selection, serialization, provider packing, structured trace
artifacts, and answer output. The bounded evidence-use tests explicitly separate:

```text
R = retrieved / selected
S = serialized
T = transmitted after provider packing
U = demonstrably used by model          NOT established by R/S/T alone
A = demonstrably supports final answer  NOT established by R/S/T alone
```

Do not relabel R/S/T as U/A without separate attribution evidence.

### 5. Remote providers remain behind policy

Remote server calls pass through `core/remote_egress.py` and PolicyKernel. Metadata-only
`data_mode="none"` is limited to a closed capability set; user prompts, memory, and audio
must not silently opt out of remote-data policy.

---

<a id="self-explain"></a>

## 🎓 Self-explanation protocol

Titan's documentation should explain the same reality at different depths without
changing truth status:

```text
“What depth do you want?”
  → plain
  → operator
  → engineer
  → reviewer
```

Rules:

1. Start shallow; deepen on demand.
2. Preserve status (`proposed/implemented/tested/wired/enabled/observed`).
3. Give evidence pointers for material claims.
4. Say `UNKNOWN` when current state cannot be established.
5. Never present an architecture explanation as hidden chain-of-thought.
6. Never treat multiple model opinions over shared context as independent evidence.

---

<a id="assurance"></a>

## 🧪 Architecture Assurance

Architecture Assurance is an engineering loop, not another authority-owning cognitive
organ:

```text
model
  → bounded implementation
  → deterministic load / fault injection
  → metrics and retained evidence
  → correction
```

Inside runtime, use invariants, fail-closed policy, limits, CAS/idempotency, and audit
hooks. Outside runtime, use load/spike/soak tests, fault injection, recovery drills,
property tests, replay, and capacity characterization.

A useful queueing intuition is:

\[
\rho = \frac{\lambda E[S]}{c}
\]

but average utilization alone is not a production guarantee. Tail latency, service-time
variance, storage amplification, common-cause failures, and recovery behavior must be
measured. Existing SQLite concurrency evidence is bounded characterization, not unlimited
multiprocess or network-filesystem proof.

---

## 🚫 What this Atlas does not claim

- zero hallucinations;
- absolute truth of sources;
- certified GDPR/compliance;
- a third-party security audit that has not occurred;
- drop-in production-ready multi-user SaaS;
- consciousness or subjective experience;
- that every `core/` module is enabled;
- that a research file or open PR is runtime behavior;
- that green CI is Operator GO or production authorization;
- that TRACE proves internal model use or answer support.

For production-hardening risks, use [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).
The bounded V1 productization ledger can be `DONE` while production-hardening work still
exists; those are different scopes.

---

## 🔄 Keeping the Atlas current

When architecture-facing behavior changes, a review should answer:

```text
1. What changed for a user?
2. Which contract changed for an engineer?
3. What status is now true?
4. Where is code/test/CI/runtime evidence?
5. What happens on failure?
```

Do not embed an undated “current SHA” as an evergreen truth. Use dated audited checkpoints
and re-query GitHub whenever live state matters.
