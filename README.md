# 🔱 VELANTRIM TITAN 9.0

**Русский** · [English](README.en.md)

> **Local-first проверяемая память для AI-агентов:** evidence-gated знания,
> явные эпистемические состояния, provenance, TRACE и заменяемый языковой слой.
>
> **Зрелость:** research-grade prototype, движущийся к production hardening.

[🗺️ Экскурсия по системе](SYSTEM_OVERVIEW.md) ·
[📊 Честный статус](docs/PROJECT_STATUS.md) ·
[🔍 Для аудитора](docs/REVIEWER_README.md) ·
[🔒 Security](SECURITY.md) ·
[🏛️ Канон истины](docs/TRUTH_AND_RINGZERO_CANON.ru.md)

---

## 👋 Titan за 60 секунд

Обычный LLM часто смешивает память, поиск, уверенность и красивую формулировку
в один непрозрачный ответ. Titan разделяет эти полномочия:

```text
Обычный LLM
  💬 prompt → 🤖 model → 🗣️ fluent answer

Velantrim Titan
  👤 query
     → 🧠 memory
     → 🔍 retrieval
     → 📦 evidence
     → ⚖️ policy / TruthGate
     → 🧾 TRACE
     → 🗣️ replaceable LLM voice
```

### Простыми словами

Titan похож на библиотеку, где:

- 📚 библиотекарь находит записи;
- 🧪 лаборант сохраняет источник и неопределённость;
- 🛂 проверочный шлюз ограничивает доверенное повышение статуса;
- 🧾 аудитор оставляет проверяемый след;
- 🗣️ LLM объясняет отобранные сведения понятным языком.

### Инженерным языком

Titan — local-first memory runtime с ESM, гибридным retrieval, контролируемой
write boundary, provenance/TRACE и feature-gated исследовательскими слоями.
LLM может читать, извлекать и формулировать, но не получает автоматического
права записать свой вывод в Canon.

> 🧭 Нужна подробная схема? Откройте
> **[Living System Atlas](SYSTEM_OVERVIEW.md)** и выберите маршрут:
> простой, операторский, инженерный или аудиторский.

---

## 🧭 Что открыть первым

| Если вы… | Начните здесь |
|---|---|
| 👤 впервые видите проект | [Atlas: объяснение за 30 секунд](SYSTEM_OVERVIEW.md#plain) |
| 🛠️ запускаете свою установку | [Быстрый старт](#quick-start) и [Security](SECURITY.md) |
| 🧑‍💻 собираетесь менять код | [Atlas: инженерные границы](SYSTEM_OVERVIEW.md#engineer) и [`AGENTS.md`](AGENTS.md) |
| 🧠 изучаете долговременный контекст для Codex, Copilot и code review | [Project Cognition & Code Review](docs/use_cases/PROJECT_COGNITION_AND_CODE_REVIEW.md) |
| 🔍 проверяете заявления | [`docs/REVIEWER_README.md`](docs/REVIEWER_README.md) |
| 💼 оцениваете зрелость или финансирование | [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) |
| 🧪 проектируете нагрузочные испытания | [Atlas: Architecture Assurance](SYSTEM_OVERVIEW.md#assurance) |
| 🔬 изучаете будущие идеи | [`research/`](research/) и [Architecture Axes](research/ARCHITECTURE_AXES.md) |

---

## 🗺️ Система одним взглядом

```text
┌────────────────────── 🌍 ЧЕЛОВЕК / АГЕНТ / ФАЙЛ ─────────────────────┐
└────────────────────────────────┬──────────────────────────────────────┘
                                 ▼
                    🔐 API · auth · policy · egress
                                 │
                ┌────────────────┴────────────────┐
                ▼                                 ▼
        🔎 read / retrieval               ✍️ explicit write
                │                                 │
                ▼                                 ▼
        📦 FactsPack + TRACE               🧠 ESM + evidence
                │                                 │
                ▼                                 ▼
        🛡️ Guardian / policy               ⚖️ TruthGate / CAS
                │                                 │
                └──────────────┬──────────────────┘
                               ▼
                     🧾 provenance · audit
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
       ⚡ indexes / projections           🗣️ replaceable LLM
```

Главная архитектурная граница:

```text
LLM предлагает.
Policy ограничивает полномочия.
Проверяемая write boundary допускает изменение.
TRACE и audit показывают, что произошло.
```

---

## 🧾 Честная легенда статусов

| Метка | Что можно утверждать |
|---|---|
| 🟢 **default path** | относится к базовому рабочему пути |
| ✅ **main / tested** | код и проверяющие тесты находятся в `main` |
| 🟡 **available / gated** | код существует, включение зависит от ENV/профиля |
| 🚧 **open PR** | ещё не является частью `main` |
| 🔬 **research / proposed** | идея описана, runtime authority отсутствует |
| ⚠️ **known limitation** | ограничение признано и не скрывается |
| 📡 **runtime observed** | подтверждено конкретным запущенным экземпляром |

```text
📄 файл есть
   ≠ 🧪 контракт доказан тестом
   ≠ 🎛️ функция включена
   ≠ 🔗 функция подключена к нужному пути
   ≠ 📡 она наблюдалась в этом runtime
```

Актуальное состояние конкретной установки проверяется через конфигурацию,
`/health`, `/layers/status` и `/titan/status`, а не по одному README.

---

## ✅ Что находится в текущем инженерном основании

| Область | Роль | Основные файлы |
|---|---|---|
| 🧠 Memory + ESM | факты, 8 эпистемических состояний, temporal state | `core/memory.py` |
| ⚖️ Trust boundary | evidence/confidence policy и write admission | `core/truth_gate.py`, `core/write_gate.py`, `core/policy_kernel.py` |
| 🔍 Retrieval | BM25, dense/graph signals и candidate narrowing | `core/hybrid_retriever.py`, `core/ngram_index.py` |
| 🧾 Provenance | источник, append-only след, audit artifacts | `core/provenance_chain.py`, `core/audit_chain.py` |
| 🛡️ Integrity | health states, snapshots, executable invariants | `core/meta_supervisor.py`, `core/immutable_core_scheduler.py`, `tests/test_invariants.py` |
| 🔐 Remote boundary | policy lease для удалённого провайдера | `core/remote_egress.py` |
| 📄 Synaptic foundation | source-linked capsules и reader contract | `core/knowledge_capsule.py`, `core/semantic_reader.py` |
| 🌐 API + Console | FastAPI surface и browser UI | `server.py`, `api/`, `static/console/` |

> ⚠️ Наличие компонента в таблице не означает, что он включён каждым профилем
> или что все callers уже унифицированы под одной policy. Границы и открытый
> долг перечислены в [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).

<details>
<summary><strong>🧠 Расширенные когнитивные и операционные модули</strong></summary>

Многие верхние слои существуют как feature-gated research-grade код:

| Область | Примеры |
|---|---|
| 🧭 Attention / focus | `GoalFrame`, `AttentionRouter`, `ComputeController` |
| 🕸️ Causal / graph | causal retrieval, graph analysis, reasoning bank |
| 🌱 Adaptive memory | decay, reconsolidation, salience, concept emergence |
| 🛡️ Response controls | output faithfulness, response guardian, circuit breaker |
| 🧬 Identity / welfare | identity traceability, welfare MVP, Innenwelt/Umwelt |
| 🧪 Research UI | separate Research Mode and browser research app |

Перед эксплуатационным заявлением проверяйте `core/feature_config.py`,
`/layers/status`, `/titan/status` и реальные метрики.

</details>

---

## 📄 Synaptic Exo-Cortex

Synaptic profile превращает длинные источники в проверяемые смысловые капсулы:

```text
📄 Raw evidence
   → ✅ SemanticReader
   → ✅ KnowledgeCapsule + exact SourceSpan
   → 🚧 LLM Reader Adapter
   → 🔬 Working Memory Gate
   → 🔬 ContextPack
   → 🔬 shadow evaluation
   → 👤 evidence-backed answer
```

Ключевые правила:

- точные source spans и SHA-256;
- `extraction_confidence` не смешивается с `truth_confidence`;
- capsule — proposal, не Canon;
- обычный query path должен стать read-only относительно Canon/ESM;
- модель остаётся provider-neutral и заменяемой;
- active integration допускается только после shadow evaluation.

📘 План:
[`docs/SYNAPTIC_EXO_CORTEX_IMPLEMENTATION_PLAN.md`](docs/SYNAPTIC_EXO_CORTEX_IMPLEMENTATION_PLAN.md)

### 🗂️ Working Desk

Working Desk сохранён в **Research Mode** как будущая task-aware композиция.
Он не является отдельным runtime-ядром и не получает власть над Canon.

```text
✅ foundation  → KnowledgeCapsule · SemanticReader · remote egress
🚧 engineering → LLM Reader Adapter
🔬 planned     → Working Memory Gate · ContextPack · shadow path
🔬 research    → Task Registry · Completion/Stagnation · Task Archive
```

📘 Registry:
[`research/WORKING_DESK_RESEARCH_MODE.md`](research/WORKING_DESK_RESEARCH_MODE.md)

---

## 🛡️ Что проект не обещает

- ❌ нулевые галлюцинации;
- ❌ абсолютную истинность любого источника;
- ❌ сертифицированную GDPR/compliance-программу;
- ❌ независимый security audit, которого ещё не было;
- ❌ production-ready multi-user SaaS «из коробки»;
- ❌ сознание или субъективный опыт;
- ❌ что каждый модуль в `core/` включён по умолчанию;
- ❌ что open PR или research-документ уже стали runtime.

Известные P0/P1/P2-риски:
[`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).

---

## 🖥️ Два режима использования

```text
┌─ 🖥️ Локальный runtime ────────────────────────────────────────────┐
│ FastAPI + local SQLite + optional graph/LLM providers             │
│ Полный API, policy boundaries, server-side memory                 │
│ http://127.0.0.1:8755/console/                                    │
└────────────────────────────────────────────────────────────────────┘

┌─ 📱 Browser PWA ───────────────────────────────────────────────────┐
│ IndexedDB + browser console + optional direct provider API         │
│ Отдельный browser-mode; не равен полному server runtime            │
│ Можно установить на Android/iOS/desktop                            │
└────────────────────────────────────────────────────────────────────┘
```

| Страница | Ссылка |
|---|---|
| 🌐 Портал | <https://velantrian.github.io/Velantrim-ExoCortex-Titan/> |
| 💬 Console PWA | <https://velantrian.github.io/Velantrim-ExoCortex-Titan/console/> |
| 🔬 Research PWA | <https://velantrian.github.io/Velantrim-ExoCortex-Titan/console/research-app.html> |
| 🗺️ Roadmap | <https://velantrian.github.io/Velantrim-ExoCortex-Titan/console/research-roadmap.html> |

> 📱 **Android:** Chrome → ⋮ → «Установить приложение».
>
> 🍎 **iPhone/iPad:** «Поделиться» → «На экран Домой».

Если GitHub Pages ещё не включён:
[`docs/GITHUB_PAGES_ENABLE.ru.md`](docs/GITHUB_PAGES_ENABLE.ru.md).

---

<a id="quick-start"></a>

## 🚀 Быстрый старт

### Вариант A — Docker

```bash
git clone https://github.com/velantrian/Velantrim-ExoCortex-Titan.git
cd Velantrim-ExoCortex-Titan

cp .env.example .env
# Укажите в .env безопасный VELANTRIM_API_KEY

docker compose up -d
```

После запуска проверьте:

```text
http://localhost:8000/health
```

### Вариант B — локальная разработка

```bash
python -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\activate

python -m pip install -e ".[server,dev]"
cp .env.example .env
# VELANTRIM_API_KEY=...

uvicorn server:app --port 8000 --reload
```

Проверка:

```bash
ruff check core/ --output-format=github
mypy core/ --show-error-codes
python -m pytest tests/ -v --tb=short
```

### Локальная web console

```powershell
cd "C:\path\to\Velantrim-ExoCortex-Titan"
.\scripts\start_console.ps1
```

Откройте:

```text
http://127.0.0.1:8755/console/
```

Обзор:
[`docs/CONSOLE_OVERVIEW.ru.md`](docs/CONSOLE_OVERVIEW.ru.md).

### Feature flags

Пример явного включения отдельных исследовательских слоёв:

```env
ENABLE_VELUM=1
ENABLE_ETIR=1
ENABLE_L45=1
ENABLE_L6_WELFARE=1
ENABLE_EVENT_BUS=1
```

Не включайте набор флагов вслепую. Сначала проверьте compute profile,
зависимости, ограничения и ожидаемое поведение деградации.

---

## 🧪 Как проект проверяет себя

```text
🧹 Ruff
   + 🧷 mypy
   + 🧪 full pytest
   + 🔒 executable invariants
   + 🐳 Docker checks
   = CI evidence, но не замена runtime-наблюдению
```

Для системной жизнеспособности нужен более широкий цикл:

```text
📐 capacity/failure model
   → 🧬 deterministic synthetic load
   → 💥 fault injection
   → 🕰️ soak tests
   → 📡 p50/p95/p99 + storage debt
   → 🔁 correction
```

Подробно:
[Architecture Assurance в Atlas](SYSTEM_OVERVIEW.md#assurance).

---

## 📚 Документация

### Начать отсюда

| Документ | Назначение |
|---|---|
| [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md) 🗺️ | многоуровневая экскурсия: plain ↔ engineer ↔ auditor |
| [`docs/use_cases/README.md`](docs/use_cases/README.md) 🧭 | подробные сценарии применения без перегрузки корневого README |
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) 📊 | зрелость, реальные риски, P0/P1/P2 |
| [`docs/REVIEWER_README.md`](docs/REVIEWER_README.md) 🔍 | карта файлов и проверок для аудитора |
| [`SECURITY.md`](SECURITY.md) 🔒 | threat model, auth, disclosure, ограничения |
| [`AGENTS.md`](AGENTS.md) 🤖 | обязательные правила для coding agents |

### Канон и архитектура

| Документ | Назначение |
|---|---|
| [`docs/TRUTH_AND_RINGZERO_CANON.ru.md`](docs/TRUTH_AND_RINGZERO_CANON.ru.md) 🏛️ | Truth Engine + Ring Zero |
| [`docs/FRACTAL_MEMORY_CANON.ru.md`](docs/FRACTAL_MEMORY_CANON.ru.md) 🌳 | Fractal Memory L0–L3 |
| [`docs/ATTENTION_NOETIC_ORCHESTRATION.ru.md`](docs/ATTENTION_NOETIC_ORCHESTRATION.ru.md) 🧭 | GoalFrame, AttentionRouter, ComputeController |
| [`research/ARCHITECTURE_AXES.md`](research/ARCHITECTURE_AXES.md) 🧩 | четыре ортогональные оси |
| [`docs/SYNAPTIC_EXO_CORTEX_IMPLEMENTATION_PLAN.md`](docs/SYNAPTIC_EXO_CORTEX_IMPLEMENTATION_PLAN.md) 📄 | executable Synaptic roadmap |

### Эксперименты

| Документ | Назначение |
|---|---|
| [`docs/RESEARCH_MODE.ru.md`](docs/RESEARCH_MODE.ru.md) 🔬 | отдельный experimental-контур |
| [`research/WORKING_DESK_RESEARCH_MODE.md`](research/WORKING_DESK_RESEARCH_MODE.md) 🗂️ | Working Desk без runtime authority |
| [`research/FUTURE_COMPONENTS.md`](research/FUTURE_COMPONENTS.md) 🔭 | будущие компоненты |
| [`research/DEPRECATIONS.md`](research/DEPRECATIONS.md) 📋 | журнал устаревших технологий |

История V8.x и прежние формулировки сохранены в
[`CHANGELOG.md`](CHANGELOG.md) и `docs/archive/legacy/`.

---

## 🌿 Философия без подмены инженерии

- [`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md) — человеческая мотивация;
- [`docs/PHILOSOPHY_SPEC.md`](docs/PHILOSOPHY_SPEC.md) — границы для AI-агентов.

Философия объясняет, **зачем** строится система. Код, тесты, метрики и
инварианты показывают, **что она действительно делает**.

---

## 🧭 Версия

**<!-- SYNC:VERSION -->v9.0.0<!-- /SYNC:VERSION --> — VELANTRIM TITAN 9.0**

Единый источник версии: `pyproject.toml` / `core.__version__`.
История: [`CHANGELOG.md`](CHANGELOG.md).

> **Titan понимает и предлагает. Граница доверия проверяет и допускает.
> Kernel сохраняет инварианты. LLM остаётся заменяемым.**
