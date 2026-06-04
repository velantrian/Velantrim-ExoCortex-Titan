# 🔱 VELANTRIM V8.6 Complex

**Language:** English  
**Russian source:** [`README.md`](README.md)  
**Purpose:** English companion README, placed next to the Russian original.

Long-term memory for AI agents with causal understanding, evidence, browser testing, and an experimental research layer.

> 🌿 **Philosophy:** [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md)  
> 🔒 **For AI agents:** [docs/PHILOSOPHY_SPEC.md](docs/PHILOSOPHY_SPEC.md)  
> 🗺️ **Project map:** [Velantrim_Project_Map.md](Velantrim_Project_Map.md)  
> 📁 **Related folders:** [docs/RELATED_PROJECTS.ru.md](docs/RELATED_PROJECTS.ru.md) — do not confuse with `Graphiti_fractal-main`

---

## 🧠 What Velantrim Is

Velantrim is not just a chatbot and not just a vector database.

It is an **ExoCortex**: a memory-and-reasoning system where truth, evidence, memory, and language generation are separated.

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

## 🆕 V8.6 Complex — ExoCortex + L6

Modules L1.5-L5.5 were moved from `Graphiti_fractal-main`. By default, most advanced layers are **off** and activated through ENV flags.

| Layer | Module | Flag / Status |
|---|---|---|
| L0 | Raw Memory | always 🟢 |
| L1 | ESM + Truth Gate | 🟢 |
| L1 | CognitiveFact / Store (v9) | `ENABLE_COGNITIVE_FACT`, `ENABLE_COGNITIVE_STORE` |
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
| — | SleepTimeWorker | `SLEEP_WORKER_ENABLED` (V8.6 only) |
| — | EventBus | `ENABLE_EVENT_BUS` |

---

## 🗺️ System At A Glance

```text
🔱 VELANTRIM_ExoCortex_V8.6
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
    ├── requirements.txt
    ├── config/exocortex-dev.env
    └── config/llm.example.env
```

---

## 🧪 Research Mode — Separate Experimental Memory

Research Mode describes a smaller experimental version next to stable V8.6.

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
http://127.0.0.1:8755/console/?v=23

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
- `docs/Velantrim_V9_Final_Audited.md` — V9 specification

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

**8.6.0** — product **VELANTRIM V8.6 Complex**.  
The repository folder may remain named `VELANTRIM_ExoCortex_V8.6`.

