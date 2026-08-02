"""Deterministic shadow continuity context projection and receipt.

This CSL output is not the final Synaptic ContextPack. It does not invoke
WorkingMemoryGate and has no truth, Canon-write, advisory, or action authority.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Iterable, Sequence, TypeVar

from .conversation_bridge import ConversationEpisode
from .thread_weaver import (
    ContinuityThread,
    ThreadLink,
    ThreadLinkStrength,
    ThreadWeaveResult,
    UnresolvedThreadReference,
)

CONTEXT_PACK_SCHEMA_VERSION = "continuity.context_pack.v1"
RECEIPT_SCHEMA_VERSION = "continuity.receipt.v1"
CONTEXT_POLICY_VERSION = "continuity.context.policy.v1"
EnumT = TypeVar("EnumT", bound=Enum)


class ContinuityContextError(ValueError):
    """Continuity context could not be built deterministically."""


class ContinuityItemKind(str, Enum):
    PRIOR_GOAL_TEXT = "prior_goal_text"
    PRIOR_TOPIC_TEXT = "prior_topic_text"
    PRIOR_INSIGHT_TEXT = "prior_insight_text"
    PRIOR_CONCLUSION_TEXT = "prior_conclusion_text"
    UNRESOLVED_CHAT_REFERENCE = "unresolved_chat_reference"


class ContinuityUncertainty(str, Enum):
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


def _text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise ContinuityContextError(f"{name} must be a string")
    result = " ".join(unicodedata.normalize("NFC", value).split())
    if not result:
        raise ContinuityContextError(f"{name} must be non-empty")
    return result


def _texts(values: Iterable[str], name: str, *, sort: bool) -> tuple[str, ...]:
    result = tuple(_text(value, name) for value in values)
    if len(result) != len(set(result)):
        raise ContinuityContextError(f"{name} cannot contain duplicates")
    return tuple(sorted(result)) if sort else result


def _enums(values: Iterable[EnumT], enum_type: type[EnumT], name: str) -> tuple[EnumT, ...]:
    result = tuple(values)
    if any(not isinstance(value, enum_type) for value in result):
        raise ContinuityContextError(f"{name} contains an invalid value")
    by_value: dict[str, EnumT] = {}
    for value in result:
        key = str(value.value)
        if key in by_value:
            raise ContinuityContextError(f"{name} cannot contain duplicates")
        by_value[key] = value
    return tuple(by_value[key] for key in sorted(by_value))


def _digest(payload: object) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(raw.encode("utf-8")).hexdigest()


def _item_payload(
    kind: ContinuityItemKind,
    source_episode_id: str,
    source_ref: str,
    text: str,
    uncertainties: tuple[ContinuityUncertainty, ...],
) -> dict[str, object]:
    return {
        "kind": kind.value,
        "source_episode_id": source_episode_id,
        "source_ref": source_ref,
        "text": text,
        "uncertainty_codes": [value.value for value in uncertainties],
    }


@dataclass(frozen=True, slots=True)
class ContinuityContextItem:
    item_id: str
    kind: ContinuityItemKind
    source_episode_id: str
    source_ref: str
    text: str
    uncertainty_codes: tuple[ContinuityUncertainty, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ContinuityItemKind):
            raise ContinuityContextError("kind must be a ContinuityItemKind")
        object.__setattr__(self, "source_episode_id", _text(self.source_episode_id, "source_episode_id"))
        object.__setattr__(self, "source_ref", _text(self.source_ref, "source_ref"))
        object.__setattr__(self, "text", _text(self.text, "text"))
        object.__setattr__(self, "uncertainty_codes", _enums(self.uncertainty_codes, ContinuityUncertainty, "uncertainty_codes"))
        if self.item_id != _digest(self.payload()):
            raise ContinuityContextError("item_id does not match item content")

    @classmethod
    def create(cls, *, kind: ContinuityItemKind, source_episode_id: str, source_ref: str,
               text: str, uncertainty_codes: Iterable[ContinuityUncertainty]) -> ContinuityContextItem:
        if not isinstance(kind, ContinuityItemKind):
            raise ContinuityContextError("kind must be a ContinuityItemKind")
        episode_id = _text(source_episode_id, "source_episode_id")
        ref = _text(source_ref, "source_ref")
        normalized_text = _text(text, "text")
        uncertainties = _enums(uncertainty_codes, ContinuityUncertainty, "uncertainty_codes")
        payload = _item_payload(kind, episode_id, ref, normalized_text, uncertainties)
        return cls(_digest(payload), kind, episode_id, ref, normalized_text, uncertainties)

    def payload(self) -> dict[str, object]:
        return _item_payload(self.kind, self.source_episode_id, self.source_ref, self.text, self.uncertainty_codes)

    def to_dict(self) -> dict[str, object]:
        return {"item_id": self.item_id, **self.payload()}


def _decision_payload(
    subject_kind: ContinuityDecisionSubject,
    subject_ref: str,
    disposition: ContinuityDisposition,
    reasons: tuple[ContinuityReason, ...],
    source_refs: tuple[str, ...],
) -> dict[str, object]:
    return {
        "subject_kind": subject_kind.value,
        "subject_ref": subject_ref,
        "disposition": disposition.value,
        "reason_codes": [value.value for value in reasons],
        "source_refs": list(source_refs),
    }


@dataclass(frozen=True, slots=True)
class ContinuityDecision:
    decision_id: str
    subject_kind: ContinuityDecisionSubject
    subject_ref: str
    disposition: ContinuityDisposition
    reason_codes: tuple[ContinuityReason, ...]
    source_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.subject_kind, ContinuityDecisionSubject):
            raise ContinuityContextError("invalid decision subject kind")
        if not isinstance(self.disposition, ContinuityDisposition):
            raise ContinuityContextError("invalid continuity disposition")
        object.__setattr__(self, "subject_ref", _text(self.subject_ref, "subject_ref"))
        object.__setattr__(self, "reason_codes", _enums(self.reason_codes, ContinuityReason, "reason_codes"))
        object.__setattr__(self, "source_refs", _texts(self.source_refs, "source_refs", sort=True))
        if not self.reason_codes or not self.source_refs:
            raise ContinuityContextError("decision reasons and sources cannot be empty")
        if self.decision_id != _digest(self.payload()):
            raise ContinuityContextError("decision_id does not match decision content")

    @classmethod
    def create(cls, *, subject_kind: ContinuityDecisionSubject, subject_ref: str,
               disposition: ContinuityDisposition, reason_codes: Iterable[ContinuityReason],
               source_refs: Iterable[str]) -> ContinuityDecision:
        if not isinstance(subject_kind, ContinuityDecisionSubject) or not isinstance(disposition, ContinuityDisposition):
            raise ContinuityContextError("invalid continuity decision enum")
        ref = _text(subject_ref, "subject_ref")
        reasons = _enums(reason_codes, ContinuityReason, "reason_codes")
        sources = _texts(source_refs, "source_refs", sort=True)
        if not reasons or not sources:
            raise ContinuityContextError("decision reasons and sources cannot be empty")
        payload = _decision_payload(subject_kind, ref, disposition, reasons, sources)
        return cls(_digest(payload), subject_kind, ref, disposition, reasons, sources)

    def payload(self) -> dict[str, object]:
        return _decision_payload(self.subject_kind, self.subject_ref, self.disposition, self.reason_codes, self.source_refs)

    def to_dict(self) -> dict[str, object]:
        return {"decision_id": self.decision_id, **self.payload()}


def _pack_payload(
    schema_version: str,
    policy_version: str,
    request_ref: str,
    current_episode_id: str,
    thread_id: str | None,
    episode_ids: tuple[str, ...],
    link_ids: tuple[str, ...],
    unresolved_ids: tuple[str, ...],
    items: tuple[ContinuityContextItem, ...],
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "policy_version": policy_version,
        "request_ref": request_ref,
        "current_episode_id": current_episode_id,
        "thread_id": thread_id,
        "episode_ids": list(episode_ids),
        "link_ids": list(link_ids),
        "unresolved_reference_ids": list(unresolved_ids),
        "items": [item.to_dict() for item in items],
    }


@dataclass(frozen=True, slots=True)
class ContinuityContextPack:
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

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _text(self.schema_version, "schema_version"))
        object.__setattr__(self, "policy_version", _text(self.policy_version, "policy_version"))
        object.__setattr__(self, "request_ref", _text(self.request_ref, "request_ref"))
        object.__setattr__(self, "current_episode_id", _text(self.current_episode_id, "current_episode_id"))
        if self.thread_id is not None:
            object.__setattr__(self, "thread_id", _text(self.thread_id, "thread_id"))
        object.__setattr__(self, "episode_ids", _texts(self.episode_ids, "episode_ids", sort=False))
        object.__setattr__(self, "link_ids", _texts(self.link_ids, "link_ids", sort=True))
        object.__setattr__(self, "unresolved_reference_ids", _texts(self.unresolved_reference_ids, "unresolved_reference_ids", sort=True))
        if any(not isinstance(item, ContinuityContextItem) for item in self.items):
            raise ContinuityContextError("items contain an invalid value")
        items = tuple(sorted(self.items, key=lambda item: item.item_id))
        if len(items) != len({item.item_id for item in items}):
            raise ContinuityContextError("items cannot contain duplicates")
        object.__setattr__(self, "items", items)
        prior_sources = {item.source_episode_id for item in items if item.kind is not ContinuityItemKind.UNRESOLVED_CHAT_REFERENCE}
        if not prior_sources.issubset(set(self.episode_ids)):
            raise ContinuityContextError("item source is absent from episode_ids")
        if self.pack_id != _digest(self.payload()):
            raise ContinuityContextError("pack_id does not match pack content")

    @classmethod
    def create(cls, *, request_ref: str, current_episode_id: str, thread_id: str | None,
               episode_ids: Iterable[str], link_ids: Iterable[str],
               unresolved_reference_ids: Iterable[str], items: Iterable[ContinuityContextItem],
               policy_version: str = CONTEXT_POLICY_VERSION) -> ContinuityContextPack:
        policy = _text(policy_version, "policy_version")
        request = _text(request_ref, "request_ref")
        current = _text(current_episode_id, "current_episode_id")
        resolved_thread = _text(thread_id, "thread_id") if thread_id is not None else None
        episodes = _texts(episode_ids, "episode_ids", sort=False)
        links = _texts(link_ids, "link_ids", sort=True)
        unresolved = _texts(unresolved_reference_ids, "unresolved_reference_ids", sort=True)
        normalized_items = tuple(sorted(tuple(items), key=lambda item: item.item_id))
        if any(not isinstance(item, ContinuityContextItem) for item in normalized_items):
            raise ContinuityContextError("items contain an invalid value")
        payload = _pack_payload(CONTEXT_PACK_SCHEMA_VERSION, policy, request, current, resolved_thread,
                                episodes, links, unresolved, normalized_items)
        return cls(_digest(payload), CONTEXT_PACK_SCHEMA_VERSION, policy, request, current,
                   resolved_thread, episodes, links, unresolved, normalized_items)

    def payload(self) -> dict[str, object]:
        return _pack_payload(self.schema_version, self.policy_version, self.request_ref,
                             self.current_episode_id, self.thread_id, self.episode_ids,
                             self.link_ids, self.unresolved_reference_ids, self.items)

    def to_dict(self) -> dict[str, object]:
        return {"pack_id": self.pack_id, **self.payload()}

    def canonical_bytes(self) -> bytes:
        return json.dumps(self.payload(), ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")


def _receipt_payload(schema_version: str, policy_version: str, request_ref: str,
                     pack_id: str, decisions: tuple[ContinuityDecision, ...]) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "policy_version": policy_version,
        "request_ref": request_ref,
        "pack_id": pack_id,
        "decisions": [item.to_dict() for item in decisions],
    }


@dataclass(frozen=True, slots=True)
class ContinuityReceipt:
    receipt_id: str
    schema_version: str
    policy_version: str
    request_ref: str
    pack_id: str
    decisions: tuple[ContinuityDecision, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _text(self.schema_version, "schema_version"))
        object.__setattr__(self, "policy_version", _text(self.policy_version, "policy_version"))
        object.__setattr__(self, "request_ref", _text(self.request_ref, "request_ref"))
        object.__setattr__(self, "pack_id", _text(self.pack_id, "pack_id"))
        if any(not isinstance(item, ContinuityDecision) for item in self.decisions):
            raise ContinuityContextError("decisions contain an invalid value")
        decisions = tuple(sorted(self.decisions, key=lambda item: item.decision_id))
        if len(decisions) != len({item.decision_id for item in decisions}):
            raise ContinuityContextError("decisions cannot contain duplicates")
        object.__setattr__(self, "decisions", decisions)
        if self.receipt_id != _digest(self.payload()):
            raise ContinuityContextError("receipt_id does not match receipt content")

    @classmethod
    def create(cls, *, request_ref: str, pack_id: str,
               decisions: Iterable[ContinuityDecision],
               policy_version: str = CONTEXT_POLICY_VERSION) -> ContinuityReceipt:
        policy = _text(policy_version, "policy_version")
        request = _text(request_ref, "request_ref")
        pack = _text(pack_id, "pack_id")
        normalized = tuple(sorted(tuple(decisions), key=lambda item: item.decision_id))
        if any(not isinstance(item, ContinuityDecision) for item in normalized):
            raise ContinuityContextError("decisions contain an invalid value")
        payload = _receipt_payload(RECEIPT_SCHEMA_VERSION, policy, request, pack, normalized)
        return cls(_digest(payload), RECEIPT_SCHEMA_VERSION, policy, request, pack, normalized)

    def payload(self) -> dict[str, object]:
        return _receipt_payload(self.schema_version, self.policy_version, self.request_ref,
                                self.pack_id, self.decisions)

    def to_dict(self) -> dict[str, object]:
        return {"receipt_id": self.receipt_id, **self.payload()}


@dataclass(frozen=True, slots=True)
class ContinuityAssemblyResult:
    pack: ContinuityContextPack
    receipt: ContinuityReceipt


class ContinuityContextAssembler:
    """Select source-backed prior episodes from the current thread."""

    def assemble(self, *, request_ref: str, current_episode: ConversationEpisode,
                 episodes: Sequence[ConversationEpisode], weave_result: ThreadWeaveResult,
                 max_prior_episodes: int = 8,
                 policy_version: str = CONTEXT_POLICY_VERSION) -> ContinuityAssemblyResult:
        _text(request_ref, "request_ref")
        if not isinstance(current_episode, ConversationEpisode):
            raise ContinuityContextError("current_episode must be a ConversationEpisode")
        if isinstance(max_prior_episodes, bool) or not isinstance(max_prior_episodes, int) or not 0 <= max_prior_episodes <= 100:
            raise ContinuityContextError("max_prior_episodes must be an integer in [0, 100]")
        if not isinstance(weave_result, ThreadWeaveResult):
            raise ContinuityContextError("weave_result must be a ThreadWeaveResult")

        by_id = self._episodes(episodes)
        current = by_id.get(current_episode.episode_id)
        if current is None or current.payload_hash != current_episode.payload_hash:
            raise ContinuityContextError("current_episode must match the episodes input")
        thread = self._thread(current_episode.episode_id, weave_result.threads)
        selected, excluded = self._select(current_episode, thread, by_id, max_prior_episodes)
        allowed = set(selected) | {current_episode.episode_id}
        thread_link_ids = set(thread.link_ids) if thread is not None else set()
        links = tuple(sorted((link for link in weave_result.links
                              if link.link_id in thread_link_ids
                              and link.source_episode_id in allowed
                              and link.target_episode_id in allowed),
                             key=lambda link: link.link_id))
        unresolved = tuple(sorted((item for item in weave_result.unresolved_references
                                   if item.source_episode_id in allowed),
                                  key=lambda item: item.reference_id))
        items = self._items(selected, by_id, unresolved)
        decisions = self._decisions(by_id, selected, excluded, links, unresolved)
        pack = ContinuityContextPack.create(
            request_ref=request_ref,
            current_episode_id=current_episode.episode_id,
            thread_id=thread.thread_id if thread is not None else None,
            episode_ids=selected,
            link_ids=(link.link_id for link in links),
            unresolved_reference_ids=(item.reference_id for item in unresolved),
            items=items,
            policy_version=policy_version,
        )
        receipt = ContinuityReceipt.create(request_ref=request_ref, pack_id=pack.pack_id,
                                           decisions=decisions, policy_version=policy_version)
        return ContinuityAssemblyResult(pack, receipt)

    @staticmethod
    def _episodes(episodes: Sequence[ConversationEpisode]) -> dict[str, ConversationEpisode]:
        by_id: dict[str, ConversationEpisode] = {}
        by_chat: dict[str, ConversationEpisode] = {}
        for episode in episodes:
            if not isinstance(episode, ConversationEpisode):
                raise ContinuityContextError("episodes contain an invalid value")
            previous = by_chat.get(episode.chat_id)
            if previous is not None and previous.payload_hash != episode.payload_hash:
                raise ContinuityContextError(f"conflicting snapshots for chat_id={episode.chat_id}")
            by_id[episode.episode_id] = episode
            by_chat[episode.chat_id] = episode
        return by_id

    @staticmethod
    def _thread(episode_id: str, threads: Sequence[ContinuityThread]) -> ContinuityThread | None:
        matches = tuple(thread for thread in threads if episode_id in thread.episode_ids)
        if len(matches) > 1:
            raise ContinuityContextError("current episode belongs to multiple threads")
        return matches[0] if matches else None

    @staticmethod
    def _select(current: ConversationEpisode, thread: ContinuityThread | None,
                by_id: dict[str, ConversationEpisode], limit: int
                ) -> tuple[tuple[str, ...], dict[str, ContinuityReason]]:
        excluded = {current.episode_id: ContinuityReason.CURRENT_EPISODE}
        if thread is None:
            excluded.update({key: ContinuityReason.NOT_IN_CURRENT_THREAD
                             for key in by_id if key != current.episode_id})
            return (), excluded
        if set(thread.episode_ids) - set(by_id):
            raise ContinuityContextError("thread references an episode absent from input")
        index = thread.episode_ids.index(current.episode_id)
        prior = list(thread.episode_ids[:index])
        excluded.update({key: ContinuityReason.AFTER_CURRENT
                         for key in thread.episode_ids[index + 1:]})
        selected = prior[-limit:] if limit else []
        excluded.update({key: ContinuityReason.LOCAL_SAFETY_LIMIT
                         for key in prior[:len(prior) - len(selected)]})
        thread_ids = set(thread.episode_ids)
        excluded.update({key: ContinuityReason.NOT_IN_CURRENT_THREAD
                         for key in by_id if key not in thread_ids})
        return tuple(selected), excluded

    @staticmethod
    def _items(selected: tuple[str, ...], by_id: dict[str, ConversationEpisode],
               unresolved: tuple[UnresolvedThreadReference, ...]) -> tuple[ContinuityContextItem, ...]:
        result: list[ContinuityContextItem] = []
        source_uncertainty = (
            ContinuityUncertainty.CURRENTNESS_UNCONFIRMED,
            ContinuityUncertainty.SOURCE_IS_CONVERSATION_PROJECTION,
        )
        for episode_id in selected:
            episode = by_id[episode_id]
            fields: list[tuple[ContinuityItemKind, str]] = [
                (ContinuityItemKind.PRIOR_GOAL_TEXT, episode.user_goal),
                (ContinuityItemKind.PRIOR_TOPIC_TEXT, episode.main_topic),
                *((ContinuityItemKind.PRIOR_INSIGHT_TEXT, value) for value in episode.key_insights),
                (ContinuityItemKind.PRIOR_CONCLUSION_TEXT, episode.conclusion),
            ]
            for kind, value in fields:
                if value.strip():
                    result.append(ContinuityContextItem.create(
                        kind=kind,
                        source_episode_id=episode.episode_id,
                        source_ref=episode.source_ref,
                        text=value,
                        uncertainty_codes=source_uncertainty,
                    ))
        for reference in unresolved:
            result.append(ContinuityContextItem.create(
                kind=ContinuityItemKind.UNRESOLVED_CHAT_REFERENCE,
                source_episode_id=reference.source_episode_id,
                source_ref=reference.source_ref,
                text=reference.target_chat_ref,
                uncertainty_codes=(ContinuityUncertainty.SOURCE_IS_CONVERSATION_PROJECTION,
                                   ContinuityUncertainty.TARGET_NOT_LOADED),
            ))
        return tuple(sorted(result, key=lambda item: item.item_id))

    @staticmethod
    def _decisions(by_id: dict[str, ConversationEpisode], selected: tuple[str, ...],
                   excluded: dict[str, ContinuityReason], links: tuple[ThreadLink, ...],
                   unresolved: tuple[UnresolvedThreadReference, ...]) -> tuple[ContinuityDecision, ...]:
        selected_set = set(selected)
        link_reasons: dict[str, set[ContinuityReason]] = {key: set() for key in selected}
        for link in links:
            reason = (ContinuityReason.EXPLICIT_LINK_PRESENT
                      if link.strength is ThreadLinkStrength.EXPLICIT
                      else ContinuityReason.STRUCTURAL_LINK_PRESENT)
            for key in (link.source_episode_id, link.target_episode_id):
                if key in link_reasons:
                    link_reasons[key].add(reason)

        result: list[ContinuityDecision] = []
        for episode_id, episode in by_id.items():
            if episode_id in selected_set:
                reasons = {ContinuityReason.CONNECTED_THREAD, ContinuityReason.PRIOR_TO_CURRENT}
                source_values = (episode.user_goal, episode.main_topic, episode.conclusion, *episode.key_insights)
                reasons.add(ContinuityReason.SOURCE_CONTENT_AVAILABLE
                            if any(value.strip() for value in source_values)
                            else ContinuityReason.EMPTY_SOURCE_CONTENT)
                reasons.update(link_reasons[episode_id])
                disposition = ContinuityDisposition.INCLUDED
            else:
                reasons = {excluded.get(episode_id, ContinuityReason.NOT_IN_CURRENT_THREAD)}
                disposition = ContinuityDisposition.EXCLUDED
            result.append(ContinuityDecision.create(
                subject_kind=ContinuityDecisionSubject.EPISODE,
                subject_ref=episode_id,
                disposition=disposition,
                reason_codes=reasons,
                source_refs=(episode.source_ref,),
            ))
        for reference in unresolved:
            result.append(ContinuityDecision.create(
                subject_kind=ContinuityDecisionSubject.UNRESOLVED_REFERENCE,
                subject_ref=reference.reference_id,
                disposition=ContinuityDisposition.INCLUDED,
                reason_codes=(ContinuityReason.UNRESOLVED_EXPLICIT_REFERENCE,),
                source_refs=(reference.source_ref,),
            ))
        return tuple(sorted(result, key=lambda item: item.decision_id))


__all__ = [
    "CONTEXT_PACK_SCHEMA_VERSION",
    "CONTEXT_POLICY_VERSION",
    "RECEIPT_SCHEMA_VERSION",
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
