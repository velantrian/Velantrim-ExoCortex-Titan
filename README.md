# 🔱 VELANTRIM V8.7 TITAN

Долговременная память для AI-агентов с каузальным пониманием, иммунной системой и осью идентичности.

> 🌿 **Философия:** [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md)
> 🔒 **Для AI-агентов:** [docs/PHILOSOPHY_SPEC.md](docs/PHILOSOPHY_SPEC.md)
> 🏛️ **Канон истины:** [docs/TRUTH_AND_RINGZERO_CANON.ru.md](docs/TRUTH_AND_RINGZERO_CANON.ru.md)
> 🗺️ **Карта проекта:** [Velantrim_Project_Map.md](Velantrim_Project_Map.md)
> 📋 **Журнал устаревших технологий:** [research/DEPRECATIONS.md](research/DEPRECATIONS.md)
> 🏛️ **4 оси архитектуры:** [research/ARCHITECTURE_AXES.md](research/ARCHITECTURE_AXES.md)
> 🔬 **Будущие компоненты:** [research/FUTURE_COMPONENTS.md](research/FUTURE_COMPONENTS.md)

## 🆕 V8.7 Titan — Иммунная система + Identity Axis + Production-ready (3 июня 2026)

**199 модулей · 91 тестовый файл · 18 инвариантов в CI · docker-compose up**

### 🛡️ Новая иммунная система
| Модуль | Назначение |
|--------|-----------|
| `core/meta_supervisor.py` | HEALTHY/DEGRADED/SAFE_MODE. Heartbeat 10 сек. L3 read-only при критической деградации |
| `core/immutable_core_scheduler.py` | SHA-256 дельта-снапшоты графа каждые 24ч |
| `core/provenance_chain.py` | Append-only hash-chain. Блокчейн для памяти |
| `core/atomic_split.py` | I91: один смысл = один факт |
| `tests/test_invariants.py` | 18 исполняемых инвариантов. Падение → деплой заблокирован |

### 🧬 Identity Axis — ось «Я»
| Модуль | Назначение |
|--------|-----------|
| `core/identity_layer.py` | F1–F4: VALUES / WORLDVIEW / BIOGRAPHY / COMPASS |
| `core/stimulus_map.py` | Двусторонняя трассируемость: стимул ↔ факт ↔ ответ |
| `core/forgetting.py` | GDPR «right to be forgotten» + PII redaction |

### 🚀 Production-ready
| Модуль | Назначение |
|--------|-----------|
| `Dockerfile` + `docker-compose.yml` | Деплой одной командой: `docker-compose up -d` |
| `core/async_store.py` | aiosqlite + run_in_executor. Event loop не блокируется |
| `core/metrics.py` | Prometheus-метрики + `/health` эндпоинт |
| `core/lightweight_metrics.py` | Лёгкие метрики: `metrics.jsonl` + grounding/trace/latency |
| `core/rate_limit.py` | Token-bucket per-IP |
| `.github/workflows/ci.yml` | CI/CD: mypy strict + ruff + pytest. BLOCKING |

### 🧠 Когнитивные модули V8.7
| Модуль | Назначение |
|--------|-----------|
| `core/perspectives.py` | 9 ролей: ENGINEER/SCIENTIST/ANALYST/CRITIC/ADVISOR/FRIEND/PHILOSOPHER/CREATIVE/CHILD |
| `core/branch_manager.py` | Multi-perspective reasoning: 3 параллельные ветки → синтез |
| `core/meta_cognition.py` | Мета-когнитивная рефлексия о ПУТИ мышления |
| `core/reconsolidation.py` | Живая память: факты переосмысливаются при использовании |
| `core/experience_replay.py` | Ночная реактивация успешных цепочек (LTP-подобно) |
| `core/adaptive_truth.py` | Адаптивные пороги TruthGate: зелёная/красная зоны |
| `core/truth_maintenance.py` | Truth Maintenance: reinforce/supersede/contradict |
| `core/epigenetic_adaptation.py` | Эпигенетическая адаптация: verification/creativity/exploration |

### 🌐 Новые API-эндпоинты
| Эндпоинт | Назначение |
|----------|-----------|
| `POST /query/roles` | Multi-perspective запрос с выбором ролей |
| `GET /system/epigenetic` | Состояние эпигенетической адаптации |
| `GET /metrics/eval` | Лёгкие метрики (grounding,trace,latency) |

### 🎛️ Каталог LLM (только актуальные)
```
OpenAI: chat-latest · gpt-5.5 | Anthropic: claude-sonnet-4-6 · claude-opus-4-8
DeepSeek: deepseek-v4-flash · deepseek-v4-pro | Qwen: qwen3.7-max · qwen3.7-plus
Google: gemini-3.5-flash | Llama: llama-4-maverick
```

## 🖥️ Веб-консоль + LLM (тест в браузере)

### 🌐 Онлайн (GitHub Pages — ПК и смартфон PWA)

> **Если видите «There isn't a GitHub Pages site here»** — один раз включите Pages:  
> [docs/GITHUB_PAGES_ENABLE.ru.md](docs/GITHUB_PAGES_ENABLE.ru.md) →  
> https://github.com/velantrian/Velantrim-ExoCortex-Titan/settings/pages → ветка **`gh-pages`**, папка **`/ (root)`**

| Страница | Ссылка |
|----------|--------|
| **Портал** | https://velantrian.github.io/Velantrim-ExoCortex-Titan/ |
| **Research PWA** (работает без сервера) | https://velantrian.github.io/Velantrim-ExoCortex-Titan/console/research-app.html |
| **UI полной консоли** (нужен API на ПК/VPS) | https://velantrian.github.io/Velantrim-ExoCortex-Titan/console/ |
| **PWA Roadmap** | https://velantrian.github.io/Velantrim-ExoCortex-Titan/console/research-roadmap.html |

На телефоне: откройте Research PWA → «Добавить на главный экран» / «Установить приложение».

### 💻 Локально (полная консоль + LLM)

Экспериментальный стенд V8.7 Titan: чат, блок памяти в **localStorage**, поиск по сообщениям, вкладка **🔗 Эссенция**.

**Обзор (красиво, с путями и переносом):** [docs/CONSOLE_OVERVIEW.ru.md](docs/CONSOLE_OVERVIEW.ru.md)

**Документация:** [docs/CONSOLE_BROWSER_TEST.ru.md](docs/CONSOLE_BROWSER_TEST.ru.md) · [http://127.0.0.1:8755/console/help](http://127.0.0.1:8755/console/help) · [roadmap](http://127.0.0.1:8755/console/roadmap)

```powershell
cd "C:\Users\VELAN\Documents\Research Velantrim\VELANTRIM_ExoCortex_V8.7_Titan"
# 1. .env: VELANTRIM_API_KEY=...  (+ LLM из config/llm.example.env)
.\scripts\start_console.ps1
# 2. Браузер: http://127.0.0.1:8755/console/?v=40
```

Профили: **citizen** · **personal** · **company** · **science** · **education** · **research** · **developer**  
Справочник: [docs/PROFILES.ru.md](docs/PROFILES.ru.md) · `GET /setup/llm` · [docs/ROADMAP_FROM_SYSTEM.ru.md](docs/ROADMAP_FROM_SYSTEM.ru.md) · [docs/HORIZONS.md](docs/HORIZONS.md) · [docs/LAYERS_AND_HORIZONS.ru.md](docs/LAYERS_AND_HORIZONS.ru.md) · [docs/RELATED_PROJECTS.ru.md](docs/RELATED_PROJECTS.ru.md).

## 🚀 Быстрый старт

```bash
# Способ 1: Docker (рекомендуется)
docker-compose up -d
# Сервер на http://localhost:8000

# Способ 2: Ручной запуск
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install fastapi "uvicorn[standard]" python-dotenv pydantic pytest httpx
cp .env.example .env
# VELANTRIM_API_KEY=...  или VELANTRIM_ALLOW_OPEN=true (только dev)
mkdir -p data
uvicorn server:app --port 8000 --reload
.\scripts\run_tests.ps1              # полный pytest
```

### ExoCortex (опционально)

```bash
ENABLE_VELUM=1
ENABLE_ETIR=1
ENABLE_L45=1
ENABLE_L6_WELFARE=1
ENABLE_EVENT_BUS=1
```

## 📚 Документация

- `docs/TRUTH_AND_RINGZERO_CANON.ru.md` 🏛️ — **единый канон-эталон**: Движок Истины (Core-3) + Ring Zero (малое ядро), вердикт `allow/gap_notice/reject`, инварианты I0–I8, conformance C1–C12 ([EN](docs/TRUTH_AND_RINGZERO_CANON.en.md))
- `docs/MIGRATION_V8.6_TO_CANON.ru.md` 🗺️ — план миграции V8.6 к канону (C1–C12 → задачи по файлам)
- `core/core3_adapter.py` 🔀 — Dual Core Router: субпроцесс-мост к Core-3 (строгая проверка high-risk)
- `docs/CONSOLE_BROWSER_TEST.ru.md` — тестовая веб-консоль в браузере
- `docs/VELANTRIM_ARCHITECTURE.md` — архитектура
- `docs/VELANTRIM_GUIDE.md` — установка
- `docs/RUN.ru.md` — быстрый старт
- `docs/FRACTAL_MEMORY_CANON.ru.md` — Fractal Memory L0–L3, MemTree/recursive retrieval canon
- `docs/ESSENCE_LAYER_CANON.ru.md` — future-work канон: суть, смысловые цепочки, короткий человеческий ответ
- `docs/ATTENTION_NOETIC_ORCHESTRATION.ru.md` — P0-контракты: GoalFrame, AttentionRouter, ComputeController, NoeticCore
- `docs/WORLD_KNOWLEDGE_CORE_v1_0.ru.md` — future-work канон: качество знания, время, negative knowledge, contradiction review
- `docs/RESEARCH_MODE.ru.md` — отдельная experimental-память и Velantrim как API-инструмент
- `docs/EITI_PWA_RESEARCH_ROADMAP.ru.md` — T1–T12 roadmap для браузерной Research PWA
- `docs/Velantrim_V9_Final_Audited.md` — спека V9

## Версия

**8.7.0 Titan** — продукт **VELANTRIM V8.7 TITAN** (3 июня 2026).  
199 модулей в `core/` · 1212 тестов · Docker + CI/CD.  
Исходный код V8.6 сохранён нетронутым в папке `VELANTRIM_ExoCortex_V8.6`.
