# 🧠 Titan Cognitive Development Map

> **Status:** `PROPOSED ORIENTATION · FUTURE-WORK / RESEARCH MAP · NOT IMPLEMENTATION AUTHORITY`
>
> **Reality rule:** this document describes desired capabilities and research directions. It does **not** claim that a capability is implemented, tested, wired, enabled, observed, production-ready, or authorized merely because it is named here.
>
> **Authority rule:** `capability idea != implementation authorization != runtime authority != production authority`.

## 1. Purpose

This document preserves a human-readable and technical map for developing Velantrim Exo-Cortex Titan without reducing the project to a collection of fashionable RAG frameworks or isolated modules.

The central design question is:

> **What capability should Titan have as a cognitive system, what human or biological function inspires it, what technical mechanism could implement it, and what evidence would justify adoption?**

The preferred reasoning order is:

```text
human idea / capability
→ technical requirement
→ current Titan mechanism
→ observed gap
→ candidate design
→ sandbox/shadow evidence
→ bounded architecture decision
→ separately authorized implementation
```

Technology selection comes after capability definition:

```text
capability first → technology second
```

Examples:

```text
associative long-term recall → evaluate HippoRAG-like ideas
hierarchical document understanding → evaluate RAPTOR-like ideas
retrieval quality correction → evaluate CRAG-like ideas
text + graph reasoning → evaluate KAG-like ideas
```

No external framework gains Canon, evidence, identity, belief, action, or runtime authority merely by being evaluated.

---

## 2. Human ↔ technical audit model

Every future capability should be reviewed in two layers.

### Human layer

Ask:

- What does this capability mean to a person?
- What human, animal, plant, fungal, ecological, or collective information-processing ability is being abstracted?
- What behavior would make a user say, “yes, this system actually remembers / understands / learns from experience”?
- What behavior would reveal that the system only stores data or imitates the appearance of cognition?

### Technical layer

Ask:

- Which component owns the capability?
- Which state is authoritative?
- What is derived/rebuildable?
- What evidence, provenance, temporal scope, epistemic state, and policy apply?
- What are the failure modes?
- What can be tested deterministically?
- What must remain proposal-only or shadow-only?

Use the bridge:

```text
human idea
→ human/biological capability
→ technical mechanism
→ current state
→ gap
→ possible improvement
```

A class, table, flag, graph, or model name is not proof that the human-level capability exists.

---

# 3. Priority map

## 🔴 FOUNDATION — strengthen before adding more intelligence

These are foundations that should be treated as architecture/correctness work, subject to live revalidation and separate authorization.

### F1 — EvidenceRefV1 / evidence integrity

**Human meaning:** Titan should know *why* it believes a retrieved claim deserves attention and whether apparently multiple sources are actually independent.

**Desired properties:**

- content digest / hash;
- source locator and revision;
- lineage;
- independence class;
- scope;
- observed time;
- resolvability;
- duplicate/same-lineage detection;
- explicit provenance.

**Invariant:**

```text
five references to the same lineage != five independent pieces of evidence
```

**Boundary:** the contract may be shared, but trusted evidence admission belongs to the evidence-owning domain; Titan must not turn transport/composition into evidence authority.

### F2 — Final-answer grounding / claim validation

**Human meaning:** even if Titan retrieved correct evidence, the final language model must not silently add unsupported claims.

Target pattern:

```text
FactsPack / ContextPack
→ generated answer
→ claim extraction/decomposition
→ evidence matching
→ supported / unsupported / uncertain
→ correction / abstention / qualified answer
```

**Invariant:**

```text
trusted retrieval != guaranteed faithful final prose
```

### F3 — Authority and ownership boundaries

Preserve independent ownership rather than building a hidden sovereign “brain”.

At ecosystem level:

- Crystal: trusted memory/evidence admission and provenance boundary;
- Soul: beliefs, identity, relationships, commitments, self-model;
- Titan: orchestration, integration, retrieval composition, experiments, providers/tools, benchmarks;
- Native Kernel: technology-neutral semantic laws/invariants;
- Mentaury Kernel: composition contracts/conformance;
- Continuum: process-continuity research, shadow-only by default.

**Core invariant:**

```text
integration != authority transfer
```

### F4 — Security and fail-closed behavior

Revalidate API/auth boundaries, error leakage, endpoint exposure, capability scope, replay, delegation, and configuration behavior before production claims.

**Invariant:**

```text
recovery / convenience / orchestration must not expand authority
```

### F5 — Component lifecycle registry

Every significant component should have an explicit state such as:

```text
LIVE
GATED
SHADOW
RESEARCH
DORMANT
DEPRECATED
ARCHIVED
```

This prevents research code, feature-gated code, and runtime code from being confused.

---

## 🟢 DEVELOP NEXT — cognitive capabilities worth strengthening after foundations

These are capability directions, not automatic milestones.

### D1 — Memory Metabolism

Treat memory as a process rather than a static store:

```text
observe
→ encode candidate
→ admit
→ link
→ retrieve
→ compare
→ revise
→ consolidate
→ weaken/archive/forget
→ reuse as experience
```

Memory should preserve different roles rather than flattening everything into a single vector store.

Relevant forms/processes include:

- semantic memory;
- episodic memory;
- procedural/system memory;
- working/context memory;
- temporal memory;
- associative memory;
- replay/experience;
- consolidation;
- supersession;
- forgetting/decay/archive/erasure;
- priming;
- contradiction management.

### D2 — Temporal understanding

**Human meaning:** “It used to be true, then it changed.”

Technical mechanisms may include:

- valid/event time;
- ingestion/knowledge time;
- supersession;
- version history;
- `as-of` queries;
- temporal scope on claims/evidence;
- explicit distinction between historical and current state.

**Invariant:**

```text
latest record != complete temporal understanding
```

### D3 — Replay / experience memory

**Human meaning:** Titan should remember not only facts, but what was tried and how it ended.

Target experience chain:

```text
Situation
→ Decision
→ Evidence
→ Action
→ Result
→ Error / success
→ Correction
```

Replay should support comparison and learning without automatically converting past behavior into a permanent rule.

### D4 — Consolidation and forgetting

Separate:

- retrieval decay;
- compression/summarization;
- archive;
- expiry;
- supersession;
- legal/user erasure.

A deleted or revoked item must not remain reachable through stale caches, vector indexes, graph projections, or summaries.

### D5 — Epistemic reasoning and uncertainty

Distinguish at least:

```text
observation
claim
hypothesis
supported claim
contradicted claim
unknown
uncertain
```

Confidence alone is insufficient. Provenance, authority, independence, contradictions, temporal validity, and admission status matter independently.

### D6 — Attention / salience

Retrieval relevance should eventually consider more than embedding similarity:

- active goal;
- current project/task;
- temporal relevance;
- unresolved contradiction;
- risk;
- relationships/commitments where authorized;
- recent events;
- evidence quality.

Attention is a selection mechanism, not truth authority.

### D7 — Context composition

Compose bounded working context from memory, evidence, graphs, task state, policy, and temporal status.

Context composition must remain separate from admission authority.

### D8 — Multiple graph views

Avoid one universal graph with overloaded semantics. Candidate views include:

- entity/relationship graph;
- temporal graph;
- causal graph;
- evidence/provenance graph;
- project/code graph;
- experience graph;
- associative graph.

**Invariant:**

```text
related_to != causes
```

### D9 — Associative memory

Explore recall through relationship structure and salience, not only lexical/vector similarity. Associative memory should remain evidence-aware and must not promote graph proximity into truth.

---

## 🟡 SHADOW LAB — evaluate, do not grant authority

These approaches may be valuable as adapters/projections/experimental routes. They should be tested against the existing Titan baseline on identical corpora and tasks.

### S1 — HippoRAG 2-style associative retrieval/memory

Research question: does graph-based associative recall improve long-term and multi-hop memory compared with Titan baseline retrieval without degrading provenance or temporal correctness?

### S2 — KAG-style text + knowledge-graph reasoning

Research question: can structured graph/text reasoning improve expert and multi-hop questions without turning generated graph relations into evidence or Canon?

### S3 — RAPTOR-style hierarchical summaries

Research question: do recursive/hierarchical summaries improve long-document and multi-level reasoning while remaining derived and traceable to source evidence?

### S4 — CRAG-style corrective retrieval

Research question: can a separate retrieval-quality evaluator detect poor candidate sets and trigger bounded alternate retrieval without becoming a universal truth judge?

### S5 — GraphRAG / LightRAG ideas

Research question: which community, global-summary, incremental-graph, and high/low-level retrieval ideas add measurable value beyond Titan’s own graph/retrieval primitives?

### S6 — CAG / context caching

Treat as an optimization profile for stable bounded corpora, not durable memory and not a replacement for evidence-aware retrieval.

### S7 — Adaptive retrieval

Continue evaluating query-complexity/cost-aware selection of lexical, hybrid, dense, reranked, and graph-expanded routes.

### S8 — Priming

Research temporary, decaying readiness states that alter attention/retrieval after meaningful events without turning the event into permanent Canon.

### S9 — Reflection and hierarchical consolidation

Reflection may produce:

```text
CandidateInsight / Hypothesis / Proposal
```

It must not directly produce trusted fact, identity fact, or action authority.

### Shadow requirements

Every shadow experiment should preserve:

```text
baseline Titan
same corpus
same questions/tasks
same evaluation rubric
exact configuration
exact code/model versions
no direct trusted-memory write
no authority escalation
reproducible metrics
```

Candidate outcomes:

```text
ADOPT IDEA
ADAPT
KEEP SHADOW
RESEARCH MORE
DEFER
REJECT
```

Framework popularity is not an adoption criterion.

---

## 🔵 RESEARCH / HYPOTHESIS — preserve for future investigation

These ideas should remain explicitly research/hypothesis until evidence supports a bounded use.

### R1 — Distributed nervous-system architecture

Biological inspiration: octopus-like local sensor/limb processing.

Potential future robotics abstraction:

```text
high-level intent
→ local bounded controllers
→ fast local reflexes
→ important events propagate upward
```

Research value: reduce central bottlenecks and latency in embodied systems.

### R2 — Swarm cognition

Biological inspiration: ants, bees, termites, flocking/schooling.

Research local, bounded processes that explore alternatives and leave signals without creating an uncontrolled multi-agent authority structure.

### R3 — Plant-inspired priming and adaptive response

Study temporary adaptive readiness, stress history, decay, and local signaling as computational abstractions. Do not anthropomorphize plant processes as human cognition.

### R4 — Fungal / slime-mold adaptive networks

Study decentralized path strengthening, pruning, resource allocation, and network resilience for derived graph/retrieval routing.

### R5 — Immune-system-inspired memory

Potential abstractions:

- anomaly/threat memory;
- faster response to repeated patterns;
- quarantine;
- source/reputation signals;
- decay and tolerance.

Security memory must remain separate from truth/evidence authority.

### R6 — Active inference / predictive world models

Future embodied loop:

```text
prediction
→ observation
→ prediction error
→ model update / bounded action
```

This may become relevant to robotics and sensor fusion after memory/evidence foundations are proven.

### R7 — Reflex and embodied robotics architecture

Research layered control where low-latency safety/reflex loops do not require central LLM reasoning. Sensor processing, action authority, and cognitive planning should remain separable.

### R8 — Bioelectric-inspired computation

Preserve as long-horizon research. Require clear computational hypotheses and falsifiable experiments before architectural adoption.

### R9 — Multi-agent / blackboard cognition

Not categorically forbidden, but any shared workboard must remain non-authoritative:

```text
Blackboard != Canon
```

### R10 — Safe self-modification

Autonomous changes to authority, policy, Canon, trust boundaries, or system instructions remain prohibited without explicit target-domain authorization. Research may focus on proposal generation, simulation, and bounded configuration adaptation.

---

# 4. What not to do

Do not turn Titan into:

```text
Titan
+ KAG
+ HippoRAG
+ GraphRAG
+ LightRAG
+ RAPTOR
+ CRAG
+ CAG
+ every new framework
```

A collection of branded subsystems is not a cognitive architecture.

Reject or defer patterns that create:

- direct model-to-trusted-memory writes;
- framework-owned Canon;
- a universal “truth oracle”;
- automatic promotion of reflection into fact;
- hidden authority transfer through integration;
- automatic production activation;
- claims that green CI proves operational authorization;
- claims that retrieval or graph proximity proves truth;
- one opaque confidence score for all epistemic questions.

---

# 5. Sandbox characterization before major expansion

Before adopting new cognitive/retrieval systems, characterize the existing Titan as a running system in a disposable laboratory.

Preferred lab rules:

```text
exact GitHub SHA
fresh disposable sandbox
synthetic data only
no production secrets
external side effects disabled by default
no direct main mutation
no production authority
reproducible experiment receipt
```

The lab should compare three realities:

```text
Titan described in documentation
Titan visible in source code
Titan behavior observed at runtime
```

Priority experiment families:

1. baseline installation/startup/tests;
2. semantic/episodic/procedural memory;
3. temporal memory;
4. replay/experience;
5. retrieval;
6. graphs and causal distinctions;
7. EvidenceRef/evidence independence;
8. TruthGate/Guardian behavior;
9. final-answer faithfulness;
10. forgetting/erasure and derived projections;
11. recovery/self-healing without authority escalation;
12. security/fail-closed behavior;
13. persistence/restore;
14. long-conversation/user-history scenarios;
15. scale within laboratory resource limits.

Each experiment should end with:

```text
Experiment ID
Titan SHA
configuration
human capability tested
technical subsystem
input
expected behavior
observed behavior
PASS / PARTIAL / FAIL / UNKNOWN
evidence/logs/metrics
architecture implication
next classification: NONE / FIX / SHADOW / RESEARCH / DEFER
```

A sandbox runtime execution does not imply production authorization:

```text
laboratory runtime execution != production authority
```

---

# 6. Decision gates

Use the following conceptual progression for new capabilities:

```text
HYPOTHESIS
→ RESEARCH
→ SHADOW
→ reproducible evidence
→ architecture decision
→ separately authorized bounded implementation
→ tested/wired state
→ separately authorized activation
```

Do not skip directly from interesting paper/module to production path.

A useful external idea may be adopted as an algorithmic principle without importing an entire framework.

---

# 7. Recommended immediate architectural direction

The next cognitive design artifact should be a bounded **Memory Metabolism** specification that explains how the following interact without collapsing their authority or semantics:

```text
temporal memory
+ replay / experience
+ consolidation
+ forgetting / supersession
+ associative retrieval
+ epistemic status
+ provenance/evidence
+ attention/salience
+ context composition
```

The specification should answer, in human and technical language:

- what is remembered;
- why it is remembered;
- who may admit it;
- how it changes over time;
- how contradictions are represented;
- how experience differs from fact;
- how retrieval differs from evidence;
- how old information is weakened, superseded, archived, or erased;
- how working context is composed;
- what outputs remain proposals/hypotheses;
- how every significant conclusion remains traceable.

This document does **not** authorize that specification to be implemented automatically.

---

# 8. Durable invariants

```text
research != runtime
specification != implementation
implementation != architecture Canon
integration != authority transfer
retrieval != evidence
receipt != truth
claim != belief
evidence != identity
identity != authority
model output != Canon
CI green != production authorization
pilot != evidence
shared vocabulary != shared ownership
reflection != fact
experience != universal rule
association != causation
projection != source of truth
laboratory runtime != production authority
```

---

# 9. Current reality statement

This document intentionally avoids claiming that the capabilities above are currently live. Before any implementation or experiment, re-resolve live GitHub `main`, current open PRs/issues, runtime flags, tests/CI, relevant Notion records, and component ownership.

The map is a **durable orientation and research classification**, not an evergreen status report.
