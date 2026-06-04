"""
Tests for core/embedding_registry.py — Embedding Registry.

Covers:
  - validate() — правильная размерность проходит
  - validate() — неправильная размерность → DimMismatchError
  - validate() — незарегистрированная модель → UnknownModelError
  - register() — добавить новую модель
  - register() — перезаписать существующую с предупреждением
  - dim() — получить ожидаемую размерность
  - is_registered() — проверка без исключения
  - all_models() — возвращает копию реестра
  - validate_safe() — мягкая версия без исключений
  - Реестр содержит ожидаемые baseline-модели
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.embedding_registry import (
    DimMismatchError,
    EmbeddingRegistry,
    UnknownModelError,
)

# ── validate() ────────────────────────────────────────────────────────────────

def test_validate_correct_dim_passes():
    """Правильная размерность → нет исключения."""
    embedding = [0.1] * 768
    EmbeddingRegistry.validate(embedding, "nomic-embed-text")  # ожидается 768


def test_validate_wrong_dim_raises_dim_mismatch():
    """Неправильная размерность → DimMismatchError."""
    embedding = [0.1] * 1024  # не 768
    with pytest.raises(DimMismatchError, match="dim mismatch"):
        EmbeddingRegistry.validate(embedding, "nomic-embed-text")


def test_validate_unknown_model_raises_unknown_model():
    """Незарегистрированная модель → UnknownModelError."""
    embedding = [0.1] * 512
    with pytest.raises(UnknownModelError, match="не зарегистрирована"):
        EmbeddingRegistry.validate(embedding, "nonexistent-model-xyz")


def test_validate_openai_3_small():
    """text-embedding-3-small: 1536."""
    emb = [0.0] * 1536
    EmbeddingRegistry.validate(emb, "text-embedding-3-small")


def test_validate_bge_large():
    """bge-large-en-v1.5: 1024."""
    emb = [0.0] * 1024
    EmbeddingRegistry.validate(emb, "bge-large-en-v1.5")


def test_validate_all_minilm():
    """all-MiniLM-L6-v2: 384."""
    emb = [0.0] * 384
    EmbeddingRegistry.validate(emb, "all-MiniLM-L6-v2")


# ── register() ───────────────────────────────────────────────────────────────

def test_register_new_model():
    """Регистрация новой модели — после этого validate() работает."""
    EmbeddingRegistry.register("test-custom-model-42", 512)
    assert EmbeddingRegistry.is_registered("test-custom-model-42")
    assert EmbeddingRegistry.dim("test-custom-model-42") == 512

    # Валидация работает
    EmbeddingRegistry.validate([0.0] * 512, "test-custom-model-42")


def test_register_overwrite_logs_but_succeeds():
    """Перезапись существующей модели не падает."""
    EmbeddingRegistry.register("test-overwrite-model", 256)
    EmbeddingRegistry.register("test-overwrite-model", 512)  # перезапись
    assert EmbeddingRegistry.dim("test-overwrite-model") == 512


def test_register_invalid_dim_raises():
    """Нулевая или отрицательная размерность → ValueError."""
    with pytest.raises(ValueError):
        EmbeddingRegistry.register("bad-model", 0)
    with pytest.raises(ValueError):
        EmbeddingRegistry.register("bad-model", -1)


# ── dim() ─────────────────────────────────────────────────────────────────────

def test_dim_known_model():
    assert EmbeddingRegistry.dim("all-MiniLM-L6-v2") == 384
    assert EmbeddingRegistry.dim("text-embedding-ada-002") == 1536
    assert EmbeddingRegistry.dim("bge-m3") == 1024


def test_dim_unknown_raises():
    with pytest.raises(UnknownModelError):
        EmbeddingRegistry.dim("definitely-not-a-real-model")


# ── is_registered() ──────────────────────────────────────────────────────────

def test_is_registered_known():
    assert EmbeddingRegistry.is_registered("nomic-embed-text") is True


def test_is_registered_unknown():
    assert EmbeddingRegistry.is_registered("definitely-not-registered") is False


# ── all_models() ─────────────────────────────────────────────────────────────

def test_all_models_returns_dict():
    models = EmbeddingRegistry.all_models()
    assert isinstance(models, dict)
    assert len(models) > 0
    assert "nomic-embed-text" in models


def test_all_models_returns_copy():
    """Мутация возвращённого словаря не меняет реестр."""
    models = EmbeddingRegistry.all_models()
    models["injected-model"] = 999
    assert not EmbeddingRegistry.is_registered("injected-model")


# ── validate_safe() ──────────────────────────────────────────────────────────

def test_validate_safe_ok_returns_none():
    """Мягкая валидация — None означает всё хорошо."""
    result = EmbeddingRegistry.validate_safe([0.0] * 768, "nomic-embed-text")
    assert result is None


def test_validate_safe_dim_mismatch_returns_string():
    """Мягкая валидация — строка с описанием ошибки."""
    result = EmbeddingRegistry.validate_safe([0.0] * 512, "nomic-embed-text")
    assert isinstance(result, str)
    assert "dim mismatch" in result.lower() or "mismatch" in result


def test_validate_safe_unknown_model_returns_string():
    """Мягкая валидация — строка для незарегистрированной модели."""
    result = EmbeddingRegistry.validate_safe([0.0] * 512, "unknown-xyz")
    assert isinstance(result, str)


# ── Baseline реестр ──────────────────────────────────────────────────────────

def test_baseline_registry_contains_expected_models():
    """Реестр содержит все baseline модели которые будут использоваться."""
    required = {
        "nomic-embed-text",
        "bge-large-en-v1.5",
        "all-MiniLM-L6-v2",
        "text-embedding-3-small",
        "text-embedding-ada-002",
    }
    registered = set(EmbeddingRegistry.all_models().keys())
    missing = required - registered
    assert not missing, f"Эти модели должны быть в реестре: {missing}"
