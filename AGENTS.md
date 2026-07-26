# Velantrim Titan repository guidance

## Verification

- For Python changes, run `ruff check core/ --output-format=github`.
- Run `mypy core/ --show-error-codes`.
- Run `python -m pytest tests/ -v --tb=short --timeout=300 -x`.
- Treat branding, repository-hygiene, CI, and Docker workflow failures as blocking.

## Code Review Rules

### Canonical memory boundary

- Flag any query, retrieval, ranking, answering, or background read path that mutates Canon, epistemic state, relations, activation history, or projection state. The safe path is to return evidence or an `AnalysisProposal` and require an explicit canonical write service for mutation.

### Policy and evidence integrity

- Flag fail-open behavior when policy, TruthGate, provenance, visibility, or evidence dependencies are unavailable. External or model-derived `WORLD_FACT` records require attributable provenance and evidence, remain unvalidated until an explicit transition, and must never be promoted by ordinary recall.

### Atomic writes and rebuildable projections

- For the currently implemented canonical write protocol, flag changes that can commit the Canon mutation without its required `VersionStore` pre-image and `AuditChain` event, or that can leave partial batch state. Require an outbox record in the same transaction only for code paths that already implement outbox-backed projection delivery; do not assume a repository-wide outbox exists until that subsystem lands. FTS, graph, and vector stores are rebuildable projections only; they must not override canonical restriction, deletion, archive, or visibility state.
