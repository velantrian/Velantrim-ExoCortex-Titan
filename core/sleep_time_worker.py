# core/sleep_time_worker.py
# Velantrim ExoCortex — Sleep-Time Worker + Core Memory Blocks
# v1.0.0
#
# Два компонента в одном файле — они тесно связаны.
#
# ── CoreMemoryBlocks ─────────────────────────────────────────────────────────
# Всегда-присутствующий блок в system prompt (~500 токенов).
# Три слота: user_profile, agent_persona, current_goals.
# Решает проблему: агент не знает кто ты при коротком запросе («помоги с кодом»).
# Источник идеи: Letta/MemGPT (memory_blocks), HYPERIA v5.25 §CoreMemoryBlocks.
#
# ── SleepTimeWorker ──────────────────────────────────────────────────────────
# Фоновый worker который активируется ТОЛЬКО когда агент простаивает.
# Ключевое отличие от «умного логгера»: метод think() запускается сам,
# без ожидания следующего сообщения пользователя.
#
# Что делает в idle:
#   1. Переоценивает текущую цель проекта
#   2. Ищет пробелы в знаниях (не по ключевым словам, а по смыслу)
#   3. Генерирует синтез если накопилось достаточно данных
#   4. suggest_next_step() — предлагает что делать дальше (из RNE документов)
#   5. Обновляет CoreMemoryBlocks.user_profile из новых фактов
#
# Источники:
#   - HYPERIA v5.25 §SleepTimeWorker (PDR-033 bug fixes встроены)
#   - Letta sleep-time compute (2026)
#   - RNE документы Grok (активный цикл think + suggest_next_step)
#
# Важные баги из PDR-033 (HYPERIA) которые уже исправлены здесь:
#   BUG-3: stop() отменяет task через cancel() + await, не просто флаг
#   RISK-1: core_blocks=None → AttributeError → optional default=None
#   RISK-5: idle отсчёт от _last_cycle_at, не от начала цикла
#
# Sprint: 2c (async + aiosqlite). Сейчас sync-заглушки для LLM-вызовов.
# TODO Sprint 2c: заменить _llm_complete() на реальный async LLM клиент.

import asyncio
import inspect
import json
import logging
import os
import sqlite3
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# ─── Константы ────────────────────────────────────────────────────────────────
CORE_BLOCKS_DB_PATH     = "./data/velantrim_core_blocks.db"
NOTEBOOK_DB_PATH        = "./data/velantrim_notebook.db"
DEFAULT_IDLE_TIMEOUT    = 300   # секунд простоя до активации
DEFAULT_SLEEP_INTERVAL  = 600   # минимальный интервал между циклами
SYNTHESIS_EVERY_N_FACTS = 5     # делать синтез каждые N новых фактов
MAX_OPEN_GAPS           = 30    # максимум открытых пробелов в блокноте


# ─── CoreMemoryBlocks ─────────────────────────────────────────────────────────

@dataclass
class CoreMemoryBlock:
    """Один слот постоянного контекста (~500 токенов на все блоки вместе)."""
    name: str
    content: str
    last_updated: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "CoreMemoryBlock":
        return cls(**d)


class CoreMemoryBlocks:
    """
    Всегда-присутствующий контекст агента в system prompt.

    Три стандартных блока:
      user_profile  — кто пользователь, имя, стек, предпочтения
      agent_persona — личность и стиль агента
      current_goals — активные цели текущего периода

    Персистируется в SQLite. Загружается при старте один раз.
    Обновляется через явный CRUD — не auto-overwrite.

    Инвариант: update() проходит через Truth Gate в production.
    MVP: прямая запись в SQLite без Truth Gate (Sprint 2c).
    """

    _DEFAULT_BLOCKS = {
        "user_profile":  "Пользователь: не указано. Стек: не указан.",
        "agent_persona": "Я — Velantrim ExoCortex, умная память для AI-агентов.",
        "current_goals": "Активные цели: не указано.",
    }

    def __init__(self, db_path: str = CORE_BLOCKS_DB_PATH) -> None:
        self.db_path = db_path
        self.blocks: dict[str, CoreMemoryBlock] = {}
        self._init_db()
        self._load()

    def _init_db(self) -> None:
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS core_blocks (
                    name         TEXT PRIMARY KEY,
                    content      TEXT NOT NULL,
                    last_updated TEXT NOT NULL
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def _load(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute(
                "SELECT name, content, last_updated FROM core_blocks"
            ).fetchall()
            for name, content, last_updated in rows:
                self.blocks[name] = CoreMemoryBlock(name, content, last_updated)
        finally:
            conn.close()

        # Создать дефолтные блоки если нет
        for name, content in self._DEFAULT_BLOCKS.items():
            if name not in self.blocks:
                self.update(name, content)

    def update(self, name: str, content: str) -> None:
        """Явное обновление блока. Не auto-overwrite."""
        now = datetime.now(UTC).isoformat()
        block = CoreMemoryBlock(name=name, content=content, last_updated=now)
        self.blocks[name] = block
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO core_blocks (name, content, last_updated)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    content      = excluded.content,
                    last_updated = excluded.last_updated
            """, (name, content, now))
            conn.commit()
        finally:
            conn.close()
        logger.debug("CoreMemoryBlocks: обновлён блок '%s'", name)

    def get(self, name: str) -> str | None:
        """Получить содержимое блока по имени."""
        block = self.blocks.get(name)
        return block.content if block else None

    def get_system_context(self) -> str:
        """
        Собрать все блоки для system prompt.
        Результат всегда ~500 токенов — не зависит от размера графа.
        """
        parts = []
        for name, block in self.blocks.items():
            parts.append(f"## {name}\n{block.content}")
        return "\n\n".join(parts)

    def all_as_dict(self) -> dict[str, str]:
        return {name: b.content for name, b in self.blocks.items()}


# ─── Research Notebook (блокнот проекта) ──────────────────────────────────────

@dataclass
class ResearchNotebook:
    """
    Живой блокнот текущего проекта.

    Хранит: цель, извлечённые намерения, ключевые вопросы,
    накопленные факты, открытые пробелы, историю синтезов.
    """
    project_id:         str
    current_goal:       str = ""
    extracted_intents:  list[dict] = field(default_factory=list)
    key_questions:      list[str]  = field(default_factory=list)
    known_facts:        list[dict] = field(default_factory=list)
    open_gaps:          list[dict] = field(default_factory=list)
    synthesis_history:  list[dict] = field(default_factory=list)
    user_style:         str  = "глубокий, честный, без воды"
    last_thought:       str  = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    version: int = 1

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, s: str) -> "ResearchNotebook":
        return cls(**json.loads(s))


class NotebookStore:
    """SQLite персистенция для ResearchNotebook."""

    def __init__(self, db_path: str = NOTEBOOK_DB_PATH) -> None:
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notebooks (
                    project_id TEXT PRIMARY KEY,
                    data       TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def load(self, project_id: str) -> ResearchNotebook | None:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT data FROM notebooks WHERE project_id = ?", (project_id,)
            ).fetchone()
            if row:
                return ResearchNotebook.from_json(row[0])
            return None
        finally:
            conn.close()

    def save(self, nb: ResearchNotebook) -> None:
        now = datetime.now(UTC).isoformat()
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO notebooks (project_id, data, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    data       = excluded.data,
                    updated_at = excluded.updated_at
            """, (nb.project_id, nb.to_json(), now))
            conn.commit()
        finally:
            conn.close()


# ─── SleepTimeWorker ──────────────────────────────────────────────────────────

class SleepTimeWorker:
    """
    Фоновый worker — активируется ТОЛЬКО при простое агента.

    Ключевое отличие от «умного логгера»: метод think() запускается
    автономно, без ожидания следующего сообщения пользователя.

    Паттерн из RNE документов:
        update_from_episode() — вызывается при каждом сообщении
        think()              — вызывается в фоне сам
        suggest_next_step()  — предлагает что делать дальше

    Важно:
        Вся работа fire-and-forget: не блокирует Fast Path.
        I28: ResponseAuditWorker и SleepTimeWorker только в Slow Path.

    Sprint 2c: заменить _llm_complete() на реальный async LLM client.
    """

    def __init__(
        self,
        project_id: str = "velantrim-core",
        idle_timeout: int = DEFAULT_IDLE_TIMEOUT,
        sleep_interval: int = DEFAULT_SLEEP_INTERVAL,
        core_blocks: CoreMemoryBlocks | None = None,
        notebook_store: NotebookStore | None = None,
        llm_fn: Callable[[str], str] | None = None,
    ) -> None:
        self.project_id     = project_id
        self.idle_timeout   = idle_timeout
        self.sleep_interval = sleep_interval

        # RISK-1 (PDR-033): core_blocks опционален — не AttributeError если None
        self.core_blocks    = core_blocks
        self._nb_store      = notebook_store or NotebookStore()
        self._llm_fn        = llm_fn  # callable(prompt) → str, None = mock

        self._notebook: ResearchNotebook | None = None
        self._lock          = asyncio.Lock()
        self._task: asyncio.Task | None = None
        self._stopped       = False
        self._last_activity = time.monotonic()
        self._last_cycle_at = 0.0  # RISK-5 (PDR-033): отдельный счётчик цикла
        self._facts_since_synthesis = 0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Запустить фоновый цикл."""
        self._stopped = False
        self._notebook = self._nb_store.load(self.project_id) or ResearchNotebook(
            project_id=self.project_id
        )
        # BUG-3 (PDR-033): сохраняем ссылку на task — иначе silent GC death
        self._task = asyncio.create_task(self._sleep_loop())
        logger.info("SleepTimeWorker: запущен (project=%s)", self.project_id)

    async def stop(self) -> None:
        """
        Остановить worker.
        BUG-3 (PDR-033): stop() должен cancel() task + await CancelledError.
        """
        self._stopped = True
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("SleepTimeWorker: остановлен")

    def notify_activity(self) -> None:
        """Вызывать при каждом сообщении пользователя — сбрасывает idle таймер."""
        self._last_activity = time.monotonic()

    # ── Основной цикл ─────────────────────────────────────────────────────────

    async def _sleep_loop(self) -> None:
        """
        Главный фоновый цикл.
        RISK-5 (PDR-033): цикл запускается если:
            idle >= idle_timeout AND (now - _last_cycle_at) >= sleep_interval
        """
        while not self._stopped:
            await asyncio.sleep(60)  # проверяем раз в минуту
            if self._is_idle():
                await self._run_sleep_cycle()

    def _is_idle(self) -> bool:
        now = time.monotonic()
        idle = now - self._last_activity
        since_cycle = now - self._last_cycle_at
        return idle >= self.idle_timeout and since_cycle >= self.sleep_interval

    async def _run_sleep_cycle(self) -> None:
        """Один полный цикл работы в idle."""
        logger.info("SleepTimeWorker: idle цикл начат")
        try:
            if os.getenv("CONSOLIDATION_ON_SLEEP", "1").strip().lower() in (
                "1",
                "true",
                "yes",
                "on",
            ):
                from core.consolidation_engine import run_consolidation

                report = await asyncio.to_thread(run_consolidation)
                logger.info(
                    "SleepTimeWorker: ConsolidationEngine %s", report.to_dict()
                )
            # V8.7: Experience Replay — ночная реактивация успешных цепочек
            try:
                from core.experience_replay import get_experience_replay_engine
                er = get_experience_replay_engine()
                er_report = await asyncio.to_thread(er.run)
                if er_report.get("facts_reactivated", 0) > 0:
                    logger.info(
                        "SleepTimeWorker: ExperienceReplay %s", er_report
                    )
            except Exception as exc:
                logger.debug("SleepTimeWorker: experience_replay skipped: %s", exc)
            await self.think()
        except Exception as e:
            logger.error("SleepTimeWorker._run_sleep_cycle error: %s", e)
        finally:
            self._last_cycle_at = time.monotonic()

    # ── Активное мышление (главная инновация из RNE) ──────────────────────────

    async def think(self) -> None:
        """
        Главный метод активного мышления.
        Запускается фоново — не ждёт следующего сообщения пользователя.

        Это ключевое отличие от «умного логгера»:
        система думает сама, между твоими сообщениями.

        FIX v8.5.3 (Claude audit + Gemini finding): раньше весь метод был
        обёрнут в один большой `async with self._lock`, и LLM-вызовы
        (_reassess_goal, _detect_gaps, _generate_synthesis) находились
        ВНУТРИ блокировки. При ответе LLM 10-30 секунд Fast Path
        (update_from_episode) намертво блокировался — прямое нарушение
        инварианта I28 о разделении Slow/Fast Path.

        Решение: разделили на три фазы. Лок захватывается только для
        быстрого чтения снапшота и для быстрой записи результатов.
        Долгие await-вызовы LLM выполняются БЕЗ блокировки, что позволяет
        Fast Path работать параллельно.
        """
        # ── ФАЗА 1: Снапшот под локом (быстро) ────────────────────────────
        async with self._lock:
            if not self._notebook:
                return
            recent_context = self._build_recent_context()
            facts_since_snapshot = self._facts_since_synthesis

        # ── ФАЗА 2: LLM-вызовы БЕЗ лока (могут идти секунды/минуты) ───────
        # Fast Path в это время полностью свободен.
        new_goal = await self._reassess_goal(recent_context)
        gaps = await self._detect_gaps(recent_context)

        should_synthesize = (
            facts_since_snapshot >= SYNTHESIS_EVERY_N_FACTS
            or len(gaps) >= 3
        )
        synthesis = await self._generate_synthesis() if should_synthesize else None

        # ── ФАЗА 3: Запись результатов под локом (быстро) ─────────────────
        async with self._lock:
            if not self._notebook:
                # Notebook могли закрыть пока мы думали — gracefully выходим
                return

            # Применяем переопределение цели
            if new_goal and new_goal != self._notebook.current_goal:
                old_goal = self._notebook.current_goal
                self._notebook.current_goal = new_goal
                self._notebook.extracted_intents.append({
                    "goal":      new_goal,
                    "prev_goal": old_goal,
                    "confidence": 0.85,
                    "at":        datetime.now(UTC).isoformat(),
                })
                logger.info(
                    "SleepTimeWorker: цель изменена: '%s' → '%s'",
                    old_goal[:50], new_goal[:50],
                )

            # Записываем найденные gaps
            for gap in gaps:
                if len(self._notebook.open_gaps) < MAX_OPEN_GAPS:
                    self._notebook.open_gaps.append(gap)

            # Записываем синтез если он был сделан
            if synthesis:
                self._notebook.synthesis_history.append({
                    "at":      datetime.now(UTC).isoformat(),
                    "content": synthesis,
                })
                self._facts_since_synthesis = 0
                logger.info("SleepTimeWorker: синтез сгенерирован")

            # Обновляем CoreMemoryBlocks если есть
            if self.core_blocks and self._notebook.current_goal:
                self.core_blocks.update(
                    "current_goals",
                    f"Активная цель: {self._notebook.current_goal}"
                )

            # Финальное сохранение
            self._notebook.last_thought = datetime.now(UTC).isoformat()
            self._notebook.version += 1
            self._nb_store.save(self._notebook)

    # ── Обновление из эпизода (вызывается при каждом сообщении) ──────────────

    async def update_from_episode(self, episode: dict[str, Any]) -> None:
        """
        Вызывается при каждом сообщении пользователя.
        Записывает факты и вопросы, запускает think() в фоне.
        """
        async with self._lock:
            if not self._notebook:
                return

            content = episode.get("content", "")

            # Извлекаем вопросы простой эвристикой
            if "?" in content:
                questions = [
                    q.strip() + "?"
                    for q in content.split("?")
                    if len(q.strip()) > 15
                ][:3]
                for q in questions:
                    if q not in self._notebook.key_questions:
                        self._notebook.key_questions.append(q)

            # Простой факт из эпизода
            if content and len(content) > 20:
                self._notebook.known_facts.append({
                    "content": content[:300],
                    "source":  episode.get("source", "user"),
                    "at":      datetime.now(UTC).isoformat(),
                })
                self._facts_since_synthesis += 1

            self._nb_store.save(self._notebook)

        self.notify_activity()
        # FIX v8.5.1 (Gemini): сохраняем ссылку на task —
        # иначе Python GC может уничтожить task прямо во время выполнения
        if not hasattr(self, "_bg_tasks"):
            self._bg_tasks: set = set()
        bg_task = asyncio.create_task(self._background_think())
        self._bg_tasks.add(bg_task)
        bg_task.add_done_callback(self._bg_tasks.discard)

    async def _background_think(self) -> None:
        """Фоновый запуск think() — fire-and-forget."""
        try:
            await self.think()
        except Exception as e:
            logger.error("SleepTimeWorker._background_think error: %s", e)

    # ── suggest_next_step (ключевая новинка из RNE) ───────────────────────────

    async def suggest_next_step(self) -> str:
        """
        Предлагает один конкретный следующий шаг проекта.

        Ключевая новинка из RNE документов Grok:
        «система ведёт себя как живой соавтор — не только фиксирует,
        но и предлагает что делать дальше».

        Возвращает строку 1-2 предложения, конкретную и полезную.
        """
        if not self._notebook:
            return "Блокнот не инициализирован. Запусти start() сначала."

        prompt = (
            f"Текущая цель проекта: {self._notebook.current_goal}\n"
            f"Накоплено фактов: {len(self._notebook.known_facts)}\n"
            f"Открытых пробелов: {len(self._notebook.open_gaps)}\n"
            f"Последние вопросы: {self._notebook.key_questions[-3:]}\n\n"
            f"Предложи ОДИН конкретный следующий шаг (1-2 предложения).\n"
            f"Стиль: {self._notebook.user_style}"
        )
        result = await self._llm_complete(prompt)
        logger.debug("SleepTimeWorker.suggest_next_step: %s", result[:80])
        return result

    async def get_notebook(self) -> dict[str, Any]:
        """
        Возвращает актуальный блокнот + автоматическое предложение следующего шага.
        Всегда вызывает think() перед показом — блокнот актуален.
        """
        await self.think()
        next_step = await self.suggest_next_step()
        nb = self._notebook

        return {
            "project_id":        nb.project_id if nb else "?",
            "current_goal":      nb.current_goal if nb else "",
            "facts_count":       len(nb.known_facts) if nb else 0,
            "questions_count":   len(nb.key_questions) if nb else 0,
            "open_gaps_count":   len(nb.open_gaps) if nb else 0,
            "last_synthesis":    (
                nb.synthesis_history[-1]["content"][:200]
                if nb and nb.synthesis_history else "Синтез ещё не создан"
            ),
            "suggested_next_step": next_step,
            "last_thought":      nb.last_thought if nb else "",
            "version":           nb.version if nb else 0,
        }

    # ── Внутренние методы ─────────────────────────────────────────────────────

    def _build_recent_context(self) -> str:
        """Собрать последние N фактов и вопросов для контекста."""
        if not self._notebook:
            return ""
        facts = self._notebook.known_facts[-5:]
        questions = self._notebook.key_questions[-3:]
        parts = []
        if facts:
            parts.append("Последние факты: " + " | ".join(
                f.get("content", "")[:100] for f in facts
            ))
        if questions:
            parts.append("Последние вопросы: " + " | ".join(questions))
        if self._notebook.open_gaps:
            parts.append(f"Открытых пробелов: {len(self._notebook.open_gaps)}")
        return "\n".join(parts)

    async def _reassess_goal(self, context: str) -> str:
        """Переоценить текущую цель проекта."""
        if not context:
            return self._notebook.current_goal if self._notebook else ""
        if self._notebook is None:
            return ""
        prompt = (
            f"Текущая цель: {self._notebook.current_goal}\n"
            f"Последний контекст:\n{context[:500]}\n\n"
            f"Какая сейчас ГЛАВНАЯ цель? Ответь одним предложением."
        )
        return await self._llm_complete(prompt)

    async def _detect_gaps(self, context: str) -> list[dict]:
        """
        Выявить пробелы в знаниях.
        Не по ключевым словам — по смысловому анализу контекста.
        MVP: эвристика + LLM. Sprint 2c: полный LLM анализ.
        """
        gaps: list[dict] = []
        if not context:
            return gaps

        # Эвристика: вопросы без ответов в known_facts
        if self._notebook:
            for q in self._notebook.key_questions[-5:]:
                answered = any(
                    q[:20].lower() in f.get("content", "").lower()
                    for f in self._notebook.known_facts
                )
                if not answered:
                    gaps.append({
                        "gap":      f"Вопрос без ответа: {q[:150]}",
                        "priority": "medium",
                        "at":       datetime.now(UTC).isoformat(),
                    })

        # LLM анализ (MVP: mock)
        prompt = (
            f"Цель: {self._notebook.current_goal if self._notebook else '?'}\n"
            f"Контекст: {context[:400]}\n\n"
            f"Какие важные аспекты темы НЕ освещены? "
            f"Верни JSON-список [{{'gap':'...','priority':'high/medium/low'}}] "
            f"или пустой список []."
        )
        llm_result = await self._llm_complete(prompt, is_json=True)
        if isinstance(llm_result, list):
            for item in llm_result[:3]:
                if isinstance(item, dict) and "gap" in item:
                    item["at"] = datetime.now(UTC).isoformat()
                    gaps.append(item)

        return gaps

    async def _generate_synthesis(self) -> str:
        """Сгенерировать синтез текущего состояния проекта."""
        if not self._notebook:
            return ""
        prompt = (
            f"Цель: {self._notebook.current_goal}\n"
            f"Фактов: {len(self._notebook.known_facts)}\n"
            f"Вопросов: {len(self._notebook.key_questions)}\n"
            f"Пробелов: {len(self._notebook.open_gaps)}\n"
            f"Стиль: {self._notebook.user_style}\n\n"
            f"Составь краткий синтез (3-5 предложений): что уже поняли, "
            f"что осталось выяснить."
        )
        return await self._llm_complete(prompt)

    async def _llm_complete(
        self, prompt: str, is_json: bool = False
    ) -> Any:
        """
        Вызов LLM. MVP: mock-заглушка.
        Sprint 2c: заменить на реальный async LLM client.

        Если передан llm_fn в конструктор — используем его.
        AUDIT-FIX v8.4.0: поддерживаем и sync, и async llm_fn через
        inspect.iscoroutinefunction. До v8.4.0 при async-callable
        результат был coroutine, а не строка → TypeError в json.loads.

        Иначе — mock возвращает заглушку.
        """
        if self._llm_fn is not None:
            try:
                # AUDIT-FIX v8.4.0: правильно обрабатываем async и sync callables
                result = self._llm_fn(prompt)
                if inspect.iscoroutine(result):
                    result = await result
                if is_json:
                    try:
                        return json.loads(result)
                    except json.JSONDecodeError:
                        return []
                return result
            except Exception as e:
                logger.warning("SleepTimeWorker._llm_complete error: %s", e)

        # Mock-заглушка (Sprint 2c: удалить)
        # BUG-FIX v8.3.1: проверка "следующий шаг" ДОЛЖНА быть ПЕРЕД "цель",
        # иначе suggest_next_step (чей prompt содержит и "цель" и "следующий шаг")
        # ошибочно матчится на "цель" и возвращает пустой current_goal.
        if is_json:
            return []
        if "следующий шаг" in prompt.lower() or "next_step" in prompt.lower():
            nb = self._notebook
            if nb and nb.open_gaps:
                return (
                    f"Закрыть открытый пробел: «{nb.open_gaps[0].get('gap', '?')[:100]}». "
                    f"Это наиболее приоритетная задача."
                )
            if nb and nb.key_questions:
                return (
                    f"Ответить на ключевой вопрос: «{nb.key_questions[-1][:100]}»."
                )
            return "Продолжать накапливать контекст по текущей цели проекта."
        if "цель" in prompt.lower() or "goal" in prompt.lower():
            return self._notebook.current_goal if self._notebook else ""
        return "[LLM mock — Sprint 2c: подключить реальный клиент]"

    # ── Публичные свойства ────────────────────────────────────────────────────

    @property
    def notebook(self) -> ResearchNotebook | None:
        """Прямой доступ к блокноту (read-only снаружи)."""
        return self._notebook

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()


# ─── Фабрика для тестовой изоляции ────────────────────────────────────────────

def make_sleep_time_worker(
    project_id: str = "velantrim-core",
    core_blocks_db: str = CORE_BLOCKS_DB_PATH,
    notebook_db: str = NOTEBOOK_DB_PATH,
    llm_fn: Callable[[str], str] | None = None,
) -> SleepTimeWorker:
    """
    Создать SleepTimeWorker с изолированными хранилищами.
    Используй в тестах с tmp_path:
        worker = make_sleep_time_worker(
            project_id="test",
            core_blocks_db=str(tmp_path / "blocks.db"),
            notebook_db=str(tmp_path / "notebook.db"),
        )
    """
    blocks = CoreMemoryBlocks(db_path=core_blocks_db)
    store  = NotebookStore(db_path=notebook_db)
    return SleepTimeWorker(
        project_id=project_id,
        core_blocks=blocks,
        notebook_store=store,
        llm_fn=llm_fn,
    )
