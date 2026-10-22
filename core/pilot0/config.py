"""Strict, secret-free configuration surface for the experimental Pilot-0 path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from core.deepseek_config import validate_deepseek_thinking_mode

Pilot0ThinkingMode = Literal["off", "high", "max"]


@dataclass(frozen=True, slots=True)
class Pilot0ReaderConfig:
    """Allowlisted Reader settings; this config contains no credential field."""

    provider: Literal["deepseek"] = "deepseek"
    model_selection: Literal["OWNER_SELECTED"] = "OWNER_SELECTED"
    deepseek_thinking: Pilot0ThinkingMode = "off"

    def __post_init__(self) -> None:
        if self.provider != "deepseek":
            raise ValueError("Pilot-0 provider is fixed to deepseek")
        if self.model_selection != "OWNER_SELECTED":
            raise ValueError("Pilot-0 model selection must remain OWNER_SELECTED")
        validate_deepseek_thinking_mode(self.deepseek_thinking)

    def to_safe_dict(self) -> dict[str, str]:
        """Return only the explicit non-secret allowlist for reproducibility."""

        return {
            "provider": self.provider,
            "model_selection": self.model_selection,
            "deepseek_thinking": self.deepseek_thinking,
        }


__all__ = ["Pilot0ReaderConfig", "Pilot0ThinkingMode"]
