# 🧾 AI Engineering Work Log

Current architecture-significant hand-off. Re-verify exact SHAs and current PR evidence.

---

## 2026-08-05 — Continuity R4 compatible compute assessment

**Scope:** draft PR #204; base `a19d16656676ad5c98c92d4776e9709edbfb920c`; initial code head `2af8eadc04ee7a1f22528ca4815e02ecc2639610`; historical source/rejected shape #144.

### Verified before change

- R1–R3 are merged on current main and remain unwired;
- `ComputePath` has five values;
- `ComputeDecision` has a seven-field constructor and seven-key serialization;
- `decide_compute_path()` has no continuity argument;
- `core.rapid_orientation._cost_for_path()` exhaustively maps every accepted path;
- direct recovery of old #144 would add an unhandled DEFER path and break public compatibility.

### Changed

- preserved legacy compute code and public contract;
- added typed `ContinuityComputeSignals`;
- added immutable shadow-only `ContinuityComputeAssessment`;
- added `assess_compute_with_continuity()` as a separate explicit API;
- allowed only VERIFY escalation and degraded DEEP-to-NORMAL capping;
- rejected `shadow_only=False`;
- expanded the Continuity workflow to cover `core/compute_controller.py`;
- added signature, constructor, serialization, legacy matrix, signal, determinism, immutability and RapidOrientation exhaustiveness tests;
- added the compatibility ADR and R4 hand-off/state/component/risk documentation.

### Authority decisions

- no new ComputePath value;
- no modification of the legacy function signature;
- no runtime caller, startup hook, worker, query integration or feature activation;
- no retrieval, persistence, Canon/ESM/TruthGate mutation;
- no answer, advice, tool or action authority.

### Validation

The initial focused Continuity gate passed. Final-head Continuity, full CI and Docker runs remain the merge authority after documentation synchronization.

### Remaining after R4

R5: rebuild replay evaluation, Advisory shadow and disabled complete runner from historical #145–#147 against current R1–R4 APIs.

---

## 2026-08-05 — Continuity R3 projection recovery

**Scope:** PR #203; merged as `a19d16656676ad5c98c92d4776e9709edbfb920c`; historical #138–#143 closed as superseded.

Added deterministic continuity context, current-state reconciliation, attested goals, typed open loops and policy-neutral adapters into the existing WorkingMemoryGate/ContextPack path. Final-head Continuity, full CI and Docker gates passed. No runtime, Canon, compute, advisory, answer or action authority.

## 2026-08-05 — Continuity R2 shadow/read-side recovery

**Scope:** PR #202; merged as `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e`; historical #133/#135/#136 closed as superseded.

Added process-local neutral ledger, read-only conversation bridge, source-fidelity correction and conservative deterministic thread projection.

## 2026-08-05 — Continuity R1 immutable foundation

**Scope:** PR #201; merged as `06529700d70854504b88629eeecf737bdc6b81d5`.

Immutable deterministic events, assertions and relations, golden vectors and authority tests. Old #131/#132 closed as superseded.

## 2026-08-05 — ARM-03 selective-memory recovery

**Scope:** PR #200; merged as `bea535d8fd5f7d59d3f1cee02d060bd026ac05cb`.

Hardened proposal-only extraction with privacy-safe serialization, injection rejection, focused CI, benchmark, replay and ADR. Old #102 closed as superseded.

## 2026-08-05 — Documentation continuity

- PR #199 merged connectorless GitHub → Notion hand-off contract;
- PR #196 merged Project Cognition use-case as `RESEARCH / PROPOSED`;
- PR #198 merged the compact AI context pack.
