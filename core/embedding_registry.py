# core/embedding_registry.py
# Velantrim ExoCortex — Embedding Registry
# v1.0.0
#
# Назначение: централизованный реестр поддерживаемых embedding-моделей
# и их размерностей. Предотвращает тихую ошибку dim mismatch.
#
# Проблема которую решает:
#   numpy.dot() с векторами разных размерностей (например 1024 vs 1536)
#   НЕ выбрасывает исключение — возвращает математически некорректный результат.
#   Этот баг был найден в HYPERIA FractalMemory v5.25 (P-08) и является
#   системной проблемой любого embedding-стека.
#
# Правило: при добавлении новой embedding-модели — СНАЧАЛА register() здесь,
#          ЗАТЕМ использовать в коде. Не хардкодить dim в коде.
#
# Источник идеи: HYPERIA v5.25 §EmbeddingRegistry (core/embedding_registry.py).
# Актуально начиная с Sprint 2a (vector retrieval).

import logging

logger = logging.getLogger(__name__)


class DimMismatchError(ValueError):
    """Embedding вектор имеет неожиданную размерность для указанной модели."""
    pass


class UnknownModelError(KeyError):
    """Модель не зарегистрирована в EmbeddingRegistry."""
    pass


class EmbeddingRegistry:
    """
    Реестр поддерживаемых embedding-моделей и их ожидаемых размерностей.

    Использование:
        # Валидация перед использованием:
        EmbeddingRegistry.validate(embedding, "nomic-embed-text")

        # Регистрация новой модели:
        EmbeddingRegistry.register("my-custom-model", 768)

        # Получить ожидаемую размерность:
        dim = EmbeddingRegistry.dim("bge-large-en-v1.5")  # → 1024
    """

    # ── Известные модели и их размерности ───────────────────────────────────
    # Расширять здесь при добавлении новой embedding-модели.
    # НЕ хардкодить размерности в коде вне этого реестра.
    _REGISTRY: dict[str, int] = {
        # OpenAI
        "text-embedding-ada-002":       1536,
        "text-embedding-3-small":       1536,
        "text-embedding-3-large":       3072,

        # Nomic (open source, Apache 2.0)
        "nomic-embed-text":             768,
        "nomic-embed-text-v1.5":        768,

        # BGE (BAAI General Embedding)
        "bge-small-en-v1.5":            384,
        "bge-base-en-v1.5":             768,
        "bge-large-en-v1.5":            1024,
        "bge-m3":                       1024,  # multilingual

        # Sentence Transformers
        "all-MiniLM-L6-v2":             384,
        "all-MiniLM-L12-v2":            384,
        "all-mpnet-base-v2":            768,

        # Ollama local (edge/offline)
        "mxbai-embed-large":            1024,
        "snowflake-arctic-embed":       1024,

        # Cohere
        "embed-english-v3.0":           1024,
        "embed-multilingual-v3.0":      1024,
    }

    @classmethod
    def register(cls, model_name: str, dim: int) -> None:
        """
        Зарегистрировать новую модель.
        Если модель уже есть — перезаписать (для корректировок).
        """
        if dim <= 0:
            raise ValueError(f"register: dim должен быть > 0, получено {dim}")
        if model_name in cls._REGISTRY and cls._REGISTRY[model_name] != dim:
            logger.warning(
                "EmbeddingRegistry: перезапись '%s' %d → %d",
                model_name, cls._REGISTRY[model_name], dim,
            )
        cls._REGISTRY[model_name] = dim
        logger.debug("EmbeddingRegistry: зарегистрирована '%s' dim=%d", model_name, dim)

    @classmethod
    def validate(cls, embedding: list[float], model_name: str) -> None:
        """
        Проверить что размерность embedding соответствует ожидаемой для модели.

        Raises:
            UnknownModelError: модель не зарегистрирована.
            DimMismatchError:  размерность не совпадает с ожидаемой.

        Использовать ПЕРЕД любым numpy.dot() или cosine_similarity().
        """
        if model_name not in cls._REGISTRY:
            raise UnknownModelError(
                f"EmbeddingRegistry: модель '{model_name}' не зарегистрирована. "
                f"Доступные: {sorted(cls._REGISTRY)}. "
                f"Добавь через EmbeddingRegistry.register(name, dim)."
            )
        expected = cls._REGISTRY[model_name]
        actual   = len(embedding)
        if actual != expected:
            raise DimMismatchError(
                f"EmbeddingRegistry: dim mismatch для '{model_name}': "
                f"ожидалось {expected}, получено {actual}. "
                f"numpy.dot с разными dim не даёт ошибку — только неверный результат!"
            )

    @classmethod
    def dim(cls, model_name: str) -> int:
        """
        Получить ожидаемую размерность для модели.

        Raises:
            UnknownModelError: если модель не зарегистрирована.
        """
        if model_name not in cls._REGISTRY:
            raise UnknownModelError(
                f"EmbeddingRegistry: модель '{model_name}' не зарегистрирована."
            )
        return cls._REGISTRY[model_name]

    @classmethod
    def is_registered(cls, model_name: str) -> bool:
        """Проверить зарегистрирована ли модель (без исключения)."""
        return model_name in cls._REGISTRY

    @classmethod
    def all_models(cls) -> dict[str, int]:
        """Вернуть копию реестра {model_name: dim}."""
        return dict(cls._REGISTRY)

    @classmethod
    def validate_safe(
        cls, embedding: list[float], model_name: str
    ) -> str | None:
        """
        Мягкая валидация — возвращает строку с ошибкой или None если всё ок.
        Используй когда нужно логировать а не падать.
        """
        try:
            cls.validate(embedding, model_name)
            return None
        except (UnknownModelError, DimMismatchError) as e:
            return str(e)
