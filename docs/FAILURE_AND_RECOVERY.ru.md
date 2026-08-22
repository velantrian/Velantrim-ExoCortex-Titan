# 🧯 Titan V1 — Failure / Recovery

Этот документ описывает bounded V1-сценарии отказа и восстановления для обычного локального пользователя.

## 🚦 Если Titan не запускается

### Порт уже занят

Сообщение bootstrap указывает занятый порт.

Восстановление:

1. остановите уже запущенный Titan/uvicorn на этом порту; или
2. запустите Titan на другом порту:

```bash
python scripts/bootstrap_titan.py --port 8765
```

Bootstrap остаётся loopback-only и не расширяет сетевую поверхность.

### Не удалось установить зависимости

Bootstrap завершится с понятной ошибкой и не будет делать вид, что runtime готов.

Проверьте:

- доступ к интернету/Python package index;
- права записи в каталог проекта;
- Python 3.11+;
- наличие рабочего `venv`/`pip`.

После исправления причины повторно выполните:

```bash
python scripts/bootstrap_titan.py
```

### Сервер завершился во время старта

Bootstrap не считает такой процесс успешным: если дочерний uvicorn завершился до readiness, пользователь получает код завершения и указание смотреть server error выше.

Исправьте указанную конфигурационную/DB/import ошибку и повторите запуск.

### `/health` не стал доступен

Bootstrap ждёт bounded readiness window. Если Titan не становится ready, запуск завершается ошибкой вместо бесконечного ожидания.

Проверьте server output, затем повторите запуск после устранения причины.

## 🤖 Если LLM-провайдер недоступен

Titan разделяет provider failure и локальную память.

Если вызов LLM падает, обычный `/chat` уже пытается сформировать локальный offline reply из доступной памяти/заметок. Потоковый `/chat/stream` делает тот же bounded fallback и помечает usage как `offline_fallback`.

Это означает:

- отказ внешнего LLM не превращает локальные факты в недоступные;
- provider output не становится Canon автоматически;
- offline fallback не означает, что удалённый provider «успешно ответил»;
- если локального ответа сформировать нельзя, ошибка остаётся явной.

Практическое восстановление:

1. проверьте provider key/model;
2. проверьте разрешён ли remote egress согласно текущей policy;
3. при необходимости продолжайте работу с локальной памятью без LLM;
4. после восстановления provider повторите запрос.

## 🧠 Если memory pipeline деградировал

Console уже имеет bounded observed-memory fallback: ошибка retrieval/pipeline не должна автоматически уничтожать доступ к локально имеющимся данным.

При этом Titan не скрывает разницу между validated memory и observed/not-yet-validated material.

## 🛑 Остановка и повторный запуск

Обычная остановка:

```text
Ctrl+C
```

Повторный запуск:

```bash
python scripts/bootstrap_titan.py
```

Stage 6 уже закрепляет regressions, что существующие SQLite facts, Console notes и пользовательская `.env` переживают restart boundary.

## 🔒 Что Stage 7 НЕ обещает

Stage 7 не является:

- disaster-recovery системой;
- backup/restore subsystem;
- replication/failover;
- cloud sync;
- автоматическим восстановлением повреждённой БД;
- production HA;
- packaging/update lifecycle.

Packaging/update относится к Stage 8. Полное ordinary-user acceptance относится к Stage 9.

## ✅ Stage 7 exit contract

Stage 7 можно считать закрытым только если:

- startup failures дают явную причину и recovery action;
- early server exit не маскируется как успешный старт;
- readiness timeout fail-closed;
- dependency failure fail-closed;
- provider failure не расширяет authority и имеет bounded local fallback там, где локальный ответ действительно возможен;
- full repository CI/CodeQL/aggregate остаются зелёными;
- нет текущего P0/P1 failure/recovery blocker.
