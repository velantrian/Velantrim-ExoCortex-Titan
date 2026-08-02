"""Fail-closed gate for mutable user and projection state outside Canon.

Canonical fact mutations remain governed by :mod:`core.write_gate`. This module
covers editable goals, notes, operational inbox/source state, and reasoning
traces. It deliberately does not gate safety/compliance ledgers, erasure
receipts, migrations, health evidence, or incident audit records: those may be
required precisely while the runtime is in SAFE_MODE.
"""

from __future__ import annotations

import re

_SAFE_SCOPE = re.compile(r"^[a-z][a-z0-9_.]{0,95}$")


class UserMutationBlockedError(RuntimeError):
    """PolicyKernel denied an auxiliary mutable-user-state operation."""

    def __init__(
        self,
        reason_code: str,
        *,
        scope: str,
        snapshot_id: str | None = None,
    ) -> None:
        self.reason_code = reason_code
        self.scope = scope
        self.snapshot_id = snapshot_id
        label = "SAFE_MODE" if reason_code == "safe_mode_writes_blocked" else "PolicyKernel"
        super().__init__(f"{label}: user mutation blocked ({scope}; {reason_code})")


def ensure_user_mutations_allowed(scope: str) -> None:
    """Raise unless the current verified policy snapshot permits mutation."""

    normalized = str(scope).strip()
    if _SAFE_SCOPE.fullmatch(normalized) is None:
        raise ValueError("scope must be a safe lower-case dotted identifier")

    from core.policy_kernel import get_policy_kernel

    snapshot = get_policy_kernel().capture_snapshot()
    if not snapshot.writes_allowed:
        raise UserMutationBlockedError(
            snapshot.reason_code,
            scope=normalized,
            snapshot_id=snapshot.snapshot_id,
        )


__all__ = ["UserMutationBlockedError", "ensure_user_mutations_allowed"]
