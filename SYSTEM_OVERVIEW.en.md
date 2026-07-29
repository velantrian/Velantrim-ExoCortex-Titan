# 🔱 Velantrim ExoCortex — How It Works

> ⚠️ **Translation status:** this English companion still preserves the older
> V8.x walkthrough. For the current evidence-labeled Living System Atlas, use
> [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md) (Russian) and
> [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md). Do not treat legacy
> sections below as current runtime evidence.

**Language:** English  
**Russian source:** [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md)  
**Purpose:** visual English companion overview.

This document explains Velantrim in human language first, then as an engineering system.

---

## 🧠 What Velantrim Is — One Paragraph

Velantrim is a personal **ExoCortex** for AI and human thinking. It stores facts, remembers sources, checks what can be trusted, builds a trace of reasoning, and lets an LLM speak only after the system has selected evidence.

In simple words:

> A normal AI talks from context.  
> Velantrim remembers, checks, connects, and then lets the AI talk.

---

## 🗺️ Full Project Map

```text
🔱 Velantrim-ExoCortex-Titan
│
│  ┌─────────────────────────────────────────────────────────────────────┐
│  │  🧠 SYSTEM CORE — what actually works right now                    │
│  │                                                                     │
│  │   📜 storage.py ──► contract: WHAT a storage layer must support    │
│  │         │                                                           │
│  │         ▼                                                           │
│  │   🧠 memory.py ──► MEMORY: facts, ESM, cache, bi-temporal          │
│  │         │                                                           │
│  │         ├──────────────────────────────────────────────────────┐   │
│  │         ▼                                                       ▼   │
│  │   🔍 trace.py ──► TRACE: who, where, when       ⚙️ pipeline.py │   │
│  │                                                  main entry     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐
│  │  🧪 TESTS — verify that the core behaves correctly                 │
│  │                                                                     │
│  │   test_esm.py ──────────────► checks memory.py                    │
│  │   test_pipeline.py ──────────► checks pipeline.py + trace.py      │
│  │   test_regression_p0.py ─────► old bugs do not return             │
│  │   test_sprint_a_wiring.py ───► 🛡️ guard: A6-A10 are not wired     │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────────────────┐
│  │  🔧 TOOLS — manual tools, not part of runtime                     │
│  │                                                                     │
│  │   velantrim_migrate_v3_1.py ─► V8 markdown → JSONL converter      │
│  │   fill_dependencies.py ──────► auto-fill depends_on               │
│  │   audit_metadata.py ─────────► JSONL quality audit                │
│  │   check_rfc_duplicates.py ───► duplicate RFC detector             │
│  │   utils/rfc_parser.py ───────► shared RFC parser utility          │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────────────────┐
│  │  📚 DOCUMENTATION — read and update                               │
│  │                                                                     │
│  │   README.md ─────────────────► main page                           │
│  │   ROADMAP.md ────────────────► done / next                         │
│  │   INVARIANTS.md ─────────────► rules that must not be broken       │
│  │   LIMITATIONS.md ────────────► honest list of limits               │
│  │   SYSTEM_OVERVIEW.md ────────► this file                           │
│  │   SYSTEM_OVERVIEW.en.md ─────► English companion                   │
│  └─────────────────────────────────────────────────────────────────────┘
│
└── ⚙️ CONFIGURATION: pyproject.toml · requirements.txt · LICENSE
```

---

## ⚙️ How The System Works — Step By Step

When an AI agent or a user asks a question, the system should not jump straight to the LLM.

```text
👤 User question:
   "Tell me about quantum entanglement"
         │
         ▼
🧭 Goal / Intent detection
   What does the user want: definition, explanation, proof, comparison?
         │
         ▼
🔍 Retrieval
   Find candidate facts in memory, graph, text index, and metadata
         │
         ▼
📦 Facts Pack
   Select 8-12 best facts with IDs, confidence, source, state
         │
         ▼
⚖️ Truth Gate
   Are these facts trusted enough to support an answer?
         │
         ├── no  ─► answer with uncertainty / missing evidence
         │
         ▼
🛡️ Guardian / Observer
   Check contradiction, drift, risk, Ring Zero rules
         │
         ▼
🗣️ LLM / BAE
   Convert evidence into a clear human answer
         │
         ▼
🧾 TRACE
   Show what was used, rejected, and why
```

---

## 🧠 How Memory Is Built

Velantrim memory is not just one database. It is a layered memory system.

```text
L0 Raw Input
  ↓ filtering / normalization
L1 Working Memory
  ↓ session digestion
L2 Episodic Summary
  ↓ review / Pending / Truth Gate
L3 Canonical Graph Memory
```

| Layer | Meaning | Example |
|---|---|---|
| ⚪ L0 Raw | raw files, chunks, user statements | imported PDF text |
| 🔵 L1 Working | current session context | "today we discussed Science Core" |
| 🟣 L2 Episodic | compressed episode / summary | "the user chose V8.6 as main" |
| 🟢 L3 Canonical | verified long-term truth | stable project rule |

Important:

> Nothing should enter L3 just because it was said once.  
> Canonical memory needs evidence, state, and review.

---

## 🧬 ESM — Epistemic State Machine

ESM answers one question:

> What kind of knowledge is this?

| State | Emoji | Meaning |
|---|---:|---|
| Observed | ⚪ | seen, captured, not verified |
| Hypothesized | 💭 | possible, needs confirmation |
| Supported | 🟡 | partly supported |
| Validated | ✅ | verified enough |
| ImmutableCore | 🔒 | protected canonical core |
| Contradicted | ❌ | conflicts with stronger knowledge |
| Deprecated | 🗑️ | outdated / no longer active |
| Retracted | ⛔ | withdrawn as wrong |

This prevents one of the biggest memory failures:

```text
note -> assumption -> fake fact -> future wrong answer
```

---

## ⏳ Bi-Temporal Memory

Velantrim can track two different times:

```python
# When the fact became true in the world:
valid_from = "2024-01-01"

# When the system learned it:
recorded_at = "2026-05-30"
```

This enables time-travel questions:

```text
What did I know on February 1?
What was true in the world at that time?
When did the system learn it?
```

---

## 🔒 Ring Zero — Immutable Core

Ring Zero is the protected center of the system.

It contains rules and identity-level constraints that should not be casually overwritten.

Examples:

- do not erase core facts without explicit review,
- do not promote hypotheses to truth,
- do not let LLM output override graph truth,
- do not silently rewrite memory.

---

## 📜 GraphStore ABC

`storage.py` defines what a storage backend must support.

This matters because the architecture should be able to use different storage engines without changing the entire system.

```text
GraphStore ABC
  ├── store fact
  ├── read fact
  ├── search facts
  ├── store relations
  ├── query graph paths
  └── return provenance
```

---

## 🔍 What `trace.py` Does

`trace.py` records the answer path.

It should make the system able to say:

```text
I used these facts.
I ignored these facts.
I trusted this source.
I rejected this claim.
I passed or failed the Truth Gate.
```

That is the difference between a fluent chatbot and an inspectable reasoning system.

---

## 🧪 Tests — What They Protect

| Test Area | Protects |
|---|---|
| ESM tests | state transitions do not break |
| pipeline tests | query route stays wired |
| regression tests | old P0 bugs do not return |
| integration tests | API and memory still work together |
| adversarial tests | bad IDs, NaN confidence, forbidden transitions |

Tests are part of the architecture because Velantrim is a memory system. A memory system without tests slowly becomes unreliable.

---

## 📚 Documents — What To Read

| Document | Meaning |
|---|---|
| `README.md` | Russian main README |
| `README.en.md` | English companion README |
| `SYSTEM_OVERVIEW.md` | Russian overview |
| `SYSTEM_OVERVIEW.en.md` | English overview |
| `docs/VELANTRIM_ARCHITECTURE.md` | Russian architecture |
| `docs/VELANTRIM_ARCHITECTURE.en.md` | English architecture |
| `docs/RESEARCH_MODE.ru.md` | experimental memory mode |
| `docs/ATTENTION_NOETIC_ORCHESTRATION.ru.md` | attention / noetic contracts |
| `docs/WORLD_KNOWLEDGE_CORE_v1_0.ru.md` | future knowledge core |

---

## ⏳ What Works Now vs What Is Research

```text
WORKS NOW
  🧠 memory.py       ESM, L0/L1 storage, facts
  🔍 retrieval       BM25 / hybrid search
  ⚖️ Truth Gate      fact validation
  🧾 TRACE           provenance and answer trace
  🖥️ console         browser test surface

RESEARCH / FUTURE
  🌌 Fractal Router
  🧬 Essence Layer
  🧠 Noetic Core
  📚 World Knowledge Core
  🔮 Predictive Reasoner
  🛡️ Adversarial / meta reasoning
```

---

## 🔑 Three Main Principles

### 1. 🧠 Memory Must Be Honest

The system must distinguish:

```text
I saw it
I believe it
I verified it
I derived it
I predict it
I do not know
```

### 2. ⚖️ Truth Must Not Belong To The LLM

The LLM is useful, but it is not the source of truth.

Truth belongs to:

```text
Graph + Evidence + State + Source + Trace
```

### 3. 🧾 Every Important Answer Needs A Trace

Without trace, the system is only persuasive.  
With trace, it becomes inspectable.

---

## 🧭 Simple Explanation

If a normal AI is like a person talking from memory, Velantrim is more like:

```text
library + notebook + fact checker + map + assistant
```

It does not just answer. It tries to remember what matters, check what is true, connect ideas, and show the path.

---

## 🧩 Full Detail Mirror From Russian Source

This section keeps the English overview closer to the Russian original. It is intentionally detailed, because the Russian document is not only a summary — it is also a visual operational map.

---

## ⚙️ Full Pipeline — Runtime View

```text
👤 User question:
   "Tell me about quantum entanglement"
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  ⚙️ pipeline.py — Main pipeline                         │
│                                                         │
│  Step 1 🔎 RETRIEVE                                     │
│  └─► Find relevant facts                                │
│      Current MVP: BM25 over mock / local DB             │
│      Result: [{fact about quantum entanglement, ...}]   │
│                                                         │
│  Step 2 📦 BUILD FACTS PACK                             │
│  └─► Save each candidate fact through memory.py         │
│      Initial state = Observed                           │
│                                                         │
│  Step 3 🔍 BUILD TRACE                                  │
│  └─► trace.py builds the provenance chain               │
│      fact_id + source + epistemic_state + score         │
│                                                         │
│  Step 4 🛡️ GUARDIAN                                     │
│  ├─► Does every fact have fact_id?                      │
│  ├─► Does every fact have claim and source?             │
│  ├─► Is every fact covered by trace?                    │
│  └─► If not: BLOCK, no answer                           │
│                                                         │
│  Step 5 🔐 TRUTH GATE                                   │
│  ├─► confidence >= floor?                               │
│  ├─► source is not empty?                               │
│  ├─► evidence is sufficient?                            │
│  └─► If not: BLOCK or answer with uncertainty           │
│                                                         │
│  Step 6 🔄 ESM TRANSITION                               │
│  └─► Facts move only through transition_esm()           │
│      Direct state mutation is forbidden                 │
│                                                         │
│  Step 7 💬 GENERATE ANSWER                              │
│  └─► Use only allowed facts                             │
│      Current: simple composition                        │
│      Future: LLM / BAE + Essence + NoeticCore           │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │
         ▼
👤 Answer:
   "Quantum entanglement links particle states..."
   + trace: [f2 | source=physics | state=Validated | bm25=1.23]
```

---

## 🌱 Fact Lifecycle — ESM In Detail

```text
                    🌱 LIFE OF A FACT
                    ────────────────

  Observed ──────► Hypothesized ──► Supported ──► Validated ──► ImmutableCore
     │                  │               │               │        Ring Zero only
     │                  │               │               │
     └──────────────────┴───────────────┴──► Contradicted ──► Deprecated ──► Collapsed
                                                conflict        obsolete       inactive

Rules:
✅ transitions only through allowed directions
✅ Collapsed and ImmutableCore are terminal
✅ state changes only through transition_esm()
❌ forbidden: UPDATE facts SET epistemic_state = 'Validated'
❌ forbidden: fact["epistemic_state"] = "Validated" in code
```

---

## 🗄️ Storage Layers — Original Detail

```text
  ┌──────────────────────────────────────────────────┐
  │  L0 — Workbench                                  │
  │  128 freshest facts · OrderedDict LRU             │
  │  Fastest access — no disk read                    │
  └──────────────────────┬───────────────────────────┘
                         │ cache miss
                         ▼
  ┌──────────────────────────────────────────────────┐
  │  L1 — Archive                                    │
  │  SQLite on disk · all facts · transition history │
  │  + bi-temporal: when learned / when true         │
  └──────────────────────┬───────────────────────────┘
                         │ future / graph layer
                         ▼
  ┌──────────────────────────────────────────────────┐
  │  L3 — Knowledge Graph                            │
  │  Relations between facts · semantic retrieval    │
  │  GraphStore ABC is ready for implementation      │
  └──────────────────────────────────────────────────┘
```

---

## 🔍 Trace Record — Detailed Shape

```json
{
  "fact_id": "f2",
  "source": "physics",
  "origin": "retrieval",
  "epistemic_state": "Validated",
  "retrieval_score": 1.23,
  "source_confidence": 0.85,
  "retrieved_at": "2026-05-11T...",
  "promoted_at": "2026-05-11T...",
  "promoted_by": "pipeline.run"
}
```

Difference:

| Field | Meaning |
|---|---|
| `retrieval_score` | query-dependent relevance score |
| `source_confidence` | stable trust in the source |

This distinction is important: a fact can be very relevant to a query but come from a weak source.

---

## 🔧 Migration Tools — Why They Exist

```text
V8 Crystal Specification (markdown, 18 784 lines)
       │
       │  velantrim_migrate_v3_1.py
       │  ├── splits into chunks
       │  ├── Cyrillic → ASCII IDs
       │  ├── extracts RFC mentions
       │  ├── assigns layer L0/L1/L2/L3...
       │  └── backup + rollback + dry-run
       ▼
Velantrim_V8_Crystal_Sprint1.jsonl
       │
       │  fill_dependencies.py
       │  └── finds RFC links → fills depends_on
       ▼
Knowledge base with dependencies
       │
       │  audit_metadata.py / check_rfc_duplicates.py
       └── quality checks: duplicates, null fields, mega-blobs

utils/rfc_parser.py:
  extract_rfc("...RFC0067 v2.0...")       → "RFC0067 v2.0"
  extract_rfc_mentions("RFC0036–0051")    → [RFC0036, ..., RFC0051]
```

These tools are not runtime memory. They are migration and quality-control tools.

---

## 🧪 Tests — Detailed Responsibility Map

```text
tests/
│
├── test_esm.py
│   ✅ exactly 8 ESM states
│   ✅ transitions only through allowed paths
│   ✅ Ring Zero immutable
│   ✅ new facts start as Observed
│   ✅ drift protection
│   ✅ bi-temporal fields on creation
│   ✅ invalidate_edge never deletes, only closes validity
│   ✅ LRU cache: 128 slots, old entries evicted
│   ✅ transition history records caller
│   ✅ deepcopy prevents external corruption of L0
│
├── test_pipeline.py
│   ✅ happy path: question → Validated facts → answer
│   ✅ no matches → blocked, not crashed
│   ✅ repeated query is idempotent
│   ✅ tokenization handles dashes correctly
│   ✅ retrieval_score != source_confidence
│   ✅ Guardian blocks uncovered facts
│   ✅ TruthGate blocks low confidence
│   ✅ promote_trace records promoted_by
│
├── test_regression_p0.py
│   ✅ old P0 bugs do not return
│   ✅ repeated store_fact does not reset Validated to Observed
│   ✅ separate SQLiteGraphStore instances stay isolated
│   ✅ Collapsed sets t_ingestion_end
│   ✅ invalidate_edge does not delete fact
│
└── test_sprint_a_wiring.py
    🛡️ sentinel test
    It checks that A6-A10 are NOT wired too early:
    event_bus, lock_manager, circuit_breaker,
    rate_limiter, health_check.
```

---

## 📚 Documentation Maintenance Rules

```text
READ DURING ONBOARDING
  1. README.md
  2. SYSTEM_OVERVIEW.md
  3. ROADMAP.md
  4. INVARIANTS.md
  5. LIMITATIONS.md

UPDATE EACH SPRINT
  README.md        version, file table, fixes
  ROADMAP.md       planned → done
  INVARIANTS.md    new invariants
  LIMITATIONS.md   remove closed limitations
  WORK_SUMMARY.md  sprint journal

DO NOT TOUCH AS CURRENT DOCS
  AUDIT_DIFF_REPORT.md
  METADATA_FIX_REPORT.md
  audit_issues.json
  validate_dangling.json
  velantrim_migration.log
  SANDBOX_CLONE.md

UPDATE WHEN A6-A10 ARE CONNECTED
  SPRINT_A_NOTES.md
  test_sprint_a_wiring.py
```

---

## ✅ What Works Now vs What Comes Next — Detailed

```text
✅ WORKS NOW
──────────────────────────────────────
🧠 memory.py
  ESM states
  L0 LRU
  L1 SQLite
  bi-temporal fields
  Ring Zero immutability
  trusted source whitelist
  drift protection
  audit trail

🔍 trace.py
  provenance chain
  atomic promote
  retrieval_score / source_confidence split

📜 storage.py
  GraphStore ABC
  bi-temporal contract methods

⚙️ pipeline.py
  BM25 Okapi retrieval
  Guardian + TruthGate placeholders / wiring
  idempotent run()

🔐 truth_gate.py
  real Truth Gate
  mode-aware: PRECISION / BALANCED / EXPLORATION / CREATIVE
  source + confidence + evidence + contradiction checks

🔎 hybrid_retriever.py
  BM25 + dense embeddings + RRF
  graceful degradation if dependencies are missing

📊 mhi.py
  Memory Health Index
  HEALTHY / DEGRADED / SAFE_MODE

📚 ngram_index.py
  FTS5 trigram pre-filter

💤 sleep_time_worker.py
  background consolidation
  idle think() cycle

🗂️ embedding_registry.py
  embedding model registry

🧪 tests/
  broad test coverage for memory, pipeline, retrieval, safety

🚧 NEXT
──────────────────────────────────────
S2a  HybridRetriever fully wired
S2b  SQLite FTS5 replacing mock database path
S2c  async/await + aiosqlite
S2c  A6-A10 wiring when ready
S2c  Neo4jGraphStore implementation

📋 SPRINT 3+
──────────────────────────────────────
RFC0066 ConceptEmergence
RFC0065 Memory Volition
RFC0067 Analogy Graph
RFC0063 Knowledge Ingestion Pipeline
RFC0068 NeuroCore / plastic memory
```

---

## 🔑 Three Main Principles — Full Form

```text
1. Graph = Truth
   Neo4j / graph memory is the intended truth store.
   LLM can speak beautifully, but it does not decide what is true.
   A fact enters the graph only after Truth Gate.
   No Truth Gate → no canonical write.

2. Memory = Physiology
   Memory behaves like a living system:
   L0 = working memory
   L1 = episodic / archival memory
   L3 = long-term structured memory
   Facts can age, decay, consolidate, or be deprecated.

3. Dual-Process
   Fast Path: milliseconds, user waits, must stay light.
   Slow Path: background, async, consolidation, learning, GC.
   Heavy work belongs to Slow Path.
```

Final source formula:

```text
Graph = Truth
LLM = Language
Memory = Physiology
Volition = Agency
```
