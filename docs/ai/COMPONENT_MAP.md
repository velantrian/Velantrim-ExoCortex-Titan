# 🗺️ Component and Authority Map

Use this map to select the smallest relevant inspection surface. Verify every path at the
exact commit or PR head under review.

## Authority model

```text
User / operator intent
        ↓
API / tool boundary
        ↓
Policy, capability and egress checks
        ↓
Read path ──────────────── Write proposal
   ↓                              ↓
Retrieval / evidence       Truth and mutation admission
   ↓                              ↓
FactsPack / TRACE           Canon transaction + receipts
   ↓                              ↓
Answer composition          Projection outbox
                                  ↓
                           Rebuildable projections
```

Rules:

- retrieval, selective-memory extraction, continuity, advisory, projection and answer
  layers do not acquire Canon authority;
- model inference or rule extraction is not user attestation;
- indexes/projections do not override canonical visibility, restriction or deletion;
- one decision type has one owner;
- implemented is different from wired, enabled and observed.

## Canon and promotion

| Item | Value |
|---|---|
| Purpose | durable facts, epistemic transitions and validated promotion |
| Owner | canonical write protocol / promotion boundary |
| First files | `core/memory.py`, `core/promotion_gateway.py`, `core/truth_gate.py`, `core/write_gate.py`, `core/policy_kernel.py` |
| First tests | promotion, ESM, transition, concurrency, TruthGate and invariant suites |
| Main risk | not every mutation family is proven to use one typed owner |

Audit transaction, CAS snapshot, version/audit/outbox coupling, direct writers and
concurrent weakening/deletion behavior.

## Projection delivery

| Item | Value |
|---|---|
| Purpose | maintain rebuildable FTS and future derived views |
| Owner | projection policy plus dispatcher lease/checkpoint protocol |
| First files | `core/projection_dispatcher.py`, projection helpers in `core/memory.py`, migrations 020–022 |
| First tests | `tests/test_bounded_local_projection_dispatcher.py` and outbox/apply-policy suites |
| Main risk | dispatcher is not runtime-wired and backlog observability is absent |

Projection application validates its own lease, scope, version, migration and resource
policy; it does not re-run Canon admission as a second epistemic owner.

## Retrieval and evidence

| Item | Value |
|---|---|
| Purpose | candidate discovery, ranking, evidence packaging and traceability |
| First files | `core/hybrid_retriever.py`, `core/ngram_index.py`, FTS helpers, FactsPack/TRACE modules |
| First tests | retrieval, evidence, provenance, visibility and restricted-data suites |
| Main risk | stale derived views or post-retrieval filtering drift |

## Selective memory — ARM-03

| Item | Value |
|---|---|
| Purpose | propose bounded source-linked memory candidates for shadow/offline evaluation |
| Authority | proposal only; no persistence, Canon, TruthGate, WriteGate, response or action authority |
| Feature flag | `ENABLE_SELECTIVE_MEMORY_CANDIDATE_SHADOW`, default off |
| First files | `core/selective_memory_candidates.py`, `core/feature_config.py`, `core/runtime_flags.py` |
| First tests | `tests/test_selective_memory_candidates.py`, `tests/test_selective_memory_speed_contract.py` |
| Evidence | `.github/workflows/arm03-contracts.yml`, benchmark and evaluation replay fixture |
| Contract | `docs/SELECTIVE_MEMORY_SPEED_AND_SAFETY.md` |
| Main risks | heuristic classification, bounded injection detection, caller-supplied identity, protected raw evidence handling |

Audit questions:

1. Does flag-off return before extraction?
2. Are candidate IDs deterministic and bound to source, subject and context?
3. Are offsets and span hashes exact?
4. Can raw contact/credential content enter portable output or repr?
5. Is instruction-shaped memory injection rejected by default?
6. Are budgets strict under large input?
7. Are write/model/network capabilities structurally absent?
8. Is ARM-04 admission still absent?

## Compute and orientation

| Item | Value |
|---|---|
| Purpose | select bounded compute profiles without becoming a central executive |
| Owner | `ComputeController` |
| First files | `core/compute_controller.py`, `core/rapid_orientation.py`, `core/goal_frame.py` |
| First tests | compute-controller and rapid-orientation suites |
| Main risk | enum/contract changes can break exhaustive downstream mappings |

New enum members require a search of every map, serializer, branch and schema plus
exhaustive set-equality tests where practical.

## Continuity — recovery required

| Item | Value |
|---|---|
| Purpose | represent events, threads, current state, goals and open loops over time |
| Authority | shadow/advisory only; no Canon, answer, tool or action authority |
| Historical PRs | #131–#147 |
| Recovery route | rebuild logical layers from current `main`; do not merge the stale chain directly |
| Main risks | stacked-review debt, `DEFER_PATH` consumers, legacy compatibility, missing trusted producer |

## Identity and personalization

| Item | Value |
|---|---|
| Current file | `core/identity_layer.py` |
| Status | `LEGACY/UNWIRED` |
| Missing owner | Identity Assertion/Admission/Reconciliation protocol |
| Required concepts | source modality, consent, scope, sensitivity, contestation, supersession, retraction, erasure |

RFC-0084 may govern mechanism evolution; it does not define admission for individual
identity assertions.

## API, auth and lifecycle

| Item | Value |
|---|---|
| Purpose | request boundary, auth, lifecycle, health and provider composition |
| First files | `server.py`, `api/`, `core/remote_egress.py`, feature configuration |
| First tests | API auth, CORS, egress, lifecycle, integration and console-security suites |
| Main risks | composition monolith, shared API key, partial static-analysis scope |

## Deployment and supply chain

| Item | Value |
|---|---|
| First files | `Dockerfile`, compose files, `pyproject.toml`, locks/requirements and workflows |
| Main risks | conflicting production profiles, broad dependency ranges, non-authoritative lock, wheel/container mismatch |

## Documentation and history

| Source | Use |
|---|---|
| `SYSTEM_OVERVIEW.md` | architectural orientation |
| `docs/PROJECT_STATUS.md` | public maturity statement; verify freshness |
| `docs/REVIEWER_README.md` | reviewer route |
| `docs/ai/` | compact current context, risks and hand-off |
| ADR/RFC | accepted or proposed durable decisions, with status checked |
| `COLLAB_JOURNAL.md` | historical narrative |
| old audits / `docs/archive/` | leads and history, not current truth |
