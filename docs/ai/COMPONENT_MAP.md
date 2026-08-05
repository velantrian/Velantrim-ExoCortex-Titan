# 🗺️ Component and Authority Map

Use this map to select the smallest relevant inspection surface. It is intentionally
compact. Verify every path at the exact commit under review.

## Authority boundaries

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

Core rules:

- retrieval, ranking, continuity, advisory, projection, and answer layers must not
  silently acquire Canon authority;
- model inference is not user attestation;
- an index or projection never overrides Canon state, visibility, deletion, or scope;
- enabled code is not proven runtime behavior;
- one architectural decision must not gain two independent owners.

## Canon and promotion

| Item | Value |
|---|---|
| Purpose | durable facts, epistemic transitions, validated promotion |
| Decision owner | canonical write protocol / promotion boundary |
| First files | `core/memory.py`, `core/promotion_gateway.py`, `core/truth_gate.py`, `core/write_gate.py`, `core/policy_kernel.py` |
| First tests | promotion, ESM, transition, concurrency, truth-gate and invariant suites |
| Operations docs | `docs/operations/promotion-ownership-inventory.md` |
| Main risk | not every mutation family is proven to use one typed owner |

Audit questions:

1. What exact function commits the durable mutation?
2. Does the same transaction include required version/audit/outbox records?
3. Is the TruthGate snapshot the same snapshot protected by CAS?
4. Can any caller bypass the gateway or invent its own policy?
5. What happens on concurrent weakening, deletion, timeout, or partial failure?

## Projection delivery

| Item | Value |
|---|---|
| Purpose | asynchronously maintain rebuildable FTS and future derived views |
| Decision owner | projection policy + dispatcher lease/checkpoint protocol |
| First files | `core/projection_dispatcher.py`, projection helpers in `core/memory.py`, migrations 020–022 |
| First tests | `tests/test_bounded_local_projection_dispatcher.py` and projection policy/outbox tests |
| ADRs | `docs/adr/ADR-2026-08-03-projection-outbox-foundation.md`, `docs/adr/ADR-2026-08-04-bounded-local-projection-dispatcher.md` |
| Main risk | dispatcher is not runtime-wired and backlog observability is absent |

Do not reuse Canon `WriteGate` as the sole projection decision. A projection apply gate
must validate lease ownership, projection policy, scope, migration state, monotonic
version, resource bounds, and local-only behavior without re-litigating an already
committed Canon promotion.

## Retrieval and evidence

| Item | Value |
|---|---|
| Purpose | candidate discovery, ranking, evidence packaging and traceability |
| First files | `core/hybrid_retriever.py`, `core/ngram_index.py`, FTS helpers, FactsPack/TRACE modules |
| First tests | retrieval, evidence, provenance, visibility and restricted-data tests |
| Main risk | derived views can become stale or drift from canonical restrictions |

Verify current-state filtering after retrieval. Never infer safety from the presence of
a relevant candidate alone.

## Compute and orientation

| Item | Value |
|---|---|
| Purpose | select bounded compute profiles without becoming a central executive |
| Decision owner | `ComputeController` |
| First files | `core/compute_controller.py`, `core/rapid_orientation.py`, `core/goal_frame.py` |
| First tests | compute-controller and rapid-orientation suites |
| Main risk | enum/contract changes can break downstream exhaustive mappings |

When a new `ComputePath` is added, search all enum consumers, maps, serializers,
branches, UI schemas, and tests. Require an exhaustive set-equality test for static maps.

## Continuity — open stack, not main

| Item | Value |
|---|---|
| Purpose | represent conversation events, threads, current state, goals and open loops over time |
| Authority | advisory/shadow only; no Canon, answer, tool, or action authority |
| First PRs | #131–#147 in dependency order |
| First files | `core/continuity/`, then the changed live consumer files |
| Main risks | stacked-review debt, failing #146, compute contract compatibility, missing live producer |

Review in checkpoints rather than only at the top:

- #131–#136: contracts, neutral ledger and ThreadWeaver;
- #138–#143: reconciliation, context and goal/open-loop projections;
- #144: live `ComputeController` contract;
- #145–#147: replay gates, advisory shadow and aggregate runner.

## Identity and personalization

| Item | Value |
|---|---|
| Current file | `core/identity_layer.py` |
| Current status | legacy/unwired prototype |
| Missing owner | Identity Assertion/Admission/Reconciliation protocol |
| Required concepts | source modality, consent, scope, sensitivity, contestation, supersession, retraction, erasure |
| Main risk | activating a direct mutable store as a parallel identity authority |

Keep two governance levels separate:

```text
RFC-0084
→ governs how the identity mechanism or classifier may safely evolve

Identity protocol
→ governs individual user-stated, confirmed, observed or inferred assertions
```

## API, auth and lifecycle

| Item | Value |
|---|---|
| Purpose | request boundary, auth, lifecycle, health, routes, provider composition |
| First files | `server.py`, `api/`, `core/remote_egress.py`, feature configuration |
| First tests | API auth, CORS, egress, lifecycle, server integration and console security |
| Main risks | composition monolith, shared API key, partial static-analysis coverage |

Search module-level initialization, singleton stores, environment parsing, startup and
shutdown paths before changing a route.

## Deployment and supply chain

| Item | Value |
|---|---|
| First files | `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml`, `pyproject.toml`, lock and requirements files, workflows |
| Main risks | conflicting production profiles, broad ranges, non-authoritative lock, wheel/runtime mismatch |

A container build passing is evidence for that image build. It is not proof that both
compose profiles express one production contract or that the dependency graph is
reproducible.

## Documentation and historical context

| Source | Use |
|---|---|
| `SYSTEM_OVERVIEW.md` | architectural orientation |
| `docs/PROJECT_STATUS.md` | public maturity statement; verify freshness |
| `docs/REVIEWER_README.md` | established reviewer path |
| `docs/ai/` | compact current AI context and hand-off |
| ADRs | accepted durable decisions |
| `COLLAB_JOURNAL.md` | historical collaboration narrative |
| old audit files | leads and regressions, not current truth |
| `docs/archive/` | history only |
