"""
Mandatory remote-egress boundary for Titan.

Every server-side LLM/STT/TTS call must obtain a PolicyKernel capability lease
before opening a remote connection. The default policy is fail-closed.

This module also applies a compatibility epistemic guard to legacy console
prompts. Older code labelled every memory row as "verified" even when a
console fallback had supplied Observed records. Until the structured
EvidenceBundle migration is complete, the guard removes that false elevation
and adds an explicit instruction not to increase the certainty of memory
entries.
"""
from __future__ import annotations

from dataclasses import dataclass


_REMOTE_BOUNDARY_MARKER = "[VELANTRIM REMOTE EPISTEMIC BOUNDARY]"

_PROMPT_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        "Ты — Velantrim ExoCortex, AI-агент с верифицированной памятью.",
        "Ты — Velantrim ExoCortex, AI-агент с памятью, где записи могут "
        "иметь разный уровень подтверждения.",
    ),
    (
        "Отвечай ТОЛЬКО на основе следующих фактов из памяти.",
        "Используй следующие записи памяти только как контекст и не "
        "повышай их уровень достоверности.",
    ),
    (
        "Верифицированные факты:",
        "Записи памяти (часть может быть неподтверждённой):",
    ),
    (
        "verified memory",
        "memory with mixed verification states",
    ),
    (
        "Verified facts:",
        "Memory entries (some may be unverified):",
    ),
)

_REMOTE_PREFIX = (
    f"{_REMOTE_BOUNDARY_MARKER}\n"
    "Memory entries are context, not automatically verified evidence. "
    "Do not present an entry as verified unless its text explicitly marks it "
    "Validated or ImmutableCore. Observed, Hypothesized, reported-only, and "
    "fallback memory must be qualified as unverified.\n\n"
)


class RemoteEgressDeniedError(RuntimeError):
    """PolicyKernel denied a remote network/data capability."""

    def __init__(
        self,
        reason_code: str,
        *,
        capability: str,
        provider: str,
        snapshot_id: str,
        policy_version: str,
    ) -> None:
        self.reason_code = reason_code
        self.capability = capability
        self.provider = provider
        self.snapshot_id = snapshot_id
        self.policy_version = policy_version
        super().__init__(
            "Remote egress denied "
            f"({reason_code}; capability={capability}; provider={provider}; "
            f"snapshot={snapshot_id})"
        )


@dataclass(frozen=True)
class RemoteEgressReceipt:
    capability: str
    provider: str
    data_mode: str
    snapshot_id: str
    policy_version: str


def ensure_remote_egress_allowed(
    capability: str,
    *,
    provider: str,
    data_mode: str = "raw",
) -> RemoteEgressReceipt:
    """Acquire and enforce a least-authority remote capability lease."""

    from core.policy_kernel import get_policy_kernel

    normalized_provider = (provider or "unknown").strip().lower() or "unknown"
    lease = get_policy_kernel().lease_capability(
        capability,
        locality="remote",
        requires_network=True,
        data_mode=data_mode,
    )
    if not lease.allowed:
        raise RemoteEgressDeniedError(
            lease.reason_code,
            capability=capability,
            provider=normalized_provider,
            snapshot_id=lease.snapshot_id,
            policy_version=lease.policy_version,
        )
    return RemoteEgressReceipt(
        capability=capability,
        provider=normalized_provider,
        data_mode=lease.data_mode,
        snapshot_id=lease.snapshot_id,
        policy_version=lease.policy_version,
    )


def sanitize_remote_system_prompt(system: str) -> str:
    """Remove legacy false verification labels and add a remote epistemic guard."""

    value = str(system or "").strip()
    if value.startswith(_REMOTE_BOUNDARY_MARKER):
        return value

    for old, new in _PROMPT_REPLACEMENTS:
        value = value.replace(old, new)

    return _REMOTE_PREFIX + value if value else _REMOTE_PREFIX.rstrip()


__all__ = [
    "RemoteEgressDeniedError",
    "RemoteEgressReceipt",
    "ensure_remote_egress_allowed",
    "sanitize_remote_system_prompt",
]
