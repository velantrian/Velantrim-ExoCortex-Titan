"""Shared base class for Semantic Reader implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from core.semantic_reader import (
    RawSource,
    ReaderBudget,
    ReaderMode,
    ReaderResult,
    ReaderStatus,
)


class BaseSemanticReader(ABC):
    """Small convenience base; implementations remain provider replaceable."""

    reader_id: ClassVar[str]
    reader_version: ClassVar[str]
    supported_modes: ClassVar[frozenset[ReaderMode]]

    def supports_mode(self, mode: ReaderMode) -> bool:
        return mode in self.supported_modes

    def unsupported_mode_result(self, mode: ReaderMode) -> ReaderResult:
        return ReaderResult.failed(
            ReaderStatus.REJECTED,
            code="UNSUPPORTED_MODE",
            safe_message=f"Reader does not support mode '{mode.value}'",
        )

    @abstractmethod
    async def extract(
        self,
        source: RawSource,
        *,
        mode: ReaderMode = ReaderMode.FAST,
        budget: ReaderBudget | None = None,
    ) -> ReaderResult:
        """Extract a source-linked capsule without mutating runtime state."""


__all__ = ["BaseSemanticReader"]
