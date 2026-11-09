"""Explicit context limits for remote LLM requests: nothing is shortened silently.

Before this module Titan cut every DeepSeek message to 4000 characters in
``core.llm_router`` (``_DEEPSEEK_MESSAGE_CHAR_LIMIT``) for all DeepSeek models.
The cut happened after the prompt was assembled, so the end of the current
question, of the system instructions or of the memory block could disappear
without any signal to the caller or the user.

Policy implemented here:

* The per-message character limit is OFF unless an operator sets
  ``DEEPSEEK_MESSAGE_CHAR_LIMIT`` (a positive integer). There is no replacement
  universal number.
* When the limit is set, Titan never cuts a message. Prompt builders fit whole
  units (memory records, history turns) and record every omission in a
  :class:`ContextReport`; the router refuses an over-limit message with
  :class:`LlmContextLimitError` instead of truncating it.
* The current question and mandatory instructions are never shortened. If they
  cannot fit, the request is refused with a clear message.
* Titan does not count tokens. The model/provider context window is enforced by
  the provider; a provider "context too long" rejection is surfaced as
  :class:`core.llm_router.LlmContextOverflowError` with a clear message.
* History/summary limits of the console are separate settings (see
  ``HISTORY_*`` / ``PREVIOUS_SUMMARY_*`` / ``BLOCK_MEMORY_*`` below). They are
  not model response-length limits (``max_tokens``), which are unchanged.

Diagnostics produced here carry setting names, roles, counts, lengths and
internal record ids only; never message text, record text or API keys.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

# ── settings (environment variables) ─────────────────────────────────────────

#: Optional hard per-message character limit for DeepSeek requests.
#: Unset/empty -> no Titan-side limit (the provider context window still applies).
DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV = "DEEPSEEK_MESSAGE_CHAR_LIMIT"

#: Number of most recent chat-history turns sent as separate messages.
#: Default 20 (the previous fixed value, now reported when applied); 0/off = no cap.
HISTORY_MAX_TURNS_ENV = "LLM_CHAT_HISTORY_MAX_TURNS"
HISTORY_MAX_TURNS_DEFAULT: int | None = 20

#: Optional per-turn character cap for the textual dialogue block built by
#: ``core.console_memory.build_chat_context_for_prompt``. Default: off
#: (previously a silent 600-character cut).
HISTORY_TURN_MAX_CHARS_ENV = "CONSOLE_HISTORY_TURN_MAX_CHARS"

#: Optional character cap for ``previous_chat_summary`` in the system prompt.
#: Default: off (previously a silent 4000-character cut; the request field is
#: itself validated to at most 8000 characters with an explicit 422 error).
PREVIOUS_SUMMARY_MAX_CHARS_ENV = "CONSOLE_PREVIOUS_SUMMARY_MAX_CHARS"

#: Number of console ``block_memory`` notes placed in the system prompt.
#: Default 40 (the previous fixed value, now reported when applied); 0/off = no cap.
BLOCK_MEMORY_MAX_ITEMS_ENV = "CONSOLE_BLOCK_MEMORY_MAX_ITEMS"
BLOCK_MEMORY_MAX_ITEMS_DEFAULT: int | None = 40

#: Stable code also used as a marker by callers that classify ValueErrors.
CONTEXT_LIMIT_CODE = "llm_context_limit"
CONTEXT_OVERFLOW_CODE = "llm_context_overflow"

TOKEN_COUNT_STATUS = "not_computed"
TOKEN_COUNT_NOTE = (
    "Titan does not count tokens; the model context window is enforced by the "
    "provider and an overflow is reported as llm_context_overflow"
)

_OFF_VALUES = frozenset({"", "off", "none", "unlimited", "0"})


class LlmContextConfigError(ValueError):
    """A context-limit setting has an invalid value."""


class LlmContextLimitError(ValueError):
    """Mandatory content does not fit an explicitly configured Titan limit.

    Raised instead of truncating. The message names the setting, the role and
    the sizes; it never contains the content itself.
    """

    code = CONTEXT_LIMIT_CODE

    def __init__(
        self,
        *,
        setting: str,
        limit: int,
        role: str,
        length: int,
        part: str,
    ) -> None:
        self.setting = setting
        self.limit = limit
        self.role = role
        self.length = length
        self.part = part
        super().__init__(
            f"{CONTEXT_LIMIT_CODE}: {part} ({role}) is {length} characters, above "
            f"{setting}={limit}. Titan did not shorten it and did not send the "
            f"request. Shorten the input or raise/unset {setting}."
        )


def _parse_optional_positive_int(name: str, default: int | None) -> int | None:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _OFF_VALUES:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise LlmContextConfigError(
            f"{name} must be a positive integer or empty/off; got a non-integer value"
        ) from exc
    if parsed <= 0:
        raise LlmContextConfigError(f"{name} must be a positive integer or empty/off")
    return parsed


def deepseek_message_char_limit() -> int | None:
    return _parse_optional_positive_int(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, None)


def message_char_limit_setting_for_provider(provider: str | None) -> str | None:
    if (provider or "").strip().lower() == "deepseek":
        return DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV
    return None


def message_char_limit_for_provider(provider: str | None) -> int | None:
    """Configured per-message limit for ``provider``; ``None`` means no Titan limit."""

    if message_char_limit_setting_for_provider(provider) is None:
        return None
    return deepseek_message_char_limit()


def history_max_turns() -> int | None:
    return _parse_optional_positive_int(HISTORY_MAX_TURNS_ENV, HISTORY_MAX_TURNS_DEFAULT)


def history_turn_max_chars() -> int | None:
    return _parse_optional_positive_int(HISTORY_TURN_MAX_CHARS_ENV, None)


def previous_summary_max_chars() -> int | None:
    return _parse_optional_positive_int(PREVIOUS_SUMMARY_MAX_CHARS_ENV, None)


def block_memory_max_items() -> int | None:
    return _parse_optional_positive_int(
        BLOCK_MEMORY_MAX_ITEMS_ENV, BLOCK_MEMORY_MAX_ITEMS_DEFAULT
    )


# ── report ───────────────────────────────────────────────────────────────────


@dataclass
class ContextReport:
    """What one request actually sent, and every limit that removed something.

    ``applied`` is empty when nothing was left out. Each entry names the
    setting, its value, what it affected and how many units were left out.
    Memory records and history turns are only ever left out whole.
    """

    provider: str = ""
    message_char_limit: int | None = None
    message_char_limit_setting: str | None = None
    memory_records_total: int = 0
    memory_records_sent: int = 0
    memory_records_omitted: list[dict[str, Any]] = field(default_factory=list)
    history_turns_total: int = 0
    history_turns_sent: int = 0
    applied: list[dict[str, Any]] = field(default_factory=list)
    sent_fact_positions: list[int] = field(default_factory=list)

    @classmethod
    def for_provider(cls, provider: str | None) -> ContextReport:
        name = (provider or "").strip().lower()
        return cls(
            provider=name,
            message_char_limit=message_char_limit_for_provider(name),
            message_char_limit_setting=message_char_limit_setting_for_provider(name),
        )

    def record_applied(
        self,
        *,
        setting: str,
        value: int,
        affected: str,
        omitted: int = 0,
        shortened: int = 0,
    ) -> None:
        self.applied.append(
            {
                "setting": setting,
                "value": value,
                "affected": affected,
                "omitted": omitted,
                "shortened": shortened,
            }
        )

    @property
    def limits_applied(self) -> bool:
        return bool(self.applied)

    def sent_facts(self, facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """The records that are in the final request, in prompt order.

        Any per-request citation map (for example ``[ev_N]`` labels) must be
        built from this list, never from the retrieved list, so that a label
        cannot point at a record the model did not receive.
        """

        return [facts[index] for index in self.sent_fact_positions if index < len(facts)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "message_char_limit": self.message_char_limit,
            "message_char_limit_setting": self.message_char_limit_setting,
            "token_count": TOKEN_COUNT_STATUS,
            "token_count_note": TOKEN_COUNT_NOTE,
            "memory_records_total": self.memory_records_total,
            "memory_records_sent": self.memory_records_sent,
            "memory_records_omitted": list(self.memory_records_omitted),
            "history_turns_total": self.history_turns_total,
            "history_turns_sent": self.history_turns_sent,
            "limits_applied": self.limits_applied,
            "applied": list(self.applied),
        }


# ── final guard used by the router ───────────────────────────────────────────


def enforce_message_char_limit(
    messages: list[dict[str, str]],
    *,
    provider: str | None,
    limit: int | None = None,
) -> list[dict[str, str]]:
    """Return ``messages`` unchanged (minus empty ones) or refuse; never truncate.

    ``limit`` defaults to the configured limit for ``provider``.
    """

    setting = message_char_limit_setting_for_provider(provider) or "message_char_limit"
    effective = message_char_limit_for_provider(provider) if limit is None else limit
    checked: list[dict[str, str]] = []
    last_user_index = max(
        (i for i, m in enumerate(messages or []) if str(m.get("role") or "user") == "user"),
        default=-1,
    )
    for index, msg in enumerate(messages or []):
        role = str(msg.get("role") or "user")
        content = str(msg.get("content") or "")
        if not content.strip():
            continue
        if effective is not None and len(content) > effective:
            if role == "system":
                part = "system instructions and memory"
            elif index == last_user_index:
                part = "current question"
            else:
                part = "history turn"
            raise LlmContextLimitError(
                setting=setting,
                limit=effective,
                role=role,
                length=len(content),
                part=part,
            )
        checked.append({"role": role, "content": content})
    return checked


_OVERFLOW_MARKERS = (
    "maximum context length",
    "context length",
    "context_length_exceeded",
    "context window",
    "too many tokens",
    "prompt is too long",
    "input is too long",
)


def looks_like_context_overflow(status_code: int, detail: str) -> bool:
    """Heuristic match of provider "context too long" rejections (HTTP 400/413)."""

    if status_code not in (400, 413):
        return False
    text = (detail or "").casefold()
    return any(marker in text for marker in _OVERFLOW_MARKERS)


def context_overflow_message(provider: str, status_code: int) -> str:
    return (
        f"{CONTEXT_OVERFLOW_CODE}: {provider} rejected the request as larger than "
        f"the model context (HTTP {status_code}). Titan did not shorten the "
        "question, instructions, memory or history and does not count tokens; "
        "reduce history, memory or document size, or choose a model with a "
        "larger context."
    )


__all__ = [
    "BLOCK_MEMORY_MAX_ITEMS_ENV",
    "CONTEXT_LIMIT_CODE",
    "CONTEXT_OVERFLOW_CODE",
    "ContextReport",
    "DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV",
    "HISTORY_MAX_TURNS_ENV",
    "HISTORY_TURN_MAX_CHARS_ENV",
    "LlmContextConfigError",
    "LlmContextLimitError",
    "PREVIOUS_SUMMARY_MAX_CHARS_ENV",
    "TOKEN_COUNT_STATUS",
    "block_memory_max_items",
    "context_overflow_message",
    "deepseek_message_char_limit",
    "enforce_message_char_limit",
    "history_max_turns",
    "history_turn_max_chars",
    "looks_like_context_overflow",
    "message_char_limit_for_provider",
    "message_char_limit_setting_for_provider",
    "previous_summary_max_chars",
]
