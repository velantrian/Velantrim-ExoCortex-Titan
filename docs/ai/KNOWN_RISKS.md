# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-05  
**Current `main`:** `a19d16656676ad5c98c92d4776e9709edbfb920c`

Code presence does not close a risk. Closure requires focused/full validation, wiring and operational evidence.

## P0

- Projection dispatcher is implemented/tested but not runtime-wired or observed.
- Production compose contracts remain materially inconsistent.
- Static-analysis and coverage scope do not uniformly cover all runtime surfaces.
- Store-wide WAL/contention/crash/restart/disk-full testing is incomplete.
- Dependency/build reproducibility and wheel/container parity remain incomplete.

## P1 — Continuity

### R1–R3 are merged but not a live continuity system

R1 contracts, R2 process-local read-side and R3 projections/adapters are in `main` and tested. They remain unwired and non-user-facing.

Residual risks:

- no trusted producers for events, assertions, attestations or open-loop signals;
- no durable adapter, consent, tenant isolation, retention, erasure or access-control contract;
- no accepted single owner for caller-supplied attention, recall, eligibility, privacy, protection and conflict policy facts;
- deterministic projections can still be wrong when their source records are wrong;
- contested state must not become answer/action authority;
- the R3 Synaptic ownership ADR remains proposed.

### R4 compatible compute assessment

Draft PR #204 deliberately preserves the legacy `ComputeController` public contract and exposes a separate shadow-only assessment.

Residual risks:

- continuity compute signals are caller-supplied typed values with no trusted producer in R4;
- assessment can recommend VERIFY or cap degraded DEEP, but no runtime owner consumes it;
- `context_rebuild_required` is evidence, not permission to retrieve or mutate;
- critical low-evidence inputs verify because no accepted DEFER semantics exist;
- adding a future `DEFER_PATH` would require exhaustive updates to `RapidOrientation` and every other consumer;
- direct `ComputeDecision` reasons remain a mutable list for compatibility, despite the frozen dataclass;
- the assessment is not calibrated against production outcomes;
- no latency, false-positive escalation or depth-cap quality evidence exists;
- no user-visible fallback or operator-review workflow is defined.

Required before runtime use:

1. trusted signal producer and policy owner;
2. replay corpus and false-escalation metrics;
3. explicit runtime caller and feature flag;
4. proof that legacy answers remain authoritative during shadow evaluation;
5. consent/privacy review for personal continuity signals;
6. monitoring, rollback and operator approval;
7. separate ADR for any new compute path.

### R5 remains unimplemented

Historical #145–#147 contain replay evaluation, Advisory shadow and a complete disabled runner, but they are stale stacked source material. They must be rebuilt independently on the current R1–R4 APIs.

## Other P1

- ARM-03 remains heuristic proposal-only; candidate precision/privacy evidence is needed before ARM-04.
- Identity remains a legacy mutable prototype without accepted consent/scope, contestation, audit/version and erasure lifecycle.
- Canon mutation ownership is not proven unified across every family.
- `server.py` remains a composition monolith.
- Shared API key is not per-user/tenant authorization.
- Wheel and container require separate supported-artifact contracts.

## P2

- large generated knowledge assets need a reproducible distribution strategy;
- historical audits need verified-SHA/superseded indexing;
- repository governance settings and discovery metadata need continued hardening.

## Update rule

Use exact states: proposed, implemented, tested, wired, enabled and observed.
