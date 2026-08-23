# 📚 Titan Reader — поэтапное чтение длинных документов

**Статус:** `PR #374 MERGED · IN MAIN · POST-V1 · EXPLICIT FOREGROUND ONLY · NO CANON AUTHORITY`

**Accepted remediation head:** `c374ccf01ea1b73ff3c3012dce3cc4b45e84c4ef`  
**Merged/main checkpoint:** `b298ce65b2e9a50aaa0cabdf7772c73fd578ef91`

Этот путь соединяет уже существующие компоненты Reader Core в один явный пользовательский сценарий. Он присутствует в `main`, но сам факт merge не означает production/runtime authorization, Operator GO, memory/Canon write authority или закрытие Issue #120.

```text
PDF / DOCX / EPUB / TXT / MD
        ↓
FileIngester (локальный parser)
        ↓
RawSource + content hash
        ↓
DocumentStructureMap
        ↓
HierarchicalSectionPlanner
        ↓
SemanticReader (обычно LlmReaderAdapter)
        ↓
SectionCards + exact source spans
        ↓
CriticalExceptionScanner
        ↓
CoverageMap
        ↓
SelectiveReReadPlanner
        ↓
не более одного bounded reread round
        ↓
ReadingSession
        ↓
GlobalDocumentSynthesis candidate
        ↓
source-grounded digest для пользователя
```

## 🎯 Для чего это нужно

Reader path предназначен для книг, статей, отчётов, политик и других длинных документов, которые не следует пытаться «понять» одним огромным prompt/context window.

Titan делит источник на bounded reading units, читает их последовательно, сохраняет source-linked `SectionCard`, проверяет coverage, выявляет потенциальные исключения и при необходимости один раз возвращается к слабым участкам через существующий `SelectiveReReadPlanner`.

## ▶️ Запуск

Сначала должен быть установлен Titan V1 и явно настроен поддерживаемый provider через существующий onboarding:

```bash
python scripts/bootstrap_titan.py
python scripts/configure_provider.py
```

Затем:

```bash
python scripts/read_document.py ./book.pdf
```

Глубина первого прохода:

```bash
python scripts/read_document.py ./book.pdf --mode fast
python scripts/read_document.py ./book.pdf --mode standard
python scripts/read_document.py ./book.pdf --mode deep
```

Machine-readable результат:

```bash
python scripts/read_document.py ./book.pdf --json
```

Поддерживаемые входные форматы определяются существующим `FileIngester`; Reader path не создаёт второй parser subsystem.

## 🧠 Что означает результат

CLI показывает:

- количество запланированных и реально прочитанных units;
- число Reader attempts и selective rereads;
- независимые CoverageMap axes;
- source-grounded digest из `SectionCard.local_essence`;
- source-linked critical exception candidates;
- оставшуюся bounded reread work и deferred work;
- идентификаторы ReadingSession / synthesis в JSON-режиме;
- warnings, которые не позволяют спутать interpretation с truth.

Пользовательский статус намеренно отделён от внутреннего `ReadingSession` state:

```text
COMPLETE
  = все reading units обработаны и открытой reread/deferred work нет

COMPLETE_WITH_OPEN_WORK
  = все reading units обработаны и synthesis может существовать,
    но остаются явные follow-up задачи (например unresolved exception target)

DEGRADED
  = часть reading units реально не была успешно обработана
```

`COMPLETE_WITH_OPEN_WORK` нельзя интерпретировать как «в документе всё разрешено и понято». Это честная маркировка: чтение источника завершено, но Reader Core сохранил открытые вопросы/действия вместо их скрытого удаления.

`source-grounded digest` — это не свободный «красивый пересказ» модели. Он собирается из уже принятых source-linked SectionCard essences. Это сознательно более консервативно: первый product bridge не расширяет доверенную поверхность LLM.

### 🔗 Provenance при bounded digest

Ограничение `max_digest_chars` не даёт synthesis права заявлять больше provenance, чем реально видно в digest. `supporting_claim_ids` формируются только для claims, чей **полный exact claim text** присутствует в фактически сохранённой части essence соответствующей SectionCard. Если claim был отброшен upstream essence budget или обрезан границей итогового digest, он не считается supporting и остаётся `unsupported_source_claim_ids` в существующем synthesis contract.

То есть сокращение digest может уменьшить declared support, но не должно создавать ложный support.

## 🔁 Bounded reread

Первый проход использует выбранный `ReaderMode`. Затем существующий `CoverageMap` и `SelectiveReReadPlanner` определяют, какие units требуют повторного внимания.

Merged Reader path исполняет **не более одного** такого reread round в рамках одной явной CLI-команды. Он не создаёт background worker, scheduler или бесконечный autonomous loop.

Только reread task с явно назначенным самим `SelectiveReReadPlanner` значением `ReaderMode` может повторно вызвать `SemanticReader`. Задачи без `ReaderMode` (например действия, требующие отдельного разрешения exception target или inspection) **не превращаются автоматически в скрытый `DEEP` LLM-вызов**; они остаются видимой открытой работой.

Если после bounded reread остаётся непрочитанный unit:

```text
ReadingSession → DEGRADED
GlobalDocumentSynthesis → NOT CREATED
remaining reread work → EXPLICIT
```

Titan не подменяет неполное чтение «готовой сутью».

## 📊 Что означают usage-метрики

`ReadingSessionUsage` в этом product bridge — это **частичная card-centric observability**, а не полный расчёт стоимости provider calls.

- `processed_units` относится к записанным cards/units, а не к числу provider вызовов;
- `source_chars` отражает source spans записанных cards и не заявляет cumulative reread transport volume;
- `model_tokens` может оставаться недоступным/default, если существующий `SemanticReader` contract не передаёт usage в product bridge;
- фактическое число execution attempts отдельно видно через `reader_attempts` и `reread_attempts`.

Titan не должен выдумывать точность token/cost accounting, которой нет в существующем контракте.

## 🔐 Authority boundary

```text
Reader output          != truth
SectionCard            != Canon
Coverage               != understanding
synthesis              != fact
model output            != authority
CLI invocation          != runtime activation
successful test         != production evidence
```

Reader product path:

- не вызывает `/ingest/text`;
- не вызывает `store_fact()`;
- не вызывает TruthGate / Write Gate;
- не меняет ESM;
- не пишет в Canon;
- не пишет в Crystal;
- не создаёт graph authority;
- не запускается в фоне;
- не авторизует production/runtime/canary.

Remote document text может передаваться только через уже существующий `LlmReaderAdapter` → `llm_router` → remote-egress policy. Настройка provider и remote-data consent остаётся у существующего Titan onboarding; этот CLI не создаёт обходной network path.

## ⚠️ Текущие ограничения v1

1. `ReadingSession` snapshot пока остаётся in-memory контрактом; durable cross-process resume этим PR не добавляется.
2. Автоматический cross-section relation detector не включён. Product v1 создаёт валидный relation set без выдумывания отношений.
3. Global synthesis остаётся source-linked interpretation candidate, а не epistemic verdict.
4. Один bounded reread round не гарантирует, что любой проблемный документ станет `COMPLETE`; возможны `COMPLETE_WITH_OPEN_WORK` или `DEGRADED`.
5. Machine-readable open-work detail можно расширять в будущем, но отсутствие richer UI metadata не скрывает сам факт remaining/deferred work и не является authority boundary.
6. Issue #120 остаётся отдельной программой production evidence: реальные rights-cleared корпуса, независимая human annotation, benchmark/calibration, shadow burn-in и Operator decision PR #374 не закрывает.

## 🧭 Почему Reader не идёт через `/ingest/text`

`/ingest/text` — существующий governed memory/write path. Для чтения книги это неправильная граница: сначала документ должен быть прочитан и разобран как источник, а уже отдельное последующее решение может определить, какие source-linked claims вообще имеют право быть предложены memory admission.

Поэтому merged Reader path использует:

```text
FileIngester → RawSource → Reader Core
```

а не:

```text
FileIngester → /ingest/text → memory → Reader
```

Это сохраняет разделение между **пониманием/извлечением** и **эпистемическим допуском/памятью**.
