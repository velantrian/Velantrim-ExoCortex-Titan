"""Provider-neutral contracts for source-to-capsule extraction.

Semantic Readers are pure extraction components.  They receive immutable source
text and return source-linked ``KnowledgeCapsule`` proposals.  They do not write
memory, promote ESM state, call TruthGate, or grant Canon authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from core.knowledge_capsule import KnowledgeCapsule


class ReaderContractError(ValueError):
    """Raised when a reader request/result violates the public contract."""


class ReaderMode(str, Enum):
    """Requested extraction depth, independent of any concrete provider."""

    FAST = "fast"
    STANDARD = "standard"
    DEEP = "deep"


class ReaderStatus(str, Enum):
    """Structured outcome of one extraction request."""

    SUCCESS = "success"
    PARTIAL = "partial"
    REJECTED = "rejected"
    PROVIDER_ERROR = "provider_error"
    INVALID_OUTPUT = "invalid_output"
    SPAN_VALIDATION_FAILED = "span_validation_failed"
    BUDGET_EXCEEDED = "budget_exceeded"


@dataclass(frozen=True, slots=True)
class RawSource:
    """One immutable source revision supplied to a Semantic Reader."""

    document_id: str
    text: str
    source_revision: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.document_id, str) or not self.document_id.strip():
            raise ReaderContractError("document_id must be a non-empty string")
        if not isinstance(self.text, str):
            raise ReaderContractError("text must be a string")
        if self.source_revision is not None and (
            not isinstance(self.source_revision, str) or not self.source_revision.strip()
        ):
            raise ReaderContractError("source_revision must be a non-empty string or None")


@dataclass(frozen=True, slots=True)
class ReaderBudget:
    """Hard limits enforced before or during extraction."""

    max_source_chars: int = 100_000
    max_claims: int = 64
    max_essence_chars: int = 1_000

    def __post_init__(self) -> None:
        for field_name in ("max_source_chars", "max_claims", "max_essence_chars"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ReaderContractError(f"{field_name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class ReaderFailure:
    """Safe, structured failure details suitable for receipts and APIs."""

    code: str
    safe_message: str
    retryable: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code.strip():
            raise ReaderContractError("failure code must be a non-empty string")
        if not isinstance(self.safe_message, str) or not self.safe_message.strip():
            raise ReaderContractError("safe_message must be a non-empty string")
        if not isinstance(self.retryable, bool):
            raise ReaderContractError("retryable must be a bool")


@dataclass(frozen=True, slots=True)
class ReaderWarning:
    """Safe, structured non-fatal condition attached to a partial result."""

    code: str
    safe_message: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code.strip():
            raise ReaderContractError("warning code must be a non-empty string")
        if not isinstance(self.safe_message, str) or not self.safe_message.strip():
            raise ReaderContractError(
                "warning safe_message must be a non-empty string"
            )


@dataclass(frozen=True, slots=True)
class ReaderResult:
    """Non-ambiguous extraction result.

    ``SUCCESS`` and ``PARTIAL`` always carry a capsule.  All other statuses
    carry a safe failure and never carry a capsule.  ``PARTIAL`` must explain
    every known truncation or omission through at least one structured warning.
    """

    status: ReaderStatus
    capsule: KnowledgeCapsule | None = None
    failure: ReaderFailure | None = None
    warnings: tuple[ReaderWarning, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, ReaderStatus):
            raise ReaderContractError("status must be a ReaderStatus")
        warnings = tuple(self.warnings)
        if any(not isinstance(item, ReaderWarning) for item in warnings):
            raise ReaderContractError("warnings must contain ReaderWarning values")
        object.__setattr__(self, "warnings", warnings)
        if self.capsule is not None and not isinstance(self.capsule, KnowledgeCapsule):
            raise ReaderContractError("capsule must be a KnowledgeCapsule or None")
        if self.failure is not None and not isinstance(self.failure, ReaderFailure):
            raise ReaderContractError("failure must be a ReaderFailure or None")

        if self.status is ReaderStatus.SUCCESS:
            if self.capsule is None or self.failure is not None or warnings:
                raise ReaderContractError(
                    "SUCCESS requires capsule and forbids failure and warnings"
                )
            return
        if self.status is ReaderStatus.PARTIAL:
            if self.capsule is None or self.failure is not None or not warnings:
                raise ReaderContractError(
                    "PARTIAL requires capsule, at least one warning, and no failure"
                )
            return
        if self.capsule is not None or self.failure is None or warnings:
            raise ReaderContractError(
                "non-success result requires failure and forbids capsule and warnings"
            )

    @property
    def accepted(self) -> bool:
        """Whether the result contains a usable capsule proposal."""

        return self.status in {ReaderStatus.SUCCESS, ReaderStatus.PARTIAL}

    @classmethod
    def success(cls, capsule: KnowledgeCapsule) -> ReaderResult:
        return cls(status=ReaderStatus.SUCCESS, capsule=capsule)

    @classmethod
    def partial(
        cls, capsule: KnowledgeCapsule, *, warnings: tuple[ReaderWarning, ...]
    ) -> ReaderResult:
        return cls(status=ReaderStatus.PARTIAL, capsule=capsule, warnings=warnings)

    @classmethod
    def failed(
        cls,
        status: ReaderStatus,
        *,
        code: str,
        safe_message: str,
        retryable: bool = False,
    ) -> ReaderResult:
        if status in {ReaderStatus.SUCCESS, ReaderStatus.PARTIAL}:
            raise ReaderContractError("failed() requires a non-success status")
        return cls(
            status=status,
            failure=ReaderFailure(
                code=code,
                safe_message=safe_message,
                retryable=retryable,
            ),
        )


@runtime_checkable
class SemanticReader(Protocol):
    """Provider-neutral asynchronous extraction interface."""

    @property
    def reader_id(self) -> str:
        ...

    @property
    def reader_version(self) -> str:
        ...

    async def extract(
        self,
        source: RawSource,
        *,
        mode: ReaderMode,
        budget: ReaderBudget,
    ) -> ReaderResult:
        ...


__all__ = [
    "RawSource",
    "ReaderBudget",
    "ReaderContractError",
    "ReaderFailure",
    "ReaderMode",
    "ReaderResult",
    "ReaderStatus",
    "ReaderWarning",
    "SemanticReader",
]
