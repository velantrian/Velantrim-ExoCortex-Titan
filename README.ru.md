# 🔱 VELANTRIM TITAN 9.0

[English](README.md) · **Русский**

> **Local-first проверяемая память/runtime для AI-агентов:** явные эпистемические
> состояния, контролируемые write/admission boundaries, provenance, TRACE, retrieval,
> tools и заменяемый LLM/provider layer.
>
> **Зрелость:** research-grade prototype, движущийся к production hardening.

[🤖 AI-агент: начать здесь](AGENTS.md) ·
[🗺️ Карта системы](SYSTEM_OVERVIEW.md) ·
[📊 Статус проекта](docs/PROJECT_STATUS.md) ·
[🔍 Для аудитора](docs/REVIEWER_README.md) ·
[🔒 Security](SECURITY.md)

> Для coding agents формальная точка входа — [`AGENTS.md`](AGENTS.md), затем
> [`docs/ai/README.md`](docs/ai/README.md). Документация — карта, а не proof:
> существенные claims проверяются по exact code/tests/CI/config/runtime evidence.

---

## 👋 Titan за 60 секунд

```text
query / действие
  → memory + retrieval
  → admitted context / typed proposals
  → policy / TruthGate / write boundaries
  → TRACE / audit / provenance
  → tools или replaceable LLM/provider layer
```

Titan не утверждает, что «знает абсолютную истину». Его задача — не смешивать
retrieval, evidence, permission, mutation, auditability и model output в одну власть.

```text
retrieval ≠ evidence
admission ≠ verification
confidence ≠ authority
model output ≠ Canon
TRACE membership ≠ semantic use ≠ answer support
CI green ≠ production authorization
```

### Текущая read boundary

`core/pipeline.py::run()` read-only относительно canonical fact storage, ESM promotion
и causal-relation mutation. Стандартные `Validated` promotion callers идут через
`PromotionGateway`; другие mutation families сохраняют собственные явные owners/contracts.

### Retrieval

`HybridRetriever` поддерживает lexical/BM25-style retrieval, optional dense embeddings,
optional graph signals и ranking fusion. Это capability, а не утверждение, что каждая
установка запускает все signals на каждом запросе. Optional dependencies/configuration
могут оставить более узкий retrieval path.

### MCP / tools

На текущей проверенной базе MCP **не dormant**: `server.py` регистрирует routes из
`api/mcp_gateway.py` через `require_api_key`; gateway использует
`core.mcp_transport.McpHandler`, capability/session ceilings и tool registry.

Правильный статус:

```text
implemented + server-wired + auth-gated
  ≠ enabled/externally exposed in every deployment
  ≠ observed in a concrete running instance
  ≠ production authorization
```

---

## 🧭 Что открыть первым

| Задача | Начать здесь |
|---|---|
| 🤖 AI coding/review | [`AGENTS.md`](AGENTS.md) → [`docs/ai/README.md`](docs/ai/README.md) |
| 👤 Понять проект | [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md) |
| 🔍 Аудит | [`docs/REVIEWER_README.md`](docs/REVIEWER_README.md) |
| 📊 Зрелость/риски | [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) |
| 🛠️ Запуск | [Security](SECURITY.md) + deployment docs |
| 🔬 Research | [`research/`](research/) |

---

## 🧾 Статусы

```text
proposed ≠ implemented ≠ tested ≠ wired ≠ enabled ≠ observed
```

Для конкретной установки проверяйте config, `/health`, `/layers/status`, `/titan/status`.
Наличие файла или server registration само по себе не является runtime observation.

---

## 📄 Synaptic Exo-Cortex

```text
Raw evidence
  → ✅ SemanticReader
  → ✅ KnowledgeCapsule + exact SourceSpan
  → ✅ LLM Reader Adapter (main/tested; standalone CLI)
  → ✅ Working Memory Gate (shadow-only)
  → ✅ ContextPack (shadow-only)
  → ✅ shadow evaluation (feature-gated; no answer authority)
  → active Synaptic answer authority: NOT AUTHORIZED
```

Shadow processing не пишет Canon/ESM и не получает answer authority автоматически.
`KnowledgeCapsule`/proposal ≠ Canon; `extraction_confidence` ≠ `truth_confidence`.

---

## 🧠 TRACE / evidence-use

Titan может наблюдать:

```text
R = retrieved / selected
S = serialized into prompt
T = transmitted/provider-packed
```

Но из этого не следует автоматически:

```text
U = model demonstrably used evidence
A = evidence demonstrably supported final answer
```

R/S/T ≠ U/A без отдельного attribution evidence.

---

## 🛡️ Что проект не обещает

- нулевые hallucinations;
- абсолютную истинность sources;
- certified GDPR/compliance;
- независимый security audit, которого не было;
- production-ready multi-user SaaS «из коробки»;
- что все optional layers enabled;
- что TRACE доказывает internal use/support;
- что server wiring = deployed/observed/production-authorized.

`docs/project_status/FOR_AI.json` может показывать **V1 productization P0/P1 = 0**.
Это отдельный frozen V1 scope и не означает, что production-hardening P0/P1 из
[`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) закрыты.

---

<a id="quick-start"></a>

## 🚀 Быстрый старт

```bash
git clone https://github.com/velantrian/Velantrim-ExoCortex-Titan.git
cd Velantrim-ExoCortex-Titan
cp .env.prod.example .env.prod
# задайте безопасный VELANTRIM_API_KEY
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

Hardened profile — это application/container hardening, а не production authorization.
Подробнее: [`docs/operations/hardened-production-profile.md`](docs/operations/hardened-production-profile.md).

Для разработки:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -e ".[server,dev]"
uvicorn server:app --port 8000 --reload
```

---

## 🌐 Языки

```text
README.md       English — основной landing README GitHub
README.ru.md    Русский — companion
README.en.md    compatibility pointer → README.md
```

---

## 🧭 Версия

**<!-- SYNC:VERSION -->v9.0.0<!-- /SYNC:VERSION --> — VELANTRIM TITAN 9.0**

Источник версии: `pyproject.toml` / `core.__version__`.
