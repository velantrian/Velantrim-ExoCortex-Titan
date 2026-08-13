# Phase 2A — Capability Registry AI Handoff

**Parent:** #53  
**Tracking:** #299  
**Implementation PR:** #300 · MERGED  
**Implementation main:** `c1fa13cf8fe6bf82d99dfb507beeac2c1c8f7aca` · signature `VERIFIED / valid`  
**Exact tested PR head:** `f0b893bac1b6fe1f58a71c70ac631f3c14becb59`  
**Runtime:** UNWIRED / NOT ENABLED  
**Authority expansion:** NONE

## Authority chain

```text
ProviderDescriptor + CapabilityDescriptor + ProviderHealth
                       |
                       v
               CapabilityRegistry()
                       |
                       v
              get_policy_kernel()
                       |
             allow / deny + reason
                       |
                       v
                SelectionResult
```

`CapabilityRegistry()` has no policy/leaser constructor argument. Production code cannot
substitute a second permission owner through the registry API. `auto` and explicit
preference are ordering hints, never permission.

## Merged bounded scope

`core/capability_registry.py` owns only stable provider/capability descriptors,
capability-specific declared `data_mode`, explicit provider health, deterministic candidate
evaluation, separate health/policy reason codes, bounded selection/no-selection, and
trace-ready metadata.

It does **not** probe or invoke providers, perform network I/O, persist TRACE, mutate Canon
or ESM, replace QueryRouter, or wire itself into runtime.

## Final evidence

```text
pre-merge Full CI:       #1105 · 31735939941 · SUCCESS
pre-merge Docker:        #723 · 31735939929 · SUCCESS
READY aggregate:         #981 · 31736858130 · SUCCESS
protected squash merge:  c1fa13cf8fe6bf82d99dfb507beeac2c1c8f7aca
post-merge Full CI:      #1106 · 31736925690 · SUCCESS
post-merge Docker:       #724 · 31736925695 · SUCCESS
post-merge aggregate:    #982 · 31736925705 · SUCCESS
```

Codex on an ancestor head returned `NOT RUN — USAGE LIMIT`; this is neither approval nor a
finding. No independent formal approval is claimed.

## Safety invariants

- existing `PolicyKernel` remains the permission owner;
- remote provider metadata cannot hide required network access;
- capability `data_mode` is policy input, not consent;
- missing/unavailable health fails closed;
- explicit preference cannot override a denied lease;
- policy evaluation failure fails closed;
- mixed policy snapshots cannot be composed into a successful selection;
- no runtime/Canon authority follows from a descriptor or selection result.

## Still unauthorized

```text
runtime registry wiring           NOT_DONE
provider probing/invocation       OUT_OF_SCOPE
embeddings/vector execution       OUT_OF_SCOPE
reranker/LLM execution            OUT_OF_SCOPE
ADAO execution                    OUT_OF_SCOPE
ARM-04                            NOT_AUTHORIZED
remote consent implementation     OUT_OF_SCOPE
network activation                false
runtime route replacement         false
runtime enablement                false
Operator GO                       false
runtime authority                 false
production authority              false
schema v8                         NOT_CREATED
Continuity 13/12                  NOT_CREATED
```

Before any later wiring or activation, re-audit live `main` and require a separate bounded
admission decision.
