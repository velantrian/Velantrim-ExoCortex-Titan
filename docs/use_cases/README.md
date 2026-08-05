# 🧭 Titan Use Cases

This directory contains detailed application scenarios that would overload the root
`README.md` if described there in full.

Each document must separate:

- current tested foundation;
- feature-gated or partial implementation;
- research / proposed capability;
- runtime-observed evidence;
- known limitations and non-goals.

Use-case documents are product and architecture orientation. They are not runtime proof.
For current implementation truth, follow the mandatory route in
[`docs/ai/README.md`](../ai/README.md), inspect the exact code/PR SHA, and verify tests,
CI, wiring, enablement, and runtime evidence.

## Available use cases

| Document | Purpose | Status |
|---|---|---|
| [🧠 Project Cognition & Code Review](PROJECT_COGNITION_AND_CODE_REVIEW.md) | Long-lived repository context, dependency-aware review and evidence-backed context for Codex, Copilot and human reviewers | 🔬 Research / proposed |

## Navigation

- [🏠 Root README](../../README.md)
- [🗺️ Living System Atlas](../../SYSTEM_OVERVIEW.md)
- [🤖 AI Agent Context Pack](../ai/README.md)
- [🔄 Documentation Sync Protocol](../ai/DOCUMENTATION_SYNC_PROTOCOL.md)
- [📊 Project Status](../PROJECT_STATUS.md)
- [🔍 Reviewer Guide](../REVIEWER_README.md)
- [🤖 Agent Rules](../../AGENTS.md)

## Documentation rule

```text
README introduces the capability.
Use-case documents explain it in depth.
PROJECT_STATUS and docs/ai state current reality.
Code, tests, CI and runtime evidence prove implementation.
Notion preserves deeper rationale and history when required.
```

Material changes to a use case must follow the repository documentation synchronization
protocol. An actor without Notion access completes the GitHub record and creates a
structured `HANDOFF_REQUIRED` item rather than leaving the result only in chat.
