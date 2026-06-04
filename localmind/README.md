# LocalMind

LocalMind is the local language layer for the Velantrim console.

It is intentionally separate from `core/`:

- `core/` keeps memory, epistemic state, TruthGate, and durable facts.
- `localmind/` understands user phrasing and composes local offline replies.

This keeps offline answers useful without changing the memory invariants.

