# core/embedding_registry.py
# Velantrim ExoCortex — Embedding Registry
# Phase 3A: strict embedding-space identity contract
#
# This remains the single embedding registry owner. The historical
# model_name -> dimension API is preserved for compatibility, while new
# persistent semantic projections must use EmbeddingSpaceDescriptor so that
# equal dimensions can never be mistaken for equal vector spaces.

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)

_SPACE_CONTRACT_VERSION = "embedding-space.v1"
_SPACE_STORAGE_PREFIX = "embedding-space-v1:"


class DimMismatchError(ValueError):
    """An embedding vector has an unexpected or incompatible dimension."""


class UnknownModelError(KeyError):
    """The requested legacy model is not registered in EmbeddingRegistry."""


class EmbeddingSpaceMismatchError(ValueError):
    """Two descriptors identify different embedding spaces."""


class _EmbeddingVectorLike(Protocol):
    """Structural type for vectors whose dimension can be checked via len()."""

    def __len__(self) -> int: ...


def _require_token(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading/trailing whitespace")


@dataclass(frozen=True)
class EmbeddingSpaceDescriptor:
    """Complete deterministic identity of one embedding vector space.

    Dimension is only one axis. Provider/model revision, normalization,
    pooling, metric, chunking and preprocessing are all identity-bearing:
    changing any one of them creates a different space.

    The descriptor is metadata only. It never loads a model, performs I/O,
    grants policy permission, calls a provider, or changes Canon.
    """

    provider_id: str
    model: str
    model_revision: str
    dimension: int
    normalization: str
    pooling: str
    distance_metric: str
    chunker_version: str
    preprocessing_version: str

    def __post_init__(self) -> None:
        for field_name in (
            "provider_id",
            "model",
            "model_revision",
            "normalization",
            "pooling",
            "distance_metric",
            "chunker_version",
            "preprocessing_version",
        ):
            _require_token(field_name, getattr(self, field_name))
        if isinstance(self.dimension, bool) or not isinstance(self.dimension, int):
            raise ValueError("dimension must be an integer")
        if self.dimension <= 0:
            raise ValueError("dimension must be > 0")

    def canonical_payload(self) -> dict[str, str | int]:
        """Canonical serialization payload used to derive the stable ID."""
        return {
            "contract_version": _SPACE_CONTRACT_VERSION,
            "provider_id": self.provider_id,
            "model": self.model,
            "model_revision": self.model_revision,
            "dimension": self.dimension,
            "normalization": self.normalization,
            "pooling": self.pooling,
            "distance_metric": self.distance_metric,
            "chunker_version": self.chunker_version,
            "preprocessing_version": self.preprocessing_version,
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.canonical_payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    @property
    def embedding_space_id(self) -> str:
        """Stable SHA-256 identity; never Python's process-salted hash()."""
        digest = hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()
        return f"{_SPACE_STORAGE_PREFIX}{digest}"

    @property
    def projection_model_name(self) -> str:
        """Axis key for the existing EmbeddingProjectionIdentity.model_name.

        EmbeddingProjectionStore already folds model_name/model_version into
        EmbeddingStore's TEXT primary-key axis. Using the full space ID here
        reuses that owner and schema while making legacy plain model-name rows
        incompatible by construction.
        """
        return self.embedding_space_id

    @property
    def projection_model_version(self) -> str:
        """Fixed version of the descriptor-to-projection binding contract."""
        return _SPACE_CONTRACT_VERSION

    def compatible_with(self, other: EmbeddingSpaceDescriptor) -> bool:
        return isinstance(other, EmbeddingSpaceDescriptor) and self == other


class EmbeddingRegistry:
    """Single registry owner for legacy dimensions and typed spaces.

    The legacy model-name API is intentionally retained because existing code
    and tests use it. New persistent projection code must not infer a complete
    space from a legacy model name/dimension pair: missing identity axes are
    unknown, not permission to reuse a vector.
    """

    _REGISTRY: dict[str, int] = {
        # OpenAI
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        # Nomic
        "nomic-embed-text": 768,
        "nomic-embed-text-v1.5": 768,
        # BGE
        "bge-small-en-v1.5": 384,
        "bge-base-en-v1.5": 768,
        "bge-large-en-v1.5": 1024,
        "bge-m3": 1024,
        # Sentence Transformers
        "all-MiniLM-L6-v2": 384,
        "all-MiniLM-L12-v2": 384,
        "all-mpnet-base-v2": 768,
        # Ollama local
        "mxbai-embed-large": 1024,
        "snowflake-arctic-embed": 1024,
        # Cohere
        "embed-english-v3.0": 1024,
        "embed-multilingual-v3.0": 1024,
    }
    _SPACES: dict[str, EmbeddingSpaceDescriptor] = {}

    @classmethod
    def register(cls, model_name: str, dim: int) -> None:
        """Register/overwrite a legacy model-name -> dimension mapping."""
        _require_token("model_name", model_name)
        if isinstance(dim, bool) or not isinstance(dim, int) or dim <= 0:
            raise ValueError(f"register: dim должен быть > 0, получено {dim}")
        if model_name in cls._REGISTRY and cls._REGISTRY[model_name] != dim:
            logger.warning(
                "EmbeddingRegistry: перезапись '%s' %d → %d",
                model_name,
                cls._REGISTRY[model_name],
                dim,
            )
        cls._REGISTRY[model_name] = dim
        logger.debug("EmbeddingRegistry: зарегистрирована '%s' dim=%d", model_name, dim)

    @classmethod
    def register_space(cls, descriptor: EmbeddingSpaceDescriptor) -> str:
        """Register typed metadata; registration performs no provider/model I/O."""
        if not isinstance(descriptor, EmbeddingSpaceDescriptor):
            raise ValueError("descriptor must be EmbeddingSpaceDescriptor")
        space_id = descriptor.embedding_space_id
        existing = cls._SPACES.get(space_id)
        if existing is not None and existing != descriptor:
            # A SHA-256 collision or a programming error must never silently
            # alias two spaces.
            raise EmbeddingSpaceMismatchError(
                f"embedding space id collision for {space_id}"
            )
        cls._SPACES[space_id] = descriptor
        return space_id

    @classmethod
    def space(cls, embedding_space_id: str) -> EmbeddingSpaceDescriptor:
        _require_token("embedding_space_id", embedding_space_id)
        try:
            return cls._SPACES[embedding_space_id]
        except KeyError as exc:
            raise KeyError(
                f"embedding space is not registered: {embedding_space_id}"
            ) from exc

    @classmethod
    def all_spaces(cls) -> dict[str, EmbeddingSpaceDescriptor]:
        return dict(cls._SPACES)

    @classmethod
    def require_compatible_spaces(
        cls,
        expected: EmbeddingSpaceDescriptor,
        actual: EmbeddingSpaceDescriptor,
    ) -> None:
        if not isinstance(expected, EmbeddingSpaceDescriptor) or not isinstance(
            actual, EmbeddingSpaceDescriptor
        ):
            raise ValueError("expected and actual must be EmbeddingSpaceDescriptor")
        if expected != actual:
            raise EmbeddingSpaceMismatchError(
                "incompatible embedding spaces: "
                f"expected={expected.embedding_space_id}, actual={actual.embedding_space_id}"
            )

    @classmethod
    def validate(cls, embedding: _EmbeddingVectorLike, model_name: str) -> None:
        """Validate a vector against a legacy model dimension."""
        if model_name not in cls._REGISTRY:
            raise UnknownModelError(
                f"EmbeddingRegistry: модель '{model_name}' не зарегистрирована. "
                f"Доступные: {sorted(cls._REGISTRY)}. "
                f"Добавь через EmbeddingRegistry.register(name, dim)."
            )
        expected = cls._REGISTRY[model_name]
        actual = len(embedding)
        if actual != expected:
            raise DimMismatchError(
                f"EmbeddingRegistry: dim mismatch для '{model_name}': "
                f"ожидалось {expected}, получено {actual}."
            )

    @classmethod
    def validate_space_vector(
        cls,
        embedding: _EmbeddingVectorLike,
        descriptor: EmbeddingSpaceDescriptor,
    ) -> None:
        """Validate a vector against an explicit typed space descriptor."""
        if not isinstance(descriptor, EmbeddingSpaceDescriptor):
            raise ValueError("descriptor must be EmbeddingSpaceDescriptor")
        actual = len(embedding)
        if actual != descriptor.dimension:
            raise DimMismatchError(
                "embedding-space dim mismatch: "
                f"space={descriptor.embedding_space_id}, "
                f"expected={descriptor.dimension}, actual={actual}"
            )

    @staticmethod
    def validate_pair_dimensions(
        left: _EmbeddingVectorLike,
        right: _EmbeddingVectorLike,
        *,
        expected_dimension: int | None = None,
    ) -> None:
        """Fail closed before any similarity scoring can truncate vectors."""
        left_dim = len(left)
        right_dim = len(right)
        if left_dim != right_dim:
            raise DimMismatchError(
                f"embedding pair dim mismatch: left={left_dim}, right={right_dim}"
            )
        if expected_dimension is not None:
            if isinstance(expected_dimension, bool) or not isinstance(expected_dimension, int):
                raise ValueError("expected_dimension must be an integer")
            if expected_dimension <= 0:
                raise ValueError("expected_dimension must be > 0")
            if left_dim != expected_dimension:
                raise DimMismatchError(
                    "embedding pair does not match declared space dimension: "
                    f"expected={expected_dimension}, actual={left_dim}"
                )

    @classmethod
    def dim(cls, model_name: str) -> int:
        if model_name not in cls._REGISTRY:
            raise UnknownModelError(
                f"EmbeddingRegistry: модель '{model_name}' не зарегистрирована."
            )
        return cls._REGISTRY[model_name]

    @classmethod
    def is_registered(cls, model_name: str) -> bool:
        return model_name in cls._REGISTRY

    @classmethod
    def all_models(cls) -> dict[str, int]:
        return dict(cls._REGISTRY)

    @classmethod
    def validate_safe(
        cls, embedding: _EmbeddingVectorLike, model_name: str
    ) -> str | None:
        try:
            cls.validate(embedding, model_name)
            return None
        except (UnknownModelError, DimMismatchError) as exc:
            return str(exc)


__all__ = [
    "DimMismatchError",
    "EmbeddingRegistry",
    "EmbeddingSpaceDescriptor",
    "EmbeddingSpaceMismatchError",
    "UnknownModelError",
]
