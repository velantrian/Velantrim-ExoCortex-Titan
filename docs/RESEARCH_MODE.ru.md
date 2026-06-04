# 🧪 Velantrim Research Mode — отдельная экспериментальная память

**Статус:** проектная спека / overview  
**Цель:** тестировать Fractal Memory Router, `RetrievalPath`, compression и Guardian layers через браузер и API, не меняя стабильную V8.6-память.

---

## 🧠 Главная идея

Velantrim можно использовать как **инструмент памяти для AI-агента**:

```text
AI / Browser Console
  -> Velantrim API
  -> отдельная Research memory DB
  -> RetrievalPath + TRACE
  -> ответ / анализ в браузере
```

Основная V8.6 остаётся стабильным ядром. Research Mode — это малая
экспериментальная версия рядом с ней, где можно включать новые идеи без риска
испортить основной граф истины.

---

## 🛡️ Stable vs Research

| Часть | Stable V8.6 | Research Mode |
|-------|-------------|---------------|
| Назначение | стабильная долговременная память | экспериментальная память и Fractal Router |
| База данных | `data/velantrim.db` | `data/velantrim_research.db` |
| API query | `POST /query` | `POST /research/query` |
| Browser UI | `/console` | `/console/research-app` + `/console/research` |
| Retrieval | текущий Hybrid/Causal pipeline | recursive retrieval + `RetrievalPath` |
| TRACE | обычный fact-level trace | TRACE + `memory_route` / `RetrievalPath` |
| Запись в L3 | только проверенная память | отдельный sandbox, без записи в stable L3 |
| Риск | низкий | изолирован |

---

## 🔌 Как использовать Velantrim как API-инструмент

Research Console должна обращаться не напрямую к файлам, а через API:

| Действие | Stable API | Research API |
|----------|------------|--------------|
| записать факт | `POST /facts` | `POST /research/facts` |
| спросить память | `POST /query` | `POST /research/query` |
| получить trace | поле `trace` | `trace` + `retrieval_path` |
| посмотреть состояние | `GET /health` | `GET /research/health` |

Так AI-агент может использовать Velantrim как внешний инструмент:

```text
tool: velantrim_memory
input: query / fact / source
output: answer + facts + trace + retrieval_path
```

---

## 🧭 Что сохраняет Research Mode

Research Mode должен сохранять отдельно:

| Данные | Зачем |
|--------|-------|
| raw input | защита от semantic drift |
| derived facts | проверка, что извлекла система |
| `RetrievalPath` | путь внимания: куда система смотрела и почему |
| TRACE | источники, ESM, confidence |
| Guardian decisions | почему разрешено/заблокировано |
| compression steps | как L0/L1/L2 превратились в summary/candidate |

Принцип:

```text
Stable memory = доверенное ядро
Research memory = песочница для обучения архитектуры
```

---

## 🗂️ Минимальный профиль

Предлагаемый файл:

```text
config/exocortex-research.env
```

Пример:

```env
VELANTRIM_PROFILE=research
VELANTRIM_DB_PATH=./data/velantrim_research.db
VELANTRIM_NGRAM_DB=./data/velantrim_research_ngram.db
ENABLE_FRACTAL_ROUTER=1
ENABLE_RETRIEVAL_PATH=1
ENABLE_RESEARCH_API=1
```

---

## 🖥️ Браузерный сценарий

```text
1. Открыть /console/research-app
2. Написать запрос
3. UI отправляет POST /research/query
4. Research pipeline ищет через Fractal Router
5. Ответ возвращает:
   - answer
   - facts
   - trace
   - retrieval_path
   - guardian
6. Всё сохраняется в research DB, stable DB не меняется
```

---

## ⚖️ Что уже есть и чего ещё нет

| Элемент | Статус |
|---------|--------|
| `core/fractal_memory.py` contracts | ✅ есть |
| `MemoryRecord`, `FractalMemoryNode`, `TraceRecord` | ✅ есть |
| `RetrievalPath` | ✅ есть |
| compression / Guardian contracts | ✅ есть |
| `/console/roadmap` описание задач | ✅ есть |
| `/research/query` runtime endpoint | 🔴 ещё нет |
| `/console/research-app` активная browser UI | ✅ есть: local sandbox |
| `/console/research` overview-страница | ✅ есть |
| `config/exocortex-research.env` | 🔴 ещё нет |

---

## 🧩 EITI PWA Roadmap

Тезисы Claude по EITI PWA приняты как отдельный roadmap для браузерной
Research-памяти, а не как изменение stable core.

| Вид | Ссылка |
|-----|--------|
| HTML в браузере | `/console/research-roadmap` |
| Активная Research App | `/console/research-app` |
| Markdown в репозитории | `docs/EITI_PWA_RESEARCH_ROADMAP.ru.md` |

Главная линия: T1–T12 реализуются в PWA/Research sandbox, затем проверенные
части можно переносить в stable через отдельные тесты.

---

## ✅ Правильный порядок реализации

1. Создать `config/exocortex-research.env`.
2. Добавить `ResearchStore` или безопасный wrapper вокруг `SQLiteGraphStore` с отдельным db path.
3. Добавить `POST /research/query` без изменения `POST /query`.
4. Подключить `RetrievalPath` как `memory_route` в ответ.
5. Добавить `/console/research-app`.
6. Сравнивать Stable vs Research на одинаковых запросах.

---

## Итоговая формула

> Velantrim Stable = доверенное ядро памяти.  
> Velantrim Research = экспериментальная песочница поверх того же API-подхода, но с отдельной памятью, Fractal Router, `RetrievalPath` и усиленным TRACE.
