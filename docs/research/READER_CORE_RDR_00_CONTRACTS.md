# PR-RDR-00 — Reader Core Contracts and Fixtures

**Status:** `IMPLEMENTED_IN_BRANCH / SHADOW_FOUNDATION / NO_RUNTIME_WIRING`  
**Parent architecture:** `READER_CORE_LONG_DOCUMENT_ARCHITECTURE.md`

## Purpose

This slice converts the Reader Core research plan into a minimal executable contract surface. It deliberately does not implement parsing, orchestration, persistence, synthesis, memory admission, query-path integration, or Native Kernel integration.

## Added executable contracts

- `DocumentSection`
- `DocumentStructureMap`
- `CoverageValue`
- `SectionRelationCandidate`
- `ReadingSessionCheckpoint`
- enums for content kind, coverage axis, relation kind, and session state
- deterministic canonical SHA-256 identity helper

All dataclasses are frozen and slot-based. They are proposal or checkpoint structures only.

## Identity contract

Reader Core identities use canonical UTF-8 JSON with sorted keys and compact separators, hashed with SHA-256.

```text
stable_reader_core_id(kind, payload)
= SHA256(canonical_json({kind, payload}))
```

Callers must normalize semantic text before building identity payloads. `DocumentSection.create()` applies NFC and whitespace normalization to headings. Python Unicode code-point offsets remain the source coordinate system, matching `SourceSpan`.

## Structure invariants

A valid `DocumentStructureMap` requires:

- one non-empty immutable source revision;
- lowercase SHA-256 source content hash;
- at least one section;
- unique section identifiers;
- sections ordered by `order_index`;
- every section bound to the same `document_id` and `source_revision`;
- exact non-empty ranges satisfying `0 <= start_offset < end_offset`.

The contract does not yet infer hierarchy or validate parent cycles. That belongs to PR-RDR-01.

## Coverage contract

Coverage is represented by observable counts per independent axis.

```text
ratio = processed_units / known_units
```

When `known_units == 0`, `ratio` is `None`, not zero and not a guessed percentage. This prevents unknown denominators from masquerading as measured coverage.

PR-RDR-00 does not define claim-discovery denominators or calibration formulas. Those remain explicit PR-RDR-04 work.

## Session checkpoint contract

`ReadingSessionCheckpoint` freezes the initial state vocabulary:

- `created`
- `structuring`
- `reading`
- `paused`
- `degraded`
- `completed`
- `failed`
- `stale`
- `cancelled`

Completed and pending section sets must be disjoint. This is a checkpoint data invariant, not yet a complete transition state machine. Lease ownership, retries, idempotency, crash recovery, and transition authorization remain PR-RDR-07 work.

## Authority boundary

These contracts contain no field or method that can:

- write Canon;
- admit memory;
- bypass TruthGate;
- call Write Gate;
- execute tools;
- change policy;
- make a graph authoritative;
- require a model or network provider.

Importing this module has no side effects and it is not wired into `/query`.

## Executable fixture

`tests/fixtures/reader_core/rdr_00_minimal_document.json` provides a minimal two-section document with a limiting condition and explicit zero-authority counters.

The fixture is intentionally small. Later corpus slices will add hidden exceptions, contradictions, footnotes, tables, prompt injection, supersession, revisions, and unsupported assets.

## Tests

`tests/test_reader_core_contracts.py` verifies:

- deterministic identities;
- immutability;
- document/revision consistency;
- section ordering;
- unknown-denominator coverage behavior;
- impossible coverage rejection;
- disjoint checkpoint progress sets;
- absence of authority-bearing fields.

## Deferred decisions

PR-RDR-00 intentionally does not freeze:

- full JSON serialization APIs;
- migrations beyond schema version `reader-core.contracts.v1`;
- hierarchy cycle validation;
- parser algorithms;
- section identity under large structural edits;
- exact coverage calibration formulas;
- session transition authorization and leases;
- relation deduplication and temporal supersession;
- synthesis claim schema;
- promotion thresholds.

Each deferred item is assigned to the later ordered Reader Core slice rather than being silently treated as complete.
