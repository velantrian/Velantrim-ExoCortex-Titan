# PR-ARCH-00: Titan Milestone 1 Architecture Baseline

- **Status:** PROPOSED
- **Scope:** Milestone 1 only
- **Date:** 2026-08-02
- **Repository:** `velantrian/Velantrim-ExoCortex-Titan`
- **Decision owner:** human operator / maintainer

## 1. Context

Titan already contains a substantial production-oriented memory runtime. The current repository includes, among other components:

- a stdlib-first Python 3.11+ core;
- SQLite-backed memory and conversation notebooks;
- an 8-state ESM and TruthGate/WriteGate path;
- provenance, traces and audit-oriented records;
- hybrid retrieval and graph-oriented memory modules;
- an existing `ComputeController` with explicit compute paths;
- an existing `ConversationConsolidator` that writes a non-canonical conversation notebook in the same SQLite database;
- immutable contract patterns using `dataclass(frozen=True, slots=True)`, NFC normalization and deterministic SHA-256 identities.

The next milestone adds cross-conversation continuity and bounded active context. The primary architectural risk is not lack of features; it is duplication of authority:

- a second canonical memory;
- a second compute controller;
- a second truth system;
- a second conversation store with incompatible contracts;
- an event bus mistaken for a durable event ledger.

This ADR freezes the Milestone 1 boundaries before runtime integration.

## 2. Decision

Milestone 1 will implement one read-only/shadow vertical slice:

```text
neutral interaction history
        -> conversation episode
        -> deterministic continuity relation
        -> prior decision / open-loop recovery
        -> bounded continuity context pack
        -> receipt and replay
```

The first user-visible answer path remains unchanged until the shadow slice passes the acceptance gates in this ADR.

## 3. Current and target state

### 3.1 Current state

| Responsibility | Current implementation |
|---|---|
| Fact and epistemic memory | Titan memory + ESM + TruthGate/WriteGate |
| Current query routing | `core/compute_controller.py` |
| Current session/conversation notebook | `core/conversation_consolidation.py` and related runtime |
| Canonical content identity patterns | `core/knowledge_capsule.py`, `core/reader_core_contracts.py` |
| Context assembly | existing `ContextPack` and retrieval modules, partial |
| Durable neutral interaction ledger | no single neutral ledger contract |
| Cross-conversation thread continuity | no authoritative deterministic layer |

### 3.2 Target state

| Responsibility | Target owner |
|---|---|
| Neutral durable interaction history | Native Kernel through `NeutralEventPort` |
| Transitional shadow history | Titan-owned `LocalShadowLedger` |
| Epistemic admission/status | existing Titan epistemic path |
| Conversation episode construction | CSL bridge over existing consolidator |
| Thread linking and state reconciliation | Titan Continuity & Situation Layer (CSL) |
| Continuity-specific selection | CSL Context Assembler |
| Full active-context budgeting | Adaptive Context Manager (ACM) |
| Processing depth | existing `ComputeController` |
| Advice form | future Advisory Gate |
| External side effects | Guardian / future explicit Action Gate contract |

Native Kernel is a target dependency, not a prerequisite for Milestone 1.

## 4. Ownership model

```text
Neutral Event Layer
  asks: What happened?

Epistemic Layer
  asks: What is asserted, and on what evidence?

CSL
  asks: How is the past connected to the present?

ACM
  asks: What should fit into working context now?

ComputeController
  asks: How deeply should the request be processed?

Advisory Gate
  asks: Should the system remind, ask, suggest, defer or remain silent?

Action Gate
  asks: Is an external side effect allowed?
```

One decision type must have one owner.

An independent `CentralExecutive` is not created in Milestone 1. Executive compute policy remains an extension point of the existing `ComputeController`. Advice and external-action decisions remain separate gate responsibilities.

## 5. Epistemic axes

The following concepts are independent and must never be collapsed into one enum or field.

### 5.1 Origin

Where an assertion came from, for example:

- `USER_STATED`
- `DOCUMENT_STATED`
- `SYSTEM_OBSERVED`
- `SYSTEM_MEASURED`
- `MODEL_INFERRED`
- `EXTERNAL_STATED`

### 5.2 Epistemic disposition

How the epistemic layer currently evaluates an assertion, for example:

- `UNKNOWN`
- `ASSERTED`
- `CORROBORATED`
- `CONTESTED`
- `RETRACTED`

This axis does not replace the repository's existing ESM. A later adapter may map continuity contracts to the authoritative ESM without redefining it.

### 5.3 Projection status

How an immutable assertion is used in a rebuildable current-state projection, for example:

- `CURRENT`
- `STALE`
- `SUPERSEDED`
- `CONTESTED`
- `EXPIRED`
- `UNRESOLVED`

`USER_STATED` means that the user made a statement. It does not automatically establish the external-world truth of the statement.

## 6. System invariants

### I-01. Query-time canonical writes are forbidden

A query may write telemetry, trace data, non-canonical receipts and shadow-evaluation output. It may not silently create, promote, retract or mutate canonical claims.

### I-02. Eviction is not deletion

Removal from ActiveContext or a rebuildable cache never implies deletion of a durable record.

### I-03. Origin, epistemic disposition and projection status are separate

No enum or field may silently combine these axes.

### I-04. Inference keeps its origin

A confidence value cannot convert `MODEL_INFERRED` into `USER_STATED` or into an objective fact.

### I-05. Provenance is mandatory

Every durable assertion and relation has source references, actor information, timestamps and schema identity.

### I-06. Durable assertions are immutable

Later correction, contradiction, support or supersession is represented by a new record/relation and a rebuilt projection. Existing assertion payloads are not rewritten.

### I-07. Projections are rebuildable

Current state, active goals and open loops are derived views. They are not a second canonical truth.

### I-08. Privacy is applied before retrieval and assembly

Authorization context, purpose, visibility and sensitivity are resolved before candidates enter the continuity/context pipeline.

### I-09. Neutral interaction events bypass TruthGate

The occurrence of a message/action is a neutral historical event. A derived `AssertionCandidate` enters the epistemic admission path; the raw occurrence event does not.

### I-10. Kernel contracts are cognitively neutral

Kernel-level contracts do not contain salience, goal priority, open-loop importance, advice usefulness, emotional interpretation or processing modes.

### I-11. Canonical serialization precedes ledger implementation

Timestamp normalization, Unicode normalization, collection ordering, number policy, hash scope and schema versioning must be specified and tested before `LocalShadowLedger` is introduced.

### I-12. Shadow mode has no response authority

Continuity, ACM and advisory shadow outputs do not change the main answer until separately promoted.

### I-13. Silent overwrite is forbidden

An existing ID with the same canonical hash is an idempotent replay. An existing ID with a different hash is an integrity conflict.

### I-14. One decision type has one owner

CSL does not decide truth, ACM does not decide compute depth, ComputeController does not decide advice form, and advisory policy does not authorize external side effects.

## 7. Milestone 1 implementation path

### PR-CONT-01: Core continuity contracts

Implement only:

- `ActorRef`
- `SubjectRef`
- `InteractionEvent`
- `AssertionRecord`
- `AssertionRelation`

Use the repository's existing stdlib-first style:

- `dataclass(frozen=True, slots=True)`;
- construction-time validation;
- immutable nested values;
- timezone-aware UTC timestamps;
- NFC normalization;
- deterministic JSON and SHA-256;
- no Pydantic dependency in the domain core.

### PR-CONT-01A: Conformance fixtures

Add golden canonical-byte/hash fixtures, negative fixtures and round-trip tests.

### PR-CONT-02: NeutralEventPort and LocalShadowLedger

Provide append/read/scan/head/verify semantics, monotonic sequence numbers, idempotency and integrity conflicts. Do not add pub/sub, background handlers or `flush()`.

### PR-CONT-03: Conversation bridge

Adapt the existing `ConversationConsolidator`; do not create a second summarizer or a second canonical conversation database.

### PR-CONT-04: Deterministic thread linking

Start with explicit references, project/goal/open-loop identifiers and source-backed prior decisions. Semantic/LLM linking remains research-only.

### PR-CONT-05: Shadow continuity pack

Produce a source-linked `ContinuityContextPack` and `ContinuityReceipt`. The main response remains unchanged.

### Later Milestone 1 work

After the first continuity demo:

- state reconciler;
- goal/open-loop projections;
- static-budget ACM;
- deterministic eviction;
- ComputeController continuity/context signals;
- replay metrics;
- advisory shadow.

## 8. First demonstration scenario

Conversation A:

> First finish the MVP. Defer the new architecture layer.

Conversation B:

> Let us add another architecture layer.

The shadow pipeline must produce:

- the prior explicit goal;
- the prior decision to defer the layer;
- an unresolved/open continuity item;
- source references;
- an uncertainty marker that the priority may have changed;
- deterministic reason codes and policy version.

It must not silently assert that the old priority is still current.

## 9. Acceptance gates

### Contract gate

- same logical payload -> same canonical bytes and SHA-256;
- changed hashed field -> changed hash;
- naive datetime rejected;
- missing provenance rejected;
- mutable/unsupported payload values rejected;
- duplicate set-like refs rejected;
- unsupported schema rejected.

### Shadow-ledger gate

- append-only;
- deterministic scan;
- monotonic sequence;
- idempotent replay;
- integrity conflict on same ID/different hash;
- real hash recomputation in `verify()`;
- feature flag off by default.

### Continuity gate

- provenance coverage: 100% on fixtures;
- inference-as-fact: 0;
- privacy leakage: 0 on fixtures;
- replay divergence: 0;
- main answer mutation: 0;
- canonical query-time writes: 0.

Metrics such as false thread merge and missed continuation are measured; they are not assumed to be zero.

## 10. Rollback

Every runtime PR must be feature-flagged or shadow-only.

Rollback means:

- disable the new path;
- keep the existing query and consolidation paths authoritative;
- preserve shadow records for diagnosis;
- avoid production-memory migrations until conformance is proven.

## 11. Research Mode boundary

Research Mode is allowed in parallel, but has no production authority.

Every research item must define:

- question and hypothesis;
- synthetic or explicitly consented dataset;
- metrics;
- risks;
- promotion and rejection criteria;
- owner and expiry/review date.

Research prototypes must not:

- write Canon;
- mutate ESM;
- influence the main answer;
- use production personal data without a dedicated approval path;
- be documented as implemented capability.

### Initial research backlog

- human-context hypotheses with short TTL and explicit correction;
- presentation/authorial lenses that cannot change facts or evidence;
- whether any legitimate responsibility remains for a future Central Executive;
- learned salience against deterministic priority classes;
- LLM-proposed thread links behind deterministic validation;
- semantic-pack unit design;
- live hardware-aware context budgets;
- graph-store alternatives;
- extraction of shared contracts after a second real consumer exists;
- multi-agent delegation/provenance;
- values/mandates/protected-policy governance;
- an `EpistemicReadPort` compatible with current Titan memory and a future Crystal-like implementation.

Promotion from research requires a separate ADR and production acceptance gates.

## 12. Consequences

### Positive

- prevents a parallel truth or memory system;
- reuses the existing ComputeController and consolidator;
- preserves a neutral future Native Kernel boundary;
- establishes deterministic cross-language-compatible records;
- gives research freedom without production authority;
- creates an early continuity demo before active advice.

### Costs

- slower initial feature activation;
- explicit schema/version discipline;
- more fixture and replay work;
- research prototypes cannot bypass promotion gates.

These costs are intentional safeguards.

## 13. Review checklist

- [ ] Current and target state are not conflated.
- [ ] No new top-level cognitive authority is introduced.
- [ ] The existing ESM remains authoritative.
- [ ] The existing ComputeController remains processing-mode owner.
- [ ] The existing conversation store is adapted rather than duplicated.
- [ ] Canonical serialization rules are tested before a ledger is added.
- [ ] All runtime additions are shadow/feature-flagged.
- [ ] Research items have no production authority.
- [ ] Human operator approval is required for promotion and merge.
