# 🔱 VELANTRIM TITAN 9.0

[English](README.md) · **Русский**

> 🗿 **Локальная память для работы с ИИ, где найденная информация ещё не означает разрешение доверять ей или действовать.**
>
> **Зачем:** ИИ-помощник может найти старую заметку «покупка согласована». Сам факт обнаружения записи не доказывает действующее одобрение. Titan разделяет поиск, происхождение, проверку и разрешённые изменения, чтобы предложение помощника не превратилось незаметно в решение человека.
>
> **Что существует:** исследовательский прототип памяти и оркестрации с явными границами доверия и записи, аудитом и опциональными интеграциями. **Не** сервис с разрешением на production-эксплуатацию и не гарантия правильных ответов.
>
> **Далее:** [объяснение за 60 секунд](#-titan-за-60-секунд) · [быстрый старт](#быстрый-старт) · [статус проекта](docs/PROJECT_STATUS.md)

> **Local-first проверяемая память для AI-агентов:** явные эпистемические
> состояния, контролируемые write/admission boundaries, provenance, TRACE, retrieval,
> tools и заменяемый LLM/provider layer.
>
> **Зрелость:** research-grade prototype, движущийся к production hardening.

[🤖 AI-агент: начать здесь](AGENTS.md) ·
[🗺️ Карта системы](SYSTEM_OVERVIEW.md) ·
[📊 Статус проекта](docs/PROJECT_STATUS.md) ·
[🔍 Для аудитора](docs/REVIEWER_README.md) ·
[🔒 Security](SECURITY.md) ·
[🏛️ Truth canon](docs/TRUTH_AND_RINGZERO_CANON.ru.md)

> 🤖 **AI coding agent или автоматизированный reviewer:** формальная точка входа —
> [`AGENTS.md`](AGENTS.md), затем маршрутизация задач в
> [`docs/ai/README.md`](docs/ai/README.md). Документация — карта, а не proof:
> существенные claims проверяются по exact code, tests, CI, выбранной конфигурации
> и observed runtime evidence.

---

## 👋 Titan за 60 секунд

Обычный LLM часто смешивает память, retrieval, уверенность, policy, tools и беглую
формулировку в один непрозрачный ответ. Titan разделяет эти ответственности:

```text
query / действие пользователя
  → memory + retrieval
  → admitted context / typed proposals
  → policy / TruthGate / write boundaries
  → TRACE / audit / provenance
  → tools или replaceable LLM/provider layer
```

Важный claim — не то, что Titan «знает истину». Важное свойство: retrieval, evidence,
permission, mutation, auditability и генерация языка не становятся одной властью молча.

```text
retrieval ≠ evidence
admission ≠ verification
confidence ≠ authority
model output ≠ Canon
TRACE membership ≠ semantic use ≠ answer support
CI green ≠ production authorization
```

Titan — local-first runtime памяти и оркестрации с явной машиной эпистемических
состояний (ESM), контролируемыми путями канонической мутации, hybrid retrieval,
поверхностями provenance/audit, remote-egress policy, аутентифицированными API/tool
поверхностями и feature-gated research-слоями. LLM может читать, извлекать, ранжировать,
суммировать или формулировать язык, но не получает автоматически право мутировать Canon.

---

## 🧭 Что открыть первым

| Вы… | Начать здесь |
|---|---|
| 🤖 AI coding agent / automated reviewer | [`AGENTS.md`](AGENTS.md) → [`docs/ai/README.md`](docs/ai/README.md) |
| 👤 Впервые смотрите Titan | [Карта системы](SYSTEM_OVERVIEW.md#plain) |
| 🛠️ Поднимаете свой инстанс | [Быстрый старт](#быстрый-старт) + [Security](SECURITY.md) |
| 🧑‍💻 Меняете код | [`AGENTS.md`](AGENTS.md) + [инженерные границы](SYSTEM_OVERVIEW.md#engineer) |
| 🔍 Аудируете claims | [`docs/REVIEWER_README.md`](docs/REVIEWER_README.md) |
| 💼 Оцениваете зрелость | [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) |
| 🧠 Изучаете project cognition / code review | [`docs/use_cases/PROJECT_COGNITION_AND_CODE_REVIEW.md`](docs/use_cases/PROJECT_COGNITION_AND_CODE_REVIEW.md) |
| 🔬 Читаете будущую работу | [`research/`](research/) + [`research/ARCHITECTURE_AXES.md`](research/ARCHITECTURE_AXES.md) |

---

## 🗺️ Система с высоты

```text
┌──────────────────── HUMAN / AGENT / FILE ─────────────────────┐
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
                     API · auth · policy
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
    read/retrieval         explicit write          tools/MCP
        │                      │                      │
        ▼                      ▼                      ▼
 admitted context          ESM + evidence        capability gate
 + TRACE                   + CAS/policy          + auth/session
        │                      │                      │
        └──────────────┬───────┴──────────────┬───────┘
                       ▼                      ▼
              provenance · audit       replaceable LLM
```

### Текущая read-path boundary

`core/pipeline.py::run()` read-only относительно canonical fact storage, ESM
promotion и causal-relation mutation. Стандартные callers `Validated` promotion идут
через проверенный путь `PromotionGateway`. Отдельные семейства мутаций — invalidation,
erasure, archival/redaction, relation lifecycle и compound supersession — сохраняют
собственные явные contracts.

### TRACE / evidence-use boundary

Titan может напрямую наблюдать стадии вроде retrieved/selected context, сериализации
в answer prompt, provider-specific packing/transmission и сохранённых trace-артефактов.
Это **не** доказывает, что модель семантически использовала конкретный item или что
item поддержал финальный ответ. Более сильные U/A claims требуют отдельного
attribution evidence.

---

## 🧾 Легенда статусов

| Метка | Значение |
|---|---|
| 🟢 **default path** | часть базового пути |
| ✅ **main / tested** | реализация и релевантные тесты есть в `main` |
| 🟡 **available / gated** | реализация есть, но profile/ENV/dependency решает использование |
| 🚧 **open PR** | предложенное изменение, ещё не часть `main` |
| 🔬 **research / proposed** | только design/research; без runtime authority |
| ⚠️ **known limitation** | признанный gap или ограниченный claim |
| 📡 **runtime observed** | подтверждено на конкретном running instance |

```text
implemented ≠ tested ≠ wired ≠ enabled ≠ observed
```

Для конкретной установки смотрите конфигурацию плюс `/health`, `/layers/status` и
`/titan/status`; не выводите live activation только из этого README.

---

## ✅ Текущий engineering foundation

| Область | Текущая роль | Основные файлы |
|---|---|---|
| 🧠 Memory + ESM | facts, 8 эпистемических состояний, temporal state | `core/memory.py` |
| ⚖️ Trust / write boundary | evidence/confidence policy и контролируемый admission | `core/truth_gate.py`, `core/write_gate.py`, `core/promotion_gateway.py`, `core/policy_kernel.py` |
| 🔍 Retrieval | lexical path плюс optional dense/graph signals и narrowing кандидатов | `core/hybrid_retriever.py`, `core/ngram_index.py` |
| 🧾 Provenance / audit | source lineage и auditable effects | `core/provenance_chain.py`, `core/audit_chain.py` |
| 🔐 Remote boundary | fail-closed capability lease + epistemic prompt guard | `core/remote_egress.py` |
| 🔌 MCP / tools | authenticated server gateway + capability-scoped JSON-RPC tools | `api/mcp_gateway.py`, `core/mcp_transport.py`, `core/tool_registry.py` |
| 📄 Synaptic foundation | source-linked capsules и reader contracts | `core/knowledge_capsule.py`, `core/semantic_reader.py` |
| 🌐 API + Console | FastAPI surface и browser UI | `server.py`, `api/`, `static/console/` |

### Retrieval precision

Hybrid retriever Titan поддерживает lexical/BM25-style retrieval, optional dense
embeddings, optional graph signals и ranking fusion. Это **не** значит, что каждая
установка выполняет каждый signal на каждом запросе. Базовый пакет не имеет обязательных
сторонних зависимостей; dense и некоторые enhanced retrieval paths требуют optional
extras/configuration и деградируют к более узким путям, когда они недоступны.

### MCP precision

На текущей проверенной базе MCP — больше, чем dormant-модуль. `server.py` импортирует
`api.mcp_gateway` и регистрирует его routes с той же границей `require_api_key`, что и
другие authenticated server surfaces. Gateway делегирует в `core.mcp_transport.McpHandler`
и применяет capability/session ceilings.

Это устанавливает **implemented + server-wired/auth-gated**. Это **не** устанавливает,
что конкретный deployment сейчас running, внешне exposed, observed, unrestricted или
production-authorized:

```text
implemented + wired
  ≠ enabled в выбранном deployment
  ≠ observed на running instance
  ≠ production authorization
```

---

## 📄 Synaptic Exo-Cortex

Текущий bounded status:

```text
Raw evidence
  → ✅ SemanticReader
  → ✅ KnowledgeCapsule + exact SourceSpan
  → ✅ LLM Reader Adapter
       main/tested; нет caller на server /query answer-path;
       standalone document-reading CLI использует scripts/read_document.py
  → ✅ Working Memory Gate
       main/tested; только shadow chain
  → ✅ ContextPack
       main/tested; только shadow chain
  → ✅ shadow evaluation
       main/tested; feature-gated; только qualifying POST /query responses;
       без answer authority
  → active answer authority
       НЕ передана Synaptic; LEGACY_QUERY остаётся authoritative
```

Каждый ✅ значит implemented/tested в `main`; это **не** значит enabled по умолчанию,
production-authorized или authoritative над answers. Shadow processing не пишет в
Canon/ESM и не получает active answer authority лишь потому, что wired как shadow logic.

Ключевые границы:

- exact source spans и SHA-256 provenance;
- `extraction_confidence` ≠ `truth_confidence`;
- capsule/proposal ≠ Canon;
- обычный `core/pipeline.py::run()` read-only относительно canonical fact/ESM и
  causal-relation mutation;
- model/provider layer остаётся replaceable;
- shadow evidence не авторизует active integration.

План: [`docs/SYNAPTIC_EXO_CORTEX_IMPLEMENTATION_PLAN.md`](docs/SYNAPTIC_EXO_CORTEX_IMPLEMENTATION_PLAN.md)

---

## 🛡️ Что Titan не обещает

- ❌ нулевые hallucinations;
- ❌ абсолютную истинность любого source;
- ❌ что retrieval/ranking доказывает evidence authority;
- ❌ certified GDPR/compliance status;
- ❌ независимый security audit, которого не было;
- ❌ drop-in production-ready multi-user SaaS;
- ❌ consciousness или subjective experience;
- ❌ что каждый модуль `core/` enabled по умолчанию;
- ❌ что open PR или research document уже является runtime behavior;
- ❌ что TRACE доказывает internal model use или causal answer support;
- ❌ что server wiring сам по себе доказывает deployed/observed production service.

Production-hardening риски и P0/P1/P2 ведутся в
[`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md). Отдельный bounded ledger
**V1 productization** может показывать V1 P0/P1 = 0; это **не** значит, что
production-hardening P0/P1 = 0 или production authorization.

---

<a id="quick-start"></a>

## 🚀 Быстрый старт

### Hardened deployment profile

```bash
git clone https://github.com/velantrian/Velantrim-ExoCortex-Titan.git
cd Velantrim-ExoCortex-Titan
cp .env.prod.example .env.prod
# Задайте сильный VELANTRIM_API_KEY в .env.prod.
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

Hardened profile — это application/container hardening profile, а не claim о
host-level firewall/TLS/WAF, compliance или production authorization. Читайте
[`docs/operations/hardened-production-profile.md`](docs/operations/hardened-production-profile.md).

Проверка:

```text
http://127.0.0.1:8000/health
```

### Локальная разработка

```bash
python -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\activate
python -m pip install -e ".[server,dev]"
cp .env.example .env
# VELANTRIM_API_KEY=...
uvicorn server:app --port 8000 --reload
```

Базовая verification:

```bash
ruff check core/ --output-format=github
mypy core/ --show-error-codes
python -m pytest tests/ -v --tb=short
```

---

## 📚 Документация

| Документ | Назначение |
|---|---|
| [`AGENTS.md`](AGENTS.md) 🤖 | формальная точка входа и обязательные правила для coding agents |
| [`docs/ai/README.md`](docs/ai/README.md) 🧭 | AI context routing и minimum-reading paths |
| [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md) 🇷🇺 | русская карта системы |
| [`SYSTEM_OVERVIEW.en.md`](SYSTEM_OVERVIEW.en.md) 🗺️ | English system tour |
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) 📊 | зрелость и production-hardening P0/P1/P2 |
| [`docs/REVIEWER_README.md`](docs/REVIEWER_README.md) 🔍 | карта для независимого review |
| [`SECURITY.md`](SECURITY.md) 🔒 | threat model и deployment boundaries |
| [`research/`](research/) 🔬 | proposed/research work; не runtime authority |

---

## 🌐 Языковая стратегия

Landing page репозитория по умолчанию на английском:

```text
README.md       English — канонический landing README
README.ru.md    Русский companion (паритет секций с README.md)
README.en.md    compatibility pointer → README.md
```

Карта системы:

```text
SYSTEM_OVERVIEW.en.md   English atlas
SYSTEM_OVERVIEW.md      Русский atlas (паритет секций)
```

---

## Предшествующий код — Apart Swarm Alignment Hackathon (6–8 ноября 2026)

Код и тесты Titan, рассмотренные в отчёте этого хакатона, являются предшествующей работой, а не новой реализацией для хакатона. Изменения сопровождения от 6–7 ноября не заявляются как вклад хакатона. Вклад хакатона состоит только из отчёта: сопоставление угроз, аудит доказательств и предложенный протокол оценки. Для этой заявки новый runtime-код не написан, и эксперимент эффективности надзора не проводился.

---

## 🧭 Версия

**<!-- SYNC:VERSION -->v9.0.0<!-- /SYNC:VERSION --> — VELANTRIM TITAN 9.0**

Источник версии: `pyproject.toml` / `core.__version__`.
История: [`CHANGELOG.md`](CHANGELOG.md).

> **Titan понимает и предлагает. Trust boundaries проверяют и допускают.
> Kernel сохраняет инварианты. LLM остаётся replaceable.**
