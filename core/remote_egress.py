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


#: Capabilities permitted to declare ``data_mode="none"``.
#:
#: ``none`` skips the remote-data policy dimension entirely (PolicyKernel checks
#: it only when ``data_mode != "none"``), so with ``network=allow`` such a call
#: proceeds even under ``remote_data=never``. That is sound ONLY where the
#: request provably carries no user content, so the set is closed and asserted
#: rather than left to each caller's judgement:
#:
#: * ``remote_model_discovery`` — metadata only: lists provider model ids.
#:   No prompt, no memory, no user text of any kind.
#: * ``remote_llm_test`` — connectivity probe. Sends one fixed,
#:   repository-owned synthetic prompt defined in ``llm_router.test_connection``.
#:   The public probe routes (``api/llm_routes.py``) forbid extra fields, so a
#:   caller cannot attach a prompt, memory, attachment or audio.
#:
#: User prompts, retrieved memory, audio and any other private payload are
#: forbidden under ``none`` and must declare ``raw`` (or ``redacted``). STT and
#: TTS therefore use ``raw``, audio being private payload.
_METADATA_ONLY_CAPABILITIES = frozenset(
    {
        "remote_model_discovery",
        "remote_llm_test",
    }
)


def ensure_remote_egress_allowed(
    capability: str,
    *,
    provider: str,
    data_mode: str = "raw",
) -> RemoteEgressReceipt:
    """Acquire and enforce a least-authority remote capability lease.

    Raises ``ValueError`` if a capability outside
    ``_METADATA_ONLY_CAPABILITIES`` declares ``data_mode="none"``. Without this,
    any new call site could opt out of the remote-data dimension by declaring
    ``none`` — and since ``data_mode`` is caller-declared and unverifiable, that
    opt-out would be invisible in review.
    """

    from core.policy_kernel import get_policy_kernel

    if data_mode == "none" and capability not in _METADATA_ONLY_CAPABILITIES:
        raise ValueError(
            f"capability {capability!r} may not declare data_mode='none': "
            "only metadata-only capabilities "
            f"({', '.join(sorted(_METADATA_ONLY_CAPABILITIES))}) may skip the "
            "remote-data policy check"
        )

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
