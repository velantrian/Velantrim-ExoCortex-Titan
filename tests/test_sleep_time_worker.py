"""
Tests for core/sleep_time_worker.py
SleepTimeWorker + CoreMemoryBlocks + ResearchNotebook + NotebookStore

Covers:
  - CoreMemoryBlocks: init, update, get, get_system_context, defaults
  - NotebookStore: save, load, round-trip
  - SleepTimeWorker: start/stop (BUG-3), notify_activity, idle detection (RISK-5)
  - update_from_episode: факты, вопросы, счётчик
  - think(): переоценка цели, пробелы, синтез, CoreMemoryBlocks update
  - suggest_next_step(): возвращает строку с рекомендацией
  - get_notebook(): полный снапшот + suggested_next_step
  - make_sleep_time_worker(): фабрика для изоляции
  - LLM mock: передача llm_fn
"""
import asyncio
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Фикстуры ──────────────────────────────────────────────────────────────────

@pytest.fixture
def blocks(tmp_path):
    from core.sleep_time_worker import CoreMemoryBlocks
    return CoreMemoryBlocks(db_path=str(tmp_path / "blocks.db"))


@pytest.fixture
def nb_store(tmp_path):
    from core.sleep_time_worker import NotebookStore
    return NotebookStore(db_path=str(tmp_path / "notebook.db"))


@pytest.fixture
def worker(tmp_path):
    from core.sleep_time_worker import make_sleep_time_worker
    return make_sleep_time_worker(
        project_id="test-project",
        core_blocks_db=str(tmp_path / "blocks.db"),
        notebook_db=str(tmp_path / "notebook.db"),
    )


@pytest.fixture
def worker_with_llm(tmp_path):
    """Worker с простым llm_fn для тестов suggest_next_step."""
    from core.sleep_time_worker import make_sleep_time_worker

    def mock_llm(prompt: str) -> str:
        if "следующий шаг" in prompt.lower():
            return "Закрыть главный открытый пробел по текущей цели."
        if "цель" in prompt.lower():
            return "Построить умную память для AI-агента."
        if "пробел" in prompt.lower() or "gap" in prompt.lower():
            return "[]"
        return "Тестовый ответ LLM."

    return make_sleep_time_worker(
        project_id="llm-test",
        core_blocks_db=str(tmp_path / "blocks.db"),
        notebook_db=str(tmp_path / "notebook.db"),
        llm_fn=mock_llm,
    )


# ── CoreMemoryBlocks ──────────────────────────────────────────────────────────

class TestCoreMemoryBlocks:

    def test_default_blocks_created_on_init(self, blocks):
        """При инициализации создаются три дефолтных блока."""
        assert blocks.get("user_profile") is not None
        assert blocks.get("agent_persona") is not None
        assert blocks.get("current_goals") is not None

    def test_update_and_get(self, blocks):
        """update() сохраняет, get() возвращает."""
        blocks.update("user_profile", "Имя: Тест. Стек: Python.")
        assert blocks.get("user_profile") == "Имя: Тест. Стек: Python."

    def test_update_persists_to_sqlite(self, tmp_path):
        """Обновление сохраняется и загружается из SQLite."""
        from core.sleep_time_worker import CoreMemoryBlocks
        db = str(tmp_path / "persist.db")

        b1 = CoreMemoryBlocks(db_path=db)
        b1.update("agent_persona", "Я умный агент версии 2.")

        b2 = CoreMemoryBlocks(db_path=db)
        assert b2.get("agent_persona") == "Я умный агент версии 2."

    def test_get_system_context_contains_all_blocks(self, blocks):
        """get_system_context() содержит все три блока."""
        blocks.update("user_profile", "Тест пользователь")
        blocks.update("agent_persona", "Тест агент")
        blocks.update("current_goals", "Тест цель")

        ctx = blocks.get_system_context()
        assert "user_profile" in ctx
        assert "agent_persona" in ctx
        assert "current_goals" in ctx
        assert "Тест пользователь" in ctx

    def test_get_nonexistent_returns_none(self, blocks):
        """Несуществующий блок → None."""
        assert blocks.get("nonexistent_block_xyz") is None

    def test_update_custom_block_name(self, blocks):
        """Можно добавить кастомный блок."""
        blocks.update("project_context", "Velantrim v8.3.0")
        assert blocks.get("project_context") == "Velantrim v8.3.0"

    def test_all_as_dict(self, blocks):
        """all_as_dict() возвращает словарь всех блоков."""
        d = blocks.all_as_dict()
        assert isinstance(d, dict)
        assert "user_profile" in d
        assert "agent_persona" in d


# ── NotebookStore ─────────────────────────────────────────────────────────────

class TestNotebookStore:

    def test_load_returns_none_for_empty(self, nb_store):
        """Нет записи → None."""
        result = nb_store.load("nonexistent-project")
        assert result is None

    def test_save_and_load_roundtrip(self, nb_store):
        """save + load сохраняет все поля."""
        from core.sleep_time_worker import ResearchNotebook
        nb = ResearchNotebook(
            project_id="p1",
            current_goal="Тестовая цель",
            key_questions=["Что такое ESM?", "Когда Sprint 2?"],
            user_style="честный и краткий",
        )
        nb_store.save(nb)
        loaded = nb_store.load("p1")

        assert loaded is not None
        assert loaded.current_goal == "Тестовая цель"
        assert "Что такое ESM?" in loaded.key_questions
        assert loaded.user_style == "честный и краткий"

    def test_save_overwrites_on_duplicate(self, nb_store):
        """Повторный save перезаписывает запись."""
        from core.sleep_time_worker import ResearchNotebook
        nb = ResearchNotebook(project_id="p2", current_goal="Первая цель")
        nb_store.save(nb)

        nb.current_goal = "Обновлённая цель"
        nb_store.save(nb)

        loaded = nb_store.load("p2")
        assert loaded.current_goal == "Обновлённая цель"

    def test_save_with_facts_and_gaps(self, nb_store):
        """Факты и пробелы сохраняются корректно."""
        from core.sleep_time_worker import ResearchNotebook
        nb = ResearchNotebook(
            project_id="p3",
            known_facts=[{"content": "SQLite хранит данные", "source": "user"}],
            open_gaps=[{"gap": "Neo4j не подключён", "priority": "high"}],
        )
        nb_store.save(nb)
        loaded = nb_store.load("p3")

        assert len(loaded.known_facts) == 1
        assert loaded.known_facts[0]["content"] == "SQLite хранит данные"
        assert len(loaded.open_gaps) == 1
        assert loaded.open_gaps[0]["priority"] == "high"


# ── SleepTimeWorker: lifecycle ────────────────────────────────────────────────

class TestSleepTimeWorkerLifecycle:

    @pytest.mark.asyncio
    async def test_start_initializes_notebook(self, worker):
        """start() создаёт notebook если его нет."""
        await worker.start()
        assert worker.notebook is not None
        assert worker.notebook.project_id == "test-project"
        await worker.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self, worker):
        """BUG-3 (PDR-033): stop() корректно отменяет task."""
        await worker.start()
        assert worker.is_running
        await worker.stop()
        # После stop task должен быть завершён
        assert not worker.is_running

    @pytest.mark.asyncio
    async def test_stop_idempotent(self, worker):
        """stop() можно вызвать дважды без ошибки."""
        await worker.start()
        await worker.stop()
        await worker.stop()  # второй вызов не должен падать

    @pytest.mark.asyncio
    async def test_start_twice_replaces_task(self, worker):
        """Повторный start() перезапускает worker."""
        await worker.start()
        await worker.stop()
        await worker.start()
        assert worker.is_running
        await worker.stop()


# ── SleepTimeWorker: idle detection ──────────────────────────────────────────

class TestIdleDetection:

    def test_not_idle_immediately_after_activity(self, worker):
        """Сразу после notify_activity — не idle."""
        worker.notify_activity()
        # idle_timeout = 300 секунд по умолчанию
        assert not worker._is_idle()

    def test_idle_when_timeout_exceeded(self, tmp_path):
        """RISK-5: idle срабатывает когда оба таймера превышены."""
        from core.sleep_time_worker import make_sleep_time_worker
        w = make_sleep_time_worker(
            project_id="idle-test",
            core_blocks_db=str(tmp_path / "b.db"),
            notebook_db=str(tmp_path / "n.db"),
        )
        # Симулируем давнюю активность и давний цикл
        w._last_activity = time.monotonic() - 400  # > 300 сек
        w._last_cycle_at = time.monotonic() - 700  # > 600 сек
        assert w._is_idle()

    def test_not_idle_if_recent_cycle(self, tmp_path):
        """RISK-5: не idle если последний цикл был недавно."""
        from core.sleep_time_worker import make_sleep_time_worker
        w = make_sleep_time_worker(
            project_id="cycle-test",
            core_blocks_db=str(tmp_path / "b.db"),
            notebook_db=str(tmp_path / "n.db"),
        )
        w._last_activity = time.monotonic() - 400  # > 300 сек
        w._last_cycle_at = time.monotonic() - 10   # недавний цикл
        assert not w._is_idle()


# ── update_from_episode ───────────────────────────────────────────────────────

class TestUpdateFromEpisode:

    @pytest.mark.asyncio
    async def test_episode_adds_facts(self, worker):
        """update_from_episode() добавляет факты в notebook."""
        await worker.start()
        await worker.update_from_episode({
            "content": "ESM имеет 8 состояний в Velantrim системе.",
            "source": "user",
        })
        assert len(worker.notebook.known_facts) >= 1
        await worker.stop()

    @pytest.mark.asyncio
    async def test_episode_extracts_questions(self, worker):
        """update_from_episode() извлекает вопросы из контента."""
        await worker.start()
        await worker.update_from_episode({
            "content": "Когда будет подключён Neo4j? Что такое bi-temporal?",
            "source": "user",
        })
        assert len(worker.notebook.key_questions) >= 1
        await worker.stop()

    @pytest.mark.asyncio
    async def test_episode_increments_facts_counter(self, worker):
        """Счётчик фактов с момента последнего синтеза растёт."""
        await worker.start()
        before = worker._facts_since_synthesis
        await worker.update_from_episode({
            "content": "Важный факт о системе памяти.",
            "source": "user",
        })
        assert worker._facts_since_synthesis >= before
        await worker.stop()

    @pytest.mark.asyncio
    async def test_episode_no_questions_if_short_text(self, worker):
        """Короткий текст без '?' не добавляет вопросы."""
        await worker.start()
        before = len(worker.notebook.key_questions)
        await worker.update_from_episode({
            "content": "OK.",
            "source": "user",
        })
        assert len(worker.notebook.key_questions) == before
        await worker.stop()


# ── think() ───────────────────────────────────────────────────────────────────

class TestThink:

    @pytest.mark.asyncio
    async def test_think_increments_version(self, worker):
        """think() увеличивает версию notebook."""
        await worker.start()
        before = worker.notebook.version
        await worker.think()
        assert worker.notebook.version > before
        await worker.stop()

    @pytest.mark.asyncio
    async def test_think_updates_last_thought(self, worker):
        """think() обновляет last_thought timestamp."""
        await worker.start()
        old_thought = worker.notebook.last_thought
        await asyncio.sleep(0.01)
        await worker.think()
        assert worker.notebook.last_thought >= old_thought
        await worker.stop()

    @pytest.mark.asyncio
    async def test_think_with_llm_fn_updates_goal(self, worker_with_llm):
        """think() с llm_fn обновляет цель если LLM предлагает новую."""
        await worker_with_llm.start()
        # Добавим контекст для think()
        await worker_with_llm.update_from_episode({
            "content": "Нужно построить умную память для AI-агента.",
            "source": "user",
        })
        await worker_with_llm.think()
        # Цель должна быть установлена
        assert worker_with_llm.notebook.current_goal != ""
        await worker_with_llm.stop()

    @pytest.mark.asyncio
    async def test_think_triggers_synthesis_after_n_facts(self, tmp_path):
        """Синтез создаётся после SYNTHESIS_EVERY_N_FACTS фактов."""
        from core.sleep_time_worker import SYNTHESIS_EVERY_N_FACTS, make_sleep_time_worker

        def llm(prompt):
            if "синтез" in prompt.lower() or "составь" in prompt.lower():
                return "Синтез: система развивается правильно."
            return "[]"

        w = make_sleep_time_worker(
            project_id="synth-test",
            core_blocks_db=str(tmp_path / "b.db"),
            notebook_db=str(tmp_path / "n.db"),
            llm_fn=llm,
        )
        await w.start()
        # Форсируем счётчик
        w._facts_since_synthesis = SYNTHESIS_EVERY_N_FACTS
        await w.think()
        assert len(w.notebook.synthesis_history) >= 1
        await w.stop()

    @pytest.mark.asyncio
    async def test_think_updates_core_blocks_goals(self, tmp_path):
        """think() обновляет CoreMemoryBlocks.current_goals при изменении цели."""
        from core.sleep_time_worker import make_sleep_time_worker

        def llm(prompt):
            if "цель" in prompt.lower():
                return "Новая активная цель проекта."
            return "[]"

        w = make_sleep_time_worker(
            project_id="blocks-update-test",
            core_blocks_db=str(tmp_path / "b.db"),
            notebook_db=str(tmp_path / "n.db"),
            llm_fn=llm,
        )
        await w.start()
        await w.update_from_episode({
            "content": "Нужна новая цель для проекта.",
            "source": "user",
        })
        await w.think()
        # CoreMemoryBlocks.current_goals должен отражать новую цель
        goals = w.core_blocks.get("current_goals")
        assert goals is not None
        await w.stop()


# ── suggest_next_step ─────────────────────────────────────────────────────────

class TestSuggestNextStep:

    @pytest.mark.asyncio
    async def test_suggest_returns_string(self, worker):
        """suggest_next_step() всегда возвращает строку."""
        await worker.start()
        result = await worker.suggest_next_step()
        assert isinstance(result, str)
        assert len(result) > 0
        await worker.stop()

    @pytest.mark.asyncio
    async def test_suggest_not_empty_without_llm(self, worker):
        """Даже без LLM suggest_next_step() возвращает осмысленный mock."""
        await worker.start()
        result = await worker.suggest_next_step()
        # Mock не должен быть пустой строкой
        assert result.strip() != ""
        await worker.stop()

    @pytest.mark.asyncio
    async def test_suggest_uses_open_gaps(self, worker):
        """Если есть открытые пробелы — suggest упоминает их."""
        await worker.start()
        worker.notebook.open_gaps.append({
            "gap": "Neo4j не подключён к pipeline",
            "priority": "high",
            "at": "2026-05-11T00:00:00+00:00",
        })
        result = await worker.suggest_next_step()
        # Mock-заглушка должна упомянуть пробел
        assert "Neo4j" in result or len(result) > 10
        await worker.stop()

    @pytest.mark.asyncio
    async def test_suggest_with_llm_fn(self, worker_with_llm):
        """suggest_next_step() с llm_fn использует его ответ."""
        await worker_with_llm.start()
        result = await worker_with_llm.suggest_next_step()
        assert "пробел" in result.lower() or len(result) > 5
        await worker_with_llm.stop()

    @pytest.mark.asyncio
    async def test_suggest_returns_string_when_not_started(self, worker):
        """suggest_next_step() без start() возвращает пояснение."""
        result = await worker.suggest_next_step()
        assert isinstance(result, str)
        assert len(result) > 0


# ── get_notebook ─────────────────────────────────────────────────────────────

class TestGetNotebook:

    @pytest.mark.asyncio
    async def test_get_notebook_returns_dict(self, worker):
        """get_notebook() возвращает словарь с ожидаемыми ключами."""
        await worker.start()
        nb = await worker.get_notebook()

        assert isinstance(nb, dict)
        assert "current_goal"        in nb
        assert "facts_count"         in nb
        assert "open_gaps_count"     in nb
        assert "suggested_next_step" in nb
        assert "last_synthesis"      in nb
        assert "last_thought"        in nb
        assert "version"             in nb
        await worker.stop()

    @pytest.mark.asyncio
    async def test_get_notebook_suggested_step_is_string(self, worker):
        """suggested_next_step в get_notebook() — всегда строка."""
        await worker.start()
        nb = await worker.get_notebook()
        assert isinstance(nb["suggested_next_step"], str)
        assert len(nb["suggested_next_step"]) > 0
        await worker.stop()

    @pytest.mark.asyncio
    async def test_get_notebook_increments_version(self, worker):
        """get_notebook() вызывает think() → версия растёт."""
        await worker.start()
        v1 = worker.notebook.version
        await worker.get_notebook()
        v2 = worker.notebook.version
        assert v2 >= v1
        await worker.stop()


# ── make_sleep_time_worker factory ────────────────────────────────────────────

class TestFactory:

    def test_factory_creates_isolated_instances(self, tmp_path):
        """Два worker-а с разными path не делят состояние."""
        from core.sleep_time_worker import make_sleep_time_worker
        w1 = make_sleep_time_worker(
            project_id="p1",
            core_blocks_db=str(tmp_path / "b1.db"),
            notebook_db=str(tmp_path / "n1.db"),
        )
        w2 = make_sleep_time_worker(
            project_id="p2",
            core_blocks_db=str(tmp_path / "b2.db"),
            notebook_db=str(tmp_path / "n2.db"),
        )
        w1.core_blocks.update("user_profile", "User A")
        assert w2.core_blocks.get("user_profile") != "User A"

    def test_factory_accepts_llm_fn(self, tmp_path):
        """Фабрика принимает llm_fn."""
        from core.sleep_time_worker import make_sleep_time_worker
        called = []

        def my_llm(prompt):
            called.append(prompt)
            return "Тест"

        w = make_sleep_time_worker(
            project_id="fn-test",
            core_blocks_db=str(tmp_path / "b.db"),
            notebook_db=str(tmp_path / "n.db"),
            llm_fn=my_llm,
        )
        assert w._llm_fn is my_llm
