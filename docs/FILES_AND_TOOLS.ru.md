# 📁🧰 Titan V1 — файлы и инструменты

Этот документ описывает **пользовательский Stage 5 путь**. Он не требует знания внутренней архитектуры FileIngester или MCP.

## 1. Сначала запусти Titan

```bash
python scripts/bootstrap_titan.py
```

Bootstrap V1 устанавливает server runtime и bounded parser dependencies в `.venv`.

## 2. Использовать локальный файл

Оставь Titan запущенным и во втором терминале выполни:

```bash
python scripts/ingest_file.py "/путь/к/файлу.pdf"
```

Windows пример:

```powershell
python scripts/ingest_file.py "C:\Users\me\Documents\report.docx"
```

Helper автоматически использует `.venv`, если она создана Stage 2 bootstrap.

Что происходит:

1. файл остаётся локальным;
2. существующий `FileIngester` извлекает текст;
3. helper отправляет текст только на локальный `127.0.0.1` endpoint `/ingest/text`;
4. используется `VELANTRIM_API_KEY` из локального `.env`;
5. запись проходит существующий server/memory write path — helper не пишет в Canon напрямую;
6. после этого содержимое можно искать и использовать через обычную Console/memory path.

Основной V1 parser extra покрывает PDF, DOCX, XLSX/CSV, text/Markdown/JSON/YAML и изображения. Тяжёлые audio/video ML dependencies не включаются автоматически.

Если конкретный формат требует дополнительную опциональную зависимость, Titan вернёт понятную parser error; это не включает пакет автоматически и не меняет authority.

## 3. Посмотреть доступные инструменты

```bash
python scripts/titan_tools.py list
```

По умолчанию запрашивается capability `reader`. Сервер всё равно применяет собственный `VELANTRIM_MCP_MAX_CAPABILITY`; клиент не может поднять себе полномочия этим параметром.

## 4. Вызвать существующий tool

Сначала посмотри имя и input schema через `list`, затем:

```bash
python scripts/titan_tools.py call search_facts '{"query":"Titan"}'
```

На PowerShell кавычки могут отличаться; JSON-аргумент должен быть объектом.

Если оператор **уже** разрешил более высокий MCP ceiling, можно запросить соответствующую capability:

```bash
python scripts/titan_tools.py --capability ingester list
```

Это не повышает ceiling: gateway по-прежнему clamp'ит запрос к server-side policy.

## 🔐 Границы безопасности

- CLI не создаёт новые tools.
- CLI не создаёт новую authority.
- `VELANTRIM_API_KEY` читается из `.env`, а не передаётся как shell argument.
- File helper обращается только к loopback Titan server.
- File helper использует существующий `/ingest/text`, поэтому действующие write gates сохраняются.
- MCP destructive tools остаются скрыты/запрещены при reader ceiling.
- Remote LLM policy из Stage 3 не меняется.

## 🧠 Что исправлено в TruthGate на этом этапе

Legacy `metadata.evidence_refs` больше не может увеличить evidence cardinality простым повторением одной и той же строки.

Пример:

```json
["source-A", "source-A"]
```

считается как **1** legacy evidence token, а:

```json
["source-A", "source-B"]
```

как **2**.

Это только bounded normalization старого string-list контракта. Оно **не** вводит EvidenceReference authority, trusted registry, independence classifier или Evidence Admission.
