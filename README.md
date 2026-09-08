# 🔱 VELANTRIM TITAN 9.0

**English** · [Русский](README.ru.md)

> **Local-first verifiable memory for AI agents:** explicit epistemic states,
> controlled write/admission boundaries, provenance, TRACE, retrieval, tools,
> and a replaceable language/provider layer.
>
> **Maturity:** research-grade prototype moving toward production hardening.

[🤖 AI agents: start here](AGENTS.md) ·
[🗺️ System tour](SYSTEM_OVERVIEW.en.md) ·
[📊 Project status](docs/PROJECT_STATUS.md) ·
[🔍 Reviewer map](docs/REVIEWER_README.md) ·
[🔒 Security](SECURITY.md) ·
[🏛️ Truth canon](docs/TRUTH_AND_RINGZERO_CANON.en.md)

> 🤖 **AI coding agent or automated reviewer:** use [`AGENTS.md`](AGENTS.md)
> as the formal repository entry point, then follow task routing in
> [`docs/ai/README.md`](docs/ai/README.md). Documentation is orientation, not proof;
> verify material claims against exact code, tests, CI, selected configuration,
> and observed runtime evidence.

---

## 👋 Titan in 60 seconds

A bare LLM often mixes memory, retrieval, confidence, policy, tools, and fluent wording
into one opaque answer. Titan separates those responsibilities:

```text
query / user action
  → memory + retrieval
  → admitted context / typed proposals
  → policy / TruthGate / write boundaries
  → TRACE / audit / provenance
  → tools or replaceable LLM/provider layer
```

The important claim is not that Titan “knows truth.” The important property is that
retrieval, evidence, permission, mutation, auditability, and language generation do not
silently become the same authority.

```text
retrieval ≠ evidence
admission ≠ verification
confidence ≠ authority
model output ≠ Canon
TRACE membership ≠ semantic use ≠ answer support
CI green ≠ production authorization
```

Titan is a local-first memory and orchestration runtime with an explicit epistemic-state
machine (ESM), controlled canonical mutation paths, hybrid retrieval capability,
provenance/audit surfaces, remote-egress policy, authenticated API/tool surfaces, and
feature-gated research layers. An LLM may read, extract, rank, summarize, or render
language, but it does not automatically gain the right to mutate Canon.

---

## 🧭 What should I open first?

| You are… | Start here |
|---|---|
| 🤖 AI coding agent / automated reviewer | [`AGENTS.md`](AGENTS.md) → [`docs/ai/README.md`](docs/ai/README.md) |
| 👤 New to Titan | [System overview](SYSTEM_OVERVIEW.en.md#plain) |
| 🛠️ Running your own instance | [Quick start](#quick-start) + [Security](SECURITY.md) |
| 🧑‍💻 Changing code | [`AGENTS.md`](AGENTS.md) + [engineering boundaries](SYSTEM_OVERVIEW.en.md#engineer) |
| 🔍 Auditing claims | [`docs/REVIEWER_README.md`](docs/REVIEWER_README.md) |
| 💼 Evaluating maturity | [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) |
| 🧠 Studying project cognition / code review | [`docs/use_cases/PROJECT_COGNITION_AND_CODE_REVIEW.md`](docs/use_cases/PROJECT_COGNITION_AND_CODE_REVIEW.md) |
| 🔬 Reading future work | [`research/`](research/) + [`research/ARCHITECTURE_AXES.md`](research/ARCHITECTURE_AXES.md) |

---

## 🗺️ System at a glance

```text
┌──────────────────── HUMAN / AGENT / FILE ─────────────────────┐
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
                     API · auth · policy
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
    read/retrieval         explicit write          tools/MCP
        │                      │                      │
        ▼                      ▼                      ▼
 admitted context          ESM + evidence        capability gate
 + TRACE                   + CAS/policy          + auth/session
        │                      │                      │
        └──────────────┬───────┴──────────────┬───────┘
                       ▼                      ▼
              provenance · audit       replaceable LLM
```

### Current read-path boundary

`core/pipeline.py::run()` is read-only with respect to canonical fact storage, ESM
promotion, and causal-relation mutation. Standard `Validated` promotion callers route
through the reviewed `PromotionGateway` path. Separate mutation families such as
invalidation, erasure, archival/redaction, relation lifecycle, and compound supersession
retain their own explicit contracts.

### TRACE / evidence-use boundary

Titan can directly observe stages such as retrieved/selected context, serialization into
an answer prompt, provider-specific packing/transmission, and stored trace artifacts.
That does **not** prove that a model semantically used a particular item or that the item
supported the final answer. Those stronger U/A claims require separate attribution evidence.

---

## 🧾 Status legend

| Label | What it means |
|---|---|
| 🟢 **default path** | part of the baseline path |
| ✅ **main / tested** | implementation and relevant tests are in `main` |
| 🟡 **available / gated** | implementation exists but profile/ENV/dependency decides use |
| 🚧 **open PR** | proposed change, not yet part of `main` |
| 🔬 **research / proposed** | design/research only; no runtime authority |
| ⚠️ **known limitation** | acknowledged gap or bounded claim |
| 📡 **runtime observed** | confirmed on a concrete running instance |

```text
implemented ≠ tested ≠ wired ≠ enabled ≠ observed
```

For a concrete installation, inspect configuration plus `/health`, `/layers/status`, and
`/titan/status`; do not infer live activation from this README alone.

---

## ✅ Current engineering foundation

| Area | Current role | Primary files |
|---|---|---|
| 🧠 Memory + ESM | facts, 8 epistemic states, temporal state | `core/memory.py` |
| ⚖️ Trust / write boundary | evidence/confidence policy and controlled admission | `core/truth_gate.py`, `core/write_gate.py`, `core/promotion_gateway.py`, `core/policy_kernel.py` |
| 🔍 Retrieval | lexical path plus optional dense/graph signals and candidate narrowing | `core/hybrid_retriever.py`, `core/ngram_index.py` |
| 🧾 Provenance / audit | source lineage and auditable effects | `core/provenance_chain.py`, `core/audit_chain.py` |
| 🔐 Remote boundary | fail-closed capability lease + epistemic prompt guard | `core/remote_egress.py` |
| 🔌 MCP / tools | authenticated server gateway + capability-scoped JSON-RPC tools | `api/mcp_gateway.py`, `core/mcp_transport.py`, `core/tool_registry.py` |
| 📄 Synaptic foundation | source-linked capsules and reader contracts | `core/knowledge_capsule.py`, `core/semantic_reader.py` |
| 🌐 API + Console | FastAPI surface and browser UI | `server.py`, `api/`, `static/console/` |

### Retrieval precision

Titan's hybrid retriever supports lexical/BM25-style retrieval, optional dense embeddings,
optional graph signals, and ranking fusion. This does **not** mean every installation
executes every signal on every request. The base package has no mandatory third-party
dependencies; dense and some enhanced retrieval paths require optional extras/configuration
and degrade to narrower paths when unavailable.

### MCP precision

MCP is more than a dormant module on the current audited base. `server.py` imports
`api.mcp_gateway` and registers its routes with the same `require_api_key` boundary used by
other authenticated server surfaces. The gateway delegates to `core.mcp_transport.McpHandler`
and applies capability/session ceilings.

That establishes **implemented + server-wired/auth-gated**. It does **not** establish that
a particular deployment is currently running, externally exposed, observed, unrestricted,
or production-authorized:

```text
implemented + wired
  ≠ enabled in a selected deployment
  ≠ observed in a running instance
  ≠ production authorization
```

---

## 📄 Synaptic Exo-Cortex

Current bounded status:

```text
Raw evidence
  → ✅ SemanticReader
  → ✅ KnowledgeCapsule + exact SourceSpan
  → ✅ LLM Reader Adapter
       main/tested; no server /query answer-path caller;
       standalone document-reading CLI uses scripts/read_document.py
  → ✅ Working Memory Gate
       main/tested; shadow chain only
  → ✅ ContextPack
       main/tested; shadow chain only
  → ✅ shadow evaluation
       main/tested; feature-gated; qualifying POST /query responses only;
       no answer authority
  → active answer authority
       NOT transferred to Synaptic; LEGACY_QUERY remains authoritative
```

Each ✅ means implemented/tested in `main`; it does **not** mean enabled by default,
production-authorized, or authoritative over answers. Shadow processing does not write to
Canon/ESM and does not gain active answer authority merely by being wired as shadow logic.

Key boundaries:

- exact source spans and SHA-256 provenance;
- `extraction_confidence` ≠ `truth_confidence`;
- capsule/proposal ≠ Canon;
- ordinary `core/pipeline.py::run()` is read-only with respect to canonical fact/ESM and
  causal-relation mutation;
- model/provider layer remains replaceable;
- shadow evidence does not authorize active integration.

Plan: [`docs/SYNAPTIC_EXO_CORTEX_IMPLEMENTATION_PLAN.md`](docs/SYNAPTIC_EXO_CORTEX_IMPLEMENTATION_PLAN.md)

---

## 🛡️ What Titan does not promise

- ❌ zero hallucinations;
- ❌ absolute truth of any source;
- ❌ that retrieval/ranking proves evidence authority;
- ❌ certified GDPR/compliance status;
- ❌ an independent security audit that has not happened;
- ❌ drop-in production-ready multi-user SaaS;
- ❌ consciousness or subjective experience;
- ❌ that every `core/` module is enabled by default;
- ❌ that an open PR or research document is already runtime behavior;
- ❌ that TRACE proves internal model use or causal answer support;
- ❌ that server wiring by itself proves a deployed/observed production service.

Production-hardening risks and P0/P1/P2 are tracked in
[`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md). The separate bounded **V1
productization** ledger may report V1 P0/P1 = 0; that does **not** mean production-
hardening P0/P1 = 0 or production authorization.

---

<a id="quick-start"></a>

## 🚀 Quick start

### Hardened deployment profile

```bash
git clone https://github.com/velantrian/Velantrim-ExoCortex-Titan.git
cd Velantrim-ExoCortex-Titan
cp .env.prod.example .env.prod
# Set a strong VELANTRIM_API_KEY in .env.prod.
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

The hardened profile is an application/container hardening profile, not a claim of
host-level firewall/TLS/WAF, compliance, or production authorization. Read
[`docs/operations/hardened-production-profile.md`](docs/operations/hardened-production-profile.md).

Check:

```text
http://127.0.0.1:8000/health
```

### Local development

```bash
python -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\activate
python -m pip install -e ".[server,dev]"
cp .env.example .env
# VELANTRIM_API_KEY=...
uvicorn server:app --port 8000 --reload
```

Verification baseline:

```bash
ruff check core/ --output-format=github
mypy core/ --show-error-codes
python -m pytest tests/ -v --tb=short
```

---

## 📚 Documentation

| Document | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) 🤖 | formal entry point and mandatory rules for coding agents |
| [`docs/ai/README.md`](docs/ai/README.md) 🧭 | AI context routing and minimum-reading paths |
| [`SYSTEM_OVERVIEW.en.md`](SYSTEM_OVERVIEW.en.md) 🗺️ | current English system tour |
| [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md) 🇷🇺 | Russian system tour |
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) 📊 | maturity and production-hardening P0/P1/P2 |
| [`docs/REVIEWER_README.md`](docs/REVIEWER_README.md) 🔍 | independent-review map |
| [`SECURITY.md`](SECURITY.md) 🔒 | threat model and deployment boundaries |
| [`research/`](research/) 🔬 | proposed/research work; not runtime authority |

---

## 🌐 Language strategy

The repository landing page is English by default:

```text
README.md       English canonical landing README
README.ru.md    Russian companion
README.en.md    compatibility pointer to README.md
```

---

## 🧭 Version

**<!-- SYNC:VERSION -->v9.0.0<!-- /SYNC:VERSION --> — VELANTRIM TITAN 9.0**

Version source: `pyproject.toml` / `core.__version__`.
History: [`CHANGELOG.md`](CHANGELOG.md).

> **Titan understands and proposes. Trust boundaries verify and admit.
> The kernel preserves invariants. The LLM remains replaceable.**
