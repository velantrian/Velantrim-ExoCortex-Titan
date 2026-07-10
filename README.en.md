# 🔱 VELANTRIM TITAN 9.0

**Language:** English
**Russian source:** [`README.md`](README.md)
**Purpose:** English companion README, placed next to the Russian original.

A local-first verifiable memory runtime for AI agents: evidence-gated AI memory with a causal graph, an immune layer, and an identity axis. Research-grade prototype moving toward production hardening.

> 🌿 **Philosophy:** [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md)
> 🔒 **For AI agents:** [docs/PHILOSOPHY_SPEC.md](docs/PHILOSOPHY_SPEC.md)
> 🗺️ **Project map:** [Velantrim_Project_Map.md](Velantrim_Project_Map.md)
> 📁 **Related folders:** [docs/RELATED_PROJECTS.ru.md](docs/RELATED_PROJECTS.ru.md) — do not confuse with `Graphiti_fractal-main`
>
> Legacy notes are preserved in [CHANGELOG.md](CHANGELOG.md) and `docs/archive/`.

---

## 🧠 What Velantrim Is

Velantrim is not just a chatbot and not just a vector database.

It is an **ExoCortex**: a memory-and-reasoning system where truth, evidence, memory, and language generation are separated — auditable provenance and truth-bound generation instead of a single opaque model call.

```text
Normal LLM:
  prompt -> model -> fluent answer

Velantrim:
  query -> memory -> retrieval -> facts -> Truth Gate -> TRACE -> LLM voice
```

Short formula:

```text
Graph = Truth
Index = Speed
Facts Pack = Evidence
Truth Gate = Trust
TRACE = Accountability
LLM / BAE = Voice
```

---

## 🆕 Titan 9.0 — Immune System + Identity Axis + Production Hardening

**199 modules · 91 test files · 18 invariants enforced in CI · docker-compose up**

| Area | Module | Purpose |
|---|---|---|
| 🛡️ Immune system | `core/meta_supervisor.py` | HEALTHY/DEGRADED/SAFE_MODE, 10s heartbeat, L3 read-only on critical degradation |
| 🛡️ Immune system | `core/immutable_core_scheduler.py` | SHA-256 delta snapshots of the graph every 24h |
| 🛡️ Immune system | `core/provenance_chain.py` | Append-only hash chain — a blockchain for memory |
| 🛡️ Immune system | `core/atomic_split.py` | I91: one proposition = one fact |
| 🧬 Identity Axis | `core/identity_layer.py` | F1–F4: VALUES / WORLDVIEW / BIOGRAPHY / COMPASS |
| 🧬 Identity Axis | `core/stimulus_map.py` | Two-way traceability: stimulus ↔ fact ↔ answer |
| 🧬 Identity Axis | `core/forgetting.py` | GDPR "right to be forgotten" + PII redaction |
| 🚀 Production | `Dockerfile` + `docker-compose.yml` | One-command deploy: `docker-compose up -d` |
| 🚀 Production | `core/async_store.py` | aiosqlite + run_in_executor — the event loop never blocks |
| 🚀 Production | `core/metrics.py` | Prometheus metrics + `/health` endpoint |
| 🚀 Production | `.github/workflows/ci.yml` | CI/CD: mypy strict + ruff + pytest, blocking |

Most advanced layers (L1.5–L5.5) are **off by default** and activated through ENV flags:

| Layer | Module | Flag / Status |
|---|---|---|
| L0 | Raw Memory | always 🟢 |
| L1 | ESM + Truth Gate | 🟢 |
| L1 | CognitiveFact / Store | `ENABLE_COGNITIVE_FACT`, `ENABLE_COGNITIVE_STORE` |
| L1.5 | Velum, Salience | `ENABLE_VELUM`, `ENABLE_SALIENCE` |
| L2 | Concept Emergence | `ENABLE_CONCEPT_EMERGENCE` |
| L2.5 | Staging (research) | 🔬 no code yet — [docs/horizons/L2_5_STAGING.md](docs/horizons/L2_5_STAGING.md) |
| L3.5a | Etir | `ENABLE_ETIR` |
| L3.5b | Immutable Core | `ENABLE_IMMUTABLE_CORE` |
| L4 | Causal, Reasoning Bank | `ENABLE_CAUSAL_GRAPH`, `ENABLE_REASONING_BANK` |
| L4.5 | Focus, Audit, Volition | `ENABLE_L45` or individual flags |
| L5.5 | Predictive Fusion | `ENABLE_PREDICTIVE_FUSION` |
| L6 | Welfare MVP | `ENABLE_L6_WELFARE` |
| — | Fractal Memory contracts | `core/fractal_memory.py` 🟡 skeleton |
| — | SleepTimeWorker | `SLEEP_WORKER_ENABLED` |
| — | EventBus | `ENABLE_EVENT_BUS` |

---

## 🗺️ System At A Glance

```text
🔱 Velantrim Titan 9.0
│
├── 🧠 Core
│   ├── memory.py             facts, ESM, cache, bi-temporal memory
│   ├── storage.py            storage contract / GraphStore ABC
│   ├── trace.py              provenance and answer trace
│   ├── pipeline.py           query orchestration
│   ├── truth_gate.py         verification and contradiction checks
│   └── hybrid_retriever.py   BM25 + dense + graph retrieval
│
├── 🖥️ Browser Console
│   ├── /console/             stable console
│   ├── /console/help         browser help
│   ├── /console/roadmap      task roadmap
│   └── /console/research-app experimental research UI
│
├── 🧪 Research Mode
│   ├── Fractal Router
│   ├── Essence Layer
│   ├── Attention / Noetic Orchestration
│   ├── RetrievalPath + stronger TRACE
│   └── separate DB: data/velantrim_research.db
│
├── 📚 Docs
│   ├── README.md / README.en.md
│   ├── SYSTEM_OVERVIEW.md / SYSTEM_OVERVIEW.en.md
│   └── docs/VELANTRIM_ARCHITECTURE.md / .en.md
│
└── ⚙️ Config
    ├── pyproject.toml
    ├── requirements-dev.txt
    ├── config/exocortex-dev.env
    └── config/llm.example.env
```

---

## 🧪 Research Mode — Separate Experimental Memory

Research Mode describes a smaller experimental version next to the stable runtime.

The browser console and AI agent can use Velantrim as an **API memory tool**, but write into a separate database:

```text
data/velantrim_research.db
```

not into the main graph store.

| Stable | Research |
|---|---|
| `/console`, `/query`, `data/velantrim.db` | `/console/research-app`, `/console/research`, `/research/query`, `data/velantrim_research.db` |
| current Hybrid / Causal pipeline | Fractal Router + Essence Layer + Attention / Noetic Orchestration + `RetrievalPath` + stronger TRACE |
| trusted memory | sandbox for experiments |

Browser:

- [http://127.0.0.1:8755/console/research-app](http://127.0.0.1:8755/console/research-app)
- spec: [docs/RESEARCH_MODE.ru.md](docs/RESEARCH_MODE.ru.md)
- EITI PWA roadmap: [docs/EITI_PWA_RESEARCH_ROADMAP.ru.md](docs/EITI_PWA_RESEARCH_ROADMAP.ru.md)
- Fractal canon: [docs/FRACTAL_MEMORY_CANON.ru.md](docs/FRACTAL_MEMORY_CANON.ru.md)

---

## 🖥️ Web Console + LLM Browser Test

The experimental browser stand includes:

- chat,
- local memory in **localStorage**,
- optional RAG through `/facts`,
- **🔗 Essence** tab,
- live graph of topic and relations through SSE,
- optional AI provider connection.

**Docs:** [docs/CONSOLE_BROWSER_TEST.ru.md](docs/CONSOLE_BROWSER_TEST.ru.md)
After server start: [http://127.0.0.1:8755/console/help](http://127.0.0.1:8755/console/help)
Roadmap: [http://127.0.0.1:8755/console/roadmap](http://127.0.0.1:8755/console/roadmap)

```powershell
# 1. .env: VELANTRIM_API_KEY=... (+ LLM from config/llm.example.env)
.\scripts\start_console.ps1

# 2. Browser:
http://127.0.0.1:8755/console/?v=40

# 3. Task roadmap:
http://127.0.0.1:8755/console/roadmap
```

Profiles:

```text
citizen · personal · company · science · education · research · developer
```

Setup and docs:

- [docs/PROFILES.ru.md](docs/PROFILES.ru.md)
- `GET /setup/llm`
- [docs/ROADMAP_FROM_SYSTEM.ru.md](docs/ROADMAP_FROM_SYSTEM.ru.md)
- [docs/HORIZONS.md](docs/HORIZONS.md)
- [docs/LAYERS_AND_HORIZONS.ru.md](docs/LAYERS_AND_HORIZONS.ru.md)
- [docs/RELATED_PROJECTS.ru.md](docs/RELATED_PROJECTS.ru.md)

---

## 🚀 Quick Start

```bash
# Option 1: Docker (recommended)
docker-compose up -d
# Server on http://localhost:8000

# Option 2: Manual run
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install fastapi "uvicorn[standard]" python-dotenv pydantic pytest httpx
cp .env.example .env
# VELANTRIM_API_KEY=... or VELANTRIM_ALLOW_OPEN=true (dev only)
mkdir -p data
uvicorn server:app --port 8000 --reload
.\scripts\run_tests.ps1
.\scripts\run_tests.ps1 -ExocortexOnly
```

### ExoCortex Optional Flags

```bash
ENABLE_VELUM=1
ENABLE_ETIR=1
ENABLE_L45=1
ENABLE_L6_WELFARE=1
ENABLE_EVENT_BUS=1
```

---

## 📚 Documentation

- [`docs/REVIEWER_README.md`](docs/REVIEWER_README.md) 🔍 — a map for reviewers: what this is, what it isn't, where to inspect first
- [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) 📊 — maturity by module, known risks, P0/P1/P2 roadmap
- [`SECURITY.md`](SECURITY.md) 🔒 — security model, API key, dev vs production, responsible disclosure
- `docs/TRUTH_AND_RINGZERO_CANON.en.md` 🏛️ — the canonical spec: Truth Engine (Core-3) + Ring Zero, verdict `allow/gap_notice/reject`, invariants I0–I8, conformance C1–C12 ([RU](docs/TRUTH_AND_RINGZERO_CANON.ru.md))
- `core/core3_adapter.py` 🔀 — Dual Core Router: subprocess bridge to Core-3 (strict high-risk verification)
- `docs/CONSOLE_BROWSER_TEST.ru.md` — browser console test
- `docs/VELANTRIM_ARCHITECTURE.md` — architecture
- `docs/VELANTRIM_ARCHITECTURE.en.md` — English architecture companion
- `docs/VELANTRIM_GUIDE.md` — installation
- `docs/RUN.ru.md` — quick start
- `docs/FRACTAL_MEMORY_CANON.ru.md` — Fractal Memory L0-L3, MemTree / recursive retrieval canon
- `docs/ESSENCE_LAYER_CANON.ru.md` — future-work canon: essence, semantic chains, short human answer
- `docs/ATTENTION_NOETIC_ORCHESTRATION.ru.md` — P0 contracts: GoalFrame, AttentionRouter, ComputeController, NoeticCore
- `docs/WORLD_KNOWLEDGE_CORE_v1_0.ru.md` — future-work canon: quality of knowledge, time, negative knowledge, contradiction review
- `docs/RESEARCH_MODE.ru.md` — separate experimental memory and Velantrim as an API tool
- `docs/EITI_PWA_RESEARCH_ROADMAP.ru.md` — T1-T12 roadmap for browser Research PWA

---

## 🌐 Language Strategy

Russian remains the main working language for the current canon.

English companion files use `.en.md`:

```text
README.md                  Russian
README.en.md               English

SYSTEM_OVERVIEW.md         Russian
SYSTEM_OVERVIEW.en.md      English

docs/VELANTRIM_ARCHITECTURE.md
docs/VELANTRIM_ARCHITECTURE.en.md
```

Later, all English files can be moved into a dedicated folder:

```text
docs/en/
```

For now, side-by-side files make comparison simple.

---

## 🧭 Version

**9.0.0** — product **VELANTRIM TITAN 9.0**.
Version history (V8.6 → V8.7 → V9.0) is preserved in [CHANGELOG.md](CHANGELOG.md) and `docs/archive/legacy/`.
