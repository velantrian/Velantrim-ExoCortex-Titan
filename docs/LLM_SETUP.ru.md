# 🤖 Titan V1 — подключение модели / провайдера

> Канонический пользовательский путь после успешного первого запуска Titan.
> Цель: подключить remote LLM **явно и предсказуемо**, не ослабляя local-first defaults без согласия владельца.

---

## ✅ Что нужно сделать

Сначала останови запущенный Titan (`Ctrl+C`), затем из корня репозитория выполни:

```bash
python scripts/configure_llm.py
```

На Windows через Python Launcher также можно:

```powershell
py -3.11 scripts/configure_llm.py
```

Wizard предложит только direct server providers, которые текущий Titan действительно умеет исполнять:

- OpenAI;
- DeepSeek;
- Google Gemini;
- OpenRouter;
- Anthropic Claude.

Qwen доступен через соответствующие модели **OpenRouter**. Titan V1 не рекламирует Qwen как отдельный direct backend, пока отдельный transport не реализован и не доказан тестами.

---

## 🔐 Почему Titan спрашивает отдельное согласие

После Stage 2 новый Titan намеренно стартует так:

```env
VELANTRIM_NETWORK_MODE=deny
VELANTRIM_REMOTE_DATA_MODE=never
LLM_PROVIDER=none
```

Это означает: локальная память и Console работают, но сервер не имеет права сам отправлять данные наружу.

При настройке remote LLM wizard объяснит границу и попросит ввести точную фразу:

```text
ALLOW REMOTE DATA
```

Только после этого локальный `.env` будет изменён на:

```env
VELANTRIM_NETWORK_MODE=allow
VELANTRIM_REMOTE_DATA_MODE=allowed
LLM_PROVIDER=<выбранный provider>
```

и в него будет записан provider API key и выбранная модель.

Wizard:

- использует скрытый ввод API key;
- не печатает secret обратно в терминал;
- не меняет `VELANTRIM_API_KEY` Titan;
- сохраняет остальные пользовательские `.env`-настройки;
- заменяет `.env` атомарно, чтобы прерванная запись не оставила обрезанный файл;
- не создаёт runtime consent broker;
- не даёт браузеру authority менять egress policy;
- не даёт remote provider права писать в Canon.

---

## 🧪 Connection test и реальный chat — не одно и то же

Titan различает две операции.

### 1. Проверка ключа

Кнопка проверки LLM отправляет провайдеру только фиксированный synthetic prompt Titan. Пользовательский prompt, память, файлы и вложения в этот probe не допускаются.

Для такого probe требуется:

```env
VELANTRIM_NETWORK_MODE=allow
```

`VELANTRIM_REMOTE_DATA_MODE=allowed` для самого probe не требуется, потому что пользовательских данных там нет.

### 2. Обычный remote chat

Обычный chat может отправлять выбранному провайдеру:

- текст запроса пользователя;
- system instructions;
- выбранный контекст / memory, необходимый для ответа.

Поэтому normal remote chat требует одновременно:

```env
VELANTRIM_NETWORK_MODE=allow
VELANTRIM_REMOTE_DATA_MODE=allowed
```

Эти два разрешения wizard включает вместе только после явного согласия, чтобы не создавать ситуацию «ключ проверился, а настоящий chat всё равно заблокирован».

---

## 📊 Проверить конфигурацию без показа секретов

```bash
python scripts/configure_llm.py --status
```

Пример:

```text
Provider: gemini
Model: gemini-3.5-flash
API key configured: yes
Network policy: allow
Remote-data policy: allowed
Connection test ready: yes
Remote chat ready: yes
```

Значение самого API key эта команда не возвращает и не печатает.

---

## 🔄 После настройки

Titan читает `.env` при старте процесса. После wizard запусти Titan снова:

```bash
python scripts/bootstrap_titan.py
```

Затем открой:

```text
http://127.0.0.1:8755/console/
```

Выбери настроенный provider/model и используй проверку ключа. После успешного probe отправь обычное сообщение в chat.

---

## 📴 Вернуться в local-first режим

Чтобы запретить remote LLM снова, в `.env` верни:

```env
LLM_PROVIDER=none
VELANTRIM_NETWORK_MODE=deny
VELANTRIM_REMOTE_DATA_MODE=never
```

и перезапусти Titan.

Это отключает server-side remote LLM egress. Локальная память/Console продолжают работать без модели.

---

## 🛠️ Если что-то не работает

### `network_denied`

Titan не разрешён внешний network egress. Запусти канонический wizard и осознанно заверши настройку:

```bash
python scripts/configure_llm.py
```

### `remote_data_forbidden`

Network уже разрешён, но normal chat всё ещё не имеет права отправлять raw пользовательские данные наружу. Не обходи policy случайной ручной правкой — повтори wizard и прочитай remote-data boundary.

### 401 / invalid API key

Provider отверг ключ. Проверь, что ключ создан именно для выбранного provider и не перепутан с `VELANTRIM_API_KEY` Titan.

### 404 / model not found

Выбранная модель недоступна провайдеру/ключу. Вернись к default model wizard или выбери модель из текущего Console provider catalog.

### 429

Provider ограничил quota/rate. Titan не должен автоматически обходить этот лимит через другой provider.

---

## 🧭 Граница Stage 3

Эта настройка решает только **Model / Provider Setup**.

Она не:

- включает research/autonomous layers;
- создаёт новую authority;
- разрешает remote Canon writes;
- подключает file ingestion;
- меняет TruthGate;
- создаёт новый provider transport ради полноты каталога;
- превращает successful provider probe в production authorization.

`configured` / `probe passed` / `chat works` — это эксплуатационные состояния, а не право модели менять Canon или политику Titan.
