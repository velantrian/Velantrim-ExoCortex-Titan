# P0 Hardening Completion Record — 2026-08-02

**Verified main:** `d7cea6ff3cf788fc1b8ff32fce3713ecf458ed96`  
**Authority:** GitHub commits, pull requests and attached CI/Docker runs.  
**Scope:** Reality Lock, immediate safety, bounded GDPR startup recovery, TruthPolicy fail-closed runtime, and SAFE_MODE mutable-state boundary.

## Completed runtime chain

```text
Reality Lock contracts
→ architecture-freeze CI
→ real-byte RAR extraction
→ SQLite/AuditChain concurrency fixes
→ typed bounded erasure receipts
→ bounded single-fact recovery
→ bounded batch recovery
→ aggregate startup runner
→ awaited recovery after migrations
→ content-free /health/recovery readiness
→ TruthPolicy fail-closed /query boundary
→ SAFE_MODE auxiliary mutation freeze
```

## Merge register

| Area | PR | Merge commit | Runtime state |
|---|---:|---|---|
| RAR real-byte extraction | #71 | `769f1941` | merged and enforced |
| AuditChain deterministic CAS test | #152 | `feff50c` | merged test gate |
| SQLite shared-connection cleanup race | #153 | `0d07bc9` | merged runtime fix |
| Reality Lock / activation / observer / freeze CI | #148 | `ef6384a` | merged governance contracts |
| Startup recovery receipt contracts | #155 | `6e96be8` | merged contracts |
| Bounded single-fact recovery | #156 | `663ab71` | merged execution adapter |
| Bounded batch recovery | #157 | `98a23fe` | merged execution adapter |
| Aggregate startup recovery runner | #158 | `db8df2f` | merged runner |
| Startup process health state | #159 | `5e00338` | merged health projection |
| Awaited startup wiring + `/health/recovery` | #160 | `94e3717` | runtime wired |
| TruthPolicy runtime adapter | #161 | `a18a0bc` | merged adapter |
| TruthPolicy `/query` fail-closed integration | #163 | `5a2aad1` | user request path active |
| SAFE_MODE auxiliary mutation gates | #162 | `d7cea6f` | runtime enforced |

## Proven safety behavior

### Reality Lock

- `NOT_OBSERVED` and `OBSERVER_FAILED` cannot pass hard gates.
- Runtime observation cannot be claimed before `STARTED`.
- New authority markers require an ADR through architecture-freeze CI.

### GDPR recovery

- Recovery executes once after migrations through one awaited `asyncio.to_thread` call.
- Single and batch work share count and monotonic-time bounds.
- No scheduler, polling loop, detached task or bypass flag was added.
- `clean` returns readiness HTTP 200.
- `not_observed`, backlog/degraded and observer failure return HTTP 503.
- Receipts expose counts and safe reason codes, not claims, fact IDs, user IDs, SQL, paths or exception text.

### TruthPolicy

- Disabled, measured `allow`, `gap_notice` and measured `reject` retain existing semantics.
- Feature-resolution or policy-evaluation failure produces a content-free `REJECT / policy_unavailable` block.
- Unverified LLM generation is blocked when the enabled truth boundary cannot produce a valid verdict.

### SAFE_MODE

- Canon writes remain governed by `core.write_gate`.
- Goal, note, source, inbox, promotion and reasoning-trace mutations now consult the verified policy snapshot.
- Inbox promotion is blocked before raw L0 append or Canon proposal.
- Policy dependency failure is fail-closed.
- Erasure, migrations, health and append-only safety/audit ledgers remain available for incident response.

## Validation discipline

Every merged runtime increment used:

- an isolated branch and draft PR;
- focused regression tests;
- self-removing patch machinery where exact changes to mature files were required;
- final maintainer-authored head;
- architecture-freeze CI;
- Ruff;
- blocking mypy;
- full repository pytest;
- Docker build/runtime hardening checks;
- manual diff review and pinned-head merge.

Codex review was unavailable because its quota was exhausted; this was not represented as approval.

## What this record does not claim

This wave does **not** make Titan a certified or generally production-ready multi-user system. Still open:

- independent security assessment and penetration testing;
- certified GDPR/compliance program and legal sign-off;
- store-wide WAL/concurrency/crash benchmarks;
- unified PromotionGateway and transactional outbox;
- persisted long-term decision/observation receipts;
- SubjectScope/privacy foundation and Continuity shadow evaluation;
- utility evidence from owner dogfooding and controlled pilots.

Research modules remain proposals/shadow-only unless separately promoted through Reality Lock gates.
