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
#   1. Предлагает цель (proposed_goal). Принятую цель меняет только владелец:
#      SleepTimeWorker.accept_goal. Фоновый анализ current_goal не трогает.
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
import hashlib
import hmac
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from core import mutation_gate

logger = logging.getLogger(__name__)

# ─── Константы ────────────────────────────────────────────────────────────────
CORE_BLOCKS_DB_PATH     = "./data/velantrim_core_blocks.db"
NOTEBOOK_DB_PATH        = "./data/velantrim_notebook.db"
DEFAULT_IDLE_TIMEOUT    = 300   # секунд простоя до активации
DEFAULT_SLEEP_INTERVAL  = 600   # минимальный интервал между циклами
SYNTHESIS_EVERY_N_FACTS = 5     # делать синтез каждые N новых фактов
MAX_OPEN_GAPS           = 30    # максимум открытых пробелов в блокноте
DEFAULT_PROJECT_ID      = "velantrim-core"
COMMIT_RETRIES          = 25    # попыток перечитать и записать при конкурентных писателях
GOAL_BLOCK_NAME         = "current_goals"  # проекция цели в CoreMemoryBlocks; НЕ источник истины
GOAL_BLOCK_DEFAULT_TEXT = "Активные цели: не указано."
OWNER_DECISION_DOMAIN   = "velantrim.sleep-worker.owner-goal-decision.v1"
OWNER_DECISION_MAX_AGE_SECONDS  = 300  # подпись решения владельца живёт 5 минут
OWNER_DECISION_MAX_SKEW_SECONDS = 60   # допуск на расхождение часов


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
        "current_goals": GOAL_BLOCK_DEFAULT_TEXT,
    }

    def __init__(self, db_path: str = CORE_BLOCKS_DB_PATH) -> None:
        self.db_path = db_path
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
            present = {name for name, _, _ in rows}
            missing = [
                (name, content) for name, content in self._DEFAULT_BLOCKS.items()
                if name not in present
            ]
            if missing:
                now = datetime.now(UTC).isoformat()
                # Another instance may have populated a missing slot since our read.
                conn.executemany("""
                    INSERT INTO core_blocks (name, content, last_updated)
                    VALUES (?, ?, ?)
                    ON CONFLICT(name) DO NOTHING
                """, [(name, content, now) for name, content in missing])
                rows = conn.execute(
                    "SELECT name, content, last_updated FROM core_blocks"
                ).fetchall()
                conn.commit()
        finally:
            conn.close()

    @property
    def blocks(self) -> dict[str, CoreMemoryBlock]:
        """A fresh committed snapshot, coherent across worker instances/processes."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("SELECT name, content, last_updated FROM core_blocks").fetchall()
            return {name: CoreMemoryBlock(name, content, updated) for name, content, updated in rows}
        finally:
            conn.close()

    def update(self, name: str, content: str) -> None:
        """Явное обновление блока. Не auto-overwrite.

        Запись проходит через ``mutation_gate`` (SAFE_MODE и отозванные
        полномочия блокируют её до первого обращения к SQLite).
        """
        mutation_gate.ensure_user_mutations_allowed("sleep_worker.core_blocks_update")
        now = datetime.now(UTC).isoformat()
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

    def _scoped_view(self, project_id: str | None) -> dict[str, str]:
        """Блоки, видимые проекту: общие блоки и ТОЛЬКО его собственный слот цели.

        Слоты ``current_goals:<project_id>`` принадлежат своим проектам. Проект по
        умолчанию видит неименованный ``current_goals``; любой другой проект видит
        свой слот (или текст по умолчанию), но не цель проекта по умолчанию и не цели
        других проектов. ``blocks``/``get`` остаются сырым доступом без фильтра.
        """
        pid = project_id or DEFAULT_PROJECT_ID
        raw = self.blocks
        view = {
            name: block.content
            for name, block in raw.items()
            if not name.startswith(GOAL_BLOCK_NAME + ":")
        }
        if pid != DEFAULT_PROJECT_ID:
            own = raw.get(f"{GOAL_BLOCK_NAME}:{pid}")
            view[GOAL_BLOCK_NAME] = own.content if own else GOAL_BLOCK_DEFAULT_TEXT
        return view

    def get_system_context(
        self, project_id: str | None = None, goal_text: str | None = None
    ) -> str:
        """
        Собрать блоки проекта для system prompt.
        Результат всегда ~500 токенов — не зависит от размера графа.

        ``goal_text`` — авторитетная формулировка цели (из NotebookStore); она заменяет
        сохранённую проекцию, которая может отставать после сбоя второй записи.
        """
        view = self._scoped_view(project_id)
        if goal_text is not None:
            view[GOAL_BLOCK_NAME] = goal_text
        return "\n\n".join(f"## {name}\n{content}" for name, content in view.items())

    def all_as_dict(self, project_id: str | None = None) -> dict[str, str]:
        return self._scoped_view(project_id)


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
    # ── Цель: принятая владельцем и предложенная моделью хранятся раздельно ──
    # current_goal меняет ТОЛЬКО SleepTimeWorker.accept_goal (решение владельца).
    # Фоновый анализ пишет лишь proposed_goal. MODEL OUTPUT ≠ OWNER DECISION.
    goal_revision:      int  = 0    # +1 при каждом решении владельца
    goal_decided_by:    str  = ""   # кто принял current_goal
    proposed_goal:      str  = ""   # предложение модели, не решение
    proposed_goal_at:   str  = ""
    proposed_goal_basis_revision: int = 0  # goal_revision, на котором сделано предложение
    proposed_goal_id:   str = ""   # идентификатор конкретного предложения (подтверждение привязано к нему)
    # Прежнее содержимое блока цели, замещённое при выравнивании проекции (история не удаляется).
    goal_projection_archive: list[dict] = field(default_factory=list)

    @property
    def goal_provenance(self) -> str:
        """NONE | OWNER_CONFIRMED | UNCONFIRMED_LEGACY.

        Цель без подтверждённого решения владельца (записана прежним фоновым
        перезаписыванием) не выдаётся за принятую; исходные данные не изменяются.
        """
        if not self.current_goal:
            return "NONE"
        if self.goal_revision > 0 and self.goal_decided_by:
            return "OWNER_CONFIRMED"
        return "UNCONFIRMED_LEGACY"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, s: str) -> "ResearchNotebook":
        raw = json.loads(s)
        known = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in raw.items() if k in known})


class NotebookConflictError(RuntimeError):
    """Блокнот изменён другим писателем после чтения (устаревшая запись отклонена)."""


class GoalRevisionConflictError(RuntimeError):
    """Решение владельца основано на устаревшей ревизии цели."""


class ProposalMismatchError(GoalRevisionConflictError):
    """Решение относится к другому предложению, чем сохранённое сейчас."""


class OwnerAuthorityError(PermissionError):
    """Решение владельца отсутствует, не подтверждено или не принадлежит этому воркеру."""


_DECISION_ACTIONS = ("accept_proposal", "set_goal")


def _proposal_id(project_id: str, goal: str, basis_revision: int, at: str) -> str:
    raw = json.dumps([project_id, goal, basis_revision, at], ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True)
class OwnerGoalDecision:
    """Подписанное решение владельца о цели одного проекта.

    Подпись (HMAC-SHA256, как у подписанных operator-решений Reader Core) связывает
    проект, действие, ожидаемую ревизию цели, конкретное предложение либо текст цели,
    автора и время. Строка ``decided_by`` сама по себе ничего не разрешает.
    Повтор решения невозможен: после принятия ревизия цели растёт.
    """

    project_id: str
    action: str
    expected_goal_revision: int
    proposal_id: str
    goal: str
    decided_by: str
    issued_at: str
    key_id: str
    signature_hex: str

    def signed_payload(self) -> bytes:
        return _decision_payload(
            project_id=self.project_id, action=self.action,
            expected_goal_revision=self.expected_goal_revision,
            proposal_id=self.proposal_id, goal=self.goal, decided_by=self.decided_by,
            issued_at=self.issued_at, key_id=self.key_id,
        )


def _decision_payload(*, project_id: str, action: str, expected_goal_revision: int,
                      proposal_id: str, goal: str, decided_by: str, issued_at: str,
                      key_id: str) -> bytes:
    return json.dumps(
        {
            "domain": OWNER_DECISION_DOMAIN,
            "project_id": project_id,
            "action": action,
            "expected_goal_revision": expected_goal_revision,
            "proposal_id": proposal_id,
            "goal_sha256": hashlib.sha256(goal.encode("utf-8")).hexdigest(),
            "decided_by": decided_by,
            "issued_at": issued_at,
            "key_id": key_id,
        },
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")


def issue_owner_goal_decision(
    *, key_id: str, secret: bytes, project_id: str, action: str,
    expected_goal_revision: int, decided_by: str,
    proposal_id: str = "", goal: str = "", issued_at: datetime | None = None,
) -> OwnerGoalDecision:
    """Подписать решение владельца. Вызывает тот, кто держит секрет развёртывания."""
    if action not in _DECISION_ACTIONS:
        raise ValueError(f"action must be one of {_DECISION_ACTIONS}")
    if not (decided_by or "").strip() or not (key_id or "").strip() or not (project_id or "").strip():
        raise ValueError("project_id, key_id and decided_by are required")
    if action == "accept_proposal" and (not proposal_id or goal):
        raise ValueError("accept_proposal names a proposal_id and carries no goal text")
    if action == "set_goal" and (not goal.strip() or proposal_id):
        raise ValueError("set_goal carries the goal text and no proposal_id")
    stamp = (issued_at or datetime.now(UTC)).astimezone(UTC).isoformat()
    payload = _decision_payload(
        project_id=project_id, action=action, expected_goal_revision=expected_goal_revision,
        proposal_id=proposal_id, goal=goal.strip(), decided_by=decided_by.strip(),
        issued_at=stamp, key_id=key_id,
    )
    return OwnerGoalDecision(
        project_id=project_id, action=action, expected_goal_revision=expected_goal_revision,
        proposal_id=proposal_id, goal=goal.strip(), decided_by=decided_by.strip(),
        issued_at=stamp, key_id=key_id,
        signature_hex=hmac.new(secret, payload, hashlib.sha256).hexdigest(),
    )


@dataclass(frozen=True)
class OwnerGoalAuthority:
    """Проверяющая сторона решений владельца; секрет задаёт развёртывание.

    Воркер без такого объекта не принимает цели вообще (путь недоступен). Ничто в
    фоновом анализе, HTTP/MCP-маршрутах или LLM-вызовах этот объект не создаёт.
    ``revoked_key_ids`` отзывает ключ: его прежние решения перестают приниматься.
    """

    key_id: str
    secret: bytes = field(repr=False)
    revoked_key_ids: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not (self.key_id or "").strip():
            raise ValueError("key_id is required")
        if not isinstance(self.secret, bytes) or len(self.secret) < 16:
            raise ValueError("secret must be at least 16 bytes")

    def verify(self, decision: OwnerGoalDecision, *, project_id: str, now: datetime) -> None:
        if not isinstance(decision, OwnerGoalDecision):
            raise OwnerAuthorityError("a signed OwnerGoalDecision is required")
        if decision.key_id != self.key_id or decision.key_id in self.revoked_key_ids:
            raise OwnerAuthorityError("decision key is unknown or revoked")
        expected = hmac.new(self.secret, decision.signed_payload(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(decision.signature_hex, expected):
            raise OwnerAuthorityError("decision signature is invalid")
        if decision.project_id != project_id:
            raise OwnerAuthorityError("decision belongs to another project")
        if decision.action not in _DECISION_ACTIONS:
            raise OwnerAuthorityError("unknown decision action")
        try:
            issued = datetime.fromisoformat(decision.issued_at)
        except ValueError as exc:
            raise OwnerAuthorityError("decision time is malformed") from exc
        if issued.tzinfo is None:
            raise OwnerAuthorityError("decision time must be timezone-aware")
        age = (now - issued).total_seconds()
        if age > OWNER_DECISION_MAX_AGE_SECONDS or age < -OWNER_DECISION_MAX_SKEW_SECONDS:
            raise OwnerAuthorityError("decision is expired or issued in the future")


@dataclass(frozen=True)
class _AnalysisBasis:
    """Основание фонового анализа: на чём он был посчитан."""

    goal_revision: int
    current_goal: str
    fact_ids: frozenset[str]
    questions: frozenset[str]

    @staticmethod
    def _fact_id(fact: dict) -> str:
        raw = f"{fact.get('at', '')}|{fact.get('content', '')}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def of(cls, nb: "ResearchNotebook") -> "_AnalysisBasis":
        return cls(
            goal_revision=nb.goal_revision,
            current_goal=nb.current_goal,
            fact_ids=frozenset(cls._fact_id(f) for f in nb.known_facts),
            questions=frozenset(nb.key_questions),
        )

    def holds_for(self, fresh: "ResearchNotebook") -> tuple[bool, bool]:
        """(рамка цели не изменилась, исходные факты и вопросы не исчезли и не изменились)."""
        now = _AnalysisBasis.of(fresh)
        framing = (now.goal_revision, now.current_goal) == (self.goal_revision, self.current_goal)
        inputs = self.fact_ids <= now.fact_ids and self.questions <= now.questions
        return framing, inputs


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
        """Безусловная запись (для миграций и тестов). Воркер использует compare_and_save."""
        mutation_gate.ensure_user_mutations_allowed("sleep_worker.notebook_save")
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

    def compare_and_save(self, nb: ResearchNotebook, expected_version: int | None) -> bool:
        """Записать блокнот, только если сохранённая версия всё ещё ``expected_version``.

        ``expected_version=None`` означает «строки ещё нет». Возвращает False, если
        между чтением и записью блокнот изменил другой писатель (другой процесс,
        решение владельца): устаревший результат не перезаписывает более свежий.
        Запись проходит через ``mutation_gate``.
        """
        mutation_gate.ensure_user_mutations_allowed("sleep_worker.notebook_save")
        now = datetime.now(UTC).isoformat()
        conn = sqlite3.connect(self.db_path)
        try:
            if expected_version is None:
                cur = conn.execute("""
                    INSERT INTO notebooks (project_id, data, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(project_id) DO NOTHING
                """, (nb.project_id, nb.to_json(), now))
            else:
                cur = conn.execute("""
                    UPDATE notebooks SET data = ?, updated_at = ?
                    WHERE project_id = ? AND json_extract(data, '$.version') = ?
                """, (nb.to_json(), now, nb.project_id, expected_version))
            conn.commit()
            return cur.rowcount == 1
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
        owner_authority: OwnerGoalAuthority | None = None,
    ) -> None:
        self.project_id     = project_id
        self.idle_timeout   = idle_timeout
        self.sleep_interval = sleep_interval

        # RISK-1 (PDR-033): core_blocks опционален — не AttributeError если None
        self.core_blocks    = core_blocks
        self._nb_store      = notebook_store or NotebookStore()
        self._llm_fn        = llm_fn  # callable(prompt) → str, None = mock
        # Без authority принятие цели недоступно: accept_goal закрыт для любого вызывающего.
        self._owner_authority = owner_authority
        self.goal_projection_in_sync = True

        self._notebook: ResearchNotebook | None = None
        self._lock          = asyncio.Lock()
        self._task: asyncio.Task | None = None
        self._bg_tasks: set[asyncio.Task] = set()
        self._stopped       = False
        self._last_activity = time.monotonic()
        self._last_cycle_at = 0.0  # RISK-5 (PDR-033): отдельный счётчик цикла
        self._facts_since_synthesis = 0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Запустить фоновый цикл (повторный start не создаёт второй цикл)."""
        if self._task is not None and not self._task.done():
            return
        self._stopped = False
        self._notebook = self._nb_store.load(self.project_id) or ResearchNotebook(
            project_id=self.project_id
        )
        # Проекция цели в CoreMemoryBlocks догоняет авторитетную запись после сбоя/падения.
        self._project_goal_locked()
        # BUG-3 (PDR-033): сохраняем ссылку на task — иначе silent GC death
        self._task = asyncio.create_task(self._sleep_loop())
        logger.info("SleepTimeWorker: запущен (project=%s)", self.project_id)

    async def stop(self) -> None:
        """
        Остановить worker.
        BUG-3 (PDR-033): stop() должен cancel() task + await CancelledError.
        """
        self._stopped = True
        tasks = set(self._bg_tasks)
        if self._task is not None:
            tasks.add(self._task)
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._bg_tasks.clear()
        self._task = None
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
            fresh = self._load_fresh_locked()
            recent_context = self._build_recent_context()
            facts_since_snapshot = self._facts_since_synthesis
            basis = _AnalysisBasis.of(fresh)

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
        # Результат фонового анализа — НЕ решение владельца и применяется к СВЕЖЕМУ
        # сохранённому состоянию. Предложение цели, пробелы и синтез посчитаны на
        # конкретном основании (рамка цели, факты и вопросы); если основание
        # изменилось к моменту записи, результат отбрасывается, а не дописывается.
        # current_goal и CoreMemoryBlocks здесь не трогаются.
        applied: dict[str, bool] = {"synthesis": False}

        def apply(nb: ResearchNotebook) -> None:
            framing_ok, inputs_ok = basis.holds_for(nb)
            if framing_ok and inputs_ok:
                if new_goal and new_goal != nb.current_goal:
                    at = datetime.now(UTC).isoformat()
                    nb.proposed_goal = new_goal
                    nb.proposed_goal_at = at
                    nb.proposed_goal_basis_revision = nb.goal_revision
                    nb.proposed_goal_id = _proposal_id(
                        nb.project_id, new_goal, nb.goal_revision, at
                    )
                    logger.info(
                        "SleepTimeWorker: предложена цель (не принята): '%s'", new_goal[:50]
                    )
                known = {g.get("gap") for g in nb.open_gaps}
                for gap in gaps:
                    if len(nb.open_gaps) < MAX_OPEN_GAPS and gap.get("gap") not in known:
                        nb.open_gaps.append({**gap, "basis_goal_revision": nb.goal_revision})
                if synthesis:
                    nb.synthesis_history.append({
                        "at":      datetime.now(UTC).isoformat(),
                        "content": synthesis,
                        "basis_goal_revision": nb.goal_revision,
                    })
                    applied["synthesis"] = True
            elif new_goal or gaps or synthesis:
                logger.info(
                    "SleepTimeWorker: основание анализа изменилось (рамка цели: %s, факты и вопросы: %s), "
                    "предложение, пробелы и синтез отброшены",
                    "прежняя" if framing_ok else "изменена",
                    "целы" if inputs_ok else "изменены",
                )
            nb.last_thought = datetime.now(UTC).isoformat()

        async with self._lock:
            if not self._notebook:
                # Notebook могли закрыть пока мы думали — gracefully выходим
                return
            try:
                self._commit_locked(apply)
            except mutation_gate.UserMutationBlockedError as exc:
                # Запись запрещена (SAFE_MODE / отозванные полномочия): анализ не сохраняем.
                logger.warning(
                    "SleepTimeWorker: запись блокнота запрещена (%s), результат отброшен",
                    exc.reason_code,
                )
                return
            except NotebookConflictError:
                logger.warning("SleepTimeWorker: блокнот изменён другим писателем, результат отброшен")
                return
            if applied["synthesis"]:
                self._facts_since_synthesis = 0
                logger.info("SleepTimeWorker: синтез сгенерирован")
            self._project_goal_locked()

    # ── Решение владельца о цели ──────────────────────────────────────────────

    async def accept_goal(self, decision: OwnerGoalDecision) -> ResearchNotebook:
        """Принять цель по подписанному решению владельца. Единственный путь ``current_goal``.

        Источник истины о принятой цели — строка блокнота в ``NotebookStore``. Решение
        должно быть подписано ключом развёртывания (``OwnerGoalAuthority``), относиться к
        этому проекту, не быть просроченным и быть привязано к ревизии цели и — для
        принятия предложения — к конкретному ``proposal_id``. Без настроенного
        authority путь закрыт. Строка ``decided_by`` сама по себе ничего не разрешает.
        Проекция цели в CoreMemoryBlocks обновляется ПОСЛЕ фиксации в блокноте и не
        является источником истины: при её сбое решение остаётся в силе, а чтение
        через ``system_context()`` берёт цель из блокнота.
        PROPOSAL ≠ ADMISSION; INITIATIVE ≠ AUTHORIZATION.
        """
        self._verify_decision(decision)           # быстрый отказ до ожидания блокировки
        async with self._lock:
            if not self._notebook:
                raise RuntimeError("worker is not started")

            def apply(nb: ResearchNotebook) -> None:
                # Выполняется после получения блокировки и на КАЖДОЙ повторной попытке записи.
                # Подпись, срок, проект и ключ проверяются заново: за время ожидания блокировки
                # или конкуренции за запись решение могло истечь, а ключ — быть отозван.
                self._verify_decision(decision)
                # Ревизия цели тоже проверяется заново: конкурентное решение
                # другого процесса делает это решение устаревшим.
                if nb.goal_revision != decision.expected_goal_revision:
                    raise GoalRevisionConflictError(
                        f"goal revision is {nb.goal_revision}, "
                        f"decision was based on {decision.expected_goal_revision}"
                    )
                if decision.action == "accept_proposal":
                    if not nb.proposed_goal or nb.proposed_goal_id != decision.proposal_id:
                        raise ProposalMismatchError(
                            "decision names a proposal that is not the stored one"
                        )
                    chosen = nb.proposed_goal
                else:
                    chosen = decision.goal
                previous = nb.current_goal
                nb.current_goal = chosen
                nb.goal_revision += 1
                nb.goal_decided_by = decision.decided_by
                nb.extracted_intents.append({
                    "kind":        "owner_decision",
                    "goal":        chosen,
                    "prev_goal":   previous,
                    "decided_by":  decision.decided_by,
                    "key_id":      decision.key_id,
                    "action":      decision.action,
                    "proposal_id": decision.proposal_id,
                    "at":          datetime.now(UTC).isoformat(),
                })
                # Любое предложение, сделанное на прежней ревизии, устарело.
                nb.proposed_goal = ""
                nb.proposed_goal_at = ""
                nb.proposed_goal_id = ""
                nb.proposed_goal_basis_revision = nb.goal_revision

            nb = self._commit_locked(apply)
            self._project_goal_locked()
            return nb

    def _verify_decision(self, decision: OwnerGoalDecision) -> None:
        """Проверить решение по текущему authority и текущему времени (вызывается повторно)."""
        authority = self._owner_authority
        if authority is None:
            raise OwnerAuthorityError(
                "owner authority is not configured for this worker; accepting goals is unavailable"
            )
        authority.verify(decision, project_id=self.project_id, now=datetime.now(UTC))

    # ── Авторитетное чтение и проекция цели ───────────────────────────────────

    def _goal_block_name(self) -> str:
        """Слот проекции цели: общий для проекта по умолчанию, отдельный для остальных."""
        if self.project_id == DEFAULT_PROJECT_ID:
            return GOAL_BLOCK_NAME
        return f"{GOAL_BLOCK_NAME}:{self.project_id}"

    @staticmethod
    def _goal_context_text(nb: ResearchNotebook | None) -> str | None:
        """Как цель выглядит в system prompt; неподтверждённая цель помечена как таковая."""
        if nb is None or nb.goal_provenance == "NONE":
            return GOAL_BLOCK_DEFAULT_TEXT
        if nb.goal_provenance == "OWNER_CONFIRMED":
            return f"Активная цель: {nb.current_goal}"
        return (
            "Цель НЕ подтверждена владельцем (происхождение неизвестно, записана "
            f"прежним фоновым процессом): {nb.current_goal}"
        )

    def system_context(self) -> str:
        """Блоки system prompt ЭТОГО проекта; цель берётся из авторитетной записи блокнота."""
        if self.core_blocks is None:
            return ""
        stored = self._nb_store.load(self.project_id) or self._notebook
        return self.core_blocks.get_system_context(
            self.project_id, goal_text=self._goal_context_text(stored)
        )

    def _project_goal_locked(self) -> bool:
        """Привести проекцию цели в CoreMemoryBlocks к записи блокнота. True — совпадает.
        Результат также доступен как ``goal_projection_in_sync``.

        Проецируется только подтверждённая цель. Ошибка записи проекции не откатывает
        решение владельца: она логируется, а следующий start/think/accept повторяет
        попытку (операция идемпотентна и сверяется с блокнотом после записи).
        """
        in_sync = self._project_goal_impl()
        self.goal_projection_in_sync = in_sync
        return in_sync

    def _project_goal_impl(self) -> bool:
        if self.core_blocks is None:
            return True
        name = self._goal_block_name()
        try:
            for _ in range(3):
                nb = self._nb_store.load(self.project_id)
                if nb is None:
                    return True               # нет авторитетной записи — нечего проецировать
                # Проекция всегда равна тому, что видит system_context(): принятая цель,
                # помеченная неподтверждённая или текст по умолчанию. Никогда не «принятая»
                # цель, которой владелец не принимал.
                want = str(self._goal_context_text(nb))
                current = self.core_blocks.get(name)
                if current != want:
                    if current and self._is_unrecorded_projection(nb, current):
                        self._archive_projection_locked(nb, name, current)
                    self.core_blocks.update(name, want)
                latest = self._nb_store.load(self.project_id)
                if latest is not None and self._goal_context_text(latest) == want \
                        and self.core_blocks.get(name) == want:
                    return True
            return False
        except Exception as exc:  # noqa: BLE001 - projection is derived state, never authority
            logger.warning("SleepTimeWorker: проекция цели не обновлена: %s", exc)
            return False

    @staticmethod
    def _is_unrecorded_projection(nb: ResearchNotebook, content: str) -> bool:
        """Содержимое блока, о котором в блокноте нет записи: его нужно сохранить до замены.

        Не требует архивации: текст по умолчанию, наша пометка о неподтверждённой цели и
        «Активная цель: …» для цели, принятой решением владельца (она есть в extracted_intents).
        """
        if content == GOAL_BLOCK_DEFAULT_TEXT or content.startswith("Цель НЕ подтверждена"):
            return False
        decided = {
            f"Активная цель: {i.get('goal')}"
            for i in nb.extracted_intents if i.get("kind") == "owner_decision"
        }
        return content not in decided

    def _archive_projection_locked(self, nb: ResearchNotebook, name: str, content: str) -> None:
        """Сохранить прежний текст блока цели в блокноте проекта (только добавление)."""
        if any(e.get("block") == name and e.get("content") == content
               for e in nb.goal_projection_archive):
            return                            # уже сохранено (повтор после сбоя записи блока)

        def apply(fresh: ResearchNotebook) -> None:
            if any(e.get("block") == name and e.get("content") == content
                   for e in fresh.goal_projection_archive):
                return
            fresh.goal_projection_archive.append({
                "block": name,
                "content": content,
                "goal_provenance": fresh.goal_provenance,
                "replaced_at": datetime.now(UTC).isoformat(),
            })

        self._commit_locked(apply)

    def _load_fresh_locked(self) -> ResearchNotebook:
        """Сохранённое состояние проекта (его мог изменить другой процесс); иначе кэш."""
        stored = self._nb_store.load(self.project_id)
        if stored is not None:
            self._notebook = stored
            return stored
        assert self._notebook is not None
        return self._notebook

    def _commit_locked(self, apply: Callable[[ResearchNotebook], None]) -> ResearchNotebook:
        """Прочитать свежее состояние, применить изменение, записать сравнением версий.

        Вызывать под ``self._lock``. Устаревший снимок не может перезаписать более
        свежую запись: при расхождении версии чтение и применение повторяются.
        """
        for _ in range(COMMIT_RETRIES):
            stored = self._nb_store.load(self.project_id)
            if stored is None:
                base = ResearchNotebook.from_json(self._notebook.to_json()) if self._notebook \
                    else ResearchNotebook(project_id=self.project_id)
                expected: int | None = None
            else:
                base = stored
                expected = stored.version
            apply(base)
            base.version = (expected or base.version) + 1
            if self._nb_store.compare_and_save(base, expected):
                self._notebook = base
                return base
        raise NotebookConflictError(f"notebook {self.project_id!r} kept changing; write abandoned")

    # ── Обновление из эпизода (вызывается при каждом сообщении) ──────────────

    async def update_from_episode(self, episode: dict[str, Any]) -> None:
        """
        Вызывается при каждом сообщении пользователя.
        Записывает факты и вопросы, запускает think() в фоне.
        """
        content = episode.get("content", "")
        source = episode.get("source", "user")
        added_fact = bool(content and len(content) > 20)

        def apply(nb: ResearchNotebook) -> None:
            # Извлекаем вопросы простой эвристикой
            if "?" in content:
                questions = [
                    q.strip() + "?"
                    for q in content.split("?")
                    if len(q.strip()) > 15
                ][:3]
                for q in questions:
                    if q not in nb.key_questions:
                        nb.key_questions.append(q)

            # Простой факт из эпизода
            if added_fact:
                nb.known_facts.append({
                    "content": content[:300],
                    "source":  source,
                    "at":      datetime.now(UTC).isoformat(),
                })

        async with self._lock:
            if not self._notebook:
                return
            # Запрет мутаций (SAFE_MODE / отозванные полномочия) поднимается вызывающему.
            self._commit_locked(apply)
            if added_fact:
                self._facts_since_synthesis += 1

        self.notify_activity()
        # FIX v8.5.1 (Gemini): сохраняем ссылку на task —
        # иначе Python GC может уничтожить task прямо во время выполнения
        if self._stopped or self._bg_tasks:
            return  # Coalesce episode bursts into the one owned background cycle.
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
            "proposed_goal":     nb.proposed_goal if nb else "",
            "proposed_goal_id":  nb.proposed_goal_id if nb else "",
            "goal_status":       nb.goal_provenance if nb else "NONE",
            "goal_revision":     nb.goal_revision if nb else 0,
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
                        "question": q,
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
    owner_authority: OwnerGoalAuthority | None = None,
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
        owner_authority=owner_authority,
    )
