# 🌿 External Architecture Patterns — Titan Research Track

**Status:** `RESEARCH / PRIOR ART`  
**Runtime authority:** none  
**Canon write authority:** none  
**Default enabled:** false  
**Date:** 2026-07-30  
**Scope:** provider-neutral research patterns that may be adapted into Titan-native contracts after independent validation

## Decision

Titan may study external open-source systems for reusable engineering patterns, but external project names, module names and data models must not become Titan architecture by default.

```text
external implementation
→ extract neutral engineering primitive
→ map to existing Titan ownership
→ check licence and security constraints
→ write Titan-native RFC
→ shadow prototype
→ deterministic evaluation
→ explicit Operator GO
→ bounded implementation PR
```

External projects remain **prior art**, not architectural authorities. A useful idea does not gain runtime, policy, truth, memory or task authority merely because it exists in another repository.

## Non-negotiable boundaries

- Canon, ESM, TruthGate, PolicyKernel, Recall Policy, Write Gate, AuditChain and ErasureCoordinator retain their existing ownership.
- Query and retrieval paths remain read-only with respect to Canon and epistemic state.
- External model output is a proposal and cannot write directly to durable memory.
- Graph, vector, FTS, caches and generated files are rebuildable projections unless a separate canonical contract says otherwise.
- No external provider, model, graph database or SaaS dependency becomes mandatory for the local-first path.
- Prior-art terminology must not leak into public Titan module, PR, roadmap or decision names.
- Code reuse requires an explicit licence review and preservation of all attribution and notice obligations.
- Architecture imitation is not a substitute for measurement on Titan workloads.

## Research portfolio

### P0 — Replay, Fork and Structural Diff

**Research source class:** event-sourced reactive graph runtimes, including ActiveGraph.

**Titan-native primitive:** `EvaluationReplay` + `ExperimentFork` + `StructuralDiff`.

**Research question:** can Titan replay a recorded, fully bounded evaluation run, fork it at a declared boundary and compare two configurations without mutating production state?

Candidate contract:

```text
EvaluationRun
├── run_id
├── protocol_version
├── corpus_snapshot_id
├── configuration_snapshot_id
├── policy_snapshot_id
├── ordered_input_events[]
├── tool/model fixtures[]
├── output_receipts[]
└── result_digest

ExperimentFork
├── parent_run_id
├── fork_event_id
├── changed_configuration
├── inherited_fixture_refs[]
└── fork_reason

StructuralDiff
├── baseline_run_id
├── candidate_run_id
├── claim_diff
├── evidence_diff
├── memory_diff
├── route_diff
├── answer_diff
├── policy_diff
└── cost_diff
```

Initial boundary:

- offline or CI-only;
- no production event-log claim;
- no replay of irreversible external effects;
- provider calls replaced by versioned fixtures or separately authorised recordings;
- deterministic input order and canonical JSON digests;
- failure is recorded as data rather than silently removed.

**Promotion gate:** implement only after the evaluation protocol in [`EVALUATION_REPLAY_PROTOCOL.md`](EVALUATION_REPLAY_PROTOCOL.md) is approved.

### P1 — Temporal Evidence and Claim Validity

**Research source class:** temporal knowledge-graph and agent-memory systems, including Graphiti-style temporal modelling.

**Titan-native primitive:** strengthen existing bi-temporal fact semantics with explicit evidence episodes and temporal conflict evaluation.

Candidate distinction:

```text
valid time  = when the claim applies in the described world
known time  = when Titan learned, observed or revised the claim
```

Candidate objects:

```text
EvidenceEpisode
├── episode_id
├── source_ref
├── observed_at
├── ingested_at
├── temporal_scope
├── exact_spans[]
└── content_digest

TemporalClaimView
├── claim_ref
├── valid_from / valid_to
├── known_from / known_to
├── supporting_episode_refs[]
├── supersession_refs[]
└── temporal_conflicts[]
```

Rules:

- absence of dates must remain unknown, not be replaced with ingestion time;
- a newer observation does not automatically make an older claim false;
- supersession must preserve lineage;
- temporal reasoning remains evidence-linked;
- the existing canonical fact contract remains authoritative until a separate migration is approved.

### P2 — Unified Decision and Run Receipts

**Research source class:** policy decision logs and data-lineage systems, including OPA and OpenLineage patterns.

**Titan-native primitive:** a shared receipt envelope, not a new policy or audit owner.

Candidate envelope:

```text
DecisionReceiptEnvelope
├── schema_version
├── operation_id
├── run_id
├── decision_kind
├── authoritative_owner
├── input_refs[]
├── evidence_refs[]
├── policy_snapshot_id
├── capability_lease_refs[]
├── decision
├── reason_codes[]
├── limitations[]
├── result_refs[]
├── parent_receipt_refs[]
├── generated_at
└── digest
```

This envelope may normalize observability across retrieval routing, failure disposition, memory admission, RCO proposals and evaluation runs. It must not replace the domain-specific contract or collapse evidence, confidence and permission into one scalar.

### P3 — Capability-based Extension Registry

**Research source class:** plugin registries and domain packs, including Exocortex-style registries and ActiveGraph packs.

**Titan-native primitive:** `ExtensionManifest` validated against capability and ownership boundaries.

Candidate manifest:

```text
ExtensionManifest
├── extension_id
├── version
├── extension_kind
├── declared_inputs[]
├── declared_outputs[]
├── requested_capabilities[]
├── locality
├── persistence_surfaces[]
├── policy_dependencies[]
├── erasure_adapters[]
├── deterministic_mode
├── failure_mode
└── licence_metadata
```

Rules:

- registration does not grant a capability;
- every optional action still requires a current PolicySnapshot and lease;
- durable storage requires ownership, retention and erasure contracts;
- extensions cannot register a second TruthGate, PolicyKernel, Canon or AuditChain;
- unknown capability requests fail closed;
- disabling an extension must preserve Canon integrity and the baseline path.

### P4 — Evaluated Procedural Skills

**Research source class:** file-based and agentic memory frameworks, including memU-style readable memory categories.

**Titan-native primitive:** human-readable procedural artifacts that remain proposals until evaluated.

Candidate lifecycle:

```text
source-linked experience
→ ProceduralSkillCandidate
→ offline evaluation cases
→ operator review
→ versioned skill artifact
→ read-only retrieval
→ optional bounded execution through existing policy/tool boundaries
```

Candidate fields:

```text
ProceduralSkill
├── skill_id
├── version
├── purpose
├── preconditions[]
├── steps[]
├── stop_conditions[]
├── failure_modes[]
├── evidence_refs[]
├── evaluation_set_id
├── measured_success_rate
├── applicable_scope
├── prohibited_effects[]
└── supersedes_ref
```

Markdown may be a readable projection, but it is not automatically Canon. A generated skill cannot become executable merely because an LLM wrote a plausible procedure.

## Existing Titan work that remains separate

The following already have their own contracts and should not be renamed or duplicated:

- adaptive retrieval and selective-memory work in [`../docs/research/ADAPTIVE_RETRIEVAL_MEMORY_ARCHITECTURE.md`](../docs/research/ADAPTIVE_RETRIEVAL_MEMORY_ARCHITECTURE.md);
- Rapid Calibrated Orientation in [`RAPID_CALIBRATED_ORIENTATION.md`](RAPID_CALIBRATED_ORIENTATION.md);
- D16 proposal vocabulary in [`D16_EXECUTIVE_CONTROL_CONTRACT.md`](D16_EXECUTIVE_CONTROL_CONTRACT.md);
- failure, lifecycle and reliability boundaries in [`FAILURE_LIFECYCLE_RELIABILITY_CONTRACT.md`](FAILURE_LIFECYCLE_RELIABILITY_CONTRACT.md);
- Working Desk in [`WORKING_DESK_RESEARCH_MODE.md`](WORKING_DESK_RESEARCH_MODE.md).

This document coordinates research questions only. It does not create a new umbrella runtime or rename existing owners.

## Explicitly rejected transfers

Do not import:

- direct LLM-to-memory or LLM-to-Canon writes;
- opaque autonomous self-modification;
- graph or vector storage as the source of truth;
- replay systems that re-execute unbounded external side effects;
- plugin registration as implicit permission;
- provider-first kernels;
- age-only deletion of memory;
- one universal confidence score;
- generated wiki or Markdown as canonical truth;
- external project names as Titan module names.

## Licence and attribution gate

For each implementation candidate, record:

```text
source_repository
source_revision
source_licence
copied_code = yes | no
modified_code = yes | no
required_notices[]
patent_terms
network/SaaS restrictions
incompatible_dependencies[]
reviewer
review_date
```

Architectural ideas may be independently reimplemented, but copied code must be tracked precisely. Unclear or restrictive terms block code reuse until reviewed.

## Promotion stages

| Stage | Meaning | Permitted artifact |
|---|---|---|
| `R0 — Notion / research note` | unverified idea | notes and source links |
| `R1 — GitHub research contract` | neutral primitive and boundaries defined | documentation only |
| `R2 — Offline prototype` | implementation exists outside authoritative runtime | fixtures, tests, benchmark harness |
| `R3 — Shadow candidate` | runs beside baseline without authority | receipts and metrics |
| `R4 — Implementation candidate` | thresholds passed | bounded RFC and draft PR |
| `R5 — Active gated slice` | explicit Operator GO | feature-flagged runtime change |

Advancement requires evidence from the previous stage. A persuasive architecture description is not evidence of runtime benefit.

## Ordered next work

1. approve the deterministic evaluation protocol;
2. implement replayable fixtures before implementing a general runtime event system;
3. evaluate temporal correctness on fixed contradictory and superseding claims;
4. compare receipt envelopes against existing domain-specific receipts;
5. prototype extension manifests without loading third-party code;
6. evaluate procedural skills as read-only artifacts;
7. stop or redesign any item that does not beat a simpler Titan-native baseline.

## Core rule

```text
Borrow patterns, not authority.
Translate names, do not transplant brands.
Measure on Titan, do not inherit another project's claims.
Promote through receipts, tests and Operator GO.
```
