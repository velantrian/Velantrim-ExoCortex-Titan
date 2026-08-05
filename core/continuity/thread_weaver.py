"""Deterministic continuity thread projection over conversation episodes.

The weaver is intentionally conservative. It consumes immutable
``ConversationEpisode`` projections and emits rebuildable links and connected
threads. It does not call an LLM, use embeddings, write to Canon, assign truth
status, or make advisory or action decisions.

Version 1 emits only two relation types:

* ``REFERENCES`` from an explicit ``related_chat_refs`` source field;
* ``CONTINUES`` from an exact normalized notebook goal match.

The wider relation taxonomy is reserved for later typed evidence. Topic text and
recency alone never create a link.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Sequence

from .conversation_bridge import ConversationEpisode

THREAD_LINK_SCHEMA_VERSION = "continuity.thread_link.v1"
CONTINUITY_THREAD_SCHEMA_VERSION = "continuity.thread.v1"
UNRESOLVED_THREAD_REFERENCE_SCHEMA_VERSION = "continuity.unresolved_thread_reference.v1"


class ThreadWeaverError(ValueError):
    """Raised when episodes cannot be woven deterministically."""


class ThreadRelation(str, Enum):
    """Typed continuity relation taxonomy.

    Version 1 of ``ThreadWeaver`` emits only ``REFERENCES`` and ``CONTINUES``.
    Other members are reserved until corresponding typed evidence exists.
    """

    CONTINUES = "continues"
    REFERENCES = "references"
    UPDATES = "updates"
    SUPERSEDES = "supersedes"
    REOPENS = "reopens"
    CONTRADICTS = "contradicts"
    BLOCKS = "blocks"
    RESOLVES = "resolves"
    DEPENDS_ON = "depends_on"
    BELONGS_TO = "belongs_to"


class ThreadLinkStrength(str, Enum):
    """Non-numeric evidence class for a projected link."""

    EXPLICIT = "explicit"
    STRUCTURAL = "structural"


class ThreadSignal(str, Enum):
    """Deterministic source signals used by version 1."""

    EXPLICIT_RELATED_CHAT_REF = "explicit_related_chat_ref"
    EXACT_NOTEBOOK_GOAL_TEXT = "exact_notebook_goal_text"
    EXACT_NOTEBOOK_TOPIC_TEXT = "exact_notebook_topic_text"


def _normalize_text(value: str) -> str:
    if not isinstance(value, str):
        raise ThreadWeaverError("text fields must be strings")
    return " ".join(unicodedata.normalize("NFC", value).split())


def _require_text(value: str, field_name: str) -> str:
    normalized = _normalize_text(value)
    if not normalized:
        raise ThreadWeaverError(f"{field_name} must be non-empty")
    return normalized


def _comparison_key(value: str) -> str:
    return _normalize_text(value).casefold()


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _stable_digest(payload: dict[str, object]) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _effective_timestamp(episode: ConversationEpisode):
    return episode.finalized_at or episode.created_at


def _validate_sorted_unique_text(values: tuple[str, ...], field_name: str) -> None:
    normalized = tuple(_require_text(value, field_name) for value in values)
    expected = tuple(sorted(set(normalized)))
    if normalized != expected:
        raise ThreadWeaverError(f"{field_name} must be sorted and unique")


@dataclass(frozen=True, slots=True)
class ThreadLink:
    """Immutable rebuildable relation between two conversation episodes."""

    link_id: str
    schema_version: str
    source_episode_id: str
    target_episode_id: str
    source_chat_id: str
    target_chat_id: str
    relation: ThreadRelation
    strength: ThreadLinkStrength
    signals: tuple[ThreadSignal, ...]
    source_refs: tuple[str, ...]
    payload_hash: str

    def __post_init__(self) -> None:
        _require_text(self.link_id, "link_id")
        _require_text(self.schema_version, "schema_version")
        _require_text(self.source_episode_id, "source_episode_id")
        _require_text(self.target_episode_id, "target_episode_id")
        _require_text(self.source_chat_id, "source_chat_id")
        _require_text(self.target_chat_id, "target_chat_id")
        if self.source_episode_id == self.target_episode_id:
            raise ThreadWeaverError("thread links require distinct episode ids")
        if self.source_chat_id == self.target_chat_id:
            raise ThreadWeaverError("thread links require distinct chat ids")
        if not isinstance(self.relation, ThreadRelation):
            raise ThreadWeaverError("relation must be a ThreadRelation")
        if not isinstance(self.strength, ThreadLinkStrength):
            raise ThreadWeaverError("strength must be a ThreadLinkStrength")
        if not self.signals:
            raise ThreadWeaverError("signals must be non-empty")
        if any(not isinstance(signal, ThreadSignal) for signal in self.signals):
            raise ThreadWeaverError("signals must contain ThreadSignal values")
        expected_signals = tuple(sorted(set(self.signals), key=lambda signal: signal.value))
        if self.signals != expected_signals:
            raise ThreadWeaverError("signals must be sorted and unique")
        _validate_sorted_unique_text(self.source_refs, "source_refs")
        expected = _stable_digest(self.identity_payload())
        if self.link_id != expected or self.payload_hash != expected:
            raise ThreadWeaverError("link identity must match link content")

    @classmethod
    def build(
        cls,
        *,
        source: ConversationEpisode,
        target: ConversationEpisode,
        relation: ThreadRelation,
        strength: ThreadLinkStrength,
        signals: Sequence[ThreadSignal],
    ) -> ThreadLink:
        if source.chat_id == target.chat_id:
            raise ThreadWeaverError("cannot link an episode to itself")
        normalized_signals = tuple(sorted(set(signals), key=lambda signal: signal.value))
        source_refs = tuple(sorted({source.source_ref, target.source_ref}))
        payload = cls._identity_payload(
            schema_version=THREAD_LINK_SCHEMA_VERSION,
            source_episode_id=source.episode_id,
            target_episode_id=target.episode_id,
            source_chat_id=source.chat_id,
            target_chat_id=target.chat_id,
            relation=relation,
            strength=strength,
            signals=normalized_signals,
            source_refs=source_refs,
        )
        digest = _stable_digest(payload)
        return cls(
            link_id=digest,
            schema_version=THREAD_LINK_SCHEMA_VERSION,
            source_episode_id=source.episode_id,
            target_episode_id=target.episode_id,
            source_chat_id=source.chat_id,
            target_chat_id=target.chat_id,
            relation=relation,
            strength=strength,
            signals=normalized_signals,
            source_refs=source_refs,
            payload_hash=digest,
        )

    @staticmethod
    def _identity_payload(
        *,
        schema_version: str,
        source_episode_id: str,
        target_episode_id: str,
        source_chat_id: str,
        target_chat_id: str,
        relation: ThreadRelation,
        strength: ThreadLinkStrength,
        signals: tuple[ThreadSignal, ...],
        source_refs: tuple[str, ...],
    ) -> dict[str, object]:
        return {
            "schema_version": _require_text(schema_version, "schema_version"),
            "source_episode_id": _require_text(source_episode_id, "source_episode_id"),
            "target_episode_id": _require_text(target_episode_id, "target_episode_id"),
            "source_chat_id": _require_text(source_chat_id, "source_chat_id"),
            "target_chat_id": _require_text(target_chat_id, "target_chat_id"),
            "relation": relation.value,
            "strength": strength.value,
            "signals": [signal.value for signal in signals],
            "source_refs": list(source_refs),
        }

    def identity_payload(self) -> dict[str, object]:
        return self._identity_payload(
            schema_version=self.schema_version,
            source_episode_id=self.source_episode_id,
            target_episode_id=self.target_episode_id,
            source_chat_id=self.source_chat_id,
            target_chat_id=self.target_chat_id,
            relation=self.relation,
            strength=self.strength,
            signals=self.signals,
            source_refs=self.source_refs,
        )

    def canonical_bytes(self) -> bytes:
        return _canonical_json(self.identity_payload()).encode("utf-8")


@dataclass(frozen=True, slots=True)
class UnresolvedThreadReference:
    """Explicit chat reference whose target was not present in the input batch."""

    reference_id: str
    schema_version: str
    source_episode_id: str
    source_chat_id: str
    target_chat_ref: str
    signal: ThreadSignal
    source_ref: str
    payload_hash: str

    def __post_init__(self) -> None:
        _require_text(self.reference_id, "reference_id")
        _require_text(self.schema_version, "schema_version")
        _require_text(self.source_episode_id, "source_episode_id")
        _require_text(self.source_chat_id, "source_chat_id")
        _require_text(self.target_chat_ref, "target_chat_ref")
        _require_text(self.source_ref, "source_ref")
        if self.source_chat_id == self.target_chat_ref:
            raise ThreadWeaverError("self references are invalid")
        if self.signal is not ThreadSignal.EXPLICIT_RELATED_CHAT_REF:
            raise ThreadWeaverError("unresolved references require an explicit reference signal")
        expected = _stable_digest(self.identity_payload())
        if self.reference_id != expected or self.payload_hash != expected:
            raise ThreadWeaverError("unresolved reference identity must match content")

    @classmethod
    def build(
        cls,
        *,
        source: ConversationEpisode,
        target_chat_ref: str,
    ) -> UnresolvedThreadReference:
        normalized_target = _require_text(target_chat_ref, "target_chat_ref")
        if normalized_target == source.chat_id:
            raise ThreadWeaverError("self references are invalid")
        payload = cls._identity_payload(
            schema_version=UNRESOLVED_THREAD_REFERENCE_SCHEMA_VERSION,
            source_episode_id=source.episode_id,
            source_chat_id=source.chat_id,
            target_chat_ref=normalized_target,
            signal=ThreadSignal.EXPLICIT_RELATED_CHAT_REF,
            source_ref=source.source_ref,
        )
        digest = _stable_digest(payload)
        return cls(
            reference_id=digest,
            schema_version=UNRESOLVED_THREAD_REFERENCE_SCHEMA_VERSION,
            source_episode_id=source.episode_id,
            source_chat_id=source.chat_id,
            target_chat_ref=normalized_target,
            signal=ThreadSignal.EXPLICIT_RELATED_CHAT_REF,
            source_ref=source.source_ref,
            payload_hash=digest,
        )

    @staticmethod
    def _identity_payload(
        *,
        schema_version: str,
        source_episode_id: str,
        source_chat_id: str,
        target_chat_ref: str,
        signal: ThreadSignal,
        source_ref: str,
    ) -> dict[str, object]:
        return {
            "schema_version": _require_text(schema_version, "schema_version"),
            "source_episode_id": _require_text(source_episode_id, "source_episode_id"),
            "source_chat_id": _require_text(source_chat_id, "source_chat_id"),
            "target_chat_ref": _require_text(target_chat_ref, "target_chat_ref"),
            "signal": signal.value,
            "source_ref": _require_text(source_ref, "source_ref"),
        }

    def identity_payload(self) -> dict[str, object]:
        return self._identity_payload(
            schema_version=self.schema_version,
            source_episode_id=self.source_episode_id,
            source_chat_id=self.source_chat_id,
            target_chat_ref=self.target_chat_ref,
            signal=self.signal,
            source_ref=self.source_ref,
        )


@dataclass(frozen=True, slots=True)
class ContinuityThread:
    """Deterministic connected component of linked conversation episodes."""

    thread_id: str
    schema_version: str
    episode_ids: tuple[str, ...]
    chat_ids: tuple[str, ...]
    link_ids: tuple[str, ...]
    payload_hash: str

    def __post_init__(self) -> None:
        _require_text(self.thread_id, "thread_id")
        _require_text(self.schema_version, "schema_version")
        if len(self.episode_ids) < 2:
            raise ThreadWeaverError("continuity threads require at least two episodes")
        if len(self.episode_ids) != len(self.chat_ids):
            raise ThreadWeaverError("episode_ids and chat_ids must have equal length")
        if len(set(self.episode_ids)) != len(self.episode_ids):
            raise ThreadWeaverError("episode_ids must be unique")
        if len(set(self.chat_ids)) != len(self.chat_ids):
            raise ThreadWeaverError("chat_ids must be unique")
        if not self.link_ids:
            raise ThreadWeaverError("link_ids must be non-empty")
        _validate_sorted_unique_text(self.link_ids, "link_ids")
        expected = _stable_digest(self.identity_payload())
        if self.thread_id != expected or self.payload_hash != expected:
            raise ThreadWeaverError("thread identity must match thread content")

    @classmethod
    def build(
        cls,
        *,
        episodes: Sequence[ConversationEpisode],
        links: Sequence[ThreadLink],
    ) -> ContinuityThread:
        if len(episodes) < 2:
            raise ThreadWeaverError("continuity threads require at least two episodes")
        ordered_episodes = tuple(
            sorted(
                episodes,
                key=lambda episode: (
                    _effective_timestamp(episode),
                    episode.chat_id,
                    episode.episode_id,
                ),
            )
        )
        episode_ids = tuple(episode.episode_id for episode in ordered_episodes)
        chat_ids = tuple(episode.chat_id for episode in ordered_episodes)
        link_ids = tuple(sorted({link.link_id for link in links}))
        payload = cls._identity_payload(
            schema_version=CONTINUITY_THREAD_SCHEMA_VERSION,
            episode_ids=episode_ids,
            chat_ids=chat_ids,
            link_ids=link_ids,
        )
        digest = _stable_digest(payload)
        return cls(
            thread_id=digest,
            schema_version=CONTINUITY_THREAD_SCHEMA_VERSION,
            episode_ids=episode_ids,
            chat_ids=chat_ids,
            link_ids=link_ids,
            payload_hash=digest,
        )

    @staticmethod
    def _identity_payload(
        *,
        schema_version: str,
        episode_ids: tuple[str, ...],
        chat_ids: tuple[str, ...],
        link_ids: tuple[str, ...],
    ) -> dict[str, object]:
        return {
            "schema_version": _require_text(schema_version, "schema_version"),
            "episode_ids": list(episode_ids),
            "chat_ids": list(chat_ids),
            "link_ids": list(link_ids),
        }

    def identity_payload(self) -> dict[str, object]:
        return self._identity_payload(
            schema_version=self.schema_version,
            episode_ids=self.episode_ids,
            chat_ids=self.chat_ids,
            link_ids=self.link_ids,
        )


@dataclass(frozen=True, slots=True)
class ThreadWeaveResult:
    """Read-only output of one deterministic weave operation."""

    links: tuple[ThreadLink, ...]
    threads: tuple[ContinuityThread, ...]
    unresolved_references: tuple[UnresolvedThreadReference, ...]


class ThreadWeaver:
    """Build conservative deterministic continuity links and threads."""

    def weave(self, episodes: Sequence[ConversationEpisode]) -> ThreadWeaveResult:
        by_chat_id = self._deduplicate(episodes)
        ordered = tuple(
            sorted(
                by_chat_id.values(),
                key=lambda episode: (
                    _effective_timestamp(episode),
                    episode.chat_id,
                    episode.episode_id,
                ),
            )
        )

        links: list[ThreadLink] = []
        unresolved: list[UnresolvedThreadReference] = []
        explicit_pairs: set[frozenset[str]] = set()

        for source in ordered:
            for target_chat_ref in source.related_chat_refs:
                if target_chat_ref == source.chat_id:
                    raise ThreadWeaverError(
                        f"episode {source.chat_id} explicitly references itself"
                    )
                target = by_chat_id.get(target_chat_ref)
                if target is None:
                    unresolved.append(
                        UnresolvedThreadReference.build(
                            source=source,
                            target_chat_ref=target_chat_ref,
                        )
                    )
                    continue
                links.append(
                    ThreadLink.build(
                        source=source,
                        target=target,
                        relation=ThreadRelation.REFERENCES,
                        strength=ThreadLinkStrength.EXPLICIT,
                        signals=(ThreadSignal.EXPLICIT_RELATED_CHAT_REF,),
                    )
                )
                explicit_pairs.add(frozenset((source.chat_id, target.chat_id)))

        for index, older in enumerate(ordered):
            for newer in ordered[index + 1 :]:
                pair = frozenset((older.chat_id, newer.chat_id))
                if pair in explicit_pairs:
                    continue
                goal_key = _comparison_key(older.user_goal)
                if not goal_key or goal_key != _comparison_key(newer.user_goal):
                    continue
                signals = [ThreadSignal.EXACT_NOTEBOOK_GOAL_TEXT]
                topic_key = _comparison_key(older.main_topic)
                if topic_key and topic_key == _comparison_key(newer.main_topic):
                    signals.append(ThreadSignal.EXACT_NOTEBOOK_TOPIC_TEXT)
                links.append(
                    ThreadLink.build(
                        source=newer,
                        target=older,
                        relation=ThreadRelation.CONTINUES,
                        strength=ThreadLinkStrength.STRUCTURAL,
                        signals=signals,
                    )
                )

        ordered_links = tuple(
            sorted(
                links,
                key=lambda link: (
                    _effective_timestamp(by_chat_id[link.source_chat_id]),
                    link.source_chat_id,
                    link.target_chat_id,
                    link.relation.value,
                    link.link_id,
                ),
            )
        )
        ordered_unresolved = tuple(
            sorted(
                unresolved,
                key=lambda reference: (
                    _effective_timestamp(by_chat_id[reference.source_chat_id]),
                    reference.source_chat_id,
                    reference.target_chat_ref,
                    reference.reference_id,
                ),
            )
        )
        threads = self._build_threads(by_chat_id, ordered_links)
        return ThreadWeaveResult(
            links=ordered_links,
            threads=threads,
            unresolved_references=ordered_unresolved,
        )

    @staticmethod
    def _deduplicate(
        episodes: Sequence[ConversationEpisode],
    ) -> dict[str, ConversationEpisode]:
        by_chat_id: dict[str, ConversationEpisode] = {}
        for episode in episodes:
            if not isinstance(episode, ConversationEpisode):
                raise ThreadWeaverError("episodes must contain ConversationEpisode values")
            existing = by_chat_id.get(episode.chat_id)
            if existing is not None and existing.payload_hash != episode.payload_hash:
                raise ThreadWeaverError(
                    f"conflicting episode snapshots for chat_id={episode.chat_id}"
                )
            by_chat_id[episode.chat_id] = episode
        return by_chat_id

    @staticmethod
    def _build_threads(
        by_chat_id: dict[str, ConversationEpisode],
        links: tuple[ThreadLink, ...],
    ) -> tuple[ContinuityThread, ...]:
        if not links:
            return ()

        parent: dict[str, str] = {}

        def find(chat_id: str) -> str:
            parent.setdefault(chat_id, chat_id)
            while parent[chat_id] != chat_id:
                parent[chat_id] = parent[parent[chat_id]]
                chat_id = parent[chat_id]
            return chat_id

        def union(left: str, right: str) -> None:
            left_root = find(left)
            right_root = find(right)
            if left_root == right_root:
                return
            if left_root < right_root:
                parent[right_root] = left_root
            else:
                parent[left_root] = right_root

        for link in links:
            union(link.source_chat_id, link.target_chat_id)

        component_chats: dict[str, set[str]] = {}
        for chat_id in parent:
            component_chats.setdefault(find(chat_id), set()).add(chat_id)

        component_links: dict[str, list[ThreadLink]] = {
            root: [] for root in component_chats
        }
        for link in links:
            component_links[find(link.source_chat_id)].append(link)

        threads = [
            ContinuityThread.build(
                episodes=[by_chat_id[chat_id] for chat_id in chats],
                links=component_links[root],
            )
            for root, chats in component_chats.items()
            if len(chats) >= 2
        ]
        return tuple(
            sorted(
                threads,
                key=lambda thread: (
                    _effective_timestamp(by_chat_id[thread.chat_ids[0]]),
                    thread.thread_id,
                ),
            )
        )


__all__ = [
    "CONTINUITY_THREAD_SCHEMA_VERSION",
    "THREAD_LINK_SCHEMA_VERSION",
    "UNRESOLVED_THREAD_REFERENCE_SCHEMA_VERSION",
    "ContinuityThread",
    "ThreadLink",
    "ThreadLinkStrength",
    "ThreadRelation",
    "ThreadSignal",
    "ThreadWeaveResult",
    "ThreadWeaver",
    "ThreadWeaverError",
    "UnresolvedThreadReference",
]
