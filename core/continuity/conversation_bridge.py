"""Read-only bridge from legacy conversation notebooks into continuity projections.

The bridge consumes the existing ``ConversationConsolidator`` read surface and
produces immutable, deterministic ``ConversationEpisode`` snapshots.  It never
calls notebook mutation methods, never appends to the neutral event ledger, and
never upgrades notebook text into epistemically confirmed facts.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Protocol, Sequence

from core.conversation_consolidation import ConversationNotebook

CONVERSATION_EPISODE_SCHEMA_VERSION = "continuity.conversation_episode.v1"


class ConversationBridgeError(ValueError):
    """Raised when a notebook cannot be projected without ambiguity."""


class ConversationNotebookReader(Protocol):
    """Minimal read-only surface required from a notebook source."""

    def get_notebook(self, chat_id: str) -> ConversationNotebook | None:
        """Return one notebook without mutating source state."""
        ...

    def search(self, query: str, limit: int = 10) -> list[ConversationNotebook]:
        """Return matching notebooks without mutating source state."""
        ...

    def list_recent(self, limit: int = 10) -> list[ConversationNotebook]:
        """Return recent finalized notebooks without mutating source state."""
        ...


def _normalize_text(value: str) -> str:
    if not isinstance(value, str):
        raise ConversationBridgeError("text fields must be strings")
    return " ".join(unicodedata.normalize("NFC", value).split())


def _require_text(value: str, field_name: str) -> str:
    normalized = _normalize_text(value)
    if not normalized:
        raise ConversationBridgeError(f"{field_name} must be non-empty")
    return normalized


def _normalize_items(
    values: Sequence[str],
    *,
    field_name: str,
    sort_items: bool,
) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = _normalize_text(value)
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    if sort_items:
        normalized.sort()
    return tuple(normalized)


def _parse_timestamp(value: str | None, field_name: str) -> datetime | None:
    if value is None:
        return None
    normalized = _require_text(value, field_name)
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ConversationBridgeError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ConversationBridgeError(f"{field_name} must be timezone-aware")
    return parsed.astimezone(UTC)


def _canonical_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ConversationBridgeError("timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _stable_digest(payload: dict[str, object]) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _validate_count(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ConversationBridgeError(f"{field_name} must be an integer >= 0")
    return value


@dataclass(frozen=True, slots=True)
class ConversationEpisode:
    """Immutable Titan projection of one conversation notebook.

    This object is rebuildable context evidence.  It intentionally carries no
    truth status, confirmation status, salience, advice, or action authority.
    """

    episode_id: str
    schema_version: str
    source_ref: str
    chat_id: str
    main_topic: str
    user_goal: str
    key_insights: tuple[str, ...]
    conclusion: str
    related_chat_refs: tuple[str, ...]
    facts_count: int
    messages_count: int
    produced_gist: bool
    created_at: datetime
    finalized_at: datetime | None
    payload_hash: str

    def __post_init__(self) -> None:
        _require_text(self.episode_id, "episode_id")
        _require_text(self.schema_version, "schema_version")
        _require_text(self.source_ref, "source_ref")
        _require_text(self.chat_id, "chat_id")
        if not isinstance(self.produced_gist, bool):
            raise ConversationBridgeError("produced_gist must be a boolean")
        _validate_count(self.facts_count, "facts_count")
        _validate_count(self.messages_count, "messages_count")
        _canonical_datetime(self.created_at)
        if self.finalized_at is not None:
            _canonical_datetime(self.finalized_at)
            if self.finalized_at < self.created_at:
                raise ConversationBridgeError("finalized_at cannot precede created_at")
        expected = _stable_digest(self.identity_payload())
        if self.episode_id != expected or self.payload_hash != expected:
            raise ConversationBridgeError(
                "episode_id and payload_hash must match projected notebook content"
            )

    @classmethod
    def from_notebook(
        cls,
        notebook: ConversationNotebook,
        *,
        schema_version: str = CONVERSATION_EPISODE_SCHEMA_VERSION,
    ) -> ConversationEpisode:
        if not isinstance(notebook, ConversationNotebook):
            raise ConversationBridgeError("notebook must be a ConversationNotebook")

        chat_id = _require_text(notebook.chat_id, "chat_id")
        created_at = _parse_timestamp(notebook.created_at, "created_at")
        if created_at is None:
            raise ConversationBridgeError("created_at is required")
        finalized_at = _parse_timestamp(notebook.finalized_at, "finalized_at")

        payload = cls._identity_payload(
            schema_version=schema_version,
            source_ref=f"conversation_notebook:{chat_id}",
            chat_id=chat_id,
            main_topic=_normalize_text(notebook.main_topic),
            user_goal=_normalize_text(notebook.user_goal),
            key_insights=_normalize_items(
                notebook.key_insights,
                field_name="key_insights",
                sort_items=False,
            ),
            conclusion=_normalize_text(notebook.conclusion),
            related_chat_refs=_normalize_items(
                notebook.related_chats,
                field_name="related_chats",
                sort_items=True,
            ),
            facts_count=_validate_count(notebook.facts_count, "facts_count"),
            messages_count=_validate_count(notebook.messages_count, "messages_count"),
            produced_gist=notebook.produced_gist,
            created_at=created_at,
            finalized_at=finalized_at,
        )
        digest = _stable_digest(payload)
        return cls(
            episode_id=digest,
            schema_version=schema_version,
            source_ref=f"conversation_notebook:{chat_id}",
            chat_id=chat_id,
            main_topic=_normalize_text(notebook.main_topic),
            user_goal=_normalize_text(notebook.user_goal),
            key_insights=_normalize_items(
                notebook.key_insights,
                field_name="key_insights",
                sort_items=False,
            ),
            conclusion=_normalize_text(notebook.conclusion),
            related_chat_refs=_normalize_items(
                notebook.related_chats,
                field_name="related_chats",
                sort_items=True,
            ),
            facts_count=_validate_count(notebook.facts_count, "facts_count"),
            messages_count=_validate_count(notebook.messages_count, "messages_count"),
            produced_gist=notebook.produced_gist,
            created_at=created_at,
            finalized_at=finalized_at,
            payload_hash=digest,
        )

    @staticmethod
    def _identity_payload(
        *,
        schema_version: str,
        source_ref: str,
        chat_id: str,
        main_topic: str,
        user_goal: str,
        key_insights: tuple[str, ...],
        conclusion: str,
        related_chat_refs: tuple[str, ...],
        facts_count: int,
        messages_count: int,
        produced_gist: bool,
        created_at: datetime,
        finalized_at: datetime | None,
    ) -> dict[str, object]:
        return {
            "schema_version": _require_text(schema_version, "schema_version"),
            "source_ref": _require_text(source_ref, "source_ref"),
            "chat_id": _require_text(chat_id, "chat_id"),
            "main_topic": _normalize_text(main_topic),
            "user_goal": _normalize_text(user_goal),
            "key_insights": list(key_insights),
            "conclusion": _normalize_text(conclusion),
            "related_chat_refs": list(related_chat_refs),
            "facts_count": _validate_count(facts_count, "facts_count"),
            "messages_count": _validate_count(messages_count, "messages_count"),
            "produced_gist": produced_gist,
            "created_at": _canonical_datetime(created_at),
            "finalized_at": (
                _canonical_datetime(finalized_at) if finalized_at is not None else None
            ),
        }

    def identity_payload(self) -> dict[str, object]:
        return self._identity_payload(
            schema_version=self.schema_version,
            source_ref=self.source_ref,
            chat_id=self.chat_id,
            main_topic=self.main_topic,
            user_goal=self.user_goal,
            key_insights=self.key_insights,
            conclusion=self.conclusion,
            related_chat_refs=self.related_chat_refs,
            facts_count=self.facts_count,
            messages_count=self.messages_count,
            produced_gist=self.produced_gist,
            created_at=self.created_at,
            finalized_at=self.finalized_at,
        )

    def canonical_bytes(self) -> bytes:
        return _canonical_json(self.identity_payload()).encode("utf-8")


class ConversationBridge:
    """Read-only adapter from notebook storage to immutable episodes."""

    def __init__(self, source: ConversationNotebookReader) -> None:
        self._source = source

    def get_episode(self, chat_id: str) -> ConversationEpisode | None:
        normalized_chat_id = _require_text(chat_id, "chat_id")
        notebook = self._source.get_notebook(normalized_chat_id)
        return None if notebook is None else ConversationEpisode.from_notebook(notebook)

    def search_episodes(self, query: str, limit: int = 10) -> tuple[ConversationEpisode, ...]:
        normalized_query = _require_text(query, "query")
        validated_limit = self._validate_limit(limit)
        return self._project_many(self._source.search(normalized_query, validated_limit))

    def list_recent(self, limit: int = 10) -> tuple[ConversationEpisode, ...]:
        validated_limit = self._validate_limit(limit)
        return self._project_many(self._source.list_recent(validated_limit))

    @staticmethod
    def _validate_limit(limit: int) -> int:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ConversationBridgeError("limit must be an integer in [1, 100]")
        return limit

    @staticmethod
    def _project_many(
        notebooks: Sequence[ConversationNotebook],
    ) -> tuple[ConversationEpisode, ...]:
        by_chat_id: dict[str, ConversationEpisode] = {}
        for notebook in notebooks:
            episode = ConversationEpisode.from_notebook(notebook)
            existing = by_chat_id.get(episode.chat_id)
            if existing is not None and existing.payload_hash != episode.payload_hash:
                raise ConversationBridgeError(
                    f"source returned conflicting snapshots for chat_id={episode.chat_id}"
                )
            by_chat_id[episode.chat_id] = episode

        return tuple(
            sorted(
                by_chat_id.values(),
                key=lambda episode: (
                    episode.finalized_at or episode.created_at,
                    episode.chat_id,
                ),
                reverse=True,
            )
        )


__all__ = [
    "CONVERSATION_EPISODE_SCHEMA_VERSION",
    "ConversationBridge",
    "ConversationBridgeError",
    "ConversationEpisode",
    "ConversationNotebookReader",
]
