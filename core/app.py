"""
💉 core/app.py — VelantrimApp: DI-фундамент V8.7 (Titan)

Убирает глобальные синглтоны (_GLOBAL_STORE, _HYBRID_RETRIEVER, _backend_singleton, …)
и заменяет их на явный application-объект, который можно создавать per-test, per-env.

Обратная совместимость:
  - Модуль экспортирует get_app() → возвращает глобальный экземпляр (поведение как раньше).
  - В тестах: `app = VelantrimApp(config=test_config)` → полная изоляция.
  - В production: `app = VelantrimApp()` → читает .env через get_config().

Инварианты:
  - Каждый компонент получает ссылку на `app`, а не импортирует глобал.
  - Hot-reload: `app.reconfigure(new_config)` пересоздаёт компоненты без перезапуска процесса.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, TypeVar

from core.feature_config import FeatureConfig, get_config as _get_global_config

logger = logging.getLogger("velantrim.app")

# ─── Переопределяемые компоненты (протоколы для DI) ──────────────────────────

T = TypeVar("T")

class _Lazy:
    """Отложенная инициализация компонента."""
    def __init__(self, factory):
        self._factory = factory
        self._instance: Any = None

    def __call__(self) -> Any:
        if self._instance is None:
            self._instance = self._factory()
        return self._instance


@dataclass
class VelantrimApp:
    """
    Центральный application-объект Velantrim.

    Создавай через конструктор для тестов; get_app() — для production.
    """

    config: FeatureConfig = field(default_factory=_get_global_config)
    _components: Dict[str, Any] = field(default_factory=dict)
    _lazy: Dict[str, _Lazy] = field(default_factory=dict)

    # ── Хранилище (L0–L3) ─────────────────────────────────────────────────

    @property
    def store(self):
        """SQLiteGraphStore — основной store фактов."""
        return self._lazy["store"]()

    @store.setter
    def store(self, value):            # тесты могут подменить
        self._components["store"] = value

    # ── Retrieve ──────────────────────────────────────────────────────────

    @property
    def hybrid_retriever(self):
        return self._lazy.get("hybrid_retriever", lambda: None)()

    @property
    def ngram_index(self):
        return self._lazy.get("ngram_index", lambda: None)()

    # ── Causal Graph ──────────────────────────────────────────────────────

    @property
    def causal_graph(self):
        return self._lazy.get("causal_graph", lambda: None)()

    # ── Event Bus ─────────────────────────────────────────────────────────

    @property
    def event_bus(self):
        return self._lazy.get("event_bus", lambda: None)()

    # ── Cognitive Runtime ─────────────────────────────────────────────────

    @property
    def cognitive_runtime(self):
        return self._lazy.get("cognitive_runtime", lambda: None)()

    # ── Прочее ────────────────────────────────────────────────────────────

    @property
    def graph_store_backend(self):
        return self._lazy.get("graph_store_backend", lambda: None)()

    @property
    def essence_layer(self):
        return self._lazy.get("essence", lambda: None)()

    @property
    def working_notebook(self):
        return self._lazy.get("working_notebook", lambda: None)()

    @property
    def consolidation_engine(self):
        return self._lazy.get("consolidation_engine", lambda: None)()

    @property
    def salience_detector(self):
        return self._lazy.get("salience", lambda: None)()

    # ── Методы DI ────────────────────────────────────────────────────────

    def register(self, name: str, factory):
        """Зарегистрировать компонент (вызывается при старте)."""
        self._lazy[name] = _Lazy(factory)

    def register_instance(self, name: str, instance: Any):
        """Зарегистрировать уже созданный экземпляр (для тестов)."""
        self._components[name] = instance
        self._lazy[name] = _Lazy(lambda: instance)

    def reconfigure(self, config: FeatureConfig) -> None:
        """Горячая перезагрузка конфигурации."""
        self.config = config
        self._components.clear()
        self._lazy.clear()
        self._init_components()
        logger.info("Конфигурация перезагружена")

    def _init_components(self) -> None:
        """Инициализировать все lazy-компоненты (вызывается при старте)."""
        # FIX #10 (Claude audit): create_store не существует → используем make_store
        from core.memory import make_store

        cfg = self.config.app

        # Store
        self._lazy["store"] = _Lazy(lambda: make_store(
            db_path=self.config.db.sqlite_graph_path,
        ))

        # NGram index
        # NGram index — always created (no feature flag in Claude's config)
        self._lazy["ngram_index"] = _Lazy(lambda: _create_ngram())

        # Hybrid retriever — lazy, соберётся при первом retrieve
        self._lazy["hybrid_retriever"] = _Lazy(lambda: _create_hybrid_retriever(self.store))

        # Event bus
        if cfg.enable_event_bus:
            self._lazy["event_bus"] = _Lazy(lambda: _create_event_bus())

        # Causal graph
        if cfg.enable_causal_graph:
            self._lazy["causal_graph"] = _Lazy(lambda: _create_causal_graph())

        # Graph store backend (для Etir, ImmutableCore)
        self._lazy["graph_store_backend"] = _Lazy(lambda: _create_graph_backend())

        # Cognitive runtime (V10)
        if cfg.enable_cognitive_runtime:
            self._lazy["cognitive_runtime"] = _Lazy(lambda: _create_cognitive_runtime())

        # Essence layer
        self._lazy["essence"] = _Lazy(lambda: _create_essence_layer())

        # Working notebook
        self._lazy["working_notebook"] = _Lazy(lambda: _create_working_notebook())

        # Consolidation engine
        self._lazy["consolidation_engine"] = _Lazy(lambda: _create_consolidation(self.store))

        # Salience detector
        self._lazy["salience"] = _Lazy(lambda: _create_salience())

        logger.debug("Компоненты зарегистрированы: %s", list(self._lazy.keys()))

    def health(self) -> Dict[str, Any]:
        """
        Быстрая проверка здоровья.

        FIX P1 (v8.7 audit): self.store обращается к _lazy["store"](), что падает
        с KeyError если _init_components() не вызвана (пустой словарь).
        Теперь безопасно проверяет наличие ключа до обращения.
        """
        store_ok = False
        try:
            if "store" in self._lazy:
                store_ok = self._lazy["store"]() is not None
        except Exception:
            pass
        return {
            "store": store_ok,
            "config.version": getattr(self.config, "version", "unknown"),
        }


# ─── Вспомогательные фабрики ─────────────────────────────────────────────────

def _create_ngram():
    from core.ngram_index import NGramIndex
    return NGramIndex()


def _create_hybrid_retriever(store):
    from core.hybrid_retriever import HybridRetriever
    facts = store.get_all_facts() or []
    return HybridRetriever(facts)


def _create_event_bus():
    from core.event_bus import EventBus
    return EventBus()


def _create_causal_graph():
    from core.pipeline import _get_causal_graph

    graph = _get_causal_graph()
    if graph is not None:
        return graph
    from core.causal_graph import CausalGraph
    import sqlite3

    conn = sqlite3.connect(os.getenv("VELANTRIM_DB_PATH", "./data/velantrim_house.db"))
    conn.execute("PRAGMA foreign_keys = ON")
    return CausalGraph(conn)


def _create_graph_backend():
    from core.storage_facade import get_graph_store
    return get_graph_store()


def _create_cognitive_runtime():
    from core.cognitive_runtime import CognitiveRuntime
    return CognitiveRuntime()


def _create_essence_layer():
    # FIX #10 (Claude audit): EssenceLayer не существует → используем compose_essence
    from core.essence import compose_essence
    return lambda: compose_essence


def _create_working_notebook():
    from core.working_notebook import WorkingNotebook
    return WorkingNotebook()


def _create_consolidation(store):
    from core.consolidation_engine import ConsolidationEngine
    return ConsolidationEngine(store)


def _create_salience():
    from core.salience import SalienceDetector
    return SalienceDetector()


# ─── Глобальный экземпляр (обратная совместимость) ───────────────────────────

_app_singleton: Optional[VelantrimApp] = None


def get_app() -> VelantrimApp:
    """Вернуть глобальный экземпляр (для обратной совместимости)."""
    global _app_singleton
    if _app_singleton is None:
        _app_singleton = VelantrimApp()
        _app_singleton._init_components()
        logger.info("VelantrimApp создан (singleton)")
    return _app_singleton


def reset_app() -> None:
    """Сбросить синглтон (только для тестов)."""
    global _app_singleton
    _app_singleton = None


__all__ = [
    "VelantrimApp",
    "get_app",
    "reset_app",
]
