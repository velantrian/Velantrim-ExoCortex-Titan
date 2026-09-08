# 🔱 VELANTRIM TITAN 9.0

**English** · [Русский](README.ru.md)

> **Local-first verifiable memory for AI agents:** evidence-gated knowledge,
> explicit epistemic states, provenance, TRACE, controlled write boundaries,
> and a replaceable language layer.
>
> **Maturity:** research-grade prototype moving toward production hardening.

[🤖 AI agents: start here](AGENTS.md) ·
[🗺️ System tour](SYSTEM_OVERVIEW.en.md) ·
[📊 Project status](docs/PROJECT_STATUS.md) ·
[🔍 Reviewer map](docs/REVIEWER_README.md) ·
[🔒 Security](SECURITY.md) ·
[🏛️ Truth canon](docs/TRUTH_AND_RINGZERO_CANON.en.md)

> 🤖 **AI coding agent or automated reviewer:** use [`AGENTS.md`](AGENTS.md)
> as the formal repository entry point, then follow the task routing in
> [`docs/ai/README.md`](docs/ai/README.md). Documentation is orientation, not proof;
> verify material claims against exact code, tests, CI, configuration, and runtime evidence.

---

## 👋 Titan in 60 seconds

A bare LLM often mixes memory, retrieval, confidence, policy, and fluent wording into one
opaque answer. Titan separates those responsibilities:

```text
Normal LLM
  prompt → model → fluent answer

Velantrim Titan
  query
    → memory
    → retrieval
    → admitted context / evidence structures
    → policy / TruthGate
    → TRACE / audit artifacts
    → replaceable LLM voice
```

The important boundary is not that Titan “knows truth.” It is that different kinds of
claims and authority are kept separate:

```text
retrieval ≠ evidence
admission ≠ verification
confidence ≠ authority
model output ≠ Canon
TRACE membership ≠ proof of semantic use
CI green ≠ production authorization
```

Titan is a local-first memory runtime with an explicit epistemic-state machine (ESM),
controlled promotion/write paths, hybrid retrieval orchestration, provenance and audit
surfaces, remote-egress policy, and feature-gated research layers. An LLM may read,
extract, rank, summarize, or render language, but it does not automatically gain the
right to mutate Canon.

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
                    API · auth · policy · egress
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        read / retrieval                explicit write
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

### Current read-path boundary

`core/pipeline.py::run()` is read-only with respect to canonical fact storage, ESM
promotion, and causal-relation mutation. Standard `Validated` promotion callers route
through the reviewed `PromotionGateway` path. Separate mutation families such as
invalidation, erasure, archival/redaction, relation lifecycle, and compound supersession
retain their own explicit contracts; they are not silently treated as one global
promotion function.

### TRACE / evidence-use boundary

Titan can directly observe stages such as retrieved/selected context, serialization into
the answer prompt, and provider-bound message packing. That does **not** prove that the
model semantically used a specific item or that the item supported the final answer.
Those stronger U/A claims require separate attribution evidence.

---

## 🧾 Status legend

| Label | What it means |
|---|---|
| 🟢 **default path** | part of the baseline working path |
| ✅ **main / tested** | implementation and relevant tests are in `main` |
| 🟡 **available / gated** | implementation exists but depends on profile / ENV / dependency |
| 🚧 **open PR** | proposed change, not yet part of `main` |
| 🔬 **research / proposed** | research or design only; no runtime authority |
| ⚠️ **known limitation** | acknowledged gap or bounded claim |
| 📡 **runtime observed** | confirmed on a concrete running instance |

```text
file exists
  ≠ contract is test-proven
  ≠ feature is wired
  ≠ feature is enabled
  ≠ behavior was observed in this runtime
```

For a concrete installation, inspect configuration plus `/health`, `/layers/status`, and
`/titan/status`; do not infer live activation from this README alone.

---

## ✅ Current engineering foundation

| Area | Current role | Primary files |
|---|---|---|
| 🧠 Memory + ESM | facts, 8 epistemic states, temporal state | `core/memory.py` |
| ⚖️ Trust / write boundary | evidence/confidence policy and controlled admission | `core/truth_gate.py`, `core/write_gate.py`, `core/promotion_gateway.py`, `core/policy_kernel.py` |
| 🔍 Retrieval | lexical retrieval plus optional dense/graph signals and candidate narrowing | `core/hybrid_retriever.py`, `core/ngram_index.py` |
| 🧾 Provenance / audit | source lineage, append-only/tamper-evident records, audit artifacts | `core/provenance_chain.py`, `core/audit_chain.py` |
| 🛡️ Integrity | health states, snapshots, executable invariants | `core/meta_supervisor.py`, `core/immutable_core_scheduler.py`, `tests/test_invariants.py` |
| 🔐 Remote boundary | fail-closed capability lease + epistemic prompt guard | `core/remote_egress.py` |
| 📄 Synaptic foundation | source-linked capsules and reader contracts | `core/knowledge_capsule.py`, `core/semantic_reader.py` |
| 🌐 API + Console | FastAPI surface and browser UI | `server.py`, `api/`, `static/console/` |

### Retrieval precision

Titan's hybrid retriever supports BM25/lexical retrieval, optional dense embeddings,
optional graph signals, and RRF-style combination. These are not equivalent to saying
every installation executes BM25 + dense + graph on every request. The base package has
no mandatory third-party dependencies; dense and some retrieval features require optional
extras/configuration and degrade to narrower paths when unavailable.

### MCP transport

`core/tool_registry.py` and `core/mcp_transport.py` contain a bounded capability-based
JSON-RPC transport implementation with capability ceilings and bounded idempotency
semantics. It is **not server-wired by default**, not runtime-enabled merely because the
module exists, and carries no production authorization by itself.

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
  → user answer
       active Synaptic answer authority is NOT authorized;
       LEGACY_QUERY remains the authoritative answer path
```

Each ✅ means implemented/tested in `main`; it does **not** mean enabled by default,
production-authorized, or authoritative over answers. The shadow path does not write to
Canon/ESM and is intentionally separate from active answer authority.

Key invariants:

- exact source spans and SHA-256 provenance;
- `extraction_confidence` ≠ `truth_confidence`;
- capsule/proposal ≠ Canon;
- ordinary query/retrieval is read-only with respect to Canon/ESM mutation;
- model/provider layer remains replaceable;
- shadow evidence does not authorize active integration.

Plan: [`docs/SYNAPTIC_EXO_CORTEX_IMPLEMENTATION_PLAN.md`](docs/SYNAPTIC_EXO_CORTEX_IMPLEMENTATION_PLAN.md)

---

## 🛡️ What Titan does not promise

- ❌ zero hallucinations;
- ❌ absolute truth of any source;
- ❌ that retrieval or ranking proves evidence authority;
- ❌ certified GDPR/compliance status;
- ❌ an independent security audit that has not happened;
- ❌ drop-in production-ready multi-user SaaS;
- ❌ consciousness or subjective experience;
- ❌ that every `core/` module is enabled by default;
- ❌ that an open PR or research document is already runtime behavior;
- ❌ that TRACE proves internal model use or causal answer support.

Production-hardening risks and P0/P1/P2 are tracked in
[`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md). The separate bounded **V1
productization** ledger may report V1 P0/P1 = 0; that does **not** mean production-
hardening P0/P1 = 0 or production authorization.

---

## 🖥️ Two usage modes

```text
Local server runtime
  FastAPI + local SQLite + optional graph/LLM providers
  full server-side API and policy boundaries

Browser PWA
  IndexedDB/browser console + optional direct provider API
  separate browser mode; not equivalent to the full server runtime
```

| Surface | Link |
|---|---|
| 🌐 Portal | <https://velantrian.github.io/Velantrim-ExoCortex-Titan/> |
| 💬 Console PWA | <https://velantrian.github.io/Velantrim-ExoCortex-Titan/console/> |
| 🔬 Research PWA | <https://velantrian.github.io/Velantrim-ExoCortex-Titan/console/research-app.html> |
| 🗺️ Roadmap | <https://velantrian.github.io/Velantrim-ExoCortex-Titan/console/research-roadmap.html> |

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

The hardened profile binds the API to loopback by default and pins research/autonomous
layers off. Read
[`docs/operations/hardened-production-profile.md`](docs/operations/hardened-production-profile.md)
before deployment. This is application/container hardening, not a claim of host-level
firewall, TLS, WAF, compliance, or production authorization.

Check:

```text
http://127.0.0.1:8000/health
```

### Compatibility / research Compose

```bash
cp .env.example .env
# Set VELANTRIM_API_KEY.
docker compose up -d
```

`docker-compose.yml` intentionally preserves compatibility/research behavior and enables
several research/cognitive layers. It is **not** the hardened production profile.

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
| [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md) 🇷🇺 | Russian living system atlas |
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) 📊 | maturity, known risks, production-hardening P0/P1/P2 |
| [`docs/REVIEWER_README.md`](docs/REVIEWER_README.md) 🔍 | code/test map for independent review |
| [`SECURITY.md`](SECURITY.md) 🔒 | threat model, auth, deployment boundaries |
| [`docs/TRUTH_AND_RINGZERO_CANON.en.md`](docs/TRUTH_AND_RINGZERO_CANON.en.md) 🏛️ | Truth Engine + Ring Zero normative specification |
| [`research/`](research/) 🔬 | proposed/research work; not runtime authority |

Historical V8.x material remains in [`CHANGELOG.md`](CHANGELOG.md) and
`docs/archive/legacy/` unless explicitly re-adopted by a current contract.

---

## 🌐 Language strategy

The repository landing page is English by default:

```text
README.md       English canonical landing README
README.ru.md    Russian companion
README.en.md    compatibility pointer to README.md
```

The architecture tour remains available in both languages:

```text
SYSTEM_OVERVIEW.en.md   English
SYSTEM_OVERVIEW.md      Russian
```

---

## 🧭 Version

**<!-- SYNC:VERSION -->v9.0.0<!-- /SYNC:VERSION --> — VELANTRIM TITAN 9.0**

Version source: `pyproject.toml` / `core.__version__`.
History: [`CHANGELOG.md`](CHANGELOG.md).

> **Titan understands and proposes. Trust boundaries verify and admit.
> The kernel preserves invariants. The LLM remains replaceable.**
