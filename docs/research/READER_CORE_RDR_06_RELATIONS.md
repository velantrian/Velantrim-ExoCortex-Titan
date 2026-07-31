# PR-RDR-06 — Cross-section relation candidates

## Boundary

`SHADOW_FOUNDATION / DETERMINISTIC_ONLY / REBUILDABLE_PROJECTION / NO_GRAPH_AUTHORITY / NO_RUNTIME_WIRING`

This layer records directed relation candidates between exact `SectionCardClaim` endpoints. It does not promote relations to truth, write Canon or memory, execute tools, call models, or make graph traversal authoritative.

## Core semantics

- relation candidate != fact;
- relation set != source of truth;
- graph projection != authority;
- source -> target is distinct from target -> source;
- self-loops are forbidden;
- duplicate directed relations are forbidden;
- every endpoint is bound to document, revision, structure map, reading plan, card, section, unit, claim, and source spans;
- every relation and relation set has a deterministic self-verifying ID.

## Denominator

The relation denominator is the number of **explicitly evaluated directed claim pairs**. It is not the number of all mathematically possible claim pairs and not the number of detected candidates.

This prevents an invented relation coverage score. Unknown or unevaluated pairs remain outside the denominator until a detector or evaluator explicitly records them as evaluated.

## Builder

`DeterministicSectionRelationBuilder` accepts:

1. immutable `SectionCard` values from one exact reading identity;
2. explicit evaluated `(source_claim_id, target_claim_id)` pairs;
3. explicit `RelationProposal` values whose pair is already in the evaluated set.

The builder validates claim membership, pair direction, uniqueness, canonical ordering, and relation identity. It performs no semantic similarity search and no model inference.

## Deferred

- automatic lexical/embedding/LLM relation detection;
- relation validation workflows;
- supersession temporal policy;
- cycles and higher-order graph reasoning;
- integration into `CoverageMap` persistence/runtime;
- promotion thresholds.
