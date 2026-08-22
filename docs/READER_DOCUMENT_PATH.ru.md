# 📚 Titan Reader — поэтапное чтение длинных документов

**Статус:** `PR #374 CANDIDATE · POST-V1 · EXPLICIT FOREGROUND ONLY · NO CANON AUTHORITY`

Этот путь соединяет уже существующие компоненты Reader Core в один явный пользовательский сценарий:

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
- оставшуюся bounded reread work;
- идентификаторы ReadingSession / synthesis в JSON-режиме;
- warnings, которые не позволяют спутать interpretation с truth.

`source-grounded digest` — это не свободный «красивый пересказ» модели. Он собирается из уже принятых source-linked SectionCard essences. Это сознательно более консервативно: первый product bridge не расширяет доверенную поверхность LLM.

## 🔁 Bounded reread

Первый проход использует выбранный `ReaderMode`. Затем существующий `CoverageMap` и `SelectiveReReadPlanner` определяют, какие units требуют повторного внимания.

PR #374 исполняет **не более одного** такого reread round в рамках одной явной CLI-команды. Он не создаёт background worker, scheduler или бесконечный autonomous loop.

Если после bounded reread остаётся непрочитанный unit:

```text
ReadingSession → DEGRADED
GlobalDocumentSynthesis → NOT CREATED
remaining reread work → EXPLICIT
```

Titan не подменяет неполное чтение «готовой сутью».

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
4. Один bounded reread round не гарантирует, что любой проблемный документ станет complete.
5. Issue #120 остаётся отдельной программой production evidence: реальные rights-cleared корпуса, независимая human annotation, benchmark/calibration, shadow burn-in и Operator decision этим PR не закрываются.

## 🧭 Почему Reader не идёт через `/ingest/text`

`/ingest/text` — существующий governed memory/write path. Для чтения книги это неправильная граница: сначала документ должен быть прочитан и разобран как источник, а уже отдельное последующее решение может определить, какие source-linked claims вообще имеют право быть предложены memory admission.

Поэтому PR #374 использует:

```text
FileIngester → RawSource → Reader Core
```

а не:

```text
FileIngester → /ingest/text → memory → Reader
```

Это сохраняет разделение между **пониманием/извлечением** и **эпистемическим допуском/памятью**.
