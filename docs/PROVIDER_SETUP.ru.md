# 🤖 Velantrim Titan — подключение модели

> Это канонический путь **Stage 3 · Model / Provider Setup** для локального Titan.
> Первый запуск должен быть уже завершён через `scripts/bootstrap_titan.py`.

## ✅ Цель

После настройки обычный пользователь может:

- выбрать поддерживаемого провайдера;
- сохранить его API-ключ только в локальном `.env`;
- явно разрешить сетевой вызов и передачу prompt/context удалённой модели;
- перезапустить Titan;
- открыть Web Console и подтвердить ключ у провайдера;
- включить LLM и продолжить обычный чат.

## 🔐 Почему нужен отдельный consent

Titan после первого запуска остаётся fail-closed:

```env
VELANTRIM_NETWORK_MODE=deny
VELANTRIM_REMOTE_DATA_MODE=never
LLM_PROVIDER=none
```

Это намеренно. Удалённая модель не должна включаться только потому, что где-то появился API-ключ.

Обычный remote chat передаёт провайдеру пользовательский prompt и может передавать выбранный Titan memory/context. Поэтому для такого режима нужны одновременно:

```env
VELANTRIM_NETWORK_MODE=allow
VELANTRIM_REMOTE_DATA_MODE=allowed
```

Конфигуратор выставляет эти значения **только после явного подтверждения пользователя**.

## 1. Останови Titan

Если сервер сейчас работает, нажми в его терминале:

```text
Ctrl+C
```

## 2. Запусти конфигуратор

Из корня репозитория:

### Windows

```powershell
python scripts/configure_provider.py
```

### macOS / Linux

```bash
python3 scripts/configure_provider.py
```

Конфигуратор предложит один из уже поддерживаемых сервером провайдеров:

- `openai`
- `deepseek`
- `gemini`
- `openrouter`
- `anthropic`

API-ключ вводится скрыто через системный password prompt и не печатается в терминал.

## 3. Подтверди remote-data boundary

Перед изменением egress policy конфигуратор объяснит, что удалённая модель получает отправленный ей prompt и может получать выбранный memory/context.

Для разрешения требуется ввести **точно**:

```text
ALLOW
```

Любой другой ответ считается отказом. В этом случае `.env` не изменяется и Titan остаётся local-only.

## 4. Что изменится в `.env`

Например, для DeepSeek:

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=<локальный секрет>
DEEPSEEK_MODEL=deepseek-v4-flash
VELANTRIM_NETWORK_MODE=allow
VELANTRIM_REMOTE_DATA_MODE=allowed
```

При этом конфигуратор:

- не меняет `VELANTRIM_API_KEY`;
- не включает `VELANTRIM_ALLOW_OPEN`;
- не меняет Canon/write authority;
- не включает research/autonomous layers;
- не отправляет ключ куда-либо сам;
- сохраняет посторонние настройки `.env`;
- записывает `.env` атомарно;
- на POSIX старается оставить новый временный файл с правами `0600` до atomic replace.

## 5. Перезапусти Titan

```bash
python scripts/bootstrap_titan.py
```

Bootstrap переиспользует существующие `.venv` и `.env` и не должен переписывать provider/egress-настройки.

## 6. Проверь модель в Console

Открой:

```text
http://127.0.0.1:8755/console/
```

Дальше:

1. выбери тот же provider;
2. при необходимости вставь его API-ключ в блок LLM;
3. нажми **«Подтвердить ключ»**;
4. дождись успешного provider probe;
5. включи **LLM**;
6. отправь обычное сообщение.

Важно: «Подтвердить ключ» — это connectivity probe без пользовательского payload. Реальный чат дополнительно проходит Titan remote-data policy. Конфигуратор выше заранее включает именно тот явный opt-in, который нужен обычному remote chat.

## 🛠️ Если не работает

### `Remote egress denied (network_denied ...)`

Текущая среда процесса всё ещё видит запрет сети. Убедись, что в `.env` есть:

```env
VELANTRIM_NETWORK_MODE=allow
```

и **перезапусти Titan**.

### `Remote egress denied (remote_data_forbidden ...)`

Сеть разрешена, но передача prompt/context запрещена. Для обычного remote chat после осознанного opt-in нужно:

```env
VELANTRIM_REMOTE_DATA_MODE=allowed
```

и перезапуск сервера.

### Ключ подтверждается, но чат не отвечает моделью

Проверка ключа специально не несёт пользовательских данных и использует более узкую metadata-only capability. Это не означает автоматического разрешения передавать провайдеру текст чата. Проверь обе egress-настройки выше и перезапуск процесса.

### Неверный ключ / 401

Создай или проверь ключ у выбранного провайдера и повтори **«Подтвердить ключ»**.

### Модель не найдена / 404

Выбери модель из текущего списка Console или снова запусти конфигуратор с явной моделью:

```bash
python scripts/configure_provider.py --provider openai --model chat-latest
```

Ключ всё равно будет запрошен скрыто.

## ⚙️ Неинтерактивный consent

Для автоматизированного локального развёртывания существует явный флаг:

```bash
python scripts/configure_provider.py --provider openai --allow-remote-data
```

Он означает то же осознанное разрешение `network=allow` + `remote_data=allowed`. API-ключ по-прежнему не принимается аргументом командной строки, чтобы не оставлять секрет в shell history.

## 🎯 Граница Stage 3

Этот путь **не**:

- даёт LLM право писать в Canon;
- меняет TruthGate;
- создаёт consent broker или новую runtime authority;
- включает remote Canon;
- включает autonomous/research layers;
- подключает файлы/tools E2E.

Он только превращает уже существующий provider runtime в предсказуемый, явный и безопасный для обычного пользователя путь настройки.
