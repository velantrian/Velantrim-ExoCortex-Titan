# core/storage.py
# Velantrim ExoCortex — Storage Abstraction Layer
# v8.1.0 (audit-fix: bi-temporal methods added to ABC — I96, V9 Sprint 1 Contract)
#
# GraphStore ABC — контракт для всех storage-бэкендов.
# Текущая реализация: SQLite через core/memory.py (MVP, синхронная).
#
# TODO Sprint 2c (async): перевести интерфейс на async def + aiosqlite.
# TODO Sprint 2c: добавить Neo4jGraphStore(GraphStore).
# TODO Sprint 2c: DI через конструктор вместо глобального state.

from abc import ABC, abstractmethod
from typing import Any


class GraphStore(ABC):
    """
    Абстрактный контракт хранилища фактов.
    MVP: синхронный интерфейс. Перевод на async — строго в Sprint 2c.

    Инварианты:
      I50:  epistemic_state изменяется ТОЛЬКО через update_state(),
            вызываемой из transition_esm(). Прямой SQL UPDATE — баг.
      I96:  каждый факт имеет 4 bi-temporal поля:
            t_event_valid_start, t_event_valid_end,
            t_ingestion_start,  t_ingestion_end.
      I97:  прямая запись в L3 запрещена вне BlackboardBus
            (при переходе на Neo4j — вместо прямого Cypher).
    """

    # ── Базовые операции ────────────────────────────────────────────────────

    @abstractmethod
    def store_fact(self, fact: dict[str, Any]) -> bool:
        """
        Создать или обновить факт.
        Инвариант P0.1: epistemic_state и history НЕ перезаписываются
        при UPDATE — только при создании новой записи.
        Bi-temporal поля t_event_valid_start и t_ingestion_start
        устанавливаются при создании и никогда не обновляются.
        """
        ...

    def transition_esm(
        self, fact_id: str, new_state: str, by: str = "transition_esm"
    ) -> bool:
        """Легальный ESM-переход факта (I50), поверх update_state().

        Конкретные хранилища переопределяют (см. core.memory.SQLiteGraphStore);
        базовая реализация — заглушка (контракт для type-checker'а).
        """
        raise NotImplementedError

    @abstractmethod
    def get_fact(self, fact_id: str) -> dict[str, Any] | None:
        """Получить факт по ID. None если не найден."""
        ...

    @abstractmethod
    def get_all_facts(
        self, epistemic_state: str | None = None
    ) -> list[dict[str, Any]]:
        """Получить все факты. Опционально — фильтр по ESM-состоянию."""
        ...

    @abstractmethod
    def update_state(
        self,
        fact_id: str,
        new_state: str,
        history_entry: dict[str, Any],
        now: str,
    ) -> bool:
        """
        Атомарно обновить epistemic_state и дописать запись в history.
        Вызывается только из transition_esm(). Прямой SQL UPDATE — баг.
        При переходе в Collapsed: устанавливает t_ingestion_end = now.
        Возвращает True если строка найдена и обновлена.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Закрыть соединение. Идемпотентен."""
        ...

    # ── Bi-temporal операции (I96, V9 Sprint 1 Contract) ───────────────────

    @abstractmethod
    def get_fact_at(
        self,
        fact_id: str,
        known_at: str,
        world_at: str,
    ) -> dict[str, Any] | None:
        """
        Time-travel запрос: что система знала о факте fact_id
        в момент known_at (ingestion time) для состояния мира world_at (event time).

        Эквивалент Cypher-запроса из V9 §2.1:
          WHERE t_ingestion_start <= known_at
            AND (t_ingestion_end IS NULL OR t_ingestion_end > known_at)
            AND t_event_valid_start <= world_at
            AND (t_event_valid_end IS NULL OR t_event_valid_end > world_at)

        known_at и world_at — ISO 8601 строки (datetime.utcnow().isoformat()).
        None если факт не существовал в указанный момент.
        """
        ...

    @abstractmethod
    def invalidate_edge(
        self,
        fact_id: str,
        t_event_valid_end: str | None = None,
        t_ingestion_end: str | None = None,
    ) -> bool:
        """
        Инвалидировать факт — НИКОГДА не DELETE, только SET t_*_end.
        Принцип V9 §2.1: «Никогда не DELETE — только инвалидируем».

        t_event_valid_end: когда факт перестал быть истинным в мире.
        t_ingestion_end:   когда система перестала верить в этот факт.
        Оба параметра по умолчанию = now.
        Уже выставленные значения не перезаписываются (COALESCE).
        Возвращает True если строка найдена.
        """
        ...

    @abstractmethod
    def search(
        self,
        query: str,
        mode: str = "bm25",
        limit: int = 10,
        epistemic_state: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Поиск фактов по тексту.
        mode: 'bm25' | 'fts5' | 'semantic' (последний — Sprint 2c с Neo4j).
        epistemic_state: опциональный фильтр (например 'Validated').

        MVP (SQLite): BM25 или FTS5 по полю claim.
        Sprint 2c (Neo4j): hybrid semantic + keyword + graph traversal.
        """
        ...

    @abstractmethod
    def get_fact_ids(
        self, limit: int = 10_000, epistemic_state: str | None = None
    ) -> list[str]:
        """
        TASK-06: Лёгкий запрос — только fact_id без полного тела факта.
        Используется в pipeline._retrieve_from_store() как первый шаг:
        получить все ID → передать в NGramIndex → тянуть полные факты
        только для отфильтрованных кандидатов.

        Намного дешевле get_all_facts() при большой базе:
        SELECT fact_id FROM facts vs SELECT * FROM facts.
        """
        ...

    @abstractmethod
    def get_facts_by_ids(self, fact_ids: list[str]) -> list[dict[str, Any]]:
        """
        TASK-06: Получить полные факты по списку ID.
        Пара к get_fact_ids(): после NGram-фильтрации тянем только нужные.
        """
        ...


# ---------------------------------------------------------------------------
# Async contract — Sprint 2c placeholder
# ---------------------------------------------------------------------------

class AsyncGraphStore(ABC):
    """
    Async контракт для Sprint 2c.
    Реализации: AsyncSQLiteGraphStore (aiosqlite) · Neo4jGraphStore (neo4j async driver).
    Все методы зеркалят GraphStore, но async.
    """

    @abstractmethod
    async def store_fact(self, fact: dict[str, Any]) -> None: ...

    @abstractmethod
    async def get_fact(self, fact_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def get_all_facts(
        self, epistemic_state: str | None = None
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def update_state(
        self, fact_id: str, new_state: str,
        history_entry: dict[str, Any], now: str,
    ) -> bool: ...

    @abstractmethod
    async def get_fact_at(
        self, fact_id: str, known_at: str, world_at: str,
    ) -> dict[str, Any] | None: ...

    @abstractmethod
    async def invalidate_edge(
        self, fact_id: str,
        t_event_valid_end: str | None = None,
        t_ingestion_end: str | None = None,
    ) -> bool: ...

    @abstractmethod
    async def search(
        self, query: str, mode: str = "bm25",
        limit: int = 10, epistemic_state: str | None = None,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def close(self) -> None: ...
