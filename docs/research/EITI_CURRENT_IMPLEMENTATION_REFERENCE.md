# EITI Current Implementation Reference for Titan Research

Status: **RESEARCH INPUT · DOCS ONLY · NO RUNTIME AUTHORITY**  
Recorded: 2026-08-21  
EITI implementation source: `velantrian/velantrim-eiti@586cff46b47110847913ea3dea1c33a46cb03f13`

## Purpose

EITI is a user-facing Exo-Cortex client/prototype where several cognitive and retrieval mechanisms already have concrete implementation evidence. That evidence is useful to Titan research, but it does **not** make those mechanisms Current in Titan.

```text
implemented in EITI != implemented in Titan
prototype evidence != production authorization
retrieval signal != evidence
association strength != epistemic confidence
proposal != approval != apply
```

## EITI mechanisms with implementation evidence

- **MOSC** — concrete lexical/concept data exists in `data/mosc_default_v1.json`.
- **Ranking / salience** — executable tests exist in `velantrim_core/tests_js/ranking.test.js` and `salience.test.js`.
- **DAAD / decay** — executable decay/accessibility tests exist in `velantrim_core/tests_js/decay.test.js`.
- **Local learning analysis** — `apply_analysis.test.js` covers a real EITI learning/apply path.
- **Cross-provider context continuity** — E2E coverage exists in `velantrim_core/e2e/cross_ai_context.spec.js`.
- **Full-context assembly** — tested in `velantrim_core/tests_js/full_ctx.test.js`.

These are EITI Current/Partial implementation facts only.

## Titan research mapping

### MOSC

Treat MOSC as a candidate inexpensive lexical/intent prior and routing/SearchSignal input. Do not treat it as a Truth Graph, evidence source, canonical relation store, or safety decision by itself.

Promotion questions:
- does it improve routing/retrieval precision or recall versus a simple baseline?
- does it introduce language/domain collisions or sensitive-routing false positives?
- can personal vocabulary adaptation remain scoped and reversible?

### Adaptive retrieval policy (EITI FL)

EITI's mechanism changes retrieval policy fields such as mode, threshold and maximum facts. It is **not federated learning and does not train neural model weights**.

Titan research name: `Adaptive Retrieval Policy Proposal`.

Evaluate against a fixed baseline using recall, precision, contradiction/evidence coverage, Safe Recall Boundary, restricted-data leakage, latency, context/token cost, faithfulness and stability.

### PKG / Hebbian-style signals

Do not create a second independent epistemic graph in Titan. Map usage/co-activation observations into bounded non-epistemic relation-strength or Charge proposals where compatible with existing Titan mechanics.

```text
EpistemicState != confidence != evidence != relation strength != Charge != utility != preference
```

### DAAD / decay

Research decay as retrieval accessibility dynamics only.

**Invariant:** forgetting/decay is a retrieval policy, not epistemic revision.

### RNE / novelty

Novelty/diversity pressure may improve context usefulness and reduce fixation, but only after authority/evidence filtering. Novelty cannot admit restricted or unsupported material.

### Velantrim Brain / intent patterns

Use only as a bounded deterministic helper candidate. Pattern proposals require a safe matcher or strict resource limits, examples, scope, expiry, conflict handling, provenance and shadow precision measurement.

### Local learning

EITI's direct local apply path is implementation evidence for the human capability, but Titan must retain proposal-first governance:

```text
observation
  -> LearningProposal
  -> deterministic validation
  -> ShadowEvaluationReceipt
  -> RFC-0084 evaluation / stability / approval
  -> future versioned apply boundary
  -> receipt + rollback
```

This document does not create runtime wiring and does not supersede `LEARNING_PROPOSAL_RFC0084_RECONCILIATION.md`.

## Promotion rule

A mechanism becomes Current in Titan only when Titan itself has:
1. an owning component and declared scope;
2. implementation on current main;
3. meaningful tests/benchmarks against a baseline;
4. authority/security/conformance negative tests;
5. an explicit promotion decision appropriate to its gate.

EITI remains empirical/prototype evidence, not delegated Titan authority.
