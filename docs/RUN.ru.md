# 🚀 Velantrim Titan — установка и первый запуск

> Это **канонический путь первого запуска Titan V1** для обычного пользователя.
> Старые инструкции с архивами v8.x, ручной миграцией SQLite и поштучной установкой пакетов больше не являются актуальным способом установки.

---

## ✅ Что получится после этих шагов

После первого запуска Titan автоматически:

- проверит, что используется Python 3.11+;
- проверит целостность checkout по ключевым файлам;
- создаст локальное виртуальное окружение `.venv`;
- установит минимальные зависимости server runtime;
- создаст `.env`, если его ещё нет;
- сгенерирует случайный `VELANTRIM_API_KEY` вместо общего dev-key;
- оставит network/remote-data policy в безопасном fail-closed режиме;
- запустит FastAPI только на `127.0.0.1`;
- дождётся `/health` и откроет локальную Web Console.

LLM **не нужен для первого запуска**. Titan стартует с `LLM_PROVIDER=none`; модель подключается отдельным явным шагом после проверки локального запуска.

---

## 📋 Требования

Нужно только:

- **Python 3.11 или новее**;
- **Git**;
- доступ к Python Package Index при первом запуске, чтобы установить server dependencies;
- Windows, macOS или Linux.

Проверь Python:

```bash
python --version
```

На Windows, если команда `python` не найдена, но установлен Python Launcher:

```powershell
py -3.11 --version
```

---

## 1. Получи Titan

```bash
git clone https://github.com/velantrian/Velantrim-ExoCortex-Titan.git
cd Velantrim-ExoCortex-Titan
```

Если репозиторий уже скачан:

```bash
git pull --ff-only
```

---

## 2. Запусти bootstrap

### Windows

```powershell
python scripts/bootstrap_titan.py
```

или через Python Launcher:

```powershell
py -3.11 scripts/bootstrap_titan.py
```

### macOS / Linux

```bash
python3 scripts/bootstrap_titan.py
```

Первый запуск может установить зависимости в `.venv`. Последующие запуски используют уже подготовленное окружение.

---

## 3. Открой Console

По умолчанию bootstrap открывает:

```text
http://127.0.0.1:8755/console/
```

Если браузер не открылся автоматически — открой этот адрес вручную.

Проверка сервера:

```text
http://127.0.0.1:8755/health
```

Остановить Titan:

```text
Ctrl+C
```

---

## 4. Подключи модель, если она нужна

Remote LLM — **не обязательная часть первого запуска**. Если локальная Console уже работает и ты хочешь подключить модель, сначала останови Titan, затем выполни:

```bash
python scripts/configure_llm.py
```

На Windows также можно:

```powershell
py -3.11 scripts/configure_llm.py
```

Wizard:

- предложит только реально поддерживаемые direct server providers;
- попросит API key через скрытый ввод;
- объяснит, какие данные будут отправляться remote provider;
- потребует явную фразу согласия перед изменением egress policy;
- не выведет secret обратно в терминал;
- сохранит остальные `.env`-настройки.

После настройки снова запусти:

```bash
python scripts/bootstrap_titan.py
```

Проверить readiness без показа API key:

```bash
python scripts/configure_llm.py --status
```

Подробно: [`LLM_SETUP.ru.md`](LLM_SETUP.ru.md).

---

## 🔐 Что происходит с `.env`

Если `.env` отсутствует, bootstrap создаёт его из `.env.example` и задаёт безопасные локальные значения:

```env
VELANTRIM_API_KEY=<случайно сгенерированный ключ>
VELANTRIM_ALLOW_OPEN=false
VELANTRIM_NETWORK_MODE=deny
VELANTRIM_REMOTE_DATA_MODE=never
LLM_PROVIDER=none
```

Если `.env` уже существует, пользовательские provider/network-настройки **не переписываются**. Если ключ пустой, bootstrap только заполняет `VELANTRIM_API_KEY`.

`.env` и `.venv` исключены из Git и не должны коммититься.

Remote model setup меняет `network/data` policy только после отдельного явного согласия пользователя. Один введённый provider API key сам по себе не является разрешением на egress.

---

## ⚙️ Полезные параметры

Запустить без автоматического открытия браузера:

```bash
python scripts/bootstrap_titan.py --no-browser
```

Использовать другой порт:

```bash
python scripts/bootstrap_titan.py --port 8765
```

Не разрешать bootstrap устанавливать отсутствующие зависимости:

```bash
python scripts/bootstrap_titan.py --no-install
```

В этом режиме он завершится с понятной ошибкой, если `.venv` ещё не подготовлено.

---

## 🛠️ Частые проблемы первого запуска

### Python ниже 3.11

Bootstrap завершится до любых изменений и сообщит обнаруженную версию.

Установи Python 3.11+ и повтори команду.

### Не удалось создать `.venv`

Убедись, что каталог проекта доступен на запись и в установленном Python присутствует модуль `venv`.

На некоторых Linux-дистрибутивах пакет `venv` устанавливается отдельно системным package manager.

### Не удалось установить зависимости

Проверь интернет-доступ и доступ к Python package index. Bootstrap не скрывает вывод `pip`, поэтому исходная ошибка остаётся видимой.

После исправления причины просто запусти ту же команду снова.

### Порт 8755 уже занят

Либо останови старый Titan, либо используй другой порт:

```bash
python scripts/bootstrap_titan.py --port 8765
```

Bootstrap **не убивает чужие процессы автоматически**.

### Сервер завершился во время старта

Bootstrap сообщит код завершения. Ошибка самого `uvicorn/server.py` остаётся в терминале прямо перед сообщением bootstrap.

### `/health` не стал доступен

Bootstrap ждёт готовность до 45 секунд. Если сервер не становится доступен, он завершает запуск с ошибкой вместо ложного сообщения «готово».

### Модель не подключается

Не меняй `deny/never` вслепую. Сначала выполни:

```bash
python scripts/configure_llm.py --status
```

Если remote LLM действительно нужен — повтори канонический wizard:

```bash
python scripts/configure_llm.py
```

Диагностика provider/policy описана в [`LLM_SETUP.ru.md`](LLM_SETUP.ru.md).

---

## 🧑‍💻 Для разработчика

Ручной dev-путь остаётся доступен и не является обязательным для обычного пользователя:

```bash
python -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\activate
python -m pip install -e ".[server,dev]"
uvicorn server:app --port 8000 --reload
```

Полный тестовый набор:

```bash
python -m pytest tests/ -v --tb=short
```

API docs по умолчанию могут быть отключены. Не используй наличие `/docs` как критерий успешного первого запуска; каноническая проверка — `/health` и Web Console.

---

## 🐳 Docker

Для hardened deployment существует отдельный операторский путь в корневом `README.md` и `docs/operations/hardened-production-profile.md`.

Он **не заменяет** этот first-run путь: этот документ предназначен для человека, который хочет впервые локально запустить Titan и открыть интерфейс.

---

## 🎯 Граница пользовательского setup

Installation и provider setup намеренно не:

- включают удалённую модель автоматически;
- дают браузеру право менять remote egress authority;
- включают research/autonomous layers;
- подключают file ingestion;
- изменяют TruthGate;
- создают новую runtime authority;
- разрешают remote Canon writes.

Сначала Titan работает локально. Remote model становится доступна только как отдельный осознанный opt-in владельца установки.
