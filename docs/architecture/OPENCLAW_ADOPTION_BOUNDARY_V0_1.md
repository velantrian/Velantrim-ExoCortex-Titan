# OpenClaw -> Titan Adoption Boundary v0.1

Status: BOUNDED ARCHITECTURAL DECISION
Date: 2026-08-24
Owner: Titan execution/orchestration plane

## 1. Purpose

OpenClaw is treated as an external operational reference, not as an epistemic or cognitive authority.

Titan may borrow implementation patterns that improve product operation, execution safety, sessions, tools, routing, diagnostics, and user-facing connectivity. This does not transfer authority over evidence, truth, identity, continuity semantics, or cross-domain composition into Titan.

## 2. Portfolio authority boundaries

- Crystal owns trusted evidence, provenance, admission, audit, and bounded Canon writes.
- Titan owns execution, orchestration, providers, tools, retrieval product surfaces, and operational gateway mechanisms.
- Native Kernel owns substrate-neutral semantic laws, invariants, and falsification work.
- Mentaury Soul owns cognition, self/identity semantics, beliefs, relationships, values, commitments, and delegated-human meaning.
- Continuum owns process-continuity semantics and experiments.
- Mentaury Kernel owns cross-domain composition/conformance contracts, not runtime authority.

Therefore:

`more operational capability in Titan != more epistemic authority`

`tool visibility != permission to change Canon`

`successful transport != semantic approval`

`retrieval != evidence != truth`

`session continuity != identity continuity`

## 3. OpenClaw patterns accepted for Titan

The following patterns are appropriate donors for Titan, provided they remain bounded by Titan's existing authorization model:

1. Manifest-first capability discovery.
2. Typed capability contracts owned by core rather than provider-specific implementations.
3. Explicit enablement and validation before runtime loading.
4. Session-key serialization for colliding work.
5. Idempotency keys for side-effecting operations.
6. Separation of tool policy from execution location/sandboxing.
7. Provider/model runtime snapshots published atomically rather than partially mutated.
8. Capability diagnostics (`doctor`) and explanation surfaces (`capability explain`).
9. Background task records separated from scheduling policy.
10. Hooks as lifecycle signals, distinct from authority-bearing semantic decisions.

These patterns are implementation candidates, not proof that the corresponding OpenClaw implementation should be copied.

## 4. Patterns explicitly rejected as direct imports

Do not directly import the following behaviors into Titan:

- in-process third-party plugins with core-equivalent trust;
- non-replayed transient events as evidence/continuity records;
- prompt compaction summaries as trusted memory;
- persona/config files as identity state;
- persistent instructions as autonomous authority;
- cron/scheduling as permission to act;
- one gateway process as central truth, identity, or Canon authority;
- uncontrolled third-party skills/plugins that bypass admission and policy.

## 5. Bounded v0.1 implementation target

The first implementation slice is deliberately smaller than an OpenClaw-style product shell.

### Required

- `CapabilityManifest` or equivalent manifest projection over existing Titan tool/capability metadata.
- manifest-first discovery without executing provider/plugin code.
- typed local gateway contract using existing Titan transport surfaces where possible.
- per-session serialization for side-effecting/competing runs.
- idempotency for side-effecting gateway operations.
- closed-world capability allow/deny behavior where an allowlist is active; deny wins.
- explicit execution/sandbox boundary metadata.
- operator diagnostics equivalent to `titan doctor`.
- operator explanation equivalent to `titan capability explain <name>`.

### Deferred

Do not include in v0.1:

- Telegram/WhatsApp/Slack channel adapters;
- public plugin marketplace;
- multi-agent delegation runtime;
- cron-driven autonomous action;
- a new memory subsystem;
- GraphRAG replacement;
- changes to Crystal admission/Canon authority;
- Soul identity semantics;
- Continuum experiment authorization.

## 6. Reuse-first requirement

Titan already contains a capability-aware `ToolRegistry`, MCP transport/gateway surfaces, provider infrastructure, and extensive policy/provenance code. The v0.1 work MUST extend or wrap those mechanisms rather than create a parallel tool registry or second gateway architecture.

Specifically, `core/tool_registry.py` remains the starting execution registry unless a concrete invariant proves it insufficient. Any new manifest object should be a safe immutable projection/contract over registered capabilities, not a second mutable source of truth.

## 7. Required safety properties

A conforming implementation must demonstrate:

- unknown capabilities fail closed;
- denied capabilities are absent from callable exposure and rejected at dispatch;
- client-supplied identity/capability cannot override server-verified principal context;
- side-effecting operations are idempotent under duplicate request delivery;
- session serialization prevents stale/superseded runs from committing competing writes;
- failed runtime/provider snapshot preparation cannot partially replace a live known-good snapshot;
- diagnostics are observational and cannot silently modify authority state;
- manifest discovery does not execute untrusted plugin/provider initialization code.

## 8. Cross-project adoption map

### Crystal
Only bounded source-adapter/manifest-first ideas are applicable. No channels, cron, multi-agent runtime, or native in-process plugin trust should be imported.

### Native Kernel
OpenClaw patterns may be used as research specimens for substrate-replacement and conformance experiments. They are not invariants until falsified/tested through Native Kernel's own process.

### Mentaury Soul
The useful semantic donor is delegation: Principal, Delegate, OnBehalfOf, explicit permission/commitment, and non-impersonation. OpenClaw persona files are NOT Soul identity state.

### Continuum
Session/transcript pruning, compaction, memory-flush, and task-ledger patterns are experimental candidates to compare against simpler continuity hypotheses. They are not adopted as Continuum truth or authorization.

### Mentaury Kernel
Capability manifests and ownership may inform a substrate-neutral cross-domain CapabilityPort contract with explicit source/target domain, semantic version, authority owner, provenance, transformations, declared loss, target admission, and compatibility.

## 9. Architectural correction to historical Titan documents

Older Titan documents that say `Graph = Truth` or exclude OpenClaw categorically are historical design artifacts, not the current federated authority model.

Current interpretation:

- graph/retrieval structures can organize and retrieve claims/evidence;
- a graph is not truth by existence or rank;
- OpenClaw is not part of Velantrim and contributes no authority, but selected operational patterns may be studied or adopted behind Velantrim boundaries.

## 10. Exit criteria

v0.1 is complete only when focused tests prove the safety properties above and the implementation remains reuse-first, bounded, and authority-neutral.

Passing CI demonstrates implementation consistency. It does NOT authorize production deployment, autonomous action, identity changes, Canon writes, or changes to another project's authority.
