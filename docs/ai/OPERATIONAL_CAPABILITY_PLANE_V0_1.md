# 🗿 Titan Operational Capability Plane v0.1

## Status

`BOUNDED IMPLEMENTATION · DRAFT PR · READ/DIAGNOSTIC SURFACE ONLY`

This slice implements the first operational pattern adopted after the OpenClaw comparison without importing OpenClaw, creating a second tool registry, or expanding Titan authority.

## Reuse-first architecture

```text
existing ToolRegistry
        │
        ▼
CapabilityManifest snapshot
        │
        ├── deterministic SHA-256
        ├── immutable metadata copy
        ├── capability access explanation
        └── bounded registry doctor
```

The implementation lives in `core/capability_plane.py` and wraps the existing `core.tool_registry.ToolRegistry`.

It does **not** execute tools, add a plugin loader, schedule work, open network channels, create agents, mutate Canon, or grant permissions.

## User/operator surface

The module exposes a stdlib-only local CLI:

```bash
python -m core.capability_plane manifest --capability reader
python -m core.capability_plane explain search_facts --capability reader
python -m core.capability_plane doctor --capability reader
```

### Manifest

A manifest is a deterministic metadata snapshot of the tools already visible to an effective capability. It contains no callables and does not retain mutable references to `ToolDef.params`.

`manifest sha256 != authority receipt`.

The SHA-256 only identifies the exact metadata snapshot; it does not prove identity, truth, approval, admission, or permission.

### Explain

`explain` returns a structured reason code for one existing tool:

- `visible`
- `insufficient_capability`
- `unknown_tool`
- `destructive_requires_admin`
- `registry_invariant_violation`

The caller must provide an already-effective capability when used behind a transport boundary. The function does not replace `resolve_authorized_capability()` and cannot raise the deployment ceiling.

### Doctor

`doctor` checks the internal consistency of the existing registry indexes, destructive-tool visibility, capability escalation, deterministic snapshot construction, and canonical JSON serializability.

It is read-only. A failed doctor returns a non-zero CLI exit status.

## Deliberately excluded from v0.1

- no new Gateway implementation;
- no Telegram/WhatsApp/Slack adapters;
- no cron/scheduler;
- no background task runtime;
- no plugin marketplace;
- no multi-agent routing;
- no sandbox implementation;
- no new authenticated identity system;
- no side-effect idempotency layer yet;
- no session serialization changes yet;
- no changes to TruthGate, Guardian, Canon, Reader authority, Soul identity semantics, or Continuum continuity semantics.

Those are separate bounded increments only after this foundation is reviewed.

## Authority boundary

```text
capability metadata != permission grant
manifest visibility != execution authorization
execution ability != epistemic authority
retrieval != evidence != truth
Titan operational plane != Soul identity authority
Titan session state != Continuum continuity Canon
```

Crystal remains the trusted evidence/admission/Canon owner in the ecosystem model. Soul owns cognition/self/identity semantics. Continuum owns process-continuity semantics/research. Native Kernel owns substrate-neutral invariant/falsification work. Mentaury-Kernel owns cross-domain composition/conformance.

## Acceptance criteria

1. Existing ToolRegistry is reused; no parallel registry exists.
2. Snapshots are deterministic and immutable with respect to later mutation of registry parameter dicts.
3. Non-canonical/non-JSON manifest material fails closed.
4. Explain never executes a tool.
5. Doctor detects stale visibility indexes and destructive visibility below admin.
6. Existing MCP/tool behavior is unchanged.
7. Full Titan CI remains green on the exact PR head.
