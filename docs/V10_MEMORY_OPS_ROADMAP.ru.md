# VELANTRIM V10 MemoryOps Roadmap

Дата: 2026-05-24

Цель этого слоя — превратить память из набора фактов в рабочую операционную
систему: у каждого знания должен быть источник, стадия допуска, история
изменений и объяснимый след прохождения через ответный путь.

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
линзу, `source_fact_ids` фактов, присутствовавших в наблюдаемом trace-пути,
`rejected_fact_ids` и заметки. `POST /query` теперь сохраняет автоматический
trace и возвращает `reasoning_trace_id`.

Важно: наличие `fact_id` в `source_fact_ids` само по себе не доказывает, что
факт был семантически использован моделью, поддержал конкретное утверждение
ответа или имеет decision authority. Trace membership — это наблюдение пути,
а не causal/answer-support attribution.

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
5. Если понадобится полный "why this answer", сначала отдельно измерить и
   определить контракт semantic use / answer support; текущий ReasoningTrace
   не должен автоматически считаться таким attribution-механизмом.
6. Добавить forgetting policy: не delete, а переходы active → archived →
   cold storage с сохранением аудита.

## Инварианты

- L0 сырьё не теряется.
- L1 facts остаются каноническим источником истины.
- Inbox не должен автоматически делать факт истинным.
- Trace не является доказательством semantic use, answer support или decision authority.
- Trace membership ≠ semantic use ≠ answer support ≠ decision authority.
- Новые контуры должны быть additive: старые API не ломаются.
