# Architecture Freeze — Reality Lock

**Status:** proposed governance contract · no runtime authority  
**Effective target:** after merge of the Reality Lock PR  
**Owner of gate decisions:** human maintainer/operator

## Purpose

Titan is temporarily optimizing for completion, evidence and hardening rather than new cognitive surface area. The freeze prevents a new authority, worker, policy owner or provider path from entering `main` without an explicit architecture decision.

The freeze does **not** stop bug fixes, security hardening, tests, observability, documentation synchronization, adapters without authority, or completion of already accepted milestones.

## Changes that require an ADR

A pull request requires a concrete file under `docs/adr/` when it introduces or materially expands any of the following:

- a new `ENABLE_*` runtime flag;
- a Canon or ESM write path;
- a new background worker, scheduler or unbounded task;
- a new compute/policy/gate owner;
- a new remote transport or provider egress path;
- a new autonomous action or external side effect;
- a new direct promotion route to a validated/canonical state.

The ADR must state ownership, data scope, privacy behavior, failure semantics, rollback, observability, test evidence and why an existing owner cannot be reused.

## Allowed without a new ADR

- security and compliance fixes;
- tests and characterization coverage;
- activation and observation receipts;
- deterministic replay and persisted evidence;
- bounded read-only/shadow adapters;
- documentation corrections that reduce claims;
- refactors that preserve public and authority contracts.

## Enforcement

`scripts/check_architecture_freeze.py` scans added runtime lines in pull-request diffs. Selected authority markers fail with `ADR_REQUIRED` unless the same PR includes a concrete decision record under `docs/adr/`.

This guard is intentionally conservative and incomplete. Passing it is not proof of safety. Reviewers must still inspect authority, privacy, erasure, replay and failure-isolation boundaries.

## Gate ownership

CI detects formal markers. AI contributors may implement and review. Only the human maintainer/operator accepts a decision gate or authorizes movement from research/shadow into active runtime.
