# 🗺️ Velantrim Titan 9.0 — живая карта системы

> **Назначение:** экскурсия по архитектуре для человека, инженера, оператора,
> аудитора и AI-агента.
>
> **Версия продукта:** <!-- SYNC:VERSION -->v9.0.0<!-- /SYNC:VERSION -->
> **Срез реализации:** [`main@1718c42`](https://github.com/velantrian/Velantrim-ExoCortex-Titan/commit/1718c42),
> проверено 29 июля 2026 года.
>
> **Статус документа:** навигация и обучение; не подменяет код, тесты,
> runtime-телеметрию или канонические спецификации.

[🇬🇧 English companion — legacy translation](SYSTEM_OVERVIEW.en.md) ·
[🏠 README](README.md) ·
[📊 статус проекта](docs/PROJECT_STATUS.md) ·
[🔍 карта для аудитора](docs/REVIEWER_README.md) ·
[🏛️ канон истины](docs/TRUTH_AND_RINGZERO_CANON.ru.md)

---

## 🧭 Выберите маршрут

Необязательно читать документ подряд. Начните с нужной глубины:

| Я хочу… | Маршрут | Время |
|---|---|---:|
| 👋 понять идею без жаргона | [объяснение за 30 секунд](#plain) | 30 секунд |
| 🗺️ увидеть систему целиком | [карта компонентов](#map) | 3–5 минут |
| 🔄 понять путь запроса и факта | [два главных потока](#flows) | 7–10 минут |
| 🧑‍💻 разобраться как инженер | [контракты и границы](#engineer) | 15–25 минут |
| 🧪 понять, как проверяется жизнеспособность | [Architecture Assurance](#assurance) | 10–15 минут |
| 🔍 проверить заявления проекта | [доказательства и ограничения](#evidence) | 10 минут |
| 🤖 объяснить Titan другому человеку | [протокол самообъяснения](#self-explain) | 5 минут |

---

<a id="plain"></a>

## 👋 L0 — Titan за 30 секунд

### Простыми словами

Velantrim Titan — это **проверяемая долговременная память для AI-агентов**.
Она отделяет четыре вещи, которые обычный чат часто смешивает:

```text
🧾 источник  →  🧠 память  →  ⚖️ проверка  →  🗣️ ответ
```

Удобная аналогия:

```text
📚 Библиотекарь   находит подходящие записи
🧪 Лаборант       сохраняет источник и степень уверенности
🛂 Пограничник    не пропускает знание без нужных условий
🧾 Аудитор        оставляет проверяемый след
🗣️ Переводчик     превращает отобранные данные в понятный ответ
```

Titan — **не оракул истины** и не «сознание в коробке». Он повышает
проверяемость памяти и ответа, но не делает любой текст автоматически истинным.

### Инженерным языком

Titan — local-first runtime, который сочетает:

- явную эпистемическую машину состояний (**ESM**);
- evidence-gated запись и promotion;
- гибридное извлечение данных;
- provenance, TRACE и проверяемые инварианты;
- заменяемый LLM-слой, не обладающий прямой властью над Canon;
- feature-gated исследовательские когнитивные модули.

Короткая инженерная формула:

```text
Memory stores state.
Retrieval proposes context.
Policy limits authority.
TruthGate evaluates admission.
TRACE preserves accountability.
LLM renders language.
```

---

## 🎚️ Четыре координаты объяснения

Чтобы документация не превращалась ни в маркетинг, ни в непроходимый учебник,
каждое объяснение нужно рассматривать сразу по четырём независимым осям:

```text
                         🗣️ РЕГИСТР
                 простой ↔ операторский ↔ инженерный
                              │
                              │
📍 ГЛУБИНА  L0 ↔ L1 ↔ L2 ↔ L3 ┼── C4 ZOOM  Context ↔ Code
                              │
                              │
                    🧾 ДОКАЗАТЕЛЬНЫЙ СТАТУС
              main / gated / open PR / research / runtime
```

| Ось | Вопрос | Пример |
|---|---|---|
| 📍 Глубина | Насколько подробно? | L0 — одна фраза; L3 — файл, контракт, тест |
| 🗣️ Регистр | Для кого объясняем? | простыми словами, оператору, инженеру |
| 🔎 Архитектурный zoom | На каком масштабе смотрим? | система, контейнер, компонент, код |
| 🧾 Статус | Чем подтверждено утверждение? | файл в `main`, feature flag, runtime-метрика |

> 💡 **Важно:** «простыми словами» не означает «неточно», а «есть код» не
> означает «модуль включён, используется и проверен в этой установке».

---

<a id="evidence"></a>

## 🧾 Как читать статусы

### Легенда

| Метка | Значение |
|---|---|
| 🟢 **default path** | код находится в `main` и относится к базовому рабочему пути |
| ✅ **main / tested** | реализация и проверяющие тесты находятся в `main`; включённость проверяется отдельно |
| 🟡 **available / gated** | код существует, но зависит от профиля или `ENABLE_*` |
| 🚧 **open PR** | работа видна в GitHub, но ещё не является частью `main` |
| 🔬 **research / proposed** | идея или контракт описаны, но runtime-власти нет |
| ⚠️ **known limitation** | известная граница, долг или неподтверждённое свойство |
| 📡 **runtime observed** | состояние подтверждено конкретным запущенным экземпляром |

### Почему одного слова «реализовано» недостаточно

```text
📄 Файл существует
      │
      ▼
🧪 Контракт покрыт тестом
      │
      ▼
🎛️ Функция включена конфигурацией
      │
      ▼
🔗 Функция реально подключена к нужному пути
      │
      ▼
📡 Работа наблюдалась в конкретном runtime
```

Это пять разных утверждений. Atlas не сжимает их в одно зелёное слово.

### Где находится источник истины для каждого вопроса

| Вопрос | Авторитетный источник |
|---|---|
| Что проект обещает? | каноническая спецификация и ADR |
| Что уже написано? | GitHub `main` |
| Что должно быть неизменно? | код инварианта + блокирующий тест |
| Что включено сейчас? | `/layers/status`, `/titan/status`, конфигурация экземпляра |
| Что реально происходило? | TRACE, audit/provenance, логи и метрики |
| Что пока исследуется? | `research/`, открытые PR и roadmap |
| Насколько система зрелая? | [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) |

> ⚠️ Документ может подтвердить архитектурное намерение и наличие кода. Только
> runtime-снимок подтверждает, что функция включена и работает в конкретной
> установке прямо сейчас.

---

<a id="map"></a>

## 🗺️ L1 — карта системы

```text
┌────────────────────────── 🌍 ВНЕШНИЙ МИР ──────────────────────────┐
│  👤 человек · 🤖 агент · 📄 файл · 🖥️ консоль · 🔌 API            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────── 📥 ИНТЕРФЕЙС И ПОЛИТИКИ ─────────────────────┐
│  server.py / api/ · auth · CORS · rate limits · remote egress      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
          🔎 ПУТЬ ЧТЕНИЯ              ✍️ ПУТЬ ЗАПИСИ
          query / retrieval            source / candidate
                    │                         │
                    ▼                         ▼
          FactsPack / TRACE              ESM + Write Gate
                    │                         │
                    ▼                         ▼
          Guardian / policy              TruthGate / CAS
                    │                         │
                    ▼                         ▼
              🗣️ ответ                 🧠 durable memory
                    │                         │
                    └──────────┬──────────────┘
                               ▼
                 🧾 provenance · audit · metrics
                               │
                               ▼
                 📚 indexes / graph projections
```

### Главная граница

```text
LLM может предложить формулировку или извлечение.
LLM не получает автоматического права сделать это Canon.
```

Индекс и графовая проекция ускоряют поиск и анализ, но не должны становиться
скрытым параллельным источником канонической записи. Если проекцию можно
перестроить из авторитетных данных, её отказ не должен менять истину.

### Карта по областям

| Область | Простыми словами | Инженерная опора |
|---|---|---|
| 📥 Интерфейс | принимает запросы и файлы | `server.py`, `api/`, web console |
| 🧭 Оркестрация | решает, какие шаги выполнить | `core/pipeline.py`, `core/app.py` |
| 🧠 Память | хранит факт и его состояние во времени | `core/memory.py`, SQLite по умолчанию |
| 🔍 Поиск | находит подходящие записи | `core/hybrid_retriever.py`, `core/ngram_index.py` |
| ⚖️ Доверие | проверяет условия допуска | `core/truth_gate.py`, `core/write_gate.py`, Policy Kernel |
| 🧾 След | показывает источники и изменения | TRACE, `core/provenance_chain.py`, AuditChain |
| 🛡️ Целостность | обнаруживает опасную деградацию | MetaSupervisor, immutable snapshots, invariants |
| 🗣️ Языковой слой | читает или формулирует текст | provider-neutral adapters; LLM заменяем |
| 🔬 Исследования | проверяет новые композиции без власти над Canon | `research/`, shadow paths, feature flags |

---

<a id="flows"></a>

## 🔄 L2 — два главных потока

### 🔎 Поток A: человек задаёт вопрос

```text
👤 Запрос
   │
   ▼
🔐 API boundary
   │  auth / policy / optional rate limit
   ▼
🧭 Pipeline
   │
   ▼
🔍 Hybrid retrieval
   │  BM25 + optional dense/graph signals
   ▼
📦 FactsPack + structured TRACE
   │
   ▼
🛡️ Guardian / truth policy
   │
   ├── ✅ данных достаточно ─────► 🗣️ grounded answer
   ├── 🟡 есть пробел ───────────► 📭 gap notice / uncertainty
   └── 🔴 политика запрещает ────► 🛑 reject / safe failure
```

#### Простыми словами

Система сначала ищет записи, затем собирает пакет доказательств и только потом
строит ответ. Если сведений недостаточно, корректный результат — показать
пробел, а не уверенно заполнить его выдумкой.

#### Инженерная оговорка

Целевой инвариант Synaptic-профиля: обычный read/query/retrieval path не
изменяет Canon, ESM или проекции. В текущем legacy pipeline остаётся известный
путь, где `POST /query` может выполнять promotion по собственной policy.
Поэтому чистота read-path — **обязательная архитектурная граница и открытая
унификация**, а не закрытое заявление обо всех сегодняшних путях. Подробности:
[`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).

### ✍️ Поток B: в систему поступает новое утверждение

```text
📄 Источник
   │
   ▼
🧩 Candidate claim
   │  точный источник / span / modality / uncertainty
   ▼
🧠 ESM: Observed
   │
   ▼
🧾 Evidence + legal transition
   │
   ▼
⚖️ TruthGate / write policy
   │
   ├── ✅ passed ─────► следующий разрешённый ESM-state
   ├── 🟡 incomplete ─► остаётся кандидатом / gap
   └── 🔴 rejected ───► нет доверенного promotion
   │
   ▼
🧾 provenance + audit snapshot
```

#### Простыми словами

Новое утверждение не становится «истиной» только потому, что его написал
пользователь или LLM. Оно начинает как наблюдение или кандидат, получает
источники и проходит разрешённые переходы.

#### Инженерная оговорка

Не все внутренние promotion-paths ещё унифицированы под одной и той же
TruthGate/CAS-политикой. Защищённые пути и оставшийся долг перечислены в
[`docs/REVIEWER_README.md`](docs/REVIEWER_README.md) и
[`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).

---

## 🧠 Память и ESM

### Простая модель

ESM — это не шкала «плохо → хорошо», а журнал эпистемического положения:

```text
👁️ Observed
   │
   ▼
💭 Hypothesized
   │
   ▼
🧩 Supported
   │
   ▼
✅ Validated

Отдельные исходы: ⚔️ Contradicted · 🕰️ Deprecated · 🗄️ Collapsed
Особая граница: 🔒 ImmutableCore
```

Фактическая матрица разрешённых переходов находится в `core/memory.py`.
Картинка выше объясняет основной путь, но не заменяет эту матрицу.

### Что нельзя смешивать

| Понятие | Что означает | Чего не означает |
|---|---|---|
| `retrieval_score` | насколько запись подходит к запросу | что запись истинна |
| `extraction_confidence` | насколько точно смысл извлечён из источника | что источник прав |
| `truth_confidence` | оценка внешней доказательной опоры | право на запись |
| ESM-state | текущий эпистемический статус | вечную неизменность |
| task status | состояние работы над задачей | эпистемический статус факта |

> 🔑 Высокая уверенность — это сигнал для проверки, а не полномочие на
> канонизацию.

---

## 📄 Synaptic Exo-Cortex — путь документа

Это активный инженерный профиль, который превращает длинный источник в
проверяемые смысловые капсулы. Состояние на указанном срезе `main`:

```text
📄 Raw evidence
   │
   ├── ✅ SemanticReader contract + deterministic ExtractiveReader
   ▼
🧩 KnowledgeCapsule
   │  ✅ exact SourceSpan + SHA-256 + modality + uncertainty
   │  ⛔ не Canon и не имеет write authority
   ▼
🤖 LLM Reader Adapter
   │  🚧 два конкурирующих draft PR: #72 и #73; в main отсутствует
   ▼
🚦 Working Memory Gate
   │  🔬 PR-SYN-04 / planned
   ▼
📦 ContextPack
   │  🔬 PR-SYN-05 / planned
   ▼
👤 Answer + source-span verification
      🔬 сначала shadow evaluation, затем отдельное решение об активации
```

| Компонент | Статус | Граница |
|---|---|---|
| `KnowledgeCapsule` | ✅ `main` | immutable proposal с точным provenance |
| `SemanticReader` | ✅ `main` | provider-neutral extraction contract |
| remote-egress boundary | ✅ `main` | remote call требует policy lease |
| LLM Reader Adapter | 🚧 [draft #72](https://github.com/velantrian/Velantrim-ExoCortex-Titan/pull/72) / [draft #73](https://github.com/velantrian/Velantrim-ExoCortex-Titan/pull/73) | вывод модели остаётся недоверенным |
| Working Memory Gate | 🔬 planned | `ACTIVE/COMPRESS/DEFER/QUARANTINE/EXCLUDE`; без `DELETE` |
| ContextPack | 🔬 planned | ограниченный пакет контекста |
| Working Desk | 🔬 research | композиция задач; runtime authority отсутствует |

Полный план:
[`docs/SYNAPTIC_EXO_CORTEX_IMPLEMENTATION_PLAN.md`](docs/SYNAPTIC_EXO_CORTEX_IMPLEMENTATION_PLAN.md).

---

<a id="engineer"></a>

## 🧑‍💻 L3 — контракты и границы

### 1. Read path и write path — разные полномочия

```text
READ
  returns facts / evidence / AnalysisProposal
  must not silently mutate Canon

WRITE
  requires explicit controller/service
  validates policy + ESM + provenance
  records auditable effect
```

Если аналитический модуль хочет изменить знание, его корректный результат —
proposal. Решение о записи принимает отдельная контролируемая граница.

### 2. Canon и проекции — разные уровни авторитета

```text
🧠 authoritative state
   ├── fact + ESM + temporal fields
   ├── evidence / provenance
   └── canonical write history

⚡ rebuildable projections
   ├── search indexes
   ├── graph analytics views
   ├── ranking caches
   └── dashboards
```

Повреждение проекции должно приводить к её перестроению или graceful
degradation, а не к незаметному изменению знания.

### 3. LLM — заменяемый исполнитель

LLM может:

- извлекать candidate claims;
- предлагать структурированный ответ;
- сжимать контекст при сохранении qualifiers;
- озвучивать grounded evidence.

LLM не может сам по себе:

- объявить candidate каноническим фактом;
- обойти Guardian, TruthGate или remote-egress policy;
- присвоить себе недоказанную «интроспекцию» runtime;
- подменить TRACE красивым рассказом о ходе мышления.

### 4. Объяснение решения строится из TRACE

`core/xai_explain.py` поддерживает уровни `brief`, `detailed` и `full_trace`.
Модуль feature-gated (`ENABLE_XAI`) и следует правилу:

```text
есть TRACE  → можно построить проверяемое объяснение
нет TRACE   → честный отказ объяснять
```

Это объяснение опирается на факты, источники и записанные события. Оно не
публикует скрытый chain-of-thought и не выдаёт сгенерированную реконструкцию за
точную трассу внутренних активаций модели.

### 5. Локальность и удалённые модели

Удалённый вызов проходит через `core/remote_egress.py` и Policy Kernel.
Политика различает как минимум:

- `raw` — передаются исходные пользовательские данные;
- `redacted` — передаётся редактированный payload;
- `none` — допустим только для закрытого списка metadata-only capabilities.

Новый remote call не должен получать «невидимое исключение» из этой границы.

---

<a id="self-explain"></a>

## 🎓 Протокол самообъяснения системы

Это операционализация идеи «система должна уметь провести экскурсию по самой
себе». Сейчас протокол реализован **в документации**; отдельный интерактивный
runtime-режим пока не заявлен.

### Как должен начинаться диалог

```text
👋 «Как вам объяснить Titan?»
       │
       ├── 🙂 Простыми словами
       ├── 🧑‍💻 Инженерным языком
       ├── 🛠️ Как оператору
       └── 🔍 Как аудитору
              │
              ▼
       📍 L0 → L1 → L2 → L3
       «Углубиться или остановиться?»
```

### Правила хорошей экскурсии

1. 🗣️ Спросить регистр один раз, если он неизвестен.
2. 💾 Запомнить предпочтение только с согласия пользователя.
3. 📍 Начать с L0/L1; углублять по запросу, а не выгружать весь репозиторий.
4. 🧾 Для каждого важного утверждения показывать статус и опору.
5. 🔁 Давать аналогию вместе с техническим соответствием.
6. ⚠️ Явно отделять current runtime, feature-gated код и research.
7. 🔗 В инженерном режиме указывать файл, контракт, тест и известный долг.
8. 🧠 Не выдавать объяснение архитектуры за внутренний chain-of-thought.
9. ❓ Если статус нельзя подтвердить — говорить «неизвестно», а не угадывать.

### Формат одного компонента

```yaml
name: TruthGate
plain: "Проверочный шлюз перед доверенным повышением статуса факта."
technical: "Evaluates evidence/confidence policy for an ESM transition."
status: "main; конкретная wiring-политика зависит от пути"
responsible_for:
  - "вердикт допуска"
not_responsible_for:
  - "доказательство абсолютной истины"
evidence:
  - "core/truth_gate.py"
  - "tests/test_truth_gate.py"
limitations:
  - "promotion-paths ещё не полностью унифицированы"
```

Пока такой блок живёт рядом с объяснением в этом Atlas, чтобы не поддерживать
вручную две расходящиеся версии — «простую» и «инженерную». Если появится
runtime renderer, следующий безопасный шаг — вынести эти поля в
машиночитаемый glossary и генерировать оба регистра из одного источника.

### Definition of Done для будущего интерактивного режима

- одинаковый факт не расходится между plain и technical режимами;
- статус берётся из GitHub/config/runtime, а не из памяти LLM;
- ссылки ведут к существующим файлам и тестам;
- feature flag не называется «работающим runtime», пока это не наблюдалось;
- новый модуль без описания и evidence-pointer выявляется CI-проверкой;
- мобильное представление читается без горизонтальной прокрутки;
- интерфейс не раскрывает секреты, prompt payload или скрытые reasoning traces.

---

<a id="assurance"></a>

## 🧪 Architecture Assurance — как доказывать жизнеспособность

Architecture Assurance — не новая «умная сущность» внутри Kernel. Это
сквозная инженерная практика:

```text
📐 модель
   ↓
🏗️ ограниченная конструкция
   ↓
🧪 синтетическая нагрузка + fault injection
   ↓
📡 реальные метрики
   ↓
🔁 коррекция модели и архитектуры
```

### Что гарантируется внутри, а что проверяется снаружи

| Внутри runtime | В тестовом/операционном контуре |
|---|---|
| инварианты и fail-closed policy | load, spike и soak tests |
| лимиты и backpressure | fault injection и recovery drill |
| идемпотентность и CAS | property-based testing и fuzzing |
| audit/provenance hooks | replay, WAL/recovery, snapshot diff |
| graceful degradation | capacity model и benchmark registry |

### Нагрузка: средняя загрузка — только начало

Общая загрузка пула:

\[
\rho = \frac{\lambda E[S]}{c}
\]

где \(\lambda\) — интенсивность входа, \(E[S]\) — среднее время обслуживания,
\(c\) — число workers.

Для LLM и тяжёлого retrieval важна не только средняя, но и дисперсия. В
одноканальном приближении Кингмана:

\[
W_q \approx
\frac{\rho}{1-\rho}
\cdot
\frac{C_a^2 + C_s^2}{2}
\cdot E[S]
\]

Поэтому одинаковое \(\rho\) может дать совершенно разные p95/p99, если длина
запросов и генераций сильно различается. Формула — гипотеза для capacity
planning; benchmark остаётся обязательным.

### Хранилище: считать не один «размер файла»

| Метрика | Что показывает |
|---|---|
| 📚 logical size | сколько полезного смысла хранится |
| 💽 physical size | сколько реально занято на диске |
| ✍️ write amplification | сколько байтов записывается на байт нового смысла |
| ♻️ compaction debt | сколько данных ждёт уплотнения |
| 🗑️ retention debt | сколько устаревшего ещё не удалено/архивировано |
| 🧩 index overhead | цена индексов, рёбер и служебных структур |

Компактация может временно увеличить physical size. Поэтому алерт только на
логический объём не защищает от заполнения диска.

### Надёжность: общие причины отказа

Формула \(R_{system}=\prod R_i\) применима только к подходящей модели
независимых последовательных звеньев. Один диск, одна БД, сеть, auth или общий
пул соединений создают коррелированные отказы.

```text
                     💥 общий диск
                    /      |      \
             🧠 memory  🧾 audit  🔍 index

Один root cause ломает несколько «независимых» модулей одновременно.
```

Для fault injection нужен fault tree с общими узлами, а не только произведение
надёжностей.

### «Один смысл → один узел»: нужен equivalence oracle

Одной генерации дублей недостаточно. Детерминированный тест должен:

1. создать группы перефразировок с закрытым `canonical_id`;
2. добавить похожие, но различающиеся по смыслу утверждения;
3. прогнать ingestion/dedup;
4. отдельно посчитать **false split** и **false merge**;
5. проверить provenance после merge;
6. повторить после replay/recovery.

Это planned assurance-сценарий, а не утверждение о уже доказанном семантическом
dedup всей системы.

### Минимальная лаборатория без LLM

```text
🧬 Synthetic Capsule Generator
           │
           ▼
🚦 Traffic Controller ───────► λ / burst / backpressure
           │
           ▼
🧪 Deterministic Gate Stubs
           │
           ▼
🧠 Memory / Router / Projections
           │
      ┌────┴────┐
      ▼         ▼
✅ Validator   📡 Telemetry
```

Приоритетный набор сценариев:

- одинаковый факт 10 000 раз;
- перефразировки одного смысла и почти одинаковые конфликты;
- медленный/недоступный диск;
- блокировка записи;
- потеря сети у optional remote provider;
- worker crash между durable write и audit artifact;
- многодневный soak с ростом журналов и индексов;
- replay после незавершённой операции.

> ⚠️ В текущем статусе проекта общая concurrency stress-проверка, persisted
> long-term observability и независимый security audit остаются открытыми
> работами. См. [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).

---

## 🔬 Исследовательский контур

### Working Desk

`Working Desk` сохранён как **research/proposed composition**, а не как новый
runtime-слой:

```text
GoalStack
  + WorkingNotebook
  + KnowledgeCapsule references
  + future ContextPack preview
  + Completion/Stagnation diagnostics
  = Working Desk research vision
```

Он не получает:

- отдельную ESM;
- второй физический audit ledger;
- прямую запись в Canon;
- автономный promotion;
- скрытый chain-of-thought;
- постоянный Task Archive без erasure coverage.

Полный registry и критерии выхода:
[`research/WORKING_DESK_RESEARCH_MODE.md`](research/WORKING_DESK_RESEARCH_MODE.md).

### Разделение статусов

```text
✅ Approved foundation
   KnowledgeCapsule → SemanticReader → remote-egress boundary

🚧 Active engineering
   LLM Reader Adapter (draft PR; нужна канонизация одной ветки)

🔬 Planned
   Working Memory Gate → ContextPack → shadow evaluation

🔬 Research
   Working Desk → Task Registry → Completion/Stagnation projections
```

---

## 🛡️ Поведение при сбоях

| Сбой | Желаемое безопасное поведение | Текущий статус |
|---|---|---|
| нет evidence | gap/reject, без тихого доверенного promotion | частично enforced; пути унифицируются |
| remote provider недоступен | локальный путь или явная ошибка | policy boundary в `main`; fallback зависит от caller |
| индекс недоступен | fallback/degraded retrieval | предусмотрено для ряда retrieval-компонентов |
| проекция повреждена | перестроить из авторитетного состояния | архитектурный инвариант; требуется end-to-end drill |
| конкурентная модификация | CAS conflict, не ложный успех | защищены конкретные write paths; не весь store |
| нет TRACE | не выдумывать объяснение | enforced в XAI-модуле |
| диск заполнен | остановить запись до коррупции | требует проверенного операционного сценария |
| audit artifact не записан после fact commit | обнаружить неполную операцию | известное crash-consistency ограничение |

---

## 🚫 Что Titan не обещает

- ❌ абсолютное отсутствие галлюцинаций;
- ❌ автоматическое доказательство истинности источника;
- ❌ сертифицированную GDPR/compliance-программу;
- ❌ независимый security audit, которого ещё не было;
- ❌ production-ready multi-user SaaS «из коробки»;
- ❌ сознание, субъективный опыт или самостоятельную волю;
- ❌ буквальный доступ LLM к весам, кластеру или скрытым внутренним активациям;
- ❌ что каждый файл в `core/` включён в default runtime;
- ❌ что открытый PR уже является частью системы.

Честная формулировка зрелости:

> **Research-grade local-first prototype moving toward production hardening.**

---

## 📚 Онбординг по ролям

### 👤 Пользователь

1. этот документ: [L0](#plain) → [карта](#map);
2. [`README.md`](README.md) — запуск и основные возможности;
3. help в web console.

### 🛠️ Оператор

1. [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md);
2. [`SECURITY.md`](SECURITY.md);
3. `/health`, `/layers/status`, `/titan/status`;
4. deployment profile и feature flags.

### 🧑‍💻 Инженер

1. [`docs/REVIEWER_README.md`](docs/REVIEWER_README.md);
2. `core/memory.py`, `core/truth_gate.py`, `core/pipeline.py`;
3. `tests/test_invariants.py`;
4. [`AGENTS.md`](AGENTS.md) — обязательные границы изменений;
5. ADR и канонические документы.

### 🔍 Аудитор

1. [`docs/REVIEWER_README.md`](docs/REVIEWER_README.md);
2. [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md);
3. [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md);
4. [`SECURITY.md`](SECURITY.md);
5. код + adversarial tests + CI, а не только README.

### 🤖 AI-агент

1. не считать этот Atlas write authority;
2. различать `main`, open PR и research;
3. проверять путь/символ перед заявлением;
4. возвращать proposal вместо скрытой мутации;
5. при конфликте документа и кода поднимать discrepancy;
6. не превращать согласие нескольких моделей с общим контекстом в независимое
   доказательство.

---

## 🔄 Как поддерживать Atlas актуальным

При изменении архитектуры PR должен ответить на пять вопросов:

```text
1. Что изменилось для человека?
2. Какой контракт изменился для инженера?
3. Какой статус теперь верен?
4. Где тест или runtime-evidence?
5. Как система ведёт себя при отказе?
```

Минимальные обновления:

- новая публичная возможность → `README.md`;
- новый или изменённый поток → этот Atlas;
- новая maturity/limitation → `docs/PROJECT_STATUS.md`;
- новый инвариант → код + тест + `docs/INVARIANTS.md`;
- исследовательская идея → `research/`, без runtime-формулировок;
- изменённая версия → `pyproject.toml` и `scripts/sync_docs.py`;
- открытый PR не переводится в 🟢 до merge и повторной проверки `main`.

---

## 💎 Суть в одной карте

```text
                         🔱 VELANTRIM TITAN
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
      🧠 ПАМЯТЬ               ⚖️ ДОВЕРИЕ             🧾 АУДИТ
          │                       │                       │
     facts + ESM          policy + evidence       TRACE + provenance
          │                       │                       │
          └───────────────┬───────┴───────────────┬───────┘
                          │                       │
                      🔍 ПОИСК                🗣️ ЯЗЫК
                          │                       │
                 indexes / graph         replaceable LLM
                          │                       │
                          └───────────┬───────────┘
                                      │
                              🧪 ПРОВЕРКА ПРЕДЕЛОВ
                                      │
                      model → test → telemetry → correction
```

> **Titan понимает и предлагает. Граница доверия проверяет и допускает.
> Kernel сохраняет инварианты. LLM остаётся заменяемым.**
