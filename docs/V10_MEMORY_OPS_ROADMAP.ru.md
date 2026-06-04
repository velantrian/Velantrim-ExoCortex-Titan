# VELANTRIM V10 MemoryOps Roadmap

Дата: 2026-05-24

Цель этого слоя — превратить память из набора фактов в рабочую операционную
систему: у каждого знания должен быть источник, стадия допуска, история
изменений и объяснимый след использования в ответе.

## Уже добавлено

### Source Registry

`source_registry` хранит явные источники:

- `source_type`: chat, document, telegram, api, operator, system.
- `label`: человекочитаемое имя источника.
- `uri`: путь, URL или внешний идентификатор.
- `trust`: базовый вес доверия источника.
- `metadata`: произвольный контекст.

API:

- `POST /sources`
- `GET /sources`
- `GET /sources/{source_id}`

### Fact Inbox

`fact_inbox` — очередь кандидатов на память. Новое знание можно сначала
положить в `pending`, потом принять, отклонить, архивировать или продвинуть в
канонический `facts`.

API:

- `POST /memory/inbox`
- `GET /memory/inbox`
- `PATCH /memory/inbox/{inbox_id}/status`
- `POST /memory/inbox/{inbox_id}/promote`

### Memory Diff

`GET /memory/diff` отвечает на вопрос: что изменилось в памяти. Он собирает
факты, inbox, источники, L0 raw entries и reasoning traces.

### Reasoning Trace

`reasoning_traces` хранит компактный след ответа: query, answer, режим,
линзу, использованные fact_id, отброшенные fact_id и заметки. `POST /query`
теперь сохраняет автоматический trace и возвращает `reasoning_trace_id`.

API:

- `POST /memory/traces`
- `GET /memory/traces`
- `GET /memory/traces/{trace_id}`

## Следующие шаги

1. Привязать Source Registry к file parsers и Telegram ingest автоматически.
2. Сделать Memory Inspector в веб-консоли: источники, inbox, diff, traces.
3. Добавить Contradiction Dashboard поверх CausalGraph и TruthGate.
4. Научить SleepTimeWorker ночью разбирать `fact_inbox`, искать дубли и
   предлагать promote/reject.
5. Расширить ReasoningTrace до полного "why this answer" с исключёнными
   фактами, thresholds и decisions TruthGate.
6. Добавить forgetting policy: не delete, а переходы active → archived →
   cold storage с сохранением аудита.

## Инварианты

- L0 сырьё не теряется.
- L1 facts остаются каноническим источником истины.
- Inbox не должен автоматически делать факт истинным.
- Trace не является доказательством; это объяснение пути ответа.
- Новые контуры должны быть additive: старые API не ломаются.
