# 🗺️ Component and Authority Map

Use the smallest relevant inspection surface and verify it at the exact commit or PR
head.

## Authority rules

- retrieval, selective-memory extraction, continuity, advisory and projections do not
  acquire Canon authority;
- origin or model inference is not truth, user attestation or action permission;
- indexes and projections do not override canonical visibility/restriction/deletion;
- one decision type has one owner;
- implemented, tested, wired, enabled and observed are separate states.

## Canon and promotion

| Item | Value |
|---|---|
| Owner | canonical write / promotion boundary |
| First files | `core/memory.py`, `core/promotion_gateway.py`, `core/truth_gate.py`, `core/write_gate.py`, `core/policy_kernel.py` |
| First tests | promotion, ESM, transition, concurrency and TruthGate suites |
| Risk | not every mutation family is proven to use one typed owner |

## Projection delivery

| Item | Value |
|---|---|
| Owner | projection policy + dispatcher lease/checkpoint protocol |
| First files | `core/projection_dispatcher.py`, projection helpers, migrations 020–022 |
| Tests | outbox/apply-policy and bounded dispatcher suites |
| Risk | no accepted runtime lifecycle or backlog observability |

## Retrieval and evidence

| Item | Value |
|---|---|
| Purpose | candidate discovery, ranking, evidence packaging and TRACE |
| First files | hybrid/NGram/FTS retrieval, FactsPack and TRACE modules |
| Risk | stale derived views or post-retrieval policy drift |

## Selective memory — ARM-03

| Item | Value |
|---|---|
| Status | `MAIN + TESTED + DEFAULT OFF / NOT WIRED` |
| Authority | proposal only |
| First files | `core/selective_memory_candidates.py`, feature config/runtime flags |
| Tests | selective-memory contracts and speed tests |
| Evidence | ARM-03 workflow, benchmark, replay and ADR |
| Risk | heuristic classification, bounded injection detection, protected evidence handling |

## Continuity R1 — immutable contracts

| Item | Value |
|---|---|
| Review | PR #201 |
| Purpose | deterministic neutral events, typed assertions and explicit assertion relations |
| Authority | contract construction/validation only |
| First files | `core/continuity/contracts.py`, `core/continuity/__init__.py` |
| Tests | `tests/test_continuity_contracts.py`, golden fixtures, R1 regressions |
| Workflow | `.github/workflows/continuity-contracts.yml` |
| ADR | `docs/adr/ADR-2026-08-05-continuity-r1-foundation.md` |
| Main risks | schema compatibility, future privacy/retention policy, missing trusted producers and persistence |

Audit R1 by checking:

1. frozen/slots contracts and absent write/action methods;
2. NFC text and UTC timestamp canonicalization;
3. sorted duplicate-free refs;
4. JSON-scalar/finite-float validation;
5. canonical bytes and SHA-256 golden vectors;
6. separation of origin from truth/projection status;
7. absence of DB, Canon, ESM, gates, runtime and feature activation.

## Continuity later layers

| Layer | Intended content | Status |
|---|---|---|
| R2 | shadow ledger, conversation bridge, deterministic threads | not implemented on current `main` |
| R3 | state, goals/open loops, WorkingMemory adapters | not implemented |
| R4 | compute signals, replay and Advisory shadow | not implemented |
| R5 | disabled complete shadow runner | not implemented |

Historical PRs #131–#147 are source material, not an accepted merge path.

## Compute and orientation

| Item | Value |
|---|---|
| Owner | `ComputeController` |
| First files | `core/compute_controller.py`, `core/rapid_orientation.py`, `core/goal_frame.py` |
| Risk | enum additions can break exhaustive consumers |

## Identity and personalization

`core/identity_layer.py` is `LEGACY/UNWIRED`. A separate assertion/admission/
reconciliation protocol must define source modality, consent, scope, sensitivity,
contestation, supersession, retraction and erasure.

## API, auth and lifecycle

Start with `server.py`, `api/`, remote-egress and feature configuration. Main risks are
composition breadth, shared-key authorization and partial verification scope.

## Deployment and supply chain

Start with Dockerfile, compose profiles, `pyproject.toml`, lock/requirements files and
workflows. Main risks are profile ambiguity, broad ranges, reproducibility and
wheel/container parity.

## Documentation and history

`docs/ai/` is current orientation; ADR/RFC status must be checked; `COLLAB_JOURNAL.md`,
old audits and archives are historical leads, not current truth.
