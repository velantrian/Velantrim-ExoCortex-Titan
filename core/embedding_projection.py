# core/embedding_projection.py — Velantrim Titan
# PR-ARM-02 (issue #92): rebuildable embedding projection contract
# =================================================================
#
# Makes the dense-embedding index an explicit, verifiable, rebuildable
# PROJECTION over canonical facts — not a hidden process cache. This module
# defines:
#
#   1. EmbeddingProjectionIdentity — what a vector is FOR (record + content +
#      model + schema), serializable, comparable without loading a model.
#   2. ProjectionState — a pure classification of a stored identity against
#      an expected one: missing / fresh / stale_content / stale_model /
#      stale_projection_version / invalid. Never mutates anything.
#   3. EmbeddingProjectionStore — a thin adapter over the EXISTING,
#      already-erasure-wired core.embedding_store.EmbeddingStore. No new
#      database, no new schema: different (model_name, model_version,
#      projection_version) axes are folded into EmbeddingStore's existing
#      `model_name` column as a composite storage key, so incompatible
#      axes physically cannot share a row, and reindex/invalidation hooks
#      that are bounded and explicit (never an unbounded background walk).
#   4. resolve_or_fallback() — the read-only decision a retrieval caller
#      makes: use the projection, or fall back to lexical/BM25. It never
#      reindexes on its own; detecting staleness and fixing it are two
#      separate, explicit actions.
#
# Relationship to core.hybrid_retriever.DenseRetriever (PR #91/#95/#99):
# DenseRetriever recomputes and caches embeddings in-process, per query,
# and is already correct by construction (its cache key is
# model_name+fact_id+sha256(claim), so it never serves stale vectors —
# that defect was fixed in PR #99). This module is NOT a rewrite of that
# fix; it is the contract for a *persistent, precomputed* projection (the
# kind core.embedding_store.EmbeddingStore exists for, per its own
# docstring, but that nothing currently populates ahead of query time).
# Wiring a live retrieval path to prefer a persistent projection over
# DenseRetriever's on-demand computation is left for a follow-up — this PR
# ships the identity/staleness/reindex/fallback contract itself, fully
# tested, so that a future ingest/indexing pipeline has a correct contract
# to write against from day one.
#
# Canonical boundary (issue #92 non-negotiables):
#   - never touches core.memory / Canon;
#   - never promotes epistemic state;
#   - read-side operations (check_state, list_stale_or_missing,
#     resolve_or_fallback) never mutate anything;
#   - write-side operations (store, rebuild, rebuild_all, invalidate_*)
#     only ever touch the derived projection table, never Canon;
#   - erasure/policy revocation of a record invalidates its projection
#     for free, because this module's storage key shares the exact same
#     (node_id, model_name) table erasure_coordinator already purges.

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.embedding_store import EmbeddingStore

logger = logging.getLogger(__name__)

_STORAGE_KEY_MODEL_SEP = "@"
_STORAGE_KEY_VERSION_SEP = "#"


class CorruptedProjectionMetadataError(ValueError):
    """Raised internally when stored projection metadata can't be parsed
    (e.g. a malformed composite storage key). Always caught within this
    module and mapped to ProjectionState.INVALID — never escapes to a
    caller as a crash."""


def compute_content_hash(claim: str) -> str:
    """SHA256 of exactly the text an embedding is computed from.

    Deliberately narrower than core.fact_integrity.compute_content_checksum,
    which also folds in source/confidence/epistemic_state for anti-
    reconsolidation detection. An embedding depends only on this text, so
    reusing that broader checksum here would flag STALE_CONTENT on a
    confidence-only or epistemic-state-only edit that never touched the
    claim — spurious reindex churn. Matches the hashing already used for
    DenseRetriever's in-process cache key (core/hybrid_retriever.py, PR #99).
    """
    return hashlib.sha256((claim or "").encode("utf-8")).hexdigest()


class ProjectionState(str, Enum):
    MISSING = "missing"
    FRESH = "fresh"
    STALE_CONTENT = "stale_content"
    STALE_MODEL = "stale_model"
    STALE_PROJECTION_VERSION = "stale_projection_version"
    INVALID = "invalid"


@dataclass(frozen=True)
class EmbeddingProjectionIdentity:
    """What a stored (or expected) embedding vector is FOR.

    Deterministic and serializable; comparing two identities never loads an
    embedding model and never uses Python's built-in `hash()` (which is
    salted per-process for str/bytes since PEP 456 and is not a stable,
    cross-process identity — dataclass field-by-field `__eq__` is used for
    comparison instead, and `storage_key()` below uses plain string
    concatenation, not `hash()`).
    """

    record_id: str
    content_hash: str
    model_name: str
    model_version: str
    projection_version: str = "1"

    def to_dict(self) -> dict[str, str]:
        return {
            "record_id": self.record_id,
            "content_hash": self.content_hash,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "projection_version": self.projection_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EmbeddingProjectionIdentity:
        """Strict: raises ValueError/KeyError on missing or malformed
        fields. Callers reading untrusted/stored metadata should catch and
        treat the failure as ProjectionState.INVALID (see
        EmbeddingProjectionStore._parse_storage_key, the only internal
        caller that does this from potentially-corrupted storage)."""
        return cls(
            record_id=str(data["record_id"]),
            content_hash=str(data["content_hash"]),
            model_name=str(data["model_name"]),
            model_version=str(data["model_version"]),
            projection_version=str(data.get("projection_version", "1")),
        )

    def storage_key(self) -> str:
        """Composite key used as EmbeddingStore's `model_name` column.

        Folds model identity + model version + projection schema version
        into one string, so a lookup under the wrong axis simply misses
        (never silently returns a different axis's vector). The identity's
        own `model_name` field stays a plain, un-mangled string for
        EmbeddingRegistry lookups; only this derived key touches storage.
        """
        if _STORAGE_KEY_MODEL_SEP in self.model_name or _STORAGE_KEY_VERSION_SEP in self.model_name:
            raise ValueError(
                f"model_name {self.model_name!r} contains a storage-key separator "
                f"({_STORAGE_KEY_MODEL_SEP!r}/{_STORAGE_KEY_VERSION_SEP!r})"
            )
        return (
            f"{self.model_name}{_STORAGE_KEY_MODEL_SEP}{self.model_version}"
            f"{_STORAGE_KEY_VERSION_SEP}{self.projection_version}"
        )


def classify_state(
    expected: EmbeddingProjectionIdentity,
    stored: EmbeddingProjectionIdentity | None,
) -> ProjectionState:
    """Pure function: never touches storage, never raises, never mutates
    anything. `stored=None` means nothing at all is projected for this
    record. When more than one axis differs simultaneously, priority is:
    a record_id mismatch is INVALID (storage corruption/misfile — this
    should be structurally impossible via EmbeddingProjectionStore, which
    always looks up by record_id, but is checked defensively); a model
    (name or version) mismatch is STALE_MODEL, since vectors from a
    different model can never be reused regardless of content; a
    projection-schema mismatch is STALE_PROJECTION_VERSION; a content
    mismatch is STALE_CONTENT; otherwise FRESH.
    """
    if stored is None:
        return ProjectionState.MISSING
    if stored.record_id != expected.record_id:
        return ProjectionState.INVALID
    if stored.model_name != expected.model_name or stored.model_version != expected.model_version:
        return ProjectionState.STALE_MODEL
    if stored.projection_version != expected.projection_version:
        return ProjectionState.STALE_PROJECTION_VERSION
    if stored.content_hash != expected.content_hash:
        return ProjectionState.STALE_CONTENT
    return ProjectionState.FRESH


@dataclass(frozen=True)
class ReindexReport:
    """Result of a bounded rebuild() call. Every field lists record_ids."""

    rebuilt: tuple[str, ...] = ()
    skipped_fresh: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()


class EmbeddingProjectionStore:
    """Derived-projection adapter over the existing, persistent
    core.embedding_store.EmbeddingStore.

    Not Canon: every row here is fully rebuildable from canonical facts
    plus a declared EmbeddingProjectionIdentity. Erasure compatibility is
    free — core.erasure_coordinator already calls
    EmbeddingStore.purge_node(fact_id) on exactly the table this class
    reads and writes, so a record erased/revoked through the existing
    coordinator has its projection removed with zero additional wiring.
    """

    def __init__(self, backing: EmbeddingStore | None = None) -> None:
        # core.embedding_store imports numpy at module level — an optional
        # dependency not every install needs (see
        # core.erasure_coordinator._get_embeddings for the same deferral).
        # Constructing this class must never raise just because numpy/
        # embedding_store isn't installed here: `available` reports it,
        # and every method below degrades to an honest no-op/miss instead.
        self._backing = backing
        self._unavailable_reason: str | None = None
        if self._backing is None:
            try:
                from core.embedding_store import get_embedding_store
                self._backing = get_embedding_store()
            except Exception as exc:  # noqa: BLE001 — optional dependency
                self._unavailable_reason = str(exc)
                logger.warning(
                    "EmbeddingProjectionStore: persistent backing unavailable (%s); "
                    "every lookup will report MISSING and every write will no-op.",
                    exc,
                )

    @property
    def available(self) -> bool:
        """False when the persistent embedding backend (numpy/
        core.embedding_store) could not be constructed — e.g. numpy isn't
        installed in this deployment. Callers combine this with their own
        model-availability check to decide `embeddings_available` for
        resolve_or_fallback()."""
        return self._backing is not None

    # ── read (never mutates) ────────────────────────────────────────────

    def _parse_storage_key(self, storage_key: str) -> tuple[str, str, str]:
        try:
            model_name, rest = storage_key.split(_STORAGE_KEY_MODEL_SEP, 1)
            model_version, projection_version = rest.split(_STORAGE_KEY_VERSION_SEP, 1)
        except ValueError as exc:
            raise CorruptedProjectionMetadataError(
                f"malformed projection storage key: {storage_key!r}"
            ) from exc
        return model_name, model_version, projection_version

    def get_stored_identity(self, record_id: str) -> EmbeddingProjectionIdentity | None:
        """Whatever axis (model/version/projection) is currently stored for
        `record_id`, if any. Returns None if nothing at all is stored (this
        also covers the persistent backend being unavailable — see
        `available` — since there is then structurally nothing to read).
        Raises CorruptedProjectionMetadataError if something is stored but
        can't be parsed as a valid identity — callers going through
        `check_state()` never see this; it is mapped to
        ProjectionState.INVALID there."""
        if self._backing is None:
            return None
        storage_key = self._backing.get_stored_model_name(record_id)
        if storage_key is None:
            return None
        model_name, model_version, projection_version = self._parse_storage_key(storage_key)
        loaded = self._backing.load_with_content_hash(record_id, storage_key)
        if loaded is None:
            raise CorruptedProjectionMetadataError(
                f"storage key present but row unreadable for {record_id!r}"
            )
        _, content_hash = loaded
        if not content_hash:
            raise CorruptedProjectionMetadataError(
                f"projection row for {record_id!r} has no content_hash"
            )
        return EmbeddingProjectionIdentity(
            record_id=record_id,
            content_hash=content_hash,
            model_name=model_name,
            model_version=model_version,
            projection_version=projection_version,
        )

    def check_state(self, expected: EmbeddingProjectionIdentity) -> ProjectionState:
        """Read-only. Never reindexes, never writes, never raises."""
        try:
            stored = self.get_stored_identity(expected.record_id)
        except CorruptedProjectionMetadataError as exc:
            logger.debug("embedding_projection: corrupted metadata for %s: %s",
                         expected.record_id, exc)
            return ProjectionState.INVALID
        return classify_state(expected, stored)

    def get_vector_if_fresh(self, expected: EmbeddingProjectionIdentity) -> Any | None:
        """Returns the stored vector only if its identity is exactly FRESH
        against `expected`; otherwise None. Read-only."""
        if self._backing is None:
            return None
        if self.check_state(expected) != ProjectionState.FRESH:
            return None
        loaded = self._backing.load_with_content_hash(expected.record_id, expected.storage_key())
        return loaded[0] if loaded is not None else None

    def list_stale_or_missing(
        self, expected: Sequence[EmbeddingProjectionIdentity]
    ) -> list[tuple[EmbeddingProjectionIdentity, ProjectionState]]:
        """Bounded, read-only classification of exactly the given
        identities. Never mutates anything — detecting staleness must not
        silently trigger a rebuild; that is always a separate, explicit
        call to rebuild()/rebuild_all()."""
        out: list[tuple[EmbeddingProjectionIdentity, ProjectionState]] = []
        for ident in expected:
            state = self.check_state(ident)
            if state != ProjectionState.FRESH:
                out.append((ident, state))
        return out

    # ── write (only ever touches the derived projection table) ─────────

    def store(self, identity: EmbeddingProjectionIdentity, vector: Any) -> bool:
        if self._backing is None:
            return False
        return self._backing.store(
            identity.record_id,
            vector,
            model_name=identity.storage_key(),
            content_hash=identity.content_hash,
        )

    def rebuild(
        self,
        identities_and_texts: Sequence[tuple[EmbeddingProjectionIdentity, str]],
        encode_fn: Callable[[list[str]], Sequence[Any]],
    ) -> ReindexReport:
        """Explicitly rebuild exactly the given (identity, text) pairs.

        Bounded by construction: the caller decides the batch (typically
        the output of list_stale_or_missing()); this never walks the whole
        corpus on its own. Already-fresh identities are skipped without
        calling encode_fn. Deterministic: rebuilding the same
        (identity, text) pairs against the same encode_fn twice produces
        the same stored state both times (idempotent — the second call
        finds everything already FRESH and skips it).
        """
        rebuilt: list[str] = []
        skipped: list[str] = []
        failed: list[str] = []
        to_encode: list[tuple[EmbeddingProjectionIdentity, str]] = []
        for ident, text in identities_and_texts:
            if self.check_state(ident) == ProjectionState.FRESH:
                skipped.append(ident.record_id)
            else:
                to_encode.append((ident, text))

        if to_encode:
            try:
                vectors = list(encode_fn([text for _, text in to_encode]))
            except Exception as exc:  # noqa: BLE001 — a failed batch fails every
                # record in it explicitly, rather than raising out of a
                # bounded, supposedly-never-crashing reindex call.
                logger.warning("embedding_projection: rebuild encode_fn failed: %s", exc)
                failed.extend(ident.record_id for ident, _ in to_encode)
                vectors = []
            for (ident, _text), vec in zip(to_encode, vectors):
                if self.store(ident, vec):
                    rebuilt.append(ident.record_id)
                else:
                    failed.append(ident.record_id)
            # encode_fn returned fewer vectors than requested (short batch) —
            # every un-paired identity explicitly fails, not silently drops.
            if len(vectors) < len(to_encode):
                failed.extend(ident.record_id for ident, _ in to_encode[len(vectors):])

        return ReindexReport(
            rebuilt=tuple(rebuilt), skipped_fresh=tuple(skipped), failed=tuple(failed)
        )

    def rebuild_all(
        self,
        records: Iterable[tuple[str, str]],
        *,
        model_name: str,
        model_version: str,
        projection_version: str,
        encode_fn: Callable[[list[str]], Sequence[Any]],
    ) -> ReindexReport:
        """Full rebuild over an explicitly-provided (record_id, claim)
        iterable — e.g. the caller's own bounded read from core.memory.
        Bounded by whatever the caller passes in; this function itself
        never scans or schedules anything on its own."""
        pairs = [
            (
                EmbeddingProjectionIdentity(
                    record_id=record_id,
                    content_hash=compute_content_hash(claim),
                    model_name=model_name,
                    model_version=model_version,
                    projection_version=projection_version,
                ),
                claim,
            )
            for record_id, claim in records
        ]
        return self.rebuild(pairs, encode_fn)

    def invalidate_record(self, record_id: str) -> int:
        """Drop every stored axis for `record_id` (all models/versions).
        Same call erasure_coordinator already makes via the shared
        EmbeddingStore — exposed here so this module's own callers/tests
        don't need to reach into core.embedding_store directly."""
        if self._backing is None:
            return 0
        return self._backing.purge_node(record_id)

    def invalidate_model(
        self, model_name: str, model_version: str, projection_version: str = "1"
    ) -> int:
        """Drop every record's projection under this exact
        (model_name, model_version, projection_version) axis — e.g. after
        a deliberate model upgrade, to force every record back to
        MISSING/STALE_MODEL rather than leaving unreachable rows behind."""
        if self._backing is None:
            return 0
        probe = EmbeddingProjectionIdentity(
            record_id="", content_hash="", model_name=model_name,
            model_version=model_version, projection_version=projection_version,
        )
        return self._backing.invalidate_model(probe.storage_key())


def resolve_or_fallback(
    identities: Sequence[EmbeddingProjectionIdentity],
    store: EmbeddingProjectionStore,
    *,
    embeddings_available: bool,
) -> tuple[str, dict[str, Any] | None]:
    """The read-only decision a retrieval caller makes: use the persistent
    dense projection, or fall back to lexical/BM25.

    Returns ("dense", {record_id: vector}) only when embeddings are
    available AND every given identity is exactly FRESH. Returns
    ("lexical_fallback", None) for any other reason: embeddings package/
    model unavailable, any identity missing, stale (on any axis), or
    invalid. Never reindexes and never writes — detecting a reason to fall
    back is not the same action as fixing it; fixing it is always a
    separate, explicit rebuild()/rebuild_all() call.
    """
    if not embeddings_available:
        return "lexical_fallback", None
    vectors: dict[str, Any] = {}
    for ident in identities:
        vec = store.get_vector_if_fresh(ident)
        if vec is None:
            return "lexical_fallback", None
        vectors[ident.record_id] = vec
    return "dense", vectors


__all__ = [
    "CorruptedProjectionMetadataError",
    "EmbeddingProjectionIdentity",
    "EmbeddingProjectionStore",
    "ProjectionState",
    "ReindexReport",
    "classify_state",
    "compute_content_hash",
    "resolve_or_fallback",
]
