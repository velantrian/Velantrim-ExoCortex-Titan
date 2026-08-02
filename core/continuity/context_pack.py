"""Deterministic shadow continuity context projection and receipt.

This module assembles source-linked continuity candidates from immutable
``ConversationEpisode`` and ``ThreadWeaveResult`` projections. It does not
produce the final prompt ``ContextPack``, invoke ``WorkingMemoryGate``, assign
truth, write Canon, or influence the answer path.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Iterable, Sequence

from .conversation_bridge import ConversationEpisode
from .thread_weaver import (
    ContinuityThread,
    ThreadLink,
    ThreadLinkStrength,
    ThreadWeaveResult,
    UnresolvedThreadReference,
)

CONTINUITY_CONTEXT_PACK_SCHEMA_VERSION = "continuity.context_pack.v1"
CONTINUITY_RECEIPT_SCHEMA_VERSION = "continuity.receipt.v1"
CONTINUITY_CONTEXT_POLICY_VERSION = "continuity.context.policy.v1"


class ContinuityContextError(ValueError):
    """Raised when continuity context cannot be assembled deterministically."""


class ContinuityItemKind(str, Enum):
    """Source-backed content kinds copied from a conversation projection."""

    PRIOR_GOAL_TEXT = "prior_goal_text"
    PRIOR_TOPIC_TEXT = "prior_topic_text"
    PRIOR_INSIGHT_TEXT = "prior_insight_text"
    PRIOR_CONCLUSION_TEXT = "prior_conclusion_text"
    UNRESOLVED_CHAT_REFERENCE = "unresolved_chat_reference"


class ContinuityUncertainty(str, Enum):
    """Mandatory uncertainty markers for continuity projection content."""

    SOURCE_IS_CONVERSATION_PROJECTION = "source_is_conversation_projection"
    CURRENTNESS_UNCONFIRMED = "currentness_unconfirmed"
    TARGET_NOT_LOADED = "target_not_loaded"


class ContinuityDisposition(str, Enum):
    INCLUDED = "included"
    EXCLUDED = "excluded"


class ContinuityDecisionSubject(str, Enum):
    EPISODE = "episode"
    UNRESOLVED_REFERENCE = "unresolved_reference"


class ContinuityReason(str, Enum):
    """Stable reason codes used by the continuity assembler."""

    CURRENT_EPISODE = "current_episode"
    CONNECTED_THREAD = "connected_thread"
    PRIOR_TO_CURRENT = "prior_to_current"
    AFTER_CURRENT = "after_current"
    NOT_IN_CURRENT_THREAD = "not_in_current_thread"
    LOCAL_SAFETY_LIMIT = "local_safety_limit"
    EXPLICIT_LINK_PRESENT = "explicit_link_present"
    STRUCTURAL_LINK_PRESENT = "structural_link_present"
    SOURCE_CONTENT_AVAILABLE = "source_content_available"
    EMPTY_SOURCE_CONTENT = "empty_source_content"
    UNRESOLVED_EXPLICIT_REFERENCE = "unresolved_explicit_reference"


def _normalize_text(value: str) -> str:
    if not isinstance(value, str):
        raise ContinuityContextError("text fields must be strings")
    return " ".join(unicodedata.normalize("NFC", value).split())


def _require_text(value: str, field_name: str) -> str:
    normalized = _normalize_text(value)
    if not normalized:
        raise ContinuityContextError(f"{field_name} must be non-empty")
    return normalized


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _stable_digest(payload: object) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _sorted_unique_text(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    normalized = tuple(_require_text(value, field_name) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ContinuityContextError(f"{field_name} cannot contain duplicates")
    return tuple(sorted(normalized))


def _sorted_unique_enum[T: Enum](values: Iterable[T], enum_type: type[T], field_name: str) -> tuple[T, ...]:
    materialized = tuple(values)
    if any(not isinstance(value, enum_type) for value in materialized):
        raise ContinuityContextError(f"{field_name} contains an invalid enum value")
    unique = {value.value: value for value in materialized}
    if len(unique) != len(materialized):
        raise ContinuityContextError(f"{field_name} cannot contain duplicates")
    return tuple(unique[key] for key in sorted(unique))


def _effective_timestamp(episode: ConversationEpisode):
    return episode.finalized_at or episode.created_at


@dataclass(frozen=True, slots=True)
class ContinuityContextItem:
    """One source-linked continuity candidate, not an admitted fact."""

    item_id: str
    kind: ContinuityItemKind
    source_episode_id: str
    source_ref: str
    text: str
    uncertainty_codes: tuple[ContinuityUncertainty, ...]
    payload_hash: str

    def __post_init__(self) -> None:
        _require_text(self.item_id, "item_id")
        if not isinstance(self.kind, ContinuityItemKind):
            raise ContinuityContextError("kind must be a ContinuityItemKind")
        _require_text(self.source_episode_id, "source_episode_id")
        _require_text(self.source_ref, "source_ref")
        _require_text(self.text, "text")
        expected_uncertainty = _sorted_unique_enum(
            self.uncertainty_codes,
            ContinuityUncertainty,
            "uncertainty_codes",
        )
        if self.uncertainty_codes != expected_uncertainty:
            raise ContinuityContextError("uncertainty_codes must be sorted and unique")
        expected = _stable_digest(self.identity_payload())
        if self.item_id != expected or self.payload_hash != expected:
            raise ContinuityContextError("item identity must match item content")

    @classmethod
    def build(
        cls,
        *,
        kind: ContinuityItemKind,
        source_episode_id: str,
        source_ref: str,
        text: str,
        uncertainty_codes: Iterable[ContinuityUncertainty],
    ) -> ContinuityContextItem:
        normalized_uncertainty = _sorted_unique_enum(
            uncertainty_codes,
            ContinuityUncertainty,
            "uncertainty_codes",
        )
        payload = cls._identity_payload(
            kind=kind,
            source_episode_id=source_episode_id,
            source_ref=source_ref,
            text=text,
            uncertainty_codes=normalized_uncertainty,
        )
        digest = _stable_digest(payload)
        return cls(
            item_id=digest,
            kind=kind,
            source_episode_id=_require_text(source_episode_id, "source_episode_id"),
            source_ref=_require_text(source_ref, "source_ref"),
            text=_require_text(text, "text"),
            uncertainty_codes=normalized_uncertainty,
            payload_hash=digest,
        )

    @staticmethod
    def _identity_payload(
        *,
        kind: ContinuityItemKind,
        source_episode_id: str,
        source_ref: str,
        text: str,
        uncertainty_codes: tuple[ContinuityUncertainty, ...],
    ) -> dict[str, object]:
        if not isinstance(kind, ContinuityItemKind):
            raise ContinuityContextError("kind must be a ContinuityItemKind")
        return {
            "kind": kind.value,
            "source_episode_id": _require_text(source_episode_id, "source_episode_id"),
            "source_ref": _require_text(source_ref, "source_ref"),
            "text": _require_text(text, "text"),
            "uncertainty_codes": [code.value for code in uncertainty_codes],
        }

    def identity_payload(self) -> dict[str, object]:
        return self._identity_payload(
            kind=self.kind,
            source_episode_id=self.source_episode_id,
            source_ref=self.source_ref,
            text=self.text,
            uncertainty_codes=self.uncertainty_codes,
        )


@dataclass(frozen=True, slots=True)
class ContinuityDecision:
    """One deterministic inclusion or exclusion decision."""

    decision_id: str
    subject_kind: ContinuityDecisionSubject
    subject_ref: str
    disposition: ContinuityDisposition
    reason_codes: tuple[ContinuityReason, ...]
    source_refs: tuple[str, ...]
    payload_hash: str

    def __post_init__(self) -> None:
        _require_text(self.decision_id, "decision_id")
        if not isinstance(self.subject_kind, ContinuityDecisionSubject):
            raise ContinuityContextError(
                "subject_kind must be a ContinuityDecisionSubject"
            )
        _require_text(self.subject_ref, "subject_ref")
        if not isinstance(self.disposition, ContinuityDisposition):
            raise ContinuityContextError("disposition must be a ContinuityDisposition")
        expected_reasons = _sorted_unique_enum(
            self.reason_codes,
            ContinuityReason,
            "reason_codes",
        )
        if not expected_reasons:
            raise ContinuityContextError("reason_codes cannot be empty")
        if self.reason_codes != expected_reasons:
            raise ContinuityContextError("reason_codes must be sorted and unique")
        expected_sources = _sorted_unique_text(self.source_refs, "source_refs")
        if not expected_sources:
            raise ContinuityContextError("source_refs cannot be empty")
        if self.source_refs != expected_sources:
            raise ContinuityContextError("source_refs must be sorted and unique")
        expected = _stable_digest(self.identity_payload())
        if self.decision_id != expected or self.payload_hash != expected:
            raise ContinuityContextError("decision identity must match decision content")

    @classmethod
    def build(
        cls,
        *,
        subject_kind: ContinuityDecisionSubject,
        subject_ref: str,
        disposition: ContinuityDisposition,
        reason_codes: Iterable[ContinuityReason],
        source_refs: Iterable[str],
    ) -> ContinuityDecision:
        normalized_reasons = _sorted_unique_enum(
            reason_codes,
            ContinuityReason,
            "reason_codes",
        )
        if not normalized_reasons:
            raise ContinuityContextError("reason_codes cannot be empty")
        normalized_sources = _sorted_unique_text(source_refs, "source_refs")
        if not normalized_sources:
            raise ContinuityContextError("source_refs cannot be empty")
        payload = cls._identity_payload(
            subject_kind=subject_kind,
            subject_ref=subject_ref,
            disposition=disposition,
            reason_codes=normalized_reasons,
            source_refs=normalized_sources,
        )
        digest = _stable_digest(payload)
        return cls(
            decision_id=digest,
            subject_kind=subject_kind,
            subject_ref=_require_text(subject_ref, "subject_ref"),
            disposition=disposition,
            reason_codes=normalized_reasons,
            source_refs=normalized_sources,
            payload_hash=digest,
        )

    @staticmethod
    def _identity_payload(
        *,
        subject_kind: ContinuityDecisionSubject,
        subject_ref: str,
        disposition: ContinuityDisposition,
        reason_codes: tuple[ContinuityReason, ...],
        source_refs: tuple[str, ...],
    ) -> dict[str, object]:
        if not isinstance(subject_kind, ContinuityDecisionSubject):
            raise ContinuityContextError(
                "subject_kind must be a ContinuityDecisionSubject"
            )
        if not isinstance(disposition, ContinuityDisposition):
            raise ContinuityContextError("disposition must be a ContinuityDisposition")
        return {
            "subject_kind": subject_kind.value,
            "subject_ref": _require_text(subject_ref, "subject_ref"),
            "disposition": disposition.value,
            "reason_codes": [reason.value for reason in reason_codes],
            "source_refs": list(source_refs),
        }

    def identity_payload(self) -> dict[str, object]:
        return self._identity_payload(
            subject_kind=self.subject_kind,
            subject_ref=self.subject_ref,
            disposition=self.disposition,
            reason_codes=self.reason_codes,
            source_refs=self.source_refs,
        )


@dataclass(frozen=True, slots=True)
class ContinuityContextPack:
    """Bounded continuity candidate projection for a single request."""

    pack_id: str
    schema_version: str
    policy_version: str
    request_ref: str
    current_episode_id: str
    thread_id: str | None
    episode_ids: tuple[str, ...]
    link_ids: tuple[str, ...]
    unresolved_reference_ids: tuple[str, ...]
    items: tuple[ContinuityContextItem, ...]
    payload_hash: str

    def __post_init__(self) -> None:
        _require_text(self.pack_id, "pack_id")
        _require_text(self.schema_version, "schema_version")
        _require_text(self.policy_version, "policy_version")
        _require_text(self.request_ref, "request_ref")
        _require_text(self.current_episode_id, "current_episode_id")
        if self.thread_id is not None:
            _require_text(self.thread_id, "thread_id")
        for field_name, values in (
            ("episode_ids", self.episode_ids),
            ("link_ids", self.link_ids),
            ("unresolved_reference_ids", self.unresolved_reference_ids),
        ):
            expected = _sorted_unique_text(values, field_name)
            if values != expected:
                raise ContinuityContextError(f"{field_name} must be sorted and unique")
        if any(not isinstance(item, ContinuityContextItem) for item in self.items):
            raise ContinuityContextError("items must contain ContinuityContextItem values")
        expected_items = tuple(sorted(self.items, key=lambda item: item.item_id))
        if len({item.item_id for item in expected_items}) != len(expected_items):
            raise ContinuityContextError("items cannot contain duplicate identities")
        if self.items != expected_items:
            raise ContinuityContextError("items must be sorted by item_id")
        item_episode_ids = {
            item.source_episode_id
            for item in self.items
            if item.kind is not ContinuityItemKind.UNRESOLVED_CHAT_REFERENCE
        }
        if not item_episode_ids.issubset(set(self.episode_ids)):
            raise ContinuityContextError("item source episodes must be included in episode_ids")
        expected = _stable_digest(self.identity_payload())
        if self.pack_id != expected or self.payload_hash != expected:
            raise ContinuityContextError("pack identity must match pack content")

    @classmethod
    def build(
        cls,
        *,
        request_ref: str,
        current_episode_id: str,
        thread_id: str | None,
        episode_ids: Iterable[str],
        link_ids: Iterable[str],
        unresolved_reference_ids: Iterable[str],
        items: Iterable[ContinuityContextItem],
        policy_version: str = CONTINUITY_CONTEXT_POLICY_VERSION,
        schema_version: str = CONTINUITY_CONTEXT_PACK_SCHEMA_VERSION,
    ) -> ContinuityContextPack:
        normalized_episode_ids = _sorted_unique_text(episode_ids, "episode_ids")
        normalized_link_ids = _sorted_unique_text(link_ids, "link_ids")
        normalized_unresolved_ids = _sorted_unique_text(
            unresolved_reference_ids,
            "unresolved_reference_ids",
        )
        normalized_items = tuple(sorted(tuple(items), key=lambda item: item.item_id))
        if any(not isinstance(item, ContinuityContextItem) for item in normalized_items):
            raise ContinuityContextError("items must contain ContinuityContextItem values")
        payload = cls._identity_payload(
            schema_version=schema_version,
            policy_version=policy_version,
            request_ref=request_ref,
            current_episode_id=current_episode_id,
            thread_id=thread_id,
            episode_ids=normalized_episode_ids,
            link_ids=normalized_link_ids,
            unresolved_reference_ids=normalized_unresolved_ids,
            items=normalized_items,
        )
        digest = _stable_digest(payload)
        return cls(
            pack_id=digest,
            schema_version=_require_text(schema_version, "schema_version"),
            policy_version=_require_text(policy_version, "policy_version"),
            request_ref=_require_text(request_ref, "request_ref"),
            current_episode_id=_require_text(current_episode_id, "current_episode_id"),
            thread_id=(
                _require_text(thread_id, "thread_id") if thread_id is not None else None
            ),
            episode_ids=normalized_episode_ids,
            link_ids=normalized_link_ids,
            unresolved_reference_ids=normalized_unresolved_ids,
            items=normalized_items,
            payload_hash=digest,
        )

    @staticmethod
    def _identity_payload(
        *,
        schema_version: str,
        policy_version: str,
        request_ref: str,
        current_episode_id: str,
        thread_id: str | None,
        episode_ids: tuple[str, ...],
        link_ids: tuple[str, ...],
        unresolved_reference_ids: tuple[str, ...],
        items: tuple[ContinuityContextItem, ...],
    ) -> dict[str, object]:
        return {
            "schema_version": _require_text(schema_version, "schema_version"),
            "policy_version": _require_text(policy_version, "policy_version"),
            "request_ref": _require_text(request_ref, "request_ref"),
            "current_episode_id": _require_text(
                current_episode_id,
                "current_episode_id",
            ),
            "thread_id": (
                _require_text(thread_id, "thread_id") if thread_id is not None else None
            ),
            "episode_ids": list(episode_ids),
            "link_ids": list(link_ids),
            "unresolved_reference_ids": list(unresolved_reference_ids),
            "items": [item.identity_payload() for item in items],
        }

    def identity_payload(self) -> dict[str, object]:
        return self._identity_payload(
            schema_version=self.schema_version,
            policy_version=self.policy_version,
            request_ref=self.request_ref,
            current_episode_id=self.current_episode_id,
            thread_id=self.thread_id,
            episode_ids=self.episode_ids,
            link_ids=self.link_ids,
            unresolved_reference_ids=self.unresolved_reference_ids,
            items=self.items,
        )

    def canonical_bytes(self) -> bytes:
        return _canonical_json(self.identity_payload()).encode("utf-8")


@dataclass(frozen=True, slots=True)
class ContinuityReceipt:
    """Deterministic audit record for one continuity assembly."""

    receipt_id: str
    schema_version: str
    policy_version: str
    request_ref: str
    pack_id: str
    decisions: tuple[ContinuityDecision, ...]
    payload_hash: str

    def __post_init__(self) -> None:
        _require_text(self.receipt_id, "receipt_id")
        _require_text(self.schema_version, "schema_version")
        _require_text(self.policy_version, "policy_version")
        _require_text(self.request_ref, "request_ref")
        _require_text(self.pack_id, "pack_id")
        if any(not isinstance(item, ContinuityDecision) for item in self.decisions):
            raise ContinuityContextError("decisions must contain ContinuityDecision values")
        expected_decisions = tuple(sorted(self.decisions, key=lambda item: item.decision_id))
        if len({item.decision_id for item in expected_decisions}) != len(expected_decisions):
            raise ContinuityContextError("decisions cannot contain duplicate identities")
        if self.decisions != expected_decisions:
            raise ContinuityContextError("decisions must be sorted by decision_id")
        expected = _stable_digest(self.identity_payload())
        if self.receipt_id != expected or self.payload_hash != expected:
            raise ContinuityContextError("receipt identity must match receipt content")

    @classmethod
    def build(
        cls,
        *,
        request_ref: str,
        pack_id: str,
        decisions: Iterable[ContinuityDecision],
        policy_version: str = CONTINUITY_CONTEXT_POLICY_VERSION,
        schema_version: str = CONTINUITY_RECEIPT_SCHEMA_VERSION,
    ) -> ContinuityReceipt:
        normalized_decisions = tuple(
            sorted(tuple(decisions), key=lambda item: item.decision_id)
        )
        if any(not isinstance(item, ContinuityDecision) for item in normalized_decisions):
            raise ContinuityContextError("decisions must contain ContinuityDecision values")
        payload = cls._identity_payload(
            schema_version=schema_version,
            policy_version=policy_version,
            request_ref=request_ref,
            pack_id=pack_id,
            decisions=normalized_decisions,
        )
        digest = _stable_digest(payload)
        return cls(
            receipt_id=digest,
            schema_version=_require_text(schema_version, "schema_version"),
            policy_version=_require_text(policy_version, "policy_version"),
            request_ref=_require_text(request_ref, "request_ref"),
            pack_id=_require_text(pack_id, "pack_id"),
            decisions=normalized_decisions,
            payload_hash=digest,
        )

    @staticmethod
    def _identity_payload(
        *,
        schema_version: str,
        policy_version: str,
        request_ref: str,
        pack_id: str,
        decisions: tuple[ContinuityDecision, ...],
    ) -> dict[str, object]:
        return {
            "schema_version": _require_text(schema_version, "schema_version"),
            "policy_version": _require_text(policy_version, "policy_version"),
            "request_ref": _require_text(request_ref, "request_ref"),
            "pack_id": _require_text(pack_id, "pack_id"),
            "decisions": [decision.identity_payload() for decision in decisions],
        }

    def identity_payload(self) -> dict[str, object]:
        return self._identity_payload(
            schema_version=self.schema_version,
            policy_version=self.policy_version,
            request_ref=self.request_ref,
            pack_id=self.pack_id,
            decisions=self.decisions,
        )


@dataclass(frozen=True, slots=True)
class ContinuityAssemblyResult:
    pack: ContinuityContextPack
    receipt: ContinuityReceipt


class ContinuityContextAssembler:
    """Build a conservative bounded continuity candidate projection."""

    def assemble(
        self,
        *,
        request_ref: str,
        current_episode: ConversationEpisode,
        episodes: Sequence[ConversationEpisode],
        weave_result: ThreadWeaveResult,
        max_prior_episodes: int = 8,
        policy_version: str = CONTINUITY_CONTEXT_POLICY_VERSION,
    ) -> ContinuityAssemblyResult:
        _require_text(request_ref, "request_ref")
        if not isinstance(current_episode, ConversationEpisode):
            raise ContinuityContextError("current_episode must be a ConversationEpisode")
        if isinstance(max_prior_episodes, bool) or not isinstance(max_prior_episodes, int):
            raise ContinuityContextError("max_prior_episodes must be an integer")
        if not 0 <= max_prior_episodes <= 100:
            raise ContinuityContextError("max_prior_episodes must be in [0, 100]")
        if not isinstance(weave_result, ThreadWeaveResult):
            raise ContinuityContextError("weave_result must be a ThreadWeaveResult")

        by_episode_id = self._deduplicate_episodes(episodes)
        source_current = by_episode_id.get(current_episode.episode_id)
        if source_current is None:
            raise ContinuityContextError("current_episode must be present in episodes")
        if source_current.payload_hash != current_episode.payload_hash:
            raise ContinuityContextError("current_episode conflicts with episodes input")

        thread = self._current_thread(current_episode.episode_id, weave_result.threads)
        selected_ids, excluded_reasons = self._select_prior_episode_ids(
            current_episode=current_episode,
            thread=thread,
            by_episode_id=by_episode_id,
            max_prior_episodes=max_prior_episodes,
        )
        selected_id_set = set(selected_ids)
        selected_with_current = selected_id_set | {current_episode.episode_id}

        relevant_links = tuple(
            sorted(
                (
                    link
                    for link in weave_result.links
                    if link.link_id in (set(thread.link_ids) if thread is not None else set())
                    and link.source_episode_id in selected_with_current
                    and link.target_episode_id in selected_with_current
                ),
                key=lambda link: link.link_id,
            )
        )
        unresolved = tuple(
            sorted(
                (
                    reference
                    for reference in weave_result.unresolved_references
                    if reference.source_episode_id in selected_with_current
                ),
                key=lambda reference: reference.reference_id,
            )
        )

        items = self._build_items(
            selected_ids=selected_ids,
            by_episode_id=by_episode_id,
            unresolved=unresolved,
        )
        decisions = self._build_decisions(
            current_episode=current_episode,
            by_episode_id=by_episode_id,
            selected_ids=selected_ids,
            excluded_reasons=excluded_reasons,
            relevant_links=relevant_links,
            unresolved=unresolved,
        )

        pack = ContinuityContextPack.build(
            request_ref=request_ref,
            current_episode_id=current_episode.episode_id,
            thread_id=thread.thread_id if thread is not None else None,
            episode_ids=selected_ids,
            link_ids=(link.link_id for link in relevant_links),
            unresolved_reference_ids=(
                reference.reference_id for reference in unresolved
            ),
            items=items,
            policy_version=policy_version,
        )
        receipt = ContinuityReceipt.build(
            request_ref=request_ref,
            pack_id=pack.pack_id,
            decisions=decisions,
            policy_version=policy_version,
        )
        return ContinuityAssemblyResult(pack=pack, receipt=receipt)

    @staticmethod
    def _deduplicate_episodes(
        episodes: Sequence[ConversationEpisode],
    ) -> dict[str, ConversationEpisode]:
        by_episode_id: dict[str, ConversationEpisode] = {}
        by_chat_id: dict[str, ConversationEpisode] = {}
        for episode in episodes:
            if not isinstance(episode, ConversationEpisode):
                raise ContinuityContextError(
                    "episodes must contain ConversationEpisode values"
                )
            existing_id = by_episode_id.get(episode.episode_id)
            if existing_id is not None and existing_id.payload_hash != episode.payload_hash:
                raise ContinuityContextError("conflicting duplicate episode identity")
            existing_chat = by_chat_id.get(episode.chat_id)
            if existing_chat is not None and existing_chat.payload_hash != episode.payload_hash:
                raise ContinuityContextError(
                    f"conflicting snapshots for chat_id={episode.chat_id}"
                )
            by_episode_id[episode.episode_id] = episode
            by_chat_id[episode.chat_id] = episode
        return by_episode_id

    @staticmethod
    def _current_thread(
        current_episode_id: str,
        threads: Sequence[ContinuityThread],
    ) -> ContinuityThread | None:
        matching = tuple(
            thread for thread in threads if current_episode_id in thread.episode_ids
        )
        if len(matching) > 1:
            raise ContinuityContextError("current episode belongs to multiple threads")
        return matching[0] if matching else None

    @staticmethod
    def _select_prior_episode_ids(
        *,
        current_episode: ConversationEpisode,
        thread: ContinuityThread | None,
        by_episode_id: dict[str, ConversationEpisode],
        max_prior_episodes: int,
    ) -> tuple[tuple[str, ...], dict[str, tuple[ContinuityReason, ...]]]:
        excluded: dict[str, tuple[ContinuityReason, ...]] = {
            current_episode.episode_id: (ContinuityReason.CURRENT_EPISODE,)
        }
        if thread is None:
            for episode_id in by_episode_id:
                if episode_id != current_episode.episode_id:
                    excluded[episode_id] = (
                        ContinuityReason.NOT_IN_CURRENT_THREAD,
                    )
            return (), excluded

        missing = set(thread.episode_ids) - set(by_episode_id)
        if missing:
            raise ContinuityContextError(
                "thread references episodes absent from the assembly input"
            )
        current_index = thread.episode_ids.index(current_episode.episode_id)
        prior_ids = list(thread.episode_ids[:current_index])
        future_ids = tuple(thread.episode_ids[current_index + 1 :])
        for episode_id in future_ids:
            excluded[episode_id] = (ContinuityReason.AFTER_CURRENT,)

        selected = prior_ids[-max_prior_episodes:] if max_prior_episodes else []
        dropped = prior_ids[: len(prior_ids) - len(selected)]
        for episode_id in dropped:
            excluded[episode_id] = (ContinuityReason.LOCAL_SAFETY_LIMIT,)

        thread_ids = set(thread.episode_ids)
        for episode_id in by_episode_id:
            if episode_id not in thread_ids:
                excluded[episode_id] = (ContinuityReason.NOT_IN_CURRENT_THREAD,)
        return tuple(selected), excluded

    @staticmethod
    def _build_items(
        *,
        selected_ids: tuple[str, ...],
        by_episode_id: dict[str, ConversationEpisode],
        unresolved: tuple[UnresolvedThreadReference, ...],
    ) -> tuple[ContinuityContextItem, ...]:
        items: list[ContinuityContextItem] = []
        base_uncertainty = (
            ContinuityUncertainty.CURRENTNESS_UNCONFIRMED,
            ContinuityUncertainty.SOURCE_IS_CONVERSATION_PROJECTION,
        )
        for episode_id in selected_ids:
            episode = by_episode_id[episode_id]
            candidates = (
                (ContinuityItemKind.PRIOR_GOAL_TEXT, episode.user_goal),
                (ContinuityItemKind.PRIOR_TOPIC_TEXT, episode.main_topic),
                *(
                    (ContinuityItemKind.PRIOR_INSIGHT_TEXT, insight)
                    for insight in episode.key_insights
                ),
                (ContinuityItemKind.PRIOR_CONCLUSION_TEXT, episode.conclusion),
            )
            for kind, text in candidates:
                normalized = _normalize_text(text)
                if not normalized:
                    continue
                items.append(
                    ContinuityContextItem.build(
                        kind=kind,
                        source_episode_id=episode.episode_id,
                        source_ref=episode.source_ref,
                        text=normalized,
                        uncertainty_codes=base_uncertainty,
                    )
                )

        for reference in unresolved:
            items.append(
                ContinuityContextItem.build(
                    kind=ContinuityItemKind.UNRESOLVED_CHAT_REFERENCE,
                    source_episode_id=reference.source_episode_id,
                    source_ref=reference.source_ref,
                    text=reference.target_chat_ref,
                    uncertainty_codes=(
                        ContinuityUncertainty.SOURCE_IS_CONVERSATION_PROJECTION,
                        ContinuityUncertainty.TARGET_NOT_LOADED,
                    ),
                )
            )
        return tuple(sorted(items, key=lambda item: item.item_id))

    @staticmethod
    def _build_decisions(
        *,
        current_episode: ConversationEpisode,
        by_episode_id: dict[str, ConversationEpisode],
        selected_ids: tuple[str, ...],
        excluded_reasons: dict[str, tuple[ContinuityReason, ...]],
        relevant_links: tuple[ThreadLink, ...],
        unresolved: tuple[UnresolvedThreadReference, ...],
    ) -> tuple[ContinuityDecision, ...]:
        decisions: list[ContinuityDecision] = []
        selected_id_set = set(selected_ids)
        link_reasons_by_episode: dict[str, set[ContinuityReason]] = {
            episode_id: set() for episode_id in selected_ids
        }
        for link in relevant_links:
            reason = (
                ContinuityReason.EXPLICIT_LINK_PRESENT
                if link.strength is ThreadLinkStrength.EXPLICIT
                else ContinuityReason.STRUCTURAL_LINK_PRESENT
            )
            for episode_id in (link.source_episode_id, link.target_episode_id):
                if episode_id in link_reasons_by_episode:
                    link_reasons_by_episode[episode_id].add(reason)

        for episode_id, episode in by_episode_id.items():
            if episode_id in selected_id_set:
                reasons = {
                    ContinuityReason.CONNECTED_THREAD,
                    ContinuityReason.PRIOR_TO_CURRENT,
                }
                reasons.update(link_reasons_by_episode[episode_id])
                if any(
                    _normalize_text(value)
                    for value in (
                        episode.user_goal,
                        episode.main_topic,
                        episode.conclusion,
                        *episode.key_insights,
                    )
                ):
                    reasons.add(ContinuityReason.SOURCE_CONTENT_AVAILABLE)
                else:
                    reasons.add(ContinuityReason.EMPTY_SOURCE_CONTENT)
                decisions.append(
                    ContinuityDecision.build(
                        subject_kind=ContinuityDecisionSubject.EPISODE,
                        subject_ref=episode_id,
                        disposition=ContinuityDisposition.INCLUDED,
                        reason_codes=reasons,
                        source_refs=(episode.source_ref,),
                    )
                )
            else:
                reasons = excluded_reasons.get(
                    episode_id,
                    (ContinuityReason.NOT_IN_CURRENT_THREAD,),
                )
                decisions.append(
                    ContinuityDecision.build(
                        subject_kind=ContinuityDecisionSubject.EPISODE,
                        subject_ref=episode_id,
                        disposition=ContinuityDisposition.EXCLUDED,
                        reason_codes=reasons,
                        source_refs=(episode.source_ref,),
                    )
                )

        if current_episode.episode_id not in by_episode_id:
            raise ContinuityContextError("current episode decision is missing")

        for reference in unresolved:
            decisions.append(
                ContinuityDecision.build(
                    subject_kind=ContinuityDecisionSubject.UNRESOLVED_REFERENCE,
                    subject_ref=reference.reference_id,
                    disposition=ContinuityDisposition.INCLUDED,
                    reason_codes=(
                        ContinuityReason.UNRESOLVED_EXPLICIT_REFERENCE,
                    ),
                    source_refs=(reference.source_ref,),
                )
            )
        return tuple(sorted(decisions, key=lambda item: item.decision_id))


__all__ = [
    "CONTINUITY_CONTEXT_PACK_SCHEMA_VERSION",
    "CONTINUITY_CONTEXT_POLICY_VERSION",
    "CONTINUITY_RECEIPT_SCHEMA_VERSION",
    "ContinuityAssemblyResult",
    "ContinuityContextAssembler",
    "ContinuityContextError",
    "ContinuityContextItem",
    "ContinuityContextPack",
    "ContinuityDecision",
    "ContinuityDecisionSubject",
    "ContinuityDisposition",
    "ContinuityItemKind",
    "ContinuityReason",
    "ContinuityReceipt",
    "ContinuityUncertainty",
]
